#!/usr/bin/env python3
"""Make the reel cover (poster).

Usage:
  python3 poster.py <slug> [--workspace DIR] [--image PATH] [--frame SECONDS]
                    [--headline TEXT] [--subline TEXT]

Background, in order: --image, visuals/poster.(png|jpg), a frame from the rendered reel
(--frame, default: middle of the first beat that has real footage), brand background colour.

Output:
  out/cover.png        1080x1920 (upload as the reel cover)
  out/cover_grid.jpg   1080x1440 centre crop: how it looks on your profile grid
"""
from __future__ import annotations

import argparse
import textwrap
from pathlib import Path

from common import H, W, ff_path, find_font, load_brand, load_env, need_ffmpeg, read_json, reel_dir, run, workspace


def wrap(text: str, width: int) -> list[str]:
    return textwrap.wrap(text, width=width, break_long_words=False) or [text]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--workspace")
    ap.add_argument("--image")
    ap.add_argument("--frame", type=float)
    ap.add_argument("--headline")
    ap.add_argument("--subline")
    a = ap.parse_args()

    ws = workspace(a.workspace)
    load_env(ws)
    need_ffmpeg()
    brand = load_brand(ws)
    rd = reel_dir(ws, a.slug)
    script = read_json(rd / "script.json")
    p = script.get("poster", {})
    headline = (a.headline or p.get("headline") or script.get("title", "")).strip()
    subline = (a.subline or p.get("subline") or "").strip()
    col = brand["colors"]
    build, out = rd / "build", rd / "out"
    build.mkdir(exist_ok=True)
    out.mkdir(exist_ok=True)

    # ---- background
    bg = None
    if a.image:
        bg = Path(a.image)
    else:
        for ext in ("png", "jpg", "jpeg", "webp"):
            if (rd / "visuals" / f"poster.{ext}").exists():
                bg = rd / "visuals" / f"poster.{ext}"
                break
    reel = out / "reel.mp4"
    if not bg and reel.exists():
        t = a.frame
        if t is None:
            timing = read_json(rd / "voice" / "timing.json", default={"beats": []})
            types = {b["id"]: b["visual"]["type"] for b in script["beats"]}
            real = [b for b in timing["beats"] if types.get(b["id"]) != "text_card"]
            b0 = real[0] if real else (timing["beats"][0] if timing["beats"] else {"start": 0, "end": 1})
            t = b0["start"] + (b0["end"] - b0["start"]) * 0.5
        # grab from the joined (caption-free) video if present, so no burned captions on the cover
        src = build / "video.mp4" if (build / "video.mp4").exists() else reel
        bg = build / "poster_bg.png"
        run(["ffmpeg", "-y", "-ss", f"{t:.2f}", "-i", str(src), "-frames:v", "1", str(bg)])

    if bg:
        inp = ["-i", str(bg)]
        base = f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1"
    else:
        inp = ["-f", "lavfi", "-i", f"color=c=0x{col['background'].lstrip('#')}:s={W}x{H}"]
        base = "[0:v]setsar=1"

    # ---- darkening bands for legibility (top to bottom of the text zone)
    # smooth vertical gradient: 0 at y=640 -> 0.65 at y=1300, held to the bottom (30px steps)
    shade = "".join(f",drawbox=x=0:y={y}:w={W}:h=30:color=black@{min(max((y - 640) / 660, 0), 1) * 0.65:.3f}:t=fill"
                    for y in range(640, H, 30))

    font = find_font(ws, brand, "bold")
    fs = 118 if len(headline) <= 28 else 98 if len(headline) <= 48 else 84
    width = 15 if fs >= 118 else 18 if fs >= 98 else 22
    lines = wrap(headline.upper() if brand["_style"].get("caption", {}).get("uppercase") else headline, width)
    line_h = int(fs * 1.12)
    block_h = line_h * len(lines) + (110 if subline else 0)
    y0 = 1180 - block_h // 2   # centred in the profile-grid safe zone (y 240..1680)

    draws = []
    for i, line in enumerate(lines):
        tf = build / f"poster_line_{i}.txt"
        tf.write_text(line, encoding="utf-8")
        draws.append(f"drawtext=fontfile='{ff_path(font)}':textfile='{ff_path(tf)}':fontsize={fs}:"
                     f"fontcolor=0x{col['text'].lstrip('#')}:borderw=4:bordercolor=black@0.6:"
                     f"x=(w-text_w)/2:y={y0 + i * line_h}")
    if subline:
        tf = build / "poster_sub.txt"
        tf.write_text(subline, encoding="utf-8")
        draws.append(f"drawtext=fontfile='{ff_path(font)}':textfile='{ff_path(tf)}':fontsize=58:"
                     f"fontcolor=0x{col.get('primary', '#111111').lstrip('#')}:box=1:boxcolor=0x{col['accent'].lstrip('#')}:boxborderw=22:"
                     f"x=(w-text_w)/2:y={y0 + len(lines) * line_h + 40}")
    # accent bar above headline
    draws.insert(0, f"drawbox=x=(iw-160)/2:y={y0 - 60}:w=160:h=12:color=0x{col['accent'].lstrip('#')}:t=fill")

    fc = base + shade + "," + ",".join(draws) + "[p0]"
    last = "p0"
    logo = ws / brand.get("logo_file", "")
    if brand.get("logo_file") and logo.is_file():
        inp += ["-i", str(logo)]
        fc += f";[1:v]scale=200:-1[lg];[p0][lg]overlay=x=(W-w)/2:y=300[p1]"
        last = "p1"
    elif brand.get("handle"):
        tf = build / "poster_handle.txt"
        tf.write_text(brand["handle"], encoding="utf-8")
        fc += (f";[p0]drawtext=fontfile='{ff_path(font)}':textfile='{ff_path(tf)}':fontsize=44:"
               f"fontcolor=white@0.9:x=(w-text_w)/2:y=1560[p1]")
        last = "p1"

    cover = out / "cover.png"
    run(["ffmpeg", "-y", *inp, "-filter_complex", fc, "-map", f"[{last}]", "-frames:v", "1", str(cover)])
    run(["ffmpeg", "-y", "-i", str(cover), "-vf", f"crop={W}:1440:0:240", "-q:v", "3", str(out / "cover_grid.jpg")])
    print(f"OK poster: {cover}")
    print(f"Grid preview: {out / 'cover_grid.jpg'}")


if __name__ == "__main__":
    main()
