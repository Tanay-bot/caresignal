# Prompt-v2 development replay

This is an error-informed replay of the same 24 notes used for the first frozen comparison. It is **not a new held-out estimate**. The notes, translations, targets, labels and gold spans retain canonical hash `a2d3a2e8dbe1d119c8cb02064963f585849ee2f01d95f2d640c7cbf426b178cf`.

The shared `walking-assistance-v2` prompt adds general fictional counterexamples about transfers, eating, device use, ability statements, guidance and safety supervision. The live adapter is `gemini-structured-v2`, using `gemini-3.1-flash-lite`.

| Recorded Gemini stage | Cases | Completed | Provider failures | Correct label | Correct label + exact evidence |
| --- | ---: | ---: | ---: | ---: | ---: |
| First replay attempt | 24 | 18 | 6 rate limits | 16/24 | 11/24 |
| One paced retry of unavailable cases only | 6 | 6 | 0 | 5/6 | 5/6 |
| Final replay, all cases retained | 24 | 24 | 0 unresolved | 21/24 (87.5%) | 16/24 (66.7%) |

There were 30 API attempts in total: the initial 24 plus one additional attempt for each of six unavailable cases. Retries were spaced at least five seconds apart. Predictions that had already completed were not resampled. The final denominator remains 24; the original six failures are preserved in the attempt history.

- [First-attempt results](first-attempt-results.json) preserve the six rate-limit outcomes.
- [Retry-only results](retry-results.json) preserve the six actual subsequent responses.
- [Retry ledger](retry-ledger.json) links each original failed row to its sole retry, with policy and file hashes.
- [Final JSON](results.json), [CSV](results.csv), and [summary](summary.md) contain the combined per-case outcomes.
- [Full replay report](report.md) shows all remaining errors, source text and exact evidence.

The three remaining label errors are `nl_0727` (guidance to sit back down attributed to walking), `na_1633` (a later garden visit attributed to the earlier aimless walk), and `nn_2108` (vague “follows well” interpreted as human walking help). Five additional correct labels use a different span set from the strict reference and therefore fail joint accuracy.

The first frozen prompt-v1 scores are unchanged in [heldout-results](../heldout-results/). The references were reviewed by coding agents, not human or clinical experts; the small lexical-stratified sample has only one or two examples of some specific classes. A new, uninspected sample and human review are needed for stronger generalization claims.

Regenerate this report offline without model calls:

```bash
uv run python -m caresignal.reporting --results docs/heldout-followup/results.json --output artifacts/replay-report.md
```
