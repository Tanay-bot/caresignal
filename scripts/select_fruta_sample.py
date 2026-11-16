"""Reproduce the pre-inference, stratified selection of 24 synthetic Fruta notes.

This selects source records only. Translation, target selection and assistance
annotations are separately reviewed and frozen before extraction is evaluated.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.request
from collections import defaultdict
from pathlib import Path

import pyarrow.parquet as pq

REVISION = "579141e3431c18a932fa3a0870e9f1c131f10367"
SOURCE_SHA256 = "205ae14313c65f57c03cc15a0fa16ac33aa827c5c242bfbc1215db621aac1c4f"
SOURCE_URL = (
    "https://huggingface.co/datasets/ekrombouts/fruta_records/resolve/"
    f"{REVISION}/data/train-00000-of-00001.parquet"
)
SEED = "caresignal-fruta-heldout-v1-20261115"
COUNTS = {
    "physical_cue": 6,
    "independence_cue": 4,
    "guidance_cue": 6,
    "other_walk": 4,
    "device_transfer_control": 4,
}
WALK = re.compile(r"\b(?:lopen|loopt|liep|loop|wandelen|wandeling|gewandeld)\b", re.I)
PHYSICAL = re.compile(
    r"fysiek|(?:arm|hand).{0,35}(?:vast|steun)|(?:vast|steun).{0,35}(?:arm|hand)|ondersteun|\bsteun\b",
    re.I,
)
INDEPENDENT = re.compile(
    r"zelfstandig|zonder hulp|zonder ondersteuning|alleen gelopen|zelf lopen", re.I
)
GUIDANCE = re.compile(
    r"begele|toezicht|supervis|in de gaten|veiligheid|valrisico|valpreventie|herinner|aanwijzin",
    re.I,
)
CONTROL = re.compile(r"rollator|looprek|wandelstok|rolstoel|transfer", re.I)
DEVELOPMENT_HASH = "3a38084484b4f8af683d8b5c97bd15a259225be9d7948d6b12ab94bd75f41a0d"


def stratum(text: str) -> str | None:
    if WALK.search(text):
        if PHYSICAL.search(text):
            return "physical_cue"
        if INDEPENDENT.search(text):
            return "independence_cue"
        if GUIDANCE.search(text):
            return "guidance_cue"
        return "other_walk"
    return "device_transfer_control" if CONTROL.search(text) else None


def select_notes(rows: list[dict]) -> tuple[list[dict], dict[str, int]]:
    buckets = defaultdict(list)
    for row in rows:
        fingerprint = hashlib.sha256(row["note"].encode("utf-8")).hexdigest()
        if row["note_id"] == "nn_1093" or fingerprint == DEVELOPMENT_HASH:
            continue
        bucket = stratum(row["note"])
        if bucket:
            buckets[bucket].append(row)
    selected = []
    for bucket, count in COUNTS.items():
        ranked = sorted(
            buckets[bucket],
            key=lambda row: hashlib.sha256(f"{SEED}:{row['note_id']}".encode()).hexdigest(),
        )
        if len(ranked) < count:
            raise ValueError(f"Not enough records in stratum {bucket}")
        selected.extend({"selection_stratum": bucket, **row} for row in ranked[:count])
    if len({row["note_id"] for row in selected}) != sum(COUNTS.values()):
        raise ValueError("Selected note IDs must be unique")
    if len({row["note"] for row in selected}) != len(selected):
        raise ValueError("Selected notes contain duplicate text; review the selection protocol")
    return selected, {bucket: len(buckets[bucket]) for bucket in COUNTS}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("artifacts/fruta-source.parquet"))
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.download and not args.source.exists():
        args.source.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(SOURCE_URL, args.source)
    actual_hash = hashlib.sha256(args.source.read_bytes()).hexdigest()
    if actual_hash != SOURCE_SHA256:
        raise ValueError("The source file does not match the pinned Fruta Parquet SHA-256")
    selected, counts = select_notes(pq.read_table(args.source).to_pylist())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in selected),
        encoding="utf-8",
    )
    print(json.dumps({"pool_sizes": counts, "selected": len(selected), "seed": SEED}))


if __name__ == "__main__":
    main()
