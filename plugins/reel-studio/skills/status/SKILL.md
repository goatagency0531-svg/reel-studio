---
name: status
description: Show every reel in the workspace, its stage, and what to do next.
---

Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/status.py"` and show the table. Then, for each reel waiting on the user (`needs_approval`, `awaiting_visuals`), give the exact next command.
