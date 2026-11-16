# Reproducible extraction evaluation

The bundled `data/fictional_development.jsonl` contains original fictional English development checks. It exercises the evaluation runner and demo logic. It is not Fruta, held-out data, or a basis for public model-performance claims. The separately frozen public synthetic development example `nn_1093` is available in `data/fruta_development.jsonl`; its pinned Dutch source and coding-agent-authored literal English translation are documented in `docs/fruta-source.md`. That translation has not been independently reviewed. See `data/source-manifest.json` for provenance and the pending live/held-out checks.

Run the phrase baseline without credentials:

```bash
python -m caresignal.evaluation --dataset data/fictional_development.jsonl --mode phrase --output-dir artifacts/evaluation
```

Check the citable public development example with the phrase matcher:

```bash
python -m caresignal.evaluation --dataset data/fruta_development.jsonl --mode phrase --output-dir artifacts/fruta-development
```

The current development-only runs are recorded exactly in `docs/development-results/`. Those measured phrase results verify the runner and identify span mismatches; they do not claim held-out performance.

Run both methods on the same frozen, annotated public sample once available:

```bash
export OPENAI_MODEL=gpt-4.1-mini
python -m caresignal.evaluation --dataset data/fruta_held_out.jsonl --mode compare --output-dir artifacts/fruta-comparison
```

Set `OPENAI_API_KEY` in the process environment for live mode; do not commit it. `--mode live` and `--mode fixture` run one method each. The fixture is restricted to the fixed walkthrough, so its score on arbitrary examples measures fixture coverage rather than model quality. Live model availability must be verified for the account. A provider failure produces an error row and exit code 1; malformed frozen data fails before any inference with exit code 2. Valid wrong predictions remain ordinary measured outcomes and return exit code 0.

## Frozen input contract

Each JSONL record supplies `id`, `split` (`development` or `held_out`), `dataset_id`, `dataset_revision`, `translation_id`, `note`, `target`, `gold_label`, and `gold_evidence`. The target specifies `resident_id`, `resident_name`, `context_key`, `observed_on` and optional `target_cue`. Each gold span contains an exact `quote` and may specify half-open Python `start` and `end` indices. A quote without offsets must occur exactly once. Invalid gold spans, blank provenance, unknown labels, duplicate example IDs, and empty datasets are rejected before inference.

Held-out records additionally require `source_note_id`, a public HTTP(S) `source_url`, `original_note`, and `annotation_id`. Frozen dataset and translation IDs must name the actual versions used. Record the translation method, model/version, prompt or procedure, and review process in a source manifest. Do not resolve ambiguous Dutch wording by inventing a more specific English assistance level. The runner rejects fictional walkthrough records and disclosed public development example `nn_1093` (including known original/translation fingerprints) in the held-out split. Fixture answer lookups cannot be used to produce held-out scores.

Freeze the held-out sample and its annotations before reviewing model predictions. Keep `nn_1093` in the development split; its label is already disclosed in the brief. The public experiment measures extraction only because comparable usual-assistance pairs have not been verified. The fictional two-resident and correction checks establish workflow behavior separately.

## Metrics and exports

Both extractors receive the same full note and selected target through the package interface. Every returned span is validated against that exact note and revision. The runner reports:

- Label accuracy: exact agreement with the frozen five-class gold label.
- Exact-evidence accuracy: the complete sorted set of `(start, end, quote)` spans matches the gold set. Partial overlaps and paraphrases fail. A different but defensible span can fail this strict metric and should be described during error review.
- Joint accuracy: both label and exact evidence match.
- Error count: unavailable inference and invalid output remain in every metric denominator.

`results.json` preserves exact counts, unrounded metric values, dataset hash, dataset/translation revisions, extractor/prompt versions, selected model identifier, and every prediction. `results.csv` includes each note, target, gold and predicted evidence, correctness flags, error category and the same provenance. `summary.md` is generated from those exact results and can be copied into the README. The input hash uses canonical JSON of all validated frozen records in order. Repeated deterministic predictions yield identical artifacts.

Before submission, inspect at least one real held-out error. Report the original note ID, frozen English text, selected target, expected label/evidence, predicted label/evidence and an explanation. No real held-out error is claimed until that experiment has run. Live inference on Fruta `nn_1093` and held-out public scores are currently pending.

This project is a prototype and is not medical advice.
