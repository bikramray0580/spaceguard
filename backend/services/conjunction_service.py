"""End-to-end nominal conjunction -> uncertainty -> risk handoff."""
from __future__ import annotations
from datetime import datetime
from itertools import combinations
from math import ceil
from conjunction.engine import calculate_conjunction
from conjunction.screening import ScreeningResult, broad_screen
from risk.upstream_adapter import assess_upstream_risk
from ..config import DEFAULT_DISTANCE_THRESHOLD_KM, DEFAULT_MAX_SCREEN_OBJECTS
from .data_service import list_objects
from .orbit_service import ConjunctionPropagator
def screen_conjunction(
    object_a: str,
    object_b: str,
    start: datetime,
    end: datetime,
    step_minutes: float = 5.0,
):
    objects = {obj.object_id: obj for obj in list_objects()}
    if object_a not in objects or object_b not in objects:
        raise KeyError("one or both objects were not found")
    if object_a == object_b:
        raise ValueError("object_a and object_b must be different")
    if end <= start:
        raise ValueError("end must be later than start")
    if step_minutes <= 0 or step_minutes > 60:
        raise ValueError("step_minutes must be greater than 0 and no more than 60 minutes")
    propagator = ConjunctionPropagator(objects)
    # Convert the requested screening interval into a bounded sampling density.
    # The conjunction engine still performs its own TCA refinement after this scan.
    result = calculate_conjunction(
        propagator,
        object_a,
        object_b,
        start,
        end,
        samples=_sample_count(start, end, step_minutes),
    )
    assessment = assess_upstream_risk(result, None)
    return result, assessment
def _sample_count(start: datetime, end: datetime, step_minutes: float) -> int:
    return max(3, ceil((end - start).total_seconds() / (step_minutes * 60.0)) + 1)
def assess_candidates(
    propagator: ConjunctionPropagator,
    candidates,
    start: datetime,
    end: datetime,
    step_minutes: float = 5.0,
):
    """Run existing pairwise detailed assessment for each screening candidate."""
    samples = _sample_count(start, end, step_minutes)
    assessed = []
    for candidate in candidates:
        result = calculate_conjunction(
            propagator,
            candidate.object_a_id,
            candidate.object_b_id,
            start,
            end,
            samples=samples,
        )
        assessed.append((result, assess_upstream_risk(result, None)))
    return tuple(assessed)
def screen_catalogue(
    start: datetime,
    end: datetime,
    object_ids: list[str] | None = None,
    step_minutes: float = 5.0,
    distance_threshold_km: float = DEFAULT_DISTANCE_THRESHOLD_KM,
    max_objects: int = DEFAULT_MAX_SCREEN_OBJECTS,
) -> tuple[tuple[str, ...], int, int, ScreeningResult, tuple]:
    """Run broad_screen() then detailed conjunction/risk for each candidate.
    The existing pairwise screen_conjunction() path is unchanged.
    """
    if end <= start:
        raise ValueError("end must be later than start")
    if step_minutes <= 0 or step_minutes > 60:
        raise ValueError("step_minutes must be greater than 0 and no more than 60 minutes")
    if distance_threshold_km < 0:
        raise ValueError("distance_threshold_km must be non-negative")
    if max_objects < 2:
        raise ValueError("max_objects must be at least 2")
    catalogue = {obj.object_id: obj for obj in list_objects()}
    catalogue_count = len(catalogue)
    if object_ids is None:
        selected_ids = tuple(list(catalogue.keys())[:max_objects])
    else:
        requested = tuple(dict.fromkeys(object_ids))
        missing = [object_id for object_id in requested if object_id not in catalogue]
        if missing:
            raise KeyError(f"objects were not found: {', '.join(missing)}")
        if len(requested) > max_objects:
            raise ValueError(f"at most {max_objects} objects can be screened at once")
        selected_ids = requested
    if len(selected_ids) < 2:
        raise ValueError("at least two objects are required for catalogue screening")
    propagator = ConjunctionPropagator({object_id: catalogue[object_id] for object_id in selected_ids})
    result = broad_screen(
        propagator,
        selected_ids,
        start,
        end,
        sampling_interval_seconds=step_minutes * 60.0,
        distance_threshold_km=distance_threshold_km,
    )
    assessments = assess_candidates(propagator, result.candidates, start, end, step_minutes)
    pair_count = sum(1 for _ in combinations(selected_ids, 2))
    return selected_ids, catalogue_count, pair_count, result, assessments