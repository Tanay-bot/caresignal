from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from caresignal.evaluation import (
    FrozenExample,
    dataset_hash,
    evaluate_examples,
    load_dataset,
    main,
    write_results,
)
from caresignal.models import AssistanceLevel, EvidenceSpan, ExtractionResult

NOTE = "She walked to breakfast independently."


def record(**changes):
    value = {
        "id": "fictional-test-1",
        "split": "development",
        "dataset_id": "fictional-test",
        "dataset_revision": "v1",
        "translation_id": "original-en-v1",
        "note": NOTE,
        "target": {
            "resident_id": "fictional-1",
            "resident_name": "Elena",
            "context_key": "to_breakfast",
            "observed_on": "2026-01-15",
            "target_cue": None,
        },
        "gold_label": "INDEPENDENT",
        "gold_evidence": [{"quote": NOTE}],
    }
    return value | changes


class CorrectExtractor:
    mode = "test"
    version = "test-v1"
    model_id = None
    prompt_version = "test-v1"

    def extract(self, note_body, target, revision_id):
        return ExtractionResult(
            label=AssistanceLevel.INDEPENDENT,
            reason_code="explicit",
            reason="Explicit independent walk.",
            evidence=[
                EvidenceSpan(revision_id=revision_id, start=0, end=len(note_body), quote=note_body)
            ],
        )


def test_exact_metrics_and_reproducible_exports(tmp_path):
    example = FrozenExample.model_validate(record())
    report = evaluate_examples([example], CorrectExtractor())
    assert report["summary"]["joint_accuracy"] == 1
    assert report["scope"] == "fictional_development"
    assert report["dataset"]["sha256"] == dataset_hash([example])
    first = write_results(report, tmp_path / "first")
    second = write_results(report, tmp_path / "second")
    for name in first:
        assert first[name].read_bytes() == second[name].read_bytes()
    restored = json.loads(first["json"].read_text())
    assert restored["examples"][0]["predicted_evidence"][0]["quote"] == NOTE
    assert "Development results verify these examples only" in first["markdown"].read_text()
    assert "live inference" not in first["markdown"].read_text()
    assert "dataset_sha256" in first["csv"].read_text()


def test_partial_evidence_is_incorrect_even_with_correct_label():
    class Partial(CorrectExtractor):
        def extract(self, note_body, target, revision_id):
            return ExtractionResult(
                label=AssistanceLevel.INDEPENDENT,
                reason_code="explicit",
                reason="Partial quote.",
                evidence=[EvidenceSpan(revision_id=revision_id, start=0, end=3, quote="She")],
            )

    report = evaluate_examples([FrozenExample.model_validate(record())], Partial())
    assert report["summary"]["label_accuracy"] == 1
    assert report["summary"]["evidence_accuracy"] == 0
    assert report["summary"]["joint_accuracy"] == 0


def test_failure_stays_in_denominator_and_never_leaks_exception():
    class Unavailable(Exception):
        category = "timeout"

    class Broken(CorrectExtractor):
        def extract(self, note_body, target, revision_id):
            raise Unavailable("secret-provider-response")

    report = evaluate_examples([FrozenExample.model_validate(record())], Broken())
    assert report["summary"]["total"] == 1
    assert report["summary"]["errors"] == 1
    assert report["summary"]["joint_accuracy"] == 0
    assert report["examples"][0]["status"] == "UNAVAILABLE"
    assert "secret-provider-response" not in json.dumps(report)


def test_invalid_predicted_offsets_are_counted_as_errors():
    class Invalid(CorrectExtractor):
        def extract(self, note_body, target, revision_id):
            return ExtractionResult(
                label=AssistanceLevel.INDEPENDENT,
                reason_code="explicit",
                reason="Invalid offsets.",
                evidence=[
                    EvidenceSpan(
                        revision_id="wrong-revision", start=0, end=len(note_body), quote=note_body
                    )
                ],
            )

    report = evaluate_examples([FrozenExample.model_validate(record())], Invalid())
    assert report["examples"][0]["status"] == "INVALID"
    assert not report["examples"][0]["label_correct"]


@pytest.mark.parametrize(
    "changes",
    [
        {"gold_evidence": [{"quote": "Invented words"}]},
        {"gold_evidence": [{"quote": NOTE, "start": 1, "end": len(NOTE)}]},
        {"gold_evidence": [{"quote": NOTE, "start": 0, "end": len(NOTE) + 1}]},
        {"gold_evidence": []},
        {"dataset_revision": " "},
    ],
)
def test_invalid_frozen_gold_is_rejected(changes):
    with pytest.raises(ValidationError):
        FrozenExample.model_validate(record(**changes))


def test_held_out_requires_public_provenance_and_rejects_fictional_split():
    with pytest.raises(ValidationError, match="Fictional"):
        FrozenExample.model_validate(record(split="held_out"))
    with pytest.raises(ValidationError, match="source_note_id"):
        FrozenExample.model_validate(record(split="held_out", dataset_id="public-example"))
    example = FrozenExample.model_validate(
        record(
            split="held_out",
            dataset_id="public-example",
            source_note_id="source-1",
            source_url="https://example.org/dataset",
            original_note="Original language text.",
            annotation_id="gold-v1",
        )
    )
    assert evaluate_examples([example], CorrectExtractor())["scope"] == "held_out_public"


def test_duplicate_ids_and_cli_invalid_data_fail(tmp_path):
    path = tmp_path / "frozen.jsonl"
    path.write_text(json.dumps(record()) + "\n" + json.dumps(record()) + "\n")
    with pytest.raises(ValueError, match="Duplicate"):
        load_dataset(path)
    path.write_text(json.dumps(record(gold_evidence=[{"quote": "missing"}])) + "\n")
    with pytest.raises(SystemExit) as exc:
        main(["--dataset", str(path), "--output-dir", str(tmp_path / "out")])
    assert exc.value.code == 2
    assert not (tmp_path / "out").exists()


