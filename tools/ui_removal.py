"""تست آزمون حذف چندمهره‌ای (نسخه ۶.۳.۰).

- بعد از مرحله‌ی ۱ می‌توان چند مهره را برای حذف انتخاب کرد.
- تا وقتی انتخاب حذف اعمال یا لغو نشده، مرحله‌ی ۱ و ۲ قفل‌اند (باگ: مرحله‌ی ۲ مجموعه‌ی قبلی را نمره می‌داد).
- «اعمال حذف» مجموعه‌ی واقعی را تغییر می‌دهد و مرحله‌ی ۱ دوباره بررسی می‌شود؛ مرحله‌ی ۲ نتیجه‌ی مجموعه‌ی جدید را می‌دهد.
- «لغو انتخاب‌ها» مجموعه را تغییر نمی‌دهد.
- کلیک روی مهره‌ی بعد از مرحله‌ی ۱ همان انتخاب برای حذف را تغییر می‌دهد.
- امتیاز آزمون حذف صفر است و مجموعه تا اعمال، تغییر نمی‌کند.
اجرا: python3 tools/ui_removal.py
"""
from playwright.sync_api import sync_playwright
from _paths import INDEX_URL

res = []
def check(name, cond, extra=""):
    res.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else "  " + str(extra)))

EXACT = "عدد احاطه‌گری دقیق"

with sync_playwright() as p:
    b = p.chromium.launch(); errs = []
    pg = b.new_page(viewport={"width": 1280, "height": 900})
    pg.on("pageerror", lambda e: errs.append("PAGEERROR " + str(e)))
    pg.goto(INDEX_URL); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_selector("#board svg")

    # ۱. K4 با سه مهره (۰،۱،۲): حذف هر مهره زائد است
    pg.select_option("#graph-select", "K4")
    pg.click("#btn-reset")
    pg.click("[data-v='0']"); pg.click("[data-v='1']"); pg.click("[data-v='2']")
    pg.click("#btn-check")
    pg.click("#btn-check2")
    check("مرحله‌ی ۲ (بدون حذف) اجرا شد و نتیجه نمایش داده شد", "احاطه‌گر است" in pg.inner_text("#result") or "مینیمال" in pg.inner_text("#result"), pg.inner_text("#result"))

    # ۲. انتخاب چند مهره برای حذف
    pg.click("#btn-check")  # مرحله‌ی ۱ دوباره (مجموعه‌ی کامل)
    pg.click("#removal-list li:nth-child(1) button")
    pg.click("#removal-list li:nth-child(2) button")
    check("دو مهره همزمان برای حذف انتخاب شدند", pg.locator("#board .vertex.removal-target").count() == 2, pg.locator("#board .vertex.removal-target").count())
    check("دکمه‌ی اعمال حذف دیده می‌شود", pg.locator("#removal-apply").is_visible())
    check("مجموعه‌ی واقعی هنوز سه مهره است", "۳" in pg.inner_text("#counts"), pg.inner_text("#counts"))

    # ۳. باگ: مرحله‌ی ۲ و ۱ با حذف انتخاب‌شده قفل‌اند
    check("مرحله‌ی ۲ با حذف انتخاب‌شده غیرفعال است", pg.is_disabled("#btn-check2"))
    check("مرحله‌ی ۱ با حذف انتخاب‌شده غیرفعال است", pg.is_disabled("#btn-check"))
    before = pg.inner_text("#result")
    pg.evaluate("document.getElementById('btn-check2').click()")  # حتی با کلیک برنامه‌ای، دکمه‌ی غیرفعال کاری نمی‌کند
    check("کلیک مرحله‌ی ۲ هنگام انتخاب حذف، نتیجه‌ی جدیدی نمی‌سازد", pg.inner_text("#result") == before, pg.inner_text("#result"))

    # ۴. لغو: مجموعه تغییری نمی‌کند و مرحله‌ها باز می‌شوند
    pg.click("#removal-clear")
    check("لغو انتخاب‌ها: انتخاب‌های حذف پاک شد", pg.locator("#board .vertex.removal-target").count() == 0)
    check("لغو انتخاب‌ها: مرحله‌ی ۲ دوباره فعال است", pg.is_enabled("#btn-check2"))

    # ۵. انتخاب دوباره و اعمال: دو مهره حذف شوند، مجموعه ({۲}) مینیمم است
    pg.click("#removal-list li:nth-child(1) button")
    pg.click("#removal-list li:nth-child(2) button")
    pg.click("#removal-apply")
    counts = pg.inner_text("#counts")
    check("اعمال حذف: مجموعه‌ی واقعی یک مهره شد", "۱" in counts and "۳" not in counts, counts)
    check("اعمال حذف: مرحله‌ی ۱ دوباره بررسی شد", "مرحله‌ی ۱ تأیید شد" in pg.inner_text("#result"), pg.inner_text("#result"))
    pg.click("#btn-check2")
    check("مرحله‌ی ۲ روی مجموعه‌ی جدید: مینیمم (۱۵ امتیاز)", EXACT in pg.inner_text("#result"), pg.inner_text("#result"))

    # ۶. کلیک روی مهره بعد از مرحله‌ی ۱ فقط انتخاب حذف را تغییر می‌دهد
    pg.click("#btn-reset")
    pg.click("[data-v='0']"); pg.click("[data-v='1']"); pg.click("#btn-check")
    pg.click("[data-v='0']")
    check("کلیک روی مهره‌ی بعد از مرحله‌ی ۱ آن را برای حذف انتخاب می‌کند", pg.locator("#board .vertex.removal-target").count() == 1)
    check("مجموعه‌ی واقعی بعد از کلیک تغییر نکرد", "۲" in pg.inner_text("#counts"), pg.inner_text("#counts"))
    pg.click("[data-v='0']")
    check("کلیک دوباره روی همان مهره انتخاب حذف را برمی‌دارد", pg.locator("#board .vertex.removal-target").count() == 0)
    check("بدون انتخاب حذف، دکمه‌ی اعمال پنهان است", pg.locator("#removal-apply").is_hidden())

    # ۷. امتیاز و تغییر مجموعه: مجموعه‌ی جدید مرحله‌ی ۱ را لازم دارد
    pg.click("[data-v='2']")
    check("تغییر مجموعه، مرحله‌ی ۲ را قفل می‌کند", pg.is_disabled("#btn-check2"))

    # ۸. C4 با مهره‌های ۰ و ۲: هر دو ضروری‌اند؛ انتخاب و اعمال نباید مجموعه‌ی احاطه‌گر را بی‌اعتبار کند بدون پیام
    pg.select_option("#graph-select", "C4")
    pg.click("#btn-reset")
    pg.click("[data-v='0']"); pg.click("[data-v='2']"); pg.click("#btn-check")
    pg.click("#removal-list li:nth-child(1) button")
    pg.click("#removal-apply")
    check("C4: حذف یک مهره‌ی ضروری مجموعه را احاطه‌گر نمی‌گذارد و پیام می‌دهد", "احاطه‌گر نیست" in pg.inner_text("#result"), pg.inner_text("#result"))
    check("C4: مرحله‌ی ۲ بعد از حذف ضروری غیرفعال است", pg.is_disabled("#btn-check2"))

    check("خطای صفحه نداریم", not errs, errs)
    print(f"\n{sum(res)}/{len(res)} بررسی موفق")
    b.close()
raise SystemExit(0 if all(res) and not errs else 1)
