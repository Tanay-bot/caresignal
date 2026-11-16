"""Render judge-readable evaluation reports from stored results, without inference."""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any, Sequence

from .models import AssistanceLevel

_LABELS = tuple(label.value for label in AssistanceLevel)
_STATUSES = ("COMPLETE", "UNAVAILABLE", "INVALID")


def _table_cell(value: Any) -> str:
    """Keep table structure intact when stored identifiers contain punctuation."""
    return str(value).replace("\\", "\\\\").replace("|", "\\|").replace("\n", "<br>")


def _code_block(value: Any, language: str = "json") -> str:
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2)
    longest = max((len(match.group()) for match in re.finditer(r"`+", text)), default=0)
    fence = "`" * max(3, longest + 1)
    return f"{fence}{language}\n{text}\n{fence}"


def _reports(report: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(report, dict):
        raise ValueError("Stored evaluation results must be a JSON object.")
    methods = report.get("methods", [report])
    if not isinstance(methods, list) or not methods:
        raise ValueError("Stored evaluation results must contain at least one method.")
    return methods


def _stored_spans(row: dict[str, Any], field: str, identifier: str) -> list[tuple[int, int, str]]:
    """Validate saved spans and normalize order without changing their contents."""
    spans: list[tuple[int, int, str]] = []
    note = row.get("note")
    if "note" in row and not isinstance(note, str):
        raise ValueError(f"Stored note must be text for {identifier}.")
    for span in row[field]:
        if not isinstance(span, dict):
            raise ValueError(f"Stored {field} contains a malformed span for {identifier}.")
        start, end, quote = span.get("start"), span.get("end"), span.get("quote")
        if (
            type(start) is not int
            or type(end) is not int
            or not isinstance(quote, str)
            or not quote
            or not 0 <= start < end
            or end - start != len(quote)
        ):
            raise ValueError(f"Stored {field} contains a malformed span for {identifier}.")
        if note is not None and (end > len(note) or note[start:end] != quote):
            raise ValueError(f"Stored {field} span does not match its note for {identifier}.")
        spans.append((start, end, quote))
    if field == "gold_evidence" and len(set(spans)) != len(spans):
        raise ValueError(f"Stored {field} contains duplicate spans for {identifier}.")
    # The frozen extractor/evaluator permits repeated predicted quotes. Retain
    # those occurrences: they produce a measurable strict mismatch against the
    # unique frozen gold spans rather than invalidating the stored experiment.
    return sorted(spans)


def _validate_method(method: dict[str, Any]) -> dict[str, Any]:
    """Check report integrity; never repair flags, predictions, or saved counts."""
    if not isinstance(method, dict):
        raise ValueError("Each stored method must be a JSON object.")
    rows = method.get("examples")
    if not isinstance(rows, list) or not rows:
        raise ValueError("Each stored method must contain nonempty example rows.")
    for key in ("dataset", "extractor", "summary"):
        if not isinstance(method.get(key), dict):
            raise ValueError(f"Each stored method requires {key} metadata.")
    dataset = method["dataset"]
    for field in ("ids", "revisions", "translation_ids"):
        if not isinstance(dataset.get(field), list) or not all(
            isinstance(value, str) and value.strip() for value in dataset[field]
        ):
            raise ValueError(f"Stored dataset {field} must be a list of nonblank strings.")
    if not isinstance(dataset.get("sha256"), str) or not dataset["sha256"].strip():
        raise ValueError("Stored dataset hash is required.")
    for field in ("mode", "version", "prompt_version"):
        value = method["extractor"].get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Stored extractor {field} is required.")
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Each stored example must be a JSON object.")
        identifier = row.get("example_id")
        if not isinstance(identifier, str) or not identifier or identifier in seen:
            raise ValueError("Stored example IDs must be nonempty and unique per method.")
        seen.add(identifier)
        if row.get("status") not in _STATUSES:
            raise ValueError(f"Unknown stored analysis status for {identifier}.")
        if row.get("gold_label") not in _LABELS:
            raise ValueError(f"Unknown stored gold label for {identifier}.")
        if not isinstance(row.get("target"), dict):
            raise ValueError(f"Stored target is required for {identifier}.")
        for field in ("gold_evidence", "predicted_evidence"):
            if not isinstance(row.get(field), list):
                raise ValueError(f"Stored {field} must be a list for {identifier}.")
        gold_spans = _stored_spans(row, "gold_evidence", identifier)
        predicted_spans = _stored_spans(row, "predicted_evidence", identifier)
        for field in ("label_correct", "evidence_correct", "joint_correct"):
            if type(row.get(field)) is not bool:
                raise ValueError(f"Stored {field} must be Boolean for {identifier}.")
        if row["joint_correct"] != (row["label_correct"] and row["evidence_correct"]):
            raise ValueError(
                f"Stored joint correctness conflicts with component flags for {identifier}."
            )
        if row["status"] == "COMPLETE":
            if row.get("predicted_label") not in _LABELS:
                raise ValueError(f"Completed prediction has an unknown label for {identifier}.")
            if row["evidence_correct"] != (gold_spans == predicted_spans):
                raise ValueError(
                    f"Stored evidence correctness conflicts with exact span sets for {identifier}."
                )
            if row["label_correct"] != (row["predicted_label"] == row["gold_label"]):
                raise ValueError(
                    f"Stored label correctness conflicts with labels for {identifier}."
                )
        elif any(row[field] for field in ("label_correct", "evidence_correct", "joint_correct")):
            raise ValueError(f"Analysis failures cannot count as correct for {identifier}.")
    statuses = Counter(row["status"] for row in rows)
    counts = {
        "total": len(rows),
        "completed": statuses["COMPLETE"],
        "errors": statuses["UNAVAILABLE"] + statuses["INVALID"],
        "label_correct": sum(row["label_correct"] for row in rows),
        "evidence_correct": sum(row["evidence_correct"] for row in rows),
        "joint_correct": sum(row["joint_correct"] for row in rows),
    }
    stored = method["summary"]
    for key, value in counts.items():
        if type(stored.get(key)) is not int or stored[key] != value:
            raise ValueError(f"Stored summary {key} conflicts with its example rows.")
    for key in ("label", "evidence", "joint"):
        stored_rate = stored.get(f"{key}_accuracy")
        expected_rate = counts[f"{key}_correct"] / counts["total"]
        if isinstance(stored_rate, bool) or not isinstance(stored_rate, (int, float)):
            raise ValueError(f"Stored {key}_accuracy is missing or invalid.")
        if not math.isclose(stored_rate, expected_rate, rel_tol=1e-12, abs_tol=1e-12):
            raise ValueError(f"Stored {key}_accuracy conflicts with its exact count.")
    return {"rows": rows, "statuses": statuses, "counts": counts}


def _error_kind(row: dict[str, Any]) -> str:
    if row["status"] == "UNAVAILABLE":
        return "Provider unavailable"
    if row["status"] == "INVALID":
        return "Invalid extraction output"
    if not row["label_correct"] and not row["evidence_correct"]:
        return "Label and strict evidence mismatch"
    if not row["label_correct"]:
        return "Label mismatch"
    return "Strict evidence span mismatch"


def _render_method(index: int, method: dict[str, Any], checked: dict[str, Any]) -> list[str]:
    rows, statuses, counts = checked["rows"], checked["statuses"], checked["counts"]
    meta = method["extractor"]
    name = _table_cell(meta.get("mode", "unknown"))
    model = _table_cell(meta.get("model_id") or "no model")
    output = [
        f"## Method {index}: {name} / {model}",
        "",
        "| N | Complete | Unavailable | Invalid | Analysis failures | Incorrect examples |",
        "| ---: | ---: | ---: | ---: | ---: | ---: |",
        f"| {counts['total']} | {statuses['COMPLETE']} | {statuses['UNAVAILABLE']} | {statuses['INVALID']} | {counts['errors']} | {counts['total'] - counts['joint_correct']} |",
        "",
        "Analysis failures are unavailable or invalid runs. Incorrect examples include those failures and every completed label or strict-span mismatch.",
        "",
        "| Metric | Exact fraction |",
        "| --- | ---: |",
        f"| Label agreement | {counts['label_correct']}/{counts['total']} |",
        f"| Exact evidence span-set agreement | {counts['evidence_correct']}/{counts['total']} |",
        f"| Joint agreement | {counts['joint_correct']}/{counts['total']} |",
        "",
        "Every input remains in the denominator. Exact evidence requires the complete frozen set of half-open `(start, end, quote)` spans; partial overlaps and paraphrases fail this strict measure. Repeated predicted spans are retained in the comparison.",
        "",
        "### Stored provenance",
        "",
        _code_block(
            {
                key: method.get(key)
                for key in ("schema_version", "scope", "dataset", "extractor", "metrics_policy")
            }
        ),
        "",
        "### Label distributions",
        "",
        "| Label | Gold | Predicted in complete runs |",
        "| --- | ---: | ---: |",
    ]
    gold = Counter(row["gold_label"] for row in rows)
    predicted = Counter(row["predicted_label"] for row in rows if row["status"] == "COMPLETE")
    for label in _LABELS:
        output.append(f"| {label} | {gold[label]} | {predicted[label]} |")
    output += [
        f"| No completed prediction | 0 | {counts['errors']} |",
        f"| Total | {counts['total']} | {counts['total']} |",
        "",
        "### Confusion table",
        "",
        "Rows are gold labels. Columns are predicted labels or analysis-failure statuses.",
        "",
        "| Gold \\ Predicted | " + " | ".join(_LABELS) + " | UNAVAILABLE | INVALID | Total |",
        "| --- | " + " | ".join(["---:"] * (len(_LABELS) + 3)) + " |",
    ]
    confusion = Counter(
        (
            row["gold_label"],
            row["predicted_label"] if row["status"] == "COMPLETE" else row["status"],
        )
        for row in rows
    )
    columns = (*_LABELS, "UNAVAILABLE", "INVALID")
    for label in _LABELS:
        values = [confusion[label, column] for column in columns]
        output.append(
            f"| {label} | " + " | ".join(str(value) for value in values) + f" | {sum(values)} |"
        )
    totals = [sum(confusion[label, column] for label in _LABELS) for column in columns]
    output += [
        "| Total | " + " | ".join(str(value) for value in totals) + f" | {counts['total']} |",
        "",
        "### Error review",
        "",
    ]
    errors = [row for row in rows if not row["joint_correct"]]
    if not errors:
        output += ["No incorrect examples or analysis failures were recorded for this method.", ""]
        return output
    kinds = Counter(_error_kind(row) for row in errors)
    output += ["| Recorded category | Count |", "| --- | ---: |"]
    output += [f"| {kind} | {number} |" for kind, number in sorted(kinds.items())]
    output += [""]
    for row in errors:
        identifier = _table_cell(row["example_id"])
        source_id = row.get("source_note_id") or row["example_id"]
        output += [
            f"#### {identifier}: {_error_kind(row)}",
            "",
            "Stored source and outcome:",
            "",
            _code_block(
                {
                    "source_note_id": source_id,
                    "example_id": row["example_id"],
                    "source_url": row.get("source_url"),
                    "status": row["status"],
                    "error_category": row.get("error_category"),
                    "reason_code": row.get("reason_code"),
                    "expected_label": row["gold_label"],
                    "predicted_label": row.get("predicted_label"),
                }
            ),
            "",
            "Selected target:",
            "",
            _code_block(row["target"]),
            "",
            "Frozen note used for extraction:",
            "",
            _code_block(row.get("note", "Not present in the stored results."), "text"),
            "",
        ]
        if row.get("original_note"):
            output += ["Original-language note:", "", _code_block(row["original_note"], "text"), ""]
        output += [
            "Expected exact evidence:",
            "",
            _code_block(row["gold_evidence"]),
            "",
            "Predicted exact evidence:",
            "",
            _code_block(row["predicted_evidence"]),
            "",
        ]
        if row["status"] != "COMPLETE":
            output += [
                "This is an analysis failure, not a completed label prediction. It remains incorrect in all three metric denominators.",
                "",
            ]
        elif row["label_correct"] and not row["evidence_correct"]:
            output += [
                "The label matches. The saved evidence span set differs from the strict frozen annotation; this report does not judge an alternative span semantically correct or incorrect.",
                "",
            ]
    return output


def write_evaluation_report(
    report: dict[str, Any],
    output_path: str | Path,
    *,
    heading: str = "CareSignal extraction evaluation",
    methods_note: str | None = None,
) -> Path:
    """Write a Markdown review from saved predictions; never call an extractor.

    ``methods_note`` records supplied qualifications such as a stratified sample
    or coding-agent annotation review. Such methods are never inferred from N,
    labels, filenames, or a perfect score. Saved summary/row conflicts fail before
    output is written so the report cannot silently change measured results.
    """
    methods = _reports(report)
    checked = [_validate_method(method) for method in methods]
    title = " ".join(heading.split())
    if not title:
        raise ValueError("The report heading cannot be blank.")
    output = [f"# {title}", "", "## Scope and methods", ""]
    dataset_ids = {
        dataset_id for method in methods for dataset_id in method["dataset"].get("ids", [])
    }
    if dataset_ids and all(
        identifier == "ekrombouts/fruta_records" or identifier.lower().startswith("fictional")
        for identifier in dataset_ids
    ):
        output += [
            "The identified source datasets contain synthetic or fictional documentation.",
            "",
        ]
    output += [
        "This report summarizes stored extraction results for the frozen inputs identified below. It does not establish clinical validity, treatment benefit, or deployment readiness. No inference was rerun to produce this report.",
        "",
    ]
    if methods_note and methods_note.strip():
        output += [methods_note.strip(), ""]
    if len({method["dataset"]["sha256"] for method in methods}) > 1:
        output += [
            "Method reports contain different frozen dataset hashes; these metrics are not a matched-input comparison.",
            "",
        ]
    scopes = {method.get("scope") for method in methods}
    if scopes != {"held_out_public"}:
        output += [
            "Development or mixed-scope results describe those examples only and do not estimate held-out Fruta performance.",
            "",
        ]
    for index, (method, validation) in enumerate(zip(methods, checked, strict=True), 1):
        output += _render_method(index, method, validation)
    output += ["This project is a prototype and is not medical advice.", ""]
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(output), encoding="utf-8")
    return destination


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--heading", default="CareSignal extraction evaluation")
    parser.add_argument("--methods-note")
    args = parser.parse_args(argv)
    try:
        report = json.loads(args.results.read_text(encoding="utf-8"))
        path = write_evaluation_report(
            report, args.output, heading=args.heading, methods_note=args.methods_note
        )
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
