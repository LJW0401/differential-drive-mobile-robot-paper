#!/usr/bin/env python3
"""
按论文元数据填充 cover.pdf 的 4 页占位字段，覆盖输出到 cover.pdf 自身。
首次运行时会把原始空白封面备份为 cover_template.pdf；后续重跑都基于该模板生成，
避免反复填充导致重叠。

页面坐标基于 PyMuPDF 抽取的字段 bbox（pdftotext + page.get_text("dict") 验证）。

依赖：pymupdf (pip install --user pymupdf)
"""

from __future__ import annotations
import shutil
from pathlib import Path

import fitz  # PyMuPDF

HERE = Path(__file__).resolve().parent
COVER = HERE / "cover.pdf"
TEMPLATE = HERE / "cover_template.pdf"

# ---- 字体 ----（项目自带，cls 已配置）
F_KAI   = str(HERE / "SIMKAI.TTF")   # 楷体（中文封面用）
F_HEI   = str(HERE / "SIMHEI.TTF")   # 黑体
F_SONG  = str(HERE / "SIMSUN.TTC")   # 宋体
F_TIMES = str(HERE / "TIMES.TTF")    # Times New Roman（俄文/西文用，避免楷体西文字距异常）
F_TIMES_BD = str(HERE / "TIMESBD.TTF")

# ---- 论文元数据 ----
META = dict(
    title_cn = "五连杆轮腿平衡机器人的运动仿真与控制研究与实现",
    title_ru = ("Моделирование и управление балансирующим "
                "колёсно-шагающим роботом с пятизвенным механизмом"),
    author_cn = "刘济伟",
    author_ru = "Лю Цзивэй",
    dept_cn = "工程系",
    dept_ru = "Факультет инженерных наук",
    major_cn = "电子与计算机工程",
    major_ru = "Электронная и вычислительная техника",
    student_id = "1120220518",
    advisor_cn = "郑建波",
    advisor_ru = "Чжэн Цзяньбо",
    advisor_title = "讲师级研究员",
    year = "2026",
    month = "6",
)


def backup_once() -> None:
    """首次运行：把空白封面存档为 cover_template.pdf"""
    if not TEMPLATE.exists():
        shutil.copy(COVER, TEMPLATE)
        print(f"[backup] 原始封面已存为 {TEMPLATE.name}")


def open_template() -> fitz.Document:
    """每次重新基于备份模板生成，避免叠写"""
    if not TEMPLATE.exists():
        raise FileNotFoundError("找不到 cover_template.pdf，请确认首次备份成功")
    return fitz.open(TEMPLATE)


def redact_rect(page: fitz.Page, x0: float, y0: float, x1: float, y1: float,
                fill_white: bool = True) -> None:
    """在矩形内挂一个 redact annotation。

    fill_white=True（默认）：apply 后矩形会被白色填充覆盖，可同时盖掉
        vector path——适合纯文字占位区域。
    fill_white=False：不指定 fill；apply 时配合 graphics=0，文字被删
        而 vector path（如表格下划线）保留。
    """
    rect = fitz.Rect(x0, y0, x1, y1)
    if fill_white:
        page.add_redact_annot(rect, fill=(1, 1, 1))
    else:
        page.add_redact_annot(rect)


def apply_redactions(page: fitz.Page, keep_graphics: bool = True) -> None:
    """
    apply 阶段：
      keep_graphics=True（默认）→ 只移除文字，保留 vector path（例如表格里
          每行从标签延伸到右页边的那条横线），避免把表单视觉骨架一起抹掉。
      keep_graphics=False → 默认行为，文字 + 图形都按 fill 覆盖（用于声明
          段落这类纯文本区域，可避免残留杂线）。
    """
    page.apply_redactions(graphics=0 if keep_graphics else 2)


def _fontname(font_path: str) -> str:
    """TTF/TTC 路径稳定映射为 PDF 内合法资源名。"""
    return "F_" + Path(font_path).stem.lower().replace("-", "_")


def write(page: fitz.Page, x: float, y: float, text: str,
          font: str = F_KAI, size: float = 16) -> None:
    # 必须同时给 fontname + fontfile；只给 fontfile 时 PyMuPDF
    # 默认拿内置 14 标准字体的 cmap 去查 glyph，CJK 一概渲染成「?」。
    page.insert_text((x, y), text,
                     fontname=_fontname(font), fontfile=font,
                     fontsize=size, color=(0, 0, 0))


