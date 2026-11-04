# Reel Studio workspace

This repository is one business's Instagram Reels workspace, run with the **reel-studio** plugin.
It is usually operated by an automated assistant (a bot) on the owner's behalf.

- Use the reel-studio commands: `/reel-studio:brand`, `/reel-studio:new`, `/reel-studio:approve`, `/reel-studio:render`, `/reel-studio:auto`, `/reel-studio:status`.
- The operator writes in English. Reel content (voiceover, on-screen text, caption, cover) is in the language set in `brand/brand.json`.
- Never open question dialogs. Ask in plain text.
- End every final reply with exactly one `STATUS: …` line, as the reel-studio commands describe.
- API keys come from environment variables (ELEVENLABS_API_KEY, HIGGSFIELD_API_KEY, HIGGSFIELD_API_SECRET). Never print them, never write them to files in this repo.
- Finished reels are committed and pushed by the deliver step; don't push anything else without being asked.
