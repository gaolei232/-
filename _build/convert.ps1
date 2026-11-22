# 批量转换：.doc -> .docx -> .txt (python-docx)，.pdf -> .txt (pdftotext)
$ErrorActionPreference = 'Continue'

$NODE = 'G:\DSH\DSH NEXT\resources\runtime\x64\primary-runtime\dependencies\node\bin\node.exe'
$CLI  = 'G:\DSH\DSH NEXT\resources\app.asar.unpacked\node_modules\@deepseek-ai\libreoffice-kit\lib\cli.js'
$PY   = 'C:\Users\86138\.dsh\dsh-runtimes\dsh-next-primary-runtime\dependencies\python\python.exe'
$EXTRACT = 'C:\Users\86138\Desktop\习题\_build\extract_docx.py'
$GITBIN = 'C:\Program Files\Git\mingw64\bin'
$PDFTOTEXT = Join-Path $GITBIN 'pdftotext.exe'
$env:PATH = "$GITBIN;$env:PATH"

$SRC = 'C:\Users\86138\Desktop\习题\三、套卷模考与冲刺'
$OUT = 'C:\Users\86138\Desktop\习题\_build\raw'
$TMP = 'C:\Users\86138\Desktop\习题\_build\tmp'
New-Item -ItemType Directory -Force -Path $OUT, $TMP | Out-Null

function SafeName([string]$rel) {
  ($rel -replace '\\', '__') -replace '[\\/:*?"<>|]', '_'
}

$docs = Get-ChildItem $SRC -Recurse -File | Where-Object { $_.Extension -ieq '.doc' }
$pdfs = Get-ChildItem $SRC -Recurse -File | Where-Object { $_.Extension -ieq '.pdf' }
Write-Host "doc=$($docs.Count) pdf=$($pdfs.Count)"

$results = New-Object System.Collections.ArrayList
$i = 0

foreach ($d in $docs) {
  $i++
  $rel = $d.FullName.Substring($SRC.Length + 1)
  $base = SafeName $rel
  $base = $base -replace '\.doc$', ''
  $docx = Join-Path $TMP "$base.docx"
  $txt  = Join-Path $OUT "$base.txt"
  if ((Test-Path -LiteralPath $txt) -and ((Get-Item -LiteralPath $txt).Length -gt 200)) {
    [void]$results.Add([pscustomobject]@{ src = $d.FullName; ok = $true; cached = $true })
    continue
  }
  & $NODE $CLI convert --input $d.FullName --output $docx 2>&1 | Out-Null
  $ok = Test-Path -LiteralPath $docx
  if ($ok) {
    & $PY $EXTRACT $docx $txt 2>&1 | Out-Null
    $ok = (Test-Path -LiteralPath $txt) -and ((Get-Item -LiteralPath $txt).Length -gt 100)
    Remove-Item -LiteralPath $docx -Force -ErrorAction SilentlyContinue
  }
  [void]$results.Add([pscustomobject]@{ src = $d.FullName; ok = $ok })
  Write-Host ("[{0}/{1}] {2} -> {3}" -f $i, $docs.Count, $d.Name, $ok)
}

$j = 0
foreach ($p in $pdfs) {
  $j++
  $rel = $p.FullName.Substring($SRC.Length + 1)
  $base = SafeName $rel
  $base = $base -replace '\.pdf$', ''
  $txt = Join-Path $OUT "$base.txt"
  if ((Test-Path -LiteralPath $txt) -and ((Get-Item -LiteralPath $txt).Length -gt 100)) {
    [void]$results.Add([pscustomobject]@{ src = $p.FullName; ok = $true; cached = $true })
    continue
  }
  & $PDFTOTEXT -enc UTF-8 $p.FullName $txt 2>&1 | Out-Null
  $ok = (Test-Path -LiteralPath $txt) -and ((Get-Item -LiteralPath $txt).Length -gt 100)
  [void]$results.Add([pscustomobject]@{ src = $p.FullName; ok = $ok })
  Write-Host ("[pdf {0}/{1}] {2} -> {3}" -f $j, $pdfs.Count, $p.Name, $ok)
}

$results | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath (Join-Path $OUT '_report.json') -Encoding UTF8
$failed = $results | Where-Object { -not $_.ok }
Write-Host "DONE failures=$($failed.Count)"
$failed | ForEach-Object { Write-Host "FAIL: $($_.src)" }