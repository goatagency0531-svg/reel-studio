---
name: reel-craft
description: Shared craft knowledge for Reel Studio agents — the script.json format, hook formulas, script rules, the review rubric, and how to write Higgsfield prompts. Load when writing, reviewing, editing or designing a reel.
user-invocable: false
---

# Reel craft

Every reel lives in `reels/<slug>/` inside the user's workspace (the current directory).
The brand profile is `brand/brand.json`. Always read it first: language, audience, offer, tone,
banned words, default CTA, colors and `reel.target_seconds` / `reel.words_per_second`.

Write all viewer-facing text (voiceover, on_screen, caption, poster) in `brand.language`.
Write Higgsfield prompts in English (the models follow English best).

## script.json — the contract between agents

```json
{
  "title": "internal name",
  "language": "en",
  "hook_formula": "which formula from hooks.md",
  "target_seconds": 30,
  "beats": [
    {
      "id": "b1",
      "voiceover": "exact words spoken. 1–3 short sentences.",
      "on_screen": "2–5 WORD PUNCH (emphasis card)",
      "visual": {"type": "ai_video | ai_image | footage | text_card", "prompt": "Higgsfield prompt", "motion": "camera move"}
    }
  ],
  "caption": "Instagram caption, first line is a second hook",
  "hashtags": ["#max5"],
  "poster": {"headline": "≤ 7 words", "subline": "≤ 4 words"}
}
```

Rules for the format:
- Beat ids are `b1`, `b2`, … in order. 4–9 beats for 20–60s.
- Beat length ≈ words ÷ `words_per_second`. Keep each beat 2–6 s; a new visual every 2–4 s holds attention.
- `b1` is the hook: ≤ 2.5 s spoken (≈ 6–9 words). Its visual must be the strongest shot.
- `on_screen` restates, never duplicates the voiceover word-for-word. Empty string is allowed.
- `text_card` = brand-coloured card with big text; use for lists, numbers, the CTA, or when no visual adds anything. Max 2 per reel.
- `footage` = the user's own clip, saved as `visuals/<id>.mp4`.
- The last beat contains the CTA (from brand `cta_default` unless the brief says otherwise).

Detailed guides (read the one you need):
- `hooks.md` (same folder as this file): 14 hook formulas with examples
- `rubric.md` (same folder as this file): the review rubric and pass threshold
- `visual-prompts.md` (same folder as this file): how to write Higgsfield prompts that cut together
