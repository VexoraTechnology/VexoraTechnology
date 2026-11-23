"""hero.svg: a camera-viewfinder hero.

Left: "open to collabs" pill, typed intro, rising-mask gradient name, cycling roles, pitch, meta row.
Right: the clip plays frame by frame (SMIL opacity switching) inside a feathered viewfinder with
corner brackets, REC dot, filename and a scrubber, all locked to one 4 s loop:
play once, hold the last frame, fade, repeat.
"""
from __future__ import annotations

import base64
import math

from . import content as C
from .kit import (CYAN, DIM, INK, PINK, REC, TEXT, VIOLET, Doc, animate, animate_transform, fmt, pulse)

W, H = 900, 420
LOOP, FADE_IN, HOLD_TO, FADE_END = 4.0, 0.2, 3.4, 3.8
X0 = 52                                   # left column
SX, SY, SW, SH = 572, 34, 284, 300        # viewfinder screen


def pill(d: Doc) -> str:
    """Availability pill: pulsing dot (the ring is invisible in the finished state) and a hairline border."""
    label, size = "open to collabs", 12.5
    pw = 38 + d.w_of("m4", label, size) + 18
    ring = (f'<circle cx="{X0 + 19}" cy="51" r="4" fill="none" stroke="{CYAN}" opacity="0">'
            f'{animate("r", [(0, 4), (2, 12)], 2, ease="out")}{animate("opacity", [(0, .7), (2, 0)], 2, ease="out")}</circle>')
    body = (f'<rect x="{X0}" y="36" width="{fmt(pw)}" height="30" rx="15" fill="{CYAN}" fill-opacity=".07" stroke="{d.ref("hair")}"/>'
            f'<circle cx="{X0 + 19}" cy="51" r="4" fill="{CYAN}"/>{ring}'
            f'{d.t(label, "m4", X0 + 34, 55.3, size, fill=TEXT)}')
    return f'<g class="{d.rise("pill", dy=-8, delay=0.05)}">{body}</g>'


def typed_line(d: Doc) -> str:
    """Typed 'Hi there, I'm': a clip rect grows one character per step (mono font keeps steps exact)."""
    s, size, y = "Hi there, I'm", 17, 100
    adv = d.w_of("m4", "H", size)
    n, full, t0, step = len(s), adv * len(s), 0.35, 0.07
    ts = [(t0 + k * step, k * adv) for k in range(n + 1)]
    dur = ts[-1][0] + 0.1
    cid = d.id("typed")
    clip = (f'<clipPath id="{cid}"><rect x="{X0}" y="{y - 22}" width="{fmt(full)}" height="30">'
            f'{animate("width", [(0, 0)] + ts, dur, discrete=True, repeat=False, freeze=True)}</rect></clipPath>')
    d.defs.append(clip)
    caret_x = [(t, X0 + w + 1) for t, w in ts]
    caret = (f'<rect x="{fmt(X0 + full + 1)}" y="{y - 17}" width="2" height="21" rx="1" fill="{CYAN}">'
             f'{animate("x", [(0, X0 + 1)] + caret_x, dur, discrete=True, repeat=False, freeze=True)}{pulse(1.06, 0, 1)}</rect>')
    return f'<g clip-path="url(#{cid})">{d.t(s, "m4", X0, y, size, fill=VIOLET)}</g>{caret}'


def name_block(d: Doc) -> str:
    """Big name: aurora gradient that flows forever, revealed by a mask that rises while the text lifts into place."""
    name, y = C.NAME, 172
    size = min(70, 468 / d.w_of("d8", name, 1))
    span = d.w_of("d8", name, size)
    flow = animate_transform("translate", [(0, "0 0"), (9, f"{fmt(2 * span)} 0")], 9, attr="gradientTransform")
    grad = d.aurora("name", X0, 0, X0 + span, 0, spread="reflect", extra=flow)
    mid = d.id("nm")
    d.defs.append(f'<mask id="{mid}" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">'
                  f'<rect x="{X0 - 12}" y="114" width="{fmt(span + 24)}" height="96" fill="#fff">'
                  f'{animate("y", [(0, 216), (0.4, 216), (1.35, 114)], 1.35, ease="out", repeat=False, freeze=True)}</rect></mask>')
    lift = animate_transform("translate", [(0, "0 20"), (0.4, "0 20"), (1.35, "0 0")], 1.35, ease="out", repeat=False, freeze=True)
    return f'<g mask="url(#{mid})"><g>{lift}{d.t(name, "d8", X0, y, size, fill=grad)}</g></g>'


