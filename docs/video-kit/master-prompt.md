# Claude master prompt — CareSignal demo video

Copy everything below into Claude and attach the supplied screenshots, storyboard, voiceover and any screen recording included in this pack.

---

You are the video producer and editor for **CareSignal**, a working hackathon prototype. Create a clear **90-second product demo video** from the attached real UI assets. Explain what the product does, demonstrate the important interactions, and finish with an honest prototype statement. Use plain English and a calm, confident presentation.

## Deliver the video, where your tools allow it

- Preferred output: `caresignal-demo.mp4`, 1920×1080, 16:9, H.264, 30 fps, with narration and readable captions. Also provide `subtitles.srt`, the final voiceover script, and the editable source/project.
- If you can render video in your environment, actually render it, inspect representative frames, confirm duration and audio, and provide the exported file. A storyboard or source code alone is not an exported video.
- If video rendering or speech generation is unavailable, state that briefly and provide the closest executable result: a complete runnable Remotion/FFmpeg project with exact asset names, an export command, narration script and SRT. If even code execution is unavailable, provide an editor-ready timed shot list, complete narration, captions and asset map. Do not claim an MP4 exists unless you created it.
- Use the attached screen recording if provided. Otherwise animate the actual screenshots with restrained pans, crops and callouts. Still-image animations must not pretend to be a recorded live interaction.

## Product facts — source of truth

**Product name:** CareSignal.

**Project repository:** https://github.com/Tanay-bot/caresignal (private). If you can access it, read the README and `docs/demo-script.md`. The attached assets and product facts below are sufficient to make the video; private-repository access is not required. Do not request or reveal API keys.

**One-sentence description:** CareSignal highlights what a shift note documents about human help for a selected walk, then compares that evidence with a staff-confirmed description of the resident’s usual help when one is available.

**Audience:** Hackathon judges and teammates reviewing a prototype for fictional memory-care handoffs.

**What exists:** A Python/Streamlit app with Pydantic contracts, local SQLite evidence history, a phrase matcher, fixed offline fixtures, a native Gemini adapter, and a selectable OpenAI adapter. The default Gemini model is `gemini-3.1-flash-lite`. The project has 231 passing tests and passing Python 3.11/3.12 CI. OpenAI live account availability has not been verified.

**The five documented-help labels:**
1. Independent.
2. Staff beside or supervising.
3. Hands-on help.
4. Help documented, type unspecified.
5. Unclear.

The model reads the selected event in the note. Deterministic code compares the result with an eligible, explicitly staff-confirmed baseline for the same resident/context/date. The output concerns documentation. It does not diagnose, predict falls, rank medical severity or recommend treatment.

**Required sentence, verbatim, visible on the closing screen and spoken if narration is available:**
> This project is a prototype and is not medical advice.

## Real UI and attached image map

Use the screenshots as the visual source of truth. Preserve their wording, result states, mode indicator and evidence. Do not redesign the app or invent extra screens.

| Asset | What it proves | What to focus on |
| --- | --- | --- |
| `01-elena-more-help.png` | Elena’s documented supervision is above her independent baseline | Selected resident/walk/date; More help than usual; Documented help; Usual help |
| `02-ruth-matches.png` | The same note yields a different comparison because Ruth’s baseline differs | Matches usual routine; supervision baseline; unchanged note |
| `03-evidence-detail.png` | The result is linked to exact source words and a separate confirmed baseline | Amber quote highlight; active note version/date; usual-assistance description |
| `04-attach-replacement.png` | A correction is a full replacement of the selected active source | Original revision, replacement form, explicit submission |
| `05-correction-history.png` | Version 2 is current, the old flag clears, and version 1 remains corrected history | Unclear result; Version 2 Active; Version 1 Corrected |
| `06-confirm-usual-assistance.png` | A person explicitly reviews and confirms the baseline | Specific level, description, confirmation date and agreement checkbox |
| `07-mobile.png` | The UI stacks at a narrow width | Resident/context before result/evidence; readable mobile layout |

The optional `assets/08-silent-walkthrough.mp4` is a 29.4-second silent 1920×1080/30fps recording of this fixture workflow; it is editing source, not a finished 90-second movie. `ASSETS.json` gives exact paths. If your tools cannot read video, use the seven PNGs and the PDF instead. If the pack includes filenames beyond this list, inspect them and use only assets whose visible content supports the scene. If a required state is absent, describe the gap; do not fabricate an app screenshot. You may create clearly editorial title cards and feature callouts around the supplied screenshots.

## Exact fictional walkthrough

The central walkthrough uses **Fixture demo**, a disclosed fixed-output mode that works without credentials. Keep a readable “Fixture demo · fictional walkthrough” label when showing it. Do not relabel these frames as live Gemini analysis.

