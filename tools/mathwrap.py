"""
mathwrap.py: جداسازی عبارت‌های ریاضی از متن فارسی.

مشکل: در متن راست‌به‌چپ، عبارت‌هایی مثل |D| = γ(G) یا n/(Δ+1) به هم می‌ریزند،
چون نویسه‌های «خنثی» (| = / ( ) ) بین نویسه‌های چپ‌به‌راست جابه‌جا می‌شوند.

راه‌حل: هر عبارت ریاضی در یک بلوک چپ‌به‌راست ایزوله قرار می‌گیرد.
  - در Markdown و کد JS: نویسه‌های یونیکد LRI (U+2066) و PDI (U+2069).
    مبدل docx این بلوک‌ها را با فونت Cambria Math می‌سازد.
  - در HTML: <span class="math" dir="ltr">…</span>.

قواعد تشخیص (یک «دَوِ» از نویسه‌های ریاضی‌گونه):
  دَو باید یکی از این‌ها را داشته باشد:
    - یک متغیر تک‌حرفی لاتین یا یونانی (n، k، D، P، γ، Δ، …)
    - یک عملگر یا نماد ریاضی (= < > ≥ ≤ ∪ ∈ ⊂ ⊆ ∖ ⌈ ⌉ | ∣ ≠ ≈ ∑ + × ÷ − *)
    - مجموعه‌ی آکولاددار {…} (مثل {۲، ۴، ۶})
  و از نویسه‌های مجاز تشکیل شده باشد (حروف لاتین، ارقام فارسی/لاتین/زیرنویس،
  پرانتز، کروشه، آکولاد، نمادهای بالا، فاصله، «_»، «^»، «/»، «.» و «،» داخلی).
  لبه‌های اضافی (فاصله، «.» و «،» و «(» انتهایی) بیرون از بلوک می‌مانند.
"""
import re

ISO_L = '\u2066'
ISO_R = '\u2069'
SUB_OPEN = '\ue000'   # جایگزین موقت <sub>
SUB_CLOSE = '\ue001'  # جایگزین موقت </sub>

RUN_CHARS = (
    r"A-Za-z0-9"
    "\u06f0-\u06f9"          # ارقام فارسی
    "\u2080-\u2089\u2099"    # زیرنویس‌ها
    "\u03b1-\u03c9\u0391-\u03a9"  # یونانی
    r"\(\)\[\]\{\}\|\u2223=<>\u2265\u2264\u2260\u2248\u222a\u2229\u2208\u2209\u2282\u2286\u2216\u2205"
    "\u2308\u2309\u230a\u230b"  # ⌈ ⌉ ⌊ ⌋
    r"\+\-\u2212/\u00d7\u00f7\u00b7_\^\u2032'!,:\.\u060c\u2211\u2261\u2192\u21d2\u2194 "
    "\u00a0"
    "\ue000\ue001"
)
RUN_RE = re.compile('[' + RUN_CHARS + ']+')
OP_RE = re.compile(r"[=<>\u2265\u2264\u222a\u2208\u2282\u2286\u2216\u2308\u2309\u230a\u230b|\u2223\u2260\u2248\u2211+\u00d7\u00f7\u2212]")
SINGLE_RE = re.compile(r"(?<![A-Za-z])[A-Za-z\u03b1-\u03c9\u0391-\u03a9](?![A-Za-z])")
GREEK_RE = re.compile(r"[\u03b1-\u03c9\u0391-\u03a9]")
EDGE_STRIP = " \u00a0\u060c.,:;(["  # لبه‌های بیرونی بلوک
PROTECTED_WORDS = ("Nazanin", "Chrome", "Firefox", "Edge", "Word", "Excel", "PDF", "Markdown", "Arena",
                   "Ctrl", "Node", "Python", "ES6", "F12", "localStorage", "CSV", "Notion", "Playwright")


def _balanced(s):
    return s.count('(') == s.count(')') and s.count('[') == s.count(']') and s.count('{') == s.count('}')


_CLOSE_TO_OPEN = {')': '(', ']': '[', '}': '{'}


def _unmatched(chunk):
    """اندیس بسته‌های بی‌جفت (U) و بازهای بی‌جفت (O) را برمی‌گرداند."""
    stack, unclosed = [], []
    for i, ch in enumerate(chunk):
        if ch in '([{':
            stack.append(i)
        elif ch in _CLOSE_TO_OPEN:
            if stack and chunk[stack[-1]] == _CLOSE_TO_OPEN[ch]:
                stack.pop()
            else:
                unclosed.append(i)
    return unclosed, stack