def role_cycle(d: Doc) -> str:
    """Roles crossfade with a small vertical drift; the first role is the static, finished state."""
    slot = 2.6
    total = slot * len(C.ROLES)
    out = []
    for i, role in enumerate(C.ROLES):
        t0 = i * slot
        pts = [(t0, 0), (t0 + .4, 1), (t0 + slot - .4, 1), (t0 + slot, 0)]
        move = [(t0, "0 9"), (t0 + .4, "0 0"), (t0 + slot - .4, "0 0"), (t0 + slot, "0 -9")]
        if i == 0:   # wraps: fades in as the last role leaves
            pts += [(total - .4, 0), (total, 1)]
            move += [(total - .4, "0 9"), (total, "0 0")]
        inner = d.t(role, "d7", X0, 216, 22, fill=TEXT)
        # the finished-state opacity lives on the animated group itself (a static opacity on the child would multiply to zero)
        out.append(f'<g opacity="{1 if i == 0 else 0}">{animate_transform("translate", move, total, ease="soft")}{animate("opacity", pts, total, ease="soft")}{inner}</g>')
    return f'<g class="{d.rise("roles", dy=8, delay=1.2)}">{"".join(out)}</g>'


def skills_block(d: Doc) -> str:
    """Bottom area: three skill columns, every item with its Simple Icons logo; the columns rise in one after another."""
    accents, out = (CYAN, VIOLET, PINK), []
    for c, (group, items) in enumerate(C.HERO_SKILLS):
        x = X0 + c * 168
        rows = d.t(group, "d7", x, 284, 12.5, fill=accents[c])
        for k, (label, slug) in enumerate(items):
            y = 308 + k * 22
            rows += d.icon(slug, x + 7.5, y - 4.6, 15) + d.t(label, "d5", x + 22, y, 13, fill=TEXT)
        out.append(f'<g class="{d.rise(f"skill{c}", dy=8, delay=1.1 + c * .18, dur=.6)}">{rows}</g>')
    return "".join(out)


