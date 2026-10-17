"""تولید کارت‌های گراف قابل چاپ (HTML + SVG) و جدول γ برای پاسخنامه."""
import math, json, sys

FA = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
def fa(x):
    """عدد لاتین را به رقم فارسی تبدیل می‌کند (کارت‌ها فارسی‌اند)."""
    return str(x).translate(FA)
from itertools import combinations
sys.path.insert(0, __file__.rsplit("/", 1)[0])

def gamma(n, E):
    adj = {v: set() for v in range(n)}
    for a, b in E: adj[a].add(b); adj[b].add(a)
    for k in range(n+1):
        for S in combinations(range(n), k):
            s = set(S)
            if all(v in s or adj[v] & s for v in range(n)): return k
GRAPHS = [
 # (کلید، عنوان HTML، n، یال‌ها، طرح‌بندی، برچسب‌ها)
 ("P3","P<sub>3</sub>",3,[(0,1),(1,2)],"line"),
 ("C4","C<sub>4</sub>",4,[(0,1),(1,2),(2,3),(3,0)],"circle"),
 ("K4","K<sub>4</sub>",4,[(a,b) for a in range(4) for b in range(a+1,4)],"circle"),
 ("S4","S<sub>4</sub>",4,[(0,1),(0,2),(0,3)],"star"),
 ("P4","P<sub>4</sub>",4,[(0,1),(1,2),(2,3)],"line"),
 ("P5","P<sub>5</sub>",5,[(i,i+1) for i in range(4)],"line"),
 ("P7","P<sub>7</sub>",7,[(i,i+1) for i in range(6)],"line"),
 ("C5","C<sub>5</sub>",5,[(i,(i+1)%5) for i in range(5)],"circle"),
 ("C6","C<sub>6</sub>",6,[(i,(i+1)%6) for i in range(6)],"circle"),
 ("C7","C<sub>7</sub>",7,[(i,(i+1)%7) for i in range(7)],"circle"),
 ("K23","K<sub>2,3</sub>",5,[(i,2+j) for i in range(2) for j in range(3)],"bip"),
 ("W4","W<sub>4</sub>",5,[(0,1),(1,2),(2,3),(3,0),(0,4),(1,4),(2,4),(3,4)],"wheel"),
 ("PT","پترسن",10,[(i,(i+1)%5) for i in range(5)]+[(i,i+5) for i in range(5)]+[(5+i,5+(i+2)%5) for i in range(5)],"petersen"),
]
def layout(kind, n):
    pts = []
    if kind == "line":
        for i in range(n): pts.append((25 + i*(150/(n-1)), 100))
    elif kind == "circle":
        for i in range(n):
            a = -math.pi/2 + 2*math.pi*i/n; pts.append((100+70*math.cos(a), 100+70*math.sin(a)))
    elif kind == "star":
        pts.append((100,100))
        for i in range(1,n):
            a = -math.pi/2 + 2*math.pi*(i-1)/(n-1); pts.append((100+70*math.cos(a), 100+70*math.sin(a)))
    elif kind == "bip":
        for i in range(2): pts.append((55, 60+i*80))
        for j in range(3): pts.append((145, 40+j*60))
    elif kind == "petersen":
        for i in range(5):
            a = -math.pi/2 + 2*math.pi*i/5; pts.append((100+75*math.cos(a), 100+75*math.sin(a)))
        for i in range(5):
            a = -math.pi/2 + 2*math.pi*i/5; pts.append((100+33*math.cos(a), 100+33*math.sin(a)))
    elif kind == "wheel":
        for i in range(n-1):
            pass
        m = n-1  # n = 5 => rim C4 has 4 vertices, hub index 4
        for i in range(m):
            a = -math.pi/2 + 2*math.pi*i/m; pts.append((100+70*math.cos(a), 100+70*math.sin(a)))
        pts.append((100,100))
    return pts

def svg(key, n, E, kind):
    P = layout(kind, n)
    out = ['<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">']
    for a,b in E:
        out.append(f'<line x1="{P[a][0]:.1f}" y1="{P[a][1]:.1f}" x2="{P[b][0]:.1f}" y2="{P[b][1]:.1f}" stroke="#333" stroke-width="2"/>')
    for i,(x,y) in enumerate(P):
        label = "c" if (kind=="wheel" and i==n-1) else fa(i+1)
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="13" fill="#fff" stroke="#1d4ed8" stroke-width="2.5"/>')
        out.append(f'<text x="{x:.1f}" y="{y+5:.1f}" text-anchor="middle" font-size="14" font-family="Arial" fill="#111">{label}</text>')
    out.append('</svg>')
    return "\n".join(out)

cards, table = [], []
for idx,(key,title,n,E,kind) in enumerate(GRAPHS, start=1):
    g = gamma(n,E)
    table.append({"key":key,"n":n,"m":len(E),"gamma":g})
    cards.append(f'''<div class="card">
  <div class="head"><span class="no">کارت {fa(idx)}</span><span class="title">{title}</span></div>
  {svg(key,n,E,kind)}
  <div class="foot">تعداد رأس: {fa(n)} — تعداد یال: {fa(len(E))}</div>
</div>''')

html = f'''<!DOCTYPE html>
<html lang="fa" dir="rtl"><head><meta charset="UTF-8">
<title>کارت‌های گراف — چالش γ</title>
<style>
 @page {{ size: A4; margin: 8mm; }}
 body {{ font-family: Tahoma, Vazirmatn, sans-serif; margin:0; background:#eee; }}
 h1 {{ text-align:center; font-size:18px; margin:12px; }}
 .sheet {{ display:grid; grid-template-columns: repeat(3, 1fr); grid-auto-rows:62mm; gap:4mm; padding:0; background:#fff; }}
 .card {{ border:1.5px dashed #555; border-radius:6px; padding:4px; height:62mm; box-sizing:border-box; display:flex; flex-direction:column; break-inside:avoid; }}
 .head {{ display:flex; justify-content:space-between; font-size:13px; font-weight:bold; }}
 .title {{ font-size:18px; direction:ltr; }}
 .card svg {{ flex:1; width:100%; height:100%; min-height:0; }}
 .foot {{ font-size:11px; text-align:center; color:#333; }}
 @media print {{ body {{ background:#fff; }} h1 {{ display:none; }} .sheet{{ padding:0; }} .card{{ page-break-inside:avoid; }} }}
</style></head>
<body>
<h1>کارت‌های گراف — بازی «چالش γ» (ریاضیات گسسته ۱۲، فصل ۲، درس ۲)</h1>
<p style="text-align:center;font-size:12px">این صفحه را روی کاغذ A4 چاپ کنید و کارت‌ها را جدا کنید. رأس‌ها با شماره نمایش داده شده‌اند؛ مقدار γ روی کارت نوشته نشده است.</p>
<div class="sheet">
{chr(10).join(cards)}
</div>
</body></html>'''
from _paths import DOCS_DIR, TOOLS_DIR
out = str(DOCS_DIR / "02_کارت‌های_گراف.html")
from mathwrap import wrap_html  # عبارت‌های ریاضی را در بلوک چپ‌به‌راست قرار می‌دهد
open(out,"w",encoding="utf-8").write(wrap_html(html))
json.dump(table, open(TOOLS_DIR / "gamma_table.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("cards:", len(cards)); print(json.dumps(table, ensure_ascii=False))
