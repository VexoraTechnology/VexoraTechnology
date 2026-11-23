"""Renders SVGs in headless Chromium at exact timestamps and builds contact sheets.

Why: GitHub strips scripts, so the only way to see an SVG's timeline is to seek it. SMIL is seeked with
setCurrentTime() and CSS animations through the Web Animations API. `--static` removes every animation first,
which is exactly what a renderer that ignores animation would show (the "finished card").

Usage: python tools/verify.py assets/hero.svg --times 0 0.5 1 2 3 --out /tmp/renders [--static] [--scale 1]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

SEEK_JS = """(t) => {
  const s = document.documentElement;
  if (s.pauseAnimations) { s.pauseAnimations(); s.setCurrentTime(t); }
  for (const a of document.getAnimations()) { a.pause(); a.currentTime = t * 1000; }
}"""


def strip_animation(svg: str) -> str:
    """Removes SMIL elements, @keyframes and animation declarations."""
    svg = re.sub(r"<(animate|animateTransform|animateMotion|set)\b[^>]*?(/>|>.*?</\1>)", "", svg, flags=re.S)
    svg = re.sub(r"@keyframes [^{]+\{(?:[^{}]*\{[^{}]*\})*[^{}]*\}", "", svg)
    return re.sub(r"animation:[^;}]+;?", "", svg)


def render(svg_path: Path, times, out_dir: Path, scale: float = 1.0, static: bool = False, tag: str = ""):
    """Returns (list of PNG paths, list of blocked non-local requests)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    src = svg_path
    if static:
        src = out_dir / f"{svg_path.stem}.static.svg"
        src.write_text(strip_animation(svg_path.read_text()))
    head = svg_path.read_text()[:400]
    w, h = (int(re.search(rf'{k}="(\d+)"', head).group(1)) for k in ("width", "height"))
    blocked, shots = [], []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=scale)

        def guard(route):
            if route.request.url.startswith(("file:", "data:")):
                route.continue_()
            else:
                blocked.append(route.request.url)
                route.abort()

        page.route("**/*", guard)
        page.goto(src.resolve().as_uri())
        page.evaluate("document.fonts ? document.fonts.ready.then(() => 1) : 1")
        for t in times:
            page.evaluate(SEEK_JS, t)
            page.wait_for_timeout(60)
            path = out_dir / f"{svg_path.stem}{tag}_{'static' if static else f't{t:05.2f}'}.png"
            page.screenshot(path=str(path))
            shots.append(path)
            if static:
                break
        browser.close()
    return shots, blocked


def sheet(paths, labels, cols=2, out: Path | None = None, width=900):
    """Tiles screenshots with captions into one image for quick review."""
    ims = [Image.open(p).convert("RGB") for p in paths]
    s = width / ims[0].width
    tiles = [im.resize((width, round(im.height * s)), Image.LANCZOS) for im in ims]
    rows = [tiles[i:i + cols] for i in range(0, len(tiles), cols)]
    gap, cap = 8, 20
    H = sum(max(t.height for t in r) + cap + gap for r in rows)
    canvas = Image.new("RGB", (cols * width + (cols + 1) * gap, H + gap), (30, 31, 40))
    d, y = ImageDraw.Draw(canvas), gap
    for r, lab_row in zip(rows, [labels[i:i + cols] for i in range(0, len(labels), cols)]):
        for i, (t, lab) in enumerate(zip(r, lab_row)):
            x = gap + i * (width + gap)
            d.text((x, y + 4), lab, fill=(190, 195, 215))
            canvas.paste(t, (x, y + cap))
        y += max(t.height for t in r) + cap + gap
    if out:
        canvas.save(out)
    return canvas


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("svg", type=Path)
    ap.add_argument("--times", type=float, nargs="*", default=[0, 1, 2, 3])
    ap.add_argument("--out", type=Path, default=Path("/tmp/renders"))
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--static", action="store_true")
    ap.add_argument("--cols", type=int, default=2)
    a = ap.parse_args(argv)
    shots, blocked = render(a.svg, a.times, a.out, a.scale, a.static)
    if blocked:
        print("BLOCKED NETWORK REQUESTS:", blocked)
        return 1
    labels = ["static (animation stripped)"] if a.static else [f"t = {t:g}s" for t in a.times]
    sheet(shots, labels, a.cols, a.out / f"{a.svg.stem}_sheet.png", width=int(a.scale * 900) if a.cols == 1 else 640)
    print("rendered", len(shots), "frames ->", a.out / f"{a.svg.stem}_sheet.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
