#!/usr/bin/env python3
"""Play the built game headless and fail loudly on any error.

    python3 scripts/playtest.py            # tests index.html
    python3 scripts/playtest.py some.html  # a full page or a body-only fragment

Checks: page loads with no JS errors, the first two clues show, Thai name search
works, clues unlock after 3 and 6 wrong guesses, 8 wrong guesses end the round,
a correct guess wins and shows the end card, and no clue repeats a guess-tile
fact (region, position, nationality, shirt number) for any mystery player.
Needs Playwright with Chromium (pip install playwright; playwright install chromium).
"""
import asyncio, os, sys
from playwright.async_api import async_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PLAY = """() => {
  const out = {};
  out.clues = [...document.querySelectorAll('#boardHint .hint')].map(h => h.innerText);
  const i = document.getElementById('guess');
  i.value = 'ธีรศิลป'; i.dispatchEvent(new Event('input'));
  out.search = document.querySelector('#sug li')?.innerText.split('\\n')[0] || '';
  const wrong = PLAYERS.filter(p => p.id !== secret.id).slice(0, 8);
  wrong.slice(0, 3).forEach(p => submit(p)); out.after3 = document.querySelectorAll('#boardHint .hint').length;
  wrong.slice(3, 6).forEach(p => submit(p)); out.after6 = document.querySelectorAll('#boardHint .hint').length;
  wrong.slice(6).forEach(p => submit(p));
  out.rows = document.querySelectorAll('#rows .row').length;
  out.lostDone = done && i.disabled;
  newRound(); submit(secret); out.wonDone = done;
  const bad = /ภาค|ตำแหน่ง|สัญชาติ|เบอร์/; out.tileLeaks = []; out.minClues = 99;
  for (const p of POOL) { const d = buildClues(p); out.minClues = Math.min(out.minClues, d.length);
    d.forEach(c => { if (bad.test(c)) out.tileLeaks.push(p.n + ': ' + c); }); }
  out.players = PLAYERS.length; out.pool = POOL.length;
  return out;
}"""


async def main(path):
    html = open(path, encoding="utf-8").read()
    if "<body" not in html:
        html = ('<!doctype html><html lang="th"><head><meta charset="utf-8">'
                '<style>[hidden]{display:none!important}</style></head><body>' + html + "</body></html>")
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 420, "height": 900})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        await page.route("**/*", lambda r: r.abort() if "fonts.g" in r.request.url else r.continue_())
        await page.set_content(html)
        r = await page.evaluate(PLAY)
        await page.wait_for_timeout(700)
        r["endCard"] = await page.evaluate("!document.getElementById('end').hidden")
        await browser.close()
    problems = []
    if errors: problems.append(f"JS errors: {errors}")
    if len(r["clues"]) != 2: problems.append(f"expected 2 starting clues, got {r['clues']}")
    if not r["search"].startswith("ธีรศิลป์"): problems.append(f"Thai search failed: {r['search']!r}")
    if (r["after3"], r["after6"]) != (3, 4): problems.append(f"clue unlocks wrong: {r['after3']}, {r['after6']}")
    if r["rows"] != 8 or not r["lostDone"]: problems.append("8 wrong guesses did not end the round")
    if not (r["wonDone"] and r["endCard"]): problems.append("correct guess did not win")
    if r["tileLeaks"]: problems.append(f"clues reveal tile facts: {r['tileLeaks'][:3]}")
    if r["minClues"] < 4: problems.append(f"a mystery player has only {r['minClues']} clues")
    print(f"players {r['players']}, mystery pool {r['pool']}, starting clues {r['clues']}")
    if problems:
        print("FAIL\n- " + "\n- ".join(problems)); sys.exit(1)
    print("PASS")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "index.html")))
