"""id-dashboard.svg: a lanyard ID badge that drops in and swings on simulated double-pendulum physics, beside a
dashboard (count-up KPI reels, a single-hue bar chart of the busiest repos, a "now" panel).

Everything shares one 12 s loop: drop and swing, rest, retract, repeat. The finished card (base attributes) is the
badge hanging still with the dashboard fully populated. The badge shows the half-shot photo, not a face crop.
"""
from __future__ import annotations

import hashlib
import math

from . import content as C, media, physics
from .brand import vexora_mark
from .glyphs import line_icon
from .kit import CYAN, DIM, PINK, TEXT, VIOLET, Doc, animate, animate_transform, fmt

FILE = "id-dashboard.svg"
W, H = 900, 540
LOOP = 12.0
PX, PY = 160, 14          # top ring (outer pivot)
CLX, CLY = 160, 158       # clasp ring (badge pivot)
BX, BY, BW, BH = 60, 150, 200, 366
PHOTO = (24, 72, 152, 176)   # x, y, w, h of the photo frame on the badge


# ───────────────────────────── badge ─────────────────────────────

def barcode(text: str, width: float = 106, height: float = 22) -> str:
    """Deterministic barcode: bar and gap widths come from a hash of the text."""
    digest = hashlib.sha256(text.encode()).digest()
    x, i, out = 0.0, 0, []
    while True:
        w = 1 + (digest[i % 32] >> (i % 3)) % 3
        if x + w > width:
            break
        out.append(f'<rect x="{fmt(x)}" width="{w}" height="{height}"/>')
        x += w + 1 + digest[(i * 7) % 32] % 2
        i += 1
    return "".join(out)


def chip(d: Doc) -> str:
    """Gold contact chip with a glint that sweeps across every 6 s."""
    cid = d.uid("chip")
    gold = d.ugrad("gold", 0, 0, 34, 26, [("0", "#f8e3a6"), (".5", "#d2a23a"), ("1", "#f4d57f")])
    d.defs.append(f'<clipPath id="{cid}"><rect width="34" height="26" rx="5"/></clipPath>')
    glint = animate_transform("translate", [(0, "-46 0"), (1.1, "52 0")], 6, ease="inout")
    return (f'<g clip-path="url(#{cid})"><rect width="34" height="26" fill="{gold}"/>'
            f'<path d="M0 8.7H34M0 17.3H34M12 0V26M22 0V26" stroke="#8a6414" stroke-opacity=".55" stroke-width=".9" fill="none"/>'
            f'<rect x="11" y="8" width="12" height="10" rx="2.5" fill="none" stroke="#8a6414" stroke-opacity=".6" stroke-width=".9"/>'
            f'<g>{glint}<rect x="0" y="-4" width="12" height="34" fill="#fff" fill-opacity=".5" transform="skewX(-20)"/></g></g>')


def badge_face(d: Doc) -> str:
    """The badge itself in its own coordinates (0,0)-(200,366)."""
    inside, rid = d.uid("badge"), d.uid("portrait")
    px, py, pw, ph = PHOTO
    d.defs.append(f'<clipPath id="{inside}"><rect width="{BW}" height="{BH}" rx="16"/></clipPath>')
    d.defs.append(f'<clipPath id="{rid}"><rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="16"/></clipPath>')
    bg = d.ugrad("badgebg", 0, 0, 0, BH, [("0", "#1b1c32"), ("1", "#0d0e1a")])
    light = d.aurora("light", px, py, px + pw, py + ph)
    foil_grad = d.ugrad("foil", 0, 0, 70, 0, [("0", "#fff", 0), (".3", CYAN, .55), (".5", "#fff", .8), (".7", PINK, .55), ("1", "#fff", 0)])
    perimeter = 2 * (pw - 32) + 2 * (ph - 32) + 2 * math.pi * 16     # real length: no pathLength dependence
    travel = animate("stroke-dashoffset", [(0, 0), (3, -perimeter)], 3)
    dash = f'{perimeter * .15:.1f} {perimeter * .85:.1f}'
    frame = f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="16" fill="none" stroke-dasharray="{dash}" stroke="{light}" stroke-linecap="round"'
    scan = (f'<rect x="70" y="326" width="2" height="26" fill="{CYAN}" opacity="0">{animate("x", [(0, 70), (1.9, 176)], 2, ease="inout")}'
            f'{animate("opacity", [(0, 0), (.15, .9), (1.75, .9), (1.9, 0)], 2)}</rect>')
    foil = (f'<g clip-path="url(#{inside})"><g>{animate_transform("translate", [(0, "-150 0"), (1.5, "330 0")], 4, ease="inout")}'
            f'<rect x="0" y="-60" width="70" height="460" fill="{foil_grad}" fill-opacity=".5" transform="rotate(18)"/></g></g>')
    uri = media.png_uri(media.badge_photo(pw * 2, ph * 2))
    photo = f'<image href="{uri}" x="{px}" y="{py}" width="{pw}" height="{ph}" clip-path="url(#{rid})" preserveAspectRatio="xMidYMid slice"/>'
    return (f'<rect width="{BW}" height="{BH}" rx="16" fill="{bg}"/><g clip-path="url(#{inside})"><rect width="{BW}" height="{BH}" fill="url(#{d.ns}-dots)"/>'
            f'<rect x="80" y="10" width="40" height="9" rx="4.5" fill="#06060c" stroke="#fff" stroke-opacity=".2"/>{vexora_mark(d, 18, 22, 30)}'
            f'{d.t("VEXORA TECHNOLOGY", "d7", 56, 40.5, 10, fill=TEXT, letter_spacing=1.2)}<path d="M18 58H182" stroke="#fff" stroke-opacity=".1"/>'
            f'{photo}{frame} stroke-width="6" opacity=".3">{travel}</rect>{frame} stroke-width="2.4">{travel}</rect>'
            f'<rect x="{px + .5}" y="{py + .5}" width="{pw - 1}" height="{ph - 1}" rx="15.5" fill="none" stroke="#fff" stroke-opacity=".16"/>'
            f'{d.t(C.NAME, "d8", 100, 278, 21, fill=TEXT, anchor="middle")}{d.t(C.ROLE, "d5", 100, 296, 11, fill=DIM, anchor="middle")}'
            f'{d.t("@" + C.HANDLE, "m7", 100, 314, 11.5, fill=CYAN, anchor="middle")}'
            f'<g transform="translate(22 326)">{chip(d)}</g><g transform="translate(70 328)" fill="#e9ebf5" fill-opacity=".85">{barcode(C.HANDLE.upper())}</g>{scan}{foil}</g>'
            f'<rect x=".5" y=".5" width="{BW - 1}" height="{BH - 1}" rx="15.5" fill="none" stroke="{d.ref("hair")}"/>')