def test_input_changes_change_frozen_hash():
    first = FrozenExample.model_validate(record())
    second = FrozenExample.model_validate(record(dataset_revision="v2"))
    assert dataset_hash([first]) != dataset_hash([second])


def test_disclosed_public_development_note_cannot_be_relabelled_held_out():
    path = Path(__file__).resolve().parents[1] / "data/fruta_development.jsonl"
    row = json.loads(path.read_text().strip())
    row["split"] = "held_out"
    with pytest.raises(ValidationError, match="disclosed public development"):
        FrozenExample.model_validate(row)
    row["id"] = "renamed-example"
    row["source_note_id"] = "renamed-source"
    with pytest.raises(ValidationError, match="disclosed public development"):
        FrozenExample.model_validate(row)


def test_fixture_answer_lookup_is_rejected_for_held_out_data():
    example = FrozenExample.model_validate(
        record(
            split="held_out",
            dataset_id="public-example",
            source_note_id="source-1",
            source_url="https://example.org/dataset",
            original_note="Original language text.",
            annotation_id="gold-v1",
        )
    )
    fixture = CorrectExtractor()
    fixture.mode = "fixture"
    with pytest.raises(ValueError, match="Fixture answer lookups"):
        evaluate_examples([example], fixture)


def test_mixed_fictional_and_public_development_never_claims_public_only():
    fictional = FrozenExample.model_validate(record())
    public = FrozenExample.model_validate(record(id="public-dev-2", dataset_id="public-example"))
    report = evaluate_examples([fictional, public], CorrectExtractor())
    assert report["scope"] == "mixed_or_development"


def test_cli_fixture_held_out_fails_before_inference(tmp_path):
    row = record(
        split="held_out",
        dataset_id="public-example",
        source_note_id="source-1",
        source_url="https://example.org/dataset",
        original_note="Original language text.",
        annotation_id="gold-v1",
    )
    path = tmp_path / "held-out.jsonl"
    path.write_text(json.dumps(row) + "\n")
    with pytest.raises(SystemExit) as exc:
        main(["--dataset", str(path), "--mode", "fixture", "--output-dir", str(tmp_path / "out")])
    assert exc.value.code == 2
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize("provider", [None, "openai", "gemini"])
@pytest.mark.parametrize("mode", ["live", "compare"])
def test_cli_selects_live_provider_and_preserves_frozen_metadata(
    tmp_path, monkeypatch, provider, mode
):
    from caresignal import extractors

    constructed = []
    calls = []

    def fake_adapter(name):
        class Adapter(CorrectExtractor):
            def __init__(self):
                constructed.append(name)
                self.mode = (
                    "gemini" if name == "gemini" else "live" if name == "openai" else "phrase"
                )
                self.version = f"{name}-mock-v1"
                self.model_id = f"{name}-mock-model" if name != "phrase" else None
                self.prompt_version = "shared-policy-v1"

            def extract(self, note_body, target, revision_id):
                calls.append((name, note_body, target.model_dump(mode="json"), revision_id))
                return super().extract(note_body, target, revision_id)

        return Adapter

    monkeypatch.setattr(extractors, "OpenAIExtractor", fake_adapter("openai"))
    monkeypatch.setattr(extractors, "GeminiExtractor", fake_adapter("gemini"), raising=False)
    monkeypatch.setattr(extractors, "PhraseMatcher", fake_adapter("phrase"))
    path = tmp_path / "frozen.jsonl"
    path.write_text(json.dumps(record()) + "\n")
    output = tmp_path / "results"
    arguments = ["--dataset", str(path), "--mode", mode, "--output-dir", str(output)]
    if provider is not None:
        arguments += ["--provider", provider]
    assert main(arguments) == 0
    selected = provider or "openai"
    assert constructed == (["phrase", selected] if mode == "compare" else [selected])
    report = json.loads((output / "results.json").read_text())
    methods = report["methods"] if mode == "compare" else [report]
    expected_hash = dataset_hash([FrozenExample.model_validate(record())])
    assert {method["dataset"]["sha256"] for method in methods} == {expected_hash}
    assert methods[-1]["extractor"] == {
        "mode": "gemini" if selected == "gemini" else "live",
        "version": f"{selected}-mock-v1",
        "model_id": f"{selected}-mock-model",
        "prompt_version": "shared-policy-v1",
    }
    assert all(method["summary"]["joint_accuracy"] == 1 for method in methods)
    assert all(call[1] == NOTE and call[2] == record()["target"] for call in calls)
    assert len({call[3] for call in calls}) == 1


def test_cli_offline_mode_does_not_construct_a_live_provider(tmp_path, monkeypatch):
    from caresignal import extractors

    def forbidden():
        raise AssertionError("Offline evaluation must not instantiate an API adapter.")

    monkeypatch.setattr(extractors, "OpenAIExtractor", forbidden)
    monkeypatch.setattr(extractors, "GeminiExtractor", forbidden, raising=False)
    monkeypatch.setattr(extractors, "PhraseMatcher", CorrectExtractor)
    path = tmp_path / "frozen.jsonl"
    path.write_text(json.dumps(record()) + "\n")
    assert (
        main(
            [
                "--dataset",
                str(path),
                "--mode",
                "phrase",
                "--provider",
                "gemini",
                "--output-dir",
                str(tmp_path / "out"),
            ]
        )
        == 0
    )
