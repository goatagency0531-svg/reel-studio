#!/usr/bin/env python3
"""List all reels and their stage. Usage: python3 status.py [--workspace DIR]"""
from __future__ import annotations

import argparse

from common import read_json, workspace

NEXT = {
    "draft": "scriptwriter is writing",
    "in_review": "reviewer is checking",
    "needs_approval": "YOU: read script.json/review.md, then approve",
    "approved": "voice step",
    "voiced": "visuals step",
    "awaiting_visuals": "YOU: generate shots from visuals/SHOTLIST.md, then render",
    "visuals_ready": "render",
    "rendered": "poster + caption",
    "done": "post it",
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace")
    ws = workspace(ap.parse_args().workspace)
    reels = sorted((ws / "reels").glob("*/status.json")) if (ws / "reels").exists() else []
    if not reels:
        print("No reels yet.")
        return
    print(f"{'REEL':44} {'STAGE':18} NEXT")
    for p in reels:
        st = read_json(p)
        print(f"{p.parent.name:44} {st['stage']:18} {NEXT.get(st['stage'], '')}")


if __name__ == "__main__":
    main()
