"""آزمون پس‌زمینه‌ی اسکرول صفحه‌ی اصلی (نسخه ۶.۳.۰: هر تب یک انیمیشن دارد).

بررسی می‌کند:
- ساختار: #bg-animation اولین فرزند body، ثابت، z-index: -1، pointer-events: none، aria-hidden
- پوشش صحنه با توکن‌های حالت روشن/تاریک (--veil-a / --veil-b)
- چهار صحنه؛ هر تب صحنه‌ی خودش را دارد (بازی: پترسن، کارنامه: C₆، آزمایشگاه: S₄، تعاریف: P₇)
- هر تب: زمان ۰ در بالای تب، ۵ در نیمه، ۱۰ در پایین؛ برگشت با بالا آمدن اسکرول
- پوشش هر صحنه در زمان‌های مشخص؛ گراف کامل در ۸ ثانیه
- طول فضای انتهای هر تب ۶۰٪ نما؛ بدون اسکرول افقی
- تغییر حالت روشن/تاریک: رنگ بوم دوباره خوانده می‌شود
- کاهش حرکت: زمان ثابت ۸ ثانیه‌ی صحنه‌ی فعال
- بدون خطای JS یا کنسول
"""
import pathlib
import sys

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
URL = (ROOT / "code" / "index.html").as_uri()
CSS = (ROOT / "code" / "css" / "petersen-bg.css").read_text(encoding="utf-8")
STYLE = (ROOT / "code" / "style.css").read_text(encoding="utf-8")
VH = 900
res = []

INIT = """
(() => {
  Object.defineProperty(window, 'DomScene', {
    configurable: true,
    set(v) { this._d = v; },
    get() {
      const d = this._d;
      if (!d || d.__w) return d;
      const m = d.mount;
      d.mount = (cfg) => { const s = m(cfg); window.__bg = s; return s; };
      d.__w = true;
      return d;
    }
  });
})();
"""

TABS = ["game", "scores", "lab", "help"]  # ترتیب صحنه‌ها: پترسن، C₆، S₄، P₇


def check(name, cond, extra=""):
    res.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if extra != "" else ""))


def new_page(b, errs, width, height=VH, reduced=None, theme=None):
    ctx = b.new_context(viewport={"width": width, "height": height},
                        reduced_motion=reduced or "no-preference")
    pg = ctx.new_page()
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.add_init_script(INIT)
    pg.goto(URL)
    if theme:
        pg.evaluate(f"localStorage.setItem('chalesh-gamma-theme', '{theme}')")
        pg.reload()
    pg.wait_for_function("window.__bg && window.__bg.frames() > 0", timeout=10000)
    return ctx, pg


def tab(pg, name, settle=300):
    pg.click(f"#tab-{name}")
    pg.wait_for_timeout(settle)


EPS = 0.15  # هموارسازی حرکت: زمان محلی تا این مقدار با هدف فاصله دارد


def scroll_frac(pg, f, settle=2200):
    """اسکرول به نسبت f (۰ تا ۱) از بازه‌ی اسکرول بخش فعال."""
    pg.evaluate("""(f) => {
        const el = document.querySelector('.view.active');
        const top = el.getBoundingClientRect().top + scrollY;
        const range = el.offsetHeight - innerHeight;
        scrollTo(0, top + f * range);
    }""", f)
    pg.wait_for_timeout(settle)


def active_scene(pg):
    return pg.evaluate("window.__bg.scene()")


def local_time(pg):
    return pg.evaluate("window.__bg.time()")


