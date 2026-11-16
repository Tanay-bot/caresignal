# CareSignal

CareSignal highlights what a shift note documents about human help for a selected walk, then compares that evidence with a staff-confirmed description of the resident’s usual help when one is available.

This project is a prototype and is not medical advice.

![CareSignal handoff result and exact source evidence](docs/screenshots/desktop.png)

## Run the prototype

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/Tanay-bot/caresignal.git
cd caresignal
uv sync --locked --extra dev
uv run streamlit run app.py
```

Open http://localhost:8501. **Fixture demo** works without credentials. With an existing Python environment, `python -m pip install -e '.[dev]'` and `streamlit run app.py` also work; `uv.lock` records the verified dependencies.

For an offline command-line replay:

```bash
uv run python -m caresignal.demo
```

## Try the handoff

1. Select **Elena**. The note documents an aide beside her on the breakfast walk. Her confirmed usual level is independent, so the card shows **More help than usual**.
2. Switch to **Ruth**. The same note shows **Matches usual routine** because her confirmed baseline is supervision for that walk.
3. Return to Elena, open **Attach replacement**, choose **Use demo replacement**, then submit. Version 2 becomes active and the prior flag clears. **Note history** preserves corrected version 1.
4. Open **Set usual assistance** to review and explicitly confirm both a specific level and its source description. This recomputes the card without a model call.
5. Load **Fruta example** to inspect public synthetic development note `nn_1093`, its frozen English translation and Dutch original. It uses the selected extraction method. Fixture results are explicitly identified.

The app supports complete custom fictional notes, selected dates and walking contexts, five assistance labels, exact evidence highlights, immutable correction history and retries. Active notes and baseline descriptions display literally, including Markdown and HTML characters. Changing methods identifies the method that produced the current result and offers reanalysis.

Each browser session receives an isolated fictional workspace in local SQLite. A new session starts a new workspace. **Load demo** resets only the current workspace. Set `CARESIGNAL_DATA_DIR` to choose the storage directory; its default is the system temporary directory under `caresignal/`. Databases and credentials are excluded from Git.

## Enable Gemini or OpenAI

| Provider | Key | Optional model setting | Current default |
| --- | --- | --- | --- |
| Gemini | `GEMINI_API_KEY` | `GEMINI_MODEL` | `gemini-3.1-flash-lite` |
| OpenAI | `OPENAI_API_KEY` | `OPENAI_MODEL` | `gpt-4.1-mini` |

Create a Gemini key in [Google AI Studio](https://aistudio.google.com/api-keys). Copy `.env.example` to a local `.env`, fill in your selected provider's key, then start with explicit environment loading:

```bash
uv run --env-file .env streamlit run app.py
```

Select **Live AI → AI provider → Gemini**. Exporting the variables in your shell also works. The app itself does not automatically read `.env`. OpenAI remains selectable; its live account availability has not been verified.

Both native SDK adapters use the same full-note/target contract, structured five-label schema, shared prompt and local evidence validation. Exact quotes must resolve to the active note revision. Baseline comparisons are deterministic code. Provider errors, invalid output and rate limits are separate from completed **Unclear** findings.

The historical `gemini-3.8-flash` development check succeeded once, but later generation requests timed out. The default changed to the available `gemini-3.1-flash-lite` before successful predictions on the frozen 24-note sample. [The stopped provider attempt](docs/heldout-results/initial-provider-failures.json) is retained.

## Measured extraction

The source is public synthetic Fruta data, pinned to revision `579141e3431c18a932fa3a0870e9f1c131f10367`. The 24-note sample, selected targets, translations and references were frozen in commit `b28451c` before extraction. Two coding agents independently reviewed labels (23/24 initial agreement); these are **not human or clinical-expert gold labels**. See the [protocol and limitations](docs/heldout-methods.md) and [annotation ledger](data/annotations/fruta_held_out_v1.json).

### First frozen comparison

<!-- BEGIN HELDOUT RESULTS -->

| Mode | Model | Scope | N | Label | Exact evidence | Joint | Errors |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| phrase | none | held_out_public | 24 | 14/24 (58.3%) | 12/24 (50.0%) | 8/24 (33.3%) | 0 |
| gemini | gemini-3.1-flash-lite | held_out_public | 24 | 11/24 (45.8%) | 14/24 (58.3%) | 7/24 (29.2%) | 0 |

<!-- END HELDOUT RESULTS -->

Gemini did not outperform the phrase matcher in this first run. The phrase matcher's 14/24 label score also only ties an always-**Unclear** label baseline, since 14 references are Unclear. The exact evidence metric compares complete span sets; a different defensible excerpt can fail it. These small, lexical-stratified results do not estimate real-world clinical accuracy.

The [full first-pass report](docs/heldout-results/report.md) includes every error, confusion tables and provenance. The [focused error analysis](docs/heldout-results/error-analysis.md) shows real failures involving help with dressing, general walking ability, independent eating, ambiguous guidance and missed safety supervision. The original predictions and scores remain unchanged.

### Prompt-v2 development replay

General fictional counterexamples were added to clarify event attribution. Reusing the same 24 notes after inspecting errors is a **post-hoc replay**, not a new held-out accuracy estimate. References and translations were not changed.

<!-- BEGIN FOLLOWUP RESULTS -->

| Mode | Model | Scope | N | Label | Exact evidence | Joint | Errors |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| phrase | none | post_hoc_replay | 24 | 14/24 (58.3%) | 12/24 (50.0%) | 8/24 (33.3%) | 0 |
| gemini | gemini-3.1-flash-lite | post_hoc_replay | 24 | 21/24 (87.5%) | 16/24 (66.7%) | 16/24 (66.7%) | 0 |

<!-- END FOLLOWUP RESULTS -->

The follow-up preserves the original rate-limited attempt, bounded retries and full 24-example denominator. See [its report and attempt history](docs/heldout-followup/). A newly frozen, uninspected sample is needed to estimate how the revised prompt generalizes.

## Verify and reproduce

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv build

# Offline: regenerate a report from the recorded actual predictions.
uv run python -m caresignal.reporting --results docs/heldout-results/results.json --output artifacts/first-pass-report.md

# Optional live development replay; uses provider quota.
uv run --env-file .env python -m caresignal.evaluation --dataset data/fruta_held_out.jsonl --mode compare --provider gemini --post-hoc --min-request-interval 5 --output-dir artifacts/fruta-replay
```

