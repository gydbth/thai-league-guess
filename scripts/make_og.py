#!/usr/bin/env python3
"""Draw og.png, the 1200x630 picture LINE / Facebook / X show when someone shares the link.

    .venv/bin/python scripts/make_og.py

Only needed when the look or the season text changes. Needs Playwright with Chromium,
like playtest.py. Uses the same night-pitch colours and Kanit font as the game.
"""
import asyncio, os
from playwright.async_api import async_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TILES = [["hit", "miss", "near", "miss", "miss"],
         ["hit", "hit", "near", "hit", "near"],
         ["hit", "hit", "hit", "hit", "hit"]]

HTML = """<!doctype html><html lang="th"><head><meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Kanit:ital,wght@0,500;0,700;1,900&display=swap">
<style>
html,body{margin:0;width:1200px;height:630px;overflow:hidden}
body{font-family:Kanit,sans-serif;color:#e9f2ec;display:flex;align-items:center;gap:56px;padding:0 80px;justify-content:space-between;box-sizing:border-box;
  background-color:#07100b;background-image:
    radial-gradient(ellipse 70% 60% at 30% 0%, rgba(120,200,150,.16), transparent 70%),
    radial-gradient(ellipse 120% 90% at 50% 50%, transparent 40%, rgba(0,0,0,.7) 100%),
    repeating-linear-gradient(90deg,#0d1d14 0 110px,#0a1810 110px 220px)}
.l{flex:none}
.season{font-size:30px;color:#8fa597;font-weight:500}
h1{font-style:italic;font-weight:900;font-size:100px;white-space:nowrap;line-height:1;margin:8px 0 22px;letter-spacing:-.01em}
h1 span{color:#4fd37f;text-shadow:0 0 30px rgba(79,211,127,.45)}
.sub{font-size:34px;font-weight:500;color:#cfdcd3;line-height:1.35}
.grid{display:grid;grid-template-columns:repeat(5,58px);gap:10px}
.t{width:58px;height:58px;border-radius:14px;background:#1d2c23;border:1px solid rgba(255,255,255,.06)}
.hit{background:#2f9a53;box-shadow:0 0 22px rgba(47,154,83,.45)}
.near{background:#d7a425}
.shirt{display:block;margin:0 auto 26px;width:150px}
</style></head><body>
<div class="l">
  <div class="season">ไทยลีก 1 · ฤดูกาล 2026/27</div>
  <h1>ทาย<span>แข้ง</span>ลีกไทย</h1>
  <div class="sub">นักเตะคนนี้คือใคร?<br>ทายให้ถูกภายใน 8 ครั้ง</div>
</div>
<div>
  <svg class="shirt" viewBox="0 0 100 100"><path d="M34 12 L20 18 L6 34 L18 46 L26 40 L26 90 L74 90 L74 40 L82 46 L94 34 L80 18 L66 12 Q50 24 34 12 Z" fill="none" stroke="rgba(255,255,255,.9)" stroke-width="3" stroke-linejoin="round"/><text x="50" y="72" text-anchor="middle" font-family="Kanit" font-weight="700" font-size="32" fill="#fff">?</text></svg>
  <div class="grid">__TILES__</div>
</div>
</body></html>"""


async def main():
    tiles = "".join(f'<div class="t {c}"></div>' for row in TILES for c in row)
    async with async_playwright() as pw:
        b = await pw.chromium.launch()
        page = await b.new_page(viewport={"width": 1200, "height": 630})
        await page.set_content(HTML.replace("__TILES__", tiles), wait_until="networkidle")
        await page.evaluate("document.fonts.ready")
        await page.screenshot(path=os.path.join(ROOT, "og.png"))
        await b.close()
    print("wrote og.png")

asyncio.run(main())
