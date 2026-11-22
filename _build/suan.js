/* ==================== 速算训练（v2.1） ==================== */
const K_SUAN = 'yp_suan_v1';
const K_SUAN_LAST = 'yp_suan_last_v1';

const SUAN_CATS = [
  { id:'basic', name:'基础计算', tag:'打磨运算本能',
    types:['add2','sub2','add3','sub3','multiadd','mul2x1','mul2x2','mul3x1','square','div3x1','div3x2','div5x3'] },
  { id:'data', name:'资料专项', tag:'公式条件反射',
    types:['jizhun','zengliang','baihua_calc','baihua_prac','fenbi','jizhunbi','nianavg','niangrowth'] },
  { id:'game', name:'专注训练', tag:'注意力与数字敏感', types:['schulte','puzzle'] },
];
const SUAN_TYPES = {
  add2:{ name:'两位数加法', cat:'basic', diff:false, desc:'两位数相加，练进位与凑整。' },
  sub2:{ name:'两位数减法', cat:'basic', diff:false, desc:'两位数相减，练借位。' },
  add3:{ name:'三位数加法', cat:'basic', diff:false, desc:'三位数相加，先加整百再加零头。' },
  sub3:{ name:'三位数减法', cat:'basic', diff:false, desc:'三位数相减，注意借位。' },
  multiadd:{ name:'多数相加', cat:'basic', diff:false, desc:'多笔数相加，练分组凑整。' },
  mul2x1:{ name:'两位数乘一位', cat:'basic', diff:false, desc:'两位数乘一位，拆成十位+个位。' },
  mul2x2:{ name:'两位数乘两位', cat:'basic', diff:false, desc:'两位数乘两位数，先拆再合。' },
  mul3x1:{ name:'三位数乘一位', cat:'basic', diff:false, desc:'三位数乘一位，逐位相乘。' },
  square:{ name:'常见平方数', cat:'basic', diff:false, desc:'11–99 的平方，背到条件反射。' },
  div3x1:{ name:'三位除一位', cat:'basic', diff:false, desc:'三位数除以一位数，先估高位。' },
  div3x2:{ name:'三位除两位', cat:'basic', diff:false, desc:'三位数除以两位数，用乘法反推。' },
  div5x3:{ name:'五位除三位', cat:'basic', diff:false, desc:'五位数除以三位数，先化整再修正。' },
  jizhun:{ name:'估算基期', cat:'data', diff:true, desc:'基期 = 现期 ÷ (1 + 增长率)。' },
  zengliang:{ name:'估算增长量', cat:'data', diff:true, desc:'增长量 = 现期 × 增长率 ÷ (1 + 增长率)。' },
  baihua_calc:{ name:'百化分计算', cat:'data', diff:true, desc:'百分数化成 1/n，直接算分母。' },
  baihua_prac:{ name:'百化分练习', cat:'data', diff:true, desc:'百分数与分数互换，双向练熟。' },
  fenbi:{ name:'分数比较', cat:'data', diff:true, desc:'交叉相乘比较两个分数的大小。' },
  jizhunbi:{ name:'基期比较', cat:'data', diff:true, desc:'增长率大的基期往往更小，先看现期再看增速。' },
  nianavg:{ name:'年平均量', cat:'data', diff:true, desc:'总和 ÷ 年数，注意单位换算。' },
  niangrowth:{ name:'年均增长率', cat:'data', diff:true, desc:'末期 = 初期 × (1+r)^n，记住常见增长率。' },
  schulte:{ name:'舒尔特方格', cat:'game', diff:false, game:'schulte', desc:'按 1→N 顺序点击，练注意力与数字敏感。' },
  puzzle:{ name:'数字谜题', cat:'game', diff:true, desc:'找出数列规律，填下一个数。' },
};
/* 旧版题型 ID（v2.1 之前）在历史记录里仍可显示名称 */
const SUAN_LEGACY = { add:'两位数加法', muldiv:'两位数乘一位', baihuafen:'百化分计算' };

function suanRnd(a, b){ return Math.floor(Math.random() * (b - a + 1)) + a; }
function suanPick(a){ return a[Math.floor(Math.random() * a.length)]; }
function suanNum(n){ return (Math.round(n * 100) / 100).toString(); }
function suanType(typeId){ return SUAN_TYPES[typeId] || null; }
function suanTypeName(typeId){ const t = suanType(typeId); return t ? t.name : (SUAN_LEGACY[typeId] || typeId); }

