"""Tests for milestone service — filtering logic."""

import pytest

from app.utils.date_utils import days_until, school_year_for


class TestDaysUntil:
    def test_future_date(self):
        from datetime import date, timedelta

        future = date.today() + timedelta(days=10)
        assert days_until(future) == 10

    def test_past_date(self):
        from datetime import date, timedelta

        past = date.today() - timedelta(days=5)
        assert days_until(past) == -5

    def test_today(self):
        assert days_until(date.today()) == 0

    def test_string_input(self):
        from datetime import date, timedelta

        future = (date.today() + timedelta(days=7)).isoformat()
        assert days_until(future) == 7


class TestSchoolYear:
    def test_september(self):
        from datetime import date

        result = school_year_for(date(2025, 9, 1))
        assert result == "2025-2026"

    def test_december(self):
        from datetime import date

        result = school_year_for(date(2025, 12, 15))
        assert result == "2025-2026"

    def test_january(self):
        from datetime import date

        result = school_year_for(date(2026, 1, 10))
        assert result == "2025-2026"

    def test_august(self):
        from datetime import date

        result = school_year_for(date(2026, 8, 31))
        assert result == "2025-2026"
