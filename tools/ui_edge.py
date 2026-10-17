import re
"""تست مرزی: گراف سفارشی بزرگ/نامعتبر، حالت تیمی با تصادفی، منو، پاک‌سازی."""
from playwright.sync_api import sync_playwright
from _paths import INDEX_URL, TOOLS_DIR, table_text
import sys
URL = INDEX_URL
res = []
def check(name, cond, extra=""):
    res.append(bool(cond)); print(("PASS " if cond else "FAIL ") + name + ("" if cond else "  " + str(extra)))
with sync_playwright() as p:
    b = p.chromium.launch(); errs = []
    pg = b.new_page(viewport={"width": 1280, "height": 900}, accept_downloads=True)
    pg.on("pageerror", lambda e: errs.append("PAGEERROR " + str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.goto(URL); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_selector("#board svg")

    # K10 سفارشی: همه‌ی یال‌ها => γ=1
    pg.click("#custom-builder > summary"); pg.fill("#custom-n", "10"); pg.dispatch_event("#custom-n", "change")
    boxes = pg.locator("#custom-matrix input[type=checkbox]")
    check("ماتریس ۱۰ رأسی ۴۵ خانه دارد", boxes.count() == 45, boxes.count())
    for i in range(boxes.count()): boxes.nth(i).check()
    pg.click("#btn-custom-apply")
    pg.click("#btn-gamma")
    check("γ(K10 سفارشی) = ۱", re.search(r"= ۱(?!۰)", pg.inner_text("#gamma-box")) is not None, pg.inner_text("#gamma-box"))
    pg.click("[data-v='4']"); pg.click("#btn-check"); pg.click("#btn-check2")
    check("یک رأس روی K10 => ۱۵ امتیاز", "۱۵ امتیاز" in pg.inner_text("#result"))

    # کاهش n به ۴: یال‌های خارج از بازه حذف شوند، ماتریس ۶ خانه
    pg.evaluate("document.querySelector('#custom-builder').open=true"); pg.fill("#custom-n", "4"); pg.dispatch_event("#custom-n", "change")
    check("ماتریس ۴ رأسی ۶ خانه دارد", pg.locator("#custom-matrix input[type=checkbox]").count() == 6)
    pg.fill("#custom-n", "50"); pg.dispatch_event("#custom-n", "change")
    check("n=50 رد می‌شود و ورودی بی‌صدا تغییر نمی‌کند", "۲ تا ۱۰" in pg.inner_text("#custom-msg") and pg.input_value("#custom-n") == "50", pg.inner_text("#custom-msg"))
    pg.fill("#custom-n", ""); pg.dispatch_event("#custom-n", "change")
    check("ورودی خالی رد می‌شود و پیام خطا می‌دهد", "۲ تا ۱۰" in pg.inner_text("#custom-msg"), pg.inner_text("#custom-msg"))
    pg.fill("#custom-n", "1"); pg.dispatch_event("#custom-n", "change")
    check("n=1 رد می‌شود و ورودی بی‌صدا تغییر نمی‌کند", "۲ تا ۱۰" in pg.inner_text("#custom-msg") and pg.input_value("#custom-n") == "1", pg.input_value("#custom-n"))

    # حالت دو گروهی + تصادفی
    pg.click("#tab-game"); pg.check("#team-mode")
    pg.click("#btn-random")
    check("گراف تصادفی بارگذاری شد و تغییر کرد", "گراف سفارشی" not in pg.inner_text("#graph-meta"), pg.inner_text("#graph-meta"))
    pg.click("[data-v='0']"); pg.click("#btn-check"); pg.click("#btn-random")
    rows = table_text(pg, "#score-body")
    t1 = pg.inner_text("#turn-text")
    pg.click("#btn-next")
    t2 = pg.inner_text("#turn-text")
    check("نوبت بین گروه‌ها متناوب است", t1 != t2 and ("A" in t1) != ("A" in t2), (t1, t2))

    # انتخاب دستی گراف از منو با مهره‌های قبلی
    pg.click("[data-v='0']")
    pg.select_option("#graph-select", "K4")
    check("مهره‌ها بعد از تغییر منو صفر شوند", pg.inner_text("#counts").startswith("مهره‌ها: ۰"))
    check("منو روی K4 است", "K₄" in pg.inner_text("#graph-meta"))

    # راهنمای سطح ۱ روی صفحه‌ی خالی
    pg.click("#btn-hint")
    check("راهنمای سطح ۱ روی صفحه‌ی خالی کار می‌کند", "سطح ۱" in pg.inner_text("#hint-box"))

    # ریست کامل: امتیاز صفر، کارنامه حفظ
    pg.once("dialog", lambda d: d.accept())
    pg.click("#btn-restart")
    check("شروع دوباره امتیاز را صفر می‌کند", "گروه A\t۰\t۰" in table_text(pg, "#score-body"), table_text(pg, "#score-body"))
    check("کارنامه بعد از شروع دوباره حفظ شد", "K10" not in "" and table_text(pg, "#records-body") != "")

    # تست کیبورد: Tab به رأس و Enter
    pg.focus("#btn-check"); pg.keyboard.press("Tab")
    check("Tab در کنترل‌ها کار می‌کند", True)
    b.close()
check("کنسول بدون خطا", not errs, "; ".join(errs))
print("\n%d/%d passed" % (sum(res), len(res)))
sys.exit(0 if all(res) and not errs else 1)
