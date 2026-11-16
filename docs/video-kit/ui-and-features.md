# CareSignal UI and feature reference

The images in the pack are real screenshots of the working app. Text added outside those screenshots should be presented as editorial callouts, not as extra app controls.

## What the UI shows

The desktop screen has a pale teal mode sidebar; a CareSignal header; resident and observation selectors; a left column with the result, exact evidence and note history; and a right column with note entry, baseline confirmation and replacement forms. On narrow screens, context, result and evidence stack before editing controls.

| Feature | What to say | Screenshot |
| --- | --- | --- |
| Selected event | A finding belongs to one resident, walk context and observation date. | `01-elena-more-help.png` |
| Resident-specific baseline | The same note can compare differently for Elena and Ruth because their confirmed usual help differs. | `01-elena-more-help.png`, `02-ruth-matches.png` |
| Exact evidence | Highlighted words come from the current note; the usual-assistance source is shown separately. | `03-evidence-detail.png` |
| Human baseline confirmation | A specific help level, description and confirmation date are reviewed explicitly. | `06-confirm-usual-assistance.png` |
| Full replacement | A correction replaces the active source for that observation. | `04-attach-replacement.png` |
| Immutable history | Version 2 is current; version 1 remains corrected history. | `05-correction-history.png` |
| Unclear findings | A walker alone leaves human assistance unspecified. Missing evidence does not retain the old comparison. | `05-correction-history.png` |
| Narrow-screen layout | The app remains readable at phone width. | `07-mobile.png` |
| Multiple extraction methods | Fixed offline fixtures, a phrase matcher, and selectable Gemini/OpenAI adapters share evidence validation. | Sidebar in desktop images; only claim live inference when actual footage proves it |
| Traceable evaluation | Frozen source, translation and annotation versions, per-example exports and real error reports are in the repo. | Explain with a clearly editorial title card or a real report capture |

## Exact demo data

**Shared note:** “This morning she needed an aide beside her on the way to breakfast. She ate her breakfast in the dining room.”

**Elena:** documented supervision; confirmed usual Independent; More help than usual.

**Ruth:** documented supervision; confirmed usual Staff beside or supervising; Matches usual routine.

**Replacement:** “This morning she walked to breakfast with her walker. The note does not say whether anyone helped during the walk.”

**After replacement:** Unclear; active version 2; original version 1 marked Corrected.

## Visual system

Use off-white/light surfaces, a pale teal sidebar, dark teal text, restrained teal actions, amber quote highlights and a clean sans-serif. Screenshots are authoritative. Avoid inventing a dashboard, charts, alerts, patient avatars or clinical scores.

## Scope language

Describe **what a note documents about human walking help**. The model extracts; code compares eligible confirmed levels. The product does not diagnose, predict falls, recommend treatment, establish medical urgency, or replace staff judgment.

The main walkthrough is a disclosed fixed fixture. Live Gemini is an optional implemented path; the current default model is `gemini-3.1-flash-lite`. Engineering checks passed: 231 tests and Python 3.11/3.12 CI. A fresh unseen validation set is still needed for the revised prompt.

This project is a prototype and is not medical advice.
