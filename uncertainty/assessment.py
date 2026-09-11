"""Integration layer from a nominal ConjunctionResult to uncertainty outputs."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
import numpy as np

from conjunction.encounter_plane import calculate_encounter_geometry
from conjunction.models import ConjunctionResult

from .covariance import Covariance
from .cross_covariance import CrossCovariance
from .encounter_frame import project_position_covariance
from .quality_flags import UncertaintyQuality, UncertaintyStatus
from .relative_covariance import relative_covariance
from .visualization import UncertaintyEllipse, covariance_ellipse


@dataclass(frozen=True)
class UncertaintyProvenance:
    source_a: str | None
    source_b: str | None
    covariance_epoch_a: datetime | None
    covariance_epoch_b: datetime | None
    evaluation_time: datetime
    reference_frame: str


@dataclass(frozen=True)
class UncertaintyAssessment:
    """Covariance-derived companion to a nominal conjunction result.

    ``pc_authoritative`` is always false: this module supplies compatible input
    to a future Pc calculator but does not calculate Pc itself.
    """
    conjunction: ConjunctionResult
    quality: UncertaintyQuality
    provenance: UncertaintyProvenance
    relative_covariance_6x6: np.ndarray | None = None
    encounter_position_covariance_km2: np.ndarray | None = None
    projection_matrix: np.ndarray | None = None
    ellipse: UncertaintyEllipse | None = None
    validation_message: str = ""
    pc_authoritative: bool = False

    @property
    def covariance_status(self) -> UncertaintyStatus:
        return self.quality.status

    @property
    def collision_probability_covariance_km2(self) -> tuple[tuple[float, float], tuple[float, float]] | None:
        """2x2 matrix ready for CollisionProbabilityInput when one is implemented."""
        if self.encounter_position_covariance_km2 is None: return None
        return tuple(tuple(float(x) for x in row) for row in self.encounter_position_covariance_km2)  # type: ignore[return-value]

    @property
    def relative_position_covariance_km2(self) -> np.ndarray | None:
        if self.relative_covariance_6x6 is None: return None
        return self.relative_covariance_6x6[:3, :3].copy()

    def to_collision_probability_input(self):
        """Build the existing structural Pc-input contract; does not calculate Pc."""
        from conjunction.collision_probability import CollisionProbabilityInput
        covariance = self.collision_probability_covariance_km2
        if covariance is None:
            raise ValueError("cannot create collision-probability input without encounter covariance")
        return CollisionProbabilityInput(self.conjunction, covariance)


def _provenance(result: ConjunctionResult, a: Covariance | None, b: Covariance | None) -> UncertaintyProvenance:
    return UncertaintyProvenance(a.source if a else None, b.source if b else None,
                                 a.epoch if a else None, b.epoch if b else None,
                                 result.tca, result.reference_frame)


def _failure(result: ConjunctionResult, status: UncertaintyStatus, reason: str,
             a: Covariance | None, b: Covariance | None) -> UncertaintyAssessment:
    return UncertaintyAssessment(result, UncertaintyQuality(status, reason), _provenance(result, a, b), validation_message=reason)


def assess_uncertainty(conjunction: ConjunctionResult, covariance_a: Covariance | None,
                       covariance_b: Covariance | None, *, cross_covariance_ab: CrossCovariance | None = None,
                       confidence_level: float = 0.95) -> UncertaintyAssessment:
    """Project compatible TCA covariances into conjunction's existing plane.

    Both covariances must already be represented at ``conjunction.tca``. Use
    :func:`propagate_covariance` first when epochs differ; no conversion or
    propagation is silently performed here.
    """
    if covariance_a is None or covariance_b is None:
        return _failure(conjunction, UncertaintyStatus.UNAVAILABLE,
                        "Pc not authoritative / unavailable because covariance is unavailable.", covariance_a, covariance_b)
    if covariance_a.reference_frame != conjunction.reference_frame or covariance_b.reference_frame != conjunction.reference_frame:
        return _failure(conjunction, UncertaintyStatus.INVALID,
                        "covariance frame is incompatible with conjunction reference frame; no conversion was performed.", covariance_a, covariance_b)
    if covariance_a.epoch != conjunction.tca or covariance_b.epoch != conjunction.tca:
        return _failure(conjunction, UncertaintyStatus.INVALID,
                        "covariance epoch does not equal TCA; propagate covariance explicitly before assessment.", covariance_a, covariance_b)
    try:
        relative = relative_covariance(covariance_a, covariance_b, cross_covariance_ab)
        # Revalidate the derived matrix, including PSD. Its provenance is carried by assessment.
        Covariance(relative, conjunction.tca, conjunction.reference_frame, "relative covariance")
        geometry = calculate_encounter_geometry(conjunction.relative_position_km, conjunction.relative_velocity_km_s)
        if geometry.plane_x is None or geometry.plane_y is None:
            return _failure(conjunction, UncertaintyStatus.INVALID,
                            "encounter-plane projection is unavailable for zero relative velocity.", covariance_a, covariance_b)
        encounter, projection = project_position_covariance(relative[:3, :3], geometry.plane_x, geometry.plane_y)
        # Ellipse validates 2-D symmetry/PSD as well as creating visualization parameters.
        nominal = geometry.nominal_coordinates_km
        ellipse = covariance_ellipse(encounter, confidence_level=confidence_level, nominal_point_km=nominal)
    except (ValueError, np.linalg.LinAlgError) as exc:
        return _failure(conjunction, UncertaintyStatus.INVALID, f"covariance assessment failed: {exc}", covariance_a, covariance_b)
    trusted = covariance_a.authoritative and covariance_b.authoritative
    status = UncertaintyStatus.AVAILABLE if trusted and not (covariance_a.estimated or covariance_b.estimated) else UncertaintyStatus.ESTIMATED
    reason = "authoritative covariance available" if status is UncertaintyStatus.AVAILABLE else "usable covariance is estimated or not explicitly authoritative"
    warnings: tuple[str, ...] = ()
    if geometry.degenerate:
        warnings = ("encounter-plane transverse orientation is convention-dependent for this degenerate geometry",)
        reason = f"{reason}; {warnings[0]}"
    relative = np.array(relative, copy=True); relative.setflags(write=False)
    encounter = np.array(encounter, copy=True); encounter.setflags(write=False)
    projection = np.array(projection, copy=True); projection.setflags(write=False)
    return UncertaintyAssessment(conjunction, UncertaintyQuality(status, reason, warnings), _provenance(conjunction, covariance_a, covariance_b),
                                 relative, encounter, projection, ellipse, "validated and projected at TCA")
