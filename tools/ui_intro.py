"""تست صفحه‌ی معرفی (code/intro/): خطا، محتوا، گراف‌ها، حرکت پین، پیوند از بازی.

اجرا: python3 tools/ui_intro.py
"""
import sys
from playwright.sync_api import sync_playwright
from _paths import CODE_DIR, INDEX_URL

INTRO_URL = (CODE_DIR / "intro" / "index.html").as_uri()
res = []


def check(name, cond, extra=""):
    res.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else "  " + str(extra)))


with sync_playwright() as p:
    b = p.chromium.launch()
    errs = []
    pg = b.new_page(viewport={"width": 1280, "height": 860})
    pg.on("pageerror", lambda e: errs.append("PAGEERROR " + str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.goto(INTRO_URL)
    pg.wait_for_selector("[data-intro] svg.graph")

    # ۱. خطا و موتور
    check("صفحه‌ی معرفی خطای JS ندارد", not errs, errs)
    check("موتور scrollcraft بارگذاری شده", pg.evaluate("typeof ScrollCraft !== 'undefined'"))
    check("فونت B Nazanin در صفحه تعریف شده", pg.evaluate(
        "[...document.fonts].some(f => f.family.includes('B Nazanin'))"))
    check("متن بدنه با B Nazanin رندر می‌شود", "B Nazanin" in pg.evaluate(
        "getComputedStyle(document.body).fontFamily"))

    # ۲. قواعد سخت مهارت و قواعد پروژه
    text = pg.inner_text("main")
    check("بدون خط تیره‌ی بلند (em dash)", "\u2014" not in text)
    check("بدون شمارنده‌ی ۰۱ / ۰۶", "/ ۰" not in text and "/ 0" not in text)
    cues = pg.locator(".scroll-cue")
    check("هیچ نشانه‌ی «اسکرول کنید» در صفحه نیست (درخواست کاربر)", cues.count() == 0, cues.count())
    check("متن «اسکرول کنید» در صفحه نیست", "اسکرول کنید" not in pg.inner_text("body"))
    stray = pg.evaluate("""() => {
        const w = document.createTreeWalker(document.querySelector('main'), NodeFilter.SHOW_TEXT);
        let n, bad = [];
        while ((n = w.nextNode())) {
            if (n.textContent.includes('γ') && !(n.parentElement && n.parentElement.closest('.math, .gamma'))) bad.push(n.textContent.trim());
        }
        return bad;
    }""")
    check("همه‌ی γ در span ریاضی هستند", not stray, stray)

    # ۳. گراف‌ها: هیرو، پین، پن (سه شکل P₇ و یک شکل C₆ در پانل‌ها)
    check("گراف C₆ هیرو رسم شده", pg.locator("figure[data-graph='C6'] svg").count() >= 2)
    check("پانل‌های پن دو گراف P₇ دارند", pg.locator("figure[data-graph='P7'] svg").count() == 2)
    check("گراف‌ها شش یا هفت رأس دارند", pg.locator("svg.graph .v").count() >= 6 + 6 + 7 + 7)

    # ۳ب. مینیمال در برابر مینیمم (نسخه ۵.۰.۰): شش پانل، و در پایان همه‌ی پانل‌ها دیده می‌شوند
    mact = "section[aria-label='مینیمال در برابر مینیمم در مسیر P₆']"
    check("بخش مینیمال در برابر مینیمم وجود دارد", pg.locator(mact).count() == 1)
    check("پانل‌های P₆: پنج شکل گراف و یک پانل اثبات", pg.locator(mact + " figure[data-graph='P6'] svg").count() == 5)
    check("بخش P₆ شش پانل دارد", pg.locator(mact + " .panel").count() == 6)
    def _goto(f):
        pg.evaluate("([sel, f]) => { const el = document.querySelector(sel); const top = el.getBoundingClientRect().top + scrollY; window.scrollTo({ top: top + f * (el.offsetHeight - innerHeight), behavior: 'instant' }); }", [mact, f])
        pg.wait_for_timeout(500)
    def _visible(idx):
        return pg.evaluate("([sel, i]) => { const r = document.querySelectorAll(sel + ' .panel')[i].getBoundingClientRect(); return r.left < innerWidth && r.right > 0; }", [mact, idx])
    _goto(0)
    check("پانل اول P₆ در ابتدای بخش دیده می‌شود", _visible(0))
    _goto(1)
    check("در پایان بخش، پانل اثبات P₆ دیده می‌شود", _visible(5), pg.evaluate("(sel)=>[...document.querySelectorAll(sel+' .panel')].map(x=>Math.round(x.getBoundingClientRect().left))", mact))

    # ۴. پوشش: مرحله‌ی تعریف به پوشش کامل می‌رسد و شمارنده‌ی ۶ از ۶ را نشان می‌دهد
    reached = False
    height = pg.evaluate("document.documentElement.scrollHeight")
    for y in range(0, height, 40):
        pg.evaluate(f"window.scrollTo(0, {y})")
        pg.wait_for_timeout(20)
        if pg.evaluate("document.querySelector('[data-intro=\"definition\"]').classList.contains('is-complete')"):
            reached = True
            break
    pg.wait_for_timeout(500)
    check("پوشش کامل C₆ در بخش تعریف دیده می‌شود", reached)
    if reached:
        check("شمارنده روی ۶ از ۶ است", "۶" in pg.inner_text("[data-intro='definition'] [data-count]") and
              pg.inner_text("[data-intro='definition'] [data-count]").strip() == "۶")

    # ۵. پیوند از بازی به صفحه‌ی معرفی و برگشت
    pg.goto(INDEX_URL)
    pg.wait_for_selector("#board svg")
    check("پیوند «صفحه‌ی معرفی» در سربرگ بازی است", pg.locator("a.topbar__link[href='intro/index.html']").count() == 1)
    pg.click("a.topbar__link")
    pg.wait_for_url("**/intro/index.html")
    check("پیوند به صفحه‌ی معرفی باز می‌شود", pg.url.endswith("intro/index.html"), pg.url)

    # ۶. واکنش‌گرایی: تبلت و موبایل بدون سرریز افقی
    for w in (390, 768):
        pg.set_viewport_size({"width": w, "height": 844})
        pg.goto(INTRO_URL)
        pg.wait_for_selector("[data-intro] svg.graph")
        overflow = pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
        check(f"بدون سرریز افقی در عرض {w}", overflow <= 2, overflow)

    # ۷. کاهش حرکت: صفحه بدون خطا بارگذاری شود
    ctx = b.new_context(reduced_motion="reduce", viewport={"width": 1280, "height": 860})
    rp = ctx.new_page()
    rerrs = []
    rp.on("pageerror", lambda e: rerrs.append(str(e)))
    rp.goto(INTRO_URL)
    rp.wait_for_selector("[data-intro] svg.graph")
    check("کاهش حرکت: بدون خطا", not rerrs, rerrs)
    ctx.close()
    b.close()

print(f"\n{sum(res)}/{len(res)} تست صفحه‌ی معرفی موفق")
sys.exit(0 if all(res) else 1)
