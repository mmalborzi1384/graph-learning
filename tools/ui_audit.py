"""حسابرسی DOM و دسترس‌پذیری هر دو صفحه‌ی برنامه (بازی و معرفی).

بررسی‌ها: شناسه‌ی تکراری، دکمه و ورودی بدون نام، ورودی بدون برچسب، ارجاع aria-controls
شکسته، لینک داخلی شکسته، lang و dir، یک h1، خطای کنسول در همه‌ی تب‌ها، و پیمایش صفحه‌کلید.

اجرا: python3 tools/ui_audit.py
"""
from playwright.sync_api import sync_playwright
from _paths import CODE_DIR

res = []


def check(name, cond, extra=""):
    res.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else "  " + str(extra)))


PAGES = {"بازی": CODE_DIR / "index.html", "معرفی": CODE_DIR / "intro" / "index.html"}

DOM_AUDIT = """() => {
  const out = {};
  const ids = [...document.querySelectorAll('[id]')].map(e => e.id);
  out.dupIds = ids.filter((x, i) => ids.indexOf(x) !== i);
  out.unnamedButtons = [...document.querySelectorAll('button')].filter(b =>
      !(b.textContent.trim() || b.getAttribute('aria-label') || b.title)).map(b => b.id || b.className);
  out.unlabeledInputs = [...document.querySelectorAll('input, select, textarea')].filter(el => {
      if (el.type === 'hidden') return false;
      const id = el.id;
      const labelled = (id && document.querySelector('label[for="' + id + '"]')) ||
                       el.closest('label') || el.getAttribute('aria-label') || el.getAttribute('aria-labelledby');
      return !labelled;
  }).map(el => el.id || el.name || el.tagName);
  out.brokenAria = [];
  document.querySelectorAll('[aria-controls]').forEach(el => {
    el.getAttribute('aria-controls').split(' ').forEach(id => {
      if (!document.getElementById(id)) out.brokenAria.push(el.id + '→' + id);
    });
  });
  out.brokenLinks = [...document.querySelectorAll('a[href]')].map(a => a.getAttribute('href'))
    .filter(h => h && !h.startsWith('#') && !h.startsWith('http') && !h.startsWith('mailto'));
  out.lang = document.documentElement.lang;
  out.dir = document.documentElement.dir;
  out.h1 = document.querySelectorAll('h1').length;
  return out;
}"""

with sync_playwright() as p:
    b = p.chromium.launch()
    for name, path in PAGES.items():
        ctx = b.new_context(viewport={"width": 1280, "height": 900})
        pg = ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append("PAGEERROR " + str(e)))
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        pg.goto(path.as_uri())
        pg.wait_for_timeout(800)
        a = pg.evaluate(DOM_AUDIT)
        check(f"[{name}] شناسه‌ی تکراری نیست", not a["dupIds"], a["dupIds"])
        check(f"[{name}] هر دکمه نام دارد", not a["unnamedButtons"], a["unnamedButtons"])
        check(f"[{name}] هر ورودی برچسب دارد", not a["unlabeledInputs"], a["unlabeledInputs"])
        check(f"[{name}] ارجاع aria-controls معتبر است", not a["brokenAria"], a["brokenAria"])
        check(f"[{name}] lang=fa و dir=rtl", a["lang"] == "fa" and a["dir"] == "rtl", (a["lang"], a["dir"]))
        check(f"[{name}] یک h1 وجود دارد", a["h1"] == 1, a["h1"])
        broken = []
        for h in a["brokenLinks"]:
            target = (path.parent / h.split("#")[0]).resolve()
            if h.split("#")[0] and not target.exists():
                broken.append(h)
        check(f"[{name}] لینک‌های داخلی معتبرند", not broken, broken)

        if name == "بازی":
            # همه‌ی تب‌ها بدون خطا باز شوند
            for tab in ("tab-lab", "tab-help", "tab-game"):
                pg.click("#" + tab)
                pg.wait_for_timeout(120)
            check(f"[{name}] جابه‌جایی همه‌ی تب‌ها بدون خطا", not errs, errs)
            # پیمایش صفحه‌کلید: دکمه‌ها قابل فوکوس‌اند
            pg.click("#tab-game")
            focusable = pg.evaluate("""() => [...document.querySelectorAll('button, select, input, a[href]')]
                .filter(e => !e.disabled && e.offsetParent !== null).length""")
            check(f"[{name}] عناصر تعاملی قابل فوکوس وجود دارند", focusable > 10, focusable)
            pg.focus("#btn-check")
            pg.keyboard.press("Tab")
            active = pg.evaluate("document.activeElement && document.activeElement.id")
            check(f"[{name}] Tab فوکوس را جلو می‌برد", bool(active), active)

        check(f"[{name}] بدون خطای کنسول", not errs, errs)
        ctx.close()
    b.close()

# ---- حاشیه: عرض ۳۲۰، و حالت ذخیره‌ی خراب ----
with sync_playwright() as p:
    b = p.chromium.launch()
    for name, path in PAGES.items():
        ctx = b.new_context(viewport={"width": 320, "height": 640})
        pg = ctx.new_page()
        pg.goto(path.as_uri())
        pg.wait_for_timeout(500)
        sw = pg.evaluate("document.documentElement.scrollWidth")
        check(f"[{name}] بدون اسکرول افقی در ۳۲۰px", sw <= 320, sw)
        ctx.close()

    ctx = b.new_context(viewport={"width": 1280, "height": 900})
    pg = ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append("PAGEERROR " + str(e)))
    pg.goto(PAGES["بازی"].as_uri())
    pg.evaluate("localStorage.setItem('chalesh-gamma-state-v1', '{broken json')")
    pg.reload()
    pg.wait_for_timeout(600)
    check("[بازی] ذخیره‌ی خراب برنامه را از کار نمی‌اندازد", not errs and pg.locator("#board svg").count() == 1, errs)
    pg.evaluate("localStorage.setItem('chalesh-gamma-state-v1', JSON.stringify({graphId: 12345, records: 'x'}))")
    pg.reload()
    pg.wait_for_timeout(600)
    check("[بازی] ذخیره‌ی با مقدار نامعتبر بازیابی می‌شود", not errs and pg.locator("#board svg").count() == 1, errs)
    ctx.close()
    b.close()

print(f"\n{sum(res)}/{len(res)} بررسی حسابرسی موفق")
