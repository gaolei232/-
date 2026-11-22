# 延长石油招聘考试备考应用

> 把 400+ 份散落的 doc/pdf 备考资料，压成一个 **12.5 MB 单文件网页**：双击就能刷题，全程离线，
> 同一份页面再套一层 Capacitor 壳即可打成安卓 App。

- **版本**：v2.2（Android `versionCode` 10）
- **题库**：18 412 题（套卷 6 246 + 专项 12 166）
- **阅读**：23 份资料 / 1 763 页
- **测试**：`216 / 216` 通过
- **许可**：MIT（代码），题库内容版权归原出题方

---

## 简介

本项目不是传统的"前后端分离应用"，而是一条**数据生产线 + 单文件 Web App**：

```
427 份原始资料  →  Python 管道抽取解析  →  结构化题库 JSON  →  注入 HTML 模板  →  单文件网页 / 安卓 App
```

设计上的三个硬约束，决定了它的全部形态：

1. **离线优先**：所有题目、答案、解析、页面逻辑全部内联进一个 `.html`，不依赖服务器、不依赖 CDN。
2. **零运行时依赖**：原生 JS + 原生 CSS，没有 webpack / Vite，没有 npm 运行时包，十年后仍能打开。
3. **一次构建、多端分发**：同一份 HTML 既是桌面网页，也是 App 的 WebView 内容源。

---

## 功能特性

| 模块 | 能力 | 规模 |
|---|---|---|
| 📝 套卷模考 | 练习 / 考试双模式、单题计时、答题卡、交卷判分、断点续做 | 81 套 / 6 246 题 |
| 🎯 专项练习 | 按模块刷题，复用套卷逻辑但无计时、不计分 | 102 库 / 12 166 题 |
| 🎲 随机刷题 | 全库 18 412 题随机抽，同轮不重复，独立进度 | 全库 |
| 📖 阅读学习 | 内置 PDF 阅读器：翻页、跳页、缩放、滑动、进度记忆 | 23 份 / 1 763 页 / 43 分卷 |
| ⚡ 速算训练 | 22 个题型参数化生成（12 基础 + 8 资料 + 2 专注），会话记录、7/30 天能力趋势 | 22 题型 |
| 👤 个人中心 | 总览统计、每日打卡、近 7 日柱图、错题本、收藏、历史、搜索 | — |
| 🤖 AI 解析 | 无原卷解析的题可调大模型讲解，支持 DeepSeek / OpenAI / 智谱 / 通义 / Ollama | 按需 |
| 📱 安卓 App | Capacitor 7 套壳，原生返回键、外链走系统浏览器 | 298 MB |

**细节设计**（不是半成品）：

- **无答案题**（2 371 道）单独处理：不判对错、不进错题本、答题卡显示虚线格、交卷不计分。
- **8 类知识域标签**：政治理论 / 常识判断 / 言语理解 / 数量关系 / 判断推理 / 资料分析 / 公共基础 / 专业知识。
- **公式丢失的解析**自动识别并整段隐藏，可展开看残文，并给 AI 入口，不展示半截假解析。

---

## 快速开始

### 方式一：生成本地网页（最常用）

```bash
# 1) 生成单文件网页（不需要 Python 依赖，纯数据拼接）
npm run build:html

# 2) 双击打开
#    Windows: start 延长石油套卷模考.html
#    macOS:   open  延长石油套卷模考.html
```

> 生成的 `延长石油套卷模考.html` **不进版本库**（属构建产物，可用一条命令重建），
> 所以克隆后需先跑一次 `npm run build:html`。

### 方式二：从源码重建题库（数据有变动时）

```bash
pip install -r requirements.txt
python _build/drill_extract.py   # 专项：源文件 → 文本
python _build/drill_parse.py     # 文本 → drill_bank.json
python _build/parse.py           # 套卷：文本 → bank.json
python _build/finalize.py        # 去重 / 清洗 / 加分类 → bank_final.json
npm run build:html               # 题库 → 网页
```

### 方式三：打包安卓 App

```bash
npm run mobile:install           # 安装 Capacitor 依赖
npm run sync                     # 复制 HTML 进 app-mobile/www 并 cap sync
npm run apk                      # gradlew assembleDebug

# 产物：app-mobile/android/app/build/outputs/apk/debug/app-debug.apk
```

打包需要 **JDK 21**（仓库内已备 `_build/jdk21`）与 **Android SDK 35 + Build-Tools 36.0.0**，
环境变量写法见 `.env.example` 与 [`app-mobile/README.md`](app-mobile/README.md)。

---

## 环境要求

| 用途 | 依赖 | 说明 |
|---|---|---|
| 打开网页 | 任意现代浏览器 | Chrome / Edge / Safari；手机浏览器同样可用 |
| 生成网页 | Node.js ≥ 18 | 只用 `node` 跑脚本，无需 `npm install` |
| 重建题库 | Python ≥ 3.10 + `requirements.txt` | 另需 `pdftotext`、LibreOffice，部分 `.doc` 需 Word COM |
| 打包 App | JDK 21、Android SDK 35、Gradle 8.11 | JDK 25 会报 `Unsupported class file major version` |
| AI 解析 | 任一 OpenAI 兼容接口的 Key | 在页面「设置」里填，不需改代码 |