/* ---------- 题目生成（模板化，不存题库，可无限练） ---------- */
function genAdd2(){
  const a = suanRnd(12, 89), b = suanRnd(12, 89);
  return { stem: a + ' + ' + b + ' = ?', answer: a + b };
}
function genSub2(){
  let a = suanRnd(21, 99), b = suanRnd(11, 89);
  if (b > a){ const t = a; a = b; b = t; }
  return { stem: a + ' - ' + b + ' = ?', answer: a - b };
}
function genAdd3(){
  const a = suanRnd(105, 899), b = suanRnd(105, 899);
  return { stem: a + ' + ' + b + ' = ?', answer: a + b };
}
function genSub3(){
  let a = suanRnd(210, 999), b = suanRnd(105, 899);
  if (b > a){ const t = a; a = b; b = t; }
  return { stem: a + ' - ' + b + ' = ?', answer: a - b };
}
function genMultiAdd(){
  const n = suanRnd(4, 6), arr = [];
  let sum = 0;
  for (let i = 0; i < n; i++){ const x = suanRnd(11, 99); arr.push(x); sum += x; }
  return { stem: arr.join(' + ') + ' = ?', answer: sum };
}
function genMul2x1(){
  const a = suanRnd(12, 99), b = suanRnd(2, 9);
  return { stem: a + ' × ' + b + ' = ?', answer: a * b };
}
function genMul2x2(){
  const a = suanRnd(11, 49), b = suanRnd(11, 29);
  return { stem: a + ' × ' + b + ' = ?', answer: a * b };
}
function genMul3x1(){
  const a = suanRnd(105, 999), b = suanRnd(2, 9);
  return { stem: a + ' × ' + b + ' = ?', answer: a * b };
}
function genSquare(){
  const n = suanRnd(11, 99);
  return { stem: n + '² = ?', answer: n * n };
}
function genDiv3x1(){
  let q, b, a, guard = 0;
  do { q = suanRnd(12, 99); b = suanRnd(2, 9); a = q * b; guard++; } while ((a < 100 || a > 999) && guard < 60);
  return { stem: a + ' ÷ ' + b + ' = ?', answer: q };
}
function genDiv3x2(){
  let q, b, a, guard = 0;
  do { q = suanRnd(3, 9); b = suanRnd(11, 99); a = q * b; guard++; } while ((a < 100 || a > 999) && guard < 80);
  return { stem: a + ' ÷ ' + b + ' = ?', answer: q };
}
function genDiv5x3(){
  let q, b, a, guard = 0;
  do { b = suanRnd(105, 899); q = suanRnd(12, 90); a = b * q; guard++; } while ((a < 10000 || a > 99999) && guard < 80);
  return { stem: a + ' ÷ ' + b + ' = ?', answer: q };
}
const SUAN_RATES = [[10,10],[20,5],[25,4],[50,2]];
function genBase(diff, askDelta){
  const adv = diff === 'advanced' || (diff === 'mixed' && Math.random() < .5);
  let p, den, base;
  if (adv){ // 12.5% / 16.7% / 33.3% / 14.3%
    p = suanPick([12.5, 16.7, 33.3, 14.3]);
    den = p === 12.5 ? 8 : p === 16.7 ? 6 : p === 33.3 ? 3 : 7;
    base = suanRnd(10, 120) * den;
  } else {
    p = suanPick([10, 20, 25, 50]);
    den = p === 10 ? 10 : p === 20 ? 5 : p === 25 ? 4 : 2;
    base = suanRnd(12, 160) * den;
  }
  const now = Math.round(base * (100 + p) / 100);
  const delta = now - base;
  if (askDelta) return { stem: '某指标现期 ' + now + '，同比增长 ' + p + '%，增长量约为多少？', answer: delta };
  return { stem: '某指标现期 ' + now + '，同比增长 ' + p + '%，基期约为多少？', answer: base };
}
const SUAN_FRACS = [[12.5,8],[16.7,6],[20,5],[25,4],[33.3,3],[50,2],[14.3,7],[11.1,9],[8.3,12],[6.7,15],[5.9,17],[9.1,11]];
function genBaihuaCalc(diff){
  const pool = diff === 'advanced' ? SUAN_FRACS : SUAN_FRACS.slice(0, 8);
  const x = suanPick(pool);
  return { stem: x[0] + '% 约等于 1/几？填写分母', answer: x[1] };
}
function genBaihuaPrac(diff){
  const pool = diff === 'advanced' ? SUAN_FRACS : SUAN_FRACS.slice(0, 8);
  const x = suanPick(pool);
  if (Math.random() < .5) return { stem: x[0] + '% 约等于 1/几？填写分母', answer: x[1] };
  return { stem: '1/' + x[1] + ' 约等于百分之几？填数字（如 12.5 或 16.7）', answer: x[0] };
}
function genFenbi(diff){
  let a, b, c, d, tries = 0;
  do {
    a = suanRnd(2, 9); b = suanRnd(3, 12); c = suanRnd(2, 9); d = suanRnd(3, 12);
    if (diff === 'advanced'){ a = suanRnd(11, 29); b = suanRnd(7, 19); c = suanRnd(11, 29); d = suanRnd(7, 19); }
    tries++;
  } while (tries < 20 && a * d === c * b && b !== d);
  const bigger = a / b > c / d ? 1 : 2;
  return { stem: '比较 ' + a + '/' + b + ' 与 ' + c + '/' + d + '，哪个更大？填 1（前者）或 2（后者）', answer: bigger };
}
function genJizhunbi(diff){
  let A1, p1, A2, p2, B1, B2, tries = 0;
  do {
    const g = () => { const p = suanPick([10, 20, 25, 50]); const den = p === 10 ? 10 : p === 20 ? 5 : p === 25 ? 4 : 2;
      const B = suanRnd(12, 120) * den; return { A: Math.round(B * (100 + p) / 100), p: p, B: B }; };
    const x = g(), y = g();
    A1 = x.A; p1 = x.p; B1 = x.B; A2 = y.A; p2 = y.p; B2 = y.B;
    tries++;
  } while (tries < 20 && B1 === B2);
  return { stem: '甲：现期 ' + A1 + '、增长 ' + p1 + '%；乙：现期 ' + A2 + '、增长 ' + p2 + '%。谁的基期更大？填 1（甲）或 2（乙）', answer: B1 > B2 ? 1 : 2 };
}
function genNianavg(diff){
  const n = suanRnd(3, 8), avg = suanRnd(12, 90) * 10, total = n * avg;
  return { stem: '某地 ' + n + ' 年累计产量 ' + total + ' 万吨，平均每年多少万吨？', answer: avg };
}
function genNiangrowth(diff){
  const p = suanPick([10, 20, 50]), n = diff === 'advanced' ? suanPick([2, 3]) : 2;
  const A = suanRnd(1, 9) * 1000;
  const B = Math.round(A * Math.pow(1 + p / 100, n));
  return { stem: '某指标从 ' + A + ' 增长到 ' + B + '，历时 ' + n + ' 年，年均增长率约为多少？填百分数整数', answer: p };
}
function genPuzzle(diff){
  const kind = suanRnd(0, 3);
  if (kind === 0){ const a = suanRnd(1, 20), d = suanRnd(2, 9); const seq = [a, a + d, a + 2 * d, a + 3 * d];
    return { stem: '找规律，填下一个数：' + seq.join(', ') + ', ?', answer: a + 4 * d }; }
  if (kind === 1){ const a = suanRnd(1, 6), r = suanPick([2, 3]); const seq = [a, a * r, a * r * r, a * r * r * r];
    return { stem: '找规律，填下一个数：' + seq.join(', ') + ', ?', answer: a * Math.pow(r, 4) }; }
  if (kind === 2){ const a = suanRnd(2, 9); const seq = [a, a * a + 1, (a + 1) * (a + 1) + 1, (a + 2) * (a + 2) + 1];
    return { stem: '找规律，填下一个数：' + seq.join(', ') + ', ?', answer: (a + 3) * (a + 3) + 1 }; }
  let x = suanRnd(2, 9); const seq = [x];
  for (let i = 0; i < 3; i++){ x = x * 2 + 1; seq.push(x); }
  return { stem: '找规律，填下一个数：' + seq.join(', ') + ', ?', answer: x * 2 + 1 };
}
function suanGenerate(typeId, diff){
  switch (typeId){
    case 'add2': return genAdd2();
    case 'sub2': return genSub2();
    case 'add3': return genAdd3();
    case 'sub3': return genSub3();
    case 'multiadd': return genMultiAdd();
    case 'mul2x1': return genMul2x1();
    case 'mul2x2': return genMul2x2();
    case 'mul3x1': return genMul3x1();
    case 'square': return genSquare();
    case 'div3x1': return genDiv3x1();
    case 'div3x2': return genDiv3x2();
    case 'div5x3': return genDiv5x3();
    case 'jizhun': return genBase(diff, false);
    case 'zengliang': return genBase(diff, true);
    case 'baihua_calc': return genBaihuaCalc(diff);
    case 'baihua_prac': return genBaihuaPrac(diff);
    case 'fenbi': return genFenbi(diff);
    case 'jizhunbi': return genJizhunbi(diff);
    case 'nianavg': return genNianavg(diff);
    case 'niangrowth': return genNiangrowth(diff);
    case 'puzzle': return genPuzzle(diff);
    default: return genAdd2();
  }
}

