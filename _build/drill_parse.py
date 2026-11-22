# -*- coding: utf-8 -*-
"""_build/raw_drill/*.txt -> _build/drill_bank.json（专项练习题库）

和二、三目录里的套卷题库分开：这里是按模块刷的专项题（练习为主）。

专项资料格式很杂，采用两套切题器取优：
  A. 标准切题器（沿用套卷 parse.py 的逻辑）：题号 + A/B/C/D 选项块 + 文末答案区
  B. 宽松切题器：题号写法多（试题N／第N题／无题号）、选项写成 A，/ A、/ 粘连、
     答案内联在题干或解析里（（C）、（答案：A）、故选C）
两套都跑，按「有答案的题数」择优，避免某一套在某类文件上崩掉。
"""
import json
import os
import re
import sys
import hashlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse import (  # noqa: E402
    normalize, PAGE_NOISE, split_answer_region, parse_key_area, parse_key_area2,
    parse_letter_grid, parse_answer_list, strip_explanations, build_questions,
    expl_quality, JUDGE_OPTS,
)

BASE = r"C:\Users\86138\Desktop\习题"
RAW = os.path.join(BASE, "_build", "raw_drill")
OUT = os.path.join(BASE, "_build", "drill_bank.json")
REPORT = os.path.join(BASE, "_build", "drill_parse_report.txt")

CATS = [
    ("1-公基各模块专项", "gk1", "公基 · 分模块专项", 1),
    ("2-公基基础强化特训", "gk2", "公基 · 基础强化特训", 2),
    ("7-公基预测押题题库", "gk3", "公基 · 预测押题库", 3),
    ("3-行测各模块专项", "xc1", "行测 · 分模块专项", 4),
    ("4-行测必做100题", "xc2", "行测 · 必做 100 题", 5),
    ("5-常识分类题库", "xc3", "行测 · 常识分类题库", 6),
    ("6-EPI综合能力题库", "epi", "行测 · EPI 综合能力题库", 7),
    ("8-行测专项预测押题", "xc4", "行测 · 专项预测押题", 8),
]
CAT_BY_DIR = {c[0]: c for c in CATS}

SUB_NAMES = {
    "01-政治（马哲·毛概·中特）": "政治（马哲·毛概·中特）",
    "02-法律": "法律", "03-经济": "经济", "04-管理": "管理",
    "05-公文写作": "公文写作", "06-历史人文": "历史人文",
    "07-地理国情": "地理国情", "08-科技常识": "科技常识",
    "09-公民道德": "公民道德", "10-计算机基础": "计算机基础",
    "11-事业单位": "事业单位",
    "01-言语理解": "言语理解", "02-数量关系": "数量关系",
    "03-判断推理": "判断推理", "04-资料分析": "资料分析",
    "05-常识判断": "常识判断",
}

STRIP_TITLE = [
    r"【[^】]{0,12}答案[^】]{0,12}】", r"（[^）]{0,12}答案[^）]{0,12}）",
    r"\([^)]{0,12}答案[^)]{0,12}\)",
    r"解析完整版", r"答案解析", r"答案及解析", r"参考答案", r"答案", r"解析",
    r"完整版", r"_2$", r"\s+",
]

# ---------------- 文本归一化 ----------------
OPT_STD = re.compile(r"(?<![0-9A-Za-z])([A-E])\s*[.．、:：)）]")
OPT_COMMA = re.compile(r"(?<![0-9A-Za-z])([A-E])[，,]")
OPT_GLUED = re.compile(r"(?<=[\u4e00-\u9fff])([A-E])[.．、:：]")
NUM = re.compile(r"(?<![\d.．])(\d{1,3})\s*[.．、]")
NUM2 = re.compile(r"(?:试题|第)\s*(\d{1,3})\s*(?:题)?\s*[:：、.．]")
NUM_BRACKET = re.compile(r"【(?:第\s*(\d{1,3})\s*题|例\s*(\d{1,3}))】")
BRACKET_TAG = re.compile(r"[\[［]\s*(答案|解析|正确答案)\s*[\]］]")

