# Implementation notes

The app reviews documentation about one selected walk. It does not derive a clinical score. The original product and engineering brief is preserved in [project-brief.txt](project-brief.txt).

## Data path

`Streamlit → CareSignalService → Repository / Extractor → validated ExtractionRun → build_comparison`

- `models.py` defines frozen Pydantic contracts, the context catalog and five assistance labels.
- `evidence.py` resolves exact source quotes to half-open Python string indices and escapes text before highlighting it. Citation validation checks the source identity and exact characters; semantic correctness still requires evaluation.
- `comparison.py` checks the active revision, completed result, specific help levels, resident, canonical context and confirmation date before comparing ranks. The rank is a documentation rule without clinical meaning.
- `repository.py` uses parameterized SQLite queries, foreign keys on every connection and workspace-scoped access. Composite foreign keys bind active and superseded revisions to the same case. Revisions, baseline confirmations and extraction runs are immutable snapshots.
- `service.py` owns analysis, usual-assistance confirmation, replacements and the current handoff view. The app and notebook use these operations.
- `extractors.py` provides fixture, phrase and native structured Gemini/OpenAI implementations behind the same full-note/target interface.
- `evaluation.py` reads frozen examples and writes source-traceable per-example and summary artifacts.

## Live providers

`GeminiExtractor` uses the Google Gen AI Python SDK and `GEMINI_API_KEY`; its requested model defaults to `gemini-3.8-flash` and can be changed with `GEMINI_MODEL`. `OpenAIExtractor` keeps the OpenAI SDK path with `OPENAI_API_KEY` and optional `OPENAI_MODEL` (default `gpt-4.1-mini`). Both use the shared full-note/target prompt and validate exact quotes with the same local evidence functions. Provider selection does not change baseline comparison or revision rules.

Runs distinguish Gemini's `gemini` mode / `gemini-structured-v1` version from OpenAI's existing `live` mode / `openai-structured-v1` version, and retain the requested model, shared prompt version and input hash. API keys stay in the process environment and are not stored in the evidence history. The app does not load `.env` automatically. The evaluation CLI uses `--provider gemini|openai` for live/compare runs and defaults to OpenAI for backward compatibility; offline modes do not construct live adapters. Provider errors stay separate from completed predictions.

Gemini `gemini-3.8-flash` completed one recorded live development check on disclosed public synthetic note `nn_1093`, returning Hands-on help with exact evidence; see [the result](gemini-development-results/results.json). OpenAI live availability and all held-out performance remain pending. SDK mocks verify transport and validation behavior, while that single development result does not estimate general extraction quality.

## Corrections and concurrency

A replacement transaction checks the expected active revision, inserts a full replacement and moves the case pointer. Both writes commit together or roll back. The model call begins after commit. Immediately after commit, the previous finding is ineligible, even if the replacement is unclear or the model is unavailable.

An extraction is always saved against the revision it requested. A correction arriving during inference cannot redirect that old run to the new source. The handoff view reads the active pointer, note, run and applicable baseline inside one read transaction.

Baseline confirmations preserve history. Selection uses the latest confirmation for the same resident/context on or before the observation date, ordered by confirmation date and save time. Updating a baseline recalculates the card without an additional model call.

## Persistence

Each browser session receives a random workspace ID. It shares a local SQLite file with other sessions, while repository operations enforce workspace ownership. A browser session does not restore a prior session’s workspace. `Load demo` resets only the current workspace.

The default data directory is the operating system’s temporary directory under `caresignal/`. Set `CARESIGNAL_DATA_DIR` for a chosen local directory. The database, secrets and generated artifacts are excluded from Git.

## Provenance and limits

Fixture results are predetermined walkthrough results and are visibly identified as fixtures. The phrase matcher is a conservative baseline. Structured model output must pass the same exact-evidence validation as the other methods. Provider failures, refusal and invalid citations are unavailable/invalid runs, separate from a completed `UNCLEAR` prediction.

The included public Fruta note is a development example with a pinned source revision and a coding-agent translation. It is not a held-out experiment. The recorded Gemini development check is one successful path, using a coding-agent translation that has not been independently reviewed. Held-out performance must be measured before claiming general extraction quality.

This project is a prototype and is not medical advice.
