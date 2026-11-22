# 一键初始化 Capacitor 工程（Windows PowerShell）
# 用法：右键「使用 PowerShell 运行」，或在 app-mobile 目录下执行 .\setup.ps1
$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

# 把 npm 缓存放到工作区，避免系统缓存目录写入被拦截
$env:npm_config_cache = Join-Path $root '.npm-cache'

Write-Host "== 1/4 检查环境 ==" -ForegroundColor Cyan
$node = (Get-Command node -ErrorAction SilentlyContinue)
if (-not $node) { throw '未找到 node，请先安装 Node.js 18+' }
Write-Host ("node {0}" -f (& node -v))

if ($env:JAVA_HOME) {
    Write-Host ("JAVA_HOME = {0}" -f $env:JAVA_HOME)
} else {
    Write-Warning '未设置 JAVA_HOME，构建时可能用到错误的 JDK'
}
Write-Host '提示：Capacitor 7 推荐 JDK 17 或 21；JDK 25 可能报 Unsupported class file major version'

Write-Host "== 2/4 同步题库 HTML ==" -ForegroundColor Cyan
& node scripts/sync-html.js

Write-Host "== 3/4 安装依赖 ==" -ForegroundColor Cyan
& npm install --no-audit --no-fund --cache $env:npm_config_cache

Write-Host "== 4/4 生成 Android 工程 ==" -ForegroundColor Cyan
if (Test-Path (Join-Path $root 'android')) {
    Write-Host 'android/ 已存在，跳过 cap add，执行 cap sync'
    & npx cap sync android
} else {
    & npx cap add android
    & npx cap sync android
}

Write-Host ''
Write-Host '完成。下一步：' -ForegroundColor Green
Write-Host '  cd android; .\gradlew.bat assembleDebug'
Write-Host '  产物：android\app\build\outputs\apk\debug\app-debug.apk'