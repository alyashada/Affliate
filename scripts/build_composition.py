#!/usr/bin/env python3
"""Generate video/index.html — the HyperFrames composition for the affiliate book video.

Everything that is timed (shots, captions, graphics) lives in the tables below,
so re-timing an edit means changing a number here and re-running:

    python3 scripts/build_composition.py
"""
import html
import json
from pathlib import Path

import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
VIDEO = ROOT / "video"
WORDS = json.loads((VIDEO / "data" / "transcript.json").read_text())

DURATION = 20.77  # length of assets/vo_final.wav (cleaned + pauses removed)
ACCENT = "#F5C518"  # "beg kuning" yellow, also the reference-image accent

# ---------------------------------------------------------------- footage cuts
# (start, end, clip, media_start, motion)   motion: punch | drift | drift-in
SHOTS = [
    # HOOK — both books on screen
    (0.00, 1.50, 1, 2.0, "punch"),    # "Korang nak start baca buku"
    (1.50, 2.86, 1, 16.0, "punch"),   # "tapi tak tahu nak mula dengan apa"
    (2.86, 4.38, 1, 20.0, "punch"),   # "this one's for you"
    # BODY 1 — How to Talk to Anyone
    (4.38, 6.60, 2, 2.0, "drift-in"),  # "Honestly, I pun dulu malas nak baca"
    (6.60, 7.70, 2, 19.4, "drift"),    # page flip — "tapi this one"
    (7.70, 8.92, 2, 26.0, "drift"),    # inside page — "kalau you jenis awkward"
    (8.92, 10.74, 2, 16.6, "drift"),   # HTTA cover — "bila jumpa orang baru macam I lah kan"
    (10.74, 12.42, 2, 59.3, "punch"),  # "memang sangat membantu"
    # BODY 2 — The Psychology of Money
    (12.42, 13.38, 3, 1.3, "drift-in"),  # "Yang ni pasal duit"
    (13.38, 15.14, 3, 28.5, "drift"),    # contents page — "bukan yang pening-pening"
    (15.14, 16.22, 3, 35.3, "punch"),    # "more to mindset"
    # CTA — both books
    (16.22, 18.94, 1, 8.0, "drift-in"),  # "link I letak kat beg kuning"
    (18.94, DURATION, 1, 12.2, "drift"),  # "Pilih satu je dulu"
]
SECTION_CUTS = {4.38, 12.42, 16.22}  # cuts that get a whoosh + blur transition

# ---------------------------------------------------------------- caption groups
# word index ranges [a, b) into transcript.json; 2–4 words per line, broken at punctuation
GROUPS = [(0, 3), (3, 5), (5, 8), (8, 12), (12, 16), (16, 19), (19, 23), (23, 26),
          (26, 30), (30, 34), (34, 38), (38, 41), (41, 45), (45, 48), (48, 51),
          (51, 54), (54, 58), (58, 61), (61, 65), (65, 68)]

# ---------------------------------------------------------------- sound effects
SFX = []  # no sound effects — voice over only

# emoji stickers that pop on a keyword: (time, emoji, x, y, rotate)
STICKERS = [
    (8.62, "😅", 800, 1010, 12),   # awkward
    (11.90, "✅", 820, 1010, -8),  # membantu
    (13.12, "💸", 790, 1010, 10),  # duit
    (15.82, "🧠", 810, 1010, -10), # mindset
]


def esc(s):
    return html.escape(s, quote=True)


def shots_html():
    out = []
    for i, (s, e, clip, ms, _m) in enumerate(SHOTS):
        out.append(
            f'      <video id="shot{i}" class="clip shot" src="assets/footage/clip{clip}.mp4" '
            f'data-start="{s:.2f}" data-duration="{e - s:.2f}" data-media-start="{ms:.2f}" '
            f'data-track-index="0" muted playsinline preload="auto"></video>'
        )
    return "\n".join(out)


def captions_html():
    out = []
    for gi, (a, b) in enumerate(GROUPS):
        start = WORDS[a]["s"]
        end = WORDS[GROUPS[gi + 1][0]]["s"] if gi + 1 < len(GROUPS) else DURATION
        spans = " ".join(
            f'<span class="w" id="w{k}">{esc(WORDS[k]["w"])}</span>' for k in range(a, b)
        )
        out.append(
            f'      <div id="cap{gi}" class="clip cap" data-start="{start:.2f}" '
            f'data-duration="{end - start:.2f}" data-track-index="2">{spans}</div>'
        )
    return "\n".join(out)


