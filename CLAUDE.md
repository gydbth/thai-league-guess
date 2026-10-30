# ทายแข้งลีกไทย (thai-league-guess)

A "Who Are Ya?"-style guessing game for Thai League 1, season 2026/27. The owner is Thai:
reply in Thai, keep it short, and talk about results rather than process.

- Live site: https://thai-league-guess.vercel.app (Vercel deploys every push to `main`)
- Single static page `index.html`, no build tool, no framework. Vercel preset "Other".
- Separate older repo `gydbth/thai-league-quiz` is a different game. Never touch it from here.

## How the game works

- Endless mode: a random mystery player each round, 8 guesses, "เล่นคนต่อไป" starts a new round.
- Each guess shows 5 tiles: club, region (ภาค), position, nationality, shirt number
  (green = match, yellow = close, arrows on shirt number).
- Clues on the board: 2 at the start, +1 after 3 wrong guesses, +1 after 6.
  **Clues must never repeat a tile fact** (no region, position, nationality or shirt number).
  Allowed: league table band, transfer/loan/stayed, age, appearances, goals; the 4th clue is
  always the first letter of the Thai name.
- Search accepts Thai or English; matching ignores Thai tone marks and Latin accents.
- Stats (win streak, best streak) live in the player's localStorage only.
- Look: dark "night match" pitch, Kanit + IBM Plex Sans Thai, red give-up button with a flag.

## Files

| Path | What it is |
|---|---|
| `scripts/game-template.html` | The game (CSS + markup + JS). Edit the game here, never in `index.html`. Placeholders: `__PLAYERS__ __COUNT__ __STANDINGS__ __ROUNDS__ __PLAYERS_DATE__ __TABLE_DATE__` |
| `scripts/update.py` | `players` / `standings` fetch from the Thai League API, then build `index.html`; `build` only rebuilds |
| `data/players.json` | Generated each night. Fields: `id c p t k n th by g m mv fr y` |
| `data/overrides.json` | Hand-made, keyed by Thai League player id: `n` (English display name), `th` (Thai spelling for foreigners), `mv`/`fr` (0 stayed, 1 moved from `fr`, 3 loan from `fr`; 2 = unknown) |
| `data/standings.json`, `data/meta.json` | League ranks + rounds played; last player update date |
| `scripts/playtest.py` | Headless play-through; must PASS before every push |
| `scripts/make_fixtures.py` | Fake API responses from `data/` for offline runs of `update.py` |
| `.github/workflows/update-data.yml` | Cron: players daily 23:00 Bangkok, standings Tuesday 08:00; manual "Run workflow" too |

Player fields: `c` club code, `p` GK/DF/MF/FW, `t` ISO2 nationality, `k` shirt number, `n` English name,
`th` Thai name, `by` birth year, `g` league goals, `m` league appearances, `y: 1` = academy player who
has not played (guessable, never chosen as the mystery player).

## Commands

```bash
python3 scripts/update.py build          # rebuild index.html after editing the template or data
python3 scripts/playtest.py              # must print PASS before pushing
python3 scripts/make_fixtures.py /tmp/fx && python3 scripts/update.py players --api-dir /tmp/fx   # offline update test
```

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
- New season: update `TOURNAMENT` and `TEAMS` in `scripts/update.py`, `STANDINGS` placeholder data,
  the season text in the template, and check club codes/regions in the template's `CLUBS`.
- Commit messages in English; the bot's daily "Auto-update" commits are expected.