Both residents use this exact note:

> This morning she needed an aide beside her on the way to breakfast. She ate her breakfast in the dining room.

The selected event is the outbound breakfast walk on January 15, 2026. It is a fictional demo observation, not the recording date.

1. **Elena:** Documented help is **Staff beside or supervising**. Her staff-confirmed usual level is **Independent**. The comparison is **More help than usual**.
2. **Ruth:** The note is unchanged. Her usual level is **Staff beside or supervising**, so the comparison becomes **Matches usual routine**. Explain that the difference comes from the confirmed baseline.
3. Open the evidence: quote highlight in the active note and the separate baseline source/confirmation date.
4. Return to Elena and attach this full replacement:

> This morning she walked to breakfast with her walker. The note does not say whether anyone helped during the walk.

5. The replacement becomes active version 2. A walker alone does not specify human help, so the result becomes **Unclear** and the prior comparison clears. Version 1 remains in history as **Corrected**. Only version 2 supplies current evidence.
6. Briefly show explicit baseline confirmation and the narrow-screen UI as supporting features.

## Suggested 90-second structure

- **0–13s:** CareSignal title, actual UI preview, selected event and the documentation-review purpose.
- **13–18s:** Explicitly identify the fixed fictional walkthrough while preserving the Fixture demo mode indicator.
- **18–32s:** Elena: documented supervision versus her independent baseline → More help than usual.
- **32–44s:** Switch to Ruth: same note, different confirmed baseline → Matches usual routine.
- **44–58s:** Evidence close-up: exact quote, active source version/date and staff-confirmed baseline; code calculates the comparison.
- **58–66s:** Attach the replacement note. Explain that it becomes the current source.
- **66–75s:** Show Unclear and the two-version history. The old note remains traceable.
- **75–84s:** Supporting features: explicit baseline confirmation, mobile layout, Gemini option and separately recorded evaluation. Do not mislabel screenshots as live analysis.
- **84–90s:** CareSignal closing title and the exact prototype statement. Hold the text long enough to read.

Use the attached `storyboard.md`, `voiceover.txt` and `subtitles.srt` as a starting point. Adjust narration timing naturally while keeping the product facts and disclosures intact.

## Visual direction

- Professional, quiet and readable; keep the UI dominant.
- Off-white page, pale teal sidebar, dark teal headings/body, restrained teal buttons, and amber evidence highlights. Match the screenshots. Declared UI palette includes `#F7FAFB`, `#EAF2F3`, `#142F35`, and `#087F8C`; app overrides include `#F7FAF9`, `#EAF2F0`, `#163D3A`, `#193F3B`, and `#176C63`.
- Use a clean system sans-serif or Inter. Add short text callouts, slow zooms, simple crossfades and subtle pointer emphasis where appropriate.
- Avoid tiny full-screen text, fast cursor movement, dramatic hospital stock footage, fake patients, medical monitor graphics, emergency alerts, flashy 3D transitions, or unsupported clinical imagery.
- Captions should be readable at laptop width, at most two lines per cue, with safe margins and adequate contrast. Do not cover the result or cited evidence.
- Narration should sound like a student founder explaining a real prototype, not an advertisement. Background music is optional and must stay quiet under speech.

## Accuracy and evaluation rules

The video may focus on the working workflow and omit numerical model scores. If you include scores, you must show the complete scope rather than an unqualified “87.5% accurate” claim:

- First frozen 24-note comparison: Gemini matched **11/24 labels** and **7/24 label-plus-exact-evidence pairs**; phrase matcher matched **14/24 labels** and **8/24 pairs**.
- After prompt changes, a **post-hoc replay of those same 24 notes** matched **21/24 labels** and **16/24 label-plus-exact-evidence pairs**. Six initial rate-limit failures were retried once with pacing and retained in the attempt history.
- The replay is not independent held-out validation. The sample is small, deliberately stratified and synthetic. Translations and reference labels were reviewed by coding agents, not human clinicians. Fresh validation is still needed.
- Never claim clinical validation, patient outcomes, fall prevention, diagnosis, HIPAA compliance, production readiness, integration with clinical systems, or superiority to the phrase baseline on the original held-out run.
- Never expose credentials or `.env` contents. Use only the fictional residents and supplied public synthetic examples.

## Final handoff checklist

Provide the exported MP4 if supported, the editable project/source or editor-ready fallback, the narration script, SRT captions, asset-to-scene map and a short verification note. The note should say what you actually rendered or checked, which assets were real screenshots/recording, and whether any speech/export capability was unavailable. Include a thumbnail/title recommendation, but do not let packaging replace the finished deliverable.

Proceed using these defaults. Ask only if a missing asset genuinely prevents completion.
