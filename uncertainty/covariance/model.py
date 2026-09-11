"""Validated 6-D Cartesian covariance data contract (km and km/s)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

import numpy as np

STATE_ORDER = ("x", "y", "z", "vx", "vy", "vz")


def _utc_time(value: datetime, name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value


@dataclass(frozen=True)
class Covariance:
    """A PSD 6x6 covariance for ``[x,y,z,vx,vy,vz]``.

    Position units are km², velocity units are (km/s)², and the off-diagonal
    block uses km²/s.  No frame or epoch transformation is implicit.
    """

    matrix: np.ndarray | Iterable[Iterable[float]]
    epoch: datetime
    reference_frame: str
    source: str = "unknown"
    estimated: bool = False
    authoritative: bool = False
    state_order: tuple[str, ...] = STATE_ORDER
    validation_message: str = "validated 6x6 covariance"
    symmetry_tolerance: float = 1e-10
    psd_tolerance: float = 1e-10
    propagation_duration_seconds: float | None = None
    propagation_direction: str | None = None

    def __post_init__(self) -> None:
        array = np.array(self.matrix, dtype=float, copy=True)
        if array.shape != (6, 6):
            raise ValueError("covariance matrix must have shape (6, 6)")
        if not np.all(np.isfinite(array)):
            raise ValueError("covariance matrix must contain only finite values")
        if not np.allclose(array, array.T, rtol=0.0, atol=self.symmetry_tolerance):
            raise ValueError("covariance matrix must be symmetric")
        # Symmetrising only removes numerical round-off already accepted above.
        array = (array + array.T) / 2.0
        minimum_eigenvalue = float(np.linalg.eigvalsh(array).min())
        if minimum_eigenvalue < -self.psd_tolerance:
            raise ValueError("covariance matrix must be positive semi-definite")
        if not self.reference_frame:
            raise ValueError("reference_frame is required")
        if not self.source:
            raise ValueError("source is required")
        if self.state_order != STATE_ORDER:
            raise ValueError(f"state_order must be {STATE_ORDER}")
        if self.estimated and self.authoritative:
            raise ValueError("estimated covariance cannot be authoritative")
        if self.propagation_direction not in (None, "forward", "backward", "same_epoch"):
            raise ValueError("invalid propagation direction")
        if self.propagation_duration_seconds is not None and not np.isfinite(self.propagation_duration_seconds):
            raise ValueError("propagation duration must be finite")
        _utc_time(self.epoch, "epoch")
        array.setflags(write=False)
        object.__setattr__(self, "matrix", array)

    @property
    def position(self) -> np.ndarray:
        """3x3 position covariance in km²."""
        return self.matrix[:3, :3].copy()

    @property
    def velocity(self) -> np.ndarray:
        """3x3 velocity covariance in (km/s)²."""
        return self.matrix[3:, 3:].copy()

    @property
    def position_velocity(self) -> np.ndarray:
        """3x3 position/velocity cross-covariance in km²/s."""
        return self.matrix[:3, 3:].copy()

    @property
    def standard_deviations(self) -> np.ndarray:
        """One-sigma values in state-vector order."""
        return np.sqrt(np.maximum(np.diag(self.matrix), 0.0))

    @property
    def position_covariance_km2(self) -> np.ndarray:
        return self.position

    @property
    def velocity_covariance_km2_s2(self) -> np.ndarray:
        return self.velocity

    @property
    def position_velocity_cross_covariance_km2_s(self) -> np.ndarray:
        return self.position_velocity
