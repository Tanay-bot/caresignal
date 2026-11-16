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

Live OpenAI inference remains pending because no API key was configured. `gpt-4.1-mini` is the requested default, not a verified successful model call. Held-out dataset selection, translation review, independent gold annotations, model comparison and a real held-out error analysis remain pending.

The GitHub workflow runs checks on Python 3.11 and 3.12. The local results above are from Python 3.12; remote workflow outcomes are recorded separately by GitHub Actions.

This project is a prototype and is not medical advice.
