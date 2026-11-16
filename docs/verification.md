# Starter verification record

Verified on 2026-11-15 with Python 3.12.14 and dependencies frozen in `uv.lock`.

| Check | Result |
| --- | --- |
| `uv run pytest` | 132 passed, including 6 Streamlit AppTest flows |
| `uv run ruff check .` | Passed |
| `uv run ruff format --check .` | Passed |
| `uv build` | Source distribution and wheel built successfully |
| `uv run python -m caresignal.demo` | Same note produces Elena MORE_HELP / Ruth MATCHES; replacement becomes v2 UNCLEAR and retains v1 |
| Walkthrough notebook code cells | Executed against the real package; demo, correction and development evaluation completed |
| Streamlit server health | HTTP 200 on local port 8501 |
| Chromium browser, 1440 × 1050 | App rendered, resident switched to Ruth and matching card appeared; no page errors |
| Chromium browser, 390 × 844 | App rendered with stacked content, collapsed sidebar and no horizontal overflow |
| Concurrent replacement conflict | Latest source displayed; user's draft preserved; retry created version 3 |
| Fruta `nn_1093` development check | Exact sourced two-sentence HANDS_ON evidence passes fixture and phrase checks |

Tests cover immutable revisions and snapshots, workspace ownership, rollback, stale replacement conflicts, late inference after correction, historical baseline eligibility, invalid evidence, HTML escaping, target attribution, exact-output exports, failure denominators and prohibition of fixture/development held-out claims.

Recorded development phrase results and per-example evidence mismatches are in [development-results](development-results/). The public source and translation method are in [fruta-source.md](fruta-source.md). Neither development check is a held-out performance estimate.

At the initial starter verification, no API key was configured. OpenAI live inference remains pending: `gpt-4.1-mini` is the requested default, not a verified successful model call. The subsequent Gemini check is recorded below. Held-out dataset selection, translation review, independent gold annotations, model comparison and a real held-out error analysis remain pending.

The GitHub workflow runs checks on Python 3.11 and 3.12. The local results above are from Python 3.12; remote workflow outcomes are recorded separately by GitHub Actions.

## Gemini provider update

Added native Google Gen AI SDK support with a Live AI provider selector and evaluation `--provider gemini`. Both live adapters use the same full-note/target contract, five-label schema, prompt and exact evidence validator.

- Full local suite: **161 tests passed**, including provider routing for every app action, actual SDK response-object parsing with mocked transport, rejection of unsupported citations, blocked/truncated responses, sanitized provider failures and correction invalidation.
- Ruff lint/format checks and source/wheel builds passed.
- **Actual live check:** `gemini-3.8-flash` returned `HANDS_ON` on frozen Fruta development example `nn_1093`, with the complete exact two-sentence span. Label, evidence and joint checks each passed for this one disclosed development example. This is not a held-out estimate.
- Exact JSON/CSV and a generated summary are in [gemini-development-results](gemini-development-results/). No additional live request was used to generate the documentation.
- Credentials are read from the process environment. A local `.env` is excluded from Git and can be loaded explicitly with `uv run --env-file .env ...`.

The Google SDK is locked to version 3.3.0 in `uv.lock`. `GEMINI_MODEL` changes the requested model. At this stage, OpenAI inference and held-out results were pending; the subsequent completed experiment is recorded below.

## Completed prototype and experiment

- **231 local tests passed**, including 11 Streamlit flow tests, 38 saved-report integrity tests, 44 evaluation/pacing tests, frozen-data checks and full per-example retry provenance checks.
- Ruff lint and formatting checks passed. Source distribution and wheel builds passed.
- The complete notebook executed successfully: **9 code cells**, no live requests by default. It replays resident comparisons/corrections and reads the actual first-pass and follow-up artifacts.
- Chromium verified Elena/Ruth comparison switching and desktop/mobile layout. At 390px, content has no horizontal overflow. Source-note and baseline Markdown/HTML syntax remain literal in an independent browser check.
- The 24-note source sample and two-agent annotation review were committed before predictions in `b28451c`. Gold source/target/translation hashes remain unchanged.
- First complete comparison, prompt v1: phrase **14/24 labels, 8/24 joint**; Gemini Flash Lite **11/24 labels, 7/24 joint**. Each completed all 24 cases without API errors. All exact outcomes, confusion counts and real failures are preserved in [heldout-results](heldout-results/).
- The initial `gemini-3.8-flash` attempt returned 14 provider failures and was stopped with a 15th request in flight. It is recorded separately and is not presented as a completed 24-note accuracy result. `gemini-3.1-flash-lite` was selected on development-example availability before successful held-out predictions.
- Prompt v2 adds general fictional examples to address attribution errors. Its **post-hoc replay** of the same 24 notes ends at **21/24 labels, 16/24 joint**. Six initial rate limits were retried once, paced five seconds apart; original attempts and actual retry rows remain in [heldout-followup](heldout-followup/). This is not a new held-out estimate.
- The default provider model is now `gemini-3.1-flash-lite`, native extractor `gemini-structured-v2`, shared prompt `walking-assistance-v2`. Request pacing is configurable for batch evaluation; provider failures remain separate from completed Unclear predictions.

The reference labels were reviewed by coding agents, not human or clinical experts. Results describe a small, deliberately stratified synthetic sample. New uninspected data and human review are required for stronger revised-prompt generalization claims; that is a validation limitation, rather than an unfinished core app feature. OpenAI live account availability remains optional and unverified.

This project is a prototype and is not medical advice.
