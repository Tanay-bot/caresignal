# Two-minute demo

Start with `uv run streamlit run app.py`. To enable Gemini from a local ignored `.env`, launch with `uv run --env-file .env streamlit run app.py`; the app does not read `.env` automatically. The credential-free workflow remains available.

1. Keep **Fixture demo** selected and click **Load demo**. Select **Elena**. Read **Staff beside or supervising** and **More help than usual**. Open **View evidence** and inspect the exact note beside her confirmed independent breakfast routine.
2. Switch to **Ruth**. The note is the same, while the card shows **Matches usual routine** because her confirmed usual level is staff supervision for the same outbound breakfast walk. The comparison comes from code and the two explicit confirmations.
3. Return to Elena. Open **Attach replacement**, choose **Use demo replacement**, then submit. Version 2 becomes active. It mentions a walker but leaves human help unspecified, so the prior comparison and citation clear.
4. Expand **Note history**. Version 1 remains available as corrected history. Current evidence comes from version 2.
5. For the live path, choose **Live AI**, select **Gemini**, and click **Load Fruta example**. The configured default is `gemini-3.1-flash-lite`; `GEMINI_MODEL` can override it. Inspect the result's actual model, method and source version, then expose the original Dutch for `nn_1093`. The expected finding is **Hands-on help**, supported by the walking attempt and physical-support sentence together. A provider failure produces a retryable unavailable result. Fixture mode offers the disclosed development expectation without making a model call.
6. Finish with the [first recorded 24-note comparison](heldout-results/summary.md), its [per-example results](heldout-results/results.json), and the [methods](heldout-methods.md). The phrase matcher matched 14/24 reference labels and 8/24 label-plus-evidence pairs; Gemini matched 11/24 labels and 7/24 pairs. Both completed all 24 without API errors. Show an actual error from the [error analysis](heldout-results/error-analysis.md) and explain what needs improvement.

For a command-line replay of the fictional workflow, run `uv run python -m caresignal.demo`. For evaluation commands and the distinction between the first measurement and later replays, see [evaluation.md](evaluation.md).

Present the limits plainly: these are 24 deliberately stratified synthetic notes with translations and reference labels reviewed by two assistant contexts, without human or clinical-expert annotation. The first Gemini result does not beat the phrase baseline on label or joint accuracy. Prompt `walking-assistance-v2` adds fictional policy examples after reviewing those results; any replay of the same 24 notes is a post-hoc follow-up, not independent held-out evidence. The [follow-up directory](heldout-followup/) keeps those artifacts separate from the first run.

The historical `gemini-3.8-flash` development success on `nn_1093` remains recorded in [gemini-development-results](gemini-development-results/). It is one disclosed development example, not a performance estimate or evidence that that model remains available.

This project is a prototype and is not medical advice.
