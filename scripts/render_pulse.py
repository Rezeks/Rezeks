#!/usr/bin/env python3
"""Render the "pulse" card: streaks, weekly rhythm and recently pushed projects.

Run after contribution_data.py. Uses the saved calendar snapshot plus the public
repository list (GITHUB_TOKEN is optional). If anything fails, the previous
cards are kept untouched.
"""

from collections import Counter
from datetime import date, datetime, timedelta, timezone
from html import escape
import json
import os
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

from contribution_data import validate_days

USERNAME = "Rezeks"
ASSETS = Path(__file__).resolve().parents[1] / "assets"
INPUT = ASSETS / "activity.json"
OUTPUT = ASSETS / "pulse.svg"
MOBILE_OUTPUT = ASSETS / "pulse-mobile.svg"
FONT = "Segoe UI, Helvetica, Arial, sans-serif"
MONO = "'Cascadia Code', Consolas, 'Liberation Mono', monospace"
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
LANGUAGE_COLORS = {
    "TypeScript": "#64d9e8", "JavaScript": "#f6c177", "Python": "#b8a5ff",
    "Java": "#ff9e7a", "Go": "#7fdbca", "Jupyter Notebook": "#f6a6c8",
}
ACCENT = "#c8ff5f"
MUTED = "#a3b0bf"
INK = "#eef2f6"
LINE = "#29323d"


def recent_repositories(limit=3):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "Rezeks-profile-pulse",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token := os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {token}"
    request = Request(f"https://api.github.com/users/{USERNAME}/repos?type=owner&sort=pushed&per_page=30", headers=headers)
    with urlopen(request, timeout=30) as response:
        repos = json.load(response)
    if not isinstance(repos, list):
        raise ValueError("GitHub returned an unexpected repository response")
    result = []
    for repo in repos:
        if not isinstance(repo, dict) or repo.get("private") is not False or repo.get("fork") is not False:
            continue
        name = repo.get("name")
        if not isinstance(name, str) or name.lower() == USERNAME.lower():
            continue
        pushed = datetime.fromisoformat(repo["pushed_at"].replace("Z", "+00:00")).date()
        result.append({
            "name": name,
            "language": repo.get("language") or "Code",
            "description": (repo.get("description") or "").strip(),
            "pushed": pushed,
        })
        if len(result) == limit:
            break
    return result


def rhythm(days):
    longest = run = 0
    best_start = best_end = None
    run_start = None
    for day in days:
        if day["count"]:
            run += 1
            run_start = run_start or day["date"]
            if run > longest:
                longest, best_start, best_end = run, run_start, day["date"]
        else:
            run, run_start = 0, None
    weekday = Counter()
    for day in days:
        weekday[date.fromisoformat(day["date"]).weekday()] += day["count"]
    weeks = Counter()
    for day in days:
        if day["count"]:
            weeks[date.fromisoformat(day["date"]).isocalendar()[:2]] += 1
    active = [d for d in days if d["count"]]
    return {
        "longest": longest,
        "longest_range": (best_start, best_end),
        "weekday": [weekday[i] for i in range(7)],
        "best_weekday": max(range(7), key=lambda i: (weekday[i], -i)),
        "active_weeks": len(weeks),
        "total_weeks": len({date.fromisoformat(d["date"]).isocalendar()[:2] for d in days}),
        "last_active": active[-1]["date"] if active else None,
    }


def short_date(value):
    if isinstance(value, str):
        value = date.fromisoformat(value)
    return value.strftime("%b %d").replace(" 0", " ")


def clip(value, size):
    return value if len(value) <= size else value[: size - 1].rstrip() + "…"


def text(x, y, value, size=13, color=MUTED, extra=""):
    return f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" {extra}>{escape(str(value))}</text>'


STYLE = (
    "<style>"
    ".bar{transform-box:fill-box;transform-origin:bottom;animation:grow 1.4s cubic-bezier(.2,.8,.2,1) both}"
    ".row{animation:fade 1s ease-out both}"
    ".beat{animation:beat 2.4s ease-in-out infinite}"
    ".ecg{stroke-dasharray:620;animation:ecg 6s linear infinite}"
    "@keyframes grow{from{transform:scaleY(.04)}to{transform:scaleY(1)}}"
    "@keyframes fade{from{opacity:0;transform:translateX(12px)}to{opacity:1;transform:none}}"
    "@keyframes beat{0%,100%{opacity:.35}50%{opacity:1}}"
    "@keyframes ecg{from{stroke-dashoffset:620}to{stroke-dashoffset:-620}}"
    "@media(prefers-reduced-motion:reduce){.bar,.row,.beat,.ecg{animation:none}}"
    "</style>"
)


