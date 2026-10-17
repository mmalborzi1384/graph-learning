"""تست: گراف تصادفی بعد از ثبت، کارنامه‌های چندگانه، صفر کردن، مهاجرت و ماندگاری."""
from playwright.sync_api import sync_playwright
from _paths import INDEX_URL, TOOLS_DIR, table_text
import sys
URL = INDEX_URL
res = []
def check(name, cond, extra=""):
    res.append(bool(cond)); print(("PASS " if cond else "FAIL ") + name + ("" if cond else "  " + str(extra)))
with sync_playwright() as p:
    b = p.chromium.launch(); errs = []
    pg = b.new_page(viewport={"width": 1280, "height": 900})
    pg.on("pageerror", lambda e: errs.append("PAGEERROR " + str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.goto(URL); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_selector("#board svg")

    # ۱. ثبت و گراف بعدی => گراف تصادفی متفاوت
    g0 = pg.inner_text("#graph-meta")
    pg.click("#tab-game")
    pg.click("[data-v='0']"); pg.click("[data-v='2']"); pg.click("#btn-check"); pg.click("#btn-check2")
    pg.click("#tab-game")
    pg.click("#btn-next")
    g1 = pg.inner_text("#graph-meta")
    check("ثبت و گراف بعدی گراف را عوض کرد", g0 != g1, (g0, g1))
    check("امتیاز ثبت شد (۱۵)", "۱۵" in table_text(pg, "#score-body"))
    # چند بار: هیچ‌وقت همان گراف نباشد
    same = 0
    for _ in range(6):
        before = pg.inner_text("#graph-meta")
        pg.click("#tab-game")
        pg.click("#btn-next")
        if pg.inner_text("#graph-meta") == before: same += 1
    check("گراف بعدی هرگز همان گراف قبلی نیست", same == 0, same)

    # ۲. کارنامه‌ی جدید
    pg.click("#tab-scores")
    pg.fill("#card-name", "تیم قرمز"); pg.click("#btn-card-add")
    pg.click("#tab-scores")
    opts = pg.inner_text("#card-select")
    check("کارنامه‌ی جدید ساخته و فعال شد", "تیم قرمز" in opts and pg.input_value("#card-select") == "1", opts)
    check("کارنامه‌ی جدید خالی است", pg.locator("#records-body tr td:nth-child(2)").first.inner_text() == "۰")
    # امتیاز در کارنامه‌ی جدید ثبت شود
    n_v = int(pg.locator(".vertex").count())
    pg.click("#tab-game")
    for i in range(n_v): pg.click(f"[data-v='{i}']")  # همه‌ی رأس‌ها: همیشه احاطه‌گر
    pg.click("#tab-game")
    pg.click("#btn-check"); pg.click("#btn-next")
    rec_new = table_text(pg, "#records-body")
    check("امتیاز در کارنامه‌ی فعال ثبت شد (تلاش=1)", any(l.split("\t")[1] == "۱" for l in rec_new.splitlines() if "\t" in l), rec_new[:160])
    # کارنامه‌ی اول دست‌نخورده
    pg.click("#tab-scores")
    pg.select_option("#card-select", "0")
    check("کارنامه‌ی اول بدون تغییر است", "تلاش" in pg.inner_text("#records-table"))
    total_first = sum(int(x) for x in pg.locator("#records-body tr td:nth-child(2)").all_inner_texts())
    check("کارنامه‌ی اول اطلاعات قبلی را دارد", total_first >= 1, total_first)

    # نام تکراری
    pg.click("#tab-scores")
    pg.select_option("#card-select", "1")
    pg.click("#tab-scores")
    pg.fill("#card-name", "تیم قرمز"); pg.click("#btn-card-add")
    check("نام تکراری پذیرفته نمی‌شود", "وجود دارد" in pg.inner_text("#card-msg"), pg.inner_text("#card-msg"))
    # نام خالی => پیش‌فرض
    pg.click("#tab-scores")
    pg.fill("#card-name", ""); pg.click("#btn-card-add")
    check("نام خالی، نام پیش‌فرض می‌گیرد", pg.locator("#card-select option").count() == 3, pg.locator("#card-select option").count())

    # نام پیش‌فرض تکراری نمی‌سازد
    pg.click("#tab-scores")
    pg.fill("#card-name", ""); pg.click("#btn-card-add")
    pg.click("#tab-scores")
    names = pg.locator("#card-select option").all_inner_texts()
    check("نام پیش‌فرض یکتا است", len(names) == len(set(names)), names)

    # ۳. صفر کردن کارنامه‌ی فعال
    pg.click("#tab-scores")
    pg.select_option("#card-select", "1")
    pg.once("dialog", lambda d: d.accept())
    pg.click("#tab-scores")
    pg.click("#btn-card-reset")
    check("صفر کردن، کارنامه‌ی فعال را پاک می‌کند", pg.locator("#records-body tr").count() > 0 and "—" in table_text(pg, "#records-body") and "C₄\t1" not in table_text(pg, "#records-body"), table_text(pg, "#records-body")[:200])
    check("صفر کردن کارنامه‌ی دیگر را پاک نمی‌کند", (pg.select_option("#card-select", "0") or True) and "C₄\t" in table_text(pg, "#records-body"))
    pg.once("dialog", lambda d: d.dismiss())
    pg.click("#tab-scores")
    pg.click("#btn-card-reset")
    check("لغو صفر کردن، داده‌ها را نگه می‌دارد", "C₄\t" in table_text(pg, "#records-body"))

    # ۴. ماندگاری بعد از رفرش
    pg.reload(); pg.wait_for_selector("#board svg")
    check("کارنامه‌ها بعد از رفرش حفظ شدند", pg.locator("#card-select option").count() >= 3 and "تیم قرمز" in pg.inner_text("#card-select"))
    check("کارنامه‌ی فعال بعد از رفرش حفظ شد", pg.input_value("#card-select") == "0", pg.input_value("#card-select"))

    # ۵. مهاجرت از نسخه‌ی قبلی (records تکی)
    pg.evaluate("""localStorage.setItem('chalesh-gamma-state-v1', JSON.stringify({graphId:'C4', marks:0, teamMode:false, teams:[{name:'A',score:0,rounds:0},{name:'B',score:0,rounds:0}], active:0, history:[], records:{C4:{name:'C4', attempts:2, best:10}}, custom:{n:4,edges:[]}}))""")
    pg.reload(); pg.wait_for_selector("#board svg")
    check("مهاجرت: کارنامه‌ی قدیمی به «کارنامه ۱» تبدیل شد", "کارنامه ۱" in pg.inner_text("#card-select") and "۱۰" in table_text(pg, "#records-body"), table_text(pg, "#records-body")[:150])

    # ۶. داده‌ی خراب
    pg.evaluate("localStorage.setItem('chalesh-gamma-state-v1', '{bad json')")
    pg.reload(); pg.wait_for_selector("#board svg")
    check("داده‌ی خراب برنامه را نمی‌شکند", pg.locator("#card-select option").count() >= 1)
    b.close()
check("کنسول بدون خطا", not errs, "; ".join(errs))
print("\n%d/%d passed" % (sum(res), len(res)))
sys.exit(0 if all(res) and not errs else 1)
