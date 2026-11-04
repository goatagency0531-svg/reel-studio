# Reel Studio

Your AI Reels team inside Claude Code.

| Role | What it does |
|---|---|
| ✍️ Scriptwriter | Writes the hook, beats, on-screen text, Higgsfield prompts, caption |
| 🔎 Reviewer | Scores the script against a 7-point rubric, rewrites weak lines, gives a pass/revise verdict |
| 🎬 Editor | ElevenLabs voiceover → Higgsfield visuals → cuts, zooms, word-by-word captions, emphasis cards, music ducking, logo, progress bar |
| 🖼️ Poster designer | Cover image (grid-safe) + ready-to-paste caption |

You approve every script before any credits are spent.

## Requirements
- Claude Code
- Python 3.9+ and ffmpeg (`brew install ffmpeg` · `winget install ffmpeg` · `apt install ffmpeg`)
- Optional: ElevenLabs account (or record your own voice), Higgsfield account

## Install
```
/plugin marketplace add <your-repo-or-folder>
/plugin install reel-studio@reel-studio
```
Then make a folder for your content, open Claude Code in it, and run:
```
/reel-studio:setup
```

## Make a reel
```
/reel-studio:new 3 mistakes cafés make on Instagram
/reel-studio:approve
# manual Higgsfield mode: generate the shots listed in visuals/SHOTLIST.md and drop them in
/reel-studio:render
```
Output: `reels/<date-name>/out/reel.mp4`, `cover.png`, `caption.txt`.

`/reel-studio:status` shows every reel and what's next.

## Your workspace
```
brand/brand.json      your brand profile (edit any time)
brand/logo.png        optional
brand/music.mp3       optional background music (ducked under the voice)
brand/fonts/          optional custom fonts
reels/<slug>/
  brief.md  script.json  review.md  hooks.md
  voice/    voice.mp3  timing.json
  visuals/  b1.mp4  b2.png  …  SHOTLIST.md
  out/      reel.mp4  cover.png  cover_grid.jpg  caption.txt
```

## Visual types per beat
- `ai_video`: Higgsfield clip (looped/trimmed to fit, punch zoom)
- `ai_image`: Higgsfield image (Ken Burns zoom)
- `footage`: your own clip, saved as `visuals/<beat>.mp4`
- `text_card`: branded card with big text

## Own voice instead of ElevenLabs
Record the approved script, save it as `reels/<slug>/voice/voice.mp3`, and run `/reel-studio:approve <slug> --own-recording`.

## Higgsfield API mode (beta)
Manual mode works with every plan. If you have API access, set `higgsfield.mode` to `api` in brand.json, add your keys to `.env`, and fill in the endpoint paths from your Higgsfield API docs.