---

## 常用命令

| 命令 | 作用 |
|---|---|
| `npm run build:html` | 题库 JSON + 模板 → `延长石油套卷模考.html` |
| `npm run build:study` | 扫描原始资料 → `study_manifest.json` + 分卷 PDF（需原始资料在场） |
| `npm test` | 跑页面逻辑测试（216 项，直接验证交付的 HTML） |
| `npm run sync` | 把 HTML 同步进 `app-mobile/www/` 并执行 `cap sync` |
| `npm run apk` | 构建 debug APK |

---

## 目录结构

```
.
├── _build/                       # 构建管道（核心代码在这里）
│   ├── template.html             #   页面模板 = 应用本体（样式 + 2972 行 JS）
│   ├── suan.js / suan.css        #   速算模块源码（注入 template 后打包）
│   ├── test_app.js               #   页面逻辑测试（216 项）
│   ├── build_html.py             #   模板 + 题库 → 单文件 HTML
│   ├── build_study.py            #   原始资料 → 阅读清单 + 分卷 PDF
│   ├── parse.py                  #   套卷：文本 → 结构化题目
│   ├── drill_extract.py          #   专项：源文件 → 文本
│   ├── drill_parse.py            #   专项：文本 → 结构化题目
│   ├── finalize.py               #   去重 / 清洗 / 过滤 / 分类
│   ├── classify.py               #   8 类知识域标注
│   ├── quality.py                #   残句判定器（含 10 条自检用例）
│   ├── bank_final.json           #   套卷题库（81 套 / 6 246 题，4.8 MB）
│   ├── drill_bank.json           #   专项题库（102 库 / 12 166 题，7.8 MB）
│   ├── study_manifest.json       #   阅读资料清单（23 份 / 1 763 页）
│   ├── manual_fixes.json         #   人工补全的解题过程
│   └── *.ps1                     #   格式转换的 Windows 辅助脚本
│
├── app-mobile/                   # Capacitor 安卓壳
│   ├── capacitor.config.json
│   ├── package.json
│   ├── scripts/sync-html.js      #   把桌面 HTML 复制进 www/
│   ├── www/pdfjs/                #   内置 PDF.js 3.11（第三方，已入库）
│   ├── www/index.html            #   同步副本（构建产物，不入库）
│   ├── www/study/                #   分卷 PDF（构建产物，不入库）
│   └── android/                  #   原生工程（构建缓存不入库）
│
├── 套卷模考网页说明.md            # 功能与数据来源的详细说明（事实文档）
├── 项目全景评估报告.md            # 项目结构与健康度评估
├── 资料库目录说明.md              # 原始资料的分类与学习顺序
├── 备考学习计划.md                # 复习节奏
├── .env.example                  # 构建环境变量示例
├── .gitignore / .gitattributes / .editorconfig
├── requirements.txt
├── package.json                  # 根级脚本入口（无 npm 依赖）
└── LICENSE
```

---

## 数据流

```
一、学习资料 / 二、专项练习 / 三、套卷模考与冲刺        ← 原始资料（不入库）
            │
            ├─ convert.ps1 / docx_to_txt.py / drill_extract.py      文本抽取
            │        ↓ raw/*.txt
            ├─ parse.py / drill_parse.py                             两套切题器取优
            │        ↓ bank.json
            ├─ finalize.py → bank_final.json                         去重 / 清洗
            ├─ classify.py                                           逐题打 8 类标签
            │
            ├─ build_study.py ──→ study_manifest.json + www/study/*.pdf
            │
            └─ build_html.py                                         注入三处占位符
                     ↓
              延长石油套卷模考.html  ──sync──→  www/index.html  ──cap sync──→  APK
```

模板内的三个注入点是构建契约：`__BANK__`（套卷）、`__DRILL__`（专项）、`__STUDY__`（阅读清单）。

---

## 使用示例

**1. 做一套真题**

首页 →「套卷模考」→ 选分类（如「历年真题」）→ 点套卷 → 选「练习」或「考试」→ 开始。
练习模式每选完一题即展开答案与解析；考试模式交卷后统一判分并出成绩单。

**2. 中断后接着做**

有进度的套卷，主按钮会变成「继续做题 · 第 12/93 题」，顶部显示「✓ 上次做到第 12 题」，
已做过的题在续做时直接展开答案解析。

**3. 配置 AI 解析**

右下角「设置」→ 选预设（DeepSeek：`https://api.deepseek.com/v1`）→ 填 API Key → 保存。
之后在没有原卷解析的题上点「AI 解析」即可；结果会缓存，同题不重复计费。

> Key 只存在浏览器 `localStorage`，不会上传到本项目；页面直连接口需要对方允许跨域（CORS）。

**4. 练速算**

任意页面右下角「⚡ 速算」胶囊 → 选题型（如「百化分计算」）→ 选题量与难度 → 开始。
交卷后出准确率与逐题复盘，个人中心可看 7/30 天能力趋势。

