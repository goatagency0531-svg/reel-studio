---
name: setup
description: First-time setup wizard for Reel Studio — creates the brand profile, API key file and folders in the current workspace, then checks the computer is ready. Use when the user installs Reel Studio, says "set up reel studio", or wants to change their brand settings.
disable-model-invocation: true
---

# Reel Studio setup

Set up the **current directory** as a Reel Studio workspace. Be friendly and brief; the user may not be technical.
Ask questions in small groups (use AskUserQuestion where it helps), not one giant form. Skip anything already filled in `brand/brand.json`.

## 1. Create the structure
```
brand/            brand.json, logo.png, music.mp3, fonts/, voice-samples.md
reels/
.env              API keys (never shared)
.gitignore        contains .env
```
Start `brand/brand.json` as a copy of `${CLAUDE_PLUGIN_ROOT}/templates/brand.example.json`.

## 2. Ask about the brand (write answers into brand.json)
- Brand name, Instagram handle, language for the reels (e.g. en, mn, es)
- Who the audience is (one sentence) and what they sell / want viewers to do
- Tone in 3 words; words they never want to say
- Default call to action
- Colors: primary, accent, text, background (hex). If they don't know, offer 3 palettes and let them pick.
- Style: `bold` (big word-by-word captions, punchy) or `minimal` (clean lower-third captions)
- Target length (default 35 s)

## 3. Files they can drop in (optional, tell them where)
- `brand/logo.png` (transparent PNG), `brand/music.mp3` (royalty-free bed music), `brand/fonts/*.ttf` (then set `fonts.family` and `fonts.bold_file`)
- `brand/voice-samples.md`: paste 3–5 captions or transcripts in their own words, so scripts sound like them

## 4. Keys
Explain plainly, then write `.env`:
- **ElevenLabs** (voice): API key from elevenlabs.io → Profile → API keys → `ELEVENLABS_API_KEY=`. Voice ID from the Voices page → `elevenlabs.voice_id` in brand.json. For non-English languages suggest `"model_id": "eleven_v3"` or `eleven_multilingual_v2` and testing both.
  No ElevenLabs? They can record themselves; the editor times captions to their recording.
- **Higgsfield** (visuals): default is `"mode": "manual"` — Reel Studio writes a shot list with prompts, they generate in Higgsfield and drop files in. If they have Higgsfield API access, set `"mode": "api"`, put `HIGGSFIELD_API_KEY` / `HIGGSFIELD_API_SECRET` in .env, and copy the endpoint paths from their Higgsfield API docs into `higgsfield.api` (beta).

Never print keys back to the chat. Never commit .env.

## 5. Check
Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/doctor.py"` (Windows: `python` / `py`) and help fix each ❌. If ffmpeg is missing give the one install command for their OS.

Finish with: "You're set. Start a reel with `/reel-studio:new <your idea>`."
