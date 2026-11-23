"""Guards the rules that keep the profile working on GitHub, plus the README and workflow wiring.

Static tests need nothing but Python. Browser tests render in headless Chromium (skipped when it is unavailable).
"""
from __future__ import annotations

import base64
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
ASSETS = ROOT / "assets"
PREFIX = {"hero.svg": "hero", "about-life.svg": "ab", "stack.svg": "st", "id-dashboard.svg": "id", "connect.svg": "cn", "contribute.svg": "co"}
ANIMATION_TAGS = {"animate", "animateTransform", "animateMotion", "set"}


def src(name: str) -> str:
    return (ASSETS / name).read_text(encoding="utf-8")


def tag(el: ET.Element) -> str:
    return el.tag.split("}")[-1]


@pytest.fixture(params=sorted(PREFIX))
def svg_name(request):
    return request.param


# ───────────────────────────── static: SVG rules ─────────────────────────────

def test_wellformed_with_dimensions(svg_name):
    root = ET.fromstring(src(svg_name))
    assert tag(root) == "svg" and root.get("viewBox") and root.get("width") == "900"


def test_no_scripts_network_or_external_references(svg_name):
    text = src(svg_name)
    assert "<script" not in text and "<foreignObject" not in text and "@import" not in text
    assert not re.search(r"https?://(?!www\.w3\.org/2000/svg)", text), "external URL found"
    for el in ET.fromstring(text).iter():
        href = el.get("href") or ""
        assert href == "" or href.startswith(("#", "data:")), f"non-local href {href[:40]}"


def test_images_are_png_or_jpeg_never_webp(svg_name):
    uris = re.findall(r'data:image/([a-z0-9+.-]+);base64,([A-Za-z0-9+/=]+)', src(svg_name))
    for mime, payload in uris:
        raw = base64.b64decode(payload)
        assert mime in {"png", "jpeg"}, f"{mime} not allowed"
        assert raw.startswith(b"\x89PNG") if mime == "png" else raw.startswith(b"\xff\xd8\xff")
    assert "image/webp" not in src(svg_name)


def test_fonts_are_embedded_woff2(svg_name):
    fonts = re.findall(r"url\(data:font/woff2;base64,([^)]+)\)", src(svg_name))
    assert all(base64.b64decode(f)[:4] == b"wOF2" for f in fonts)
    families = set(re.findall(r'@font-face\{font-family:"([^"]+)"', src(svg_name)))
    assert families == {"Bricolage", "Azeret"}, f"need display + mono, got {families}"
    assert not re.search(r"url\((?!data:|#)", src(svg_name)), "css url() must be data: or #id"


def test_ids_are_namespaced_unique_and_resolve(svg_name):
    text = src(svg_name)
    ids = re.findall(r'\bid="([^"]+)"', text)
    assert len(ids) == len(set(ids)), "duplicate ids"
    assert all(i.startswith(PREFIX[svg_name] + "-") for i in ids)
    refs = set(re.findall(r"url\(#([^)]+)\)", text)) | set(re.findall(r'href="#([^"]+)"', text))
    assert refs <= set(ids), f"dangling references: {refs - set(ids)}"


def test_smil_timelines_start_at_zero_with_valid_keytimes(svg_name):
    count = 0
    for el in ET.fromstring(src(svg_name)).iter():
        if tag(el) not in ANIMATION_TAGS:
            continue
        count += 1
        assert el.get("begin") in (None, "0s"), f"{tag(el)} begin={el.get('begin')}: delays belong in keyTimes"
        key_times, values = el.get("keyTimes"), el.get("values")
        if not key_times:
            continue
        kt, vals = [float(x) for x in key_times.split(";")], values.split(";")
        assert len(kt) == len(vals) and kt[0] == 0 and kt == sorted(kt) and kt[-1] <= 1
        if el.get("calcMode") != "discrete":
            assert kt[-1] == 1
        if el.get("keySplines"):
            assert len(el.get("keySplines").split(";")) == len(vals) - 1
    assert count >= 5


def test_css_entrances_use_fill_mode_both(svg_name):
    css = " ".join(el.text or "" for el in ET.fromstring(src(svg_name)).iter() if tag(el) == "style")
    declarations = [d for d in re.findall(r"animation:([^;}]+)", css) if not d.strip().startswith("none")]
    assert all(re.search(r"\bboth\b", d) for d in declarations)


