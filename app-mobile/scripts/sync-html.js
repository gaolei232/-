// 把题库网页复制进 www/index.html，保证 App 与桌面版始终是同一份
const fs = require('node:fs');
const path = require('node:path');

// 依次尝试：环境变量 → 原地（桌面/习题）→ 固定的原始位置（工程被搬到别处时用）
const CANDIDATES = [
  process.env.QUIZ_HTML,
  path.resolve(__dirname, '..', '..', '延长石油套卷模考.html'),
  'C:\\Users\\86138\\Desktop\\习题\\延长石油套卷模考.html',
].filter(Boolean);

const SRC = CANDIDATES.find(p => fs.existsSync(p));
const DEST = path.resolve(__dirname, '..', 'www', 'index.html');

if (!SRC) {
  console.error('找不到题库 HTML，试过这些位置：');
  CANDIDATES.forEach(p => console.error('  ' + p));
  console.error('可以用环境变量指定：$env:QUIZ_HTML="D:\\延长石油套卷模考.html"; npm run sync');
  process.exit(1);
}

fs.mkdirSync(path.dirname(DEST), { recursive: true });
fs.copyFileSync(SRC, DEST);

const mb = (fs.statSync(DEST).size / 1024 / 1024).toFixed(2);
console.log('源文件：' + SRC);
console.log('已同步到 www/index.html（' + mb + ' MB）');