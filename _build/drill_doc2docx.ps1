# 把 LibreOffice 转不了的 .doc 用本机 Word 转成 docx，供 drill_extract.py 复用
# 用法（需要 danger-full-access，Word COM 在沙箱下会被拒绝）：
#   powershell -File _build\drill_doc2docx.ps1
$ErrorActionPreference = 'Continue'
$base = 'C:\Users\86138\Desktop\习题'
$src  = Join-Path $base '二、专项练习（做·练）'
$report = Join-Path $base '_build\drill_extract_report.json'
$cache  = Join-Path $base '_build\tmp\drill_docx'
New-Item -ItemType Directory -Force -Path $cache | Out-Null

if (-not (Test-Path -LiteralPath $report)) { throw "缺少 $report，先跑 drill_extract.py" }
$rows = Get-Content -LiteralPath $report -Raw -Encoding UTF8 | ConvertFrom-Json
$failed = @($rows | Where-Object { -not $_.ok -and $_.src -like '*.doc' })
Write-Host "failed doc = $($failed.Count)"

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$word.Options.SaveInterval = 0
$done = 0; $bad = 0
try {
  foreach ($r in $failed) {
    $srcPath = Join-Path $src $r.src
    $rel = $r.src -replace '\.doc$',''
    $safe = $rel -replace '\\','__'
    $safe = $safe -replace '[\\/:*?"<>|]','_'
    $dst = Join-Path $cache ($safe + '.docx')
    if ((Test-Path -LiteralPath $dst) -and ((Get-Item -LiteralPath $dst).Length -gt 2000)) { $done++; continue }
    try {
      $doc = $word.Documents.Open($srcPath, $false, $true)
      try { $doc.SaveAs2($dst, 16) } catch { $doc.SaveAs([ref][string]$dst, [ref]16) }
      $doc.Close($false)
      $done++
      Write-Host ("[ok] {0} -> {1}" -f $r.src, (Get-Item -LiteralPath $dst).Length)
    } catch {
      $bad++
      Write-Host ("[FAIL] {0}: {1}" -f $r.src, $_.Exception.Message)
    }
  }
} finally {
  $word.Quit()
  [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
}
Write-Host "DONE converted=$done failed=$bad"