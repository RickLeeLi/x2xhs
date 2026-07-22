"""封面图生成（PIL）。"""
from PIL import Image, ImageDraw, ImageFont
from config import FONT_BOLD, FONT_REGULAR

COVER_W, COVER_H = 1080, 1440
THEMES = [
    {"bg": (255, 95, 109), "bg2": (255, 159, 67), "fg": (255, 255, 255), "accent": (255, 241, 118)},
    {"bg": (106, 76, 255), "bg2": (255, 99, 179), "fg": (255, 255, 255), "accent": (180, 248, 255)},
    {"bg": (34, 193, 195), "bg2": (253, 187, 45), "fg": (255, 255, 255), "accent": (255, 255, 255)},
    {"bg": (25, 42, 86), "bg2": (73, 124, 214), "fg": (255, 255, 255), "accent": (124, 247, 239)},
    {"bg": (240, 84, 122), "bg2": (255, 142, 83), "fg": (255, 255, 255), "accent": (255, 234, 167)},
]


def _font(size, bold=True):
    path = FONT_BOLD if bold else FONT_REGULAR
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def _wrap(text, draw, font, max_w):
    lines, cur = [], ""
    for ch in text:
        if ch == "\n":
            lines.append(cur); cur = ""; continue
        test = cur + ch
        if draw.textlength(test, font=font) <= max_w:
            cur = test
        else:
            lines.append(cur); cur = ch
    if cur:
        lines.append(cur)
    return lines


def _gradient(theme):
    base = Image.new("RGB", (COVER_W, COVER_H), theme["bg"])
    top = Image.new("RGB", (COVER_W, COVER_H), theme["bg2"])
    mask = Image.new("L", (COVER_W, COVER_H))
    md = ImageDraw.Draw(mask)
    md.rectangle([0, 0, COVER_W, COVER_H], fill=0)
    for y in range(COVER_H):
        a = int(255 * (1 - y / COVER_H))
        md.line([(0, y), (COVER_W, y)], fill=a)
    base = Image.composite(top, base, mask)
    return base


def generate_cover(title, output_path, subtitle="", theme_index=None):
    import random
    if theme_index is None:
        theme = random.choice(THEMES)
    else:
        theme = THEMES[theme_index % len(THEMES)]
    img = _gradient(theme)
    d = ImageDraw.Draw(img)
    d.ellipse([-120, -120, 260, 260], fill=theme["accent"])
    d.ellipse([COVER_W - 200, COVER_H - 260, COVER_W + 80, COVER_H + 20], fill=theme["accent"])
    title_font = _font(72, True)
    lines = _wrap(title, d, title_font, COVER_W - 140)
    lines = lines[:4]
    y = 360
    for ln in lines:
        d.text((70, y), ln, font=title_font, fill=theme["fg"])
        y += 96
    if subtitle:
        sub_font = _font(34, False)
        sub_lines = _wrap(subtitle, d, sub_font, COVER_W - 160)
        yy = y + 20
        for ln in sub_lines[:2]:
            d.text((72, yy), ln, font=sub_font, fill=theme["fg"]); yy += 48
    d.text((70, COVER_H - 120), "X \u2192 \u5c0f\u7ea2\u4e66 \u00b7 \u6bcf\u65e5\u642c\u8fd0", font=_font(30, True), fill=theme["fg"])
    img.save(output_path, quality=95)
    return output_path
