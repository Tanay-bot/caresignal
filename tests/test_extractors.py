"""Executable attribution checks and mocked transport contracts; no API needed."""

from datetime import date
from types import SimpleNamespace

import pytest

from caresignal.extractors import (
    ExtractionUnavailable,
    FixtureExtractor,
    InvalidExtraction,
    OpenAIExtractor,
    PhraseMatcher,
)
from caresignal.fixtures import (
    DEMO_DATE,
    DEMO_NOTE,
    DEMO_REPLACEMENT,
    WALKING_ATTEMPT_NOTE,
    WALKING_ATTEMPT_QUOTE,
)
from caresignal.models import AssistanceLevel, Target


def target(context="to_breakfast", **kwargs):
    values = dict(
        resident_id="elena", resident_name="Elena", context_key=context, observed_on=DEMO_DATE
    )
    values.update(kwargs)
    return Target(**values)


def assert_source(result, body):
    for span in result.evidence:
        assert span.revision_id == "revision-1"
        assert body[span.start : span.end] == span.quote


def test_fixture_walkthrough_has_exact_evidence_and_two_resident_compatibility():
    extractor = FixtureExtractor()
    for name in ("Elena", "Ruth"):
        result = extractor.extract(DEMO_NOTE, target(resident_name=name), "revision-1")
        assert result.label == AssistanceLevel.SUPERVISION
        assert_source(result, DEMO_NOTE)
    replacement = extractor.extract(DEMO_REPLACEMENT, target(), "revision-1")
    assert replacement.label == AssistanceLevel.UNCLEAR
    assert replacement.device == "walker"
    assert_source(replacement, DEMO_REPLACEMENT)


@pytest.mark.parametrize(
    "body,selected",
    [
        ("She walked independently to breakfast.", target()),
        (DEMO_NOTE, target("from_breakfast")),
        (DEMO_NOTE, target(observed_on=date(2025, 1, 1))),
        (DEMO_NOTE, target(target_cue="afternoon walk")),
    ],
)
def test_fixture_never_pretends_to_analyze_custom_input(body, selected):
    result = FixtureExtractor().extract(body, selected, "revision-1")
    assert result.label == AssistanceLevel.UNCLEAR
    assert result.reason_code == "FIXTURE_INPUT_UNSUPPORTED"
    assert not result.evidence


def test_fictional_adjacent_sentence_fixture_is_not_claimed_as_fruta():
    result = FixtureExtractor().extract(
        WALKING_ATTEMPT_NOTE, target("walking_attempt"), "revision-1"
    )
    assert result.label == AssistanceLevel.HANDS_ON
    assert result.evidence[0].quote == WALKING_ATTEMPT_QUOTE
    assert_source(result, WALKING_ATTEMPT_NOTE)


