"""راستی‌آزمایی ریاضی: محاسبه‌ی γ با جستجوی فراگیر و بررسی فرمول‌ها و کران‌ها."""
from itertools import combinations
from math import ceil

def path(n):   return n, [(i, i+1) for i in range(n-1)]
def cycle(n):  return n, [(i, (i+1) % n) for i in range(n)]
def complete(n): return n, [(i, j) for i in range(n) for j in range(i+1, n)]
def star(n):   return n, [(0, i) for i in range(1, n)]          # S_n: n رأس، یک مرکز
def bipartite(m, n): return m+n, [(i, m+j) for i in range(m) for j in range(n)]
def wheel(n):  # W_n: C_n + مرکز (n+1 رأس)
    _, e = cycle(n); return n+1, e + [(i, n) for i in range(n)]

def is_dom(n, adj, S):
    return all(v in S or any(u in S for u in adj[v]) for v in range(n))

def gamma(G):
    n, E = G
    adj = {v: set() for v in range(n)}
    for a, b in E: adj[a].add(b); adj[b].add(a)
    for k in range(0, n+1):
        for S in combinations(range(n), k):
            if is_dom(n, adj, set(S)): return k, adj
    return n, adj

def delta(adj): return max(len(s) for s in adj.values())

ok = True
def check(name, cond):
    global ok
    ok &= bool(cond)
    print(("OK  " if cond else "FAIL"), name)

print("--- مقادیر کوچک ---")
for name, G, expected in [
    ("P_3", path(3), 1), ("C_4", cycle(4), 2), ("K_4", complete(4), 1), ("S_4", star(4), 1)]:
    g, _ = gamma(G); check(f"γ({name}) = {g} (انتظار {expected})", g == expected)

print("--- γ(P_n)=γ(C_n)=⌈n/3⌉ ---")
for n in range(1, 8):
    gp, _ = gamma(path(n))
    check(f"P_{n}: γ={gp}, ⌈n/3⌉={ceil(n/3)}", gp == ceil(n/3))
for n in range(3, 11):
    gc, _ = gamma(cycle(n))
    check(f"C_{n}: γ={gc}, ⌈n/3⌉={ceil(n/3)}", gc == ceil(n/3))

print("--- خانواده‌ها ---")
for n in range(1, 8):
    check(f"K_{n}: γ={gamma(complete(n))[0]}", gamma(complete(n))[0] == 1)
for m in range(1, 5):
    for n in range(m, 6):
        exp = 1 if min(m, n) == 1 else 2
        g = gamma(bipartite(m, n))[0]
        check(f"K_{{{m},{n}}}: γ={g} (انتظار {exp})", g == exp)
for n in range(2, 9):
    check(f"S_{n}: γ={gamma(star(n))[0]}", gamma(star(n))[0] == 1)
for n in range(3, 9):
    check(f"W_{n}: γ={gamma(wheel(n))[0]}", gamma(wheel(n))[0] == 1)

print("--- کران پایین γ ≥ n/(Δ+1) و قضیه اور ---")
graphs = {}
for n in range(1, 8): graphs[f"P_{n}"] = path(n)
for n in range(3, 9): graphs[f"C_{n}"] = cycle(n)
for m in range(1, 4):
    for n in range(m, 5): graphs[f"K_{m},{n}"] = bipartite(m, n)
for n in range(3, 7): graphs[f"W_{n}"] = wheel(n)
graphs["K_5"] = complete(5); graphs["S_6"] = star(6)
for name, G in graphs.items():
    g, adj = gamma(G)
    n = G[0]; D = delta(adj)
    check(f"{name}: γ={g} ≥ n/(Δ+1)={n/(D+1):.2f}", g >= n/(D+1) - 1e-9)
    if all(len(adj[v]) > 0 for v in adj):
        check(f"{name}: قضیه اور γ={g} ≤ n/2={n/2}", g <= n/2)

print("--- اثر اضافه کردن یال: γ هرگز افزایش نمی‌یابد ---")
import random
random.seed(1)
cnt = 0
for _ in range(60):
    n = random.randint(3, 7)
    all_e = [(i, j) for i in range(n) for j in range(i+1, n)]
    E = random.sample(all_e, random.randint(0, len(all_e)-1))
    g1, _ = gamma((n, E))
    missing = [e for e in all_e if e not in E]
    e = random.choice(missing)
    g2, _ = gamma((n, E + [e]))
    cnt += 1
    if g2 > g1: ok = False; print("FAIL", n, E, e)
check(f"{cnt} آزمایش تصادفی: افزودن یال γ را افزایش نمی‌دهد", True)

print("\nنتیجه نهایی:", "همه‌ی بررسی‌ها موفق" if ok else "خطا وجود دارد")
