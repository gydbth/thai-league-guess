# ทายแข้งลีกไทย (thai-league-guess)

A "Who Are Ya?"-style guessing game for Thai League 1, season 2026/27. The owner is Thai:
reply in Thai, keep it short, and talk about results rather than process.

- Live site: https://thai-league-guess.vercel.app (Vercel deploys every push to `main`)
- Single static page `index.html`, no build tool, no framework. Vercel preset "Other".
- Separate older repo `gydbth/thai-league-quiz` is a different game. Never touch it from here.

## How the game works

- Endless mode: a random mystery player each round, 8 guesses, "เล่นคนต่อไป" starts a new round.
- Two levels (toggle "ปกติ / ง่าย", saved in localStorage `tl-mode`): easy only picks regulars with
  at least half of the league rounds played; it has its own stats (`tl-easy-stats`).
- Each guess shows 5 tiles: club, region (ภาค), position, nationality, shirt number
  (green = match, yellow = close, arrows on shirt number).
- Clues on the board: 2 at the start, +1 after 3 wrong guesses, +1 after 6.
  **Clues must never repeat a tile fact** (no region, position, nationality or shirt number).
  Allowed: transfer/loan/stayed, age, appearances, goals (no league-table clue: the owner removed it);
  if a player has fewer than 3 of these, the surname's first letter fills in. The 4th clue is
  always the first letter of the Thai name (for a leading vowel เ แ โ ใ ไ it shows vowel + consonant, e.g. "เป…").
- Search accepts Thai or English; matching ignores Thai tone marks and Latin accents.
- Stats (win streak, best streak) live in the player's localStorage only.
- The share text ends with the site link; `og.png` (made by `scripts/make_og.py`) is the link-preview picture.
- Look: dark "night match" pitch, Kanit + IBM Plex Sans Thai, red give-up button with a flag.

## Files

| Path | What it is |
|---|---|
| `scripts/game-template.html` | The game (CSS + markup + JS). Edit the game here, never in `index.html`. Placeholders: `__PLAYERS__ __COUNT__ __STANDINGS__ __ROUNDS__ __PLAYERS_DATE__ __TABLE_DATE__ __SEASON_START__` |
| `scripts/update.py` | `players` / `standings` fetch from the Thai League API, then build `index.html`; `build` only rebuilds |
| `data/players.json` | Generated each night. Fields: `id c p t k n th by g m mv fr y` |
| `data/overrides.json` | Hand-made, keyed by Thai League player id: `n` (English display name), `th` (Thai spelling for foreigners), `mv`/`fr` (0 stayed, 1 moved from `fr` (no `fr` = was without a club), 3 loan from `fr`, 4 back from a loan at `fr`; 2 = unknown) |
| `data/standings.json`, `data/meta.json` | League ranks + rounds played; last player update date |
| `scripts/playtest.py` | Headless play-through; must PASS before every push |
| `scripts/make_og.py` | Draws `og.png` (1200x630 link preview); rerun when the look or season text changes |
| `scripts/make_fixtures.py` | Fake API responses from `data/` for offline runs of `update.py` |
| `.github/workflows/update-data.yml` | Cron: players daily 23:00 Bangkok, standings Tuesday 08:00; manual "Run workflow" too |

Player fields: `c` club code, `p` GK/DF/MF/FW, `t` ISO2 nationality, `k` shirt number, `n` English name,
`th` Thai name, `by` birth year, `g` league goals, `m` league appearances, `y: 1` = academy player who
has not played (guessable, never chosen as the mystery player).

## Commands

```bash
python3 scripts/update.py build          # rebuild index.html after editing the template or data
python3 scripts/playtest.py              # must print PASS before pushing
.venv/bin/python scripts/playtest.py     # same, on this Mac (Playwright lives in the git-ignored .venv)
python3 scripts/make_fixtures.py /tmp/fx && python3 scripts/update.py players --api-dir /tmp/fx   # offline update test
```

Local preview: `node .claude/serve.mjs` (launch config "thai-league-guess", port 8765). On macOS,
Python's http.server can't start inside ~/Documents from the app, so use the Node server.

## Rules learned the hard way

- Always run `scripts/playtest.py` after any change and before pushing. A data update once deleted
  `const MAX = 8;` and the live game was broken for a week because only the data was checked.
- Data source is the official registration on thaileague.co.th (API host
  `competition.tl.prod.c0d1um.io`). Do not use Wikipedia squad pages: they lag by months.
  Thai players use their registered Thai name; `update.py` cleans stray vowel marks.
- Cloud sandboxes may block the API host. GitHub Actions and a normal computer can reach it.
  If blocked, work with `--api-dir` fixtures or trigger the workflow instead of guessing data.
- New registrations (e.g. January transfer window) appear automatically, but foreigners show their
  English name and have no transfer clue until someone adds an entry to `data/overrides.json`.
- Transfer clue order: `overrides.json` > API loan field > official transfer list
  (`team-transactions-public`, same data as thaileague.co.th/transfers/224) > unknown (`mv: 2`).
  Only transfer-list arrivals that name a source club count: "No Club" also covers contract renewals.
  That list holds national ID numbers: never save it raw.
- Nov 2026: transfer info for ~120 players was filled from Transfermarkt squad pages ("Joined" date +
  "Signed from"; joined before June 2026 = stayed). Thai clubs are written with their official Thai
  name from the API; foreign clubs keep their English name. ~40 pool players (mostly academy kids
  not on Transfermarkt) are still `mv: 2`.
- Foreign players' Thai names (`th` in overrides): the owner wants the spelling Thai media and club
  pages use (e.g. "เปาลินโญ่", "นาธาน เปไล"), NOT Thai Wikipedia's Royal Institute spelling. All 160 were
  checked against Google results team by team in Nov 2026 (80 changed). About 11 rest on only 1-2 hits
  and ~15 names were not found in Thai media at all (kept as they were). Background bulk fetching of
  Google is blocked as bot-check circumvention: search with normal page loads, one player at a time.
- New season: update `TOURNAMENT`, `SEASON_START` and `TEAMS` in `scripts/update.py`, rerun `make_og.py`, `STANDINGS` placeholder data,
  the season text in the template, and check club codes/regions in the template's `CLUBS`.
- Commit messages in English; the bot's daily "Auto-update" commits are expected.
