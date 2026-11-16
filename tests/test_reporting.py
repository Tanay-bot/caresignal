from __future__ import annotations

import copy
import json

import pytest

from caresignal.reporting import main, write_evaluation_report


def example(identifier, gold, predicted, *, status="COMPLETE", evidence_correct=True):
    note = "She walked to breakfast with help."
    evidence = [{"start": 0, "end": len(note), "quote": note}]
    label_correct = status == "COMPLETE" and gold == predicted
    evidence_correct = status == "COMPLETE" and evidence_correct
    return {
        "example_id": identifier,
        "source_note_id": f"original-{identifier}",
        "source_url": "https://example.org/synthetic-records",
        "status": status,
        "error_category": "timeout"
        if status == "UNAVAILABLE"
        else "invalid_output"
        if status == "INVALID"
        else None,
        "reason_code": "test-reason",
        "note": note,
        "original_note": "Originele synthetische notitie.",
        "target": {
            "resident_id": "fictional-1",
            "resident_name": "Elena",
            "context_key": "to_breakfast",
            "observed_on": "2026-01-15",
            "target_cue": "outbound walk",
        },
        "gold_label": gold,
        "predicted_label": predicted,
        "gold_evidence": evidence,
        "predicted_evidence": evidence if evidence_correct else [],
        "label_correct": label_correct,
        "evidence_correct": evidence_correct,
        "joint_correct": label_correct and evidence_correct,
    }


def method(rows=None, *, mode="gemini", model="recorded-model", dataset_hash="a" * 64):
    if rows is None:
        rows = [example("success", "HANDS_ON", "HANDS_ON")]
    total = len(rows)
    summary = {
        "total": total,
        "completed": sum(row["status"] == "COMPLETE" for row in rows),
        "errors": sum(row["status"] != "COMPLETE" for row in rows),
        "label_correct": sum(row["label_correct"] for row in rows),
        "evidence_correct": sum(row["evidence_correct"] for row in rows),
        "joint_correct": sum(row["joint_correct"] for row in rows),
    }
    summary.update(
        {
            f"{name}_accuracy": summary[f"{name}_correct"] / total
            for name in ["label", "evidence", "joint"]
        }
    )
    return {
        "schema_version": "1.0",
        "scope": "held_out_public",
        "dataset": {
            "sha256": dataset_hash,
            "ids": ["ekrombouts/fruta_records"],
            "revisions": ["frozen-dataset-revision"],
            "translation_ids": ["frozen-translation-v1"],
            "splits": {"held_out": total},
        },
        "extractor": {
            "mode": mode,
            "version": f"{mode}-test-v1",
            "model_id": model,
            "prompt_version": "frozen-prompt-v1",
        },
        "summary": summary,
        "metrics_policy": "Exact span-set match; all examples including errors remain in denominator.",
        "examples": rows,
    }


