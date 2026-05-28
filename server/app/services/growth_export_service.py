"""Growth profile export service — generate long image for sharing."""

from __future__ import annotations

import io
import logging
import uuid
from datetime import date

from PIL import Image, ImageDraw, ImageFont
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.growth_record import GrowthRecord
from app.models.student import Student

logger = logging.getLogger(__name__)

CANVAS_W = 750
PADDING = 60
CARD_PADDING = 30
CARD_GAP = 20
FONT_SIZE_TITLE = 40
FONT_SIZE_SUBTITLE = 30
FONT_SIZE_BODY = 26
FONT_SIZE_SMALL = 22
FONT_SIZE_WATERMARK = 20
LINE_SPACING = 12
MAX_CONTENT_WIDTH = CANVAS_W - PADDING * 2 - CARD_PADDING * 2

BG_COLOR = (245, 247, 250)
CARD_BG = (255, 255, 255)
TITLE_COLOR = (51, 51, 51)
SUBTITLE_COLOR = (102, 102, 102)
BODY_COLOR = (68, 68, 68)
HINT_COLOR = (153, 153, 153)
ACCENT_COLOR = (74, 144, 217)
DIVIDER_COLOR = (238, 238, 238)
WATERMARK_COLOR = (180, 180, 180)

RECORD_TYPE_LABELS = {
    "award": "🏆 获奖",
    "progress": "📈 进步",
    "performance": "🎭 表现",
    "breakthrough": "💡 突破",
    "memo": "📝 备忘",
}


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


def _text_width(font: ImageFont.FreeTypeFont | ImageFont.ImageFont, text: str) -> int:
    try:
        bbox = font.getbbox(text)
        return bbox[2] - bbox[0]
    except AttributeError:
        return font.getsize(text)[0]


def _text_height(font: ImageFont.FreeTypeFont | ImageFont.ImageFont, text: str) -> int:
    try:
        bbox = font.getbbox(text)
        return bbox[3] - bbox[1]
    except AttributeError:
        return font.getsize(text)[1]


def _wrap_text(text: str, font: ImageFont.FreeTypeFont | ImageFont.ImageFont, max_width: int) -> list[str]:
    lines = []
    current_line = ""
    for char in text:
        test_line = current_line + char
        if _text_width(font, test_line) > max_width:
            if current_line:
                lines.append(current_line)
            current_line = char
        else:
            current_line = test_line
    if current_line:
        lines.append(current_line)
    return lines


def _measure_card_height(record: GrowthRecord, body_font: ImageFont.FreeTypeFont | ImageFont.ImageFont, small_font: ImageFont.FreeTypeFont | ImageFont.ImageFont) -> int:
    h = CARD_PADDING * 2

    type_label = RECORD_TYPE_LABELS.get(record.record_type, record.record_type)
    h += _text_height(body_font, type_label) + LINE_SPACING

    title_lines = _wrap_text(record.title or "", body_font, MAX_CONTENT_WIDTH)
    h += len(title_lines) * (_text_height(body_font, record.title or "") + LINE_SPACING)

    if record.description:
        desc_lines = _wrap_text(record.description, small_font, MAX_CONTENT_WIDTH)
        h += LINE_SPACING
        h += len(desc_lines) * (_text_height(small_font, "Ay") + 6)

    h += LINE_SPACING
    h += _text_height(small_font, "Ay") + LINE_SPACING

    return h


def _draw_card(
    draw: ImageDraw.ImageDraw,
    y: int,
    record: GrowthRecord,
    body_font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    small_font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
) -> int:
    card_x = PADDING
    card_w = CANVAS_W - PADDING * 2
    card_h = _measure_card_height(record, body_font, small_font)

    draw.rounded_rectangle(
        [(card_x, y), (card_x + card_w, y + card_h)],
        radius=12,
        fill=CARD_BG,
    )

    cy = y + CARD_PADDING

    type_label = RECORD_TYPE_LABELS.get(record.record_type, record.record_type)
    draw.text((card_x + CARD_PADDING, cy), type_label, fill=ACCENT_COLOR, font=body_font)
    cy += _text_height(body_font, type_label) + LINE_SPACING

    title_lines = _wrap_text(record.title or "", body_font, MAX_CONTENT_WIDTH)
    for line in title_lines:
        draw.text((card_x + CARD_PADDING, cy), line, fill=TITLE_COLOR, font=body_font)
        cy += _text_height(body_font, line) + LINE_SPACING

    if record.description:
        cy += LINE_SPACING
        desc_lines = _wrap_text(record.description, small_font, MAX_CONTENT_WIDTH)
        for line in desc_lines:
            draw.text((card_x + CARD_PADDING, cy), line, fill=BODY_COLOR, font=small_font)
            cy += _text_height(small_font, "Ay") + 6

    cy += LINE_SPACING
    date_str = record.record_date.strftime("%Y-%m-%d") if record.record_date else ""
    if record.awarding_body:
        date_str = f"{record.awarding_body} · {date_str}"
    draw.text((card_x + CARD_PADDING, cy), date_str, fill=HINT_COLOR, font=small_font)

    return card_h


