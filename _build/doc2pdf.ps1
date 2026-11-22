$ErrorActionPreference = 'Stop'
$root = "C:\Users\86138\Desktop\习题\一、学习资料（看·学）"
$outDir = "C:\Users\86138\Desktop\习题\_build\study_pdf"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

$docs = @(
  @{ src = "1-公共基础知识\07-内部讲义\3.公共基础知识（综合知识）内部讲义 .doc";                       name = "gg07_neibu.pdf" },
  @{ src = "1-公共基础知识\08-企业文化\新版陕西延长石油集团企业文化常考知识点总结.doc";                 name = "gg08_qiye.pdf" },
  @{ src = "2-职业能力测试（行测）\03-金牌讲义\常识判断\1.最新版【行测讲义】常识判断（共30页）.doc";    name = "xc03_changshi.pdf" },
  @{ src = "2-职业能力测试（行测）\03-金牌讲义\言语理解\3.最新版【行测讲义】言语理解与表达（共231页）.doc"; name = "xc03_yanyu.pdf" }
)

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
  foreach ($d in $docs) {
    $src = Join-Path $root $d.src
    $dst = Join-Path $outDir $d.name
    if (-not (Test-Path -LiteralPath $src)) { "MISSING: $($d.src)"; continue }
    if (Test-Path -LiteralPath $dst) { "SKIP exists: $($d.name) ($([math]::Round((Get-Item -LiteralPath $dst).Length/1MB,1)) MB)"; continue }
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $doc = $word.Documents.Open($src, $false, $true)
    try { $doc.SaveAs2($dst, 17) } catch { $doc.SaveAs([ref][string]$dst, [ref]17) }
    $doc.Close($false)
    $sw.Stop()
    "$($d.name): $([math]::Round((Get-Item -LiteralPath $dst).Length/1MB,1)) MB in $([math]::Round($sw.Elapsed.TotalSeconds,1))s"
  }
} finally {
  $word.Quit()
}