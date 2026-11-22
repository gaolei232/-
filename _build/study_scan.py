import os, json, pypdf

root = r"C:\Users\86138\Desktop\习题\一、学习资料（看·学）"
out = []
tot = 0
for dp, dn, fn in os.walk(root):
    for f in sorted(fn):
        p = os.path.join(dp, f)
        rel = os.path.relpath(p, root)
        size = os.path.getsize(p)
        n = None
        if f.lower().endswith(".pdf"):
            try:
                n = len(pypdf.PdfReader(p).pages)
                tot += n
            except Exception as e:
                n = "ERR:" + str(e)[:40]
        out.append({"rel": rel, "size": size, "pages": n})
        print("%6s %8.1fMB %s" % (n, size / 1048576, rel))
print("TOTAL PAGES", tot, "FILES", len(out))
json.dump(out, open(r"C:\Users\86138\Desktop\习题\_build\study_scan.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)