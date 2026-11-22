$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot          # 习题 根目录
$jdk = Join-Path $PSScriptRoot 'jdk21'

if (-not (Test-Path (Join-Path $jdk 'bin\java.exe'))) {
    Write-Host '== 下载 JDK 21（华为云镜像）=='
    $zip = Join-Path $PSScriptRoot 'jdk21.zip'
    curl.exe -L --fail --retry 3 -o $zip 'https://mirrors.huaweicloud.com/openjdk/21.0.2/openjdk-21.0.2_windows-x64_bin.zip'
    if (-not (Test-Path $zip)) { throw 'JDK 下载失败' }
    Write-Host ('zip MB: ' + [math]::Round((Get-Item $zip).Length / 1MB, 1))
    Write-Host '== 解压 =='
    $tmp = Join-Path $PSScriptRoot 'jdk21tmp'
    Expand-Archive -Path $zip -DestinationPath $tmp -Force
    $inner = Get-ChildItem $tmp -Directory | Select-Object -First 1
    Move-Item $inner.FullName $jdk
    Remove-Item $zip -Force
    Remove-Item $tmp -Recurse -Force
}

Write-Host '== JDK =='
& (Join-Path $jdk 'bin\java.exe') -version 2>&1

$env:JAVA_HOME = $jdk
$env:PATH = (Join-Path $jdk 'bin') + ';' + $env:PATH
Set-Location (Join-Path $root 'app-mobile\android')

Write-Host '== gradle assembleDebug =='
& .\gradlew.bat assembleDebug --no-daemon --console=plain 2>&1

Write-Host '== 产物 =='
Get-ChildItem (Join-Path $root 'app-mobile\android\app\build\outputs\apk\debug') -ErrorAction SilentlyContinue |
    Select-Object Name, @{n = 'MB'; e = { [math]::Round($_.Length / 1MB, 1) } } | Format-Table -AutoSize