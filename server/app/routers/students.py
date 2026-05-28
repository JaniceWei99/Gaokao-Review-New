"""Students router — CRUD for student profiles."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user_id
from app.schemas.student import StudentCreate, StudentListResponse, StudentResponse, StudentUpdate
from app.services.student_service import (
    create_student,
    delete_student,
    get_student,
    list_students,
    update_student,
)

router = APIRouter()


@router.get("", response_model=StudentListResponse)
async def list_my_students(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List all student profiles for the authenticated user."""
    students = await list_students(user_id, db)
    return StudentListResponse(students=students)


@router.post("", response_model=StudentResponse, status_code=201)
async def create_my_student(
    body: StudentCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Create a new student profile (during onboarding or later)."""
    return await create_student(user_id, body, db)


@router.get("/{student_id}", response_model=StudentResponse)
async def get_my_student(
    student_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get a single student profile by ID."""
    return await get_student(student_id, user_id, db)


@router.put("/{student_id}", response_model=StudentResponse)
async def update_my_student(
    student_id: uuid.UUID,
    body: StudentUpdate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing student profile."""
    return await update_student(student_id, user_id, body, db)


@router.delete("/{student_id}", status_code=204)
async def delete_my_student(
    student_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete a student profile."""
    await delete_student(student_id, user_id, db)