def test_file_sizes_stay_readme_friendly(svg_name):
    limit = 1_200_000 if svg_name == "hero.svg" else 400_000
    assert (ASSETS / svg_name).stat().st_size < limit


def test_hero_frames_switch_with_smil():
    root = ET.fromstring(src("hero.svg"))
    frames = [el for el in root.iter() if tag(el) == "image" and "jpeg" in (el.get("href") or "")]
    assert len(frames) >= 2
    for frame in frames:
        anim = [c for c in frame if tag(c) == "animate"][0]
        assert anim.get("calcMode") == "discrete" and anim.get("dur") == "4s"


# ───────────────────────────── static: README and workflow ─────────────────────────────

def test_readme_images_are_cache_busted_and_exist():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    sources = re.findall(r'<img[^>]*\bsrc="([^"]+)"', readme)
    assert len(sources) == 7
    for source in sources:
        assert re.search(r"\?v=\d+$", source), f"{source} lacks a ?v= cache-buster"
        path = ROOT / source.split("?")[0]
        assert path.exists() or "profile-3d-contrib" in source, f"{source} missing"
    assert all('alt="' in m for m in re.findall(r"<img[^>]*>", readme))
    assert "profile-night-view.svg" in readme and "| **Flowra**" in readme and "contribute.svg" in readme
    for url in ("linkedin.com/in/jaykishandas", "instagram.com/jay_dev._._", "mailto:jaykishandas30@gmail.com", "github.com/VexoraTechnology"):
        assert url in readme, f"README is missing {url}"


def test_workflow_is_daily_pinned_and_safe():
    yaml = pytest.importorskip("yaml")
    workflow = yaml.safe_load((ROOT / ".github/workflows/profile-3d.yml").read_text())
    triggers = workflow.get("on", workflow.get(True))
    assert triggers["schedule"][0]["cron"].count(" ") == 4 and "workflow_dispatch" in triggers
    assert workflow["permissions"]["contents"] == "write"
    text = (ROOT / ".github/workflows/profile-3d.yml").read_text()
    assert "yoshi389111/github-profile-3d-contrib@v" in text and "@latest" not in text
    assert "USERNAME: ${{ github.repository_owner }}" in text and "git diff --cached --quiet" in text


def test_commit_count_reads_the_link_header():
    from profile_kit import github
    link = '<https://api.github.com/repositories/1/commits?per_page=1&page=2>; rel="next", <https://api.github.com/repositories/1/commits?per_page=1&page=34>; rel="last"'
    assert github.commit_count(link, [{}]) == 34 and github.commit_count(None, [{}]) == 1 and github.commit_count(None, None) == 0


# ───────────────────────────── browser: rendering ─────────────────────────────

@pytest.fixture(scope="module")
def chromium():
    sync_api = pytest.importorskip("playwright.sync_api")
    with sync_api.sync_playwright() as pw:
        try:
            browser = pw.chromium.launch()
        except Exception as exc:  # browsers not installed
            pytest.skip(f"Chromium unavailable: {exc}")
        yield browser
        browser.close()


def render(browser, name: str, t: float | None, static: bool = False, tmp: Path | None = None):
    """Screenshot at SMIL/CSS time t, or with every animation stripped; returns (array, blocked requests)."""
    from verify import SEEK_JS, strip_animation
    path = ASSETS / name
    if static:
        path = tmp / name
        path.write_text(strip_animation(src(name)))
    root = ET.fromstring(src(name))
    page = browser.new_page(viewport={"width": 900, "height": int(root.get("height"))})
    blocked = []
    page.route("**/*", lambda r: r.continue_() if r.request.url.startswith(("file:", "data:")) else (blocked.append(r.request.url), r.abort()))
    page.goto(path.resolve().as_uri())
    page.evaluate("document.fonts.ready.then(() => 1)")
    if t is not None:
        page.evaluate(SEEK_JS, t)
    page.wait_for_timeout(60)
    shot = page.screenshot()
    page.close()
    import io
    return np.array(Image.open(io.BytesIO(shot)).convert("RGB")).astype(int), blocked


def test_no_network_requests_at_any_time(chromium, svg_name):
    assert render(chromium, svg_name, 0.5)[1] == []


