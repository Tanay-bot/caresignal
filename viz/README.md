# Divergence

A presentation visual (title → what CareSignal does → the note → the race → the swing → the verdict) of the frozen 24-note comparison (freeze commit `b28451c`): phrase baseline, `gemini-3.1-flash-lite` with prompt v1, and the prompt-v2 **post-hoc replay**.

Open `divergence.html` in a browser. It is one self-contained file with no network requests (CSP `default-src 'none'`), randomness or clock reads, so it works in airplane mode.

Regenerate from saved results only (no model calls):

```bash
python scripts/export_divergence.py
```

This writes `viz/data.json`, inlines it into `viz/src/divergence.template.html` → `viz/divergence.html`, and prints a coverage table.

Keys: `space`/`→` next · `←` back · `1–9`,`0` jump to note (two quick digits reach 11–24) · `a` autoplay (full-length) · `Shift+3` 3-minute preset autoplay · `v` prompt v1/v2 · `d` ribbon view (again: label ⇄ joint) · `l` limitations · `s` save PNG · `r` reset · `?` legend.

Segment durations for both timing profiles print to the browser console on load. The explainer uses the app's own fictional demo (Elena/Ruth), read from `caresignal/` and `app.py` at export time.