def _trim(run):
    """لبه‌های بیرونی بلوک را جدا می‌کند؛ پرانتز متعادل داخل بلوک حفظ می‌شود."""
    s, e = 0, len(run)
    changed = True
    while changed and s < e:
        changed = False
        head, tail = run[s], run[e - 1]
        if head in EDGE_STRIP and head not in '([':
            s += 1; changed = True; continue
        if tail in EDGE_STRIP and tail not in ')]}':
            e -= 1; changed = True; continue
        chunk = run[s:e]
        U, O = _unmatched(chunk)
        if head in '([' and 0 in O:          # بازِ بی‌جفت در ابتدا
            s += 1; changed = True; continue
        if U and U[0] == 0:                  # بسته‌ی بی‌جفت در ابتدا (متعلق به متن بیرون)
            s += 1; changed = True; continue
        if U:                                # بسته‌ی بی‌جفت وسط: بلوک تا قبل از آن
            e = s + U[0]; changed = True; continue
        if tail in ')]}' and (len(chunk) - 1) in U:   # بسته‌ی بی‌جفت در انتها
            e -= 1; changed = True; continue
        if O:                                 # بازِ بی‌جفت وسط‌ِ انتها: از همان‌جا ببر
            e = s + O[0]; changed = True; continue
    return s, e


def _is_math(chunk):
    if any(w in chunk for w in PROTECTED_WORDS):
        return False
    if '{' in chunk and '}' in chunk:
        return True
    return bool(SINGLE_RE.search(chunk) or OP_RE.search(chunk) or GREEK_RE.search(chunk))


def wrap_plain(text, open_s, close_s):
    """در یک متن بدون برچسب، عبارت‌های ریاضی را با open_s و close_s می‌پوشاند."""
    out, pos = [], 0
    for m in RUN_RE.finditer(text):
        run = m.group(0)
        s, e = _trim(run)
        if e <= s:
            continue
        chunk = run[s:e]
        if not _is_math(chunk):
            continue
        a, b = m.start() + s, m.start() + e
        out.append(text[pos:a])
        out.append(open_s + text[a:b] + close_s)
        pos = b
    out.append(text[pos:])
    return ''.join(out)


def strip_iso(text):
    return text.replace(ISO_L, '').replace(ISO_R, '')


def wrap_md_line(line):
    """یک خط Markdown را پردازش می‌کند. کد درون بک‌تیک و آدرس لینک دست‌نخورده می‌ماند."""
    line = strip_iso(line)
    prefix = ''
    m = re.match(r'^(\s*(?:[-*]\s+|\d+\.\s+|>\s*|#{1,6}\s+)?)', line)
    if m and m.group(1):
        prefix = m.group(1)
        line = line[len(prefix):]
    # جدول: هر سلول جدا
    if line.lstrip().startswith('|'):
        parts = line.split('|')
        new = []
        for p in parts:
            new.append(_wrap_md_segments(p))
        return prefix + '|'.join(new)
    return prefix + _wrap_md_segments(line)


def _wrap_md_segments(text):
    # بخش‌های محافظت‌شده: `code` و ](url)
    pieces = re.split(r'(`[^`]*`|\]\([^)]*\))', text)
    out = []
    for i, p in enumerate(pieces):
        if i % 2 == 1:
            out.append(p)
        else:
            out.append(wrap_plain(p, ISO_L, ISO_R))
    return ''.join(out)


# برچسب را با احترام به نقل‌قول‌های ویژگی‌ها پیدا می‌کند (مثلاً href="…<svg…>…")
TAG_SPLIT = re.compile(r'(<[a-zA-Z/!][^"\'>]*(?:(?:"[^"]*"|\'[^\']*\')[^"\'>]*)*>)')
HTML_SKIP = ('script', 'style', 'code', 'pre', 'title', 'svg', 'text', 'option', 'textarea')


def wrap_html(html):
    """متن گره‌های HTML را پردازش می‌کند. برچسب‌ها و ویژگی‌ها دست‌نخورده می‌مانند."""
    # حذف پوشش‌های قبلی
    html = re.sub(r'<span class="math" dir="ltr">(.*?)</span>', r'\1', html, flags=re.S)
    html = html.replace('<sub>', SUB_OPEN).replace('</sub>', SUB_CLOSE)
    tokens = re.split(TAG_SPLIT, html)
    skip_depth = 0
    out = []
    for tok in tokens:
        if TAG_SPLIT.fullmatch(tok):
            m = re.match(r'</?\s*([a-zA-Z0-9]+)', tok)
            if m:
                name = m.group(1).lower()
                if name in HTML_SKIP:
                    skip_depth += -1 if tok.startswith('</') else (0 if tok.endswith('/>') else 1)
                    skip_depth = max(skip_depth, 0)
            out.append(tok)
        else:
            if skip_depth or not tok.strip():
                out.append(tok)
            else:
                out.append(wrap_plain(tok, '<span class="math" dir="ltr">', '</span>'))
    res = ''.join(out)
    return res.replace(SUB_OPEN, '<sub>').replace(SUB_CLOSE, '</sub>')


def wrap_markdown(md):
    lines = md.split('\n')
    fence = False
    out = []
    for ln in lines:
        if ln.strip().startswith('```'):
            fence = not fence
            out.append(ln)
            continue
        out.append(ln if fence else wrap_md_line(ln))
    return '\n'.join(out)
