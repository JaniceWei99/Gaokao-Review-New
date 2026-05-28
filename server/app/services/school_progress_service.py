"""School progress service — CRUD and error-note linkage."""

from __future__ import annotations

import uuid

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.middleware.error_handler import ResourceNotFound, StudentNotFound
from app.models.error_note import ErrorNote
from app.models.school_progress import SchoolProgress
from app.models.student import Student


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


async def list_school_progress(
    student_id: uuid.UUID,
    user_id: uuid.UUID,
    subject_id: str | None = None,
    db: AsyncSession = None,
) -> list[dict]:
    await _verify_student(student_id, user_id, db)

    query = select(SchoolProgress).where(
        SchoolProgress.student_id == student_id
    )
    if subject_id:
        query = query.where(SchoolProgress.subject_id == subject_id)

    query = query.order_by(desc(SchoolProgress.created_at))
    result = await db.execute(query)
    records = result.scalars().all()

    items = []
    for r in records:
        error_count = 0
        if r.knowledge_node_id:
            count_result = await db.execute(
                select(func.count()).select_from(ErrorNote).where(
                    ErrorNote.student_id == student_id,
                    ErrorNote.knowledge_node_id == r.knowledge_node_id,
                )
            )
            error_count = count_result.scalar() or 0

        items.append({
            "id": str(r.id),
            "student_id": str(r.student_id),
            "subject_id": r.subject_id,
            "content": r.content,
            "start_date": r.start_date.isoformat() if r.start_date else None,
            "end_date": r.end_date.isoformat() if r.end_date else None,
            "knowledge_node_id": str(r.knowledge_node_id) if r.knowledge_node_id else None,
            "error_count": error_count,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        })

    return items


async def create_school_progress(
    student_id: uuid.UUID,
    user_id: uuid.UUID,
    subject_id: str,
    content: str,
    start_date: str | None = None,
    end_date: str | None = None,
    knowledge_node_id: str | None = None,
    db: AsyncSession = None,
) -> dict:
    await _verify_student(student_id, user_id, db)

    import datetime

    record = SchoolProgress(
        student_id=student_id,
        subject_id=subject_id,
        content=content,
        start_date=datetime.date.fromisoformat(start_date) if start_date else None,
        end_date=datetime.date.fromisoformat(end_date) if end_date else None,
        knowledge_node_id=uuid.UUID(knowledge_node_id) if knowledge_node_id else None,
    )
    db.add(record)
    await db.flush()

    error_count = 0
    if record.knowledge_node_id:
        count_result = await db.execute(
            select(func.count()).select_from(ErrorNote).where(
                ErrorNote.student_id == student_id,
                ErrorNote.knowledge_node_id == record.knowledge_node_id,
            )
        )
        error_count = count_result.scalar() or 0

    await db.commit()

    return {
        "id": str(record.id),
        "student_id": str(record.student_id),
        "subject_id": record.subject_id,
        "content": record.content,
        "start_date": record.start_date.isoformat() if record.start_date else None,
        "end_date": record.end_date.isoformat() if record.end_date else None,
        "knowledge_node_id": str(record.knowledge_node_id) if record.knowledge_node_id else None,
        "error_count": error_count,
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "updated_at": record.updated_at.isoformat() if record.updated_at else None,
    }


async def update_school_progress(
    student_id: uuid.UUID,
    progress_id: uuid.UUID,
    user_id: uuid.UUID,
    content: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    knowledge_node_id: str | None = None,
    db: AsyncSession = None,
) -> dict:
    await _verify_student(student_id, user_id, db)

    record = await db.get(SchoolProgress, progress_id)
    if record is None or record.student_id != student_id:
        raise ResourceNotFound()

    import datetime

    if content is not None:
        record.content = content
    if start_date is not None:
        record.start_date = datetime.date.fromisoformat(start_date) if start_date else None
    if end_date is not None:
        record.end_date = datetime.date.fromisoformat(end_date) if end_date else None
    if knowledge_node_id is not None:
        record.knowledge_node_id = uuid.UUID(knowledge_node_id) if knowledge_node_id else None

    await db.flush()

    error_count = 0
    if record.knowledge_node_id:
        count_result = await db.execute(
            select(func.count()).select_from(ErrorNote).where(
                ErrorNote.student_id == student_id,
                ErrorNote.knowledge_node_id == record.knowledge_node_id,
            )
        )
        error_count = count_result.scalar() or 0

    await db.commit()

    return {
        "id": str(record.id),
        "student_id": str(record.student_id),
        "subject_id": record.subject_id,
        "content": record.content,
        "start_date": record.start_date.isoformat() if record.start_date else None,
        "end_date": record.end_date.isoformat() if record.end_date else None,
        "knowledge_node_id": str(record.knowledge_node_id) if record.knowledge_node_id else None,
        "error_count": error_count,
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "updated_at": record.updated_at.isoformat() if record.updated_at else None,
    }


async def delete_school_progress(
    student_id: uuid.UUID,
    progress_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> None:
    await _verify_student(student_id, user_id, db)

    record = await db.get(SchoolProgress, progress_id)
    if record is None or record.student_id != student_id:
        raise ResourceNotFound()

    await db.delete(record)
    await db.commit()


async def get_linked_errors(
    student_id: uuid.UUID,
    progress_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> list[dict]:
    await _verify_student(student_id, user_id, db)

    record = await db.get(SchoolProgress, progress_id)
    if record is None or record.student_id != student_id:
        raise ResourceNotFound()

    if not record.knowledge_node_id:
        return []

    result = await db.execute(
        select(ErrorNote)
        .where(
            ErrorNote.student_id == student_id,
            ErrorNote.knowledge_node_id == record.knowledge_node_id,
        )
        .order_by(desc(ErrorNote.created_at))
    )
    errors = result.scalars().all()

    return [
        {
            "id": str(e.id),
            "subject_id": e.subject_id,
            "error_type": e.error_type,
            "source": e.source,
            "note": e.note,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in errors
    ]