def sfx_html():
    out = [
        '      <audio id="vo" class="clip" src="assets/vo_final.wav" data-start="0" '
        f'data-duration="{DURATION:.2f}" data-volume="1" data-track-index="5"></audio>'
    ]
    lane_free = {}  # studio lane -> time it frees up, so overlapping sfx sit on separate lanes
    for i, (t, name, vol) in enumerate(SFX):
        d = sf.info(str(VIDEO / "assets" / "sfx" / f"{name}.wav")).duration
        lane = next(l for l in range(6, 20) if lane_free.get(l, 0) <= t + 1e-6)
        lane_free[lane] = t + d
        out.append(
            f'      <audio id="sfx{i}" class="clip" src="assets/sfx/{name}.wav" '
            f'data-start="{t:.2f}" data-duration="{d:.2f}" data-volume="{vol}" data-track-index="{lane}"></audio>'
        )
    return "\n".join(out)


def stickers_html():
    return "\n".join(
        f'      <div id="stk{i}" class="clip sticker" data-start="{t:.2f}" data-duration="1.00" '
        f'data-track-index="3" style="left:{x}px;top:{y}px">{e}</div>'
        for i, (t, e, x, y, _r) in enumerate(STICKERS)
    )


def timeline_js():
    js = []
    # shot motion
    for i, (s, e, _c, _ms, motion) in enumerate(SHOTS):
        d = e - s
        sel = f'"#shot{i}"'
        if motion == "punch":
            js.append(f'tl.fromTo({sel}, {{scale: 1.16}}, {{scale: 1.04, duration: 0.28, ease: "power3.out"}}, {s:.2f});')
            js.append(f'tl.to({sel}, {{scale: 1.0, duration: {max(d - 0.28, 0.1):.2f}, ease: "none"}}, {s + 0.28:.2f});')
        elif motion == "drift-in":
            js.append(f'tl.fromTo({sel}, {{scale: 1.12}}, {{scale: 1.0, duration: {d:.2f}, ease: "power1.out"}}, {s:.2f});')
        else:
            js.append(f'tl.fromTo({sel}, {{scale: 1.0}}, {{scale: 1.07, duration: {d:.2f}, ease: "none"}}, {s:.2f});')
        if round(s, 2) in SECTION_CUTS:
            js.append(f'tl.fromTo({sel}, {{filter: "blur(14px) brightness(1.35)"}}, {{filter: "blur(0px) brightness(1)", duration: 0.22, ease: "power2.out"}}, {s:.2f});')
    # flash on section cuts
    for n, t in enumerate(sorted(SECTION_CUTS)):
        ir = ", immediateRender: false"  # #flash rests at opacity 0 (CSS) until each cut
        js.append(f'tl.fromTo("#flash", {{opacity: 0.55}}, {{opacity: 0, duration: 0.25, ease: "power2.out"{ir}}}, {t:.2f});')

    # captions: group entrance + word-by-word highlight (white text -> black text on white pill)
    starts = [w["s"] for w in WORDS]
    for gi, (a, b) in enumerate(GROUPS):
        js.append(f'tl.fromTo("#cap{gi}", {{y: 24, opacity: 0}}, {{y: 0, opacity: 1, duration: 0.14, ease: "back.out(2)"}}, {WORDS[a]["s"]:.2f});')
        for k in range(a, b):
            on = WORDS[k]["s"]
            nxt = starts[k + 1] if k + 1 < len(WORDS) else DURATION
            off = nxt if nxt - WORDS[k]["e"] < 0.35 else WORDS[k]["e"] + 0.1
            if k == b - 1:  # last word of the line stays lit until the line leaves
                off = min(off, nxt)
            js.append(f'tl.set("#w{k}", {{backgroundColor: "#ffffff", color: "#0b0b0b", textShadow: "none"}}, {on:.2f});')
            js.append(f'tl.fromTo("#w{k}", {{scale: 0.92}}, {{scale: 1.06, duration: 0.09, ease: "power2.out"}}, {on:.2f});')
            js.append(f'tl.to("#w{k}", {{scale: 1, duration: 0.08}}, {on + 0.09:.2f});')
            js.append(f'tl.set("#w{k}", {{backgroundColor: "rgba(255,255,255,0)", color: "#ffffff", textShadow: SHADOW}}, {off:.2f});')

    # stickers
    for i, (t, _e, _x, _y, r) in enumerate(STICKERS):
        js.append(f'tl.fromTo("#stk{i}", {{scale: 0, rotation: {r - 30}}}, {{scale: 1, rotation: {r}, duration: 0.32, ease: "back.out(3)"}}, {t:.2f});')
        js.append(f'tl.to("#stk{i}", {{scale: 0, opacity: 0, duration: 0.18, ease: "power2.in"}}, {t + 0.8:.2f});')
    return "\n      ".join(js)


