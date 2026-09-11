"""SGP4 propagator for a TLE at a single UTC timestamp."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sgp4.api import Satrec, jday

from orbit_propagation.state_propagation.models import PropagatedState

SGP4_FRAME = "TEME"
POSITION_UNITS = "km"
VELOCITY_UNITS = "km/s"


def _require_tle_line(value: object, name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    line = value.strip()
    if not line:
        raise ValueError(f"{name} must be a non-empty TLE line")
    return line


def _require_utc_datetime(value: object, name: str = "timestamp") -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{name} must be a datetime instance")
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _require_positive_step(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("step_seconds must be a number")
    if value <= 0:
        raise ValueError("step_seconds must be greater than 0")
    return float(value)


class SGP4Propagator:
    """Propagate a two-line element set with SGP4 to one epoch."""

    def propagate(
        self,
        line1: str,
        line2: str,
        timestamp: datetime,
    ) -> PropagatedState:
        """Parse a TLE and propagate it to ``timestamp``.

        Args:
            line1: First TLE line.
            line2: Second TLE line.
            timestamp: Requested epoch in UTC. Naive datetimes are treated as UTC.

        Returns:
            PropagatedState in TEME with position in km and velocity in km/s.
        """
        line1 = _require_tle_line(line1, "line1")
        line2 = _require_tle_line(line2, "line2")
        utc = _require_utc_datetime(timestamp)

        try:
            satellite = Satrec.twoline2rv(line1, line2)
        except (ValueError, TypeError, IndexError) as exc:
            raise ValueError("invalid TLE input") from exc

        if satellite.error != 0:
            raise ValueError("invalid TLE input")

        second = utc.second + utc.microsecond / 1_000_000.0
        julian_day, julian_fraction = jday(
            utc.year,
            utc.month,
            utc.day,
            utc.hour,
            utc.minute,
            second,
        )
        error, position, velocity = satellite.sgp4(julian_day, julian_fraction)

        if error != 0:
            raise ValueError("SGP4 could not propagate the TLE to the requested time")

        return PropagatedState(
            timestamp=utc,
            position=(float(position[0]), float(position[1]), float(position[2])),
            velocity=(float(velocity[0]), float(velocity[1]), float(velocity[2])),
            frame=SGP4_FRAME,
            position_units=POSITION_UNITS,
            velocity_units=VELOCITY_UNITS,
        )

    def propagate_window(
        self,
        line1: str,
        line2: str,
        start_time: datetime,
        end_time: datetime,
        step_seconds: float,
    ) -> list[PropagatedState]:
        """Propagate a TLE across a time window at a fixed step.

        Timestamps start at ``start_time`` and advance by ``step_seconds``.
        ``end_time`` is included only when a generated timestamp lands on it
        exactly. Each state is produced by ``propagate()``.
        """
        start_utc = _require_utc_datetime(start_time, "start_time")
        end_utc = _require_utc_datetime(end_time, "end_time")
        if end_utc < start_utc:
            raise ValueError("end_time must be greater than or equal to start_time")
        step = _require_positive_step(step_seconds)
        delta = timedelta(seconds=step)

        states: list[PropagatedState] = []
        current = start_utc
        while current <= end_utc:
            states.append(self.propagate(line1, line2, current))
            next_time = current + delta
            if next_time <= current:
                raise ValueError("step_seconds is too small to advance the window")
            current = next_time
        return states
