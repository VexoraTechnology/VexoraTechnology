"""contribute.svg: how much I have contributed, and in which projects.

Card 1: count-up totals, a donut of each project's share of commits and a ranked list with bars.
Card 2: commits per day (stacked by project) over the whole period, plus a project-by-day activity grid.
Data comes from tools/data/github.json (real commit dates, UTC days like GitHub's own graph); every project keeps one
colour sampled from the aurora ramp across all charts.
"""
from __future__ import annotations

import math
from datetime import date, timedelta

from . import content as C
from .kit import CYAN, DIM, PINK, TEXT, VIOLET, Doc, animate, animate_transform, fmt, ramp

FILE = "contribute.svg"
W = 900
LOOP = 12.0
GRID_X, COLW, CELL_W = 190, 12.5, 9.5


def day_label(day: date) -> str:
    return f"{day.day} {day.strftime('%b')}"


def kpi_tiles(d: Doc, gh: dict, repos: list[dict]) -> str:
    """Four count-up tiles (odometer reels) across the top of card 1."""
    items = [("Commits", gh["commits"], ""), ("Projects", len(repos), ""), ("Active days", gh["active_days"], ""),
             ("Longest streak", gh["streak"], "days")]
    accents, tile_w, size, out = (CYAN, VIOLET, PINK, CYAN), 202, 32, []
    adv = d.w_of("m7", "0", size)
    for i, (label, value, suffix) in enumerate(items):
        x, digits = 28 + i * (tile_w + 12), str(value)
        out.append(f'<rect x="{x}" y="84" width="{tile_w}" height="78" rx="14" fill="#fff" fill-opacity=".035" stroke="#fff" stroke-opacity=".1"/>'
                   f'{d.t(label, "d5", x + 16, 108, 12, fill=DIM)}<rect x="{x + 16}" y="152" width="22" height="3" rx="1.5" fill="{accents[i]}"/>')
        for k, ch in enumerate(digits):
            out.append(d.reel(x + 16 + k * adv, 142, int(ch), size, .5 + i * .12, 1 if k == len(digits) - 1 else 0, LOOP))
        if suffix:
            out.append(d.t(suffix, "d5", x + 16 + len(digits) * adv + 8, 142, 14, fill=DIM))
    return "".join(out)


def donut(d: Doc, repos: list[dict], colors: list[str], total: int) -> str:
    """Share of commits per project. Arcs use real circumference lengths (no pathLength) and draw in one after another."""
    cx, cy, r, sw = 150, 272, 64, 24
    circ = 2 * math.pi * r
    gap, start, out = 2.2, 0.0, [f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#fff" stroke-opacity=".06" stroke-width="{sw}"/>']
    empty = f"0 {fmt(circ)}"
    for i, repo in enumerate(repos):
        share = repo["commits"] / total
        length = max(share * circ - gap, 1.0)
        dash = f"{fmt(length)} {fmt(circ - length)}"
        draw = animate("stroke-dasharray", [(0, empty), (.3 + i * .22, empty), (.9 + i * .22, dash), (11.2, dash), (11.7, empty)], LOOP, ease="out")
        out.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{colors[i]}" stroke-width="{sw}" stroke-dasharray="{dash}" '
                   f'stroke-dashoffset="{fmt(-start)}" transform="rotate(-90 {cx} {cy})">{draw}</circle>')
        start += share * circ
    out.append(d.t(str(total), "d8", cx, cy + 4, 34, fill=TEXT, anchor="middle") + d.t("commits", "d5", cx, cy + 26, 12, fill=DIM, anchor="middle"))
    return "".join(out)


def project_list(d: Doc, repos: list[dict], colors: list[str], total: int) -> str:
    """Ranked rows: colour dot, name, language, bar, commit count and share."""
    top, out = repos[0]["commits"], []
    for k, repo in enumerate(repos):
        y = 204 + k * 29
        w = max(4.0, 220 * repo["commits"] / top)
        grow = animate("width", [(0, 0), (.8 + k * .12, 0), (2.0 + k * .12, w)], LOOP, ease="out")
        share = round(100 * repo["commits"] / total)
        out.append(f'<circle cx="278" cy="{y}" r="5" fill="{colors[k]}"/>'
                   f'{d.t(repo["name"], "d7", 294, y + 5, 14, fill=TEXT)}{d.t(repo["language"], "d5", 452, y + 4.5, 12, fill=DIM)}'
                   f'<rect x="548" y="{y - 4}" width="220" height="8" rx="4" fill="#fff" fill-opacity=".07"/>'
                   f'<rect x="548" y="{y - 4}" width="{fmt(w)}" height="8" rx="4" fill="{colors[k]}">{grow}</rect>'
                   f'{d.t(str(repo["commits"]), "m7", 806, y + 4.5, 13, fill=TEXT, anchor="end")}'
                   f'{d.t(f"{share}%", "d5", 872, y + 4.5, 12, fill=DIM, anchor="end")}')
    return "".join(out)


