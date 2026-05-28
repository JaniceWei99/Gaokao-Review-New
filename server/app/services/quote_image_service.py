"""Quote share image generation service."""

from __future__ import annotations

import io
import logging
import uuid

from PIL import Image, ImageDraw, ImageFont

from app.config import settings

logger = logging.getLogger(__name__)

BG_COLOR = (74, 144, 217)
TEXT_COLOR = (255, 255, 255)
AUTHOR_COLOR = (220, 230, 245)
WATERMARK_COLOR = (180, 200, 230)

CANVAS_W = 750
CANVAS_H = 1334
PADDING = 80
QUOTE_MAX_WIDTH = CANVAS_W - PADDING * 2
FONT_SIZE_QUOTE = 42
FONT_SIZE_AUTHOR = 32
FONT_SIZE_WATERMARK = 24
LINE_SPACING = 20


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    font_paths = [
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
    ]
    for path in font_paths:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def _wrap_text(text: str, font: ImageFont.FreeTypeFont | ImageFont.ImageFont, max_width: int) -> list[str]:
    lines = []
    current_line = ""
    for char in text:
        test_line = current_line + char
        try:
            bbox = font.getbbox(test_line)
            w = bbox[2] - bbox[0]
        except AttributeError:
            w = font.getsize(test_line)[0]
        if w > max_width:
            if current_line:
                lines.append(current_line)
            current_line = char
        else:
            current_line = test_line
    if current_line:
        lines.append(current_line)
    return lines


def generate_quote_image(content: str, author: str | None = None) -> bytes:
    """Generate a shareable quote image and return PNG bytes."""
    img = Image.new("RGB", (CANVAS_W, CANVAS_H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    quote_font = _load_font(FONT_SIZE_QUOTE)
    author_font = _load_font(FONT_SIZE_AUTHOR)
    watermark_font = _load_font(FONT_SIZE_WATERMARK)

    lines = _wrap_text(content, quote_font, QUOTE_MAX_WIDTH)

    total_text_height = len(lines) * (FONT_SIZE_QUOTE + LINE_SPACING)
    author_block = FONT_SIZE_AUTHOR + LINE_SPACING if author else 0
    total_height = total_text_height + author_block

    y_start = (CANVAS_H - total_height) // 2

    y = y_start
    for line in lines:
        try:
            bbox = quote_font.getbbox(line)
            tw = bbox[2] - bbox[0]
        except AttributeError:
            tw = quote_font.getsize(line)[0]
        x = (CANVAS_W - tw) // 2
        draw.text((x, y), line, fill=TEXT_COLOR, font=quote_font)
        y += FONT_SIZE_QUOTE + LINE_SPACING

    if author:
        y += LINE_SPACING
        author_text = "— " + author
        try:
            bbox = author_font.getbbox(author_text)
            tw = bbox[2] - bbox[0]
        except AttributeError:
            tw = author_font.getsize(author_text)[0]
        x = (CANVAS_W - tw) // 2
        draw.text((x, y), author_text, fill=AUTHOR_COLOR, font=author_font)

    watermark = "高考复习助手"
    try:
        bbox = watermark_font.getbbox(watermark)
        tw = bbox[2] - bbox[0]
    except AttributeError:
        tw = watermark_font.getsize(watermark)[0]
    wx_pos = (CANVAS_W - tw - 40, CANVAS_H - 80)
    draw.text(wx_pos, watermark, fill=WATERMARK_COLOR, font=watermark_font)

    buf = io.BytesIO()
    img.save(buf, format="PNG", quality=95)
    return buf.getvalue()


async def generate_and_upload_quote_image(
    quote_id: uuid.UUID,
    content: str,
    author: str | None = None,
) -> str:
    """Generate a quote share image and upload to COS. Returns the image URL."""
    try:
        png_bytes = generate_quote_image(content, author)

        image_key = f"share/quotes/{quote_id}.png"

        if settings.cos_bucket and settings.cos_secret_id:
            from app.services.image_service import _cos_client

            client = _cos_client()
            client.put_object(
                Bucket=settings.cos_bucket,
                Key=image_key,
                Body=png_bytes,
                ContentType="image/png",
            )

            from app.services.image_service import get_signed_url
            return get_signed_url(image_key, expires_hours=24)
        else:
            logger.info("COS not configured, returning mock URL for quote %s", quote_id)
            return f"https://mock-cos.example.com/{image_key}"

    except Exception as exc:
        logger.error("Failed to generate quote image for %s: %s", quote_id, exc)
        raise
