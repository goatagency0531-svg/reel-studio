#!/usr/bin/env python3
"""Prepare or generate the visuals for each beat.

Usage:
  python3 visuals.py <slug> [--workspace DIR]           # manual or api, per brand.higgsfield.mode
  python3 visuals.py <slug> --check                     # only report what is missing

Expected files in reels/<slug>/visuals/:
  <beat_id>.mp4 / .mov        for visual.type == "ai_video"  (or "footage" = your own clip)
  <beat_id>.png / .jpg / .webp for visual.type == "ai_image"
  text_card beats need nothing; they are drawn from your brand colors.

Manual mode (default, works with any Higgsfield plan):
  writes visuals/SHOTLIST.md with every prompt, the length each shot needs and the exact
  filename to save it as. Generate in Higgsfield, download, drop files into visuals/.

API mode (beta): calls the Higgsfield REST API configured in brand.json -> higgsfield.api.
  Endpoint paths differ by model and change over time, so they are configuration, not code.
"""
from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

from common import die, load_brand, load_env, read_json, reel_dir, set_stage, workspace, write_json

VIDEO_EXT = (".mp4", ".mov", ".webm", ".m4v")
IMAGE_EXT = (".png", ".jpg", ".jpeg", ".webp")
NEEDS_FILE = {"ai_video": VIDEO_EXT, "footage": VIDEO_EXT, "ai_image": IMAGE_EXT}


def find_asset(vdir: Path, bid: str, exts) -> Path | None:
    # accept either the exact type or any visual (an image for a video beat still renders)
    for e in exts + tuple(x for x in VIDEO_EXT + IMAGE_EXT if x not in exts):
        p = vdir / f"{bid}{e}"
        if p.exists():
            return p
    return None


def beat_lengths(rd: Path) -> dict:
    t = read_json(rd / "voice" / "timing.json", default={})
    return {b["id"]: b["end"] - b["start"] for b in t.get("beats", [])}


def write_shotlist(rd: Path, script: dict, missing: list[dict], lengths: dict) -> Path:
    lines = [
        f"# Shot list: {script.get('title', rd.name)}",
        "",
        "Generate each shot in Higgsfield, download it, and save it in this folder with the exact filename.",
        "All shots are vertical 9:16. Shots can be longer than needed; they are trimmed automatically.",
        "",
    ]
    for b in missing:
        v = b["visual"]
        ext = "mp4" if v["type"] in ("ai_video", "footage") else "png"
        need = lengths.get(b["id"])
        lines += [
            f"## {b['id']}  →  save as `{b['id']}.{ext}`",
            f"- Type: {v['type']}" + (f"  ·  needs ~{need:.1f}s" if need else ""),
            f"- Voiceover: {b['voiceover']}",
            f"- Prompt: {v.get('prompt', '')}",
        ]
        if v.get("motion"):
            lines.append(f"- Camera motion: {v['motion']}")
        lines.append("")
    p = rd / "visuals" / "SHOTLIST.md"
    p.write_text("\n".join(lines), encoding="utf-8")
    return p


# ---------- API mode (beta) ----------

def _auth_headers(cfg: dict) -> dict:
    fmt = cfg.get("auth_format", "Bearer {HIGGSFIELD_API_KEY}")
    try:
        val = fmt.format(**{k: v for k, v in os.environ.items() if k.startswith("HIGGSFIELD")})
    except KeyError as e:
        die(f"Missing {e} in .env (needed by higgsfield.api.auth_format)")
    return {cfg.get("auth_header", "Authorization"): val, "Content-Type": "application/json", "Accept": "application/json"}


def _http(method: str, url: str, headers: dict, body: dict | None = None) -> dict:
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        die(f"Higgsfield {method} {url} -> {e.code}: {e.read().decode(errors='replace')[:500]}")
    except urllib.error.URLError as e:
        die(f"Could not reach Higgsfield: {e.reason}")
    return {}


def _find(obj, keys: tuple) -> str | None:
    if isinstance(obj, dict):
        for k in keys:
            if isinstance(obj.get(k), str) and obj[k]:
                return obj[k]
        for v in obj.values():
            r = _find(v, keys)
            if r:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = _find(v, keys)
            if r:
                return r
    return None