GRAPHICS_JS = """
      // HOOK title — on-screen text from the script
      tl.fromTo("#hook .l1", {y: -40, opacity: 0}, {y: 0, opacity: 1, duration: 0.3, ease: "back.out(2)"}, 0.06);
      tl.fromTo("#hook .l2", {scale: 0.6, opacity: 0}, {scale: 1, opacity: 1, duration: 0.32, ease: "back.out(2.5)"}, 0.32);
      tl.to("#hook .arrow", {y: 14, duration: 0.35, repeat: 9, yoyo: true, ease: "sine.inOut"}, 0.6);
      tl.to("#hook", {y: -30, opacity: 0, duration: 0.2, ease: "power2.in"}, 4.18);

      // book names: soft fade-up
      tl.fromTo("#chip1", {y: 16, opacity: 0}, {y: 0, opacity: 1, duration: 0.35, ease: "power2.out"}, 4.50);
      tl.to("#chip1", {opacity: 0, duration: 0.2}, 12.22);
      tl.fromTo("#chip2", {y: 16, opacity: 0}, {y: 0, opacity: 1, duration: 0.35, ease: "power2.out"}, 12.56);
      tl.to("#chip2", {opacity: 0, duration: 0.2}, 16.05);


      // final: both book names
      tl.fromTo("#pick .row1", {y: 16, opacity: 0}, {y: 0, opacity: 1, duration: 0.35, ease: "power2.out"}, 18.96);
      tl.fromTo("#pick .row2", {y: 16, opacity: 0}, {y: 0, opacity: 1, duration: 0.35, ease: "power2.out"}, 19.14);
"""


