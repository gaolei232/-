# 用 pdftotext -raw 重新提取所有 PDF（-raw 保持内容流顺序，避免公式/栏目造成的错位）
$ErrorActionPreference = 'Continue'
$GITBIN = 'C:\Program Files\Git\mingw64\bin'
$env:PATH = "$GITBIN;$env:PATH"
$PDFTOTEXT = Join-Path $GITBIN 'pdftotext.exe'
$SRC = 'C:\Users\86138\Desktop\习题\三、套卷模考与冲刺'
$OUT = 'C:\Users\86138\Desktop\习题\_build\raw'

function SafeName([string]$rel) {
  ($rel -replace '\\', '__') -replace '[\\/:*?"<>|]', '_'
}

$pdfs = Get-ChildItem $SRC -Recurse -File | Where-Object { $_.Extension -ieq '.pdf' }
$ok = 0; $fail = 0
foreach ($p in $pdfs) {
  $rel = $p.FullName.Substring($SRC.Length + 1)
  $base = (SafeName $rel) -replace '\.pdf$', ''
  $txt = Join-Path $OUT "$base.txt"
  & $PDFTOTEXT -enc UTF-8 -raw $p.FullName $txt 2>&1 | Out-Null
  if ((Test-Path -LiteralPath $txt) -and ((Get-Item -LiteralPath $txt).Length -gt 100)) {
    $ok++
    Write-Host ("[ok] {0} -> {1} bytes" -f $p.Name, (Get-Item $txt).Length)
  } else {
    $fail++
    Write-Host ("[FAIL] {0}" -f $p.Name)
  }
}
Write-Host "DONE ok=$ok fail=$fail"