def write_box(page: fitz.Page, x0: float, y0: float, x1: float, y1: float,
              text: str, font: str = F_KAI, size: float = 16,
              align: int = fitz.TEXT_ALIGN_LEFT) -> None:
    page.insert_textbox(fitz.Rect(x0, y0, x1, y1), text,
                        fontname=_fontname(font), fontfile=font,
                        fontsize=size, color=(0, 0, 0), align=align)


# ============================================================
# 页 1：中文封面
# ============================================================
def fill_page1(page: fitz.Page) -> None:
    # ---- 清除标题占位文字（两行）----
    redact_rect(page, 100, 348, 500, 416)
    # ---- 清除每行字段值区域 ----
    # 原表单在 姓名/院系/专业/学号/指导教师/职称 各行从标签右沿延伸到
    # 接近页右沿画了一条 vector 下划线，是表单的视觉骨架；apply 时
    # 用 graphics=0 保留这些 path，否则横线会一并被白底盖掉。
    # 注意：不包含 y=697 的提交日期行——它没有占位文字，只有 "年 月 日"
    # 三个常驻汉字，redact 会把它们当作文本一起删掉。
    for y in (493, 527, 561, 595, 629, 663):
        # 字段行：用 fill_white=False 让 annotation 不画白底，
        # 再配合 apply_redactions(keep_graphics=True) 保留下划线。
        redact_rect(page, 218, y, 555, y + 28, fill_white=False)
    apply_redactions(page, keep_graphics=True)

    # ---- 标题（中文 + 俄文，居中；手动布局避免 textbox 静默失败）----
    # 中文标题 25 个字 22pt 单行放不下；按"机器人的/运动仿真"自然分隔
    cn1 = "五连杆轮腿平衡机器人的"
    cn2 = "运动仿真与控制研究与实现"
    write_box(page, 60, 348, 540, 378, cn1,
              font=F_KAI, size=22, align=fitz.TEXT_ALIGN_CENTER)
    write_box(page, 60, 376, 540, 406, cn2,
              font=F_KAI, size=22, align=fitz.TEXT_ALIGN_CENTER)
    # 俄文标题：Times 12pt
    write_box(page, 60, 410, 540, 460, META["title_ru"],
              font=F_TIMES, size=12, align=fitz.TEXT_ALIGN_CENTER)

    # ---- 字段值（左对齐，x 起点统一为 240）----
    # y 取自原占位文本 baseline（约 + 12 ~ 14）
    rows = [
        (513, META["author_cn"]),
        (547, META["dept_cn"]),
        (581, META["major_cn"]),
        (615, META["student_id"]),
        (649, META["advisor_cn"]),
        (683, META["advisor_title"]),
    ]
    for y, val in rows:
        if val:
            write(page, 240, y, val, font=F_KAI, size=16)

    # ---- 提交日期：年 月 日 之前各插入数字 ----
    # 年/月/日 字符位置（来自 bbox）：年=300, 月=341, 日=382
    write(page, 268, 717, META["year"],  font=F_KAI, size=16)
    write(page, 322, 717, META["month"], font=F_KAI, size=16)


