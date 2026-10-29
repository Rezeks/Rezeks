#!/usr/bin/env python3
"""Render self-hosted GitHub profile cards using only public REST API data.

Run from any directory: python scripts/update_stats.py
GITHUB_TOKEN is optional locally; GitHub Actions supplies its built-in token.
Existing cards are replaced only after every request and validation succeeds.
"""

from collections import Counter
from datetime import datetime, timezone
from html import escape
import json
import os
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


USERNAME = "Rezeks"
OUTPUT = Path(__file__).resolve().parents[1] / "assets" / "stats.svg"
MOBILE_OUTPUT = OUTPUT.with_name("stats-mobile.svg")
COLORS = ["#c8ff5f", "#b8a5ff", "#64d9e8", "#f6c177", "#768597"]


def github(path):
    """Request public endpoints; never inspect private repository metadata."""
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "Rezeks-profile-stats",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token := os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {token}"
    request = Request(f"https://api.github.com{path}", headers=headers)
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def collect_stats():
    profile = github(f"/users/{USERNAME}")
    if not isinstance(profile, dict) or profile.get("login", "").lower() != USERNAME.lower():
        raise ValueError("GitHub returned an unexpected user profile")
    followers = profile.get("followers")
    if not isinstance(followers, int) or followers < 0:
        raise ValueError("GitHub returned an invalid follower count")

    repositories = []
    page = 1
    while True:
        batch = github(f"/users/{USERNAME}/repos?type=owner&per_page=100&page={page}")
        if not isinstance(batch, list):
            raise ValueError("GitHub returned an unexpected repository response")
        for repo in batch:
            if not isinstance(repo, dict) or not isinstance(repo.get("name"), str):
                raise ValueError("GitHub returned an invalid repository")
            if repo.get("private") is not False:
                continue
            if repo.get("owner", {}).get("login", "").lower() != USERNAME.lower():
                continue
            if repo.get("fork") is not False:
                continue
            stars = repo.get("stargazers_count")
            if not isinstance(stars, int) or stars < 0:
                raise ValueError("GitHub returned an invalid star count")
            language = repo.get("language")
            if language is not None and not isinstance(language, str):
                raise ValueError("GitHub returned an invalid language")
            repositories.append(repo)
        if len(batch) < 100:
            break
        page += 1

    languages = Counter(
        repo["language"]
        for repo in repositories
        if repo["language"] and repo["name"].lower() != USERNAME.lower()
    )
    return {
        "repositories": len(repositories),
        "stars": sum(repo["stargazers_count"] for repo in repositories),
        "followers": followers,
        "languages": languages,
    }


def language_groups(stats):
    languages = sorted(stats["languages"].items(), key=lambda entry: (-entry[1], entry[0]))
    if len(languages) > 5:
        languages = languages[:4] + [("Other", sum(count for _, count in languages[4:]))]
    return languages


def render(stats, updated):
    languages = language_groups(stats)
    total = sum(count for _, count in languages)
    elements = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="960" height="270" viewBox="0 0 960 270" role="img" aria-labelledby="title desc">',
        '<title id="title">Rezeks — public GitHub statistics</title>',
        '<desc id="desc">' + escape(
            f"{stats['repositories']} public owned non-fork repositories, "
            f"{stats['stars']} stars, {stats['followers']} followers. "
            "Languages count each repository's primary language, excluding the profile repository. "
            f"Updated {updated} UTC."
        ) + '</desc>',
        '<rect x="0.5" y="0.5" width="959" height="269" rx="18" fill="#0d1117" stroke="#29323d"/>',
        '<g font-family="Segoe UI, Helvetica, Arial, sans-serif">',
        '<text x="32" y="36" fill="#eef2f6" font-size="19" font-weight="600">GitHub, in numbers.</text>',
        '<circle cx="794" cy="29" r="3" fill="#c8ff5f"/>',
        '<text x="807" y="33" fill="#a3b0bf" font-size="10" letter-spacing="1.8">PUBLIC SNAPSHOT</text>',
    ]
    for x, key, label in [(32, "repositories", "Public repos"), (342, "stars", "Stars earned"), (652, "followers", "Followers")]:
        elements.append(f'<text x="{x}" y="87" fill="#c8ff5f" font-size="34" font-weight="600">{stats[key]:,}</text>')
        elements.append(f'<text x="{x}" y="112" fill="#a3b0bf" font-size="13">{label}</text>')
    elements += [
        '<path d="M310 60v55 M620 60v55 M32 135h896" fill="none" stroke="#29323d"/>',
        '<text x="32" y="162" fill="#eef2f6" font-size="11" letter-spacing="1.6">PRIMARY LANGUAGES</text>',
        '<text x="928" y="162" text-anchor="end" fill="#a3b0bf" font-size="11">By repository count</text>',
        '<defs><clipPath id="language-bar"><rect x="32" y="178" width="896" height="9" rx="4.5"/></clipPath></defs>',
        '<rect x="32" y="178" width="896" height="9" rx="4.5" fill="#29323d"/>',
        '<g clip-path="url(#language-bar)">',
    ]
    offset = 32.0
    for index, (_, count) in enumerate(languages):
        width = 896 * count / total
        elements.append(f'<rect x="{offset:.3f}" y="178" width="{width:.3f}" height="9" fill="{COLORS[index]}"/>')
        offset += width
    elements.append('</g>')
    for index, (language, count) in enumerate(languages):
        x = 32 + index * 179
        elements.append(f'<circle cx="{x + 4}" cy="209" r="4" fill="{COLORS[index]}"/>')
        # GitHub language names can be long; retain the full label in a tooltip.
        label = language if len(language) <= 18 else language[:17] + "…"
        elements.append(f'<text x="{x + 15}" y="213" fill="#a3b0bf" font-size="11"><title>{escape(language)}</title>{escape(label)} · {count}</text>')
    if not languages:
        elements.append('<text x="32" y="213" fill="#a3b0bf" font-size="11">No primary-language data yet</text>')
    elements += [
        '<text x="32" y="248" fill="#a3b0bf" font-size="10">Owned public repos · No forks · Languages exclude this profile</text>',
        f'<text x="928" y="248" text-anchor="end" fill="#a3b0bf" font-size="10">Updated {escape(updated)} UTC</text>',
        '</g>',
        '</svg>',
    ]
    return "\n".join(elements) + "\n"


