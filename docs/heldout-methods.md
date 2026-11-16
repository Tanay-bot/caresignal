# Fruta 24-note evaluation protocol

This is a small, deliberately stratified check of extraction on public synthetic Dutch nursing-home notes. “Held out” means these notes were not used to implement or tune CareSignal before the first recorded evaluation. The upstream dataset split is named `train`; model-provider training exposure is unknown.

## Source and selection

The source is [Fruta Records](https://huggingface.co/datasets/ekrombouts/fruta_records), pinned to revision `579141e3431c18a932fa3a0870e9f1c131f10367`. The 14,533-row Parquet file has SHA-256 `205ae14313c65f57c03cc15a0fa16ac33aa827c5c242bfbc1215db621aac1c4f`. The dataset card describes entirely artificial notes and declares MIT metadata. No real patient records are included.

Before either extractor ran, records were assigned to mutually exclusive lexical strata in the order below. Within each stratum, records were sorted by `SHA256(seed + ':' + note_id)`, using seed `caresignal-fruta-heldout-v1-20261115`. The first fixed number of rows was selected. These strata are source-text screens, not gold labels.

| Source-text stratum | Eligible pool | Selected |
| --- | ---: | ---: |
| Walking plus physical/support cue | 35 | 6 |
| Walking plus independence cue | 42 | 4 |
| Walking plus guidance/safety cue | 105 | 6 |
| Other walking mention | 414 | 4 |
| Device/transfer mention without a walking keyword | 795 | 4 |

The already disclosed development example `nn_1093` was excluded by both ID and original-text fingerprint. Selected records contain no repeated note ID or exact duplicate text. Target residents, dates, canonical contexts and event cues were fixed before annotation. Some notes describe ability, another activity or no completed walk; those controls test abstention.

Reproduce source selection without making model calls:

```bash
uv run python scripts/select_fruta_sample.py --download --output artifacts/reselected-sources.jsonl
```

The output should exactly match [fruta_held_out_sources.jsonl](../data/fruta_held_out_sources.jsonl). [Target specifications](../data/fruta_held_out_targets.json) are curated separately and preserved verbatim.

## Translation and reference labels

Two coding agents independently labeled the original Dutch for the same targets, without reading extractor predictions or one another's labels. Agent A also produced literal English translations. After both independent label files were complete, agent B reviewed the translations; root applied its correction and adjudicated the label disagreement. These are separate assistant contexts from the same model family, not human or clinical-expert annotations.

The initial label agreement was **23/24**. The disagreement, `nb_0890`, describes independent walker use during a walk. Root chose `UNCLEAR` because independent device handling does not explicitly establish absence of human help. The translation retains the original distinction. A translation correction in `nm_0865` changes “Helped well” to “Cooperated well” to keep the resident as the person cooperating with morning care.

Ambiguous `begeleiding` and generic `ondersteuning` remain guidance/support in English. They do not acquire physical contact through translation. Two cases (`nm_1286`, `na_0689`) received `HANDS_ON` from both reviewers because support is directly linked to bodily instability or maintaining balance. That interpretation remains an annotation uncertainty recorded in the ledger.

| Frozen reference label | Count |
| --- | ---: |
| Independent | 1 |
| Staff beside or supervising | 1 |
| Hands-on help | 2 |
| Help documented, type unspecified | 6 |
| Unclear | 14 |

The translation identifier is `caresignal-agent-en-reviewed-v1`; the annotation identifier is `caresignal-two-agent-adjudicated-v1`. The [annotation ledger](../data/annotations/fruta_held_out_v1.json) preserves both independent decisions, rationale, Dutch evidence, final label and adjudication.

## Evidence policy and freeze

Gold evidence uses the minimal contiguous full sentence(s) needed to identify the event and supported help. Intervening text stays in a span when the walk and assistance are in separate sentences. An unclear result on a documented walk cites its walking/device sentence. When no completed target walk is documented, evidence may be empty. The strict metric compares the complete sorted set of `(start, end, quote)` spans; another defensible span can fail it.

The [freeze manifest](../data/fruta_held_out_manifest.json) records source selection, targets, annotation ledger, exact JSONL file and canonical dataset hashes, the pre-inference extractor-source hash and planned model/prompt versions. The dataset and its review were committed before evaluation. Predictions must not be used to revise this frozen version. Any changes informed by these results require a new version and a clearly labeled follow-up analysis.

The initial planned model, `gemini-3.8-flash`, returned no usable predictions: the serial attempt was stopped after 14 provider failures, with the 15th request interrupted. Those attempts remain in [initial-provider-failures.json](heldout-results/initial-provider-failures.json). Separate checks on disclosed development note `nn_1093` found `gemini-3.1-flash-lite` available. The runtime amendment selects that model with extractor `gemini-structured-v2` before any successful held-out prediction. It changes the default model, not the prompt, notes, targets, translations, labels, or evidence. The full comparison records the working model explicitly; the stopped infrastructure attempt is not silently treated as a completed 24-note accuracy run.

Run the paired comparison on identical full notes and targets:

```bash
uv run --env-file .env python -m caresignal.evaluation --dataset data/fruta_held_out.jsonl --mode compare --provider gemini --output-dir artifacts/fruta-held-out
uv run python -m caresignal.reporting --results artifacts/fruta-held-out/results.json --output artifacts/fruta-held-out/report.md
```

Every input remains in each denominator, including provider failures and invalid evidence. The comparison evaluates extraction only; public usual-assistance pairs were not established. The separate fictional workflow verifies resident-specific comparisons and corrections.

## Interpretation limits

This 24-note lexical challenge sample is not prevalence-weighted. Rare categories have only one or two examples, and some notes share synthetic residents/scenarios. Agent-reviewed translations and reference labels need human review before stronger accuracy claims. Results describe this frozen translated sample, not real clinical documentation or clinical validity.

This project is a prototype and is not medical advice.
