"""把套卷目录下的 .docx 全量抽取为 txt（含表格、文本框、公式文本），存到 _build/raw_docx/"""
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_docx_full import extract  # noqa: E402

SRC = r"C:\Users\86138\Desktop\习题\三、套卷模考与冲刺"
OUT = r"C:\Users\86138\Desktop\习题\_build\raw_docx"
os.makedirs(OUT, exist_ok=True)


def safe_name(rel):
    for ch in '\\/:*?"<>|':
        rel = rel.replace(ch, "_")
    return rel


def main():
    files = glob.glob(os.path.join(SRC, "**", "*.docx"), recursive=True)
    ok = 0
    for f in sorted(files):
        rel = os.path.relpath(f, SRC)
        base = safe_name(rel).replace("__", "_")  # 防止与 pdf 命名规则冲突
        base = base[:-5] if base.lower().endswith(".docx") else base
        base = base.replace("_", "__", 1) if "__" not in base else base
        # 统一为 folder__filename 形式：第一层目录用 __ 连接
        parts = rel.split(os.sep)
        name = "__".join([parts[0]] + parts[1:])
        name = safe_name(name)
        name = name[:-5] if name.lower().endswith(".docx") else name
        txt = os.path.join(OUT, name + ".txt")
        try:
            text = extract(f)
        except Exception as e:
            print("[FAIL]", os.path.basename(f), e)
            continue
        if len(text) < 200:
            print("[SKIP tiny]", os.path.basename(f), len(text))
            continue
        open(txt, "w", encoding="utf-8").write(text)
        ok += 1
        print("[ok] %-58s %6d 字" % (os.path.basename(f)[:58], len(text)))
    print("DONE", ok, "/", len(files))


if __name__ == "__main__":
    main()