"""Builds every SVG into ../assets.

Usage:  python tools/build.py [--only hero about stack dashboard connect contribute] [--video clip.mp4] [--hero-kb 900]
Why a build script: base64 fonts/images and animation timelines are generated, never hand-edited.
"""
from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from profile_kit import content as C, media  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets"
TARGETS = ("hero", "about", "stack", "dashboard", "connect", "contribute")


def write(name: str, svg: str) -> None:
    OUT.mkdir(exist_ok=True)
    path = OUT / name
    path.write_text(svg, encoding="utf-8")
    print(f"  {name:<18} {len(svg.encode()) / 1024:7.1f} KB")


def build_hero(video: Path | None, budget_kb: int) -> None:
    from profile_kit import hero
    scale = 1.5
    w, h = round(hero.SW * scale), round(hero.SH * scale)
    if video:
        frames, fps = media.video_frames(video, w, h)
        label = video.name
    else:
        frames, fps = media.idle_frames(w, h)
        label = "jay_idle.mov"
    jpegs, info = media.encode_jpegs(frames, (budget_kb or max(640, 14 * len(frames))) * 1024)
    print(f"  hero frames: {len(jpegs)} @ {fps:g} fps, {info['size'][0]}x{info['size'][1]}, q{info['quality']}, {info['total'] / 1024:.0f} KB")
    write("hero.svg", hero.build(jpegs, dict(name=label, frames=len(jpegs), fps=fps), C.github()))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", choices=TARGETS, default=list(TARGETS))
    ap.add_argument("--video", type=Path, help="2-second clip; every frame is embedded")
    ap.add_argument("--refresh", action="store_true", help="re-pull stars, commits and repos from the GitHub API first (use GITHUB_TOKEN)")
    ap.add_argument("--hero-kb", type=int, default=0, help="JPEG budget for the hero frames (default: 14 KB per frame, at least 640)")
    a = ap.parse_args(argv)
    if a.refresh:
        from profile_kit import github
        snap = github.refresh()
        print(f"  refreshed: {len(snap['repos'])} repos")
    for target in a.only:
        if target == "hero":
            build_hero(a.video, a.hero_kb)
        else:
            module = importlib.import_module(f"profile_kit.{target}")
            write(module.FILE, module.build(C.github()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
