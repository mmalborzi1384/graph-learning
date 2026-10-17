"""آزمون انیمیشن‌های احاطه‌گری مستقل (C6 و S4) با موتور مشترک dom-scene.js.

بررسی می‌کند:
- بدون خطای کنسول، و تعریف‌شدن DomScene
- پوشش مجموعه‌ی انتخاب‌ها در t = 0, 2.5, 4, 7 (C6: 0,3,6,6 ؛ S4: 0,4,4,4)
- نگاشت اسکرول: پایان مسیر = ۱۰ ثانیه، نیمه‌ی مسیر = ۵ ثانیه
- در ۸ ثانیه گراف کامل نمایش داده می‌شود؛ در ۱۰ ثانیه محو شده است
- کاهش حرکت: زمان ثابت ۸ ثانیه، بدون اسکرول
- بدون اسکرول افقی در ۳۷۵ پیکسل
"""
import pathlib
import sys

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGES = {
    "C6": ("code/animations/cycle_c6.html", [0, 3, 6, 6]),
    "S4": ("code/animations/star_s4.html", [0, 4, 4, 4]),
}
res = []
INIT = """
(() => {
  Object.defineProperty(window, 'DomScene', {
    configurable: true,
    set(v) { this._d = v; },
    get() {
      const d = this._d;
      if (!d || d.__w) return d;
      const c = d.mount;
      d.mount = (cfg) => { const s = c(cfg); window.__scene = s; return s; };
      d.__w = true;
      return d;
    }
  });
})();
"""


def check(name, cond, extra=""):
    res.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if extra != "" else ""))


def new_page(b, errs, width, height=900, reduced=None, url=None):
    ctx = b.new_context(viewport={"width": width, "height": height},
                        reduced_motion=reduced or "no-preference")
    pg = ctx.new_page()
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.goto(url.as_uri())
    pg.wait_for_function("window.__scene && window.__scene.frames() > 0", timeout=10000)
    return ctx, pg


def canvas_len(pg):
    return pg.evaluate("document.getElementById('scene').toDataURL().length")


def scroll_to(pg, y):
    pg.evaluate(f"window.scrollTo(0, {y})")
    pg.wait_for_timeout(1800)


with sync_playwright() as p:
    b = p.chromium.launch()
    errs = []
    for label, (rel, expected) in PAGES.items():
        url = ROOT / rel
        check(f"{label}: فایل وجود دارد", url.exists(), rel)
    # صحنه‌ها با create ساخته می‌شوند؛ برای دسترسی به کنترل، نسخه‌ی آزمون از create را پوشش می‌دهیم
    for label, (rel, expected) in PAGES.items():
        url = ROOT / rel
        ctx = b.new_context(viewport={"width": 1280, "height": 900})
        pg = ctx.new_page()
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        pg.add_init_script(INIT)
        pg.goto(url.as_uri())
        pg.wait_for_function("window.__scene && window.__scene.frames() > 0", timeout=10000)
        check(f"{label}: بالای صفحه زمان ۰ است", pg.evaluate("window.__scene.time()") == 0)
        cov = [pg.evaluate(f"window.__scene.coverageAt({t})") for t in (0, 2.5, 4, 7)]
        check(f"{label}: پوشش در t = 0, 2.5, 4, 7 برابر {expected} است", cov == expected, cov)
        check(f"{label}: scrubEnd برابر ۱۰ ثانیه است", pg.evaluate("window.__scene.scrubEnd") == 10)
        check(f"{label}: صفحه قابل اسکرول است",
              pg.evaluate("document.documentElement.scrollHeight > innerHeight + 200"))

        scroll_to(pg, int(0.5 * 1.5 * 900))
        t_half = pg.evaluate("window.__scene.time()")
        check(f"{label}: نیمه‌ی مسیر زمان ۵ ثانیه است", abs(t_half - 5.0) < 0.1, t_half)

        scroll_to(pg, int(0.8 * 1.5 * 900))
        t8 = pg.evaluate("window.__scene.time()")
        png8 = canvas_len(pg)
        check(f"{label}: در ۸ ثانیه گراف کامل نمایش داده می‌شود", abs(t8 - 8.0) < 0.05 and png8 > 5000, (t8, png8))

        scroll_to(pg, 5000)
        t10 = pg.evaluate("window.__scene.time()")
        png10 = canvas_len(pg)
        check(f"{label}: پایان مسیر زمان ۱۰ ثانیه است", abs(t10 - 10.0) < 1e-6, t10)
        check(f"{label}: در ۱۰ ثانیه صحنه محو شده است", png10 < png8, (png10, png8))
        pg.close(); ctx.close()

        # کاهش حرکت: زمان ثابت ۸ ثانیه، بدون اسکرول
        ctx = b.new_context(viewport={"width": 1280, "height": 900}, reduced_motion="reduce")
        pg = ctx.new_page()
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        pg.add_init_script(INIT)
        pg.goto(url.as_uri())
        pg.wait_for_function("window.__scene && window.__scene.frames() > 0", timeout=10000)
        scroll_to(pg, 400)
        check(f"{label}: کاهش حرکت، زمان ثابت ۸ ثانیه", abs(pg.evaluate("window.__scene.time()") - 8.0) < 1e-6)
        pg.close(); ctx.close()

        # موبایل: بدون اسکرول افقی
        ctx = b.new_context(viewport={"width": 375, "height": 812})
        pg = ctx.new_page()
        pg.goto(url.as_uri())
        pg.wait_for_timeout(500)
        sw = pg.evaluate("document.documentElement.scrollWidth")
        check(f"{label}: بدون اسکرول افقی در ۳۷۵px", sw <= 375, sw)
        pg.close(); ctx.close()

    check("بدون خطای JS یا کنسول", not errs, errs)
    b.close()

print(f"\n{sum(res)}/{len(res)} تست انیمیشن موفق")
sys.exit(0 if all(res) else 1)
