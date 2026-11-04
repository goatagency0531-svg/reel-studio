---
name: new
description: Start a new Instagram reel from an idea — the scriptwriter drafts it, the reviewer redacts and scores it, then it waits for approval. Use when the user wants a new reel, script or video idea turned into a reel.
argument-hint: "<idea or brief>"
---

# New reel

Brief: $ARGUMENTS

1. If `brand/brand.json` doesn't exist: reply that the brand profile is missing and end with `STATUS: NEED_INFO Send the business profile with /reel-studio:brand`.
2. If the brief is empty or too vague to write 30 seconds about, end with `STATUS: NEED_INFO <the one question that would fix it>`. Otherwise ask nothing.
3. Create the reel folder: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/new_reel.py" "<short title of the idea>"` → prints the slug. Write the full brief (everything useful you were given: offer, numbers, examples, audience notes) into `reels/<slug>/brief.md`.
4. Use the **reel-studio:scriptwriter** agent: "Write the script for reels/<slug>."
5. `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/stage.py" <slug> in_review`, then the **reel-studio:reviewer** agent: "Review and redact reels/<slug>."
6. If the verdict is `revise`: send `notes_for_writer` to the scriptwriter once, then review again. Max 2 rounds.
7. `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/stage.py" <slug> needs_approval`

## Reply (the approval gate)
```
REEL: <slug>
HOOK: <hook line, brand language>
SCORE: <before> -> <after>
LENGTH: ~<n>s
BEATS:
1. VO: <voiceover> | TEXT: <on_screen> | VISUAL: <type> – <6-word summary>
2. ...
CAPTION: <caption first line>
COVER: <poster headline>
NOTES: <reviewer flags, or "none">
```
Then: `STATUS: NEEDS_APPROVAL slug=<slug>`

Do not spend credits on voice or visuals before approval. If asked for changes: edit script.json (or re-run the scriptwriter for big changes), reply in the same format with the changed beats, and end with NEEDS_APPROVAL again.

## Status protocol (a bot may be reading this session)
- Never open question dialogs (no AskUserQuestion). If something is missing, ask in plain text and end with `STATUS: NEED_INFO <one-line question>`.
- End **every** final reply with exactly one status line, alone on the last line, in English, no formatting:
  `STATUS: BRAND_SAVED` · `STATUS: NEEDS_APPROVAL slug=<slug>` · `STATUS: WAITING_FOR_SHOTS slug=<slug>` · `STATUS: DONE slug=<slug>` · `STATUS: NEED_INFO <question>` · `STATUS: ERROR <short reason>`
- Talk to the operator in English. Viewer-facing reel content stays in the brand language.
