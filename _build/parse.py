#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
_build/raw/*.txt  ->  _build/bank.json

流程（先剥解析，再切题，避免解析正文里的数字/字母干扰切分）：
  1. 归一化
  2. 找答案来源：
     A 文末「参考答案(及解析)」区            -> 逐题 "1.C【解析】…"
     B 题目区内单独的答案清单 "1、D 2、B …"  -> 直接映射
     C 习题后紧跟的解析段 "[解析] N. … 故正确答案为 X"
     D 每题内的行内标记 "【选C】"
  3. 把解析正文从题干里剥掉
  4. 以「选项块」为锚点切题，按题号归档
"""
import glob
import json
import os
import re

RAW = r"C:\Users\86138\Desktop\习题\_build\raw_final"
OUT = r"C:\Users\86138\Desktop\习题\_build\bank.json"
REPORT = r"C:\Users\86138\Desktop\习题\_build\parse_report.txt"

ZERO_WIDTH = "\u200b\u200c\u200d\ufeff"
SPACES = "\u00a0\u3000\t\r"

# 全角数字/字母 → 半角（行测答案常用 "1．Ｂ" 这种全角写法，不转换就会整段解析失败）
FW_TABLE = str.maketrans(
    "０１２３４５６７８９ＡＢＣＤＥａｂｃｄｅ",
    "0123456789ABCDEabcde",
)

OPT = re.compile(r"(?<![0-9A-Za-z\u4e00-\u9fff])(?P<letter>[A-D])[ ]*[.．、:：)）][ ]*")
NUMDOT = re.compile(r"(?<![\d.])(?P<num>\d{1,3})[ ]*[.．、]")
CORRECT_TAIL = re.compile(r"故正确答案为[ ]*(?P<ans>[A-D])")
INLINE_PICK = re.compile(r"【\s*选\s*(?P<ans>[A-D](?:[ ]*[A-D])*)\s*】")
JIE_TAG = re.compile(r"【[^】]{0,10}解析[^】]{0,10}】")
ANSWER_HEAD = re.compile(
    r"(?m)^[ ]*(?:参考答案(?:及解析|与解析|和解析|详解)?|答案解析|答案与解析|答案及解析|答案详解|答案速查|【参考答案】)[ ]*[:：]?[ ]*$"
)
ANSWER_HEAD_ANY = re.compile(r"参考答案(?:及解析|与解析|和解析|详解)?")
KEY_PAIR = re.compile(
    r"(?<![\d.])(?P<num>\d{1,3})[ ]*[.．、,，]?[ ]*(?P<ans>[A-D]{1,4})(?![A-Za-z\u4e00-\u9fff])"
)
PAGE_NOISE = re.compile(
    r"第\s*\d+\s*页\s*共\s*\d+\s*页|\n\s*\d{1,3}\s*\n|绝密真题[ ]*禁止外泄|绝密真题|【真题保密】|www\.chinaexam\.org"
    # docx 版里夹带的广告水印
    r"|包过各类国企央企银行证券笔试无忧上岸微信[;；]?\s*x719514"
    r"|包过各类国企央企银行证券笔试"
    r"|无忧上岸微信[;；]?\s*x719514"
    r"|微信[;；]?\s*x719514"
)

UNIT_AFTER = set("年月日分秒亿元万人个％%点倍米克吨岁届次条例")


def normalize(text: str) -> str:
    text = text.replace("\x0c", "\n")
    text = text.translate(FW_TABLE)
    for ch in ZERO_WIDTH:
        text = text.replace(ch, "")
    for ch in SPACES:
        text = text.replace(ch, " ")
    text = re.sub(r"[ ]{2,}", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def clean_opt(s: str) -> str:
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"^[.．、:：)）\s]+", "", s)
    s = re.sub(r"[\s.．、]+$", "", s)
    return s.strip()


def expl_quality(expl: str) -> bool:
    if not expl:
        return True
    compact = re.sub(r"\s+", "", expl)
    if len(compact) < 25:
        return False
    zh = len(re.findall(r"[\u4e00-\u9fff]", compact))
    if zh / max(1, len(compact)) < 0.35:
        return False
    if len(re.findall(r"[、，。：]\s*(?:$|[、，。])", expl)) >= 4:
        return False
    return True


# ---------------------------------------------------------------- 答案区
def split_answer_region(text: str):
    m = ANSWER_HEAD.search(text)
    if m:
        return text[: m.start()], text[m.end():]
    m2 = ANSWER_HEAD_ANY.search(text)
    if m2 and m2.start() > len(text) * 0.25:
        return text[: m2.start()], text[m2.end():]
    return text, ""


def parse_key_area(area: str):
    """答案区多种写法，按可靠性依次尝试：
    (a) '1.C【解析】…'                     —— 最常见的逐题答案
    (b) '1、本题考查… 故正确答案为 C。'      —— 带推理的解析
    (c) '1.【答案】D。解析：…'
    (d) '1、【解析】A。'                   —— 仅当上面都失败时兜底
    """
    res = {}
    if not area:
        return res

    # (a)
    seq = []
    for m in KEY_PAIR.finditer(area):
        n = int(m.group("num"))
        if not seq:
            if 1 <= n <= 2:
                seq.append(m)
            continue
        if n == int(seq[-1].group("num")) + 1:
            seq.append(m)
    if len(seq) >= 10 and not re.search(r"【答案】", area[:4000]):
        for i, m in enumerate(seq):
            end = seq[i + 1].start() if i + 1 < len(seq) else len(area)
            expl = JIE_TAG.sub("", area[m.end():end], count=1)
            expl = re.sub(r"^[\s】\]，,。.、]+", "", expl)
            res[int(m.group("num"))] = {"ans": m.group("ans"), "expl": expl.strip()}
        return res

    # (b) 按 '1、' 切段，段内找「故正确答案为 X」或「【答案】X」
    secs = []
    for m in NUMDOT.finditer(area):
        n = int(m.group("num"))
        if not secs:
            if 1 <= n <= 2:
                secs.append(m)
            continue
        if n == int(secs[-1].group("num")) + 1:
            secs.append(m)
    for i, m in enumerate(secs):
        end = secs[i + 1].start() if i + 1 < len(secs) else len(area)
        seg = area[m.end():end]
        an = re.search(r"【答案】[ ]*([A-D]{1,4})", seg)
        ans = an.group(1) if an else None
        if not ans:
            found = CORRECT_TAIL.findall(seg)
            ans = found[-1] if found else None
        if not ans:
            continue
        expl = re.sub(r"^\s*【答案】[ ]*[A-D]{1,4}[。．.，,]?", "", seg)
        expl = re.sub(r"^\s*解析[：:]?", "", expl).strip()
        res[int(m.group("num"))] = {"ans": ans, "expl": re.sub(r"\s+", " ", expl).strip()}

    if len(res) >= 8:
        return res

    # (d) 兜底：「1、【解析】A。」这类一行一题的写法
    seq4 = []
    for m in re.finditer(
        r"(?m)^[ \t]*(?P<num>\d{1,3})[ \t]*[、．.][ \t]*\n?[ \t]*"
        r"(?:【解析】|【答案】|解析[ \t]*[:：])?[ \t]*(?P<ans>[A-D])(?![A-Za-z])",
        area,
    ):
        n = int(m.group("num"))
        if not seq4:
            if 1 <= n <= 2:
                seq4.append(m)
            continue
        if n == int(seq4[-1].group("num")) + 1:
            seq4.append(m)
    for i, m in enumerate(seq4):
        num = int(m.group("num"))
        if num in res:
            continue
        end = seq4[i + 1].start() if i + 1 < len(seq4) else len(area)
        seg = area[m.end():end]
        cut = re.search(r"(?m)^\s*\d{1,3}\s*[、．.]\s*(?:【答案】|【解析】|解析)", seg)
        if cut:
            seg = seg[:cut.start()]
        expl = JIE_TAG.sub("", seg, count=1)
        expl = re.sub(r"^[\s】\]，,。.、A-D]+", "", expl)
        res[num] = {"ans": m.group("ans"), "expl": expl.strip()}
    return res


def parse_key_area2(area: str, maxnum: int = 300):
    """更宽容的答案解析（与 parse_key_area 结果取并集，只补不覆盖）：

    - 认全角字母/数字（已由 normalize 处理）
    - 允许题号断档（老逻辑一旦断档，后面全部丢失）
    - 认 '1、D 解析：…'、'1．B 【解析】…'、'1. B。' 等混合写法
    - 兜底：整段只有答案字母的网格（'DBCDC ABCAA …'）交给 parse_letter_grid
    """
    res = {}
    if not area:
        return res
    a = area
    cands = []
    for m in KEY_PAIR.finditer(a):
        n = int(m.group("num"))
        if 1 <= n <= maxnum:
            cands.append((m.start(), m.end(), n, m.group("ans")))
    # 没有直接「题号+答案」的候选也别急着返回，后面还有【答案】/【解析】兜底

    # 只要题号不回退太厉害就接受（允许断档，避免一道题没解析导致后面全丢）
    chain, chains = [], []
    last = 0
    for c in cands:
        n = c[2]
        if not chain:
            if n <= 3:
                chain = [c]
                last = n
            continue
        if n > last:                      # 往前推进（允许任意断档）
            if n - last > 30:             # 跳太远说明换到别的列表了，另起一段
                if len(chain) >= 5:
                    chains.append(chain)
                chain = [c]
            else:
                chain.append(c)
            last = n
    if len(chain) >= 5:
        chains.append(chain)
    if not chains:
        chains = [cands] if len(cands) >= 5 else []

    seen = set()
    for ch in chains:
        for i, (s, e, n, ans) in enumerate(ch):
            if n in seen:
                continue
            seen.add(n)
            end = ch[i + 1][0] if i + 1 < len(ch) else min(len(a), e + 1200)
            seg = JIE_TAG.sub("", a[e:end], count=1)
            seg = re.sub(r"^\s*[［\[(（]?\s*解析\s*[］\])）]?\s*[:：]?", "", seg)
            ct = CORRECT_TAIL.search(seg)
            if ct:
                seg = seg[: ct.end()]
            expl = re.sub(r"\s+", " ", seg).strip(" ，,。；;：:、")
            ans = re.sub(r"\s+", "", ans)
            if n not in res or len(expl) > len(res[n]["expl"]):
                res[n] = {"ans": ans, "expl": expl}

    # 兜底 A：「1.【答案】B。解析：…」「1、\n【解析】\nC。…」这类把答案标在标记后面的写法
    for m in re.finditer(
        r"(?<![\d.])(\d{1,3})\s*[.．、,，:：]?\s*"
        r"(?:[\[【［(（]\s*(?:答案|解析|参考答案)\s*[\]】］)）]\s*)?"
        r"([A-D])(?![A-Za-z0-9])",
        a,
    ):
        n = int(m.group(1))
        if 1 <= n <= maxnum and n not in res:
            res[n] = {"ans": m.group(2), "expl": ""}

    # 兜底 B：「解析：… 故答案选 B。」——答案藏在解析正文里
    for m in re.finditer(
        r"(?<![\d.])(\d{1,3})\s*[.．、]\s*(?:[\[【［]\s*解析\s*[\]】］]\s*[:：]?)?"
        r"([\s\S]{0,220}?)(?:答案选|故选|应选|答案是)\s*([A-D])(?![A-Za-z])",
        a,
    ):
        n = int(m.group(1))
        if 1 <= n <= maxnum and n not in res:
            res[n] = {"ans": m.group(3), "expl": re.sub(r"\s+", " ", m.group(2)).strip()}
    return res


GRID_TOKEN = re.compile(r"(?<![A-Za-z0-9])[A-D]{2,}(?![A-Za-z0-9])")


def parse_letter_grid(area: str):
    """答案是一串没有题号的字母时（'DBCDC ABCAA …'），按顺序返回字母串；否则 None。"""
    if not area:
        return None
    letters = "".join(m.group(0) for m in GRID_TOKEN.finditer(area))
    if len(letters) < 20:
        return None
    # 区域内除了字母网格基本没有别的有效内容，才认为是「无题号答案表」
    residue = GRID_TOKEN.sub("", area)
    residue = re.sub(r"[\s\d.．、，,。；;：:（）()\[\]【】-]", "", residue)
    if len(residue) > 20:
        return None
    return letters


def parse_answer_list(body: str):
    """题目区内单独的答案清单 '1、D 2、B …'（至少 15 条连续）"""
    best = None
    for m0 in re.finditer(r"(?<![\d.])(?P<n>1)[ ]*[.．、]?[ ]*(?P<a>[A-D])(?![A-Za-z\u4e00-\u9fff])", body):
        marks = list(KEY_PAIR.finditer(body, m0.start()))
        seq = []
        for m in marks:
            n = int(m.group("num"))
            if not seq:
                if n == 1:
                    seq.append(m)
                continue
            if n == int(seq[-1].group("num")) + 1:
                seq.append(m)
        if len(seq) >= 15 and (best is None or len(seq) > len(best[1])):
            best = (m0.start(), seq)
    if not best:
        return None
    return {int(m.group("num")): m.group("ans") for m in best[1]}, best[0]


# ---------------------------------------------------------------- 剥离解析
def strip_explanations(body: str):
    """返回 (去掉解析后的题目区, {num: (ans, expl)})"""
    found = {}

    # 1) 逐个解析点：从标记开始，到「下一个解析标记」或「故正确答案为X」结束
    marks = [
        (m.start(), m.end(), m.group("num"), bool(m.group("pony")))
        for m in re.finditer(r"(?P<pony>【[^】]{0,10}解析[^】]{0,10}】)|(?P<num>(?<![\d.])\d{1,3}[ ]*[.．、])", body)
    ]

    spans = []
    for i, (s, e, num, is_jie) in enumerate(marks):
        if not is_jie:
            continue
        # 终点优先取下一个解析标记；否则取 3000 字内
        nxt_jie = None
        for s2, e2, n2, j2 in marks[i + 1:]:
            if j2:
                nxt_jie = s2
                break
        hard_end = min(len(body), s + 3000)
        end = nxt_jie if nxt_jie is not None else hard_end
        seg = body[s:end]
        ct = CORRECT_TAIL.search(seg)
        if ct:
            end = s + ct.end()
            seg = body[s:end]
        ans = None
        picks = INLINE_PICK.findall(seg)
        if picks:
            ans = re.sub(r"\s+", "", picks[-1])
        if not ans and ct:
            ans = ct.group("ans")
        if not ans:
            continue
        mnum = re.match(r"【[^】]{0,10}解析[^】]{0,10}】[ ]*(\d{1,3})[ ]*[.．、]?", seg)
        num_key = int(mnum.group(1)) if mnum else int(num) if num else None
        if num_key is None:
            continue
        expl = JIE_TAG.sub("", seg, count=1)
        expl = re.sub(r"^\s*\d{1,3}[ ]*[.．、]", "", expl)
        expl = re.sub(r"\s+", " ", expl).strip()
        found[num_key] = (ans, expl)
        spans.append((s, end))

    # 2) 'N、本题考查… 故正确答案为 X' 串行解析段
    if len(found) < 5:
        for m in NUMDOT.finditer(body):
            n = int(m.group("num"))
            if n in found:
                continue
            seg_end = None
            for m2 in NUMDOT.finditer(body, m.end()):
                seg_end = m2.start()
                break
            seg = body[m.end(): seg_end if seg_end else len(body)]
            ct = CORRECT_TAIL.findall(seg)
            if ct and ("本题考查" in seg or "项正确" in seg or "项错误" in seg):
                found[n] = (ct[-1], re.sub(r"\s+", " ", seg).strip())

    # 从文本中删除解析区间
    if spans:
        out = []
        prev = 0
        for s, e in sorted(spans):
            if s < prev:
                continue
            out.append(body[prev:s])
            prev = e
        out.append(body[prev:])
        body = "".join(out)
    return body, found


def option_blocks(text: str):
    hits = [(m.start(), m.group("letter"), m.end()) for m in OPT.finditer(text)]
    blocks = []
    i, n = 0, len(hits)
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
            i = i + len(seq)
        else:
            i += 1
    return blocks


# 判断题只给两个选项：正确 / 错误。只有这种才允许 2 选项块，避免把正文里的 A、B 误当成选项。
JUDGE_OPTS = {"正确", "错误", "对", "错", "√", "×", "说法正确", "说法错误", "对的", "错的"}


def is_judge_options(opts):
    if len(opts) != 2:
        return False
    return all(re.sub(r"[\s。．.、，,]", "", v) in JUDGE_OPTS for v in opts.values())


def find_num_before(text: str, pos: int, lo: int, window: int = 1500):
    seg_start = max(lo, pos - window)
    seg = text[seg_start:pos]
    best = None
    for m in NUMDOT.finditer(seg):
        after = seg[m.end():m.end() + 1]
        if re.match(r"^\d", seg[m.end():m.end() + 6]):
            continue
        if after and after in UNIT_AFTER:
            continue
        num_txt = m.group("num")
        if len(num_txt) == 4 and 1900 <= int(num_txt) <= 2100:
            continue
        best = m
    if not best:
        return None
    return seg_start + best.start(), int(best.group("num")), seg_start + best.end()


def build_questions(body: str):
    blocks = option_blocks(body)
    qs = []
    prev_end = 0
    for bi, (start, seq) in enumerate(blocks):
        nxt_start = blocks[bi + 1][0] if bi + 1 < len(blocks) else len(body)
        found = find_num_before(body, start, prev_end)
        if not found:
            continue
        npos, num, num_end = found
        stem = body[num_end:start]
        opts = {}
        for k, (p, letter, e) in enumerate(seq):
            end = seq[k + 1][0] if k + 1 < len(seq) else nxt_start
            opts[letter] = clean_opt(body[e:end])
        if len(opts) < 2:
            continue
        # 最后一个选项的文本会一直延伸到下一题，按「下一个题号」截断
        last_letter = sorted(opts)[-1]
        m = re.search(r"(?<![\d.])(\d{1,3})[ ]*[.．、]", opts[last_letter])
        if m and m.start() > 0:
            opts[last_letter] = clean_opt(opts[last_letter][: m.start()])
        if len(opts) == 2 and not is_judge_options(opts):
            continue
        stem = re.sub(r"\s+", " ", stem).strip()
        if len(stem) < 4:
            continue
        qs.append({"num": num, "npos": npos, "stem": stem, "options": opts})
        prev_end = npos
    by_num = {}
    for q in qs:
        cur = by_num.get(q["num"])
        if cur is None or len(q["stem"]) > len(cur["stem"]):
            by_num[q["num"]] = q
    return sorted(by_num.values(), key=lambda q: q["npos"])


def extract_key_from_text(text: str):
    """从「答案版」单独文件里抽 (num -> {ans, expl})"""
    text = PAGE_NOISE.sub("\n", normalize(text))
    _, area = split_answer_region(text)
    key = parse_key_area(area if area else text)
    return key


def main():
    files = sorted(glob.glob(os.path.join(RAW, "*.txt")))
    texts = {p: normalize(open(p, encoding="utf-8", errors="replace").read()) for p in files}
    # 「答案版」索引：去掉 ' - 答案版' 后的 key
    answer_editions = {}
    for p in files:
        stem = p[:-4]
        if stem.endswith("- 答案版"):
            answer_editions[stem[: -len(" - 答案版")]] = p

    papers, stats = [], []
    for path in files:
        base = os.path.basename(path)[:-4]
        stem = path[:-4]
        if stem.endswith("- 答案版"):
            continue  # 答案版单独处理
        # 纯图片 PDF
        if len(texts[path]) < 500:
            stats.append((base, 0, 0, 0, "空/纯图片 PDF，无文本层"))
            continue
        text = PAGE_NOISE.sub("\n", texts[path])
        body, area = split_answer_region(text)
        key = parse_key_area(area)
        # 宽容解析补齐：老解析器在题号断档处会把后面全丢掉
        for n, v in parse_key_area2(area).items():
            if n not in key or not key[n].get("ans"):
                key[n] = v
        grid = parse_letter_grid(area)

        # 对应的「答案版」
        if stem in answer_editions:
            k2 = extract_key_from_text(texts[answer_editions[stem]])
            for n, v in k2.items():
                key.setdefault(n, v)

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

        qs = build_questions(body)
        # 无题号答案表（'DBCDC ABCAA …'）：题数与答案数对得上才按顺序套，否则放弃
        if grid and qs:
            matched = sum(1 for q in qs if (key.get(q["num"]) or {}).get("ans"))
            if matched < len(qs) * 0.2 and abs(len(grid) - len(qs)) <= 2:
                for i, q in enumerate(sorted(qs, key=lambda x: x["npos"])):
                    if i < len(grid):
                        key.setdefault(q["num"], {"ans": grid[i], "expl": ""})
        kept = []
        for q in qs:
            rec = key.get(q["num"])
            ans = rec["ans"] if rec else None
            expl = (rec.get("expl") if rec else "") or ""
            if not ans:
                continue
            expl = re.sub(r"\s+", " ", expl).strip()
            if not expl_quality(expl):
                expl = ""
            kept.append(
                {
                    "num": q["num"],
                    "stem": q["stem"],
                    "options": {k: v for k, v in sorted(q["options"].items())},
                    "answer": re.sub(r"\s+", "", ans),
                    "expl": expl,
                }
            )
        kept.sort(key=lambda x: x["num"])

        folder = base.partition("__")[0]
        name = base.partition("__")[2]
        m = re.search(r"\((\d+)\)\s*$", name)
        papers.append(
            {
                "folder": folder,
                "title": re.sub(r"\s*\(\d+\)\s*$", "", name).strip(),
                "variant": int(m.group(1)) if m else None,
                "source": os.path.basename(path),
                "questions": kept,
            }
        )
        stats.append((base, len(qs), len(kept), sum(1 for k in kept if k["expl"]), ""))

    total = sum(len(p["questions"]) for p in papers)
    wexp = sum(1 for p in papers for q in p["questions"] if q["expl"])
    print(f"papers={len(papers)} questions={total} with_expl={wexp}")
    json.dump(papers, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    with open(REPORT, "w", encoding="utf-8") as f:
        for name, nq, ng, ne, note in stats:
            f.write(f"{ng:5d}/{nq:<5d} expl={ne:<5d} {name[:70]} {note}\n")
    print("wrote", OUT)


if __name__ == "__main__":
    main()





