#!/usr/bin/env python3
"""Check that this computer and workspace are ready for Reel Studio.

Usage: python3 doctor.py [--workspace DIR]
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys

from common import load_brand, load_env, workspace

OK, WARN, BAD = "✅", "⚠️ ", "❌"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace")
    a = ap.parse_args()
    ws = workspace(a.workspace)
    load_env(ws)
    problems = 0

    def line(icon, msg):
        nonlocal problems
        if icon == BAD:
            problems += 1
        print(f"{icon} {msg}")

    line(OK if sys.version_info >= (3, 9) else BAD, f"Python {sys.version.split()[0]} (need 3.9+)")
    if shutil.which("ffmpeg"):
        filters = subprocess.run(["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True).stdout
        need = ["ass", "drawtext", "zoompan", "sidechaincompress", "xstack"]
        miss = [f for f in need if f" {f} " not in filters]
        line(OK if not miss else BAD, "ffmpeg found" + (f" but missing filters: {', '.join(miss)} (install a full build)" if miss else " with all needed filters"))
    else:
        line(BAD, "ffmpeg not found. macOS: brew install ffmpeg · Windows: winget install ffmpeg · Linux: apt install ffmpeg")

    bj = ws / "brand" / "brand.json"
    line(OK if bj.exists() else BAD, f"brand/brand.json {'found' if bj.exists() else 'missing — run setup'}")
    brand = load_brand(ws)
    line(OK if os.environ.get("ELEVENLABS_API_KEY") else WARN,
         "ELEVENLABS_API_KEY " + ("set" if os.environ.get("ELEVENLABS_API_KEY") else "not set (you can still use your own recordings)"))
    line(OK if brand.get("elevenlabs", {}).get("voice_id") else WARN, "ElevenLabs voice_id " + ("set" if brand.get("elevenlabs", {}).get("voice_id") else "not set"))
    mode = brand.get("higgsfield", {}).get("mode", "manual")
    if mode == "api":
        has = bool(os.environ.get("HIGGSFIELD_API_KEY"))
        path = brand["higgsfield"]["api"].get("text_to_image_path")
        line(OK if has and path else BAD, f"Higgsfield API mode: key {'set' if has else 'MISSING'}, text_to_image_path {'set' if path else 'MISSING'}")
    else:
        line(OK, "Higgsfield manual mode (shot list + drop files in)")
    for key, label in (("logo_file", "logo"), ("music_file", "background music")):
        f = brand.get(key)
        line(OK if f and (ws / f).is_file() else WARN, f"{label}: " + (f if f and (ws / f).is_file() else "none (optional)"))
    gi = ws / ".gitignore"
    if (ws / ".env").exists() and (not gi.exists() or ".env" not in gi.read_text()):
        line(WARN, ".env is not in .gitignore — don't commit your API keys")
    print("\nReady." if problems == 0 else f"\n{problems} problem(s) to fix.")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