def overview(d: Doc, gh: dict, repos: list[dict], colors: list[str]) -> str:
    total = sum(r["commits"] for r in repos)
    head = (d.t("Contributions", "d8", 28, 46, 24, fill=TEXT)
            + d.t(f"Commits in my repositories, {day_label(gh['first_day'])} to {day_label(gh['last_day'])} {gh['last_day'].year}", "d5", 28, 67, 12.5, fill=DIM))
    fade = animate("opacity", [(0, 0), (.4, 1), (11.3, 1), (11.8, 0)], LOOP)
    return f'<g>{fade}{head}{kpi_tiles(d, gh, repos)}{donut(d, repos, colors, total)}{project_list(d, repos, colors, total)}</g>'


def activity(d: Doc, gh: dict, repos: list[dict], colors: list[str]) -> tuple[str, int]:
    """Stacked commits per day, month ticks, a project-by-day grid and a scanning highlight."""
    first, end = gh["first_day"], gh["fetched_date"]
    n_days = (end - first).days + 1
    colw = min(64.0, max(COLW, 660.0 / max(n_days, 1)))
    cell_w = min(24.0, colw * 0.76) if colw > COLW else CELL_W
    x_of = lambda i: GRID_X + i * colw
    base, tallest = 172, 84
    peak = max(gh["per_day"].values())
    scale = tallest / peak
    out = [d.t("Daily activity", "d7", 28, 40, 17, fill=TEXT)]

    # legend (intensity steps)
    out.append(d.t("Less", "d5", 724, 36, 11, fill=DIM, anchor="end"))
    for k, op in enumerate((.06, .38, .58, .8, 1)):
        out.append(f'<rect x="{732 + k * 15}" y="27" width="11" height="11" rx="3" fill="#fff" fill-opacity="{op}"/>')
    out.append(d.t("More", "d5", 812, 36, 11, fill=DIM))

    # gridlines and axis labels
    for v in sorted({0, peak // 2, peak}):
        y = base - v * scale
        out.append(f'<path d="M{GRID_X} {fmt(y)}H{fmt(x_of(n_days))}" stroke="#fff" stroke-opacity="{.22 if v == 0 else .07}" stroke-dasharray="{"0" if v == 0 else "2 5"}"/>'
                   + d.t(str(v), "m4", GRID_X - 10, y + 3.5, 10.5, fill=DIM, anchor="end"))
    out.append(d.t("commits per day", "d5", 28, base - tallest / 2 + 4, 12, fill=DIM))

    # stacked bars (one segment per project per day)
    by_day: dict[int, list[tuple[int, int]]] = {}
    for ri, repo in enumerate(repos):
        for day, n in repo.get("daily", {}).items():
            by_day.setdefault((date.fromisoformat(day) - first).days, []).append((ri, n))
    seg_order = 0
    for idx in sorted(by_day):
        stack = 0.0
        for ri, n in sorted(by_day[idx]):
            h, y = max(n * scale - 1, 2), base - stack - n * scale + .5
            t0 = .6 + seg_order * .045
            grow = animate("height", [(0, 0), (t0, 0), (t0 + .7, h), (11.2, h), (11.7, 0)], LOOP, ease="out")
            rise = animate("y", [(0, base), (t0, base), (t0 + .7, y), (11.2, y), (11.7, base)], LOOP, ease="out")
            out.append(f'<rect x="{fmt(x_of(idx) + (colw - cell_w) / 2)}" y="{fmt(y)}" width="{fmt(cell_w)}" height="{fmt(h)}" rx="2" fill="{colors[ri]}">{grow}{rise}</rect>')
            stack += n * scale
            seg_order += 1

    # busiest day callout
    best_day, best_n = gh["busiest"]
    bi = (date.fromisoformat(best_day) - first).days
    callout = f"{best_n} {'commit' if best_n == 1 else 'commits'} on {day_label(date.fromisoformat(best_day))}"
    if bi > 0 and x_of(bi) - GRID_X >= d.w_of("d7", callout, 11.5) + 22:
        tx, ty, anchor = x_of(bi) - 8, base - best_n * scale + 11, "end"
    else:
        tx, ty, anchor = x_of(bi) + (colw - cell_w) / 2, base - tallest - 10, "start"
    out.append(d.t(callout, "d7", tx, ty, 11.5, fill=TEXT, anchor=anchor))

    # month ticks along the bottom
    ticks = [(0, day_label(first), "start")]
    day = first
    while day <= end:
        if day.day == 1 and day != first:
            ticks.append(((day - first).days, f"1 {day.strftime('%b')}", "start"))
        day += timedelta(days=1)
    if n_days > 1:
        ticks.append((n_days - 1, day_label(end), "end"))
    for idx, label, anchor in ticks:
        out.append(f'<path d="M{fmt(x_of(idx) + colw / 2)} {base}v5" stroke="#fff" stroke-opacity=".3"/>'
                   + d.t(label, "d5", x_of(idx) + (0 if anchor == "start" else colw), base + 20, 11, fill=DIM, anchor=anchor))

    # project-by-day grid
    row0, pitch = base + 46, 25
    out.append(d.t("Where the commits went", "d7", 28, row0 - 14, 12.5, fill=DIM))
    for ri, repo in enumerate(repos):
        y = row0 + ri * pitch
        out.append(f'<circle cx="34" cy="{y + 8}" r="4" fill="{colors[ri]}"/>{d.t(repo["name"], "d5", 46, y + 12.5, 12.5, fill=TEXT)}')
        daily = {(date.fromisoformat(k) - first).days: v for k, v in repo.get("daily", {}).items()}
        for i in range(n_days):
            n = daily.get(i, 0)
            if not n:
                out.append(f'<rect x="{fmt(x_of(i) + (colw - cell_w) / 2)}" y="{y}" width="{fmt(cell_w)}" height="16" rx="3" fill="#fff" fill-opacity=".05"/>')
                continue
            level = .4 if n == 1 else .6 if n <= 3 else .82 if n <= 6 else 1
            t0 = .5 + i * .05
            appear = animate("opacity", [(0, 0), (t0, 0), (t0 + .35, level), (11.2, level), (11.7, 0)], LOOP, ease="out")
            out.append(f'<rect x="{fmt(x_of(i) + (colw - cell_w) / 2)}" y="{y}" width="{fmt(cell_w)}" height="16" rx="3" fill="{colors[ri]}" opacity="{level}">{appear}</rect>')
    grid_bottom = row0 + (len(repos) - 1) * pitch + 16

    # scanning highlight sweeping across the whole chart
    sweep = animate_transform("translate", [(0, "0 0"), (8, f"{fmt(n_days * colw)} 0")], 8)
    out.append(f'<rect x="{GRID_X}" y="{base - tallest - 6}" width="{fmt(colw)}" height="{fmt(grid_bottom - (base - tallest - 6) + 4)}" rx="3" fill="#fff" opacity=".07">{sweep}</rect>')
    fade = animate("opacity", [(0, 0), (.4, 1), (11.3, 1), (11.8, 0)], LOOP)
    return f'<g>{fade}{"".join(out)}</g>', int(grid_bottom + 26)


def build(gh: dict) -> str:
    repos = sorted((r for r in gh["repos"] if r["commits"]), key=lambda r: r["commits"], reverse=True)
    colors = ramp(len(repos))
    total = sum(r["commits"] for r in repos)
    d = Doc("co", W, 10, "Contributions by project",
            f"{total} {'commit' if total == 1 else 'commits'} across {len(repos)} {'project' if len(repos) == 1 else 'projects'} between {day_label(gh['first_day'])} and {day_label(gh['last_day'])}, on {gh['active_days']} active {'day' if gh['active_days'] == 1 else 'days'}; "
            + ", ".join(f"{r['name']} {r['commits']}" for r in repos) + ".")
    card1_h = 372
    body2, card2_h = activity(d, gh, repos, colors)
    d.h = card1_h + 16 + card2_h
    d.body.append(d.card(0, 0, W, card1_h, overview(d, gh, repos, colors), auras=(("c", .05, .0, .7, 19), ("p", .98, .95, .6, 23))))
    d.body.append(d.card(0, card1_h + 16, W, card2_h, body2, auras=(("v", .02, 1.0, .6, 21), ("c", .98, .0, .5, 17))))
    return d.svg()