def head(width, height, data, repos):
    first, last = data["longest_range"]
    desc = (
        f"Longest streak {data['longest']} days"
        + (f" ({first} to {last})" if first else "")
        + f". Active in {data['active_weeks']} of {data['total_weeks']} weeks. "
        f"Most productive weekday: {WEEKDAY_NAMES[data['best_weekday']]}. "
        "Recently pushed: " + ", ".join(r["name"] for r in repos) + "."
    )
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Rezeks — coding rhythm and recent projects</title>',
        f'<desc id="desc">{escape(desc)}</desc>',
        '<defs><linearGradient id="pulse-bar" x1="0" y1="0" x2="0" y2="1">'
        f'<stop stop-color="{ACCENT}"/><stop offset="1" stop-color="{ACCENT}" stop-opacity=".25"/></linearGradient>'
        '<linearGradient id="pulse-edge" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#4f6a33"/>'
        '<stop offset=".5" stop-color="#29333f"/><stop offset="1" stop-color="#5d4f7a"/></linearGradient>'
        f"{STYLE}</defs>",
        f'<rect x=".5" y=".5" width="{width-1}" height="{height-1}" rx="18" fill="#0d1117" stroke="url(#pulse-edge)"/>',
        f'<g font-family="{FONT}">',
    ]


def ecg(x, y, width):
    beat = [(0, 0), (.38, 0), (.42, -6), (.46, 5), (.5, -22), (.54, 14), (.58, 0), (1, 0)]
    pts = " ".join(f"{x + width * px:.1f},{y + py:.1f}" for px, py in beat)
    return (f'<polyline points="{pts}" fill="none" stroke="{LINE}" stroke-width="1.5"/>'
            f'<polyline class="ecg" points="{pts}" fill="none" stroke="{ACCENT}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>')


def weekday_bars(data, x, y, width, height, label_size):
    peak = max(data["weekday"]) or 1
    slot = width / 7
    bar = slot * .56
    out = []
    for i, value in enumerate(data["weekday"]):
        h = max(3.0, height * value / peak)
        bx = x + i * slot + (slot - bar) / 2
        best = i == data["best_weekday"] and value > 0
        fill = "url(#pulse-bar)" if best else "#2b3a45"
        out.append(f'<rect x="{bx:.1f}" y="{y + height - h:.1f}" width="{bar:.1f}" height="{h:.1f}" rx="4" fill="{fill}" '
                   f'class="bar" style="animation-delay:{i * .08:.2f}s"><title>{WEEKDAY_NAMES[i]}: {value} contributions</title></rect>')
        out.append(text(f"{bx + bar / 2:.1f}", y + height + label_size + 8, WEEKDAYS[i], label_size,
                        INK if best else MUTED, 'text-anchor="middle"'))
    return out


def repo_rows(repos, x, y, width, gap, name_size, meta_size, desc_chars):
    out = []
    for i, repo in enumerate(repos):
        ry = y + i * gap
        color = LANGUAGE_COLORS.get(repo["language"], "#768597")
        out.append(f'<g class="row" style="animation-delay:{.2 + i * .15:.2f}s">')
        out.append(f'<rect x="{x}" y="{ry}" width="{width}" height="{gap - 10}" rx="10" fill="#10171f" stroke="#25323d"/>')
        out.append(f'<rect x="{x}" y="{ry + 12}" width="3" height="{gap - 34}" rx="1.5" fill="{color}"/>')
        out.append(text(x + 18, ry + name_size + 10, clip(repo["name"], 26), name_size, INK, 'font-weight="600"'))
        out.append(text(x + width - 16, ry + name_size + 10, short_date(repo["pushed"]), meta_size, MUTED,
                        f'text-anchor="end" font-family="{MONO}"'))
        meta = repo["language"] + (" · " + clip(repo["description"], desc_chars) if repo["description"] else "")
        out.append(text(x + 18, ry + name_size + meta_size + 18, meta, meta_size, MUTED))
        out.append("</g>")
    if not repos:
        out.append(text(x, y + 20, "No public pushes yet", meta_size))
    return out


