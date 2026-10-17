"""بررسی هماهنگی: هر id که script.js با $('...') می‌گیرد باید در index.html باشد، و برعکس عناصر بی‌استفاده را گزارش می‌کند."""
import re, sys
from _paths import CODE_DIR
html = (CODE_DIR / "index.html").read_text(encoding="utf-8")
js = (CODE_DIR / "script.js").read_text(encoding="utf-8")
html_ids = set(re.findall(r'\sid="([^"]+)"', html))
js_ids = set(re.findall(r"\$\('([^']+)'\)", js)) | set(re.findall(r'getElementById\("([^"]+)"\)', js))
missing = sorted(js_ids - html_ids)
unused = sorted(html_ids - js_ids)
print(f"id در index.html: {len(html_ids)}  ·  id استفاده‌شده در script.js: {len(js_ids)}")
for m in missing: print("FAIL id گم‌شده در HTML:", m)
for u in unused: print("note id بدون استفاده در JS:", u)
sys.exit(1 if missing else 0)
