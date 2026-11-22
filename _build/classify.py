# -*- coding: utf-8 -*-
"""给每道题打上 8 个分类标识之一（供 App 显示分类标签、专项按分类聚合）。

分类：政治理论 / 常识判断 / 言语理解与表达 / 数量关系 / 判断推理 / 资料分析 /
      公共基础知识 / 专业知识

- 专项题库：大部分整套同属一个模块，按来源目录 + 标题判断；混合题集（行测专项题库、综合必做题库等）
  逐题用关键词打分
- 套卷：每套是整卷，逐题关键词打分；无法判断时按卷子的 catLabel 兜底（公基卷→公共基础知识，行测卷→言语）
- build_html.py 在注入网页前调用 enrich(bank, drill)，不改动源 JSON
"""
import re

CATS = [
    ("politics", "政治理论"),
    ("common", "常识判断"),
    ("verbal", "言语理解与表达"),
    ("quant", "数量关系"),
    ("logic", "判断推理"),
    ("data", "资料分析"),
    ("gongji", "公共基础知识"),
    ("major", "专业知识"),
]
CAT_IDS = [c[0] for c in CATS]
CAT_LABEL = dict(CATS)
CAT_ORDER = {cid: i for i, (cid, _) in enumerate(CATS)}

# 关键词打分表（命中次数累加）
RULES = [
    ("major", ["石油", "延长石油", "原油", "炼化", "勘探", "钻井", "采油", "企业文化"]),
    ("data", ["资料分析", "同比", "环比", "增长率", "增长量", "比重", "百分点", "翻番", "年均", "占比",
               "增速", "统计", "表中", "图表", "柱状图", "折线图", "调查数据", "增速为"]),
    ("quant", ["数学运算", "数字推理", "工程问题", "行程问题", "利润", "浓度", "排列组合", "概率",
                "几何", "等差数列", "等比数列", "植树", "年龄", "容斥", "牛吃草", "鸡兔同笼",
                "多少种", "多少元", "速度", "效率", "倍数", "余数", "周期", "数列"]),
    ("logic", ["定义判断", "类比推理", "图形推理", "逻辑判断", "下列属于", "下列不属于", "属于", "削弱",
                "加强", "假设", "最能", "结论", "如果", "只有", "所有", "有的", "相当于", "对于",
                "推理", "矛盾关系", "真假"]),
    ("verbal", ["选词填空", "依次填入", "划横线", "横线", "成语", "病句", "没有语病", "有语病",
                 "这段话", "这段文字", "主旨", "意在说明", "主要说明", "主要表达", "概括", "标题",
                 "作者", "语境", "词语", "填入", "最恰当"]),
    ("politics", ["马克思主义", "哲学", "唯物", "唯心", "辩证法", "矛盾", "实践", "认识论",
                   "毛泽东思想", "邓小平", "三个代表", "科学发展观", "习近平", "新时代",
                   "中国特色社会主义", "党史", "党的", "时政", "人民代表大会", "政治", "社会形态",
                   "生产力", "生产关系", "上层建筑"]),
    ("gongji", ["宪法", "刑法", "民法", "行政法", "诉讼法", "合同", "法律", "条例", "公务员",
                 "经济", "市场", "财政", "货币", "管理", "公文", "道德", "事业单位", "计算机",
                 "专利", "商标", "著作权", "犯罪", "赔偿", "诉讼"]),
    ("common", ["常识", "地理", "历史", "文学", "科技", "生物", "物理", "化学", "天文", "气候",
                 "山脉", "河流", "奥运", "节日", "生活常识", "古代", "朝代", "诗句", "发明"]),
]

# 专项题库整卷判定
def drill_set_cat(d):
    src = (d.get("source") or "").replace("\\", "/")
    top = src.split("/")[0]
    sub = d.get("sub") or ""
    title = d.get("title") or ""

    if top.startswith("1-公基各模块"):
        if "政治" in sub:
            return "politics"
        if "历史人文" in sub or "地理国情" in sub or "科技常识" in sub:
            return "common"
        return "gongji"
    if top.startswith("2-公基基础强化"):
        if any(k in title for k in ("哲学", "党史", "毛概", "中特")):
            return "politics"
        if any(k in title for k in ("文史", "科技")):
            return "common"
        return "gongji"
    if top.startswith("3-行测各模块"):
        if "言语" in sub:
            return "verbal"
        if "数量" in sub:
            return "quant"
        if "判断" in sub:
            return "logic"
        if "资料" in sub:
            return "data"
        if "常识" in sub:
            return "common"
        return None
    if top.startswith("4-行测必做"):
        if "判断" in title:
            return "logic"
        if "数量" in title:
            return "quant"
        if "言语" in title:
            return "verbal"
        if "资料" in title:
            return "data"
        return None
    if top.startswith("5-常识"):
        return "common"
    if top.startswith("6-EPI"):
        if "数字" in sub or "数学" in sub:
            return "quant"
        if "言语" in sub:
            return "verbal"
        if "图形" in sub or "逻辑" in sub:
            return "logic"
        if "资料" in sub:
            return "data"
        if "常识" in sub:
            return "common"
        return None
    if top.startswith("7-公基预测"):
        return "gongji"
    if top.startswith("8-行测专项"):
        return None
    return None


