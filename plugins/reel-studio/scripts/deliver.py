#!/usr/bin/env python3
"""Deliver a finished reel: commit + push the outputs and print download links.

Usage: python3 deliver.py <slug> [--workspace DIR] [--no-push]

Prints machine-readable lines the bot can parse:
  DELIVERY_REEL: <url or path>
  DELIVERY_COVER: <url or path>
  DELIVERY_CAPTION: <url or path>
If the workspace is not a git repo with a GitHub remote (e.g. running locally on the bot's
computer), the lines contain absolute file paths instead of URLs.
"""
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path
from urllib.parse import quote

from common import load_brand, reel_dir, set_stage, workspace

OUTPUTS = ["out/reel.mp4", "out/cover.png", "out/cover_grid.jpg", "out/caption.txt"]


def git(ws: Path, *args: str, check: bool = True) -> str:
    r = subprocess.run(["git", "-C", str(ws), *args], capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or r.stdout.strip())
    return r.stdout.strip()


def github_base(remote: str) -> str | None:
    # https://github.com/o/r(.git) | git@github.com:o/r(.git) | proxied URLs ending in /o/r(.git)
    m = re.search(r"github\.com[/:]([^/]+)/([^/]+?)(?:\.git)?$", remote) or re.search(r"/([^/]+)/([^/]+?)(?:\.git)?$", remote)
    return f"https://github.com/{m.group(1)}/{m.group(2)}" if m else None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--workspace")
    ap.add_argument("--no-push", action="store_true")
    a = ap.parse_args()
    ws = workspace(a.workspace)
    brand = load_brand(ws)
    rd = reel_dir(ws, a.slug)
    missing = [o for o in OUTPUTS[:2] if not (rd / o).exists()]
    if missing:
        print(f"STATUS: ERROR missing outputs: {', '.join(missing)}")
        raise SystemExit(1)

    rel = rd.relative_to(ws).as_posix()
    links = {o: str(rd / o) for o in OUTPUTS if (rd / o).exists()}
    push = brand.get("delivery", {}).get("git_push", True) and not a.no_push
    is_repo = subprocess.run(["git", "-C", str(ws), "rev-parse", "--is-inside-work-tree"], capture_output=True).returncode == 0

    if push and is_repo:
        try:
            branch = brand.get("delivery", {}).get("branch") or git(ws, "rev-parse", "--abbrev-ref", "HEAD")
            extras = [f for f in ("script.json", "review.md", "brief.md") if (rd / f).exists()]
            git(ws, "add", "--", *[f"{rel}/{f}" for f in extras], *[f"{rel}/{o}" for o in links])
            if git(ws, "status", "--porcelain", "--", rel):
                git(ws, "commit", "-m", f"reel: {a.slug}", "--", rel)
            out = None
            for attempt in range(4):
                r = subprocess.run(["git", "-C", str(ws), "push", "-u", "origin", branch], capture_output=True, text=True)
                if r.returncode == 0:
                    out = "ok"
                    break
                import time
                time.sleep(2 ** (attempt + 1))
            if out:
                base = github_base(git(ws, "remote", "get-url", "origin", check=False))
                if base:
                    links = {o: f"{base}/raw/{quote(branch)}/{quote(rel)}/{o}" for o in links}
                print(f"PUSHED: {branch}")
            else:
                print(f"PUSH_FAILED: {r.stderr.strip()[:300]} (files are still in the workspace)")
        except RuntimeError as e:
            print(f"PUSH_FAILED: {e} (files are still in the workspace)")

    print(f"DELIVERY_REEL: {links.get('out/reel.mp4')}")
    print(f"DELIVERY_COVER: {links.get('out/cover.png')}")
    if "out/caption.txt" in links:
        print(f"DELIVERY_CAPTION: {links['out/caption.txt']}")
    set_stage(rd, "done", "delivered")


if __name__ == "__main__":
    main()
