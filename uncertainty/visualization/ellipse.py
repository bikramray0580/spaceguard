"""Encounter-plane uncertainty ellipse parameters, not collision probability."""
from __future__ import annotations
from dataclasses import dataclass
from math import atan2, log, sqrt
import numpy as np

@dataclass(frozen=True)
class UncertaintyEllipse:
    confidence_level: float
    semi_major_axis_km: float
    semi_minor_axis_km: float
    orientation_rad: float
    nominal_point_km: tuple[float, float] | None = None

def covariance_ellipse(covariance: object, *, confidence_level: float = 0.95,
                       nominal_point_km: tuple[float, float] | None = None) -> UncertaintyEllipse:
    """Return a 2-D Gaussian confidence ellipse from an encounter covariance."""
    matrix = np.asarray(covariance, dtype=float)
    if matrix.shape != (2, 2) or not np.all(np.isfinite(matrix)): raise ValueError("encounter covariance must be finite 2x2")
    if not np.allclose(matrix, matrix.T, rtol=0.0, atol=1e-10): raise ValueError("encounter covariance must be symmetric")
    if not 0.0 < confidence_level < 1.0: raise ValueError("confidence_level must be between 0 and 1")
    values, vectors = np.linalg.eigh(matrix)
    if values[0] < -1e-10: raise ValueError("encounter covariance must be positive semi-definite")
    values = np.maximum(values, 0.0)
    scale = -2.0 * log(1.0 - confidence_level)  # chi-square quantile, 2 DoF
    major_vector = vectors[:, 1]
    return UncertaintyEllipse(confidence_level, sqrt(scale * values[1]), sqrt(scale * values[0]),
                              atan2(float(major_vector[1]), float(major_vector[0])), nominal_point_km)