with sync_playwright() as p:
    b = p.chromium.launch()
    errs = []

    # ---- ۱. ساختار و CSS ----
    ctx, pg = new_page(b, errs, 1280)
    st = pg.evaluate("""() => {
        const el = document.getElementById('bg-animation');
        const cs = getComputedStyle(el);
        return {
          first: document.body.firstElementChild.id,
          pos: cs.position, z: cs.zIndex, pe: cs.pointerEvents, ov: cs.overflow,
          aria: el.getAttribute('aria-hidden'),
          canvas: !!el.querySelector('canvas'),
          w: el.getBoundingClientRect().width, h: el.getBoundingClientRect().height,
          vw: innerWidth, vh: innerHeight,
        };
    }""")
    check("#bg-animation اولین فرزند body است", st["first"] == "bg-animation", st["first"])
    check("position: fixed", st["pos"] == "fixed", st["pos"])
    check("z-index: -1", st["z"] == "-1", st["z"])
    check("pointer-events: none", st["pe"] == "none", st["pe"])
    check("overflow: hidden", st["ov"] == "hidden", st["ov"])
    check("aria-hidden=\"true\"", st["aria"] == "true", st["aria"])
    check("اندازه برابر نمای دید", abs(st["w"] - st["vw"]) < 1 and abs(st["h"] - st["vh"]) < 1, st)
    check("canvas داخل نشانه ساخته شده است", st["canvas"])
    check("پوشش با توکن‌های روشن/تاریک است", "var(--veil-a)" in CSS and "var(--veil-b)" in CSS)
    check("پنل‌ها نیمه‌شفاف‌اند (--panel با آلفای کمتر از ۱)", "--panel: rgba(255, 251, 243, 0.84)" in STYLE)
    check("چهار صحنه: یکی برای هر تب", pg.evaluate("window.__bg.count") == 4)
    runway_ok = []
    for t in TABS:
        tab(pg, t)
        runway_ok.append(abs(pg.evaluate("document.querySelector('.view.active .scroll-runway').getBoundingClientRect().height") - 0.6 * VH) < 2)
    check("فضای انتهای هر تب ۶۰٪ نما است", all(runway_ok), runway_ok)

    # ---- ۲. هر تب صحنه‌ی خودش را دارد ----
    for i, t in enumerate(TABS):
        tab(pg, t)
        scroll_frac(pg, 0.0, 600)
        check(f"تب {t}: صحنه‌ی {i}", active_scene(pg) == i, active_scene(pg))
    tab(pg, "game")

    # ---- ۳. زمان محلی: بالا = ۰، نیمه = ۵، پایین = ۱۰ (برای هر تب) ----
    for i, t in enumerate(TABS):
        tab(pg, t)
        scroll_frac(pg, 0.0, 600)
        t0 = local_time(pg)
        scroll_frac(pg, 0.5)
        tm = local_time(pg)
        scroll_frac(pg, 1.0)
        t1 = local_time(pg)
        check(f"تب {t}: بالا ۰، نیمه ۵، پایین ۱۰",
              abs(t0) < EPS and abs(tm - 5.0) < EPS and abs(t1 - 10.0) < EPS, (t0, round(tm, 2), t1))

    # ---- ۴. برگشت با بالا آمدن اسکرول (تب پترسن) ----
    tab(pg, "game")
    scroll_frac(pg, 1.0)
    scroll_frac(pg, 0.3)
    check("با بالا آمدن اسکرول، زمان برمی‌گردد", abs(local_time(pg) - 3.0) < 0.1, round(local_time(pg), 2))

    # ---- ۵. پوشش هر صحنه ----
    # پترسن (صحنه ۰): ۰، ۴، ۷، ۱۰ | C₆ (۱): ۰، ۳، ۶، ۶ | S₄ (۲): ۰، ۴، ۴، ۴ | P₇ (۳): ۰، ۳، ۶، ۷
    cov = pg.evaluate("""() => {
        const out = {};
        [0,1,2,3].forEach(k => { out[k] = [0, 2.5, 4, 7].map(t => window.__bg.coverageAt(t, k)); });
        return out;
    }""")
    check("پوشش پترسن برابر ۰، ۴، ۷، ۱۰", cov["0"] == [0, 4, 7, 10], cov["0"])
    check("پوشش C₆ برابر ۰، ۳، ۶، ۶", cov["1"] == [0, 3, 6, 6], cov["1"])
    check("پوشش S₄ برابر ۰، ۴، ۴، ۴", cov["2"] == [0, 4, 4, 4], cov["2"])
    check("پوشش P₇ برابر ۰، ۳، ۶، ۷", cov["3"] == [0, 3, 6, 7], cov["3"])

    # ---- ۶. گراف کامل در ۸ ثانیه، برای هر صحنه ----
    for i, t in enumerate(TABS):
        tab(pg, t)
        scroll_frac(pg, 0.8, 600)  # زمان ۸ برای هر صحنه
        check(f"صحنه‌ی {i}: در ۸ ثانیه گراف کامل است", abs(local_time(pg) - 8.0) < EPS, round(local_time(pg), 3))
    tab(pg, "game")

    # ---- ۷. تغییر تب: صحنه‌ی تازه از ابتدا ----
    scroll_frac(pg, 1.0, 600)
    tab(pg, "help")
    check("تغییر تب: صفحه به بالا برمی‌گردد", pg.evaluate("scrollY") == 0)
    check("تغییر تب: زمان صحنه‌ی تازه صفر است", abs(local_time(pg)) < EPS, local_time(pg))

    # ---- ۸. بدون اسکرول افقی و اندازه‌ی گره در نماهای مختلف ----
    ctx.close()
    for w, h in [(1280, 900), (390, 844), (768, 1024)]:
        ctx, pg = new_page(b, errs, w, h)
        sw = pg.evaluate("document.documentElement.scrollWidth")
        check(f"بدون اسکرول افقی در {w}px", sw <= w, sw)
        npx = pg.evaluate("window.__bg.nodePx()")
        check(f"شعاع گره در {w}×{h} حداقل ۱۲ پیکسل است", npx >= 12, round(npx, 1))
        ctx.close()

    # ---- ۹. حالت تاریک: رنگ بوم دوباره خوانده می‌شود ----
    ctx, pg = new_page(b, errs, 1280)
    light_bg = pg.evaluate("window.__bg.colors().BG")
    pg.click("#theme-toggle")
    pg.wait_for_timeout(300)
    dark_bg = pg.evaluate("window.__bg.colors().BG")
    check("حالت تاریک: زمینه‌ی بوم تیره می‌شود", light_bg.upper() == "#FFF6E5" and dark_bg.upper() == "#13211B",
          (light_bg, dark_bg))
    pg.click("#theme-toggle")
    pg.wait_for_timeout(200)
    check("بازگشت به روشن: زمینه‌ی بوم روشن است", pg.evaluate("window.__bg.colors().BG").upper() == "#FFF6E5")
    ctx.close()

    # ---- ۱۰. کاهش حرکت: زمان ثابت ۸ ثانیه‌ی صحنه‌ی فعال ----
    ctx, pg = new_page(b, errs, 1280, reduced="reduce")
    check("کاهش حرکت: زمان ثابت ۸ ثانیه", abs(local_time(pg) - 8.0) < 1e-6, local_time(pg))
    f1 = pg.evaluate("window.__bg.frames()")
    pg.evaluate("scrollTo(0, 400)")
    pg.wait_for_timeout(500)
    check("کاهش حرکت: اسکرول فریم جدیدی نمی‌سازد", pg.evaluate("window.__bg.frames()") == f1)
    ctx.close()

    check("بدون خطای JS یا کنسول", not errs, errs)
    b.close()

print(f"\n{sum(res)}/{len(res)} تست پس‌زمینه‌ی توالی موفق")
sys.exit(0 if all(res) else 1)
