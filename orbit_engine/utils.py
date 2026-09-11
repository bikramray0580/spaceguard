"""Datetime helpers for the orbit propagation module."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone


def require_utc_datetime(timestamp: datetime) -> datetime:
    """Validate an aware datetime and normalize it to UTC.

    A naive datetime has no unambiguous instant, so the public API rejects it
    instead of assuming a local timezone.
    """
    if not isinstance(timestamp, datetime):
        raise TypeError("timestamp must be a datetime")
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware (use UTC)")
    return timestamp.astimezone(timezone.utc)


def generate_time_steps(
    start_time: datetime, end_time: datetime, step_minutes: float
) -> list[datetime]:
    """Generate inclusive, timezone-aware UTC timestamps at a fixed interval.

    The end time must lie exactly on a step. This prevents a caller from
    accidentally receiving an unexpected final timestamp beyond its range.
    """
    start = require_utc_datetime(start_time)
    end = require_utc_datetime(end_time)
    if end < start:
        raise ValueError("end_time must be greater than or equal to start_time")
    if step_minutes <= 0:
        raise ValueError("step_minutes must be greater than zero")

    step = timedelta(minutes=step_minutes)
    timestamps: list[datetime] = []
    current = start
    while current <= end:
        timestamps.append(current)
        current += step
    if timestamps[-1] != end:
        raise ValueError("end_time must fall exactly on a time step")
    return timestamps
