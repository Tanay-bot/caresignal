# Extraction methods

The adapter contract accepts the complete note, one `Target`, and the exact source revision ID. It returns `ExtractionResult` with validated `EvidenceSpan` values. The UI, notebook and evaluation runner share this contract.

## Live structured extraction

The native Gemini and OpenAI adapters share `SYSTEM_PROMPT` (currently `walking-assistance-v2`) in [extractors.py](../caresignal/extractors.py), the full-note/target input contract, five-label output schema and local exact-evidence validator.

| Adapter | Mode | Extractor version | Current default model | Environment variables |
| --- | --- | --- | --- | --- |
| `GeminiExtractor` | `gemini` | `gemini-structured-v2` | `gemini-3.1-flash-lite` | `GEMINI_API_KEY`, optional `GEMINI_MODEL` |
| `OpenAIExtractor` | `live` | `openai-structured-v1` | `gpt-4.1-mini` | `OPENAI_API_KEY`, optional `OPENAI_MODEL` |

Gemini uses the Google Gen AI Python SDK's native `client.models.generate_content` structured JSON schema support; see the [official Pydantic schema documentation](https://github.com/googleapis/python-genai#pydantic-model-schema-support). Obtain a Gemini API key from [Google AI Studio](https://aistudio.google.com/api-keys). OpenAI uses `client.responses.parse` with a Pydantic response schema; see the [official structured outputs guide](https://developers.openai.com/api/docs/guides/structured-outputs). Gemini's configured model completed the recorded 24-note first comparison. OpenAI live availability remains unverified. Every stored run records the requested model identifier; availability can change.

Input consists of a system policy and a JSON user payload containing the complete original note and target. The policy treats note text and target cues as source data, including embedded instructions. Output includes one of five labels, a reason code, reason, exact source quotes and optional device. The application resolves unique quotes to Python string offsets and validates the source revision and exact substring. Adjacent sentences can form one contiguous quote.

The policy separates actual walking help from transfers, device setup, other people, other times, future plans, conditional assistance and declined help. It preserves uncertainty. Code compares confirmed baselines; the model does not make that comparison or interpret clinical risk. A valid citation establishes that quoted words occur in the source; it does not prove that the prediction interprets them correctly.

Malformed output, absent structured predictions and unresolved evidence are invalid analyses. Missing credentials, timeouts, rate limits and provider failures are unavailable analyses. Neither becomes a completed `UNCLEAR` prediction. Provider exception details are not exposed as card copy because they may contain submitted text or sensitive headers.

## Prompt and measured-run history

- **`walking-assistance-v1`** was used for the historical successful `gemini-3.8-flash` / `gemini-structured-v1` development check on disclosed Fruta `nn_1093`. The [stored result](gemini-development-results/results.json) returned `HANDS_ON` with the exact two-sentence evidence. This single example is not a performance estimate.
- **`walking-assistance-v1`** was also used for the [first completed 24-note comparison](heldout-results/results.json), with `gemini-3.1-flash-lite` / `gemini-structured-v2`. The working model was selected from availability checks on the disclosed development input before any successful held-out prediction. The earlier 14 provider failures are preserved [separately](heldout-results/initial-provider-failures.json). First-run Gemini accuracy was 11/24 labels and 7/24 exact label-plus-evidence pairs, with no API errors.
- **`walking-assistance-v2`** retains the task, taxonomy and output schema while adding fictional policy counterexamples. They clarify activity attribution, independently handling a device versus walking unaided, general ability versus a completed event, unspecified guidance/support, safety supervision in later sentences and explicit physical support. These changes followed inspection of the first comparison's failure patterns. Replaying those same 24 notes is a **post-hoc follow-up**, even though the examples added to the prompt are fictional. Use `--post-hoc` and a separate output directory; preserve the first-run results unchanged.

The [frozen methods](heldout-methods.md) and [evaluation guide](evaluation.md) identify input hashes, annotations, model changes and the distinction between the first measurement and later replays. The public `nn_1093` source and its literal agent-authored translation are documented in [fruta-source.md](fruta-source.md). The separate fictional walking-attempt fixture is not represented as that public note.

## Fixture demo

`FixtureExtractor` version `fictional-walkthrough-v1` accepts exact frozen fictional note strings, their date (`2026-01-15`), canonical context and supported optional cue. It supports the breakfast walkthrough, its walker-only correction and the fictional adjacent-sentence walking attempt. It also supports the exact frozen public Fruta `nn_1093` development text only with its source resident display name, walking-attempt context, observation date and target cue. That result is explicitly marked as a fixed development expectation rather than live inference. Elena and Ruth use the same pronoun-based note with different confirmed baselines.

Other inputs yield an explanatory `UNCLEAR` fixture result inviting selection of Live AI or the phrase baseline. Fixture output demonstrates the workflow; it is not a model experiment and cannot produce held-out scores.

## Phrase baseline

`PhraseMatcher` version `phrase-v1`, prompt/rules version `rules-v1`, uses a conservative set of sentence and phrase rules. It anchors the canonical walking context, avoids explicit other residents and past/future distractors, distinguishes outbound and return routes, and can include a physical-support continuation sentence. It keeps devices separate and abstains for unresolved candidate events. Explicit ISO calendar dates on a walking sentence or a proposed support continuation must match the selected observation date. Mere staff presence does not itself trigger supervision; purposeful accompaniment or explicit support/safety wording is required.

This baseline has limited language coverage. The first frozen 24-note comparison measured 14/24 labels and 8/24 exact label-plus-evidence pairs, with no API errors. It often abstains when its phrases cannot bind the selected event, and it can fail the exact-evidence metric despite a matching label. The [stored per-example rows](heldout-results/results.json) retain those failures.

The earlier fictional development run has two exact-evidence mismatches despite matching all seven labels: the replacement case returns no span rather than the annotated walker sentence, and the transfer-distractor case returns the walker sentence rather than an empty span. See [the development rows](development-results/results.json). Development checks and mocked tests remain distinct from the first public sample measurement.

Known limits include non-ISO date wording, dates established in earlier paragraphs, unrestricted name/coreference resolution and complex free-text target cues. The small stratified Fruta sample uses assistant-reviewed translations and reference labels; stronger claims need an untouched evaluation sample and human review.
