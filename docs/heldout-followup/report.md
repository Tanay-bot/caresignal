# CareSignal prompt-v2 post-hoc replay

## Scope and methods

The identified source datasets contain synthetic or fictional documentation.

This report summarizes stored extraction results for the frozen inputs identified below. It does not establish clinical validity, treatment benefit, or deployment readiness. No inference was rerun to produce this report.

This reuses the same 24-note lexical-stratified synthetic sample after inspecting prompt-v1 errors. It is development replay, not a new held-out estimate. References were reviewed by coding agents, not humans or clinicians. Six initial rate-limit failures were retried once, paced at least five seconds apart. The initial attempt, retry-only predictions and per-example attempt ledger are preserved; all 24 notes remain in the final metric denominator.

Development or mixed-scope results describe those examples only and do not estimate held-out Fruta performance.

## Method 1: phrase / no model

| N | Complete | Unavailable | Invalid | Analysis failures | Incorrect examples |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 24 | 24 | 0 | 0 | 0 | 16 |

Analysis failures are unavailable or invalid runs. Incorrect examples include those failures and every completed label or strict-span mismatch.

| Metric | Exact fraction |
| --- | ---: |
| Label agreement | 14/24 |
| Exact evidence span-set agreement | 12/24 |
| Joint agreement | 8/24 |

Every input remains in the denominator. Exact evidence requires the complete frozen set of half-open `(start, end, quote)` spans; partial overlaps and paraphrases fail this strict measure. Repeated predicted spans are retained in the comparison.

### Stored provenance

```json
{
  "schema_version": "1.0",
  "scope": "post_hoc_replay",
  "dataset": {
    "ids": [
      "ekrombouts/fruta_records"
    ],
    "revisions": [
      "579141e3431c18a932fa3a0870e9f1c131f10367"
    ],
    "sha256": "a2d3a2e8dbe1d119c8cb02064963f585849ee2f01d95f2d640c7cbf426b178cf",
    "splits": {
      "held_out": 24
    },
    "translation_ids": [
      "caresignal-agent-en-reviewed-v1"
    ]
  },
  "extractor": {
    "mode": "phrase",
    "model_id": null,
    "prompt_version": "rules-v1",
    "version": "phrase-v1"
  },
  "metrics_policy": "Exact span-set match; all examples including errors remain in denominator."
}
```

### Label distributions

| Label | Gold | Predicted in complete runs |
| --- | ---: | ---: |
| INDEPENDENT | 1 | 3 |
| SUPERVISION | 1 | 0 |
| HANDS_ON | 2 | 0 |
| HELP_UNSPECIFIED | 6 | 2 |
| UNCLEAR | 14 | 19 |
| No completed prediction | 0 | 0 |
| Total | 24 | 24 |

### Confusion table

Rows are gold labels. Columns are predicted labels or analysis-failure statuses.

| Gold \ Predicted | INDEPENDENT | SUPERVISION | HANDS_ON | HELP_UNSPECIFIED | UNCLEAR | UNAVAILABLE | INVALID | Total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| INDEPENDENT | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| SUPERVISION | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 1 |
| HANDS_ON | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 2 |
| HELP_UNSPECIFIED | 1 | 0 | 0 | 1 | 4 | 0 | 0 | 6 |
| UNCLEAR | 1 | 0 | 0 | 1 | 12 | 0 | 0 | 14 |
| Total | 3 | 0 | 0 | 2 | 19 | 0 | 0 | 24 |

### Error review

| Recorded category | Count |
| --- | ---: |
| Label and strict evidence mismatch | 6 |
| Label mismatch | 4 |
| Strict evidence span mismatch | 6 |

#### na_0145: Strict evidence span mismatch

Stored source and outcome:

```json
{
  "source_note_id": "na_0145",
  "example_id": "na_0145",
  "source_url": "https://huggingface.co/datasets/ekrombouts/fruta_records/blob/579141e3431c18a932fa3a0870e9f1c131f10367/data/train-00000-of-00001.parquet",
  "status": "COMPLETE",
  "error_category": null,
  "reason_code": "NO_SCOPED_PHRASE",
  "expected_label": "UNCLEAR",
  "predicted_label": "UNCLEAR"
}
```

Selected target:

```json
{
  "context_key": "other_walk",
  "observed_on": "2024-06-05",
  "resident_id": "fruta-ca_02",
  "resident_name": "Fruta synthetic resident ca_02",
  "target_cue": "walk to the shared room this morning"
}
```

Frozen note used for extraction:

```text
The resident was helped with getting up and dressing this morning. He had some difficulty walking to the shared room, but with the walker it went reasonably well. The tremors are visible, especially when grasping the handles.
```

Original-language note:

```text
Dhr. is vanochtend geholpen met opstaan en aan kleden. Hij had wat moeite met lopen naar de gezamenlijke ruimte, maar met de rollator ging het redelijk. De tremoren zijn zichtbaar, vooral bij het vastpakken van de handgrepen.
```

Expected exact evidence:

```json
[
  {
    "end": 162,
    "quote": "He had some difficulty walking to the shared room, but with the walker it went reasonably well.",
    "start": 67
  }
]
```

Predicted exact evidence:

```json
[]
```

The label matches. The saved evidence span set differs from the strict frozen annotation; this report does not judge an alternative span semantically correct or incorrect.

#### nd_0902: Label mismatch

Stored source and outcome:

```json
{
  "source_note_id": "nd_0902",
  "example_id": "nd_0902",
  "source_url": "https://huggingface.co/datasets/ekrombouts/fruta_records/blob/579141e3431c18a932fa3a0870e9f1c131f10367/data/train-00000-of-00001.parquet",
  "status": "COMPLETE",
  "error_category": null,
  "reason_code": "HUMAN_HELP_UNSPECIFIED",
  "expected_label": "HELP_UNSPECIFIED",
  "predicted_label": "UNCLEAR"
}
```

