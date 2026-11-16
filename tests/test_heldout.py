"""Integrity checks for the pre-inference frozen sample and review provenance."""

import hashlib
import json
from collections import Counter
from pathlib import Path

from caresignal.evaluation import dataset_hash, load_dataset
from scripts.select_fruta_sample import COUNTS, select_notes, stratum

ROOT = Path(__file__).resolve().parents[1]


def read_json(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_frozen_hashes_and_original_sources_remain_consistent():
    manifest = read_json("data/fruta_held_out_manifest.json")
    frozen = manifest["frozen_dataset"]
    examples = load_dataset(ROOT / frozen["path"])
    assert len(examples) == frozen["rows"] == 24
    assert dataset_hash(examples) == frozen["canonical_sha256"]
    for path_key, hash_key, section in [
        ("path", "file_sha256", frozen),
        ("annotation_ledger_path", "annotation_ledger_sha256", frozen),
        ("source_records_path", "source_records_sha256", manifest["selection"]),
        ("target_specifications_path", "targets_sha256", manifest["selection"]),
    ]:
        actual = hashlib.sha256((ROOT / section[path_key]).read_bytes()).hexdigest()
        assert actual == section[hash_key]
    assert Counter(e.gold_label.value for e in examples) == frozen["label_counts"]


def test_heldout_sources_targets_and_reference_spans_match_reviewed_records():
    examples = load_dataset(ROOT / "data/fruta_held_out.jsonl")
    sources = [
        json.loads(line)
        for line in (ROOT / "data/fruta_held_out_sources.jsonl").read_text().splitlines()
    ]
    by_id = {row["note_id"]: row for row in sources}
    targets = read_json("data/fruta_held_out_targets.json")
    assert len(by_id) == len({e.note for e in examples}) == 24
    assert "nn_1093" not in by_id
    for example in examples:
        source = by_id[example.id]
        assert example.original_note == source["note"]
        assert example.target.model_dump(mode="json") == targets[example.id]
        assert example.target.observed_on.isoformat() == source["date"][:10]
        assert example.source_note_id == example.id
        assert example.annotation_id == "caresignal-two-agent-adjudicated-v1"
        assert example.translation_id == "caresignal-agent-en-reviewed-v1"


def test_selection_is_reproducible_and_strata_are_source_cues_not_gold_labels():
    sources = [
        json.loads(line)
        for line in (ROOT / "data/fruta_held_out_sources.jsonl").read_text().splitlines()
    ]
    reproduced, _ = select_notes(list(reversed(sources)))
    assert reproduced == sources
    assert Counter(row["selection_stratum"] for row in sources) == COUNTS
    assert all(stratum(row["note"]) == row["selection_stratum"] for row in sources)
    # Physical-cue screening deliberately retains a transfer/device distractor.
    assert (
        next(row for row in sources if row["note_id"] == "na_0145")["selection_stratum"]
        == "physical_cue"
    )


def test_independent_review_disagreement_and_translation_fix_are_preserved():
    ledger = read_json("data/annotations/fruta_held_out_v1.json")
    examples = {e.id: e for e in load_dataset(ROOT / "data/fruta_held_out.jsonl")}
    reviews = {row["note_id"]: row for row in ledger["reviews"]}
    assert set(reviews) == set(examples)
    disagreements = [
        key
        for key, row in reviews.items()
        if row["annotation_a"]["gold_label"] != row["blind_annotation_b"]["label"]
    ]
    assert disagreements == ledger["blind_label_agreement"]["disagreement_ids"] == ["nb_0890"]
    assert examples["nb_0890"].gold_label.value == reviews["nb_0890"]["final_label"] == "UNCLEAR"
    assert "Cooperated well" in examples["nm_0865"].note
    for key, row in reviews.items():
        assert examples[key].gold_label.value == row["final_label"]
        assert [span.model_dump() for span in examples[key].gold_evidence] == row["final_evidence"]
