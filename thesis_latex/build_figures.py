#!/usr/bin/env python3
"""
把 ../figures/*.svg 转成 thesis_latex/figures/*.pdf 供 LaTeX \\includegraphics 使用。

用 WeasyPrint（基于 Pango）做按字符字体后备，
相比 cairosvg 能在缺 SimSun/Times New Roman 的环境下用 Noto Serif CJK SC
和 DejaVu 等系统已装字体把中文、希腊字母、Unicode 下/上标都正确渲染出来。

依赖：weasyprint  (pip install --user weasyprint)
"""
from __future__ import annotations
import pathlib

import weasyprint

ROOT     = pathlib.Path(__file__).resolve().parent
SRC_DIR  = ROOT.parent / "figures"           # 项目根目录下的 svg
DEST_DIR = ROOT / "figures"                  # thesis_latex/figures/*.pdf
DEST_DIR.mkdir(exist_ok=True)

# 与各 svg 的 viewBox 尺寸保持一致，避免 WeasyPrint 按页面默认尺寸裁切
SIZES = {
    "fig1_system_framework": (920, 760),
    "fig2_robot_structure":  (920, 560),
    "fig3_five_bar_kinematics": (920, 560),
    "fig4_sim_platform":        (920, 600),
    "fig5_ctrl_interface":      (920, 780),
    "fig7_pid_cascade":         (920, 720),
    "fig9_mpc_pgd_flow":        (920, 880),
}


def render(name: str, width: int, height: int) -> None:
    src = SRC_DIR / f"{name}.svg"
    dst = DEST_DIR / f"{name}.pdf"
    html = f"""<!doctype html>
<html><head><meta charset="utf-8">
<style>
  @page {{ margin: 0; size: {width}px {height}px; }}
  body  {{ margin: 0; padding: 0; }}
  svg   {{ width: {width}px; height: {height}px; display: block; }}
</style></head><body>
{src.read_text(encoding='utf-8')}
</body></html>"""
    weasyprint.HTML(string=html).write_pdf(str(dst))
    print(f"[ok] {dst.relative_to(ROOT.parent)}  ({dst.stat().st_size // 1024} KB)")


def main() -> None:
    for name, (w, h) in SIZES.items():
        render(name, w, h)


if __name__ == "__main__":
    main()
