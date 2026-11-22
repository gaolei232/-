# -*- coding: utf-8 -*-
"""扫描「一、学习资料（看·学）」，生成 App 阅读学习板块的数据 + 打包用 PDF 资源。

产物：
  1. app-mobile/www/study/*.pdf    —— 供 App 内 PDF.js 直接读取（ASCII 文件名）
  2. _build/study_manifest.json    —— 目录结构 / 页数 / 分卷信息，build_html.py 会注入 HTML

超过 30MB 的扫描版按约 12MB 一卷切分（pypdf 原样搬页，不重新编码，画质不变），
避免手机一次把 177MB 读进内存。
"""
import json
import os
import re
import shutil
import time

from pypdf import PdfReader, PdfWriter

BASE = r"C:\Users\86138\Desktop\习题"
ROOT = os.path.join(BASE, "一、学习资料（看·学）")
DOCPDF = os.path.join(BASE, "_build", "study_pdf")          # .doc 已转好的 PDF
WWW = os.path.join(BASE, "app-mobile", "www", "study")      # 打包进 App 的资源
MANIFEST = os.path.join(BASE, "_build", "study_manifest.json")

CHUNK_BYTES = 12 * 1024 * 1024
SPLIT_OVER = 30 * 1024 * 1024

# 阅读顺序与阶段提示来自《资料库目录说明.md》
SUBJECTS = [
    {
        "id": "gj", "name": "公共基础知识", "icon": "📘", "accent": "var(--c1)",
        "desc": "8 个专题：先搭框架，再补细节，最后背口诀与企业文化",
        "cats": [
            {"id": "gj1", "name": "思维导图", "dir": "1-公共基础知识/01-思维导图",
             "hint": "一页纸看清公基全貌，先建立框架", "stage": "第 1 周 · 先看它"},
            {"id": "gj2", "name": "彩色笔记", "dir": "1-公共基础知识/02-彩色笔记",
             "hint": "必过彩色笔记，带答案", "stage": "第 1–2 周 · 精读"},
            {"id": "gj3", "name": "高分笔记整合版", "dir": "1-公共基础知识/03-高分笔记整合版",
             "hint": "知识点全覆盖，用来查漏补缺", "stage": "第 2 周"},
            {"id": "gj4", "name": "教材版笔记", "dir": "1-公共基础知识/04-教材版笔记",
             "hint": "150 页教材版，系统学习的底本", "stage": "随时查阅"},
            {"id": "gj5", "name": "复习指导与高频考点", "dir": "1-公共基础知识/05-复习指导与高频考点",
             "hint": "重点难点提炼", "stage": "第 3 周 · 抓高频"},
            {"id": "gj6", "name": "记忆口诀", "dir": "1-公共基础知识/06-记忆口诀",
             "hint": "背下来就能提分", "stage": "贯穿全程"},
            {"id": "gj7", "name": "内部讲义", "dir": "1-公共基础知识/07-内部讲义",
             "hint": "综合知识内部讲义（Word 原件已转 PDF）", "stage": "配合专项练习看"},
            {"id": "gj8", "name": "企业文化", "dir": "1-公共基础知识/08-企业文化",
             "hint": "延长石油特色考点", "stage": "每天一点 · 必背"},
        ],
    },
    {
        "id": "xc", "name": "职业能力测试（行测）", "icon": "📗", "accent": "var(--c2)",
        "desc": "核心考点 → 提速秘籍 → 五个模块金牌讲义 → 方法专项讲练",
        "cats": [
            {"id": "xc1", "name": "核心考点", "dir": "2-职业能力测试（行测）/01-核心考点",
             "hint": "五个模块的考点地图", "stage": "第 1 周 · 先学方法"},
            {"id": "xc2", "name": "高分突破秘籍", "dir": "2-职业能力测试（行测）/02-高分突破秘籍",
             "hint": "提速与秒杀思路", "stage": "第 1–2 周"},
            {"id": "xc3a", "name": "金牌讲义 · 常识判断", "dir": "2-职业能力测试（行测）/03-金牌讲义/常识判断",
             "hint": "30 页，最省力的模块", "stage": "按模块顺序学"},
            {"id": "xc3b", "name": "金牌讲义 · 判断推理", "dir": "2-职业能力测试（行测）/03-金牌讲义/判断推理",
             "hint": "63 页，图形推理是重点", "stage": "按模块顺序学"},
            {"id": "xc3c", "name": "金牌讲义 · 数量关系", "dir": "2-职业能力测试（行测）/03-金牌讲义/数量关系",
             "hint": "46 页，挑高频题型学", "stage": "按模块顺序学"},
            {"id": "xc3d", "name": "金牌讲义 · 言语理解", "dir": "2-职业能力测试（行测）/03-金牌讲义/言语理解",
             "hint": "231 页，份量最重", "stage": "按模块顺序学"},
            {"id": "xc3e", "name": "金牌讲义 · 资料分析", "dir": "2-职业能力测试（行测）/03-金牌讲义/资料分析",
             "hint": "58 页，提分最快", "stage": "按模块顺序学"},
            {"id": "xc4", "name": "言语理解 · 专项讲练", "dir": "2-职业能力测试（行测）/04-言语理解方法（专项讲练）",
             "hint": "讲义 + 答案，配合刷题", "stage": "配合刷题用"},
            {"id": "xc5", "name": "数量关系 · 专项讲练", "dir": "2-职业能力测试（行测）/05-数量关系方法（专项讲练）",
             "hint": "讲义 + 答案，配合刷题", "stage": "配合刷题用"},
        ],
    },
]