def render(data, repos):
    svg = head(960, 300, data, repos)
    svg += [
        text(32, 40, "Rhythm & pulse.", 19, INK, 'font-weight="600"'),
        f'<circle class="beat" cx="794" cy="33" r="3" fill="{ACCENT}"/>',
        text(807, 37, "LAST 12 MONTHS", 10, MUTED, 'letter-spacing="1.8"'),
        ecg(200, 34, 150),
    ]
    metrics = [
        (32, f"{data['longest']}d", "longest streak"),
        (172, f"{data['active_weeks']}/{data['total_weeks']}", "active weeks"),
        (312, WEEKDAYS[data["best_weekday"]], "peak weekday"),
    ]
    for x, value, label in metrics:
        svg.append(text(x, 92, value, 30, ACCENT, 'font-weight="650"'))
        svg.append(text(x, 114, label, 12))
    svg.append(f'<path d="M32 134h408 M484 60v212" fill="none" stroke="{LINE}"/>')
    svg.append(text(32, 160, "WEEKLY RHYTHM", 10, INK, 'letter-spacing="1.6"'))
    svg += weekday_bars(data, 28, 172, 412, 76, 11)
    svg.append(text(512, 70, "RECENTLY SHIPPED", 10, INK, 'letter-spacing="1.6"'))
    svg += repo_rows(repos, 512, 84, 416, 66, 15, 11, 34)
    last = data["last_active"]
    svg.append(text(928, 288, f"Last contribution {short_date(last)}" if last else "No contributions yet", 10, "#7f91a3",
                    'text-anchor="end"'))
    svg += ["</g>", "</svg>"]
    return "\n".join(svg) + "\n"


def render_mobile(data, repos):
    svg = head(600, 640, data, repos)
    svg += [
        text(28, 46, "Rhythm & pulse.", 27, INK, 'font-weight="600"'),
        ecg(350, 38, 222),
    ]
    metrics = [
        (28, f"{data['longest']}d", "longest streak"),
        (218, f"{data['active_weeks']}/{data['total_weeks']}", "active weeks"),
        (408, WEEKDAYS[data["best_weekday"]], "peak weekday"),
    ]
    for x, value, label in metrics:
        svg.append(text(x, 110, value, 40, ACCENT, 'font-weight="650"'))
        svg.append(text(x, 138, label, 17))
    svg.append(f'<path d="M28 160h544" fill="none" stroke="{LINE}"/>')
    svg.append(text(28, 194, "Weekly rhythm", 18, INK, 'font-weight="600"'))
    svg += weekday_bars(data, 24, 208, 552, 92, 16)
    svg.append(text(28, 368, "Recently shipped", 18, INK, 'font-weight="600"'))
    svg += repo_rows(repos, 28, 384, 544, 80, 20, 15, 30)
    svg += ["</g>", "</svg>"]
    return "\n".join(svg) + "\n"


def main():
    try:
        snapshot = json.loads(INPUT.read_text(encoding="utf-8"))
        validate_days(snapshot["days"])
        data = rhythm(snapshot["days"])
        repos = recent_repositories()
        cards = {OUTPUT: render(data, repos), MOBILE_OUTPUT: render_mobile(data, repos)}
        for svg in cards.values():
            ET.fromstring(svg)
        changed = {p: s for p, s in cards.items() if not p.exists() or p.read_text(encoding="utf-8") != s}
        if not changed:
            print("Pulse card is unchanged.")
            return 0
        for path, svg in changed.items():
            temporary = path.with_suffix(".svg.tmp")
            temporary.write_text(svg, encoding="utf-8", newline="\n")
            temporary.replace(path)
        print(f"Updated {', '.join(p.name for p in changed)}: longest streak {data['longest']}d, "
              f"{data['active_weeks']} active weeks, recent: {', '.join(r['name'] for r in repos)}.")
        return 0
    except (HTTPError, URLError, TimeoutError, ValueError, KeyError, TypeError, OSError, ET.ParseError) as error:
        print(f"Could not update the pulse card; the previous one was kept: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
