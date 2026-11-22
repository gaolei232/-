import json
from collections import Counter

b = json.load(open(r"C:\Users\86138\Desktop\习题\_build\bank_final.json", encoding="utf-8"))
c = Counter(p["cat"] for p in b)
order = ["1-历年真题（2019-2023）", "2-公基模拟套卷", "3-行测模拟卷", "6-历年试题汇编模拟卷", "4-名师押题模拟卷30套"]
for k in order:
    sub = [p for p in b if p["cat"] == k]
    qn = sum(len(x["questions"]) for x in sub)
    en = sum(1 for x in sub for qq in x["questions"] if qq["e"])
    print(f"| {k} | {len(sub)} | {qn} | {en} |")
total = sum(len(p["questions"]) for p in b)
expl = sum(1 for p in b for q in p["questions"] if q["e"])
print(f"TOTAL papers={len(b)} questions={total} expl={expl} rate={expl/total*100:.1f}%")
print("multi:", sum(1 for p in b for q in p["questions"] if len(q["a"]) > 1))