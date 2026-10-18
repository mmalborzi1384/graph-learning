/**
 * script.js — منطق رابط کاربری «چالش γ» (نسخه ۶.۴.۰)
 *
 * بخش‌ها:
 *   ۱. وضعیت برنامه و ذخیره‌سازی (localStorage)
 *   ۲. ساخت گراف (کتابخانه یا سفارشی)
 *   ۳. بازگشت/تکرار مهره‌ها (Undo/Redo)
 *   ۴. رسم گراف با SVG و تعامل
 *   ۵. بررسی، امتیازدهی، راهنما، سابقه، کارنامه و خروجی CSV
 *   ۶. سازنده‌ی گراف سفارشی
 *   ۷. آزمایشگاه (ایستگاه‌های ۱ تا ۵)
 *   ۹. تمرین مینیمال، رسم بر اساس n و γ، رنگ‌بندی پوشش (نسخه ۶.۴.۰)
 *   ۸. تب‌ها، میان‌برها و راه‌اندازی
 *
 * وابستگی: graphs.js (window.GraphLib)
 */
(function () {
  'use strict';

  const L = window.GraphLib;
  const SVG_NS = 'http://www.w3.org/2000/svg';
  const STORAGE_KEY = 'chalesh-gamma-state-v1';
  const CUSTOM_ID = 'custom';
  const GEN_ID = 'gen';            // گراف ساخته‌شده با n و γ
  /** تعداد رنگ مهره. رنگ‌ها در style.css به صورت --bead-0 تا --bead-9 تعریف شده‌اند (هر دو حالت روشن و تاریک). */
  const BEADS = 10;
  const FA_DIGITS = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹'];
  const MAX_UNDO = 200;
  const $ = (id) => document.getElementById(id);
  /** متن ریاضی را در بلوک چپ‌به‌راست ایزوله می‌کند تا در متن فارسی به هم نریزد (textContent). */
  const M = (s) => '\u2066' + s + '\u2069';
  /** متن ریاضی برای innerHTML: یک span چپ‌به‌راست با فونت ریاضی. */
  const MH = (s) => '<span class="math" dir="ltr">' + s + '</span>';

  /* ==================================================================
   * ۱. وضعیت برنامه و ذخیره‌سازی
   * ================================================================== */

  const state = {
    graphId: 'C4',
    graph: null,
    marks: 0,            // ماسک بیتی مهره‌ها
    timed: null,         // چالش زمان‌دار فعال: { round, score, endsAt, log } یا null (ذخیره نمی‌شود)
    pending: 0,          // ماسک مهره‌هایی که برای حذف انتخاب شده‌اند ولی هنوز اعمال نشده‌اند (ذخیره نمی‌شود)
    tested: [],          // مهره‌هایی که در آزمون حذف برای این مجموعه امتحان شده‌اند
    testedKey: '',       // کلید مجموعه‌ای که آزمون‌های tested مربوط به آن است
    checked: null,       // نتیجه‌ی آخرین بررسی برای دور جاری
    teamMode: false,
    teams: [
      { name: 'گروه A', score: 0, rounds: 0 },
      { name: 'گروه B', score: 0, rounds: 0 },
    ],
    active: 0,           // اندیس گروه فعال
    history: [],         // سابقه‌ی دورهای ثبت‌شده
    scorecards: [{ id: 1, name: 'کارنامه ۱', records: {} }], // کارنامه‌ها: records = { graphId: {name, attempts, best} }
    activeCard: 0,       // اندیس کارنامه‌ی فعال
    custom: { n: 4, edges: [] }, // مشخصات گراف سفارشی
    undo: [],            // پشته‌ی بازگشت (ماسک‌های قبلی)
    redo: [],            // پشته‌ی تکرار
    hintLevel: 0,        // ۰ تا ۳ برای دور جاری
    hintVertex: null,    // رأس پیشنهادی در سطح ۲
    entering: false,     // true یعنی گراف تازه بارگذاری شده و رئوس باید با انیمیشن ظاهر شوند
    gen: null,           // گراف ساخته‌شده با n و γ: { n, k, edges }
    practice: false,     // حالت تمرین مینیمال (بدون امتیاز)
    stage1: null,        // ماسک مجموعه‌ای که مرحله‌ی ۱ (احاطه‌گری) برایش تأیید شده
  };

  /** ذخیره‌ی وضعیت پایدار در localStorage. */
  function saveState() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({
        graphId: state.graphId,
        marks: state.marks,
        checked: state.checked,
        teamMode: state.teamMode,
        teams: state.teams,
        active: state.active,
        history: state.history,
        scorecards: state.scorecards,
        activeCard: state.activeCard,
        custom: state.custom,
        gen: state.gen,
        practice: state.practice,
        stage1: state.stage1,
      }));
    } catch (e) {
      /* localStorage غیرفعال است؛ برنامه بدون ذخیره ادامه می‌دهد */
    }
  }

  /** بارگذاری وضعیت ذخیره‌شده؛ داده‌ی نامعتبر نادیده گرفته می‌شود. */
  function loadState() {
    let s;
    try {
      s = JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null');
    } catch (e) {
      s = null;
    }
    if (!s || typeof s !== 'object') return;

    if (s.custom && Number.isInteger(s.custom.n) && Array.isArray(s.custom.edges)) {
      state.custom = sanitizeCustom(s.custom.n, s.custom.edges);
    }
    if (s.gen && Number.isInteger(s.gen.n) && Number.isInteger(s.gen.k) && Array.isArray(s.gen.edges)) {
      const clean = sanitizeCustom(s.gen.n, s.gen.edges);
      state.gen = { n: clean.n, k: s.gen.k, edges: clean.edges };
    }
    if (typeof s.graphId === 'string') {
      if (s.graphId === CUSTOM_ID || isLibraryId(s.graphId)) state.graphId = s.graphId;
      if (s.graphId === GEN_ID && state.gen) state.graphId = GEN_ID;
    }
    if (typeof s.practice === 'boolean') state.practice = s.practice;
    if (Number.isInteger(s.stage1) && s.stage1 >= 0) state.stage1 = s.stage1;
    if (Number.isInteger(s.marks) && s.marks >= 0) state.marks = s.marks;
    if (s.checked && s.checked.evaluation && typeof s.checked.evaluation.points === 'number') {
      state.checked = s.checked;
    }
    if (typeof s.teamMode === 'boolean') state.teamMode = s.teamMode;
    if (Array.isArray(s.teams) && s.teams.length === 2) state.teams = s.teams;
    if (s.active === 0 || s.active === 1) state.active = s.active;
    if (Array.isArray(s.history)) state.history = s.history;
    if (Array.isArray(s.scorecards) && s.scorecards.length) {
      const cards = s.scorecards
        .filter((c) => c && typeof c.name === 'string' && c.records && typeof c.records === 'object')
        .map((c, i) => ({ id: Number.isInteger(c.id) ? c.id : i + 1, name: c.name.slice(0, 30), records: c.records }));
      if (cards.length) state.scorecards = cards;
      if (Number.isInteger(s.activeCard) && s.activeCard >= 0 && s.activeCard < state.scorecards.length) {
        state.activeCard = s.activeCard;
      }
    } else if (s.records && typeof s.records === 'object') {
      // مهاجرت از نسخه‌ی قبلی: کارنامه‌ی تکی به «کارنامه ۱» تبدیل می‌شود
      state.scorecards = [{ id: 1, name: 'کارنامه ۱', records: s.records }];
      state.activeCard = 0;
    }
  }

  /* ==================================================================
   * ۲. ساخت گراف
   * ================================================================== */

  function isLibraryId(id) {
    return L.listGraphs().some((x) => x.id === id);
  }

  /** اعتبارسنجی یال‌های گراف سفارشی: حذف یال‌های خارج از بازه و تکراری. */
  function sanitizeCustom(n, edges) {
    const N = Math.min(10, Math.max(2, n | 0));
    const seen = new Set();
    const clean = [];
    for (const e of edges) {
      if (!Array.isArray(e)) continue;
      let [a, b] = e.map(Number);
      if (!Number.isInteger(a) || !Number.isInteger(b)) continue;
      if (a === b || a < 0 || b < 0 || a >= N || b >= N) continue;
      if (a > b) [a, b] = [b, a];
      const key = a + ',' + b;
      if (!seen.has(key)) { seen.add(key); clean.push([a, b]); }
    }
    return { n: N, edges: clean };
  }

  /** ساخت شیء گراف جاری (کتابخانه یا سفارشی). */
  function buildGraph(id) {
    if (id === CUSTOM_ID) {
      return L.makeCustomGraph(state.custom.n, state.custom.edges, 'circle', undefined, 'گراف سفارشی');
    }
    if (id === GEN_ID && state.gen) {
      return L.makeCustomGraph(state.gen.n, state.gen.edges, 'circle', undefined, 'گراف ساخته‌شده');
    }
    return L.getGraph(id);
  }

  /** نام ساده‌ی گراف (بدون HTML). */
  function plainName(g) {
    return htmlToText(g.name);
  }

  /** نگاشت نویسه‌های زیرنویس یونیکد (برای متن ساده، مثل گزینه‌ی select). */
  const SUB_MAP = { '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄', '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉', 'n': 'ₙ', ',': ',' };

  /** HTML ساده‌ی نام گراف (<sub>) را به متن خوانا تبدیل می‌کند: C<sub>4</sub> → C₄. */
  function htmlToText(html) {
    return html
      .replace(/<sub>(.*?)<\/sub>/g, (_, t) => t.split('').map((ch) => SUB_MAP[ch] || ch).join(''))
      .replace(/<[^>]+>/g, '');
  }

  /* ==================================================================
   * ۳. بازگشت و تکرار
   * ================================================================== */

  /** تغییر ماسک مهره‌ها؛ در صورت لزوم در پشته‌ی بازگشت ثبت می‌شود. */
  function setMarks(newMarks, recordUndo) {
    if (recordUndo) {
      state.undo.push(state.marks);
      if (state.undo.length > MAX_UNDO) state.undo.shift();
      state.redo = [];
    }
    state.marks = newMarks;
    state.pending = 0;
    state.checked = null;
    state.stage1 = null; // هر تغییر مجموعه، هر دو مرحله‌ی تأیید را بی‌اعتبار می‌کند
    clearResult();
    renderBoard();
    updateButtons();
    saveState();
  }

  /** آیا آزمون حذف فعال است (مرحله‌ی ۱ برای همین مجموعه تأیید شده)؟ */
  function removalReady() {
    return state.stage1 !== null && state.stage1 === state.marks;
  }

  /** کلیک روی رأس: بعد از مرحله‌ی ۱، کلیک روی مهره فقط انتخاب برای حذف را تغییر می‌دهد. */
  function toggleVertex(v) {
    const bit = 1 << v;
    if (removalReady() && (state.marks & bit)) {
      state.pending ^= bit;
      renderBoard();
      updateButtons();
      return;
    }
    setMarks(state.marks ^ bit, true);
  }

  /** اعمال حذف‌های انتخاب‌شده روی مجموعه؛ سپس مرحله‌ی ۱ دوباره بررسی می‌شود. */
  function applyRemoval() {
    if (!state.pending) return;
    setMarks(state.marks & ~state.pending, true);
    checkStage1();
  }

  /** لغو همه‌ی حذف‌های انتخاب‌شده (مجموعه تغییری نمی‌کند). */
  /**
   * تمرین هدفمند: کوچک‌ترین گرافی (ترجیحاً از همان خانواده) را پیدا می‌کند که یک مجموعه‌ی
   * احاطه‌گر با رأس زائد دارد. این همان اشتباه دانش‌آموز است، روی گرافی کوچک‌تر.
   */
  function findTargetedCase(currentId) {
    const info = L.listGraphs();
    const cur = info.find((x) => x.id === currentId);
    let best = null;
    info.forEach((item) => {
      if (item.id === currentId) return;
      const g = L.getGraph(item.id);
      if (g.n < 3 || g.n > 6) return;
      const rank = (item.family === (cur && cur.family) ? 0 : 1) * 10 + g.n;
      if (best && rank >= best.rank) return;
      for (let S = 1; S < (1 << g.n); S++) {
        const a = L.analyzeSet(g, S);
        if (a.dominating && a.redundant.length > 0) {
          best = { id: item.id, S, redundant: a.redundant, rank };
          break;
        }
      }
    });
    return best;
  }

  /** نمایش یک پیام راهنما (بدون امتیاز) در کادر نتیجه. */
  function showNote(title, detail) {
    const box = $('result');
    box.className = 'result stage';
    box.innerHTML = '';
    const strong = document.createElement('strong');
    strong.textContent = title;
    const small = document.createElement('small');
    small.textContent = detail;
    box.appendChild(strong);
    box.appendChild(small);
  }

  /** بعد از نتیجه‌ی «احاطه‌گر ولی غیرمینیمال»، دکمه‌ی تمرین هدفمند نشان داده می‌شود. */
  function offerTargeted() {
    const c = findTargetedCase(state.graphId);
    if (!c) return;
    const btn = document.createElement('button');
    btn.id = 'btn-targeted';
    btn.className = 'btn small';
    btn.textContent = 'تمرین هدفمند: گراف کوچک‌تر با همین اشتباه';
    btn.addEventListener('click', () => startTargeted(c));
    $('result').appendChild(btn);
  }

  /** بارگذاری گراف تمرین هدفمند با مجموعه‌ی غیرمینیمال؛ دانش‌آموز باید رأس زائد را بردارد. */
  function startTargeted(c) {
    switchView('game');
    loadGraph(c.id);
    setMarks(c.S, false);
    const g = state.graph;
    showNote(
      'تمرین هدفمند: ' + plainName(g),
      'این مجموعه احاطه‌گر است، ولی رأس ' + listLabels(g, c.redundant) +
      ' زائد است. آن را بردارید، سپس مرحله‌ی ۱ و ۲ را بزنید.'
    );
  }

  function clearRemoval() {
    state.pending = 0;
    renderBoard();
    updateButtons();
  }

  function undo() {
    if (!state.undo.length) return;
    state.redo.push(state.marks);
    setMarks(state.undo.pop(), false);
  }

  function redo() {
    if (!state.redo.length) return;
    state.undo.push(state.marks);
    setMarks(state.redo.pop(), false);
  }

  /* ==================================================================
   * ۴. رسم گراف با SVG
   * ================================================================== */

  function svgEl(tag, attrs) {
    const e = document.createElementNS(SVG_NS, tag);
    for (const k in attrs) e.setAttribute(k, String(attrs[k]));
    return e;
  }

  /** برچسب نمایشی رأس با رقم فارسی (مرکز چرخ «c» است). */
  function labelOf(graph, v) {
    return toFa(L.vertexLabel(graph, v));
  }

  function listLabels(graph, vs) {
    return vs.map((v) => labelOf(graph, v)).join('، ');
  }

  function bitsOf(mask, n) {
    const out = [];
    for (let v = 0; v < n; v++) if (mask & (1 << v)) out.push(v);
    return out;
  }

  /** اندیس رنگ یک مهره (رأس u). رنگ هر رأس ثابت است و با تغییر حالت نمایش عوض نمی‌شود. */
  function colorIndex(u) {
    return u % BEADS;
  }

  /** مسیر یک بخش‌ـ دایره (برای پوشش مشترک): بخش i از m بخش مساوی. */
  function wedgePath(cx, cy, r, i, m) {
    const span = (2 * Math.PI) / m;
    const a0 = -Math.PI / 2 + i * span;
    const a1 = a0 + span;
    const x0 = cx + r * Math.cos(a0), y0 = cy + r * Math.sin(a0);
    const x1 = cx + r * Math.cos(a1), y1 = cy + r * Math.sin(a1);
    const large = span > Math.PI ? 1 : 0;
    return 'M ' + cx + ' ' + cy + ' L ' + x0.toFixed(2) + ' ' + y0.toFixed(2) +
      ' A ' + r + ' ' + r + ' 0 ' + large + ' 1 ' + x1.toFixed(2) + ' ' + y1.toFixed(2) + ' Z';
  }

  /**
   * رسم کامل صفحه‌ی گراف بر اساس state؛ فوکوس کیبورد حفظ می‌شود.
   * قاعده‌ی رنگ:
   *   - مهره: دایره‌ی یکدست با رنگ خودش (بدون رنگ دیگر).
   *   - پوشش‌داده‌شده با یک مهره: هاشور با رنگ آن مهره.
   *   - پوشش مشترک: دایره به بخش‌های مساوی، هر بخش با رنگ یکی از مهره‌های پوشاننده.
   */
  function renderBoard() {
    const g = state.graph;
    const board = $('board');
    // آزمون حذف: مهره‌ی برداشته‌شده فقط در نمایش کم می‌شود؛ مجموعه‌ی واقعی دست‌نخورده است
    const marks = state.marks & ~state.pending;
    const active = document.activeElement;
    const focusedV = active && active.classList && active.classList.contains('vertex')
      ? active.getAttribute('data-v') : null;
    board.innerHTML = '';

    const svg = svgEl('svg', {
      viewBox: '0 0 320 320',
      role: 'group',
      'aria-label': 'گراف ' + plainName(g),
    });

    // الگوهای هاشور: یک الگو برای هر رنگ مهره؛ رنگ خط هاشور از متغیر --hatch-i (در هر حالت نمایش)
    const defs = svgEl('defs', {});
    for (let i = 0; i < BEADS; i++) {
      const pattern = svgEl('pattern', {
        id: 'hatch-' + i, patternUnits: 'userSpaceOnUse', width: 7, height: 7, patternTransform: 'rotate(45)',
      });
      pattern.appendChild(svgEl('rect', { width: 7, height: 7, style: 'fill: var(--sheet)' }));
      pattern.appendChild(svgEl('line', { x1: 0, y1: 0, x2: 0, y2: 7, style: 'stroke: var(--hatch-' + i + ')', 'stroke-width': 2.2 }));
      defs.appendChild(pattern);
    }
    svg.appendChild(defs);

    const cov = L.coverage(g.closed, marks);
    const missing = state.checked ? state.checked.evaluation.missing : [];
    const hintMiss = state.hintLevel >= 1 ? L.uncoveredVertices(g.n, g.closed, marks) : [];
    const removalMiss = state.pending === 0 ? [] : L.uncoveredVertices(g.n, g.closed, marks);

    for (const [a, b] of g.edges) {
      svg.appendChild(svgEl('line', {
        class: 'edge',
        x1: g.points[a].x, y1: g.points[a].y,
        x2: g.points[b].x, y2: g.points[b].y,
      }));
    }

    for (let v = 0; v < g.n; v++) {
      const p = g.points[v];
      const isMarked = (marks & (1 << v)) !== 0;
      const isCovered = (cov & (1 << v)) !== 0;
      // مهره‌هایی که v را پوشش می‌دهند (N[v] ∩ S)، شامل خود v اگر مهره باشد
      const owners = bitsOf(marks & g.closed[v], g.n);

      let cls = 'uncovered';
      if (isMarked) cls = 'marked';
      else if (isCovered) cls = 'covered';
      if (owners.length >= 2 && !isMarked) cls += ' shared';
      if (missing.indexOf(v) !== -1) cls += ' missing';
      if (hintMiss.indexOf(v) !== -1) cls += ' hint-uncov';
      if (removalMiss.indexOf(v) !== -1) cls += ' removal-miss';
      if (state.pending & (1 << v)) cls += ' removal-target';
      if (state.hintVertex === v) cls += ' hint-target';

      const grp = svgEl('g', {
        style: '--i:' + v,
        class: 'vertex ' + cls,
        tabindex: 0,
        role: 'button',
        'data-v': v,
        'aria-label': 'رأس ' + labelOf(g, v) + (isMarked ? '، مهره دارد' : isCovered ? '، پوشش‌داده‌شده' : '، پوشش‌داده‌نشده'),
        'aria-pressed': isMarked ? 'true' : 'false',
      });

      const bg = svgEl('circle', { class: 'vertex-bg', cx: p.x, cy: p.y, r: 18 });
      if (isMarked) {
        bg.style.fill = 'var(--bead-' + colorIndex(v) + ')';
      } else if (owners.length === 1) {
        bg.style.fill = 'url(#hatch-' + colorIndex(owners[0]) + ')';
      } else {
        bg.style.fill = 'var(--sheet)';
      }
      grp.appendChild(bg);

      if (!isMarked && owners.length >= 2) {
        owners.forEach((u, i) => {
          grp.appendChild(svgEl('path', {
            class: 'vertex-part',
            d: wedgePath(p.x, p.y, 18, i, owners.length),
            style: 'fill: url(#hatch-' + colorIndex(u) + ')',
          }));
        });
        // حاشیه‌ی دایره روی بخش‌ها می‌ماند
        grp.appendChild(svgEl('circle', { class: 'vertex-ring', cx: p.x, cy: p.y, r: 18 }));
      }

      const txt = svgEl('text', { class: 'vertex-label' + (isMarked ? ' on-dark' : ''), x: p.x, y: p.y });
      txt.textContent = labelOf(g, v);
      grp.appendChild(txt);

      grp.addEventListener('click', () => toggleVertex(v));
      grp.addEventListener('keydown', (ev) => {
        if (ev.key === 'Enter' || ev.key === ' ') {
          ev.preventDefault();
          toggleVertex(v);
        }
      });
      svg.appendChild(grp);
    }

    board.appendChild(svg);
    if (state.entering) {
      svg.classList.add('entering');
      state.entering = false;
    }
    if (focusedV !== null) {
      const again = svg.querySelector('.vertex[data-v="' + focusedV + '"]');
      if (again) again.focus({ preventScroll: true });
    }

    const k = L.popcount(state.marks);
    const covered = L.popcount(cov);
    $('counts').textContent = 'مهره‌ها: ' + toFa(k) + '، پوشش‌داده‌شده: ' + toFa(covered) + ' از ' + toFa(g.n);

    if (!state.checked) {
      if (cov === L.fullMask(g.n) && k > 0) {
        setBadge('همه‌ی رأس‌ها پوشش داده شد', 'ok');
      } else {
        setBadge(k === 0 ? 'آماده' : 'در حال انتخاب', '');
      }
    }
    renderPractice();
    renderRemovalBox();
  }

  function setBadge(text, cls) {
    const b = $('status-badge');
    b.textContent = text;
    b.className = 'badge' + (cls ? ' ' + cls : '');
  }

  /** وضعیت دکمه‌ها (بازگشت، تکرار، راهنما، گراف بعدی). */
  function updateButtons() {
    $('btn-undo').disabled = state.undo.length === 0;
    $('btn-redo').disabled = state.redo.length === 0;
    $('hint-level').textContent = String(state.hintLevel);
    $('btn-hint').disabled = state.hintLevel >= 3;
    // در حالت تمرین امتیازی ثبت نمی‌شود، پس دکمه فقط گراف بعدی است
    // در حالت امتیازی و پس از بررسی، دکمه می‌گوید که امتیاز ثبت می‌شود
    $('btn-next').textContent = state.practice || !state.checked ? 'گراف بعدی' : 'ثبت و گراف بعدی';
    $('btn-next').title = state.practice || !state.checked ? '' : 'امتیاز این دور ثبت می‌شود';
    const pendingCount = L.popcount(state.pending);
    const stage1Ready = pendingCount === 0;
    $('btn-check').disabled = !stage1Ready;
    $('btn-check').title = stage1Ready ? '' : 'ابتدا حذف‌های انتخاب‌شده را اعمال یا لغو کنید';
    const stage2Ready = removalReady() && stage1Ready;
    $('btn-check2').disabled = !stage2Ready;
    $('btn-timed').textContent = state.timed ? 'پایان چالش' : 'چالش زمان‌دار';
    $('btn-timed').disabled = state.practice;
    $('btn-timed').title = state.practice ? 'در حالت فقط تمرین، چالش امتیازی نداریم' : '';
    $('btn-check2').title = stage2Ready ? '' : (pendingCount ? 'ابتدا حذف‌های انتخاب‌شده را اعمال یا لغو کنید' : 'ابتدا مرحله‌ی ۱ را تأیید کنید');
    $('removal-apply').hidden = pendingCount === 0;
    $('removal-clear').hidden = pendingCount === 0;
  }

  /* ==================================================================
   * ۵. بررسی، امتیازدهی، راهنما، سابقه، کارنامه، CSV
   * ================================================================== */

  const MESSAGES = {
    exact: { text: 'عدد احاطه‌گری دقیق! ۱۵ امتیاز', cls: 'exact', badge: ['ok', 'مینیمم: ۱۵ امتیاز'] },
    minimal: { text: 'مینیمال، ولی مینیمم نیست. ۱۰ امتیاز', cls: 'nonmin', badge: ['warn', 'مینیمال: ۱۰ امتیاز'] },
    validNonMinimal: { text: 'احاطه‌گر است، ولی مینیمال نیست. ۵ امتیاز', cls: 'nonmin', badge: ['warn', 'احاطه‌گر: ۵ امتیاز'] },
    notDominating: { text: 'مجموعه احاطه‌گر نیست. ۰ امتیاز', cls: 'bad', badge: ['bad', 'احاطه‌گر نیست'] },
    stage1: { text: 'مرحله‌ی ۱ تأیید شد: مجموعه احاطه‌گر است.', cls: 'stage', badge: ['ok', 'مرحله‌ی ۱ تأیید شد'] },
  };

  /** پیام‌های حالت تمرین: همان وضعیت‌ها بدون عدد امتیاز (امتیازی ثبت نمی‌شود). */
  const PRACTICE_MESSAGES = {
    exact: { text: 'عدد احاطه‌گری دقیق است.', cls: 'exact', badge: ['ok', 'مینیمم'] },
    minimal: { text: 'مینیمال، ولی مینیمم نیست.', cls: 'nonmin', badge: ['warn', 'مینیمال'] },
    validNonMinimal: { text: 'احاطه‌گر است، ولی مینیمال نیست.', cls: 'nonmin', badge: ['warn', 'احاطه‌گر'] },
    notDominating: { text: 'مجموعه احاطه‌گر نیست.', cls: 'bad', badge: ['bad', 'احاطه‌گر نیست'] },
    stage1: MESSAGES.stage1,
  };

  function clearResult() {
    const box = $('result');
    box.className = 'result';
    box.innerHTML = '';
    hideHint();
  }

  function showResult(status, detail) {
    const m = (state.practice ? PRACTICE_MESSAGES : MESSAGES)[status];
    const box = $('result');
    box.className = 'result ' + m.cls;
    box.innerHTML = '';
    const strong = document.createElement('strong');
    strong.textContent = m.text;
    const small = document.createElement('small');
    small.textContent = detail;
    box.appendChild(strong);
    box.appendChild(small);
    setBadge(m.badge[1], m.badge[0]);
  }

  /** مرحله‌ی ۱: آیا مجموعه‌ی فعلی احاطه‌گر است؟ */
  function checkStage1() {
    if (state.pending) { showResult('notDominating', 'ابتدا حذف‌های انتخاب‌شده را اعمال یا لغو کنید.'); return; }
    // اگر مرحله‌ی ۲ قبلاً برای همین مجموعه انجام شده، نتیجه‌ی آن حفظ می‌شود
    // (بازبینی مرحله‌ی ۱ امتیاز ۱۵ را به ۵ کاهش نمی‌دهد).
    if (state.checked && state.checked.stage === 2 && state.checked.marks === state.marks && state.stage1 === state.marks) {
      checkStage2();
      return;
    }
    const g = state.graph;
    const evaluation = L.evaluateMarks(g, state.marks);
    state.checked = { evaluation, stage: 1, marks: state.marks };
    if (!evaluation.dominating) {
      state.stage1 = null;
      showResult('notDominating', 'رأس‌های پوشش‌داده‌نشده: ' + listLabels(g, evaluation.missing) + '.');
    } else {
      state.stage1 = state.marks;
      showResult('stage1', state.practice
        ? 'حالا مرحله‌ی ۲ را بزنید تا مینیمال و مینیمم بودن بررسی شود.'
        : 'حالا مرحله‌ی ۲ را بزنید تا مینیمال و مینیمم بودن بررسی شود. (بدون مرحله‌ی ۲ بیش از ۵ امتیاز نمی‌گیرید.)');
    }
    updateButtons();
    renderBoard();
    saveState();
  }

  /** مرحله‌ی ۲: آیا مجموعه‌ی احاطه‌گر مینیمال است؟ مینیمم است؟ */
  function checkStage2() {
    if (state.pending) { showResult('notDominating', 'ابتدا حذف‌های انتخاب‌شده را اعمال یا لغو کنید.'); return; }
    if (state.stage1 === null || state.stage1 !== state.marks) {
      showResult('notDominating', 'ابتدا مرحله‌ی ۱ را تأیید کنید.');
      return;
    }
    const g = state.graph;
    const evaluation = L.evaluateMarks(g, state.marks);
    state.checked = { evaluation, stage: 2, marks: state.marks };
    let detail;
    if (evaluation.status === 'exact') {
      detail = 'تعداد مهره‌ها ' + toFa(evaluation.k) + ' ' + M('= γ(G)') + ' است.';
    } else if (evaluation.status === 'minimal') {
      detail = 'حذف هر مهره احاطه‌گری را خراب می‌کند، ولی ' + M('|D| = ' + toFa(evaluation.k)) + ' از ' + M('γ(G) = ' + toFa(g.gamma)) + ' بزرگ‌تر است.';
    } else {
      detail = 'این مهره‌ها زائدند: ' + listLabels(g, evaluation.redundant) +
        '. یکی از آن‌ها را بردارید و دوباره مرحله‌ی ۱ و ۲ را بزنید.';
    }
    showResult(evaluation.status, detail + (state.practice ? ' (تمرین: امتیازی ثبت نمی‌شود.)' : ''));
    if (evaluation.status === 'validNonMinimal') offerTargeted();
    updateButtons();
    renderBoard();
    saveState();
  }

  /**
   * امتیاز دور جاری بر اساس دو مرحله:
   *   - مرحله‌ی ۱ برای همین مجموعه تأیید نشده: ۰
   *   - فقط مرحله‌ی ۱: ۵ (احاطه‌گر، بدون بررسی مینیمال)
   *   - مرحله‌ی ۲ هم تأیید شده: ۰ / ۵ / ۱۰ / ۱۵ طبق وضعیت مجموعه
   */
  function roundPoints() {
    if (state.stage1 === null || state.stage1 !== state.marks) return 0;
    if (state.checked && state.checked.stage === 2 && state.checked.marks === state.marks) {
      return state.checked.evaluation.points;
    }
    return 5;
  }

  /** وضعیت سابقه‌ی یک دور بر اساس امتیاز آن. */
  function roundStatus() {
    if (!state.checked) return 'skipped';
    if (state.stage1 === null || state.stage1 !== state.marks) return 'notDominating';
    if (state.checked && state.checked.stage === 2 && state.checked.marks === state.marks) {
      return state.checked.evaluation.status;
    }
    return 'stage1only';
  }

  /* ---------- راهنمای سه‌سطحه ---------- */

  function showHint(text) {
    const box = $('hint-box');
    box.textContent = text;
    box.hidden = false;
  }

  function hideHint() {
    $('hint-box').hidden = true;
    state.hintVertex = null;
  }

  /**
   * سطح ۱: رأس‌های پوشش‌نداده را نشان می‌دهد.
   * سطح ۲: یک رأس از یک مجموعه‌ی مینیمم را پیشنهاد می‌کند.
   * سطح ۳: γ(G) و یک مجموعه‌ی احاطه‌گر مینیمم را آشکار می‌کند.
   */
  function useHint() {
    if (state.hintLevel >= 3) return;
    const g = state.graph;
    state.hintLevel += 1;
    state.hintVertex = null;

    if (state.hintLevel === 1) {
      const miss = L.uncoveredVertices(g.n, g.closed, state.marks);
      showHint(miss.length
        ? 'سطح ۱: رأس‌های پوشش‌داده‌نشده ' + listLabels(g, miss) + ' هستند (با خط‌چین نشان داده شده‌اند).'
        : 'سطح ۱: همه‌ی رأس‌ها پوشش داده شده‌اند. حالا به کمینه بودن تعداد مهره‌ها فکر کنید.');
    } else if (state.hintLevel === 2) {
      const set = g.minSets[0];
      const members = bitsOf(set, g.n);
      const candidate = members.find((v) => !(state.marks & (1 << v))) ?? members[0];
      state.hintVertex = candidate;
      showHint('سطح ۲: رأس ' + labelOf(g, candidate) + ' عضو یک مجموعه‌ی احاطه‌گر مینیمم است (با حاشیه‌ی آبی مشخص شده).');
    } else {
      const members = bitsOf(g.minSets[0], g.n);
      showHint('سطح ۳: ' + M('γ(G) = ' + toFa(g.gamma)) + ' و یک مجموعه‌ی مینیمم: ' + M('{' + listLabels(g, members) + '}') + '.');
    }
    updateButtons();
    renderBoard();
    saveState();
  }

  /* ---------- سابقه، امتیاز، کارنامه ---------- */

  /** ثبت دور جاری در سابقه، امتیاز گروه فعال و کارنامه‌ی گراف. */
  function commitRound() {
    const g = state.graph;
    const team = state.teams[state.active];
    const checked = state.checked !== null;
    if (state.practice) {
      // تمرین مینیمال: امتیازی ثبت نمی‌شود و کارنامه تغییر نمی‌کند
      state.history.push({
        team: state.teamMode ? team.name : 'بازیکن',
        graph: plainName(g),
        k: L.popcount(state.marks),
        gamma: g.gamma,
        status: 'practice',
        points: 0,
        hints: state.hintLevel,
      });
      if (state.history.length > 200) state.history.shift();
      return;
    }
    const points = roundPoints();
    team.score += points;
    team.rounds += 1;

    state.history.push({
      team: state.teamMode ? team.name : 'بازیکن',
      graph: plainName(g),
      k: L.popcount(state.marks),
      gamma: g.gamma,
      status: roundStatus(),
      points,
      hints: state.hintLevel,
    });
    if (state.history.length > 200) state.history.shift();

    if (points > 0 || checked) {
      const card = activeCard();
      const rec = card.records[state.graphId] || { name: plainName(g), attempts: 0, best: null };
      rec.name = plainName(g);
      rec.attempts += 1;
      rec.best = rec.best === null ? points : Math.max(rec.best, points);
      card.records[state.graphId] = rec;
    }
  }

  /** پایان دور جاری و شروع دور بعد (گراف جدید یا همان گراف). */
  function nextRound() {
    if (state.timed) { timedAdvance(); return; }
    state.pending = 0;
    if (state.graph) commitRound();
    // در تمرین مینیمال نوبت عوض نمی‌شود (تمرین تک‌نفره است)
    if (state.teamMode && !state.practice) state.active = 1 - state.active;
    loadGraph(randomGraph());
  }


  /* ---------- چالش زمان‌دار ----------
   * ۵ گراف تصادفی در ۳ دقیقه. امتیاز هر گراف = امتیاز همان دور (۰/۵/۱۰/۱۵) + پاداش سرعت
   * (هر ۱۰ ثانیه‌ی باقی‌مانده یک امتیاز، فقط وقتی دور امتیاز دارد). کارنامه و گروه‌ها تغییر نمی‌کنند. */
  const TIMED_ROUNDS = 5;
  const TIMED_SECONDS = 180;
  let timedTimer = null;

  function startTimed() {
    if (state.practice) return;
    state.timed = { round: 0, score: 0, endsAt: Date.now() + TIMED_SECONDS * 1000, log: [] };
    state.pending = 0;
    switchView('game');
    setTimedLock(true);
    timedTimer = setInterval(timedTick, 250);
    timedNewGraph();
  }

  function timedNewGraph() {
    state.timed.round += 1;
    loadGraph(randomGraph());
    timedTick();
    updateButtons();
  }

  /** دور جاری را ثبت می‌کند و گراف بعدی یا پایان چالش را انجام می‌دهد. */
  function timedAdvance() {
    const t = state.timed;
    if (!t) return;
    const left = Math.max(0, t.endsAt - Date.now());
    const base = state.graph && state.stage1 === state.marks ? roundPoints() : 0;
    const bonus = base > 0 ? Math.floor(left / 10000) : 0;
    t.score += base + bonus;
    t.log.push({ graph: plainName(state.graph), points: base, bonus });
    if (t.round >= TIMED_ROUNDS || left <= 0) finishTimed(false);
    else timedNewGraph();
  }

  function timedTick() {
    const t = state.timed;
    const box = $('timed-box');
    if (!t) { box.hidden = true; return; }
    const left = Math.max(0, t.endsAt - Date.now());
    // وقتی زمان تمام شد، دور جاری هم با وضعیت فعلی ثبت و چالش پایان می‌یابد
    if (left <= 0 && t.round > 0) { timedAdvance(); return; }
    const sec = Math.ceil(left / 1000);
    const mm = Math.floor(sec / 60), ss = sec % 60;
    box.hidden = false;
    box.textContent = 'چالش زمان‌دار: گراف ' + toFa(t.round) + ' از ' + toFa(TIMED_ROUNDS) +
      '، زمان باقی‌مانده ' + toFa(mm) + ':' + toFa(String(ss).padStart(2, '0')) +
      '، امتیاز ' + toFa(t.score);
  }

  /** پایان چالش: aborted = true یعنی کاربر زودتر تمام کرده است. */
  function finishTimed(aborted) {
    const t = state.timed;
    if (!t) return;
    clearInterval(timedTimer);
    timedTimer = null;
    state.timed = null;
    setTimedLock(false);
    const box = $('timed-box');
    box.hidden = false;
    box.textContent = (aborted ? 'چالش متوقف شد.' : 'چالش تمام شد.') + ' امتیاز کل: ' + toFa(t.score) +
      ' از ' + toFa(TIMED_ROUNDS * 25) + ' (' + toFa(t.log.length) + ' گراف بررسی شد).';
    showNote('نتیجه‌ی چالش زمان‌دار', 'امتیاز کل ' + toFa(t.score) + '. این امتیاز در کارنامه ثبت نمی‌شود.');
    updateButtons();
  }

  /** در حین چالش، تغییر گراف و تنظیمات قفل می‌شود تا شمارش دورها درست بماند. */
  function setTimedLock(on) {
    ['graph-select', 'btn-random', 'btn-restart', 'btn-generate', 'practice-mode', 'team-mode'].forEach((id) => {
      const el = $(id);
      if (el) el.disabled = on;
    });
  }

  function randomGraph() {
    const all = L.listGraphs().map((x) => x.id);
    const others = all.filter((x) => x !== state.graphId);
    const pool = others.length ? others : all;
    return pool[Math.floor(Math.random() * pool.length)];
  }

  /**
   * بارگذاری گراف و آماده‌سازی دور.
   * @param {string} id شناسه‌ی گراف یا 'custom'
   * @param {boolean} keepMarks حفظ مهره‌ها (برای بارگذاری از localStorage)
   */
  function loadGraph(id, keepMarks) {
    if (id === GEN_ID && !state.gen) id = 'C4'; // گراف ساخته‌شده‌ای نیست
    state.graphId = id;
    state.graph = buildGraph(id);
    if (!keepMarks) state.marks = 0;
    state.marks &= L.fullMask(state.graph.n);
    const restored = keepMarks && state.checked && state.checked.evaluation;
    state.checked = restored ? state.checked : null;
    if (restored && state.checked.evaluation.k !== L.popcount(state.marks)) state.checked = null;
    if (!keepMarks) state.stage1 = null;
    if (keepMarks && state.stage1 !== null && state.stage1 !== state.marks) state.stage1 = null;
    state.undo = [];
    state.redo = [];
    state.hintLevel = 0;
    state.hintVertex = null;
    state.entering = true;

    refreshGraphSelect();
    clearResult();
    if (state.checked) {
      const ev = state.checked.evaluation;
      const detail = ev.status === 'notDominating'
        ? 'رأس‌های پوشش‌داده‌نشده: ' + listLabels(state.graph, ev.missing) + '.'
        : 'تعداد مهره‌ها: ' + toFa(ev.k) + '.';
      showResult(ev.status, detail);
    }
    $('gamma-box').hidden = true;
    updateMeta();
    renderBoard();
    renderScores();
    renderRecords();
    updateButtons();
    saveState();
  }

  /** همگام‌سازی منوی گراف با گراف جاری (شامل گزینه‌ی سفارشی). */
  function refreshGraphSelect() {
    const sel = $('graph-select');
    [[CUSTOM_ID, 'سفارشی: گراف ساخته‌شده'], [GEN_ID, 'ساخته‌شده با n و γ']].forEach(([id, label]) => {
      let opt = sel.querySelector('option[value="' + id + '"]');
      if (state.graphId === id && !opt) {
        opt = document.createElement('option');
        opt.value = id;
        opt.textContent = label;
        sel.appendChild(opt);
      }
    });
    sel.value = state.graphId;
  }

  function updateMeta() {
    const g = state.graph;
    $('graph-meta').textContent =
      M(plainName(g)) + '، خانواده‌ی ' + g.family + '. ' + M('n = ' + toFa(g.n)) +
      '، ' + M('|E| = ' + toFa(g.edges.length)) + '، ' + M('Δ = ' + toFa(g.delta)) + '.';
  }

  function renderScores() {
    const body = $('score-body');
    body.innerHTML = '';
    const rows = state.teamMode
      ? state.teams
      : [{ name: 'بازیکن', score: state.teams[0].score + state.teams[1].score, rounds: state.history.length }];
    rows.forEach((t, i) => {
      const tr = document.createElement('tr');
      if (state.teamMode && i === state.active) tr.className = 'active';
      [t.name, t.score, t.rounds].forEach((val) => {
        const td = document.createElement('td');
        td.textContent = typeof val === 'number' ? toFa(val) : String(val);
        tr.appendChild(td);
      });
      body.appendChild(tr);
    });
    $('turn-text').textContent = state.teamMode
      ? 'نوبت فعلی: ' + state.teams[state.active].name
      : 'حالت یک‌نفره. برای بازی گروهی، گزینه‌ی «بازی دو گروهی» را فعال کنید.';
    $('live-score').textContent = state.teamMode
      ? 'نوبت: ' + state.teams[state.active].name + '، ' + state.teams.map((t) => t.name + ': ' + toFa(t.score)).join('، ')
      : 'امتیاز: ' + toFa(state.teams[0].score + state.teams[1].score);

    const hist = $('history');
    hist.innerHTML = '';
    state.history.slice(-20).reverse().forEach((h) => {
      const li = document.createElement('li');
      const label = { exact: 'مینیمم', minimal: 'مینیمال، غیرمینیمم', validNonMinimal: 'احاطه‌گر، غیرمینیمال', stage1only: 'فقط مرحله‌ی ۱', notDominating: 'نامعتبر', skipped: 'رد شد', practice: 'تمرین' }[h.status] || h.status;
      li.textContent = h.team + '، ' + M(h.graph) + '، ' + M('|D| = ' + toFa(h.k)) +
        '، ' + M('γ = ' + (h.gamma === null ? '—' : toFa(h.gamma))) + '، ' + label +
        '، ' + toFa(h.points) + ' امتیاز' + (h.hints ? '، راهنما: ' + toFa(h.hints) : '');
      hist.appendChild(li);
    });
  }

  /* ---------- گزارش چاپی برای معلم ----------
   * همان داده‌ی صفحه‌ی کارنامه، در قالب ساده برای چاپ یا ذخیره به‌صورت PDF. */
  const STATUS_FA = {
    exact: 'مینیمم', minimal: 'مینیمال، غیرمینیمم', validNonMinimal: 'احاطه‌گر، غیرمینیمال',
    stage1only: 'فقط مرحله‌ی ۱', notDominating: 'نامعتبر', skipped: 'رد شد', practice: 'تمرین',
  };

  function addReportTable(root, title, heads, rows) {
    const h = document.createElement('h2');
    h.textContent = title;
    root.appendChild(h);
    const table = document.createElement('table');
    const thead = document.createElement('thead');
    const hr = document.createElement('tr');
    heads.forEach((x) => { const th = document.createElement('th'); th.textContent = x; hr.appendChild(th); });
    thead.appendChild(hr);
    table.appendChild(thead);
    const tbody = document.createElement('tbody');
    if (!rows.length) {
      const tr = document.createElement('tr');
      const td = document.createElement('td');
      td.colSpan = heads.length;
      td.textContent = 'هنوز داده‌ای ثبت نشده است.';
      tr.appendChild(td);
      tbody.appendChild(tr);
    }
    rows.forEach((row) => {
      const tr = document.createElement('tr');
      row.forEach((cell) => { const td = document.createElement('td'); td.textContent = cell; tr.appendChild(td); });
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    root.appendChild(table);
  }

  function buildPrintReport() {
    const root = $('print-report');
    root.innerHTML = '';
    const h1 = document.createElement('h1');
    h1.textContent = 'گزارش بازی «چالش γ»';
    root.appendChild(h1);
    const meta = document.createElement('p');
    meta.textContent = 'تاریخ گزارش: ' + new Date().toLocaleDateString('fa-IR');
    root.appendChild(meta);

    addReportTable(root, 'گروه‌ها و امتیاز کل', ['گروه', 'امتیاز', 'تعداد دور'],
      state.teams.map((t) => [t.name, toFa(t.score), toFa(t.rounds)]));

    const card = activeCard();
    const recs = Object.values(card.records).sort((a, b) => a.name.localeCompare(b.name, 'fa'));
    addReportTable(root, 'کارنامه: ' + card.name, ['گراف', 'تعداد تلاش', 'بهترین امتیاز'],
      recs.map((r) => [r.name, toFa(r.attempts), r.best === null ? '—' : toFa(r.best)]));

    addReportTable(root, 'سابقه‌ی ۲۰ دور اخیر', ['گروه', 'گراف', 'وضعیت', 'امتیاز'],
      state.history.slice(-20).reverse().map((x) => [x.team, x.graph, STATUS_FA[x.status] || x.status, toFa(x.points)]));
  }

  /** گزارش را می‌سازد و پنجره‌ی چاپ را باز می‌کند؛ فقط بخش گزارش چاپ می‌شود. */
  function printReport() {
    buildPrintReport();
    document.body.classList.add('printing-report');
    const done = () => {
      document.body.classList.remove('printing-report');
      window.removeEventListener('afterprint', done);
    };
    window.addEventListener('afterprint', done);
    window.print();
  }

  function activeCard() {
    return state.scorecards[state.activeCard] || state.scorecards[0];
  }

  /** فهرست کارنامه‌ها در منو و جدول کارنامه‌ی فعال. */
  function renderRecords() {
    const sel = $('card-select');
    sel.innerHTML = '';
    state.scorecards.forEach((c, i) => {
      const o = document.createElement('option');
      o.value = String(i);
      o.textContent = c.name;
      if (i === state.activeCard) o.selected = true;
      sel.appendChild(o);
    });

    const card = activeCard();
    const body = $('records-body');
    body.innerHTML = '';
    const rows = L.listGraphs().map((x) => ({ id: x.id, name: htmlToText(x.name) }));
    if (card.records[CUSTOM_ID]) rows.push({ id: CUSTOM_ID, name: 'سفارشی' });
    if (card.records[GEN_ID]) rows.push({ id: GEN_ID, name: 'ساخته‌شده با n و γ' });
    rows.forEach((r) => {
      const rec = card.records[r.id];
      const tr = document.createElement('tr');
      const cells = [r.name, rec ? rec.attempts : 0, rec && rec.best !== null ? rec.best : '—'];
      cells.forEach((c) => {
        const td = document.createElement('td');
        td.textContent = typeof c === 'number' ? toFa(c) : String(c);
        tr.appendChild(td);
      });
      body.appendChild(tr);
    });
  }

  /** خروجی CSV سابقه‌ی دورها (با BOM برای باز شدن درست در Excel). */
  function exportCsv() {
    const header = ['گروه', 'گراف', '|D|', 'γ', 'وضعیت', 'امتیاز', 'تعداد راهنما'];
    const statusFa = { exact: 'مینیمم', minimal: 'مینیمال، غیرمینیمم', validNonMinimal: 'احاطه‌گر، غیرمینیمال', stage1only: 'فقط مرحله‌ی ۱', notDominating: 'احاطه‌گر نیست', skipped: 'رد شد', practice: 'تمرین مینیمال' };
    const esc = (v) => '"' + String(v === null || v === undefined ? '' : v).replace(/"/g, '""') + '"';
    const lines = [header.map(esc).join(',')];
    state.history.forEach((h) => {
      lines.push([h.team, h.graph, h.k, h.gamma, statusFa[h.status] || h.status, h.points, h.hints || 0].map(esc).join(','));
    });
    const blob = new Blob(['\uFEFF' + lines.join('\r\n')], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'chalesh-gamma-history.csv';
    document.body.appendChild(a);
    a.click();
    setTimeout(() => { URL.revokeObjectURL(url); a.remove(); }, 0);
  }

  /** افزودن کارنامه‌ی جدید و انتخاب آن به‌عنوان کارنامه‌ی فعال. */
  function addCard() {
    const input = $('card-name');
    let name = input.value.trim();
    if (!name) {
      // نام پیش‌فرض یکتا: «کارنامه ۲»، «کارنامه ۳» و ... تا نام آزاد پیدا شود
      let k = state.scorecards.length + 1;
      while (state.scorecards.some((c) => c.name === 'کارنامه ' + toFa(k))) k++;
      name = 'کارنامه ' + toFa(k);
    }
    if (state.scorecards.some((c) => c.name === name)) {
      showCardMsg('نامی با این عنوان وجود دارد؛ نام دیگری انتخاب کنید.');
      return;
    }
    const nextId = state.scorecards.reduce((m, c) => Math.max(m, c.id), 0) + 1;
    state.scorecards.push({ id: nextId, name: name.slice(0, 30), records: {} });
    state.activeCard = state.scorecards.length - 1;
    input.value = '';
    showCardMsg('کارنامه‌ی «' + name + '» ایجاد و فعال شد.');
    renderRecords();
    saveState();
  }

  /** صفر کردن کارنامه‌ی فعال (سابقه‌ی دورها و امتیاز جاری دست‌نخورده می‌ماند). */
  function resetCard() {
    const card = activeCard();
    if (!window.confirm('کارنامه‌ی «' + card.name + '» صفر شود؟ این عمل قابل بازگشت نیست.')) return;
    card.records = {};
    showCardMsg('کارنامه‌ی «' + card.name + '» صفر شد.');
    renderRecords();
    saveState();
  }

  function showCardMsg(text) {
    const box = $('card-msg');
    if (box) box.textContent = text;
  }

  function restartGame() {
    if (!window.confirm('امتیازها و سابقه‌ی بازی پاک شود؟ (کارنامه حفظ می‌شود)')) return;
    state.teams.forEach((t) => { t.score = 0; t.rounds = 0; });
    state.history = [];
    state.active = 0;
    loadGraph(state.graphId);
  }

  function showGamma() {
    const g = state.graph;
    const t = $('gamma-text');
    t.innerHTML = '';
    const strong = document.createElement('strong');
    strong.textContent = M('γ(' + plainName(g) + ') = ' + toFa(g.gamma));
    t.appendChild(strong);
    $('gamma-set').textContent = 'همه‌ی مجموعه‌های احاطه‌گر مینیمم (' + toFa(g.minSets.length) + ' مجموعه):';
    const chips = $('gamma-sets');
    chips.innerHTML = '';
    g.minSets.forEach((set) => {
      const span = document.createElement('span');
      span.className = 'set-chip';
      span.textContent = M('{' + listLabels(g, bitsOf(set, g.n)) + '}');
      chips.appendChild(span);
    });
    $('gamma-box').hidden = false;
  }

  /* ---------- آزمون حذف: چرا مجموعه مینیمال است یا نه ---------- */
  /**
   * بعد از تأیید مرحله‌ی ۱، دانش‌آموز هر مهره‌ی D را موقتاً حذف می‌کند و می‌بیند کدام رأس‌ها
   * بی‌پوشش می‌شوند. اگر حذف هیچ مهره‌ای احاطه‌گری را خراب نکند، آن مهره زائد است و مجموعه مینیمال نیست.
   * این آزمون امتیاز را تغییر نمی‌دهد؛ فقط آموزشی است.
   */
  function renderRemovalBox() {
    const box = $('removal-box');
    const g = state.graph;
    const ready = !!g && removalReady();
    box.hidden = !ready;
    if (!ready) return;

    const key = state.graphId + ':' + state.marks;
    if (state.testedKey !== key) {
      state.testedKey = key;
      state.tested = [];
    }

    const members = bitsOf(state.marks, g.n);
    const list = $('removal-list');
    list.innerHTML = '';
    members.forEach((v) => {
      const li = document.createElement('li');
      const btn = document.createElement('button');
      const on = (state.pending & (1 << v)) !== 0;
      btn.className = 'btn small' + (on ? ' primary' : '');
      btn.textContent = on ? 'لغو انتخاب ' + labelOf(g, v) : 'انتخاب برای حذف ' + labelOf(g, v);
      btn.setAttribute('aria-pressed', on ? 'true' : 'false');
      btn.addEventListener('click', () => {
        state.pending ^= (1 << v);
        if (state.tested.indexOf(v) === -1) state.tested.push(v);
        renderBoard();
        updateButtons();
      });
      const info = document.createElement('span');
      info.className = 'removal-info';
      if (state.tested.indexOf(v) !== -1) {
        const miss = L.uncoveredVertices(g.n, g.closed, state.marks & ~(1 << v));
        info.textContent = miss.length
          ? 'بی‌پوشش می‌شوند: ' + listLabels(g, miss) + ' (ضروری)'
          : 'هیچ رأسی بی‌پوشش نمی‌شود (زائد)';
      }
      li.appendChild(btn);
      li.appendChild(info);
      list.appendChild(li);
    });

    const summary = $('removal-summary');
    const pendingList = members.filter((v) => (state.pending & (1 << v)) !== 0);
    if (pendingList.length) {
      summary.textContent = 'برای حذف انتخاب شده: ' + listLabels(g, pendingList) +
        '. با «اعمال حذف» مجموعه به‌روز می‌شود؛ سپس مرحله‌ی ۱ و ۲ را بزنید.';
      return;
    }
    if (state.tested.length < members.length) {
      summary.textContent = 'آزمون را برای همه‌ی مهره‌ها انجام دهید (' + toFa(state.tested.length) + ' از ' + toFa(members.length) + ').';
      return;
    }
    const redundant = members.filter((v) => L.uncoveredVertices(g.n, g.closed, state.marks & ~(1 << v)).length === 0);
    summary.textContent = redundant.length
      ? 'نتیجه: ' + listLabels(g, redundant) + ' زائد است؛ پس مجموعه مینیمال نیست. آن مهره‌ها را انتخاب و اعمال کنید.'
      : 'نتیجه: حذف هر مهره احاطه‌گری را خراب می‌کند؛ پس مجموعه مینیمال است.';
  }

  /* ---------- تمرین مینیمال ---------- */

  /** نمایش نتیجه‌ی تحلیل مجموعه‌ی فعلی: احاطه‌گر؟ مینیمال؟ مینیمم؟ و چالش گراف. */
  function renderPractice() {
    const box = $('practice-box');
    if (!box) return;
    box.hidden = !state.practice;
    if (!state.practice || !state.graph) return;
    const g = state.graph;
    const a = L.analyzeSet(g, state.marks);
    const yn = (b) => (b ? 'بله' : 'خیر');
    const lines = [];
    lines.push('احاطه‌گر: ' + yn(a.dominating) + '.');
    if (a.dominating) {
      lines.push('مینیمال (حذف هر مهره احاطه‌گری را خراب کند): ' + yn(a.minimal) + '.');
      if (!a.minimal) lines.push('مهره‌های زائد: ' + listLabels(g, a.redundant) + '. حذف هر کدام احاطه‌گری را نگه می‌دارد.');
      lines.push('مینیمم (' + M('|D| = γ') + '): ' + yn(a.minimum) + '.');
    } else {
      lines.push('مینیمال و مینیمم: پیش از احاطه‌گر بودن بررسی نمی‌شوند.');
    }
    const hasTarget = g.minimal.some((m) => L.popcount(m) > g.gamma);
    if (hasTarget) {
      const done = a.dominating && a.minimal && !a.minimum;
      lines.push('چالش: یک مجموعه‌ی مینیمال بسازید که مینیمم نباشد. ' + (done ? 'انجام شد ✓' : 'هنوز انجام نشده.'));
    } else {
      lines.push('چالش: در این گراف هر مجموعه‌ی مینیمال، مینیمم است.');
    }
    box.innerHTML = '';
    lines.forEach((text) => {
      const p = document.createElement('p');
      p.textContent = text;
      box.appendChild(p);
    });
  }

  /** حالت بازی: امتیازی (on = false) یا فقط تمرین (on = true). در تمرین، بخش‌های امتیازی محو می‌شوند. */
  function setPractice(on) {
    if (on && state.timed) finishTimed(true);
    state.practice = on;
    $('practice-mode').checked = on;
    document.body.classList.toggle('mode-practice', on);
    $('practice-mode').setAttribute('aria-checked', on ? 'true' : 'false');
    // تب کارنامه در تمرین وجود ندارد: اگر باز بود، به تب بازی برمی‌گردیم
    if (on && $('view-scores').classList.contains('active')) switchView('game');
    clearResult();
    updateButtons();
    renderBoard();
    saveState();
  }

  /** نمایش عدد به رقم فارسی. */
  function toFa(x) {
    return String(x).replace(/[0-9]/g, (d) => FA_DIGITS[Number(d)]);
  }

  /** عدد اعشاری با جداکننده‌ی فارسی «٫» و بدون صفرهای انتهایی (مثلاً ۲٫۵). */
  function toFaDecimal(x) {
    return toFa(String(+x.toFixed(3)).replace('.', '٫'));
  }

  /* ---------- رسم گراف بر اساس n و γ ---------- */

  function generateGraph() {
    const n = Number($('gen-n').value);
    const k = Number($('gen-k').value);
    const msg = $('gen-msg');
    if (!Number.isInteger(n) || n < 2 || n > 10) {
      msg.textContent = 'تعداد رأس ' + M('n') + ' باید عدد صحیحی از ۲ تا ۱۰ باشد.';
      return;
    }
    if (!Number.isInteger(k) || k < 1 || k > n) {
      msg.textContent = 'عدد احاطه‌گری ' + M('γ') + ' باید عدد صحیحی از ۱ تا ' + M('n') + ' باشد.';
      return;
    }
    const edges = L.generateWithGamma(n, k);
    if (!edges) {
      msg.textContent = 'ساخت گراف با این مشخصات ممکن نشد.';
      return;
    }
    const clean = sanitizeCustom(n, edges);
    state.gen = { n: clean.n, k, edges: clean.edges };
    switchView('game');
    loadGraph(GEN_ID);
    msg.textContent = state.graph.gamma === k
      ? 'گراف با ' + M('n = ' + toFa(n)) + ' و ' + M('γ = ' + toFa(k)) + ' رسم شد؛ ' + M('|E| = ' + toFa(clean.edges.length)) + '.'
      : 'هشدار: ' + M('γ') + ' گراف ساخته‌شده برابر ' + toFa(state.graph.gamma) + ' است، نه ' + toFa(k) + '.';
  }

  /* ==================================================================
   * ۶. سازنده‌ی گراف سفارشی
   * ================================================================== */

  let draftEdges = [];

  function drawMatrix() {
    const n = Number($('custom-n').value);
    // مقدار نامعتبر: ماتریس قبلی حفظ می‌شود و ورودی بی‌صدا اصلاح نمی‌شود
    if (!Number.isInteger(n) || n < 2 || n > 10) {
      $('custom-msg').textContent = 'تعداد رأس‌ها باید عدد صحیحی از ۲ تا ۱۰ باشد.';
      return;
    }
    draftEdges = draftEdges.filter(([a, b]) => a < n && b < n);

    const table = $('custom-matrix');
    table.innerHTML = '';
    const thead = document.createElement('thead');
    const hr = document.createElement('tr');
    hr.appendChild(document.createElement('th'));
    for (let j = 0; j < n; j++) {
      const th = document.createElement('th');
      th.textContent = toFa(j + 1);
      hr.appendChild(th);
    }
    thead.appendChild(hr);
    table.appendChild(thead);

    const tbody = document.createElement('tbody');
    for (let i = 0; i < n; i++) {
      const tr = document.createElement('tr');
      const th = document.createElement('th');
      th.textContent = toFa(i + 1);
      tr.appendChild(th);
      for (let j = 0; j < n; j++) {
        const td = document.createElement('td');
        if (i >= j) {
          // فقط مثلث بالایی نمایش داده می‌شود تا هر یال یک‌بار و با یک خانه باشد
          td.className = 'diag';
        } else {
          const cb = document.createElement('input');
          cb.type = 'checkbox';
          const [a, b] = i < j ? [i, j] : [j, i];
          cb.checked = draftEdges.some(([x, y]) => x === a && y === b);
          cb.setAttribute('aria-label', 'یال ' + toFa(a + 1) + ' و ' + toFa(b + 1));
          cb.addEventListener('change', () => { toggleDraftEdge(a, b, cb.checked); drawPad(); });
          td.appendChild(cb);
        }
        tr.appendChild(td);
      }
      tbody.appendChild(tr);
    }
    table.appendChild(tbody);
    $('custom-msg').textContent = 'تعداد یال‌های انتخابی: ' + toFa(draftEdges.length) + '. پس از انتخاب، دکمه‌ی «بازی با این گراف» را بزنید.';
  }

  function toggleDraftEdge(a, b, on) {
    draftEdges = draftEdges.filter(([x, y]) => !(x === a && y === b));
    if (on) draftEdges.push([a, b]);
    $('custom-msg').textContent = 'تعداد یال‌های انتخابی: ' + toFa(draftEdges.length) + '. پس از انتخاب، دکمه‌ی «بازی با این گراف» را بزنید.';
  }

  /* ---------- ویرایشگر کشیدنی گراف سفارشی ----------
   * مختصات رأس‌ها در فضای ۰..۳۰۰ ذخیره می‌شود (فقط نمایش). یال‌ها همان draftEdges هستند،
   * پس جدول و صفحه همیشه یکی‌اند. */
  const PAD_SIZE = 300;
  const PAD_R = 15;
  let padPos = [];
  let padEdgeMode = false;
  let padPick = null;
  let padDrag = null;

  function padRing(n) {
    const pts = [];
    for (let i = 0; i < n; i++) {
      const a = -Math.PI / 2 + (2 * Math.PI * i) / n;
      pts.push({ x: 150 + 110 * Math.cos(a), y: 150 + 110 * Math.sin(a) });
    }
    return pts;
  }

  /** صفحه‌ی گراف را از روی n و draftEdges دوباره می‌سازد. */
  function drawPad() {
    const pad = $('pad');
    if (!pad) return;
    const n = Number($('custom-n').value);
    if (!Number.isInteger(n) || n < 2 || n > 10) { pad.innerHTML = ''; return; }
    if (padPos.length !== n) padPos = padRing(n);
    if (padPick !== null && padPick >= n) padPick = null;
    pad.innerHTML = '';
    const svg = svgEl('svg', { viewBox: '0 0 ' + PAD_SIZE + ' ' + PAD_SIZE, class: 'pad-svg', role: 'group', 'aria-label': 'صفحه‌ی ساخت گراف' });
    draftEdges.forEach(([a, b]) => {
      if (a >= n || b >= n) return;
      svg.appendChild(svgEl('line', { class: 'pad-edge', 'data-a': a, 'data-b': b,
        x1: padPos[a].x, y1: padPos[a].y, x2: padPos[b].x, y2: padPos[b].y }));
    });
    for (let v = 0; v < n; v++) {
      const g = svgEl('g', { class: 'pad-v' + (padPick === v ? ' pick' : ''), tabindex: 0, role: 'button', 'data-pv': v,
        'aria-label': 'رأس ' + toFa(v + 1) + (padPick === v ? '، انتخاب‌شده برای یال' : '') });
      g.appendChild(svgEl('circle', { cx: padPos[v].x, cy: padPos[v].y, r: PAD_R }));
      const label = svgEl('text', { class: 'pad-label', x: padPos[v].x, y: padPos[v].y });
      label.textContent = toFa(v + 1);
      g.appendChild(label);
      g.addEventListener('pointerdown', (e) => onPadDown(e, v));
      g.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); padTap(v); }
      });
      svg.appendChild(g);
    }
    svg.addEventListener('pointermove', onPadMove);
    svg.addEventListener('pointerup', onPadUp);
    svg.addEventListener('pointercancel', onPadUp);
    pad.appendChild(svg);
  }

  /** فقط موقعیت‌ها را به‌روز می‌کند تا هنگام کشیدن عنصر SVG عوض نشود (فوکوس و capture حفظ شود). */
  function updatePadGeometry(svg) {
    svg.querySelectorAll('.pad-v').forEach((g) => {
      const v = Number(g.getAttribute('data-pv'));
      g.querySelector('circle').setAttribute('cx', padPos[v].x);
      g.querySelector('circle').setAttribute('cy', padPos[v].y);
      const label = g.querySelector('text');
      label.setAttribute('x', padPos[v].x);
      label.setAttribute('y', padPos[v].y);
    });
    svg.querySelectorAll('.pad-edge').forEach((l) => {
      const a = Number(l.getAttribute('data-a')), b = Number(l.getAttribute('data-b'));
      l.setAttribute('x1', padPos[a].x); l.setAttribute('y1', padPos[a].y);
      l.setAttribute('x2', padPos[b].x); l.setAttribute('y2', padPos[b].y);
    });
  }

  function svgPoint(svg, e) {
    const r = svg.getBoundingClientRect();
    return {
      x: ((e.clientX - r.left) / r.width) * PAD_SIZE,
      y: ((e.clientY - r.top) / r.height) * PAD_SIZE,
    };
  }

  function onPadDown(e, v) {
    if (padEdgeMode) { e.preventDefault(); padTap(v); return; }
    const svg = e.currentTarget.ownerSVGElement;
    padDrag = { v: v };
    svg.setPointerCapture(e.pointerId);
    e.preventDefault();
  }

  function onPadMove(e) {
    if (!padDrag) return;
    const pt = svgPoint(e.currentTarget, e);
    const m = PAD_R + 2;
    padPos[padDrag.v] = {
      x: Math.min(PAD_SIZE - m, Math.max(m, pt.x)),
      y: Math.min(PAD_SIZE - m, Math.max(m, pt.y)),
    };
    updatePadGeometry(e.currentTarget);
  }

  function onPadUp() {
    padDrag = null;
  }

  /** انتخاب دو رأس برای ساخت یا حذف یال (همان تغییری که در جدول انجام می‌شود). */
  function padTap(v) {
    if (padPick === null) {
      padPick = v;
    } else if (padPick === v) {
      padPick = null;
    } else {
      const a = Math.min(padPick, v), b = Math.max(padPick, v);
      const exists = draftEdges.some(([x, y]) => x === a && y === b);
      toggleDraftEdge(a, b, !exists);
      padPick = null;
      drawMatrix();
    }
    drawPad();
  }

  function applyCustom() {
    const n = Number($('custom-n').value);
    // اعتبارسنجی صریح: مقدار خارج از بازه نباید بی‌صدا تغییر کند
    if (!Number.isInteger(n) || n < 2 || n > 10) {
      $('custom-msg').textContent = 'تعداد رأس‌ها باید عدد صحیحی از ۲ تا ۱۰ باشد.';
      return;
    }
    state.custom = sanitizeCustom(n, draftEdges);
    draftEdges = state.custom.edges.slice();
    switchView('game');
    loadGraph(CUSTOM_ID);
    $('custom-msg').textContent = 'گراف سفارشی بارگذاری شد: ' + M('n = ' + toFa(state.custom.n)) + '، ' + M('|E| = ' + toFa(state.custom.edges.length)) + '.';
  }

  /* ==================================================================
   * ۷. آزمایشگاه
   * ================================================================== */

  function fillSelect(sel, selectedId) {
    sel.innerHTML = '';
    L.listGraphs().forEach((x) => {
      const o = document.createElement('option');
      o.value = x.id;
      o.textContent = x.family + ': ' + htmlToText(x.name);
      if (x.id === selectedId) o.selected = true;
      sel.appendChild(o);
    });
  }

  function buildStation1() {
    const body = $('st1-body');
    body.innerHTML = '';
    ['P3', 'C4', 'K4', 'S4'].forEach((id) => {
      const g = L.getGraph(id);
      const sets = g.minSets.map((set) => '{' + listLabels(g, bitsOf(set, g.n)) + '}').join('؛ ');
      const tr = document.createElement('tr');
      [g.name, toFa(g.n), M(sets), toFa(g.gamma)].forEach((c, i) => {
        const td = document.createElement('td');
        if (i === 0) td.innerHTML = c; else td.textContent = c;
        tr.appendChild(td);
      });
      body.appendChild(tr);
    });
    const note = document.createElement('tr');
    const c4 = L.getGraph('C4');
    note.innerHTML = '<td colspan="4" class="hint">' + MH('C<sub>4</sub>') + ' ' + toFa(c4.minSets.length) + ' مجموعه‌ی احاطه‌گر مینیمم دارد؛ همه‌ی آن‌ها در جدول آمده‌اند.</td>';
    body.appendChild(note);
  }

  function buildStation2() {
    const table = $('st2-table');
    const N = 7;
    const gp = [], gc = [], ceil = [];
    for (let n = 1; n <= N; n++) {
      gp.push(L.computeGamma(n, L.path(n).edges).gamma);
      ceil.push(Math.ceil(n / 3));
      gc.push(n >= 3 ? L.computeGamma(n, L.cycle(n).edges).gamma : null);
    }
    const row = (label, values) => {
      const tr = document.createElement('tr');
      const th = document.createElement('th');
      th.innerHTML = label; // برچسب‌ها ثابت هستند و از ورودی کاربر نمی‌آیند
      tr.appendChild(th);
      values.forEach((v) => {
        const td = document.createElement('td');
        td.textContent = v === null ? '—' : toFa(v);
        tr.appendChild(td);
      });
      return tr;
    };
    table.innerHTML = '';
    const thead = document.createElement('thead');
    const head = document.createElement('tr');
    head.innerHTML = '<th>' + MH('n') + '</th>';
    for (let n = 1; n <= N; n++) head.innerHTML += '<th>' + toFa(n) + '</th>';
    thead.appendChild(head);
    const tbody = document.createElement('tbody');
    tbody.appendChild(row(MH('γ(P<sub>n</sub>)'), gp));
    tbody.appendChild(row(MH('⌈n/۳⌉'), ceil));
    tbody.appendChild(row(MH('γ(C<sub>n</sub>)'), gc));
    const matchP = gp.every((v, i) => v === ceil[i]);
    const matchC = gc.every((v, i) => v === null || v === ceil[i]);
    const verdict = document.createElement('tr');
    verdict.innerHTML = '<th>تطابق</th><td colspan="' + N + '" class="' + (matchP && matchC ? 'ok-cell' : 'bad-cell') + '">' +
      (matchP && matchC ? MH('γ(P<sub>n</sub>) = γ(C<sub>n</sub>) = ⌈n/۳⌉') + ' برای ' + MH('n = ۱ تا ۷') + ' ✓' : 'عدم تطابق — بررسی کنید') + '</td>';
    tbody.appendChild(verdict);
    table.appendChild(thead);
    table.appendChild(tbody);
  }

  let st3Graph = null;

  function buildStation3(id) {
    st3Graph = L.getGraph(id);
    const g = st3Graph;
    const lower = g.n / (g.delta + 1);
    const lowerOk = g.gamma >= lower - 1e-9;
    const tight = Math.abs(g.gamma - lower) < 1e-9;
    const iso = L.hasIsolatedVertex(g.n, g.edges);
    const ore = iso ? null : g.n / 2;
    const oreOk = ore === null ? null : g.gamma <= ore + 1e-9;

    const rows = [
      [MH('n'), g.n],
      [MH('|E|'), g.edges.length],
      [MH('Δ(G)'), g.delta],
      ['کران پایین ' + MH('n/(Δ+1)'), toFaDecimal(lower)],
      [MH('γ(G)'), g.gamma],
      [MH('γ ≥ n/(Δ+1)') + '؟', lowerOk ? 'بله ✓' + (tight ? ' (تیز)' : '') : 'خیر ✗'],
      ['رأس منفرد؟', iso ? 'دارد' : 'ندارد'],
      ['کران اور ' + MH('n/2'), iso ? 'کاربرد ندارد' : toFaDecimal(ore)],
      [MH('γ ≤ n/2') + '؟', iso ? 'کاربرد ندارد' : (oreOk ? 'بله ✓' : 'خیر ✗')],
    ];
    const t = $('st3-table');
    t.innerHTML = '';
    rows.forEach(([k, v]) => {
      const tr = document.createElement('tr');
      tr.innerHTML = '<th>' + k + '</th><td>' + (typeof v === 'number' ? toFa(v) : v) + '</td>';
      t.appendChild(tr);
    });

    const sel = $('st3-edge');
    sel.innerHTML = '';
    for (let a = 0; a < g.n; a++) {
      for (let b = a + 1; b < g.n; b++) {
        if (!L.hasEdge(g.edges, a, b)) {
          const o = document.createElement('option');
          o.value = a + ',' + b;
          o.textContent = labelOf(g, a) + ' و ' + labelOf(g, b);
          sel.appendChild(o);
        }
      }
    }
    $('st3-edge-result').textContent = sel.options.length
      ? ''
      : 'این گراف کامل است؛ یال ناموجودی برای افزودن وجود ندارد.';
    $('st3-add').disabled = sel.options.length === 0;
  }

  function runEdgeExperiment() {
    const g = st3Graph;
    const sel = $('st3-edge');
    if (!sel.value) return;
    const [a, b] = sel.value.split(',').map(Number);
    const after = L.computeGamma(g.n, g.edges.concat([[a, b]])).gamma;
    const before = g.gamma;
    let msg = M('γ قبل = ' + toFa(before)) + '، ' + M('γ بعد = ' + toFa(after)) + '. ';
    msg += after <= before
      ? M('γ') + ' افزایش نیافت ✓ (مطابق قضیه‌ی اثر یال).'
      : 'توجه: ' + M('γ') + ' افزایش یافت — این با قضیه تناقض دارد؛ داده را بررسی کنید.';
    $('st3-edge-result').textContent = msg;
  }

  /** ایستگاه ۴: فهرست همه‌ی مجموعه‌های احاطه‌گر مینیمال و مشخص کردن مینیمم‌ها. */
  function buildStation4(id) {
    const g = L.getGraph(id);
    const rows = g.minimal.slice().sort((a, b) => L.popcount(a) - L.popcount(b) || a - b);
    const minimumCount = rows.filter((m) => L.popcount(m) === g.gamma).length;
    const nonMinimum = rows.length - minimumCount;
    $('st4-summary').textContent = M('γ(' + plainName(g) + ') = ' + toFa(g.gamma)) + '. تعداد مجموعه‌های احاطه‌گر مینیمال: ' +
      toFa(rows.length) + '، که از آن‌ها ' + toFa(minimumCount) + ' مینیمم و ' + toFa(nonMinimum) + ' غیرمینیمم است.';
    const table = $('st4-table');
    table.innerHTML = '';
    const thead = document.createElement('thead');
    thead.innerHTML = '<tr><th>مجموعه‌ی مینیمال</th><th>' + MH('|D|') + '</th><th>مینیمم است؟</th></tr>';
    table.appendChild(thead);
    const tbody = document.createElement('tbody');
    rows.forEach((m) => {
      const k = L.popcount(m);
      const tr = document.createElement('tr');
      const isMin = k === g.gamma;
      const cells = [M('{' + listLabels(g, bitsOf(m, g.n)) + '}'), toFa(k), isMin ? 'بله' : 'خیر'];
      cells.forEach((c) => {
        const td = document.createElement('td');
        td.textContent = c;
        tr.appendChild(td);
      });
      if (!isMin) tr.className = 'nonmin-row';
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
  }

  /* ==================================================================
   * ۸. تب‌ها، میان‌برها و راه‌اندازی
   * ================================================================== */

  function switchView(name) {
    document.querySelectorAll('.tab').forEach((t) => {
      const on = t.dataset.view === name;
      t.classList.toggle('active', on);
      t.setAttribute('aria-selected', on ? 'true' : 'false');
    });
    document.querySelectorAll('.view').forEach((v) => {
      v.classList.toggle('active', v.id === 'view-' + name);
    });
    // هر تب انیمیشن خودش را از ابتدا شروع می‌کند: صفحه به بالای تب برمی‌گردد
    if (typeof window.scrollTo === 'function') window.scrollTo(0, 0);
  }

  function isTyping(target) {
    return target && (target.tagName === 'INPUT' || target.tagName === 'SELECT' || target.tagName === 'TEXTAREA');
  }

  function bindEvents() {
    document.querySelectorAll('.tab').forEach((t) => {
      t.addEventListener('click', () => switchView(t.dataset.view));
    });

    $('graph-select').addEventListener('change', (e) => {
      loadGraph(e.target.value);
    });

    $('btn-check').addEventListener('click', checkStage1);
    $('btn-check2').addEventListener('click', checkStage2);
    $('removal-apply').addEventListener('click', applyRemoval);
    $('removal-clear').addEventListener('click', clearRemoval);
    $('btn-reset').addEventListener('click', () => setMarks(0, true));
    $('btn-undo').addEventListener('click', undo);
    $('btn-redo').addEventListener('click', redo);
    $('btn-hint').addEventListener('click', useHint);
    $('btn-next').addEventListener('click', nextRound);
    $('btn-timed').addEventListener('click', () => (state.timed ? finishTimed(true) : startTimed()));
    $('btn-random').addEventListener('click', () => loadGraph(randomGraph()));
    $('btn-card-add').addEventListener('click', addCard);
    $('btn-card-reset').addEventListener('click', resetCard);
    $('card-select').addEventListener('change', (e) => {
      state.activeCard = Number(e.target.value);
      renderRecords();
      saveState();
    });
    $('btn-restart').addEventListener('click', restartGame);
    $('btn-gamma').addEventListener('click', showGamma);
    $('btn-csv').addEventListener('click', exportCsv);
    $('btn-print').addEventListener('click', printReport);

    $('team-mode').addEventListener('change', (e) => {
      state.teamMode = e.target.checked;
      state.active = 0;
      renderScores();
      saveState();
    });

    $('custom-n').addEventListener('change', () => { drawMatrix(); drawPad(); });
    $('pad-mode').addEventListener('click', () => {
      padEdgeMode = !padEdgeMode;
      padPick = null;
      $('pad-mode').textContent = 'حالت یال: ' + (padEdgeMode ? 'روشن' : 'خاموش');
      $('pad-mode').setAttribute('aria-pressed', padEdgeMode ? 'true' : 'false');
      drawPad();
    });
    $('btn-custom-apply').addEventListener('click', applyCustom);

    $('st3-graph').addEventListener('change', (e) => buildStation3(e.target.value));
    $('st3-add').addEventListener('click', runEdgeExperiment);
    $('st4-graph').addEventListener('change', (e) => buildStation4(e.target.value));
    $('btn-generate').addEventListener('click', generateGraph);
    $('practice-mode').addEventListener('change', (e) => setPractice(e.target.checked));
    $('st5-go').addEventListener('click', () => {
      state.teamMode = true;
      $('team-mode').checked = true;
      state.teams.forEach((t) => { t.score = 0; t.rounds = 0; });
      state.history = [];
      state.active = 0;
      switchView('game');
      loadGraph(state.graphId);
    });

    document.addEventListener('keydown', (e) => {
      if (isTyping(e.target) || !$('view-game').classList.contains('active')) return;
      const mod = e.ctrlKey || e.metaKey;
      if (mod && !e.shiftKey && e.key.toLowerCase() === 'z') { e.preventDefault(); undo(); }
      else if (mod && (e.key.toLowerCase() === 'y' || (e.shiftKey && e.key.toLowerCase() === 'z'))) { e.preventDefault(); redo(); }
    });
  }

  function init() {
    if (!L) return;
    loadState();
    fillSelect($('graph-select'), state.graphId);
    fillSelect($('st3-graph'), 'C5');
    fillSelect($('st4-graph'), 'P6');
    $('team-mode').checked = state.teamMode;
    $('practice-mode').checked = state.practice;
    document.body.classList.toggle('mode-practice', state.practice);
    $('practice-mode').setAttribute('aria-checked', state.practice ? 'true' : 'false');
    if (!L.SHOW_GAMMA_BUTTON) $('gamma-btn-row').hidden = true;

    draftEdges = state.custom.edges.slice();
    $('custom-n').value = String(state.custom.n);
    drawMatrix();
    drawPad();

    bindEvents();
    buildStation1();
    buildStation2();
    buildStation3($('st3-graph').value);
    buildStation4($('st4-graph').value);
    loadGraph(state.graphId, true);
  }

  document.addEventListener('DOMContentLoaded', init);
})();
