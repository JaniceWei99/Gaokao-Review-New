"""Province reference data — loaded from seeds at import time.

Provides province-aware subject scores, elective counts, and school system info.
For multi-province: add a new entry to seeds/provinces.json and this module picks it up.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_SEEDS_DIR = Path(__file__).resolve().parent.parent.parent / "seeds"

_provinces: list[dict[str, Any]] = []
_provinces_by_id: dict[str, dict[str, Any]] = {}
_regions: list[dict[str, Any]] = []
_regions_by_province: dict[str, list[dict[str, Any]]] = {}

# Default fallback scores when province has no override
_DEFAULT_MAX_SCORES: dict[str, int] = {
    "chinese": 150,
    "math": 150,
    "english": 150,
    "physics": 100,
    "chemistry": 100,
    "biology": 100,
    "politics": 100,
    "history": 100,
    "geography": 100,
}


def _load() -> None:
    global _provinces, _provinces_by_id, _regions, _regions_by_province

    provinces_path = _SEEDS_DIR / "provinces.json"
    regions_path = _SEEDS_DIR / "regions.json"

    if provinces_path.exists():
        _provinces = json.loads(provinces_path.read_text(encoding="utf-8"))
        _provinces_by_id = {p["id"]: p for p in _provinces}
        logger.info("Loaded %d provinces", len(_provinces))
    else:
        logger.warning("provinces.json not found at %s", provinces_path)

    if regions_path.exists():
        _regions = json.loads(regions_path.read_text(encoding="utf-8"))
        for r in _regions:
            prov = r.get("province", "shanghai")
            _regions_by_province.setdefault(prov, []).append(r)
        logger.info("Loaded %d regions", len(_regions))


def get_provinces() -> list[dict[str, Any]]:
    if not _provinces:
        _load()
    return _provinces


def get_province(province_id: str) -> dict[str, Any] | None:
    if not _provinces_by_id:
        _load()
    return _provinces_by_id.get(province_id)


def get_regions(province_id: str | None = None) -> list[dict[str, Any]]:
    if not _regions:
        _load()
    if province_id:
        return _regions_by_province.get(province_id, [])
    return _regions


def get_default_max_score(subject_id: str, province: str | None = None) -> int:
    """Resolve the default max score for a subject.

    Priority: province config > subject table default (100/150).
    """
    if province:
        prov = get_province(province)
        if prov:
            scores = prov.get("gaokao_max_scores", {})
            if subject_id in scores:
                return scores[subject_id]
    return _DEFAULT_MAX_SCORES.get(subject_id, 100)


def get_elective_count(province: str | None = None) -> int:
    """How many elective subjects the student must choose."""
    if province:
        prov = get_province(province)
        if prov:
            return prov.get("elective_count", 3)
    return 3


def get_property(province: str, key: str, default: Any = None) -> Any:
    """Get a boolean/string property from province config."""
    prov = get_province(province)
    if prov:
        return prov.get(key, default)
    return default


def has_spring_exam(province: str) -> bool:
    return bool(get_property(province, "has_spring_exam", False))


def has_english_twice(province: str) -> bool:
    return bool(get_property(province, "english_exam_twice", False))


# Load on import
_load()
