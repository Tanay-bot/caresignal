"""Export saved held-out results into viz/data.json for the Divergence visual.

Reads only files already committed to this repository. It never calls a model
provider, never imports the extractor adapters and never fills a value it cannot
find: absent values are recorded as missing and shown as missing in the visual.

    python scripts/export_divergence.py            # writes viz/data.json and viz/divergence.html
    python scripts/export_divergence.py --no-html  # data only

Output is deterministic: sorted keys, no generation timestamp, stable ordering.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FREEZE_COMMIT_PREFIX = "b28451c"
EXPECTED_NOTES = 24

DATASET = "data/fruta_held_out.jsonl"
MANIFEST = "data/fruta_held_out_manifest.json"
ANNOTATIONS = "data/annotations/fruta_held_out_v1.json"
FIRST_PASS = "docs/heldout-results/results.json"
FOLLOWUP = "docs/heldout-followup/results.json"
RETRY_LEDGER = "docs/heldout-followup/retry-ledger.json"
TEMPLATE = "viz/src/divergence.template.html"
OUT_DATA = "viz/data.json"
OUT_HTML = "viz/divergence.html"

# Editorial choice for Act I: the annotators' rationale places the supervision
# cue ("We kept an extra close eye on whether he might fall.") in sentence 3 of 5,
# and the three systems disagree. Falls back to a data-derived rule if absent.
ACT1_PREFERRED = "nk_0797"

SYSTEMS = {
    "baseline": {
        "file": FIRST_PASS,
        "mode": "phrase",
        "prompt_version": "rules-v1",
        "name": "Baseline",
        "detail": "phrase rules",
    },
    "v1": {
        "file": FIRST_PASS,
        "mode": "gemini",
        "prompt_version": "walking-assistance-v1",
        "name": "Model",
        "detail": "gemini-3.1-flash-lite · prompt v1",
    },
    "v2": {
        "file": FOLLOWUP,
        "mode": "gemini",
        "prompt_version": "walking-assistance-v2",
        "name": "Model",
        "detail": "gemini-3.1-flash-lite · prompt v2",
    },
}


# ---------------------------------------------------------------- helpers
def read_json(rel: str) -> Any | None:
    path = ROOT / rel
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(rel: str) -> list[dict] | None:
    path = ROOT / rel
    if not path.exists():
        return None
    return [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]


def sha256_file(rel: str) -> str | None:
    path = ROOT / rel
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def frozen_dataset_check() -> str:
    """Compare the dataset file with its bytes at the freeze commit, if git is usable."""
    try:
        frozen = subprocess.run(
            ["git", "show", f"{FREEZE_COMMIT_PREFIX}:{DATASET}"],
            cwd=ROOT,
            capture_output=True,
            check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return "unverified (git object unavailable)"
    current = (ROOT / DATASET).read_bytes()
    return "identical to freeze commit" if frozen == current else "DIFFERS from freeze commit"


_SENTENCE_END = re.compile(r"[.!?](?=\s+|$)")


def sentence_bounds(text: str) -> list[list[int]]:
    """Derive [start, end) sentence offsets: split after . ! ? followed by whitespace/end."""
    bounds, start = [], 0
    for match in _SENTENCE_END.finditer(text):
        end = match.end()
        if text[start:end].strip():
            lead = len(text[start:end]) - len(text[start:end].lstrip())
            bounds.append([start + lead, end])
        start = end
    if text[start:].strip():
        lead = len(text[start:]) - len(text[start:].lstrip())
        bounds.append([start + lead, len(text.rstrip())])
    return bounds


def resolve_span(text: str, item: dict) -> dict:
    """Return a span with offsets, recording whether offsets were stored or derived."""
    quote = item.get("quote")
    start, end = item.get("start"), item.get("end")
    out = {"quote": quote, "start": None, "end": None, "offset_source": "unresolved"}
    stored_ok = (
        isinstance(start, int)
        and isinstance(end, int)
        and 0 <= start < end <= len(text)
        and (quote is None or text[start:end] == quote)
    )
    if stored_ok:
        out.update(start=start, end=end, offset_source="stored")
        if quote is None:
            out["quote"] = text[start:end]
        return out
    if not quote:
        out["problem"] = "no quote and no valid stored offsets"
        return out
    hits = [m.start() for m in re.finditer(re.escape(quote), text)]
    if len(hits) == 1:
        out.update(start=hits[0], end=hits[0] + len(quote), offset_source="derived_exact_match")
    elif len(hits) > 1:
        out["problem"] = f"quote occurs {len(hits)} times; offset ambiguous"
    else:
        out["problem"] = "quote not found in note text"
    if start is not None and out["offset_source"] != "unresolved":
        out["problem"] = "stored offsets did not match quote; re-located by exact match"
    return out


def find_method(results: dict | None, mode: str, prompt_version: str) -> dict | None:
    if not results:
        return None
    for method in results.get("methods", []):
        extractor = method.get("extractor", {})
        if extractor.get("mode") == mode and extractor.get("prompt_version") == prompt_version:
            return method
    return None


def span_key(spans: list[dict]) -> list[list[int]] | None:
    if any(s["start"] is None for s in spans):
        return None
    return sorted([s["start"], s["end"]] for s in spans)


def _src(rel: str) -> str:
    path = ROOT / rel
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _string_constant(source: str, name: str) -> str | None:
    """Read a module-level string constant written as adjacent literals."""
    match = re.search(rf"^{name} = \(\n((?:\s+\".*\"\n)+)\)", source, re.M)
    if not match:
        return None
    return "".join(json.loads(line.strip()) for line in match.group(1).splitlines())


def demo_content(warnings: list[str]) -> dict:
    """Fictional walkthrough shown in the explainer, read from the app's own source."""
    fixtures, extractors = _src("caresignal/fixtures.py"), _src("caresignal/extractors.py")
    service, models, app = (
        _src("caresignal/service.py"),
        _src("caresignal/models.py"),
        _src("app.py"),
    )
    note = _string_constant(fixtures, "DEMO_NOTE")
    date = re.search(r"^DEMO_DATE = date\((\d+), (\d+), (\d+)\)", fixtures, re.M)
    quote = None
    block = re.search(r"note_body == DEMO_NOTE:(.*?)\)\n", extractors, re.S)
    if block and note:
        quotes = [json.loads(q) for q in re.findall(r'^\s+(".*")', block.group(1), re.M)]
        quote = next((q for q in quotes if q in note), None)
    level = re.search(r"note_body == DEMO_NOTE:.*?AssistanceLevel\.(\w+)", extractors, re.S)
    labels = dict(re.findall(r'AssistanceLevel\.(\w+): "([^"]+)"', models))
    residents = [
        {"name": n, "usual_level": lv, "usual_label": labels.get(lv), "usual_description": d}
        for n, lv, d in re.findall(
            r'\(\s*"(\w+)",\s*AssistanceLevel\.(\w+),\s*"([^"]+)",?\s*\)', service
        )
    ]
    ranks = dict(re.findall(r"AssistanceLevel\.(\w+): (\d)", models))
    headlines = dict(re.findall(r'"(MORE_HELP|LESS_HELP|MATCHES)": "([^"]+)"', app))
    observed = level.group(1) if level else None
    for r in residents:
        o, u = ranks.get(observed or ""), ranks.get(r["usual_level"])
        if o is None or u is None:
            r["result"] = None
            continue
        key = "MORE_HELP" if o > u else "LESS_HELP" if o < u else "MATCHES"
        r["result"] = headlines.get(key)
    out = {
        "note": note,
        "date": "-".join(f"{int(x):02d}" for x in date.groups()) if date else None,
        "evidence_quote": quote,
        "evidence_start": note.find(quote) if note and quote else None,
        "observed_level": observed,
        "observed_label": labels.get(observed or ""),
        "residents": residents,
        "sources": [
            "caresignal/fixtures.py",
            "caresignal/extractors.py",
            "caresignal/service.py",
            "caresignal/models.py",
            "app.py",
        ],
    }
    for key in ("note", "evidence_quote", "observed_label"):
        if not out[key]:
            warnings.append(f"demo: {key} not found in app source; explainer omits it")
    if len(residents) < 2 or any(r["result"] is None for r in residents):
        warnings.append("demo: resident baselines or comparison wording incomplete")
    return out


