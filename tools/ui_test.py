"""تست دودی رابط «چالش γ» با Chromium بی‌سر: خطای کنسول، کلیک، بررسی، امتیاز، آزمایشگاه."""
from playwright.sync_api import sync_playwright
from _paths import INDEX_URL, TOOLS_DIR, table_text
import sys
URL = INDEX_URL
errors = []
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1280, "height": 900})
    pg.on("console", lambda m: errors.append(m.text) if m.type in ("error", "warning") else None)
    pg.on("pageerror", lambda e: errors.append("PAGEERROR: " + str(e)))
    pg.goto(URL); pg.evaluate("localStorage.clear()"); pg.reload()
    pg.wait_for_selector("#board svg")
    print("graph:", pg.inner_text("#graph-meta"))
    # C4: {1,3} -> exact
    pg.click("[data-v='0']"); pg.click("[data-v='2']")
    print("counts:", pg.inner_text("#counts"))
    pg.click("#btn-check")
    print("result:", pg.inner_text("#result").replace("\n", " | "))
    pg.click("#btn-next")
    print("score:", table_text(pg, "#score-body").replace("\n", " | "))
    # bad set on new graph
    print("graph2:", pg.inner_text("#graph-meta"))
    pg.click("#btn-check")
    print("result2:", pg.inner_text("#result").replace("\n", " | "))
    pg.click("#btn-gamma"); print("gamma:", pg.inner_text("#gamma-box").replace("\n", " | "))
    pg.screenshot(path="/tmp/shot_game.png", full_page=True)
    # team mode
    pg.check("#team-mode")
    print("turn:", pg.inner_text("#turn-text"))
    # lab
    pg.click("#tab-lab")
    print("st1:", pg.inner_text("#st1-body").replace("\n", " | ")[:300])
    print("st2 verdict:", pg.inner_text("#st2-table").replace("\n", " | ")[-120:])
    pg.select_option("#st3-graph", "W4"); print("st3:", pg.inner_text("#st3-table").replace("\n", " | "))
    pg.click("#st3-add"); print("edge:", pg.inner_text("#st3-edge-result"))
    pg.select_option("#st4-graph", "P6")
    print("st4:", pg.inner_text("#st4-summary"))
    pg.screenshot(path="/tmp/shot_lab.png", full_page=True)
    pg.click("#tab-game"); pg.click("[data-v='1']")
    pg.click("#btn-check"); print("P3 {2}:", pg.inner_text("#result").replace("\n"," | "))
    b.close()
print("CONSOLE ERRORS:", errors if errors else "none")
import sys
sys.exit(1 if errors else 0)
