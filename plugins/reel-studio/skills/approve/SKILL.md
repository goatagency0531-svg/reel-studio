---
name: approve
description: Approve a reel script and produce it — voiceover, visuals and render. Use when the user approves a script or says to go ahead with a reel.
argument-hint: "[slug] [--own-recording]"
---

# Approve and produce

Arguments: $ARGUMENTS

1. Pick the reel: the slug given, otherwise the single reel in stage `needs_approval` (run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/status.py"`). If several, ask which.
2. `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/stage.py" <slug> approved "approved by user"`
3. Use the **reel-studio:editor** agent: "Reel reels/<slug> is approved. Make the voiceover (own recording: yes/no), prepare visuals, and render if all shots are ready."
4. If shots are missing (manual Higgsfield mode): show the user the shot list in a compact form (file name · type · seconds · prompt) and say:
   "Generate these in Higgsfield, save them into `reels/<slug>/visuals/` with those names, then run `/reel-studio:render <slug>`."
5. If it rendered: continue exactly as `/reel-studio:render` step 3 (poster + caption).
