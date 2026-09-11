"""Public risk assessment entry point."""

from __future__ import annotations

from .alert_rules import confidence_for, evaluate_alert
from .decision_tables import RiskThresholds, classify_severity
from .models import PcStatus, RiskAssessment, RiskInput
from .risk_trend import calculate_trend


def assess_risk(event: RiskInput, thresholds: RiskThresholds | None = None) -> RiskAssessment:
    """Turn a conjunction result into an evidence-backed decision card.

    This layer does not calculate Pc. It only carries Pc supplied by an
    upstream recognized calculation and explicitly preserves its status.
    """
    thresholds = thresholds or RiskThresholds()
    risk_level = classify_severity(event, thresholds)
    trend = calculate_trend(event)
    confidence, confidence_reasons = confidence_for(event)
    alert, alert_type, priority, action = evaluate_alert(
        event, risk_level, confidence, trend, thresholds
    )

    quality_parts = [
        f"covariance={event.covariance_status}",
        f"historical_validation={event.historical_validation}",
        f"propagation={event.propagation_quality}",
    ]
    if event.epoch_age_hours is not None:
        quality_parts.append(f"epoch_age_hours={event.epoch_age_hours:g}")
    quality_status = "; ".join(quality_parts)

    pc = event.pc if event.pc_status == PcStatus.AUTHORITATIVE else None
    pc_status = event.pc_status
    if event.pc is not None and event.pc_status == PcStatus.ESTIMATED:
        confidence_reasons = confidence_reasons + (
            "a non-authoritative Pc estimate was supplied; it is not exposed as authoritative Pc",
        )

    explanation = (
        f"{risk_level.value} risk based on prototype severity rules: "
        f"miss distance={event.miss_distance_km:g} km"
    )
    if event.pc_status == PcStatus.AUTHORITATIVE and event.pc is not None:
        explanation += f", authoritative Pc={event.pc:g}"
    else:
        explanation += ", authoritative Pc unavailable"
    explanation += f"; trend={trend.value.lower()}; confidence={confidence.value.lower()}."

    return RiskAssessment(
        object_a=event.object_a,
        object_b=event.object_b,
        tca_utc=event.tca_utc,
        miss_distance_km=event.miss_distance_km,
        relative_velocity_km_s=event.relative_velocity_km_s,
        risk_level=risk_level,
        priority=priority,
        confidence=confidence,
        confidence_reasons=confidence_reasons,
        trend=trend,
        alert=alert,
        alert_type=alert_type,
        explanation=explanation,
        recommended_action=action,
        pc=pc,
        pc_status=pc_status,
        quality_status=quality_status,
        provenance=dict(event.provenance),
    )
