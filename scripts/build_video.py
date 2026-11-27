#!/usr/bin/env python3
"""Build a HyperFrames composition in the saved affiliate house style from a project's edit.json.

    python3 scripts/build_video.py videos/<project>

The project folder holds:
  edit.json                  — the edit (shots, caption groups, hook text, product titles, stickers)
  data/transcript.json       — word timestamps of assets/vo_final.wav
  assets/vo_final.wav        — cleaned voice over, pauses removed
  assets/footage/clipN.mp4   — upright 1080x1920 footage (proxies for preview)
and gets index.html written into it. Style rules: .claude/skills/affiliate-video-edit/SKILL.md
"""
import html
import json
import sys
from pathlib import Path

ACCENT = "#F5C518"  # only used for the hook pill
SHADOW = ("0 4px 0 #000, 0 0 14px rgba(0,0,0,.85), 3px 3px 0 #000, -3px -3px 0 #000, "
          "3px -3px 0 #000, -3px 3px 0 #000")


def esc(s):
    return html.escape(s, quote=True)


def build(project: Path):
    cfg = json.loads((project / "edit.json").read_text())
    words = json.loads((project / "data" / "transcript.json").read_text())
    dur = cfg["duration"]
    shots, groups = cfg["shots"], cfg["groups"]
    cuts = {round(t, 2) for t in cfg.get("section_cuts", [])}
    stickers = cfg.get("stickers", [])
    hook = cfg.get("hook")
    titles = cfg.get("titles", [])
    ending = cfg.get("ending")

    body, js = [], []

    # ---- footage
    for i, (s, e, clip, ms, motion) in enumerate(shots):
        d = e - s
        body.append(f'      <video id="shot{i}" class="clip shot" src="assets/footage/clip{clip}.mp4" '
                    f'data-start="{s:.2f}" data-duration="{d:.2f}" data-media-start="{ms:.2f}" '
                    f'data-track-index="0" muted playsinline preload="auto"></video>')
        sel = f'"#shot{i}"'
        if motion == "punch":
            js.append(f'tl.fromTo({sel}, {{scale: 1.16}}, {{scale: 1.04, duration: 0.28, ease: "power3.out"}}, {s:.2f});')
            js.append(f'tl.to({sel}, {{scale: 1.0, duration: {max(d - 0.28, 0.1):.2f}, ease: "none"}}, {s + 0.28:.2f});')
        elif motion == "drift-in":
            js.append(f'tl.fromTo({sel}, {{scale: 1.12}}, {{scale: 1.0, duration: {d:.2f}, ease: "power1.out"}}, {s:.2f});')
        else:
            js.append(f'tl.fromTo({sel}, {{scale: 1.0}}, {{scale: 1.07, duration: {d:.2f}, ease: "none"}}, {s:.2f});')
        if round(s, 2) in cuts:
            js.append(f'tl.fromTo({sel}, {{filter: "blur(14px) brightness(1.35)"}}, {{filter: "blur(0px) brightness(1)", duration: 0.22, ease: "power2.out"}}, {s:.2f});')
    body.append('      <div id="shade"></div>\n      <div id="flash"></div>')
    for t in sorted(cuts):
        js.append(f'tl.fromTo("#flash", {{opacity: 0.55}}, {{opacity: 0, duration: 0.25, ease: "power2.out", immediateRender: false}}, {t:.2f});')

    # ---- hook text (the only yellow element)
    if hook:
        he = hook["end"]
        body.append(f'      <div id="hook" class="clip" data-start="0" data-duration="{he:.2f}" data-track-index="1">\n'
                    f'        <div class="l1">{esc(hook["l1"])}</div>\n'
                    f'        <div class="l2">{esc(hook["l2"])}</div>\n'
                    f'        <span class="arrow">👇</span>\n      </div>')
        js += ['tl.fromTo("#hook .l1", {y: -40, opacity: 0}, {y: 0, opacity: 1, duration: 0.3, ease: "back.out(2)"}, 0.06);',
               'tl.fromTo("#hook .l2", {scale: 0.6, opacity: 0}, {scale: 1, opacity: 1, duration: 0.32, ease: "back.out(2.5)"}, 0.32);',
               f'tl.to("#hook .arrow", {{y: 14, duration: 0.35, repeat: {max(int((he - 0.8) / 0.35), 1)}, yoyo: true, ease: "sine.inOut"}}, 0.6);',
               f'tl.to("#hook", {{y: -30, opacity: 0, duration: 0.2, ease: "power2.in"}}, {he - 0.2:.2f});']

    # ---- product / book names: plain white text
    for i, t in enumerate(titles):
        body.append(f'      <div id="title{i}" class="clip book" data-start="{t["start"]:.2f}" '
                    f'data-duration="{t["end"] - t["start"]:.2f}" data-track-index="1">\n'
                    f'        <div class="title">{esc(t["title"])}</div><span class="by">{esc(t["sub"])}</span>\n      </div>')
        js.append(f'tl.fromTo("#title{i}", {{y: 16, opacity: 0}}, {{y: 0, opacity: 1, duration: 0.35, ease: "power2.out"}}, {t["start"]:.2f});')
        js.append(f'tl.to("#title{i}", {{opacity: 0, duration: 0.2}}, {t["end"] - 0.2:.2f});')
    if ending:
        rows = "\n".join(f'        <div class="row row{k}"><span class="title">{esc(it["title"])}</span>'
                         f'<span class="by">{esc(it["sub"])}</span></div>' for k, it in enumerate(ending["items"]))
        body.append(f'      <div id="pick" class="clip" data-start="{ending["start"]:.2f}" '
                    f'data-duration="{dur - ending["start"]:.2f}" data-track-index="1">\n{rows}\n      </div>')
        for k in range(len(ending["items"])):
            js.append(f'tl.fromTo("#pick .row{k}", {{y: 16, opacity: 0}}, {{y: 0, opacity: 1, duration: 0.35, ease: "power2.out"}}, {ending["start"] + 0.02 + 0.18 * k:.2f});')

    # ---- emoji stickers
    for i, (t, e, x, y, r) in enumerate(stickers):
        body.append(f'      <div id="stk{i}" class="clip sticker" data-start="{t:.2f}" data-duration="1.00" '
                    f'data-track-index="3" style="left:{x}px;top:{y}px">{e}</div>')
        js.append(f'tl.fromTo("#stk{i}", {{scale: 0, rotation: {r - 30}}}, {{scale: 1, rotation: {r}, duration: 0.32, ease: "back.out(3)"}}, {t:.2f});')
        js.append(f'tl.to("#stk{i}", {{scale: 0, opacity: 0, duration: 0.18, ease: "power2.in"}}, {t + 0.8:.2f});')

    # ---- captions: word-by-word, spoken word black on a white pill
    starts = [w["s"] for w in words]
    for gi, (a, b) in enumerate(groups):
        start = words[a]["s"]
        end = words[groups[gi + 1][0]]["s"] if gi + 1 < len(groups) else dur
        spans = " ".join(f'<span class="w" id="w{k}">{esc(words[k]["w"])}</span>' for k in range(a, b))
        body.append(f'      <div id="cap{gi}" class="clip cap" data-start="{start:.2f}" '
                    f'data-duration="{end - start:.2f}" data-track-index="2">{spans}</div>')
        js.append(f'tl.fromTo("#cap{gi}", {{y: 24, opacity: 0}}, {{y: 0, opacity: 1, duration: 0.14, ease: "back.out(2)"}}, {start:.2f});')
        for k in range(a, b):
            on = words[k]["s"]
            nxt = starts[k + 1] if k + 1 < len(words) else dur
            off = nxt if nxt - words[k]["e"] < 0.35 else words[k]["e"] + 0.1
            if k == b - 1:
                off = min(off, end)
            js.append(f'tl.set("#w{k}", {{backgroundColor: "#ffffff", color: "#0b0b0b", textShadow: "none"}}, {on:.2f});')
            js.append(f'tl.fromTo("#w{k}", {{scale: 0.92}}, {{scale: 1.06, duration: 0.09, ease: "power2.out"}}, {on:.2f});')
            js.append(f'tl.to("#w{k}", {{scale: 1, duration: 0.08}}, {on + 0.09:.2f});')
            js.append(f'tl.set("#w{k}", {{backgroundColor: "rgba(255,255,255,0)", color: "#ffffff", textShadow: SHADOW}}, {off:.2f});')

    # ---- voice over only, no sound effects
    body.append(f'      <audio id="vo" class="clip" src="assets/vo_final.wav" data-start="0" '
                f'data-duration="{dur:.2f}" data-volume="1" data-track-index="5"></audio>')

    page = (TEMPLATE.replace("__TITLE__", esc(cfg.get("title", project.name)))
            .replace("__ACCENT__", ACCENT).replace("__DUR__", f"{dur:.2f}")
            .replace("__BODY__", "\n".join(body)).replace("__SHADOW__", SHADOW)
            .replace("__TIMELINE__", "\n      ".join(js)))
    (project / "index.html").write_text(page)
    print("wrote", project / "index.html")