EXPL_START = re.compile(
    r"(?m)(?:^|\n)\s*(?:【解析】|【答案解析】|【答案】|【正确答案】|【参考答案】|解析|解答|分析|详解|说明)\s*[:：]?"
    r"|(?:故|所以|因此)?\s*(?:正确)?答案(?:是|为|选)?\s*[:：]"
    r"|本题正确答案\s*[:：]"
)
ANS_PATTERNS = [
    re.compile(r"【\s*(?:正确)?答案\s*】\s*[:：]?\s*([A-E]{1,5})(?![A-Za-z0-9])"),
    re.compile(r"(?:本题)?(?:正确)?答案(?:是|为|选)?\s*[:：]?\s*([A-E]{1,5})(?![A-Za-z0-9])"),
    re.compile(r"(?:故|所以|因此|应|那么|则|即)?\s*选\s*([A-E]{1,5})(?![A-Za-z0-9])"),
    re.compile(r"^\s*([A-E]{1,5})\s*$", re.M),
    re.compile(r"[（(]\s*([A-E]{1,5})\s*[）)]"),
]


def title_of(stem):
    t = stem
    for pat in STRIP_TITLE:
        t = re.sub(pat, "", t, flags=re.I)
    t = re.sub(r"(?:试题|题本)$", "", t)
    return t.strip(" _-·.、")


def is_answer_edition(stem):
    return bool(re.search(r"答案|解析完整版", stem)) and not re.search(r"试题|题库完整版|押题题库$", stem)


def pre_normalize(text):
    t = normalize(text)
    t = PAGE_NOISE.sub("\n", t)
    # [答案]：[解析] -> 【答案】/【解析】（部分题库用方括号）
    t = BRACKET_TAG.sub(lambda m: "【%s】" % m.group(1), t)
    # 【答案】：/【解析】： 去掉冒号，便于答案区解析
    t = re.sub(r"(【(?:答案|解析|正确答案)】)\s*[:：]", r"\1", t)
    # 重复字母 'A: A. xxx' -> 'A: xxx'
    t = re.sub(r"(?<![0-9A-Za-z])([A-E])\s*[:：]\s*\1\s*[.．、]\s*", r"\1: ", t)
    # '1．答案：C' -> '1．【答案】C'
    t = re.sub(r"(\d\s*[.．、])\s*(?:答案|正确答案)\s*[:：]\s*", r"\1【答案】", t)
    # 题号写法统一成 'N．'
    t = NUM2.sub(lambda m: "\n%d．" % int(m.group(1)), t)
    t = NUM_BRACKET.sub(lambda m: "\n%d．" % int(m.group(1) or m.group(2)), t)
    # 选项粘连在中文后面（'的模式C: '、'喜爱B. '）→ 拆到行首
    n_std = len(OPT_STD.findall(t))
    n_glued = len(OPT_GLUED.findall(t))
    if n_glued >= 100 or n_glued > max(8, n_std):
        t = OPT_GLUED.sub(lambda m: "\n%s." % m.group(1), t)
    n_std = len(OPT_STD.findall(t))
    n_comma = len(OPT_COMMA.findall(t))
    if n_comma > max(12, n_std):
        t = OPT_COMMA.sub(lambda m: "\n%s．" % m.group(1), t)
    return t


# ---------------- 通用小工具 ----------------
def clean_opt(s):
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"^[.．、:：)）\s]+", "", s)
    s = re.sub(r"[\s.．、；;，,。]+$", "", s)
    return s.strip()


def split_tail(opt_text):
    """最后一个选项后面常跟解析/答案，切出来作为解析，返回 (选项, 解析)"""
    mb = re.search(r"(?m)^[ \t]*([A-E]{1,5})[ \t]*$", opt_text)
    if mb and mb.start() > 0:
        return opt_text[:mb.start()], opt_text[mb.start():]
    m = EXPL_START.search(opt_text)
    if m and m.start() > 0:
        return opt_text[:m.start()], opt_text[m.start():]
    m2 = re.search(r"(?:解析|解答|分析|详解)\s*[:：]", opt_text)
    if m2 and m2.start() > 0:
        return opt_text[:m2.start()], opt_text[m2.start():]
    return opt_text, ""


