#!/usr/bin/env python3
"""Render the reel: per-beat visuals + voice + animated captions + emphasis cards + music + logo.

Usage:
  python3 render.py <slug> [--workspace DIR] [--draft]

--draft renders faster at lower quality for checking timing.

Output:
  reels/<slug>/out/reel.mp4        1080x1920, 30fps, H.264/AAC, Instagram-ready
  reels/<slug>/build/preview.jpg   contact sheet (one frame per beat) for review
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
from pathlib import Path

from common import (FPS, H, W, die, duration, ff_path, find_font, hex_to_ass, load_brand, load_env,
                    need_ffmpeg, read_json, reel_dir, run, set_stage, workspace, write_json)
from visuals import IMAGE_EXT, VIDEO_EXT, find_asset

# ---------------------------------------------------------------- segments

def seg_video(src: Path, dur: float, out: Path, style: dict, enc: list) -> None:
    frames = max(1, round(dur * FPS))
    punch = style["motion"].get("video_punch_zoom", 1.0)
    vf = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS}"
    if punch > 1.0:
        rate = (punch - 1.0) / frames
        vf += (f",zoompan=z='min(1+on*{rate:.6f},{punch})':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
               f":s={W}x{H}:fps={FPS}")
    vf += ",setsar=1,format=yuv420p"
    run(["ffmpeg", "-y", "-stream_loop", "-1", "-i", str(src), "-an", "-vf", vf, "-frames:v", str(frames), *enc, str(out)])


def seg_image(src: Path, dur: float, out: Path, style: dict, enc: list, n: int) -> None:
    frames = max(1, round(dur * FPS))
    zmax = style["motion"].get("image_zoom", 1.1)
    rate = (zmax - 1.0) / frames
    # alternate zoom in / zoom out per beat for variety
    z = f"min(1+on*{rate:.6f},{zmax})" if n % 2 == 0 else f"max({zmax}-on*{rate:.6f},1)"
    vf = (f"scale={W*2}:{H*2}:force_original_aspect_ratio=increase,crop={W*2}:{H*2},"
          f"zoompan=z='{z}':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={FPS},"
          f"setsar=1,format=yuv420p")
    run(["ffmpeg", "-y", "-loop", "1", "-i", str(src), "-vf", vf, "-frames:v", str(frames), *enc, str(out)])


def seg_card(color: str, accent: str, dur: float, out: Path, enc: list) -> None:
    frames = max(1, round(dur * FPS))
    c = color.lstrip("#")
    a = accent.lstrip("#")
    vf = (f"drawbox=x=0:y=ih-ih/3:w=iw:h=ih/3:color=0x{a}@0.10:t=fill,"
          f"drawbox=x=80:y=ih/2+260:w=180:h=14:color=0x{a}@1:t=fill,format=yuv420p")
    run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=0x{c}:s={W}x{H}:r={FPS}", "-vf", vf,
         "-frames:v", str(frames), *enc, str(out)])


# ---------------------------------------------------------------- captions (ASS)

def ass_time(t: float) -> str:
    t = max(t, 0)
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def ass_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace("{", "(").replace("}", ")").replace("\n", " ")


def font_family(ws: Path, brand: dict) -> str:
    f = brand.get("fonts", {})
    rel = f.get("bold_file")
    if rel and shutil.which("fc-scan"):
        p = ws / rel
        if p.exists():
            fam = subprocess.run(["fc-scan", "--format", "%{family[0]}", str(p)], capture_output=True, text=True).stdout
            if fam:
                return fam.strip()
    return f.get("family", "Inter")


def group_words(words: list[dict], per: int) -> list[list[dict]]:
    groups, cur = [], []
    for w in words:
        if cur and (cur[-1]["beat"] != w["beat"]):
            groups.append(cur)
            cur = []
        cur.append(w)
        if len(cur) >= per or w["w"][-1] in ".!?,;:":
            groups.append(cur)
            cur = []
    if cur:
        groups.append(cur)
    return groups


def build_ass(ws: Path, brand: dict, script: dict, timing: dict) -> str:
    st = brand["_style"]
    cap, emp = st["caption"], st["emphasis"]
    col = brand["colors"]
    fam = font_family(ws, brand)
    text_c, accent_c = hex_to_ass(col["text"]), hex_to_ass(col["accent"])
    dark_c = hex_to_ass(col.get("primary", "#111111"))
    black = "&H00000000"
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,{fam},{cap['font_size']},{text_c},{accent_c},{black},&H80000000,-1,0,0,0,100,100,0,0,1,{cap['outline']},{cap['shadow']},5,90,90,0,1
Style: Emphasis,{fam},{emp['font_size']},{dark_c},{dark_c},{accent_c},{accent_c},-1,0,0,0,100,100,0,0,{3 if emp.get('box') else 1},18,0,5,90,90,0,1
Style: Card,{fam},{int(emp['font_size']*1.05)},{text_c},{text_c},{black},{black},-1,0,0,0,100,100,0,0,1,0,0,4,80,80,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    upper = cap.get("uppercase", False)
    y = cap["position_y"]
    words = timing["words"]
    beats_t = {b["id"]: b for b in timing["beats"]}
    card_beats = {b["id"] for b in script["beats"] if b["visual"]["type"] == "text_card"}

    def fmt(w):
        t = w["w"]
        return ass_escape(t.upper() if upper else t)

    groups = group_words([w for w in words if w["beat"] not in card_beats], cap["words_per_group"])
    for gi, g in enumerate(groups):
        g_end = groups[gi + 1][0]["start"] if gi + 1 < len(groups) else g[-1]["end"] + 0.3
        g_end = min(g_end, g[-1]["end"] + 0.6)
        if cap.get("highlight_active_word"):
            for wi, w in enumerate(g):
                s = w["start"] if wi else g[0]["start"]
                e = g[wi + 1]["start"] if wi + 1 < len(g) else g_end
                parts = [("{\\c" + accent_c + "}" + fmt(x) + "{\\c" + text_c + "}") if x is w else fmt(x) for x in g]
                pop = "{\\fscx82\\fscy82\\t(0,90,\\fscx100\\fscy100)}" if (wi == 0 and cap.get("pop_in")) else ""
                ev.append(f"Dialogue: 1,{ass_time(s)},{ass_time(e)},Caption,,0,0,0,,{{\\an5\\pos({W//2},{y})}}{pop}{' '.join(parts)}")
        else:
            ev.append(f"Dialogue: 1,{ass_time(g[0]['start'])},{ass_time(g_end)},Caption,,0,0,0,,"
                      f"{{\\an5\\pos({W//2},{y})\\fad(80,80)}}{' '.join(fmt(w) for w in g)}")

    for b in script["beats"]:
        bt = beats_t.get(b["id"])
        txt = (b.get("on_screen") or "").strip()
        if not bt or not txt:
            continue
        if b["id"] in card_beats:
            ev.append(f"Dialogue: 2,{ass_time(bt['start'])},{ass_time(bt['end'])},Card,,0,0,0,,"
                      f"{{\\an4\\pos(80,{H//2 + 60})\\fad(120,0)\\fscx92\\fscy92\\t(0,220,\\fscx100\\fscy100)}}{ass_escape(txt)}")
        elif emp.get("enabled"):
            e = min(bt["start"] + emp["duration"], bt["end"])
            ev.append(f"Dialogue: 3,{ass_time(bt['start'] + 0.05)},{ass_time(e)},Emphasis,,0,0,0,,"
                      f"{{\\an5\\pos({W//2},{emp['position_y']})\\fad(60,140)\\frz-2\\fscx125\\fscy125\\t(0,140,\\fscx100\\fscy100)}}"
                      f"{ass_escape(txt)}")
    return head + "\n".join(ev) + "\n"


# ---------------------------------------------------------------- main

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--workspace")
    ap.add_argument("--draft", action="store_true")
    a = ap.parse_args()

    ws = workspace(a.workspace)
    load_env(ws)
    need_ffmpeg()
    brand = load_brand(ws)
    style = brand["_style"]
    rd = reel_dir(ws, a.slug)
    script = read_json(rd / "script.json")
    timing = read_json(rd / "voice" / "timing.json")
    voice = rd / "voice" / "voice.mp3"
    if not voice.exists():
        die("no voice/voice.mp3 — run the voice step first")
    total = timing["duration"]
    build, out = rd / "build", rd / "out"
    build.mkdir(exist_ok=True)
    out.mkdir(exist_ok=True)

    enc = ["-c:v", "libx264", "-preset", "ultrafast" if a.draft else "veryfast", "-crf", "28" if a.draft else "16",
           "-pix_fmt", "yuv420p", "-r", str(FPS)]
    col = brand["colors"]
    vdir = rd / "visuals"
    beats_t = {b["id"]: b for b in timing["beats"]}
    seg_files, used = [], []
    for n, b in enumerate(script["beats"]):
        bt = beats_t[b["id"]]
        dur = bt["end"] - bt["start"]
        seg = build / f"seg_{n:02d}.mp4"
        vtype = b["visual"]["type"]
        src = None if vtype == "text_card" else find_asset(vdir, b["id"], VIDEO_EXT if vtype in ("ai_video", "footage") else IMAGE_EXT)
        if src and src.suffix.lower() in VIDEO_EXT:
            seg_video(src, dur, seg, style, enc); used.append((b["id"], "video", src.name))
        elif src:
            seg_image(src, dur, seg, style, enc, n); used.append((b["id"], "image", src.name))
        else:
            seg_card(col["background"], col["accent"], dur, seg, enc)
            used.append((b["id"], "text_card" if vtype == "text_card" else "PLACEHOLDER card (shot missing)", ""))
            if vtype != "text_card":
                b = dict(b, visual=dict(b["visual"], type="text_card"))
                script["beats"][n] = b
        seg_files.append(seg)
        print(f"  segment {b['id']}: {dur:.2f}s  {used[-1][1]} {used[-1][2]}")

    lst = build / "segments.txt"
    lst.write_text("".join(f"file '{p.name}'\n" for p in seg_files))
    joined = build / "video.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(joined)])

    ass = build / "captions.ass"
    ass.write_text(build_ass(ws, brand, script, timing), encoding="utf-8")

    # ---- final composite
    inputs = ["-i", str(joined), "-i", str(voice)]
    fontsdir = ws / "brand" / "fonts"
    sub = f"ass='{ff_path(ass)}'" + (f":fontsdir='{ff_path(fontsdir)}'" if fontsdir.exists() else "")
    fc = [f"[0:v]{sub}[v0]"]
    vlast, idx = "v0", 2
    pb = style.get("progress_bar", {})
    if pb.get("enabled"):
        hgt = pb.get("height", 8)
        inputs += ["-f", "lavfi", "-i", f"color=c=0x{col['accent'].lstrip('#')}:s={W}x{hgt}:r={FPS}"]
        fc.append(f"[{vlast}][{idx}:v]overlay=x='-W+W*t/{total:.3f}':y=H-{hgt}:shortest=1[v{idx}]")
        vlast, idx = f"v{idx}", idx + 1
    logo = ws / brand.get("logo_file", "")
    if brand.get("logo_file") and logo.is_file():
        inputs += ["-i", str(logo)]
        fc.append(f"[{idx}:v]scale=150:-1,format=rgba,colorchannelmixer=aa=0.9[lg]")
        fc.append(f"[{vlast}][lg]overlay=x=W-w-50:y=90[v{idx}]")
        vlast, idx = f"v{idx}", idx + 1
    music = ws / brand.get("music_file", "")
    if brand.get("music_file") and music.is_file():
        inputs += ["-stream_loop", "-1", "-i", str(music)]
        vol = brand.get("music_volume", 0.12)
        fc.append(f"[1:a]aformat=sample_rates=44100:channel_layouts=stereo,asplit=2[vo][vk]")
        fc.append(f"[{idx}:a]aformat=sample_rates=44100:channel_layouts=stereo,volume={vol},"
                  f"afade=t=out:st={max(total-1.2,0):.2f}:d=1.2[mu]")
        fc.append("[mu][vk]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=300[duck]")
        fc.append("[vo][duck]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[aout]")
        idx += 1
    else:
        fc.append("[1:a]aformat=sample_rates=44100:channel_layouts=stereo,loudnorm=I=-14:TP=-1.5:LRA=11[aout]")

    final = out / "reel.mp4"
    run(["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(fc), "-map", f"[{vlast}]", "-map", "[aout]",
         "-t", f"{total:.3f}", *enc, "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-movflags", "+faststart", str(final)])

    # ---- contact sheet for review (one frame from the middle of each beat)
    frames = []
    for n, b in enumerate(timing["beats"]):
        fp = build / f"frame_{n:02d}.jpg"
        mid = b["start"] + min(1.0, (b["end"] - b["start"]) / 2)
        run(["ffmpeg", "-y", "-ss", f"{mid:.2f}", "-i", str(final), "-frames:v", "1", "-vf", "scale=270:480", str(fp)])
        frames.append(fp)
    cols = min(len(frames), 5)
    rows = -(-len(frames) // cols)
    run(["ffmpeg", "-y", *sum((["-i", str(f)] for f in frames), []), "-filter_complex",
         "".join(f"[{i}:v]" for i in range(len(frames))) +
         f"xstack=inputs={len(frames)}:layout=" + "|".join(f"{(i % cols)*270}_{(i // cols)*480}" for i in range(len(frames)))
         + f":fill=black[o]" if len(frames) > 1 else "[0:v]null[o]",
         "-map", "[o]", str(build / "preview.jpg")])
    for f in frames:
        f.unlink(missing_ok=True)

    placeholders = [u[0] for u in used if u[1].startswith("PLACEHOLDER")]
    write_json(build / "render_report.json", {"duration": total, "segments": used, "placeholders": placeholders, "draft": a.draft})
    set_stage(rd, "rendered", "draft" if a.draft else "final")
    print(f"OK render: {final} ({duration(final):.1f}s)")
    print(f"Preview sheet: {build / 'preview.jpg'}")
    if placeholders:
        print(f"NOTE: {len(placeholders)} beat(s) used placeholder cards: {', '.join(placeholders)}")


if __name__ == "__main__":
    main()
