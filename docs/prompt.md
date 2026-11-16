# Extraction methods

The adapter contract accepts the complete note, one `Target`, and the exact source revision ID. It returns `ExtractionResult` with validated `EvidenceSpan` values. The UI, notebook, and evaluation runner share this contract.

## Live structured extraction

- Adapter: `OpenAIExtractor`, version `openai-structured-v1`.
- Prompt: `walking-assistance-v1`; the complete text is the `SYSTEM_PROMPT` constant in [extractors.py](../caresignal/extractors.py).
- Default model: `gpt-4.1-mini`, configurable with `OPENAI_MODEL`. Every stored run records the actual requested identifier.
- API: OpenAI Python SDK `client.responses.parse`, using a Pydantic response schema. See the [official structured outputs guide](https://developers.openai.com/api/docs/guides/structured-outputs).
- Input: a system policy and a JSON user message containing the complete original note and target. The policy treats note text and target cues as source data, including any embedded instructions.
- Output: one of five labels, a reason code, reason, exact source quotes, and optional device. The application resolves unique quotes to Python string offsets and validates the source revision and exact substring. Adjacent sentences can form one contiguous quote.

The prompt separates actual walking help from transfers, device setup, other people, other times, future plans, conditional assistance, and declined help. It preserves uncertainty. Code compares confirmed baselines; the model does not make that comparison or interpret clinical risk.

Malformed output, refusals, absent structured predictions, and unresolved evidence are invalid analyses. Credentials, timeouts, rate limits, and provider failures are unavailable analyses. Neither failure becomes a completed `UNCLEAR` prediction. Provider exception details are not exposed as card copy because they may contain submitted text or sensitive headers.

The transport and validation paths have mocked tests. The public Fruta `nn_1093` source note and an agent-authored English translation are now frozen with provenance in [fruta-source.md](fruta-source.md). A real model inference remains pending until live credentials are available and an actual run is recorded. The separate fictional walking-attempt fixture is explicitly authored for development and is not represented as that Fruta note.

## Fixture demo

`FixtureExtractor` version `fictional-walkthrough-v1` accepts exact frozen fictional note strings, their date (`2026-01-15`), canonical context, and supported optional cue. It supports the breakfast walkthrough, its walker-only correction, and the fictional adjacent-sentence walking attempt. It also supports the exact frozen public Fruta `nn_1093` development text only with its source resident display name, walking-attempt context, observation date and target cue. That result is explicitly marked as a fixed development expectation rather than live inference. Elena and Ruth use the same pronoun-based note with different confirmed baselines.

Other inputs yield an explanatory `UNCLEAR` fixture result inviting selection of Live AI or the phrase baseline. Fixture output demonstrates the workflow; it is not a model experiment.

## Phrase baseline

`PhraseMatcher` version `phrase-v1` uses a conservative, transparent set of sentence and phrase rules. It anchors the canonical walking context, avoids explicit other residents and past/future distractors, distinguishes outbound and return routes, and can include a physical-support continuation sentence. It keeps devices separate and abstains for unresolved candidate events. Explicit ISO calendar dates on a walking sentence or a proposed support continuation must match the selected observation date. Mere staff presence such as “with staff beside her” does not itself trigger supervision; purposeful accompaniment or explicit support/safety wording is required.

This small baseline intentionally has limited language coverage. It is not a general semantic parser. Its performance must be measured on the same frozen examples and targets as the live extractor. Development fixture results and mocked tests do not establish held-out accuracy.


The recorded fictional development run has two exact-evidence mismatches despite matching all seven labels: the replacement case returns no span rather than the annotated walker sentence, and the transfer-distractor case returns the walker sentence rather than the annotated empty span. See [the recorded rows](development-results/results.json). Those are development errors, not held-out findings. The public development example currently matches both label and span; one inspected example does not estimate general performance.

Known unmeasured limits include non-ISO calendar-date wording, dates established in earlier paragraphs, unrestricted name/coreference resolution, and complex free-text target cues. The baseline rejects some ambiguous cases conservatively but does not solve general event attribution.