TEMPLATE = """<!doctype html>
<html lang="ms" data-resolution="portrait">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>Buku Pertama — affiliate</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@600;800;900&family=Inter:wght@400;600&family=Noto+Color+Emoji&display=block" rel="stylesheet" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <style>
      :root {
        --ground: #0b0b0b;
        --ink: #ffffff;
        --accent: __ACCENT__;
        --chip: rgba(14, 14, 14, 0.82);
        --font-display: "Poppins", "Noto Color Emoji", sans-serif;
        --font-plain: "Inter", "Helvetica Neue", Arial, sans-serif;
      }
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: 1080px; height: 1920px; overflow: hidden; background: var(--ground); }
      #root { position: relative; width: 1080px; height: 1920px; overflow: hidden; font-family: var(--font-display); color: var(--ink); }

      .shot { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; transform-origin: 50% 45%; }
      #shade { position: absolute; inset: 0; pointer-events: none; z-index: 5;
        background: linear-gradient(180deg, rgba(0,0,0,.55) 0%, rgba(0,0,0,0) 26%, rgba(0,0,0,0) 48%, rgba(0,0,0,.55) 78%, rgba(0,0,0,.7) 100%); }
      #flash { position: absolute; inset: 0; background: #fff; opacity: 0; z-index: 6; pointer-events: none; }

      /* captions: white words, the spoken word turns black on a white pill */
      .cap { position: absolute; left: 90px; right: 150px; top: 1120px; z-index: 20; text-align: center;
        font-weight: 800; font-size: 76px; line-height: 1.28; letter-spacing: -0.01em; }
      .cap .w { display: inline-block; padding: 0 14px; margin: 4px -2px; border-radius: 16px; color: #fff;
        background-color: rgba(255,255,255,0); text-shadow: 0 4px 0 #000, 0 0 14px rgba(0,0,0,.85), 3px 3px 0 #000, -3px -3px 0 #000, 3px -3px 0 #000, -3px 3px 0 #000; }

      /* hook title */
      #hook { position: absolute; top: 250px; left: 70px; right: 70px; z-index: 15; text-align: center; }
      #hook .l1 { font-weight: 800; font-size: 64px; line-height: 1.1; text-shadow: 0 4px 18px rgba(0,0,0,.8); }
      #hook .l2 { display: inline-block; margin-top: 18px; padding: 10px 30px 14px; border-radius: 22px; background: var(--accent);
        color: #111; font-weight: 900; font-size: 72px; line-height: 1.05; box-shadow: 0 12px 40px rgba(0,0,0,.45); }
      #hook .arrow { display: block; margin-top: 10px; font-size: 64px; }

      /* book names: plain white text, simple sans */
      .book { position: absolute; left: 80px; right: 80px; top: 260px; z-index: 15; font-family: var(--font-plain);
        text-shadow: 0 2px 16px rgba(0,0,0,.75), 0 1px 3px rgba(0,0,0,.6); }
      .book .title { font-weight: 600; font-size: 56px; line-height: 1.1; color: #fff; letter-spacing: -0.01em; }
      .book .by { display: block; font-weight: 400; font-size: 32px; color: rgba(255,255,255,.82); margin-top: 8px; }

      .sticker { position: absolute; z-index: 21; font-size: 130px; line-height: 1; font-family: "Noto Color Emoji", sans-serif;
        filter: drop-shadow(0 8px 14px rgba(0,0,0,.5)); }


      /* final: both book names, same plain style */
      #pick { position: absolute; left: 80px; right: 80px; top: 260px; z-index: 15; font-family: var(--font-plain);
        text-shadow: 0 2px 16px rgba(0,0,0,.75), 0 1px 3px rgba(0,0,0,.6); }
      #pick .row { display: block; margin-bottom: 22px; }
      #pick .title { display: block; font-weight: 600; font-size: 52px; line-height: 1.1; color: #fff; }
      #pick .by { display: block; font-weight: 400; font-size: 30px; color: rgba(255,255,255,.82); margin-top: 4px; }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="__DUR__" data-width="1080" data-height="1920">
      <!-- footage -->
__SHOTS__
      <div id="shade"></div>
      <div id="flash"></div>

      <!-- hook title (script on-screen text) -->
      <div id="hook" class="clip" data-start="0" data-duration="4.40" data-track-index="1">
        <div class="l1">kalau nak start baca,</div>
        <div class="l2">start dengan ni dulu</div>
        <span class="arrow">👇</span>
      </div>

      <!-- book names -->
      <div id="chip1" class="clip book" data-start="4.50" data-duration="7.95" data-track-index="1">
        <div class="title">How to Talk to Anyone</div><span class="by">Leil Lowndes</span>
      </div>
      <div id="chip2" class="clip book" data-start="12.56" data-duration="3.72" data-track-index="1">
        <div class="title">The Psychology of Money</div><span class="by">Morgan Housel</span>
      </div>

      <!-- keyword stickers -->
__STICKERS__

      <!-- final: pick one -->
      <div id="pick" class="clip" data-start="18.94" data-duration="__PICKDUR__" data-track-index="1">
        <div class="row row1"><span class="title">How to Talk to Anyone</span><span class="by">Leil Lowndes</span></div>
        <div class="row row2"><span class="title">The Psychology of Money</span><span class="by">Morgan Housel</span></div>
      </div>

      <!-- captions -->
__CAPTIONS__

      <!-- audio: cleaned voice over -->
__AUDIO__
    </div>
    <script>
      const SHADOW = "0 4px 0 #000, 0 0 14px rgba(0,0,0,.85), 3px 3px 0 #000, -3px -3px 0 #000, 3px -3px 0 #000, -3px 3px 0 #000";
      const tl = gsap.timeline({ paused: true });
      __TIMELINE__
__GRAPHICS__
      window.__timelines = window.__timelines || {};
      window.__timelines["main"] = tl;
      tl.seek(0);
    </script>
  </body>
</html>
"""


def main():
    page = (
        TEMPLATE.replace("__ACCENT__", ACCENT)
        .replace("__DUR__", f"{DURATION:.2f}")
        .replace("__PICKDUR__", f"{DURATION - 18.94:.2f}")
        .replace("__SHOTS__", shots_html())
        .replace("__STICKERS__", stickers_html())
        .replace("__CAPTIONS__", captions_html())
        .replace("__AUDIO__", sfx_html())
        .replace("__TIMELINE__", timeline_js())
        .replace("__GRAPHICS__", GRAPHICS_JS)
    )
    (VIDEO / "index.html").write_text(page)
    print("wrote", VIDEO / "index.html")


if __name__ == "__main__":
    main()
