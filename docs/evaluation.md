# Reproducible extraction evaluation

CareSignal has a recorded first comparison on 24 frozen public synthetic Fruta notes. Both methods received the same full English notes and selected targets. The data was frozen before the first successful held-out predictions; the phrase matcher and Gemini completed all 24 without API errors. The [methods](heldout-methods.md), [raw results](heldout-results/results.json), [CSV](heldout-results/results.csv) and [summary](heldout-results/summary.md) preserve the evidence.

| First-run method | Label agreement | Exact evidence | Label + evidence | API/output errors |
| --- | ---: | ---: | ---: | ---: |
| Phrase rules `phrase-v1` / `rules-v1` | 14/24 (58.3%) | 12/24 (50.0%) | 8/24 (33.3%) | 0 |
| Gemini `gemini-3.1-flash-lite` / `gemini-structured-v2` / `walking-assistance-v1` | 11/24 (45.8%) | 14/24 (58.3%) | 7/24 (29.2%) | 0 |

Gemini did not beat the phrase baseline on label or joint agreement in this sample. These are a small, deliberately stratified challenge sample of artificial notes, with translations and reference labels reviewed by two independent assistant contexts from the same model family. They are not human or clinical-expert annotations. “Held out” describes separation from implementation and tuning before this first run; upstream Fruta calls its split `train`, and provider training exposure is unknown. Results do not estimate prevalence-weighted performance or clinical validity.

The canonical frozen dataset hash is `a2d3a2e8dbe1d119c8cb02064963f585849ee2f01d95f2d640c7cbf426b178cf`, frozen at commit `b28451c45fe6a4814855a816f50e310b269f4b8e`. The source is `ekrombouts/fruta_records` revision `579141e3431c18a932fa3a0870e9f1c131f10367`; translation identifier `caresignal-agent-en-reviewed-v1` and annotation identifier `caresignal-two-agent-adjudicated-v1` identify the exact reviewed versions. See the [freeze manifest](../data/fruta_held_out_manifest.json) and [annotation ledger](../data/annotations/fruta_held_out_v1.json).

## First measurement, failures and follow-up

The initial planned `gemini-3.8-flash` attempt produced 14 provider failures before it was stopped, with a subsequent request interrupted. Those attempts remain in [initial-provider-failures.json](heldout-results/initial-provider-failures.json); they are not a completed 24-note accuracy run. Availability checks using disclosed development note `nn_1093` identified `gemini-3.1-flash-lite` before any successful held-out prediction. That runtime amendment changed the model/adapter while preserving the v1 prompt, notes, targets, translations, labels and evidence. The table above is the first completed paired measurement with the working model.

Current code uses prompt `walking-assistance-v2`, with fictional policy examples added after inspecting the first run's failure patterns. Any replay on these same 24 notes is a **post-hoc follow-up**, not independent held-out performance. The frozen annotations and first-run artifacts stay unchanged. Follow-up output belongs in a separate directory and must carry that scope explicitly:

```bash
uv run --env-file .env python -m caresignal.evaluation \
  --dataset data/fruta_held_out.jsonl \
  --mode compare --provider gemini --post-hoc \
  --output-dir artifacts/fruta-post-hoc
uv run python -m caresignal.reporting \
  --results artifacts/fruta-post-hoc/results.json \
  --output artifacts/fruta-post-hoc/report.md \
  --heading "CareSignal post-hoc replay on the original 24 notes"
```

The recorded follow-up belongs in [heldout-followup](heldout-followup/), separately from [heldout-results](heldout-results/). A new independent test of v2 needs untouched examples frozen before their predictions are inspected. Re-running the current default prompt cannot recreate the earlier v1 prediction sequence; the saved model/prompt metadata identifies what each historical run actually measured.

Render a report from the first saved results without making model calls:

```bash
uv run python -m caresignal.reporting \
  --results docs/heldout-results/results.json \
  --output artifacts/first-comparison-report.md
```

The reporting command validates stored counts and evidence flags. It does not repair or rerun predictions. Read the [first-run error analysis](heldout-results/error-analysis.md) alongside the exact rows; wrong labels and strict-span mismatches remain visible.

## Development checks and provider setup

The bundled [fictional development checks](../data/fictional_development.jsonl) are original English inputs that exercise the runner and workflow. They are neither Fruta nor held-out measurements. The separately frozen public development example `nn_1093` is in [fruta_development.jsonl](../data/fruta_development.jsonl); its pinned Dutch source and literal coding-agent English translation are documented in [fruta-source.md](fruta-source.md). That translation has not been independently reviewed. Provenance and recorded checks are listed in [source-manifest.json](../data/source-manifest.json).