def answer_from_text(s):
    for i, rx in enumerate(ANS_PATTERNS):
        m = rx.search(s)
        if m:
            if i == 3:
                seg = s[max(0, m.start() - 4):m.end() + 4]
                if re.search(r"[A-Za-z]{2,}", seg):
                    continue
            return m.group(1).upper()
    return ""


def inline_answer(stem):
    ans = ""
    m = re.search(r"[（(【\[]\s*(?:参考答案|正确答案|答案)\s*[:：]?\s*([A-E]{1,5})\s*[)）】\]]", stem)
    if m:
        return (stem[:m.start()] + stem[m.end():]).strip(), m.group(1).upper()
    m = re.search(r"(?:参考答案|正确答案|答案)\s*[:：]?\s*([A-E]{1,5})(?![A-Za-z0-9])", stem)
    if m:
        return (stem[:m.start()] + stem[m.end():]).strip(), m.group(1).upper()
    m = re.search(r"[:：]\s*([A-E]{1,5})\s*[。.．]?\s*$", stem)
    if m:
        return stem[:m.start()].strip(), m.group(1).upper()
    cands = list(re.finditer(r"[（(]\s*([A-E])\s*[）)]", stem))
    if len(cands) == 1:
        c = cands[0]
        return (stem[:c.start()] + "（ ）" + stem[c.end():]).strip(), c.group(1).upper()
    return stem, ans


def norm_ans(ans, letters):
    a = re.sub(r"[^A-E]", "", (ans or "").upper())
    a = "".join(sorted(set(a)))
    return "".join(c for c in a if c in letters)


def finalize_items(qs, key, key_extra=None):
    """qs: [{num, stem, options, tail?}] -> 题库条目"""
    out, seen = [], set()
    key_extra = key_extra or {}
    for q in qs:
        stem = re.sub(r"\s+", " ", q["stem"]).strip()
        stem, ia = inline_answer(stem)
        stem = re.sub(r"\s+", " ", stem).strip()
        stem = re.sub(r"(?:参考答案|正确答案)\s*$", "", stem).strip()
        stem = re.sub(r"^[（(]\s*(?:单|多|不定项)?选\s*[）)]\s*", "", stem).strip()
        stem = re.sub(r"^(?:单选题|多选题|不定项选择题|判断题|单项选择题|多项选择题)[\s:：、]*", "", stem).strip()
        stem = re.sub(r"^第\s*\d+\s*题[\s:：、.．]*", "", stem).strip()
        stem = re.sub(r"^[【\[［]\s*\d{1,3}\s*[】\]］][\s:：、.．]*", "", stem).strip()
        if len(stem) < 6:
            continue
        opts = {k: clean_opt(v) for k, v in q["options"].items()}
        letters = sorted(opts)
        if letters != [chr(ord("A") + i) for i in range(len(letters))] or len(letters) < 2:
            continue
        if len(letters) == 2 and not all(
                re.sub(r"[\s。．.、，,]", "", v) in JUDGE_OPTS for v in opts.values()):
            continue
        if any(not v or len(v) > 200 for v in opts.values()):
            continue
        rec = key.get(q["num"]) or key_extra.get(q["num"]) or {}
        tail = q.get("tail") or ""
        ans = rec.get("ans") or ia or answer_from_text(tail)
        expl = (rec.get("expl") or "").strip() or tail
        expl = re.split(r"第\s*\d+\s*题|(?<![\d.])\d{1,3}\s*[.．、]\s*(?=[\u4e00-\u9fff])", expl)[0]
        ans = norm_ans(ans, letters)
        if ans:
            expl = re.sub(r"\s+", " ", expl)
            expl = re.sub(r"^[、，,。.：:\s]+", "", expl)
            if not expl_quality(expl):
                expl = ""
            expl = expl[:700]
        else:
            ans, expl = "", ""
        ns = re.sub(r"[\s，。；：、（）()【】\[\]?!！?？]", "", stem)
        if ns in seen:
            continue
        seen.add(ns)
        item = {"n": len(out) + 1, "q": stem, "o": [opts[L] for L in letters]}
        if ans:
            item["a"] = ans
            if expl:
                item["e"] = expl
        else:
            item["na"] = 1
        out.append(item)
    return out