def test_report_exact_counts_confusion_and_every_recorded_error(tmp_path):
    rows = [
        example("correct", "INDEPENDENT", "INDEPENDENT"),
        example("label-only", "HANDS_ON", "SUPERVISION"),
        example("span-only", "SUPERVISION", "SUPERVISION", evidence_correct=False),
        example("both", "HELP_UNSPECIFIED", "UNCLEAR", evidence_correct=False),
        example("provider", "UNCLEAR", None, status="UNAVAILABLE"),
        example("invalid", "HANDS_ON", None, status="INVALID"),
    ]
    saved = method(rows)
    original = copy.deepcopy(saved)
    output = write_evaluation_report(saved, tmp_path / "report.md")
    text = output.read_text()
    assert saved == original  # Reporting cannot rewrite saved predictions or flags.
    assert "| 6 | 4 | 1 | 1 | 2 | 5 |" in text
    assert "| Label agreement | 2/6 |" in text
    assert "| Exact evidence span-set agreement | 2/6 |" in text
    assert "| Joint agreement | 1/6 |" in text
    assert "| No completed prediction | 0 | 2 |" in text
    assert "| HANDS_ON | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 2 |" in text
    assert "| Total | 1 | 2 | 0 | 0 | 1 | 1 | 1 | 6 |" in text
    for identifier in ["label-only", "span-only", "both", "provider", "invalid"]:
        assert f'"source_note_id": "original-{identifier}"' in text
    assert "#### correct:" not in text
    assert "#### span-only: Strict evidence span mismatch" in text
    assert "#### label-only: Label mismatch" in text
    assert "#### both: Label and strict evidence mismatch" in text
    assert "#### provider: Provider unavailable" in text
    assert "#### invalid: Invalid extraction output" in text
    assert '"context_key": "to_breakfast"' in text
    assert '"expected_label": "HANDS_ON"' in text
    assert '"predicted_label": "SUPERVISION"' in text
    assert "Expected exact evidence:" in text and "Predicted exact evidence:" in text
    assert '"quote": "She walked to breakfast with help."' in text
    assert "Original-language note:" in text
    assert "not a completed label prediction" in text
    assert "does not judge an alternative span semantically" in text


def test_zero_error_report_does_not_invent_error_or_annotation_method(tmp_path):
    text = write_evaluation_report(method(), tmp_path / "zero.md").read_text()
    assert "| 1 | 1 | 0 | 0 | 0 | 0 |" in text
    assert "No incorrect examples or analysis failures were recorded" in text
    assert "####" not in text
    assert "stratified" not in text
    assert "human-reviewed" not in text
    assert "agent-reviewed" not in text
    assert "synthetic or fictional documentation" in text
    assert "does not establish clinical validity" in text


def test_multiple_methods_preserve_each_exact_metadata_snapshot(tmp_path):
    saved = {"schema_version": "1.0", "methods": [method(mode="phrase", model=None), method()]}
    text = write_evaluation_report(
        saved,
        tmp_path / "nested/report.md",
        heading="Small frozen sample",
        methods_note="A small stratified sample with coding-agent-reviewed annotations; not human gold.",
    ).read_text()
    assert text.startswith("# Small frozen sample\n")
    assert (
        "A small stratified sample with coding-agent-reviewed annotations; not human gold." in text
    )
    assert "## Method 1: phrase / no model" in text
    assert "## Method 2: gemini / recorded-model" in text
    for value in [
        "a" * 64,
        "frozen-dataset-revision",
        "frozen-translation-v1",
        "frozen-prompt-v1",
        "gemini-test-v1",
        "phrase-test-v1",
    ]:
        assert value in text
    assert text.count("No inference was rerun") == 1
    assert "do not estimate held-out Fruta performance" not in text


def test_development_scope_cannot_be_presented_as_held_out(tmp_path):
    saved = method()
    saved["scope"] = "public_development"
    text = write_evaluation_report(saved, tmp_path / "dev.md").read_text()
    assert "Development or mixed-scope results describe those examples only" in text
    assert "do not estimate held-out Fruta performance" in text


@pytest.mark.parametrize("field,value", [("total", 99), ("errors", 1), ("label_accuracy", 0.5)])
def test_inconsistent_saved_summary_fails_before_overwriting(tmp_path, field, value):
    saved = method()
    saved["summary"][field] = value
    output = tmp_path / "report.md"
    output.write_text("Preserve the previous report.")
    with pytest.raises(ValueError, match="conflicts"):
        write_evaluation_report(saved, output)
    assert output.read_text() == "Preserve the previous report."


def test_inconsistent_saved_correctness_is_not_silently_repaired(tmp_path):
    saved = method()
    saved["examples"][0]["label_correct"] = False
    with pytest.raises(ValueError, match="joint correctness"):
        write_evaluation_report(saved, tmp_path / "invalid.md")
    assert not (tmp_path / "invalid.md").exists()


