# CareSignal Claude video kit

A ready-to-use production handoff for a **90-second hackathon demo video**.

For a quick tour of the working app, [watch or download the captioned feature recording](assets/09-quick-feature-tour.mp4). This separate MP4 shows resident comparisons, exact evidence, baseline confirmation, corrections and history, new-note analysis, AI settings, and the phone layout. It uses fictional data, fixture results and actual phrase-matcher extraction; the AI settings segment makes no live provider request. [Matching captions](assets/09-quick-feature-tour.srt) are included beside the recording.

## Start here

1. Download [the complete ZIP](../CareSignal-Claude-Kit.zip), then unzip it.
2. Upload **CareSignal-Visual-Brief.pdf** and the seven PNG screenshots to Claude. The MP4 is optional editing footage; if your Claude setup cannot accept video, the screenshots and PDF are sufficient.
3. Paste [master-prompt.md](master-prompt.md). It contains the full product facts, scene order, output requirements and truthful claim boundaries.
4. Ask Claude to export an MP4 where its tools support rendering. Otherwise, it should produce a runnable editing project or timed editor-ready package and explain the missing capability.

## Included

| File | Use |
| --- | --- |
| [master-prompt.md](master-prompt.md) | Copy-paste Claude production prompt |
| [CareSignal-Visual-Brief.pdf](CareSignal-Visual-Brief.pdf) | Illustrated UI/features and six-page production brief |
| [ui-overview.png](ui-overview.png) | Quick visual overview of real app states |
| [ui-and-features.md](ui-and-features.md) | Feature-to-image map and exact demo facts |
| [storyboard.md](storyboard.md) | Timed 90-second scene plan |
| [voiceover.txt](voiceover.txt) | 178-word narration |
| [subtitles.srt](subtitles.srt) | 19 timed subtitle cues |
| [voiceover-timing.md](voiceover-timing.md) | Narration/caption timing reference |
| [assets/screenshots](assets/screenshots/) | Seven actual app captures |
| [08-silent-walkthrough.mp4](assets/08-silent-walkthrough.mp4) | 29.4-second silent reference recording, 1080p/30fps |
| [ASSETS.json](ASSETS.json) | Machine-readable asset map |

## What the footage demonstrates

Elena’s More help than usual card → Ruth’s Matches usual routine card for the same note → exact evidence → full replacement → Unclear with original version preserved → explicit baseline review.

The source recording has no narration, music, or finished promotional editing. It is editing material for Claude or another video editor. It includes ordinary navigation/loading; trim those moments as needed. The separate still images are ready for zooms and readable close-ups.

Every pictured result is **Fixture demo**, a disclosed fixed fictional walkthrough. Do not label it live AI. The product separately implements Gemini extraction, and the repository preserves actual evaluation results.

Do not describe the post-hoc 21/24 replay as independently validated accuracy. Exact first-run and replay scope rules are in the master prompt. No credentials or `.env` contents are included.

This project is a prototype and is not medical advice.
