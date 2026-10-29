#!/usr/bin/env python3
"""Save the contribution calendar visible on Rezeks's public GitHub profile.

No token is needed. Only dates, counts and GitHub's color levels are stored.
If GitHub changes its HTML or the request fails, keep the previous snapshot.
"""

from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib.request import Request, urlopen

USERNAME = "Rezeks"
OUTPUT = Path(__file__).resolve().parents[1] / "assets" / "activity.json"
SOURCE = f"https://github.com/users/{USERNAME}/contributions"


class ContributionParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.cells = {}
        self.tooltips = {}
        self.active_tooltip = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("data-date") and "ContributionCalendar-day" in attrs.get("class", ""):
            key = attrs.get("id")
            if not key or key in self.cells:
                raise ValueError("Missing or duplicate calendar cell ID")
            self.cells[key] = {"date": attrs["data-date"], "level": int(attrs["data-level"])}
        if tag == "tool-tip" and attrs.get("for"):
            self.active_tooltip = attrs["for"]
            self.tooltips[self.active_tooltip] = ""

    def handle_data(self, value):
        if self.active_tooltip is not None:
            self.tooltips[self.active_tooltip] += value

    def handle_endtag(self, tag):
        if tag == "tool-tip":
            self.active_tooltip = None

    def days(self):
        result = []
        for key, cell in self.cells.items():
            label = self.tooltips.get(key, "").strip()
            match = re.match(r"^(No|[\d,]+) contributions? on ", label)
            if not match:
                raise ValueError(f"Cannot read contribution count for {cell['date']}")
            count = 0 if match[1] == "No" else int(match[1].replace(",", ""))
            result.append({"date": cell["date"], "count": count, "level": cell["level"]})
        return sorted(result, key=lambda day: day["date"])


def validate_days(days, today=None):
    if not isinstance(days, list) or not 350 <= len(days) <= 371:
        raise ValueError("Expected one complete year of contribution calendar cells")
    previous = None
    for day in days:
        current = date.fromisoformat(day["date"])
        if previous is not None and current != previous + timedelta(days=1):
            raise ValueError("Contribution dates are missing or duplicated")
        if type(day["count"]) is not int or day["count"] < 0:
            raise ValueError("Invalid contribution count")
        if type(day["level"]) is not int or not 0 <= day["level"] <= 4:
            raise ValueError("Invalid contribution color level")
        if (day["count"] == 0) != (day["level"] == 0):
            raise ValueError("Contribution count and color level disagree")
        previous = current
    if today is not None and not today - timedelta(days=1) <= previous <= today:
        raise ValueError("GitHub returned a stale or future calendar")


def collect():
    today = datetime.now(timezone.utc).date()
    request = Request(SOURCE, headers={"User-Agent": "Rezeks-profile-calendar", "Accept-Language": "en-US,en;q=0.9"})
    with urlopen(request, timeout=45) as response:
        html = response.read().decode("utf-8")
    parser = ContributionParser()
    parser.feed(html)
    days = parser.days()
    validate_days(days, today)
    return {"username": USERNAME, "generated_at": today.isoformat(), "days": days}


def main():
    try:
        snapshot = collect()
        output = json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n"
        if OUTPUT.exists() and OUTPUT.read_text(encoding="utf-8") == output:
            print("Contribution calendar is unchanged.")
            return 0
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        temporary = OUTPUT.with_suffix(".json.tmp")
        temporary.write_text(output, encoding="utf-8", newline="\n")
        temporary.replace(OUTPUT)
        print(f"Saved {len(snapshot['days'])} days and {sum(d['count'] for d in snapshot['days'])} contributions.")
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Calendar update failed; the previous snapshot was kept: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
