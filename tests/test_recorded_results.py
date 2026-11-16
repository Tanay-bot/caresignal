"""Recorded experiments remain tied to frozen sources and actual retry rows."""

import hashlib
import json
from pathlib import Path

from caresignal.evaluation import dataset_hash, load_dataset

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_first_pass_and_replay_use_identical_frozen_notes_targets_and_gold():
    frozen = {e.id: e for e in load_dataset(ROOT / "data/fruta_held_out.jsonl")}
    canonical_hash = dataset_hash(list(frozen.values()))
    for path in ("docs/heldout-results/results.json", "docs/heldout-followup/results.json"):
        report = read(path)
        for method in report["methods"]:
            assert method["dataset"]["sha256"] == canonical_hash
            assert len(method["examples"]) == len(frozen) == method["summary"]["total"]
            assert {row["example_id"] for row in method["examples"]} == set(frozen)
            for row in method["examples"]:
                example = frozen[row["example_id"]]
                assert row["note"] == example.note
                assert row["original_note"] == example.original_note
                assert row["target"] == example.target.model_dump(mode="json")
                assert row["gold_label"] == example.gold_label.value
                assert row["gold_evidence"] == [span.model_dump() for span in example.gold_evidence]


def test_error_informed_prompt_is_marked_post_hoc_and_first_pass_is_preserved():
    first = read("docs/heldout-results/results.json")
    replay = read("docs/heldout-followup/results.json")
    assert (
        first["freeze_commit"]
        == replay["freeze_commit"]
        == "b28451c45fe6a4814855a816f50e310b269f4b8e"
    )
    original = next(m for m in first["methods"] if m["extractor"]["mode"] == "gemini")
    current = next(m for m in replay["methods"] if m["extractor"]["mode"] == "gemini")
    assert original["extractor"]["prompt_version"] == "walking-assistance-v1"
    assert original["scope"] == "held_out_public"
    assert current["extractor"]["prompt_version"] == "walking-assistance-v2"
    assert all(m["scope"] == "post_hoc_replay" for m in replay["methods"])
    assert all(m["scope_note"] for m in replay["methods"])


def test_retries_replace_only_unavailable_rows_and_keep_all_actual_attempts():
    final = read("docs/heldout-followup/results.json")
    policy = final["retry_policy"]
    original_path = ROOT / policy["first_attempt_results_path"]
    assert (
        hashlib.sha256(original_path.read_bytes()).hexdigest()
        == policy["first_attempt_results_sha256"]
    )
    retry_path = ROOT / policy["retry_results_path"]
    assert hashlib.sha256(retry_path.read_bytes()).hexdigest() == policy["retry_results_sha256"]
    original = json.loads(original_path.read_text())
    retry = json.loads(retry_path.read_text())
    ledger = read(policy["attempt_history_path"])
    initial_method = next(m for m in original["methods"] if m["extractor"]["mode"] == "gemini")
    final_method = next(m for m in final["methods"] if m["extractor"]["mode"] == "gemini")
    first_rows = {row["example_id"]: row for row in initial_method["examples"]}
    retry_rows = {row["example_id"]: row for row in retry["examples"]}
    assert policy["additional_attempt_count"] == len(retry_rows) == 6
    assert set(retry_rows) == {
        row["example_id"] for row in initial_method["examples"] if row["status"] == "UNAVAILABLE"
    }
    for row in final_method["examples"]:
        assert row == retry_rows.get(row["example_id"], first_rows[row["example_id"]])
    for item in ledger["retried_examples"]:
        assert item["attempts"] == [first_rows[item["example_id"]], retry_rows[item["example_id"]]]
    assert len(final_method["examples"]) == policy["final_metric_denominator"] == 24


def test_stopped_provider_attempt_does_not_invent_unattempted_predictions():
    stopped = read("docs/heldout-results/initial-provider-failures.json")
    assert stopped["completed_attempts"] == len(stopped["attempts"]) == 14
    assert stopped["successful_predictions"] == 0
    assert all(row["status"] == "UNAVAILABLE" for row in stopped["attempts"])
    attempted = {row["example_id"] for row in stopped["attempts"]}
    assert stopped["interrupted_example_id"] not in attempted
    assert attempted.isdisjoint(stopped["unattempted_example_ids"])
    assert (
        len(attempted) + len(stopped["unattempted_example_ids"]) + 1 == stopped["planned_examples"]
    )
