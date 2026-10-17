"""تست آزمون حذف (مینیمال بودن) و تب کارنامه.

- آزمون حذف فقط بعد از تأیید مرحله‌ی ۱ دیده می‌شود.
- انتخاب موقت یک مهره برای حذف، رأس‌های بی‌پوشش را قرمز می‌کند و مجموعه‌ی واقعی را تغییر نمی‌دهد.
- نتیجه‌ی آزمون بعد از امتحان همه‌ی مهره‌ها اعلام می‌شود (زائد یا ضروری).
- امتیاز تغییر نمی‌کند.
- تب «کارنامه» جدول امتیاز و کارنامه را دارد و خط امتیاز زنده در تب بازی نمایش داده می‌شود.
اجرا: python3 tools/ui_minimal.py
"""
from playwright.sync_api import sync_playwright
from _paths import INDEX_URL, table_text

res = []
def check(name, cond, extra=""):
    res.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else "  " + str(extra)))

with sync_playwright() as p:
    b = p.chromium.launch(); errs = []
    pg = b.new_page(viewport={"width": 1280, "height": 900})
    pg.on("pageerror", lambda e: errs.append("PAGEERROR " + str(e)))
    pg.goto(INDEX_URL); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_selector("#board svg")

    # ۱. پیش از مرحله‌ی ۱: آزمون حذف پنهان است
    check("آزمون حذف پیش از مرحله‌ی ۱ پنهان است", pg.locator("#removal-box").is_hidden())

    # ۲. C4 با مهره‌های ۱ و ۳ (ضروری‌ها: هر دو)
    pg.select_option("#graph-select", "C4")
    pg.click("#btn-reset")
    pg.click("[data-v='0']"); pg.click("[data-v='2']")
    pg.click("#btn-check")
    check("آزمون حذف بعد از تأیید مرحله‌ی ۱ دیده می‌شود", pg.locator("#removal-box").is_visible())
    check("تعداد دکمه‌های حذف برابر تعداد مهره‌ها است", pg.locator("#removal-list li").count() == 2)

    pg.click("#removal-list li:nth-child(1) button")
    miss_cls = pg.locator("#board .vertex.removal-miss").count()
    check("حذف مهره‌ی اول رأس بی‌پوشش را قرمز می‌کند", miss_cls >= 1, miss_cls)
    check("مهره‌ی برداشته‌شده نشانه‌ی حذف دارد", pg.locator("#board .vertex.removal-target").count() == 1)
    check("مجموعه‌ی واقعی تغییر نکرده (۲ مهره)", pg.inner_text("#counts").count("۲") >= 1, pg.inner_text("#counts"))
    check("توضیح حذف نمایش داده شده", "ضروری" in pg.locator("#removal-list li:nth-child(1) .removal-info").inner_text())
    check("خلاصه‌ی انتخاب حذف، مهره‌ی انتخاب‌شده را نشان می‌دهد", "انتخاب شده" in pg.inner_text("#removal-summary"), pg.inner_text("#removal-summary"))

    pg.click("#removal-list li:nth-child(1) button")  # برگرداندن
    check("برگرداندن، نشانه‌ی حذف را پاک می‌کند", pg.locator("#board .vertex.removal-miss").count() == 0)
    pg.click("#removal-list li:nth-child(2) button")
    pg.click("#removal-list li:nth-child(2) button")
    check("امتحان همه‌ی مهره‌ها: نتیجه‌ی مینیمال", "مینیمال است" in pg.inner_text("#removal-summary"), pg.inner_text("#removal-summary"))
    check("امتیاز آزمون حذف صفر است (امتیاز جاری تغییر نکرد)", "ثبت" not in pg.inner_text("#result"))

    # ۳. K4 با مهره‌های ۱ و ۲: مهره‌ی زائد وجود دارد
    pg.select_option("#graph-select", "K4")
    pg.click("#btn-reset")
    pg.click("[data-v='0']"); pg.click("[data-v='1']")
    pg.click("#btn-check")
    for i in range(1, 3):
        pg.click(f"#removal-list li:nth-child({i}) button")
    pg.click("#removal-clear")  # لغو انتخاب‌ها تا نتیجه‌ی همه‌ی مهره‌ها نمایش داده شود
    summary = pg.inner_text("#removal-summary")
    check("K4 با دو مهره: حذف هر مهره زائد است (مینیمال نیست)", "زائد" in summary and "مینیمال نیست" in summary, summary)
    check("K4: هیچ رأسی بی‌پوشش نمی‌شود", "زائد" in pg.locator("#removal-list li:nth-child(1) .removal-info").inner_text())

    # ۴. تغییر مجموعه، آزمون را ریست می‌کند
    pg.click("[data-v='2']")
    check("تغییر مجموعه، آزمون حذف را ریست می‌کند", pg.locator("#removal-box").is_hidden() or "از" in pg.inner_text("#removal-summary"))

    # ۵. تب کارنامه
    pg.click("#tab-game")
    check("خط امتیاز زنده در تب بازی است", pg.locator("#live-score").inner_text().strip() != "")
    check("راهنمای سریع در تب بازی است", pg.locator("#rules-box").count() == 1)
    pg.click("#tab-scores")
    check("تب کارنامه باز می‌شود", pg.locator("#view-scores").is_visible())
    check("جدول امتیاز در تب کارنامه است", pg.locator("#score-table").is_visible())
    check("کارنامه‌ی گراف‌ها در تب کارنامه است", pg.locator("#card-select").is_visible())
    check("تب بازی شامل جدول امتیاز نیست", pg.locator("#view-game #score-body").count() == 0)
    check("سه بخش مجزا: بازی، کارنامه، آزمایشگاه (تب‌ها)", pg.locator(".tab").count() == 4)
    check("بدون خطای صفحه", not errs, errs)
    b.close()

print(f"\n{sum(res)}/{len(res)} تست آزمون حذف و تب کارنامه موفق")
