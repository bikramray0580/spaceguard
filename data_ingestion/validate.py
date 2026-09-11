"""Validate CelesTrak GP JSON records before database insertion."""

from __future__ import annotations

from datetime import datetime
from math import isfinite
from typing import Any

REQUIRED_FIELDS = ("NORAD_CAT_ID", "EPOCH", "MEAN_MOTION")
NUMERIC_FIELDS = (
    "MEAN_MOTION",
    "ECCENTRICITY",
    "INCLINATION",
    "RA_OF_ASC_NODE",
    "ARG_OF_PERICENTER",
    "MEAN_ANOMALY",
    "BSTAR",
    "MEAN_MOTION_DOT",
    "MEAN_MOTION_DDOT",
)
INTEGER_FIELDS = ("NORAD_CAT_ID", "EPHEMERIS_TYPE", "ELEMENT_SET_NO", "REV_AT_EPOCH")
ANGLE_FIELDS = ("INCLINATION", "RA_OF_ASC_NODE", "ARG_OF_PERICENTER", "MEAN_ANOMALY")


def validate_records(records: list[dict]) -> tuple[list[dict], int]:
    """Return valid GP records and the number skipped.

    The database layer casts several fields before insertion, so validation
    checks type/range issues up front and returns normalized copies.
    """
    valid: list[dict] = []
    skipped = 0
    for item in records:
        normalized = normalize_record(item)
        if normalized is None:
            skipped += 1
            continue
        valid.append(normalized)
    return valid, skipped


def normalize_record(item: object) -> dict[str, Any] | None:
    """Return a cleaned GP record, or None when the record is unusable."""
    if not isinstance(item, dict):
        return None
    if any(_is_blank(item.get(field)) for field in REQUIRED_FIELDS):
        return None

    normalized = dict(item)
    for field in INTEGER_FIELDS:
        if field in normalized and not _is_blank(normalized.get(field)):
            value = _as_int(normalized[field])
            if value is None:
                return None
            normalized[field] = value

    if normalized["NORAD_CAT_ID"] <= 0:
        return None

    for field in NUMERIC_FIELDS:
        if field in normalized and not _is_blank(normalized.get(field)):
            value = _as_float(normalized[field])
            if value is None:
                return None
            normalized[field] = value

    epoch = _normalize_epoch(normalized["EPOCH"])
    if epoch is None:
        return None
    normalized["EPOCH"] = epoch

    if normalized["MEAN_MOTION"] <= 0:
        return None
    eccentricity = normalized.get("ECCENTRICITY")
    if eccentricity is not None and not 0 <= eccentricity < 1:
        return None
    inclination = normalized.get("INCLINATION")
    if inclination is not None and not 0 <= inclination <= 180:
        return None
    for field in ANGLE_FIELDS:
        value = normalized.get(field)
        if value is not None and field != "INCLINATION" and not 0 <= value < 360:
            return None

    return normalized


def _is_blank(value: object) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _as_int(value: object) -> int | None:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def _as_float(value: object) -> float | None:
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    if not isfinite(number):
        return None
    return number


def _normalize_epoch(value: object) -> str | None:
    if _is_blank(value):
        return None
    text = str(value).strip()
    parseable = text.replace("Z", "+00:00")
    try:
        datetime.fromisoformat(parseable)
    except ValueError:
        return None
    return text
