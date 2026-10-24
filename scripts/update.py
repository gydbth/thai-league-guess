#!/usr/bin/env python3
"""Refresh the game's data from thaileague.co.th and rebuild index.html.

    python3 scripts/update.py players     # squads, goals, appearances (daily 23:00)
    python3 scripts/update.py standings   # league table (Tuesdays)
    python3 scripts/update.py build       # rebuild index.html from data/ only

Data comes from the public API behind thaileague.co.th. Hand-made fields that the
API does not have (Thai spelling of foreign players' names, common names, past
club / loan info) live in data/overrides.json, keyed by the API player id.

Use --api-dir DIR to read saved API responses instead of the network (testing).
"""
import json, os, re, sys, time, urllib.request
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
API = "https://competition.tl.prod.c0d1um.io/thaileague/api/"
TOURNAMENT = 224  # BYD Sealion 6 League I 2026/27; change for a new season
# tournament_team id -> club code used by the game (2026/27)
TEAMS = {7112: "BRU", 7113: "BGP", 7114: "POR", 7115: "RBM", 7116: "BKU", 7117: "PTP",
         7118: "AYU", 7119: "CRU", 7120: "CHO", 7121: "RAY", 7122: "LWR", 7123: "UTT",
         7124: "SKU", 7125: "SUK", 7126: "RSL", 7127: "PTN"}
BKK = timezone(timedelta(hours=7))
THAI_MONTHS = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]
API_DIR = None


def get(path):
    if API_DIR:  # offline fixtures: file name is the path with unsafe chars replaced
        with open(os.path.join(API_DIR, re.sub(r"[^A-Za-z0-9]+", "_", path) + ".json"), encoding="utf-8") as f:
            return json.load(f)
    req = urllib.request.Request(API + path, headers={
        "Accept": "application/json", "Origin": "https://thaileague.co.th",
        "Referer": "https://thaileague.co.th/", "User-Agent": "Mozilla/5.0 (thai-league-guess updater)"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except Exception as e:  # retry transient failures
            if attempt == 3:
                raise
            print(f"retry {path}: {e}", file=sys.stderr)
            time.sleep(5 * (attempt + 1))


def load(name, default=None):
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save(name, obj, compact=False):
    with open(os.path.join(DATA, name), "w", encoding="utf-8") as f:
        if compact:
            json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
        else:
            json.dump(obj, f, ensure_ascii=False, indent=1)


def title(s):
    return " ".join("-".join(p.capitalize() for p in w.split("-")) for w in s.split())


def thai_date(d):
    return f"{d.day} {THAI_MONTHS[d.month - 1]} {d.year + 543}"


def today():
    return datetime.now(BKK).date()


def update_players():
    overrides = load("overrides.json", {})
    teams = get(f"tournament-team-public/?tournament={TOURNAMENT}")
    teams = teams.get("results", teams) if isinstance(teams, dict) else teams
    club_name = {t["club"]: re.sub(r"\s*เอฟซี$", "", t["name"]).replace("สิงห์ ", "") for t in teams}
    players, per_team = [], {}
    for team_id, code in TEAMS.items():
        page, n = 1, 0
        while True:
            r = get(f"player-public/all_players_search/?page={page}&tournament={TOURNAMENT}&tournament_team={team_id}")
            for p in r["results"]:
                n += 1
                num = p.get("tnm_shirt_number") or p.get("shirt_number")
                if num is None:
                    continue
                pid = str(p["id"])
                o = overrides.get(pid, {})
                nat = (p.get("nationality") or {}).get("code") or "TH"
                by = int(str(p.get("birth_date") or "2000")[:4])
                m = p.get("match_count") or 0
                x = {"id": p["id"], "c": code, "p": p.get("position_short_name") or "MF", "t": nat, "k": int(num),
                     "n": o.get("n") or title(re.sub(r"\s+", " ", p.get("full_name_en") or "").strip()),
                     "th": o.get("th") if nat != "TH" and o.get("th") else re.sub(r"\s+", " ", p.get("full_name") or "").replace("​", "").strip(),
                     "by": by, "g": p.get("goal_for") or 0, "m": m}
                if "mv" in o:
                    x["mv"] = o["mv"]
                    if o.get("fr"):
                        x["fr"] = o["fr"]
                elif p.get("loan_source_club"):
                    x["mv"], x["fr"] = 3, club_name.get(p["loan_source_club"], "สโมสรอื่น")
                else:
                    x["mv"] = 2
                if m == 0 and by >= 2007:
                    x["y"] = 1  # unknown academy player: guessable, never the mystery player
                players.append(x)
            if not r.get("next"):
                break
            page += 1
        per_team[code] = n
    # Refuse to publish an obviously broken fetch
    if len(players) < 300 or min(per_team.values()) < 15:
        sys.exit(f"Fetched data looks incomplete, not saving: {per_team}")
    old = load("players.json", [])
    added = sorted({p["id"] for p in players} - {p["id"] for p in old})
    gone = sorted({p["id"] for p in old} - {p["id"] for p in players})
    print(f"players: {len(players)} (+{len(added)} / -{len(gone)})", per_team)
    save("players.json", players, compact=True)
    meta = load("meta.json", {})
    meta["players_updated"] = today().isoformat()
    save("meta.json", meta)


def update_standings():
    rows = get(f"stage-standing-public/dashboard/?tournament={TOURNAMENT}")
    rows = rows.get("results", rows) if isinstance(rows, dict) else rows
    ranks, rounds = {}, 0
    for r in rows:
        code = TEAMS.get(r.get("tournament_team"))
        if code:
            ranks[code] = int(r["current_rank"])
            rounds = max(rounds, int(r.get("match_play") or 0))
    if len(ranks) != len(TEAMS):
        sys.exit(f"Standings incomplete, not saving: {ranks}")
    print("standings:", sorted(ranks, key=ranks.get), "rounds", rounds)
    save("standings.json", {"updated": today().isoformat(), "rounds": rounds, "ranks": ranks})


def build():
    players = load("players.json")
    st = load("standings.json")
    meta = load("meta.json", {})
    with open(os.path.join(ROOT, "scripts", "game-template.html"), encoding="utf-8") as f:
        t = f.read()
    d = lambda s: thai_date(datetime.strptime(s, "%Y-%m-%d").date())
    body = (t.replace("__PLAYERS__", json.dumps(players, ensure_ascii=False, separators=(",", ":")))
             .replace("__COUNT__", str(len(players)))
             .replace("__STANDINGS__", json.dumps(st["ranks"], separators=(",", ":")))
             .replace("__ROUNDS__", str(st["rounds"]))
             .replace("__PLAYERS_DATE__", d(meta.get("players_updated", st["updated"])))
             .replace("__TABLE_DATE__", d(st["updated"])))
    page = ('<!doctype html>\n<html lang="th">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            '<meta name="theme-color" content="#07100b">\n'
            '<meta name="description" content="เกมทายนักเตะไทยลีก 1 ฤดูกาล 2026/27 เล่นได้ไม่จำกัด">\n'
            '<style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}'
            'body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>\n</head>\n<body>\n'
            + body + '\n</body>\n</html>\n')
    with open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8") as f:
        f.write(page)
    print("built index.html:", len(players), "players")


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--api-dir" in args:
        i = args.index("--api-dir")
        API_DIR = args[i + 1]
        del args[i:i + 2]
    mode = args[0] if args else "build"
    if mode == "players":
        update_players()
    elif mode == "standings":
        update_standings()
    elif mode != "build":
        sys.exit(f"unknown mode {mode}")
    build()
