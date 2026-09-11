"""Adapters from the upstream conjunction/uncertainty contracts into Person 5.

This module is deliberately an adapter boundary: Person 5 owns severity,
confidence, trend, alerts, and actions, while conjunction and uncertainty own
their scientific calculations and quality contracts.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .engine import assess_risk
from .models import PcStatus, RiskAssessment, RiskInput

if TYPE_CHECKING:
    from conjunction.models import ConjunctionResult
    from uncertainty.assessment import UncertaintyAssessment


def risk_input_from_upstream(
    conjunction: "ConjunctionResult",
    uncertainty: "UncertaintyAssessment | None" = None,
    *,
    previous: RiskInput | None = None,
) -> RiskInput:
    """Map the real upstream contracts into the normalized Person 5 input.

    No Pc is invented here. The current upstream uncertainty contract explicitly
    reports ``pc_authoritative=False``, and the repository does not yet expose a
    recognized Pc calculator, so Person 5 receives Pc as unavailable.
    """
    provenance: dict[str, Any] = {
        "reference_frame": conjunction.reference_frame,
        "conjunction_status": conjunction.status,
        "tca_quality": {
            "sample_count": conjunction.tca_quality.sample_count,
            "residual_km2_s": conjunction.tca_quality.residual_km2_s,
            "converged": conjunction.tca_quality.converged,
            "boundary_minimum": conjunction.tca_quality.boundary_minimum,
            "bracket_start": conjunction.tca_quality.bracket_start.isoformat(),
            "bracket_end": conjunction.tca_quality.bracket_end.isoformat(),
        },
    }

    covariance_status = "UNAVAILABLE"
    historical_validation = "UNKNOWN"
    propagation_quality = "VALIDATED" if conjunction.tca_quality.converged else "NOT_CONVERGED"
    source: str | None = None
    epoch_utc: str | None = None
    update_time_utc: str | None = None
    epoch_age_hours: float | None = None

    if uncertainty is not None:
        covariance_status = uncertainty.covariance_status.value
        provenance.update(
            {
                "uncertainty_status": uncertainty.covariance_status.value,
                "uncertainty_reason": uncertainty.quality.reason,
                "uncertainty_warnings": list(uncertainty.quality.warnings),
                "pc_authoritative": uncertainty.pc_authoritative,
                "source_a": uncertainty.provenance.source_a,
                "source_b": uncertainty.provenance.source_b,
                "covariance_epoch_a": (
                    uncertainty.provenance.covariance_epoch_a.isoformat()
                    if uncertainty.provenance.covariance_epoch_a is not None
                    else None
                ),
                "covariance_epoch_b": (
                    uncertainty.provenance.covariance_epoch_b.isoformat()
                    if uncertainty.provenance.covariance_epoch_b is not None
                    else None
                ),
                "evaluation_time": uncertainty.provenance.evaluation_time.isoformat(),
            }
        )

        sources = [s for s in (uncertainty.provenance.source_a, uncertainty.provenance.source_b) if s]
        if sources:
            source = sources[0] if len(set(sources)) == 1 else "; ".join(dict.fromkeys(sources))

        epochs = [
            e
            for e in (
                uncertainty.provenance.covariance_epoch_a,
                uncertainty.provenance.covariance_epoch_b,
            )
            if e is not None
        ]
        if len(epochs) == 2 and epochs[0] == epochs[1] == conjunction.tca:
            epoch_utc = epochs[0].isoformat()
            epoch_age_hours = 0.0

        update_time_utc = uncertainty.provenance.evaluation_time.isoformat()

    provenance["source"] = source
    provenance["epoch_utc"] = epoch_utc
    provenance["update_time_utc"] = update_time_utc

    return RiskInput(
        object_a=conjunction.object_a_id,
        object_b=conjunction.object_b_id,
        miss_distance_km=conjunction.miss_distance_km,
        tca_utc=conjunction.tca.isoformat(),
        relative_velocity_km_s=conjunction.relative_speed_km_s,
        pc=None,
        pc_status=PcStatus.UNAVAILABLE,
        source=source,
        epoch_utc=epoch_utc,
        update_time_utc=update_time_utc,
        covariance_status=covariance_status,
        historical_validation=historical_validation,
        propagation_quality=propagation_quality,
        epoch_age_hours=epoch_age_hours,
        provenance=provenance,
        previous=previous,
    )


def assess_upstream_risk(
    conjunction: "ConjunctionResult",
    uncertainty: "UncertaintyAssessment | None" = None,
    *,
    previous: RiskInput | None = None,
) -> RiskAssessment:
    """Run Person 5 risk/actionability directly on upstream outputs."""
    return assess_risk(risk_input_from_upstream(conjunction, uncertainty, previous=previous))
