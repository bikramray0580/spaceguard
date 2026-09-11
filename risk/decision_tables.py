"""Configurable prototype decision table for risk severity."""

from dataclasses import dataclass

from .models import PcStatus, RiskInput, RiskLevel


@dataclass(frozen=True)
class RiskThresholds:
    """Prototype thresholds; not operational collision-avoidance limits."""

    high_miss_distance_km: float = 1.0
    medium_miss_distance_km: float = 5.0
    high_pc: float = 1e-4
    medium_pc: float = 1e-6
    high_tca_hours: float = 24.0
    medium_tca_hours: float = 72.0


def classify_severity(event: RiskInput, thresholds: RiskThresholds = RiskThresholds()) -> RiskLevel:
    """Classify severity using evidence available in the event.

    Authoritative Pc can strengthen a classification. Distance remains a
    prototype severity signal, not a probability of collision.
    """
    distance_level = (
        RiskLevel.HIGH
        if event.miss_distance_km <= thresholds.high_miss_distance_km
        else RiskLevel.MEDIUM
        if event.miss_distance_km <= thresholds.medium_miss_distance_km
        else RiskLevel.LOW
    )

    if event.pc is not None and event.pc_status == PcStatus.AUTHORITATIVE:
        if event.pc >= thresholds.high_pc:
            return RiskLevel.HIGH
        if event.pc >= thresholds.medium_pc:
            return max_risk(distance_level, RiskLevel.MEDIUM)

    return distance_level


def max_risk(a: RiskLevel, b: RiskLevel) -> RiskLevel:
    order = {RiskLevel.LOW: 0, RiskLevel.MEDIUM: 1, RiskLevel.HIGH: 2}
    return a if order[a] >= order[b] else b
