# 手机 App（Capacitor 套壳）

把 `延长石油套卷模考.html` 装进原生 WebView，产出可安装的 APK。
题库和逻辑仍然是那一个 HTML，改完只需 `npm run sync` 一次。

App 里现在有三个板块：

1. **套卷模考**（`📝`）：81 套 / 6246 题，整卷练习或计时模考；随机刷题从套卷 + 专项共 18412 题里抽
2. **专项练习**（`🧩`，2026-11-15 新增）：102 个专项题库 / 12166 题，来自 `二、专项练习（做·练）`，
   按模块刷题、只有练习模式，和套卷完全分开
3. **阅读学习**（`📖`）：看 `一、学习资料（看·学）` 里的 23 份资料，PDF 原样呈现

阅读资料已打包进 `www/study`，所以 APK 会比早期版本大很多（≈360 MB+）。

**当前状态：已能出包**（`android/` 已存在，插件已装，v2.2 的 `app-debug.apk` 已生成在
`android/app/build/outputs/apk/debug/`，根目录也放了一份 `延长石油刷题-v2.2-速算分类.apk`，
298.1 MB / versionCode 10）。

v2.0：按设计稿重做界面——底部四栏导航（套卷模考/专项训练/阅读学习/个人中心）、
题目 8 类分类标签（政治理论/常识判断/言语/数量/判断/资料/公基/专业知识）、个人中心统计与近 7 日柱状图、
搜索/收藏/历史/学习记录。

v1.5 起：做题支持断点续做（下次默认从上次那道题继续，做过的题标「已做」并直接显示答案），
随机刷题进度也单独保存；界面加了页面入场、卡片悬停、数字滚动等轻量动效。
v1.6：随机刷题题库由「只有套卷」改为「套卷 + 专项全部 18412 题」，每题标注出处。
v2.0：全新四栏界面 + 8 类分类标识 + 个人中心统计。
v2.1：新增「速算训练」模块（悬浮胶囊入口 / 专项场景卡 / 阅读文末练一练 / 个人中心速算能力），
      题型模板生成、可无限练，训练会话与聚合统计存本机。
v2.2：速算题型按设计稿细分为 22 个——基础计算 12 个（两位数加减/三位数加减/多数相加/乘法 3 种/
      常见平方数/除法 3 种）、资料专项 8 个（估算基期、增长量、百化分计算/练习、分数比较、基期比较、
      年平均量、年均增长率）、专注训练 2 个。

---

## 阅读学习板块（2026-11-14 新增）

首页顶部两个页签切换：`📝 套卷模考` / `📖 阅读学习`。

- 板块内按 **科目 → 专题** 分层（公基 8 个专题、行测 9 个专题），顺序照《资料库目录说明.md》
  的推荐阅读顺序，每项还带"第 1 周 / 贯穿全程"这样的阶段提示
- 点开即在 App 内用 **PDF.js 3.11** 渲染原始 PDF：翻页、跳页、＋－缩放、左右滑动；
  退出时记住看到第几页，列表和"接着上次看"都会显示进度
- 20 个 PDF + 4 个 `.doc`（用 Word 导成 PDF，共 23 份 —— 企业文化那份 `.doc` 与同目录 PDF 内容重复，已去重）
- 桌面版（直接双击 HTML，`file://`）点开则用浏览器自带的 PDF 阅读器打开原文件，不加载 PDF.js

### 体积

| 部分 | 大小 |
|---|---|
| `www/study/*.pdf` — 43 个资源（含 22 个分卷） | 353 MB |
| `www/pdfjs/` — PDF.js + 中文 CMap + 标准字体 | 3.3 MB |
| `www/index.html` | 3.0 MB |

两个大扫描件按约 12 MB 切卷：**教材版笔记**（177 MB / 150 页）分 15 卷、**思维导图**（75 MB / 216 页）
分 7 卷。切卷用 pypdf 原样搬页，不重新编码，画质和原文件一致；手机一次只读一卷，不会因为 177 MB
整包进内存而卡死或崩溃。

### 资料有变动时怎么重建

```powershell
# 0) 只在新增/改动了 .doc 时需要（要本机装了 Word）
powershell -File _build\doc2pdf.ps1
# 1) 扫描目录：生成 _build\study_manifest.json，并把 PDF 复制/切卷到 app-mobile\www\study
python _build\build_study.py
# 2) 重新生成网页（把题库 + 资料目录注入 template.html）
python _build\build_html.py
# 3) 同步进 App
cd app-mobile; npm run sync
```

