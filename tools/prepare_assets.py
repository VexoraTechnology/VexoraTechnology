"""One-off helper: copies the font sources and Simple Icons paths the build needs into tools/assets.

Why: the build must run offline and reproducibly, so fonts and icon paths are committed.
Run only when fonts or icons change:  npm i simple-icons @fontsource/azeret-mono @fontsource-variable/bricolage-grotesque
"""
import json
import os
import shutil
import subprocess
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
NODE_MODULES = Path(os.environ.get("NODE_MODULES", TOOLS / "node_modules"))
OUT = TOOLS / "assets"

# Every Simple Icons slug the SVGs use (Java ships as "openjdk"; CSS3 as "css").
SLUGS = [
    "c", "dart", "kotlin", "flask", "nestjs", "electron", "apachetomcat", "postgresql", "numpy", "pandas", "plotly",
    "scipy", "tensorflow", "instagram", "html5", "css", "javascript", "typescript", "react", "tailwindcss", "threedotjs",
    "greensock", "framer", "nodedotjs", "express", "firebase", "supabase", "mysql", "python", "scikitlearn", "opencv",
    "fastapi", "git", "github", "openjdk", "flutter", "gmail",
]

# Marks Simple Icons no longer ships (or never had), drawn here so every brand still gets a real glyph.
CUSTOM = {
    "linkedin": {"title": "LinkedIn", "hex": "0A66C2", "path": (
        "M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046"
        "c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 "
        "2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 "
        ".774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z")},
    "matplotlib": {"title": "Matplotlib", "hex": "5B9BD5", "path": (
        "M12 2a10 10 0 1 1 0 20 10 10 0 0 1 0-20zM12 4.4a7.6 7.6 0 1 0 0 15.2 7.6 7.6 0 0 0 0-15.2zM7.2 15.2h2.2v2.4H7.2z"
        "M10.9 11.4h2.2v6.2h-2.2zM14.6 13.4h2.2v4.2h-2.2z")},
    "antigravity": {"title": "Antigravity", "hex": "8AB4F8", "path": (
        "M12 1.5c.5 4.2 2.1 6.1 8.5 8.5-6.4 2.4-8 4.3-8.5 8.5-.5-4.2-2.1-6.1-8.5-8.5 6.4-2.4 8-4.3 8.5-8.5z")},
}

DUMP_JS = """
import * as si from 'simple-icons';
const want = new Set(JSON.parse(process.argv[1]));
const out = {};
for (const i of Object.values(si)) if (i && i.slug && want.has(i.slug)) out[i.slug] = {title: i.title, hex: i.hex, path: i.path};
console.log(JSON.stringify(out));
"""


def copy_fonts() -> None:
    """Copies the variable Bricolage Grotesque and the two Azeret Mono weights."""
    fonts = OUT / "fonts"
    fonts.mkdir(parents=True, exist_ok=True)
    pairs = {
        NODE_MODULES / "@fontsource-variable/bricolage-grotesque/files/bricolage-grotesque-latin-standard-normal.woff2":
            "bricolage-grotesque-standard.woff2",
        NODE_MODULES / "@fontsource/azeret-mono/files/azeret-mono-latin-400-normal.woff2": "azeret-mono-400.woff2",
        NODE_MODULES / "@fontsource/azeret-mono/files/azeret-mono-latin-700-normal.woff2": "azeret-mono-700.woff2",
    }
    for src, name in pairs.items():
        shutil.copy(src, fonts / name)


def dump_icons() -> None:
    """Writes {slug: {title, hex, path}} for the icons above; Simple Icons is CC0."""
    result = subprocess.run(
        ["node", "--input-type=module", "-e", DUMP_JS, json.dumps(SLUGS)],
        cwd=NODE_MODULES.parent, capture_output=True, text=True, check=True,
    )
    icons = json.loads(result.stdout)
    missing = sorted(set(SLUGS) - set(icons))
    if missing:
        raise SystemExit(f"Simple Icons is missing: {missing}")
    icons.update(CUSTOM)
    icons["reactnative"] = {**icons["react"], "title": "React Native"}   # same atom mark, its own label
    (OUT / "icons.json").write_text(json.dumps(icons, indent=1))
    print(f"icons: {len(icons)}")


def measure_glyphs() -> None:
    """Measures every line-icon path once (browser getTotalLength) so draw-in animations use real lengths, never pathLength."""
    from playwright.sync_api import sync_playwright
    import sys
    sys.path.insert(0, str(TOOLS))
    from profile_kit.glyphs import LINES
    paths = "".join(f'<path id="{n}-{i}" d="{d}"/>' for n, ds in LINES.items() for i, d in enumerate(ds))
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(f'<svg xmlns="http://www.w3.org/2000/svg">{paths}</svg>')
        lengths = page.evaluate("Object.fromEntries([...document.querySelectorAll('path')].map(p => [p.id, +p.getTotalLength().toFixed(2)]))")
        browser.close()
    (OUT / "glyph_lengths.json").write_text(json.dumps(lengths, indent=1))
    print(f"glyph lengths: {len(lengths)}")


if __name__ == "__main__":
    import sys
    if "--measure" in sys.argv:
        measure_glyphs()
    else:
        copy_fonts()
        dump_icons()
