"""Refreshes tools/data/github.json from the GitHub REST API.

Why a snapshot: SVGs cannot fetch anything at view time, so the numbers they show are baked in at build time.
Unauthenticated calls are capped at 60 per hour per IP, so set GITHUB_TOKEN for anything beyond a quick refresh.
"""
from __future__ import annotations

import json
import os
import collections
import re
import subprocess
import tempfile
import urllib.error
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

from . import content as C

API = "https://api.github.com"


def _get(path: str, token: str | None):
    """GET returning (json, headers); a 409 (empty repository) is reported as (None, {})."""
    req = urllib.request.Request(API + path, headers={"Accept": "application/vnd.github+json", "User-Agent": "profile-build",
                                                      **({"Authorization": f"Bearer {token}"} if token else {})})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp), resp.headers
    except urllib.error.HTTPError as err:
        if err.code == 409:
            return None, {}
        raise SystemExit(f"GitHub API {err.code} for {path}: {err.reason} (set GITHUB_TOKEN to lift the rate limit)")


def commit_count(link_header: str | None, first_page: list | None) -> int:
    """With per_page=1 the 'last' page number in the Link header equals the commit count."""
    if link_header:
        match = re.search(r'[?&]page=(\d+)>; rel="last"', link_header)
        if match:
            return int(match.group(1))
    return len(first_page or [])


def daily_commits(login: str, name: str, work: Path) -> tuple[dict, collections.Counter]:
    """Per-day commit counts (UTC, matching GitHub's own graph) via a metadata-only bare clone: no file contents are downloaded."""
    path = work / f"{name}.git"
    subprocess.run(["git", "clone", "-q", "--bare", "--filter=blob:none", "--no-tags", f"https://github.com/{login}/{name}.git", str(path)],
                   check=True, timeout=180)
    log = subprocess.run(["git", "--git-dir", str(path), "log", "--format=%aI|%an"], capture_output=True, text=True, check=True).stdout
    days, authors = collections.Counter(), collections.Counter()
    for line in filter(None, log.split("\n")):
        stamp, author = line.split("|", 1)
        days[datetime.fromisoformat(stamp).astimezone(timezone.utc).date().isoformat()] += 1
        authors[author] += 1
    return dict(sorted(days.items())), authors


def refresh(login: str = C.HANDLE, token: str | None = None) -> dict:
    """Pulls the profile and every public, non-fork repository, then writes the snapshot used by the builds."""
    token = token or os.environ.get("GITHUB_TOKEN")
    user, _ = _get(f"/users/{login}", token)
    repos, page = [], 1
    while True:
        batch, _ = _get(f"/users/{login}/repos?per_page=100&type=owner&page={page}", token)
        repos += batch
        if len(batch) < 100:
            break
        page += 1
    rows, authors = [], collections.Counter()
    with tempfile.TemporaryDirectory() as tmp:
        for r in (r for r in repos if not r["fork"]):
            first, headers = _get(f"/repos/{login}/{r['name']}/commits?per_page=1", token)
            try:
                daily, who = daily_commits(login, r["name"], Path(tmp))
            except (subprocess.SubprocessError, OSError):
                daily, who = {}, collections.Counter()   # empty or unreachable repo: keep the counts, skip the calendar
            authors.update(who)
            rows.append(dict(name=r["name"], language=r["language"] or "Other", stars=r["stargazers_count"], forks=r["forks_count"],
                             commits=commit_count(headers.get("Link") if headers else None, first), created=r["created_at"][:10], daily=daily))
    snap = dict(fetched=date.today().isoformat(), source="GitHub REST API plus metadata-only git clones", authors=dict(authors.most_common()),
                profile=dict(login=user["login"], public_repos=user["public_repos"], followers=user["followers"], joined=user["created_at"][:10]),
                repos=sorted(rows, key=lambda r: r["name"].lower()))
    (C.DATA / "github.json").write_text(json.dumps(snap, indent=1))
    return snap
