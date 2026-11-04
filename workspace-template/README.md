# Reel workspace

Instagram Reels for one business, made with Reel Studio.

- `brand/`: the business profile (`brand.json`, `business.md`), logo, music, fonts
- `reels/<date-name>/out/`: finished `reel.mp4`, `cover.png`, `caption.txt`

## One-time setup (Claude Code on the web)
1. Open this repo in Claude Code on the web (claude.ai/code).
2. Cloud environment settings:
   - Environment variables: `ELEVENLABS_API_KEY` (+ `HIGGSFIELD_API_KEY`, `HIGGSFIELD_API_SECRET` if using the Higgsfield API)
   - Setup script: `apt-get update && apt-get install -y ffmpeg`
   - Network: allow api.elevenlabs.io (and the Higgsfield API host)
3. Start a session and run `/reel-studio:brand <business profile>`.
