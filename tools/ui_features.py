"""تست ویژگی‌های نسخه ۱.۱: بازگشت/تکرار، راهنما، گراف سفارشی، کارنامه، CSV، میان‌بر."""
from playwright.sync_api import sync_playwright
from _paths import INDEX_URL, TOOLS_DIR, table_text
import sys
URL = INDEX_URL
res = []
def check(name, cond, extra=""):
    res.append(bool(cond)); print(("PASS " if cond else "FAIL ") + name + ("" if cond else "  " + str(extra)))

with sync_playwright() as p:
    b = p.chromium.launch()
    errs = []
    pg = b.new_page(viewport={"width": 1280, "height": 900}, accept_downloads=True)
    pg.on("pageerror", lambda e: errs.append("PAGEERROR " + str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.goto(URL); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_selector("#board svg")
    counts = lambda: pg.inner_text("#counts")

    # --- بازگشت/تکرار ---
    check("بازگشت در ابتدا غیرفعال", pg.is_disabled("#btn-undo"))
    pg.click("[data-v='0']"); pg.click("[data-v='2']")
    pg.click("#btn-undo")
    check("بازگشت یک مهره را برمی‌دارد", counts().startswith("مهره‌ها: ۱"), counts())
    pg.click("#btn-redo")
    check("تکرار مهره را برمی‌گرداند", counts().startswith("مهره‌ها: ۲"), counts())
    pg.click("#btn-undo"); pg.click("#btn-undo")
    check("بازگشت دوم، صفر مهره", counts().startswith("مهره‌ها: ۰"), counts())
    pg.keyboard.press("Control+y")
    check("Ctrl+Y تکرار می‌کند", counts().startswith("مهره‌ها: ۱"), counts())
    pg.keyboard.press("Control+z")
    check("Ctrl+Z بازگشت می‌دهد", counts().startswith("مهره‌ها: ۰"), counts())
    pg.click("#btn-reset")
    check("بازنشانی هم قابل بازگشت است", pg.is_enabled("#btn-undo"))

    # --- راهنمای سه‌سطحه ---
    pg.click("[data-v='0']")  # C4 با {1}: رأس 3 پوشش داده نشده
    pg.click("#btn-hint")
    check("راهنمای سطح ۱ نشان داده شد", "سطح ۱" in pg.inner_text("#hint-box"), pg.inner_text("#hint-box"))
    check("شمارنده‌ی راهنما ۱ شد", pg.inner_text("#hint-level") == "1")
    pg.click("#btn-hint")
    check("راهنمای سطح ۲ یک رأس پیشنهاد می‌دهد", "سطح ۲" in pg.inner_text("#hint-box"))
    check("رأس پیشنهادی حلقه دارد", pg.locator(".vertex.hint-target").count() == 1)
    pg.click("#btn-hint")
    check("راهنمای سطح ۳ γ را نشان می‌دهد", "γ(G) = ۲" in pg.inner_text("#hint-box"), pg.inner_text("#hint-box"))
    check("دکمه‌ی راهنما بعد از سطح ۳ غیرفعال", pg.is_disabled("#btn-hint"))
    pg.click("#btn-check")
    pg.click("#btn-next")
    check("راهنما امتیاز را تغییر نمی‌دهد (دور رد شد=0)", "بازیکن\t۰\t۱" in table_text(pg, "#score-body"), table_text(pg, "#score-body"))
    check("راهنما در سابقه ثبت شد", "راهنما: ۳" in pg.inner_text("#history"), pg.inner_text("#history"))

    # --- گراف سفارشی: مسیر P_4 (۱-۲-۳-۴) => γ=2 ---
    pg.click("#tab-game")
    pg.click("#custom-builder > summary")
    pg.fill("#custom-n", "4"); pg.dispatch_event("#custom-n", "change")
    pg.check("#custom-matrix input[aria-label='یال ۱ و ۲']")
    pg.check("#custom-matrix input[aria-label='یال ۲ و ۳']")
    pg.check("#custom-matrix input[aria-label='یال ۳ و ۴']")
    pg.click("#btn-custom-apply")
    check("گراف سفارشی بارگذاری شد", "گراف سفارشی" in pg.inner_text("#graph-meta") and "n = ۴" in pg.inner_text("#graph-meta"), pg.inner_text("#graph-meta"))
    pg.click("#btn-gamma")
    check("γ گراف سفارشی P4 = 2", "γ(گراف سفارشی) = ۲" in pg.inner_text("#gamma-box"), pg.inner_text("#gamma-box"))
    pg.click("[data-v='1']"); pg.click("#btn-check")
    check("{2} روی P4 احاطه‌گر نیست", "نیست" in pg.inner_text("#result"))
    pg.click("[data-v='2']"); pg.click("#btn-check"); pg.click("#btn-check2")
    check("{2,3} روی P4 => ۱۵ امتیاز", "۱۵ امتیاز" in pg.inner_text("#result"), pg.inner_text("#result"))
    pg.reload(); pg.wait_for_selector("#board svg")
    check("گراف سفارشی پس از رفرش بازیابی شد", "گراف سفارشی" in pg.inner_text("#graph-meta"), pg.inner_text("#graph-meta"))
    pg.reload(); pg.wait_for_selector("#board svg")
    check("نتیجه‌ی بررسی بعد از رفرش بازیابی شد", "۱۵ امتیاز" in pg.inner_text("#result"), pg.inner_text("#result"))
    pg.click("#btn-next")

    # --- کارنامه ---
    rec = table_text(pg, "#records-body")
    check("کارنامه برای گراف‌های بازی‌شده ثبت شد", "۱۵" in rec, rec[:200])

    # --- CSV ---
    with pg.expect_download() as d:
        pg.click("#tab-scores"); pg.click("#btn-csv")
    path = d.value.path()
    content = open(path, encoding="utf-8-sig").read()
    check("CSV دانلود شد با سطر سرتیتر", content.splitlines()[0] == '"گروه","گراف","|D|","γ","وضعیت","امتیاز","تعداد راهنما"', content[:120])
    check("CSV شامل سطرهای سابقه است", len(content.splitlines()) >= 3, content)

    # --- کیبورد: Ctrl+Z وقتی تایپ نمی‌کنیم ---
    b.close()

check("کنسول بدون خطا", not errs, "; ".join(errs))
print("\n%d/%d passed" % (sum(res), len(res)))
sys.exit(0 if all(res) and not errs else 1)
