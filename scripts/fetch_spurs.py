#!/usr/bin/env python3
"""Write Tottenham's next fixture and last result to data/spurs.json.

Primary source: TheSportsDB free tier (all competitions). Fallback: ESPN's
public schedule endpoint (Premier League only). No API key needed for either.
"""
import json
import sys
import urllib.request
from datetime import datetime, timezone

OUT = "data/spurs.json"
TSDB_ID = "133616"   # Tottenham Hotspur on TheSportsDB
ESPN_ID = "367"      # Tottenham Hotspur on ESPN
UA = {"User-Agent": "Mozilla/5.0 (robpaine1.github.io feed fetcher)"}


def iso(stamp):
    """Normalise 'YYYY-MM-DDTHH:MMZ' to include seconds so every Date parser accepts it."""
    date, _, time = stamp.rstrip("Z").partition("T")
    parts = (time or "00:00").split(":")
    while len(parts) < 3:
        parts.append("00")
    return f"{date}T{':'.join(parts[:3])}Z"


def get_json(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def from_thesportsdb():
    nxt = (get_json(f"https://www.thesportsdb.com/api/v1/json/3/eventsnext.php?id={TSDB_ID}").get("events") or [None])[0]
    last = (get_json(f"https://www.thesportsdb.com/api/v1/json/3/eventslast.php?id={TSDB_ID}").get("results") or [None])[0]
    out = {}
    if nxt:
        out["next"] = {
            "home": nxt["strHomeTeam"], "away": nxt["strAwayTeam"],
            "kickoff": iso(f'{nxt["dateEvent"]}T{nxt.get("strTime") or "00:00:00"}'),
            "competition": nxt.get("strLeague"), "venue": nxt.get("strVenue"),
        }
    if last and last.get("intHomeScore") is not None:
        out["last"] = {
            "home": last["strHomeTeam"], "away": last["strAwayTeam"],
            "homeScore": int(last["intHomeScore"]), "awayScore": int(last["intAwayScore"]),
            "date": last["dateEvent"], "competition": last.get("strLeague"),
        }
    return out


def from_espn():
    def parse(ev):
        c = ev["competitions"][0]
        home = next(t for t in c["competitors"] if t["homeAway"] == "home")
        away = next(t for t in c["competitors"] if t["homeAway"] == "away")
        return c, home, away

    out = {}
    upcoming = get_json(f"https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/teams/{ESPN_ID}/schedule?fixture=true").get("events", [])
    for ev in upcoming:
        c, home, away = parse(ev)
        if c["status"]["type"]["state"] in ("pre", "in"):
            out["next"] = {
                "home": home["team"]["displayName"], "away": away["team"]["displayName"],
                "kickoff": iso(ev["date"]),
                "competition": "English Premier League", "venue": (c.get("venue") or {}).get("fullName"),
            }
            break
    played = get_json(f"https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/teams/{ESPN_ID}/schedule").get("events", [])
    for ev in played:  # newest first
        c, home, away = parse(ev)
        if c["status"]["type"]["state"] == "post":
            out["last"] = {
                "home": home["team"]["displayName"], "away": away["team"]["displayName"],
                "homeScore": int(home["score"]["displayValue"] if isinstance(home["score"], dict) else home["score"]),
                "awayScore": int(away["score"]["displayValue"] if isinstance(away["score"], dict) else away["score"]),
                "date": ev["date"][:10], "competition": "English Premier League",
            }
            break
    return out


def main():
    data = {}
    for source in (from_thesportsdb, from_espn):
        try:
            data = source()
        except Exception as e:  # noqa: BLE001
            print(f"{source.__name__} failed: {e}", file=sys.stderr)
            continue
        if data.get("next") or data.get("last"):
            data["source"] = source.__name__.replace("from_", "")
            break
    if not data:
        print("No fixture data from any source", file=sys.stderr)
        sys.exit(1)
    data["updated"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with open(OUT, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"Wrote {OUT} from {data['source']}")


if __name__ == "__main__":
    main()
