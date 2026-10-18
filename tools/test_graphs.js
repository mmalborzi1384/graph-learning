// تست واحد منطق گراف (graphs.js) — اجرا: node tools/test_graphs.js
const fs = require('fs'), path = require('path');
const src = fs.readFileSync(path.join(__dirname, '../code/graphs.js'), 'utf8');
const win = {}; new Function('window', src)(win);
const L = win.GraphLib;
const expect = {P3:1,P4:2,P5:2,P6:2,P7:3,C3:1,C4:2,C5:2,C6:2,C7:3,K3:1,K4:1,K5:1,S4:1,S5:1,K14:1,K22:2,K23:2,K33:2,W4:1,W5:1,PT:3};
let fails = 0; const eq = (name, got, want) => { const ok = JSON.stringify(got) === JSON.stringify(want); if (!ok) fails++; console.log(ok ? 'OK  ' : 'FAIL', name, 'got=', got, 'want=', want); };
for (const g of L.listGraphs()) eq('gamma ' + g.id, L.getGraph(g.id).gamma, expect[g.id]);
const PT = L.getGraph('PT');
eq('PT n=10', PT.n, 10);
eq('PT |E|=15 (سه‌منظم)', PT.edges.length, 15);
eq('PT minimum sets = 10 (بررسی مستقل)', PT.minSets.length, 10);
eq('PT minimal sets = 27 (بررسی مستقل)', PT.minimal.length, 27);
eq('PT مختصات: ۱۰ نقطه‌ی یکتا', new Set(PT.points.map(p => p.x.toFixed(1) + ',' + p.y.toFixed(1))).size, 10);
const C4 = L.getGraph('C4');
eq('C4 {1,3} exact', L.evaluateMarks(C4, 0b0101).points, 15);
eq('C4 {1,2,3} nonmin', L.evaluateMarks(C4, 0b0111).points, 5);
eq('P6 {2,4,6} مینیمال غیرمینیمم = 10', L.evaluateMarks(L.getGraph('P6'), 0b101010).points, 10);
eq('C4 {1} notdom', L.evaluateMarks(C4, 0b0001).points, 0);
eq('C4 {} notdom', L.evaluateMarks(C4, 0).points, 0);
eq('P4+{1,3} gamma', L.makeCustomGraph(4, [[0,1],[1,2],[2,3],[0,2]], 'line').gamma, 1);
eq('K1 gamma', L.computeGamma(1, []).gamma, 1);
eq('P1 gamma', L.computeGamma(1, []).gamma, 1);
eq('edgeless N3 gamma', L.computeGamma(3, []).gamma, 3);
console.log(fails ? `\n${fails} FAIL` : '\nall unit tests passed');
process.exitCode = fails ? 1 : 0;

// ---- نسخه ۶.۴.۰: احاطه‌گر مینیمال، تحلیل مجموعه، و ساخت بر اساس n و γ ----
{
  let f2 = 0; const ok2 = (name, cond) => { if (!cond) f2++; console.log(cond ? 'OK  ' : 'FAIL', name); };
  const P6 = L.getGraph('P6');
  // {2،4،6} = بیت‌های 1،3،5
  const m246 = (1 << 1) | (1 << 3) | (1 << 5);
  const a = L.analyzeSet(P6, m246);
  ok2('P6 {2,4,6} احاطه‌گر است', a.dominating === true);
  ok2('P6 {2,4,6} مینیمال است', a.minimal === true);
  ok2('P6 {2,4,6} مینیمم نیست', a.minimum === false);
  ok2('P6 {2,4,6} مهره‌ی زائد ندارد', a.redundant.length === 0);
  // {2،3،5،6} احاطه‌گر اما غیرمینیمال: حذف ۳ یا ... باید زائد باشد
  const m2356 = (1 << 1) | (1 << 2) | (1 << 4) | (1 << 5);
  const b2 = L.analyzeSet(P6, m2356);
  ok2('P6 {2,3,5,6} غیرمینیمال است', b2.minimal === false && b2.dominating === true);
  ok2('P6 {2,3,5,6} زائد دارد', b2.redundant.length > 0);
  ok2('P6 {1} احاطه‌گر نیست', L.analyzeSet(P6, 1).dominating === false);
  // هر مینیمم مینیمال است
  for (const id of ['P5', 'P7', 'C6', 'K33', 'W4']) {
    const g = L.getGraph(id);
    const allMin = g.minSets.every((s) => g.minimal.indexOf(s) !== -1);
    ok2('هر مینیمم مینیمال است: ' + id, allMin);
  }
  // مینیمال‌ها همه با حذف تک‌تک اعضا بررسی می‌شوند
  const C6 = L.getGraph('C6');
  ok2('C6: هر مینیمال واقعاً مینیمال است', C6.minimal.every((s) => L.isMinimalDominating(6, C6.closed, s)));
  // ساخت بر اساس n و γ
  let gok = true;
  for (let n = 2; n <= 8; n++) for (let k = 1; k <= n; k++) {
    for (let t = 0; t < 5; t++) {
      const e = L.generateWithGamma(n, k);
      if (!e || L.computeGamma(n, e).gamma !== k) gok = false;
    }
  }
  ok2('generateWithGamma: γ = k برای n=2..8', gok);
  ok2('generateWithGamma: k > n رد می‌شود', L.generateWithGamma(3, 4) === null);
  ok2('generateWithGamma: n=11 رد می‌شود', L.generateWithGamma(11, 2) === null);
  // راستی‌آزمایی قضیه‌ی ساختاری: هر احاطه‌گر شامل یک مینیمال است
  let sub = true;
  for (const id of ['P6', 'C6', 'W4']) {
    const g = L.getGraph(id);
    for (let S = 1; S <= L.fullMask(g.n); S++) {
      if (!L.isDominating(g.n, g.closed, S)) continue;
      if (!g.minimal.some((m) => (m & S) === m)) { sub = false; }
    }
  }
  ok2('هر احاطه‌گر شامل یک احاطه‌گر مینیمال است', sub);
  console.log(f2 ? `\n${f2} FAIL (نسخه ۶.۴.۰)` : 'نسخه ۶.۴.۰: همه‌ی تست‌های منطق گراف موفق');
  if (f2) process.exitCode = 1;
}
