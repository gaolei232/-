#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
_build/bank.json -> _build/bank_final.json

- 按源文件内容去重（名师押题目录是 行测模拟卷 的同名副本）
- 去掉套内重复题
- 过滤伪题（选项缺失/题干异常/答案不在选项内）
- 统一试卷标题、分类、题量
"""
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from quality import analyze  # noqa: E402

SRC = r"C:\Users\86138\Desktop\习题\_build\bank.json"
EXTRA = r"C:\Users\86138\Desktop\习题\_build\bank_extra.json"
OCR_BANK = r"C:\Users\86138\Desktop\习题\_build\bank_ocr.json"
NA_BANK = r"C:\Users\86138\Desktop\习题\_build\bank_na.json"

# 题本版没有答案的卷子，按这套对应关系并进同名卷（否则会多出一份「只有无答案题」的卷子）
NA_TITLE_MAP = {
    "公基模考特训（模拟卷1）题本": "模拟套卷1",
    "公基模考特训（模拟卷2）题本": "模拟套卷2",
    "公基模考特训（模拟卷3）题本": "模拟套卷3",
    "公基模考特训（模拟卷4）题本": "模拟套卷4",
    "公基模考特训（模拟卷5）题本": "模拟套卷5",
    "公基模考特训（模拟卷6）题本": "模拟套卷6",
}


def title_key(t: str) -> str:
    """标题归一：去掉出版社/集团前缀和括号空格，用来认出「同一套卷换了名字」"""
    t = (t or "").replace("新版陕西延长石油集团招聘考试", "").replace("陕西延长石油集团招聘", "")
    t = t.replace("【全新版】", "").replace("新版", "")
    return re.sub(r"[（）()\s·、]", "", t)
OUT = r"C:\Users\86138\Desktop\习题\_build\bank_final.json"
FIXFILE = r"C:\Users\86138\Desktop\习题\_build\manual_fixes.json"

MANUAL = {}
if os.path.exists(FIXFILE):
    _raw = json.load(open(FIXFILE, encoding="utf-8"))
    MANUAL = {k: v for k, v in _raw.items() if not k.startswith("_")}

FOLDER_ORDER = {
    "1-历年真题（2019-2023）": 1,
    "2-公基模拟套卷": 2,
    "5-考前冲刺EPI全真": 3,
    "3-行测模拟卷": 4,
    "6-历年试题汇编模拟卷": 5,
    "4-名师押题模拟卷30套": 6,
}


def dedupe_key(q):
    stem = re.sub(r"\s+", "", q["stem"])
    opts = "".join(f"{k}{re.sub(r'\\s+', '', v)}" for k, v in sorted(q["options"].items()))
    return hashlib.md5((stem + opts).encode("utf-8")).hexdigest()


NOISE = re.compile(
    r"第\s*\d+\s*页\s*共\s*\d+\s*页|绝密真题[ ]*禁止外泄|绝密真题|【真题保密】|www\.chinaexam\.org"
    r"|【[^】]{0,6}选\s*[A-D]\s*】"
)


def clean_stem(s: str) -> str:
    s = NOISE.sub(" ", s)
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"^[\s、，。.]+", "", s)
    # 去掉残留的章节标题
    s = re.sub(r"^(?:[一二三四五六七八九十]+、)?[^。？]{0,12}(?:题|部分)[^。？]{0,12}[。，]\s*", "", s) if len(s) > 60 else s
    return s.strip()


def clean_opt_text(s: str) -> str:
    """选项里偶尔粘了下一部分的标题/引导语，截掉。"""
    s = re.sub(r"第[一二三四五六七八九十]+部分(?:结束)?[\s\S]*$", "", s) if "部分" in s else s
    s = re.sub(r"请(?:开始|继续)答题[\s\S]*$", "", s)
    s = re.sub(r"\s+", " ", s).strip(" ；;，,。.")
    return s


def valid(q, allow_na=False):
    na = allow_na and q.get("na") and not q.get("answer")
    if not na:
        if not q.get("answer"):
            return False
        ans = q["answer"]
        if not re.fullmatch(r"[A-D]{1,4}", ans):
            return False
        if any(c not in q["options"] for c in ans):
            return False
    if len(q["options"]) < 2:
        return False
    if any(len(v.strip()) == 0 for v in q["options"].values()):
        return False
    if len(q["stem"]) < 6:
        return False
    # 题干几乎没有中文、却有成串英文字母：多是「字符查找」类排版题被抽成了乱码
    #（数字推理题如「8，16，22，24，（ ）」没有中文但要保留）
    _cjk = len(re.findall(r"[\u4e00-\u9fff]", q["stem"]))
    _latin = len(re.findall(r"[A-Za-z]", q["stem"]))
    # 非中文、非 ASCII 的字母（知觉速度/字符替换题抽出来是一串乱码符号）
    _weird = sum(1 for c in q["stem"] if ord(c) > 127 and c.isalpha()
                 and not ("\u4e00" <= c <= "\u9fff"))
    if _cjk < 4 and (_latin >= 6 or _weird >= 4):
        return False
    # 题干里混进大量选项标记说明切分失败
    if len(re.findall(r"(?<![A-Za-z])(?:A|B|C|D)[．.、]", q["stem"])) >= 2:
        return False
    # 选项文本里又以题号开头 => 两题被并到一起
    for v in q["options"].values():
        if re.match(r"^\s*\d{1,3}\s*[.．、]", v):
            return False
        if re.search(r"[。．][ ]*\d{1,3}\s*[.．、][ ]*\S{4,}", v[40:]):
            return False
    return True


def clean_expl(e: str, num) -> str:
    if not e:
        return ""
    # 讲义体解析以「【选 B】」收尾，其后往往粘了下一题题干，先按此截断（必须在 NOISE 之前）
    m = re.search(r"【\s*选\s*[A-D]{1,4}\s*】", e)
    if m:
        e = e[: m.end()]
    e = NOISE.sub(" ", e)
    # 解析末尾粘了下一题题干：遇到「N.」「N、」且后面还有较长内容就截断
    for m in re.finditer(r"(?<![\d.])(\d{1,3})[ ]*[.．、]", e[20:]):
        pos = m.start() + 20
        if abs(int(m.group(1)) - int(num)) == 1 and len(e) - pos > 15:
            e = e[:pos]
            break
    e = re.sub(r"\s+", " ", e).strip()
    return e


CAT_LABEL = {
    "1-历年真题（2019-2023）": "历年真题",
    "2-公基模拟套卷": "公基模拟套卷",
    "3-行测模拟卷": "行测模拟卷",
    "6-历年试题汇编模拟卷": "历年试题汇编卷",
    "4-名师押题模拟卷30套": "名师押题卷",
}


def sub_of(cat: str, title: str) -> str:
    """二级分类：卷系"""
    if cat.startswith("1-"):
        return "2019–2023 历年真题"
    if cat.startswith("2-"):
        return "王军涛 · 公基模拟套卷"
    if cat.startswith("6-"):
        return "历年试题汇编模拟卷（一～四）"
    if cat.startswith("4-"):
        return "名师押题模拟卷"
    if cat.startswith("3-"):
        if "行政职业能力测验模拟预测" in title:
            return "行政职业能力测验模拟预测试卷"
        return "新版职业能力测验模拟卷"
    return CAT_LABEL.get(cat, cat)


def main():
    papers = json.load(open(SRC, encoding="utf-8"))

    # 只有题本、没答案的卷子：用 borrow_answers.py 借同题答案后补进来，
    # 同一个源文件就替换掉 bank.json 里那份不完整的
    extra_path = EXTRA
    if os.path.exists(extra_path):
        extra = json.load(open(extra_path, encoding="utf-8"))
        by_src = {e["source"]: e for e in extra}
        before_n = len(papers)
        papers = [by_src.pop(p["source"], p) for p in papers] + list(by_src.values())
        print(f"并入借答案卷子 {len(extra)} 套（替换/新增）")

    # OCR 出来的扫描版试卷（极致模考 8 套 + 真题 4 套）
    if os.path.exists(OCR_BANK):
        ocr_papers = json.load(open(OCR_BANK, encoding="utf-8"))
        have = {p["source"] for p in papers}
        papers += [p for p in ocr_papers if p["source"] not in have]
        print(f"并入 OCR 试卷 {len(ocr_papers)} 套")

    # 无答案题（题本版）：尽量并进已有的同一套卷，并不上就单独成卷
    if os.path.exists(NA_BANK):
        na_papers = json.load(open(NA_BANK, encoding="utf-8"))
        by_src = {p.get("source"): p for p in papers}
        by_sig = {(p.get("folder"), p.get("title"), p.get("variant")): p for p in papers}
        merged_n = new_n = 0
        for np_ in na_papers:
            qs = np_["questions"]
            target = by_src.get(np_["source"]) or by_sig.get(
                (np_["folder"], np_["title"], np_["variant"]))
            if target is None and np_["title"] in NA_TITLE_MAP:
                want = NA_TITLE_MAP[np_["title"]]
                for p in papers:
                    if p.get("title") == want:
                        target = p
                        break
            if target is None:
                for p in papers:
                    if title_key(p.get("title") or "") == title_key(np_["title"]):
                        target = p
                        break
            if target is not None:
                target["questions"] = list(target["questions"]) + qs
                merged_n += 1
            else:
                papers.append(np_)
                new_n += 1
        print(f"并入无答案题 {len(na_papers)} 组（并进已有卷 {merged_n} 组，单独成卷 {new_n} 组）")
    # 内容级去重
    seen_hash = {}
    out = []
    dropped = {}
    for p in papers:
        sig = hashlib.md5(
            ("|".join(sorted(dedupe_key(q) for q in p["questions"])) + p["title"]).encode("utf-8")
        ).hexdigest()
        qsig = hashlib.md5("|".join(sorted(dedupe_key(q) for q in p["questions"])).encode("utf-8")).hexdigest()
        if qsig in seen_hash and p["questions"]:
            dropped[p["source"]] = seen_hash[qsig]
            continue
        seen_hash[qsig] = p["source"]
        seen_hash.setdefault(sig, p["source"])
        out.append(p)

    final = []
    for p in out:
        qs = []
        seen = set()
        for q in p["questions"]:
            q["stem"] = clean_stem(q["stem"])
            q["options"] = {k: clean_opt_text(v) for k, v in q["options"].items()}
            is_na = bool(q.get("na")) and not q.get("answer")
            if not valid(q, allow_na=is_na):
                continue
            k = dedupe_key(q)
            if k in seen:
                continue
            seen.add(k)

            expl = clean_expl(q.get("expl", ""), q["num"])
            broken, raw_expl = 0, ""
            # 公式/图形没进文本层 -> 残句，隐藏原文并可查看
            if expl:
                bad, _score, _why = analyze(expl)
                if bad:
                    broken, raw_expl, expl = 1, expl, ""
            manual = 0
            proc = ""
            fix = MANUAL.get(p["source"], {}).get(str(q["num"]))
            if fix:
                manual = 1
                if fix.get("e"):
                    expl, broken, raw_expl = fix["e"], 0, ""
                if fix.get("p"):
                    proc, broken, raw_expl = fix["p"], 0, ""

            item = {
                "n": q["num"],
                "q": q["stem"],
                "o": [q["options"][c] for c in sorted(q["options"])],
                "a": "" if is_na else q["answer"],
                "e": expl,
            }
            if is_na:
                item["na"] = 1
            if proc:
                item["p"] = proc
            if broken:
                item["bq"] = 1
                item["re"] = raw_expl
            if manual:
                item["mf"] = 1
            qs.append(item)
        if len(qs) < 8:
            continue
        title = p["title"]
        if p["variant"] and "名师押题" not in p["folder"]:
            title = f"{title}（{p['variant']}）"
        final.append(
            {
                "id": re.sub(r"\W+", "-", f"{p['folder']}-{title}")[:60],
                "title": title,
                "cat": p["folder"],
                "catLabel": CAT_LABEL.get(p["folder"], p["folder"]),
                "sub": sub_of(p["folder"], title),
                "order": FOLDER_ORDER.get(p["folder"], 9),
                "questions": qs,
            }
        )

    # 卷级去重：同一套卷在题库里换了名字（公基模考特训≈模拟套卷、新版职业能力测验≈预测试卷），
    # 题集重合 >85% 视为同一套，保留题目多、带解析多的那份
    def qset(paper):
        # 只用题干（前 40 字）做卷级去重：同一套卷的两个副本选项文字常有细微差别
        return {
            re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", q["q"])[:40]
            for q in paper["questions"]
        }

    kept = []
    for p in sorted(final, key=lambda x: (-len(x["questions"]),
                                          "题本" in x["title"],
                                          -sum(1 for q in x["questions"] if q.get("e")))):
        s = qset(p)
        target = None
        for k in kept:
            t = qset(k)
            small = min(len(s), len(t))
            if small and len(s & t) / small > 0.85:
                target = k
                break
        if target is None:
            kept.append(p)
            continue
        # 是同一套卷的另一个副本：把对方独有的题并进来，别白丢
        have = qset(target)
        for q in p["questions"]:
            kk = re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", q["q"])[:40]
            if kk and kk not in have:
                target["questions"].append(q)
                have.add(kk)
    dropped_dup = len(final) - len(kept)
    final = kept

    for p in final:
        p["questions"].sort(key=lambda q: q["n"])

    final.sort(key=lambda x: (x["order"], x["title"]))
    for i, p in enumerate(final):
        p["idx"] = i

    total = sum(len(p["questions"]) for p in final)
    wexp = sum(1 for p in final for q in p["questions"] if q["e"])
    print(f"papers={len(final)} questions={total} with_expl={wexp}")
    print("dropped duplicate papers:", len(dropped), "| 卷级去重:", dropped_dup)
    json.dump(final, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    from collections import Counter

    c = Counter(p["cat"] for p in final)
    for k in sorted(c, key=lambda k: FOLDER_ORDER.get(k, 9)):
        sub = [p for p in final if p["cat"] == k]
        print(f"  {k}: {c[k]} 套 / {sum(len(x['questions']) for x in sub)} 题")


if __name__ == "__main__":
    main()
