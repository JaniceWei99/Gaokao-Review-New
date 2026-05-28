"""Tests for student service — subject selection validation."""

import pytest
from pydantic import ValidationError

from app.schemas.student import StudentCreate, StudentUpdate


class TestStudentCreateValidation:
    def test_gao1_without_subjects(self):
        s = StudentCreate(name="测试", grade="gao1")
        assert s.has_selected_subjects is False
        assert s.selected_subjects is None

    def test_gao1_with_subjects(self):
        s = StudentCreate(
            name="测试",
            grade="gao1",
            has_selected_subjects=True,
            selected_subjects=["physics", "chemistry", "history"],
        )
        assert s.has_selected_subjects is True
        assert s.selected_subjects == ["physics", "chemistry", "history"]

    def test_gao3_must_have_subjects(self):
        with pytest.raises(ValidationError, match="高三"):
            StudentCreate(name="测试", grade="gao3", has_selected_subjects=False)

    def test_gao3_must_have_three_subjects(self):
        with pytest.raises(ValidationError, match="3门"):
            StudentCreate(
                name="测试",
                grade="gao3",
                has_selected_subjects=True,
                selected_subjects=["physics", "chemistry"],
            )

    def test_gao3_valid_subjects(self):
        s = StudentCreate(
            name="测试",
            grade="gao3",
            has_selected_subjects=True,
            selected_subjects=["physics", "chemistry", "biology"],
        )
        assert s.selected_subjects == ["physics", "chemistry", "biology"]

    def test_duplicate_subjects_rejected(self):
        with pytest.raises(ValidationError, match="重复"):
            StudentCreate(
                name="测试",
                grade="gao2",
                has_selected_subjects=True,
                selected_subjects=["physics", "physics", "chemistry"],
            )

    def test_invalid_subject_id_rejected(self):
        with pytest.raises(ValidationError, match="无效"):
            StudentCreate(
                name="测试",
                grade="gao2",
                has_selected_subjects=True,
                selected_subjects=["physics", "chemistry", "math"],
            )

    def test_has_selected_false_clears_subjects(self):
        s = StudentCreate(
            name="测试",
            grade="gao1",
            has_selected_subjects=False,
            selected_subjects=["physics", "chemistry", "biology"],
        )
        assert s.selected_subjects is None

    def test_district_optional(self):
        s = StudentCreate(name="测试", grade="gao1", district="xuhui")
        assert s.district == "xuhui"

    def test_jan_english_exam_default_false(self):
        s = StudentCreate(name="测试", grade="gao3", has_selected_subjects=True,
                          selected_subjects=["physics", "chemistry", "biology"])
        assert s.has_jan_english_exam is False


class TestStudentUpdateValidation:
    def test_all_fields_optional(self):
        s = StudentUpdate()
        assert s.name is None
        assert s.grade is None

    def test_partial_update(self):
        s = StudentUpdate(name="新名字", district="pudong")
        assert s.name == "新名字"
        assert s.district == "pudong"
