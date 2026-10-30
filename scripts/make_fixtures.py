#!/usr/bin/env python3
"""Write fake Thai League API responses from data/ so update.py can run offline.

    python3 scripts/make_fixtures.py /tmp/tl-fixtures
    python3 scripts/update.py players --api-dir /tmp/tl-fixtures

Useful where the API host is blocked (e.g. a sandbox) or to test changes to
update.py. Running the round trip should leave data/players.json unchanged
apart from today's date in data/meta.json; restore that with git checkout.
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from update import TEAMS, TOURNAMENT  # noqa: E402

out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/tl-fixtures"
os.makedirs(out, exist_ok=True)
data = lambda n: json.load(open(os.path.join(ROOT, "data", n), encoding="utf-8"))
players, standings = data("players.json"), data("standings.json")


def write(path, obj):
    with open(os.path.join(out, re.sub(r"[^A-Za-z0-9]+", "_", path) + ".json"), "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)


write(f"tournament-team-public/?tournament={TOURNAMENT}",
      [{"id": tid, "club": 1000 + i, "name": code} for i, (tid, code) in enumerate(TEAMS.items())])
for tid, code in TEAMS.items():
    rows = [{"id": x["id"], "full_name": x["th"], "full_name_en": x["n"].upper(),
             "position_short_name": x["p"], "nationality": {"code": x["t"]}, "tnm_shirt_number": x["k"],
             "birth_date": f"{x['by']}-01-01", "goal_for": x["g"], "match_count": x["m"], "loan_source_club": None}
            for x in players if x["c"] == code]
    pages = [rows[i:i + 40] for i in range(0, len(rows), 40)] or [[]]
    for n, page in enumerate(pages, 1):
        write(f"player-public/all_players_search/?page={n}&tournament={TOURNAMENT}&tournament_team={tid}",
              {"results": page, "next": "more" if n < len(pages) else None})
write(f"stage-standing-public/dashboard/?tournament={TOURNAMENT}",
      [{"tournament_team": tid, "current_rank": standings["ranks"][code], "match_play": standings["rounds"]}
       for tid, code in TEAMS.items()])
print("fixtures written to", out)
