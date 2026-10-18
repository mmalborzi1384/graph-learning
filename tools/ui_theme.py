"""آزمون حالت روشن/تاریک (نسخه ۶.۴.۰) در صفحه‌ی بازی و صفحه‌ی معرفی.

بررسی می‌کند:
- پیش‌فرض روشن است (بدون ذخیره‌ی قبلی)
- دکمه در هر دو صفحه حالت را عوض می‌کند و برچسب و aria-pressed درست می‌شود
- انتخاب در localStorage می‌ماند و پس از بارگذاری دوباره اعمال می‌شود
- توکن‌های کلیدی هر حالت درست‌اند (متن، زمینه، مهره‌ها)
- بین دو صفحه انتخاب مشترک است
- بدون خطای JS
"""
import sys
from playwright.sync_api import sync_playwright
from _paths import INDEX_URL

INTRO_URL = INDEX_URL.replace("index.html", "intro/index.html")
res = []


def check(name, cond, extra=""):
    res.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else "  " + str(extra)))


def token(pg, name):
    return pg.evaluate(f"getComputedStyle(document.documentElement).getPropertyValue('{name}').trim()")


with sync_playwright() as p:
    b = p.chromium.launch()
    errs = []
    ctx = b.new_context(viewport={"width": 1280, "height": 900})
    pg = ctx.new_page()
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)

    pg.goto(INDEX_URL)
    pg.evaluate("localStorage.removeItem('chalesh-gamma-theme')")
    pg.reload()
    pg.wait_for_selector("#theme-toggle")
    check("پیش‌فرض: حالت روشن", pg.evaluate("document.documentElement.getAttribute('data-theme')") is None)
    check("پیش‌فرض: زمینه‌ی کرم", token(pg, "--paper").upper() == "#FFF6E5", token(pg, "--paper"))
    check("پیش‌فرض: متن ذغالی", token(pg, "--ink").upper() in ("#1F2A25", "#29352F"), token(pg, "--ink"))

    pg.click("label.trigger--theme")
    pg.wait_for_function("document.documentElement.getAttribute('data-theme') === 'dark'", timeout=3000)
    check("گزینه‌ی تاریک: data-theme=dark", pg.evaluate("document.documentElement.getAttribute('data-theme')") == "dark")
    check("گزینه‌ی تاریک: کلید روشن است (checked)", pg.is_checked("#theme-toggle"))
    check("گزینه‌ی تاریک: aria-checked=true", pg.get_attribute("#theme-toggle", "aria-checked") == "true")
    check("تاریک: زمینه‌ی تیره", token(pg, "--paper").upper() == "#13211B", token(pg, "--paper"))
    check("تاریک: مهره‌ها همان مقادیر روشن‌اند", token(pg, "--bead-0").upper() == "#D9A441")
    check("تاریک: خط هاشور روشن‌تر است", token(pg, "--hatch-0").upper() == "#E6C484", token(pg, "--hatch-0"))

    # انتخاب ذخیره می‌شود و در صفحه‌ی معرفی هم اعمال می‌شود
    check("انتخاب در localStorage ذخیره شد", pg.evaluate("localStorage.getItem('chalesh-gamma-theme')") == "dark")
    pg.goto(INTRO_URL)
    pg.wait_for_selector("#theme-toggle")
    check("صفحه‌ی معرفی: حالت تاریک را از انتخاب مشترک می‌گیرد",
          pg.evaluate("document.documentElement.getAttribute('data-theme')") == "dark")
    check("صفحه‌ی معرفی: زمینه‌ی تیره", token(pg, "--paper").upper() == "#13211B", token(pg, "--paper"))
    pg.click("label.trigger--theme")
    pg.wait_for_function("document.documentElement.getAttribute('data-theme') === null", timeout=3000)
    check("صفحه‌ی معرفی: بازگشت به روشن", pg.evaluate("document.documentElement.getAttribute('data-theme')") is None)
    check("صفحه‌ی معرفی: انتخاب روشن ذخیره شد", pg.evaluate("localStorage.getItem('chalesh-gamma-theme')") == "light")

    pg.goto(INDEX_URL)
    pg.wait_for_selector("#theme-toggle")
    check("بازگشت به بازی: حالت روشن باقی مانده", pg.evaluate("document.documentElement.getAttribute('data-theme')") is None)
    pg.click("label.trigger--theme")
    pg.wait_for_function("document.documentElement.getAttribute('data-theme') === 'dark'", timeout=3000)
    pg.wait_for_timeout(300)
    pg.reload()
    pg.wait_for_selector("#theme-toggle")
    check("بعد از بارگذاری دوباره: حالت تاریک می‌ماند",
          pg.evaluate("document.documentElement.getAttribute('data-theme')") == "dark")
    pg.evaluate("localStorage.removeItem('chalesh-gamma-theme')")
    ctx.close()

    check("بدون خطای JS یا کنسول", not errs, errs)
    b.close()

print(f"\n{sum(res)}/{len(res)} تست حالت روشن/تاریک موفق")
sys.exit(0 if all(res) else 1)
