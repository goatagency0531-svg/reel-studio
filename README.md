# Reel Studio

AI Instagram Reels production for businesses, run by a Grok bot through Claude Code.

| Folder | What it is | Who uses it |
|---|---|---|
| `plugins/reel-studio/` | The Claude Code plugin: scriptwriter, reviewer, editor, poster-designer agents + render engine | Claude |
| `workspace-template/` | Template for each client's private repo (brand profile, reels, auto-enables the plugin) | Copied once per client |
| `grok-bot/INSTRUCTIONS.md` | The bot playbook: onboarding, Mongolian client messages, English commands to Claude, status handling | The Grok bot |

## Flow
```
Client (Mongolian) ⇄ Grok bot ──English commands──▶ claude.ai/code session on the client's repo
                                                     └ Reel Studio: script → review → approval
                                                       → ElevenLabs voice → Higgsfield visuals
                                                       → motion graphics render → cover → push
Grok bot ◀── STATUS lines + download links ───────────┘
```

## Before you publish
1. Push this repo to GitHub as `goatagency0531-svg/reel-studio`. Publish `workspace-template/` as its own template repo
   `goatagency0531-svg/reel-workspace-template` (enable "Template repository" in its settings).
2. The `goatagency0531-svg` names are already filled in `workspace-template/.claude/settings.json` and `grok-bot/INSTRUCTIONS.md`.
3. `reel-studio` is public, so client accounts need no extra access to load the plugin. Client repos stay private.

## Commands (Claude side)
`/reel-studio:brand` · `/reel-studio:new` · `/reel-studio:approve` · `/reel-studio:render` · `/reel-studio:auto` · `/reel-studio:status` · `/reel-studio:setup` (humans only)

Every reply ends with one machine-readable line: `STATUS: NEEDS_APPROVAL | WAITING_FOR_SHOTS | DONE | NEED_INFO | BRAND_SAVED | ERROR`.
