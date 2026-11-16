# Two-minute demo

1. Run `uv run streamlit run app.py`, keep **Fixture demo** selected and click **Load demo**.
2. Select **Elena**. Read **Staff beside or supervising** and **More help than usual**. Open **View evidence** and inspect the exact note text alongside her confirmed independent breakfast routine.
3. Switch to **Ruth**. The note text stays the same; the card shows **Matches usual routine** because her confirmed usual level is staff supervision for the same outbound breakfast walk.
4. Return to Elena. Open **Attach replacement**, choose **Use demo replacement** and submit. Version 2 becomes active. The replacement mentions a walker but leaves human help unspecified, so the previous comparison clears.
5. Expand **Note history**. Version 1 remains available as corrected history. The current evidence comes from version 2.
6. Optional: load the public **Fruta nn_1093** development example. Inspect the two-sentence walking attempt and physical-support evidence and expose the original Dutch source. The mode displayed with the result identifies the method actually used.
7. For a custom fictional note, select **Phrase matcher**, or configure `OPENAI_API_KEY` and select **Live AI**. Fixture mode supports the frozen walkthrough; it does not pretend to analyze arbitrary input.

For a command-line replay, run `uv run python -m caresignal.demo`.

Live inference on `nn_1093` and held-out AI-versus-phrase scores remain pending until the required credentials and frozen held-out annotations are available. Do not present development checks as performance estimates.

This project is a prototype and is not medical advice.
