"""Shared helpers for Reel Studio scripts. Standard library only."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
W, H, FPS = 1080, 1920, 30

STAGES = [
    "draft",            # scriptwriter working
    "in_review",        # reviewer working
    "needs_approval",   # waiting for the human
    "approved",
    "voiced",           # voice.mp3 + alignment ready
    "awaiting_visuals", # manual Higgsfield mode: user drops clips in visuals/
    "visuals_ready",
    "rendered",
    "done",
]


def die(msg: str, code: int = 1) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def workspace(path: str | None = None) -> Path:
    ws = Path(path or os.environ.get("REEL_STUDIO_WORKSPACE") or os.getcwd()).resolve()
    return ws


def load_env(ws: Path) -> None:
    """Load KEY=VALUE pairs from <workspace>/.env without overriding real env vars."""
    env_file = ws / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def read_json(p: Path, default=None):
    if not p.exists():
        if default is not None:
            return default
        die(f"missing file: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def write_json(p: Path, data) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_brand(ws: Path) -> dict:
    brand = read_json(PLUGIN_ROOT / "templates" / "brand.example.json")
    user = ws / "brand" / "brand.json"
    if user.exists():
        deep_merge(brand, read_json(user))
    style_name = brand.get("style", "bold")
    style_file = PLUGIN_ROOT / "templates" / "styles" / f"{style_name}.json"
    custom = ws / "brand" / "styles" / f"{style_name}.json"
    style = read_json(custom if custom.exists() else style_file, default={})
    brand["_style"] = style
    return brand


def deep_merge(base: dict, over: dict) -> dict:
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            deep_merge(base[k], v)
        else:
            base[k] = v
    return base


def reel_dir(ws: Path, slug: str) -> Path:
    d = ws / "reels" / slug
    if not d.exists():
        die(f"reel not found: {d}")
    return d


def set_stage(rd: Path, stage: str, note: str = "") -> None:
    if stage not in STAGES:
        die(f"unknown stage {stage}")
    st = read_json(rd / "status.json", default={"stage": "draft", "history": []})
    st["stage"] = stage
    st.setdefault("history", []).append(
        {"stage": stage, "at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "note": note}
    )
    write_json(rd / "status.json", st)


def run(cmd: list[str], quiet: bool = True) -> None:
    res = subprocess.run(cmd, capture_output=quiet, text=True)
    if res.returncode != 0:
        tail = (res.stderr or "")[-2500:] if quiet else ""
        die(f"command failed: {' '.join(cmd[:6])} ...\n{tail}")


def need_ffmpeg() -> None:
    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            die(f"{tool} not found. Install ffmpeg (macOS: brew install ffmpeg, Windows: winget install ffmpeg).")


def duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True,
    ).stdout.strip()
    try:
        return float(out)
    except ValueError:
        return 0.0


def find_font(ws: Path, brand: dict, weight: str = "bold") -> str:
    """Return a font file path: brand font -> fontconfig match -> common fallbacks."""
    fonts = brand.get("fonts", {})
    rel = fonts.get(f"{weight}_file") or fonts.get("bold_file")
    if rel:
        p = (ws / rel) if not Path(rel).is_absolute() else Path(rel)
        if p.exists():
            return str(p)
    family = fonts.get("family", "Inter")
    if shutil.which("fc-match"):
        out = subprocess.run(["fc-match", "-f", "%{file}", f"{family}:{weight}"], capture_output=True, text=True).stdout
        if out and Path(out).exists():
            return out
    for cand in [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]:
        if Path(cand).exists():
            return cand
    die("no usable font found. Put a .ttf/.otf in brand/fonts/ and set fonts.bold_file in brand/brand.json")
    return ""


def hex_to_ass(hex_color: str, alpha: int = 0) -> str:
    """#RRGGBB -> &HAABBGGRR (ASS colour format)."""
    h = hex_color.lstrip("#")
    r, g, b = h[0:2], h[2:4], h[4:6]
    return f"&H{alpha:02X}{b}{g}{r}".upper()


def ff_color(hex_color: str, alpha: float = 1.0) -> str:
    return f"0x{hex_color.lstrip('#')}@{alpha}"


def ff_path(p: Path | str) -> str:
    """Escape a path for use inside an ffmpeg filter argument."""
    s = str(p).replace("\\", "/")
    return s.replace(":", r"\:").replace("'", r"\'")