Selected target:

```json
{
  "context_key": "other_walk",
  "observed_on": "2024-12-30",
  "resident_id": "fruta-cd_04",
  "resident_name": "Fruta synthetic resident cd_04",
  "target_cue": "short walk with the walker"
}
```

Frozen note used for extraction:

```text
Provided support during a shorter walk with the walker, during which her balance and awareness improved. The resident said that she felt safe.
```

Original-language note:

```text
Ondersteunde tijdens een kortere wandeling met de rollator, waarbij haar balans en bewustzijn werden verbeterd. Mw. zei dat ze zich veilig voelde.
```

Expected exact evidence:

```json
[
  {
    "end": 104,
    "quote": "Provided support during a shorter walk with the walker, during which her balance and awareness improved.",
    "start": 0
  }
]
```

Predicted exact evidence:

```json
[
  {
    "end": 104,
    "quote": "Provided support during a shorter walk with the walker, during which her balance and awareness improved.",
    "start": 0
  }
]
```

#### nm_1286: Label and strict evidence mismatch

Stored source and outcome:

```json
{
  "source_note_id": "nm_1286",
  "example_id": "nm_1286",
  "source_url": "https://huggingface.co/datasets/ekrombouts/fruta_records/blob/579141e3431c18a932fa3a0870e9f1c131f10367/data/train-00000-of-00001.parquet",
  "status": "COMPLETE",
  "error_category": null,
  "reason_code": "NO_SCOPED_PHRASE",
  "expected_label": "HANDS_ON",
  "predicted_label": "UNCLEAR"
}
```

Selected target:

```json
{
  "context_key": "garden_walk",
  "observed_on": "2024-06-01",
  "resident_id": "fruta-cm_07",
  "resident_name": "Fruta synthetic resident cm_07",
  "target_cue": "garden walk used as distraction"
}
```

Frozen note used for extraction:

```text
The resident was sitting in the living room. Kept asking where her bag was (not brought in on admission). Became restless when we said it was not there. Taken for a short walk in the garden as a distraction. Walked unsteadily; support had to be provided.
```

Original-language note:

```text
Mw. zat in huiskamer. Vroeg steeds waar haar tas was (niet meegebracht bij opname). Werd onrustig toen we zeiden dat ze er niet was. Om af te leiden meegenomen voor korte wandeling in de tuin. Liep onstabiel, moest ondersteunen.
```

Expected exact evidence:

```json
[
  {
    "end": 254,
    "quote": "Taken for a short walk in the garden as a distraction. Walked unsteadily; support had to be provided.",
    "start": 153
  }
]
```

Predicted exact evidence:

```json
[]
```

#### na_0762: Label and strict evidence mismatch

Stored source and outcome:

```json
{
  "source_note_id": "na_0762",
  "example_id": "na_0762",
  "source_url": "https://huggingface.co/datasets/ekrombouts/fruta_records/blob/579141e3431c18a932fa3a0870e9f1c131f10367/data/train-00000-of-00001.parquet",
  "status": "COMPLETE",
  "error_category": null,
  "reason_code": "AMBIGUOUS_EVENT",
  "expected_label": "HELP_UNSPECIFIED",
  "predicted_label": "UNCLEAR"
}
```

Selected target:

```json
{
  "context_key": "other_walk",
  "observed_on": "2024-10-20",
  "resident_id": "fruta-ca_05",
  "resident_name": "Fruta synthetic resident ca_05",
  "target_cue": "walk with the walker described before sitting on the sofa"
}
```

Frozen note used for extraction:

```text
The resident had difficulty walking with the walker. We provided additional support. She was visibly anxious after last week's fall. After a short walk, she sat on the sofa for a while to recover.
```

Original-language note:

```text
Mw. had moeite met lopen met de rollator. We hebben extra ondersteuning geboden. Ze was zichtbaar angstig na de valpartij van vorige week. Na een kort wandelingetje heeft ze even op de bank gezeten om bij te komen.
```

Expected exact evidence:

```json
[
  {
    "end": 84,
    "quote": "The resident had difficulty walking with the walker. We provided additional support.",
    "start": 0
  }
]
```

Predicted exact evidence:

```json
[]
```

#### na_0689: Label and strict evidence mismatch

Stored source and outcome:

```json
{
  "source_note_id": "na_0689",
  "example_id": "na_0689",
  "source_url": "https://huggingface.co/datasets/ekrombouts/fruta_records/blob/579141e3431c18a932fa3a0870e9f1c131f10367/data/train-00000-of-00001.parquet",
  "status": "COMPLETE",
  "error_category": null,
  "reason_code": "HUMAN_HELP_UNSPECIFIED",
  "expected_label": "HANDS_ON",
  "predicted_label": "UNCLEAR"
}
```

Selected target:

```json
{
  "context_key": "other_walk",
  "observed_on": "2024-09-29",
  "resident_id": "fruta-ca_05",
  "resident_name": "Fruta synthetic resident ca_05",
  "target_cue": "short walk with the walker after lunch"
}
```

Frozen note used for extraction:

```text
At midday, the resident ate well, but she still seemed tired. After lunch, we took a short walk together with the walker. She had difficulty keeping her balance, but with my support it went reasonably well. We took it slowly.
```

Original-language note:

```text
Tijdens het middaguur heeft mevrouw goed gegeten, maar ze leek nog steeds moe. Na de lunch hebben we samen een korte wandeling gemaakt met de rollator. Ze had moeite om haar balans te houden, maar met mijn ondersteuning ging het redelijk. We hebben rustig aan gedaan.
```

Expected exact evidence:

