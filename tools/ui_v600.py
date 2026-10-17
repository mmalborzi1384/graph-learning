import re
"""تست نسخه‌ی ۶.۳.۰: رنگ‌بندی پوشش، همه‌ی مینیمم‌ها، رسم بر اساس n و γ، تمرین مینیمال،
ایستگاه ۴ (مینیمال در برابر مینیمم)، و متن راهنما. اجرا: python3 tools/ui_v600.py"""
import sys
from playwright.sync_api import sync_playwright
from _paths import INDEX_URL, table_text

PALETTE0 = "#d9a441"  # رنگ مهره‌ی رأس ۱ (--bead-0 در style.css)
BEAD_HEX = ["#d9a441", "#7fa886", "#5fa7a0", "#d4825e", "#c9708a", "#9b88c7", "#6f9bc4", "#b8a24e", "#8db35e", "#b07aa8"]
res = []

def clean(s):
    """حذف نویسه‌های ایزوله‌ی یونیکد (U+2066/U+2069) برای مقایسه‌ی متن."""
    return s.replace("\u2066", "").replace("\u2069", "")

def FA(x):
    """عدد لاتین را به رقم فارسی تبدیل می‌کند (همان نمایش بازی)."""
    return str(x).translate(str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹'))
def check(name, cond, extra=""):
    res.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else "  " + str(extra)))

def fill_of(pg, v):
    """رنگ inline رأس؛ مرورگر hex را به rgb() و url را با نقل‌قول برمی‌گرداند، پس نرمال می‌کنیم."""
    raw = pg.evaluate(f"document.querySelector(\".vertex[data-v='{v}'] .vertex-bg\").style.fill")
    if raw.startswith("url("):
        return "url(#" + raw.split("#", 1)[1].rstrip(")").strip('"') + ")"
    return raw

def hexify(rgb):
    """rgb(r, g, b) را به hex کوچک تبدیل می‌کند تا با رنگ‌های مهره مقایسه شود؛ var(--bead-i) به hex نگاشت می‌شود."""
    if rgb.startswith("var(--bead-"):
        return BEAD_HEX[int(rgb[len("var(--bead-"):].split(")")[0])]
    if not rgb.startswith("rgb("):
        return rgb
    r, g, b = [int(x) for x in rgb[4:-1].split(",")]
    return "#%02x%02x%02x" % (r, g, b)

