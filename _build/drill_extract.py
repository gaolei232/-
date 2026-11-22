# -*- coding: utf-8 -*-
"""把「二、专项练习（做·练）」的全部源文件抽取成纯文本，供专项题库解析器使用。

产物：
  1. _build/raw_drill/<相对路径>__<扩展名>.txt
  2. _build/drill_extract_report.json  每个文件的抽取结果

规则：
  - .docx  : extract_docx_full（正文+表格+文本框+公式）
  - .pdf   : pdftotext -raw（Git 自带）
  - .doc   : 先查 _build/tmp/drill_docx/<safe>.docx 缓存（Word COM 转出的），
             没有就用 libreoffice-kit CLI 转 docx 再抽取；CLI 失败的记 fail 等 COM 补齐
  - 文件名带 `_2` 的副本：若同目录存在去掉 `_2` 的同扩展名文件则跳过
"""
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_docx_full import extract as extract_docx  # noqa: E402

BASE = r"C:\Users\86138\Desktop\习题"
SRC = os.path.join(BASE, "二、专项练习（做·练）")
OUT = os.path.join(BASE, "_build", "raw_drill")
TMP = os.path.join(BASE, "_build", "tmp")
DOCX_CACHE = os.path.join(TMP, "drill_docx")
REPORT = os.path.join(BASE, "_build", "drill_extract_report.json")

NODE = r"G:\DSH\DSH NEXT\resources\runtime\x64\primary-runtime\dependencies\node\bin\node.exe"
CLI = r"G:\DSH\DSH NEXT\resources\app.asar.unpacked\node_modules\@deepseek-ai\libreoffice-kit\lib\cli.js"
PDFTOTEXT = r"C:\Program Files\Git\mingw64\bin\pdftotext.exe"

BAD = re.compile(r'[\\/:*?"<>|]')


def safe(rel):
    return BAD.sub("_", rel.replace(os.sep, "__"))


def pick_files():
    """列出要抽取的文件；跳过 `_2` 副本"""
    out = []
    skipped = []
    for dirpath, _dirnames, names in os.walk(SRC):
        for n in sorted(names):
            p = os.path.join(dirpath, n)
            stem, ext = os.path.splitext(n)
            ext = ext.lower()
            if ext not in (".doc", ".docx", ".pdf"):
                continue
            if stem.endswith("_2"):
                base = os.path.join(dirpath, stem[:-2] + ext)
                if os.path.exists(base):
                    skipped.append(p)
                    continue
            out.append(p)
    return out, skipped


def convert_doc(src, cache_name):
    """doc -> docx；返回 docx 路径或 None"""
    cached = os.path.join(DOCX_CACHE, cache_name + ".docx")
    if os.path.exists(cached) and os.path.getsize(cached) > 2000:
        return cached
    os.makedirs(TMP, exist_ok=True)
    tmp_out = os.path.join(TMP, cache_name + ".docx")
    logf = os.path.join(TMP, "drill_doc_convert.log")
    try:
        # 沙箱下不能用管道捕获子进程输出（named pipe 被禁），改为重定向到文件
        with open(logf, "wb") as lf:
            r = subprocess.run([NODE, CLI, "convert", "--input", src, "--output", tmp_out],
                               stdout=lf, stderr=subprocess.STDOUT,
                               timeout=180, check=False)
        try:
            msg = open(logf, encoding="utf-8", errors="ignore").read()[:200]
        except Exception:  # noqa: BLE001
            msg = ""
    except Exception as e:  # noqa: BLE001
        msg = "EXC " + str(e)
    if os.path.exists(tmp_out) and os.path.getsize(tmp_out) > 2000:
        os.makedirs(DOCX_CACHE, exist_ok=True)
        os.replace(tmp_out, cached)
        return cached
    return None, msg


def pdf_text(src, dst):
    r = subprocess.run([PDFTOTEXT, "-raw", "-enc", "UTF-8", src, dst],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       timeout=600, check=False)
    return r.returncode, os.path.exists(dst)


def main():
    os.makedirs(OUT, exist_ok=True)
    files, skipped = pick_files()
    print("files=%d skipped_dupes=%d" % (len(files), len(skipped)), flush=True)
    report = []
    for i, p in enumerate(files, 1):
        rel = os.path.relpath(p, SRC)
        stem, ext = os.path.splitext(rel)
        ext = ext.lower()
        name = safe(stem) + "__" + ext.lstrip(".")
        txt = os.path.join(OUT, name + ".txt")
        if os.path.exists(txt) and os.path.getsize(txt) > 100:
            report.append({"src": rel, "txt": name + ".txt", "ok": True,
                           "chars": os.path.getsize(txt), "cached": True})
            continue
        ok, err, chars = False, "", 0
        try:
            if ext == ".docx":
                text = extract_docx(p)
            elif ext == ".pdf":
                rc, made = pdf_text(p, txt)
                ok = made and os.path.getsize(txt) > 100
                if not ok:
                    err = "pdftotext rc=%s" % rc
                report.append({"src": rel, "txt": name + ".txt", "ok": ok,
                               "chars": os.path.getsize(txt) if made else 0, "error": err})
                print("[%d/%d] %s -> %s" % (i, len(files), rel, ok), flush=True)
                continue
            else:  # .doc
                r = convert_doc(p, safe(stem))
                if isinstance(r, tuple):
                    docx, msg = r
                    err = "convert-fail " + msg
                    report.append({"src": rel, "txt": name + ".txt", "ok": False,
                                   "chars": 0, "error": err})
                    print("[%d/%d] %s -> FAIL %s" % (i, len(files), rel, msg[:80]), flush=True)
                    continue
                text = extract_docx(r)
            if len(text.strip()) >= 100:
                open(txt, "w", encoding="utf-8").write(text)
                ok, chars = True, len(text)
        except Exception as e:  # noqa: BLE001
            err = "EXC " + str(e)[:150]
        report.append({"src": rel, "txt": name + ".txt", "ok": ok, "chars": chars, "error": err})
        print("[%d/%d] %s -> %s (%d)" % (i, len(files), rel, ok, chars), flush=True)

    with open(REPORT, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    bad = [r for r in report if not r["ok"]]
    print("DONE ok=%d fail=%d skipped=%d" % (len(report) - len(bad), len(bad), len(skipped)))
    for r in bad:
        print("  FAIL", r["src"], "|", r.get("error", "")[:100])


if __name__ == "__main__":
    main()