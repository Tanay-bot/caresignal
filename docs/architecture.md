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
- `evaluation.py` reads frozen examples and writes source-traceable per-example and summary artifacts. `reporting.py` validates stored result counts and renders readable reports without inference.

## Live providers and version history

`GeminiExtractor` uses the Google Gen AI Python SDK and `GEMINI_API_KEY`. Its requested model defaults to `gemini-3.1-flash-lite`, configurable with `GEMINI_MODEL`. `OpenAIExtractor` keeps the OpenAI SDK path with `OPENAI_API_KEY` and optional `OPENAI_MODEL` (default `gpt-4.1-mini`). Both use the shared full-note/target prompt and local exact-evidence functions. Provider selection does not change comparison or revision rules.

Current runs identify Gemini as mode `gemini`, extractor `gemini-structured-v2`, and OpenAI as mode `live`, extractor `openai-structured-v1`. Both currently use prompt `walking-assistance-v2`. Runs retain the requested model, prompt version, input hash and source revision. API keys stay in the process environment and are not stored in the evidence history. The app does not load `.env` automatically. The evaluation CLI uses `--provider gemini|openai` for live/compare runs and defaults to OpenAI; offline modes do not construct live adapters. Provider errors remain separate from completed predictions.

The historical `gemini-3.8-flash` / `gemini-structured-v1` / `walking-assistance-v1` adapter completed one [recorded live development check](gemini-development-results/results.json) on `nn_1093`. A subsequent 24-note attempt using that model stopped after 14 provider failures; the [failed attempts](heldout-results/initial-provider-failures.json) remain archived. Availability checks on the disclosed development input identified `gemini-3.1-flash-lite` before any successful held-out prediction, and the runtime amendment changed the model/adapter without changing the frozen dataset or v1 prompt.

The [first completed paired comparison](heldout-results/results.json) used `gemini-3.1-flash-lite`, `gemini-structured-v2`, and prompt `walking-assistance-v1`. Both methods completed all 24 examples. Gemini matched 11/24 reference labels and 7/24 exact label-plus-evidence pairs; phrase rules matched 14/24 and 8/24. These measurements remain intact. The current v2 prompt adds fictional counterexamples after review of that result; a replay of the same sample is [post-hoc follow-up](heldout-followup/), not a new independent held-out experiment. OpenAI live availability remains unverified.

## Corrections and concurrency

A replacement transaction checks the expected active revision, inserts a full replacement and moves the case pointer. Both writes commit together or roll back. The model call begins after commit. Immediately after commit, the previous finding is ineligible, even if the replacement is unclear or the model is unavailable.

An extraction is always saved against the revision it requested. A correction arriving during inference cannot redirect that old run to the new source. The handoff view reads the active pointer, note, run and applicable baseline inside one read transaction.

Baseline confirmations preserve history. Selection uses the latest confirmation for the same resident/context on or before the observation date, ordered by confirmation date and save time. Updating a baseline recalculates the card without an additional model call.

## Persistence

Each browser session receives a random workspace ID. It shares a local SQLite file with other sessions, while repository operations enforce workspace ownership. A browser session does not restore a prior session’s workspace. `Load demo` resets only the current workspace.

The default data directory is the operating system’s temporary directory under `caresignal/`. Set `CARESIGNAL_DATA_DIR` for a chosen local directory. The database, secrets and generated runtime artifacts are excluded from Git. Selected evaluation artifacts are intentionally recorded under `docs/` for review.

## Provenance and limits

Fixture outputs are predetermined walkthrough results and are visibly identified as fixtures. The phrase matcher is a small transparent baseline. Structured output must pass exact-evidence validation, but a valid quotation does not prove that the model selected the right event or label. Provider failures and invalid citations are unavailable/invalid runs, distinct from completed `UNCLEAR` predictions.

Fruta `nn_1093` is a disclosed development example with a pinned source and coding-agent translation. The separate 24-note sample was frozen at commit `b28451c45fe6a4814855a816f50e310b269f4b8e` before its first successful predictions. Its translations and reference labels were reviewed by two assistant contexts, not human annotators. The small lexical challenge sample is not prevalence-weighted and does not establish general extraction quality or clinical validity. See [heldout-methods.md](heldout-methods.md) for the review, uncertainty ledger and source hashes.

This project is a prototype and is not medical advice.
