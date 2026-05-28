"""Tests for quote service — assignment algorithm."""

import pytest

from app.utils.date_utils import calculate_phase


class TestCalculatePhase:
    def test_normal_phase(self):
        assert calculate_phase("gao1", 60) == "normal"

    def test_pre_exam_30d(self):
        assert calculate_phase("gao3", 25) == "pre_exam_30d"

    def test_pre_exam_7d(self):
        assert calculate_phase("gao3", 5) == "pre_exam_7d"

    def test_post_exam(self):
        assert calculate_phase("gao3", 0) == "post_exam"
        assert calculate_phase("gao3", -3) == "post_exam"

    def test_none_days(self):
        assert calculate_phase("gao1", None) == "normal"

    def test_boundary_30(self):
        assert calculate_phase("gao2", 30) == "pre_exam_30d"

    def test_boundary_7(self):
        assert calculate_phase("gao2", 7) == "pre_exam_7d"

    def test_boundary_31(self):
        assert calculate_phase("gao2", 31) == "normal"

    def test_boundary_8(self):
        assert calculate_phase("gao2", 8) == "pre_exam_30d"
