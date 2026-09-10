"""Genera una miniatura llamativa combinando la foto del personaje con texto de alto impacto."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from src import config


def _fit_cover(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    ratio = max(target_w / img.width, target_h / img.height)
    new_size = (int(img.width * ratio), int(img.height * ratio))
    img = img.resize(new_size, Image.Resampling.LANCZOS)
    left = (img.width - target_w) // 2
    top = (img.height - target_h) // 2
    return img.crop((left, top, left + target_w, top + target_h))


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    words = text.upper().split()
    lines, current = [], ""
    for word in words:
        trial = f"{current} {word}".strip()
        if draw.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines[:3]


def build_thumbnail(photo_path: Path, headline: str, out_path: Path) -> Path:
    """Compone una miniatura vertical: foto de fondo, viñeta oscura inferior y titular en texto grande."""
    w, h = config.VIDEO_WIDTH, config.VIDEO_HEIGHT
    base = _fit_cover(Image.open(photo_path).convert("RGB"), w, h).convert("RGBA")

    # Viñeta oscura en la parte inferior para que el texto sea legible
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    grad_draw = ImageDraw.Draw(overlay)
    gradient_height = int(h * 0.45)
    for i in range(gradient_height):
        alpha = int(190 * (i / gradient_height))
        y = h - gradient_height + i
        grad_draw.line([(0, y), (w, y)], fill=(0, 0, 0, alpha))
    base = Image.alpha_composite(base, overlay)

    draw = ImageDraw.Draw(base)
    font = ImageFont.truetype(config.FONT_PATH, 92)
    lines = _wrap_text(draw, headline, font, int(w * 0.9))

    line_height = 106
    y = h - int(h * 0.06) - line_height * len(lines)
    for line in lines:
        text_w = draw.textlength(line, font=font)
        x = (w - text_w) / 2
        for dx in (-4, 4):
            for dy in (-4, 4):
                draw.text((x + dx, y + dy), line, font=font, fill="black")
        draw.text((x, y), line, font=font, fill="#FFE600")
        y += line_height

    # Etiqueta de contexto en la esquina superior
    tag_font = ImageFont.truetype(config.FONT_PATH, 48)
    tag_text = "NOTICIA"
    tag_w = draw.textlength(tag_text, font=tag_font) + 40
    draw.rectangle([30, 30, 30 + tag_w, 100], fill="#E30613")
    draw.text((50, 42), tag_text, font=tag_font, fill="white")

    base.convert("RGB").save(out_path, quality=92)
    return out_path
