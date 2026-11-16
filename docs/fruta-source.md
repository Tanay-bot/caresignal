# Frozen Fruta development example

The public [Fruta Records dataset](https://huggingface.co/datasets/ekrombouts/fruta_records), authored by Eva Rombouts, contains artificial Dutch nursing-home notes. Its [dataset card at the frozen revision](https://huggingface.co/datasets/ekrombouts/fruta_records/blob/579141e3431c18a932fa3a0870e9f1c131f10367/README.md) explicitly says it contains no real patient data and declares the MIT license in its metadata. The generation code is linked by the author at [GenCareAI](https://github.com/ekrombouts/GenCareAI).

The exact `nn_1093` record was read from `data/train-00000-of-00001.parquet` at dataset revision `579141e3431c18a932fa3a0870e9f1c131f10367`. The record belongs to synthetic client `cn_04`, scenario `sn_046`, and is dated `2024-03-07 08:00:00+00:00`.

The frozen file [data/fruta_nn_1093.json](../data/fruta_nn_1093.json) contains the original Dutch, English translation, source links, dataset revision, and SHA-256 hashes of the original text, translation, and upstream Parquet file. The English translation was authored by the Codex coding agent, is identified as `caresignal-agent-en-literal-v1`, and has not been independently reviewed. No separate translation service or translation-model API was used. The awkward final source phrase about safety is preserved as “clarified safety,” without adding a clinical interpretation.

Original:

> Mw. maakte een poging om zelf te lopen, maar stelde vast dat ze steun nodig had. We gaven haar fysieke ondersteuning en verduidelijkten de veiligheid.

Frozen English:

> The resident attempted to walk on her own, but found that she needed support. We gave her physical support and clarified safety.

The brief's development expectation is `HANDS_ON`, with both adjacent sentences quoted together to bind the physical support to the walking attempt. This example has been inspected during implementation and must remain in the **development** split. It cannot count toward held-out extraction performance. It does not establish a comparable resident baseline.

A real historical Gemini check is recorded in [gemini-development-results/results.json](gemini-development-results/results.json): model `gemini-3.8-flash`, extractor `gemini-structured-v1`, prompt `walking-assistance-v1` returned `COMPLETE` / `HANDS_ON` with the exact full two-sentence English span. The input hash is `402f819b3b610fd760591c8dc876ff4cc4597c1c030e03c5b2923f2cad56c49e`. This establishes one successful disclosed development path; it is not a held-out performance estimate or a promise of continued model availability.

The current Gemini default is `gemini-3.1-flash-lite` with extractor `gemini-structured-v2` and prompt `walking-assistance-v2`. The separately frozen 24-note public sample excludes `nn_1093` and its original-text fingerprint. Its translation/annotation procedure, source hashes and first-run runtime amendment are documented in [heldout-methods.md](heldout-methods.md). Two assistant contexts reviewed that sample's translations and reference labels; this development note retains its separate literal-v1 provenance. Neither annotation process is human or clinical-expert gold.

The [first 24-note comparison](heldout-results/results.json) used prompt `walking-assistance-v1` and remains unchanged. Replaying the same sample with the current v2 prompt is a post-hoc follow-up, not independent held-out evidence. See [evaluation.md](evaluation.md) for measured counts, limits and commands.
