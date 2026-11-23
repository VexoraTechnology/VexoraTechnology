"""Everything personal lives here: edit this file, run `python tools/build.py`, done."""
from __future__ import annotations

import collections
import json
from datetime import date, timedelta
from pathlib import Path

from .kit import CYAN, PINK, VIOLET

DATA = Path(__file__).resolve().parents[1] / "data"

NAME = "Jaykishan Das"
HANDLE = "Itzjay169"
ROLE = "Full Stack Web Developer"
COMPANY = "Vexora Technology"
LOCATION = "Balasore, Odisha, India"
EMAIL = "jaykishandas30@gmail.com"
GITHUB = "https://github.com/VexoraTechnology"
LINKEDIN = "https://www.linkedin.com/in/jaykishandas"
INSTAGRAM = "https://www.instagram.com/jay_dev._._"

# Connect cards: (icon slug, title, visible text, url). Order = order on the page.
LINKS = [
    ("github", "GitHub", "github.com/VexoraTechnology", GITHUB),
    ("gmail", "Email", EMAIL, f"mailto:{EMAIL}"),
    ("linkedin", "LinkedIn", "linkedin.com/in/jaykishandas", LINKEDIN),
    ("instagram", "Instagram", "instagram.com/jay_dev._._", INSTAGRAM),
]

# Cycling role lines in the hero (first one is the finished-card default).
ROLES = [ROLE, "AI-powered app builder", "Desktop software developer", "UI/UX tinkerer"]
PITCH = "I turn random ideas into full-stack apps, AI tools and desktop software."

# Hero bottom area: three columns of skills, each with its logo. (label, Simple Icons slug)
HERO_SKILLS = [
    ("Frontend", [("React", "react"), ("TypeScript", "typescript"), ("Flutter", "flutter"), ("CSS3", "css")]),
    ("Backend", [("Node.js", "nodedotjs"), ("Express.js", "express"), ("NestJS", "nestjs"), ("Flask", "flask")]),
    ("Data and AI", [("Firebase", "firebase"), ("PostgreSQL", "postgresql"), ("Python", "python"), ("TensorFlow", "tensorflow")]),
]

# Orbit icons by slug. Moons circle the React icon (React Native shares React's mark, so it stays in the chips).
ORBITS = [
    dict(a=150, b=58, tilt=-24, period=16, clockwise=True, icons=["html5", "css", "javascript", "git"]),
    dict(a=234, b=94, tilt=16, period=26, clockwise=False, icons=["nodedotjs", "express", "firebase", "postgresql", "github"]),
    dict(a=330, b=128, tilt=-6, period=38, clockwise=True, icons=["react", "openjdk", "flutter", "python", "tensorflow"]),
]
MOONS = ["typescript", "electron"]
HOST = "react"

# Chip grid, two rows of four groups. Everything in the tech-stack screenshot appears here once.
CHIPS = {
    "Languages": [("C", "c"), ("Dart", "dart"), ("Java", "openjdk"), ("JavaScript", "javascript"), ("Kotlin", "kotlin"),
                  ("Python", "python"), ("TypeScript", "typescript")],
    "Frontend": [("HTML5", "html5"), ("CSS3", "css"), ("React", "react"), ("Tailwind CSS", "tailwindcss")],
    "Motion and 3D": [("Three.js", "threedotjs"), ("GSAP", "greensock"), ("Framer Motion", "framer")],
    "Mobile and desktop": [("Flutter", "flutter"), ("React Native", "reactnative"), ("Electron", "electron")],
    "Backend": [("Node.js", "nodedotjs"), ("Express.js", "express"), ("NestJS", "nestjs"), ("Flask", "flask"),
                ("FastAPI", "fastapi"), ("Apache Tomcat", "apachetomcat")],
    "Data": [("Firebase", "firebase"), ("Supabase", "supabase"), ("PostgreSQL", "postgresql"), ("MySQL", "mysql")],
    "AI and data science": [("TensorFlow", "tensorflow"), ("NumPy", "numpy"), ("Pandas", "pandas"), ("SciPy", "scipy"),
                            ("Plotly", "plotly"), ("Matplotlib", "matplotlib"), ("scikit-learn", "scikitlearn"), ("OpenCV", "opencv")],
    "Tools": [("Git", "git"), ("GitHub", "github"), ("Antigravity", "antigravity")],
}

# Capability rows beside the browser illustration (about-life.svg).
CAPABILITIES = [
    ("layout", "Frontend and UI/UX", "React.js, HTML5, CSS3 and responsive layouts"),
    ("server", "Backend and APIs", "Node.js, Express.js, Firebase and REST integrations"),
    ("sparkle", "AI and desktop apps", "AI-powered tools, plus Java and Electron software"),
]

# Hobby carousel: the hobby is building random projects, shown through four things actually built.
SLIDES = [
    dict(tab="Random projects", kind="spark", title="Building random projects", sub="Pick an idea, open the editor, see what ships."),
    dict(tab="Trading desk", kind="voice", title="A trading desk that listens", sub="F.R.I.D.A.Y, a voice-driven multi-agent AI desk (paper trading only)."),
    dict(tab="Study locks", kind="phone", title="Study locks and expense logs", sub="Flowra, an offline-first Flutter planner with zero cloud and zero ads."),
    dict(tab="Classifier", kind="forest", title="Teaching a tracker to sort", sub="Finflow's Random Forest classifier: 95.83% on 240 unseen rows."),
]
RINGS = [("code", "Build", CYAN, 100), ("book", "Learn", VIOLET, 72), ("rocket", "Ship", PINK, 88)]

NOW = [
    ("Shipping", "Flowra v1.2.0, an offline-first Flutter planner"),
    ("Building", "F.R.I.D.A.Y 2.0, a voice-driven AI desk"),
    ("Exploring", "AI-powered apps and desktop software at Vexora Technology"),
]


def github() -> dict:
    """Loads the committed GitHub snapshot and derives every number the SVGs show."""
    snap = json.loads((DATA / "github.json").read_text())
    repos = snap["repos"]
    stars = sum(r["stars"] for r in repos)
    commits = sum(r["commits"] for r in repos)
    fetched = date.fromisoformat(snap["fetched"])
    joined = date.fromisoformat(snap["profile"]["joined"])
    # With no stars yet the chart falls back to commits; it switches to stars automatically.
    metric = "stars" if stars else "commits"
    ranked = sorted(repos, key=lambda r: (r[metric], r["commits"]), reverse=True)

    per_day = collections.Counter()
    for r in repos:
        per_day.update(r.get("daily", {}))
    active = sorted(date.fromisoformat(d) for d in per_day)
    streak = best = 0
    for i, day in enumerate(active):
        streak = streak + 1 if i and (day - active[i - 1]).days == 1 else 1
        best = max(best, streak)
    busiest = max(per_day.items(), key=lambda kv: kv[1]) if per_day else (None, 0)
    return dict(snap=snap, repos=repos, ranked=ranked, stars=stars, commits=commits, metric=metric,
                days=(fetched - joined).days, public_repos=snap["profile"]["public_repos"],
                languages=len({r["language"] for r in repos}), fetched=fetched.strftime("%d %b %Y").lstrip("0"),
                fetched_date=fetched, per_day=dict(per_day), active_days=len(active), streak=best,
                first_day=active[0] if active else fetched, last_day=active[-1] if active else fetched,
                busiest=busiest, authors=snap.get("authors", {}))
