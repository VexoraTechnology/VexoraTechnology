"""about-life.svg: two cards side by side.

Left: a fake browser (URL bar with blinking caret, isometric full-stack illustration) plus three capability rows.
Right: a hobby carousel (16 s loop, 4 s per slide, Instagram-style segment bars, caption per slide) and three daily rings.
"""
from __future__ import annotations

import math
import random

from . import content as C
from .brand import vexora_mark
from .glyphs import line_icon
from .kit import (CYAN, DIM, PINK, TEXT, VIOLET, Doc, animate, animate_transform, fmt, motion)

FILE = "about-life.svg"
W, H = 900, 420
SLIDE_T = 4.0


def wrap(d: Doc, face: str, text: str, size: float, maxw: float) -> list[str]:
    """Greedy word wrap using real glyph metrics."""
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if cur and d.w_of(face, trial, size) > maxw:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    return lines + [cur]


def bob(amp: float, period: float, phase: float, n: int = 8):
    """Sampled vertical float used for the slabs and chips (phase in 0..1 of the period)."""
    return [(period * k / n, f"0 {fmt(-amp * math.sin(2 * math.pi * (k / n + phase)))}") for k in range(n + 1)]


# ───────────────────────────── left card ─────────────────────────────

def slab(cx: float, cy: float, colour: str) -> str:
    """One isometric slab: three faces plus an inset 'screen' on top."""
    hw, hh, t = 56, 26, 9
    pts = lambda *p: " ".join(f"{fmt(x)},{fmt(y)}" for x, y in p)
    top = pts((cx, cy - hh), (cx + hw, cy), (cx, cy + hh), (cx - hw, cy))
    inset = pts((cx, cy - hh * .5), (cx + hw * .5, cy), (cx, cy + hh * .5), (cx - hw * .5, cy))
    left = pts((cx - hw, cy), (cx, cy + hh), (cx, cy + hh + t), (cx - hw, cy + t))
    right = pts((cx + hw, cy), (cx, cy + hh), (cx, cy + hh + t), (cx + hw, cy + t))
    return (f'<polygon points="{left}" fill="{colour}" fill-opacity=".45"/><polygon points="{right}" fill="{colour}" fill-opacity=".26"/>'
            f'<polygon points="{top}" fill="{colour}" fill-opacity=".82"/><polygon points="{inset}" fill="#fff" fill-opacity=".26"/>'
            f'<polygon points="{top}" fill="none" stroke="#fff" stroke-opacity=".4" stroke-width=".8" stroke-linejoin="round"/>')


