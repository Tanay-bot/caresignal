# First-pass error analysis: frozen 24-note Fruta sample

**Gemini underperformed the phrase matcher on label and joint agreement in the first valid paired run.** Phrase labels matched 14/24 and joint label-plus-evidence matched 8/24; Gemini labels matched 11/24 and joint matched 7/24. A constant `UNCLEAR` label would match 14/24 because 14 references are `UNCLEAR`. The phrase result merely ties that label-only baseline; these results do not demonstrate an AI advantage.

| Method | Label agreement | Exact evidence | Joint agreement | Complete | Analysis failures |
| --- | ---: | ---: | ---: | ---: | ---: |
| phrase | 14/24 | 12/24 | 8/24 | 24/24 | 0 |
| gemini | 11/24 | 14/24 | 7/24 | 24/24 | 0 |

The constant-label comparison above measures labels only; its evidence and joint performance were not evaluated. Gemini supplied more exact reference span sets than the phrase matcher (14 versus 12), but it made more label errors (13 versus 10). Exact quote matching alone does not establish that the quote supports the predicted label. Both valid-run methods completed all 24 cases with zero provider or invalid-output failures.

| Error category | Phrase | Gemini |
| --- | ---: | ---: |
| Label only | 4 | 7 |
| Strict span only | 6 | 4 |
| Label and strict span | 6 | 6 |

This document analyzes only the preserved first valid run in [results.json](results.json), using `gemini-3.1-flash-lite`, extractor `gemini-structured-v2`, prompt `walking-assistance-v1`, and phrase baseline `phrase-v1` / `rules-v1`. It does not silently incorporate later prompt changes. The [complete generated report](report.md) lists every error; the examples below are selected for distinct failure modes. Failure-family descriptions interpret the saved texts and outputs. They do not reveal the model’s internal reasoning.

## Frozen scope and qualifications

Canonical dataset SHA-256: `a2d3a2e8dbe1d119c8cb02064963f585849ee2f01d95f2d640c7cbf426b178cf`. Exact JSONL file SHA-256: `48bb25f8cf61ca5f352581b2ccefd94c5869385597976e2d29875c0c4e8c9b80`. Dataset revision: `579141e3431c18a932fa3a0870e9f1c131f10367`. Translation: `caresignal-agent-en-reviewed-v1`. Reference annotation: `caresignal-two-agent-adjudicated-v1`.

These 24 public synthetic notes were selected by lexical strata before predictions. They form a small challenge sample, not a prevalence-weighted sample. Two coding agents in separate contexts supplied independent Dutch labels; translation review and one root adjudication followed. The agents share a model family, and these references are neither human nor clinical-expert gold. Specific categories have only one or two examples. “Held out” describes app development; upstream data use the `train` split and provider training exposure is unknown. See [the protocol](../heldout-methods.md) and [annotation ledger](../../data/annotations/fruta_held_out_v1.json).

The earlier `gemini-3.8-flash` attempt returned 14 provider failures and no labels before request 15 was interrupted. It is preserved separately in [initial-provider-failures.json](initial-provider-failures.json). It is not a completed 24-note accuracy run. The working model was chosen through availability testing on a disclosed development note before any successful held-out prediction.

## `na_0145` · Personal-care help must not become walking help

The only explicit human assistance is with getting up and dressing. The selected walking sentence describes difficulty and a walker, without saying that a person helped during that walk. Gemini returned `HELP_UNSPECIFIED` while citing exactly the reference walking sentence. This is a label-only error despite a valid, exact citation. The result is consistent with help leaking from another activity or difficulty/device use being treated as human assistance; the saved output does not establish which internal cause occurred. The phrase matcher kept `UNCLEAR` but missed the required walking excerpt, so its error is strict-span-only.

