# 把 App 工程复制到纯英文路径（规避 AGP 的中文路径检查）
# 用法：.\move-to-ascii-path.ps1              复制到 %USERPROFILE%\ycsy-quiz
#       .\move-to-ascii-path.ps1 -Dest D:\ycsy-quiz
param(
    [string]$Dest = "$env:USERPROFILE\ycsy-quiz"
)

$ErrorActionPreference = 'Stop'
$src = Split-Path -Parent $MyInvocation.MyCommand.Path

if ($Dest -match '[^\x00-\x7F]') {
    throw "目标路径含非 ASCII 字符，构建仍会失败：$Dest"
}
if (Test-Path $Dest) {
    Write-Host "目标已存在：$Dest" -ForegroundColor Yellow
    Write-Host '如需覆盖，先手动删除或换一个 -Dest'
    exit 1
}

Write-Host "从 $src 复制到 $Dest ..." -ForegroundColor Cyan

# 排除缓存与构建产物，其余（含 node_modules）一起复制，免去重新联机安装
$robocopyArgs = @(
    $src, $Dest, '/E', '/NFL', '/NDL', '/NJH', '/NJS', '/NP',
    '/XD', 'node_modules\.cache', '.npm-cache', '.gradle', 'android\.gradle',
    'android\build', 'android\app\build', '.idea'
)
& robocopy @robocopyArgs | Out-Null
# robocopy 成功码是 0-7
if ($LASTEXITCODE -ge 8) { throw "复制失败（robocopy 退出码 $LASTEXITCODE）" }

$target = Join-Path $Dest 'android'
Write-Host ''
Write-Host '复制完成。' -ForegroundColor Green
Write-Host "接下来：Android Studio 打开 $target"
Write-Host ''
Write-Host '注意：' -ForegroundColor Yellow
Write-Host '  1. 题库源文件仍在 桌面\习题\延长石油套卷模考.html'
Write-Host "  2. 改了题库后，在 $Dest 里执行 npm run sync 再重新 Build"
Write-Host '  3. 同步脚本已内置原始路径回退，搬走后依然能找到源文件'