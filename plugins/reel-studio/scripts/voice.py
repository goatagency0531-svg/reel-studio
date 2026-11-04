#!/usr/bin/env python3
"""Generate the voiceover with ElevenLabs (with word timings), or time a recording you made yourself.

Usage:
  python3 voice.py <slug> [--workspace DIR] [--own-recording]

Output (reels/<slug>/voice/):
  voice.mp3     the voiceover
  timing.json   {"duration", "words": [{"w","start","end","beat"}], "beats": [{"id","start","end"}]}

Own recording: put your file at reels/<slug>/voice/voice.mp3 (or .wav/.m4a) and pass --own-recording.
Timings are then estimated from text length, which is good enough for captions in most cases.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

from common import die, duration, load_brand, load_env, need_ffmpeg, read_json, reel_dir, run, set_stage, workspace, write_json

API = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps?output_format=mp3_44100_128"


def beat_spans(beats: list[dict]) -> tuple[str, list[tuple[int, int, str]]]:
    parts, spans, pos = [], [], 0
    for b in beats:
        t = " ".join(b["voiceover"].split())
        spans.append((pos, pos + len(t), b["id"]))
        parts.append(t)
        pos += len(t) + 1
    return " ".join(parts), spans


def beat_at(spans, idx: int) -> str:
    for s, e, bid in spans:
        if s <= idx < e + 1:
            return bid
    return spans[-1][2]


def words_from_alignment(text: str, al: dict, spans) -> list[dict]:
    chars = al["characters"]
    st, en = al["character_start_times_seconds"], al["character_end_times_seconds"]
    words, cur, cs, ce, ci = [], "", None, None, 0
    for i, ch in enumerate(chars):
        if ch.isspace():
            if cur:
                words.append({"w": cur, "start": cs, "end": ce, "beat": beat_at(spans, ci)})
            cur, cs = "", None
            continue
        if not cur:
            cs, ci = st[i], i
        cur += ch
        ce = en[i]
    if cur:
        words.append({"w": cur, "start": cs, "end": ce, "beat": beat_at(spans, ci)})
    return words


def words_estimated(text: str, spans, total: float, lead: float = 0.15, tail: float = 0.3) -> list[dict]:
    tokens = [(m.group(), m.start()) for m in re.finditer(r"\S+", text)]
    # pauses after punctuation count extra
    weights = [len(t) + 1 + (4 if t[-1] in ".!?" else 2 if t[-1] in ",;:" else 0) for t, _ in tokens]
    usable = max(total - lead - tail, 0.5)
    unit = usable / max(sum(weights), 1)
    t, out = lead, []
    for (tok, idx), wgt in zip(tokens, weights):
        d = wgt * unit
        out.append({"w": tok, "start": round(t, 3), "end": round(t + d * 0.85, 3), "beat": beat_at(spans, idx)})
        t += d
    return out


def beats_timing(words: list[dict], beats: list[dict], total: float) -> list[dict]:
    out = []
    ids = [b["id"] for b in beats]
    for n, bid in enumerate(ids):
        ws = [w for w in words if w["beat"] == bid]
        start = 0.0 if n == 0 else out[-1]["end"]
        if n + 1 < len(ids):
            nxt = [w for w in words if w["beat"] == ids[n + 1]]
            end = nxt[0]["start"] if nxt else (ws[-1]["end"] if ws else start + 1)
        else:
            end = total
        out.append({"id": bid, "start": round(start, 3), "end": round(max(end, start + 0.4), 3)})
    return out


def elevenlabs(text: str, brand: dict, out_mp3: Path) -> dict:
    key = os.environ.get("ELEVENLABS_API_KEY")
    el = brand.get("elevenlabs", {})
    voice_id = os.environ.get("ELEVENLABS_VOICE_ID") or el.get("voice_id")
    if not key:
        die("ELEVENLABS_API_KEY is not set. Add it to .env in your workspace, or use --own-recording.")
    if not voice_id:
        die("No ElevenLabs voice_id. Set elevenlabs.voice_id in brand/brand.json (run setup again).")
    body = {
        "text": text,
        "model_id": el.get("model_id", "eleven_multilingual_v2"),
        "voice_settings": {
            "stability": el.get("stability", 0.45),
            "similarity_boost": el.get("similarity_boost", 0.8),
            "style": el.get("style", 0.2),
            "use_speaker_boost": True,
            "speed": el.get("speed", 1.0),
        },
    }
    lang = brand.get("elevenlabs", {}).get("language_code")
    if lang:
        body["language_code"] = lang
    req = urllib.request.Request(
        API.format(voice_id=voice_id),
        data=json.dumps(body).encode(),
        headers={"xi-api-key": key, "Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            data = json.loads(r.read())
    except urllib.error.HTTPError as e:
        die(f"ElevenLabs returned {e.code}: {e.read().decode(errors='replace')[:600]}")
    except urllib.error.URLError as e:
        die(f"Could not reach ElevenLabs: {e.reason}")
    out_mp3.write_bytes(base64.b64decode(data["audio_base64"]))
    return data.get("alignment") or data.get("normalized_alignment")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--workspace")
    ap.add_argument("--own-recording", action="store_true")
    a = ap.parse_args()

    ws = workspace(a.workspace)
    load_env(ws)
    need_ffmpeg()
    brand = load_brand(ws)
    rd = reel_dir(ws, a.slug)
    script = read_json(rd / "script.json")
    beats = script["beats"]
    text, spans = beat_spans(beats)
    vdir = rd / "voice"
    vdir.mkdir(exist_ok=True)
    mp3 = vdir / "voice.mp3"

    if a.own_recording:
        src = next((p for p in [vdir / f"voice.{x}" for x in ("mp3", "wav", "m4a", "aac")] if p.exists()), None)
        if not src:
            die(f"Put your recording at {vdir}/voice.mp3 (or .wav/.m4a) first.")
        if src != mp3:
            run(["ffmpeg", "-y", "-i", str(src), "-ar", "44100", "-ac", "1", "-b:a", "160k", str(mp3)])
        total = duration(mp3)
        words = words_estimated(text, spans, total)
        source = "own_recording_estimated"
    else:
        alignment = elevenlabs(text, brand, mp3)
        total = duration(mp3)
        if alignment and len(alignment.get("characters", [])) > 0:
            words = words_from_alignment(text, alignment, spans)
            source = "elevenlabs_alignment"
        else:
            words = words_estimated(text, spans, total)
            source = "elevenlabs_estimated"

    timing = {"duration": round(total, 3), "source": source, "words": words, "beats": beats_timing(words, beats, total)}
    write_json(vdir / "timing.json", timing)
    set_stage(rd, "voiced", source)
    print(f"OK voice: {mp3} ({total:.1f}s, {len(words)} words, timing={source})")
    if total > brand.get("reel", {}).get("max_seconds", 90):
        print(f"WARNING: voiceover is {total:.0f}s, over your max_seconds. Consider trimming the script.")


if __name__ == "__main__":
    main()
