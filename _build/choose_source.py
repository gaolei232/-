"""对比同一份试卷的 pdf 版与 docx 版文本，保留能解析出更多「带答案的题」的那份。

输出到 _build/raw_final/，文件名与原来一致，供 parse.py 使用。
"""
import glob
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parse  # noqa: E402

RAW_PDF = r"C:\Users\86138\Desktop\习题\_build\raw"
RAW_DOCX = r"C:\Users\86138\Desktop\习题\_build\raw_docx"
OUT = r"C:\Users\86138\Desktop\习题\_build\raw_final"


def score(text: str):
    """返回 (题目数, 有答案的题数)"""
    try:
        t = parse.normalize(text)
        t = parse.PAGE_NOISE.sub("\n", t)
        body, area = parse.split_answer_region(t)
        key = parse.parse_key_area(area)
        alist = parse.parse_answer_list(body)
        if alist:
            amap, apos = alist
            for n, a in amap.items():
                key.setdefault(n, {"ans": a, "expl": ""})
            body = body[:apos]
        body, inline = parse.strip_explanations(body)
        for n, (a, e) in inline.items():
            key.setdefault(n, {"ans": a, "expl": e})
        qs = parse.build_questions(body)
        good = sum(1 for q in qs if key.get(q["num"], {}).get("ans"))
        return len(qs), good
    except Exception:
        return 0, 0


def main():
    os.makedirs(OUT, exist_ok=True)
    pdfs = {os.path.basename(p): p for p in glob.glob(os.path.join(RAW_PDF, "*.txt"))}
    docxs = {os.path.basename(p): p for p in glob.glob(os.path.join(RAW_DOCX, "*.txt"))}
    names = sorted(set(pdfs) | set(docxs))

    picked = {"pdf": 0, "docx": 0, "only": 0}
    rows = []
    for name in names:
        cands = []
        if name in pdfs:
            t = open(pdfs[name], encoding="utf-8", errors="replace").read()
            cands.append(("pdf", pdfs[name], score(t)))
        if name in docxs:
            t = open(docxs[name], encoding="utf-8", errors="replace").read()
            cands.append(("docx", docxs[name], score(t)))
        # 择优：先比「有答案的题数」，再比题目总数；相同则优先 pdf（此前已验证过）
        best = max(cands, key=lambda c: (c[2][1], c[2][0], 1 if c[0] == "pdf" else 0))
        shutil.copyfile(best[1], os.path.join(OUT, name))
        if len(cands) == 1:
            picked["only"] += 1
        else:
            picked[best[0]] += 1
        rows.append((name[:56], [("pdf", c[2]) for c in cands if c[0] == "pdf"],
                     [("docx", c[2]) for c in cands if c[0] == "docx"], best[0]))

    print("选用统计:", picked)
    print()
    changed = [r for r in rows if len(r[1]) and len(r[2]) and r[1][0][1] != r[2][0][1]]
    print("两版结果不同的套卷:", len(changed))
    for name, p, d, best in changed:
        print("  %-56s pdf=%s docx=%s → %s" % (name, p[0][1], d[0][1], best))


if __name__ == "__main__":
    main()