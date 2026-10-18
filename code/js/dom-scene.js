/*!
 * dom-scene.js — موتور مشترک صحنه‌های احاطه‌گری (نسخه ۶.۴.۰)
 *
 * هر صحنه یک گراف، یک لیست انتخاب (picks) و یک مقدار γ دارد. زمان‌بندی درون هر صحنه:
 *   - ۰ تا ۰٫۸ ثانیه: ظاهر شدن گره‌ها
 *   - ۱٫۰ تا ۲٫۰ ثانیه: ظاهر شدن یال‌ها (گام ۰٫۰۵ برای هر یال)
 *   - هر انتخاب در زمان at: رنگ گرفتن گره، و پخش موج پوشش به N[v] در ۰٫۹ ثانیه
 *   - ۰ تا DRAW_END (۸ ثانیه): رسم صحنه
 *   - DRAW_END تا FADE_END (۱۰ ثانیه): محو شدن صحنه به رنگ پس‌زمینه
 *
 * هر تب (بخش) صحنه‌ی خودش را دارد. موتور هنگام اسکرول، پیشرفت p را از موقعیت اسکرول
 * نسبت به همان بخش به دست می‌آورد: p = (اسکرول − بالای بخش) / (بلندی بخش − بلندی نما).
 * یعنی انیمیشن از بالای تب تا پایین آن، در طول اسکرول همان تب پخش می‌شود و با بالا رفتن
 * اسکرول برمی‌گردد. با تغییر تب، صحنه‌ی آن تب از ابتدا شروع می‌شود.
 *
 * رنگ‌ها از توکن‌های CSS خوانده می‌شوند (--scene-*، --bead-i، --hatch-i)، پس با حالت
 * روشن/تاریک هماهنگ‌اند. رویداد «chalesh:theme» رنگ‌ها را دوباره می‌خواند.
 * صحنه فقط گراف است: هیچ متن یا فرمولی روی بوم نیست.
 *
 * استفاده:
 *   DomScene.mount({ container | canvas, sections: [el, ...], scenes: [spec, ...] })
 *   spec = { nodes: { شماره: [x, y] }, edges: [[a, b], ...],
 *            picks: [{ v, c, at }, ...], gamma }   (c: اندیس مهره، ۰ تا ۹)
 *   اگر sections داده نشود، صحنه‌ها پشت سر هم روی کل اسکرول صفحه پخش می‌شوند.
 *   مختصات در فضای ۱۶۰۰×۹۰۰ تعریف می‌شوند و بوم با حفظ نسبت به نما جا می‌شود.
 */
