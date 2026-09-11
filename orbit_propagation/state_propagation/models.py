"""Models representing a propagated orbital state."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Sequence


def _as_xyz(value: Sequence[float], name: str) -> tuple[float, float, float]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise TypeError(f"{name} must be a sequence of three numeric components")
    if len(value) != 3:
        raise ValueError(f"{name} must contain exactly three components")
    try:
        x, y, z = (float(value[0]), float(value[1]), float(value[2]))
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{name} components must be numeric") from exc
    return (x, y, z)


def _require_non_empty_str(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


@dataclass(frozen=True)
class PropagatedState:
    """A single propagated orbital state at a given epoch.

    Attributes:
        timestamp: Epoch of the state.
        position: Position vector (x, y, z) in ``position_units``.
        velocity: Velocity vector (vx, vy, vz) in ``velocity_units``.
        frame: Coordinate / reference frame (for example ``TEME`` or ``ECI``).
        position_units: Length unit for ``position``.
        velocity_units: Speed unit for ``velocity``.
    """

    timestamp: datetime
    position: tuple[float, float, float]
    velocity: tuple[float, float, float]
    frame: str
    position_units: str
    velocity_units: str

    def __post_init__(self) -> None:
        if not isinstance(self.timestamp, datetime):
            raise TypeError("timestamp must be a datetime instance")
        object.__setattr__(self, "position", _as_xyz(self.position, "position"))
        object.__setattr__(self, "velocity", _as_xyz(self.velocity, "velocity"))
        object.__setattr__(self, "frame", _require_non_empty_str(self.frame, "frame"))
        object.__setattr__(
            self,
            "position_units",
            _require_non_empty_str(self.position_units, "position_units"),
        )
        object.__setattr__(
            self,
            "velocity_units",
            _require_non_empty_str(self.velocity_units, "velocity_units"),
        )
