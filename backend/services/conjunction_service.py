"""End-to-end nominal conjunction -> uncertainty -> risk handoff."""
from __future__ import annotations
from datetime import datetime

from conjunction.engine import calculate_conjunction
from risk.upstream_adapter import assess_upstream_risk

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
    from math import ceil
    samples = max(3, ceil((end - start).total_seconds() / (step_minutes * 60.0)) + 1)
    result = calculate_conjunction(
        propagator,
        object_a,
        object_b,
        start,
        end,
        samples=samples,
    )
    assessment = assess_upstream_risk(result, None)
    return result, assessment
