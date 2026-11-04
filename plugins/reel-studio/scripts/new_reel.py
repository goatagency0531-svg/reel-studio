#!/usr/bin/env python3
"""Create a reel folder. Prints the slug.

Usage: python3 new_reel.py "<idea>" [--workspace DIR] [--slug SLUG]
"""
from __future__ import annotations

import argparse
import re
import unicodedata
from datetime import date

from common import set_stage, workspace


def slugify(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE).strip().lower()
    s = re.sub(r"[\s_-]+", "-", s)
    return s[:40].strip("-") or "reel"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("idea")
    ap.add_argument("--workspace")
    ap.add_argument("--slug")
    a = ap.parse_args()
    ws = workspace(a.workspace)
    base = f"{date.today().isoformat()}-{a.slug or slugify(a.idea)}"
    slug, n = base, 2
    while (ws / "reels" / slug).exists():
        slug, n = f"{base}-{n}", n + 1
    rd = ws / "reels" / slug
    for sub in ("voice", "visuals", "build", "out"):
        (rd / sub).mkdir(parents=True, exist_ok=True)
    (rd / "brief.md").write_text(f"# Brief\n\n{a.idea.strip()}\n", encoding="utf-8")
    set_stage(rd, "draft", "created")
    print(slug)


if __name__ == "__main__":
    main()
