"""آزمون تریگرهای نسخه ۶.۴.۰: کلید حالت بازی (امتیازی | فقط تمرین) و محو شدن بخش‌های امتیازی.

بررسی می‌کند:
- پیش‌فرض: امتیازی؛ کلید حالت بازی روشن نیست و بخش‌های امتیازی نمایان‌اند
- کلید حالت بازی را کلیک کنیم: body.mode-practice؛ تب کارنامه، کلید دو گروهی، خط امتیاز زنده،
  ایستگاه ۵ و قانون‌های امتیازی پنهان می‌شوند (display: none پس از محو)
- در تمرین، پیام‌های نتیجه بدون عدد امتیاز هستند و دکمه‌ی «گراف بعدی» برچسب ساده دارد
- برگشت به امتیازی: بخش‌ها دوباره نمایان‌اند؛ ثبت امتیاز دوباره کار می‌کند
- انتخاب حالت بعد از بارگذاری دوباره حفظ می‌شود
- کلید با صفحه‌کلید (Space) کار می‌کند
- در موبایل و دسکتاپ هیچ افقی‌اسکرولی نیست و کلیدها داخل نما هستند
- بدون خطای JS یا کنسول
"""
import sys
from playwright.sync_api import sync_playwright
from _paths import INDEX_URL

res = []


def check(name, cond, extra=""):
    res.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else "  " + str(extra)))


def shown(pg, sel):
    """آیا عنصر در صفحه قابل دیدن است (display و opacity)."""
    return pg.evaluate("""(sel) => {
        const el = document.querySelector(sel);
        if (!el) return false;
        const cs = getComputedStyle(el);
        return cs.display !== 'none' && cs.visibility !== 'hidden' && parseFloat(cs.opacity) > 0.5;
    }""", sel)


SCORING = ["#tab-scores", "#team-mode", "#live-score", "#st5-go"]

with sync_playwright() as p:
    b = p.chromium.launch()
    errs = []
    for label, vp, mob in [("دسکتاپ", {"width": 1280, "height": 900}, False), ("موبایل", {"width": 390, "height": 844}, True)]:
        ctx = b.new_context(viewport=vp, is_mobile=mob, has_touch=mob)
        pg = ctx.new_page()
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        pg.goto(INDEX_URL)
        pg.evaluate("localStorage.clear()")
        pg.reload()
        pg.wait_for_selector("#practice-mode", state="attached")
        pg.wait_for_timeout(500)

        check(f"[{label}] پیش‌فرض: حالت امتیازی", not pg.is_checked("#practice-mode")
              and "mode-practice" not in pg.evaluate("document.body.className"))
        check(f"[{label}] پیش‌فرض: بخش‌های امتیازی نمایان‌اند",
              all(shown(pg, s) for s in SCORING), [s for s in SCORING if not shown(pg, s)])

        # بازی یک گراف را در حالت امتیازی انجام می‌دهیم: پیام با امتیاز
        pg.click("#btn-check")
        pg.wait_for_timeout(200)
        pg.click("[data-v='0']")
        pg.click("#btn-check")
        pg.wait_for_timeout(300)
        check(f"[{label}] امتیازی: پیام نتیجه عدد امتیاز دارد", "امتیاز" in pg.inner_text("#result"), pg.inner_text("#result")[:80])

        # کلید حالت بازی در تب بازی است: کارنامه را باز می‌کنیم، برمی‌گردیم و به تمرین می‌رویم
        pg.click("#tab-scores")
        pg.wait_for_timeout(200)
        pg.click("#tab-game")
        pg.wait_for_timeout(200)
        pg.click("label.trigger--mode")
        pg.wait_for_timeout(900)
        check(f"[{label}] تمرین: body.mode-practice", "mode-practice" in pg.evaluate("document.body.className"))
        check(f"[{label}] تمرین: کلید حالت بازی روشن است", pg.is_checked("#practice-mode"))
        check(f"[{label}] تمرین: تب بازی باز است", pg.locator("#view-game").is_visible())
        hidden = [s for s in SCORING if pg.evaluate("(s)=>{const e=document.querySelector(s); if(!e) return true; const h=e.closest('.scoring')||e; return getComputedStyle(h).display==='none';}", s)]
        check(f"[{label}] تمرین: بخش‌های امتیازی پنهان‌اند", len(hidden) == len(SCORING), [s for s in SCORING if s not in hidden])
        check(f"[{label}] تمرین: ایستگاه ۵ پنهان است",
              pg.evaluate("getComputedStyle(document.querySelector('#st5-go').closest('article')).display") == "none")
        check(f"[{label}] تمرین: قانون‌های امتیازی پنهان‌اند",
              pg.evaluate("[...document.querySelectorAll('li.scoring')].every(li => getComputedStyle(li).display === 'none')"))

        # بازی در تمرین: پیام بدون امتیاز
        pg.click("[data-v='1']")
        pg.click("#btn-check")
        pg.wait_for_timeout(300)
        msg = pg.inner_text("#result")
        check(f"[{label}] تمرین: پیام نتیجه بدون عدد امتیاز", "امتیاز" not in msg, msg[:120])
        check(f"[{label}] تمرین: دکمه‌ی گراف بعدی برچسب ساده دارد", pg.inner_text("#btn-next").strip() == "گراف بعدی")

        # برگشت به امتیازی
        pg.click("label.trigger--mode")
        pg.wait_for_timeout(900)
        check(f"[{label}] برگشت: بخش‌های امتیازی دوباره نمایان‌اند",
              all(shown(pg, s) for s in SCORING), [s for s in SCORING if not shown(pg, s)])
        check(f"[{label}] برگشت: دکمه‌ی بعدی برچسب امتیازی دارد", "بدون امتیاز" in pg.inner_text("#btn-next") or "ثبت" in pg.inner_text("#btn-next"), pg.inner_text("#btn-next"))

        # حفظ انتخاب بعد از بارگذاری دوباره
        pg.click("label.trigger--mode")
        pg.wait_for_timeout(500)
        pg.reload()
        pg.wait_for_selector("#practice-mode", state="attached")
        pg.wait_for_timeout(500)
        check(f"[{label}] حالت تمرین بعد از بارگذاری حفظ شد", "mode-practice" in pg.evaluate("document.body.className"))

        # صفحه‌کلید: فوکوس روی کلید و Space
        pg.focus("#practice-mode")
        pg.keyboard.press("Space")
        pg.wait_for_timeout(900)
        check(f"[{label}] Space کلید را به امتیازی برمی‌گرداند", not pg.is_checked("#practice-mode"))

        # طرح: بدون اسکرول افقی و کلیدها در نما
        sw = pg.evaluate("document.documentElement.scrollWidth")
        check(f"[{label}] بدون اسکرول افقی", sw <= vp["width"], sw)
        box = pg.evaluate("(()=>{const r=document.querySelector('label.trigger--mode').getBoundingClientRect(); return [r.left>=0, r.right<=innerWidth];})()")
        check(f"[{label}] کلید حالت بازی داخل نماست", all(box), box)
        ctx.close()

    check("بدون خطای JS یا کنسول", not errs, errs)
    b.close()

print(f"\n{sum(res)}/{len(res)} تست تریگرهای حالت بازی موفق")
sys.exit(0 if all(res) else 1)
