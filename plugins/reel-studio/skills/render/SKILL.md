---
name: render
description: Render a reel's video and make its cover and caption. Use after visuals are dropped in, to re-render after edits, or to remake the poster.
argument-hint: "[slug] [--draft] [--poster-only]"
---

# Render

Arguments: $ARGUMENTS

1. Pick the reel: given slug, otherwise the most recent reel in `awaiting_visuals`, `visuals_ready` or `rendered`.
2. Unless `--poster-only`: use the **reel-studio:editor** agent: "Render reels/<slug>" (+ "draft" if `--draft`; + "render anyway with placeholders" if the user said so).
3. Use the **reel-studio:poster-designer** agent: "Make the cover and caption for reels/<slug>."
4. Show the user:
   - `reels/<slug>/out/reel.mp4` (duration), `out/cover.png`, `out/caption.txt` contents
   - anything the editor flagged
   - "Post: upload reel.mp4, choose cover.png as the cover, paste caption.txt."