/* ---------- 判分 ---------- */
function suanNorm(v){
  return String(v == null ? '' : v).trim().replace(/\s+/g, '')
    .replace(/[，,]/g, '').replace(/[％%]/g, '').replace(/[。.]$/, '');
}
function suanCheck(q, user){
  const a = suanNorm(q.answer), u = suanNorm(user);
  if (!u) return false;
  if (a === u) return true;
  const na = Number(a), nu = Number(u);
  if (isFinite(na) && isFinite(nu)) return Math.abs(na - nu) < 1e-6;
  return false;
}

/* ---------- 会话存储 / 聚合 ---------- */
function suanData(){ const d = store.get(K_SUAN, null); return (d && d.sessions) ? d : { sessions: [] }; }
function suanSaveSession(sess){
  const d = suanData();
  d.sessions.unshift(sess);
  d.sessions = d.sessions.slice(0, 40);
  store.set(K_SUAN, d);
}
function suanAgg(days){
  const d = suanData();
  const from = Date.now() - days * 86400000;
  const list = d.sessions.filter(s => (s.end || 0) >= from);
  let qs = 0, right = 0, ms = 0, answered = 0;
  const byType = {};
  list.forEach(s => {
    qs += s.count || 0;
    right += s.right || 0;
    ms += s.totalMs || 0;
    answered += (s.answered || s.count || 0);
    if (!byType[s.typeId]) byType[s.typeId] = { n:0, right:0, ms:0, sessions:0 };
    const b = byType[s.typeId];
    b.sessions++; b.n += s.count || 0; b.right += s.right || 0; b.ms += s.totalMs || 0;
  });
  return { sessions: list.length, questions: qs, right: right, ms: ms, answered: answered,
    acc: answered ? Math.round(right / answered * 100) : 0,
    avgMs: answered ? Math.round(ms / answered) : 0, byType: byType };
}
function suanTypeStat(typeId, days){
  const agg = suanAgg(days || 30), b = agg.byType[typeId];
  if (!b || !b.n) return null;
  return { sessions: b.sessions, n: b.n, acc: Math.round(b.right / b.n * 100), avgMs: Math.round(b.ms / b.n) };
}
function suanFmtTime(ms){ return ms >= 1000 ? (ms / 1000).toFixed(1) + ' 秒' : Math.round(ms) + ' 毫秒'; }
function suanFmtSec(ms){ if (!ms || ms <= 0) return '—'; return (ms / 1000).toFixed(1) + ' 秒'; }
function suanScrollRecent(){ try { const el = document.getElementById('suanRecent'); if (el && el.scrollIntoView) el.scrollIntoView({behavior:'smooth'}); } catch(e){} }

