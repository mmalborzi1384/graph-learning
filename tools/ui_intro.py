"""تست صفحه‌ی معرفی (code/intro/): خطا، محتوا، گراف‌ها، حرکت پین، کارت‌های محو متقاطع، نوار پیشرفت، پیوند از بازی.

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
        pg.wait_for_timeout(450)
    def _op(idx):
        return pg.evaluate("([sel, i]) => parseFloat(document.querySelectorAll(sel + ' .card')[i].style.opacity)", [mact, idx])
    check("بخش P₆ شش کارت دارد", pg.locator(mact + " .card").count() == 6)
    _goto(0)
    check("کارت اول P₆ در ابتدا کاملاً دیده می‌شود", _op(0) > 0.99, _op(0))
    check("شمارنده‌ی کارت‌ها: ۱ از ۶", "۱ از ۶" in pg.inner_text(mact + " [data-cards-count]"), pg.inner_text(mact + " [data-cards-count]"))
    _goto(1)
    check("در پایان بخش، کارت اثبات P₆ کاملاً دیده می‌شود", _op(5) > 0.99, _op(5))
    check("در پایان بخش، کارت اول محو شده است", _op(0) < 0.01, _op(0))
    check("شمارنده‌ی پایان: ۶ از ۶", "۶ از ۶" in pg.inner_text(mact + " [data-cards-count]"))
    _goto(2.5 / 5)
    o2, o3 = _op(2), _op(3)
    check("وسط دو کارت: هر دو نیمه‌شفاف‌اند", 0.3 < o2 < 0.7 and 0.3 < o3 < 0.7, (o2, o3))
    check("وسط دو کارت: مجموع opacity برابر ۱ است", abs(o2 + o3 - 1) < 0.02, o2 + o3)
    check("در وسط دو کارت، کارت فعال ۳ از ۶ است", "۳ از ۶" in pg.inner_text(mact + " [data-cards-count]") or "۴ از ۶" in pg.inner_text(mact + " [data-cards-count]"))
    check("صفحه هیچ‌جا بیش از عرض دید اسکرول افقی ندارد", pg.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"), pg.evaluate("[document.documentElement.scrollWidth, innerWidth]"))
    check("بخش‌های پن دیگر ریل افقی ندارند", pg.locator(".rail:not(#rail), [data-sc-pan], .act--pan, .act--stack").count() == 0)
    # نوار پیشرفت: با اسکرول پر می‌شود
    bar = "document.querySelector('.rail__fill')"
    scale = "parseFloat(({}.style.transform.match(/scaleY\\(([-0-9.]+)\\)/) || [0, 0])[1])".format(bar)
    pg.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
    pg.wait_for_timeout(120)
    s1 = pg.evaluate(scale)
    # ریل پیشرفت: عمودی، لبه‌ی راست، دور از گوشه، و هم‌اندازه با بخش‌ها
    rb = pg.evaluate("(() => { const r = document.getElementById('rail').getBoundingClientRect(); return {x: r.left, w: r.width, h: r.height, top: r.top, right: innerWidth - r.right, vw: innerWidth, vh: innerHeight}; })()")
    check("ریل پیشرفت عمودی است (ارتفاع بیشتر از عرض)", rb["h"] > rb["w"] * 4, rb)
    check("ریل پیشرفت در لبه‌ی راست صفحه است", rb["x"] > rb["vw"] * 0.85, rb)
    check("ریل پیشرفت به گوشه نچسبیده (فاصله‌ی بالا و پایین)", rb["top"] > 80 and rb["top"] + rb["h"] < rb["vh"] - 40, rb)
    check("تعداد نقاط ریل برابر تعداد بخش‌هاست", pg.evaluate("document.querySelectorAll('.rail__tick').length") == pg.evaluate("document.querySelectorAll('section[data-rail]').length") == 6)
    # نقاط ریل باید با طول واقعی بخش‌ها هم‌خوان باشند (نه فاصله‌ی برابر)
    ratios = pg.evaluate("""(() => {
      const max = document.documentElement.scrollHeight - innerHeight;
      const track = document.querySelector('.rail__track').getBoundingClientRect();
      return [...document.querySelectorAll('.rail__list li')].map((li, i) => {
        const sec = document.querySelectorAll('section[data-rail]')[i];
        const want = (sec.getBoundingClientRect().top + scrollY) / max;
        const btn = li.querySelector('.rail__dot').getBoundingClientRect();
        const got = (btn.top + btn.height / 2 - track.top) / track.height;
        return {want: want, got: got};
      });
    })()""")
    worst = max(abs(r["want"] - r["got"]) for r in ratios)
    check("نقاط ریل روی شروع واقعی بخش‌ها قرار دارند (خطا کمتر از ۲٪)", worst < 0.02, ratios)
    gaps = [ratios[i+1]["got"] - ratios[i]["got"] for i in range(len(ratios)-1)]
    check("فاصله‌ی نقاط با طول بخش‌ها تناسب دارد (نه یکسان)", max(gaps) - min(gaps) > 0.05, gaps)
    check("هر بخش برچسب دارد", pg.evaluate("[...document.querySelectorAll('.rail__label')].every(l => l.textContent.trim().length > 0)"))
    pg.evaluate("window.scrollTo(0, 0)"); pg.wait_for_timeout(150)
    check("بخش فعال در بالای صفحه نقطه‌ی اول است", pg.evaluate("document.querySelector('.rail__tick').classList.contains('is-active')"))
    pg.click(".rail__list li:nth-child(3) .rail__tick")
    pg.wait_for_timeout(1200)
    check("کلیک روی نقطه‌ی سوم، به بخش سوم می‌برد", pg.evaluate("document.querySelectorAll('.rail__tick')[2].classList.contains('is-active')"), pg.evaluate("[...document.querySelectorAll('.rail__tick')].map(t=>t.className)"))
    check("نوار پیشرفت در پایین صفحه کامل است", abs(s1 - 1) < 0.001, s1)
    pg.evaluate("window.scrollTo(0, 0)")
    pg.wait_for_timeout(120)
    s2 = pg.evaluate(scale)
    check("نوار پیشرفت در بالای صفحه صفر است", abs(s2) < 0.001, s2)

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
