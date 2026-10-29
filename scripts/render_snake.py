#!/usr/bin/env python3
"""Turn the public contribution snapshot into a looping, self-contained SVG.

Run after contribution_data.py. No runtime image service or personal token is
needed. The animation traverses the calendar; it does not represent commit order.
"""

from datetime import date, timedelta
from html import escape
import json
import math
from pathlib import Path
import sys
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "assets" / "activity.json"
OUTPUT = ROOT / "assets" / "contribution-snake.svg"
COLORS = ["#19242c", "#38583c", "#638a41", "#93be49", "#c8ff5f"]
DURATION = "46s"


def validate(snapshot):
    if snapshot.get("username") != "Rezeks":
        raise ValueError("Expected Rezeks's contribution snapshot")
    date.fromisoformat(snapshot["generated_at"])
    days = snapshot.get("days")
    if not isinstance(days, list) or not 350 <= len(days) <= 378:
        raise ValueError("Expected a complete annual contribution calendar")
    previous = None
    for day in days:
        current = date.fromisoformat(day["date"])
        if previous is not None and current != previous + timedelta(days=1):
            raise ValueError("Contribution dates must be contiguous and ordered")
        if type(day.get("count")) is not int or day["count"] < 0:
            raise ValueError("Contribution counts must be nonnegative integers")
        if type(day.get("level")) is not int or not 0 <= day["level"] <= 4:
            raise ValueError("Contribution levels must be in the range 0..4")
        previous = current


