"""مسیرهای مرجع پروژه. همه‌ی ابزارها از این فایل استفاده می‌کنند تا پروژه در هر مسیری اجرا شود."""
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent          # .../chalesh-gamma/tools
ROOT = TOOLS_DIR.parent                              # .../chalesh-gamma
CODE_DIR = ROOT / "code"                             # index.html, script.js, graphs.js, style.css
DOCS_DIR = ROOT / "docs"
INDEX_URL = (CODE_DIR / "index.html").as_uri()       # file:///... (بدون مسیر ثابت)


def table_text(pg, sel):
    """متن یک جدول به‌صورت ردیف‌ها (خط‌جدید) و خانه‌ها (تب). کار با جدول‌های روی تب پنهان هم درست است،
    چون inner_text برای عنصر پنهان فاصله‌ی خانه‌ها را نمی‌دهد."""
    return pg.evaluate(
        "(s) => [...document.querySelectorAll(s + ' tr')].map(r => [...r.cells].map(c => c.textContent.trim()).join('\\t')).join('\\n')",
        sel,
    )
