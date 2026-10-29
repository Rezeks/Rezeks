#!/usr/bin/env python3
"""Render animated SVG charts from the saved public contribution calendar.

Run contribution_data.py first to refresh the snapshot. SVGs need no JavaScript,
external fonts, remote image services, or libraries. Height encodes daily counts.
"""

from collections import Counter
from datetime import date, timedelta
from html import escape
import json
import math
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

from contribution_data import validate_days

ASSETS = Path(__file__).resolve().parents[1] / "assets"
FONT = "Segoe UI, Helvetica, Arial, sans-serif"
LEVEL_COLORS = ["#263640", "#4d7947", "#77ad48", "#a2dc50", "#d5ff80"]


def text(x, y, value, size=14, color="#a3b0bf", extra=""):
    return f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" {extra}>{escape(str(value))}</text>'


def points(values):
    return " ".join(f"{x:.2f},{y:.2f}" for x, y in values)


def polygon(vertices, fill, extra=""):
    return f'<polygon points="{points(vertices)}" fill="{fill}" {extra}/>'


def start(width, height, title, description):
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        f'<title id="title">{escape(title)}</title><desc id="desc">{escape(description)}</desc>',
        '<defs><linearGradient id="surface" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#18242b"/><stop offset="1" stop-color="#0d151c"/></linearGradient>',
        '<linearGradient id="fill" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#c8ff5f" stop-opacity=".22"/><stop offset="1" stop-color="#c8ff5f" stop-opacity=".01"/></linearGradient>',
        '<filter id="glow" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="3"/></filter></defs>',
        '<style>.scan{animation:scan 14s linear infinite}.spark{animation:spark 5s ease-in-out infinite}.trace{animation:trace 12s linear infinite}@keyframes scan{from{stroke-dashoffset:650}to{stroke-dashoffset:0}}@keyframes spark{0%,100%{opacity:.18}50%{opacity:.55}}@keyframes trace{to{stroke-dashoffset:-320}}@media(prefers-reduced-motion:reduce){.scan,.spark,.trace{animation:none}}</style>',
        f'<rect x=".5" y=".5" width="{width-1}" height="{height-1}" rx="20" fill="#0d1117" stroke="#2e3a40"/>',
        f'<g font-family="{FONT}">',
    ]