def viewfinder(d: Doc, jpegs: list[bytes], clip: dict) -> str:
    """Feathered video, brackets that redraw each loop, REC dot, filename and a scrubber synced to the loop."""
    play = clip["frames"] / clip["fps"]
    soft, mid = d.id("soft"), d.id("vmask")
    d.defs.append(f'<filter id="{soft}" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="8"/></filter>')
    d.defs.append(f'<mask id="{mid}" maskUnits="userSpaceOnUse" x="{SX}" y="{SY}" width="{SW}" height="{SH}">'
                  f'<rect x="{SX + 22}" y="{SY + 22}" width="{SW - 44}" height="{SH - 44}" rx="18" fill="#fff" filter="url(#{soft})"/></mask>')
    n, step = len(jpegs), play / len(jpegs)
    imgs = []
    for i, jpg in enumerate(jpegs):
        t0, t1 = i * step, (i + 1) * step
        pts = [(0, 1), (t1, 0)] if i == 0 else ([(0, 0), (t0, 1)] if i == n - 1 else [(0, 0), (t0, 1), (t1, 0)])
        uri = "data:image/jpeg;base64," + base64.b64encode(jpg).decode()
        imgs.append(f'<image href="{uri}" x="{SX}" y="{SY}" width="{SW}" height="{SH}" preserveAspectRatio="none" opacity="{1 if i == n - 1 else 0}">'
                    f'{animate("opacity", pts, LOOP, discrete=True)}</image>')
    fade = animate("opacity", [(0, 0), (FADE_IN, 1), (HOLD_TO, 1), (FADE_END, 0)], LOOP)
    video = f'<g mask="url(#{mid})"><g>{fade}{"".join(imgs)}</g></g>'

    cx, cy = SX + SW / 2, SY + SH / 2
    thirds = (f'<path d="M{SX + SW / 3:.1f} {SY}v{SH}M{SX + 2 * SW / 3:.1f} {SY}v{SH}M{SX} {SY + SH / 3:.1f}h{SW}M{SX} {SY + 2 * SH / 3:.1f}h{SW}" '
              f'stroke="#fff" stroke-opacity=".08" stroke-dasharray="2 6" fill="none"/>')
    reticle = (f'<circle cx="{fmt(cx)}" cy="{fmt(cy)}" r="14" fill="none" stroke="#fff" stroke-width="1.5" opacity="0">'
               f'{animate("r", [(0, 26), (.7, 14)], LOOP, ease="out")}{animate("opacity", [(0, 0), (.15, .8), (.9, .8), (1.1, 0)], LOOP)}</circle>')

    x0, y0, x1, y1, arm = SX - 6, SY - 6, SX + SW + 6, SY + SH + 6, 24
    stroke = d.aurora("brk", SX, 0, SX + SW, 0)
    corners = [f"M{x0} {y0 + arm}V{y0}H{x0 + arm}", f"M{x1 - arm} {y0}H{x1}V{y0 + arm}",
               f"M{x1} {y1 - arm}V{y1}H{x1 - arm}", f"M{x0 + arm} {y1}H{x0}V{y1 - arm}"]
    draw = animate("stroke-dashoffset", [(0, 2 * arm + 1), (.5, 0)], LOOP, ease="out")      # each bracket is two straight arms
    brackets = "".join(f'<path d="{c}" stroke-dasharray="{2 * arm + 1}" stroke-dashoffset="0">{draw}</path>' for c in corners)
    brackets = f'<g fill="none" stroke="{stroke}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">{brackets}</g>'

    hud = (f'<circle cx="{SX + 22}" cy="{SY + 22}" r="4.5" fill="{REC}">{pulse(1.0, .15, 1)}</circle>'
           f'{d.t("REC", "m7", SX + 33, SY + 26, 11, fill=TEXT, letter_spacing=1)}'
           f'{d.t(clip["name"], "m4", SX + SW - 18, SY + 26, 10.5, fill=DIM, anchor="end")}')

    ty = SY + SH + 22
    track = f'<rect x="{SX}" y="{ty}" width="{SW}" height="4" rx="2" fill="#fff" fill-opacity=".12"/>'
    fill_g = d.aurora("scrub", SX, 0, SX + SW, 0)
    prog = [(0, 0), (play, SW), (FADE_END, SW), (LOOP, 0)]
    scrub = (f'<rect x="{SX}" y="{ty}" width="{SW}" height="4" rx="2" fill="{fill_g}">{animate("width", prog, LOOP)}</rect>'
             f'<circle cx="{SX + SW}" cy="{ty + 2}" r="5.5" fill="#fff">{animate("cx", [(a, SX + b) for a, b in prog], LOOP)}</circle>')
    total_s = round(play)
    secs = list(range(int(play) + 1))
    states = []
    for s in secs:
        last = s == secs[-1]
        pts = ([(0, 1)] if s == 0 else [(0, 0), (s, 1)]) + ([] if last else [(s + 1, 0)])
        label = d.t(f"00:{s:02d} / 00:{total_s:02d}", "m4", SX, ty + 24, 11, fill=DIM, opacity=1 if last else 0)
        states.append(label.replace("</text>", f'{animate("opacity", pts, LOOP, discrete=True)}</text>'))
    return video + thirds + reticle + brackets + hud + track + scrub + "".join(states)


def build(jpegs: list[bytes], clip: dict, gh: dict) -> str:
    """Assembles hero.svg; `clip` = {name, frames, fps}."""
    d = Doc("hero", W, H, f"{C.NAME}, {C.ROLE}",
            f"{C.NAME} is a {C.ROLE} at {C.COMPANY}. Animated hero: a camera viewfinder plays a short clip of the developer, beside a typed "
            "greeting, a gradient name, rotating role lines and the skills he works with, each with its logo.")
    inner = pill(d) + typed_line(d) + name_block(d) + role_cycle(d)
    inner += d.t(C.PITCH, "d5", X0, 248, 14.5, fill=DIM, cls=d.rise("pitch", dy=8, delay=1.0))
    inner += skills_block(d) + viewfinder(d, jpegs, clip)
    d.body.append(d.card(0, 0, W, H, inner, r=26, auras=(("c", .06, .04, .75, 17), ("v", .82, .5, .6, 21), ("p", .98, 1.0, .7, 25))))
    return d.svg()