```json
[
  {
    "end": 206,
    "quote": "After lunch, we took a short walk together with the walker. She had difficulty keeping her balance, but with my support it went reasonably well.",
    "start": 62
  }
]
```

Predicted exact evidence:

```json
[
  {
    "end": 121,
    "quote": "After lunch, we took a short walk together with the walker.",
    "start": 62
  }
]
```

#### nb_0960: Label and strict evidence mismatch

Stored source and outcome:

```json
{
  "source_note_id": "nb_0960",
  "example_id": "nb_0960",
  "source_url": "https://huggingface.co/datasets/ekrombouts/fruta_records/blob/579141e3431c18a932fa3a0870e9f1c131f10367/data/train-00000-of-00001.parquet",
  "status": "COMPLETE",
  "error_category": null,
  "reason_code": "PHRASE_MATCH",
  "expected_label": "HELP_UNSPECIFIED",
  "predicted_label": "INDEPENDENT"
}
```

Selected target:

```json
{
  "context_key": "walking_attempt",
  "observed_on": "2024-09-10",
  "resident_id": "fruta-cb_05",
  "resident_name": "Fruta synthetic resident cb_05",
  "target_cue": "attempt to walk to her room with the walker"
}
```

Frozen note used for extraction:

```text
The resident tried to walk independently to her room with the walker. She forgot how it works and had to be guided.
```

Original-language note:

```text
Mw. probeerde zelfstandig naar haar kamer te lopen met de rollator. Ze vergat hoe deze werkt en moest worden begeleid.
```

Expected exact evidence:

```json
[
  {
    "end": 115,
    "quote": "The resident tried to walk independently to her room with the walker. She forgot how it works and had to be guided.",
    "start": 0
  }
]
```

Predicted exact evidence:

```json
[
  {
    "end": 69,
    "quote": "The resident tried to walk independently to her room with the walker.",
    "start": 0
  }
]
```

#### nm_0182: Strict evidence span mismatch

Stored source and outcome:

```json
{
  "source_note_id": "nm_0182",
  "example_id": "nm_0182",
  "source_url": "https://huggingface.co/datasets/ekrombouts/fruta_records/blob/579141e3431c18a932fa3a0870e9f1c131f10367/data/train-00000-of-00001.parquet",
  "status": "COMPLETE",
  "error_category": null,
  "reason_code": "NO_SCOPED_PHRASE",
  "expected_label": "UNCLEAR",
  "predicted_label": "UNCLEAR"
}
```

Selected target:

```json
{
  "context_key": "garden_walk",
  "observed_on": "2024-03-28",
  "resident_id": "fruta-cm_02",
  "resident_name": "Fruta synthetic resident cm_02",
  "target_cue": "garden walk after lunch"
}
```

Frozen note used for extraction:

```text
Lunch: ate independently. Afterwards, a short walk in the garden with a walker. Visibly enjoyed the fresh air. Talked about his former garden; seemed to be a positive memory.
```

Original-language note:

```text
Lunch: at zelfstandig. Daarna korte wandeling in de tuin met rollator. Genoot zichtbaar van de buitenlucht. Praatte over zijn vroegere tuin, leek positieve herinnering.
```

Expected exact evidence:

```json
[
  {
    "end": 79,
    "quote": "Afterwards, a short walk in the garden with a walker.",
    "start": 26
  }
]
```

Predicted exact evidence:

```json
[]
```

The label matches. The saved evidence span set differs from the strict frozen annotation; this report does not judge an alternative span semantically correct or incorrect.

#### nb_0890: Label mismatch

Stored source and outcome:

```json
{
  "source_note_id": "nb_0890",
  "example_id": "nb_0890",
  "source_url": "https://huggingface.co/datasets/ekrombouts/fruta_records/blob/579141e3431c18a932fa3a0870e9f1c131f10367/data/train-00000-of-00001.parquet",
  "status": "COMPLETE",
  "error_category": null,
  "reason_code": "PHRASE_MATCH",
  "expected_label": "UNCLEAR",
  "predicted_label": "INDEPENDENT"
}
```

Selected target:

```json
{
  "context_key": "garden_walk",
  "observed_on": "2024-08-18",
  "resident_id": "fruta-cb_05",
  "resident_name": "Fruta synthetic resident cb_05",
  "target_cue": "afternoon garden walk"
}
```

Frozen note used for extraction:

```text
During the afternoon walk in the garden, the resident used her walker independently. She walked calmly and said that the pain in her knees was not too bad today.
```

Original-language note:

```text
Tijdens de middagwandeling in de tuin gebruikte mw. haar rollator zelfstandig. Ze liep rustig en gaf aan dat de pijn in haar knieën vandaag meevalt.
```

Expected exact evidence:

```json
[
  {
    "end": 84,
    "quote": "During the afternoon walk in the garden, the resident used her walker independently.",
    "start": 0
  }
]
```

Predicted exact evidence:

```json
[
  {
    "end": 84,
    "quote": "During the afternoon walk in the garden, the resident used her walker independently.",
    "start": 0
  }
]
```

#### nl_0727: Strict evidence span mismatch

Stored source and outcome:

```json
{
  "source_note_id": "nl_0727",
  "example_id": "nl_0727",
  "source_url": "https://huggingface.co/datasets/ekrombouts/fruta_records/blob/579141e3431c18a932fa3a0870e9f1c131f10367/data/train-00000-of-00001.parquet",
  "status": "COMPLETE",
  "error_category": null,
  "reason_code": "NO_SCOPED_PHRASE",
  "expected_label": "UNCLEAR",
  "predicted_label": "UNCLEAR"
}
```

Selected target:

```json
{
  "context_key": "other_walk",
  "observed_on": "2024-07-17",
  "resident_id": "fruta-cl_04",
  "resident_name": "Fruta synthetic resident cl_04",
  "target_cue": "walking around during lunch; exclude help to sit back down"
}
```