with sync_playwright() as p:
    b = p.chromium.launch(); errs = []
    pg = b.new_page(viewport={"width": 1280, "height": 900})
    pg.on("pageerror", lambda e: errs.append("PAGEERROR " + str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.goto(INDEX_URL); pg.evaluate("localStorage.clear()"); pg.reload()
    pg.wait_for_selector("#board svg")

    # ۱. رنگ‌بندی پوشش روی C4 (رئوس ۱..۴ در حلقه)
    pg.select_option("#graph-select", "C4")
    pg.click("[data-v='0']")  # مهره روی رأس ۱
    check("مهره رنگ خودش را دارد", hexify(fill_of(pg, 0)) == PALETTE0, fill_of(pg, 0))
    check("رأس پوشش‌داده‌شده هاشور با رنگ مهره دارد", fill_of(pg, 1) == "url(#hatch-0)", fill_of(pg, 1))
    check("مهره هیچ بخش رنگی دیگری ندارد", pg.locator(".vertex[data-v='0'] .vertex-part").count() == 0)
    pg.click("[data-v='2']")  # مهره روی رأس ۳: رأس ۲ و ۴ هر دو زیر پوشش دو مهره‌اند
    check("پوشش مشترک: دو بخش رنگی", pg.locator(".vertex[data-v='1'] .vertex-part").count() == 2)
    check("پوشش مشترک: حاشیه‌ی دایره روی بخش‌ها", pg.locator(".vertex[data-v='1'] .vertex-ring").count() == 1)
    parts = pg.evaluate("[...document.querySelectorAll(\".vertex[data-v='1'] .vertex-part\")].map(e => e.getAttribute('style'))")
    check("بخش‌های پوشش مشترک هر دو رنگ مهره‌ها را دارند",
          any("hatch-0" in x for x in parts) and any("hatch-2" in x for x in parts), parts)
    check("مهره‌ی انتخاب‌شده در پوشش مشترک یکدست می‌ماند", pg.locator(".vertex[data-v='0'] .vertex-part").count() == 0
          and hexify(fill_of(pg, 0)) == PALETTE0)
    check("مهره‌ی رأس ۳ رنگ خودش را دارد", hexify(fill_of(pg, 2)) == "#5fa7a0", fill_of(pg, 2))
    pg.click("#btn-reset")

    # ۲. همه‌ی مجموعه‌های مینیمم در کادر γ
    pg.click("#btn-gamma")
    chips = pg.locator("#gamma-sets .set-chip").count()
    check("C4: شش مجموعه‌ی مینیمم در فهرست است", chips == 6, chips)

    # ۳. رسم بر اساس n و γ
    for n, k in [(6, 2), (7, 3), (5, 5), (10, 1), (9, 4)]:
        pg.evaluate("document.querySelector('#gen-builder').open=true")
        pg.fill("#gen-n", str(n)); pg.fill("#gen-k", str(k)); pg.click("#btn-generate")
        msg = pg.inner_text("#gen-msg")
        vcount = pg.locator(".board .vertex").count()
        check(f"رسم n={n} γ={k}: {n} رأس و γ درست", vcount == n and "رسم شد" in msg, (vcount, msg))
        pg.click("#btn-gamma")
        check(f"γ گراف ساخته‌شده برابر {k} است", f"= {FA(k)}" in pg.inner_text("#gamma-text"), pg.inner_text("#gamma-text"))
    pg.fill("#gen-n", "6"); pg.fill("#gen-k", "7"); pg.click("#btn-generate")
    check("γ بزرگ‌تر از n رد می‌شود", "۱ تا n" in clean(pg.inner_text("#gen-msg")), pg.inner_text("#gen-msg"))
    pg.fill("#gen-n", "11"); pg.fill("#gen-k", "2"); pg.click("#btn-generate")
    check("n=11 رد می‌شود", "۲ تا ۱۰" in clean(pg.inner_text("#gen-msg")), pg.inner_text("#gen-msg"))

    # ۴. تمرین مینیمال روی P6: {2،4،6} مینیمال و غیرمینیمم است
    pg.select_option("#graph-select", "P6")
    pg.check("#practice-mode")
    check("جعبه‌ی تمرین نمایش داده می‌شود", pg.is_visible("#practice-box"))
    pg.click("[data-v='1']"); pg.click("[data-v='3']"); pg.click("[data-v='5']")
    box = pg.inner_text("#practice-box")
    check("تمرین: {2،4،6} احاطه‌گر و مینیمال است", "مینیمال" in box and "انجام شد" in box, box)
    check("تمرین: این مجموعه مینیمم نیست", "مینیمم (|D| = γ): خیر" in clean(box), box)
    pg.click("#btn-check")
    pg.click("#btn-next")
    rows = pg.inner_text("#history")
    check("تمرین در سابقه با وضعیت «تمرین» ثبت می‌شود", "تمرین" in rows, rows[:200])
    score = table_text(pg, "#score-body")
    check("تمرین امتیاز نمی‌دهد", "۰" in score and "۱۰" not in score, score)
    pg.check("#practice-mode") if not pg.is_checked("#practice-mode") else None
    pg.uncheck("#practice-mode")
    check("خاموش کردن تمرین جعبه را پنهان می‌کند", not pg.is_visible("#practice-box"))

    # ۵. ایستگاه ۴: مینیمال در برابر مینیمم
    pg.click("#tab-lab")
    pg.select_option("#st4-graph", "P6")
    rows_n = pg.locator("#st4-table tbody tr").count()
    check("P6: هفت مجموعه‌ی مینیمال در جدول است", rows_n == 7, rows_n)
    summ = pg.inner_text("#st4-summary")
    check("P6: خلاصه‌ی ایستگاه ۴ مینیمال غیرمینیمم را گزارش می‌کند", "غیرمینیمم" in summ, summ)
    check("ایستگاه ۴: ستون مینیمم است؟ وجود دارد", "مینیمم است؟" in pg.inner_text("#st4-table"))

    # ۵.۵ دو مرحله‌ای: مرحله‌ی ۲ قفل است تا مرحله‌ی ۱ تأیید شود
    pg.click("#tab-game")
    pg.select_option("#graph-select", "P6"); pg.uncheck("#practice-mode")
    pg.click("#btn-reset")
    check("مرحله‌ی ۲ در ابتدا غیرفعال است", pg.is_disabled("#btn-check2"))
    pg.click("[data-v='0']"); pg.click("#btn-check")
    check("مجموعه‌ی ناکامل: مرحله‌ی ۲ فعال نمی‌شود", pg.is_disabled("#btn-check2"))
    check("مجموعه‌ی ناکامل: ۰ امتیاز", "۰ امتیاز" in pg.inner_text("#result"), pg.inner_text("#result"))
    pg.click("#btn-reset")
    pg.click("[data-v='1']"); pg.click("[data-v='3']"); pg.click("[data-v='5']")
    pg.click("#btn-check")
    check("مرحله‌ی ۱ برای {2،4،6} تأیید شد و مرحله‌ی ۲ فعال است", "مرحله‌ی ۱ تأیید شد" in pg.inner_text("#result") and pg.is_enabled("#btn-check2"))
    pg.click("#btn-check2")
    check("{2،4،6} در P6: مینیمال ولی غیرمینیمم = ۱۰ امتیاز", "۱۰ امتیاز" in pg.inner_text("#result"), pg.inner_text("#result"))
    pg.click("[data-v='3']")  # بعد از مرحله‌ی ۱: فقط انتخاب برای حذف (مجموعه تغییر نمی‌کند)
    check("انتخاب برای حذف، مرحله‌ی ۲ را تا اعمال یا لغو قفل می‌کند", pg.is_disabled("#btn-check2"))
    pg.click("[data-v='3']")  # برداشتن انتخاب: مجموعه همان است و مرحله‌ی ۲ باز می‌شود
    check("لغو انتخاب حذف، مجموعه‌ی تأییدشده را دوباره باز می‌کند", pg.is_enabled("#btn-check2"))
    pg.click("[data-v='0']")  # افزودن مهره: مجموعه تغییر می‌کند و هر دو مرحله بی‌اعتبار می‌شوند
    check("تغییر مجموعه، مرحله‌ی ۲ را دوباره قفل می‌کند", pg.is_disabled("#btn-check2"))
    pg.click("[data-v='0']")  # بازگشت به همان مجموعه (باید دوباره مرحله‌ی ۱ بخواهد)
    check("بازگشت به همان مجموعه بدون تأیید مرحله‌ی ۱ قفل است", pg.is_disabled("#btn-check2"))
    # احاطه‌گر ولی زائد: {2،3،5} در P6
    pg.click("#btn-reset")
    pg.click("[data-v='1']"); pg.click("[data-v='2']"); pg.click("[data-v='4']")
    pg.click("#btn-check"); pg.click("#btn-check2")
    txt = pg.inner_text("#result")
    check("{2،3،5} در P6: احاطه‌گر ولی غیرمینیمال = ۵ امتیاز", "۵ امتیاز" in txt, txt)
    # امتیاز: تنها مرحله‌ی ۱ => ۵ امتیاز؛ مرحله‌ی ۱ و ۲ برای مینیمم => ۱۵
    pg.click("#btn-reset")
    pg.click("[data-v='1']"); pg.click("[data-v='4']")  # {2،5} در P6: مینیمم
    pg.click("#btn-check"); pg.click("#btn-check2")
    check("{2،5} در P6 مینیمم است = ۱۵ امتیاز", "۱۵ امتیاز" in pg.inner_text("#result"), pg.inner_text("#result"))
    pg.click("#btn-next")
    rows = table_text(pg, "#score-body")
    check("امتیاز مینیمم ۱۵ ثبت شد", "۱۵" in rows, rows)
    pg.select_option("#graph-select", "P6")
    pg.click("[data-v='1']"); pg.click("[data-v='3']"); pg.click("[data-v='5']"); pg.click("#btn-check")
    pg.click("#btn-next")
    check("فقط مرحله‌ی ۱ امتیاز ۵ می‌دهد", "۵ امتیاز" in pg.inner_text("#history"), pg.inner_text("#history")[:200])

    # ۶. راهنما و نسخه
    pg.click("#tab-help")
    check("تعاریف: بخش مینیمال و مینیمم وجود دارد", "احاطه‌گر مینیمال و مینیمم" in pg.inner_text("#view-help"))
    check("پاورقی نسخه‌ی ۶.۳.۰ است", "۶.۳.۰" in pg.inner_text("footer"))
    check("بدون خطای صفحه/کنسول", not errs, errs)
    # ۴. گراف پترسن (نسخه ۶.۳.۰): ۱۰ رأس، γ = ۳، ۱۰ مجموعه‌ی مینیمم
    pg.click("#tab-game")
    pg.select_option("#graph-select", "PT")
    check("پترسن: ۱۰ رأس روی صفحه است", pg.locator(".board .vertex").count() == 10, pg.locator(".board .vertex").count())
    meta = pg.inner_text("#graph-meta")
    check("پترسن: خط توصیف نام، n = ۱۰ و |E| = ۱۵ را دارد", "پترسن" in meta and "n = ۱۰" in meta and "|E| = ۱۵" in meta, meta)
    pg.click("#btn-gamma")
    check("پترسن: γ = ۳", "= ۳" in pg.inner_text("#gamma-text"), pg.inner_text("#gamma-text"))
    chips = pg.locator("#gamma-sets .set-chip").count()
    check("پترسن: ده مجموعه‌ی مینیمم در فهرست است", chips == 10, chips)
    pg.click("#btn-reset")

    # ۵. رگرسیون: بازبینی مرحله‌ی ۱ پس از تأیید مرحله‌ی ۲ امتیاز ۱۵ را به ۵ کاهش نمی‌دهد
    pg.select_option("#graph-select", "C4")
    pg.click("[data-v='0']"); pg.click("[data-v='2']")
    pg.click("#btn-check"); pg.click("#btn-check2")
    pg.click("#btn-check")
    pg.click("#btn-next")
    check("بازبینی مرحله‌ی ۱ پس از مرحله‌ی ۲ امتیاز ۱۵ را حفظ می‌کند", "۱۵ امتیاز" in pg.inner_text("#history"), pg.inner_text("#history")[:200])
    pg.click("#btn-reset")

    # ۶. ارقام فارسی در جدول ایستگاه ۲ و ماتریس گراف سفارشی
    pg.click("#tab-lab")
    st2 = pg.inner_text("#st2-table")
    check("ایستگاه ۲: جدول بدون رقم لاتین است", re.search(r"[0-9]", st2) is None, st2[:120])
    pg.click("#tab-game")
    pg.evaluate("document.getElementById('custom-builder').open = true")
    hdr = pg.inner_text("#custom-matrix thead") if pg.locator("#custom-matrix thead").count() else ""
    check("ماتریس سفارشی: سرستون‌ها فارسی‌اند", hdr != "" and re.search(r"[0-9]", hdr) is None, hdr)

    b.close()

print(f"\n{sum(res)}/{len(res)} تست نسخه‌ی ۶.۳.۰ موفق")
sys.exit(0 if all(res) else 1)
