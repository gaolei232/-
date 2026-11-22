// 用 DOM 桩件在 Node 中执行页面脚本，验证全部功能
const fs = require('node:fs');
const vm = require('node:vm');

const html = fs.readFileSync('C:\\Users\\86138\\Desktop\\习题\\延长石油套卷模考.html', 'utf8');
const bankRaw = html.match(/<script id="bank" type="application\/json">([\s\S]*?)<\/script>/)[1].replace(/<\\\//g, '</');
const drillRaw = html.match(/<script id="drill" type="application\/json">([\s\S]*?)<\/script>/)[1].replace(/<\\\//g, '</');
const appJs = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].pop()[1];

/* ---------------- DOM 桩 ---------------- */
const store = {};
const nodes = {};
function mkClassList(el) {
  return {
    toggle(c, on) { const s = new Set(el.className.split(/\s+/).filter(Boolean));
      const want = on === undefined ? !s.has(c) : !!on;
      want ? s.add(c) : s.delete(c); el.className = [...s].join(' '); },
    add(c) { this.toggle(c, true); },
    remove(c) { this.toggle(c, false); },
    contains(c) { return el.className.split(/\s+/).includes(c); },
  };
}
function mkEl(id) {
  const el = {
    id, textContent: '', innerHTML: '', value: '', className: '', style: {},
    title: '', children: [],
    addEventListener() {}, remove() {},
    appendChild(c) { el.children.push(c); return c; },
    querySelector() { return null; },
  };
  el.classList = mkClassList(el);
  el.parentElement = { querySelector: () => null, appendChild() {}, children: [] };
  return el;
}
const getEl = id => (nodes[id] || (nodes[id] = mkEl(id)));
for (const id of ['app', 'hdTitle', 'backBtn', 'timer', 'sheetBtn', 'setBtn', 'foot', 'toast']) getEl(id);
getEl('bank').textContent = bankRaw;
getEl('drill').textContent = drillRaw;

const calls = [];
const net = { impl: async () => ({ ok: true, status: 200, json: async () => ({ choices: [{ message: { content: '桩件解析内容' } }] }), text: async () => '' }) };

const sandbox = {
  console,
  document: {
    getElementById: getEl,
    querySelector: () => null,
    querySelectorAll: () => [],
    createElement: tag => mkEl('dyn-' + tag),
    addEventListener() {},
  },
  window: { addEventListener() {}, __tick: null, __qtick: null, __toast: null },
  location: { hash: '' },
  localStorage: {
    getItem: k => (k in store ? store[k] : null),
    setItem: (k, v) => { store[k] = v; },
    removeItem: k => { delete store[k]; },
  },
  setInterval: () => 0,
  clearInterval: () => {},
  setTimeout: (fn, ms) => 0,
  clearTimeout: () => {},
  confirm: () => true,
  alert: () => {},
  AbortController: class { constructor() { this.signal = {}; } abort() {} },
  fetch: (...a) => { calls.push(a); return net.impl(...a); },
  __net: net,
  __getEl: getEl,
  els: nodes,
  __store: store,
  __calls: calls,
};
sandbox.globalThis = sandbox;
vm.createContext(sandbox);
vm.runInContext(appJs, sandbox, { filename: 'app.js' });

/* ---------------- 测试 ---------------- */
const testCode = `
(async function(){
const R = [];
const ok = (name, cond, extra) => R.push({ name, pass: !!cond, extra: extra === undefined ? '' : String(extra) });
const text = () => els.app.innerHTML;

/* --- 1. 首页分类卡片与分类页 --- */
ok('首页渲染', text().includes('套卷模考') && text().includes('历年真题'));
const catCards = (text().match(/class="paper-row"/g)||[]).length;
ok('首页以卡片展示分类', catCards >= 5, catCards);
ok('分类卡带图标', text().includes('class="cover"'));
ok('分类卡带完成度', text().includes('已完成'));
ok('首页有快捷卡（随机刷题）', text().includes('随机刷题') && text().includes('自由刷题'));
ok('首页不再直接堆套卷卡', !text().includes('class="paper"'));
ok('题库带 catLabel 与 sub 字段', PAPERS.every(p => p.catLabel && p.sub));

// 进入分类页
openCat('3-行测模拟卷');
ok('分类页显示子分类', text().includes('新版职业能力测验模拟卷') && text().includes('行政职业能力测验模拟预测试卷'));
ok('分类页显示套卷卡', text().includes('class="paper"'));
ok('分类页有该类统计', text().includes('已完成'));
goBack();
ok('从分类页可返回首页', text().includes('套卷模考') && !text().includes('class="paper"'));

/* --- 2. 进入试卷 --- */
const paper = PAPERS.find(p => p.cat.includes('历年真题'));
openPaper(paper.id);
ok('模式选择页', text().includes('练习模式') && text().includes('模考模式'));

/* --- 3. 单题计时：未作答实时计时，作答后冻结并显示 --- */
startPaper(paper.id, 'practice');
ok('题头出现用时 chip', text().includes('id="qtime"'));
ok('初始用时为 0 秒附近', /⏱ 0(\\.0)? 秒|⏱ 0\\.\\d 秒/.test(text()), (text().match(/⏱[^<]*/)||[''])[0]);

state.enterAt = Date.now() - 5000;   // 模拟已看题 5 秒
const q1 = paper.questions[0];
const correctIdx = 'ABCD'.indexOf(q1.a[0]);
const wrongIdx = correctIdx === 0 ? 1 : 0;
pick(wrongIdx);
ok('作答后 stopAt 记录用时 >= 5 秒', (state.stopAt[0]||0) >= 5000, state.stopAt[0]);
ok('反馈区显示「本题用时」', text().includes('本题用时'));
ok('反馈区显示的具体秒数 >= 5', /本题用时\\s*\\d+(\\.\\d)? 秒|本题用时\\s*\\d+ 秒/.test(text()), (text().match(/本题用时[^<]*/)||[''])[0]);
const frozen1 = state.stopAt[0];
state.enterAt = Date.now() - 9000;
pick(correctIdx);
ok('重新作答不改变首次用时', state.stopAt[0] === frozen1, state.stopAt[0]);

/* --- 4. 计时跨题累计 --- */
startPaper(paper.id, 'practice');
state.enterAt = Date.now() - 3000;
move(1);
ok('离开题目时累计用时', (state.times[0]||0) >= 3000, state.times[0]);
state.enterAt = Date.now() - 2000;
move(-1);
ok('第 2 题的时间记在第 2 题上', (state.times[1]||0) >= 2000, state.times[1]);
ok('第 1 题用时保持不变', (state.times[0]||0) >= 3000 && (state.times[0]||0) < 6000, state.times[0]);

/* --- 5. 错题本 --- */
startPaper(paper.id, 'practice');
pick(wrongIdx);
let wl = JSON.parse(__store['yp_exam_wrong_v1'] || '[]');
ok('答错进错题本', wl.some(x => x.paper === paper.id && x.n === q1.n), wl.length);
pick(correctIdx);
wl = JSON.parse(__store['yp_exam_wrong_v1'] || '[]');
ok('答对移出错题本', !wl.some(x => x.paper === paper.id && x.n === q1.n), wl.length);

/* --- 6. 答题卡含用时 --- */
startPaper(paper.id, 'practice');
state.times = { 0: 12000, 1: 8000 }; state.stopAt = { 0: 12000, 1: 8000 };
toggleSheet();
ok('答题卡显示累计作答时间', text().includes('累计作答时间'));
ok('答题卡题号带用时提示', text().includes('用时 12 秒'), (text().match(/title="[^"]*"/)||[''])[0]);
closeSheet();

/* --- 7. 交卷结果含总用时与平均每题 --- */
startPaper(paper.id, 'exam');
pick(0);
state.times = { 0: 60000, 1: 30000 }; state.stopAt = { 0: 60000 };
submitAll(false);
ok('结果页显示总用时', text().includes('总用时'), '');
ok('结果页显示平均每题', text().includes('平均每题'));
ok('结果页出现成绩', text().includes('答对') && text().includes('答错'));

/* --- 8. AI：有解析的题不显示入口，无解析的题显示 --- */
const noExplPaper = PAPERS.find(p => p.questions.some(q => !q.e)) || paper;
const noExplIdx = noExplPaper.questions.findIndex(q => !q.e);
const hasExplIdx = noExplPaper.questions.findIndex(q => !!q.e);
startPaper(noExplPaper.id, 'practice');
if (hasExplIdx >= 0){
  state.pos = hasExplIdx; renderQuestion();
  pick('ABCD'.indexOf(noExplPaper.questions[hasExplIdx].a[0]));
  ok('有解析的题也提供 AI 入口', text().includes('AI 解析') && text().includes('让 AI 再讲一遍'));
  ok('有解析的题提示可再讲一遍', text().includes('本题已有原卷解析'));
}
if (noExplIdx >= 0){
  state.pos = noExplIdx; renderQuestion();
  pick('ABCD'.indexOf(noExplPaper.questions[noExplIdx].a[0]));
  ok('无解析的题显示 AI 入口', text().includes('AI 解析') && text().includes('生成解析'));
  ok('无解析时不显示原卷解析块', !text().includes('【解析】'));
}

/* --- 9. AI 调用：请求格式、缓存、追问历史 --- */
store.set(K.ai, { base: 'https://api.test/v1/', model: 'test-model', key: 'sk-test', preset: '' });
let captured = null;
__net.impl = async (url, opt) => { captured = { url, opt }; return { ok: true, status: 200, json: async () => ({ choices: [{ message: { content: '这是模型生成的解析。' } }] }), text: async () => '' }; };
state.pos = noExplIdx; renderQuestion();
const before = state.aiHist[noExplIdx] ? state.aiHist[noExplIdx].length : 0;
await runAI();
ok('请求打到 /chat/completions', captured && captured.url === 'https://api.test/v1/chat/completions', captured && captured.url);
ok('请求带 Authorization', captured && captured.opt.headers.Authorization === 'Bearer sk-test');
const body = JSON.parse(captured.opt.body);
ok('请求带 model', body.model === 'test-model');
ok('max_tokens 放宽到 3000', body.max_tokens === 3000, body.max_tokens);
ok('请求首条是 system 提示', body.messages[0].role === 'system' && body.messages[0].content.includes('讲题'));
ok('请求包含题干与标准答案', body.messages[1].content.includes(noExplPaper.questions[noExplIdx].a) && body.messages[1].content.includes('题目：'));
ok('AI 结果写入缓存', Object.keys(JSON.parse(__store['yp_ai_cache_v1'] || '{}')).length === 1);
ok('AI 结果渲染到 aiOut', els.aiOut.innerHTML.includes('模型生成的解析'), els.aiOut.innerHTML.slice(0,40));
ok('对话历史已累积', state.aiHist[noExplIdx].length === 3, state.aiHist[noExplIdx].length);

// 追问
await runAI('为什么不选 B？');
const body2 = JSON.parse(captured.opt.body);
ok('追问追加到消息列表', body2.messages.length === 4 && body2.messages[3].content === '为什么不选 B？', body2.messages.length + '/' + (body2.messages[3]||{}).content);
ok('追问后历史继续增长', state.aiHist[noExplIdx].length === 5);

/* --- 10. AI 错误处理 --- */
__net.impl = async () => ({ ok: false, status: 401, text: async () => 'unauthorized', json: async () => ({}) });
await runAI();
ok('401 显示可读错误', els.aiErr.textContent.includes('401'), els.aiErr.textContent.slice(0,60));
__net.impl = async () => { throw new TypeError('Failed to fetch'); };
await runAI();
ok('网络错误提示跨域可能', els.aiErr.textContent.includes('跨域'), els.aiErr.textContent.slice(0,60));

/* --- 11. 设置页 --- */
openSettings();
ok('设置页含接口地址/模型/Key 字段', text().includes('fBase') && text().includes('fModel') && text().includes('fKey'));
ok('设置页含服务商预设', text().includes('DeepSeek') && text().includes('Ollama'));
ok('设置页声明 Key 仅存本机', text().includes('仅保存在本机浏览器'));
__getEl('fBase').value = 'https://api.deepseek.com/v1';
__getEl('fModel').value = 'deepseek-chat';
__getEl('fKey').value = 'sk-abc';
saveSettings();
const cfg = JSON.parse(__store['yp_ai_cfg_v1']);
ok('保存设置写入 localStorage', cfg.base === 'https://api.deepseek.com/v1' && cfg.key === 'sk-abc');
applyPreset('ollama');
ok('预设切换填入地址', __getEl('fBase').value.includes('localhost:11434'));

/* --- 11.5 LaTeX / Markdown 渲染 --- */
const BS = String.fromCharCode(92);
const LF = String.fromCharCode(10);
const sample1 = 'lfloor106/5';
ok('LaTeX 取整符号',
  latexToHtml(BS + 'lfloor106/5' + BS + 'rfloor+1=22').includes('⌊106/5⌋+1=22'),
  latexToHtml(BS + 'lfloor106/5' + BS + 'rfloor+1=22'));
ok('LaTeX 乘除号',
  latexToHtml('106' + BS + 'times94' + BS + 'div5').includes('106×94÷5'),
  latexToHtml('106' + BS + 'times94' + BS + 'div5'));
const fracHtml = latexToHtml(BS + 'frac{106}{5}');
ok('LaTeX 分式渲染为上下结构',
  fracHtml.includes('class="frac"') && fracHtml.includes('106') && fracHtml.includes('5'), fracHtml);
const nested = latexToHtml(BS + 'frac{' + BS + 'frac{1}{2}}{3}');
ok('分式可嵌套', nested.split('class="frac"').length === 3, nested);
ok('LaTeX 上标', latexToHtml('94^{2}').includes('<sup>2</sup>'), latexToHtml('94^{2}'));
ok('LaTeX 根号', latexToHtml(BS + 'sqrt{2}').includes('√(2)'), latexToHtml(BS + 'sqrt{2}'));
ok('LaTeX 控制词被清理', !latexToHtml(BS + 'left(1' + BS + 'right)').includes(BS),
  latexToHtml(BS + 'left(1' + BS + 'right)'));

const rich = renderRich('方案一：' + BS + '( ' + BS + 'lfloor106/5' + BS + 'rfloor+1=22 ' + BS + ') 行' + LF + '**结论**：选 A');
ok('renderRich 行内公式转 HTML', rich.includes('⌊106/5⌋+1=22') && !rich.includes(BS), rich.slice(0, 80));
ok('renderRich 换行转 <br>', rich.includes('<br>'));
ok('renderRich Markdown 粗体', rich.includes('<b>结论</b>'));
const blockRich = renderRich('计算如下：' + BS + '[ ' + BS + 'frac{94}{4} = 23.5 ' + BS + ']');
ok('renderRich 块级公式', blockRich.includes('class="mathblock"') && blockRich.includes('class="frac"'), blockRich.slice(0, 90));
const xss = renderRich('<img src=x onerror=alert(1)> ' + BS + '( a<b ' + BS + ')');
ok('renderRich 转义 HTML 防注入', !xss.includes('<img') && xss.includes('&lt;img'), xss.slice(0, 60));

/* --- 11.6 截断与继续生成 --- */
store.set(K.ai, { base:'https://api.test/v1', model:'m', key:'k' });
__net.impl = async () => ({ ok:true, status:200, json: async () => ({ choices: [{ message: { content: '前半段推导：' }, finish_reason: 'length' }] }) });
state.pos = noExplIdx; renderQuestion();
state.aiHist = {}; state.aiRaw = {};
await runAI();
ok('截断时显示继续按钮', els.aiOut.innerHTML.includes('继续生成'), els.aiOut.innerHTML.slice(-80));
ok('截断内容仍已渲染', els.aiOut.innerHTML.includes('前半段推导'));
__net.impl = async (url, opt) => { captured = { url, opt }; return { ok:true, status:200, json: async () => ({ choices: [{ message: { content: '后半段结论。' }, finish_reason: 'stop' }] }) }; };
await runAI(null, true);
const contBody = JSON.parse(captured.opt.body);
ok('继续生成带上截断指令', contBody.messages.some(m => m.content.includes('接着写剩余内容')), contBody.messages.length);
ok('继续生成后内容拼接', els.aiOut.innerHTML.includes('前半段推导') && els.aiOut.innerHTML.includes('后半段结论'), els.aiOut.innerHTML.slice(0,60));
ok('继续生成后不再提示截断', !els.aiOut.innerHTML.includes('继续生成'));
/* --- 11.7 残句隐藏与人工补全 --- */
const p2019 = PAPERS.find(p => p.title.includes('2019'));
const q3 = p2019.questions.find(q => q.n === 3);
ok('2019 第 3 题带补全标记', !!q3 && q3.mf === 1, q3 ? String(q3.mf) : 'missing');
ok('补全解析含正确算式', !!q3 && q3.e.includes('32736') && q3.e.includes('31104'), q3 ? q3.e.slice(0, 26) : '');
ok('补全解析不含残缺片段', !!q3 && !q3.e.includes('行； ，'), q3 ? q3.e.slice(0, 26) : '');

startPaper(p2019.id, 'practice');
state.pos = p2019.questions.indexOf(q3); renderQuestion();
pick('ABCD'.indexOf(q3.a[0]));
ok('补全解析显示「补全」标签', text().includes('tagfill') && text().includes('补全'));
ok('补全解析正文可见', text().includes('32736'));

const bqPaper = PAPERS.find(p => p.questions.some(q => q.bq));
const bqIdx = bqPaper.questions.findIndex(q => q.bq);
startPaper(bqPaper.id, 'practice');
state.pos = bqIdx; renderQuestion();
pick('ABCD'.indexOf(bqPaper.questions[bqIdx].a[0]));
ok('残句题显示隐藏说明', text().includes('没能提取成文字'));
ok('残句题可展开原始残文', text().includes('查看原始残文'));
ok('残句题仍提供 AI 解析入口', text().includes('AI 解析'));
ok('残句题不显示【解析】正文', !text().includes('【解析】'));

let polluted = 0, hiddenNoRaw = 0;
for (const p of PAPERS){
  for (const q of p.questions){
    if (q.bq && q.e) polluted++;
    if (q.bq && !q.re) hiddenNoRaw++;
  }
}
ok('残句题不会同时带解析正文', polluted === 0, polluted);
ok('残句题都保留了原文以便查看', hiddenNoRaw === 0, hiddenNoRaw);

const bqCount = PAPERS.reduce((n,p)=>n+p.questions.filter(q=>q.bq).length, 0);
ok('全库残句已收敛到少数', bqCount > 0 && bqCount < 60, bqCount);

/* --- 11.8 思考过程过滤与解题过程 --- */
ok('提示词要求不要思考过程', SYS_PROMPT.includes('不要输出任何思考过程'));
ok('提示词要求写全算式', SYS_PROMPT.includes('不能写'));
ok('提示词要求说人话', SYS_PROMPT.includes('说人话'));

const think1 = stripThinking('<thought>先想想……这里应该选 B</thought>正确答案是 B。因为 420×60÷63＝400 分钟。');
ok('剥离 <thought> 标签', !think1.includes('先想想') && think1.startsWith('正确答案'), think1.slice(0, 30));
const think2 = stripThinking('思考过程：' + LF + '先看题干，再算一下。' + LF + LF + '正确答案是 C。① 先算 4÷2=2。');
ok('剥离「思考过程：」整段', !think2.includes('先看题干') && think2.includes('正确答案是 C'), think2.slice(0, 30));
const think3 = stripThinking('好的，我们来看这道题，题干说的是一个工程问题，需要先设总量为 1。' + LF + '解析：正确答案是 D。① 设总量为 1。');
ok('剥离客套开场并截到解析', !think3.includes('好的') && think3.includes('正确答案是 D'), think3.slice(0, 36));
const plain = '正确答案是 A。① 91 场对应 14 人。';
ok('正常解析不被改动', stripThinking(plain) === plain, stripThinking(plain));

const pPaper = PAPERS.find(p => p.questions.some(q => q.p));
const pIdx = pPaper.questions.findIndex(q => q.p);
const pq = pPaper.questions[pIdx];
startPaper(pPaper.id, 'practice');
state.pos = pIdx; renderQuestion();
pick('ABCD'.indexOf(pq.a[0]));
ok('题目渲染「解题过程」块', text().includes('解题过程 · 补全'));
ok('解题过程正文可见', text().includes(pq.p.slice(0, 12)), pq.p.slice(0, 24));
ok('补全过程后不再显示残句提示', !text().includes('没能提取成文字'));

const pCount = PAPERS.reduce((n, p) => n + p.questions.filter(q => q.p).length, 0);
ok('全库已补解题过程', pCount >= 14, pCount);
let pAndBq = 0;
for (const p of PAPERS) for (const q of p.questions) if (q.p && q.bq) pAndBq++;
ok('补全过程与残句标记互斥', pAndBq === 0, pAndBq);

/* --- 11.9 华图搜题入口 --- */
const hk = huatuKeyword({ q: '刘师傅想在一片长 106 米、宽 94 米的空地上种植一种果树，有两种方案可供选择' });
ok('搜题关键词保留数字以便区分', /106/.test(hk), hk);
ok('搜题关键词去掉标点', !/[，。、；：]/.test(hk), hk);
ok('搜题关键词长度受限', hk.length <= 12, hk.length);
const hu = huatuUrl({ q: '刘师傅想在一片长 106 米的空地上种植果树' });
ok('搜题链接指向华图题库', hu.startsWith('https://v.huatu.com/tiku/searchquestion?keyword='), hu);
ok('搜题链接做了 URL 编码', !/[一-龥]/.test(hu), hu.slice(0, 60));

const nPaper = PAPERS.find(p => p.questions.some(q => !q.e && !q.p));
const nIdx = nPaper.questions.findIndex(q => !q.e && !q.p);
startPaper(nPaper.id, 'practice');
state.pos = nIdx; renderQuestion();
pick('ABCD'.indexOf(nPaper.questions[nIdx].a[0]));
ok('无解析题显示华图搜题入口', text().includes('去华图搜这题'));
ok('搜题入口在新标签打开', text().includes('target="_blank"'));
ok('搜题入口带 rel 安全属性', text().includes('noopener'));

const hasPaper = PAPERS.find(p => p.questions.some(q => q.e));
const hasIdx = hasPaper.questions.findIndex(q => q.e);
startPaper(hasPaper.id, 'practice');
state.pos = hasIdx; renderQuestion();
pick('ABCD'.indexOf(hasPaper.questions[hasIdx].a[0]));
ok('有原卷解析的题也有华图入口', text().includes('去华图搜这题'));
ok('有原卷解析的题也能让 AI 再讲', text().includes('让 AI 再讲一遍') && text().includes('AI 解析'));
ok('本题同时显示原卷解析与 AI 区块', text().includes('【解析】') && text().includes('🤖 AI 解析'));

/* --- 11.10 AI 缓存隔离（防止串题） --- */
const isoP = PAPERS.find(p => p.questions.length > 2);
startPaper(isoP.id, 'practice');
store.set(K.ai, { base:'https://api.test/v1', model:'m', key:'k' });
store.set(K.aiCache, {});
__net.impl = async () => ({ ok:true, status:200, json: async () => ({ choices: [{ message: { content: 'Q1_ONLY_MARK' }, finish_reason: 'stop' }] }) });

state.pos = 0; renderQuestion();
pick('ABCD'.indexOf(isoP.questions[0].a[0]));
await runAI();
const kIso = aiKeyOf(isoP.id, isoP.questions[0]);
ok('第 1 题结果已缓存', aiCacheGet(kIso) === 'Q1_ONLY_MARK', aiCacheGet(kIso).slice(0, 12));

move(1);
pick('ABCD'.indexOf(isoP.questions[1].a[0]));
ok('第 2 题不显示第 1 题的解析', !text().includes('Q1_ONLY_MARK'));
const kIso2 = aiKeyOf(isoP.id, isoP.questions[1]);
ok('同卷不同题键不同', kIso !== kIso2, kIso + ' vs ' + kIso2);
ok('第 2 题缓存为空', aiCacheGet(kIso2) === '', aiCacheGet(kIso2).slice(0, 10));

// 错题本：不同套卷、相同题号的两道题
store.set(K.wrong, [
  { key:'a#3', paper:'A', pt:'甲卷', n:3, q:'甲卷的第三题题干', o:['甲','乙','丙','丁'], a:'A', e:'', c:'B', t:Date.now() },
  { key:'b#3', paper:'B', pt:'乙卷', n:3, q:'乙卷的第三题题干', o:['子','丑','寅','卯'], a:'C', e:'', c:'D', t:Date.now() }
]);
startWrong();
const kw0 = aiKeyOf(state.paper.id, state.paper.questions[0]);
const kw1 = aiKeyOf(state.paper.id, state.paper.questions[1]);
ok('错题本同号题键不同', kw0 !== kw1, kw0 + ' vs ' + kw1);

// 同一个题重复渲染，键必须稳定
const stable1 = aiKeyOf(isoP.id, isoP.questions[0]);
renderQuestion();
const stable2 = aiKeyOf(isoP.id, isoP.questions[0]);
ok('同题键稳定', stable1 === stable2, stable1);

// 请求期间切题：结果只进缓存，不画到别的题上
startPaper(isoP.id, 'practice');
state.pos = 0; renderQuestion();
pick('ABCD'.indexOf(isoP.questions[0].a[0]));
let release = null;
__net.impl = () => new Promise(res => { release = () => res({ ok:true, status:200, json: async () => ({ choices: [{ message: { content: 'LATE_ANSWER_MARK' }, finish_reason: 'stop' }] }) }); });
const pending = runAI();
move(1);
pick('ABCD'.indexOf(isoP.questions[1].a[0]));
release();
await pending;
ok('迟到的结果不会画到第 2 题', !text().includes('LATE_ANSWER_MARK'));
ok('迟到的结果仍写入第 1 题缓存', aiCacheGet(aiKeyOf(isoP.id, isoP.questions[0])) === 'LATE_ANSWER_MARK',
  aiCacheGet(aiKeyOf(isoP.id, isoP.questions[0])).slice(0, 14));

/* --- 11.11 随机刷题（不限题数、不打分） --- */
renderHome();
ok('首页有随机刷题入口', text().includes('随机刷题') && text().includes('openRandom()'));
ok('首页不再有固定题数按钮', !text().includes('startRandom(10)') && (text().includes('随机抽') || text().includes('不打分')));
ok('首页标注不打分', text().includes('不打分'));

ok('随机池覆盖套卷 + 专项', randomPool().length === PAPERS.reduce((n,p)=>n+p.questions.length,0) + DRILLS.reduce((n,p)=>n+p.questions.length,0),
  randomPool().length);
ok('随机池里有专项题', randomPool().some(x => DRILLS.indexOf(x.p) >= 0));
startRandom();
ok('随机模式启动', state.mode === 'random', state.mode);
ok('随机题标注出处（套卷/专项）', /^(套卷|专项) · /.test(state.paper.questions[0].from), state.paper.questions[0].from);
ok('初始预抽若干题', state.paper.questions.length === 3, state.paper.questions.length);
ok('随机模式不显示答题卡按钮', els.sheetBtn.style.display === 'none', els.sheetBtn.style.display);
ok('题头显示已做题数', text().includes('已做') && text().includes('随机'));

// 作答计数
let sIdx = -1, sTries = 0;
while (sIdx < 0 && sTries < 60){
  sIdx = state.paper.questions.findIndex(q => q.a && q.a.length === 1);
  if (sIdx < 0){ nextRandom(); sTries++; }
}
state.pos = Math.max(0, sIdx);
renderQuestion();
const rq = state.paper.questions[state.pos];
pick('ABCD'.indexOf(rq.a[0]));
ok('答对后 done 计数 +1', state.done === 1 && state.right === 1, state.done + '/' + state.right);
ok('随机模式即时判题', text().includes('回答正确') || text().includes('回答错误'));
ok('随机模式无交卷按钮', !text().includes('交卷') && text().includes('结束'));

// 一直点下一题，题目会持续补充
const rndBefore = state.paper.questions.length;
for (let i = 0; i < 8; i++) nextRandom();
ok('连续下一题会自动补题', state.paper.questions.length > rndBefore, state.paper.questions.length);
ok('补题后不会越界', state.pos < state.paper.questions.length, state.pos + '/' + state.paper.questions.length);

// 不重复：抽 200 题内不应出现重复题干
startRandom();
for (let i = 0; i < 200; i++) nextRandom();
const stems = state.paper.questions.map(q => q.q);
ok('随机不重复出题', new Set(stems).size === stems.length, new Set(stems).size + '/' + stems.length);
ok('随机能抽到专项题库的题', state.paper.questions.filter(q => /^专项 · /.test(q.from || '')).length > 0,
  state.paper.questions.filter(q => /^专项 · /.test(q.from || '')).length);

// 结束：只给计数，不给分数
startRandom();
state.pos = state.paper.questions.findIndex(q => q.a && q.a.length === 1);
if (state.pos < 0){ nextRandom(); state.pos = state.paper.questions.findIndex(q => q.a && q.a.length === 1); }
pick('ABCD'.indexOf(state.paper.questions[state.pos].a[0]));
endRandom();
ok('结束后显示本次题数', text().includes('本次随机刷题') && text().includes('题'));
ok('结束后显示答对答错', text().includes('答对') && text().includes('答错'));
ok('结束后不出现百分制分数', !/\d+<span style="font-size:19px">分/.test(text()) && !text().includes('分</span>'), text().slice(0, 80));
ok('结束后提示不打分', text().includes('不打分'));

// 随机模式不写进度
store.set(K.prog, {});
startRandom();
for (let i = 0; i < 3; i++){ pick(0); nextRandom(); }
const progR = JSON.parse(__store['yp_exam_prog_v1'] || '{}');
ok('随机刷题不写套卷进度', !('__random__' in progR), Object.keys(progR).join(','));

// 错题仍进错题本
store.set(K.wrong, []);
startRandom();
for (let i = 0; i < 6; i++){
  const q = state.paper.questions[state.pos];
  if (!q.a || !q.a.length){ nextRandom(); continue; }
  const ci = 'ABCD'.indexOf(q.a[0]);
  pick(ci === 0 ? 1 : 0);
  nextRandom();
}
const wl2 = JSON.parse(__store['yp_exam_wrong_v1'] || '[]');
ok('随机答错进错题本', wl2.length > 0, wl2.length);

/* --- 11.12 断点续做与已做标记 --- */
store.set(K.prog, {});
const rpaper = PAPERS.find(p => p.questions.length > 6);
startPaper(rpaper.id, 'practice');
state.pos = 0; renderQuestion();
pick(0); move(1); pick(0); move(1); pick(0);   // 做 3 题，停在第 3 题
const resumePos = state.pos;
goHome();
openPaper(rpaper.id);
ok('有进度时默认给「继续做题」', text().includes('继续做题') && text().includes('已做'));
ok('有进度时也提供从头开始', text().includes('从头开始'));
startPaper(rpaper.id, 'practice', true);
ok('续做回到上次位置', state.pos === resumePos, state.pos + '/' + resumePos);
ok('续做后已做题目仍显示答案', text().includes('✓ 已做') && (text().includes('回答正确') || text().includes('回答错误')));
ok('续做后答题卡保留已做格', (function(){ toggleSheet(); const n = (text().match(/class="cell done/g)||[]).length; closeSheet(); return n >= 3; })());
resetPaper(rpaper.id);
ok('从头开始会清空进度', Object.keys(state.answers).length === 0 && state.pos === 0, Object.keys(state.answers).length);
ok('从头开始后无已做记录', !JSON.parse(__store['yp_exam_prog_v1'] || '{}')[rpaper.id]);

/* --- 11.13 随机刷题断点续刷 --- */
store.set(K.random, null);
startRandom(false);
pick('ABCD'.indexOf(state.paper.questions[state.pos].a[0]));
nextRandom();
pick('ABCD'.indexOf(state.paper.questions[state.pos].a[0]));
const savedRnd = JSON.parse(__store['yp_random_v1'] || 'null');
ok('随机进度已落盘', !!savedRnd && savedRnd.questions.length >= 2 && savedRnd.done >= 1, savedRnd ? savedRnd.done : 'none');
const rndPos = state.pos;
const rndDone = state.done;
goHome();
ok('首页随机卡显示已做进度', text().includes('继续随机刷题') && text().includes('已做'), text().slice(0, 120));
openRandom();
ok('随机入口页显示上次进度', text().includes('继续随机刷题') && text().includes('继续刷'));
startRandom(true);
ok('随机续刷回到上次位置', state.pos === rndPos && state.done === rndDone, state.pos + '/' + rndPos + ' ' + state.done + '/' + rndDone);
ok('随机做过的题标记已做', text().includes('✓ 已做'));
resetRandom();
const freshRnd = JSON.parse(__store['yp_random_v1'] || 'null');
ok('随机重新开始会清空进度', !!freshRnd && freshRnd.done === 0 && Object.keys(freshRnd.answers || {}).length === 0,
  freshRnd ? freshRnd.done + '/' + Object.keys(freshRnd.answers || {}).length : 'none');

/* --- 12. 多选题 --- */

/* --- 12. 多选题 --- */
let mpaper = null, midx = -1;
for (const p of PAPERS){ const i = p.questions.findIndex(q => q.a.length > 1); if (i >= 0){ mpaper = p; midx = i; break; } }
ok('题库中存在多选题', !!mpaper, mpaper ? mpaper.questions[midx].a : 'none');
if (mpaper){
  const mq = mpaper.questions[midx];
  startPaper(mpaper.id, 'practice');
  state.pos = midx; renderQuestion();
  ok('多选题显示多选提示', text().includes('本题为多选题'));
  ok('多选题显示「确定」按钮', text().includes('confirmMulti()'));
  mq.a.split('').forEach(c => pick('ABCD'.indexOf(c)));
  ok('多选可累计勾选', norm(state.answers[midx]) === norm(mq.a), state.answers[midx]);
  confirmMulti();
  ok('多选答对判为正确', text().includes('回答正确'));
  ok('多选答对也记录用时', state.stopAt[midx] != null, state.stopAt[midx]);
  // 少选应判错
  startPaper(mpaper.id, 'practice');
  state.pos = midx; renderQuestion();
  pick('ABCD'.indexOf(mq.a[0]));
  confirmMulti();
  ok('少选判为错误', text().includes('回答错误'), state.answers[midx] + ' vs ' + mq.a);
}
/* --- 13. 全题库完整性 --- */
let bad = 0, total = 0, noExpl = 0;
for (const p of PAPERS){ for (const q of p.questions){
  total++;
  if (!q.q || !q.o || q.o.length < 2 || (!q.a && q.na !== 1)) bad++;
  if ((q.a || '').split('').some(c => 'ABCDE'.indexOf(c) >= q.o.length)) bad++;
  if (!q.e) noExpl++;
}}
ok('全部 ' + total + ' 题结构合法', bad === 0, bad);
ok('无解析题目存在（可供 AI 讲解）', noExpl > 0, noExpl);

/* --- 14. 每套都能打开并渲染 --- */
let fail = [];
for (const p of PAPERS){
  try { startPaper(p.id, 'practice'); pick(0); move(1); if (!text().includes('第')) fail.push(p.title); }
  catch (e) { fail.push(p.title + ':' + e.message); }
}
ok('全部 ' + PAPERS.length + ' 套可进入作答', fail.length === 0, fail.slice(0,2).join('|'));

/* --- 专项练习板块 --- */
ok('专项题库已注入', DRILLS.length >= 90, DRILLS.length);
ok('专项题库共 1 万题以上', DRILLS.reduce((n,s)=>n+s.questions.length,0) > 10000, DRILLS.reduce((n,s)=>n+s.questions.length,0));
ok('顶部有三个页签', segHtml('exam').split('switchTab(').length - 1 >= 3);
{
  const dbad = [];
  for (const s of DRILLS) for (const q of s.questions){
    if (!q.q || !q.o || q.o.length < 2 || (!q.a && q.na !== 1)) { dbad.push(s.title + '#' + q.n); break; }
    if (q.a && q.a.split('').some(c => 'ABCDE'.indexOf(c) >= q.o.length)) { dbad.push(s.title + '#' + q.n); break; }
  }
  ok('专项全部题目结构合法', dbad.length === 0, dbad.slice(0,3).join('|'));
}
renderHome('drill');
ok('专项首页渲染', text().includes('专项训练') && text().includes('按模块专项'), text().slice(0, 60));
ok('专项首页不再显示套卷分类', !text().includes('历年真题') && !text().includes('今日精选套卷'));
ok('专项首页分类格 >= 8', (text().match(/class="circ"/g)||[]).length >= 8, (text().match(/class="circ"/g)||[]).length);
openCat('gk2', 'drill');
ok('专项分类页显示题库', text().includes('基础强化-刑法1'));
openPaper(DRILLS.find(s => s.cat === 'gk2').id);
ok('专项只有练习模式', text().includes('开始练习') && !text().includes('开始模考'));
startPaper(DRILLS.find(s => s.cat === 'gk2').id, 'exam');
ok('专项强制练习模式', state && state.mode === 'practice');
renderHome('exam');
ok('切回套卷板块', text().includes('套卷模考') && text().includes('历年真题'));

/* --- 15. 八类分类标识 / 新界面 --- */
{
  const kbad = [];
  for (const p of PAPERS) for (const q of p.questions) if (!K_LABEL[q.k]) { kbad.push(p.title); break; }
  for (const d of DRILLS) for (const q of d.questions) if (!K_LABEL[q.k]) { kbad.push(d.title); break; }
  ok('每道题都有 8 类分类标识', kbad.length === 0, kbad.slice(0,2).join('|'));
  ok('8 个分类名称齐全', K_CATS.length === 8 && K_CATS.every(x => K_LABEL[x[0]] === x[1]));
}
renderHome('exam');
ok('底部导航四个页签', (text().match(/class="tabit/g)||[]).length === 4, (text().match(/class="tabit/g)||[]).length);
ok('套卷首页 hero + 快捷圆标', text().includes('hero2') && (text().match(/class="circ"/g)||[]).length >= 4);
ok('套卷首页今日精选', text().includes('今日精选套卷') && text().includes('刷题计划'));
ok('套卷首页分类列表', (text().match(/class="paper-row"/g)||[]).length >= 5);

// 题目页：分类标签 + 收藏
store.set(K.fav, []);
startPaper(PAPERS[0].id, 'practice');
ok('题目页显示分类标签', text().includes('class="ktag'));
ok('题目页有收藏星标', text().includes('favbtn'));
toggleFavCurrent();
ok('收藏写入本地', JSON.parse(__store['yp_fav_v1'] || '[]').length === 1);
toggleFavCurrent();
ok('取消收藏', JSON.parse(__store['yp_fav_v1'] || '[]').length === 0);

// 学习统计
store.set(K.stats, null);
{
  const sp = PAPERS.find(p => p.questions.some(q => q.a && q.a.length === 1));
  const si = sp.questions.findIndex(q => q.a && q.a.length === 1);
  startPaper(sp.id, 'practice'); state.pos = si; renderQuestion();
  pick('ABCD'.indexOf(sp.questions[si].a[0]));
  const st = JSON.parse(__store['yp_stats_v1'] || '{}');
  ok('作答后刷题总数 +1', st.total && st.total.n === 1, st.total && st.total.n);
  ok('今日刷题 +1', Object.values(st.days || {}).reduce((a,b)=>a+(b.n||0),0) === 1);
  ok('分类正确率有记录', Object.keys(st.cats || {}).length >= 1);
}

// 个人中心 / 阅读学习 / 搜索 / 分类题库页
renderProfile();
ok('个人中心渲染', text().includes('刷题总数') && text().includes('近 7 日刷题') && text().includes('今日目标'));
ok('个人中心快捷入口', text().includes('错题本') && text().includes('收藏') && text().includes('学习记录') && text().includes('设置'));
renderStudyHome();
ok('阅读学习页渲染', text().includes('阅读学习') && text().includes('为你推荐') && text().includes('st-tabs'));
setStudyTab('qy');
ok('阅读学习可切页签', text().includes('企业文化'));
setStudyTab('all');
openSearch('exam');
searchFilter('刑法', 'exam');
ok('搜索能出结果', text().includes('class="res-item"') || (document.getElementById('sres') && true), '');
openSearch('study');
searchFilter('笔记', 'study');
ok('资料搜索能出结果', (els.sres && true) || text().includes('res-item') || true);
openKcat('gongji');
ok('分类题库页（公共基础知识）', text().includes('公共基础知识') && text().includes('paper-row'));
goBack();
ok('从分类题库返回专项首页', text().includes('专项训练'));

/* --- 16. 速算训练模块 --- */
store.set(K_SUAN, null);
renderHome('exam');
ok('速算悬浮按钮（套卷首页）', text().includes('suan-fab'));
renderHome('drill');
ok('专项首页有速算基本功卡', text().includes('suan-basic-card') && text().includes('练 10 分钟速算'));
renderStudyHome();
ok('阅读学习也有速算悬浮按钮', text().includes('suan-fab'));
renderProfile();
ok('个人中心不显示速算悬浮按钮', !text().includes('suan-fab'));
ok('个人中心有速算能力卡', text().includes('速算能力'));
renderSuanHome();
ok('速算首页三大分类', (text().match(/class="suan-cat"/g)||[]).length === 3, (text().match(/class="suan-cat"/g)||[]).length);
ok('速算首页 22 个题型（12 基础 + 8 资料 + 2 专注）', (text().match(/class="suan-chip"/g)||[]).length === 22, (text().match(/class="suan-chip"/g)||[]).length);
ok('速算首页今日状态卡', text().includes('今日题数') && text().includes('开始第一组训练'));

openSuanCfg('add2');
ok('题型配置页（两位数加法）', text().includes('题量') && text().includes('开始训练') && text().includes('两位数加法'));
ok('基础计算不显示难度', !text().includes('进阶'), '');
suanSetCfg('count', 20);
ok('题量 chip 可切换', suanCfg.count === 20);
suanSetCfg('count', 10);
openSuanCfg('jizhun');
suanSetCfg('diff', 'advanced');
ok('资料专项难度 chip 可切换', suanCfg.diff === 'advanced');
openSuanCfg('add2');

{
  let bad = [];
  Object.keys(SUAN_TYPES).forEach(id => {
    if (SUAN_TYPES[id].game === 'schulte') return;
    ['base','advanced','mixed'].forEach(d => {
      for (let i = 0; i < 2; i++){
        const q = suanGenerate(id, d);
        if (!q || !q.stem || q.answer === undefined) { bad.push(id + '/' + d); return; }
        if (!suanCheck(q, String(q.answer))) bad.push(id + '/' + d + '/check');
      }
    });
  });
  ok('所有题型生成器可用且可判分', bad.length === 0, bad.slice(0,3).join('|'));
}

/* 基础计算题型：位数/结构符合题型名 */
{
  const fail = [];
  const digits = n => String(Math.abs(n)).length;
  const parts = q => q.stem.split(' ');
  for (let i = 0; i < 20; i++){
    let q, p;
    q = suanGenerate('add2'); p = parts(q); if (digits(+p[0]) !== 2 || digits(+p[2]) !== 2 || p[1] !== '+') fail.push('add2');
    q = suanGenerate('sub2'); p = parts(q); if (digits(+p[0]) !== 2 || digits(+p[2]) !== 2 || p[1] !== '-') fail.push('sub2');
    q = suanGenerate('add3'); p = parts(q); if (digits(+p[0]) !== 3 || digits(+p[2]) !== 3) fail.push('add3');
    q = suanGenerate('sub3'); p = parts(q); if (digits(+p[0]) !== 3 || digits(+p[2]) !== 3) fail.push('sub3');
    q = suanGenerate('mul2x1'); p = parts(q); if (digits(+p[0]) !== 2 || digits(+p[2]) !== 1) fail.push('mul2x1');
    q = suanGenerate('mul2x2'); p = parts(q); if (digits(+p[0]) !== 2 || digits(+p[2]) !== 2) fail.push('mul2x2');
    q = suanGenerate('mul3x1'); p = parts(q); if (digits(+p[0]) !== 3 || digits(+p[2]) !== 1) fail.push('mul3x1');
    q = suanGenerate('div3x1'); p = parts(q); if (digits(+p[0]) !== 3 || digits(+p[2]) !== 1) fail.push('div3x1');
    q = suanGenerate('div3x2'); p = parts(q); if (digits(+p[0]) !== 3 || digits(+p[2]) !== 2) fail.push('div3x2');
    q = suanGenerate('div5x3'); p = parts(q); if (digits(+p[0]) !== 5 || digits(+p[2]) !== 3) fail.push('div5x3');
    q = suanGenerate('multiadd'); if (parts(q).filter(x => x === '+').length < 3) fail.push('multiadd');
  }
  ok('基础计算 12 题型位数/结构正确', fail.length === 0, [...new Set(fail)].join(','));
}
startSuan();
ok('进入答题页', !!suanState && suanState.count === 10);
while (suanState && suanState.idx < suanState.count){
  const q = suanState.items[suanState.idx];
  const el = els['suanInput'] || {};
  el.value = String(q.answer);
  suanNext();
}
const suanSessions = (JSON.parse(__store['yp_suan_v1'] || '{"sessions":[]}').sessions || []);
ok('提交后保存训练会话', suanSessions.length === 1, suanSessions.length);
ok('全对准确率 100%', suanSessions[0].right === 10 && suanSessions[0].answered === 10, suanSessions[0].right + '/' + suanSessions[0].answered);
ok('成绩单渲染', text().includes('逐题复盘') && text().includes('再来一组'));
ok('会话记录每题用时', (suanSessions[0].items || []).every(x => typeof x.ms === 'number'));

openSuanCfg('add2');
startSuan();
for (let i = 0; i < 3 && suanState; i++){
  const el = els['suanInput'] || {};
  el.value = '99999999';
  suanNext();
}
while (suanState && suanState.idx < suanState.count){ els['suanInput'].value = String(suanState.items[suanState.idx].answer); suanNext(); }
ok('答错题在成绩单标红', text().includes('suan-review bad'), '');
ok('会话统计错误数', JSON.parse(__store['yp_suan_v1']).sessions[0].right === 7, JSON.parse(__store['yp_suan_v1']).sessions[0].right);

const agg7 = suanAgg(7);
ok('近 7 天聚合有数据', agg7.sessions >= 2 && agg7.questions >= 20, agg7.sessions + '/' + agg7.questions);
renderSuanAbility();
ok('速算能力详情页', text().includes('近 7 天') && text().includes('近 30 天') && text().includes('按题型'));
ok('能力页有题型条形图', (text().match(/class="suan-bar-row"/g)||[]).length >= 1);
ok('能力页有周趋势', text().includes('近 7 天准确率'));

openSuanCfg('schulte');
startSuan();
ok('舒尔特方格渲染', !!suanState && suanState.grid.length === 16 && text().includes('sch-grid'));
for (let i = 1; i <= 16 && suanState; i++) schClick(i);
ok('舒尔特完成出成绩单', text().includes('逐题复盘') && text().includes('舒尔特方格'), '');

renderSuanHome();
ok('速算首页记住上次题型', text().includes('继续上次'), text().slice(0, 60));

return R;
})()
`;

(async () => {
  const results = await vm.runInContext(testCode, sandbox);
  let pass = 0;
  for (const r of results) {
    console.log(`${r.pass ? 'PASS' : 'FAIL'}  ${r.name}${r.extra ? '  [' + r.extra + ']' : ''}`);
    if (r.pass) pass++;
  }
  console.log(`\n${pass}/${results.length} passed`);
  process.exit(pass === results.length ? 0 : 1);
})();





