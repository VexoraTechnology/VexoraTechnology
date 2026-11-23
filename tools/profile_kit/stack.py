"""stack.svg: three tilted elliptical orbits of Simple Icons around a glowing core, with two moons circling the
React icon while it travels its own orbit, plus a grouped chip grid whose borders glow one after another.

Every orbiting icon sits at its t=0 position through a base translate() and moves with a RELATIVE animateMotion
path, so a renderer that ignores SMIL still shows every icon on its orbit instead of piling them at the origin.
"""
from __future__ import annotations

import math
import random

from . import content as C
from .glyphs import line_icon
from .kit import (CYAN, DIM, PINK, TEXT, VIOLET, Doc, _ICONS, animate, animate_transform, ellipse_path, fmt, motion, readable)

FILE = "stack.svg"
W = 900
CX, CY = 450, 204            # orbit centre
CORE_R = 30
ORBIT_H = 396
BEAD_R, HOST_R, MOON_R, MOON_ORBIT = 19, 21, 10, 38


def bead(d: Doc, slug: str, r: float, icon: float) -> str:
    """Glass bead: faint brand-tinted halo, ink disc, hairline ring and the Simple Icons glyph."""
    tint = readable("#" + _ICONS[slug]["hex"])
    return (f'<circle r="{fmt(r + 8)}" fill="{tint}" fill-opacity=".09"/><circle r="{fmt(r)}" fill="#141526" stroke="#fff" stroke-opacity=".18"/>'
            f'{d.icon(slug, 0, 0, icon)}')


def depth(period: float, theta0: float, direction: int, n: int = 12) -> str:
    """Near side of the tilted orbit is larger and brighter; far side smaller and dimmer."""
    scale, opacity = [], []
    for k in range(n + 1):
        z = math.sin(math.radians(theta0) + direction * 2 * math.pi * k / n)
        scale.append((period * k / n, fmt(1 + .17 * z, 3)))
        opacity.append((period * k / n, fmt(.82 + .18 * z, 3)))
    return animate_transform("scale", scale, period) + animate("opacity", opacity, period)


def moons(d: Doc) -> str:
    """Two small moons on one circle around the host icon, half a turn apart (they never meet or touch the host)."""
    rho, out = MOON_ORBIT, []
    for k, slug in enumerate(C.MOONS):
        sign = 1 if k == 0 else -1
        path = f"M0 0a{rho} {rho} 0 1 1 {-2 * rho * sign} 0a{rho} {rho} 0 1 1 {2 * rho * sign} 0"
        out.append(f'<g class="moon" transform="translate({sign * rho} 0)">{motion(path, 6.5)}{bead(d, slug, MOON_R, 11)}</g>')
    return "".join(out)


def orbit_icons(d: Doc, idx: int, o: dict) -> str:
    """All icons of one orbit, evenly spaced; the host icon carries the moons."""
    n, out = len(o["icons"]), []
    direction = 1 if o["clockwise"] else -1
    for k, slug in enumerate(o["icons"]):
        theta0 = k * 360 / n + idx * 47
        (dx, dy), path = ellipse_path(o["a"], o["b"], o["tilt"], theta0, o["clockwise"])
        host = slug == C.HOST
        art = bead(d, slug, HOST_R if host else BEAD_R, 23 if host else 20) + (moons(d) if host else "")
        out.append(f'<g transform="translate({fmt(CX + dx)} {fmt(CY + dy)})">{motion(path, o["period"])}'
                   f'<g>{depth(o["period"], theta0, direction)}{art}</g></g>')
    return "".join(out)


def core(d: Doc) -> str:
    """Glowing core: breathing aurora, three staggered shock rings, glass sphere and a </> mark."""
    glow = d.id("coreglow")
    d.defs.append(f'<radialGradient id="{glow}"><stop offset="0" stop-color="{VIOLET}" stop-opacity=".55"/>'
                  f'<stop offset=".5" stop-color="{CYAN}" stop-opacity=".16"/><stop offset="1" stop-color="{CYAN}" stop-opacity="0"/></radialGradient>')
    sphere = d.id("sphere")
    d.defs.append(f'<radialGradient id="{sphere}" cx=".34" cy=".28" r=".95"><stop offset="0" stop-color="#e0f7ff"/>'
                  f'<stop offset=".3" stop-color="{CYAN}"/><stop offset=".68" stop-color="{VIOLET}"/><stop offset="1" stop-color="{PINK}"/></radialGradient>')
    breathe = animate("opacity", [(0, .85), (2.2, 1), (4.4, .85)], 4.4, ease="soft")
    rings = "".join(f'<circle r="{CORE_R}" fill="none" stroke="{c}" stroke-width="1.5" opacity="0">'
                    f'{animate("r", [(0, CORE_R), (3.6, 78)], 3.6, ease="out")}{animate("opacity", [(0, 0), (k * 1.2, 0), (k * 1.2 + .2, .5), (3.6, 0)], 3.6)}</circle>'
                    for k, c in enumerate((CYAN, VIOLET, PINK)))
    return (f'<g transform="translate({CX} {CY})"><circle r="96" fill="url(#{glow})">{breathe}</circle>{rings}'
            f'<circle class="core" r="{CORE_R}" fill="url(#{sphere})"/><ellipse cx="-9" cy="-12" rx="12" ry="7" fill="#fff" fill-opacity=".38" transform="rotate(-28 -9 -12)"/>'
            f'{line_icon("code", -13, -13, 26, "#0d0e16", 2.1)}</g>')


