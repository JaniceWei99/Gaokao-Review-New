"""Error note service — CRUD, filtering, and statistics."""

from __future__ import annotations

import uuid

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.middleware.error_handler import ResourceNotFound, StudentNotFound
from app.middleware.permission import check_error_note_limit, get_user_plan
from app.models.error_note import ErrorNote
from app.models.student import Student
from app.models.subject import Subject
from app.schemas.error_note import (
    ErrorNoteCreate,
    ErrorNoteListResponse,
    ErrorNoteResponse,
    ErrorNoteStats,
)
from app.services.image_service import delete_image, get_signed_url


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


async def create_error_note(
    student_id: uuid.UUID,
    user_id: uuid.UUID,
    body: ErrorNoteCreate,
    db: AsyncSession,
) -> ErrorNoteResponse:
    student = await _verify_student(student_id, user_id, db)
    plan = await get_user_plan(user_id, db)
    await check_error_note_limit(student_id, db, plan)

    note = ErrorNote(
        student_id=student_id,
        subject_id=body.subject_id,
        knowledge_node_id=body.knowledge_node_id,
        error_type=body.error_type,
        source=body.source,
        question_image_url=body.question_image_url,
        correction_image_url=body.correction_image_url,
        note=body.note,
    )
    db.add(note)
    await db.flush()

    resp = _to_response(note)
    await db.commit()
    return resp


async def list_error_notes(
    student_id: uuid.UUID,
    user_id: uuid.UUID,
    subject_id: str | None = None,
    knowledge_node_id: uuid.UUID | None = None,
    error_type: str | None = None,
    source: str | None = None,
    page: int = 1,
    page_size: int = 20,
    sort: str = "newest",
    db: AsyncSession = None,
) -> ErrorNoteListResponse:
    await _verify_student(student_id, user_id, db)

    query = select(ErrorNote).where(ErrorNote.student_id == student_id)

    if subject_id:
        query = query.where(ErrorNote.subject_id == subject_id)
    if knowledge_node_id:
        query = query.where(ErrorNote.knowledge_node_id == knowledge_node_id)
    if error_type:
        query = query.where(ErrorNote.error_type == error_type)
    if source:
        query = query.where(ErrorNote.source == source)

    order_col = desc(ErrorNote.created_at) if sort == "newest" else ErrorNote.created_at
    query = query.order_by(order_col)

    count_result = await db.execute(
        select(func.count()).select_from(ErrorNote).where(ErrorNote.student_id == student_id)
    )
    total = count_result.scalar() or 0

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    notes = result.scalars().all()

    stats = await _compute_stats(student_id, db)

    return ErrorNoteListResponse(
        error_notes=[_to_response(n) for n in notes],
        total=total,
        page=page,
        page_size=page_size,
        stats=stats,
    )


async def get_error_note(
    student_id: uuid.UUID,
    note_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> ErrorNoteResponse:
    await _verify_student(student_id, user_id, db)
    note = await db.get(ErrorNote, note_id)
    if note is None or note.student_id != student_id:
        raise ResourceNotFound()
    return _to_response(note, with_signed_url=True)


async def delete_error_note(
    student_id: uuid.UUID,
    note_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> None:
    await _verify_student(student_id, user_id, db)
    note = await db.get(ErrorNote, note_id)
    if note is None or note.student_id != student_id:
        raise ResourceNotFound()

    if note.question_image_url:
        try:
            delete_image(note.question_image_url)
        except Exception:
            pass
    if note.correction_image_url:
        try:
            delete_image(note.correction_image_url)
        except Exception:
            pass

    await db.delete(note)
    await db.commit()


async def get_error_note_stats(
    student_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> dict:
    await _verify_student(student_id, user_id, db)
    return await _compute_detailed_stats(student_id, db)


async def _compute_stats(
    student_id: uuid.UUID, db: AsyncSession
) -> ErrorNoteStats:
    total_result = await db.execute(
        select(func.count()).select_from(ErrorNote).where(ErrorNote.student_id == student_id)
    )
    total_count = total_result.scalar() or 0

    by_subject_result = await db.execute(
        select(ErrorNote.subject_id, func.count())
        .where(ErrorNote.student_id == student_id)
        .group_by(ErrorNote.subject_id)
    )
    by_subject = {row[0]: row[1] for row in by_subject_result.all()}

    by_error_type_result = await db.execute(
        select(ErrorNote.error_type, func.count())
        .where(ErrorNote.student_id == student_id, ErrorNote.error_type.isnot(None))
        .group_by(ErrorNote.error_type)
    )
    by_error_type = {row[0]: row[1] for row in by_error_type_result.all()}

    return ErrorNoteStats(
        total_count=total_count,
        by_subject=by_subject,
        by_error_type=by_error_type,
    )


async def _compute_detailed_stats(
    student_id: uuid.UUID, db: AsyncSession
) -> dict:
    stats = await _compute_stats(student_id, db)

    by_subject_detail = []
    for subject_id, count in stats.by_subject.items():
        subject = await db.get(Subject, subject_id)
        by_subject_detail.append({
            "subject_id": subject_id,
            "subject_name": subject.name if subject else subject_id,
            "count": count,
        })

    by_error_type_detail = []
    for error_type, count in stats.by_error_type.items():
        by_error_type_detail.append({
            "error_type": error_type,
            "count": count,
        })

    by_knowledge_result = await db.execute(
        select(
            ErrorNote.knowledge_node_id,
            func.count(),
        )
        .where(
            ErrorNote.student_id == student_id,
            ErrorNote.knowledge_node_id.isnot(None),
        )
        .group_by(ErrorNote.knowledge_node_id)
    )
    by_knowledge_node = []
    for node_id, count in by_knowledge_result.all():
        from app.models.knowledge import KnowledgeNode

        node = await db.get(KnowledgeNode, node_id)
        subject_name = ""
        if node and node.subject_id:
            subject = await db.get(Subject, node.subject_id)
            subject_name = subject.name if subject else ""
        by_knowledge_node.append({
            "node_id": str(node_id),
            "node_name": node.name if node else str(node_id),
            "subject_name": subject_name,
            "count": count,
        })

    return {
        "total_count": stats.total_count,
        "by_subject": by_subject_detail,
        "by_error_type": by_error_type_detail,
        "by_knowledge_node": by_knowledge_node,
    }


def _to_response(note: ErrorNote, with_signed_url: bool = False) -> ErrorNoteResponse:
    question_url = note.question_image_url
    correction_url = note.correction_image_url

    if with_signed_url:
        try:
            question_url = get_signed_url(note.question_image_url)
        except Exception:
            pass
        if correction_url:
            try:
                correction_url = get_signed_url(note.correction_image_url)
            except Exception:
                pass

    return ErrorNoteResponse(
        id=note.id,
        student_id=note.student_id,
        subject_id=note.subject_id,
        knowledge_node_id=note.knowledge_node_id,
        error_type=note.error_type,
        source=note.source,
        question_image_url=question_url,
        correction_image_url=correction_url,
        note=note.note,
        created_at=note.created_at,
    )
