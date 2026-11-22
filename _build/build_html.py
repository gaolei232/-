import json
import os
import sys

BASE = r"C:\Users\86138\Desktop\习题"
TPL = os.path.join(BASE, "_build", "template.html")
BANK = os.path.join(BASE, "_build", "bank_final.json")
DRILL = os.path.join(BASE, "_build", "drill_bank.json")
STUDY = os.path.join(BASE, "_build", "study_manifest.json")
OUT = os.path.join(BASE, "延长石油套卷模考.html")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import classify  # noqa: E402

bank = json.load(open(BANK, encoding="utf-8"))
drill = json.load(open(DRILL, encoding="utf-8")) if os.path.exists(DRILL) else []
clf = classify.enrich(bank, drill)
payload = json.dumps(bank, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
dp = json.dumps(drill, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

study = json.load(open(STUDY, encoding="utf-8"))
spayload = json.dumps(study, ensure_ascii=False, separators=(",", ":"))
spayload = spayload.replace("</", "<\\/")

html = open(TPL, encoding="utf-8").read()
assert "__BANK__" in html and "__STUDY__" in html and "__DRILL__" in html
html = html.replace("__BANK__", payload)
html = html.replace("__STUDY__", spayload)
html = html.replace("__DRILL__", dp)
open(OUT, "w", encoding="utf-8").write(html)

size = os.path.getsize(OUT)
total = sum(len(p["questions"]) for p in bank)
print(f"wrote {OUT}")
print(f"papers={len(bank)} questions={total} size={size/1024/1024:.2f} MB")
st = study.get("stats", {})
dq = sum(len(p["questions"]) for p in drill)
print(f"drill: sets={len(drill)} questions={dq}")
print("classify: 套卷", {k: v for k, v in clf["bank"].items() if v}, "| 专项", {k: v for k, v in clf["drill"].items() if v})
print(f"study: files={st.get('files')} pages={st.get('pages')} "
      f"assets={st.get('assets')} copied_assets_mb={st.get('bytes', 0)/1048576:.1f}")