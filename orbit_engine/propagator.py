"""SGP4-based propagation of satellite TLEs into TEME state vectors."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import overload

from sgp4.api import SGP4_ERRORS, Satrec
from sgp4.conveniences import jday_datetime

from .models import Position, PropagationResult, Velocity
from .utils import require_utc_datetime


class TLEValidationError(ValueError):
    """Raised when TLE lines are structurally invalid or cannot be parsed."""


class PropagationError(RuntimeError):
    """Raised when SGP4 cannot compute a valid state vector."""


def parse_tle(line1: str, line2: str) -> Satrec:
    """Create an SGP4 record from a matching pair of TLE lines."""
    if not isinstance(line1, str) or not isinstance(line2, str):
        raise TLEValidationError("TLE lines must be strings")
    line1, line2 = line1.rstrip(), line2.rstrip()
    if len(line1) < 69 or len(line2) < 69:
        raise TLEValidationError("TLE lines must each contain at least 69 characters")
    if not line1.startswith("1 ") or not line2.startswith("2 "):
        raise TLEValidationError("TLE line 1 must start with '1 ' and line 2 with '2 '")
    if line1[2:7] != line2[2:7]:
        raise TLEValidationError("TLE lines refer to different satellite catalog IDs")
    try:
        satellite = Satrec.twoline2rv(line1, line2)
    except (TypeError, ValueError, RuntimeError) as error:
        raise TLEValidationError(f"Unable to parse TLE: {error}") from error
    if satellite.satnum <= 0:
        raise TLEValidationError("Unable to parse a valid satellite catalog ID from TLE")
    return satellite


def _propagate_satellite(
    satellite: Satrec, name: str, timestamp: datetime
) -> PropagationResult:
    timestamp = require_utc_datetime(timestamp)
    julian_date, fraction = jday_datetime(timestamp)
    error_code, position, velocity = satellite.sgp4(julian_date, fraction)
    if error_code != 0:
        message = SGP4_ERRORS.get(error_code, "unknown SGP4 error")
        raise PropagationError(
            f"SGP4 failed for satellite {satellite.satnum} at "
            f"{timestamp.isoformat()}: [{error_code}] {message}"
        )
    if len(position) != 3 or len(velocity) != 3:
        raise PropagationError("SGP4 returned an incomplete position or velocity vector")

    return PropagationResult(
        object_id=str(satellite.satnum),
        object_name=name,
        timestamp=timestamp,
        position=Position(*map(float, position)),
        velocity=Velocity(*map(float, velocity)),
    )


@overload
def propagate_tle(
    name: str, line1: str, line2: str, timestamps: datetime
) -> PropagationResult: ...


@overload
def propagate_tle(
    name: str, line1: str, line2: str, timestamps: Iterable[datetime]
) -> list[PropagationResult]: ...


def propagate_tle(
    name: str, line1: str, line2: str, timestamps: datetime | Iterable[datetime]
) -> PropagationResult | list[PropagationResult]:
    """Propagate a TLE at one aware UTC time or a series of aware UTC times.

    Returned position is ``x/y/z`` kilometres and velocity is ``vx/vy/vz``
    kilometres per second, both expressed in the TEME frame.
    """
    if not isinstance(name, str) or not name.strip():
        raise ValueError("name must be a non-empty string")
    satellite = parse_tle(line1, line2)
    if isinstance(timestamps, datetime):
        return _propagate_satellite(satellite, name, timestamps)
    try:
        timestamp_list = list(timestamps)
    except TypeError as error:
        raise TypeError("timestamps must be a datetime or iterable of datetimes") from error
    return [_propagate_satellite(satellite, name, timestamp) for timestamp in timestamp_list]
