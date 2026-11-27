---
name: affiliate-video-edit
description: Edit a short TikTok/Reels affiliate video (product held to camera + the user's voice over) in the user's saved house style with HyperFrames — clean VO, cut pauses, word-by-word captions, plain book/product titles, no sound effects. Use whenever the user asks to edit, cut, caption or render an affiliate video, or says "same style as buku final".
---

# Affiliate video edit — house style

Reference edit: `video/` + `scripts/build_composition.py` in this repo ("buku final", 2 books, 20.8s).
Copy that project as the starting point for a new video; change the tables at the top of
`build_composition.py` (SHOTS, GROUPS, STICKERS, DURATION) and the HTML text, then re-run it.

The user writes in Malay (mixed with English). Reply the same way.

## Ground rules the user set

- **Preview first, never render until the user says so.** Rendering spends nothing locally, but the
  user wants to approve a preview before any final file. Never use `hyperframes cloud` (HeyGen credits).
- **No sound effects.** Voice over only. (The user said SFX made it "obviously AI-made".)
- **No logos / icon graphics** (e.g. no shopping-bag icon for the yellow basket). Keep it simple.
- **Product / book names: plain white text, simple font, no yellow, no boxes, no numbers.**
- Final file name is whatever the user asks (last one: `buku final.mp4`).

## Look

| Element | Style |
|---|---|
| Canvas | 1080×1920 portrait, 30 fps |
| Captions | Poppins 800, 76px, white with black outline/shadow, 2–4 words per line, broken at punctuation, placed at top ≈1120px (clear of TikTok's bottom UI and right-side buttons, x 90–930) |
| Word highlight | the word being spoken turns **black on a white rounded pill** (radius 16px), small scale pop 0.92→1.06→1; it stays lit until the next word starts (gap < 0.35s) |
| Book / product names | Inter 600, 56px, white, soft text shadow, author/brand under it in Inter 400 32px at 82% white; top-left at top 260px, left 80px; fade-up 16px over 0.35s; fade out 0.2s before the next section |
| Hook text | the script's on-screen text at top 250px, centred: line 1 Poppins 800 64px white; line 2 Poppins 900 72px in a yellow (#F5C518) pill with dark text; 👇 bouncing under it; leaves at the end of the hook (user kept this one yellow element) |
| Emoji stickers | one emoji pops (back.out, ~130px, slight rotation) on a keyword in the body (e.g. 😅 awkward, ✅ membantu, 💸 duit, 🧠 mindset), beside the caption, gone after ~0.8s; max one at a time |
| Ending | the product/book names again, same plain style, stacked, fading up one after the other |
| Shading | gradient darkening top 0–26% and bottom 48–100% so white text reads on any footage |

## Motion & cutting

- Cut on the voice: one shot per caption phrase, roughly 1–2.5s each. Match footage to what is being said
  (product name said → that product's cover; "inside / content" → inside pages; CTA → all products together).
- Hook shots (first ~4s): `punch` — scale 1.16→1.04 in 0.28s (power3.out) then slow settle.
- Body shots: `drift` (1.0→1.07 linear over the shot) or `drift-in` (1.12→1.0) on the first shot of a section.
- Section changes (hook→product 1→product 2→CTA): 0.22s blur(14px)+brightness flash on the new shot,
  plus a 0.25s white flash fading from 0.55 opacity (`immediateRender: false` on every flash fromTo).
- Prefer steady, sharp frames; skip blurry hand-movement frames. Check with `hyperframes snapshot`.

## Audio

1. Clean the VO with ffmpeg:
   `volume=-3dB,highpass=f=80,lowpass=f=15000,afftdn=nr=12:nf=-55:tn=1,deesser=i=0.4,acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120:makeup=2,loudnorm=I=-14:TP=-1.5:LRA=9`
2. Remove pauses: find silent runs (10ms RMS < loud-percentile − 32 dB) ≥ 0.12s and shrink each to ~0.10s,
   joined with 8ms crossfades; trim leading/trailing breath.
3. Strong hook: drop filler openers ("Okay,", "So,") so the video starts on the first real word —
   find the cut with a fine (5ms) energy scan and confirm by transcribing from the cut point.

## Transcribe

- faster-whisper **large-v3**, `language="ms"`, `word_timestamps=True`, pass the user's script as
  `initial_prompt`. (`medium` mishears casual Malay — "I" → "ayah".) Pass audio as a numpy array
  (the installed `av` breaks `decode_audio`). Set `HF_HUB_DISABLE_XET=1` for the model download.
- Re-transcribe the **final cleaned/tightened** audio so timestamps match the edit.
- Correct words against the script, but caption what the user actually said; flag any unclear phrase.

## Workflow

1. Download footage (Drive: `https://drive.usercontent.google.com/download?id=<id>&export=download&confirm=t`;
   phone clips carry rotation −90 → transcode upright 1080×1920 for the project, 540×960 proxies for preview).
2. Contact sheets (1 fps with timestamps) to pick shots.
3. Clean VO → cut pauses → transcribe → caption groups.
4. Fill `build_composition.py` tables, build, `npx hyperframes lint .`, `npx hyperframes snapshot --at …` and look.
5. Publish the preview (`video/preview.html` + composition as `composition.html` + proxies) as a private
   Artifact; wait for the user's OK.
6. Only on approval: `npx hyperframes render -o "<name>.mp4" -f 30 -q delivery`, check it, send the file.
