---
name: new
description: Start a new Instagram reel from an idea — the scriptwriter drafts it, the reviewer redacts and scores it, then it waits for the user's approval. Use when the user wants a new reel, script or video idea turned into a reel.
argument-hint: "<idea or brief>"
---

# New reel

Idea: $ARGUMENTS

1. If `brand/brand.json` doesn't exist, tell the user to run `/reel-studio:setup` first and stop.
2. If the idea is empty or too vague to write 30 seconds about, ask one question to sharpen it (who it's for / the one point / any proof or example). Otherwise don't ask anything.
3. Create the reel folder: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/new_reel.py" "<idea>"` → prints the slug. Add anything useful from the conversation (links, numbers, examples) to `reels/<slug>/brief.md`.
4. Use the **reel-studio:scriptwriter** agent: "Write the script for reels/<slug>."
5. `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/stage.py" <slug> in_review`, then use the **reel-studio:reviewer** agent: "Review and redact reels/<slug>."
6. If the verdict is `revise`: send `notes_for_writer` back to the scriptwriter once, then review again. Max 2 rounds.
7. `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/stage.py" <slug> needs_approval`

## Show the user (the approval gate)
- Hook + score (before → after)
- The script as a short table: beat · voiceover · on-screen · visual (type + 6-word summary)
- Estimated length
- Anything the reviewer flagged

End with: "Approve with `/reel-studio:approve <slug>` — or tell me what to change." Do not spend credits on voice or visuals before approval.
If they ask for changes, edit script.json directly (or re-run the scriptwriter for big changes) and show the changed beats.
