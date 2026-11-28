#!/usr/bin/env python3
"""Build a text-only "vtt goyang" HyperFrames composition from a project's edit.json.

    python3 scripts/build_goyang.py videos/<project>

Style: no voice over, no sound effects (the user adds a trending song in TikTok). The footage
sways to a 120 BPM beat ("goyang"), cuts land on the beat, and TikTok-style plain white text
sits mid-screen: a hook, then points popping in one by one, then the CTA.

edit.json keys (points, cta and wobble are optional):
  duration, beat (s), wobble {deg, x, half}, plain_cuts (true = straight cuts, no punch-in/flash), zoom (e.g. 0.06), zoom_period (s)
  shots   [[start, end, clip, media_start], ...]   footage in assets/footage/clipN.mp4
  hook    {end, text, size (px, optional)}
  points  {end, items: [{t, title, sub}, ...]}     items stay on screen until points.end
  cta     {start, l1, l2}
"""
import html
import json
import sys
from pathlib import Path

# TikTok's own text look: white, thin dark edge, soft shadow — no boxes, no colour
EDGE = ("0 0 3px rgba(0,0,0,.95), 2px 2px 0 rgba(0,0,0,.55), -2px -2px 0 rgba(0,0,0,.55), "
        "2px -2px 0 rgba(0,0,0,.55), -2px 2px 0 rgba(0,0,0,.55), 0 4px 18px rgba(0,0,0,.55)")


def esc(s):
    return html.escape(s, quote=True)


