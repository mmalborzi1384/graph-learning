/**
 * graphs.js — تعریف گراف‌های از پیش‌تعریف‌شده و توابع کمکی احاطه‌گری.
 * پروژه‌ی «چالش γ» — ریاضیات گسسته ۱۲، فصل ۲، درس ۲. (نسخه‌ی ۶.۳.۰)
 *
 * نمادگذاری:
 *   G = (V, E)، رئوس با شماره‌های 1..n در UI و اندیس‌های 0..n-1 در داخل.
 *   N(v): مجموعه‌ی همسایگان v.  N[v] = N(v) ∪ {v}.
 *   مجموعه‌ی D احاطه‌گر است اگر ∪_{v∈D} N[v] = V.
 *   γ(G): کمترین اندازه‌ی مجموعه‌ی احاطه‌گر.
 *
 * تمام مجموعه‌ها با ماسک بیتی (عدد صحیح) نمایش داده می‌شوند؛ بیت v یعنی رأس v.
 * جستجوی فراگیر برای n ≤ MAX_N (= ۱۰) مجاز است (حداکثر ۲^۱۰ = ۱۰۲۴ حالت).
 *
 * این فایل بدون وابستگی و به‌صورت اسکریپت ساده بارگذاری می‌شود و
 * API آن از طریق window.GraphLib در دسترس است.
 */