def render_mobile(stats, updated):
    """Use the same snapshot in a taller layout with readable mobile labels."""
    languages = language_groups(stats)
    total = sum(count for _, count in languages)
    elements = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="600" height="430" viewBox="0 0 600 430" role="img" aria-labelledby="title desc">',
        '<title id="title">Rezeks — public GitHub statistics</title>',
        '<desc id="desc">' + escape(
            f"{stats['repositories']} public owned non-fork repositories, "
            f"{stats['stars']} stars, {stats['followers']} followers. "
            "Languages count each repository's primary language, excluding the profile repository. "
            f"Updated {updated} UTC."
        ) + '</desc>',
        '<rect x="0.5" y="0.5" width="599" height="429" rx="18" fill="#0d1117" stroke="#29323d"/>',
        '<g font-family="Segoe UI, Helvetica, Arial, sans-serif">',
        '<text x="28" y="44" fill="#eef2f6" font-size="27" font-weight="600">GitHub, in numbers.</text>',
    ]
    for x, key, label in [(28, "repositories", "Public repos"), (218, "stars", "Stars earned"), (408, "followers", "Followers")]:
        elements.append(f'<text x="{x}" y="105" fill="#c8ff5f" font-size="42" font-weight="600">{stats[key]:,}</text>')
        elements.append(f'<text x="{x}" y="135" fill="#a3b0bf" font-size="18">{label}</text>')
    elements += [
        '<path d="M198 75v62 M388 75v62 M28 159h544" fill="none" stroke="#29323d"/>',
        '<text x="28" y="190" fill="#eef2f6" font-size="18" font-weight="600">Primary languages</text>',
        '<text x="572" y="190" text-anchor="end" fill="#a3b0bf" font-size="18">By repo count</text>',
        '<defs><clipPath id="language-bar"><rect x="28" y="207" width="544" height="13" rx="6.5"/></clipPath></defs>',
        '<rect x="28" y="207" width="544" height="13" rx="6.5" fill="#29323d"/>',
        '<g clip-path="url(#language-bar)">',
    ]
    offset = 28.0
    for index, (_, count) in enumerate(languages):
        width = 544 * count / total
        elements.append(f'<rect x="{offset:.3f}" y="207" width="{width:.3f}" height="13" fill="{COLORS[index]}"/>')
        offset += width
    elements.append('</g>')
    for index, (language, count) in enumerate(languages):
        x = 28 + (index % 2) * 278
        y = 254 + (index // 2) * 32
        label = language if len(language) <= 18 else language[:17] + "…"
        elements.append(f'<circle cx="{x + 5}" cy="{y - 6}" r="5" fill="{COLORS[index]}"/>')
        elements.append(f'<text x="{x + 20}" y="{y}" fill="#a3b0bf" font-size="18"><title>{escape(language)}</title>{escape(label)} · {count}</text>')
    if not languages:
        elements.append('<text x="28" y="254" fill="#a3b0bf" font-size="18">No primary-language data yet</text>')
    elements += [
        '<text x="28" y="355" fill="#a3b0bf" font-size="17">Owned public repos · No forks</text>',
        '<text x="28" y="380" fill="#a3b0bf" font-size="17">Languages exclude this profile</text>',
        f'<text x="28" y="405" fill="#a3b0bf" font-size="17">Updated {escape(updated)} UTC</text>',
        '</g>',
        '</svg>',
    ]
    return "\n".join(elements) + "\n"


def main():
    try:
        stats = collect_stats()
        updated = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        cards = {OUTPUT: render(stats, updated), MOBILE_OUTPUT: render_mobile(stats, updated)}
        for svg in cards.values():
            ET.fromstring(svg)
        changed = {path: svg for path, svg in cards.items()
                   if not path.exists() or path.read_text(encoding="utf-8") != svg}
        if not changed:
            print("Profile statistics are unchanged.")
            return 0
        for path, svg in changed.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_suffix(".svg.tmp")
            temporary.write_text(svg, encoding="utf-8", newline="\n")
            temporary.replace(path)
        print(f"Updated {', '.join(path.name for path in changed)}: {stats['repositories']} repos, {stats['stars']} stars, {stats['followers']} followers.")
        return 0
    except (HTTPError, URLError, TimeoutError, ValueError, OSError, ET.ParseError) as error:
        print(f"Could not update public GitHub statistics: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
