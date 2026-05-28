"""Student profile schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

ELECTIVE_SUBJECTS: set[str] = {
    "physics",
    "chemistry",
    "biology",
    "politics",
    "history",
    "geography",
}


class StudentCreate(BaseModel):
    """Payload for creating a new student profile."""

    name: str = Field(..., max_length=20)
    grade: Literal["gao1", "gao2", "gao3"]
    district: str | None = Field(None, max_length=20)
    has_selected_subjects: bool = False
    selected_subjects: list[str] | None = Field(
        None, description="List of exactly 3 elective subject IDs"
    )
    has_jan_english_exam: bool = False

    @model_validator(mode="after")
    def _validate_subjects(self) -> StudentCreate:
        # gao3 students must have selected subjects
        if self.grade == "gao3" and not self.has_selected_subjects:
            raise ValueError(
                "高三学生必须已选科 (has_selected_subjects must be True for gao3)"
            )
        if self.grade == "gao3" and (
            not self.selected_subjects or len(self.selected_subjects) != 3
        ):
            raise ValueError(
                "高三学生必须选择3门选考科目 (selected_subjects must have exactly 3 items for gao3)"
            )

        # If subjects are flagged as selected, validate them
        if self.has_selected_subjects:
            if not self.selected_subjects or len(self.selected_subjects) != 3:
                raise ValueError(
                    "已选科时必须提供恰好3门科目 (selected_subjects must have exactly 3 items)"
                )
            if len(set(self.selected_subjects)) != 3:
                raise ValueError(
                    "选考科目不能重复 (selected_subjects must contain 3 unique items)"
                )
            invalid = set(self.selected_subjects) - ELECTIVE_SUBJECTS
            if invalid:
                raise ValueError(
                    f"无效的选考科目: {invalid}，"
                    f"可选项为: {sorted(ELECTIVE_SUBJECTS)}"
                )

        # Clear selected_subjects when not selected
        if not self.has_selected_subjects:
            self.selected_subjects = None

        return self


class StudentUpdate(BaseModel):
    """Payload for updating an existing student profile (all fields optional)."""

    name: str | None = Field(None, max_length=20)
    grade: Literal["gao1", "gao2", "gao3"] | None = None
    district: str | None = None
    has_selected_subjects: bool | None = None
    selected_subjects: list[str] | None = None
    has_jan_english_exam: bool | None = None


class StudentListResponse(BaseModel):
    """Wrapper for a list of students."""

    students: list[StudentResponse]


class StudentResponse(BaseModel):
    """Student profile as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    grade: str
    district: str | None
    has_selected_subjects: bool
    selected_subject_1: str | None
    selected_subject_2: str | None
    selected_subject_3: str | None
    has_jan_english_exam: bool
    created_at: datetime
    updated_at: datetime
