#!/usr/bin/env python3
"""Write recent Last.fm scrobbles to data/lastfm.json.

Needs LASTFM_API_KEY and LASTFM_USER in the environment (repo secrets in
Actions). If they're missing the script exits 0 without touching the file,
so the rest of the workflow still runs.
"""
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone

OUT = "data/lastfm.json"
LIMIT = 5


def main():
    key, user = os.environ.get("LASTFM_API_KEY"), os.environ.get("LASTFM_USER")
    if not key or not user:
        print("LASTFM_API_KEY / LASTFM_USER not set; skipping", file=sys.stderr)
        return
    q = urllib.parse.urlencode({"method": "user.getrecenttracks", "user": user, "api_key": key,
                                "format": "json", "limit": LIMIT})
    req = urllib.request.Request("https://ws.audioscrobbler.com/2.0/?" + q,
                                 headers={"User-Agent": "robpaine1.github.io feed fetcher"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        tracks = json.load(resp)["recenttracks"]["track"]

    out = []
    for t in tracks[:LIMIT]:
        images = [i["#text"] for i in t.get("image", []) if i.get("size") == "medium"]
        out.append({
            "track": t["name"], "artist": t["artist"]["#text"], "album": t["album"]["#text"],
            "url": t["url"], "image": images[0] if images and images[0] else None,
            "nowPlaying": t.get("@attr", {}).get("nowplaying") == "true",
            "playedAt": datetime.fromtimestamp(int(t["date"]["uts"]), timezone.utc).isoformat() if "date" in t else None,
        })
    with open(OUT, "w") as f:
        json.dump({"updated": datetime.now(timezone.utc).isoformat(timespec="seconds"), "user": user, "tracks": out}, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"Wrote {len(out)} tracks to {OUT}")


if __name__ == "__main__":
    main()