科目名、专题名、阅读提示都写在 `_build/build_study.py` 的 `SUBJECTS` 里；新增文件夹时在那里加一条，
再跑上面 1→3 步。

### 专项练习题库有变动时怎么重建

```powershell
# 1) 抽取「二、专项练习」全部源文件文本（.doc 里 LibreOffice 转不了的会自动记下来）
python _build\drill_extract.py
# 2) 如有 .doc 转失败（报告里 fail 且是 .doc），用 Word 转一次（需 danger-full-access）
pwsh -File _build\drill_doc2docx.ps1
python _build\drill_extract.py          # 再跑一遍，用 Word 转出的 docx 补上
# 3) 解析成专项题库 + 重新生成网页 + 同步进 App
python _build\drill_parse.py
python _build\build_html.py
cd app-mobile; npm run sync
```

分类、命名规则在 `_build/drill_parse.py` 的 `CATS` / `SUB_NAMES` 里；单个源文件质量不合格不想收录时，
加到 `DROP_SOURCES`。解析统计见 `_build/drill_parse_report.txt`。

---

## 这台机器的实测情况（2026-11-14 更新）

| 项目 | 状态 |
|---|---|
| Node / npm | ✅ v24.21.0 / 11.17.0 |
| Capacitor 依赖 | ✅ 已装，Android 工程已生成 |
| 页面同步 | ✅ `android/app/src/main/assets/public/`（index.html 3.0 MB + study 353 MB + pdfjs 3.3 MB） |
| JDK | ✅ 已下 `_build/jdk21`（Temurin/Huawei 镜像 openjdk-21.0.2），`JAVA_HOME` 指它即可；Studio 自带 JBR 是 **25**，不能直接用 |
| Android SDK | ✅ android-35 已就位（早先记的"缺 35"已过时），build-tools 36.0.0 已钉在 `app/build.gradle` |
| Gradle | ✅ 8.11.1 已在 `~/.gradle/wrapper/dists` 缓存；wrapper 的 `.lck` 在建机限制下会报"拒绝访问"，改用解压后的 `gradle.bat` 直接跑即可 |
| 打包结果 | ✅ 已产出 `app-debug.apk`（v1.5，298 MB，含套卷 81 套 6246 题 + 专项 102 库 12166 题 + 阅读学习），见「方式 B」 |
| `ANDROID_HOME` | ❌ 指向 `E:\adb`（不存在），已在 `local.properties` 里显式指定真实路径 |

---

## 方式 B：命令行打包（这次就是这么出的包，最快）

工程里已经备好 `_build/jdk21`（JDK 21）与解压好的 Gradle 8.11.1，直接在 PowerShell 里跑：

```powershell
cd C:\Users\86138\Desktop\习题\app-mobile\android
$env:JAVA_HOME = "C:\Users\86138\Desktop\习题\_build\jdk21"
$env:PATH = "$env:JAVA_HOME\bin;$env:PATH"
# 缓存和临时目录都放工作区内，避免用户目录 / 系统 temp 的权限问题
$env:GRADLE_USER_HOME = "C:\Users\86138\Desktop\习题\_build\gradle-home"
$env:GRADLE_OPTS = "-Djava.io.tmpdir=C:\Users\86138\Desktop\习题\_build\tmp"
$env:TEMP = "C:\Users\86138\Desktop\习题\_build\tmp"
$env:TMP  = "C:\Users\86138\Desktop\习题\_build\tmp"

# wrapper 的锁文件在本机会报"拒绝访问"，所以直接用解压后的 gradle
& "$env:USERPROFILE\.gradle\wrapper\dists\gradle-8.11.1-bin\eac4u065zwes5phgltp5f9b9e\gradle-8.11.1\bin\gradle.bat" `
    assembleDebug --no-daemon --console=plain