# ---------------------------------------------------------------- export
def build() -> tuple[dict, list[list[str]], list[str]]:
    warnings: list[str] = []
    dataset = read_jsonl(DATASET) or []
    manifest = read_json(MANIFEST) or {}
    annotations = read_json(ANNOTATIONS) or {}
    ledger = read_json(RETRY_LEDGER) or {}
    results = {rel: read_json(rel) for rel in {FIRST_PASS, FOLLOWUP}}
    if not dataset:
        warnings.append(f"{DATASET} missing or empty: note text falls back to results files")

    reviews = {r.get("note_id"): r for r in annotations.get("reviews", [])}
    retried = sorted(r.get("example_id") for r in ledger.get("retried_examples", []))

    methods: dict[str, dict | None] = {}
    by_id: dict[str, dict[str, dict]] = {}
    for key, spec in SYSTEMS.items():
        method = find_method(results[spec["file"]], spec["mode"], spec["prompt_version"])
        methods[key] = method
        if method is None:
            warnings.append(
                f"system {key}: no {spec['mode']}/{spec['prompt_version']} run in {spec['file']}"
            )
        by_id[key] = {ex["example_id"]: ex for ex in (method or {}).get("examples", [])}

    # Baseline replayed in the follow-up must be identical to the first pass.
    replay = find_method(results[FOLLOWUP], "phrase", "rules-v1")
    baseline_replay_identical = None
    if replay and methods["baseline"]:
        a = {
            e["example_id"]: (e["predicted_label"], e["predicted_evidence"])
            for e in methods["baseline"]["examples"]
        }
        b = {
            e["example_id"]: (e["predicted_label"], e["predicted_evidence"])
            for e in replay["examples"]
        }
        baseline_replay_identical = a == b

    # Note order: frozen dataset order; then any IDs that only appear in results.
    order = [row["id"] for row in dataset]
    for key in SYSTEMS:
        for ex_id in by_id[key]:
            if ex_id not in order:
                order.append(ex_id)
                warnings.append(f"{ex_id}: present in {key} results but not in {DATASET}")
    rows = {row["id"]: row for row in dataset}

    expected_ids = [
        item.get("id") or item.get("note_id")
        for item in (manifest.get("frozen_dataset", {}) or {}).get("examples", [])
        if isinstance(item, dict)
    ]
    missing_expected = [i for i in expected_ids if i and i not in order]

    cov = {
        f: {"present": 0, "derived": 0, "missing": 0}
        for f in [
            "note text",
            "sentence boundaries",
            "gold label",
            "gold span offsets",
            "baseline label",
            "baseline span offsets",
            "v1 label",
            "v1 span offsets",
            "v2 label",
            "v2 span offsets",
        ]
    }
    notes = []
    for index, note_id in enumerate(order):
        row = rows.get(note_id)
        source_ex = next((by_id[k][note_id] for k in SYSTEMS if note_id in by_id[k]), None)
        text = row["note"] if row else (source_ex or {}).get("note")
        if text is None:
            cov["note text"]["missing"] += 1
            cov["sentence boundaries"]["missing"] += 1
        else:
            cov["note text"]["present" if row else "derived"] += 1
            cov["sentence boundaries"]["derived"] += 1
        for k in SYSTEMS:
            other = by_id[k].get(note_id)
            if other and text is not None and other.get("note") != text:
                warnings.append(f"{note_id}: {k} results note text differs from frozen dataset")

        gold_src = row or source_ex or {}
        gold_label = gold_src.get("gold_label")
        cov["gold label"]["present" if gold_label else "missing"] += 1
        gold_spans = (
            [resolve_span(text, s) for s in gold_src.get("gold_evidence", [])] if text else []
        )
        _count_spans(
            cov["gold span offsets"], gold_spans, gold_src.get("gold_evidence") is not None
        )

        review = reviews.get(note_id, {})
        note = {
            "index": index,
            "id": note_id,
            "text": text,
            "sentences": sentence_bounds(text) if text else None,
            "target_cue": (gold_src.get("target") or {}).get("target_cue"),
            "context_key": (gold_src.get("target") or {}).get("context_key"),
            "selection_stratum": review.get("selection_stratum"),
            "rationale": (review.get("annotation_a") or {}).get("rationale"),
            "gold": {"label": gold_label, "spans": gold_spans},
            "pred": {},
        }
        for key in SYSTEMS:
            ex = by_id[key].get(note_id)
            if ex is None:
                cov[f"{key} label"]["missing"] += 1
                cov[f"{key} span offsets"]["missing"] += 1
                note["pred"][key] = None
                continue
            label = ex.get("predicted_label")
            cov[f"{key} label"]["present" if label else "missing"] += 1
            spans = (
                [resolve_span(text, s) for s in ex.get("predicted_evidence") or []] if text else []
            )
            _count_spans(
                cov[f"{key} span offsets"], spans, ex.get("predicted_evidence") is not None
            )
            pred = {
                "label": label,
                "status": ex.get("status"),
                "reason_code": ex.get("reason_code"),
                "error_category": ex.get("error_category"),
                "spans": spans,
                "label_correct": ex.get("label_correct"),
                "evidence_correct": ex.get("evidence_correct"),
                "joint_correct": ex.get("joint_correct"),
                "correctness_source": "stored",
            }
            # Re-check stored correctness against labels and exact span sets; never overwrite.
            gk, pk = span_key(gold_spans), span_key(spans)
            if label and gold_label and gk is not None and pk is not None:
                lc, ec = label == gold_label, gk == pk
                if pred["label_correct"] is None:
                    pred.update(
                        label_correct=lc,
                        evidence_correct=ec,
                        joint_correct=lc and ec,
                        correctness_source="derived",
                    )
                elif (lc, ec, lc and ec) != (
                    pred["label_correct"],
                    pred["evidence_correct"],
                    pred["joint_correct"],
                ):
                    warnings.append(
                        f"{note_id}/{key}: stored correctness disagrees with recomputation"
                    )
            if key == "v2":
                pred["retried_after_rate_limit"] = note_id in retried
            note["pred"][key] = pred
        notes.append(note)

    for mid in missing_expected:
        notes.append(
            {
                "index": len(notes),
                "id": mid,
                "text": None,
                "sentences": None,
                "missing": True,
                "gold": {"label": None, "spans": []},
                "pred": {k: None for k in SYSTEMS},
            }
        )
        warnings.append(f"{mid}: listed in manifest but absent from dataset and results")

    # Act I note.
    act1 = ACT1_PREFERRED if any(n["id"] == ACT1_PREFERRED and n["text"] for n in notes) else None
    if act1 is None:
        candidates = [
            n for n in notes if n["text"] and n["gold"]["spans"] and n["gold"]["spans"][-1]["end"]
        ]
        candidates.sort(key=lambda n: (-(n["gold"]["spans"][-1]["end"] or 0), n["index"]))
        act1 = candidates[0]["id"] if candidates else None

    resolvable = sum(
        1
        for n in notes
        for s in n["gold"]["spans"] + [s for p in n["pred"].values() if p for s in p["spans"]]
        if s["start"] is not None
    )
    total_spans = sum(
        len(n["gold"]["spans"]) + sum(len(p["spans"]) for p in n["pred"].values() if p)
        for n in notes
    )

    systems = {}
    for key, spec in SYSTEMS.items():
        m = methods[key]
        systems[key] = {
            "name": spec["name"],
            "detail": spec["detail"],
            "source_file": spec["file"],
            "present": m is not None,
            "extractor": (m or {}).get("extractor"),
            "scope": (m or {}).get("scope"),
            "scope_note": (m or {}).get("scope_note"),
            "summary": (m or {}).get("summary"),
        }

    first, follow = results[FIRST_PASS] or {}, results[FOLLOWUP] or {}
    gold_unclear = sum(1 for n in notes if n["gold"]["label"] == "UNCLEAR")
    data = {
        "schema": "divergence-v1",
        "expected_notes": EXPECTED_NOTES,
        "act1_note_id": act1,
        "span_offsets_resolvable": resolvable,
        "span_offsets_total": total_spans,
        "degraded_ribbon_only": total_spans > 0 and resolvable == 0,
        "missing_expected_ids": missing_expected,
        "always_unclear_label_correct": gold_unclear,
        "systems": systems,
        "notes": notes,
        "provenance": {
            "freeze_commit": first.get("freeze_commit"),
            "freeze_commit_matches_b28451c": str(first.get("freeze_commit", "")).startswith(
                FREEZE_COMMIT_PREFIX
            )
            and str(follow.get("freeze_commit", "")).startswith(FREEZE_COMMIT_PREFIX),
            "dataset_vs_freeze_commit": frozen_dataset_check()
            if dataset
            else "dataset file missing",
            "first_pass_runtime_commit": first.get("runtime_commit"),
            "followup_runtime_commit": follow.get("runtime_commit"),
            "followup_evaluation_design": follow.get("evaluation_design"),
            "dataset_revision": ((methods["baseline"] or {}).get("dataset") or {}).get("revisions"),
            "dataset_sha256": ((methods["baseline"] or {}).get("dataset") or {}).get("sha256"),
            "annotation_process": annotations.get("process"),
            "blind_label_agreement": annotations.get("blind_label_agreement"),
            "baseline_replay_identical_in_followup": baseline_replay_identical,
            "v2_retry_policy": follow.get("retry_policy"),
            "v2_retried_ids": retried,
            "file_sha256": {
                rel: sha256_file(rel)
                for rel in [DATASET, MANIFEST, ANNOTATIONS, FIRST_PASS, FOLLOWUP, RETRY_LEDGER]
            },
        },
        "demo": demo_content(warnings),
        "warnings": warnings,
    }
    table = [["field", "present", "derived", "missing"]] + [
        [field, str(c["present"]), str(c["derived"]), str(c["missing"])] for field, c in cov.items()
    ]
    return data, table, warnings