def browser_page(d: Doc) -> str:
    """The page being 'built' inside the window: nav, shimmering skeleton copy, buttons and a full-stack iso stack."""
    bars = ((20, 52, 170, 11, 5.5), (20, 70, 124, 11, 5.5), (20, 94, 176, 5, 2.5), (20, 105, 148, 5, 2.5))
    skel = '#fff" fill-opacity=".2'
    clip = d.id("skelclip")
    d.defs.append(f'<clipPath id="{clip}">' + "".join(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}"/>' for x, y, w, h, r in bars) + '</clipPath>')
    shine = d.ugrad("shine", 0, 0, 70, 0, [("0", "#fff", 0), (".5", "#fff", .55), ("1", "#fff", 0)])
    shimmer = (f'<g clip-path="url(#{clip})"><rect x="-70" y="44" width="70" height="76" fill="{shine}" transform="translate(0 0)">'
               f'{animate_transform("translate", [(0, "0 0"), (2.6, "300 0")], 2.6)}</rect></g>')
    cx = 262
    slabs = [(52, VIOLET, "React UI"), (84, CYAN, "Node API"), (116, PINK, "Firebase")]
    stack = ""
    for k, (cy, colour, tag) in enumerate(slabs):
        stack += (f'<g>{animate_transform("translate", bob(2.2, 4.4, k * .22), 4.4, ease="soft")}{slab(cx, cy, colour)}</g>'
                  f'{d.t(tag, "d5", cx + 62, cy + 5, 11.5, fill=colour)}')
    packets = ""
    for k, (path, dur) in enumerate(((f"M{cx} 38V140", 2.4), (f"M{cx} 140V38", 3.1))):
        fade = animate("opacity", [(0, 0), (dur * .15, 1), (dur * .85, 1), (dur, 0)], dur)
        packets += f'<circle r="3" fill="#fff" opacity="0">{motion(path, dur)}{fade}</circle>'
    chip = (f'<g>{animate_transform("translate", bob(2.5, 3.6, .3), 3.6, ease="soft")}'
            f'<rect x="322" y="5" width="66" height="20" rx="10" fill="{CYAN}" fill-opacity=".14" stroke="{CYAN}" stroke-opacity=".5"/>'
            f'{d.t("200 OK", "m7", 355, 18.6, 10.5, fill=CYAN, anchor="middle")}</g>')
    mark = vexora_mark(d, 14, 8, 26)
    nav = "".join(f'<rect x="{x}" y="19" width="{w}" height="4" rx="2" fill="#fff" fill-opacity=".2"/>' for x, w in ((50, 30), (90, 38), (138, 30)))
    copy = ("".join(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="#fff" fill-opacity=".2"/>' for x, y, w, h, r in bars) + shimmer +
            f'<rect x="20" y="126" width="74" height="22" rx="11" fill="{d.aurora("btn", 20, 0, 94, 0)}"/>'
            f'<rect x="102.5" y="126.5" width="66" height="21" rx="10.5" fill="none" stroke="#fff" stroke-opacity=".3"/>')
    return mark + nav + copy + stack + packets + chip


def browser(d: Doc) -> str:
    """Window chrome: traffic lights, URL bar with typed path and a blinking caret, clipped page content."""
    url = "localhost:3000/jaykishan"
    size = 11
    uw = d.w_of("m4", url, size)
    clip = d.id("win")
    d.defs.append(f'<clipPath id="{clip}"><rect width="400" height="196" rx="12"/></clipPath>')
    caret = (f'<rect x="{fmt(86 + uw + 2)}" y="8.5" width="1.6" height="11" fill="{CYAN}">'
             f'{animate("opacity", [(0, 1), (.53, 0)], 1.06, discrete=True)}</rect>')
    dots = "".join(f'<circle cx="{x}" cy="16" r="4.5" fill="{c}"/>' for x, c in ((18, PINK), (32, VIOLET), (46, CYAN)))
    chrome = (f'<rect width="400" height="32" fill="#fff" fill-opacity=".045"/>{dots}'
              f'<rect x="66" y="6" width="314" height="20" rx="10" fill="#fff" fill-opacity=".07"/>'
              f'{line_icon("lock", 70, 10.5, 11, DIM, 1.4)}{d.t(url, "m4", 86, 19.6, size, fill=TEXT)}')
    page = f'<g transform="translate(0 32)"><rect width="400" height="164" fill="#0a0b13"/>{browser_page(d)}</g>'
    return (f'<g transform="translate(20 20)"><g clip-path="url(#{clip})">{page}{chrome}{caret}</g>'
            f'<rect x=".5" y=".5" width="399" height="195" rx="11.5" fill="none" stroke="#fff" stroke-opacity=".14"/></g>')


def capabilities(d: Doc) -> str:
    """Three capability rows with icon tiles; they slide in from the left (fill-mode both)."""
    out = []
    colours = (CYAN, VIOLET, PINK)
    for k, (icon, title, sub) in enumerate(C.CAPABILITIES):
        y = 238 + k * 56
        tile = (f'<rect x="20" y="{y}" width="44" height="44" rx="12" fill="#fff" fill-opacity=".04" stroke="{d.ref("hair")}"/>'
                f'{line_icon(icon, 31, y + 11, 22, colours[k], 1.6)}')
        text = d.t(title, "d7", 80, y + 18, 16, fill=TEXT) + d.t(sub, "d5", 80, y + 37, 12.5, fill=DIM)
        out.append(f'<g class="{d.rise(f"cap{k}", dx=-16, dy=0, delay=.1 + k * .1, dur=.5)}">{tile}{text}</g>')
    return "".join(out)


# ───────────────────────────── slide illustrations (400 x 182) ─────────────────────────────

def twinkle(x: float, y: float, s: float, period: float, phase: float, colour: str) -> str:
    """Four-point sparkle whose opacity breathes; `phase` offsets it inside the loop."""
    star = f"M0 {-s}Q0 0 {s} 0Q0 0 0 {s}Q0 0 {-s} 0Q0 0 0 {-s}z"
    pts = [(period * k / 6, fmt(.55 + .4 * math.sin(2 * math.pi * (k / 6 + phase)), 3)) for k in range(7)]
    return f'<path d="{star}" transform="translate({fmt(x)} {fmt(y)})" fill="{colour}" opacity=".9">{animate("opacity", pts, period)}</path>'


def ill_spark(d: Doc) -> str:
    """Idea -> build -> ship: three nodes joined by flowing connectors with travelling packets."""
    nodes = [(70, "bulb", "idea", VIOLET), (200, "code", "build", CYAN), (330, "rocket", "ship", PINK)]
    out = []
    for (x1, _, _, c1), (x2, _, _, c2) in zip(nodes, nodes[1:]):
        path = f"M{x1 + 40} 84H{x2 - 40}"
        flow = animate("stroke-dashoffset", [(0, 0), (1.2, -20)], 1.2)
        out.append(f'<path d="{path}" stroke="#fff" stroke-opacity=".28" stroke-dasharray="4 6" fill="none" stroke-linecap="round">{flow}</path>')
        out.append(f'<circle r="3.2" fill="{c2}" opacity="0">{motion(path, 1.8)}{animate("opacity", [(0, 0), (.3, 1), (1.5, 1), (1.8, 0)], 1.8)}</circle>')
    for x, icon, label, colour in nodes:
        out.append(f'<circle cx="{x}" cy="84" r="34" fill="{colour}" fill-opacity=".1" stroke="{colour}" stroke-opacity=".6" stroke-width="1.5"/>'
                   f'{line_icon(icon, x - 14, 70, 28, colour, 1.6)}{d.t(label, "d5", x, 140, 12, fill=DIM, anchor="middle")}')
    for x, y, s, p, ph, c in ((30, 30, 5, 3.0, 0, CYAN), (140, 26, 4, 2.4, .25, PINK), (268, 28, 5, 3.4, .5, VIOLET), (372, 40, 4, 2.8, .75, CYAN), (180, 156, 4, 3.2, .25, VIOLET)):
        out.append(twinkle(x, y, s, p, ph, c))
    return "".join(out)


def ill_voice(d: Doc) -> str:
    """Live waveform (listening) beside a candlestick chart with a self-drawing moving average."""
    base = [18, 34, 58, 44, 76, 52, 88, 46, 66, 36, 22]
    bars = []
    for k, h in enumerate(base):
        pts_h = [(1.6 * j / 6, fmt(h * (.45 + .55 * abs(math.sin(math.pi * (j / 6 + k * .13)))))) for j in range(7)]
        pts_y = [(t, fmt(91 - float(v) / 2)) for t, v in pts_h]
        bars.append(f'<rect x="{22 + k * 14}" y="{91 - h / 2}" width="8" height="{h}" rx="4" fill="{VIOLET if k % 2 else CYAN}" fill-opacity=".85">'
                    f'{animate("height", pts_h, 1.6)}{animate("y", pts_y, 1.6)}</rect>')
    rng, price, candles, line = random.Random(5), 84.0, [], []
    for k in range(9):
        o, c = price, min(max(price + rng.uniform(-30, 34), 40), 138)
        hi, lo = max(o, c) + rng.uniform(6, 16), min(o, c) - rng.uniform(6, 16)
        x, col = 222 + k * 20, CYAN if c >= o else PINK
        candles.append(f'<line x1="{x}" y1="{176 - hi:.1f}" x2="{x}" y2="{176 - lo:.1f}" stroke="{col}" stroke-width="1.6" stroke-linecap="round"/>'
                       f'<rect x="{x - 6}" y="{176 - max(o, c):.1f}" width="12" height="{max(abs(c - o), 3):.1f}" rx="2.5" fill="{col}"/>')
        line.append(f"{x},{176 - (o + c) / 2:.1f}")
        price = c
    pts = [tuple(map(float, p.split(","))) for p in line]
    length = sum(math.dist(a, b) for a, b in zip(pts, pts[1:])) + 1
    draw = animate("stroke-dashoffset", [(0, length), (1.8, 0), (5, 0)], 5, ease="inout")
    ma = (f'<polyline points="{" ".join(line)}" fill="none" stroke="{d.aurora("ma", 222, 0, 382, 0)}" stroke-width="2.2" '
          f'stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="{fmt(length)} {fmt(length)}" stroke-dashoffset="0">{draw}</polyline>')
    return "".join(bars) + "".join(candles) + ma + d.t("listening", "d5", 22, 168, 12, fill=DIM) + d.t("paper trades only", "d5", 222, 168, 12, fill=DIM)


def ill_phone(d: Doc) -> str:
    """Phone with a timetable and a study lock, next to a growing daily-expense bar chart."""
    blocks = [(10, 22, 66, CYAN), (36, 30, 50, VIOLET), (70, 18, 62, PINK), (92, 26, 44, CYAN)]
    scr = "".join(f'<rect x="{78 + dx}" y="{30 + y}" width="{w}" height="{h * .8:.0f}" rx="5" fill="{c}" fill-opacity=".75"/>'
                  for dx, (y, h, w, c) in zip((0, 8, 0, 14), blocks))
    phone = (f'<rect x="64" y="10" width="92" height="162" rx="16" fill="#0a0b13" stroke="#fff" stroke-opacity=".3" stroke-width="1.5"/>'
             f'<rect x="100" y="16" width="20" height="4" rx="2" fill="#fff" fill-opacity=".25"/>{scr}'
             f'<rect x="80" y="138" width="60" height="22" rx="11" fill="{PINK}" fill-opacity=".18" stroke="{PINK}" stroke-opacity=".7"/>'
             f'{line_icon("lock", 100, 142, 14, PINK, 1.5)}{d.t("focus", "d5", 120, 153.5, 11, fill=TEXT)}')
    heights = [38, 62, 28, 78, 52, 94, 44]
    bars = []
    for k, h in enumerate(heights):
        grow = animate("height", [(0, 0), (.3 + k * .12, 0), (1.2 + k * .12, h), (5.2, h), (5.8, 0)], 5.8, ease="out")
        move = animate("y", [(0, 150), (.3 + k * .12, 150), (1.2 + k * .12, 150 - h), (5.2, 150 - h), (5.8, 150)], 5.8, ease="out")
        bars.append(f'<rect x="{196 + k * 26}" y="{150 - h}" width="16" height="{h}" rx="5" fill="{CYAN if k != 5 else PINK}" fill-opacity=".85">{grow}{move}</rect>')
    return phone + "".join(bars) + d.t("daily expenses", "d5", 196, 30, 12, fill=DIM) + f'<path d="M190 151H386" stroke="#fff" stroke-opacity=".18"/>'


def ill_forest(d: Doc) -> str:
    """Two noisy classes, a decision boundary and the accuracy figure."""
    rng, pts = random.Random(7), []
    for cx, cy, col in ((88, 62, CYAN), (142, 112, PINK)):
        for _ in range(20):
            pts.append((rng.gauss(cx, 19), rng.gauss(cy, 19), col))
    dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.6" fill="{c}" opacity=".85">'
                   f'{animate("opacity", [(0, .85), (i * .08, .85), (i * .08 + .3, .25), (i * .08 + .6, .85)], 5)}</circle>'
                   for i, (x, y, c) in enumerate(pts))
    boundary = f'<path d="M50 150L180 22" stroke="#fff" stroke-opacity=".55" stroke-dasharray="5 5" fill="none" stroke-linecap="round"/>'
    big = d.t("95.83%", "d8", 232, 96, 44, fill=d.aurora("acc", 232, 0, 380, 0))
    return (f'<rect x="12" y="12" width="196" height="158" rx="12" fill="#fff" fill-opacity=".03"/>{dots}{boundary}{big}'
            + d.t("held-out accuracy", "d5", 234, 120, 12, fill=DIM) + d.t("on 240 unseen rows", "d5", 234, 138, 12, fill=DIM))


ILLUSTRATIONS = {"spark": ill_spark, "voice": ill_voice, "phone": ill_phone, "forest": ill_forest}


# ───────────────────────────── right card ─────────────────────────────

def carousel(d: Doc) -> str:
    """Segment bars + sliding/crossfading slides; slide 0 is the finished (static) state."""
    n = len(C.SLIDES)
    total = n * SLIDE_T
    seg_w = (400 - 6 * (n - 1)) / n
    bars = []
    for i in range(n):
        x = 20 + i * (seg_w + 6)
        grow = animate("width", [(i * SLIDE_T, 0), ((i + 1) * SLIDE_T, seg_w)], total)
        tab_pts = [(0, 1), (SLIDE_T, .45)] if i == 0 else [(0, .45), (i * SLIDE_T, 1), ((i + 1) * SLIDE_T, .45)]
        label = d.t(C.SLIDES[i]["tab"], "d5", x, 41, 11.5, fill=TEXT, opacity=1 if i == 0 else .45).replace(
            "</text>", f'{animate("opacity", tab_pts, total, discrete=True)}</text>')
        bars.append(f'<rect x="{fmt(x)}" y="18" width="{fmt(seg_w)}" height="3" rx="1.5" fill="#fff" fill-opacity=".16"/>'
                    f'<rect x="{fmt(x)}" y="18" width="{fmt(seg_w if i == 0 else 0)}" height="3" rx="1.5" fill="{d.aurora(f"seg{i}", x, 0, x + seg_w, 0)}">{grow}</rect>{label}')
    slides = []
    fade = .3                                                     # illustrations crossfade quickly
    for i, s in enumerate(C.SLIDES):
        t0, t1 = i * SLIDE_T, (i + 1) * SLIDE_T
        if i == 0:
            op = [(0, 1), (t1 - fade, 1), (t1, 0), (total - fade, 0), (total, 1)]
            mv = [(0, "0 0"), (t1 - fade, "0 0"), (t1, "-20 0"), (total - fade, "20 0"), (total, "0 0")]
            cap_op = [(0, 1), (t1 - .45, 1), (t1 - .15, 0), (total - .15, 0), (total, 1)]
        else:
            op = [(0, 0), (t0 - fade, 0), (t0, 1), (t1 - fade, 1), (t1, 0)]
            mv = [(0, "20 0"), (t0 - fade, "20 0"), (t0, "0 0"), (t1 - fade, "0 0"), (t1, "-20 0")]
            cap_op = [(0, 0), (t0 - .15, 0), (t0 + .15, 1), (t1 - .45, 1), (t1 - .15, 0)]
        art = ILLUSTRATIONS[s["kind"]](d)
        cap = d.t(s["title"], "d7", 20, 254, 19, fill=TEXT)
        for j, line in enumerate(wrap(d, "d5", s["sub"], 12.5, 400)):
            cap += d.t(line, "d5", 20, 276 + j * 17, 12.5, fill=DIM)
        k = 170 / 182
        panel = (f'<rect x="20" y="52" width="400" height="170" rx="14" fill="#fff" fill-opacity=".025" stroke="#fff" stroke-opacity=".08"/>'
                 f'<g transform="translate({fmt(20 + 400 * (1 - k) / 2)} 52) scale({fmt(k, 4)})">{art}</g>')
        # art and caption have separate timelines: the caption fades out and the next one fades in (no overlapping text)
        slides.append(f'<g opacity="{1 if i == 0 else 0}">{animate("opacity", op, total, ease="soft")}'
                      f'<g>{animate_transform("translate", mv, total, ease="soft")}{panel}</g></g>'
                      f'<g opacity="{1 if i == 0 else 0}">{animate("opacity", cap_op, total, ease="soft")}{cap}</g>')
    return "".join(bars) + "".join(slides)


def rings(d: Doc) -> str:
    """Three daily rings on an 8 s loop: full at 0 s (the finished state), drain near the end, then refill in sequence."""
    dur, out = 8.0, [f'<path d="M20 316H420" stroke="#fff" stroke-opacity=".08"/>']
    for k, (icon, label, colour, pct) in enumerate(C.RINGS):
        cx, cy, r = 80 + k * 140, 350, 24
        circ = 2 * math.pi * r
        full, empty = f"{fmt(circ * pct / 100)} {fmt(circ)}", f"0 {fmt(circ)}"
        j = .1 * k
        fill = animate("stroke-dasharray", [(0, full), (5.6 + j, full), (6.1 + j, empty), (6.4 + j, empty), (7.6 + j, full)], dur, ease="out")
        out.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#fff" stroke-opacity=".09" stroke-width="6"/>'
                   f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{colour}" stroke-width="6" stroke-linecap="round" '
                   f'stroke-dasharray="{full}" transform="rotate(-90 {cx} {cy})">{fill}</circle>'
                   f'{line_icon(icon, cx - 8, cy - 8, 16, colour, 1.5)}{d.t(label, "d5", cx, cy + 46, 12.5, fill=DIM, anchor="middle")}')
    return "".join(out)


def build(gh: dict) -> str:
    d = Doc("ab", W, H, "About: what I do and what I build for fun",
            "Left card: a browser window showing a full-stack illustration and three capabilities. Right card: a carousel of four random "
            "projects that make up the hobby of building random projects, with three daily progress rings.")
    left = browser(d) + capabilities(d)
    right = carousel(d) + rings(d)
    d.body.append(d.card(0, 0, 440, H, left, auras=(("v", .1, .05, .8, 19), ("c", .95, 1.0, .6, 25))))
    d.body.append(d.card(460, 0, 440, H, right, auras=(("p", .9, .05, .7, 21), ("c", .05, 1.0, .7, 17))))
    return d.svg()