TEMPLATE = """<!doctype html>
<html lang="ms" data-resolution="portrait">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>__TITLE__</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@600;800;900&family=Inter:wght@400;600&family=Noto+Color+Emoji&display=block" rel="stylesheet" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <style>
      :root {
        --ground: #0b0b0b;
        --ink: #ffffff;
        --accent: __ACCENT__;
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
      .cap { position: absolute; left: 90px; right: 150px; top: 1120px; z-index: 20; text-align: center;
        font-weight: 800; font-size: 76px; line-height: 1.28; letter-spacing: -0.01em; }
      .cap .w { display: inline-block; padding: 0 14px; margin: 4px -2px; border-radius: 16px; color: #fff;
        background-color: rgba(255,255,255,0); text-shadow: __SHADOW__; }
      #hook { position: absolute; top: 250px; left: 70px; right: 70px; z-index: 15; text-align: center; }
      #hook .l1 { font-weight: 800; font-size: 64px; line-height: 1.1; text-shadow: 0 4px 18px rgba(0,0,0,.8); }
      #hook .l2 { display: inline-block; margin-top: 18px; padding: 10px 30px 14px; border-radius: 22px; background: var(--accent);
        color: #111; font-weight: 900; font-size: 72px; line-height: 1.05; box-shadow: 0 12px 40px rgba(0,0,0,.45); }
      #hook .arrow { display: block; margin-top: 10px; font-size: 64px; }
      .book { position: absolute; left: 80px; right: 80px; top: 260px; z-index: 15; font-family: var(--font-plain);
        text-shadow: 0 2px 16px rgba(0,0,0,.75), 0 1px 3px rgba(0,0,0,.6); }
      .book .title { font-weight: 600; font-size: 56px; line-height: 1.1; color: #fff; letter-spacing: -0.01em; }
      .book .by { display: block; font-weight: 400; font-size: 32px; color: rgba(255,255,255,.82); margin-top: 8px; }
      .sticker { position: absolute; z-index: 21; font-size: 130px; line-height: 1; font-family: "Noto Color Emoji", sans-serif;
        filter: drop-shadow(0 8px 14px rgba(0,0,0,.5)); }
      #pick { position: absolute; left: 80px; right: 80px; top: 260px; z-index: 15; font-family: var(--font-plain);
        text-shadow: 0 2px 16px rgba(0,0,0,.75), 0 1px 3px rgba(0,0,0,.6); }
      #pick .row { display: block; margin-bottom: 22px; }
      #pick .title { display: block; font-weight: 600; font-size: 52px; line-height: 1.1; color: #fff; }
      #pick .by { display: block; font-weight: 400; font-size: 30px; color: rgba(255,255,255,.82); margin-top: 4px; }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="__DUR__" data-width="1080" data-height="1920">
__BODY__
    </div>
    <script>
      const SHADOW = "__SHADOW__";
      const tl = gsap.timeline({ paused: true });
      __TIMELINE__
      window.__timelines = window.__timelines || {};
      window.__timelines["main"] = tl;
      tl.seek(0);
    </script>
  </body>
</html>
"""

if __name__ == "__main__":
    build(Path(sys.argv[1]).resolve())