def build(project: Path):
    cfg = json.loads((project / "edit.json").read_text())
    dur = cfg["duration"]
    wob = cfg.get("wobble")  # omit for no sway
    plain = cfg.get("plain_cuts", False)  # true: straight cuts, no punch-in or flash
    zoom = cfg.get("zoom", 0)  # e.g. 0.06: each shot zooms in or out by 6%, alternating
    body, js = [], []

    # ---- footage inside a "camera" wrapper that sways
    vids = []
    for i, (s, e, clip, ms) in enumerate(cfg["shots"]):
        vids.append(f'        <video id="shot{i}" class="clip shot" src="assets/footage/clip{clip}.mp4" '
                    f'data-start="{s:.2f}" data-duration="{e - s:.2f}" data-media-start="{ms:.2f}" '
                    f'data-track-index="0" muted playsinline preload="auto"></video>')
        if not plain:  # every cut is on the beat: a short punch-in, then a slow push
            js.append(f'tl.fromTo("#shot{i}", {{scale: 1.14}}, {{scale: 1.0, duration: 0.26, ease: "power3.out"}}, {s:.2f});')
            js.append(f'tl.to("#shot{i}", {{scale: 1.04, duration: {max(e - s - 0.26, 0.1):.2f}, ease: "none"}}, {s + 0.26:.2f});')
        if zoom:  # gentle zoom, alternating in / out shot by shot (or every zoom_period seconds)
            step = cfg.get("zoom_period") or (e - s)
            t, k = s, i
            while t < e - 1e-6:
                d = min(step, e - t)
                lo, hi = (1.0, 1.0 + zoom) if k % 2 == 0 else (1.0 + zoom, 1.0)
                js.append(f'tl.fromTo("#shot{i}", {{scale: {lo:.3f}}}, {{scale: {hi:.3f}, duration: {d:.2f}, ease: "sine.inOut", immediateRender: {str(t == s).lower()}}}, {t:.2f});')
                t, k = t + d, k + 1
        if i and not plain:
            js.append(f'tl.fromTo("#flash", {{opacity: 0.4}}, {{opacity: 0, duration: 0.2, ease: "power2.out", immediateRender: false}}, {s:.2f});')
    cam_style = '' if wob else ' style="scale: 1"'
    body.append(f'      <div id="cam"{cam_style}>\n' + "\n".join(vids) + '\n      </div>')
    body.append('      <div id="shade"></div>\n      <div id="flash"></div>')

    # goyang: rotate + slide left/right, one swing per half beat
    half = wob["half"] if wob else 0
    js.append('tl.set("#cam", {rotation: 0, x: 0}, 0);')
    k, t = 0, 0.0
    while wob and t < dur - 1e-6:
        sgn = 1 if k % 2 == 0 else -1
        d = min(half, dur - t)
        js.append(f'tl.to("#cam", {{rotation: {sgn * wob["deg"]}, x: {sgn * wob["x"]}, duration: {d:.2f}, ease: "sine.inOut"}}, {t:.2f});')
        k, t = k + 1, t + half

    # ---- hook
    hook = cfg["hook"]
    size = f' style="font-size: {hook["size"]}px"' if hook.get("size") else ""  # default 84px
    body.append(f'      <div id="hook" class="clip txt" data-start="0" data-duration="{hook["end"]:.2f}" '
                f'data-track-index="1"><div class="big"{size}>{esc(hook["text"])}</div></div>')
    js.append('tl.fromTo("#hook .big", {scale: 0.55, opacity: 0}, {scale: 1, opacity: 1, duration: 0.32, ease: "back.out(2.4)"}, 0.05);')
    if hook["end"] < dur:
        js.append(f'tl.to("#hook .big", {{scale: 0.9, opacity: 0, duration: 0.12, ease: "power2.in"}}, {hook["end"] - 0.12:.2f});')

    # ---- points: pop in one by one, stay until points.end
    pts = cfg.get("points")
    if pts and pts["items"]:
        p0 = pts["items"][0]["t"]
        rows = "\n".join(f'        <div class="pt" id="pt{i}"><div class="pt-t">{esc(it["title"])}</div>'
                         f'<div class="pt-s">{esc(it["sub"])}</div></div>' for i, it in enumerate(pts["items"]))
        body.append(f'      <div id="points" class="clip txt" data-start="{p0:.2f}" data-duration="{pts["end"] - p0:.2f}" '
                    f'data-track-index="1">\n{rows}\n      </div>')
        for i, it in enumerate(pts["items"]):
            js.append(f'tl.fromTo("#pt{i}", {{scale: 0.5, opacity: 0, y: 30}}, {{scale: 1, opacity: 1, y: 0, duration: 0.3, ease: "back.out(2.6)", immediateRender: true}}, {it["t"]:.2f});')
        js.append(f'tl.to("#points", {{opacity: 0, scale: 0.94, duration: 0.12, ease: "power2.in"}}, {pts["end"] - 0.12:.2f});')

    # ---- CTA
    cta = cfg.get("cta")
    if cta:
        body.append(f'      <div id="cta" class="clip txt" data-start="{cta["start"]:.2f}" data-duration="{dur - cta["start"]:.2f}" '
                    f'data-track-index="1"><div class="big">{esc(cta["l1"])}</div><div class="sub">{esc(cta["l2"])}</div></div>')
        js.append(f'tl.fromTo("#cta .big", {{scale: 0.55, opacity: 0}}, {{scale: 1, opacity: 1, duration: 0.32, ease: "back.out(2.4)"}}, {cta["start"] + 0.02:.2f});')
        js.append(f'tl.fromTo("#cta .sub", {{y: 24, opacity: 0}}, {{y: 0, opacity: 1, duration: 0.28, ease: "power2.out"}}, {cta["start"] + 0.5:.2f});')

    page = (TEMPLATE.replace("__TITLE__", esc(cfg.get("title", project.name)))
            .replace("__DUR__", f"{dur:.2f}").replace("__EDGE__", EDGE)
            .replace("__BODY__", "\n".join(body))
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
    <link href="https://fonts.googleapis.com/css2?family=TikTok+Sans:wght@500;700;800&family=Noto+Color+Emoji&display=block" rel="stylesheet" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <style>
      :root { --ground: #0b0b0b; --ink: #ffffff;
        --font-tiktok: "TikTok Sans", "Noto Color Emoji", "Helvetica Neue", Arial, sans-serif; }
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: 1080px; height: 1920px; overflow: hidden; background: var(--ground); }
      #root { position: relative; width: 1080px; height: 1920px; overflow: hidden; font-family: var(--font-tiktok); color: var(--ink); }
      #cam { position: absolute; inset: 0; transform-origin: 50% 55%; scale: 1.1; }
      .shot { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; transform-origin: 50% 50%; }
      #shade { position: absolute; inset: 0; pointer-events: none; z-index: 5;
        background: linear-gradient(180deg, rgba(0,0,0,.30) 0%, rgba(0,0,0,.42) 30%, rgba(0,0,0,.46) 52%, rgba(0,0,0,.30) 75%, rgba(0,0,0,.45) 100%); }
      #flash { position: absolute; inset: 0; background: #fff; opacity: 0; z-index: 6; pointer-events: none; }
      .txt { position: absolute; left: 70px; right: 70px; top: 0; bottom: 0; z-index: 15; display: flex; flex-direction: column;
        align-items: center; justify-content: center; text-align: center; padding-bottom: 170px; text-shadow: __EDGE__; }
      .txt .big { font-weight: 700; font-size: 84px; line-height: 1.12; letter-spacing: -0.01em; text-wrap: balance; }
      .txt .sub { font-weight: 500; font-size: 50px; line-height: 1.2; margin-top: 20px; }
      #points { gap: 40px; }
      .pt-t { font-weight: 700; font-size: 66px; line-height: 1.1; letter-spacing: -0.01em; }
      .pt-s { font-weight: 500; font-size: 42px; line-height: 1.2; margin-top: 8px; color: rgba(255,255,255,.92); }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="__DUR__" data-width="1080" data-height="1920">
__BODY__
    </div>
    <script>
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