def lanyard(d: Doc) -> str:
    """Hook ring, printed strap, crimp and swivel ring. The ring that passes through the badge slot is the badge pivot."""
    metal = d.metal()
    strap = d.ugrad("strap", 144, 0, 176, 0, [("0", "#171829"), (".5", "#24263f"), ("1", "#171829")])
    text = d.t("VEXORA TECHNOLOGY", "m7", 0, 0, 7.4, fill=TEXT, letter_spacing=0.9, opacity=".9")
    return (f'<rect x="147" y="-4" width="26" height="9" rx="3" fill="{metal}"/><circle cx="{PX}" cy="{PY}" r="7" fill="none" stroke="{metal}" stroke-width="2.6"/>'
            f'<rect x="144" y="12" width="32" height="108" rx="3" fill="{strap}"/>'
            f'<path d="M147.5 14V118M172.5 14V118" stroke="#fff" stroke-opacity=".22" stroke-dasharray="3 3" fill="none"/>'
            f'<path d="M144 12V120" stroke="{CYAN}" stroke-opacity=".6" stroke-width="1.5"/><path d="M176 12V120" stroke="{PINK}" stroke-opacity=".6" stroke-width="1.5"/>'
            f'<g transform="translate({PX - 2.6} 17) rotate(90)">{text}</g>'
            f'<rect x="141" y="116" width="38" height="14" rx="3" fill="{metal}"/><rect x="153" y="130" width="14" height="14" rx="4" fill="{metal}"/>')


def clasp_ring(d: Doc) -> str:
    return f'<circle cx="{CLX}" cy="{CLY}" r="8" fill="none" stroke="{d.metal()}" stroke-width="3.2"/>'


def swinging(d: Doc) -> str:
    """Outer group: drop and retract (translate) plus strap angle about the top ring; inner group: badge angle about the clasp."""
    rows = [(0.55 + t, a, b) for t, a, b in physics.swing(seconds=8.6, out_hz=25)]
    outer = [(0, f"0 {fmt(physics.drop(0))}")]
    for k in range(1, 91):
        t = k / 60
        outer.append((t, f"0 {fmt(physics.drop(t), 2)}"))
    outer += [(10.2, "0 0")]
    start = 10.4
    for k in range(0, 67):
        t = start + k / 60
        outer.append((t, f"0 {fmt(physics.retract(t, start), 2)}"))
    outer += [(LOOP, f"0 {fmt(physics.retract(start + 2, start))}")]
    strap_pts = [(0, f"0 {PX} {PY}"), (0.55, f"0 {PX} {PY}")] + [(t, f"{fmt(a, 3)} {PX} {PY}") for t, a, _ in rows] + [(10.0, f"0 {PX} {PY}")]
    badge_pts = [(0, f"0 {CLX} {CLY}"), (0.55, f"0 {CLX} {CLY}")] + [(t, f"{fmt(b - a, 3)} {CLX} {CLY}") for t, a, b in rows] + [(10.0, f"0 {CLX} {CLY}")]
    return (f'<g>{animate_transform("translate", outer, LOOP)}<g>{animate_transform("rotate", strap_pts, LOOP)}{lanyard(d)}'
            f'<g>{animate_transform("rotate", badge_pts, LOOP)}<g transform="translate({BX} {BY})">{badge_face(d)}</g>{clasp_ring(d)}</g></g></g>')


# ───────────────────────────── dashboard ─────────────────────────────

