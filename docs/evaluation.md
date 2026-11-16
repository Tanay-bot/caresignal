# Reproducible extraction evaluation

The bundled `data/fictional_development.jsonl` contains original fictional English development checks. It exercises the evaluation runner and demo logic. It is not Fruta, held-out data, or a basis for public model-performance claims. The separately frozen public synthetic development example `nn_1093` is available in `data/fruta_development.jsonl`; its pinned Dutch source and coding-agent-authored literal English translation are documented in `docs/fruta-source.md`. That translation has not been independently reviewed. See `data/source-manifest.json` for provenance, the completed Gemini development check and pending OpenAI/held-out checks.

Run the phrase baseline without credentials:

```bash
python -m caresignal.evaluation --dataset data/fictional_development.jsonl --mode phrase --output-dir artifacts/evaluation
```

Check the citable public development example with the phrase matcher:

```bash
python -m caresignal.evaluation --dataset data/fruta_development.jsonl --mode phrase --output-dir artifacts/fruta-development
```

The phrase development-only runs are recorded exactly in `docs/development-results/`. Those measured results verify the runner and identify span mismatches; they do not claim held-out performance.

A real Gemini API call has also been recorded in [gemini-development-results](gemini-development-results). `gemini-3.8-flash`, extractor `gemini-structured-v1`, prompt `walking-assistance-v1` returned `COMPLETE` / `HANDS_ON` for `nn_1093`, with the exact full two-sentence span (label/evidence/joint correct: 1/1; errors: 0). The frozen input hash is `402f819b3b610fd760591c8dc876ff4cc4597c1c030e03c5b2923f2cad56c49e`. It uses dataset revision `579141e3431c18a932fa3a0870e9f1c131f10367` and coding-agent-authored translation `caresignal-agent-en-literal-v1`, which has not been independently reviewed. This disclosed development check establishes one successful live path; it does not estimate held-out performance. OpenAI live inference remains pending.

Choose the live provider with `--provider gemini` or `--provider openai` (the default). For example, after setting `GEMINI_API_KEY`, run the phrase baseline and Gemini on the same disclosed development input:

```bash
python -m caresignal.evaluation --dataset data/fruta_development.jsonl --mode compare --provider gemini --output-dir artifacts/fruta-development-gemini
```

Run both methods on the same frozen, annotated public held-out sample once available:

```bash
export GEMINI_MODEL=gemini-3.8-flash
python -m caresignal.evaluation --dataset data/fruta_held_out.jsonl --mode compare --provider gemini --output-dir artifacts/fruta-comparison
```

Set the selected provider’s `GEMINI_API_KEY` or `OPENAI_API_KEY` in the process environment; do not commit it. Gemini requests `gemini-3.8-flash` by default, configurable with `GEMINI_MODEL`. OpenAI requests `gpt-4.1-mini`, configurable with `OPENAI_MODEL`. Obtain Gemini keys from [Google AI Studio](https://aistudio.google.com/api-keys). The CLI does not load `.env` automatically. If keys are stored in a local ignored `.env`, explicitly prefix the command with `uv run --env-file .env python -m caresignal.evaluation ...` instead of `python -m caresignal.evaluation ...`. `--mode live` runs the selected native SDK adapter, and `--mode compare` runs the phrase baseline plus that adapter. Run separate output directories to compare both providers on the same frozen dataset hash. `--provider` does not make API calls in offline `phrase` or `fixture` mode. `--mode fixture` runs one fixed-answer method. The fixture is restricted to the fixed walkthrough, so its score on arbitrary examples measures fixture coverage rather than model quality. Live model availability must be verified for the account. A provider failure produces an error row and exit code 1; malformed frozen data fails before any inference with exit code 2. Valid wrong predictions remain ordinary measured outcomes and return exit code 0.

## Frozen input contract

Each JSONL record supplies `id`, `split` (`development` or `held_out`), `dataset_id`, `dataset_revision`, `translation_id`, `note`, `target`, `gold_label`, and `gold_evidence`. The target specifies `resident_id`, `resident_name`, `context_key`, `observed_on` and optional `target_cue`. Each gold span contains an exact `quote` and may specify half-open Python `start` and `end` indices. A quote without offsets must occur exactly once. Invalid gold spans, blank provenance, unknown labels, duplicate example IDs, and empty datasets are rejected before inference.

Held-out records additionally require `source_note_id`, a public HTTP(S) `source_url`, `original_note`, and `annotation_id`. Frozen dataset and translation IDs must name the actual versions used. Record the translation method, model/version, prompt or procedure, and review process in a source manifest. Do not resolve ambiguous Dutch wording by inventing a more specific English assistance level. The runner rejects fictional walkthrough records and disclosed public development example `nn_1093` (including known original/translation fingerprints) in the held-out split. Fixture answer lookups cannot be used to produce held-out scores.

Freeze the held-out sample and its annotations before reviewing model predictions. Keep `nn_1093` in the development split; its label is already disclosed in the brief. The public experiment measures extraction only because comparable usual-assistance pairs have not been verified. The fictional two-resident and correction checks establish workflow behavior separately.

## Metrics and exports

The phrase baseline and selected live adapter receive the same full note and selected target through the package interface. Gemini uses mode `gemini` and version `gemini-structured-v1`; OpenAI retains mode `live` and version `openai-structured-v1`. Their shared prompt policy is `walking-assistance-v1`. Model, provider-specific extractor mode/version, prompt version and frozen input hash remain in every exported method report. Every returned span is validated against that exact note and revision. The runner reports:

- Label accuracy: exact agreement with the frozen five-class gold label.
- Exact-evidence accuracy: the complete sorted set of `(start, end, quote)` spans matches the gold set. Partial overlaps and paraphrases fail. A different but defensible span can fail this strict metric and should be described during error review.
- Joint accuracy: both label and exact evidence match.
- Error count: unavailable inference and invalid output remain in every metric denominator.

`results.json` preserves exact counts, unrounded metric values, dataset hash, dataset/translation revisions, extractor/prompt versions, selected model identifier, and every prediction. `results.csv` includes each note, target, gold and predicted evidence, correctness flags, error category and the same provenance. `summary.md` is generated from those exact results and can be copied into the README. The input hash uses canonical JSON of all validated frozen records in order. Repeated deterministic predictions yield identical artifacts.

Before submission, inspect at least one real held-out error. Report the original note ID, frozen English text, selected target, expected label/evidence, predicted label/evidence and an explanation. No real held-out error is claimed until that experiment has run. The recorded Gemini `nn_1093` development check is available above. OpenAI live inference and all held-out public scores remain pending. Mocked transport tests alone do not establish live model availability or accuracy.

This project is a prototype and is not medical advice.
