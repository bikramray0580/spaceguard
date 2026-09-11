"""End-to-end nominal conjunction -> uncertainty -> risk handoff."""
from __future__ import annotations
from datetime import datetime

from conjunction.engine import calculate_conjunction
from risk import assess_upstream_risk

from .data_service import find_object, list_objects
from .orbit_service import ConjunctionPropagator


def screen_conjunction(object_a: str, object_b: str, start: datetime, end: datetime):
    objects = {obj.object_id: obj for obj in list_objects()}
    if object_a not in objects or object_b not in objects:
        raise KeyError("one or both objects were not found")
    if object_a == object_b:
        raise ValueError("object_a and object_b must be different")

    propagator = ConjunctionPropagator(objects)
    result = calculate_conjunction(propagator, object_a, object_b, start, end)
    assessment = assess_upstream_risk(result, None)
    return result, assessment