def render(snapshot):
    validate(snapshot)
    days = snapshot["days"]
    first = date.fromisoformat(days[0]["date"])
    last = date.fromisoformat(days[-1]["date"])
    sunday = first - timedelta(days=(first.weekday() + 1) % 7)
    weeks = (last - sunday).days // 7 + 1
    step = min(16.0, 836.0 / max(weeks - 1, 1))
    origin_x, origin_y = 68.0, 117.0
    size = 12.0
    calendar = {
        ((date.fromisoformat(day["date"]) - sunday).days // 7,
         (date.fromisoformat(day["date"]).weekday() + 1) % 7): day
        for day in days
    }

    # Visit every cell exactly once, then return outside the board. The closed
    # path gives both the moving head and its tail a continuous loop.
    points, arrivals = [], {}
    distance = 0.0
    for row in range(7):
        for week in (range(weeks) if row % 2 == 0 else reversed(range(weeks))):
            point = (origin_x + week * step, origin_y + row * 16)
            if points:
                distance += math.dist(points[-1], point)
            arrivals[(week, row)] = distance
            points.append(point)
    for point in [(points[-1][0] + 16, 237), (48, 237), (48, 117), points[0]]:
        distance += math.dist(points[-1], point)
        points.append(point)
    path = "M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in points) + " Z"
    total = sum(day["count"] for day in days)
    active = sum(day["count"] > 0 for day in days)

    css = [
        "text{font-family:'Segoe UI',Arial,sans-serif}",
        ".mono{font-family:Consolas,'Liberation Mono',monospace}",
        ".food{animation-duration:" + DURATION + ";animation-timing-function:linear;animation-iteration-count:infinite}",
        ".snake-tail{fill:none;stroke-linecap:round;stroke-linejoin:round;animation-duration:" + DURATION + ";animation-timing-function:linear;animation-iteration-count:infinite}",
        ".signal{animation:pulse 2.8s ease-in-out infinite}",
        "@keyframes pulse{0%,100%{opacity:.35}50%{opacity:1}}",
    ]
    food = []
    for index, ((week, row), day) in enumerate(calendar.items()):
        if not day["count"]:
            continue
        arrival = arrivals[(week, row)] / distance * 100
        # Restore the board while the snake travels below it, before its next lap.
        css.append(
            f"@keyframes eat{index}{{0%,{max(0, arrival - .02):.4f}%{{opacity:1}}"
            f"{arrival + .02:.4f}%,94%{{opacity:0}}98%,100%{{opacity:1}}}}"
        )
        x, y = origin_x + week * step - size / 2, origin_y + row * 16 - size / 2
        title = f"{day['date']}: {day['count']} contributions"
        food.append(
            f'<rect class="food" x="{x:.2f}" y="{y:.2f}" width="12" height="12" rx="3" '
            f'fill="{COLORS[max(1, day["level"])]}" style="animation-name:eat{index}"><title>{escape(title)}</title></rect>'
        )
    tails = []
    for name, length, width, color in [
        ("tail", 78, 7, "#b8a5ff"),
        ("middle", 53, 9, "#9ccf62"),
        ("body", 31, 11, "#c8ff5f"),
    ]:
        css.append(f"@keyframes {name}{{from{{stroke-dashoffset:{length}}}to{{stroke-dashoffset:{length-distance:.4f}}}}}")
        tails.append(
            f'<path class="snake-tail" d="{path}" stroke="{color}" stroke-width="{width}" '
            f'stroke-dasharray="{length} {distance-length:.4f}" stroke-dashoffset="{length}" style="animation-name:{name}"/>'
        )
    css.append("@media(prefers-reduced-motion:reduce){.snake{display:none}.food{animation:none!important;opacity:1!important}.signal{animation:none}}")

    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="960" height="300" viewBox="0 0 960 300" role="img" aria-labelledby="title desc">',
        '<title id="title">Rezeks — contribution snake</title>',
        '<desc id="desc">' + escape(
            f"Animated view of the public contribution calendar from {first} to {last}. "
            f"{total} contributions on {active} active days. The snake visits every day, "
            "eats the colored squares, and returns outside the calendar as the board resets. "
            "This is a decorative traversal, not the chronological order of contributions."
        ) + '</desc>',
        '<defs><filter id="glow" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="1.3"/></filter></defs>',
        '<style>' + "\n".join(css) + '</style>',
        '<rect x=".5" y=".5" width="959" height="299" rx="20" fill="#0d1117" stroke="#303a44"/>',
        '<text x="36" y="39" fill="#eef2f6" font-size="24" font-weight="650">Contribution snake.</text>',
        '<text x="36" y="65" fill="#a3b0bf" font-size="13">A year of activity. One square at a time.</text>',
        '<circle class="signal" cx="812" cy="34" r="4" fill="#c8ff5f"/>',
        '<text x="827" y="38" fill="#c8ff5f" font-size="11" letter-spacing="1.4" class="mono">AUTO / LOOP</text>',
        f'<text x="924" y="65" text-anchor="end" fill="#b8a5ff" font-size="13">{total:,} contributions · {active} active days</text>',
    ]
    for row, label in [(1, "M"), (3, "W"), (5, "F")]:
        out.append(f'<text x="40" y="{origin_y + row*16 + 4:.0f}" fill="#687886" font-size="10" text-anchor="middle" class="mono">{label}</text>')
    for day in days:
        current = date.fromisoformat(day["date"])
        if current.day == 1:
            week = (current - sunday).days // 7
            out.append(f'<text x="{origin_x + week*step - 6:.2f}" y="96" fill="#a3b0bf" font-size="11" class="mono">{current.strftime("%b")}</text>')
    for week in range(weeks):
        for row in range(7):
            x, y = origin_x + week * step - size/2, origin_y + row * 16 - size/2
            fill = COLORS[0] if (week, row) in calendar else "#111820"
            out.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="12" height="12" rx="3" fill="{fill}"/>')
    out.extend(food)
    out += [
        '<g class="snake">',
        *tails,
        '<g>',
        f'<animateMotion path="{path}" dur="{DURATION}" repeatCount="indefinite" rotate="auto" calcMode="paced"/>',
        '<rect x="-7" y="-7" width="15" height="14" rx="5" fill="#c8ff5f" stroke="#e3ffab" stroke-width=".8"/>',
        '<circle cx="3" cy="-3" r="1.5" fill="#132015"/><circle cx="3" cy="3" r="1.5" fill="#132015"/>',
        '</g></g>',
        '<path d="M36 251H924" stroke="#29323d"/>',
        f'<text x="36" y="275" fill="#a3b0bf" font-size="11">{first} — {last} · Public contribution calendar</text>',
        '<text x="924" y="275" text-anchor="end" fill="#a3b0bf" font-size="11">Less</text>',
    ]
    # Keep the legend before the final label, with spacing away from the date.
    out[-1] = '<text x="752" y="275" fill="#a3b0bf" font-size="11">Less</text>'
    for i, color in enumerate(COLORS):
        out.append(f'<rect x="{783+i*18}" y="265" width="12" height="12" rx="3" fill="{color}"/>')
    out += ['<text x="882" y="275" fill="#a3b0bf" font-size="11">More</text>', '</svg>']
    svg = "\n".join(out) + "\n"
    ET.fromstring(svg)
    return svg


def main():
    try:
        snapshot = json.loads(INPUT.read_text(encoding="utf-8"))
        svg = render(snapshot)
        if OUTPUT.exists() and OUTPUT.read_text(encoding="utf-8") == svg:
            print("Contribution snake is unchanged.")
            return 0
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        temporary = OUTPUT.with_suffix(".svg.tmp")
        temporary.write_text(svg, encoding="utf-8", newline="\n")
        temporary.replace(OUTPUT)
        print(f"Updated {OUTPUT.name} from {len(snapshot['days'])} real contribution days.")
        return 0
    except (OSError, ValueError, KeyError, TypeError, ET.ParseError) as error:
        print(f"Could not render contribution snake; previous image kept: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