def generate_growth_image(
    student_name: str,
    grade: str | None,
    records: list[dict],
) -> bytes:
    title_font = _load_font(FONT_SIZE_TITLE)
    subtitle_font = _load_font(FONT_SIZE_SUBTITLE)
    body_font = _load_font(FONT_SIZE_BODY)
    small_font = _load_font(FONT_SIZE_SMALL)
    watermark_font = _load_font(FONT_SIZE_WATERMARK)

    header_h = 200
    footer_h = 80

    cards_total_h = 0
    for rec in records:
        mock = type("R", (), rec)()
        cards_total_h += _measure_card_height(mock, body_font, small_font) + CARD_GAP
    if records:
        cards_total_h -= CARD_GAP

    total_h = header_h + cards_total_h + footer_h + PADDING * 2
    total_h = max(total_h, 800)

    img = Image.new("RGB", (CANVAS_W, total_h), BG_COLOR)
    draw = ImageDraw.Draw(img)

    hy = PADDING
    draw.text((PADDING, hy), f"{student_name}的成长档案", fill=TITLE_COLOR, font=title_font)
    hy += _text_height(title_font, "Ay") + LINE_SPACING

    if grade:
        draw.text((PADDING, hy), f"年级：{grade}", fill=SUBTITLE_COLOR, font=subtitle_font)
        hy += _text_height(subtitle_font, "Ay") + LINE_SPACING

    draw.text((PADDING, hy), f"共 {len(records)} 条记录", fill=HINT_COLOR, font=small_font)

    cy = header_h + PADDING
    for rec in records:
        mock = type("R", (), rec)()
        card_h = _draw_card(draw, cy, mock, body_font, small_font)
        cy += card_h + CARD_GAP

    wm = "高考复习助手"
    wm_w = _text_width(watermark_font, wm)
    draw.text(
        (CANVAS_W - wm_w - 40, total_h - 60),
        wm,
        fill=WATERMARK_COLOR,
        font=watermark_font,
    )

    buf = io.BytesIO()
    img.save(buf, format="PNG", quality=95)
    return buf.getvalue()


async def export_growth_profile(
    student_id: uuid.UUID,
    user_id: uuid.UUID,
    year: int | None,
    db: AsyncSession,
) -> str:
    result = await db.execute(
        select(Student).where(Student.id == student_id, Student.user_id == user_id)
    )
    student = result.scalar_one_or_none()
    if student is None:
        from app.middleware.error_handler import StudentNotFound
        raise StudentNotFound()

    query = select(GrowthRecord).where(GrowthRecord.student_id == student_id)
    if year:
        start = date(year, 9, 1)
        end = date(year + 1, 8, 31)
        query = query.where(
            GrowthRecord.record_date >= start,
            GrowthRecord.record_date <= end,
        )
    query = query.order_by(GrowthRecord.record_date.desc())

    result = await db.execute(query)
    records = result.scalars().all()

    if not records:
        from app.middleware.error_handler import InvalidParams
        raise InvalidParams("No growth records to export")

    record_dicts = []
    for r in records:
        record_dicts.append({
            "record_type": r.record_type,
            "title": r.title,
            "description": r.description,
            "record_date": r.record_date,
            "category": r.category,
            "awarding_body": r.awarding_body,
        })

    student_name = student.name or "同学"
    grade = student.grade

    png_bytes = generate_growth_image(student_name, grade, record_dicts)

    image_key = f"export/growth/{student_id}/{uuid.uuid4().hex[:8]}.png"

    if settings.cos_bucket and settings.cos_secret_id:
        from app.services.image_service import _cos_client, get_signed_url

        client = _cos_client()
        client.put_object(
            Bucket=settings.cos_bucket,
            Key=image_key,
            Body=png_bytes,
            ContentType="image/png",
        )
        return get_signed_url(image_key, expires_hours=48)
    else:
        logger.info("COS not configured, returning mock URL for growth export")
        return f"https://mock-cos.example.com/{image_key}"
