"""connect.svg: the pointing character with its neon "Itzjay169" sign, and one link card per channel.

The sticker's checkerboard is baked into its pixels, so media.sticker_layers() cuts the character and the sign into two
transparent layers; the sign then glows and floats on its own. SVG used through <img> cannot hold clickable links, so
the README wraps this image in a link and repeats every URL as text.
"""
from __future__ import annotations

from . import content as C, media
from .glyphs import line_icon
from .kit import CYAN, DIM, TEXT, VIOLET, Doc, _ICONS, animate, animate_transform, fmt, readable

FILE = "connect.svg"
W, H = 900, 470
CARD_X, CARD_W, CARD_H = 330, 530, 68
SCALE = 430 / 1522            # display scale: the character layer is 430 px tall on the card


def character(d: Doc) -> str:
    """Spotlight, floor shadow, the floating character and the pulsing neon sign."""
    layers = media.sticker_layers()
    (cx0, cy0, cx1, cy1), (sx0, sy0, sx1, sy1) = layers["char_box"], layers["sign_box"]
    ix, iy = 22, 22
    char = layers["char"].crop(layers["char_box"])
    sign = layers["sign"].crop(layers["sign_box"])
    cw, ch = (cx1 - cx0) * SCALE, (cy1 - cy0) * SCALE
    sw, sh = (sx1 - sx0) * SCALE, (sy1 - sy0) * SCALE
    sx, sy = ix + (sx0 - cx0) * SCALE, iy + (sy0 - cy0) * SCALE
    spot, shade, glow = d.id("spot"), d.id("shade"), d.id("signglow")
    d.defs.append(f'<radialGradient id="{spot}"><stop offset="0" stop-color="{VIOLET}" stop-opacity=".4"/><stop offset=".6" stop-color="{CYAN}" stop-opacity=".1"/>'
                  f'<stop offset="1" stop-color="{CYAN}" stop-opacity="0"/></radialGradient>')
    d.defs.append(f'<radialGradient id="{shade}"><stop offset="0" stop-color="#000" stop-opacity=".6"/><stop offset="1" stop-color="#000" stop-opacity="0"/></radialGradient>')
    d.defs.append(f'<radialGradient id="{glow}"><stop offset="0" stop-color="#2f6bff" stop-opacity=".6"/><stop offset=".55" stop-color="#2f6bff" stop-opacity=".18"/>'
                  f'<stop offset="1" stop-color="#2f6bff" stop-opacity="0"/></radialGradient>')
    def bob(amp: float) -> str:
        return animate_transform("translate", [(0, "0 0"), (2.5, f"0 {-amp}"), (5, "0 0")], 5, ease="soft")

    pulse = animate("opacity", [(0, .55), (1.5, 1), (3, .55)], 3, ease="soft")
    return (f'<circle cx="{fmt(ix + cw / 2)}" cy="240" r="190" fill="url(#{spot})"/>'
            f'<ellipse cx="{fmt(ix + cw / 2)}" cy="{fmt(iy + ch)}" rx="62" ry="9" fill="url(#{shade})"/>'
            f'<g class="{d.rise("char", dy=18, dur=.9)}"><g>{bob(4)}<image href="{media.png_uri(char.resize((round(cw * 2), round(ch * 2)), media.Image.LANCZOS), 256)}" '
            f'x="{ix}" y="{iy}" width="{fmt(cw)}" height="{fmt(ch)}"/></g></g>'
            f'<circle cx="{fmt(sx + sw / 2)}" cy="{fmt(sy + sh / 2)}" r="118" fill="url(#{glow})" opacity="1">{pulse}</circle>'
            f'<g class="{d.rise("sign", dy=-10, dur=.9, delay=.25)}"><g>{animate_transform("translate", [(0, "0 0"), (3, "0 -3"), (6, "0 0")], 6, ease="soft")}'
            f'<image href="{media.png_uri(sign.resize((round(sw * 2), round(sh * 2)), media.Image.LANCZOS))}" x="{fmt(sx)}" y="{fmt(sy)}" width="{fmt(sw)}" height="{fmt(sh)}"/></g></g>')


def link_card(d: Doc, k: int, y: float, slug: str, title: str, text: str) -> str:
    """One link card: icon tile, title, mono address and an arrow that nudges right on its own beat (delay lives in keyTimes)."""
    tint = readable("#" + _ICONS[slug]["hex"])
    beat = 3.2
    start = .4 + k * .5
    nudge = animate_transform("translate", [(start, "0 0"), (start + .22, "9 0"), (start + .55, "0 0")], beat, ease="soft")
    body = (f'<rect x=".5" y=".5" width="{CARD_W - 1}" height="{CARD_H - 1}" rx="17.5" fill="#fff" fill-opacity=".04" stroke="{d.ref("hair")}"/>'
            f'<rect x="14" y="12" width="44" height="44" rx="12" fill="{tint}" fill-opacity=".1" stroke="{tint}" stroke-opacity=".45"/>{d.icon(slug, 36, 34, 22)}'
            f'{d.t(title, "d7", 72, 30, 17, fill=TEXT)}{d.t(text, "m4", 72, 51, 12.5, fill=DIM)}'
            f'<g transform="translate({CARD_W - 44} {CARD_H / 2 - 9})"><g>{nudge}{line_icon("arrow", 0, 0, 18, tint, 1.8)}</g></g>')
    return f'<g class="{d.rise(f"card{k}", dx=26, dy=0, delay=.35 + k * .13, dur=.7)}"><g transform="translate({CARD_X} {y})">{body}</g></g>'


def build(gh: dict) -> str:
    names = ", ".join(f"{title} ({text})" for _, title, text, _ in C.LINKS)
    d = Doc("cn", W, H, f"Connect with {C.NAME}", f"{C.NAME} points at a neon {C.HANDLE} sign. Ways to get in touch: {names}. Open to collaborations.")
    heading, size = "Let's build something together", 32
    size = min(size, 520 / d.w_of("d8", heading, 1))
    span = d.w_of("d8", heading, size)
    flow = animate_transform("translate", [(0, "0 0"), (10, f"{fmt(2 * span)} 0")], 10, attr="gradientTransform")
    grad = d.aurora("head", CARD_X, 0, CARD_X + span, 0, spread="reflect", extra=flow)
    text = (f'<g class="{d.rise("head", dy=12, delay=.2)}">{d.t(heading, "d8", CARD_X, 92, size, fill=grad)}</g>'
            f'<g class="{d.rise("sub", dy=10, delay=.35)}">{d.t("Open to collabs on web apps, AI-powered tools and desktop software.", "d5", CARD_X, 120, 14.5, fill=DIM)}</g>')
    cards = "".join(link_card(d, k, 148 + k * (CARD_H + 10), icon, title, shown) for k, (icon, title, shown, _) in enumerate(C.LINKS))
    d.body.append(d.card(0, 0, W, H, character(d) + text + cards, r=26, auras=(("v", .1, .55, .7, 19), ("c", .98, .05, .6, 23), ("p", .9, 1.0, .6, 17))))
    return d.svg()
