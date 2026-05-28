"""Growth record service — CRUD, school-year grouping, and quote matching."""

from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import date

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.middleware.error_handler import ResourceNotFound, StudentNotFound
from app.middleware.permission import check_growth_record_limit, get_user_plan
from app.models.growth_record import GrowthRecord
from app.models.quote import DailyQuote
from app.models.student import Student
from app.schemas.growth_record import (
    GrowthRecordCreate,
    GrowthRecordCreateResponse,
    GrowthRecordListResponse,
    GrowthRecordResponse,
)
from app.schemas.quote import QuoteResponse
from app.services.image_service import delete_image, get_signed_url


RECORD_TYPE_TO_QUOTE_CATEGORY = {
    "award": "achievement",
    "progress": "progress",
    "performance": "performance",
    "breakthrough": "breakthrough",
    "memo": "encouragement",
}


async def _verify_student(
    student_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession
) -> Student:
    result = await db.execute(
        select(Student).where(Student.id == student_id, Student.user_id == user_id)
    )
    student = result.scalar_one_or_none()
    if student is None:
        raise StudentNotFound()
    return student


def _school_year_for(record_date: date) -> str:
    year = record_date.year
    if record_date.month >= 9:
        return f"{year}-{year + 1}"
    else:
        return f"{year - 1}-{year}"


async def create_growth_record(
    student_id: uuid.UUID,
    user_id: uuid.UUID,
    body: GrowthRecordCreate,
    db: AsyncSession,
) -> GrowthRecordCreateResponse:
    student = await _verify_student(student_id, user_id, db)
    plan = await get_user_plan(user_id, db)
    await check_growth_record_limit(student_id, db, plan)

    record = GrowthRecord(
        student_id=student_id,
        record_type=body.record_type,
        title=body.title,
        description=body.description,
        record_date=body.record_date,
        category=body.category,
        awarding_body=body.awarding_body,
        image_url=body.image_url,
        auto_generated=body.auto_generated,
    )
    db.add(record)
    await db.flush()

    matched_quote = await _match_quote(body.record_type, db)
    if matched_quote:
        record.linked_quote_id = matched_quote.id
        await db.flush()

    resp = _to_response(record)
    quote_resp = _quote_to_response(matched_quote) if matched_quote else None

    await db.commit()
    return GrowthRecordCreateResponse(growth_record=resp, matched_quote=quote_resp)


async def list_growth_records(
    student_id: uuid.UUID,
    user_id: uuid.UUID,
    record_type: str | None = None,
    year: int | None = None,
    page: int = 1,
    page_size: int = 50,
    db: AsyncSession = None,
) -> GrowthRecordListResponse:
    await _verify_student(student_id, user_id, db)

    query = select(GrowthRecord).where(GrowthRecord.student_id == student_id)

    if record_type:
        query = query.where(GrowthRecord.record_type == record_type)

    if year:
        start = date(year, 9, 1)
        end = date(year + 1, 8, 31)
        query = query.where(
            GrowthRecord.record_date >= start,
            GrowthRecord.record_date <= end,
        )

    count_result = await db.execute(
        select(func.count()).select_from(GrowthRecord).where(
            GrowthRecord.student_id == student_id
        )
    )
    total = count_result.scalar() or 0

    query = query.order_by(desc(GrowthRecord.record_date))
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    records = result.scalars().all()

    all_records_query = select(GrowthRecord).where(
        GrowthRecord.student_id == student_id
    ).order_by(desc(GrowthRecord.record_date))
    all_result = await db.execute(all_records_query)
    all_records = all_result.scalars().all()

    by_school_year = defaultdict(list)
    for rec in all_records:
        sy = _school_year_for(rec.record_date)
        by_school_year[sy].append(_to_response(rec))

    return GrowthRecordListResponse(
        growth_records=[_to_response(r) for r in records],
        total=total,
        by_school_year=dict(by_school_year),
    )


async def delete_growth_record(
    student_id: uuid.UUID,
    record_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> None:
    await _verify_student(student_id, user_id, db)
    record = await db.get(GrowthRecord, record_id)
    if record is None or record.student_id != student_id:
        raise ResourceNotFound()

    if record.image_url:
        try:
            delete_image(record.image_url)
        except Exception:
            pass

    await db.delete(record)
    await db.commit()


async def _match_quote(record_type: str, db: AsyncSession) -> DailyQuote | None:
    category = RECORD_TYPE_TO_QUOTE_CATEGORY.get(record_type, "encouragement")
    result = await db.execute(
        select(DailyQuote)
        .where(DailyQuote.category == category)
        .order_by(func.random())
        .limit(1)
    )
    return result.scalar_one_or_none()


def _to_response(record: GrowthRecord) -> GrowthRecordResponse:
    image_url = record.image_url
    if image_url:
        try:
            image_url = get_signed_url(image_url)
        except Exception:
            pass

    return GrowthRecordResponse(
        id=record.id,
        student_id=record.student_id,
        record_type=record.record_type,
        title=record.title,
        description=record.description,
        record_date=record.record_date,
        category=record.category,
        awarding_body=record.awarding_body,
        image_url=image_url,
        auto_generated=record.auto_generated,
        linked_quote_id=record.linked_quote_id,
        created_at=record.created_at,
    )


def _quote_to_response(quote: DailyQuote) -> QuoteResponse:
    return QuoteResponse(
        id=quote.id,
        content=quote.content,
        author=quote.author,
        category=quote.category,
        applicable_grades=quote.applicable_grades,
    )