# ---------------- A. 标准切题器 ----------------
def parse_standard(text):
    t = pre_normalize(text)
    body, area = split_answer_region(t)
    key = parse_key_area(area)
    for n, v in parse_key_area2(area).items():
        if n not in key or not key[n].get("ans"):
            key[n] = v
    grid = parse_letter_grid(area)
    alist = parse_answer_list(body)
    if alist:
        amap, apos = alist
        for n, a in amap.items():
            key.setdefault(n, {"ans": a, "expl": ""})
        body = body[:apos]
    body, inline = strip_explanations(body)
    for n, (a, e) in inline.items():
        if n not in key or not key[n].get("ans"):
            key[n] = {"ans": a, "expl": e}
    raw_qs = build_questions(body)
    if grid and raw_qs:
        matched = sum(1 for q in raw_qs if (key.get(q["num"]) or {}).get("ans"))
        if matched < len(raw_qs) * 0.2 and abs(len(grid) - len(raw_qs)) <= 2:
            for i, q in enumerate(raw_qs):
                key.setdefault(q["num"], {"ans": grid[i], "expl": ""})
    qs = []
    for q in raw_qs:
        opts = dict(q["options"])
        last = sorted(opts)[-1]
        opts[last], tail = split_tail(opts[last])
        qs.append({"num": q["num"], "stem": q["stem"], "options": opts, "tail": tail.strip()})
    return qs, key


# ---------------- B. 宽松切题器 ----------------
def option_blocks(text):
    hits = [(m.start(), m.group(1), m.end()) for m in OPT_STD.finditer(text)]
    blocks, i, n = [], 0, len(hits)
    while i < n:
        if hits[i][1] != "A":
            i += 1
            continue
        seq = [hits[i]]
        expect = "B"
        j = i + 1
        while j < n and len(seq) < 4:
            if hits[j][1] == expect and hits[j][0] > seq[-1][0]:
                seq.append(hits[j])
                expect = chr(ord(expect) + 1)
                j += 1
            elif hits[j][1] in "ABCD" and hits[j][0] > seq[-1][0]:
                break
            else:
                j += 1
        if len(seq) >= 2:
            blocks.append((seq[0][0], seq))
            i += len(seq)
        else:
            i += 1
    return blocks


def parse_loose(text):
    t = pre_normalize(text)
    body, area = split_answer_region(t)
    key = parse_key_area(area)
    for n, v in parse_key_area2(area).items():
        if n not in key or not key[n].get("ans"):
            key[n] = v
    grid = parse_letter_grid(area)
    if alist := parse_answer_list(body):
        amap, apos = alist
        for n, a in amap.items():
            key.setdefault(n, {"ans": a, "expl": ""})
        body = body[:apos]

    blocks = option_blocks(body)
    if not blocks:
        return [], key
    # 每个选项块找它前面的题号，判断这份文件是否「有题号」
    cand = []
    for start, seq in blocks:
        pre = body[max(0, start - 320):start]
        ms = list(NUM.finditer(pre))
        if ms and (start - (max(0, start - 320) + ms[-1].end())) <= 260:
            cand.append(int(ms[-1].group(1)))
        else:
            cand.append(None)
    numbered = sum(1 for c in cand if c is not None) >= max(3, len(blocks) * 0.5)

    qs, last_num = [], 0
    for bi, (start, seq) in enumerate(blocks):
        nxt = blocks[bi + 1][0] if bi + 1 < len(blocks) else len(body)
        num = cand[bi] if numbered else None
        if numbered and num is None:
            continue                     # 解析正文里的「A项」等假选项块
        if num is not None and (num <= last_num or num > last_num + 400):
            num = last_num + 1
        if num is None:
            num = last_num + 1
        pre = body[0 if bi == 0 else (blocks[bi - 1][1][-1][2]):start]
        if numbered:
            ms = list(NUM.finditer(pre))
            stem = pre[ms[-1].end():] if ms else pre
        else:
            # 无题号：上一题最后一个选项的尾巴要切掉——按最后一段换行分界
            parts = pre.rsplit("\n", 1)
            stem = parts[-1] if len(parts) > 1 else pre
            if len(stem.strip()) < 6 and len(parts) > 1:
                stem = parts[0].rsplit("\n", 1)[-1] + stem
        stem = re.sub(r"(?m)^.*?(?:解析|解答|分析)\s*[:：].*$", "", stem)
        stem = re.sub(r"\s+", " ", stem).strip()
        opts = {}
        for k, (p, letter, e) in enumerate(seq):
            end = seq[k + 1][0] if k + 1 < len(seq) else nxt
            opts[letter] = body[e:end]
        last = sorted(opts)[-1]
        opts[last], tail = split_tail(opts[last])
        mn = re.search(r"(?<![\d.])(\d{1,3})\s*[.．、]", opts[last])
        if mn and mn.start() > 0:
            opts[last] = opts[last][:mn.start()]
        if not numbered:
            # 无题号时最后一个选项会吞掉下一题题干，按空行/换行切
            cut = re.split(r"\n\s*\n", opts[last])
            if len(cut) > 1:
                opts[last], extra = cut[0], "\n".join(cut[1:])
                tail = (extra + "\n" + tail).strip()
        qs.append({"num": num, "stem": stem, "options": opts,
                   "tail": tail.strip(), "npos": start})
        last_num = num
    return qs, key


