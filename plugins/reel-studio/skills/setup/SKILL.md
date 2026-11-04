---
name: setup
description: Interactive first-time setup for a human using Reel Studio directly (bots should use /reel-studio:brand instead). Creates the brand profile and checks the computer is ready.
disable-model-invocation: true
---

# Reel Studio setup (interactive)

Ask the user, in small groups and plain language, for: brand name, handle, reel language, audience, offer, tone (3 words), banned words, default CTA, colors (offer 3 palettes if unsure), style (`bold`/`minimal`), target length.
Then do everything `/reel-studio:brand` does with those answers (read `${CLAUDE_PLUGIN_ROOT}/skills/brand/SKILL.md`).

Keys (never ask for them in chat, never print them):
- Running in Claude Code on the web: add `ELEVENLABS_API_KEY` (and `HIGGSFIELD_API_KEY`, `HIGGSFIELD_API_SECRET` if using the Higgsfield API) as environment variables in the cloud environment settings; add `apt-get install -y ffmpeg` to the environment's setup script if `doctor.py` says ffmpeg is missing. Start a new session afterwards.
- Running locally: put them in `.env` in the workspace (already git-ignored).
- ElevenLabs voice ID goes in `brand/brand.json` → `elevenlabs.voice_id`.
- Higgsfield: a connected Higgsfield MCP server or an API key both work; with neither, the shot list is produced for manual generation.

Finish by running `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/doctor.py"` and helping fix each ❌.
