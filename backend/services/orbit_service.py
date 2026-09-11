"""Bridge the API object model to the main SGP4 propagator."""
from __future__ import annotations
from datetime import datetime

from orbit_propagation.sgp4.propagator import SGP4Propagator

from ..models.object import SpaceObject

_PROPAGATOR = SGP4Propagator()


def create_time_grid(start: datetime, end: datetime, step_minutes: float) -> list[datetime]:
    if end <= start:
        raise ValueError("end must be later than start")
    step_seconds = step_minutes * 60
    current = start
    result: list[datetime] = []
    while current <= end:
        result.append(current)
        current = current.fromtimestamp(current.timestamp() + step_seconds, tz=current.tzinfo)
    return result


def propagate_object(obj: SpaceObject, timestamps: list[datetime]) -> list[dict]:
    states = []
    for timestamp in timestamps:
        state = _PROPAGATOR.propagate(obj.line1, obj.line2, timestamp)
        states.append({
            "object_id": obj.object_id,
            "object_name": obj.name,
            "timestamp": state.timestamp,
            "position": {"x_km": state.position[0], "y_km": state.position[1], "z_km": state.position[2]},
            "velocity": {"x_km_s": state.velocity[0], "y_km_s": state.velocity[1], "z_km_s": state.velocity[2]},
            "coordinate_frame": state.frame,
            "position_units": state.position_units,
            "velocity_units": state.velocity_units,
        })
    return states


class ConjunctionPropagator:
    """Adapter implementing conjunction.StatePropagator from SGP4."""
    def __init__(self, objects: dict[str, SpaceObject]):
        self.objects = objects

    def state_at(self, object_id: str, when: datetime):
        from conjunction.models import StateVector
        obj = self.objects[object_id]
        state = _PROPAGATOR.propagate(obj.line1, obj.line2, when)
        return StateVector(object_id, state.timestamp, state.position, state.velocity, state.frame)