def _media_url(obj) -> str | None:
    if isinstance(obj, str) and obj.startswith("http") and obj.split("?")[0].lower().endswith(VIDEO_EXT + IMAGE_EXT):
        return obj
    if isinstance(obj, dict):
        for k in ("url", "video_url", "image_url", "raw", "min"):
            if isinstance(obj.get(k), str) and obj[k].startswith("http"):
                return obj[k]
        for v in obj.values():
            r = _media_url(v)
            if r:
                return r
    if isinstance(obj, list):
        for v in obj:
            r = _media_url(v)
            if r:
                return r
    return None


def _submit_and_wait(cfg: dict, path: str, body: dict) -> str:
    base = cfg["base_url"].rstrip("/")
    h = _auth_headers(cfg)
    res = _http("POST", base + path, h, body)
    url = _media_url(res) if str(res.get("status", "")).lower() in ("completed", "succeeded", "done") else None
    status_url = _find(res, ("status_url", "polling_url"))
    rid = _find(res, ("request_id", "id", "job_set_id"))
    if not status_url and rid and cfg.get("status_path"):
        status_url = base + cfg["status_path"].format(request_id=rid)
    deadline = time.time() + cfg.get("timeout_seconds", 600)
    while not url:
        if not status_url:
            die(f"Higgsfield response had no status URL or request id. Response: {json.dumps(res)[:400]}")
        if time.time() > deadline:
            die("Higgsfield generation timed out")
        time.sleep(cfg.get("poll_seconds", 6))
        res = _http("GET", status_url, h)
        st = str(_find(res, ("status", "state")) or "").lower()
        if st in ("failed", "error", "nsfw", "cancelled", "canceled"):
            die(f"Higgsfield generation {st}: {json.dumps(res)[:400]}")
        if st in ("completed", "succeeded", "done", "success"):
            url = _media_url(res)
    return url


def _download(url: str, dest: Path) -> None:
    with urllib.request.urlopen(url, timeout=300) as r:
        dest.write_bytes(r.read())


def api_generate(rd: Path, brand: dict, missing: list[dict]) -> list[str]:
    cfg = brand["higgsfield"]["api"]
    t2i, i2v = cfg.get("text_to_image_path"), cfg.get("image_to_video_path")
    if not t2i:
        die("higgsfield.api.text_to_image_path is empty in brand.json. Copy it from your Higgsfield API docs, or use mode=manual.")
    done = []
    for b in missing:
        v = b["visual"]
        if v["type"] == "footage":
            continue
        print(f"… generating {b['id']} ({v['type']})")
        img_url = _submit_and_wait(cfg, t2i, {"prompt": v["prompt"], "aspect_ratio": "9:16", **cfg.get("text_to_image_extra", {})})
        if v["type"] == "ai_video" and i2v:
            prompt = v["prompt"] + (f". Camera: {v['motion']}" if v.get("motion") else "")
            vid_url = _submit_and_wait(cfg, i2v, {"prompt": prompt, "image_url": img_url, **cfg.get("image_to_video_extra", {})})
            _download(vid_url, rd / "visuals" / f"{b['id']}.mp4")
        else:
            ext = Path(img_url.split("?")[0]).suffix or ".png"
            _download(img_url, rd / "visuals" / f"{b['id']}{ext}")
        done.append(b["id"])
    return done


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--workspace")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    ws = workspace(a.workspace)
    load_env(ws)
    brand = load_brand(ws)
    rd = reel_dir(ws, a.slug)
    script = read_json(rd / "script.json")
    vdir = rd / "visuals"
    vdir.mkdir(exist_ok=True)

    def missing_now():
        return [b for b in script["beats"] if b["visual"]["type"] in NEEDS_FILE
                and not find_asset(vdir, b["id"], NEEDS_FILE[b["visual"]["type"]])]

    missing = missing_now()
    if missing and not a.check and brand["higgsfield"].get("mode") == "api":
        api_generate(rd, brand, missing)
        missing = missing_now()

    report = {"missing": [b["id"] for b in missing], "total_beats": len(script["beats"])}
    write_json(vdir / "status.json", report)
    if missing:
        sl = write_shotlist(rd, script, missing, beat_lengths(rd))
        if not a.check:
            set_stage(rd, "awaiting_visuals", f"{len(missing)} shots missing")
        print(f"WAITING: {len(missing)} shot(s) missing: {', '.join(report['missing'])}")
        print(f"Shot list: {sl}")
        print("Tip: you can also render now; missing shots become branded text cards.")
    else:
        if not a.check:
            set_stage(rd, "visuals_ready")
        print("OK visuals: all shots present")


if __name__ == "__main__":
    main()