def score_categories(text):
    scores = {}
    for cid, words in RULES:
        sc = 0
        for w in words:
            sc += text.count(w)
        if sc:
            scores[cid] = sc
    return scores


def classify_question(q, fallback):
    stem = (q.get("q") or "")[:400]
    opts = " ".join(q.get("o") or [])
    text = stem + " " + opts[:260]
    scores = score_categories(text)
    if not scores:
        # 没有任何关键词时，靠数字特征兜底
        if re.search(r"\d", stem) and any(w in stem for w in ("多少", "几", "倍", "平均", "比例", "增长", "速度", "元")):
            return "quant"
        return fallback
    # 优先级：总分最高；相同时按 CAT_ORDER（专业/资料/数量/判断/言语/政治/公基/常识）
    best = max(scores.items(), key=lambda kv: (kv[1], -CAT_ORDER[kv[0]]))
    # 分数太弱时用兜底；但数量/言语/判断/资料这类「见到一个特征词就基本确定」的类别直接采信
    if best[1] < 2 and fallback and best[0] in ("politics", "gongji", "common"):
        return fallback
    return best[0]


def paper_fallback(p):
    label = (p.get("catLabel") or "") + (p.get("cat") or "")
    if "公基" in label or "公共基础" in label:
        return "gongji"
    if "EPI" in label or "行测" in label or "职业能力" in label:
        return "verbal"
    return "common"


def enrich(bank, drills):
    """原地给每道题加 k 字段；给每套加 kcat（出现最多的分类）。返回统计信息"""
    for p in bank:
        fb = paper_fallback(p)
        for q in p.get("questions", []):
            q["k"] = classify_question(q, fb)
        p["kcat"] = dominant_cat([q["k"] for q in p["questions"]])
    for d in drills:
        set_cat = drill_set_cat(d)
        for q in d.get("questions", []):
            # 整套同模块的直接用它；混合题集逐题判断；带石油/企业文化的题优先标「专业知识」
            stem = q.get("q") or ""
            if any(w in stem for w in ("石油", "延长石油", "炼化", "勘探", "钻井", "采油", "企业文化")):
                q["k"] = "major"
            else:
                q["k"] = set_cat or classify_question(q, "verbal")
        d["kcat"] = dominant_cat([q["k"] for q in d["questions"]])
    stats = {"bank": {}, "drill": {}}
    for p in bank:
        for q in p.get("questions", []):
            stats["bank"][q["k"]] = stats["bank"].get(q["k"], 0) + 1
    for d in drills:
        for q in d.get("questions", []):
            stats["drill"][q["k"]] = stats["drill"].get(q["k"], 0) + 1
    return stats


def dominant_cat(cats):
    if not cats:
        return "common"
    cnt = {}
    for c in cats:
        cnt[c] = cnt.get(c, 0) + 1
    return max(cnt.items(), key=lambda kv: kv[1])[0]


if __name__ == "__main__":
    import json
    import os
    base = r"C:\Users\86138\Desktop\习题\_build"
    bank = json.load(open(os.path.join(base, "bank_final.json"), encoding="utf-8"))
    drift = json.load(open(os.path.join(base, "drill_bank.json"), encoding="utf-8"))
    st = enrich(bank, drift)
    print("套卷分类分布：")
    for cid, name in CATS:
        print("  %-8s %-12s %5d" % (cid, name, st["bank"].get(cid, 0)))
    print("专项分类分布：")
    for cid, name in CATS:
        print("  %-8s %-12s %5d" % (cid, name, st["drill"].get(cid, 0)))
    print("套卷 kcat 分布：", {k: sum(1 for p in bank if p["kcat"] == k) for k in CAT_IDS})