def kpis(d: Doc, gh: dict) -> str:
    items = [("Repos", gh["public_repos"]), ("Commits", gh["commits"]), ("Languages", gh["languages"]),
             ("Stars", gh["stars"]) if gh["stars"] else ("Days on GitHub", gh["days"])]
    out, accents, tile_w = [], (CYAN, VIOLET, PINK, CYAN), 118
    adv = d.w_of("m7", "0", 34)
    for i, (label, value) in enumerate(items):
        x, digits = 28 + i * (tile_w + 12), str(value)
        out.append(f'<rect x="{x}" y="66" width="{tile_w}" height="84" rx="14" fill="#fff" fill-opacity=".035" stroke="#fff" stroke-opacity=".1"/>'
                   f'{d.t(label, "d5", x + 14, 90, 12, fill=DIM)}<rect x="{x + 14}" y="137" width="22" height="3" rx="1.5" fill="{accents[i]}"/>')
        for k, ch in enumerate(digits):
            out.append(d.reel(x + 14 + k * adv, 128, int(ch), 34, .5 + i * .12, 1 if k == len(digits) - 1 else 0, LOOP))
    return "".join(out)


def chart(d: Doc, gh: dict) -> str:
    """Single-hue horizontal bars of the busiest (or most-starred) repos; values are labelled at the bar ends."""
    metric = gh["metric"]
    rows = gh["ranked"][:5]
    top = max((r[metric] for r in rows), default=1) or 1
    title, sub = (("Most-starred repos", "stars per repo") if metric == "stars"
                  else ("Busiest repos", "commits per repo; this switches to stars once repos earn some"))
    out = [d.t(title, "d7", 28, 192, 16, fill=TEXT), d.t(sub, "d5", 28, 211, 12, fill=DIM)]
    for k, r in enumerate(rows):
        y, w = 230 + k * 28, max(5.0, 300 * r[metric] / top)
        opacity = fmt(1 - k * .09, 2)
        grow = animate("width", [(0, 0), (.9 + k * .12, 0), (2.1 + k * .12, w)], LOOP, ease="out")
        out.append(d.t(r["name"], "d5", 28, y + 11, 12.5, fill=TEXT)
                   + f'<rect x="170" y="{y}" width="{fmt(w)}" height="13" rx="6.5" fill="{CYAN}" fill-opacity="{opacity}">{grow}</rect>'
                   + d.t(str(r[metric]), "m7", 170 + w + 9, y + 11, 12, fill=CYAN).replace(
                       "</text>", f'{animate("opacity", [(0, 0), (1.6 + k * .12, 0), (2.1 + k * .12, 1)], LOOP)}</text>'))
    return "".join(out)


def now_panel(d: Doc) -> str:
    """'Now': a live dot and three current activities (edit them in content.py)."""
    ring = f'<circle cx="52" cy="402" r="4" fill="none" stroke="{CYAN}" opacity="0">{animate("r", [(0, 4), (2, 12)], 2, ease="out")}{animate("opacity", [(0, .7), (2, 0)], 2, ease="out")}</circle>'
    out = [f'<rect x="28" y="376" width="508" height="136" rx="16" fill="#fff" fill-opacity=".035" stroke="#fff" stroke-opacity=".1"/>',
           f'<circle cx="52" cy="402" r="4" fill="{CYAN}"/>{ring}{d.t("Now", "d7", 66, 407, 15, fill=TEXT)}']
    for k, (verb, text) in enumerate(C.NOW):
        y = 440 + k * 27
        out.append(d.t(verb, "d7", 50, y, 13, fill=(CYAN, VIOLET, PINK)[k]) + d.t(text, "d5", 132, y, 13, fill=TEXT))
    return "".join(out)


def dashboard(d: Doc, gh: dict) -> str:
    head = (d.icon("github", 40, 38, 22) + d.t(C.HANDLE, "d8", 60, 45, 22, fill=TEXT)
            + d.t(f"as of {gh['fetched']}", "d5", 536, 44, 12, fill=DIM, anchor="end"))
    fade = animate("opacity", [(0, 0), (.4, 1), (11.3, 1), (11.8, 0)], LOOP)
    return f'<g>{fade}{head + kpis(d, gh) + chart(d, gh) + now_panel(d)}</g>'


def build(gh: dict) -> str:
    d = Doc("id", W, H, f"ID badge and GitHub dashboard for {C.NAME}",
            f"A lanyard ID badge for {C.NAME} ({C.ROLE}, {C.COMPANY}) with a half-shot photo swings from a strap, next to a dashboard of GitHub numbers: "
            f"{gh['public_repos']} repos, {gh['commits']} commits across the main repos, a bar chart of the busiest repos and a Now panel.")
    d.body.append(d.card(0, 0, 320, H, swinging(d), auras=(("v", .5, .55, .9, 21), ("c", .1, .05, .6, 17), ("p", .95, 1.0, .6, 25))))
    d.body.append(d.card(336, 0, 564, H, dashboard(d, gh), auras=(("c", .95, .0, .6, 19), ("v", .05, 1.0, .6, 23))))
    return d.svg()
