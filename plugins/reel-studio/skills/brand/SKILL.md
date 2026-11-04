---
name: brand
description: Save or update the business/brand profile from a pasted block of text (no questions asked). Use when a bot or user pastes business information for Reel Studio.
argument-hint: "<business profile as text or JSON>"
---

# Save brand profile

Profile:
$ARGUMENTS

1. Load `brand/brand.json` if it exists, otherwise start from `${CLAUDE_PLUGIN_ROOT}/templates/brand.example.json`.
2. Map the pasted information onto the fields: brand_name, handle, language (ISO code, e.g. `mn`, `en`), audience, offer, tone (3 words), banned_words, cta_default (in the brand language), colors (hex), style (`bold`|`minimal`), reel.target_seconds, elevenlabs.voice_id / model_id, higgsfield.mode.
   - Keep anything already set that the new text doesn't mention.
   - Missing colors: choose a tasteful palette that fits the business and say so.
   - Extra useful facts (products, prices, address, opening hours, proof, customer pains, what makes them different) go to `brand/business.md` as bullet points. The scriptwriter reads it.
   - Example captions or posts in the owner's voice go to `brand/voice-samples.md`.
3. Create `brand/`, `reels/` and a `.gitignore` with `.env` and `reels/*/build/` if missing.
4. Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/doctor.py"`. Do not treat missing optional items (logo, music) as errors.
5. Reply with a 5-line summary of the saved profile and anything still missing that matters (e.g. no ElevenLabs voice_id).

If language, audience or offer cannot be determined, end with `STATUS: NEED_INFO` instead.

## Status protocol (a bot may be reading this session)
- Never open question dialogs (no AskUserQuestion). If something is missing, ask in plain text and end with `STATUS: NEED_INFO <one-line question>`.
- End **every** final reply with exactly one status line, alone on the last line, in English, no formatting:
  `STATUS: BRAND_SAVED` · `STATUS: NEEDS_APPROVAL slug=<slug>` · `STATUS: WAITING_FOR_SHOTS slug=<slug>` · `STATUS: DONE slug=<slug>` · `STATUS: NEED_INFO <question>` · `STATUS: ERROR <short reason>`
- Talk to the operator in English. Viewer-facing reel content stays in the brand language.