**5. 看资料**

「阅读学习」→ 选科目 → 打开资料。桌面版调用浏览器自带 PDF 阅读器；App 内使用内置 PDF.js，页码会自动记忆。

---

## 题库与数据规模

| 指标 | 套卷 | 专项 | 合计 |
|---|---|---|---|
| 库数 | 81 套 | 102 库 | 183 |
| 题量 | 6 246 | 12 166 | **18 412** |
| 有答案 | 5 262 | 10 779 | 16 041（87.1%） |
| 无答案（自测） | 984 | 1 387 | 2 371（12.9%） |
| 有原卷解析 | 3 648 | 5 880 | 9 528（51.7%） |
| 完全重复题干 | 277 处 | 284 处 | 561 处（待清理） |

---

## 测试

```bash
npm test          # → 216/216 passed
```

测试用 Node 的 `vm` + 自建 DOM 桩件，**直接读取交付的 `延长石油套卷模考.html`**（而非源码），
覆盖计时、判分、断点续做、随机池去重、AI 输出过滤、公式渲染、残句判定、速算生成器、舒尔特方格等。

> 注意：测试读取 HTML，所以要先 `npm run build:html`。

---

## 原始资料目录（重要）

三个资料目录**不进版本库**，原因：

- 合计 **1.2 GB**，最大单文件 185 MB，超出 GitHub / Gitee 的 100 MB 单文件上限；
- 它们是"素材"而非"源码"，且题库解析结果（`bank_final.json` / `drill_bank.json`）已入库，
  删掉素材不影响刷题，只影响「阅读学习」板块和"重新解析题库"。

需要时把目录放回仓库根目录同名即可：

```
一、学习资料（看·学）/      # 阅读学习板块 + build_study.py 的输入
二、专项练习（做·练）/      # drill_extract.py 的输入
三、套卷模考与冲刺/          # parse.py 的输入
```

---

## 已知限制

- **48.3% 的题没有原卷解析**（8 884 题），只能靠 AI 解析按需生成。
- **公式 / 图形丢失**：原卷中作为图片的算式无法文本化，30 题解析已整段隐藏，17 题连题干数据也缺失（无法还原，不编造）。
- **少数长材料题库**存在题干与下一题选项粘连，答案仍按原卷序号对应。
- **561 处重复题干**，同一道题可能在不同模拟卷里出现两次。
- **数据只存本地**：清浏览器缓存 = 进度、错题、速算记录全部丢失（当前无导出功能）。
- **构建不可全量复现**：`raw/`、`raw_docx/`、`raw_drill/` 等中间文本未入库，重跑解析需重新执行耗时的格式转换。
- **APK 298 MB**，且 `build.gradle` 未配置 release 签名，当前只能出 debug 包。

更完整的风险评估见 [`项目全景评估报告.md`](项目全景评估报告.md)。

---

## 数据来源与版权

- 题目、答案、解析均来自公开出版的备考资料，**判分依据是原卷自带答案**，不是模型推测。
- 代码以 MIT 许可开源；**题库内容与原始资料的版权归原出题 / 出版方**，本仓库仅作个人备考用途，
  请勿用于商业分发。详见 [`LICENSE`](LICENSE) 末尾的说明。
- 「延长石油」等名称仅为描述用途，与相关企业无隶属关系。

---

## 贡献说明

欢迎提 Issue / PR，但请遵守本项目的三条硬约束：

1. **不要破坏单文件分发**：新增功能请写在 `_build/template.html` 或 `_build/suan.js` 里，
   不要引入 npm 运行时依赖或构建工具。
2. **改完必须跑测试**：`npm run build:html && npm test`，216 项全绿才提 PR。
3. **不要提交构建产物**：`延长石油套卷模考.html`、`www/index.html`、`www/study/`、`*.apk`
   均已在 `.gitignore` 中，请勿用 `git add -f` 绕过。

**修正一道题的解析**：不要直接改 `bank_final.json`（会被下次解析覆盖），
而是写进 `_build/manual_fixes.json`：

```json
{
  "源文件名": {
    "题号": { "p": "解题过程", "e": "完整解析", "note": "备注" }
  }
}
```

**改速算模块**：`suan.js` 是注入源，改完必须重新注入 `template.html` 再构建，否则页面仍跑旧代码。

**提交信息**：建议 `feat(module): ...` / `fix(module): ...` / `docs: ...` / `data: ...` 前缀。

---

## 相关文档

| 文档 | 内容 |
|---|---|
| [`套卷模考网页说明.md`](套卷模考网页说明.md) | 功能全貌、题库来源、解析质量、重建步骤 |
| [`项目全景评估报告.md`](项目全景评估报告.md) | 结构盘点、技术债、待办优先级（P0/P1/P2） |
| [`资料库目录说明.md`](资料库目录说明.md) | 原始资料的分类与建议学习顺序 |
| [`app-mobile/README.md`](app-mobile/README.md) | 安卓打包步骤与常见报错处理 |

---

## 许可证

[MIT](LICENSE) © 2026 gl