def _count_spans(bucket: dict, spans: list[dict], list_present: bool) -> None:
    """Count per span. An empty stored span list is present (a deliberate empty set)."""
    if not list_present:
        bucket["missing"] += 1
        return
    if not spans:
        bucket["present"] += 1
        return
    for span in spans:
        src = span["offset_source"]
        bucket[
            "present" if src == "stored" else "derived" if src.startswith("derived") else "missing"
        ] += 1


def print_report(data: dict, table: list[list[str]], warnings: list[str]) -> None:
    widths = [max(len(r[i]) for r in table) for i in range(4)]
    print(
        "\nCoverage (span rows count individual spans; an empty stored span set counts once as present)"
    )
    for i, r in enumerate(table):
        print(
            "  "
            + "  ".join(
                c.ljust(widths[j]) if j == 0 else c.rjust(widths[j]) for j, c in enumerate(r)
            )
        )
        if i == 0:
            print("  " + "  ".join("-" * w for w in widths))
    print(f"\nNotes exported: {len(data['notes'])} (expected {data['expected_notes']})")
    print(
        f"Span offsets resolvable: {data['span_offsets_resolvable']}/{data['span_offsets_total']}"
    )
    print(f"Act I note: {data['act1_note_id']}")
    for key, s in data["systems"].items():
        sm = s["summary"] or {}
        print(
            f"  {key:8s} {s['detail']:40s} scope={s['scope']}  label {sm.get('label_correct')}/{sm.get('total')}"
            f"  joint {sm.get('joint_correct')}/{sm.get('total')}  evidence {sm.get('evidence_correct')}/{sm.get('total')}"
        )
    p = data["provenance"]
    print(
        f"Freeze commit {p['freeze_commit']} (b28451c match: {p['freeze_commit_matches_b28451c']});"
        f" dataset {p['dataset_vs_freeze_commit']}"
    )
    print(f"Baseline identical in follow-up replay: {p['baseline_replay_identical_in_followup']}")
    print(f"v2 rows retried after rate limit: {', '.join(p['v2_retried_ids']) or 'none'}")
    print("Warnings: " + ("none" if not warnings else ""))
    for w in warnings:
        print("  - " + w)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--no-html", action="store_true", help="write viz/data.json only")
    args = parser.parse_args(argv)
    data, table, warnings = build()
    payload = json.dumps(data, ensure_ascii=False, sort_keys=True, indent=1) + "\n"
    (ROOT / "viz").mkdir(exist_ok=True)
    (ROOT / OUT_DATA).write_text(payload, encoding="utf-8")
    print(
        f"wrote {OUT_DATA} ({len(payload.encode())} bytes, sha256 {hashlib.sha256(payload.encode()).hexdigest()[:12]})"
    )
    if not args.no_html:
        template = ROOT / TEMPLATE
        if not template.exists():
            print(f"{TEMPLATE} not found; skipped HTML", file=sys.stderr)
        else:
            inline = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            inline = inline.replace("</", "<\\/")  # keep the inline <script> unbreakable
            html = template.read_text(encoding="utf-8").replace(
                "/*__DIVERGENCE_DATA__*/null", inline, 1
            )
            (ROOT / OUT_HTML).write_text(html, encoding="utf-8")
            print(f"wrote {OUT_HTML} ({len(html.encode())} bytes)")
    print_report(data, table, warnings)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