# .doc 已用 Word 转成 PDF（键 = 相对 ROOT 的原路径）
DOC2PDF = {
    "1-公共基础知识/07-内部讲义/3.公共基础知识（综合知识）内部讲义 .doc": "gg07_neibu.pdf",
    "1-公共基础知识/08-企业文化/新版陕西延长石油集团企业文化常考知识点总结.doc": "gg08_qiye.pdf",
    "2-职业能力测试（行测）/03-金牌讲义/常识判断/1.最新版【行测讲义】常识判断（共30页）.doc": "xc03_changshi.pdf",
    "2-职业能力测试（行测）/03-金牌讲义/言语理解/3.最新版【行测讲义】言语理解与表达（共231页）.doc": "xc03_yanyu.pdf",
}

# 卡片标题：按原文件名（去扩展名）映射，键必须与磁盘上的 stem 完全一致
TITLE_FIX = {
    "公共基础知识思维导图": "公共基础知识思维导图",
    "全新陕西延长石油集团必过公共基础知识彩色笔记（答案）": "必过彩色笔记（含答案）",
    "更新版陕西延长石油集团招聘【公共基础知识】高分笔记整合版知识点全覆盖": "高分笔记整合版 · 知识点全覆盖",
    "公共基础知识教材版笔记（ 共150页）": "教材版笔记（150 页）",
    "新版公共基础知识复习指导重点难点": "复习指导 · 重点难点",
    "公共基础知识高效记忆口诀_": "高效记忆口诀",
    "3.公共基础知识（综合知识）内部讲义 ": "综合知识内部讲义",
    "新版陕西延长石油集团企业文化常考知识点总结": "企业文化常考知识点总结",
    "职业能力测验核心考点": "职业能力测验核心考点",
    "职业能力测验高分突破秘籍": "高分突破秘籍",
    "1.最新版【行测讲义】常识判断（共30页）": "常识判断讲义（30 页）",
    "4.最新版【行测讲义】判断推理（共63页）": "判断推理讲义（63 页）",
    "2.最新版【行测讲义】数量关系": "数量关系讲义",
    "3.最新版【行测讲义】言语理解与表达（共231页）": "言语理解与表达讲义（231 页）",
    "5.最新版【行测讲义】资料分析（共58页）": "资料分析讲义（58 页）",
    "专项讲练-言语理解讲义": "专项讲练 · 言语理解讲义",
    "专项讲练-言语理解讲义答案": "专项讲练 · 言语理解答案",
    "专项讲练-数量关系讲义": "专项讲练 · 数量关系讲义",
    "专项讲练-数量关系讲义答案": "专项讲练 · 数量关系答案",
    "言语理解讲义": "言语理解讲义",
    "言语理解讲义答案": "言语理解答案",
    "数量关系讲义": "数量关系讲义",
    "数量关系讲义答案": "数量关系答案",
}

NOISE = [
    "更新版", "最新版", "全新", "新版", "陕西延长石油集团招聘", "陕西延长石油集团",
    "【公共基础知识】", "【行测讲义】", "公共基础知识",
]


def clean_title(fname):
    stem = os.path.splitext(fname)[0]
    if stem in TITLE_FIX:
        return TITLE_FIX[stem]
    t = re.sub(r"^\d+\.", "", stem)
    for n in NOISE:
        t = t.replace(n, "")
    t = re.sub(r"[（(]\s*共\s*\d+\s*页\s*[）)]", "", t)
    t = re.sub(r"\s+", " ", t).strip(" ._-·")
    return t or stem


def rel_base(p):
    return os.path.relpath(p, BASE).replace("\\", "/")


def rel_root(p):
    return os.path.relpath(p, ROOT).replace("\\", "/")


def order_key(e):
    """讲义在前、答案在后；专项讲练优先于完整讲义。"""
    ans = 1 if "答案" in e["title"] else 0
    spec = 0 if e["title"].startswith("专项讲练") else 1
    return (ans, spec)