```

产物在同一目录的 `app\build\outputs\apk\debug\app-debug.apk`（这次跑出的是 `BUILD SUCCESSFUL in 20s`，
20 秒内出包，只有改过代码/资源时才会重跑对应任务）。

> 如果没有设 `GRADLE_OPTS` / `TEMP`，`MergeJavaRes` 或最后的 problems 报告会报
> `AccessDeniedException`（本机 temp 与 `build/reports` 权限问题）。APK 通常已经在那之前写好了，
> 但更省事的做法是按上面把临时目录指到 `_build\tmp`。

> 版本号已在 `app/build.gradle` 改成 `versionCode 7 / versionName "1.6"`（v1.5 断点续做 + 动效，v1.6 随机刷题覆盖全库）。

---

## 方式 A：用 Android Studio 打包（图形界面，想改代码时更顺手）

### 已替你准备好的

- `android/local.properties` 已写入 SDK 路径（`%LOCALAPPDATA%\Android\Sdk`）
- `gradle-wrapper.properties` 已把发行包改成 `-bin`（体积小一半），
  下载超时放宽到 **180 秒**（默认 10 秒，网慢必失败）
- 应用名「延长石油刷题」、包名 `com.ycsy.quiz`、版本 1.0

### 四步走

**1. 打开工程**

Android Studio 在 `G:\ADB\bin\studio64.exe`。
`File > Open` 选择 **`app-mobile\android`**（注意是 android 这层，不是 app-mobile）。

**2. 把 Gradle JDK 换成 21（关键）**

这台 Studio 自带的 JBR 是 **JDK 25**，而工程用的 Gradle 8.11 / AGP 8.7
最高只支持到 21，直接用会报 `Unsupported class file major version` 或 Gradle 启动失败。

`File > Settings`（Ctrl+Alt+S）→ `Build, Execution, Deployment` → `Build Tools` → `Gradle`
→ 右侧 **Gradle JDK** 下拉 → 选 `Download JDK…` → Version 选 **21** → Download

（若列表里已有 17/21 的 JDK，直接选它也行。）

**3. 装缺失的 SDK**

工程要 `compileSdk 35`，但本机只有 `android-37.0`。
Gradle Sync 时 Studio 会提示缺组件，点提示里的
**「Install missing SDK package(s)」**；或打开
`Tools > SDK Manager` → `SDK Platforms` 勾 **Android 15 (API 35)** →
`SDK Tools` 勾 **Build-Tools 35.0.0** → Apply。

**4. 打包**

等 Gradle Sync 跑完（首次会下载 Gradle 8.11.1 约 130 MB，网慢请耐心），然后：

`Build > Build Bundle(s) / APK(s) > Build APK(s)`

完成后右下角会弹「APK(s) generated successfully」，点 **locate** 定位到：

```
android\app\build\outputs\apk\debug\app-debug.apk
```

把这个文件传到手机安装（需允许「安装未知来源应用」）。

### 报「project path contains non-ASCII characters」

因为工程在 `桌面\习题` 下，AGP 在 Windows 上会直接拒绝：

```
Failed to apply plugin 'com.android.internal.application'.
> Your project path contains non-ASCII characters.
```

两种处理，先试简单的：

**方案 1：打开开关（已默认开启）**

`android/gradle.properties` 里已加：

```properties
android.overridePathCheck=true
```

回 Studio 点 `Sync Project with Gradle Files` 再试。

**方案 2：把工程搬到纯英文路径（最稳）**

如果方案 1 之后仍在 `aapt2` / `javac` 阶段失败，就是中文路径真的影响了工具链，必须搬：

```powershell
cd C:\Users\86138\Desktop\习题\app-mobile
.\move-to-ascii-path.ps1
```

默认复制到 `C:\Users\86138\ycsy-quiz`（含 node_modules，不用重新联网装依赖），
然后用 Studio 打开 `C:\Users\86138\ycsy-quiz\android`。

搬走以后：

- 题库源文件仍在 `桌面\习题\延长石油套卷模考.html`
- 改完题库，在新目录里跑 `npm run sync`（同步脚本会回退到原始路径找源文件）
- 想搬到别的盘：`.\move-to-ascii-path.ps1 -Dest D:\ycsy-quiz`

### Gradle 下载不下来怎么办

报错长这样：

```
Could not install Gradle distribution from 'https://services.gradle.org/...'
Reason: java.net.ConnectException: Connection timed out
```

说明 `services.gradle.org` 连不上（国内常见）。三种解法，从省事到最稳：

**解法 1：切国内镜像（已默认切好）**

```powershell
cd app-mobile
.\switch-gradle-source.ps1 -Mirror tencent     # 腾讯
.\switch-gradle-source.ps1 -Mirror huawei      # 华为
```

然后 Android Studio 里点 `Sync Project with Gradle Files`。
若仍失败，先清掉半截缓存再试：

```powershell
Remove-Item -Recurse -Force "$env:USERPROFILE\.gradle\wrapper\dists\gradle-8.11.1-bin"
```

**解法 2：用浏览器手动下载，再指向本地文件（最稳，绕过一切网络限制）**

1. 浏览器打开 `https://mirrors.cloud.tencent.com/gradle/gradle-8.11.1-bin.zip` 下载
2. 放到比如 `D:\gradle-8.11.1-bin.zip`
3. 执行：

