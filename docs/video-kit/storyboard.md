# CareSignal — 90-second storyboard

Use real screenshots or recorded UI footage. The central walkthrough is **Fixture demo**, clearly labeled as a fixed fictional walkthrough. Do not imply that the pictured fixture results came from live Gemini inference.

| Time | Screen / asset | Action or editorial motion | On-screen text | Narrative purpose |
| --- | --- | --- | --- | --- |
| 00:00–00:13 | CareSignal title over `01-elena-more-help.png` | Gentle reveal; crop to resident/context/date and the note | CareSignal / Walking assistance, grounded in the note | Establish documentation-review purpose and the selected event |
| 00:13–00:18 | `01-elena-more-help.png` | Keep the actual mode indicator readable | Fixture demo · fictional walkthrough | Disclose fixed fictional results clearly |
| 00:18–00:32 | `01-elena-more-help.png` | Emphasize documented and usual levels, then result | Documented: staff beside / Usual: independent / More help than usual | Show Elena’s comparison and its explicit baseline |
| 00:32–00:44 | `02-ruth-matches.png` | Cut or recorded switch; preserve note text in view | Same note. Different confirmed routine. / Matches usual routine | Show resident-specific comparison rather than a universal flag |
| 00:44–00:58 | `03-evidence-detail.png` | Pan between amber quote and baseline source; pause to read | Exact note evidence / Staff-confirmed usual assistance / Active source version | Demonstrate traceability and separate evidence sources |
| 00:58–01:06 | `04-attach-replacement.png` | Show original revision, complete replacement and explicit submission | This replacement becomes the current source. | Explain the correction action before the state change |
| 01:06–01:15 | `05-correction-history.png` | Move from Unclear to versions 2/1; no fabricated cursor if screenshot-only | Version 2: Active / Version 1: Corrected / Human help unspecified | Show flag clearing and preserved history; a walker is a device |
| 01:15–01:24 | `06-confirm-usual-assistance.png`, then `07-mobile.png` | Short editorial montage; indicate optional Gemini and separately recorded evaluation | Explicit confirmation / Narrow-screen layout / Gemini option | Briefly cover supporting features without crowding the core story |
| 01:24–01:30 | Closing card using actual UI colors | Hold; show the statement fully | CareSignal / This project is a prototype and is not medical advice. | Finish with scope and a readable prototype disclosure |

## Editing notes

- Prefer 1080p, 16:9, H.264, 30 fps. Use a calm 90-second voiceover and matching captions.
- Keep the real UI labels, source version, observation date and Fixture demo mode legible.
- For still screenshots, use restrained pans and callouts. Never describe those pans as a live screen recording.
- All demo residents and walkthrough notes are fictional. No patient images or clinical stock footage are needed.
- Preserve the exact source note and replacement text from `master-prompt.md`.
- Optional technical callout: Python · Streamlit · Pydantic · SQLite · Gemini; 231 tests; Python 3.11/3.12 CI passed. These are engineering facts, not evidence of clinical accuracy.
- Omit model-score charts in this short cut unless their small-sample, agent-reviewed and post-hoc scope can remain readable. Full verified numbers and restrictions are in `master-prompt.md`.
- Use the supplied narration and SRT as editable timing assets. If actual recording duration differs, retime captions to speech rather than speeding through the evidence.
