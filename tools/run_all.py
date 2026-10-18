"""اجرای همه‌ی تست‌ها با یک دستور. خروجی: جدول نتایج و کد خروج ۰ (همه موفق) یا ۱ (خطا).

    python3 tools/run_all.py            # همه‌ی تست‌ها
    python3 tools/run_all.py --fast     # فقط ریاضی و واحد (بدون مرورگر)
"""
import subprocess, sys, time
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
PY = sys.executable
NODE = "node"

FAST = [
    ("ریاضی: verify.py", [PY, str(TOOLS / "verify.py")]),
    ("واحد گراف: test_graphs.js", [NODE, str(TOOLS / "test_graphs.js")]),
    ("بررسی نحو: script.js", [NODE, "--check", str(ROOT / "code" / "script.js")]),
    ("بررسی نحو: graphs.js", [NODE, "--check", str(ROOT / "code" / "graphs.js")]),
    ("هماهنگی id ها: check_ids.py", [PY, str(TOOLS / "check_ids.py")]),
]
BROWSER = [
    ("رابط دودی: ui_test.py", [PY, str(TOOLS / "ui_test.py")]),
    ("رابط جامع: ui_bugs.py", [PY, str(TOOLS / "ui_bugs.py")]),
    ("ویژگی‌ها: ui_features.py", [PY, str(TOOLS / "ui_features.py")]),
    ("مرزی: ui_edge.py", [PY, str(TOOLS / "ui_edge.py")]),
    ("کارنامه‌ها: ui_cards.py", [PY, str(TOOLS / "ui_cards.py")]),
    ("آزمون حذف و تب کارنامه: ui_minimal.py", [PY, str(TOOLS / "ui_minimal.py")]),
    ("آزمون حذف چندمهره‌ای: ui_removal.py", [PY, str(TOOLS / "ui_removal.py")]),
    ("امکانات ۶.۴.۰: ui_v640.py", [PY, str(TOOLS / "ui_v640.py")]),
    ("صفحه‌ی معرفی: ui_intro.py", [PY, str(TOOLS / "ui_intro.py")]),
    ("نسخه ۶.۴.۰: ui_v600.py", [PY, str(TOOLS / "ui_v600.py")]),
    ("پس‌زمینه‌ی پترسن: ui_bg.py", [PY, str(TOOLS / "ui_bg.py")]),
    ("حالت روشن و تاریک: ui_theme.py", [PY, str(TOOLS / "ui_theme.py")]),
    ("تریگرهای حالت بازی: ui_triggers.py", [PY, str(TOOLS / "ui_triggers.py")]),
    ("انیمیشن‌های C6 و S4: ui_anim.py", [PY, str(TOOLS / "ui_anim.py")]),
    ("حسابرسی DOM و دسترس‌پذیری: ui_audit.py", [PY, str(TOOLS / "ui_audit.py")]),
    ("جست‌وجوی تکمیلی: hunt2.py", [PY, str(TOOLS / "hunt2.py")]),
]

def run(name, cmd):
    t0 = time.time()
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=600, cwd=str(ROOT))
        out = p.stdout + p.stderr
        # معیار ساده: کد خروج غیرصفر یا وجود خط FAIL/Traceback
        lines = out.splitlines()
        bad = p.returncode != 0 or any(l.startswith("FAIL") or l.startswith("Traceback") for l in lines)
        summary = next((l for l in reversed(lines) if l.strip()), "")
    except subprocess.TimeoutExpired:
        bad, summary, out = True, "timeout", ""
    dt = time.time() - t0
    print(f"{'✗ FAIL' if bad else '✓ PASS'}  {name:<32} {dt:6.1f}s  {summary[:70]}")
    if bad:
        print("\n".join("      " + l for l in out.splitlines()[-40:]))
    return not bad

if __name__ == "__main__":
    suites = FAST if "--fast" in sys.argv else FAST + BROWSER
    results = [run(n, c) for n, c in suites]
    print(f"\n{sum(results)}/{len(results)} بخش موفق")
    sys.exit(0 if all(results) else 1)