def readout(d: Doc) -> str:
    """Tiny mono counter (derived from content.py) in the corner: data-like text is where the mono face belongs."""
    items = [f"{len(C.ORBITS)} orbits", f"{sum(len(o['icons']) for o in C.ORBITS)} tools", f"{len(C.MOONS)} moons"]
    x, out = 30.0, []
    for item in items:
        out.append(d.t(item, "m4", x, ORBIT_H - 26, 11.5, fill=DIM))
        x += d.w_of("m4", item, 11.5) + 24
    return "".join(out)


def orbit_card(d: Doc) -> str:
    """Title, orbit rings (static hairlines), dust, icons and core."""
    ring_grad = d.aurora("ring", 120, 0, 780, 0)
    rings = "".join(f'<ellipse cx="{CX}" cy="{CY}" rx="{o["a"]}" ry="{o["b"]}" transform="rotate({o["tilt"]} {CX} {CY})" fill="none" '
                    f'stroke="{ring_grad}" stroke-opacity=".42" stroke-width="1.2"/>' for o in C.ORBITS)
    rng = random.Random(3)
    dust = "".join(f'<circle cx="{rng.uniform(20, W - 20):.0f}" cy="{rng.uniform(20, ORBIT_H - 20):.0f}" r="{rng.choice((.8, 1, 1.2))}" fill="#fff" opacity=".3">'
                   f'{animate("opacity", [(0, .15), (rng.uniform(1.5, 3.5), .6), (rng.uniform(4, 6), .15)], 6, ease="soft")}</circle>' for _ in range(26))
    title = (d.t("What I build with", "d7", 30, 46, 22, fill=TEXT)
             + d.t(f"Three orbits of tools, with {_ICONS[C.MOONS[0]]['title']} and {_ICONS[C.MOONS[1]]['title']} circling {_ICONS[C.HOST]['title']}.",
                   "d5", 30, 68, 13, fill=DIM))
    icons = "".join(orbit_icons(d, i, o) for i, o in reversed(list(enumerate(C.ORBITS))))
    return dust + rings + title + icons + core(d) + readout(d)


# ───────────────────────────── chip grid ─────────────────────────────

def chip_grid(d: Doc) -> tuple[str, int]:
    """Eight labelled groups in two rows of four; chip borders glow in sequence on a shared loop. Returns (markup, height)."""
    cols, gap, x0 = 4, 18, 28
    col_w = (W - 2 * x0 - (cols - 1) * gap) / cols
    palette = (CYAN, VIOLET, PINK)
    groups, placed, heights = list(C.CHIPS.items()), [], []
    for gi, (_, chips) in enumerate(groups):
        x, y = 0.0, 0.0
        for label, slug in chips:
            w = 14 + 14 + 8 + d.w_of("d5", label, 12) + 12
            if x and x + w > col_w:
                x, y = 0.0, y + 38
            placed.append(dict(gi=gi, x=x, y=y, w=w, label=label, slug=slug))
            x += w + 8
        heights.append(y + 30)
    rows = [range(r * cols, (r + 1) * cols) for r in range(len(groups) // cols)]
    row_h = [max(heights[i] for i in r) + 48 for r in rows]
    row_y = [20]
    for h in row_h[:-1]:
        row_y.append(row_y[-1] + h + 14)
    total = len(placed) * .3 + 1.6
    out = []
    for gi, (group, _) in enumerate(groups):
        gx, gy = x0 + (gi % cols) * (col_w + gap), row_y[gi // cols]
        out.append(f'<circle cx="{fmt(gx + 4)}" cy="{gy + 22}" r="4" fill="{palette[gi % 3]}"/>' + d.t(group, "d7", gx + 16, gy + 27, 15, fill=TEXT))
    for j, c in enumerate(placed):
        gx, gy = x0 + (c["gi"] % cols) * (col_w + gap), row_y[c["gi"] // cols]
        x, y, w, accent = gx + c["x"], gy + 48 + c["y"], c["w"], palette[c["gi"] % 3]
        s0 = j * .3
        pts = [(0, 0), (s0, 0), (s0 + .12, 1), (s0 + .3, 1), (s0 + .7, 0)]
        glow = animate("opacity", pts, total, ease="soft")
        halo = animate("opacity", [(a, b * .22) for a, b in pts], total, ease="soft")
        out.append(f'<rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(w)}" height="30" rx="9" fill="#fff" fill-opacity=".035" stroke="#fff" stroke-opacity=".13"/>'
                   f'<rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(w)}" height="30" rx="9" fill="none" stroke="{accent}" stroke-width="7" opacity="0">{halo}</rect>'
                   f'<rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(w)}" height="30" rx="9" fill="none" stroke="{accent}" stroke-width="1.6" opacity="0">{glow}</rect>'
                   f'{d.icon(c["slug"], x + 21, y + 15, 14)}{d.t(c["label"], "d5", x + 36, y + 19.5, 12, fill=TEXT)}')
    return "".join(out), round(row_y[-1] + row_h[-1] + 22)


def build(gh: dict) -> str:
    d = Doc("st", W, 10, "Tech stack: three orbits of tools and a grouped chip grid",
            "Brand icons ride three tilted orbits around a glowing </> core; TypeScript and Electron orbit the React icon. "
            "Below, every skill sits in a chip grouped as Languages, Frontend, Mobile and desktop, Backend, Data, AI and data science, "
            "Motion and 3D, and Tools; their borders glow one after another.")
    chips, chips_h = chip_grid(d)
    d.h = ORBIT_H + 16 + chips_h
    d.body.append(d.card(0, 0, W, ORBIT_H, orbit_card(d), auras=(("v", .5, .5, .9, 21), ("c", .06, .1, .6, 17), ("p", .96, .96, .6, 25))))
    d.body.append(d.card(0, ORBIT_H + 16, W, chips_h, chips, auras=(("c", .05, .0, .6, 19), ("p", .98, 1.0, .5, 23))))
    return d.svg()