/* ---------- ① 速算训练首页 ---------- */
let suanFrom = 'exam';
function renderSuanHome(){
  suanFrom = (curBank === 'drill') ? 'drill' : (curBank === 'study' ? 'study' : 'exam');
  view = 'suanHome'; curBank = 'exam';
  setBtn.style.display = 'none'; backBtn.style.display = 'grid';
  sheetBtn.style.display = 'none'; timerEl.style.display = 'none';
  hdTitle.textContent = '速算训练';
  if (hdEl) hdEl.style.display = '';
  foot.style.display = 'none';
  const today = suanAgg(1);
  const last = store.get(K_SUAN_LAST, null);
  const lastType = last && SUAN_TYPES[last.typeId] ? last.typeId : null;
  let html = '<div class="page" style="padding-top:10px">';
  html += '<div class="suan-hero"><div class="sh-top"><span class="sh-ico">⚡</span><div><b>今日速算</b><span>每天 10 分钟，资料分析快一倍</span></div>'
    + '<button class="h2btn" style="margin-left:auto;background:#fff;color:#2563EB;box-shadow:0 4px 12px rgba(37,99,235,.14)" onclick="suanScrollRecent()">🕘</button></div>'
    + '<div class="sh-stats"><div><b>' + today.questions + '</b><span>今日题数</span></div>'
    + '<div><b>' + (today.avgMs ? suanFmtSec(today.avgMs) : '—') + '</b><span>平均耗时</span></div>'
    + '<div><b>' + (today.questions ? today.acc + '%' : '—') + '</b><span>准确率</span></div></div>'
    + '<button class="suan-cta" onclick="' + (lastType ? 'openSuanCfg(\'' + lastType + '\')' : 'openSuanCfg(\'add2\')') + '">' + (lastType ? '继续上次：' + suanTypeName(lastType) : '开始第一组训练') + '</button></div>';

  SUAN_CATS.forEach(c => {
    html += '<div class="suan-cat"><div class="sc-head"><b>' + c.name + '</b><span>' + c.tag + '</span></div><div class="sc-grid">';
    c.types.forEach(tid => {
      const st = suanTypeStat(tid, 30);
      html += '<button class="suan-chip" onclick="openSuanCfg(\'' + tid + '\')">'
        + '<span class="sc-name">' + suanTypeName(tid) + '</span>'
        + '<span class="sc-meta">' + (st ? st.acc + '% · ' + suanFmtSec(st.avgMs) : '还没练过') + '</span></button>';
    });
    html += '</div></div>';
  });

  const d = suanData();
  html += '<div class="sec-head" id="suanRecent"><b>最近成绩</b><span>' + d.sessions.length + ' 组</span></div>';
  if (!d.sessions.length){
    html += '<div class="empty">还没有训练记录</div>';
  } else {
    d.sessions.slice(0, 6).forEach(s => {
      html += '<div class="list-item"><span class="li-main"><b>' + suanTypeName(s.typeId) + ' · ' + s.count + ' 题</b>'
        + '<span>准确率 ' + (s.answered ? Math.round(s.right / s.answered * 100) : 0) + '% · 用时 ' + suanFmtSec(s.totalMs) + ' · ' + fmtWhen(s.end) + '</span></span></div>';
    });
  }
  html += '</div>';
  app.innerHTML = html;
  syncChrome();
}

