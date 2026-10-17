"""تست جامع رابط برای یافتن باگ. اجرا: python3 tools/ui_bugs.py"""
from playwright.sync_api import sync_playwright
from _paths import INDEX_URL, TOOLS_DIR, table_text
import sys
URL = INDEX_URL
results = []
def check(name, cond, extra=""):
    results.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name + ("  " + extra if extra and not cond else ""))

with sync_playwright() as p:
    b = p.chromium.launch()
    errs = []
    def new_page(w=1280, h=900):
        pg = b.new_page(viewport={"width": w, "height": h})
        pg.on("pageerror", lambda e: errs.append("PAGEERROR " + str(e)))
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        return pg
    pg = new_page()
    pg.goto(URL); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_selector("#board svg")

    # 1. کلیک و toggle
    pg.click("[data-v='0']"); pg.click("[data-v='0']")
    check("toggle مهره دو بار کلیک = بدون مهره", pg.inner_text("#counts").startswith("مهره‌ها: ۰"))

    # 2. امتیاز ۱۰ و ۵ و ۰
    pg.click("[data-v='0']"); pg.click("[data-v='2']"); pg.click("#btn-check"); pg.click("#btn-check2")
    check("C4 {1,3} => ۱۵ امتیاز", "۱۵ امتیاز" in pg.inner_text("#result"))
    pg.click("#btn-next")
    check("امتیاز پس از گراف بعدی = ۱۵", "۱۵" in table_text(pg, "#score-body"), table_text(pg, "#score-body"))

    # گراف بعدی تصادفی است؛ برای مراحل بعدی صریحاً C4 را بار می‌کنیم
    pg.select_option("#graph-select", "C4")
    # 3. فرایند بازنشانی مهره‌ها و نتیجه قبلی
    pg.click("[data-v='1']"); pg.click("#btn-check"); pg.click("#btn-reset")
    check("بازنشانی، پیام نتیجه را پاک می‌کند", pg.inner_text("#result").strip() == "", pg.inner_text("#result"))

    # 4. ذخیره‌سازی مهره‌ها پس از رفرش
    pg.click("[data-v='1']"); pg.click("[data-v='3']")
    pg.reload(); pg.wait_for_selector("#board svg")
    marks_after = pg.inner_text("#counts")
    check("مهره‌ها پس از رفرش بازیابی شوند (localStorage)", marks_after.startswith("مهره‌ها: ۲"), marks_after)

    # 5. کیبورد: Enter روی رأس
    pg.reload(); pg.wait_for_selector("#board svg"); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_selector("#board svg")
    pg.focus("[data-v='1']"); pg.keyboard.press("Enter")
    focused = pg.evaluate("document.activeElement && document.activeElement.getAttribute('data-v')")
    check("کیبورد: فوکوس بعد از Enter روی همان رأس بماند", focused == "1", f"active={focused}")

    # 6. حالت دو گروهی و نوبت
    pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_selector("#board svg")
    pg.check("#team-mode")
    pg.click("[data-v='0']"); pg.click("[data-v='2']"); pg.click("#btn-check"); pg.click("#btn-check2"); pg.click("#btn-next")
    rows = table_text(pg, "#score-body")
    check("گروه A بعد از دور اول امتیاز گرفت", "گروه A\t۱۵" in rows, rows)
    check("نوبت به گروه B رفت", "گروه B" in pg.inner_text("#turn-text"), pg.inner_text("#turn-text"))

    # 7. رد کردن دور بدون بررسی (نباید امتیاز بدهد)
    pg.click("#btn-next")
    rows = table_text(pg, "#score-body")
    check("رد کردن دور بی‌امتیاز است", "گروه B\t۰" in rows, rows)

    # 8. تغییر گراف با منوی کشویی: دور قبلی بررسی‌شده نباید امتیاز بی‌صدا از دست برود
    pg.select_option("#graph-select", "P3")
    check("انتخاب گراف از منو", "P₃" in pg.inner_text("#graph-meta"))
    pg.click("[data-v='1']"); pg.click("#btn-check"); pg.click("#btn-check2")
    check("P3 {2} => ۱۵ امتیاز", "۱۵ امتیاز" in pg.inner_text("#result"))

    # 9. آزمایشگاه: ایستگاه ۴ (مینیمال در برابر مینیمم) و نبود ILP
    pg.click("#tab-lab")
    check("ایستگاه ILP حذف شده است", pg.locator("#st4-vars, #st4-solve").count() == 0)
    pg.select_option("#st4-graph", "P6")
    rows = pg.inner_text("#st4-table")
    check("P6: مجموعه‌ی مینیمال {2، 4، 6} در جدول است", "۲، ۴، ۶" in rows, rows[:200])
    check("P6: خلاصه‌ی ایستگاه ۴ تعداد مینیمال‌ها را دارد", "مینیمال" in pg.inner_text("#st4-summary"), pg.inner_text("#st4-summary"))

    # 10. ایستگاه ۵ حالت تیمی
    pg.click("#tab-lab"); pg.click("#st5-go")
    check("ایستگاه ۵ به بازی دو گروهی می‌رود", pg.is_checked("#team-mode") and "گروه A" in pg.inner_text("#turn-text"))

    # 11. واکنش‌گرایی موبایل
    m = new_page(390, 844)
    m.goto(URL); m.evaluate("localStorage.clear()"); m.reload(); m.wait_for_selector("#board svg")
    sw = m.evaluate("document.documentElement.scrollWidth")
    check("بدون اسکرول افقی در موبایل (390px)", sw <= 392, f"scrollWidth={sw}")
    m.screenshot(path="/tmp/shot_mobile.png", full_page=True)

    # 12. تبلت
    t = new_page(820, 1000)
    t.goto(URL); t.evaluate("localStorage.clear()"); t.reload(); t.wait_for_selector("#board svg")
    sw = t.evaluate("document.documentElement.scrollWidth")
    check("بدون اسکرول افقی در تبلت (820px)", sw <= 822, f"scrollWidth={sw}")
    b.close()

check("کنسول بدون خطا", not errs, "; ".join(errs))
print("\n%d/%d passed" % (sum(ok for _, ok in results), len(results)))
