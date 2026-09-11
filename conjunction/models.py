"""Serializable data contracts used by nominal conjunction assessment."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from math import isclose, isfinite, sqrt
from typing import Literal

Vector3 = tuple[float, float, float]
SUPPORTED_REFERENCE_FRAMES = frozenset({"TEME", "GCRF", "ITRF", "ECEF"})


def _vector(values: tuple[float, float, float], name: str) -> Vector3:
    if len(values) != 3 or not all(isfinite(float(value)) for value in values):
        raise ValueError(f"{name} must contain exactly three finite values")
    return tuple(float(value) for value in values)  # type: ignore[return-value]


@dataclass(frozen=True)
class StateVector:
    """A UTC-aware Cartesian state in one declared frame (km and km/s)."""

    object_id: str
    epoch: datetime
    position_km: Vector3
    velocity_km_s: Vector3
    reference_frame: str

    def __post_init__(self) -> None:
        if not self.object_id:
            raise ValueError("object_id is required")
        if self.epoch.tzinfo is None or self.epoch.utcoffset() is None:
            raise ValueError("epoch must be a UTC-aware datetime")
        if self.reference_frame not in SUPPORTED_REFERENCE_FRAMES:
            raise ValueError(f"unsupported reference frame: {self.reference_frame}")
        object.__setattr__(self, "position_km", _vector(self.position_km, "position_km"))
        object.__setattr__(self, "velocity_km_s", _vector(self.velocity_km_s, "velocity_km_s"))


@dataclass(frozen=True)
class TcaQuality:
    """Numerical evidence produced by broad screening and refinement."""

    sample_count: int
    bracket_start: datetime
    bracket_end: datetime
    residual_km2_s: float  # dot(relative_position, relative_velocity) at TCA
    converged: bool
    boundary_minimum: bool

    def __post_init__(self) -> None:
        if self.sample_count < 1 or self.bracket_end < self.bracket_start:
            raise ValueError("invalid TCA quality bracket")
        if not isfinite(self.residual_km2_s):
            raise ValueError("TCA residual must be finite")


@dataclass(frozen=True)
class ConjunctionResult:
    """Nominal, covariance-free handoff contract for the uncertainty module."""

    object_a_id: str
    object_b_id: str
    tca: datetime
    relative_position_km: Vector3
    relative_velocity_km_s: Vector3
    miss_distance_vector_km: Vector3
    miss_distance_km: float
    relative_speed_km_s: float
    closing_rate_km_s: float
    relative_motion_direction: Vector3 | None
    miss_distance_direction: Vector3 | None
    reference_frame: str
    tca_quality: TcaQuality
    status: Literal["success", "boundary_minimum"]

    def __post_init__(self) -> None:
        if self.tca.tzinfo is None or self.tca.utcoffset() is None:
            raise ValueError("tca must be a UTC-aware datetime")
        if self.reference_frame not in SUPPORTED_REFERENCE_FRAMES:
            raise ValueError(f"unsupported reference frame: {self.reference_frame}")
        for name in ("relative_position_km", "relative_velocity_km_s", "miss_distance_vector_km"):
            object.__setattr__(self, name, _vector(getattr(self, name), name))
        for name in ("miss_distance_km", "relative_speed_km_s", "closing_rate_km_s"):
            if not isfinite(getattr(self, name)):
                raise ValueError(f"{name} must be finite")
        if self.miss_distance_km < 0 or self.relative_speed_km_s < 0:
            raise ValueError("miss distance and relative speed must be non-negative")
        position_norm = sqrt(sum(component * component for component in self.relative_position_km))
        if not isclose(position_norm, self.miss_distance_km, rel_tol=1e-12, abs_tol=1e-12):
            raise ValueError("miss_distance_km must equal the relative-position magnitude")
        if self.miss_distance_vector_km != self.relative_position_km:
            raise ValueError("miss-distance vector must equal relative position at TCA")
        for name in ("relative_motion_direction", "miss_distance_direction"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, _vector(value, name))

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-ready representation (datetimes are ISO-8601 strings)."""
        value = asdict(self)
        value["tca"] = self.tca.isoformat()
        quality = value["tca_quality"]
        assert isinstance(quality, dict)
        quality["bracket_start"] = self.tca_quality.bracket_start.isoformat()
        quality["bracket_end"] = self.tca_quality.bracket_end.isoformat()
        return value