def render_landscape(snapshot, mobile=False):
    days = snapshot["days"]
    start_date, end_date = date.fromisoformat(days[0]["date"]), date.fromisoformat(days[-1]["date"])
    sunday = start_date - timedelta(days=(start_date.weekday() + 1) % 7)
    columns = ((end_date - sunday).days // 7) + 1
    total = sum(day["count"] for day in days)
    active = sum(day["count"] > 0 for day in days)
    peak = max(day["count"] for day in days)
    width, height = (600, 470) if mobile else (960, 500)
    desc = f"Isometric contribution calendar for Rezeks, {start_date} through {end_date}. {total} contributions across {active} active days. The tallest day has {peak} contributions. Column height is proportional to the daily contribution count."
    svg = start(width, height, "Rezeks — contribution city", desc)
    svg += [text(28 if mobile else 32, 43, "CONTRIBUTION CITY", 22 if mobile else 23, "#eef2f6", 'font-weight="650" letter-spacing="1"'),
            text(28 if mobile else 32, 71, "One day. One block. A year of building.", 17 if mobile else 14)]
    metric_y = 113
    for x, number, label in [(28 if mobile else 32, total, "contributions"), (222 if mobile else 252, active, "active days"), (414 if mobile else 472, peak, "peak day")]:
        svg.append(text(x, metric_y, number, 28, "#c8ff5f", 'font-weight="650"'))
        svg.append(text(x + (len(str(number)) * 17) + 9, metric_y, label, 15 if mobile else 14))
    if not mobile:
        svg.append(text(928, 109, "PUBLIC PROFILE / LAST YEAR", 11, "#7f91a3", 'text-anchor="end" letter-spacing="1.2"'))

    # Project an upright grid onto an isometric floor, then extrude each day.
    # Draw from far to near so taller neighboring columns occlude correctly.
    scene = []
    origin = (152, 178)
    wx, wy, dx, dy = 13.25, 3.25, -15.6, 7.7
    def project(week, weekday):
        return origin[0] + week * wx + weekday * dx, origin[1] + week * wy + weekday * dy
    floor = [project(-.3, -.3), project(columns+.3, -.3), project(columns+.3, 7.3), project(-.3, 7.3)]
    scene.append(polygon([(x, y+13) for x, y in floor], "#080d12"))
    scene.append(polygon([floor[1], floor[2], (floor[2][0], floor[2][1]+9), (floor[1][0], floor[1][1]+9)], "#101a23"))
    scene.append(polygon([floor[2], floor[3], (floor[3][0], floor[3][1]+9), (floor[2][0], floor[2][1]+9)], "#17242d"))
    scene.append(polygon(floor, "url(#surface)", 'stroke="#3a4e52" stroke-width="1"'))
    cells = []
    for day in days:
        offset = (date.fromisoformat(day["date"]) - sunday).days
        week, weekday = divmod(offset, 7)
        x, y = project(week + .08, weekday + .08)
        cells.append((y, x, week, weekday, day))
    for _, _, week, weekday, day in sorted(cells):
        a = project(week+.08, weekday+.08)
        b = project(week+.92, weekday+.08)
        c = project(week+.92, weekday+.92)
        d = project(week+.08, weekday+.92)
        h = 2 + (day["count"] * 94 / max(peak, 1))
        top = [(x, y-h) for x, y in [a, b, c, d]]
        level = day["level"]
        side = "#14212b" if not level else "#2c5335"
        front = "#1b2a33" if not level else "#527a37"
        scene.append(f'<g><title>{day["date"]}: {day["count"]} contributions</title>')
        scene.append(polygon([top[1], top[2], c, b], side))
        scene.append(polygon([top[2], top[3], d, c], front))
        scene.append(polygon(top, LEVEL_COLORS[level], 'stroke="#07120f" stroke-width=".45"'))
        if level >= 3:
            scene.append(polygon(top, "#c8ff5f", f'class="spark" filter="url(#glow)" style="animation-delay:-{week%5}s"'))
        scene.append('</g>')
    # Motion stays on the platform edge; data heights never animate or change.
    edge = [floor[3], floor[2], floor[1]]
    scene.append(f'<polyline points="{points(edge)}" fill="none" stroke="#607d59" stroke-width="1"/>')
    scene.append(f'<polyline class="scan" points="{points(edge)}" fill="none" stroke="#c8ff5f" stroke-width="2" stroke-linecap="round" stroke-dasharray="45 605"/>')
    for week in range(0, columns, 8):
        x, y = project(week+.5, 8.3)
        label_date = sunday + timedelta(weeks=week)
        scene.append(text(round(x, 1), round(y+7, 1), label_date.strftime("%b"), 12, "#8b9ca9", 'text-anchor="middle"'))
    if mobile:
        svg.append('<g transform="translate(10 56) scale(.66)">')
    else:
        svg.append('<g>')
    svg.extend(scene)
    svg.append('</g>')
    legend_y = 408 if mobile else 444
    svg.append(text(28 if mobile else 32, legend_y, "LOW", 14 if mobile else 11, "#7f91a3"))
    for index, color in enumerate(LEVEL_COLORS):
        x = (70 if mobile else 66) + index*22
        svg.append(f'<rect x="{x}" y="{legend_y-12}" width="15" height="15" rx="3" fill="{color}"/>')
    svg.append(text(190 if mobile else 187, legend_y, "HIGH", 14 if mobile else 11, "#7f91a3"))
    svg.append(text(28 if mobile else 928, 438 if mobile else legend_y, "Height = daily contributions", 16 if mobile else 12, "#a3b0bf", '' if mobile else 'text-anchor="end"'))
    svg.append(text(572 if mobile else 32, 460 if mobile else 478, f"{start_date} — {end_date}", 13 if mobile else 11, "#7f91a3", 'text-anchor="end"' if mobile else ''))
    if not mobile:
        svg.append(text(928, 478, f"Updated {snapshot['generated_at']} UTC", 11, "#7f91a3", 'text-anchor="end"'))
    svg += ['</g>', '</svg>']
    return "\n".join(svg) + "\n"


def render_monthly(snapshot, mobile=False):
    months = Counter()
    for day in snapshot["days"]:
        months[day["date"][:7]] += day["count"]
    entries = sorted(months.items())
    width, height = (600, 420) if mobile else (960, 360)
    svg = start(width, height, "Rezeks — monthly contribution rhythm", "Calendar-month contribution totals from the public GitHub profile. " + "; ".join(f"{month}: {count}" for month, count in entries) + ". Boundary months may be partial.")
    svg += [text(28 if mobile else 32, 43, "THE BUILDING RHYTHM", 22, "#eef2f6", 'font-weight="650" letter-spacing="1"'),
            text(28 if mobile else 32, 71, "Contributions, month by month.", 17 if mobile else 14)]
    left, right, top, bottom = (54, 568, 112, 297) if mobile else (60, 924, 106, 260)
    maximum = max(5, math.ceil(max(count for _, count in entries) / 5) * 5)
    for tick in range(0, 6):
        y = bottom - (bottom-top) * tick/5
        svg.append(f'<path d="M{left} {y:.2f}H{right}" stroke="#26313b" stroke-dasharray="3 6"/>')
        svg.append(text(left-13, round(y+5, 2), f"{maximum*tick/5:g}", 15 if mobile else 12, "#7f91a3", 'text-anchor="end"'))
    coordinates = [(left + (right-left)*i/(len(entries)-1), bottom - count/maximum*(bottom-top)) for i, (_, count) in enumerate(entries)]
    path = "M" + " L".join(f"{x:.2f} {y:.2f}" for x, y in coordinates)
    area = path + f" L{right} {bottom} L{left} {bottom}Z"
    svg += [f'<path d="{area}" fill="url(#fill)"/>',
            f'<path d="{path}" fill="none" stroke="#c8ff5f" stroke-width="2.5" stroke-linejoin="round"/>',
            f'<path class="trace" d="{path}" fill="none" stroke="#fff" stroke-opacity=".65" stroke-width="2" stroke-dasharray="7 153"/>']
    for i, ((month, count), (x, y)) in enumerate(zip(entries, coordinates)):
        svg.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4" fill="#0d1117" stroke="#c8ff5f" stroke-width="2"><title>{month}: {count} contributions</title></circle>')
        if count:
            svg.append(text(round(x, 2), round(y-13, 2), count, 16 if mobile else 12, "#c8ff5f", 'text-anchor="middle"'))
        if not mobile or i%2 == 0:
            label = date.fromisoformat(month+"-01").strftime("%b")
            if i == 0 or i == len(entries)-1:
                label += " '" + month[2:4]
            svg.append(text(round(x, 2), bottom+29, label, 14 if mobile else 12, "#a3b0bf", 'text-anchor="middle"'))
    if mobile:
        svg.append(text(28, 368, "Calendar months · edge months are partial", 16))
        svg.append(text(28, 395, f"Updated {snapshot['generated_at']} UTC", 15, "#7f91a3"))
    else:
        svg.append(text(32, 331, "Calendar-month totals · boundary months may be partial", 12))
        svg.append(text(928, 331, f"Updated {snapshot['generated_at']} UTC", 11, "#7f91a3", 'text-anchor="end"'))
    svg += ['</g>', '</svg>']
    return "\n".join(svg) + "\n"


def main():
    try:
        snapshot = json.loads((ASSETS / "activity.json").read_text(encoding="utf-8"))
        if snapshot.get("username") != "Rezeks":
            raise ValueError("Unexpected calendar owner")
        date.fromisoformat(snapshot["generated_at"])
        validate_days(snapshot["days"])
        cards = {
            "activity-3d.svg": render_landscape(snapshot),
            "activity-3d-mobile.svg": render_landscape(snapshot, mobile=True),
            "activity-monthly.svg": render_monthly(snapshot),
            "activity-monthly-mobile.svg": render_monthly(snapshot, mobile=True),
        }
        for svg in cards.values():
            ET.fromstring(svg)
        for name, svg in cards.items():
            destination = ASSETS / name
            if destination.exists() and destination.read_text(encoding="utf-8") == svg:
                continue
            temporary = destination.with_suffix(".svg.tmp")
            temporary.write_text(svg, encoding="utf-8", newline="\n")
            temporary.replace(destination)
        print("Rendered contribution city and monthly charts for desktop and mobile.")
        return 0
    except (OSError, ValueError, KeyError, TypeError, ET.ParseError) as error:
        print(f"Activity charts were not refreshed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