/* ---------- ② 题型配置页 ---------- */
let suanCfg = { typeId:'add2', count:10, diff:'base', timed:true };
function openSuanCfg(typeId){
  const t = suanType(typeId);
  if (!t) return;
  suanCfg = { typeId: typeId, count: 10, diff: t.diff ? 'base' : 'base', timed: true };
  renderSuanCfg();
}
function renderSuanCfg(){
  view = 'suanCfg';
  const t = suanType(suanCfg.typeId);
  hdTitle.textContent = t.name;
  backBtn.style.display = 'grid'; setBtn.style.display = 'none'; sheetBtn.style.display = 'none'; timerEl.style.display = 'none';
  if (hdEl) hdEl.style.display = '';
  let demo = null;
  try { demo = t.game === 'schulte' ? { stem:'按 1→16 顺序点击方格里的数字', answer:'—' } : suanGenerate(suanCfg.typeId, 'base'); } catch(e){}
  let html = '<div class="page" style="padding-top:10px">';
  html += '<div class="panel"><div style="font-size:18px;font-weight:800">' + t.name + '</div>'
    + '<div class="hint" style="margin-top:6px">' + t.desc + '</div>'
    + (demo ? '<div class="suan-demo"><span>示例</span><b>' + esc(demo.stem) + '</b></div>' : '')
    + '</div>';
  html += '<div class="panel"><b>题量</b><div class="chips" style="margin-top:10px">';
  [10, 20, 30].forEach(n => { html += '<button class="chipbtn ' + (suanCfg.count === n ? 'on' : '') + '" onclick="suanSetCfg(\'count\',' + n + ')">' + n + ' 题</button>'; });
  html += '</div>';
  if (t.diff){
    html += '<b style="display:block;margin-top:16px">难度</b><div class="chips" style="margin-top:10px">';
    [['base','基础'],['advanced','进阶'],['mixed','混合']].forEach(x => { html += '<button class="chipbtn ' + (suanCfg.diff === x[0] ? 'on' : '') + '" onclick="suanSetCfg(\'diff\',\'' + x[0] + '\')">' + x[1] + '</button>'; });
    html += '</div>';
  }
  html += '<div style="display:flex;align-items:center;justify-content:space-between;margin-top:18px">'
    + '<div><b>计时</b><div class="hint" style="margin-top:2px">记录每题耗时与总用时</div></div>'
    + '<button class="switch ' + (suanCfg.timed ? 'on' : '') + '" onclick="suanSetCfg(\'timed\',!' + suanCfg.timed + ')"><i></i></button></div>';
  html += '</div>';
  html += '<div class="suan-foot"><button class="cta" onclick="startSuan()">开始训练</button></div>';
  html += '</div>';
  app.innerHTML = html;
  syncChrome();
}
function suanSetCfg(key, val){
  suanCfg[key] = val;
  renderSuanCfg();
}

/* ---------- ③ 答题页 ---------- */
let suanState = null;
function startSuan(){
  const cfg = suanCfg, t = suanType(cfg.typeId);
  if (t.game === 'schulte'){
    suanState = { typeId: cfg.typeId, count: 1, diff: cfg.diff, timed: cfg.timed,
      schulte: true, size: cfg.diff === 'advanced' ? 5 : 4, start: Date.now(),
      grid: [], clicked: 0, mistakes: 0, done: false };
    const size = suanState.size, total = size * size;
    const arr = []; for (let i = 1; i <= total; i++) arr.push(i);
    for (let i = arr.length - 1; i > 0; i--){ const j = Math.floor(Math.random() * (i + 1)); const tmp = arr[i]; arr[i] = arr[j]; arr[j] = tmp; }
    suanState.grid = arr;
    store.set(K_SUAN_LAST, { typeId: cfg.typeId, difficulty: cfg.diff, count: 1, at: Date.now() });
    renderSuanRun();
    return;
  }
  const items = [];
  for (let i = 0; i < cfg.count; i++){
    let q, guard = 0;
    do { q = suanGenerate(cfg.typeId, cfg.diff); guard++; } while (guard < 30 && !q);
    items.push({ n: i + 1, stem: q.stem, answer: q.answer });
  }
  suanState = { typeId: cfg.typeId, count: cfg.count, diff: cfg.diff, timed: cfg.timed,
    items: items, answers: {}, times: {}, idx: 0, start: Date.now(), qStart: Date.now() };
  store.set(K_SUAN_LAST, { typeId: cfg.typeId, difficulty: cfg.diff, count: cfg.count, at: Date.now() });
  renderSuanRun();
}

