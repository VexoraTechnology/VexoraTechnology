"""Shared SVG toolkit used by every generator: fonts, cards, animation helpers.

Rules baked in here (GitHub renders these files through <img>, so only CSS + SMIL run):
  * base attributes always describe the FINISHED state; animation only departs from it,
    so a renderer that ignores animation still shows a complete card;
  * every SMIL timeline begins at 0s and encodes delays in keyTimes;
  * CSS entrances use fill-mode "both";
  * ids are namespaced per document, fonts and images are inlined as base64.
"""
from __future__ import annotations

import base64
import io
import json
from collections import defaultdict
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

TOOLS = Path(__file__).resolve().parents[1]
ASSETS = TOOLS / "assets"

INK = "#0d0e16"
CYAN, VIOLET, PINK = "#22d3ee", "#a78bfa", "#f472b6"
TEXT, DIM, FAINT = "#e9ebf5", "#8f94ab", "#5d627d"
REC = "#ff4d6d"
METAL = [("0", "#f6f8fc"), (".34", "#aab1c2"), (".56", "#6a7186"), (".82", "#dbe0ec"), ("1", "#8a91a7")]

# Spline presets for calcMode="spline" (one curve reused for every segment).
EASE = {"out": "0.16 1 0.3 1", "in": "0.7 0 0.84 0", "inout": "0.65 0 0.35 1", "soft": "0.4 0 0.2 1"}


def fmt(v, nd: int = 2) -> str:
    """Formats numbers compactly (no trailing zeros, no '-0'); strings pass through."""
    if isinstance(v, str):
        return v
    if isinstance(v, int):
        return str(v)
    s = f"{v:.{nd}f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def attrs(**kw) -> str:
    """Builds an attribute string; trailing '_' drops reserved words, '_' becomes '-'."""
    out = []
    for k, v in kw.items():
        if v is None or v is False:
            continue
        out.append(f' {k.rstrip("_").replace("_", "-")}="{fmt(v)}"')
    return "".join(out)


