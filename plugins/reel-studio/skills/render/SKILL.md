---
name: render
description: Render (or re-render) a reel after shots were added or edits were made, then make the cover, caption and deliver. Use after visuals are dropped in, to re-render after edits, or to remake the poster.
argument-hint: "[slug] [--draft] [--poster-only] [--placeholders-ok]"
---

# Render

Arguments: $ARGUMENTS

1. Pick the reel: the slug given, otherwise the most recent reel in `awaiting_visuals`, `visuals_ready` or `rendered`.
2. If the workspace is a git repo, run `git pull --ff-only` first (shots may have been uploaded to GitHub).
3. Unless `--poster-only`: use the **reel-studio:editor** agent: "Render reels/<slug>" (+ "draft" / "placeholders are ok").
   If shots are still missing and placeholders aren't ok → same reply as approve step 4, ending `STATUS: WAITING_FOR_SHOTS slug=<slug>`.
4. Use the **reel-studio:poster-designer** agent: "Make the cover and caption for reels/<slug>."
5. Unless `--draft`: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/deliver.py" <slug>`
6. Reply in the same format as approve step 7, ending `STATUS: DONE slug=<slug>`.

## Status protocol (a bot may be reading this session)
- Never open question dialogs (no AskUserQuestion). If something is missing, ask in plain text and end with `STATUS: NEED_INFO <one-line question>`.
- End **every** final reply with exactly one status line, alone on the last line, in English, no formatting:
  `STATUS: BRAND_SAVED` · `STATUS: NEEDS_APPROVAL slug=<slug>` · `STATUS: WAITING_FOR_SHOTS slug=<slug>` · `STATUS: DONE slug=<slug>` · `STATUS: NEED_INFO <question>` · `STATUS: ERROR <short reason>`
- Talk to the operator in English. Viewer-facing reel content stays in the brand language.