function suanElapsed(){ return suanState ? Date.now() - suanState.start : 0; }
function renderSuanRun(){
  if (!suanState) return;
  view = 'suanRun';
  const st = suanState;
  if (st.schulte){ renderSchulte(); return; }
  const q = st.items[st.idx];
  hdTitle.textContent = suanTypeName(st.typeId);
  backBtn.style.display = 'grid'; setBtn.style.display = 'none'; sheetBtn.style.display = 'none';
  if (hdEl) hdEl.style.display = '';
  timerEl.style.display = st.timed ? 'flex' : 'none';
  timerEl.textContent = fmtClock(Math.floor(suanElapsed() / 1000));
  clearInterval(window.__suanTick);
  if (st.timed) window.__suanTick = setInterval(() => { if (suanState && !suanState.submitted) timerEl.textContent = fmtClock(Math.floor(suanElapsed() / 1000)); }, 500);
  const answered = Object.keys(st.answers).length;
  app.innerHTML = '<div class="page suan-run">'
    + '<div class="suan-progress"><b>第 ' + (st.idx + 1) + ' / ' + st.count + ' 题</b><span>' + (st.timed ? '计时中' : '不计时') + '</span></div>'
    + '<div class="pbar"><i style="width:' + Math.round(answered / st.count * 100) + '%"></i></div>'
    + '<div class="suan-q">' + esc(q.stem) + '</div>'
    + '<input id="suanInput" class="suan-input" autocomplete="off" inputmode="decimal" placeholder="填答案，回车下一题" value="' + esc(st.answers[st.idx] || '') + '" onkeydown="suanKey(event)">'
    + '<div class="suan-hintline">回车/下一题 进入下一题 · 最后一题回车直接交卷</div>'
    + '<div class="suan-runbar"><button class="btn ghost" onclick="suanSkip()">跳过</button>'
    + '<button class="btn primary" onclick="suanNext()">' + (st.idx === st.count - 1 ? '提交' : '下一题') + '</button></div>'
    + '<div class="hint" style="text-align:center;margin-top:8px">已答 ' + answered + ' / ' + st.count + ' · 未答完提交会先提示</div>'
    + '</div>';
  syncChrome();
  try { const el = document.getElementById('suanInput'); if (el && el.focus) el.focus(); } catch(e){}
}
function suanKey(e){
  if (e.key === 'Enter' || e.key === 'Tab'){ e.preventDefault(); suanNext(); }
}
function suanNext(){
  if (!suanState) return;
  const el = document.getElementById('suanInput');
  suanCommitAnswer(el ? el.value : '');
  if (suanState.idx >= suanState.count - 1){ suanTrySubmit(); return; }
  suanState.idx++; suanState.qStart = Date.now(); renderSuanRun();
}
function suanCommitAnswer(val){
  const st = suanState;
  if (!st) return;
  if (val !== undefined) st.answers[st.idx] = String(val).trim();
  if (st.times[st.idx] == null) st.times[st.idx] = Date.now() - st.qStart;
}
function suanSkip(){
  if (!suanState) return;
  suanCommitAnswer('');
  if (suanState.idx >= suanState.count - 1){ suanTrySubmit(); return; }
  suanState.idx++; suanState.qStart = Date.now(); renderSuanRun();
}
function suanTrySubmit(){
  const st = suanState;
  if (!st) return;
  const blank = st.count - Object.keys(st.answers).length;
  if (blank > 0 && !confirm('还有 ' + blank + ' 题未答，仍然提交？')) return;
  suanFinish();
}
function suanFinish(){
  const st = suanState;
  if (!st) return;
  clearInterval(window.__suanTick);
  const end = Date.now();
  const items = [];
  let right = 0, answered = 0;
  st.items.forEach((q, i) => {
    const user = st.answers[i] == null ? '' : st.answers[i];
    const ok = user !== '' && suanCheck(q, user);
    if (user !== '') answered++;
    if (ok) right++;
    items.push({ stem: q.stem, your: user, correct: String(q.answer), ms: st.times[i] || 0, ok: ok });
  });
  const sess = { sid: 's' + end, typeId: st.typeId, count: st.count, diff: st.diff,
    start: st.start, end: end, totalMs: end - st.start, right: right, answered: answered,
    items: items };
  suanSaveSession(sess);
  suanState = null;
  lastSuanSession = sess;
  renderSuanResult(sess);
}

