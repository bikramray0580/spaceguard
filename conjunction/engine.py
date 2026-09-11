"""Orchestrator for covariance-free nominal conjunction assessment."""
from __future__ import annotations
from datetime import datetime
from math import isfinite
from typing import Protocol
from .encounter_plane import calculate_encounter_geometry
from .miss_distance import calculate_miss_distance
from .models import ConjunctionResult, StateVector
from .relative_velocity import calculate_relative_velocity
from .tca import find_tca
from .validation import validate_assessment_input, validate_result, validate_state_pair

class PropagationError(RuntimeError):
    """Raised when a propagator cannot produce a valid requested state."""
class NumericalOptimizationError(RuntimeError):
    """Raised when the numerical objective is non-finite."""
class StatePropagator(Protocol):
    def state_at(self, object_id: str, when: datetime) -> StateVector: ...

class ConjunctionEngine:
    """Validate → TCA → nominal geometry → validated result; no covariance/Pc."""
    def __init__(self, propagator: StatePropagator, *, samples: int = 121, tolerance_seconds: float = 1e-5) -> None:
        if samples < 3: raise ValueError("samples must be at least 3")
        if tolerance_seconds <= 0: raise ValueError("tolerance_seconds must be positive")
        self.propagator, self.samples, self.tolerance_seconds = propagator, samples, tolerance_seconds

    def assess(self, object_a_id: str, object_b_id: str, start: datetime, end: datetime) -> ConjunctionResult:
        validate_assessment_input(object_a_id, object_b_id, start, end)
        def states(when: datetime) -> tuple[StateVector, StateVector]: return self._states(object_a_id, object_b_id, when)
        def objective(when: datetime) -> float:
            a, b = states(when); distance = calculate_miss_distance(a.position_km, b.position_km).distance_km
            value = distance * distance
            if not isfinite(value): raise NumericalOptimizationError("squared separation is not finite")
            return value
        def residual(when: datetime) -> float:
            a, b = states(when); miss = calculate_miss_distance(a.position_km, b.position_km)
            velocity = calculate_relative_velocity(a.position_km, a.velocity_km_s, b.position_km, b.velocity_km_s)
            return sum(x*y for x, y in zip(miss.vector_km, velocity.vector_km_s))
        search = find_tca(objective, residual, start, end, samples=self.samples, tolerance_seconds=self.tolerance_seconds)
        a, b = states(search.tca); miss = calculate_miss_distance(a.position_km, b.position_km)
        velocity = calculate_relative_velocity(a.position_km, a.velocity_km_s, b.position_km, b.velocity_km_s)
        geometry = calculate_encounter_geometry(miss.vector_km, velocity.vector_km_s)
        result = ConjunctionResult(object_a_id, object_b_id, search.tca, miss.relative_position_km, velocity.vector_km_s,
            miss.vector_km, miss.distance_km, velocity.speed_km_s, velocity.closing_rate_km_s,
            geometry.relative_motion_direction, miss.direction, a.reference_frame, search.quality,
            "boundary_minimum" if search.quality.boundary_minimum else "success")
        validate_result(result); return result

    def _states(self, a_id: str, b_id: str, when: datetime) -> tuple[StateVector, StateVector]:
        try: a, b = self.propagator.state_at(a_id, when), self.propagator.state_at(b_id, when)
        except Exception as exc: raise PropagationError(f"state propagation failed at {when.isoformat()}") from exc
        if a.object_id != a_id or b.object_id != b_id or a.epoch != when or b.epoch != when:
            raise PropagationError("propagator returned a state with an unexpected object or epoch")
        validate_state_pair(a, b, a_id, b_id, when)
        return a, b

def calculate_conjunction(propagator: StatePropagator, object_a_id: str, object_b_id: str, start: datetime, end: datetime, **settings: object) -> ConjunctionResult:
    """Convenience public API for one nominal conjunction assessment."""
    return ConjunctionEngine(propagator, **settings).assess(object_a_id, object_b_id, start, end)
