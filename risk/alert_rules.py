"""Alert rules and action selection for the SpaceGuard risk layer."""

from .models import Confidence, RecommendedAction, RiskInput, RiskLevel, Trend
from .decision_tables import RiskThresholds


def confidence_for(event: RiskInput) -> tuple[Confidence, tuple[str, ...]]:
    reasons: list[str] = []
    score = 0

    covariance = event.covariance_status.upper()
    validation = event.historical_validation.upper()
    propagation = event.propagation_quality.upper()

    if covariance in {"AUTHORITATIVE", "VALIDATED"}:
        score += 2
        reasons.append("authoritative/validated covariance is available")
    elif covariance in {"ESTIMATED", "PARTIAL"}:
        score += 1
        reasons.append("covariance is present but not fully authoritative")
    else:
        reasons.append("authoritative covariance is unavailable")

    if validation in {"VALIDATED", "GOOD", "PASS", "PASSED"}:
        score += 2
        reasons.append("historical prediction validation is positive")
    elif validation in {"PARTIAL", "LIMITED"}:
        score += 1
        reasons.append("historical validation is limited")
    else:
        reasons.append("historical validation is unavailable or unknown")

    if propagation in {"VALIDATED", "GOOD", "PASS", "PASSED"}:
        score += 1
        reasons.append("propagation quality is positive")
    elif propagation not in {"UNKNOWN", ""}:
        reasons.append("propagation quality is not fully validated")

    if event.epoch_age_hours is not None:
        if event.epoch_age_hours <= 24:
            score += 1
            reasons.append("source epoch is recent")
        elif event.epoch_age_hours > 72:
            reasons.append("source epoch is stale")

    confidence = Confidence.HIGH if score >= 5 else Confidence.MEDIUM if score >= 3 else Confidence.LOW
    return confidence, tuple(reasons)


def evaluate_alert(
    event: RiskInput,
    risk_level: RiskLevel,
    confidence: Confidence,
    trend: Trend,
    thresholds: RiskThresholds,
) -> tuple[bool, str | None, int, RecommendedAction]:
    """Return alert flag, alert type, priority (1 highest), and next action."""
    if risk_level == RiskLevel.HIGH:
        return True, "HIGH_RISK", 1, RecommendedAction.PRIORITIZE_REVIEW

    if risk_level == RiskLevel.MEDIUM and trend == Trend.WORSENING:
        return True, "WORSENING_RISK", 2, RecommendedAction.REASSESS

    if risk_level == RiskLevel.MEDIUM:
        return True, "MEDIUM_RISK", 3, RecommendedAction.REASSESS

    if trend == Trend.WORSENING:
        return True, "WORSENING_TREND", 3, RecommendedAction.REASSESS

    if confidence == Confidence.LOW and event.miss_distance_km <= thresholds.medium_miss_distance_km:
        return True, "LOW_CONFIDENCE_CLOSE_APPROACH", 3, RecommendedAction.REASSESS

    return False, None, 4, RecommendedAction.MONITOR