/* 舒尔特方格 */
function renderSchulte(){
  const st = suanState;
  clearInterval(window.__suanTick);
  hdTitle.textContent = '舒尔特方格';
  backBtn.style.display = 'grid'; setBtn.style.display = 'none'; sheetBtn.style.display = 'none';
  timerEl.style.display = 'flex'; timerEl.textContent = fmtClock(Math.floor(suanElapsed() / 1000));
  window.__suanTick = setInterval(() => { if (suanState && !suanState.done) timerEl.textContent = fmtClock(Math.floor(suanElapsed() / 1000)); }, 500);
  let cells = '';
  st.grid.forEach(n => {
    cells += '<button class="sch-cell ' + (n <= st.clicked ? 'done' : '') + '" onclick="schClick(' + n + ')">' + (n <= st.clicked ? '✓' : n) + '</button>';
  });
  app.innerHTML = '<div class="page suan-run">'
    + '<div class="suan-progress"><b>按 1 → ' + (st.size * st.size) + ' 顺序点击</b><span>失误 ' + st.mistakes + ' 次</span></div>'
    + '<div class="sch-grid" style="grid-template-columns:repeat(' + st.size + ',1fr)">' + cells + '</div>'
    + '<div class="hint" style="text-align:center;margin-top:14px">点错会记一次失误，点完自动出成绩</div>'
    + '</div>';
  syncChrome();
}
function schClick(n){
  const st = suanState;
  if (!st || st.done) return;
  if (n === st.clicked + 1){ st.clicked = n; }
  else { st.mistakes++; toast('点错啦，按顺序来'); }
  if (st.clicked >= st.size * st.size){
    st.done = true;
    const end = Date.now();
    const ms = end - st.start;
    const sess = { sid: 's' + end, typeId: 'schulte', count: 1, diff: st.diff,
      start: st.start, end: end, totalMs: ms, right: 1, answered: 1,
      items: [{ stem: st.size + '×' + st.size + ' 舒尔特方格（失误 ' + st.mistakes + ' 次）', your: '完成', correct: '完成', ms: ms, ok: true }] };
    suanSaveSession(sess);
    suanState = null;
    lastSuanSession = sess;
    renderSuanResult(sess);
    return;
  }
  renderSchulte();
}

/* ---------- ④ 成绩单 ---------- */
let lastSuanSession = null;
function renderSuanResult(sess){
  view = 'suanResult';
  hdTitle.textContent = '成绩单';
  backBtn.style.display = 'grid'; setBtn.style.display = 'none'; sheetBtn.style.display = 'none'; timerEl.style.display = 'none';
  const acc = sess.answered ? Math.round(sess.right / sess.answered * 100) : 0;
  const wrong = sess.answered - sess.right;
  let html = '<div class="page" style="padding-top:10px">';
  html += '<div class="suan-score"><div class="ss-big">' + acc + '<span>%</span></div>'
    + '<div class="ss-sub">' + suanTypeName(sess.typeId) + ' · ' + sess.count + ' 题</div>'
    + '<div class="ss-grid">'
    + '<div><b>' + sess.count + '</b><span>题数</span></div>'
    + '<div><b style="color:var(--ok)">' + sess.right + '</b><span>正确</span></div>'
    + '<div><b style="color:var(--bad)">' + wrong + '</b><span>错误</span></div>'
    + '<div><b>' + suanFmtSec(sess.totalMs) + '</b><span>总耗时</span></div>'
    + '<div><b>' + suanFmtSec(sess.totalMs / Math.max(1, sess.count)) + '</b><span>平均每题</span></div>'
    + '</div></div>';
  html += '<div class="sec-head"><b>逐题复盘</b><span>红底为错题</span></div>';
  sess.items.forEach((it, i) => {
    html += '<div class="suan-review ' + (it.ok ? '' : 'bad') + '">'
      + '<div class="sr-top"><b>第 ' + (i + 1) + ' 题</b><span>' + (it.ms ? suanFmtSec(it.ms) : '') + '</span></div>'
      + '<div class="sr-stem">' + esc(it.stem) + '</div>'
      + '<div class="sr-ans">你的答案：<b>' + (it.your || '未答') + '</b> ｜ 正确答案：<b>' + esc(it.correct) + '</b></div>'
      + '</div>';
  });
  html += '<div class="suan-foot" style="display:flex;gap:10px">'
    + '<button class="btn primary" onclick="suanAgain()">再来一组</button>'
    + '<button class="btn ghost" onclick="renderSuanAbility()">查看能力趋势</button></div>';
  html += '<div style="text-align:center;margin-top:10px"><button class="link-btn" onclick="renderSuanHome()">返回速算首页</button></div>';
  html += '</div>';
  app.innerHTML = html;
  syncChrome();
}
function suanAgain(){
  const s = lastSuanSession;
  if (!s) { renderSuanHome(); return; }
  suanCfg = { typeId: s.typeId, count: s.count, diff: s.diff, timed: true };
  startSuan();
}