def test_static_fallback_is_a_finished_card(chromium, svg_name, tmp_path):
    arr, _ = render(chromium, svg_name, None, static=True, tmp=tmp_path)
    assert (arr.max(axis=2) > 150).mean() > 0.01, "static render looks empty"


def test_static_hero_shows_name_without_animation(chromium, tmp_path):
    arr, _ = render(chromium, "hero.svg", None, static=True, tmp=tmp_path)
    name_area = arr[116:196, 52:520]
    assert (name_area.max(axis=2) > 170).sum() > 4000, "name missing from the finished card"


def test_orbit_icons_are_not_piled_at_the_origin_without_smil(chromium, tmp_path):
    from verify import strip_animation
    path = tmp_path / "stack.svg"
    path.write_text(strip_animation(src("stack.svg")))
    page = chromium.new_page(viewport={"width": 900, "height": 700})
    page.goto(path.resolve().as_uri())
    centres = page.evaluate("[...document.querySelectorAll('use')].map(u => { const r = u.getBoundingClientRect(); return [r.x + r.width / 2, r.y + r.height / 2]; })")
    page.close()
    assert len(centres) >= 20 and all(x > 40 and y > 40 for x, y in centres)


def test_animation_moves_pixels_over_time(chromium, svg_name):
    a, _ = render(chromium, svg_name, 0.35)
    b, _ = render(chromium, svg_name, 2.9)
    assert np.abs(a - b).mean() > 0.4, "nothing changed between t=0.35s and t=2.9s"


def test_moons_never_touch_the_core(chromium):
    page = chromium.new_page(viewport={"width": 900, "height": 700})
    page.goto((ASSETS / "stack.svg").resolve().as_uri())
    page.evaluate("document.documentElement.pauseAnimations()")
    samples = page.evaluate("""(times) => { const s = document.documentElement, out = [];
        for (const t of times) { s.setCurrentTime(t); const c = document.querySelector('.core').getBoundingClientRect();
          for (const m of document.querySelectorAll('.moon')) { const r = m.getBoundingClientRect();
            out.push(Math.hypot(r.x + r.width / 2 - (c.x + c.width / 2), r.y + r.height / 2 - (c.y + c.height / 2)) - c.width / 2 - Math.max(r.width, r.height) / 2); } }
        return out; }""", [i * 0.5 for i in range(500)])
    page.close()
    assert len(samples) == 1000 and min(samples) > 12, f"closest approach {min(samples):.1f}px"


def text_boxes(browser, name: str, tmp: Path):
    """Bounding boxes of every <text> in the finished (animation-stripped) state."""
    from verify import strip_animation
    path = tmp / name
    path.write_text(strip_animation(src(name)))
    root = ET.fromstring(src(name))
    page = browser.new_page(viewport={"width": 900, "height": int(root.get("height"))})
    page.goto(path.resolve().as_uri())
    page.evaluate("document.fonts.ready.then(() => 1)")
    # odometer strips are meant to sit mostly outside their clip window, so only their window is judged by the clip
    boxes = page.evaluate("[...document.querySelectorAll('text')].filter(t => !t.closest('[clip-path*=\"reel\"]')).map(t => { const r = t.getBoundingClientRect(); return [t.textContent, r.left, r.top, r.right, r.bottom]; })")
    page.close()
    return boxes, int(root.get("height"))


def test_text_stays_inside_the_canvas(chromium, svg_name, tmp_path):
    boxes, height = text_boxes(chromium, svg_name, tmp_path)
    assert len(boxes) >= 5
    for text, left, top, right, bottom in boxes:
        assert left >= 6 and right <= 894 and top >= 3 and bottom <= height - 3, f"{text!r} spills: {left:.0f},{top:.0f},{right:.0f},{bottom:.0f}"


def test_hero_left_column_clears_the_viewfinder(chromium, tmp_path):
    boxes, _ = text_boxes(chromium, "hero.svg", tmp_path)
    left_column = [b for b in boxes if b[1] < 540]
    assert left_column and max(b[3] for b in left_column) <= 556, "left column crowds the viewfinder brackets"


def test_hero_cycles_through_every_role(chromium):
    """Regression: each role must actually appear in its slot (a child opacity once hid roles 2-4)."""
    for t in (2.0, 3.6, 6.2, 8.8):
        arr, _ = render(chromium, "hero.svg", t)
        role_area = arr[196:226, 52:360]
        assert (role_area.max(axis=2) > 170).sum() > 600, f"no role text visible at t={t}s"


