"""Image preparation: base64 PNG/JPEG helpers, character cut-outs, video frame extraction.

Why: GitHub strips network access from SVGs, so every raster is inlined. Stills are PNG (never WebP),
video frames are JPEG, and sizes are budgeted so each SVG stays light enough for README viewing.
"""
from __future__ import annotations

import base64
import io
import math
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image  # noqa: F401  (re-exported for callers that resize layers)
from scipy import ndimage as ndi

MEDIA = Path(__file__).resolve().parents[1] / "media"


def png_uri(img: Image.Image, colors: int | None = None) -> str:
    """Encodes an image as a base64 PNG data URI; optional palette quantisation keeps alpha."""
    if colors:
        img = img.quantize(colors=colors, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def resize_rgba(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    """LANCZOS resize in premultiplied space, which avoids dark fringes on cut-out edges."""
    return img.convert("RGBa").resize(size, Image.LANCZOS).convert("RGBA")


def office() -> Image.Image:
    """The half-shot photo in the Vexora office (1312 x 1199)."""
    return Image.open(MEDIA / "office.png").convert("RGB")


def badge_photo(w: int, h: int) -> Image.Image:
    """Half-shot crop (head to laptop) for the ID badge, cover-fitted to w x h.

    The window starts right of the wall slogan so no half-cut letters show at the left edge.
    """
    box_w = 850
    box_h = box_w * h / w
    return office().crop((275, 89, 275 + box_w, round(89 + box_h))).resize((w, h), Image.LANCZOS)


def sticker_layers() -> dict:
    """Cuts the new sticker into a character layer and a neon-sign layer.

    The PNG has no real alpha: its 'transparent' checkerboard is baked into the pixels (light and dark grey squares).
    Foreground = anything that is not bright and neutral; enclosed bright areas (sneakers, sparkles) are filled back in.
    The character gets a freshly generated white die-cut outline; the sign's glow edge is decontaminated so no grey
    checker colour bleeds onto the dark card. Returns RGBA layers at full size plus the fingertip position.
    """
    rgb = np.array(Image.open(MEDIA / "sticker.png").convert("RGB"))
    px = rgb.astype(np.int16)
    spread, peak = px.max(2) - px.min(2), px.max(2)
    fg = ndi.binary_opening(~((spread < 16) & (peak > 135)), iterations=1)
    lab, n = ndi.label(fg)
    sizes = ndi.sum(np.ones_like(lab), lab, range(1, n + 1))
    fg = np.isin(lab, [i + 1 for i, v in enumerate(sizes) if v > 400])
    filled = ndi.binary_fill_holes(fg)
    # a thin bridge (the elbow meets the sign's glow) fuses them; they separate at erosion 12, then each pixel joins its nearest core
    cores_lab, _ = ndi.label(ndi.binary_erosion(filled, iterations=12))
    body_id, sign_id = cores_lab[520, 250], cores_lab[400, 760]
    assert body_id and sign_id and body_id != sign_id, "character and sign cores did not split"
    _, (iy, ix) = ndi.distance_transform_edt(~((cores_lab == body_id) | (cores_lab == sign_id)), return_indices=True)
    owner = cores_lab[iy, ix]
    body, sign = filled & (owner == body_id), filled & (owner == sign_id)

    # the sign's glow blends into the grey squares: keep only strongly blue or dark-navy pixels, then refill white cores
    blue = px[..., 2] - np.maximum(px[..., 0], px[..., 1])
    strong = sign & ((blue > 55) | (peak < 100))
    strong = ndi.binary_fill_holes(ndi.binary_closing(strong, iterations=2))
    lab3, n3 = ndi.label(strong)
    sizes3 = ndi.sum(np.ones_like(lab3), lab3, range(1, n3 + 1))
    sign = np.isin(lab3, [i + 1 for i, v in enumerate(sizes3) if v > 250])

    # character: original pixels + regenerated white outline (exact disc, anti-aliased)
    dist = ndi.distance_transform_edt(~body)
    ring = np.clip(11.5 - dist, 0, 1)
    char = np.dstack([np.where(body[..., None], rgb, 255), (np.maximum(ring, body) * 255).astype(np.uint8)])

    # sign: soft alpha, colours copied outward from a 2px-eroded core to drop the checker fringe
    core = ndi.binary_erosion(sign, iterations=3)
    _, (jy, jx) = ndi.distance_transform_edt(~core, return_indices=True)
    clean = rgb[jy, jx]
    soft = np.clip((ndi.gaussian_filter(ndi.binary_erosion(sign, iterations=1).astype(np.float32), 1.3) - 0.3) / 0.4, 0, 1)
    sg = np.dstack([clean, (soft * 255).astype(np.uint8)])

    tip_rows = np.where(body[380:430].any(axis=0))[0]
    tip = (int(tip_rows.max()), 405)
    return dict(char=Image.fromarray(char, "RGBA"), sign=Image.fromarray(sg, "RGBA"), tip=tip,
                char_box=Image.fromarray(char, "RGBA").getbbox(), sign_box=Image.fromarray(sg, "RGBA").getbbox())


# ───────────────────────────── hero clip frames ─────────────────────────────

def idle_frames(w: int, h: int, fps: int = 15, seconds: float = 2.0) -> tuple[list[Image.Image], float]:
    """Stand-in clip: a slow push-in on the office half-shot. Used only when no video is supplied."""
    n, frames, photo = round(fps * seconds), [], office()
    x0, y0, bw = 205, 70, 890
    bh = bw * h / w
    ax, ay = 650, 300                                     # zoom anchored on the face
    for i in range(n):
        e = 0.5 - 0.5 * math.cos(math.pi * i / (n - 1))
        z = 1 + 0.05 * e
        left, top = ax - (ax - x0) / z, ay - (ay - y0) / z
        frames.append(photo.transform((w, h), Image.EXTENT, (left, top, left + bw / z, top + bh / z), Image.BICUBIC))
    return frames, float(fps)


def _ffmpeg() -> str:
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    import imageio_ffmpeg  # bundled binary from PyPI, used when ffmpeg is not installed
    return imageio_ffmpeg.get_ffmpeg_exe()


def video_frames(path: Path, w: int, h: int, focus=(0.5, 0.32)) -> tuple[list[Image.Image], float]:
    """Extracts EVERY frame of the clip and cover-fits it to w x h (no frame is skipped or resampled in time)."""
    import re
    exe = _ffmpeg()
    probe = subprocess.run([exe, "-hide_banner", "-i", str(path)], capture_output=True, text=True).stderr
    fps = float(re.search(r"([\d.]+) fps", probe).group(1))
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([exe, "-v", "error", "-i", str(path), "-fps_mode", "passthrough", f"{tmp}/f_%05d.png"], check=True)
        frames = []
        for f in sorted(Path(tmp).glob("f_*.png")):
            im = Image.open(f).convert("RGB")
            s = max(w / im.width, h / im.height)
            im = im.resize((math.ceil(im.width * s), math.ceil(im.height * s)), Image.LANCZOS)
            left = round((im.width - w) * focus[0])
            top = round((im.height - h) * focus[1])
            frames.append(im.crop((left, top, left + w, top + h)))
    return frames, fps


def encode_jpegs(frames: list[Image.Image], budget: int) -> tuple[list[bytes], dict]:
    """Encodes all frames as JPEG, lowering quality (then resolution) until the total fits the byte budget."""
    scale = 1.0
    while True:
        size = (round(frames[0].width * scale), round(frames[0].height * scale))
        for quality in (82, 76, 70, 64, 58, 52, 46, 40):
            out = []
            for fr in frames:
                buf = io.BytesIO()
                (fr if scale == 1 else fr.resize(size, Image.LANCZOS)).save(buf, "JPEG", quality=quality, optimize=True, subsampling=2)
                out.append(buf.getvalue())
            total = sum(map(len, out))
            if total <= budget:
                return out, dict(quality=quality, size=size, total=total)
        scale *= 0.85
        if scale < 0.5:
            return out, dict(quality=quality, size=size, total=total)
