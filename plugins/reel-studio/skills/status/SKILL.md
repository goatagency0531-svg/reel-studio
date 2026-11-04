---
name: status
description: Show every reel in the workspace, its stage, and what to do next.
---

Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/status.py"` and show the table. For each reel waiting on someone (`needs_approval`, `awaiting_visuals`) give the exact next command.
End with `STATUS: DONE` (or `STATUS: ERROR <reason>` if the workspace isn't set up).
