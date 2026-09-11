"""Validated metadata contract for covariance between two object states."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
import numpy as np

from .covariance import STATE_ORDER


@dataclass(frozen=True)
class CrossCovariance:
    """``P_AB = Cov(state_A, state_B)`` in the declared shared frame and epoch."""
    matrix: object
    reference_frame: str
    epoch: datetime
    source: str
    state_order: tuple[str, ...] = STATE_ORDER

    def __post_init__(self) -> None:
        matrix = np.array(self.matrix, dtype=float, copy=True)
        if matrix.shape != (6, 6): raise ValueError("cross covariance P_AB must have shape (6, 6)")
        if not np.all(np.isfinite(matrix)): raise ValueError("cross covariance P_AB must contain only finite values")
        if not self.reference_frame or not self.source: raise ValueError("cross covariance frame and source are required")
        if self.epoch.tzinfo is None or self.epoch.utcoffset() is None: raise ValueError("cross covariance epoch must be timezone-aware")
        if self.state_order != STATE_ORDER: raise ValueError(f"state_order must be {STATE_ORDER}")
        matrix.setflags(write=False)
        object.__setattr__(self, "matrix", matrix)