def test_builds_are_byte_reproducible(tmp_path):
    """Two builds of the same content must be identical, so regenerating never creates noisy git diffs."""
    import hashlib
    import importlib
    from profile_kit import content as C
    first = [hashlib.sha256(importlib.import_module(f"profile_kit.{m}").build(C.github()).encode()).hexdigest() for m in ("connect", "about")]
    second = [hashlib.sha256(importlib.import_module(f"profile_kit.{m}").build(C.github()).encode()).hexdigest() for m in ("connect", "about")]
    assert first == second


# ───────────────────────────── content requests ─────────────────────────────

def texts(name: str) -> list[str]:
    return [el.text or "" for el in ET.fromstring(src(name)).iter() if tag(el) == "text"]


def test_no_engine_has_to_support_pathlength(svg_name):
    """pathLength on shapes is ignored by some engines (WebKit), so every dash uses a real length."""
    assert "pathLength" not in src(svg_name)


def test_hero_bottom_area_shows_skills_not_address_or_company():
    shown = texts("hero.svg")
    for skill in ("React", "TypeScript", "Flutter", "Node.js", "NestJS", "Firebase", "PostgreSQL", "Python", "TensorFlow"):
        assert skill in shown, f"hero is missing {skill}"
    assert not any("Balasore" in t or t == "Vexora Technology" for t in shown)
    assert src("hero.svg").count("<use ") >= 12, "each skill needs its logo"


def test_stack_covers_every_skill_from_the_screenshot():
    shown = set(texts("stack.svg"))
    screenshot = ["C", "Dart", "CSS3", "HTML5", "Java", "JavaScript", "Kotlin", "Python", "TypeScript", "Firebase", "Electron", "Express.js",
                  "Flask", "Flutter", "NestJS", "Node.js", "React Native", "React", "Apache Tomcat", "MySQL", "PostgreSQL", "Supabase",
                  "NumPy", "Pandas", "Plotly", "SciPy", "TensorFlow", "Matplotlib", "Git", "GitHub"]
    assert not [s for s in screenshot if s not in shown], f"missing: {[s for s in screenshot if s not in shown]}"


def test_id_badge_uses_the_half_shot_photo():
    root = ET.fromstring(src("id-dashboard.svg"))
    photos = [el for el in root.iter() if tag(el) == "image"]
    assert len(photos) == 1 and (photos[0].get("width"), photos[0].get("height")) == ("152", "176")


def test_connect_has_the_sign_and_all_four_links():
    shown = texts("connect.svg")
    for needed in ("GitHub", "Email", "LinkedIn", "Instagram", "github.com/VexoraTechnology", "jaykishandas30@gmail.com",
                   "linkedin.com/in/jaykishandas", "instagram.com/jay_dev._._"):
        assert needed in shown, f"connect is missing {needed}"
    assert len([el for el in ET.fromstring(src("connect.svg")).iter() if tag(el) == "image"]) == 2   # character + neon sign


def test_contribution_data_is_internally_consistent():
    from profile_kit import content as C
    gh = C.github()
    for repo in gh["repos"]:
        assert sum(repo["daily"].values()) == repo["commits"], repo["name"]
    assert gh["commits"] == sum(gh["per_day"].values()) and gh["streak"] >= 1
    shown = texts("contribute.svg")
    assert "Contributions" in shown and all(r["name"] in shown for r in gh["repos"])


def test_about_life_finished_state_shows_rows_rings_and_all_hobby_tabs(chromium, tmp_path):
    from profile_kit import content as C
    shown = texts("about-life.svg")
    for tab in (s["tab"] for s in C.SLIDES):
        assert tab in shown
    arr, _ = render(chromium, "about-life.svg", None, static=True, tmp=tmp_path)
    for k in range(3):                                           # each capability row has visible text
        y = 238 + k * 56
        assert (arr[y:y + 44, 80:420].max(axis=2) > 150).sum() > 300, f"capability row {k} not visible"
    ring_area = arr[322:372, 56:420]                              # all three rings are drawn in the finished state
    assert (ring_area.max(axis=2) > 120).sum() > 900
