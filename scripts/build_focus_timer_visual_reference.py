#!/usr/bin/env python3
"""Render the Focus Timer GitHub journey graphic and developer PDF."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Iterable, Sequence

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
PAGE_SIZE = landscape(A4)
CANVAS = "#050805"
PANEL = "#0B120D"
PANEL_RAISED = "#101A12"
GREEN = "#40FF5E"
GREEN_SOFT = "#B8FFC3"
GREEN_MUTED = "#6DBA78"
LINE = "#1D5128"
WHITE = "#F4FFF6"
BLACK = "#000000"
RED = "#FF7777"

FONT_CANDIDATES = (
    (
        Path("/System/Library/Fonts/STHeiti Medium.ttc"),
        Path("/System/Library/Fonts/STHeiti Medium.ttc"),
    ),
    (
        Path(
            "/System/Library/AssetsV2/com_apple_MobileAsset_Font7/"
            "3419f2a427639ad8c8e139149a287865a90fa17e.asset/AssetData/"
            "PingFang.ttc"
        ),
        Path(
            "/System/Library/AssetsV2/com_apple_MobileAsset_Font7/"
            "3419f2a427639ad8c8e139149a287865a90fa17e.asset/AssetData/"
            "PingFang.ttc"
        ),
    ),
    (
        Path("/System/Library/Fonts/Hiragino Sans GB.ttc"),
        Path("/System/Library/Fonts/Hiragino Sans GB.ttc"),
    ),
)

JOURNEY_STATES = (
    ("01", "语音设时", "开始专注", "durationSeconds: 600"),
    ("02", "idle", "10:00", "開始"),
    ("03", "running", "09:58", "一時停止"),
    ("04", "paused", "09:45", "再開"),
    ("05", "running", "09:44", "一時停止"),
    ("06", "finished", "00:00", "最初から"),
)

PAGE_TITLES = (
    "专注计时器 · 开发者视觉参考",
    "01 · 从对话到计时页面",
    "02 · _current 关键状态",
    "03 · _blank 完整操作",
    "04 · 点头与触摸板事件映射",
    "05 · 验证证据与人工门槛",
)


def find_cjk_fonts() -> tuple[Path, Path]:
    """Return a local CJK-capable regular/bold font pair."""

    for regular, bold in FONT_CANDIDATES:
        if regular.is_file() and bold.is_file():
            return regular, bold
    system_fonts = Path("/System/Library/Fonts")
    regular_matches = tuple(
        path
        for path in system_fonts.glob("*W3.ttc")
        if "角" in path.name or "Hiragino" in path.name
    )
    bold_matches = tuple(
        path
        for path in system_fonts.glob("*W6.ttc")
        if "角" in path.name or "Hiragino" in path.name
    )
    if regular_matches and bold_matches:
        return regular_matches[0], bold_matches[0]
    raise RuntimeError("No supported CJK font found")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_font(path: Path, size: int, index: int = 0) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size=size, index=index)


def text_width(draw: ImageDraw.ImageDraw, value: str, font: ImageFont.FreeTypeFont) -> int:
    box = draw.textbbox((0, 0), value, font=font)
    return box[2] - box[0]


def centered_text(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    value: str,
    font: ImageFont.FreeTypeFont,
    fill: str,
) -> None:
    bounds = draw.textbbox((0, 0), value, font=font)
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    x = box[0] + (box[2] - box[0] - width) / 2
    y = box[1] + (box[3] - box[1] - height) / 2 - bounds[1]
    draw.text((x, y), value, font=font, fill=fill)


def rounded_panel(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    radius: int = 24,
    fill: str = PANEL,
    outline: str = LINE,
    width: int = 2,
) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def draw_pillow_chip(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    value: str,
    font: ImageFont.FreeTypeFont,
    *,
    active: bool = False,
) -> int:
    padding_x = 18
    chip_width = text_width(draw, value, font) + padding_x * 2
    fill = GREEN if active else PANEL_RAISED
    ink = BLACK if active else GREEN_MUTED
    draw.rounded_rectangle(
        (x, y, x + chip_width, y + 42),
        radius=21,
        fill=fill,
        outline=GREEN if active else LINE,
        width=2,
    )
    centered_text(draw, (x, y, x + chip_width, y + 42), value, font, ink)
    return chip_width


def draw_arrow(draw: ImageDraw.ImageDraw, x1: int, y: int, x2: int) -> None:
    draw.line((x1, y, x2, y), fill=GREEN_MUTED, width=4)
    draw.polygon(
        ((x2, y), (x2 - 14, y - 9), (x2 - 14, y + 9)), fill=GREEN_MUTED
    )


def draw_journey_card(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    item: tuple[str, str, str, str],
    fonts: dict[str, ImageFont.FreeTypeFont],
) -> None:
    number, stage, main_value, action = item
    x1, y1, x2, y2 = box
    rounded_panel(draw, box, radius=28, width=3)
    draw.text((x1 + 24, y1 + 20), number, font=fonts["eyebrow"], fill=GREEN)
    draw.text((x1 + 74, y1 + 19), stage, font=fonts["label"], fill=GREEN_SOFT)

    viewport = (x1 + 22, y1 + 82, x2 - 22, y2 - 26)
    draw.rounded_rectangle(
        viewport, radius=20, fill=BLACK, outline=LINE, width=2
    )
    vx1, vy1, vx2, vy2 = viewport
    draw.text(
        (vx1 + 18, vy1 + 15),
        "ROKID  ·  _current",
        font=fonts["micro"],
        fill=GREEN_MUTED,
    )
    draw.line((vx1 + 18, vy1 + 47, vx2 - 18, vy1 + 47), fill=LINE, width=2)

    if number == "01":
        draw.text((vx1 + 18, vy1 + 78), "USER", font=fonts["micro"], fill=GREEN_MUTED)
        draw.multiline_text(
            (vx1 + 18, vy1 + 115),
            "“开始专注”",
            font=fonts["quote"],
            fill=WHITE,
            spacing=8,
        )
        draw.text(
            (vx1 + 18, vy1 + 196),
            "默认 10 分钟",
            font=fonts["body"],
            fill=GREEN_SOFT,
        )
        rounded_panel(
            draw,
            (vx1 + 16, vy1 + 248, vx2 - 16, vy1 + 310),
            radius=10,
            fill=PANEL,
            width=2,
        )
        centered_text(
            draw,
            (vx1 + 16, vy1 + 248, vx2 - 16, vy1 + 310),
            action,
            fonts["code"],
            GREEN,
        )
        draw.text(
            (vx1 + 18, vy1 + 338),
            "fresh Page invocation",
            font=fonts["micro"],
            fill=GREEN_MUTED,
        )
        return

    state_color = GREEN if stage in {"running", "finished"} else GREEN_MUTED
    draw.text((vx1 + 18, vy1 + 72), stage.upper(), font=fonts["micro"], fill=state_color)
    draw.text(
        (vx1 + 18, vy1 + 108),
        "フォーカスタイマー",
        font=fonts["body"],
        fill=GREEN_SOFT,
    )
    centered_text(
        draw,
        (vx1 + 10, vy1 + 145, vx2 - 10, vy1 + 265),
        main_value,
        fonts["time"],
        GREEN,
    )
    if stage != "idle":
        progress = {"running": 8, "paused": 25, "finished": 100}.get(stage, 0)
        bar = (vx1 + 18, vy1 + 282, vx2 - 18, vy1 + 294)
        draw.rounded_rectangle(bar, radius=6, fill=PANEL_RAISED)
        filled = int((bar[2] - bar[0]) * progress / 100)
        if filled:
            draw.rounded_rectangle(
                (bar[0], bar[1], bar[0] + filled, bar[3]), radius=6, fill=GREEN
            )
    button = (vx1 + 18, vy2 - 76, vx2 - 18, vy2 - 20)
    draw.rounded_rectangle(button, radius=8, fill=GREEN, outline=GREEN, width=2)
    centered_text(draw, button, action, fonts["button"], BLACK)


def render_journey_png(path: Path, regular_path: Path, bold_path: Path) -> None:
    image = Image.new("RGB", (2400, 1200), CANVAS)
    draw = ImageDraw.Draw(image)
    fonts = {
        "title": load_font(bold_path, 60),
        "subtitle": load_font(regular_path, 28),
        "eyebrow": load_font(bold_path, 26),
        "label": load_font(bold_path, 26),
        "micro": load_font(regular_path, 18),
        "quote": load_font(bold_path, 36),
        "body": load_font(regular_path, 25),
        "code": load_font(regular_path, 21),
        "time": load_font(bold_path, 58),
        "button": load_font(bold_path, 24),
        "footer": load_font(regular_path, 22),
    }

    draw.text((80, 58), "FOCUS TIMER · USER JOURNEY", font=fonts["title"], fill=GREEN)
    draw.text(
        (82, 137),
        "语音设定 → Page 初始化 → 点头或触摸板执行主要操作",
        font=fonts["subtitle"],
        fill=GREEN_SOFT,
    )
    chip_x = 1774
    chip_x += draw_pillow_chip(draw, chip_x, 74, "AIUI 0.17.0", fonts["micro"], active=True) + 14
    draw_pillow_chip(draw, chip_x, 74, "PAGE ONLY", fonts["micro"])

    card_width = 340
    gap = 35
    card_y1 = 235
    card_y2 = 948
    start_x = 82
    for index, item in enumerate(JOURNEY_STATES):
        x1 = start_x + index * (card_width + gap)
        x2 = x1 + card_width
        draw_journey_card(draw, (x1, card_y1, x2, card_y2), item, fonts)
        if index < len(JOURNEY_STATES) - 1:
            draw_arrow(draw, x2 + 7, (card_y1 + card_y2) // 2, x2 + gap - 7)

    strip = (82, 987, 2318, 1071)
    rounded_panel(draw, strip, radius=18, fill=PANEL_RAISED, width=2)
    centered_text(
        draw,
        strip,
        "点头 nod  ·  触摸板 Enter / GlobalHook  ·  聚焦按钮 bindtap",
        fonts["label"],
        GREEN_SOFT,
    )
    draw.text(
        (84, 1110),
        "Rokid Glasses 视野效果示意（非真机实拍）",
        font=fonts["footer"],
        fill=GREEN_MUTED,
    )
    draw.text(
        (2318 - text_width(draw, "默认 10 分钟 · durationSeconds: 600", fonts["footer"]), 1110),
        "默认 10 分钟 · durationSeconds: 600",
        font=fonts["footer"],
        fill=GREEN_MUTED,
    )
    image.save(path, format="PNG", optimize=True)


def register_pdf_fonts(regular_path: Path, bold_path: Path) -> tuple[str, str]:
    regular = "FocusCJK"
    bold = "FocusCJKBold"
    pdfmetrics.registerFont(TTFont(regular, str(regular_path), subfontIndex=0))
    pdfmetrics.registerFont(TTFont(bold, str(bold_path), subfontIndex=0))
    return regular, bold


def set_fill(pdf: canvas.Canvas, value: str) -> None:
    pdf.setFillColor(HexColor(value))


def set_stroke(pdf: canvas.Canvas, value: str) -> None:
    pdf.setStrokeColor(HexColor(value))


def pdf_text_width(value: str, font: str, size: float) -> float:
    return pdfmetrics.stringWidth(value, font, size)


def draw_pdf_text(
    pdf: canvas.Canvas,
    x: float,
    y: float,
    value: str,
    font: str,
    size: float,
    color: str = GREEN_SOFT,
) -> None:
    set_fill(pdf, color)
    pdf.setFont(font, size)
    pdf.drawString(x, y, value)


def wrap_pdf_text(value: str, font: str, size: float, max_width: float) -> list[str]:
    lines: list[str] = []
    current = ""
    for character in value:
        candidate = current + character
        if current and pdf_text_width(candidate, font, size) > max_width:
            lines.append(current.rstrip())
            current = character.lstrip()
        else:
            current = candidate
    if current:
        lines.append(current.rstrip())
    return lines or [""]


def draw_wrapped_text(
    pdf: canvas.Canvas,
    x: float,
    y: float,
    value: str,
    font: str,
    size: float,
    max_width: float,
    *,
    leading: float | None = None,
    color: str = GREEN_SOFT,
    max_lines: int | None = None,
) -> float:
    line_height = leading or size * 1.45
    lines = wrap_pdf_text(value, font, size, max_width)
    if max_lines is not None:
        lines = lines[:max_lines]
    for line in lines:
        draw_pdf_text(pdf, x, y, line, font, size, color)
        y -= line_height
    return y


def draw_pdf_panel(
    pdf: canvas.Canvas,
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    radius: float = 6,
    fill: str = PANEL,
    stroke: str = LINE,
    line_width: float = 1,
) -> None:
    set_fill(pdf, fill)
    set_stroke(pdf, stroke)
    pdf.setLineWidth(line_width)
    pdf.roundRect(x, y, width, height, radius, stroke=1, fill=1)


def draw_pdf_chip(
    pdf: canvas.Canvas,
    x: float,
    y: float,
    value: str,
    font: str,
    *,
    active: bool = False,
) -> float:
    size = 8.5
    width = pdf_text_width(value, font, size) + 9 * mm
    fill = GREEN if active else PANEL_RAISED
    ink = BLACK if active else GREEN_MUTED
    draw_pdf_panel(pdf, x, y, width, 8 * mm, radius=4 * mm, fill=fill, stroke=GREEN if active else LINE)
    draw_pdf_text(pdf, x + 4.5 * mm, y + 2.55 * mm, value, font, size, ink)
    return width


def draw_page_header(
    pdf: canvas.Canvas,
    page_number: int,
    title: str,
    regular: str,
    bold: str,
) -> None:
    width, height = PAGE_SIZE
    set_fill(pdf, CANVAS)
    pdf.rect(0, 0, width, height, stroke=0, fill=1)
    draw_pdf_text(pdf, 16 * mm, height - 14 * mm, "ROKID AIUI · FOCUS TIMER", bold, 11, GREEN)
    draw_pdf_text(pdf, 16 * mm, height - 27 * mm, title, bold, 24, GREEN_SOFT)
    set_stroke(pdf, LINE)
    pdf.setLineWidth(1)
    pdf.line(16 * mm, height - 32 * mm, width - 16 * mm, height - 32 * mm)
    draw_pdf_text(pdf, width - 28 * mm, 9 * mm, f"{page_number} / 6", regular, 8, GREEN_MUTED)


def draw_device_note(pdf: canvas.Canvas, regular: str) -> None:
    draw_pdf_text(
        pdf,
        16 * mm,
        9 * mm,
        "Rokid Glasses 视野效果示意（非真机实拍）",
        regular,
        8,
        GREEN_MUTED,
    )


def draw_stat_card(
    pdf: canvas.Canvas,
    x: float,
    y: float,
    width: float,
    label: str,
    value: str,
    regular: str,
    bold: str,
) -> None:
    draw_pdf_panel(pdf, x, y, width, 25 * mm, radius=4)
    draw_pdf_text(pdf, x + 5 * mm, y + 16 * mm, label, regular, 8, GREEN_MUTED)
    draw_pdf_text(pdf, x + 5 * mm, y + 6 * mm, value, bold, 15, GREEN_SOFT)


def draw_flow_arrow(pdf: canvas.Canvas, x1: float, y: float, x2: float) -> None:
    set_stroke(pdf, GREEN_MUTED)
    set_fill(pdf, GREEN_MUTED)
    pdf.setLineWidth(1.5)
    pdf.line(x1, y, x2, y)
    pdf.line(x2 - 4, y + 3, x2, y)
    pdf.line(x2 - 4, y - 3, x2, y)


def draw_state_screen(
    pdf: canvas.Canvas,
    x: float,
    y: float,
    width: float,
    height: float,
    state: str,
    time_value: str,
    action: str,
    regular: str,
    bold: str,
    *,
    target: str = "_current",
    progress: int = 0,
    secondary: Sequence[str] = (),
) -> None:
    draw_pdf_panel(pdf, x, y, width, height, radius=8, fill=BLACK, stroke=LINE, line_width=1.2)
    draw_pdf_text(pdf, x + 5 * mm, y + height - 7 * mm, f"ROKID · {target}", regular, 6.8, GREEN_MUTED)
    set_stroke(pdf, LINE)
    pdf.line(x + 5 * mm, y + height - 10 * mm, x + width - 5 * mm, y + height - 10 * mm)
    draw_pdf_text(pdf, x + 5 * mm, y + height - 17 * mm, state.upper(), bold, 7, GREEN)
    draw_pdf_text(pdf, x + 5 * mm, y + height - 25 * mm, "フォーカスタイマー", regular, 8.5, GREEN_SOFT)
    time_width = pdf_text_width(time_value, bold, 27)
    draw_pdf_text(pdf, x + (width - time_width) / 2, y + height * 0.45, time_value, bold, 27, GREEN)

    if target == "_blank":
        bar_x = x + 5 * mm
        bar_y = y + height * 0.39
        bar_width = width - 10 * mm
        set_fill(pdf, PANEL_RAISED)
        pdf.roundRect(bar_x, bar_y, bar_width, 2.4 * mm, 1.2 * mm, stroke=0, fill=1)
        if progress:
            set_fill(pdf, GREEN)
            pdf.roundRect(
                bar_x,
                bar_y,
                bar_width * min(progress, 100) / 100,
                2.4 * mm,
                1.2 * mm,
                stroke=0,
                fill=1,
            )
        draw_pdf_text(pdf, bar_x, bar_y - 5 * mm, f"進捗 {progress}%", regular, 7, GREEN_MUTED)

    button_x = x + 5 * mm
    button_y = y + (17 * mm if secondary else 7 * mm)
    button_w = width - 10 * mm
    set_fill(pdf, GREEN)
    pdf.roundRect(button_x, button_y, button_w, 10 * mm, 2, stroke=0, fill=1)
    action_width = pdf_text_width(action, bold, 9)
    draw_pdf_text(pdf, button_x + (button_w - action_width) / 2, button_y + 3.3 * mm, action, bold, 9, BLACK)
    if secondary:
        each = button_w / len(secondary)
        for index, value in enumerate(secondary):
            sx = button_x + index * each
            draw_pdf_panel(pdf, sx, y + 4 * mm, each - 1.5 * mm, 8 * mm, radius=2, fill=PANEL, stroke=LINE)
            value_width = pdf_text_width(value, regular, 7)
            draw_pdf_text(pdf, sx + (each - 1.5 * mm - value_width) / 2, y + 6.6 * mm, value, regular, 7, GREEN_SOFT)


def draw_page_one(pdf: canvas.Canvas, regular: str, bold: str) -> None:
    width, height = PAGE_SIZE
    draw_page_header(pdf, 1, PAGE_TITLES[0], regular, bold)
    x = 16 * mm
    top = height - 43 * mm
    draw_pdf_text(pdf, x, top, "Focus Timer", bold, 38, GREEN)
    draw_wrapped_text(
        pdf,
        x,
        top - 13 * mm,
        "面向 Rokid Glasses 的 Page-only 专注计时器。语音负责设时，点头或触摸板负责当前主要操作。",
        regular,
        12,
        148 * mm,
        leading=7 * mm,
    )
    chip_y = top - 35 * mm
    chip_x = x
    for value, active in (("AIUI 0.17.0", True), ("PAGE ONLY", False), ("DEFAULT 10 MIN", False), ("NO EYE TRACKING", False)):
        chip_x += draw_pdf_chip(pdf, chip_x, chip_y, value, bold, active=active) + 3 * mm

    cards_y = 43 * mm
    card_gap = 5 * mm
    card_width = (width - 32 * mm - card_gap * 3) / 4
    cards = (
        ("输入", "durationSeconds", "1–3600 秒整数；省略时使用 600。"),
        ("计时", "Date.now()", "截止时间是真值；定时器只刷新界面。"),
        ("交互", "nod / touchpad", "点头、Enter、GlobalHook 进入同一主要操作。"),
        ("边界", "manual gates", "不承诺后台、通知、系统闹钟或持久化恢复。"),
    )
    for index, (label, value, detail) in enumerate(cards):
        cx = x + index * (card_width + card_gap)
        draw_pdf_panel(pdf, cx, cards_y, card_width, 46 * mm, radius=6)
        draw_pdf_text(pdf, cx + 5 * mm, cards_y + 35 * mm, label, bold, 8, GREEN)
        draw_pdf_text(pdf, cx + 5 * mm, cards_y + 25 * mm, value, bold, 13, GREEN_SOFT)
        draw_wrapped_text(pdf, cx + 5 * mm, cards_y + 16 * mm, detail, regular, 8.2, card_width - 10 * mm, leading=4.6 * mm, color=GREEN_MUTED)
    draw_device_note(pdf, regular)


def draw_page_two(pdf: canvas.Canvas, regular: str, bold: str) -> None:
    width, height = PAGE_SIZE
    draw_page_header(pdf, 2, PAGE_TITLES[1], regular, bold)
    y = 44 * mm
    panel_height = 118 * mm
    left_x = 16 * mm
    left_w = 76 * mm
    mid_x = 100 * mm
    mid_w = 70 * mm
    right_x = 178 * mm
    right_w = width - right_x - 16 * mm
    for x, w in ((left_x, left_w), (mid_x, mid_w), (right_x, right_w)):
        draw_pdf_panel(pdf, x, y, w, panel_height, radius=6)

    draw_pdf_text(pdf, left_x + 6 * mm, y + 104 * mm, "1 · 用户说", bold, 11, GREEN)
    draw_pdf_text(pdf, left_x + 6 * mm, y + 88 * mm, "“开始专注”", bold, 18, WHITE)
    draw_pdf_text(pdf, left_x + 6 * mm, y + 78 * mm, "→ 默认 10 分钟", regular, 9, GREEN_MUTED)
    set_stroke(pdf, LINE)
    pdf.line(left_x + 6 * mm, y + 69 * mm, left_x + left_w - 6 * mm, y + 69 * mm)
    draw_pdf_text(pdf, left_x + 6 * mm, y + 54 * mm, "“专注 25 分钟”", bold, 18, WHITE)
    draw_pdf_text(pdf, left_x + 6 * mm, y + 44 * mm, "→ 25 × 60 = 1500", regular, 9, GREEN_MUTED)
    draw_wrapped_text(pdf, left_x + 6 * mm, y + 25 * mm, "可选任务名写入 label；未提供时显示“フォーカスタイマー”。", regular, 8.5, left_w - 12 * mm, leading=5 * mm, color=GREEN_SOFT)

    draw_pdf_text(pdf, mid_x + 6 * mm, y + 104 * mm, "2 · Agent 转换", bold, 11, GREEN)
    draw_pdf_panel(pdf, mid_x + 7 * mm, y + 65 * mm, mid_w - 14 * mm, 24 * mm, radius=4, fill=BLACK)
    draw_pdf_text(pdf, mid_x + 12 * mm, y + 79 * mm, "durationSeconds", regular, 8, GREEN_MUTED)
    draw_pdf_text(pdf, mid_x + 12 * mm, y + 69 * mm, "600 / 1500", bold, 17, GREEN)
    draw_flow_arrow(pdf, mid_x + 16 * mm, y + 55 * mm, mid_x + mid_w - 16 * mm)
    draw_pdf_text(pdf, mid_x + 17 * mm, y + 47 * mm, "fresh Page", bold, 11, GREEN_SOFT)
    draw_wrapped_text(pdf, mid_x + 7 * mm, y + 29 * mm, "时间变化会创建新的 Page；不会承诺原卡片原地变更。", regular, 8.5, mid_w - 14 * mm, leading=5 * mm, color=GREEN_MUTED)

    draw_pdf_text(pdf, right_x + 6 * mm, y + 104 * mm, "3 · Page 校验", bold, 11, GREEN)
    rows = (
        ("缺省", "durationSeconds: 600", "idle · 10:00"),
        ("有效", "1 … 3600", "idle"),
        ("无效", "0 / 3601 / 小数 / 字符串", "error"),
        ("名称", "label ≤ 48 code points", "可选"),
    )
    row_y = y + 82 * mm
    for label, value, result in rows:
        draw_pdf_text(pdf, right_x + 6 * mm, row_y, label, bold, 8, GREEN)
        draw_pdf_text(pdf, right_x + 24 * mm, row_y, value, regular, 8.5, GREEN_SOFT)
        result_width = pdf_text_width(result, bold, 8)
        draw_pdf_text(pdf, right_x + right_w - 6 * mm - result_width, row_y, result, bold, 8, GREEN_MUTED)
        set_stroke(pdf, LINE)
        pdf.line(right_x + 6 * mm, row_y - 4 * mm, right_x + right_w - 6 * mm, row_y - 4 * mm)
        row_y -= 20 * mm
    draw_pdf_text(pdf, right_x + 6 * mm, y + 8 * mm, "schema.data → onLoad(query)", regular, 8, GREEN_MUTED)


def draw_page_three(pdf: canvas.Canvas, regular: str, bold: str) -> None:
    width, height = PAGE_SIZE
    draw_page_header(pdf, 3, PAGE_TITLES[2], regular, bold)
    left = 16 * mm
    bottom = 35 * mm
    gap = 7 * mm
    frame_width = (width - 32 * mm - gap * 3) / 4
    frame_height = 116 * mm
    states = (
        ("idle", "10:00", "開始", 0),
        ("running", "09:58", "一時停止", 1),
        ("paused", "09:45", "再開", 25),
        ("finished", "00:00", "最初から", 100),
    )
    for index, (state, value, action, progress) in enumerate(states):
        x = left + index * (frame_width + gap)
        draw_state_screen(pdf, x, bottom, frame_width, frame_height, state, value, action, regular, bold, progress=progress)
        note = {
            "idle": "点头 / 单击：开始",
            "running": "截止时间不因重复点击漂移",
            "paused": "暂停时保存真实剩余毫秒",
            "finished": "仅完成态显示 100%",
        }[state]
        draw_pdf_text(pdf, x, bottom - 7 * mm, note, regular, 7.2, GREEN_MUTED)
    draw_device_note(pdf, regular)


def draw_page_four(pdf: canvas.Canvas, regular: str, bold: str) -> None:
    width, height = PAGE_SIZE
    draw_page_header(pdf, 4, PAGE_TITLES[3], regular, bold)
    left_x = 16 * mm
    y = 31 * mm
    frame_w = 118 * mm
    frame_h = 126 * mm
    draw_state_screen(
        pdf,
        left_x,
        y,
        frame_w,
        frame_h,
        "running",
        "07:32",
        "一時停止",
        regular,
        bold,
        target="_blank",
        progress=25,
        secondary=("最初から", "リセット"),
    )
    right_x = 144 * mm
    draw_pdf_text(pdf, right_x, y + 117 * mm, "完整状态与全部操作", bold, 17, GREEN_SOFT)
    draw_wrapped_text(pdf, right_x, y + 104 * mm, "_blank 保留任务名、剩余时间、精确状态、进度与所有合法操作。", regular, 10, width - right_x - 16 * mm, leading=6 * mm, color=GREEN_MUTED)
    actions = (
        ("idle", "開始", "开始新计时"),
        ("running", "一時停止", "冻结真实剩余时间"),
        ("paused", "再開", "以剩余时间生成新截止点"),
        ("finished", "最初から", "按原时长重新开始"),
        ("running / paused", "最初から", "立即从总时长重启"),
        ("非 error", "リセット", "回到 idle"),
    )
    row_y = y + 80 * mm
    for state, action, meaning in actions:
        draw_pdf_panel(pdf, right_x, row_y, width - right_x - 16 * mm, 12 * mm, radius=3, fill=PANEL_RAISED)
        draw_pdf_text(pdf, right_x + 4 * mm, row_y + 4 * mm, state, bold, 7.5, GREEN)
        draw_pdf_text(pdf, right_x + 39 * mm, row_y + 4 * mm, action, bold, 8, GREEN_SOFT)
        draw_pdf_text(pdf, right_x + 70 * mm, row_y + 4 * mm, meaning, regular, 7.5, GREEN_MUTED)
        row_y -= 15 * mm
    draw_pdf_text(pdf, right_x, y + 1 * mm, "error 状态不显示无效恢复按钮；应回到对话重新设定。", regular, 8, RED)
    draw_device_note(pdf, regular)


def draw_mapping_lane(
    pdf: canvas.Canvas,
    y: float,
    label: str,
    nodes: Sequence[str],
    regular: str,
    bold: str,
) -> None:
    width, _ = PAGE_SIZE
    draw_pdf_text(pdf, 16 * mm, y + 7 * mm, label, bold, 9, GREEN)
    lane_x = 53 * mm
    lane_w = width - lane_x - 16 * mm
    gap = 4 * mm
    node_w = (lane_w - gap * (len(nodes) - 1)) / len(nodes)
    for index, node in enumerate(nodes):
        x = lane_x + index * (node_w + gap)
        draw_pdf_panel(pdf, x, y, node_w, 20 * mm, radius=4, fill=PANEL_RAISED)
        lines = wrap_pdf_text(node, bold if index in {0, len(nodes) - 1} else regular, 8.2, node_w - 8 * mm)
        text_y = y + 12.5 * mm + (len(lines) - 1) * 2.2 * mm
        for line in lines:
            font = bold if index in {0, len(nodes) - 1} else regular
            line_w = pdf_text_width(line, font, 8.2)
            draw_pdf_text(pdf, x + (node_w - line_w) / 2, text_y, line, font, 8.2, GREEN_SOFT)
            text_y -= 4.4 * mm
        if index < len(nodes) - 1:
            draw_flow_arrow(pdf, x + node_w + 1 * mm, y + 10 * mm, x + node_w + gap - 1 * mm)


def draw_page_five(pdf: canvas.Canvas, regular: str, bold: str) -> None:
    width, height = PAGE_SIZE
    draw_page_header(pdf, 5, PAGE_TITLES[4], regular, bold)
    draw_mapping_lane(pdf, 129 * mm, "点头", ("nod", "onHeadGesture", "visible + supported", "_runPrimaryAction"), regular, bold)
    draw_mapping_lane(pdf, 98 * mm, "触摸板", ("Enter / GlobalHook", "onKeyUp", "preventDefault", "_runPrimaryAction"), regular, bold)
    draw_mapping_lane(pdf, 67 * mm, "聚焦按钮", ("focus", "bindfocus", "bindtap", "state handler"), regular, bold)

    draw_pdf_panel(pdf, 16 * mm, 31 * mm, width - 32 * mm, 25 * mm, radius=5)
    draw_pdf_text(pdf, 22 * mm, 46 * mm, "视觉反馈", bold, 9, GREEN)
    draw_pdf_text(pdf, 55 * mm, 46 * mm, "bindfocus → 高亮当前操作", regular, 8.5, GREEN_SOFT)
    draw_pdf_text(pdf, 132 * mm, 46 * mm, "bindblur → 清除高亮", regular, 8.5, GREEN_SOFT)
    draw_pdf_text(pdf, 199 * mm, 46 * mm, "bindtap → 执行动作", regular, 8.5, GREEN_SOFT)
    draw_pdf_text(pdf, 22 * mm, 36 * mm, "无眼球追踪。error、非 nod 与其他按键均为 no-op。", regular, 8, GREEN_MUTED)


def draw_evidence_row(
    pdf: canvas.Canvas,
    y: float,
    label: str,
    evidence: str,
    status: str,
    regular: str,
    bold: str,
) -> None:
    width, _ = PAGE_SIZE
    row_x = 16 * mm
    row_w = width - 32 * mm
    draw_pdf_panel(pdf, row_x, y, row_w, 16 * mm, radius=3, fill=PANEL_RAISED)
    status_fill = GREEN if status == "PASS" else RED
    draw_pdf_text(pdf, row_x + 5 * mm, y + 6 * mm, label, bold, 8, GREEN_SOFT)
    draw_pdf_text(pdf, row_x + 55 * mm, y + 6 * mm, evidence, regular, 7.7, GREEN_MUTED)
    status_w = pdf_text_width(status, bold, 8)
    draw_pdf_text(pdf, row_x + row_w - 5 * mm - status_w, y + 6 * mm, status, bold, 8, status_fill)


def draw_page_six(pdf: canvas.Canvas, regular: str, bold: str) -> None:
    width, height = PAGE_SIZE
    draw_page_header(pdf, 6, PAGE_TITLES[5], regular, bold)
    draw_pdf_text(pdf, 16 * mm, height - 44 * mm, "本地可重复证据", bold, 12, GREEN)
    rows = (
        ("源码合同", "Page-only、输入边界、状态与交互绑定", "PASS"),
        ("可控时钟测试", "Date.now / pause / resume / finish / lifecycle", "PASS"),
        ("严格校验", "validate_aiui_project.py --target-version 0.17.0 --strict", "PASS"),
        ("AIX 命令", "先查 --help，再执行 preview / pack / list", "PASS"),
        ("模拟器交互", "Enter 单击：开始 → 暂停 → 继续", "PASS"),
        ("AIUI Studio", "登录、GitHub 导入与运行时签名", "BLOCKED / 人工门槛"),
        ("物理眼镜", "点头、触摸板、_current / _blank 真机表现", "BLOCKED / 人工门槛"),
    )
    row_y = height - 64 * mm
    for label, evidence, status in rows:
        draw_evidence_row(pdf, row_y, label, evidence, status, regular, bold)
        row_y -= 19 * mm
    draw_pdf_text(pdf, 16 * mm, 18 * mm, "不承诺：后台持续运行 · 系统闹钟 · 通知 · 持久化恢复", bold, 9, GREEN_SOFT)
    draw_pdf_text(pdf, width - 93 * mm, 18 * mm, "真机结论必须来自人工验证，不由示意图或模拟器替代。", regular, 8, GREEN_MUTED)


def render_developer_pdf(path: Path, regular_path: Path, bold_path: Path) -> None:
    regular, bold = register_pdf_fonts(regular_path, bold_path)
    pdf = canvas.Canvas(
        str(path),
        pagesize=PAGE_SIZE,
        pageCompression=1,
        invariant=1,
    )
    pdf.setTitle("Focus Timer Developer Visual Reference")
    pdf.setAuthor("BreezeLife / ROKID AIUI Agent Skill")
    page_functions = (
        draw_page_one,
        draw_page_two,
        draw_page_three,
        draw_page_four,
        draw_page_five,
        draw_page_six,
    )
    for render_page in page_functions:
        render_page(pdf, regular, bold)
        pdf.showPage()
    pdf.save()


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=ROOT,
        help="Repository-shaped output root (default: this repository)",
    )
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    output_root = args.output_root.absolute()
    png_path = output_root / "docs" / "assets" / "focus-timer-user-journey.png"
    pdf_path = output_root / "output" / "pdf" / "focus-timer-developer-reference.pdf"
    png_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    regular_path, bold_path = find_cjk_fonts()
    render_journey_png(png_path, regular_path, bold_path)
    render_developer_pdf(pdf_path, regular_path, bold_path)
    summary = {
        "png": str(png_path),
        "pdf": str(pdf_path),
        "pages": 6,
        "png_sha256": sha256(png_path),
        "pdf_sha256": sha256(pdf_path),
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
