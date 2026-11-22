# 切换 Gradle 下载源 / 使用本地包
# 用法：
#   .\switch-gradle-source.ps1 -Mirror tencent        # 改用腾讯镜像
#   .\switch-gradle-source.ps1 -Mirror huawei         # 改用华为镜像
#   .\switch-gradle-source.ps1 -Mirror official       # 改回官方
#   .\switch-gradle-source.ps1 -LocalZip D:\gradle-8.11.1-bin.zip   # 用已下载的本地包
param(
    [ValidateSet('tencent', 'huawei', 'official', '')]
    [string]$Mirror = '',
    [string]$LocalZip = ''
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$props = Join-Path $root 'android\gradle\wrapper\gradle-wrapper.properties'
if (-not (Test-Path $props)) { throw "找不到 $props" }

$version = '8.11.1'
$urls = @{
    tencent  = "https://mirrors.cloud.tencent.com/gradle/gradle-$version-bin.zip"
    huawei   = "https://mirrors.huaweicloud.com/gradle/gradle-$version-bin.zip"
    official = "https://services.gradle.org/distributions/gradle-$version-bin.zip"
}

if ($LocalZip) {
    if (-not (Test-Path $LocalZip)) { throw "本地包不存在：$LocalZip" }
    $full = (Resolve-Path $LocalZip).Path -replace '\\', '/'
    $url = "file\\:///$full"     # properties 文件里冒号要转义
    Write-Host "使用本地包：$full"
}
elseif ($Mirror) {
    $url = $urls[$Mirror] -replace ':', '\:'
    Write-Host "使用镜像：$($urls[$Mirror])"
}
else {
    throw '请指定 -Mirror tencent|huawei|official 或 -LocalZip <zip 路径>'
}

$text = Get-Content -LiteralPath $props -Raw
$text = $text -replace '(?m)^distributionUrl=.*$', "distributionUrl=$url"
Set-Content -LiteralPath $props -Value $text -Encoding ASCII -NoNewline

Write-Host ''
Write-Host '已更新 gradle-wrapper.properties：' -ForegroundColor Green
Get-Content $props | Where-Object { $_ -match 'distributionUrl|networkTimeout' } | ForEach-Object { '  ' + $_ }

Write-Host ''
Write-Host '下次在 Android Studio 里点 "Sync Project with Gradle Files" 即可生效。' -ForegroundColor Cyan
Write-Host '如果仍然报错，先删掉半截下载缓存：'
Write-Host "  Remove-Item -Recurse -Force `"$env:USERPROFILE\.gradle\wrapper\dists\gradle-$version-bin`""