@pytest.mark.parametrize(
    "body,context,expected",
    [
        (DEMO_NOTE, "to_breakfast", "SUPERVISION"),
        (WALKING_ATTEMPT_NOTE, "walking_attempt", "HANDS_ON"),
        ("She walked independently to breakfast with her walker.", "to_breakfast", "INDEPENDENT"),
        ("She walked to breakfast with her walker.", "to_breakfast", "UNCLEAR"),
        ("An aide helped her walk to breakfast.", "to_breakfast", "HELP_UNSPECIFIED"),
        (
            "She walked to breakfast with verbal cueing from an aide.",
            "to_breakfast",
            "HELP_UNSPECIFIED",
        ),
        ("Nobody helped her while she walked to breakfast.", "to_breakfast", "INDEPENDENT"),
        ("I did not see whether anyone helped her walk to breakfast.", "to_breakfast", "UNCLEAR"),
        ("Yesterday she walked to breakfast with hands-on support.", "to_breakfast", "UNCLEAR"),
        ("Her roommate walked independently to breakfast.", "to_breakfast", "UNCLEAR"),
        ("Ruth walked independently to breakfast.", "to_breakfast", "UNCLEAR"),
        ("She would have walked to breakfast with hands-on support.", "to_breakfast", "UNCLEAR"),
        ("She declined assistance walking to breakfast.", "to_breakfast", "UNCLEAR"),
        (
            "An aide helped her get out of bed. She walked to breakfast with her walker.",
            "to_breakfast",
            "UNCLEAR",
        ),
        (
            "She walked to breakfast. An aide helped her transfer into a chair.",
            "to_breakfast",
            "UNCLEAR",
        ),
        (
            "She walked independently to breakfast. On her return from breakfast, staff stayed beside her while walking.",
            "to_breakfast",
            "INDEPENDENT",
        ),
        (
            "She walked independently to breakfast. On her return from breakfast, staff stayed beside her while walking.",
            "from_breakfast",
            "SUPERVISION",
        ),
        (
            "She walked to breakfast and nobody helped her. An aide would have held her arm if needed.",
            "to_breakfast",
            "INDEPENDENT",
        ),
        (
            "She walked independently to breakfast. Later she walked to breakfast with hands-on support.",
            "to_breakfast",
            "UNCLEAR",
        ),
        (
            "She walked down the hallway while staff stayed beside her for safety.",
            "hallway_walk",
            "SUPERVISION",
        ),
        ("She walked unaided in the garden.", "garden_walk", "INDEPENDENT"),
    ],
)
def test_phrase_matcher_scopes_human_help_to_event(body, context, expected):
    result = PhraseMatcher().extract(body, target(context), "revision-1")
    assert result.label.value == expected
    assert_source(result, body)


def test_phrase_preserves_whitespace_between_adjacent_sentences():
    body = "She tried walking to the lounge this morning.\n  An aide held her arm while she took steps."
    result = PhraseMatcher().extract(body, target("walking_attempt"), "revision-1")
    assert result.label == AssistanceLevel.HANDS_ON
    assert result.evidence[0].quote == body
    assert_source(result, body)


def test_phrase_does_not_ignore_conflicting_target_cue():
    result = PhraseMatcher().extract(
        DEMO_NOTE, target(target_cue="return walk in the afternoon"), "revision-1"
    )
    assert result.label == AssistanceLevel.UNCLEAR


class FakeResponses:
    def __init__(self, prediction=None, error=None):
        self.prediction = prediction
        self.error = error
        self.kwargs = None

    def parse(self, **kwargs):
        self.kwargs = kwargs
        if self.error:
            raise self.error
        return SimpleNamespace(output_parsed=self.prediction)


def adapter(prediction=None, error=None):
    responses = FakeResponses(prediction, error)
    return OpenAIExtractor(
        "test-compatible-model", client=SimpleNamespace(responses=responses)
    ), responses


def prediction(**kwargs):
    result = dict(
        label="SUPERVISION",
        reason_code="HUMAN_SUPERVISION",
        reason="An aide stayed beside her.",
        quotes=["This morning she needed an aide beside her on the way to breakfast."],
        device=None,
    )
    result.update(kwargs)
    return result


def test_live_adapter_structures_full_note_and_target_then_resolves_exact_quote():
    extractor, responses = adapter(prediction())
    result = extractor.extract(DEMO_NOTE, target(), "revision-1")
    assert result.label == AssistanceLevel.SUPERVISION
    assert_source(result, DEMO_NOTE)
    assert responses.kwargs["model"] == "test-compatible-model"
    assert responses.kwargs["text_format"].__name__ == "_StructuredPrediction"
    import json

    payload = json.loads(responses.kwargs["input"][1]["content"])
    assert payload["note"] == DEMO_NOTE
    assert payload["target"]["context_key"] == "to_breakfast"


@pytest.mark.parametrize(
    "output",
    [
        None,
        prediction(quotes=["The aide held her arm."]),
        prediction(quotes=[]),
        prediction(label="NOT_A_LABEL"),
        prediction(quotes=["She walked."], label="HANDS_ON"),
    ],
)
def test_live_adapter_rejects_refusal_malformed_and_fabricated_evidence(output):
    extractor, _ = adapter(output)
    with pytest.raises(InvalidExtraction):
        extractor.extract(DEMO_NOTE, target(), "revision-1")


