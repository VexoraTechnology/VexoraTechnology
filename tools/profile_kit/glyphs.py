"""Hand-drawn 16x16 line icons used across the SVGs (stroked, so they can draw themselves in)."""
from __future__ import annotations

import json

from .kit import ASSETS, CYAN, animate, fmt

LENGTHS = json.loads((ASSETS / "glyph_lengths.json").read_text())   # measured once in a browser; see prepare_assets.py --measure

LINES = {
    "pin": ["M8 14.5s4.7-4 4.7-7.8a4.7 4.7 0 0 0-9.4 0c0 3.8 4.7 7.8 4.7 7.8z", "M8 8.6a1.9 1.9 0 1 0 0-3.8 1.9 1.9 0 0 0 0 3.8z"],
    "briefcase": ["M2 5.2h12v8.3H2z", "M5.6 5.2V3.4h4.8v1.8", "M2 9h12"],
    "repo": ["M3.2 2.5h9.6v10.3H4.6a1.4 1.4 0 0 0-1.4 1.4z", "M3.2 14.2a1.4 1.4 0 0 0 1.4 1.3h8.2"],
    "star": ["M8 1.8l1.9 4 4.3.5-3.2 3 .9 4.3L8 11.5l-3.9 2.1.9-4.3-3.2-3 4.3-.5z"],
    "commit": ["M1.5 8h4.2", "M10.3 8h4.2", "M8 10.7a2.7 2.7 0 1 0 0-5.4 2.7 2.7 0 0 0 0 5.4z"],
    "layout": ["M2 3h12v10H2z", "M2 6.4h12", "M6 6.4V13"],
    "server": ["M2.5 2.5h11v4.2h-11z", "M2.5 9.3h11v4.2h-11z", "M5 4.6h.1", "M5 11.4h.1"],
    "sparkle": ["M8 1.5c.4 3.2 1.6 4.7 6.5 6.5-4.9 1.8-6.1 3.3-6.5 6.5-.4-3.2-1.6-4.7-6.5-6.5C6.4 6.2 7.6 4.7 8 1.5z"],
    "bulb": ["M8 1.8a4.4 4.4 0 0 0-2.6 8c.5.4.8 1 .8 1.6v.4h3.6v-.4c0-.6.3-1.2.8-1.6A4.4 4.4 0 0 0 8 1.8z", "M6.4 14h3.2"],
    "code": ["M5.5 4.5L2 8l3.5 3.5", "M10.5 4.5L14 8l-3.5 3.5", "M9 3l-2 10"],
    "rocket": ["M9.5 2.2c2.2.2 4 2 4.3 4.3-1 2-2.7 3.4-4.5 4.2L5.5 7.1c.8-1.8 2.2-3.5 4-4.9z", "M5.6 8.8l-2.1.5.6-2.6 1.8-.5",
               "M7.2 10.4l-.5 2.1 2.6-.6.5-1.8", "M10.6 5.9h.1"],
    "book": ["M2.5 3.2c2-.5 4.2-.3 5.5 1v9c-1.3-1.3-3.5-1.5-5.5-1z", "M13.5 3.2c-2-.5-4.2-.3-5.5 1v9c1.3-1.3 3.5-1.5 5.5-1z"],
    "lock": ["M4 7.2h8v6.3H4z", "M5.6 7.2V5.4a2.4 2.4 0 0 1 4.8 0v1.8"],
    "arrow": ["M2 8h11", "M9 4l4 4-4 4"],
    "mail": ["M2 3.5h12v9H2z", "M2.4 4l5.6 4.6L13.6 4"],
}


def line_icon(name: str, x: float, y: float, size: float = 16, color: str = CYAN, width: float = 1.5,
              draw_at: float | None = None, draw_dur: float = 0.7) -> str:
    """Stroked icon placed at (x, y); optionally draws itself in (delay encoded in keyTimes, starts at 0s).

    The dash length is the path's measured length, so no engine has to support pathLength.
    """
    paths = []
    for i, d in enumerate(LINES[name]):
        length = LENGTHS[f"{name}-{i}"] + 0.5
        anim = ""
        if draw_at is not None:
            anim = animate("stroke-dashoffset", [(0, length), (draw_at, length), (draw_at + draw_dur, 0)], draw_at + draw_dur,
                           ease="out", repeat=False, freeze=True)
        paths.append(f'<path d="{d}" stroke-dasharray="{fmt(length)} {fmt(length)}" stroke-dashoffset="0">{anim}</path>')
    return (f'<g transform="translate({fmt(x)} {fmt(y)}) scale({fmt(size / 16, 4)})" fill="none" stroke="{color}" '
            f'stroke-width="{fmt(width * 16 / size)}" stroke-linecap="round" stroke-linejoin="round">{"".join(paths)}</g>')