```powershell
.\switch-gradle-source.ps1 -LocalZip D:\gradle-8.11.1-bin.zip
```

**解法 3：挂代理**

在 `android/gradle.properties` 里加（按自己的代理端口改）：

```properties
systemProp.http.proxyHost=127.0.0.1
systemProp.http.proxyPort=7890
systemProp.https.proxyHost=127.0.0.1
systemProp.https.proxyPort=7890
```

### 依赖也下不动？

已经默认在 `android/build.gradle` 里把 **阿里云 Maven 镜像**放在官方源前面：

```gradle
maven { url 'https://maven.aliyun.com/repository/google' }
maven { url 'https://maven.aliyun.com/repository/public' }
maven { url 'https://maven.aliyun.com/repository/gradle-plugin' }
google()
mavenCentral()
```

镜像不可用时会自动回落到官方源，不用手动改回。

## 方式 B：纯命令行

前提：JDK 17 或 21、Android SDK Platform 35。

```powershell
# 1) 装 JDK 21 并指过去
$env:JAVA_HOME = "C:\Program Files\Java\jdk-21"

# 2) 若没有 sdkmanager，先装 cmdline-tools（解压到 SDK 的 cmdline-tools/latest）
#    https://developer.android.com/studio#command-line-tools-only

# 3) 装需要的 SDK 组件
& "$env:LOCALAPPDATA\Android\Sdk\cmdline-tools\latest\bin\sdkmanager.bat" `
   "platforms;android-35" "build-tools;35.0.0" "platform-tools"

# 4) 告诉工程 SDK 在哪（本机 ANDROID_HOME 是坏的，必须显式指定）
"ANDROID_HOME=$env:LOCALAPPDATA\Android\Sdk" | Out-File android\local.properties -Encoding ascii

# 5) 编译
cd android
.\gradlew.bat assembleDebug
```

产物同上。

---

## 首次初始化（本机已做过，换电脑时才需要）

```powershell
cd app-mobile
$env:npm_config_cache = "$PWD\.npm-cache"   # 避免写系统缓存目录被拦截
npm install
npx cap add android
npx cap sync
```

或直接跑 `.\setup.ps1`（已封装上述步骤）。

---

## 日常改题库后

```powershell
cd app-mobile
npm run sync        # 复制新 HTML 到 www/ 并同步进 android 工程
cd android
.\gradlew.bat assembleDebug
```

`www/index.html` 是 `延长石油套卷模考.html` 的副本，**不要手改**，会被覆盖。

---

## 这个壳已经处理好的事

HTML 里内置了「原生壳适配」，只在 `window.Capacitor` 存在时生效，浏览器里完全不受影响：

1. **外链走系统浏览器**：「去华图搜这题」不会把 App 导航走，而是调
   `@capacitor/browser` 打开系统浏览器（失败回落 `_system`）
2. **键盘不遮输入框**：AI 追问框聚焦后自动滚到可视区
3. **安卓返回键**：优先走页面内返回（首页 / 分类页 / 题目），无层级时才退出
4. **https scheme**：`server.androidScheme = "https"`，Origin 不是 `null`，
   调大模型接口时 CORS 比 `file://` 正常

---

## 改应用名 / 图标

- 应用名：改 `capacitor.config.json` 的 `appName` → `npx cap sync`
- 图标：准备 1024×1024 PNG 放 `resources/icon.png`，然后
  ```powershell
  npx @capacitor/assets generate
  npx cap sync
  ```

---

## 常见报错

| 报错 | 原因与处理 |
|---|---|
| `Unsupported class file major version` | JDK 太新，换 17/21 |
| `SDK location not found` | 没写 `android/local.properties`，或 `ANDROID_HOME` 无效 |
| `Failed to install the following SDK components` | 缺 platform 35 / build-tools 35，用 sdkmanager 装 |
| Gradle 下载卡住 | 配国内镜像，或先用 Android Studio 完成一次同步 |
| 白屏 | 看 `chrome://inspect` 连真机调试；本工程已开 `webContentsDebuggingEnabled` |

---

## 已知限制

- 进度、错题、AI 缓存存在 **localStorage**：系统内存紧张时可能被清。
  要更稳可换 `@capacitor/preferences`，或加「导出进度」按钮。
- AI 解析需联网；题库、判分、解析、错题本全部离线可用。
- 首启解析 3 MB 单文件需几百毫秒，保留启动图可避免白屏。
- iOS 需要 Mac + Xcode：`npx cap add ios` 后 `npx cap open ios`。