Run the phrase baseline without credentials:

```bash
uv run python -m caresignal.evaluation --dataset data/fictional_development.jsonl --mode phrase --output-dir artifacts/development
uv run python -m caresignal.evaluation --dataset data/fruta_development.jsonl --mode phrase --output-dir artifacts/fruta-development
```

The historical real Gemini `nn_1093` call is preserved in [gemini-development-results](gemini-development-results/). `gemini-3.8-flash`, extractor `gemini-structured-v1`, prompt `walking-assistance-v1` returned `COMPLETE` / `HANDS_ON` with the exact two-sentence span: label/evidence/joint correct 1/1, errors 0. Its canonical input hash is `402f819b3b610fd760591c8dc876ff4cc4597c1c030e03c5b2923f2cad56c49e`. One disclosed development success is not an estimate of general accuracy or assurance of later model availability.

Current Gemini runs default to `gemini-3.1-flash-lite` (`GEMINI_MODEL` can override it); OpenAI defaults to `gpt-4.1-mini` (`OPENAI_MODEL` can override it). Set the selected provider's `GEMINI_API_KEY` or `OPENAI_API_KEY` in the process environment. Gemini keys are available from [Google AI Studio](https://aistudio.google.com/api-keys). The CLI does not load `.env` automatically; `uv run --env-file .env` explicitly loads a local ignored file. Never commit credentials.

For a new Gemini call on the disclosed development input:

```bash
uv run --env-file .env python -m caresignal.evaluation \
  --dataset data/fruta_development.jsonl --mode compare --provider gemini \
  --output-dir artifacts/fruta-development-current
```

`--mode live` runs one selected adapter; `--mode compare` runs phrase rules plus that adapter. `--provider gemini|openai` defaults to OpenAI and has no effect on API calls in offline `phrase` or `fixture` modes. `--mode fixture` runs a fixed-answer method and cannot generate held-out scores. OpenAI live inference remains unverified. A provider failure writes an error row and returns exit code 1; malformed frozen data fails before inference with exit code 2. Valid wrong predictions are measured outcomes and return exit code 0.

## Frozen input contract

Each JSONL record supplies `id`, `split` (`development` or `held_out`), `dataset_id`, `dataset_revision`, `translation_id`, `note`, `target`, `gold_label` and `gold_evidence`. The target specifies `resident_id`, `resident_name`, `context_key`, `observed_on` and optional `target_cue`. Each gold span contains an exact `quote` and may specify half-open Python `start` and `end` indices. A quote without offsets must occur exactly once. Invalid spans, blank provenance, unknown labels, duplicate example IDs and empty datasets are rejected before inference.

Held-out records additionally require `source_note_id`, a public HTTP(S) `source_url`, `original_note` and `annotation_id`. Source manifests describe actual dataset/translation versions and the translation and review procedure. Ambiguous Dutch guidance/support must not acquire physical contact in translation. The runner rejects fictional walkthrough records and disclosed public development example `nn_1093`, including its known original/translation fingerprints, as held-out inputs.

The first 24-note sample and annotations were frozen before prediction review. Predictions must not revise that frozen version. Any result-informed revision requires a new identifier and explicit follow-up scope. The public experiment measures extraction only because comparable usual-assistance pairs have not been established. Fictional two-resident and correction checks establish workflow behavior separately.

## Metrics and exports

Every returned span is validated against its exact note and revision. Exported method reports retain provider, model, extractor/prompt versions, dataset/translation revisions and the canonical input hash. Metrics are:

- Label agreement: exact match with the frozen five-class reference label.
- Exact-evidence agreement: the complete sorted set of `(start, end, quote)` spans matches the reference set. Partial overlaps and paraphrases fail; a defensible alternative span can fail this strict metric.
- Joint agreement: both label and exact evidence match.
- Error count: unavailable inference and invalid output remain in every metric denominator.

`results.json` retains exact counts, unrounded values and every prediction. `results.csv` includes note, target, reference/predicted evidence, correctness flags, errors and provenance. `summary.md` is generated from those results. The canonical input hash covers validated frozen records in order. A deterministic extractor over identical input yields identical artifacts; live provider responses are not guaranteed deterministic.

This project is a prototype and is not medical advice.