Source note ID: `na_0145`. [Pinned source dataset](https://huggingface.co/datasets/ekrombouts/fruta_records/blob/579141e3431c18a932fa3a0870e9f1c131f10367/data/train-00000-of-00001.parquet).

**Original Dutch**

```text
Dhr. is vanochtend geholpen met opstaan en aan kleden. Hij had wat moeite met lopen naar de gezamenlijke ruimte, maar met de rollator ging het redelijk. De tremoren zijn zichtbaar, vooral bij het vastpakken van de handgrepen.
```

**Frozen English used by both extractors**

```text
The resident was helped with getting up and dressing this morning. He had some difficulty walking to the shared room, but with the walker it went reasonably well. The tremors are visible, especially when grasping the handles.
```

**Selected target**

```json
{
  "context_key": "other_walk",
  "observed_on": "2024-06-05",
  "resident_id": "fruta-ca_02",
  "resident_name": "Fruta synthetic resident ca_02",
  "target_cue": "walk to the shared room this morning"
}
```

**Reference label: `UNCLEAR`. Expected exact evidence:**

```json
[
  {
    "end": 162,
    "quote": "He had some difficulty walking to the shared room, but with the walker it went reasonably well.",
    "start": 67
  }
]
```

| Method | Predicted label | Label matches | Exact evidence matches | Recorded error |
| --- | --- | --- | --- | --- |
| phrase | `UNCLEAR` | Yes | No | Strict span only |
| gemini | `HELP_UNSPECIFIED` | No | Yes | Label only |

**phrase predicted exact evidence** (`NO_SCOPED_PHRASE`):

```json
[]
```

**gemini predicted exact evidence** (`WALK_ASSISTANCE_UNSPECIFIED`):

```json
[
  {
    "end": 162,
    "quote": "He had some difficulty walking to the shared room, but with the walker it went reasonably well.",
    "start": 67
  }
]
```

## `nk_1089` · General ability and toilet help are not a completed supported walk

The note says the resident “can still walk short distances with support.” That states capability, while the completed episode describes toilet assistance and subsequent wheelchair rest. The reference therefore has `UNCLEAR` with no walking-event evidence. Gemini returned `HANDS_ON` and cited both toilet help and the capability sentence. That converts ability and a different activity into physical assistance on the selected event. The phrase matcher correctly abstained with no excerpt.

Source note ID: `nk_1089`. [Pinned source dataset](https://huggingface.co/datasets/ekrombouts/fruta_records/blob/579141e3431c18a932fa3a0870e9f1c131f10367/data/train-00000-of-00001.parquet).

**Original Dutch**

```text
Bij het toiletbezoek vandaag had dhr. weer wat hulp nodig. Hij is zichtbaar moe, maar kan nog steeds korte afstanden lopen met ondersteuning. Na het toiletbezoek hebben we hem even laten rusten in zijn rolstoel.
```

**Frozen English used by both extractors**

```text
The resident needed some help again during today's toilet visit. He is visibly tired, but can still walk short distances with support. After the toilet visit, we let him rest in his wheelchair for a while.
```

**Selected target**

```json
{
  "context_key": "other_walk",
  "observed_on": "2024-12-18",
  "resident_id": "fruta-ck_06",
  "resident_name": "Fruta synthetic resident ck_06",
  "target_cue": "walking in the episode described in this note"
}
```

**Reference label: `UNCLEAR`. Expected exact evidence:**

```json
[]
```

| Method | Predicted label | Label matches | Exact evidence matches | Recorded error |
| --- | --- | --- | --- | --- |
| phrase | `UNCLEAR` | Yes | Yes | No error |
| gemini | `HANDS_ON` | No | No | Label + strict span |

**phrase predicted exact evidence** (`NO_SCOPED_PHRASE`):

```json
[]
```

**gemini predicted exact evidence** (`SUPPORTED_WALKING`):

```json
[
  {
    "end": 64,
    "quote": "The resident needed some help again during today's toilet visit.",
    "start": 0
  },
  {
    "end": 134,
    "quote": "He is visibly tired, but can still walk short distances with support.",
    "start": 65
  }
]
```

## `nm_0182` · Independence at lunch does not establish independent garden walking

“Ate independently” belongs to lunch. The later garden walk mentions only a walker; human help is unspecified. Gemini returned `INDEPENDENT` while quoting exactly the reference garden-walk sentence, with reason code `DEVICE_ONLY`. The observed failure is unsupported walking independence with an exact citation. Cross-activity independence leakage and interpreting a device-only walk as independent are plausible explanations, not observed model reasoning. The phrase matcher kept the correct `UNCLEAR` label but omitted the frozen walking excerpt.

Source note ID: `nm_0182`. [Pinned source dataset](https://huggingface.co/datasets/ekrombouts/fruta_records/blob/579141e3431c18a932fa3a0870e9f1c131f10367/data/train-00000-of-00001.parquet).

**Original Dutch**

```text
Lunch: at zelfstandig. Daarna korte wandeling in de tuin met rollator. Genoot zichtbaar van de buitenlucht. Praatte over zijn vroegere tuin, leek positieve herinnering.
```

**Frozen English used by both extractors**

```text
Lunch: ate independently. Afterwards, a short walk in the garden with a walker. Visibly enjoyed the fresh air. Talked about his former garden; seemed to be a positive memory.
```

**Selected target**

```json
{
  "context_key": "garden_walk",
  "observed_on": "2024-03-28",
  "resident_id": "fruta-cm_02",
  "resident_name": "Fruta synthetic resident cm_02",
  "target_cue": "garden walk after lunch"
}
```

**Reference label: `UNCLEAR`. Expected exact evidence:**

```json
[
  {
    "end": 79,
    "quote": "Afterwards, a short walk in the garden with a walker.",
    "start": 26
  }
]
```

| Method | Predicted label | Label matches | Exact evidence matches | Recorded error |
| --- | --- | --- | --- | --- |
| phrase | `UNCLEAR` | Yes | No | Strict span only |
| gemini | `INDEPENDENT` | No | Yes | Label only |

**phrase predicted exact evidence** (`NO_SCOPED_PHRASE`):

```json
[]
```

**gemini predicted exact evidence** (`DEVICE_ONLY`):

```json
[
  {
    "end": 79,
    "quote": "Afterwards, a short walk in the garden with a walker.",
    "start": 26
  }
]
```

## `nk_0797` · A safety-watch sentence was missed

The full event includes staff keeping an extra close eye on whether the resident might fall. The reference treats that purposeful monitoring as `SUPERVISION` and cites the walk through the safety-watch sentence. Gemini instead returned `INDEPENDENT` and quoted only the first walking-frame sentence. The phrase matcher returned `UNCLEAR` with no evidence. Both miss documented safety monitoring; Gemini also asserts independence that the note never states. Lunch help afterwards is a separate activity and does not determine walking assistance.

Source note ID: `nk_0797`. [Pinned source dataset](https://huggingface.co/datasets/ekrombouts/fruta_records/blob/579141e3431c18a932fa3a0870e9f1c131f10367/data/train-00000-of-00001.parquet).

**Original Dutch**

```text
Tijdens de middagshift heeft dhr. een korte wandeling gemaakt met het looprek. Hij was wat onrustig en zag dingen die er niet waren. We hebben extra goed in de gaten gehouden of hij niet zou vallen. Na de wandeling hebben we hem geholpen met zijn lunch, wat goed ging. Hij at met smaak.
```

**Frozen English used by both extractors**

```text
During the afternoon shift, the resident took a short walk with the walking frame. He was somewhat restless and saw things that were not there. We kept an extra close eye on whether he might fall. After the walk, we helped him with his lunch, which went well. He ate with enjoyment.
```

**Selected target**

```json
{
  "context_key": "other_walk",
  "observed_on": "2024-07-03",
  "resident_id": "fruta-ck_04",
  "resident_name": "Fruta synthetic resident ck_04",
  "target_cue": "walk with the walking frame during the afternoon shift"
}
```

**Reference label: `SUPERVISION`. Expected exact evidence:**

```json
[
  {
    "end": 196,
    "quote": "During the afternoon shift, the resident took a short walk with the walking frame. He was somewhat restless and saw things that were not there. We kept an extra close eye on whether he might fall.",
    "start": 0
  }
]
```

| Method | Predicted label | Label matches | Exact evidence matches | Recorded error |
| --- | --- | --- | --- | --- |
| phrase | `UNCLEAR` | No | No | Label + strict span |
| gemini | `INDEPENDENT` | No | No | Label + strict span |

**phrase predicted exact evidence** (`NO_SCOPED_PHRASE`):

```json
[]
```

**gemini predicted exact evidence** (`NO_SUPPORT_DOCUMENTED`):

```json
[
  {
    "end": 82,
    "quote": "During the afternoon shift, the resident took a short walk with the walking frame.",
    "start": 0
  }
]
```

## `nk_0846` · Ambiguous guidance was over-specified as supervision

Dutch `begeleiding` is retained as “guidance” in the frozen translation. The reference establishes human help but leaves its subtype unresolved, so it is `HELP_UNSPECIFIED`. Gemini selected `SUPERVISION` with the exact same sentence as the reference, making this a label-only error. The phrase matcher matched both label and span. The issue is assistance-taxonomy interpretation rather than quote resolution; a fluent translation does not justify adding a more specific type of support.

Source note ID: `nk_0846`. [Pinned source dataset](https://huggingface.co/datasets/ekrombouts/fruta_records/blob/579141e3431c18a932fa3a0870e9f1c131f10367/data/train-00000-of-00001.parquet).

**Original Dutch**

```text
Aan het einde van de dag was mw. moe. Ze heeft een korte wandeling gemaakt met begeleiding. Het was een rustige dag, maar ze heeft wel wat moeite met het wennen aan de nieuwe omgeving.
```

**Frozen English used by both extractors**

```text
At the end of the day, the resident was tired. She took a short walk with guidance. It was a quiet day, but she is having some difficulty getting used to the new surroundings.
```

**Selected target**

```json
{
  "context_key": "other_walk",
  "observed_on": "2024-10-26",
  "resident_id": "fruta-ck_05",
  "resident_name": "Fruta synthetic resident ck_05",
  "target_cue": "short walk at the end of the day"
}
```

**Reference label: `HELP_UNSPECIFIED`. Expected exact evidence:**

```json
[
  {
    "end": 83,
    "quote": "She took a short walk with guidance.",
    "start": 47
  }
]
```

| Method | Predicted label | Label matches | Exact evidence matches | Recorded error |
| --- | --- | --- | --- | --- |
| phrase | `HELP_UNSPECIFIED` | Yes | Yes | No error |
| gemini | `SUPERVISION` | No | Yes | Label only |

**phrase predicted exact evidence** (`PHRASE_MATCH`):

```json
[
  {
    "end": 83,
    "quote": "She took a short walk with guidance.",
    "start": 47
  }
]
```

**gemini predicted exact evidence** (`SUPERVISED_WALK`):

```json
[
  {
    "end": 83,
    "quote": "She took a short walk with guidance.",
    "start": 47
  }
]
```

## `nd_0902` · Generic support was over-specified as physical contact

The reference reads generic support during a walk as `HELP_UNSPECIFIED`; the sentence does not explicitly describe holding, steadying or bodily contact. Gemini returned `HANDS_ON` and shortened the evidence to the opening clause, producing both a label error and a strict span mismatch. The phrase matcher cited the full reference sentence but returned `UNCLEAR`, failing to retain the documented human-help finding. The original wording remains available for human Dutch review; the saved agent reference is not clinical gold.

Source note ID: `nd_0902`. [Pinned source dataset](https://huggingface.co/datasets/ekrombouts/fruta_records/blob/579141e3431c18a932fa3a0870e9f1c131f10367/data/train-00000-of-00001.parquet).

**Original Dutch**

```text
Ondersteunde tijdens een kortere wandeling met de rollator, waarbij haar balans en bewustzijn werden verbeterd. Mw. zei dat ze zich veilig voelde.
```

**Frozen English used by both extractors**

```text
Provided support during a shorter walk with the walker, during which her balance and awareness improved. The resident said that she felt safe.
```

**Selected target**

```json
{
  "context_key": "other_walk",
  "observed_on": "2024-12-30",
  "resident_id": "fruta-cd_04",
  "resident_name": "Fruta synthetic resident cd_04",
  "target_cue": "short walk with the walker"
}
```

**Reference label: `HELP_UNSPECIFIED`. Expected exact evidence:**

```json
[
  {
    "end": 104,
    "quote": "Provided support during a shorter walk with the walker, during which her balance and awareness improved.",
    "start": 0
  }
]
```

| Method | Predicted label | Label matches | Exact evidence matches | Recorded error |
| --- | --- | --- | --- | --- |
| phrase | `UNCLEAR` | No | Yes | Label only |
| gemini | `HANDS_ON` | No | No | Label + strict span |

**phrase predicted exact evidence** (`HUMAN_HELP_UNSPECIFIED`):

```json
[
  {
    "end": 104,
    "quote": "Provided support during a shorter walk with the walker, during which her balance and awareness improved.",
    "start": 0
  }
]
```

**gemini predicted exact evidence** (`PHYSICAL_SUPPORT_DOCUMENTED`):

```json
[
  {
    "end": 54,
    "quote": "Provided support during a shorter walk with the walker",
    "start": 0
  }
]
```

## `na_0689` · Correct help label, different span segmentation

Gemini matched the reference `HANDS_ON` label. Its two exact sentence spans contain the same substantive words as the one contiguous reference span, but omit the inter-sentence space from the span set. The frozen exact-set metric therefore marks its evidence and joint result wrong. This is a strict span-only mismatch, not a label error and not a paraphrased or fabricated citation. Both annotating agents chose `HANDS_ON` because the support is directly tied to maintaining balance; that interpretation is an annotation uncertainty recorded in the protocol. The phrase matcher missed the hands-on finding and cited only the walking sentence.

Source note ID: `na_0689`. [Pinned source dataset](https://huggingface.co/datasets/ekrombouts/fruta_records/blob/579141e3431c18a932fa3a0870e9f1c131f10367/data/train-00000-of-00001.parquet).

**Original Dutch**

```text
Tijdens het middaguur heeft mevrouw goed gegeten, maar ze leek nog steeds moe. Na de lunch hebben we samen een korte wandeling gemaakt met de rollator. Ze had moeite om haar balans te houden, maar met mijn ondersteuning ging het redelijk. We hebben rustig aan gedaan.
```

**Frozen English used by both extractors**

```text
At midday, the resident ate well, but she still seemed tired. After lunch, we took a short walk together with the walker. She had difficulty keeping her balance, but with my support it went reasonably well. We took it slowly.
```

**Selected target**

```json
{
  "context_key": "other_walk",
  "observed_on": "2024-09-29",
  "resident_id": "fruta-ca_05",
  "resident_name": "Fruta synthetic resident ca_05",
  "target_cue": "short walk with the walker after lunch"
}
```

**Reference label: `HANDS_ON`. Expected exact evidence:**

```json
[
  {
    "end": 206,
    "quote": "After lunch, we took a short walk together with the walker. She had difficulty keeping her balance, but with my support it went reasonably well.",
    "start": 62
  }
]
```

| Method | Predicted label | Label matches | Exact evidence matches | Recorded error |
| --- | --- | --- | --- | --- |
| phrase | `UNCLEAR` | No | No | Label + strict span |
| gemini | `HANDS_ON` | Yes | No | Strict span only |

**phrase predicted exact evidence** (`HUMAN_HELP_UNSPECIFIED`):

```json
[
  {
    "end": 121,
    "quote": "After lunch, we took a short walk together with the walker.",
    "start": 62
  }
]
```

**gemini predicted exact evidence** (`PHYSICAL_SUPPORT_DOCUMENTED`):

```json
[
  {
    "end": 121,
    "quote": "After lunch, we took a short walk together with the walker.",
    "start": 62
  },
  {
    "end": 206,
    "quote": "She had difficulty keeping her balance, but with my support it went reasonably well.",
    "start": 122
  }
]
```

## `na_1633` · Assistance from a later event crossed the selected-event boundary

The target is the resident’s aimless walking before the carer took him to the garden. The reference leaves help on that earlier walk `UNCLEAR`. Gemini cited the earlier walking sentence together with the later garden action and returned `SUPERVISION`. The quoted words are real, but the help is not established for the selected earlier event. The phrase matcher kept `UNCLEAR` but supplied no excerpt, so it failed the strict evidence annotation only.

Source note ID: `na_1633`. [Pinned source dataset](https://huggingface.co/datasets/ekrombouts/fruta_records/blob/579141e3431c18a932fa3a0870e9f1c131f10367/data/train-00000-of-00001.parquet).

**Original Dutch**

```text
Dhr. had een onrustige middag. Hij liep rond zonder doel en leek angstig. De verzorgende heeft hem meegenomen naar de tuin voor wat frisse lucht. Dit hielp hem om wat te ontspannen.
```

**Frozen English used by both extractors**

```text
The resident had a restless afternoon. He walked around aimlessly and seemed anxious. The carer took him to the garden for some fresh air. This helped him relax a little.
```

**Selected target**

```json
{
  "context_key": "other_walk",
  "observed_on": "2024-03-05",
  "resident_id": "fruta-ca_08",
  "resident_name": "Fruta synthetic resident ca_08",
  "target_cue": "aimless walking before the carer took him to the garden"
}
```

**Reference label: `UNCLEAR`. Expected exact evidence:**

```json
[
  {
    "end": 85,
    "quote": "He walked around aimlessly and seemed anxious.",
    "start": 39
  }
]
```

| Method | Predicted label | Label matches | Exact evidence matches | Recorded error |
| --- | --- | --- | --- | --- |
| phrase | `UNCLEAR` | Yes | No | Strict span only |
| gemini | `SUPERVISION` | No | No | Label + strict span |

**phrase predicted exact evidence** (`NO_SCOPED_PHRASE`):

```json
[]
```

**gemini predicted exact evidence** (`DIRECT_SUPERVISION_COMPLETED`):

```json
[
  {
    "end": 138,
    "quote": "He walked around aimlessly and seemed anxious. The carer took him to the garden for some fresh air.",
    "start": 39
  }
]
```

## Implications for the next experiment

The first-pass failures motivate stricter checks for a completed selected event, separation of walking from transfers/eating/toilet assistance, preservation of generic guidance/support as unspecified, and inclusion of event-linked safety monitoring. Evidence-boundary normalization should be specified before a future test; treating split sentences as equivalent after inspecting this result would change the metric after the fact.

A prompt modified using this review is a post-hoc replay on already inspected examples. Its scores can describe the change on these notes but cannot replace the frozen first pass or establish performance on a new held-out sample. A stronger claim needs another frozen sample and human review of translations, taxonomy judgments and evidence boundaries. The current results concern documentation extraction only; they do not validate clinical interpretation or care decisions.

This project is a prototype and is not medical advice.
