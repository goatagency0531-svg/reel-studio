---
name: auto
description: Make a complete reel in one go with no approval stop — script, review, voice, visuals, render, cover, caption, delivery. Use only when explicitly asked for a fully automatic reel.
argument-hint: "<idea or brief>"
disable-model-invocation: true
---

# Fully automatic reel

Brief: $ARGUMENTS

Do `/reel-studio:new` steps 1–7 (the reviewer's verdict must be `pass`; if after 2 rounds it is still `revise`, stop and reply as the approval gate with `STATUS: NEEDS_APPROVAL slug=<slug>`).
Then do `/reel-studio:approve <slug>` steps 2–7. Include the script table (HOOK + BEATS) above the delivery block in the final reply.

## Status protocol (a bot may be reading this session)
- Never open question dialogs (no AskUserQuestion). If something is missing, ask in plain text and end with `STATUS: NEED_INFO <one-line question>`.
- End **every** final reply with exactly one status line, alone on the last line, in English, no formatting:
  `STATUS: BRAND_SAVED` · `STATUS: NEEDS_APPROVAL slug=<slug>` · `STATUS: WAITING_FOR_SHOTS slug=<slug>` · `STATUS: DONE slug=<slug>` · `STATUS: NEED_INFO <question>` · `STATUS: ERROR <short reason>`
- Talk to the operator in English. Viewer-facing reel content stays in the brand language.
