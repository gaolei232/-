import sys
import docx

d = docx.Document(sys.argv[1])
parts = []
for p in d.paragraphs:
    parts.append(p.text)
for t in d.tables:
    for row in t.rows:
        parts.append(" ".join(c.text for c in row.cells))
open(sys.argv[2], "w", encoding="utf-8").write("\n".join(parts))