def readable(hex_color: str) -> str:
    """Makes brand colours legible on the dark card: near-black marks become soft white,
    saturated dark colours are lightened just enough (never washed out)."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))

    def lum(r, g, b):
        lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in (r, g, b)]
        return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]

    if lum(r, g, b) < 0.06 and max(r, g, b) - min(r, g, b) < 0.15:
        return "#dfe2ee"
    while lum(r, g, b) < 0.30:
        r, g, b = (c + (1 - c) * 0.06 for c in (r, g, b))
    return "#{:02x}{:02x}{:02x}".format(round(r * 255), round(g * 255), round(b * 255))


def ramp(n: int) -> list[str]:
    """n colours sampled evenly along the aurora ramp (cyan, violet, pink)."""
    stops = [(34, 211, 238), (167, 139, 250), (244, 114, 182)]
    out = []
    for i in range(n):
        t = i / max(n - 1, 1) * 2
        a, b, f = stops[min(int(t), 1)], stops[min(int(t), 1) + 1], t - min(int(t), 1)
        out.append("#{:02x}{:02x}{:02x}".format(*(round(x + (y - x) * f) for x, y in zip(a, b))))
    return out


# ───────────────────────────── fonts ─────────────────────────────

class Face:
    """One font style: keeps the instanced TTF bytes for measuring and subsetting."""

    def __init__(self, family: str, weight: int, font: TTFont, stack: str):
        self.family, self.weight, self.stack = family, weight, stack
        buf = io.BytesIO()
        font.flavor, font.recalcTimestamp = None, False   # pinned timestamps keep builds byte-reproducible
        font.save(buf)
        self.data = buf.getvalue()
        probe = TTFont(io.BytesIO(self.data))
        self.cmap, self.hmtx, self.upem = probe.getBestCmap(), probe["hmtx"], probe["head"].unitsPerEm

    def width(self, text: str, size: float, tracking: float = 0.0) -> float:
        """Advance width without kerning: slightly generous, which is the safe side for layout."""
        total = sum(self.hmtx[self.cmap.get(ord(c), ".notdef")][0] for c in text)
        return total * size / self.upem + tracking * len(text)

    def woff2(self, chars: set[str]) -> bytes:
        """Subsets to the glyphs the document really uses and compresses to WOFF2."""
        opts = subset.Options()
        opts.flavor, opts.hinting, opts.layout_features = "woff2", False, ["*"]
        opts.notdef_outline, opts.name_IDs, opts.glyph_names = True, [1, 2], False
        font = TTFont(io.BytesIO(self.data), recalcTimestamp=False)
        sub = subset.Subsetter(options=opts)
        sub.populate(text="".join(sorted(chars | {" "})))
        sub.subset(font)
        buf = io.BytesIO()
        font.flavor = "woff2"
        font.save(buf)
        return buf.getvalue()


class Fonts:
    """Display = Bricolage Grotesque instanced from its variable file; mono = Azeret Mono."""

    SANS = '"Segoe UI",system-ui,-apple-system,Helvetica,Arial,sans-serif'
    MONO = 'ui-monospace,"SF Mono",Menlo,Consolas,monospace'

    def __init__(self):
        fonts = ASSETS / "fonts"

        def bricolage(opsz: int, wght: int) -> TTFont:
            return instancer.instantiateVariableFont(
                TTFont(fonts / "bricolage-grotesque-standard.woff2"), {"opsz": opsz, "wght": wght, "wdth": 100})

        self.faces = {
            "d8": Face("Bricolage", 800, bricolage(96, 800), self.SANS),
            "d7": Face("Bricolage", 700, bricolage(32, 700), self.SANS),
            "d5": Face("Bricolage", 500, bricolage(14, 500), self.SANS),
            "m4": Face("Azeret", 400, TTFont(fonts / "azeret-mono-400.woff2"), self.MONO),
            "m7": Face("Azeret", 700, TTFont(fonts / "azeret-mono-700.woff2"), self.MONO),
        }

    def width(self, face: str, text: str, size: float, tracking: float = 0.0) -> float:
        return self.faces[face].width(text, size, tracking)


_FONTS: Fonts | None = None


def fonts() -> Fonts:
    """Builds the (slow) font instances once per process."""
    global _FONTS
    if _FONTS is None:
        _FONTS = Fonts()
    return _FONTS


_ICONS = json.loads((ASSETS / "icons.json").read_text())


# ───────────────────────────── animation helpers ─────────────────────────────

def _timeline(pts, dur):
    """Pads (time, value) points to span 0..dur so every timeline starts at 0s."""
    pts = sorted(pts, key=lambda p: p[0])
    if pts[0][0] > 0:
        pts = [(0, pts[0][1])] + pts
    if pts[-1][0] < dur:
        pts = pts + [(dur, pts[-1][1])]
    values = ";".join(fmt(v) for _, v in pts)
    key_times = ";".join(fmt(min(1, t / dur), 5) for t, _ in pts)
    return values, key_times, len(pts)


def _timing(dur, ease, discrete, repeat, freeze, n):
    extra = {"dur": f"{fmt(dur, 3)}s", "begin": "0s"}
    if discrete:
        extra["calcMode"] = "discrete"
    elif ease:
        extra["calcMode"] = "spline"
        extra["keySplines"] = ";".join([EASE[ease]] * (n - 1))
    if repeat:
        extra["repeatCount"] = "indefinite"
    if freeze:
        extra["fill"] = "freeze"
    return extra


def animate(attr, pts, dur, *, ease=None, discrete=False, repeat=True, freeze=False, **more) -> str:
    """<animate> over [(seconds, value)] inside a loop of `dur` seconds."""
    values, key_times, n = _timeline(pts, dur)
    return "<animate" + attrs(attributeName=attr, values=values, keyTimes=key_times,
                              **_timing(dur, ease, discrete, repeat, freeze, n), **more) + "/>"


def animate_transform(kind, pts, dur, *, attr="transform", ease=None, repeat=True, freeze=False, **more) -> str:
    """<animateTransform> (translate/rotate/scale) over [(seconds, 'a b c')]."""
    values, key_times, n = _timeline(pts, dur)
    return "<animateTransform" + attrs(attributeName=attr, type=kind, values=values, keyTimes=key_times,
                                       **_timing(dur, ease, False, repeat, freeze, n), **more) + "/>"


def motion(path, dur, **more) -> str:
    """<animateMotion> along a path; rotate=0 keeps artwork upright."""
    return "<animateMotion" + attrs(path=path, dur=f"{fmt(dur, 3)}s", begin="0s", repeatCount="indefinite",
                                    rotate="0", **more) + "/>"


def pulse(dur, lo=0.25, hi=1.0, duty=0.5):
    """Hard on/off blink pattern used for cursors and REC dots."""
    return animate("opacity", [(0, hi), (dur * duty, lo)], dur, discrete=True)


def ellipse_path(a, b, phi_deg, theta0_deg, clockwise=True):
    """Relative two-arc ellipse starting at its own (0,0); returns (absolute start offset fn, path).

    The element sits at its t=0 position via a base translate(), and this path returns to (0,0),
    so a renderer ignoring animateMotion still shows every icon at a sensible spot.
    """
    import math
    phi, th = math.radians(phi_deg), math.radians(theta0_deg)
    cx = a * math.cos(th) * math.cos(phi) - b * math.sin(th) * math.sin(phi)
    cy = a * math.cos(th) * math.sin(phi) + b * math.sin(th) * math.cos(phi)
    sweep = 1 if clockwise else 0
    path = f"M0 0a{fmt(a)} {fmt(b)} {fmt(phi_deg)} 1 {sweep} {fmt(-2 * cx)} {fmt(-2 * cy)}a{fmt(a)} {fmt(b)} {fmt(phi_deg)} 1 {sweep} {fmt(2 * cx)} {fmt(2 * cy)}"
    return (cx, cy), path


# ───────────────────────────── document ─────────────────────────────

class Doc:
    """One standalone SVG: collects defs, css and body, then inlines only the font glyphs it used."""

    def __init__(self, ns: str, width: int, height: int, title: str, desc: str):
        self.ns, self.w, self.h, self.title, self.desc = ns, width, height, title, desc
        self.defs: list[str] = []
        self.css: list[str] = []
        self.body: list[str] = []
        self.chars: dict[str, set[str]] = defaultdict(set)
        self._icons: set[str] = set()
        self._n = 0
        self.font = fonts()
        self._standard_defs()

    # ── ids ──
    def id(self, name: str) -> str:
        return f"{self.ns}-{name}"

    def ref(self, name: str) -> str:
        return f"url(#{self.id(name)})"

    def uid(self, prefix: str = "u") -> str:
        self._n += 1
        return self.id(f"{prefix}{self._n}")

    # ── text ──
    def reg(self, face: str, s: str) -> None:
        self.chars[face].update(s)

    def t(self, s, face, x, y, size, fill=TEXT, anchor=None, cls="", **kw) -> str:
        """Registers glyphs for subsetting and returns a <text> element."""
        self.reg(face, s)
        return (f'<text x="{fmt(x)}" y="{fmt(y)}" class="{face}{" " + cls if cls else ""}" font-size="{fmt(size)}"'
                f'{attrs(fill=fill, text_anchor=anchor, **kw)}>{esc(s)}</text>')

    def w_of(self, face: str, s: str, size: float, tracking: float = 0.0) -> float:
        return self.font.width(face, s, size, tracking)

    # ── gradients ──
    def ugrad(self, name, x1, y1, x2, y2, stops, spread=None, extra="") -> str:
        """userSpaceOnUse linear gradient (safe for zero-height strokes); returns url(#id)."""
        body = "".join(f'<stop offset="{o}" stop-color="{c}"{attrs(stop_opacity=op)}/>' for o, c, *rest in stops
                       for op in [rest[0] if rest else None])
        self.defs.append(f'<linearGradient id="{self.id(name)}" gradientUnits="userSpaceOnUse"'
                         f'{attrs(x1=x1, y1=y1, x2=x2, y2=y2, spreadMethod=spread)}>{extra}{body}</linearGradient>')
        return self.ref(name)

    def aurora(self, name, x1, y1, x2, y2, spread=None, extra="") -> str:
        return self.ugrad(name, x1, y1, x2, y2, [("0", CYAN), (".5", VIOLET), ("1", PINK)], spread, extra)

    def metal(self, name="metal") -> str:
        if self.id(name) not in "".join(self.defs):
            stops = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in METAL)
            self.defs.append(f'<linearGradient id="{self.id(name)}" x1="0" y1="0" x2="1" y2="1">{stops}</linearGradient>')
        return self.ref(name)

    # ── icons ──
    def icon_def(self, slug: str) -> str:
        """Defines a Simple Icons path once and returns its element id."""
        if slug not in self._icons:
            self._icons.add(slug)
            self.defs.append(f'<path id="{self.id("ic-" + slug)}" d="{_ICONS[slug]["path"]}"/>')
        return self.id("ic-" + slug)

    def icon(self, slug: str, cx: float, cy: float, size: float, fill: str | None = None) -> str:
        """Draws a Simple Icons glyph centred at (cx, cy)."""
        ident = self.icon_def(slug)
        s = size / 24
        colour = fill or readable("#" + _ICONS[slug]["hex"])
        return f'<use href="#{ident}" fill="{colour}" transform="translate({fmt(cx - 12 * s)} {fmt(cy - 12 * s)}) scale({fmt(s, 4)})"/>'

    # ── odometer ──
    def reel(self, x, y, digit, size, start, spins, loop, face="m7", fill=TEXT) -> str:
        """One odometer digit: a strip scrolls (ones digits spin extra turns) and lands on `digit` (finished state)."""
        adv, pitch = self.w_of(face, "0", size), size * 1.35
        stop = digit + 10 * spins
        cid = self.uid("reel")
        self.defs.append(f'<clipPath id="{cid}"><rect x="{fmt(x - 1)}" y="{fmt(y - size * .86)}" width="{fmt(adv + 2)}" height="{fmt(size * 1.02)}"/></clipPath>')
        strip = "".join(self.t(str(i % 10), face, x, y + i * pitch, size, fill=fill) for i in range(stop + 1))
        roll = animate_transform("translate", [(0, "0 0"), (start, "0 0"), (start + 1.5, f"0 {fmt(-stop * pitch)}")], loop, ease="out")
        return f'<g clip-path="url(#{cid})"><g transform="translate(0 {fmt(-stop * pitch)})">{roll}{strip}</g></g>'

    # ── css ──
    def rise(self, name, dy=10, dx=0, dur=0.7, delay=0.0, ease="cubic-bezier(.2,.8,.2,1)") -> str:
        """CSS entrance (fade + slide) with fill-mode both; the base style is the finished state."""
        cls = self.id(name)
        self.css.append(f"@keyframes {cls}{{from{{opacity:0;transform:translate({fmt(dx)}px,{fmt(dy)}px)}}}}"
                        f".{cls}{{animation:{cls} {fmt(dur)}s {ease} {fmt(delay)}s both}}")
        return f"ent {cls}"

    # ── card chrome ──
    def _standard_defs(self) -> None:
        ns = self.ns
        self.defs += [
            f'<linearGradient id="{ns}-hair" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{CYAN}" stop-opacity=".8"/>'
            f'<stop offset=".5" stop-color="{VIOLET}" stop-opacity=".22"/><stop offset="1" stop-color="{PINK}" stop-opacity=".75"/></linearGradient>',
            f'<linearGradient id="{ns}-glass" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".06"/>'
            f'<stop offset=".55" stop-color="#fff" stop-opacity=".012"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>',
            f'<pattern id="{ns}-dots" width="16" height="16" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1" fill="#fff" fill-opacity=".075"/></pattern>',
        ]
        for key, colour, op in (("c", CYAN, ".30"), ("v", VIOLET, ".28"), ("p", PINK, ".24")):
            self.defs.append(f'<radialGradient id="{ns}-a{key}"><stop offset="0" stop-color="{colour}" stop-opacity="{op}"/>'
                             f'<stop offset="1" stop-color="{colour}" stop-opacity="0"/></radialGradient>')

    def card(self, x, y, w, h, inner, r=22, auras=(("c", .08, .02, .75, 17), ("p", .95, 1.0, .7, 23))) -> str:
        """Midnight-glass card: ink fill, sheen, drifting aurora, dot texture, gradient hairline.

        `inner` is drawn in card-local coordinates and clipped to the rounded rectangle.
        """
        cid = self.uid("card")
        blobs = []
        for key, fx, fy, size, period in auras:
            rx, ry = w * size / 2, h * size * 0.62 / 2
            drift = animate_transform("translate", [(0, "0 0"), (period / 2, f"{fmt(w * .025)} {fmt(-h * .03)}"), (period, "0 0")],
                                      period, ease="soft")
            blobs.append(f'<ellipse cx="{fmt(w * fx)}" cy="{fmt(h * fy)}" rx="{fmt(rx)}" ry="{fmt(ry)}" fill="url(#{self.ns}-a{key})">{drift}</ellipse>')
        return (f'<g transform="translate({fmt(x)} {fmt(y)})"><clipPath id="{cid}"><rect width="{fmt(w)}" height="{fmt(h)}" rx="{fmt(r)}"/></clipPath>'
                f'<rect width="{fmt(w)}" height="{fmt(h)}" rx="{fmt(r)}" fill="{INK}"/>'
                f'<g clip-path="url(#{cid})">{"".join(blobs)}<rect width="{fmt(w)}" height="{fmt(h)}" fill="url(#{self.ns}-glass)"/>'
                f'<rect width="{fmt(w)}" height="{fmt(h)}" fill="url(#{self.ns}-dots)"/>{inner}</g>'
                f'<rect x=".5" y=".5" width="{fmt(w - 1)}" height="{fmt(h - 1)}" rx="{fmt(r - .5)}" fill="none" stroke="url(#{self.ns}-hair)"/></g>')

    # ── output ──
    def font_css(self) -> str:
        rules, classes = [], []
        for key, chars in sorted(self.chars.items()):
            face = self.font.faces[key]
            b64 = base64.b64encode(face.woff2(chars)).decode()
            rules.append(f'@font-face{{font-family:"{face.family}";font-style:normal;font-weight:{face.weight};'
                         f'src:url(data:font/woff2;base64,{b64}) format("woff2")}}')
            classes.append(f'.{key}{{font-family:"{face.family}",{face.stack};font-weight:{face.weight}}}')
        return "".join(rules + classes)

    def svg(self) -> str:
        css = self.font_css() + "".join(self.css) + "@media (prefers-reduced-motion:reduce){.ent{animation:none!important}}"
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}" '
                f'role="img" aria-labelledby="{self.ns}-t {self.ns}-d"><title id="{self.ns}-t">{esc(self.title)}</title>'
                f'<desc id="{self.ns}-d">{esc(self.desc)}</desc><style>{css}</style><defs>{"".join(self.defs)}</defs>'
                f'{"".join(self.body)}</svg>')
