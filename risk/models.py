"""Data contracts for the SpaceGuard risk and actionability layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Confidence(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Trend(str, Enum):
    IMPROVING = "IMPROVING"
    STABLE = "STABLE"
    WORSENING = "WORSENING"
    UNKNOWN = "UNKNOWN"


class RecommendedAction(str, Enum):
    MONITOR = "MONITOR"
    REASSESS = "REASSESS"
    PRIORITIZE_REVIEW = "PRIORITIZE_REVIEW"


class PcStatus(str, Enum):
    AUTHORITATIVE = "AUTHORITATIVE"
    ESTIMATED = "ESTIMATED"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class RiskInput:
    """Normalized inputs consumed by Person 5.

    Field names intentionally mirror the concepts in the project plan while
    remaining independent of upstream implementations. Upstream modules can
    construct this object directly or map their common event schema into it.
    """

    object_a: str
    object_b: str
    miss_distance_km: float
    tca_utc: str
    relative_velocity_km_s: float | None = None
    pc: float | None = None
    pc_status: PcStatus = PcStatus.UNAVAILABLE
    source: str | None = None
    epoch_utc: str | None = None
    update_time_utc: str | None = None
    covariance_status: str = "UNKNOWN"
    historical_validation: str = "UNKNOWN"
    propagation_quality: str = "UNKNOWN"
    epoch_age_hours: float | None = None
    provenance: Mapping[str, Any] = field(default_factory=dict)
    hard_body_radius_km: float | None = None
    previous: "RiskInput | None" = None

    def __post_init__(self) -> None:
        """Normalize enum inputs so adapters may safely pass wire-format strings."""
        try:
            status = self.pc_status if isinstance(self.pc_status, PcStatus) else PcStatus(self.pc_status)
        except ValueError as exc:
            raise ValueError(f"invalid pc_status: {self.pc_status!r}") from exc
        object.__setattr__(self, "pc_status", status)

        if self.miss_distance_km < 0:
            raise ValueError("miss_distance_km must be non-negative")
        if self.pc is not None and self.pc < 0:
            raise ValueError("pc must be non-negative")
        if self.epoch_age_hours is not None and self.epoch_age_hours < 0:
            raise ValueError("epoch_age_hours must be non-negative")


@dataclass(frozen=True)
class RiskAssessment:
    object_a: str
    object_b: str
    tca_utc: str
    miss_distance_km: float
    relative_velocity_km_s: float | None
    risk_level: RiskLevel
    priority: int
    confidence: Confidence
    confidence_reasons: tuple[str, ...]
    trend: Trend
    alert: bool
    alert_type: str | None
    explanation: str
    recommended_action: RecommendedAction
    pc: float | None
    pc_status: PcStatus
    quality_status: str
    provenance: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly representation for dashboard/integration use."""
        return {
            "object_a": self.object_a,
            "object_b": self.object_b,
            "tca_utc": self.tca_utc,
            "miss_distance_km": self.miss_distance_km,
            "relative_velocity_km_s": self.relative_velocity_km_s,
            "risk_level": self.risk_level.value,
            "priority": self.priority,
            "confidence": self.confidence.value,
            "confidence_reasons": list(self.confidence_reasons),
            "trend": self.trend.value,
            "alert": self.alert,
            "alert_type": self.alert_type,
            "explanation": self.explanation,
            "recommended_action": self.recommended_action.value,
            "pc": self.pc,
            "pc_status": self.pc_status.value,
            "quality_status": self.quality_status,
            "provenance": dict(self.provenance),
        }