/* ---------- ⑤ 速算能力详情 ---------- */
let suanAbilityFrom = 'profile';
function renderSuanAbility(){
  view = 'suanAbility';
  hdTitle.textContent = '速算能力';
  backBtn.style.display = 'grid'; setBtn.style.display = 'none'; sheetBtn.style.display = 'none'; timerEl.style.display = 'none';
  const a7 = suanAgg(7), a30 = suanAgg(30);
  let html = '<div class="page" style="padding-top:10px">';
  html += '<div class="panel"><b>近 7 天</b><div class="fstats" style="margin-top:10px">'
    + '<div><b>' + a7.sessions + '</b><span>训练次数</span></div>'
    + '<div><b>' + (a7.questions ? a7.acc + '%' : '—') + '</b><span>平均准确率</span></div>'
    + '<div><b>' + (a7.avgMs ? suanFmtSec(a7.avgMs) : '—') + '</b><span>平均每题</span></div></div></div>';
  html += '<div class="panel"><b>近 30 天</b><div class="fstats" style="margin-top:10px">'
    + '<div><b>' + a30.sessions + '</b><span>训练次数</span></div>'
    + '<div><b>' + (a30.questions ? a30.acc + '%' : '—') + '</b><span>平均准确率</span></div>'
    + '<div><b>' + (a30.avgMs ? suanFmtSec(a30.avgMs) : '—') + '</b><span>平均每题</span></div></div></div>';

  const list = Object.keys(SUAN_TYPES).filter(id => SUAN_TYPES[id].game !== 'schulte').map(id => {
    const st = suanTypeStat(id, 30), t = SUAN_TYPES[id];
    return { id: id, name: t.name, st: st };
  }).filter(x => x.st);
  html += '<div class="sec-head"><b>按题型</b><span>准确率 / 平均耗时</span></div>';
  if (!list.length){
    html += '<div class="empty">还没有训练数据，先去练几组吧</div>';
  } else {
    list.forEach(x => {
      html += '<div class="suan-bar-row"><div class="sb-name">' + x.name + '</div>'
        + '<div class="sb-track"><i style="width:' + x.st.acc + '%"></i></div>'
        + '<div class="sb-val">' + x.st.acc + '% · ' + suanFmtSec(x.st.avgMs) + '</div></div>';
    });
    let weak = null;
    list.forEach(x => { if (!weak || x.st.acc < weak.st.acc || (x.st.acc === weak.st.acc && x.st.avgMs > weak.st.avgMs)) weak = x; });
    if (weak) html += '<div class="weak-card"><span class="wico">⚡</span><span class="wt"><b>' + weak.name + (weak.st.acc < 80 ? '准确率偏低' : '平均耗时偏高') + '</b><span>近 30 天 ' + weak.st.n + ' 题，建议再练 10 题</span></span>'
      + '<button class="weak-btn" onclick="openSuanCfg(\'' + weak.id + '\')">练 10 题</button></div>';
  }

  // 最近 7 天趋势（准确率）
  const days = [];
  for (let i = 6; i >= 0; i--){
    const from = new Date(); from.setHours(0,0,0,0); from.setDate(from.getDate() - i);
    const to = from.getTime() + 86400000;
    const list2 = suanData().sessions.filter(s => s.end >= from.getTime() && s.end < to);
    const q = list2.reduce((n, s) => n + (s.answered || 0), 0);
    const r = list2.reduce((n, s) => n + (s.right || 0), 0);
    days.push({ label: '一二三四五六日'[new Date(from).getDay() === 0 ? 6 : new Date(from).getDay() - 1],
      acc: q ? Math.round(r / q * 100) : 0, q: q });
  }
  const maxAcc = Math.max.apply(null, days.map(x => x.acc).concat([100]));
  html += '<div class="sec-head"><b>近 7 天准确率</b><span>按天</span></div><div class="chart">';
  days.forEach(d => {
    const h = Math.max(6, Math.round(d.acc / maxAcc * 100));
    html += '<div class="bar"><i style="height:' + h + '%;opacity:' + (d.q ? 1 : .3) + '"></i><span>' + d.label + '</span></div>';
  });
  html += '</div>';
  html += '<div class="suan-foot"><button class="cta" onclick="renderSuanHome()">去练一组</button></div>';
  html += '</div>';
  app.innerHTML = html;
  syncChrome();
}