# ============================================================
# 页 2：俄文封面
# ============================================================
def fill_page2(page: fitz.Page) -> None:
    # ---- 清除占位 ----
    # Факультет ХХХ：整行清掉重写
    redact_rect(page, 80, 144, 520, 167)
    # «Тема ВКР»：标题
    redact_rect(page, 250, 487, 348, 512)
    # Направление подготовки ХХ.ХХ.ХХ «  »：整行清掉重写
    redact_rect(page, 80, 418, 525, 443)
    # 2023 → year
    redact_rect(page, 278, 740, 322, 765)
    apply_redactions(page, keep_graphics=True)

    # ---- 用 Times 写俄文 ----
    # Факультет 行（保持原 14pt 加粗效果）
    write_box(page, 80, 145, 520, 167,
              f"Факультет инженерных наук",
              font=F_TIMES_BD, size=14, align=fitz.TEXT_ALIGN_CENTER)

    # Направление подготовки 行（不加粗）
    write_box(page, 80, 421, 525, 443,
              f"Направление подготовки 11.03.04 «{META['major_ru']}»",
              font=F_TIMES, size=12, align=fitz.TEXT_ALIGN_CENTER)

    # 俄文题目（«…»）
    write_box(page, 60, 486, 540, 555, f"«{META['title_ru']}»",
              font=F_TIMES, size=14, align=fitz.TEXT_ALIGN_CENTER)

    # ---- 姓名行：清掉原模板的"Работу выполнил:"/"Научный руководитель:" 重写整行 ----
    redact_rect(page, 320, 580, 548, 605)   # Работу выполнил:
    redact_rect(page, 320, 627, 548, 651)   # Научный руководитель:
    apply_redactions(page, keep_graphics=True)
    write_box(page, 200, 583, 545, 605,
              f"Работу выполнил: {META['author_ru']}",
              font=F_TIMES, size=14, align=fitz.TEXT_ALIGN_RIGHT)
    write_box(page, 200, 630, 545, 652,
              f"Научный руководитель: {META['advisor_ru']}",
              font=F_TIMES, size=14, align=fitz.TEXT_ALIGN_RIGHT)

    # 年份
    write(page, 286, 758, META["year"], font=F_TIMES, size=14)


# ============================================================
# 页 3：中文诚信声明
# ============================================================
def fill_page3(page: fitz.Page) -> None:
    # ---- 把诚信声明四行整段清掉，标题嵌入后重排（拉高 box，并改用 13pt）----
    redact_rect(page, 54, 192, 548, 300)
    apply_redactions(page, keep_graphics=True)

    full_paragraph = (
        f"本人郑重声明：所呈交的毕业论文（设计），题目《{META['title_cn']}》"
        f"是本人在指导教师的指导下，独立进行研究工作所取得的成果。"
        f"对本文的研究做出重要贡献的个人和集体，均已在文中以明确方式注明。"
        f"除此之外，本论文不包含任何其他个人或集体已经发表或撰写过的作品成果。"
        f"本人完全意识到本声明的法律结果。"
    )
    # 首行用两个全角空格缩进（中文论文规范）
    write_box(page, 54, 195, 548, 300,
              "　　" + full_paragraph,
              font=F_SONG, size=13, align=fitz.TEXT_ALIGN_LEFT)

    # ---- 诚信声明日期：2026 年 6 月 ___ 日（日留白）----
    write(page, 350, 365, META["year"],  font=F_SONG, size=14)
    write(page, 393, 365, META["month"], font=F_SONG, size=14)

    # ---- 学位论文使用授权书日期 ----
    write(page, 357, 745, META["year"],  font=F_SONG, size=14)
    write(page, 400, 745, META["month"], font=F_SONG, size=14)


# ============================================================
# 页 4：俄文声明
# ============================================================
def fill_page4(page: fitz.Page) -> None:
    # ---- 整段俄文声明 8 行（y ~ 195–340）整段清掉，把题目嵌入后重排 ----
    redact_rect(page, 54, 192, 548, 345)
    apply_redactions(page, keep_graphics=True)

    ru_paragraph = (
        "Я делаю серьезное заявление: представленная выпускная работа "
        "(дипломный проект) с темой "
        f"«{META['title_ru']}» "
        "является результатом исследовательской работы, проведенной мной "
        "самостоятельно под руководством научного руководителя. "
        "В тексте дипломной работы отчетливо указаны все отдельные лица "
        "и коллективы, внёсшие важный вклад в исследование. Кроме того, "
        "в дипломной работе не содержатся опубликованные либо написанные "
        "произведения отдельных лиц или коллективов. Я полностью осознаю "
        "юридическую ответственность за данное заявление."
    )
    write_box(page, 54, 195, 548, 345,
              "    " + ru_paragraph,
              font=F_TIMES, size=13, align=fitz.TEXT_ALIGN_LEFT)


def main() -> None:
    backup_once()
    doc = open_template()
    fill_page1(doc[0])
    fill_page2(doc[1])
    fill_page3(doc[2])
    fill_page4(doc[3])
    doc.save(COVER, garbage=4, deflate=True)
    doc.close()
    print(f"[write] 已生成 {COVER}（{COVER.stat().st_size // 1024} KB）")


if __name__ == "__main__":
    main()
