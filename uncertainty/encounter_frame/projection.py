"""Covariance projection onto axes supplied by conjunction.encounter_plane."""
from __future__ import annotations
import numpy as np


def project_position_covariance(position_covariance: object, plane_x: object, plane_y: object) -> tuple[np.ndarray, np.ndarray]:
    """Return ``(P_encounter, H)`` for externally supplied 3-D plane axes.

    This module intentionally creates no encounter-frame convention of its own.
    ``plane_x`` and ``plane_y`` must be the existing conjunction geometry axes.
    """
    covariance = np.asarray(position_covariance, dtype=float)
    projection = np.asarray((plane_x, plane_y), dtype=float)
    if covariance.shape != (3, 3) or not np.all(np.isfinite(covariance)):
        raise ValueError("position covariance must be a finite 3x3 matrix")
    if projection.shape != (2, 3) or not np.all(np.isfinite(projection)):
        raise ValueError("encounter-plane projection axes must form a finite 2x3 matrix")
    if not np.allclose(covariance, covariance.T, rtol=0.0, atol=1e-10):
        raise ValueError("position covariance must be symmetric")
    if not np.allclose(projection @ projection.T, np.eye(2), rtol=0.0, atol=1e-10):
        raise ValueError("encounter-plane axes must be orthonormal")
    return projection @ covariance @ projection.T, projection