def main():
    if os.path.isdir(WWW):
        shutil.rmtree(WWW)
    os.makedirs(WWW, exist_ok=True)

    out_subjects = []
    used_dirs = set()
    idx = 0
    total_pages = 0
    total_bytes = 0
    chunk_files = 0
    problems = []

    for subj in SUBJECTS:
        cats_out = []
        for cat in subj["cats"]:
            d = os.path.join(ROOT, cat["dir"].replace("/", os.sep))
            if not os.path.isdir(d):
                problems.append("缺少目录：" + cat["dir"])
                continue
            used_dirs.add(os.path.normcase(d))
            entries = []
            for f in sorted(os.listdir(d)):
                src = os.path.join(d, f)
                if not os.path.isfile(src):
                    continue
                ext = os.path.splitext(f)[1].lower()
                if ext not in (".pdf", ".doc"):
                    continue
                if ext == ".doc":
                    # 同目录已有同名 PDF 时跳过 .doc（内容重复）
                    twin = os.path.join(d, os.path.splitext(f)[0] + ".pdf")
                    if os.path.isfile(twin):
                        continue
                    conv = DOC2PDF.get(rel_root(src))
                    if not conv:
                        problems.append("未转换的 .doc：" + rel_root(src))
                        continue
                    pdf_src = os.path.join(DOCPDF, conv)
                    converted = True
                else:
                    pdf_src = src
                    converted = False
                if not os.path.isfile(pdf_src):
                    problems.append("缺少 PDF：" + pdf_src)
                    continue

                idx += 1
                fid = "f%02d" % idx
                base_id = "s%02d" % idx
                size = os.path.getsize(pdf_src)
                reader = PdfReader(pdf_src)
                npages = len(reader.pages)

                if size <= SPLIT_OVER:
                    dst = base_id + ".pdf"
                    shutil.copyfile(pdf_src, os.path.join(WWW, dst))
                    chunks = [{"f": dst, "from": 1, "to": npages}]
                else:
                    per = max(1, int(npages * CHUNK_BYTES / size))
                    chunks = []
                    k = 0
                    for start in range(0, npages, per):
                        k += 1
                        end = min(npages, start + per)
                        w = PdfWriter()
                        for i in range(start, end):
                            w.add_page(reader.pages[i])
                        name = "%s_%d.pdf" % (base_id, k)
                        with open(os.path.join(WWW, name), "wb") as fh:
                            w.write(fh)
                        chunks.append({"f": name, "from": start + 1, "to": end})
                        chunk_files += 1
                    got = sum(len(PdfReader(os.path.join(WWW, c["f"])).pages) for c in chunks)
                    if got != npages:
                        problems.append("分卷页数不符：%s (%d != %d)" % (rel_root(src), got, npages))

                entries.append({
                    "id": fid,
                    "title": clean_title(f),
                    "orig": f,
                    "web": rel_base(pdf_src) if converted else rel_base(src),
                    "converted": converted,
                    "bytes": size,
                    "pages": npages,
                    "chunks": chunks,
                })
                total_pages += npages
                total_bytes += size

            entries.sort(key=order_key)
            if entries:
                c = {k: v for k, v in cat.items() if k != "dir"}
                c["files"] = entries
                cats_out.append(c)
            else:
                problems.append("目录里没有可用文件：" + cat["dir"])
        s = {k: v for k, v in subj.items() if k != "cats"}
        s["cats"] = cats_out
        out_subjects.append(s)

    for dp, dn, fn in os.walk(ROOT):
        if fn and os.path.normcase(dp) not in used_dirs and not any(
                os.path.normcase(dp) == os.path.normcase(os.path.join(ROOT, c["dir"].replace("/", os.sep)))
                for s in SUBJECTS for c in s["cats"]):
            problems.append("未收录目录：%s (%d 个文件)" % (rel_root(dp), len(fn)))

    manifest = {
        "version": 1,
        "built": time.strftime("%Y-%m-%d %H:%M"),
        "root": "一、学习资料（看·学）",
        "subjects": out_subjects,
        "stats": {
            "files": idx,
            "pages": total_pages,
            "bytes": total_bytes,
            "assets": len(os.listdir(WWW)),
            "chunks": chunk_files,
        },
    }
    with open(MANIFEST, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, separators=(",", ":"))

    print("文件 %d 个 · %d 页 · %.1f MB · 资源 %d 个（其中分卷 %d）"
          % (idx, total_pages, total_bytes / 1048576, len(os.listdir(WWW)), chunk_files))
    for s in out_subjects:
        print("\n[%s] %s" % (s["icon"], s["name"]))
        for c in s["cats"]:
            print("  - %s  (%s)" % (c["name"], c["stage"]))
            for e in c["files"]:
                print("      %-40s %4d 页 %7.1f MB %s%s"
                      % (e["title"][:40], e["pages"], e["bytes"] / 1048576,
                         ("分 %d 卷" % len(e["chunks"])) if len(e["chunks"]) > 1 else "",
                         "  [doc→pdf]" if e["converted"] else ""))
    if problems:
        print("\n!! 需要注意：")
        for p in problems:
            print("   " + p)


if __name__ == "__main__":
    main()