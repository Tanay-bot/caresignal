"""Gemini transport, completion, evidence, and service checks without network calls."""

import json

import pytest
from google import genai
from google.genai import errors, types

from caresignal.extractors import (
    SYSTEM_PROMPT,
    ExtractionUnavailable,
    GeminiExtractor,
    InvalidExtraction,
)
from caresignal.fixtures import (
    FRUTA_DATE,
    FRUTA_NOTE,
    FRUTA_RESIDENT_NAME,
    FRUTA_TARGET_CUE,
)
from caresignal.models import AssistanceLevel, RunStatus, Target
from caresignal.service import CareSignalService


def target():
    return Target(
        resident_id="source-resident",
        resident_name=FRUTA_RESIDENT_NAME,
        context_key="walking_attempt",
        observed_on=FRUTA_DATE,
        target_cue=FRUTA_TARGET_CUE,
    )


def prediction(**updates):
    result = {
        "label": "HANDS_ON",
        "reason_code": "PHYSICAL_SUPPORT",
        "reason": "Physical support was given during this walking attempt.",
        "quotes": [FRUTA_NOTE],
        "device": None,
    }
    return {**result, **updates}


def response(text=None, finish="STOP", **kwargs):
    return types.GenerateContentResponse(
        candidates=[
            types.Candidate(
                content=types.Content(parts=[types.Part(text=text or json.dumps(prediction()))]),
                finish_reason=finish,
            )
        ],
        **kwargs,
    )


class FakeClient:
    def __init__(self, result=None, error=None):
        self.models = self
        self.result = result if result is not None else response()
        self.error = error
        self.kwargs = None
        self.closed = False

    def generate_content(self, **kwargs):
        self.kwargs = kwargs
        if self.error:
            raise self.error
        return self.result

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.closed = True


def test_gemini_native_contract_preserves_full_target_note_and_exact_adjacent_evidence():
    client = FakeClient()
    extractor = GeminiExtractor(model_id="test-gemini", client=client)
    result = extractor.extract(FRUTA_NOTE, target(), "source-v1")
    assert result.label == AssistanceLevel.HANDS_ON
    assert len(result.evidence) == 1
    span = result.evidence[0]
    assert span.revision_id == "source-v1"
    assert FRUTA_NOTE[span.start : span.end] == span.quote == FRUTA_NOTE
    assert json.loads(client.kwargs["contents"]) == {
        "target": target().model_dump(mode="json"),
        "note": FRUTA_NOTE,
    }
    assert client.kwargs["model"] == "test-gemini"
    config = types.GenerateContentConfig.model_validate(client.kwargs["config"])
    assert config.system_instruction == SYSTEM_PROMPT
    assert config.response_mime_type == "application/json"
    assert config.response_json_schema["additionalProperties"] is False
    assert not client.closed  # Injected clients stay caller-owned.


@pytest.mark.parametrize(
    "text",
    [
        "{",
        json.dumps(prediction(label="SEVERE")),
        json.dumps(prediction(quotes=["A staff member steadied her while walking."])),
        json.dumps(prediction(quotes=[])),
        json.dumps({**prediction(), "unexpected": "field"}),
    ],
)
def test_gemini_rejects_invalid_json_schema_and_unsupported_evidence(text):
    with pytest.raises(InvalidExtraction):
        GeminiExtractor(client=FakeClient(response(text))).extract(FRUTA_NOTE, target(), "v1")


def test_gemini_rejects_repeated_quote_without_unique_event_evidence():
    with pytest.raises(InvalidExtraction):
        GeminiExtractor(client=FakeClient()).extract(FRUTA_NOTE + " " + FRUTA_NOTE, target(), "v1")


@pytest.mark.parametrize(
    "finish,category", [("MAX_TOKENS", "incomplete_response"), ("SAFETY", "refusal")]
)
def test_gemini_never_accepts_valid_looking_json_from_an_incomplete_or_blocked_response(
    finish, category
):
    with pytest.raises(ExtractionUnavailable, match=category):
        GeminiExtractor(client=FakeClient(response(finish=finish))).extract(
            FRUTA_NOTE, target(), "v1"
        )


def test_gemini_prompt_block_is_unavailable_even_without_candidates():
    blocked = types.GenerateContentResponse(
        prompt_feedback=types.GenerateContentResponsePromptFeedback(block_reason="SAFETY")
    )
    with pytest.raises(ExtractionUnavailable, match="refusal"):
        GeminiExtractor(client=FakeClient(blocked)).extract(FRUTA_NOTE, target(), "v1")


def test_gemini_missing_candidate_is_invalid_output():
    with pytest.raises(InvalidExtraction):
        GeminiExtractor(client=FakeClient(types.GenerateContentResponse())).extract(
            FRUTA_NOTE, target(), "v1"
        )


@pytest.mark.parametrize(
    "code,category",
    [
        (403, "authentication"),
        (429, "rate_limit"),
        (404, "incompatible_model"),
        (504, "timeout"),
        (500, "provider_error"),
    ],
)
def test_gemini_provider_errors_are_sanitized(code, category):
    error = errors.APIError(code, {"error": {"message": "private-key-and-note-sentinel"}})
    with pytest.raises(ExtractionUnavailable) as raised:
        GeminiExtractor(client=FakeClient(error=error)).extract(FRUTA_NOTE, target(), "v1")
    assert str(raised.value) == category
    assert "private-key" not in str(raised.value)


def test_gemini_invalid_key_error_is_authentication_instead_of_model_error():
    error = errors.APIError(400, {"error": {"details": [{"reason": "API_KEY_INVALID"}]}})
    with pytest.raises(ExtractionUnavailable, match="authentication"):
        GeminiExtractor(client=FakeClient(error=error)).extract(FRUTA_NOTE, target(), "v1")


def test_gemini_missing_key_never_constructs_provider_client(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    def unexpected(**kwargs):
        pytest.fail("A missing credential must not construct an API client")

    monkeypatch.setattr(genai, "Client", unexpected)
    with pytest.raises(ExtractionUnavailable, match="missing_credentials"):
        GeminiExtractor().extract(FRUTA_NOTE, target(), "v1")


def test_gemini_owned_client_uses_bounded_timeout_and_closes(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_MODEL", "configured-gemini")
    client = FakeClient()
    created = {}

    def factory(**kwargs):
        created.update(kwargs)
        return client

    monkeypatch.setattr(genai, "Client", factory)
    extractor = GeminiExtractor()
    extractor.extract(FRUTA_NOTE, target(), "v1")
    assert extractor.model_id == "configured-gemini"
    assert created["api_key"] == "test-key"
    assert created["http_options"]["timeout"] == 30_000
    assert client.closed


def test_incomplete_gemini_replacement_clears_prior_result_and_preserves_safe_error(tmp_path):
    service = CareSignalService(tmp_path / "history.sqlite3", "session")
    case = service.reset_demo()[0]
    before = service.get_handoff_view(case.id)
    assert before.comparison.status == "MORE_HELP"
    service.replace_active_revision(case.id, before.revision.id, FRUTA_NOTE)
    run = service.analyze_active_revision(
        case.id, GeminiExtractor(client=FakeClient(response(finish="MAX_TOKENS")))
    )
    view = service.get_handoff_view(case.id)
    assert run.status == RunStatus.UNAVAILABLE
    assert run.error_category == "incomplete_response"
    assert view.comparison.status == "ANALYSIS_UNAVAILABLE"
    assert view.run.result is None
    assert [item.version for item in service.history(case.id)] == [2, 1]