Frozen note used for extraction:

```text
The resident was restless during lunch and kept getting up to walk around. He accepted guidance to sit back down.
```

Original-language note:

```text
Dhr. was onrustig tijdens de lunch en bleef opstaan om rond te lopen. Hij accepteerde begeleiding om weer te gaan zitten.
```

Expected exact evidence:

```json
[
  {
    "end": 74,
    "quote": "The resident was restless during lunch and kept getting up to walk around.",
    "start": 0
  }
]
```

Predicted exact evidence:

```json
[]
```

The label matches. The saved evidence span set differs from the strict frozen annotation; this report does not judge an alternative span semantically correct or incorrect.

#### nn_1577: Label mismatch

Stored source and outcome:

```json
{
  "source_note_id": "nn_1577",
  "example_id": "nn_1577",
  "source_url": "https://huggingface.co/datasets/ekrombouts/fruta_records/blob/579141e3431c18a932fa3a0870e9f1c131f10367/data/train-00000-of-00001.parquet",
  "status": "COMPLETE",
  "error_category": null,
  "reason_code": "HUMAN_HELP_UNSPECIFIED",
  "expected_label": "HELP_UNSPECIFIED",
  "predicted_label": "UNCLEAR"
}
```

Selected target:

```json
{
  "context_key": "other_walk",
  "observed_on": "2024-06-28",
  "resident_id": "fruta-cn_06",
  "resident_name": "Fruta synthetic resident cn_06",
  "target_cue": "short afternoon walk with the walker"
}
```

Frozen note used for extraction:

```text
The afternoon activity was a short walk with the walker, during which we regularly reminded her to use it. She liked the light exercise.
```

Original-language note:

```text
Middagactiviteit was een korte wandeling met de rollator, waarbij we regelmatig herinnerden om deze te gebruiken. Ze hield goed van de lichte beweging.
```

Expected exact evidence:

```json
[
  {
    "end": 106,
    "quote": "The afternoon activity was a short walk with the walker, during which we regularly reminded her to use it.",
    "start": 0
  }
]
```

Predicted exact evidence:

```json
[
  {
    "end": 106,
    "quote": "The afternoon activity was a short walk with the walker, during which we regularly reminded her to use it.",
    "start": 0
  }
]
```

#### nn_2000: Label and strict evidence mismatch

Stored source and outcome:

```json
{
  "source_note_id": "nn_2000",
  "example_id": "nn_2000",
  "source_url": "https://huggingface.co/datasets/ekrombouts/fruta_records/blob/579141e3431c18a932fa3a0870e9f1c131f10367/data/train-00000-of-00001.parquet",
  "status": "COMPLETE",
  "error_category": null,
  "reason_code": "NO_SCOPED_PHRASE",
  "expected_label": "HELP_UNSPECIFIED",
  "predicted_label": "UNCLEAR"
}
```

Selected target:

```json
{
  "context_key": "hallway_walk",
  "observed_on": "2024-08-27",
  "resident_id": "fruta-cn_07",
  "resident_name": "Fruta synthetic resident cn_07",
  "target_cue": "short hallway walk"
}
```

Frozen note used for extraction:

```text
The resident was guided for a short walk in the hallway; he was enthusiastic but sometimes had to be reminded about safety.
```

Original-language note:

```text
Dhr. werd bijgeleid voor een korte wandeling in de gang; hij was enthousiast maar moest soms worden herinnerd aan veiligheid.
```

Expected exact evidence:

```json
[
  {
    "end": 123,
    "quote": "The resident was guided for a short walk in the hallway; he was enthusiastic but sometimes had to be reminded about safety.",
    "start": 0
  }
]
```

Predicted exact evidence:

```json
[]
```

#### nk_0797: Label and strict evidence mismatch

Stored source and outcome:

```json
{
  "source_note_id": "nk_0797",
  "example_id": "nk_0797",
  "source_url": "https://huggingface.co/datasets/ekrombouts/fruta_records/blob/579141e3431c18a932fa3a0870e9f1c131f10367/data/train-00000-of-00001.parquet",
  "status": "COMPLETE",
  "error_category": null,
  "reason_code": "NO_SCOPED_PHRASE",
  "expected_label": "SUPERVISION",
  "predicted_label": "UNCLEAR"
}
```

Selected target:

```json
{
  "context_key": "other_walk",
  "observed_on": "2024-07-03",
  "resident_id": "fruta-ck_04",
  "resident_name": "Fruta synthetic resident ck_04",
  "target_cue": "walk with the walking frame during the afternoon shift"
}
```

Frozen note used for extraction:

```text
During the afternoon shift, the resident took a short walk with the walking frame. He was somewhat restless and saw things that were not there. We kept an extra close eye on whether he might fall. After the walk, we helped him with his lunch, which went well. He ate with enjoyment.
```

Original-language note:

```text
Tijdens de middagshift heeft dhr. een korte wandeling gemaakt met het looprek. Hij was wat onrustig en zag dingen die er niet waren. We hebben extra goed in de gaten gehouden of hij niet zou vallen. Na de wandeling hebben we hem geholpen met zijn lunch, wat goed ging. Hij at met smaak.
```

Expected exact evidence:

```json
[
  {
    "end": 196,
    "quote": "During the afternoon shift, the resident took a short walk with the walking frame. He was somewhat restless and saw things that were not there. We kept an extra close eye on whether he might fall.",
    "start": 0
  }
]
```

Predicted exact evidence:

```json
[]
```

#### nb_1319: Strict evidence span mismatch

Stored source and outcome:

```json
{
  "source_note_id": "nb_1319",
  "example_id": "nb_1319",
  "source_url": "https://huggingface.co/datasets/ekrombouts/fruta_records/blob/579141e3431c18a932fa3a0870e9f1c131f10367/data/train-00000-of-00001.parquet",
  "status": "COMPLETE",
  "error_category": null,
  "reason_code": "NO_SCOPED_PHRASE",
  "expected_label": "UNCLEAR",
  "predicted_label": "UNCLEAR"
}
```

Selected target:

```json
{
  "context_key": "other_walk",
  "observed_on": "2024-04-04",
  "resident_id": "fruta-cb_07",
  "resident_name": "Fruta synthetic resident cb_07",
  "target_cue": "short walk with the walking stick"
}
```

Frozen note used for extraction:

```text
During a short walk with the walking stick, the resident said that she felt a little more stable. She did tire quickly.
```

Original-language note:

```text
Tijdens een korte wandeling met de wandelstok gaf mw. aan dat ze zich wat stabieler voelde. Ze was wel snel moe.
```

Expected exact evidence:

```json
[
  {
    "end": 97,
    "quote": "During a short walk with the walking stick, the resident said that she felt a little more stable.",
    "start": 0
  }
]
```

Predicted exact evidence:

```json
[]
```

The label matches. The saved evidence span set differs from the strict frozen annotation; this report does not judge an alternative span semantically correct or incorrect.

#### nd_0297: Label mismatch

Stored source and outcome:

```json
{
  "source_note_id": "nd_0297",
  "example_id": "nd_0297",
  "source_url": "https://huggingface.co/datasets/ekrombouts/fruta_records/blob/579141e3431c18a932fa3a0870e9f1c131f10367/data/train-00000-of-00001.parquet",
  "status": "COMPLETE",
  "error_category": null,
  "reason_code": "PHRASE_MATCH",
  "expected_label": "UNCLEAR",
  "predicted_label": "HELP_UNSPECIFIED"
}
```

Selected target:

```json
{
  "context_key": "other_walk",
  "observed_on": "2025-01-23",
  "resident_id": "fruta-cd_02",
  "resident_name": "Fruta synthetic resident cd_02",
  "target_cue": "walk before the wheezing was observed"
}
```

Frozen note used for extraction:

```text
The resident was noticed to have increased wheezing in her chest after a walk; help and comfort were quickly offered.
```

Original-language note:

```text
Mw. werd opgemerkt met een verhoogde piepende borst na wandeling; hulp en troost werden snel aangeboden.
```

Expected exact evidence:

```json
[
  {
    "end": 117,
    "quote": "The resident was noticed to have increased wheezing in her chest after a walk; help and comfort were quickly offered.",
    "start": 0
  }
]
```

Predicted exact evidence:

```json
[
  {
    "end": 117,
    "quote": "The resident was noticed to have increased wheezing in her chest after a walk; help and comfort were quickly offered.",
    "start": 0
  }
]
```

#### na_1633: Strict evidence span mismatch

Stored source and outcome:

```json
{
  "source_note_id": "na_1633",
  "example_id": "na_1633",
  "source_url": "https://huggingface.co/datasets/ekrombouts/fruta_records/blob/579141e3431c18a932fa3a0870e9f1c131f10367/data/train-00000-of-00001.parquet",
  "status": "COMPLETE",
  "error_category": null,
  "reason_code": "NO_SCOPED_PHRASE",
  "expected_label": "UNCLEAR",
  "predicted_label": "UNCLEAR"
}
```

Selected target:

```json
{
  "context_key": "other_walk",
  "observed_on": "2024-03-05",
  "resident_id": "fruta-ca_08",
  "resident_name": "Fruta synthetic resident ca_08",
  "target_cue": "aimless walking before the carer took him to the garden"
}
```

Frozen note used for extraction:

```text
The resident had a restless afternoon. He walked around aimlessly and seemed anxious. The carer took him to the garden for some fresh air. This helped him relax a little.
```

Original-language note:

```text
Dhr. had een onrustige middag. Hij liep rond zonder doel en leek angstig. De verzorgende heeft hem meegenomen naar de tuin voor wat frisse lucht. Dit hielp hem om wat te ontspannen.
```

Expected exact evidence:

```json
[
  {
    "end": 85,
    "quote": "He walked around aimlessly and seemed anxious.",
    "start": 39
  }
]
```

Predicted exact evidence:

```json
[]
```

The label matches. The saved evidence span set differs from the strict frozen annotation; this report does not judge an alternative span semantically correct or incorrect.

#### nn_2108: Strict evidence span mismatch

Stored source and outcome:

```json
{
  "source_note_id": "nn_2108",
  "example_id": "nn_2108",
  "source_url": "https://huggingface.co/datasets/ekrombouts/fruta_records/blob/579141e3431c18a932fa3a0870e9f1c131f10367/data/train-00000-of-00001.parquet",
  "status": "COMPLETE",
  "error_category": null,
  "reason_code": "NO_SCOPED_PHRASE",
  "expected_label": "UNCLEAR",
  "predicted_label": "UNCLEAR"
}
```

Selected target:

```json
{
  "context_key": "other_walk",
  "observed_on": "2024-09-25",
  "resident_id": "fruta-cn_07",
  "resident_name": "Fruta synthetic resident cn_07",
  "target_cue": "quiet walk in the sun at the end of the afternoon"
}
```

Frozen note used for extraction:

```text
The afternoon ends with a quiet walk in the sun. The client is quiet and follows well, which helps to end his day positively.
```

Original-language note:

```text
De middag eindigt met een rustige wandeling in de zon. De client is stil en volgt goed, wat helpt om zijn dag positief af te sluiten.
```

Expected exact evidence:

```json
[
  {
    "end": 48,
    "quote": "The afternoon ends with a quiet walk in the sun.",
    "start": 0
  }
]
```