# ---------------- 汇总 ----------------
def pick_better(a_items, b_items):
    """两套切题器结果取优：先比有答案题数，再比总题数"""
    def score(items):
        ans = sum(1 for q in items if q.get("a"))
        return (ans, len(items))
    return b_items if score(b_items) > score(a_items) else a_items


DROP_SOURCES = {
    # 计算机基础知识专题：原文档是「知识题+判断√×」混排，单选答案与题序错位（实测首题答案就错），
    # 收进来会误导，故排除；需要背的知识点可去「阅读学习」看原资料。
    "计算机基础知识专题",
}

def main():
    entries = sorted(f for f in os.listdir(RAW) if f.endswith(".txt"))
    answer_editions = {}
    for fn in entries:
        rel_name = re.sub(r"__(?:docx|doc|pdf)$", "", fn[:-4])
        parts = rel_name.split("__")
        if is_answer_edition(parts[-1]):
            answer_editions.setdefault((parts[0], title_of(parts[-1])), []).append(fn)

    extra_keys = {}
    for (top, title), fns in answer_editions.items():
        merge = {}
        for fn in fns:
            t = pre_normalize(open(os.path.join(RAW, fn), encoding="utf-8", errors="replace").read())
            key = parse_key_area(t)
            for n, v in parse_key_area2(t).items():
                if n not in key or not key[n].get("ans"):
                    key[n] = v
            for n, v in key.items():
                if n not in merge or (not merge[n].get("ans") and v.get("ans")):
                    merge[n] = v
        extra_keys[(top, title)] = merge
        print("  answer edition: %-44s keys=%d" % (title[:44], len(merge)), flush=True)

    sets, report = [], []
    for fn in entries:
        full = os.path.join(RAW, fn)
        rel_name = re.sub(r"__(?:docx|doc|pdf)$", "", fn[:-4])
        parts = rel_name.split("__")
        top, stem = parts[0], parts[-1]
        if top not in CAT_BY_DIR:
            report.append((fn, 0, 0, 0, "目录未映射"))
            continue
        _d, cat, cat_label, order = CAT_BY_DIR[top]
        base_title = title_of(stem)
        if base_title in DROP_SOURCES:
            report.append((fn, 0, 0, 0, "质量不合格已排除"))
            continue
        if is_answer_edition(stem):
            report.append((fn, 0, 0, 0, "答案版（只取答案）"))
            continue
        text = open(full, encoding="utf-8", errors="replace").read()
        if len(text.strip()) < 400:
            report.append((fn, 0, 0, 0, "文本太少"))
            continue
        extra = extra_keys.get((top, base_title)) or {}
        full_key = {}
        tfull = pre_normalize(text)
        k_full = parse_key_area2(tfull, maxnum=900)
        if len(k_full) >= 10:
            full_key = k_full
        qs1, key1 = parse_standard(text)
        merged1 = dict(key1)
        for k, v in full_key.items():
            if k not in merged1 or not merged1[k].get("ans"):
                merged1[k] = v
        for k, v in extra.items():
            if k not in merged1 or not merged1[k].get("ans"):
                merged1[k] = v
        items1 = finalize_items(qs1, merged1)
        qs2, key2 = parse_loose(text)
        merged2 = dict(key2)
        for k, v in full_key.items():
            if k not in merged2 or not merged2[k].get("ans"):
                merged2[k] = v
        for k, v in extra.items():
            if k not in merged2 or not merged2[k].get("ans"):
                merged2[k] = v
        items2 = finalize_items(qs2, merged2)
        items = pick_better(items1, items2)
        if len(items) < 8:
            report.append((fn, max(len(qs1), len(qs2)), len(items), 0, "切题太少"))
            continue
        n_ans = sum(1 for q in items if q.get("a"))
        sub = ""
        if len(parts) >= 3:
            sub = SUB_NAMES.get(parts[1], re.sub(r"^\d+-", "", parts[1]))
        title = re.sub(r"\s*\(\d+\)\s*$", "", stem).strip()
        title = re.sub(r"_+$", "", title).strip()
        item_set = {
            "id": "d" + hashlib.md5((cat + "|" + title).encode("utf-8")).hexdigest()[:8],
            "title": title, "cat": cat, "catLabel": cat_label,
            "sub": sub or cat_label, "order": order,
            "source": rel_name.replace("__", "/"), "questions": items,
        }
        sets.append((item_set, n_ans / max(1, len(items)), len(items)))
        report.append((fn, max(len(qs1), len(qs2)), len(items), n_ans,
                       "std" if items is items1 else "loose"))

    best = {}
    for s, ratio, n in sets:
        k = (s["cat"], s["sub"], s["title"])
        score = (round(ratio, 2), n)
        if k not in best or score > best[k][1]:
            best[k] = (s, score)
    final = [v[0] for v in best.values()]

    # 内容去重：同分类题干预重合 >85% 的两套只留题多的那套
    kept = []
    for s in sorted(final, key=lambda x: -len(x["questions"])):
        stems = {re.sub(r"\s+", "", q["q"])[:60] for q in s["questions"]}
        dup = False
        for k in kept:
            ks = {re.sub(r"\s+", "", q["q"])[:60] for q in k["questions"]}
            inter = len(stems & ks)
            if inter >= 0.85 * min(len(stems), len(ks)) and len(stems) > 20:
                dup = True
                break
        if not dup:
            kept.append(s)
    final = sorted(kept, key=lambda s: (s["order"], s["sub"], s["title"]))

    total = sum(len(s["questions"]) for s in final)
    total_ans = sum(1 for s in final for q in s["questions"] if q.get("a"))
    total_na = sum(1 for s in final for q in s["questions"] if q.get("na"))
    total_exp = sum(1 for s in final for q in s["questions"] if q.get("e"))
    json.dump(final, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    with open(REPORT, "w", encoding="utf-8") as f:
        for name, nq, ng, na, note in report:
            f.write("%5d/%5d ans=%-5d %-72s %s\n" % (ng, nq, na, name[:72], note))
        f.write("\n")
        for s in final:
            n = len(s["questions"])
            a = sum(1 for q in s["questions"] if q.get("a"))
            f.write("%-4s %-22s %-28s %4d题 有答案%4d 解析%4d\n" % (
                s["cat"], s["sub"][:22], s["title"][:28], n, a,
                sum(1 for q in s["questions"] if q.get("e"))))
    print("sets=%d questions=%d answered=%d na=%d expl=%d" % (
        len(final), total, total_ans, total_na, total_exp))
    print("wrote", OUT)


if __name__ == "__main__":
    main()