The evaluation runner writes per-example JSON/CSV and a generated Markdown table. Results retain dataset/translation hashes, extractor/prompt versions, model identifier and all failures in the denominator. `--min-request-interval` paces live calls only; offline fixture and phrase modes do not wait. The report generator verifies stored metrics, labels and exact evidence before rendering them.

The [notebook](notebooks/01_walkthrough.ipynb) replays the application workflow and inspects saved first-pass and follow-up results without making API calls. Historical fictional/development checks remain in [development-results](docs/development-results/) and [gemini-development-results](docs/gemini-development-results/).

## Project map

| Location | Purpose |
| --- | --- |
| `app.py` | Streamlit handoff screen |
| `caresignal/models.py`, `evidence.py`, `comparison.py` | Frozen contracts, exact citations and eligibility/comparison rules |
| `caresignal/repository.py`, `service.py` | Workspace-scoped SQLite, immutable snapshots and atomic replacements |
| `caresignal/extractors.py` | Fixture, phrase, Gemini and OpenAI adapters |
| `caresignal/evaluation.py`, `reporting.py` | Frozen evaluation, pacing, exact exports and error reports |
| `data/fruta_held_out*`, `data/annotations/` | Frozen sources, targets, translations, references and review history |
| `scripts/select_fruta_sample.py` | Reproducible pre-inference source selection |
| `tests/`, `.github/workflows/ci.yml` | Verification and Python 3.11/3.12 CI |

Read the [original brief](docs/project-brief.txt), [architecture](docs/architecture.md), [demo script](docs/demo-script.md), [prompt policy](docs/prompt.md), [evaluation procedure](docs/evaluation.md), [Fruta provenance](docs/fruta-source.md), and [verification record](docs/verification.md).

Demo residents and walkthrough notes are fictional. The public experiment measures extraction; it does not establish resident baselines. Clinical interpretation, urgency, fall-risk scoring, treatment, production patient records and clinical-system integration remain outside this prototype.
