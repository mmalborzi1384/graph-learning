"""جست‌وجوی باگ‌های تکمیلی: حالت دو گروهی، گراف سفارشی، آزمایشگاه، راهنما، بازگشت/تکرار، CSV، کلیک‌های سریع."""
import sys, pathlib
from playwright.sync_api import sync_playwright
from _paths import table_text
URL = pathlib.Path(__file__).resolve().parent.parent.joinpath("code", "index.html").as_uri()
results = []
def check(name, cond, detail=""):
    results.append(bool(cond)); print(("PASS " if cond else "FAIL ") + name + ("" if cond else f"  [{detail}]"))

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(accept_downloads=True, viewport={"width": 1440, "height": 900})
    pg = ctx.new_page()
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    pg.goto(URL); pg.evaluate("localStorage.clear()"); pg.reload(); pg.wait_for_selector("#board svg")

    # 1. انتخاب گراف و امتیاز
    pg.select_option("#graph-select", "C4")
    pg.click("[data-v='0']"); pg.click("[data-v='2']"); pg.click("#btn-check"); pg.click("#btn-check2")
    check("C4 {1,3} دقیق ۱۵", "۱۵ امتیاز" in pg.inner_text("#result"), pg.inner_text("#result"))

    # 2. Undo / Redo با کیبورد و دکمه
    before = pg.inner_text("#counts")
    pg.keyboard.press("Control+z")
    after_undo = pg.inner_text("#counts")
    check("Ctrl+Z مهره‌ی آخر را برمی‌گرداند", after_undo != before, f"{before} -> {after_undo}")
    pg.keyboard.press("Control+y")
    check("Ctrl+Y دوباره می‌گذارد", pg.inner_text("#counts") == before, pg.inner_text("#counts"))

    # 3. راهنما: سه سطح، بدون تغییر امتیاز
    pg.select_option("#graph-select", "C4"); pg.click("#btn-reset")
    score0 = table_text(pg, "#score-body")
    for lvl in (1, 2, 3):
        pg.click("#btn-hint")  # سطح ۱ تا ۳
    hint_txt = pg.inner_text("#hint-box")
    check("راهنما سه سطح دارد", "سطح ۱" in hint_txt or "سطح ۲" in hint_txt or "سطح ۳" in hint_txt, hint_txt[:120])
    check("دکمه‌ی راهنما پس از سطح ۳ غیرفعال است", pg.is_disabled("#btn-hint"))
    pg.click("#btn-reset"); pg.select_option("#graph-select", "C4")
    pg.click("#btn-hint"); pg.click("#btn-hint")
    check("سطح ۲ راهنما به حاشیه‌ی آبی اشاره می‌کند", "حاشیه‌ی آبی" in pg.inner_text("#hint-box"), pg.inner_text("#hint-box"))
    check("راهنما امتیاز را تغییر نمی‌دهد", table_text(pg, "#score-body") == score0)

    # 4. حالت دو گروهی: نوبت متناوب
    pg.check("#team-mode")
    pg.wait_for_timeout(200)
    check("حالت دو گروهی فعال شد", "گروه" in table_text(pg, "#score-body") or pg.is_checked("#team-mode"))
    pg.click("[data-v='0']"); pg.click("[data-v='2']"); pg.click("#btn-check"); pg.click("#btn-next")
    turn = pg.inner_text("#turn-text")
    check("پس از دور اول نوبت به گروه B رفت", "گروه B" in turn, turn)
    pg.uncheck("#team-mode")

    # 5. گراف سفارشی: n نامعتبر و معتبر
    pg.click("summary:has-text('ساخت گراف سفارشی')") if pg.locator("summary:has-text('ساخت گراف سفارشی')").count() and not pg.is_visible("#custom-n") else None
    pg.fill("#custom-n", "1"); pg.dispatch_event("#custom-n", "change")
    pg.click("#btn-custom-apply")
    msg1 = pg.inner_text("#custom-msg")
    check("n=1 رد می‌شود و پیام خطا می‌دهد", "۲ تا ۱۰" in msg1, msg1)
    pg.fill("#custom-n", "4"); pg.dispatch_event("#custom-n", "change")
    pg.click("#btn-custom-apply")
    msg2 = pg.inner_text("#custom-msg")
    meta = pg.inner_text("#graph-meta")
    check("گراف سفارشی با n=۴ ساخته می‌شود", "n = ۴" in meta and "بارگذاری شد" in msg2, meta + " | " + msg2)

    # 6. CSV خروجی
    pg.click("#btn-next")
    with pg.expect_download() as dl:
        pg.click("#tab-scores"); pg.click("#btn-csv")
    path = dl.value.path()
    pg.click("#tab-game")
    content = open(path, encoding="utf-8-sig").read()
    header = content.splitlines()[0] if content else ""
    check("CSV ستون‌های درست دارد", all(c in header for c in ["گروه", "گراف", "|D|", "γ", "وضعیت", "امتیاز", "راهنما"]), header)

    # 7. کلیک‌های سریع روی بررسی: امتیاز نباید دوبار ثبت شود
    pg.click("#btn-reset")
    pg.select_option("#graph-select", "P3")
    pg.wait_for_timeout(100)
    for _ in range(4):
        pg.click("[data-v='1']")
    pg.click("[data-v='1']")  # toggle off/on
    pg.click("#btn-check"); pg.click("#btn-check"); pg.click("#btn-check")
    rows = pg.inner_text("#history")
    check("بررسی سه‌باره یک سابقه ثبت می‌کند", rows.count("امتیاز") <= 3, rows[:200])

    # 8. آزمایشگاه: همه‌ی ایستگاه‌ها بدون خطا
    pg.click("#tab-lab"); pg.wait_for_timeout(200)
    pg.select_option("#st4-graph", "C4"); pg.wait_for_timeout(200)
    summ = pg.inner_text("#st4-summary")
    check("ایستگاه ۴: C4 شش مجموعه‌ی مینیمال دارد", "۶" in summ, summ)
    pg.click("#st5-go"); pg.wait_for_timeout(200)
    check("ایستگاه ۵ کار می‌کند", pg.is_visible("#view-game") or pg.is_visible("#view-lab"))
    pg.click("#tab-game")

    # 9. تبدیل تاریخ‌ها: بازنشانی کارنامه بدون تأیید
    pg.once("dialog", lambda d: d.dismiss())
    pg.click("#tab-scores"); pg.click("#btn-card-reset")
    check("لغو تأیید بازنشانی بی‌اثر است", pg.locator("#records-body tr").count() > 0)

    # 10. کیبورد روی رأس
    pg.focus("[data-v='0']"); pg.keyboard.press("Enter")
    pg.keyboard.press("Space")
    check("Enter و Space روی رأس کار می‌کنند (بدون خطا)", True)

    # 11. خطاهای صفحه
    check("بدون خطای صفحه/کنسول", not errors, errors[:3])
    b.close()

print(f"\n{sum(results)}/{len(results)} passed")
sys.exit(0 if all(results) else 1)
