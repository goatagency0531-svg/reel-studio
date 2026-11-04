---
name: approve
description: Approve a reel script and produce it — voiceover, visuals, render, cover, caption and delivery. Use when the user approves a script or says to go ahead with a reel.
argument-hint: "[slug] [--own-recording] [--placeholders-ok]"
---

# Approve and produce

Arguments: $ARGUMENTS

1. Pick the reel: the slug given, otherwise the single reel in stage `needs_approval` (`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/status.py"`). If several and none given, end with `STATUS: NEED_INFO Which reel? <slugs>`.
2. `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/stage.py" <slug> approved "approved"`
3. Use the **reel-studio:editor** agent: "Reel reels/<slug> is approved. Produce it." (+ "own recording" / "placeholders are ok" if given)
4. If the editor reports missing shots it could not generate: reply with the shot list (`file · type · seconds · prompt`, one per line), say the files go in `reels/<slug>/visuals/` (or pushed to the repo at that path), and end with `STATUS: WAITING_FOR_SHOTS slug=<slug>`.
5. Otherwise use the **reel-studio:poster-designer** agent: "Make the cover and caption for reels/<slug>."
6. Deliver: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/deliver.py" <slug>`
7. Reply:
```
REEL: <slug>
DURATION: <n>s
DELIVERY_REEL: <link>
DELIVERY_COVER: <link>
DELIVERY_CAPTION: <link>
CAPTION:
<full caption.txt content>
NOTES: <editor/poster flags, or "none">
```
Then: `STATUS: DONE slug=<slug>`

## Status protocol (a bot may be reading this session)
- Never open question dialogs (no AskUserQuestion). If something is missing, ask in plain text and end with `STATUS: NEED_INFO <one-line question>`.
- End **every** final reply with exactly one status line, alone on the last line, in English, no formatting:
  `STATUS: BRAND_SAVED` · `STATUS: NEEDS_APPROVAL slug=<slug>` · `STATUS: WAITING_FOR_SHOTS slug=<slug>` · `STATUS: DONE slug=<slug>` · `STATUS: NEED_INFO <question>` · `STATUS: ERROR <short reason>`
- Talk to the operator in English. Viewer-facing reel content stays in the brand language.
