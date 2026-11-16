"""Frozen, exact-evidence extraction evaluation shared by CLI and notebooks.

Fictional development checks are workflow checks. They never stand in for a
held-out public experiment, and provider failures remain in the denominator.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import time
from pathlib import Path
from typing import Any, Callable, Literal, Protocol, Sequence

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .evidence import validate_evidence
from .models import AssistanceLevel, ExtractionResult, Target

# Disclosed development examples can never become held-out by changing a split.
# The original/translation fingerprints also catch relabelled source identifiers.
_KNOWN_DEVELOPMENT_IDS = frozenset({"nn_1093"})
_KNOWN_DEVELOPMENT_TEXT_HASHES = frozenset(
    {
        "3a38084484b4f8af683d8b5c97bd15a259225be9d7948d6b12ab94bd75f41a0d",
        "2562a37612a79e1672a3106140d1b681dc6d3d73698c4e102850b058a843ab35",
    }
)


class EvaluatedExtractor(Protocol):
    mode: str
    version: str
    model_id: str | None
    prompt_version: str

    def extract(self, note_body: str, target: Target, revision_id: str) -> ExtractionResult: ...


def _validated_request_interval(value: float) -> float:
    interval = float(value)
    if not math.isfinite(interval) or not 0 <= interval <= 60:
        raise ValueError("Request interval must be a finite number from 0 to 60 seconds.")
    return interval


def _parse_request_interval(value: str) -> float:
    try:
        return _validated_request_interval(float(value))
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


class PacedExtractor:
    """Space serial live request starts while preserving the provider contract.

    Offline modes and an interval of zero never read the clock or sleep.
    Provider exceptions propagate unchanged, and failed attempts still establish
    the next request's earliest start time. This wrapper adds no retries.
    """

    def __init__(
        self,
        extractor: EvaluatedExtractor,
        min_request_interval: float = 0,
        *,
        clock: Callable[[], float] | None = None,
        sleep: Callable[[float], None] | None = None,
    ) -> None:
        self.min_request_interval = _validated_request_interval(min_request_interval)
        self._extractor = extractor
        self._extract_method = extractor.extract
        self._clock = clock if clock is not None else time.monotonic
        self._sleep = sleep if sleep is not None else time.sleep
        self._last_started_at: float | None = None
        self._live = extractor.mode in {"live", "gemini"}

    @property
    def mode(self) -> str:
        return self._extractor.mode

    @property
    def version(self) -> str:
        return self._extractor.version

    @property
    def model_id(self) -> str | None:
        return self._extractor.model_id

    @property
    def prompt_version(self) -> str:
        return self._extractor.prompt_version

    def extract(self, note_body: str, target: Target, revision_id: str) -> ExtractionResult:
        if self._live and self.min_request_interval > 0:
            started_at = self._clock()
            if self._last_started_at is not None:
                remaining = self._last_started_at + self.min_request_interval - started_at
                if remaining > 0:
                    self._sleep(remaining)
                    started_at = self._clock()
            self._last_started_at = started_at
        return self._extract_method(note_body, target, revision_id)


class GoldEvidence(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    quote: str = Field(min_length=1)
    start: int | None = Field(default=None, ge=0)
    end: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def complete_offsets(self) -> "GoldEvidence":
        if (self.start is None) != (self.end is None):
            raise ValueError("Gold evidence must supply both start and end or neither.")
        if self.start is not None and self.end <= self.start:
            raise ValueError("Gold evidence must be a nonempty half-open span.")
        return self


class FrozenExample(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    id: str = Field(min_length=1)
    split: Literal["development", "held_out"]
    dataset_id: str = Field(min_length=1)
    dataset_revision: str = Field(min_length=1)
    translation_id: str = Field(min_length=1)
    note: str = Field(min_length=1)
    target: Target
    gold_label: AssistanceLevel
    gold_evidence: list[GoldEvidence]
    source_note_id: str | None = None
    source_url: str | None = None
    original_note: str | None = None
    annotation_id: str | None = None

    @model_validator(mode="after")
    def exact_gold_and_provenance(self) -> "FrozenExample":
        for name in ("id", "dataset_id", "dataset_revision", "translation_id", "note"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} cannot be blank.")
        if self.gold_label != AssistanceLevel.UNCLEAR and not self.gold_evidence:
            raise ValueError("A supported gold assistance label requires exact evidence.")
        spans = _gold_spans(self)
        if len(set(spans)) != len(spans):
            raise ValueError("Duplicate gold spans are not permitted.")
        # Held-out publication requires traceable original text, its public URL,
        # frozen version/translation, and a stable gold-annotation identifier.
        if self.split == "held_out":
            identifiers = {self.id, self.source_note_id}
            fingerprints = {
                hashlib.sha256(text.encode("utf-8")).hexdigest()
                for text in (self.note, self.original_note)
                if text
            }
            if (
                identifiers & _KNOWN_DEVELOPMENT_IDS
                or fingerprints & _KNOWN_DEVELOPMENT_TEXT_HASHES
            ):
                raise ValueError("A disclosed public development example cannot be held-out data.")
            if self.dataset_id.lower().startswith("fictional"):
                raise ValueError("Fictional walkthrough data must stay in the development split.")
            for name in ("source_note_id", "source_url", "original_note", "annotation_id"):
                value = getattr(self, name)
                if not value or not value.strip():
                    raise ValueError(f"Held-out data requires {name} provenance.")
            if not self.source_url.startswith(("https://", "http://")):
                raise ValueError("Held-out source_url must be a public HTTP(S) source.")
        return self


def _gold_spans(example: FrozenExample) -> list[tuple[int, int, str]]:
    spans = []
    for item in example.gold_evidence:
        if item.start is None:
            start = example.note.find(item.quote)
            if start < 0 or example.note.find(item.quote, start + 1) >= 0:
                raise ValueError("A gold quote must occur exactly once, or supply exact offsets.")
            end = start + len(item.quote)
        else:
            start, end = item.start, item.end
        if not (0 <= start < end <= len(example.note)) or example.note[start:end] != item.quote:
            raise ValueError("Gold evidence offsets do not match the original note text.")
        spans.append((start, end, item.quote))
    return sorted(spans)


def load_dataset(path: str | Path) -> list[FrozenExample]:
    """Load a frozen JSONL file; reject malformed gold, duplicate IDs and emptiness."""
    examples: list[FrozenExample] = []
    seen = set()
    with Path(path).open(encoding="utf-8") as source:
        for line_no, line in enumerate(source, 1):
            if not line.strip():
                continue
            try:
                example = FrozenExample.model_validate_json(line)
            except ValueError as exc:
                raise ValueError(f"Invalid dataset row {line_no}: {exc}") from exc
            if example.id in seen:
                raise ValueError(f"Duplicate example ID at row {line_no}: {example.id}")
            seen.add(example.id)
            examples.append(example)
    if not examples:
        raise ValueError("The frozen dataset is empty.")
    return examples


def dataset_hash(examples: Sequence[FrozenExample]) -> str:
    canonical = json.dumps(
        [example.model_dump(mode="json") for example in examples],
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def evaluate_examples(
    examples: Sequence[FrozenExample], extractor: EvaluatedExtractor, *, post_hoc: bool = False
) -> dict[str, Any]:
    """Score label, exact evidence, and their intersection on identical inputs.

    Correct evidence means the sorted complete set of half-open spans equals the
    frozen gold set. Partial overlaps and semantically similar paraphrases fail.
    Every input, including provider errors and invalid evidence, is counted.
    """
    if not examples:
        raise ValueError("Evaluation requires at least one frozen example.")
    if extractor.mode == "fixture" and any(e.split == "held_out" for e in examples):
        raise ValueError("Fixture answer lookups cannot be evaluated as held-out extraction.")
    examples = [FrozenExample.model_validate(e.model_dump()) for e in examples]
    if len({e.id for e in examples}) != len(examples):
        raise ValueError("Evaluation example IDs must be unique.")
    rows: list[dict[str, Any]] = []
    for example in examples:
        revision_id = f"eval:{example.id}"
        row: dict[str, Any] = {
            "example_id": example.id,
            "split": example.split,
            "dataset_id": example.dataset_id,
            "dataset_revision": example.dataset_revision,
            "translation_id": example.translation_id,
            "source_note_id": example.source_note_id,
            "source_url": example.source_url,
            "original_note": example.original_note,
            "annotation_id": example.annotation_id,
            "note": example.note,
            "target": example.target.model_dump(mode="json"),
            "gold_label": example.gold_label.value,
            "gold_evidence": [dict(start=s, end=e, quote=q) for s, e, q in _gold_spans(example)],
            "status": "COMPLETE",
            "predicted_label": None,
            "predicted_evidence": [],
            "reason_code": None,
            "error_category": None,
            "label_correct": False,
            "evidence_correct": False,
            "joint_correct": False,
        }
        try:
            result = extractor.extract(example.note, example.target, revision_id)
            validate_evidence(example.note, revision_id, result)
            predicted = sorted((span.start, span.end, span.quote) for span in result.evidence)
            row.update(
                predicted_label=result.label.value,
                predicted_evidence=[dict(start=s, end=e, quote=q) for s, e, q in predicted],
                reason_code=result.reason_code,
                label_correct=result.label == example.gold_label,
                evidence_correct=predicted == _gold_spans(example),
            )
            row["joint_correct"] = row["label_correct"] and row["evidence_correct"]
        except Exception as exc:
            # Keep private provider response bodies, keys and input echoes out of
            # reports. Public note/target content above is intentionally frozen.
            category = getattr(exc, "category", None)
            row["status"] = "UNAVAILABLE" if category else "INVALID"
            row["error_category"] = (
                category
                if category
                in {
                    "missing_credentials",
                    "timeout",
                    "authentication",
                    "rate_limit",
                    "connection",
                    "connection_error",
                    "permission_denied",
                    "incompatible_model",
                    "provider_error",
                    "refusal",
                    "incomplete_response",
                }
                else "invalid_output"
                if not category
                else "provider_error"
            )
        rows.append(row)
    count = len(rows)
    summary = {
        "total": count,
        "completed": sum(row["status"] == "COMPLETE" for row in rows),
        "errors": sum(row["status"] != "COMPLETE" for row in rows),
        "label_correct": sum(row["label_correct"] for row in rows),
        "evidence_correct": sum(row["evidence_correct"] for row in rows),
        "joint_correct": sum(row["joint_correct"] for row in rows),
    }
    summary.update(
        {
            "label_accuracy": summary["label_correct"] / count,
            "evidence_accuracy": summary["evidence_correct"] / count,
            "joint_accuracy": summary["joint_correct"] / count,
        }
    )
    report = {
        "schema_version": "1.0",
        "scope": "held_out_public"
        if all(e.split == "held_out" for e in examples)
        else "fictional_development"
        if all(e.dataset_id.lower().startswith("fictional") for e in examples)
        else "public_development"
        if all(
            e.split == "development" and not e.dataset_id.lower().startswith("fictional")
            for e in examples
        )
        else "mixed_or_development",
        "dataset": {
            "sha256": dataset_hash(examples),
            "ids": sorted({e.dataset_id for e in examples}),
            "revisions": sorted({e.dataset_revision for e in examples}),
            "translation_ids": sorted({e.translation_id for e in examples}),
            "splits": {
                split: sum(e.split == split for e in examples)
                for split in sorted({e.split for e in examples})
            },
        },
        "extractor": {
            "mode": extractor.mode,
            "version": extractor.version,
            "model_id": extractor.model_id,
            "prompt_version": extractor.prompt_version,
        },
        "metrics_policy": "Exact span-set match; all examples including errors remain in denominator.",
        "summary": summary,
        "examples": rows,
    }
    if post_hoc:
        report["scope"] = "post_hoc_replay"
        report["scope_note"] = (
            "Post-hoc replay on previously evaluated frozen examples. "
            "These descriptive results are not a new held-out performance estimate."
        )
    return report


def _method_reports(report: dict[str, Any]) -> list[dict[str, Any]]:
    return report["methods"] if "methods" in report else [report]


def summary_markdown(report: dict[str, Any]) -> str:
    reports = _method_reports(report)
    output = [
        "| Mode | Model | Scope | N | Label | Exact evidence | Joint | Errors |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for method in reports:
        meta, summary = method["extractor"], method["summary"]
        output.append(
            f"| {meta['mode']} | {meta['model_id'] or 'none'} | {method['scope']} | {summary['total']} "
            f"| {summary['label_correct']}/{summary['total']} ({summary['label_accuracy']:.1%}) "
            f"| {summary['evidence_correct']}/{summary['total']} ({summary['evidence_accuracy']:.1%}) "
            f"| {summary['joint_correct']}/{summary['total']} ({summary['joint_accuracy']:.1%}) "
            f"| {summary['errors']} |"
        )
    if any(method["scope"] == "post_hoc_replay" for method in reports):
        output += [
            "",
            "Post-hoc replay on previously evaluated examples. These results are not a new held-out performance estimate.",
        ]
    elif any(method["scope"] != "held_out_public" for method in reports):
        output += [
            "",
            "Development results verify these examples only. They do not estimate held-out Fruta performance.",
        ]
    return "\n".join(output) + "\n"


def write_results(report: dict[str, Any], output_dir: str | Path) -> dict[str, Path]:
    """Write exact results and a README-ready compact table without rounding JSON."""
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    files = {
        "json": directory / "results.json",
        "csv": directory / "results.csv",
        "markdown": directory / "summary.md",
    }
    files["json"].write_text(
        json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    rows = []
    for method in _method_reports(report):
        for result in method["examples"]:
            row = {
                **result,
                **{f"extractor_{k}": v for k, v in method["extractor"].items()},
                "dataset_sha256": method["dataset"]["sha256"],
            }
            rows.append(
                {
                    key: json.dumps(value, ensure_ascii=False, sort_keys=True)
                    if isinstance(value, (dict, list))
                    else value
                    for key, value in row.items()
                }
            )
    with files["csv"].open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(
            target, fieldnames=list(rows[0]) if rows else ["example_id"], lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)
    files["markdown"].write_text(summary_markdown(report), encoding="utf-8")
    return files


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True, type=Path)
    parser.add_argument(
        "--mode", choices=["phrase", "fixture", "live", "compare"], default="phrase"
    )
    parser.add_argument(
        "--provider",
        choices=["openai", "gemini"],
        default="openai",
        help="Live adapter for --mode live/compare; offline modes do not call a provider.",
    )
    parser.add_argument(
        "--post-hoc",
        action="store_true",
        help="Mark a replay after prior result inspection; never a new held-out estimate.",
    )
    parser.add_argument(
        "--min-request-interval",
        type=_parse_request_interval,
        default=0.0,
        help="Minimum seconds between serial live request starts (0 to 60; default 0).",
    )
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/evaluation"))
    args = parser.parse_args(argv)
    try:
        examples = load_dataset(args.dataset)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    from .extractors import FixtureExtractor, OpenAIExtractor, PhraseMatcher

    if args.mode == "fixture" and any(example.split == "held_out" for example in examples):
        parser.error("Fixture answer lookups cannot be evaluated as held-out extraction.")

    def make_live_extractor():
        if args.provider == "gemini":
            from .extractors import GeminiExtractor

            extractor = GeminiExtractor()
        else:
            extractor = OpenAIExtractor()
        if args.min_request_interval > 0:
            return PacedExtractor(extractor, args.min_request_interval)
        return extractor

    extractors = {
        "phrase": lambda: [PhraseMatcher()],
        "fixture": lambda: [FixtureExtractor()],
        "live": lambda: [make_live_extractor()],
        "compare": lambda: [PhraseMatcher(), make_live_extractor()],
    }[args.mode]()
    reports = [
        evaluate_examples(examples, extractor, post_hoc=args.post_hoc) for extractor in extractors
    ]
    report = reports[0] if len(reports) == 1 else {"schema_version": "1.0", "methods": reports}
    write_results(report, args.output_dir)
    print(summary_markdown(report))
    # A failed inference must be visible to scripts rather than looking like a
    # successful experiment. Wrong valid predictions are ordinary measured data.
    return 1 if any(method["summary"]["errors"] for method in reports) else 0


if __name__ == "__main__":
    raise SystemExit(main())