@pytest.mark.parametrize("saved", [{"methods": []}, [], {"examples": []}])
def test_empty_or_wrong_schema_rejected(saved, tmp_path):
    with pytest.raises(ValueError):
        write_evaluation_report(saved, tmp_path / "invalid.md")


def test_source_text_with_markdown_fences_remains_quoted(tmp_path):
    saved = method([example("unsafe-note", "HANDS_ON", "SUPERVISION")])
    saved["examples"][0]["note"] = "Source text\n```\n# Embedded heading\n```\nEnd."
    note = saved["examples"][0]["note"]
    span = {"start": 0, "end": len(note), "quote": note}
    saved["examples"][0]["gold_evidence"] = [span]
    saved["examples"][0]["predicted_evidence"] = [span.copy()]
    text = write_evaluation_report(saved, tmp_path / "quoted.md").read_text()
    assert "````text\nSource text\n```\n# Embedded heading\n```\nEnd.\n````" in text


def test_cli_uses_stored_results_without_any_inference(tmp_path, monkeypatch):
    from caresignal import evaluation

    def forbidden(*args, **kwargs):
        raise AssertionError("Report rendering must not run an experiment.")

    monkeypatch.setattr(evaluation, "evaluate_examples", forbidden)
    results = tmp_path / "results.json"
    results.write_text(json.dumps(method()))
    output = tmp_path / "report.md"
    assert (
        main(
            [
                "--results",
                str(results),
                "--output",
                str(output),
                "--heading",
                "Judge review",
                "--methods-note",
                "Annotations reviewed by coding agents; no human gold claim.",
            ]
        )
        == 0
    )
    assert output.read_text().startswith("# Judge review\n")
    assert "Annotations reviewed by coding agents; no human gold claim." in output.read_text()


def test_cli_malformed_results_fails_without_output(tmp_path):
    results = tmp_path / "invalid.json"
    results.write_text("not json")
    output = tmp_path / "report.md"
    with pytest.raises(SystemExit) as exc:
        main(["--results", str(results), "--output", str(output)])
    assert exc.value.code == 2
    assert not output.exists()


def test_different_frozen_inputs_are_not_presented_as_matched_comparison(tmp_path):
    saved = {"methods": [method(dataset_hash="a" * 64), method(dataset_hash="b" * 64)]}
    text = write_evaluation_report(saved, tmp_path / "separate.md").read_text()
    assert "different frozen dataset hashes" in text
    assert "not a matched-input comparison" in text


def test_missing_provenance_fails_cleanly_before_writing(tmp_path):
    saved = method()
    saved["dataset"]["translation_ids"] = [None]
    with pytest.raises(ValueError, match="translation_ids"):
        write_evaluation_report(saved, tmp_path / "incomplete.md")
    assert not (tmp_path / "incomplete.md").exists()


def test_fabricated_perfect_evidence_flag_is_rejected_with_consistent_summary(tmp_path):
    row = example("fabricated-perfect", "HANDS_ON", "HANDS_ON")
    row["predicted_evidence"] = []
    saved = method([row])  # Counts and rates agree with the fabricated flags.
    assert saved["summary"]["joint_accuracy"] == 1
    output = tmp_path / "perfect.md"
    with pytest.raises(ValueError, match="evidence correctness conflicts with exact span sets"):
        write_evaluation_report(saved, output)
    assert not output.exists()


def test_fabricated_incorrect_evidence_flag_is_also_rejected(tmp_path):
    row = example("fabricated-error", "HANDS_ON", "HANDS_ON", evidence_correct=False)
    row["predicted_evidence"] = copy.deepcopy(row["gold_evidence"])
    with pytest.raises(ValueError, match="evidence correctness conflicts with exact span sets"):
        write_evaluation_report(method([row]), tmp_path / "false-error.md")


def test_duplicate_stored_gold_spans_rejected(tmp_path):
    saved = method()
    saved["examples"][0]["gold_evidence"] *= 2
    with pytest.raises(ValueError, match="duplicate spans"):
        write_evaluation_report(saved, tmp_path / "duplicates.md")


