#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
识别「PDF 里的公式/图形没进文本层」留下的残句。

不把「标点前有空格」当依据——PDF 换行会把「》」和「。」挤成「》 。」，
正文读起来完全正常，单凭空格会大面积误判。

强信号（命中任意一条即判残句）：
  · 空括号          「总人数的（）工人」（原公式在括号里）
  · 冒号/分号紧跟标点「总数的：；」
  · 连续标点        「本题考查经济。 。」
  · 运算符后直接断句「1-（）＝。」
中信号（命中两条以上判残句）：
  · 连接词后空格再接标点「则有 ，」「故 ，」
  · 动词后空格再接量词  「经过 分钟」「有 场次比赛」
"""
import re

EMPTY_BRACKET = re.compile(r"（[ \t]*）|\([ \t]*\)")
COLON_PUNCT = re.compile(r"[：；][ \t]*[，。；]")
PAIR_PUNCT = re.compile(r"[，。；][ \t]*[，。；]")
OP_PUNCT = re.compile(r"[=＝÷×+＋\-−][ \t]*[，。；）)]")
CONNECTOR = re.compile(r"[故即为则是有得][ \t]+[，。；、]")
VERB_UNIT = re.compile(
    r"[为是有得计经过约共完成了][ \t]+(元|人|行|列|棵|件|分钟|小时|天|米|倍|种|台|辆|场次|场|个|次)"
)

STRONG = ((EMPTY_BRACKET, "空括号"), (COLON_PUNCT, "冒号后断句"),
          (PAIR_PUNCT, "连续标点"), (OP_PUNCT, "运算符后断句"))
MEDIUM = ((CONNECTOR, "连接词后断句"), (VERB_UNIT, "量词前空格"))


def analyze(expl: str):
    """返回 (是否残句, 分数, 命中原因列表)"""
    if not expl:
        return False, 0, []
    why, strong, medium = [], 0, 0
    for rx, name in STRONG:
        n = len(rx.findall(expl))
        if n:
            strong += n
            why.append(f"{name}×{n}")
    for rx, name in MEDIUM:
        n = len(rx.findall(expl))
        if n:
            medium += n
            why.append(f"{name}×{n}")
    score = strong * 3 + medium
    broken = strong >= 1 or medium >= 2
    return broken, score, why


if __name__ == "__main__":
    cases = [
        # (原文, 期望是否残句, 说明)
        ("（1）将短边作为行： ，则能种植 行； ，则能种植 列。故可种植桃树 棵。", True, "2019#3 公式丢失"),
        ("即 420 分钟，则实际时间经过 分钟。故提前了 分钟。", True, "2019#2 缺算式"),
        ("本题考查经济。 。 现在需要的货币供应量为 (万亿元)，超出 2.8 万亿元", True, "2021#11"),
        ("A 项错误：作品是《赤壁赋》 。B 项错误：著有《兰亭集序》 。", False, "公基换行误判"),
        ("A 项，根据“良渚古城遗址”可知，表述正确，当选。", False, "法律类正常"),
        ("B 项正确：邓小平提出了“建设有中国特色的社会主义” 。C 项错误", False, "公基换行误判2"),
        ("［解析］甲工地的工作，需要总人数的（）工人工作半天。", True, "行测空括号"),
        ("只用B商品的家庭占被调查家庭总数的：；同样", True, "行测冒号断句"),
        ("之和为 ，错误；C 项，收录图书之和为 ，正确；", True, "2019#45"),
        ("三管齐开2分钟后还未完成的工作量是1-（）×2。", True, "行测空括号2"),
    ]
    bad = 0
    for text, want, note in cases:
        got, score, why = analyze(text)
        mark = "OK " if got == want else "ERR"
        if got != want:
            bad += 1
        print(f"{mark} 期望={str(want):5s} 实得={str(got):5s} score={score:<3d} {note}  {why}")
    print(f"\n{len(cases) - bad}/{len(cases)} 判定正确")