Predicted exact evidence:

```json
[]
```

The label matches. The saved evidence span set differs from the strict frozen annotation; this report does not judge an alternative span semantically correct or incorrect.

## Method 2: gemini / gemini-3.1-flash-lite

| N | Complete | Unavailable | Invalid | Analysis failures | Incorrect examples |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 24 | 24 | 0 | 0 | 0 | 8 |

Analysis failures are unavailable or invalid runs. Incorrect examples include those failures and every completed label or strict-span mismatch.

| Metric | Exact fraction |
| --- | ---: |
| Label agreement | 21/24 |
| Exact evidence span-set agreement | 16/24 |
| Joint agreement | 16/24 |

Every input remains in the denominator. Exact evidence requires the complete frozen set of half-open `(start, end, quote)` spans; partial overlaps and paraphrases fail this strict measure. Repeated predicted spans are retained in the comparison.

### Stored provenance

```json
{
  "schema_version": "1.0",
  "scope": "post_hoc_replay",
  "dataset": {
    "ids": [
      "ekrombouts/fruta_records"
    ],
    "revisions": [
      "579141e3431c18a932fa3a0870e9f1c131f10367"
    ],
    "sha256": "a2d3a2e8dbe1d119c8cb02064963f585849ee2f01d95f2d640c7cbf426b178cf",
    "splits": {
      "held_out": 24
    },
    "translation_ids": [
      "caresignal-agent-en-reviewed-v1"
    ]
  },
  "extractor": {
    "mode": "gemini",
    "model_id": "gemini-3.1-flash-lite",
    "prompt_version": "walking-assistance-v2",
    "version": "gemini-structured-v2"
  },
  "metrics_policy": "Exact span-set match; all examples including errors remain in denominator."
}
```

### Label distributions

| Label | Gold | Predicted in complete runs |
| --- | ---: | ---: |
| INDEPENDENT | 1 | 1 |
| SUPERVISION | 1 | 2 |
| HANDS_ON | 2 | 2 |
| HELP_UNSPECIFIED | 6 | 8 |
| UNCLEAR | 14 | 11 |
| No completed prediction | 0 | 0 |
| Total | 24 | 24 |

### Confusion table

Rows are gold labels. Columns are predicted labels or analysis-failure statuses.

| Gold \ Predicted | INDEPENDENT | SUPERVISION | HANDS_ON | HELP_UNSPECIFIED | UNCLEAR | UNAVAILABLE | INVALID | Total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| INDEPENDENT | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| SUPERVISION | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 1 |
| HANDS_ON | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 2 |
| HELP_UNSPECIFIED | 0 | 0 | 0 | 6 | 0 | 0 | 0 | 6 |
| UNCLEAR | 0 | 1 | 0 | 2 | 11 | 0 | 0 | 14 |
| Total | 1 | 2 | 2 | 8 | 11 | 0 | 0 | 24 |

### Error review

| Recorded category | Count |
| --- | ---: |
| Label and strict evidence mismatch | 3 |
| Strict evidence span mismatch | 5 |

#### nd_0902: Strict evidence span mismatch

Stored source and outcome:

```json
{
  "source_note_id": "nd_0902",
  "example_id": "nd_0902",
  "source_url": "https://huggingface.co/datasets/ekrombouts/fruta_records/blob/579141e3431c18a932fa3a0870e9f1c131f10367/data/train-00000-of-00001.parquet",
  "status": "COMPLETE",
  "error_category": null,
  "reason_code": "GENERIC_SUPPORT",
  "expected_label": "HELP_UNSPECIFIED",
  "predicted_label": "HELP_UNSPECIFIED"
}
```

Selected target:

```json
{
  "context_key": "other_walk",
  "observed_on": "2024-12-30",
  "resident_id": "fruta-cd_04",
  "resident_name": "Fruta synthetic resident cd_04",
  "target_cue": "short walk with the walker"
}
```

Frozen note used for extraction:

```text
Provided support during a shorter walk with the walker, during which her balance and awareness improved. The resident said that she felt safe.
```

Original-language note:

```text
Ondersteunde tijdens een kortere wandeling met de rollator, waarbij haar balans en bewustzijn werden verbeterd. Mw. zei dat ze zich veilig voelde.
```

Expected exact evidence:

```json
[
  {
    "end": 104,
    "quote": "Provided support during a shorter walk with the walker, during which her balance and awareness improved.",
    "start": 0
  }
]
```

Predicted exact evidence:

```json
[
  {
    "end": 54,
    "quote": "Provided support during a shorter walk with the walker",
    "start": 0
  }
]
```

The label matches. The saved evidence span set differs from the strict frozen annotation; this report does not judge an alternative span semantically correct or incorrect.

#### na_0762: Strict evidence span mismatch

Stored source and outcome:

```json
{
  "source_note_id": "na_0762",
  "example_id": "na_0762",
  "source_url": "https://huggingface.co/datasets/ekrombouts/fruta_records/blob/579141e3431c18a932fa3a0870e9f1c131f10367/data/train-00000-of-00001.parquet",
  "status": "COMPLETE",
  "error_category": null,
  "reason_code": "GENERIC_SUPPORT_WALK",
  "expected_label": "HELP_UNSPECIFIED",
  "predicted_label": "HELP_UNSPECIFIED"
}
```

Selected target:

```json
{
  "context_key": "other_walk",
  "observed_on": "2024-10-20",
  "resident_id": "fruta-ca_05",
  "resident_name": "Fruta synthetic resident ca_05",
  "target_cue": "walk with the walker described before sitting on the sofa"
}
```

Frozen note used for extraction:

```text
The resident had difficulty walking with the walker. We provided additional support. She was visibly anxious after last week's fall. After a short walk, she sat on the sofa for a while to recover.
```