def test_live_adapter_rejects_ambiguous_quote():
    extractor, _ = adapter(
        prediction(quotes=["She walked independently to breakfast."], label="INDEPENDENT")
    )
    with pytest.raises(InvalidExtraction):
        extractor.extract(
            "She walked independently to breakfast. She walked independently to breakfast.",
            target(),
            "revision-1",
        )


def test_provider_failure_exposes_only_safe_category():
    timeout = type("APITimeoutError", (Exception,), {})
    extractor, _ = adapter(error=timeout("SECRET key and note contents"))
    with pytest.raises(ExtractionUnavailable) as error:
        extractor.extract(DEMO_NOTE, target(), "revision-1")
    assert error.value.category == "timeout"
    assert str(error.value) == "timeout"
    assert "SECRET" not in str(error.value)


def test_missing_live_credentials_is_unavailable_not_unclear(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ExtractionUnavailable, match="missing_credentials"):
        OpenAIExtractor().extract(DEMO_NOTE, target(), "revision-1")


def test_public_development_fixture_preserves_adjacent_exact_span_and_provenance():
    import json
    from pathlib import Path

    source = json.loads(
        (Path(__file__).resolve().parents[1] / "data" / "fruta_nn_1093.json").read_text()
    )
    selected = Target.model_validate(source["target"])
    result = FixtureExtractor().extract(source["note"], selected, "revision-1")
    assert result.label == AssistanceLevel.HANDS_ON
    assert result.reason_code == "FRUTA_DEVELOPMENT_FIXTURE"
    assert result.evidence[0].quote == source["note"]
    assert_source(result, source["note"])
    assert "fixture" in result.reason
    for changes in (
        {"resident_name": "Elena"},
        {"observed_on": DEMO_DATE},
        {"target_cue": None},
        {"context_key": "to_breakfast"},
    ):
        unsupported = FixtureExtractor().extract(
            source["note"], selected.model_copy(update=changes), "revision-1"
        )
        assert unsupported.reason_code == "FIXTURE_INPUT_UNSUPPORTED"


@pytest.mark.parametrize(
    "body",
    [
        "She did not walk independently to breakfast.",
        "She walked to breakfast but was not independent.",
        "She walked to breakfast with no supervision.",
        "She walked to breakfast without hands-on help.",
    ],
)
def test_phrase_matcher_does_not_count_negated_assistance_phrases(body):
    result = PhraseMatcher().extract(body, target(), "revision-1")
    assert result.label == AssistanceLevel.UNCLEAR


@pytest.mark.parametrize(
    "body,expected",
    [
        ("On 2026-01-14 she walked independently to breakfast.", "UNCLEAR"),
        ("On 2026-01-15 she walked independently to breakfast.", "INDEPENDENT"),
        ("On 2026-01-15 she tried walking. On 2026-01-14 an aide held her arm.", "UNCLEAR"),
        ("On 2026-01-15 she tried walking. On 2026-01-15 an aide held her arm.", "HANDS_ON"),
    ],
)
def test_phrase_matcher_does_not_borrow_help_from_another_explicit_date(body, expected):
    selected = target("walking_attempt") if "tried walking" in body else target()
    result = PhraseMatcher().extract(body, selected, "revision-1")
    assert result.label.value == expected
    assert_source(result, body)


@pytest.mark.parametrize(
    "body,expected",
    [
        ("She walked to breakfast with staff beside her.", "UNCLEAR"),
        ("She walked to breakfast with an aide beside her.", "UNCLEAR"),
        ("She walked to breakfast with staff beside her for safety.", "SUPERVISION"),
        ("She needed an aide beside her on the way to breakfast.", "SUPERVISION"),
    ],
)
def test_phrase_matcher_requires_more_than_mere_staff_presence(body, expected):
    result = PhraseMatcher().extract(body, target(), "revision-1")
    assert result.label.value == expected
    assert_source(result, body)
