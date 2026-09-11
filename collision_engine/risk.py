"""Transparent demonstration risk thresholds for conjunction events."""

from __future__ import annotations

from math import isfinite

HIGH_MISS_DISTANCE_KM = 1.0
"""Initial project threshold: a miss distance at or below this is HIGH risk."""

MEDIUM_MISS_DISTANCE_KM = 10.0
"""Initial project threshold: a miss distance at or below this is MEDIUM risk."""


def classify_risk(
    miss_distance_km: float,
    *,
    high_threshold_km: float = HIGH_MISS_DISTANCE_KM,
    medium_threshold_km: float = MEDIUM_MISS_DISTANCE_KM,
) -> str:
    """Classify sampled miss distance using configurable project thresholds.

    These are demonstration/engineering thresholds, not operational or ISRO
    collision-avoidance thresholds.
    """
    values = (miss_distance_km, high_threshold_km, medium_threshold_km)
    if any(not isinstance(value, (int, float)) or isinstance(value, bool) or not isfinite(value) for value in values):
        raise ValueError("risk distances and thresholds must be finite numeric values")
    if miss_distance_km < 0 or high_threshold_km < 0 or medium_threshold_km < 0:
        raise ValueError("risk distances and thresholds cannot be negative")
    if high_threshold_km > medium_threshold_km:
        raise ValueError("high_threshold_km cannot exceed medium_threshold_km")
    if miss_distance_km <= high_threshold_km:
        return "HIGH"
    if miss_distance_km <= medium_threshold_km:
        return "MEDIUM"
    return "LOW"


def explain_risk(risk_level: str, miss_distance_km: float, relative_velocity_km_s: float) -> str:
    """Return a compact, human-readable explanation of the classification."""
    return (
        f"{risk_level} because miss distance = {miss_distance_km:.3f} km "
        f"and relative velocity = {relative_velocity_km_s:.3f} km/s"
    )
