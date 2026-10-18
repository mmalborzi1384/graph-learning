/* ============================================================================
   intro.js · گراف‌های صفحه‌ی معرفی
   ----------------------------------------------------------------------------
   - گراف‌ها را با SVG می‌سازد (بدون کتابخانه‌ی خارجی).
   - مجموعه‌ی احاطه‌گر و پوشش را از روی داده‌ها محاسبه می‌کند (نه به‌صورت دستی).
   - اگر شکل داخل یک بخش پین/پن باشد، با --sc-p که موتور scrollcraft روی بخش
     می‌نویسد پیش می‌رود. شکل‌های بیرون از بخش، یک‌بار با data-marked رسم می‌شوند.
   - «موج پوشش»: هاشور از رأس انتخاب‌شده با تأخیر متناسب با فاصله‌ی گرافی پخش می‌شود.
   ============================================================================ */
(function () {
  'use strict';

  var NS = 'http://www.w3.org/2000/svg';
  var FA = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹'];
  var uid = 0;

  /** عدد لاتین را به رقم فارسی تبدیل می‌کند. */
  function toFa(x) {
    return String(x).replace(/[0-9]/g, function (d) { return FA[+d]; });
  }

  /* ---------- کارت‌ها: محوشدن متقاطع با اسکرول ---------- */
  var cardSets = [];
  var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)');

  /** هر بخش [data-cards] را ثبت می‌کند. */
  function bindCards() {
    document.documentElement.classList.add('js');
    document.querySelectorAll('[data-cards]').forEach(function (act) {
      cardSets.push({
        act: act,
        cards: Array.prototype.slice.call(act.querySelectorAll('.card')),
        count: act.querySelector('[data-cards-count]'),
        lastP: -1
      });
    });
  }

  /**
   * موقعیت x = p·(n−۱) است. کارت i با opacity = 1 − |x − i| دیده می‌شود، پس وسط دو کارت
   * هر دو نیمه‌شفاف‌اند و مجموع opacity همواره ۱ است. با حرکت کاهش‌یافته فقط کارت فعال دیده می‌شود.
   */
  function renderCards(c, p) {
    var n = c.cards.length;
    if (!n) return;
    var t = Math.min(1, Math.max(0, p));
    var x = t * (n - 1);
    var active = Math.round(x);
    var snap = !!(reduceMotion && reduceMotion.matches);
    c.cards.forEach(function (card, i) {
      var o = snap ? (i === active ? 1 : 0) : Math.max(0, 1 - Math.abs(x - i));
      card.style.opacity = o.toFixed(3);
      card.style.transform = snap ? 'none' : 'scale(' + (0.97 + 0.03 * o).toFixed(4) + ')';
      card.style.pointerEvents = o >= 0.5 ? 'auto' : 'none';
      card.setAttribute('aria-hidden', o >= 0.5 ? 'false' : 'true');
    });
    if (c.count) c.count.textContent = toFa(active + 1) + ' از ' + toFa(n);
  }

  /** مختصات دایره‌ای برای دور C_n (بالا شروع می‌شود). */
  function ring(n) {
    var pts = [];
    for (var i = 0; i < n; i++) {
      var a = -Math.PI / 2 + (2 * Math.PI * i) / n;
      pts.push({ x: 300 + 150 * Math.cos(a), y: 180 + 150 * Math.sin(a) });
    }
    return pts;
  }

  /** مختصات خطی برای مسیر P_n. */
  function line(n) {
    var pts = [];
    for (var i = 0; i < n; i++) pts.push({ x: 70 + (460 * i) / (n - 1), y: 180 });
    return pts;
  }

  /** داده‌ی گراف‌ها. اندیس رأس‌ها از صفر است؛ برچسب نمایشی = اندیس + ۱. */
  var GRAPHS = {
    C6: { n: 6, edges: [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 0]], pos: ring(6) },
    P6: { n: 6, edges: [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5]], pos: line(6) },
    P7: { n: 7, edges: [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 6]], pos: line(7) }
  };

  /** گراف‌ها را برای همسایگی آماده می‌کند. */
  Object.keys(GRAPHS).forEach(function (k) {
    var g = GRAPHS[k];
    g.adj = [];
    for (var i = 0; i < g.n; i++) g.adj.push([]);
    g.edges.forEach(function (e) { g.adj[e[0]].push(e[1]); g.adj[e[1]].push(e[0]); });
  });

  /**
   * وضعیت پوشش را برای مجموعه‌ی marked محاسبه می‌کند.
   * covered[i] یعنی i در N[v] برای یک v ∈ D است.
   * dist[i] فاصله‌ی گرافی i از نزدیک‌ترین رأس D است (برای تأخیر موج).
   */
  function coverState(g, marked) {
    var covered = [], dist = [], queue = [], i;
    for (i = 0; i < g.n; i++) { covered.push(false); dist.push(-1); }
    marked.forEach(function (v) {
      covered[v] = true;
      dist[v] = 0;
      queue.push(v);
      g.adj[v].forEach(function (u) {
        covered[u] = true;
      });
    });
    // BFS چندمنبعی برای فاصله
    while (queue.length) {
      var v = queue.shift();
      g.adj[v].forEach(function (u) {
        if (dist[u] === -1) { dist[u] = dist[v] + 1; queue.push(u); }
      });
    }
    var count = covered.filter(Boolean).length;
    return { covered: covered, dist: dist, count: count };
  }

  /** یک عنصر SVG با ویژگی‌ها می‌سازد. */
  function el(tag, attrs) {
    var e = document.createElementNS(NS, tag);
    Object.keys(attrs || {}).forEach(function (k) { e.setAttribute(k, attrs[k]); });
    return e;
  }

  /** رنگ مهره‌ها: همان متغیرهای --bead-i و --hatch-i بازی (style.css)، در هر دو حالت روشن و تاریک. */
  var BEADS = 10;

  /** مسیر یک بخش دایره (برای پوشش مشترک). مرکز مبدأ محلی است. */
  function sectorPath(r, a0, a1) {
    var x0 = r * Math.cos(a0), y0 = r * Math.sin(a0);
    var x1 = r * Math.cos(a1), y1 = r * Math.sin(a1);
    var large = (a1 - a0) > Math.PI ? 1 : 0;
    return 'M0 0 L' + x0 + ' ' + y0 + ' A' + r + ' ' + r + ' 0 ' + large + ' 1 ' + x1 + ' ' + y1 + ' Z';
  }

  /**
   * SVG یک گراف را می‌سازد و یک تابع update برمی‌گرداند.
   * قاعده‌ی رنگ (همان بازی):
   *   - مهره: دایره‌ی یکدست با رنگ همان رأس.
   *   - رأس پوشش‌داده: هاشور با رنگ مهره‌های پوشاننده. اگر چند مهره پوشانند، دایره به بخش‌های مساوی تقسیم می‌شود.
   *   - رأس بی‌پوشش: خط‌چین قرمز (کلاس is-missing).
   * هر SVG الگوهای هاشور خودش را دارد؛ شناسه‌ها یکتا هستند.
   */
  function buildGraph(key, host) {
    var g = GRAPHS[key];
    var hatchId = 'hatch-' + (++uid);
    var svg = el('svg', {
      viewBox: '0 0 600 360',
      class: 'graph',
      role: 'img',
      'aria-label': 'گراف ' + key + ' با ' + g.n + ' رأس'
    });

    var defs = el('defs', {});
    for (var ci = 0; ci < BEADS; ci++) {
      var pattern = el('pattern', {
        id: hatchId + '-' + ci, patternUnits: 'userSpaceOnUse', width: 8, height: 8, patternTransform: 'rotate(45)'
      });
      pattern.appendChild(el('rect', { width: 8, height: 8, style: 'fill: var(--sheet)' }));
      pattern.appendChild(el('line', { x1: 0, y1: 0, x2: 0, y2: 8, style: 'stroke: var(--hatch-' + ci + ')', 'stroke-width': 2.2 }));
      defs.appendChild(pattern);
    }
    svg.appendChild(defs);

    var edges = el('g', {});
    g.edges.forEach(function (e) {
      edges.appendChild(el('line', {
        class: 'edge',
        x1: g.pos[e[0]].x, y1: g.pos[e[0]].y, x2: g.pos[e[1]].x, y2: g.pos[e[1]].y
      }));
    });
    svg.appendChild(edges);

    var verts = [];
    for (var i = 0; i < g.n; i++) {
      var grp = el('g', { class: 'v', transform: 'translate(' + g.pos[i].x + ' ' + g.pos[i].y + ')' });
      var bg = el('circle', { class: 'v-bg', r: 24 });
      var wedges = el('g', { class: 'v-wedges' });
      var label = el('text', { class: 'v-label' });
      label.textContent = toFa(i + 1);
      grp.appendChild(bg);
      grp.appendChild(wedges);
      grp.appendChild(label);
      svg.appendChild(grp);
      verts.push({ grp: grp, bg: bg, wedges: wedges });
    }

    host.appendChild(svg);

    /** پوشاننده‌های رأس i در مجموعه‌ی marked (شامل خود i). */
    function coverersOf(i, marked) {
      return marked.filter(function (j) { return j === i || g.adj[i].indexOf(j) !== -1; });
    }

    /** وضعیت گراف را بر اساس مجموعه‌ی marked به‌روز می‌کند. */
    function update(marked, showMissing) {
      var st = coverState(g, marked);
      for (var i = 0; i < g.n; i++) {
        var v = verts[i];
        var isMarked = marked.indexOf(i) !== -1;
        var isCovered = st.covered[i] && !isMarked;
        var isMissing = !st.covered[i] && showMissing;
        v.grp.classList.toggle('is-marked', isMarked);
        v.grp.classList.toggle('is-covered', isCovered);
        v.grp.classList.toggle('is-missing', isMissing);
        // موج پوشش: تأخیر متناسب با فاصله از نزدیک‌ترین رأس انتخاب‌شده
        v.bg.style.transitionDelay = (st.dist[i] > 0 ? st.dist[i] * 110 : 0) + 'ms';
        // پاک‌سازی بخش‌های قبلی
        while (v.wedges.firstChild) v.wedges.removeChild(v.wedges.firstChild);

        if (isMarked) {
          var mc = 'var(--bead-' + (i % BEADS) + ')';
          v.bg.style.fill = mc;
          v.bg.style.stroke = mc;
        } else if (isCovered) {
          var cv = coverersOf(i, marked);
          v.bg.style.fill = 'var(--sheet)';
          v.bg.style.stroke = '';
          if (cv.length === 1) {
            v.wedges.appendChild(el('circle', { r: 24, fill: 'url(#' + hatchId + '-' + (cv[0] % BEADS) + ')' }));
          } else {
            cv.forEach(function (j, t) {
              var a0 = -Math.PI / 2 + (2 * Math.PI * t) / cv.length;
              var a1 = -Math.PI / 2 + (2 * Math.PI * (t + 1)) / cv.length;
              v.wedges.appendChild(el('path', {
                d: sectorPath(24, a0, a1),
                fill: 'url(#' + hatchId + '-' + (j % BEADS) + ')'
              }));
            });
          }
        } else {
          v.bg.style.fill = 'var(--sheet)';
          v.bg.style.stroke = '';
        }
      }
      return st;
    }

    return { svg: svg, update: update, n: g.n };
  }

  /* ------------------------------------------------------------------
   * مراحل بخش‌های پیش‌رونده (بر اساس --sc-p)
   * هر مرحله از at شروع می‌شود و مجموعه‌ی marked را تعیین می‌کند.
   * ------------------------------------------------------------------ */
  var STEPS = {
    definition: [
      { at: 0, marked: [] },
      { at: 0.25, marked: [0] },
      { at: 0.5, marked: [0, 3] }
    ]
  };

  /** آخرین مرحله‌ای که at آن ≤ p است. */
  function pickLast(list, p) {
    var chosen = list[0];
    list.forEach(function (item) { if (p >= item.at) chosen = item; });
    return chosen;
  }

  /** کپشن فعال: آخرین کپشن با data-at ≤ p. */
  function activateCaptions(act, p) {
    var caps = act.querySelectorAll('.cap');
    var active = null;
    caps.forEach(function (c) {
      var at = parseFloat(c.getAttribute('data-at')) || 0;
      if (p >= at) active = c;
    });
    caps.forEach(function (c) { c.classList.toggle('is-active', c === active); });
  }

  /* ------------------------------------------------------------------
   * راه‌اندازی
   * ------------------------------------------------------------------ */
  var driven = []; // بخش‌هایی که با --sc-p پیش می‌روند

  /**
   * ریل پیشرفت لبه‌ی راست: نوار طلایی نسبت اسکرول به کل صفحه را نشان می‌دهد؛
   * هر بخش یک نقطه دارد. بخش فعال (وسط دید) برچسب و موج کوتاه می‌گیرد.
   * با کلیک روی نقطه، صفحه به ابتدای همان بخش می‌رود.
   */
  function bindRail() {
    var nav = document.getElementById('rail');
    if (!nav) return;
    var list = nav.querySelector('.rail__list');
    var fill = nav.querySelector('.rail__fill');
    var knob = nav.querySelector('.rail__knob');
    var secs = Array.prototype.slice.call(document.querySelectorAll('section[data-rail]'));
    var ticks = secs.map(function (sec, i) {
      var li = document.createElement('li');
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'rail__tick';
      btn.setAttribute('aria-label', 'بخش ' + toFa(i + 1) + ': ' + sec.getAttribute('data-rail'));
      var label = document.createElement('span');
      label.className = 'rail__label';
      label.textContent = sec.getAttribute('data-rail');
      var dot = document.createElement('span');
      dot.className = 'rail__dot';
      btn.appendChild(label);
      btn.appendChild(dot);
      li.appendChild(btn);
      list.appendChild(li);
      btn.addEventListener('click', function () {
        var top = sec.getBoundingClientRect().top + window.scrollY;
        var smooth = !(reduceMotion && reduceMotion.matches);
        window.scrollTo({ top: top, behavior: smooth ? 'smooth' : 'auto' });
      });
      return btn;
    });
    var queued = false;
    var active = -1;
    var items = ticks.map(function (b) { return b.parentNode; }); // li های نقطه‌ها
    /** هر نقطه دقیقاً به موقعیت شروع بخش روی مسیر اسکرول می‌رود، نه فاصله‌ی برابر. */
    function place(max) {
      secs.forEach(function (sec, i) {
        var top = sec.getBoundingClientRect().top + window.scrollY;
        var f = max > 0 ? Math.min(1, Math.max(0, top / max)) : 0;
        items[i].style.top = 'calc((100% - 24px) * ' + f.toFixed(5) + ')';
      });
    }
    function pulse() {
      knob.classList.remove('is-pulse');
      void knob.offsetWidth; // اجرای دوباره‌ی انیمیشن
      knob.classList.add('is-pulse');
    }
    function update() {
      queued = false;
      var max = document.documentElement.scrollHeight - window.innerHeight;
      var p = max > 0 ? Math.min(1, Math.max(0, window.scrollY / max)) : 0;
      place(max);
      fill.style.transform = 'scaleY(' + p.toFixed(4) + ')';
      // دایره از ۱۲px تا ۱۲px مانده به پایین حرکت می‌کند (هم‌تراز با نقاط)
      knob.style.top = 'calc(12px + (100% - 24px) * ' + p.toFixed(4) + ')';
      var mid = window.scrollY + window.innerHeight * 0.5;
      var idx = 0;
      secs.forEach(function (sec, i) {
        if (sec.getBoundingClientRect().top + window.scrollY <= mid) idx = i;
      });
      if (idx !== active) {
        var prev = active;
        active = idx;
        ticks.forEach(function (t, i) {
          t.classList.toggle('is-active', i === idx);
          t.classList.toggle('is-passed', i < idx);
        });
        if (prev >= 0) pulse();
      }
      nav.classList.toggle('is-on', window.scrollY > 4);
    }
    window.addEventListener('scroll', function () {
      if (!queued) { queued = true; window.requestAnimationFrame(update); }
    }, { passive: true });
    window.addEventListener('resize', update);
    window.addEventListener('load', update);
    update();
  }

  function init() {
    bindRail();
    bindCards();
    // بخش‌های پیش‌رونده
    document.querySelectorAll('[data-intro]').forEach(function (act) {
      var fig = act.querySelector('figure[data-graph]');
      if (!fig) return;
      var key = fig.getAttribute('data-graph');
      var built = buildGraph(key, fig);
      var counter = fig.querySelector('[data-count]');
      driven.push({
        act: act,
        name: act.getAttribute('data-intro'),
        built: built,
        counter: counter,
        lastP: -1
      });
    });

    // شکل‌های ثابت (هیرو و پانل‌های پن)
    document.querySelectorAll('figure[data-graph]').forEach(function (fig) {
      if (fig.closest('[data-intro]')) return;
      var key = fig.getAttribute('data-graph');
      var built = buildGraph(key, fig);
      var marked = parseList(fig.getAttribute('data-marked'));
      var missing = fig.hasAttribute('data-missing');
      built.update(marked, missing);
    });

    requestAnimationFrame(loop);
  }

  function parseList(s) {
    if (!s) return [];
    return s.split(',').map(function (x) { return parseInt(x, 10); }).filter(function (x) { return !isNaN(x); });
  }

  /** حلقه‌ی اصلی: فقط وقتی --sc-p عوض شده کار می‌کند. */
  function loop() {
    cardSets.forEach(function (c) {
      var p = parseFloat(c.act.style.getPropertyValue('--sc-p'));
      if (isNaN(p)) p = 0;
      if (Math.abs(p - c.lastP) < 0.0005) return;
      c.lastP = p;
      renderCards(c, p);
    });
    driven.forEach(function (d) {
      var p = parseFloat(d.act.style.getPropertyValue('--sc-p'));
      if (isNaN(p)) p = 0;
      if (Math.abs(p - d.lastP) < 0.0005) return;
      d.lastP = p;

      activateCaptions(d.act, p);

      if (d.name && STEPS[d.name]) {
        var step = pickLast(STEPS[d.name], p);
        var st = d.built.update(step.marked, false);
        if (d.counter) d.counter.textContent = toFa(st.count);
        d.act.classList.toggle('is-complete', st.count === d.built.n);
      }
    });
    requestAnimationFrame(loop);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