(function (global) {
  'use strict';

  /** حداکثر تعداد رأس برای محاسبه‌ی خودکار γ */
  const MAX_N = 10;

  /**
   * نمایش دکمه‌ی «محاسبه‌ی γ(G)» در بخش اطلاعات گراف.
   * برای کلاسی که می‌خواهد γ را فقط از معلم بپرسد، false کنید.
   */
  const SHOW_GAMMA_BUTTON = true;

  /* ------------------------------------------------------------------
   * ساخت گراف‌های استاندارد (نمادگذاری کتاب)
   * ------------------------------------------------------------------ */

  /** مسیر P_n: n رأس، n−1 یال. */
  function path(n) {
    const edges = [];
    for (let i = 0; i < n - 1; i++) edges.push([i, i + 1]);
    return { n, edges, layout: 'line' };
  }

  /** دور C_n (n ≥ 3). */
  function cycle(n) {
    const edges = [];
    for (let i = 0; i < n; i++) edges.push([i, (i + 1) % n]);
    return { n, edges, layout: 'circle' };
  }

  /** گراف کامل K_n. */
  function complete(n) {
    const edges = [];
    for (let i = 0; i < n; i++)
      for (let j = i + 1; j < n; j++) edges.push([i, j]);
    return { n, edges, layout: 'circle' };
  }

  /** گراف ستاره S_n: n رأس، رأس ۰ مرکز و بقیه برگ. */
  function star(n) {
    const edges = [];
    for (let i = 1; i < n; i++) edges.push([0, i]);
    return { n, edges, layout: 'star' };
  }

  /** گراف دوبخشی کامل K_{m,n}: بخش اول رأس‌های 0..m−1، بخش دوم m..m+n−1. */
  function bipartite(m, n) {
    const edges = [];
    for (let i = 0; i < m; i++)
      for (let j = 0; j < n; j++) edges.push([i, m + j]);
    return { n: m + n, edges, layout: 'bip', parts: [m, n] };
  }

  /** چرخ W_n: دور C_n به‌علاوه‌ی رأس مرکزی (رأس n). جمعاً n+1 رأس. */
  function wheel(n) {
    const c = cycle(n);
    const edges = c.edges.slice();
    for (let i = 0; i < n; i++) edges.push([i, n]);
    return { n: n + 1, edges, layout: 'wheel' };
  }

  /**
   * گراف پترسن: ۱۰ رأس، سه‌منظم.
   * رئوس ۰ تا ۴: پنج‌ضلعی بیرونی (دور C_5)؛ رئوس ۵ تا ۹: پنج‌ضلعی درونی ستاره‌ای.
   * رأس درونی ۵+i به رأس‌های درونی ۵+((i+۲) mod ۵) و ۵+((i+۳) mod ۵) مجاور است؛
   * و یال‌های عمودی i ↔ i+۵ دو پنج‌ضلعی را وصل می‌کنند.
   */
  function petersen() {
    const edges = [];
    for (let i = 0; i < 5; i++) edges.push([i, (i + 1) % 5]);
    for (let i = 0; i < 5; i++) edges.push([i, i + 5]);
    for (let i = 0; i < 5; i++) edges.push([5 + i, 5 + ((i + 2) % 5)]);
    return { n: 10, edges, layout: 'petersen' };
  }

  /* ------------------------------------------------------------------
   * کتابخانه‌ی گراف‌های بازی
   * هر مورد: id، نام نمایشی (HTML امن و ثابت)، خانواده، و ساختار گراف.
   * ------------------------------------------------------------------ */
  const LIBRARY_DEFS = [
    { id: 'P3', name: 'P<sub>3</sub>', family: 'مسیر', build: () => path(3) },
    { id: 'P4', name: 'P<sub>4</sub>', family: 'مسیر', build: () => path(4) },
    { id: 'P5', name: 'P<sub>5</sub>', family: 'مسیر', build: () => path(5) },
    { id: 'P6', name: 'P<sub>6</sub>', family: 'مسیر', build: () => path(6) },
    { id: 'P7', name: 'P<sub>7</sub>', family: 'مسیر', build: () => path(7) },
    { id: 'C3', name: 'C<sub>3</sub>', family: 'دور', build: () => cycle(3) },
    { id: 'C4', name: 'C<sub>4</sub>', family: 'دور', build: () => cycle(4) },
    { id: 'C5', name: 'C<sub>5</sub>', family: 'دور', build: () => cycle(5) },
    { id: 'C6', name: 'C<sub>6</sub>', family: 'دور', build: () => cycle(6) },
    { id: 'C7', name: 'C<sub>7</sub>', family: 'دور', build: () => cycle(7) },
    { id: 'K3', name: 'K<sub>3</sub>', family: 'کامل', build: () => complete(3) },
    { id: 'K4', name: 'K<sub>4</sub>', family: 'کامل', build: () => complete(4) },
    { id: 'K5', name: 'K<sub>5</sub>', family: 'کامل', build: () => complete(5) },
    { id: 'S4', name: 'S<sub>4</sub>', family: 'ستاره', build: () => star(4) },
    { id: 'S5', name: 'S<sub>5</sub>', family: 'ستاره', build: () => star(5) },
    { id: 'K14', name: 'K<sub>1,4</sub>', family: 'دوبخشی', build: () => bipartite(1, 4) },
    { id: 'K22', name: 'K<sub>2,2</sub>', family: 'دوبخشی', build: () => bipartite(2, 2) },
    { id: 'K23', name: 'K<sub>2,3</sub>', family: 'دوبخشی', build: () => bipartite(2, 3) },
    { id: 'K33', name: 'K<sub>3,3</sub>', family: 'دوبخشی', build: () => bipartite(3, 3) },
    { id: 'W4', name: 'W<sub>4</sub>', family: 'چرخ', build: () => wheel(4) },
    { id: 'W5', name: 'W<sub>5</sub>', family: 'چرخ', build: () => wheel(5) },
    { id: 'PT', name: 'پترسن', family: 'منظم', build: () => petersen() },
  ];

  /* ------------------------------------------------------------------
   * توابع پایه‌ی گراف و احاطه‌گری (ماسک بیتی)
   * ------------------------------------------------------------------ */

  /** تعداد بیت‌های یک‌ (وزن همینگ) برای ماسک. */
  function popcount(mask) {
    let c = 0;
    while (mask) { mask &= mask - 1; c++; }
    return c;
  }

  /** ماسک کامل: همه‌ی n رأس. */
  function fullMask(n) {
    return (1 << n) - 1;
  }

  /**
   * ماسک بسته‌ی همسایگی N[v] برای هر رأس v.
   * @returns {number[]} closed[v] = ماسکی از N[v] شامل خود v.
   */
  function closedNeighborhoods(n, edges) {
    const closed = new Array(n);
    for (let v = 0; v < n; v++) closed[v] = 1 << v;
    for (const [a, b] of edges) {
      closed[a] |= 1 << b;
      closed[b] |= 1 << a;
    }
    return closed;
  }

  /** فهرست همسایگان (بدون خود رأس) برای نمایش. */
  function neighborLists(n, edges) {
    const adj = Array.from({ length: n }, () => []);
    for (const [a, b] of edges) {
      adj[a].push(b);
      adj[b].push(a);
    }
    return adj.map((list) => list.sort((x, y) => x - y));
  }

  /** پوشش یک مجموعه‌ی مهره‌ها: ∪_{v∈S} N[v] به‌صورت ماسک. */
  function coverage(closed, S) {
    let cov = 0;
    for (let v = 0; v < closed.length; v++) if (S & (1 << v)) cov |= closed[v];
    return cov;
  }

  /** آیا S مجموعه‌ی احاطه‌گر است؟ */
  function isDominating(n, closed, S) {
    return coverage(closed, S) === fullMask(n);
  }

  /** لیست رئوس پوشش‌نداده (اندیس‌های صفر-مبنا). */
  function uncoveredVertices(n, closed, S) {
    const cov = coverage(closed, S);
    const out = [];
    for (let v = 0; v < n; v++) if (!(cov & (1 << v))) out.push(v);
    return out;
  }

  /**
   * محاسبه‌ی γ(G) با جستجوی فراگیر.
   * @returns {{gamma:number, minSets:number[]}|null}
   *   gamma: عدد احاطه‌گری؛ minSets: همه‌ی مجموعه‌های احاطه‌گر مینیمم (ماسک).
   *   در صورت n > MAX_N مقدار null برمی‌گرداند.
   */
  function computeGamma(n, edges) {
    if (n > MAX_N || n < 1) return null;
    const closed = closedNeighborhoods(n, edges);
    const full = fullMask(n);
    for (let k = 1; k <= n; k++) {
      const minSets = [];
      for (let S = 1; S <= full; S++) {
        if (popcount(S) === k && coverage(closed, S) === full) minSets.push(S);
      }
      if (minSets.length) return { gamma: k, minSets };
    }
    return { gamma: n, minSets: [full] }; // نرسیده‌ایم؛ برای ایمنی
  }

  /** بیشینه‌ی درجه Δ(G). */
  function maxDegree(n, edges) {
    const deg = new Array(n).fill(0);
    for (const [a, b] of edges) { deg[a]++; deg[b]++; }
    return n ? Math.max(...deg) : 0;
  }

  /** آیا رأس منفرد (بدون همسایه) دارد؟ */
  function hasIsolatedVertex(n, edges) {
    const deg = new Array(n).fill(0);
    for (const [a, b] of edges) { deg[a]++; deg[b]++; }
    return deg.some((d) => d === 0);
  }

  /** آیا یال {a,b} وجود دارد؟ */
  function hasEdge(edges, a, b) {
    return edges.some(([x, y]) => (x === a && y === b) || (x === b && y === a));
  }

  /* ------------------------------------------------------------------
   * احاطه‌گر مینیمال و تحلیل یک مجموعه (نسخه‌ی ۶.۳.۰)
   *
   * مجموعه‌ی احاطه‌گر D «مینیمال» است اگر هیچ زیرمجموعه‌ی سره‌ی آن احاطه‌گر
   * نباشد. «مینیمم» است اگر |D| = γ(G) باشد. هر مینیمم مینیمال است، ولی عکس
   * آن لازم نیست درست باشد.
   *
   * لم: هر ابرمجموعه‌ی یک مجموعه‌ی احاطه‌گر، احاطه‌گر است. پس برای تشخیص
   * مینیمال بودن کافی است حذف تک‌تک اعضا را بررسی کنیم: اگر T ⊂ D احاطه‌گر
   * باشد و v ∈ D∖T، آنگاه D∖{v} ⊇ T احاطه‌گر است.
   * ------------------------------------------------------------------ */

  /** آیا S احاطه‌گر است و حذف هیچ عضوی آن را از احاطه‌گری نمی‌اندازد؟ */
  function isMinimalDominating(n, closed, S) {
    if (!isDominating(n, closed, S)) return false;
    for (let v = 0; v < n; v++) {
      if (S & (1 << v) && isDominating(n, closed, S & ~(1 << v))) return false;
    }
    return true;
  }

  /**
   * همه‌ی مجموعه‌های احاطه‌گر مینیمال (ماسک). برای n > MAX_N فهرست خالی است.
   * @returns {number[]} به ترتیب عددی ماسک.
   */
  function minimalDominatingSets(n, closed) {
    if (n > MAX_N || n < 1) return [];
    const out = [];
    const full = fullMask(n);
    for (let S = 1; S <= full; S++) {
      if (isMinimalDominating(n, closed, S)) out.push(S);
    }
    return out;
  }

  /**
   * تحلیل کامل یک مجموعه‌ی مهره‌ها برای آموزش و تمرین.
   * @returns {{k:number, dominating:boolean, minimal:boolean, minimum:boolean, redundant:number[]}}
   *   redundant: رأس‌هایی که حذفشان احاطه‌گری را نگه می‌دارد (در مجموعه‌ی غیرمینیمال زائدند).
   */
  function analyzeSet(graph, S) {
    const dominating = isDominating(graph.n, graph.closed, S);
    const redundant = [];
    if (dominating) {
      for (let v = 0; v < graph.n; v++) {
        if (S & (1 << v) && isDominating(graph.n, graph.closed, S & ~(1 << v))) redundant.push(v);
      }
    }
    const minimal = dominating && redundant.length === 0;
    const minimum = dominating && graph.gamma !== null && popcount(S) === graph.gamma;
    return { k: popcount(S), dominating, minimal, minimum, redundant };
  }

  /**
   * ساخت یک گراف با n رأس و عدد احاطه‌گری k (۱ ≤ k ≤ n، ۲ ≤ n ≤ MAX_N).
   * ابتدا چند گراف تصادفی امتحان می‌شود. اگر پیدا نشد، گراف قطعی با k مؤلفه‌ی
   * ستاره ساخته می‌شود: هر ستاره γ = ۱ دارد و γ مجموع مؤلفه‌هاست، پس γ = k.
   * @returns {number[][]|null} فهرست یال‌ها، یا null برای ورودی نامعتبر.
   */
  function generateWithGamma(n, k, attempts) {
    if (!Number.isInteger(n) || !Number.isInteger(k)) return null;
    if (n < 2 || n > MAX_N || k < 1 || k > n) return null;
    const tries = attempts === undefined ? 300 : attempts;
    for (let t = 0; t < tries; t++) {
      const p = 0.15 + Math.random() * 0.45;
      const edges = [];
      for (let i = 0; i < n; i++)
        for (let j = i + 1; j < n; j++)
          if (Math.random() < p) edges.push([i, j]);
      const res = computeGamma(n, edges);
      if (res && res.gamma === k) return edges;
    }
    // ساخت قطعی: k ستاره با اندازه‌های جمعاً n
    const sizes = new Array(k).fill(1);
    for (let r = 0; r < n - k; r++) sizes[Math.floor(Math.random() * k)]++;
    const edges = [];
    let start = 0;
    for (const size of sizes) {
      for (let j = 1; j < size; j++) edges.push([start, start + j]);
      start += size;
    }
    return edges;
  }

  /* ------------------------------------------------------------------
   * طرح‌بندی رئوس برای SVG (مختصات در فضای 320×320)
   * ------------------------------------------------------------------ */
  const BOX = 320;
  const CX = BOX / 2;
  const CY = BOX / 2;
  const R = 115;

  /**
   * مختصات رئوس.
   * @returns {{x:number,y:number}[]} به ترتیب اندیس رأس.
   */
  function layoutPoints(graph) {
    const { n, layout } = graph;
    const pts = [];
    if (layout === 'line') {
      for (let i = 0; i < n; i++) {
        const x = n === 1 ? CX : 40 + (i * (BOX - 80)) / (n - 1);
        pts.push({ x, y: CY });
      }
    } else if (layout === 'circle') {
      for (let i = 0; i < n; i++) {
        const a = -Math.PI / 2 + (2 * Math.PI * i) / n;
        pts.push({ x: CX + R * Math.cos(a), y: CY + R * Math.sin(a) });
      }
    } else if (layout === 'star') {
      pts.push({ x: CX, y: CY });
      const m = n - 1;
      for (let i = 0; i < m; i++) {
        const a = -Math.PI / 2 + (2 * Math.PI * i) / m;
        pts.push({ x: CX + R * Math.cos(a), y: CY + R * Math.sin(a) });
      }
    } else if (layout === 'bip') {
      const [m, k] = graph.parts;
      for (let i = 0; i < m; i++)
        pts.push({ x: 90, y: CY + (i - (m - 1) / 2) * (m > 1 ? 120 : 0) });
      for (let j = 0; j < k; j++)
        pts.push({ x: 230, y: CY + (j - (k - 1) / 2) * (k > 1 ? 90 : 0) });
    } else if (layout === 'petersen') {
      // پنج رأس بیرونی روی دایره‌ی بزرگ، پنج رأس درونی روی دایره‌ی کوچک‌تر، هم‌زاویه با بیرونی‌ها
      for (let i = 0; i < 5; i++) {
        const a = -Math.PI / 2 + (2 * Math.PI * i) / 5;
        pts.push({ x: CX + R * Math.cos(a), y: CY + R * Math.sin(a) });
      }
      for (let i = 0; i < 5; i++) {
        const a = -Math.PI / 2 + (2 * Math.PI * i) / 5;
        pts.push({ x: CX + 0.45 * R * Math.cos(a), y: CY + 0.45 * R * Math.sin(a) });
      }
    } else if (layout === 'wheel') {
      const m = n - 1;
      for (let i = 0; i < m; i++) {
        const a = -Math.PI / 2 + (2 * Math.PI * i) / m;
        pts.push({ x: CX + R * Math.cos(a), y: CY + R * Math.sin(a) });
      }
      pts.push({ x: CX, y: CY }); // مرکز
    }
    return pts;
  }

  /** برچسب رأس برای نمایش (شماره‌ی ۱-مبنا؛ مرکز چرخ با «c»). */
  function vertexLabel(graph, v) {
    if (graph.layout === 'wheel' && v === graph.n - 1) return 'c';
    return String(v + 1);
  }

  /* ------------------------------------------------------------------
   * رابط عمومی: ساخت شیء گراف کامل از شناسه
   * ------------------------------------------------------------------ */

  /** فهرست خلاصه‌ی گراف‌ها برای منوی کشویی. */
  function listGraphs() {
    return LIBRARY_DEFS.map(({ id, name, family }) => ({ id, name, family }));
  }

  /**
   * شیء کامل گراف با همه‌ی اطلاعات محاسباتی.
   * @param {string} id شناسه‌ی گراف (مثلاً 'C4')
   */
  function getGraph(id) {
    const def = LIBRARY_DEFS.find((d) => d.id === id);
    if (!def) throw new Error('گراف ناشناخته: ' + id);
    const base = def.build();
    const { n, edges } = base;
    const closed = closedNeighborhoods(n, edges);
    const res = computeGamma(n, edges);
    return {
      id,
      name: def.name,
      family: def.family,
      n,
      edges,
      layout: base.layout,
      parts: base.parts,
      closed,
      adj: neighborLists(n, edges),
      delta: maxDegree(n, edges),
      gamma: res ? res.gamma : null,
      minSets: res ? res.minSets : [],
      minimal: minimalDominatingSets(n, closed),
      points: layoutPoints({ n, layout: base.layout, parts: base.parts }),
    };
  }

  /** گراف دلخواه از فهرست یال‌ها (برای آزمایشگاه یال). */
  function makeCustomGraph(n, edges, layout, parts, name) {
    const closed = closedNeighborhoods(n, edges);
    const res = computeGamma(n, edges);
    return {
      id: 'custom',
      name: name || 'گراف سفارشی',
      family: 'سفارشی',
      n,
      edges,
      layout,
      parts,
      closed,
      adj: neighborLists(n, edges),
      delta: maxDegree(n, edges),
      gamma: res ? res.gamma : null,
      minSets: res ? res.minSets : [],
      minimal: minimalDominatingSets(n, closed),
      points: layoutPoints({ n, layout, parts }),
    };
  }

  /**
   * امتیازدهی نسخه‌ی ۶.۳.۰ (دو مرحله‌ای):
   *   notDominating   (احاطه‌گر نیست)                      ۰ امتیاز
   *   validNonMinimal (احاطه‌گر، ولی مینیمال نیست)          ۵ امتیاز
   *   minimal         (مینیمال، ولی مینیمم نیست: |D| > γ)  ۱۰ امتیاز
   *   exact           (مینیمم: |D| = γ)                      ۱۵ امتیاز
   * هر مینیمم مینیمال است؛ پس چهار وضعیت مجزا و کامل‌اند.
   */
  function evaluateMarks(graph, marks) {
    const a = analyzeSet(graph, marks);
    const missing = uncoveredVertices(graph.n, graph.closed, marks);
    let status = 'notDominating';
    if (a.dominating) {
      if (a.minimum) status = 'exact';
      else if (a.minimal) status = 'minimal';
      else status = 'validNonMinimal';
    }
    const POINTS = { notDominating: 0, validNonMinimal: 5, minimal: 10, exact: 15 };
    return {
      k: a.k, dominating: a.dominating, minimal: a.minimal, minimum: a.minimum,
      missing, redundant: a.redundant, status, points: POINTS[status],
    };
  }

  global.GraphLib = {
    MAX_N,
    SHOW_GAMMA_BUTTON,
    path, cycle, complete, star, bipartite, wheel,
    popcount, fullMask, closedNeighborhoods, neighborLists, coverage,
    isDominating, uncoveredVertices, computeGamma, maxDegree,
    hasIsolatedVertex, hasEdge, layoutPoints, vertexLabel,
    listGraphs, getGraph, makeCustomGraph, evaluateMarks,
    isMinimalDominating, minimalDominatingSets, analyzeSet, generateWithGamma,
    MAX_N_VALUE: MAX_N,
  };
})(window);
