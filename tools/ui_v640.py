"""تست نسخه‌ی ۶.۴.۰: تمرین هدفمند، چالش زمان‌دار، ویرایشگر کشیدنی، گزارش چاپی.

اجرا: python3 tools/ui_v640.py
"""
from playwright.sync_api import sync_playwright
from _paths import INDEX_URL

res = []
def check(name, cond, extra=""):
    res.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else "  " + str(extra)))

with sync_playwright() as p:
    b = p.chromium.launch(); errs = []
    pg = b.new_page(viewport={"width": 1280, "height": 900})
    pg.on("pageerror", lambda e: errs.append("PAGEERROR " + str(e)))
    pg.add_init_script("window.__printed = 0; window.print = () => { window.__printed++; };")
    pg.goto(INDEX_URL); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_selector("#board svg")

    # ---------- ویژگی ۲: تمرین هدفمند ----------
    pg.select_option("#graph-select", "K4")
    pg.click("#btn-reset")
    for v in (0, 1, 2):
        pg.click(f"[data-v='{v}']")
    pg.click("#btn-check"); pg.click("#btn-check2")
    check("K4 با سه مهره: احاطه‌گر ولی غیرمینیمال", "احاطه‌گر است، ولی مینیمال نیست" in pg.inner_text("#result"), pg.inner_text("#result"))
    check("دکمه‌ی تمرین هدفمند نشان داده شد", pg.locator("#btn-targeted").count() == 1)
    pg.click("#btn-targeted")
    result = pg.inner_text("#result")
    check("تمرین هدفمند: یک گراف دیگر بارگذاری شد", pg.evaluate("document.querySelector('#graph-select').value") != "K4")
    check("تمرین هدفمند: توضیح رأس زائد نمایش داده شد", "زائد است" in result, result)
    check("تمرین هدفمند: مجموعه‌ی غیرمینیمال از پیش گذاشته شد", pg.locator("#board .vertex.marked").count() >= 2, pg.locator("#board .vertex.marked").count())
    check("تمرین هدفمند: مرحله‌ی ۲ هنوز قفل است (ابتدا مرحله‌ی ۱)", pg.is_disabled("#btn-check2"))

    # ---------- ویژگی ۵: چالش زمان‌دار ----------
    pg.click("#btn-reset")
    pg.click("#btn-timed")
    check("چالش شروع شد و جعبه‌ی زمان دیده می‌شود", pg.locator("#timed-box").is_visible())
    check("چالش: شمارنده‌ی گراف ۱ از ۵", "گراف ۱ از ۵" in pg.inner_text("#timed-box"), pg.inner_text("#timed-box"))
    check("چالش: انتخاب گراف قفل است", pg.is_disabled("#graph-select"))
    check("چالش: دکمه‌ی پایان چالش", "پایان چالش" in pg.inner_text("#btn-timed"))
    for _ in range(4):
        pg.click("#btn-next")
    check("چالش: پس از ۴ گراف، گراف ۵ از ۵", "گراف ۵ از ۵" in pg.inner_text("#timed-box"), pg.inner_text("#timed-box"))
    pg.click("#btn-next")
    check("چالش: پایان بعد از ۵ گراف", "چالش تمام شد" in pg.inner_text("#timed-box"), pg.inner_text("#timed-box"))
    check("چالش تمام شده: گراف‌ها دوباره آزاد", pg.is_enabled("#graph-select"))
    check("چالش تمام شده: دکمه به شروع برگشت", "چالش زمان‌دار" in pg.inner_text("#btn-timed"))
    pg.click("#btn-timed")
    pg.click("#btn-timed")  # پایان زودهنگام
    check("پایان زودهنگام: پیام توقف", "چالش متوقف شد" in pg.inner_text("#timed-box"), pg.inner_text("#timed-box"))
    pg.click("#practice-mode")
    check("در حالت فقط تمرین، دکمه‌ی چالش غیرفعال است", pg.is_disabled("#btn-timed"))
    pg.click("#practice-mode")
    check("خروج از تمرین: چالش دوباره فعال است", pg.is_enabled("#btn-timed"))

    # ---------- ویژگی ۳: ویرایشگر کشیدنی ----------
    pg.click("#custom-builder > summary")
    pg.fill("#custom-n", "4"); pg.dispatch_event("#custom-n", "change")
    check("ویرایشگر: ۴ رأس روی صفحه", pg.locator("#pad .pad-v").count() == 4)
    before = pg.evaluate("document.querySelector('#pad [data-pv=\"0\"] circle').getAttribute('cx')")
    box = pg.locator("#pad [data-pv='0'] circle").bounding_box()
    pg.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    pg.mouse.down()
    pg.mouse.move(box["x"] + 60, box["y"] + 40, steps=8)
    pg.mouse.up()
    after = pg.evaluate("document.querySelector('#pad [data-pv=\"0\"] circle').getAttribute('cx')")
    check("کشیدن رأس: موقعیت تغییر کرد", before != after, (before, after))
    check("کشیدن رأس: یال نساخت", pg.locator("#pad .pad-edge").count() == 0)
    pg.click("#pad-mode")
    check("حالت یال روشن شد", "روشن" in pg.inner_text("#pad-mode") and pg.get_attribute("#pad-mode", "aria-pressed") == "true")
    pg.click("#pad [data-pv='0']"); pg.click("#pad [data-pv='2']")
    check("دو رأس پشت‌سرهم: یال ۱–۳ ساخته شد", pg.locator("#pad .pad-edge").count() == 1)
    check("یال ساخته‌شده در جدول تیک خورده", pg.is_checked("#custom-matrix input[aria-label='یال ۱ و ۳']"))
    pg.click("#pad [data-pv='0']"); pg.click("#pad [data-pv='2']")
    check("دوباره همان دو رأس: یال حذف شد", pg.locator("#pad .pad-edge").count() == 0)
    pg.click("#pad [data-pv='1']"); pg.click("#pad [data-pv='1']")
    check("انتخاب و لغو همان رأس: یالی ساخته نشد", pg.locator("#pad .pad-edge").count() == 0)
    pg.click("#pad [data-pv='0']"); pg.click("#pad [data-pv='1']")
    pg.click("#pad-mode")
    pg.click("#btn-custom-apply")
    check("بازی با گراف کشیده‌شده: گراف سفارشی بارگذاری شد", "گراف سفارشی بارگذاری شد" in pg.inner_text("#custom-msg"), pg.inner_text("#custom-msg"))

    # ---------- ویژگی ۱: گزارش چاپی ----------
    pg.click("#tab-scores")
    pg.click("#btn-print")
    rep = pg.evaluate("document.querySelector('#print-report').textContent")
    check("گزارش: عنوان گزارش ساخته شد", "گزارش بازی" in rep)
    check("گزارش: جدول گروه‌ها و کارنامه و سابقه وجود دارد", "گروه‌ها و امتیاز کل" in rep and "سابقه‌ی ۲۰ دور اخیر" in rep and "کارنامه:" in rep)
    check("گزارش: خالی بودن سابقه پیام دارد", "هنوز داده‌ای" in rep)
    check("گزارش: پنجره‌ی چاپ یک بار باز شد", pg.evaluate("window.__printed") == 1, pg.evaluate("window.__printed"))
    check("گزارش: هنگام چاپ کلاس printing-report روی بدنه است", pg.evaluate("document.body.classList.contains('printing-report')"))
    pg.evaluate("window.dispatchEvent(new Event('afterprint'))")
    check("گزارش: بعد از چاپ، کلاس برداشته می‌شود", not pg.evaluate("document.body.classList.contains('printing-report')"))
    pg.click("#tab-game")

    check("خطای صفحه نداریم", not errs, errs)
    print(f"\n{sum(res)}/{len(res)} بررسی موفق")
    b.close()
raise SystemExit(0 if all(res) and not errs else 1)