Original-language note:

```text
Mw. had moeite met lopen met de rollator. We hebben extra ondersteuning geboden. Ze was zichtbaar angstig na de valpartij van vorige week. Na een kort wandelingetje heeft ze even op de bank gezeten om bij te komen.
```

Expected exact evidence:

```json
[
  {
    "end": 84,
    "quote": "The resident had difficulty walking with the walker. We provided additional support.",
    "start": 0
  }
]
```

Predicted exact evidence:

```json
[
  {
    "end": 84,
    "quote": "The resident had difficulty walking with the walker. We provided additional support.",
    "start": 0
  },
  {
    "end": 196,
    "quote": "After a short walk, she sat on the sofa for a while to recover.",
    "start": 133
  }
]
```

The label matches. The saved evidence span set differs from the strict frozen annotation; this report does not judge an alternative span semantically correct or incorrect.

#### na_0689: Strict evidence span mismatch

Stored source and outcome:

```json
{
  "source_note_id": "na_0689",
  "example_id": "na_0689",
  "source_url": "https://huggingface.co/datasets/ekrombouts/fruta_records/blob/579141e3431c18a932fa3a0870e9f1c131f10367/data/train-00000-of-00001.parquet",
  "status": "COMPLETE",
  "error_category": null,
  "reason_code": "PHYSICAL_SUPPORT_DOCUMENTED",
  "expected_label": "HANDS_ON",
  "predicted_label": "HANDS_ON"
}
```

Selected target:

```json
{
  "context_key": "other_walk",
  "observed_on": "2024-09-29",
  "resident_id": "fruta-ca_05",
  "resident_name": "Fruta synthetic resident ca_05",
  "target_cue": "short walk with the walker after lunch"
}
```

Frozen note used for extraction:

```text
At midday, the resident ate well, but she still seemed tired. After lunch, we took a short walk together with the walker. She had difficulty keeping her balance, but with my support it went reasonably well. We took it slowly.
```

Original-language note:

```text
Tijdens het middaguur heeft mevrouw goed gegeten, maar ze leek nog steeds moe. Na de lunch hebben we samen een korte wandeling gemaakt met de rollator. Ze had moeite om haar balans te houden, maar met mijn ondersteuning ging het redelijk. We hebben rustig aan gedaan.
```

Expected exact evidence:

```json
[
  {
    "end": 206,
    "quote": "After lunch, we took a short walk together with the walker. She had difficulty keeping her balance, but with my support it went reasonably well.",
    "start": 62
  }
]
```

Predicted exact evidence:

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

The label matches. The saved evidence span set differs from the strict frozen annotation; this report does not judge an alternative span semantically correct or incorrect.

#### nb_0960: Strict evidence span mismatch

Stored source and outcome:

```json
{
  "source_note_id": "nb_0960",
  "example_id": "nb_0960",
  "source_url": "https://huggingface.co/datasets/ekrombouts/fruta_records/blob/579141e3431c18a932fa3a0870e9f1c131f10367/data/train-00000-of-00001.parquet",
  "status": "COMPLETE",
  "error_category": null,
  "reason_code": "GUIDANCE_ONLY",
  "expected_label": "HELP_UNSPECIFIED",
  "predicted_label": "HELP_UNSPECIFIED"
}
```

Selected target:

```json
{
  "context_key": "walking_attempt",
  "observed_on": "2024-09-10",
  "resident_id": "fruta-cb_05",
  "resident_name": "Fruta synthetic resident cb_05",
  "target_cue": "attempt to walk to her room with the walker"
}
```

Frozen note used for extraction:

```text
The resident tried to walk independently to her room with the walker. She forgot how it works and had to be guided.
```

Original-language note:

```text
Mw. probeerde zelfstandig naar haar kamer te lopen met de rollator. Ze vergat hoe deze werkt en moest worden begeleid.
```

Expected exact evidence:

```json
[
  {
    "end": 115,
    "quote": "The resident tried to walk independently to her room with the walker. She forgot how it works and had to be guided.",
    "start": 0
  }
]
```

Predicted exact evidence:

```json
[
  {
    "end": 69,
    "quote": "The resident tried to walk independently to her room with the walker.",
    "start": 0
  },
  {
    "end": 115,
    "quote": "She forgot how it works and had to be guided.",
    "start": 70
  }
]
```

The label matches. The saved evidence span set differs from the strict frozen annotation; this report does not judge an alternative span semantically correct or incorrect.

#### nl_0727: Label and strict evidence mismatch

Stored source and outcome:

```json
{
  "source_note_id": "nl_0727",
  "example_id": "nl_0727",
  "source_url": "https://huggingface.co/datasets/ekrombouts/fruta_records/blob/579141e3431c18a932fa3a0870e9f1c131f10367/data/train-00000-of-00001.parquet",
  "status": "COMPLETE",
  "error_category": null,
  "reason_code": "VERBAL_GUIDANCE_ONLY",
  "expected_label": "UNCLEAR",
  "predicted_label": "HELP_UNSPECIFIED"
}
```

Selected target:

```json
{
  "context_key": "other_walk",
  "observed_on": "2024-07-17",
  "resident_id": "fruta-cl_04",
  "resident_name": "Fruta synthetic resident cl_04",
  "target_cue": "walking around during lunch; exclude help to sit back down"
}
```

Frozen note used for extraction:

```text
The resident was restless during lunch and kept getting up to walk around. He accepted guidance to sit back down.
```

Original-language note:

```text
Dhr. was onrustig tijdens de lunch en bleef opstaan om rond te lopen. Hij accepteerde begeleiding om weer te gaan zitten.
```

Expected exact evidence:

```json
[
  {
    "end": 74,
    "quote": "The resident was restless during lunch and kept getting up to walk around.",
    "start": 0
  }
]
```

Predicted exact evidence:

```json
[
  {
    "end": 113,
    "quote": "The resident was restless during lunch and kept getting up to walk around. He accepted guidance to sit back down.",
    "start": 0
  }
]
```

#### nk_0797: Strict evidence span mismatch

Stored source and outcome:

```json
{
  "source_note_id": "nk_0797",
  "example_id": "nk_0797",
  "source_url": "https://huggingface.co/datasets/ekrombouts/fruta_records/blob/579141e3431c18a932fa3a0870e9f1c131f10367/data/train-00000-of-00001.parquet",
  "status": "COMPLETE",
  "error_category": null,
  "reason_code": "SAFETY_WATCH_DURING_WALK",
  "expected_label": "SUPERVISION",
  "predicted_label": "SUPERVISION"
}
```

Selected target:

```json
{
  "context_key": "other_walk",
  "observed_on": "2024-07-03",
  "resident_id": "fruta-ck_04",
  "resident_name": "Fruta synthetic resident ck_04",
  "target_cue": "walk with the walking frame during the afternoon shift"
}
```

Frozen note used for extraction:

```text
During the afternoon shift, the resident took a short walk with the walking frame. He was somewhat restless and saw things that were not there. We kept an extra close eye on whether he might fall. After the walk, we helped him with his lunch, which went well. He ate with enjoyment.
```

Original-language note:

```text
Tijdens de middagshift heeft dhr. een korte wandeling gemaakt met het looprek. Hij was wat onrustig en zag dingen die er niet waren. We hebben extra goed in de gaten gehouden of hij niet zou vallen. Na de wandeling hebben we hem geholpen met zijn lunch, wat goed ging. Hij at met smaak.
```

Expected exact evidence:

```json
[
  {
    "end": 196,
    "quote": "During the afternoon shift, the resident took a short walk with the walking frame. He was somewhat restless and saw things that were not there. We kept an extra close eye on whether he might fall.",
    "start": 0
  }
]
```

Predicted exact evidence:

```json
[
  {
    "end": 82,
    "quote": "During the afternoon shift, the resident took a short walk with the walking frame.",
    "start": 0
  },
  {
    "end": 196,
    "quote": "We kept an extra close eye on whether he might fall.",
    "start": 144
  }
]
```

The label matches. The saved evidence span set differs from the strict frozen annotation; this report does not judge an alternative span semantically correct or incorrect.

#### na_1633: Label and strict evidence mismatch

Stored source and outcome:

```json
{
  "source_note_id": "na_1633",
  "example_id": "na_1633",
  "source_url": "https://huggingface.co/datasets/ekrombouts/fruta_records/blob/579141e3431c18a932fa3a0870e9f1c131f10367/data/train-00000-of-00001.parquet",
  "status": "COMPLETE",
  "error_category": null,
  "reason_code": "DIRECTED_ACCOMPANIMENT",
  "expected_label": "UNCLEAR",
  "predicted_label": "SUPERVISION"
}
```

Selected target:

```json
{
  "context_key": "other_walk",
  "observed_on": "2024-03-05",
  "resident_id": "fruta-ca_08",
  "resident_name": "Fruta synthetic resident ca_08",
  "target_cue": "aimless walking before the carer took him to the garden"
}
```

Frozen note used for extraction:

```text
The resident had a restless afternoon. He walked around aimlessly and seemed anxious. The carer took him to the garden for some fresh air. This helped him relax a little.
```

Original-language note:

```text
Dhr. had een onrustige middag. Hij liep rond zonder doel en leek angstig. De verzorgende heeft hem meegenomen naar de tuin voor wat frisse lucht. Dit hielp hem om wat te ontspannen.
```

Expected exact evidence:

```json
[
  {
    "end": 85,
    "quote": "He walked around aimlessly and seemed anxious.",
    "start": 39
  }
]
```

Predicted exact evidence:

```json
[
  {
    "end": 138,
    "quote": "The carer took him to the garden for some fresh air.",
    "start": 86
  }
]
```

#### nn_2108: Label and strict evidence mismatch

Stored source and outcome:

```json
{
  "source_note_id": "nn_2108",
  "example_id": "nn_2108",
  "source_url": "https://huggingface.co/datasets/ekrombouts/fruta_records/blob/579141e3431c18a932fa3a0870e9f1c131f10367/data/train-00000-of-00001.parquet",
  "status": "COMPLETE",
  "error_category": null,
  "reason_code": "GUIDANCE_ONLY",
  "expected_label": "UNCLEAR",
  "predicted_label": "HELP_UNSPECIFIED"
}
```

Selected target:

```json
{
  "context_key": "other_walk",
  "observed_on": "2024-09-25",
  "resident_id": "fruta-cn_07",
  "resident_name": "Fruta synthetic resident cn_07",
  "target_cue": "quiet walk in the sun at the end of the afternoon"
}
```

Frozen note used for extraction:

```text
The afternoon ends with a quiet walk in the sun. The client is quiet and follows well, which helps to end his day positively.
```

Original-language note:

```text
De middag eindigt met een rustige wandeling in de zon. De client is stil en volgt goed, wat helpt om zijn dag positief af te sluiten.
```

Expected exact evidence:

```json
[
  {
    "end": 48,
    "quote": "The afternoon ends with a quiet walk in the sun.",
    "start": 0
  }
]
```

Predicted exact evidence:

```json
[
  {
    "end": 48,
    "quote": "The afternoon ends with a quiet walk in the sun.",
    "start": 0
  },
  {
    "end": 125,
    "quote": "The client is quiet and follows well, which helps to end his day positively.",
    "start": 49
  }
]
```

This project is a prototype and is not medical advice.
