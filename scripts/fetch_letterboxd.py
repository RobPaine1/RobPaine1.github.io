#!/usr/bin/env python3
"""Fetch the Letterboxd RSS feed and write the latest films to data/letterboxd.json.

Runs in GitHub Actions on a schedule; the page reads the JSON client-side.
Uses only the standard library so the workflow needs no pip install.
"""
import html
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

FEED = "https://letterboxd.com/robpaine4/rss/"
OUT = "data/letterboxd.json"
LIMIT = 8
NS = {"letterboxd": "https://letterboxd.com"}


def text(item, path):
    node = item.find(path, NS)
    return node.text.strip() if node is not None and node.text else ""


def main():
    req = urllib.request.Request(FEED, headers={"User-Agent": "Mozilla/5.0 (robpaine1.github.io feed fetcher)"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        root = ET.fromstring(resp.read())

    films = []
    for item in root.iter("item"):
        title = text(item, "letterboxd:filmTitle")
        if not title:
            continue  # list entries and other non-film items
        desc = text(item, "description")
        poster = re.search(r'<img src="([^"]+)"', desc)
        films.append({
            "title": html.unescape(title),
            "year": text(item, "letterboxd:filmYear"),
            "rating": float(text(item, "letterboxd:memberRating") or 0) or None,
            "watched": text(item, "letterboxd:watchedDate"),
            "rewatch": text(item, "letterboxd:rewatch") == "Yes",
            "link": text(item, "link"),
            "poster": poster.group(1) if poster else None,
        })
        if len(films) >= LIMIT:
            break

    if not films:
        print("No films parsed; leaving existing data untouched", file=sys.stderr)
        sys.exit(1)

    payload = {"updated": datetime.now(timezone.utc).isoformat(timespec="seconds"), "films": films}
    with open(OUT, "w") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"Wrote {len(films)} films to {OUT}")


if __name__ == "__main__":
    main()