(function (global) {
  'use strict';

  const TAU = Math.PI * 2;
  const W = 1600, H = 900;           // فضای مختصات مشترک صحنه‌ها
  // ناحیه‌ی برش در نماهای عمودی (موبایل): فقط محدوده‌ی گراف، تا گره‌ها کوچک نشوند
  const CROP = { x: 440, y: 100, w: 720, h: 700 };
  const DRAW_END = 8.0;              // پایان رسم هر صحنه
  const FADE_END = 10.0;             // پایان محو هر صحنه؛ پایان بخش اسکرول آن
  const EASE = 0.18;                 // هموارسازی به سمت هدف در هر فریم
  const INK = '#1F2A25';             // متن روی مهره (مهره‌ها روشن‌اند)
  const NR = 28;                     // شعاع گره
  const NODE_D = 0.8, EDGE_T0 = 1.0, EDGE_STEP = 0.05, PULSE_D = 0.6, WAVE_LAG = 0.3, WAVE_D = 0.9;
  const FONT = '\"B Nazanin\", Tahoma, \"Segoe UI\", Arial, sans-serif';
  const DIGITS = ['\u06F0', '\u06F1', '\u06F2', '\u06F3', '\u06F4', '\u06F5', '\u06F6', '\u06F7', '\u06F8', '\u06F9'];

  const clamp = (x, a = 0, b = 1) => (x < a ? a : x > b ? b : x);
  const prog = (t, t0, d) => clamp((t - t0) / d);
  const fa = (n) => String(n).replace(/\d/g, (d) => DIGITS[+d]);

  // ترکیب دو رنگ hex با نسبت k (۰ = رنگ اول، ۱ = رنگ دوم)
  function mixHex(c1, c2, k) {
    const a = [1, 3, 5].map((i) => parseInt(c1.substr(i, 2), 16));
    const b = [1, 3, 5].map((i) => parseInt(c2.substr(i, 2), 16));
    const m = a.map((x, i) => Math.round(x + (b[i] - x) * k));
    return '#' + m.map((x) => x.toString(16).padStart(2, '0')).join('');
  }

  // رنگ‌های فعلی از توکن‌های CSS (حالت روشن یا تاریک)
  function readColors() {
    const cs = getComputedStyle(document.documentElement);
    const v = (name, fb) => cs.getPropertyValue(name).trim() || fb;
    const bead = [], hatch = [];
    for (let i = 0; i < 10; i++) {
      bead.push(v('--bead-' + i, '#B8A24E'));
      hatch.push(v('--hatch-' + i, '#675A29'));
    }
    return {
      BG: v('--scene-bg', '#FFF6E5'),
      GRIDC: v('--scene-grid', '#EFE3C6'),
      NSTROKE: v('--scene-node', '#5E6B64'),
      ECOL: v('--scene-edge', '#A9B3AC'),
      TEXT: v('--scene-text', '#5E6B64'),
      INK, bead, hatch,
    };
  }

  // ساخت یک صحنه: همسایگی، پوشش، و تابع رسم محتوای گراف (بدون پس‌زمینه و محو)
  function buildScene(spec) {
    const { nodes, edges, picks, gamma } = spec;
    const ids = Object.keys(nodes).map(Number);
    const adj = {};
    ids.forEach((v) => { adj[v] = new Set(); });
    edges.forEach(([a, b]) => { adj[a].add(b); adj[b].add(a); });
    const NB = (v) => new Set([v, ...adj[v]]);

    // بررسی ریاضی: مجموعه‌ی انتخاب‌ها باید احاطه‌گر و به اندازه‌ی γ باشد
    const full = new Set();
    picks.forEach((p) => NB(p.v).forEach((u) => full.add(u)));
    if (full.size !== ids.length) throw new Error('dom-scene: مجموعه‌ی انتخاب‌ها احاطه‌گر نیست');
    if (picks.length !== gamma) throw new Error('dom-scene: |D| با γ گراف برابر نیست');

    const pickOf = {};
    picks.forEach((p) => { pickOf[p.v] = p; });
    const coverersOf = {};
    ids.forEach((u) => { coverersOf[u] = picks.filter((p) => NB(p.v).has(u)); });

    // رنگ‌ها در لحظه‌ی رسم خوانده می‌شوند (با تغییر حالت، بدون ساخت دوباره)
    const fillOf = (C, pk) => C.bead[pk.c];
    const strokeOf = (C, pk) => C.hatch[pk.c];

    function drawGrid(g, C) {
      g.save();
      g.strokeStyle = C.GRIDC; g.lineWidth = 1; g.beginPath();
      for (let x = 0; x <= W; x += 40) { g.moveTo(x + 0.5, 0); g.lineTo(x + 0.5, H); }
      for (let y = 0; y <= H; y += 40) { g.moveTo(0, y + 0.5); g.lineTo(W, y + 0.5); }
      g.stroke();
      g.restore();
    }

    function drawEdges(g, C, t) {
      edges.forEach(([a, b], i) => {
        const p = prog(t, EDGE_T0 + i * EDGE_STEP, 0.3);
        if (p <= 0) return;
        const [x1, y1] = nodes[a], [x2, y2] = nodes[b];
        g.save();
        g.lineCap = 'round'; g.strokeStyle = C.ECOL; g.globalAlpha = p; g.lineWidth = 4;
        g.beginPath(); g.moveTo(x1, y1); g.lineTo(x2, y2); g.stroke();
        g.restore();
      });
      // موج پوشش: از رأس انتخاب‌شده به همسایه‌هایش
      picks.forEach((pk) => {
        const w = prog(t, pk.at + WAVE_LAG, WAVE_D);
        if (w <= 0) return;
        adj[pk.v].forEach((u) => {
          const [x1, y1] = nodes[pk.v], [x2, y2] = nodes[u];
          g.save();
          g.lineCap = 'round'; g.strokeStyle = fillOf(C, pk); g.lineWidth = 4; g.globalAlpha = 0.55 * w;
          g.beginPath(); g.moveTo(x1, y1); g.lineTo(x1 + (x2 - x1) * w, y1 + (y2 - y1) * w); g.stroke();
          g.restore();
        });
      });
    }

    function drawNode(g, C, t, v) {
      const k = prog(t, 0, NODE_D);
      if (k <= 0) return;
      const pk = pickOf[v];
      const hp = pk ? prog(t, pk.at, PULSE_D) : 0;
      const [x, y] = nodes[v];
      const s = 0.8 + 0.2 * k;
      g.save();
      g.globalAlpha = k;
      g.translate(x, y); g.scale(s, s);
      g.beginPath(); g.arc(0, 0, NR, 0, TAU); g.fillStyle = C.BG; g.fill();
      if (pk) {
        g.globalAlpha = k * hp; g.fillStyle = fillOf(C, pk); g.fill(); g.globalAlpha = k;
      } else {
        // راه‌راه برای هر انتخاب‌کننده‌ای که این گره را پوشش داده است
        const covers = coverersOf[v].filter((c) => t >= c.at + WAVE_LAG);
        if (covers.length) {
          g.save();
          g.beginPath(); g.arc(0, 0, NR - 2, 0, TAU); g.clip();
          g.rotate(-Math.PI / 4);
          covers.forEach((c, ci) => {
            const w = prog(t, c.at + WAVE_LAG, WAVE_D);
            for (let o = -48 + ci * 4; o < 48; o += 8) {
              g.globalAlpha = k * 0.2 * w;
              g.fillStyle = fillOf(C, c);
              g.fillRect(o, -48, 4, 96);
            }
          });
          g.restore();
        }
      }
      g.globalAlpha = k;
      g.beginPath(); g.arc(0, 0, NR - 2, 0, TAU);
      g.strokeStyle = pk ? mixHex(C.NSTROKE, strokeOf(C, pk), hp) : C.NSTROKE;
      g.lineWidth = 4; g.stroke();
      // شماره‌ی رأس بخشی از گراف است؛ روی مهره‌ی رنگی متن تیره می‌ماند
      g.font = '600 20px ' + FONT;
      g.textAlign = 'center'; g.textBaseline = 'middle';
      g.fillStyle = pk ? mixHex(C.TEXT, C.INK, hp) : C.TEXT;
      g.fillText(fa(v), 0, 1);
      g.restore();
    }

    // محتوای گراف در زمان محلی t (بدون پس‌زمینه و محو)
    function renderGraph(g, C, t) {
      drawGrid(g, C);
      drawEdges(g, C, t);
      ids.forEach((v) => drawNode(g, C, t, v));
    }

    return { renderGraph, coverageAt: (t) => {
      const s = new Set();
      picks.forEach((p) => { if (t >= p.at) NB(p.v).forEach((u) => s.add(u)); });
      return s.size;
    }, picks: picks.map((p) => p.v), gamma };
  }

  // ساخت کنترل اصلی: بوم، حلقه‌ی اسکرول، و نگاشت بخش‌ها به صحنه‌ها
  function mount(cfg) {
    const scenes = cfg.scenes.map(buildScene);
    const N = scenes.length;
    if (!N) throw new Error('dom-scene: حداقل یک صحنه لازم است');
    const sections = cfg.sections && cfg.sections.length ? cfg.sections : null;
    if (sections && sections.length !== N) throw new Error('dom-scene: تعداد بخش‌ها با تعداد صحنه‌ها برابر نیست');

    let canvas = cfg.canvas;
    if (!canvas) {
      canvas = document.createElement('canvas');
      canvas.setAttribute('aria-hidden', 'true');
      cfg.container.appendChild(canvas);
    }
    const g = canvas.getContext('2d');
    let C = readColors();

    // نگاشت فضای ۱۶۰۰×۹۰۰ به بوم (حفظ نسبت، با حاشیه)
    const view = { fit: 1, ox: 0, oy: 0, dpr: 1 };
    function resize() {
      const dpr = Math.min(global.devicePixelRatio || 1, 2);
      const cw = canvas.clientWidth || W, ch = canvas.clientHeight || H;
      canvas.width = Math.round(cw * dpr);
      canvas.height = Math.round(ch * dpr);
      // نمای افقی: کل فضای ۱۶۰۰×۹۰۰؛ نمای عمودی: برش گراف، با حفظ نسبت و در مرکز
      const vb = cw >= ch ? { x: 0, y: 0, w: W, h: H } : CROP;
      view.dpr = dpr;
      view.fit = Math.min(canvas.width / vb.w, canvas.height / vb.h);
      view.ox = (canvas.width - vb.w * view.fit) / 2 - vb.x * view.fit;
      view.oy = (canvas.height - vb.h * view.fit) / 2 - vb.y * view.fit;
    }

    const reduce = global.matchMedia && global.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const mobile = global.matchMedia && global.matchMedia('(max-width: 768px)').matches;
    const minDt = 1000 / (mobile ? 30 : 60);  // سقف نرخ: ۳۰ روی موبایل، ۶۰ روی دسکتاپ
    const st = { current: 0, target: 0, raf: 0, last: 0, frames: 0, running: true };

    // بخش فعال: اولین بخشی که در صفحه نمایش داده می‌شود (بدون بخش، صفر)
    const activeSection = () => {
      if (!sections) return 0;
      const i = sections.findIndex((el) => el && el.getClientRects().length > 0);
      return i < 0 ? 0 : i;
    };

    // پیشرفت اسکرول در [0, 1]: در بخش فعال اگر بخش دارد، وگرنه روی کل صفحه
    const progress = () => {
      if (!sections) {
        const max = (document.documentElement.scrollHeight || 0) - global.innerHeight;
        return clamp(global.scrollY / Math.max(1, max));
      }
      const el = sections[activeSection()];
      const top = el.getBoundingClientRect().top + global.scrollY;
      const range = el.offsetHeight - global.innerHeight;
      if (range <= 0) return 1;
      return clamp((global.scrollY - top) / range);
    };

    // صحنه‌ی فعال و زمان محلی آن
    const locate = (P) => {
      if (sections) return { k: activeSection(), t: clamp(P) * FADE_END };
      const k = Math.min(N - 1, Math.floor(P * N));
      return { k, t: clamp(P * N - k) * FADE_END };
    };

    function render(P) {
      const { k, t } = locate(P);
      g.setTransform(1, 0, 0, 1, 0, 0);
      g.globalAlpha = 1;
      g.fillStyle = C.BG;
      g.fillRect(0, 0, canvas.width, canvas.height);
      g.setTransform(view.fit, 0, 0, view.fit, view.ox, view.oy);
      scenes[k].renderGraph(g, C, t);
      // محو: از DRAW_END تا FADE_END، صحنه به رنگ پس‌زمینه می‌رسد
      const fade = clamp((t - DRAW_END) / (FADE_END - DRAW_END));
      if (fade > 0) {
        g.globalAlpha = fade;
        g.fillStyle = C.BG;
        g.fillRect(-view.ox / view.fit, -view.oy / view.fit, canvas.width / view.fit, canvas.height / view.fit);
      }
      g.globalAlpha = 1;
      st.frames++;
    }

    const kick = () => {
      if (!st.raf && st.running && !document.hidden && !reduce) st.raf = global.requestAnimationFrame(tick);
    };
    function tick(now) {
      st.raf = 0;
      if (document.hidden || !st.running) return;
      if (now - st.last < minDt) { kick(); return; }
      st.last = now;
      const d = st.target - st.current;
      if (Math.abs(d) < 1e-6) { st.current = st.target; render(st.current); return; }
      st.current += d * EASE;
      render(st.current);
      kick();
    }
    function onScroll() {
      st.target = progress();
      kick();
    }
    // تغییر تب: صحنه‌ی تازه از ابتدای خودش، بدون گذار از صحنه‌ی قبلی
    function onSectionChange() {
      st.target = st.current = progress();
      render(st.current);
      kick();
    }
    function onResize() {
      resize();
      if (reduce) render(st.current);
      else { onScroll(); render(st.current); }
    }
    function onTheme() {
      C = readColors();
      render(st.current);
    }

    resize();
    C = readColors();
    if (reduce) {
      // کاهش حرکت: فریم ثابت (t = DRAW_END) از صحنه‌ی فعال، گراف کامل بدون محو و بدون اسکرول
      st.current = st.target = DRAW_END / FADE_END;
      render(st.current);
    } else {
      global.addEventListener('scroll', onScroll, { passive: true });
      global.addEventListener('resize', onResize);
      global.addEventListener('chalesh:theme', onTheme);
      if (sections && global.MutationObserver) {
        const mo = new MutationObserver(() => onSectionChange());
        sections.forEach((el) => { if (el) mo.observe(el, { attributes: true, attributeFilter: ['class', 'hidden', 'style'] }); });
      }
      document.addEventListener('visibilitychange', () => {
        if (document.hidden) { global.cancelAnimationFrame(st.raf); st.raf = 0; }
        else { st.last = 0; kick(); }
      });
      onScroll();
      render(st.current);
    }

    return {
      progress,
      time: () => locate(st.current).t,            // زمان محلی صحنه‌ی فعال
      scene: () => locate(st.current).k,           // اندیس صحنه‌ی فعال
      frames: () => st.frames,
      scrubEnd: FADE_END,
      count: N,
      colors: () => C,
      coverageAt: (t, k = 0) => scenes[k].coverageAt(t),
      picks: (k = 0) => scenes[k].picks.slice(),
      pause() { st.running = false; global.cancelAnimationFrame(st.raf); st.raf = 0; },
      resume() { st.running = true; kick(); },
      renderAt(P) { st.running = false; st.current = P; render(P); },
      // شعاع گره بر حسب پیکسل CSS (برای آزمون خوانایی روی موبایل)
      nodePx: () => NR * view.fit / view.dpr,
    };
  }

  global.DomScene = { mount, DRAW_END, FADE_END };
})(window);
