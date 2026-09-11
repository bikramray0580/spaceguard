"""Orbit propagation service wrapping orbit_engine."""

from datetime import datetime

from orbit_engine import generate_time_steps, propagate_tle

from ..models.object import SpaceObject
from ..models.orbit import OrbitResult


def create_time_grid(
    start: datetime, end: datetime, step_minutes: float
) -> list[datetime]:
    """Generate one shared, inclusive UTC time grid."""
    return generate_time_steps(start, end, step_minutes)


def propagate_object(obj: SpaceObject, timestamps: list[datetime]) -> OrbitResult:
    """Propagate one object over the shared time grid using orbit_engine."""
    results = propagate_tle(obj.name, obj.line1, obj.line2, timestamps)
    states = []
    for result in results:
        state = result.to_dict()
        state["object_id"] = obj.object_id
        state["object_name"] = obj.name
        states.append(state)
    return OrbitResult(object_id=obj.object_id, object_name=obj.name, states=states)
