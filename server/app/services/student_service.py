"""Student service — CRUD operations and subject-selection validation."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.middleware.error_handler import ResourceNotFound, StudentNotFound
from app.models.student import Student
from app.schemas.student import StudentCreate, StudentResponse, StudentUpdate

ELECTIVE_SUBJECTS = {"physics", "chemistry", "biology", "politics", "history", "geography"}


def _subjects_to_columns(selected_subjects: list[str] | None) -> dict:
    """Convert a list of 3 elective subjects to the three DB columns."""
    if not selected_subjects:
        return {
            "selected_subject_1": None,
            "selected_subject_2": None,
            "selected_subject_3": None,
        }
    return {
        "selected_subject_1": selected_subjects[0] if len(selected_subjects) > 0 else None,
        "selected_subject_2": selected_subjects[1] if len(selected_subjects) > 1 else None,
        "selected_subject_3": selected_subjects[2] if len(selected_subjects) > 2 else None,
    }


async def list_students(user_id: uuid.UUID, db: AsyncSession) -> list[StudentResponse]:
    """List all students belonging to the authenticated user."""
    result = await db.execute(
        select(Student)
        .where(Student.user_id == user_id)
        .order_by(Student.created_at)
    )
    students = result.scalars().all()
    return [StudentResponse.model_validate(s) for s in students]


async def get_student(student_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession) -> StudentResponse:
    """Get a single student by ID, ensuring it belongs to the user."""
    result = await db.execute(
        select(Student).where(Student.id == student_id, Student.user_id == user_id)
    )
    student = result.scalar_one_or_none()
    if student is None:
        raise StudentNotFound()
    return StudentResponse.model_validate(student)


async def create_student(user_id: uuid.UUID, data: StudentCreate, db: AsyncSession) -> StudentResponse:
    """Create a new student profile for the authenticated user."""
    subject_cols = _subjects_to_columns(data.selected_subjects)

    student = Student(
        user_id=user_id,
        name=data.name,
        grade=data.grade,
        province=data.province,
        region_code=data.region_code,
        has_selected_subjects=data.has_selected_subjects,
        has_jan_english_exam=data.has_jan_english_exam,
        **subject_cols,
    )
    db.add(student)
    await db.flush()

    return StudentResponse.model_validate(student)


async def update_student(
    student_id: uuid.UUID,
    user_id: uuid.UUID,
    data: StudentUpdate,
    db: AsyncSession,
) -> StudentResponse:
    """Update an existing student profile."""
    result = await db.execute(
        select(Student).where(Student.id == student_id, Student.user_id == user_id)
    )
    student = result.scalar_one_or_none()
    if student is None:
        raise StudentNotFound()

    update_data = data.model_dump(exclude_unset=True)

    if "selected_subjects" in update_data:
        subject_cols = _subjects_to_columns(update_data.pop("selected_subjects"))
        update_data.update(subject_cols)

    for field, value in update_data.items():
        setattr(student, field, value)

    await db.flush()

    return StudentResponse.model_validate(student)


async def delete_student(student_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession) -> None:
    """Delete a student profile."""
    result = await db.execute(
        select(Student).where(Student.id == student_id, Student.user_id == user_id)
    )
    student = result.scalar_one_or_none()
    if student is None:
        raise StudentNotFound()

    await db.delete(student)
    await db.flush()
