"""The Vexora mark redrawn as vector from the office-wall logo: silver left arm, blue right arm, circuit trace."""
from __future__ import annotations

from .kit import Doc, fmt

BOX_W, BOX_H = 87.0, 72.0


def _gradient(d: Doc, name: str, x1, y1, x2, y2, stops) -> str:
    """Defines a gradient once per document and returns its url(#id)."""
    if d.id(name) not in "".join(d.defs):
        d.ugrad(name, x1, y1, x2, y2, stops)
    return d.ref(name)


def vexora_mark(d: Doc, x: float, y: float, width: float) -> str:
    """The mark scaled to `width` (aspect kept) with its top-left corner at (x, y)."""
    silver = _gradient(d, "vx-silver", 0, 12, 0, 54, [("0", "#d6dae8"), ("1", "#7a8096")])
    blue = _gradient(d, "vx-blue", 58, 10, 36, 64, [("0", "#5b97ff"), ("1", "#1a3fd8")])
    trace = "#d4ecff"
    return (f'<g transform="translate({fmt(x)} {fmt(y)}) scale({fmt(width / BOX_W, 4)})">'
            f'<path d="M7.2 15 25.2 12.5 40.5 38 30 54z" fill="{silver}" stroke="{silver}" stroke-width="1.2" stroke-linejoin="round"/>'
            f'<path d="M58.5 10 80.5 8.2 48 61.5Q43 66.5 36.5 64Q31 61.5 30.8 56z" fill="{blue}"/>'
            f'<path d="M58.5 10 80.5 8.2" stroke="#a9c8ff" stroke-width=".8" stroke-linecap="round" fill="none"/>'
            f'<circle cx="62.2" cy="19.8" r="2.8" fill="none" stroke="{trace}" stroke-width=".9"/>'
            f'<path d="M61.2 22.2 47 43 41 47 39.6 57" fill="none" stroke="{trace}" stroke-width=".9" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<rect x="38.2" y="57" width="2.8" height="2.8" fill="{trace}"/><rect x="42.6" y="52.6" width="1.6" height="6.2" fill="{trace}"/></g>')
