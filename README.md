# CareSignal

CareSignal highlights what a shift note documents about human help for a selected walk, then compares that evidence with a staff-confirmed description of the resident’s usual help when one is available.

This project is a prototype and is not medical advice.

![CareSignal fixture demo showing the handoff result and exact source evidence](docs/screenshots/desktop.png)

## Run it

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/Tanay-bot/caresignal.git
cd caresignal
uv sync --locked --extra dev
uv run streamlit run app.py
```

Open http://localhost:8501. **Fixture demo** runs without API credentials. With an existing Python environment, `python -m pip install -e '.[dev]'` and `streamlit run app.py` also work; `uv.lock` records the exact verified dependency set.

For a quick offline walkthrough without a browser:

```bash
uv run python -m caresignal.demo
```

## Try the handoff

1. Click **Load demo** and select **Elena**. The note documents an aide beside her on the breakfast walk; her confirmed usual level is independent, so the card shows **More help than usual**.
2. Select **Ruth**. The same note now shows **Matches usual routine** because her confirmed baseline is supervision for that walk.
3. Return to Elena, open **Attach replacement**, click **Use demo replacement**, then submit. The new active note leaves human help unspecified, so the prior flag clears. **Note history** retains the original as corrected version 1.
4. Load **Fruta example** to inspect real public synthetic development note `nn_1093`, its frozen English translation, exact two-sentence evidence and Dutch original. The preset uses the selected extraction mode and identifies fixture output explicitly.

The app supports complete custom fictional notes, selected dates and walk contexts, explicit usual-assistance confirmation, exact evidence highlights, immutable correction history and retryable analysis failures. It reports five documentation labels: Independent, Staff beside or supervising, Hands-on help, Help documented/type unspecified and Unclear.

Each browser session has an isolated fictional demo workspace in local SQLite. A new session starts a new workspace. Set `CARESIGNAL_DATA_DIR` to choose the storage directory; the default is the system temporary directory under `caresignal/`. **Load demo** resets only the current workspace. The database is excluded from Git.

## Enable Live AI

Export `OPENAI_API_KEY` in the shell that starts Streamlit, optionally set `OPENAI_MODEL`, then select **Live AI**. The default requested model is `gpt-4.1-mini`; account availability has not been verified. `.env.example` documents the environment variables; the app does not automatically load `.env` files.

The OpenAI adapter uses Pydantic structured output and checks exact evidence locally. Every result records the requested model, extractor/prompt versions and input hash. Missing credentials, provider errors and invalid citations produce an unavailable card instead of a guessed finding. **Phrase matcher** is a separate, transparent baseline. **Fixture demo** supports only frozen walkthrough inputs and clearly explains unsupported custom input.

**Live inference is pending:** no model credentials were available during this build. The Fruta hands-on check passed through the fixture and phrase matcher; this is not a live model result.

## Verify and evaluate

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run python -m caresignal.evaluation --dataset data/fictional_development.jsonl --mode phrase --output-dir artifacts/development
uv run python -m caresignal.evaluation --dataset data/fruta_development.jsonl --mode phrase --output-dir artifacts/fruta-development
```

The runner writes per-example JSON/CSV and a generated Markdown summary, including exact counts, source/translation revisions, dataset hash, prompt/extractor versions and model identifier. Label, exact span-set evidence and joint accuracy include errors in the denominator. The notebook [01_walkthrough.ipynb](notebooks/01_walkthrough.ipynb) calls the same package functions as the app.

Recorded **development-only phrase checks** are in [docs/development-results](docs/development-results). These small examples check behavior and reveal strict evidence mismatches; they do not estimate generalization or AI performance.

<!-- BEGIN DEVELOPMENT RESULTS -->
| Mode | Model | Scope | N | Label | Exact evidence | Joint | Errors |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| phrase | none | fictional_development | 7 | 7/7 (100.0%) | 5/7 (71.4%) | 5/7 (71.4%) | 0 |
| phrase | none | public_development | 1 | 1/1 (100.0%) | 1/1 (100.0%) | 1/1 (100.0%) | 0 |
<!-- END DEVELOPMENT RESULTS -->

**Held-out Fruta evaluation is pending.** Freeze a translated, independently annotated held-out sample before reviewing predictions. `nn_1093` is a disclosed development example and cannot be used as held-out data. Fixture mode cannot score held-out data. Once the sample and model credentials are available, `--mode compare` runs the phrase matcher and live model on identical notes and targets. See [evaluation.md](docs/evaluation.md) for the input contract and reporting procedure.

## Project map

| Location | Purpose |
| --- | --- |
| `app.py` | Streamlit handoff screen |
| `caresignal/models.py` | Frozen contracts, labels and context catalog |
| `caresignal/evidence.py`, `comparison.py` | Exact citations, eligibility checks and deterministic comparisons |
| `caresignal/repository.py`, `service.py` | Workspace-scoped SQLite, baseline snapshots and atomic replacements |
| `caresignal/extractors.py` | Fixture, phrase and replaceable OpenAI adapters |
| `caresignal/evaluation.py` | Frozen-data evaluation and reproducible exports |
| `data/` | Fictional development checks and sourced Fruta development example |
| `tests/` | Domain, service, extraction, evaluation and Streamlit flow checks |
| `.github/workflows/ci.yml` | Python 3.11/3.12 verification |

Read the [original brief](docs/project-brief.txt), [architecture](docs/architecture.md), [demo script](docs/demo-script.md), [prompt policy](docs/prompt.md), [Fruta provenance](docs/fruta-source.md) and [verification record](docs/verification.md).

The source Fruta dataset is public synthetic Dutch documentation, pinned to revision `579141e3431c18a932fa3a0870e9f1c131f10367`. The included English translation was authored by the coding agent and has not been independently reviewed. Demo residents and walkthrough notes are fictional. Clinical interpretation, urgency, fall-risk scoring, treatment, production patient records and clinical-system integration remain outside the prototype scope.