@pytest.mark.parametrize("field", ["gold_evidence", "predicted_evidence"])
@pytest.mark.parametrize(
    "span",
    [
        {},
        "not-a-span",
        {"start": -1, "end": 2, "quote": "She"},
        {"start": True, "end": 4, "quote": "She"},
        {"start": 0, "end": 3, "quote": ""},
        {"start": 0, "end": 3, "quote": "wrong-length"},
        {"start": 0, "end": 3, "quote": "Not"},
        {"start": 99, "end": 102, "quote": "She"},
    ],
)
def test_malformed_or_nonmatching_stored_spans_rejected(field, span, tmp_path):
    saved = method()
    saved["examples"][0][field] = [span]
    with pytest.raises(ValueError, match="malformed span|does not match its note"):
        write_evaluation_report(saved, tmp_path / "malformed.md")
    assert not (tmp_path / "malformed.md").exists()


def test_evidence_set_order_is_normalized_without_altering_saved_predictions(tmp_path):
    row = example("reordered", "HANDS_ON", "HANDS_ON")
    row["gold_evidence"] = [
        {"start": 0, "end": 3, "quote": "She"},
        {"start": 4, "end": 10, "quote": "walked"},
    ]
    row["predicted_evidence"] = list(reversed(row["gold_evidence"]))
    saved = method([row])
    original = copy.deepcopy(saved)
    text = write_evaluation_report(saved, tmp_path / "ordered.md").read_text()
    assert "No incorrect examples or analysis failures were recorded" in text
    assert saved == original


def test_span_shape_can_be_checked_when_older_artifact_omits_note(tmp_path):
    saved = method()
    del saved["examples"][0]["note"]
    assert write_evaluation_report(saved, tmp_path / "no-note.md").exists()


def test_real_evaluator_duplicate_prediction_remains_reportable_strict_mismatch(tmp_path):
    from caresignal.evaluation import FrozenExample, evaluate_examples
    from caresignal.models import AssistanceLevel, EvidenceSpan, ExtractionResult

    note = "An aide held her arm while she walked to breakfast."
    frozen = FrozenExample.model_validate(
        {
            "id": "fictional-duplicate-prediction",
            "split": "development",
            "dataset_id": "fictional-report-integration",
            "dataset_revision": "v1",
            "translation_id": "original-en-v1",
            "note": note,
            "target": {
                "resident_id": "fictional-1",
                "resident_name": "Elena",
                "context_key": "to_breakfast",
                "observed_on": "2026-01-15",
                "target_cue": None,
            },
            "gold_label": "HANDS_ON",
            "gold_evidence": [{"quote": note}],
        }
    )

    class RepeatedQuoteExtractor:
        mode = "duplicate-test"
        version = "duplicate-test-v1"
        model_id = None
        prompt_version = "test-v1"

        def extract(self, note_body, target, revision_id):
            span = EvidenceSpan(
                revision_id=revision_id, start=0, end=len(note_body), quote=note_body
            )
            return ExtractionResult(
                label=AssistanceLevel.HANDS_ON,
                reason_code="repeated-quote",
                reason="Test repeated predicted quote.",
                evidence=[span, span.model_copy()],
            )

    report = evaluate_examples([frozen], RepeatedQuoteExtractor())
    assert report["examples"][0]["status"] == "COMPLETE"
    assert report["examples"][0]["label_correct"]
    assert not report["examples"][0]["evidence_correct"]
    original = copy.deepcopy(report)
    text = write_evaluation_report(report, tmp_path / "repeated-prediction.md").read_text()
    assert "Strict evidence span mismatch" in text
    assert "| Label agreement | 1/1 |" in text
    assert "| Exact evidence span-set agreement | 0/1 |" in text
    assert "| Joint agreement | 0/1 |" in text
    assert len(report["examples"][0]["predicted_evidence"]) == 2
    assert report == original
