"""全量抽取 docx 文本：正文 + 表格 + 文本框 + 公式(m:t)，保持文档顺序。"""
import glob

import docx
from docx.oxml.ns import qn

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
M = "{http://schemas.openxmlformats.org/officeDocument/2006/math}"


def iter_text(el):
    """按顺序收集 w:t / m:t 文本，段落结束加换行"""
    tag = el.tag
    if tag == W + "p":
        buf = []
        for t in el.iter():
            if t.tag in (W + "t", M + "t") and t.text:
                buf.append(t.text)
        return "".join(buf) + "\n"
    return ""


def extract(path):
    d = docx.Document(path)
    body = d.element.body
    out = []
    for child in body.iterchildren():
        # 段落、表格都遍历其内部的所有 w:p
        if child.tag == W + "p":
            out.append(iter_text(child))
        elif child.tag == W + "tbl":
            for p in child.iter(W + "p"):
                out.append(iter_text(p))
        elif child.tag == W + "sdt":
            for p in child.iter(W + "p"):
                out.append(iter_text(p))
    return "".join(out)


if __name__ == "__main__":
    path = glob.glob(r"C:\Users\86138\Desktop\习题\三、套卷模考与冲刺\1-历年真题（2019-2023）\*.docx")[0]
    t = extract(path)
    print("抽取长度:", len(t))
    i = t.find("参考答案")
    print("答案区位置:", i)
    print("---- 答案区 1500 字 ----")
    print(t[i:i + 1500] if i > 0 else t[:800])