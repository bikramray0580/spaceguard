"""Feature extraction at the boundary between the orbit and collision engines."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from math import sqrt

from collision_engine import ConjunctionEvent, OrbitalState

EARTH_MEAN_RADIUS_KM = 6371.0
FEATURES = (
    "miss_distance_km", "relative_velocity_km_s", "time_to_tca_hours",
    "object_a_altitude_km", "object_b_altitude_km", "altitude_difference_km",
)


def _altitude_km(state: OrbitalState) -> float:
    position = state.position_km
    return sqrt(position.x**2 + position.y**2 + position.z**2) - EARTH_MEAN_RADIUS_KM


def _state_at_tca(states: Sequence[OrbitalState], event: ConjunctionEvent) -> OrbitalState:
    for state in states:
        if state.timestamp == event.time_of_closest_approach:
            return state
    raise ValueError("state series does not contain the event time of closest approach")


def build_features(event: ConjunctionEvent, states_a: Sequence[OrbitalState], states_b: Sequence[OrbitalState], *, analysis_time: datetime) -> dict[str, float]:
    """Build ML input only from orbit- and collision-engine outputs."""
    if not states_a or not states_b:
        raise ValueError("state series cannot be empty")
    if analysis_time.tzinfo is None or analysis_time.utcoffset() is None:
        raise ValueError("analysis_time must be timezone-aware")
    if event.object_a != states_a[0].object_id or event.object_b != states_b[0].object_id:
        raise ValueError("state series object IDs must match the conjunction event")
    altitude_a = _altitude_km(_state_at_tca(states_a, event))
    altitude_b = _altitude_km(_state_at_tca(states_b, event))
    return {
        "miss_distance_km": event.miss_distance_km,
        "relative_velocity_km_s": event.relative_velocity_km_s,
        "time_to_tca_hours": (event.time_of_closest_approach - analysis_time).total_seconds() / 3600,
        "object_a_altitude_km": altitude_a,
        "object_b_altitude_km": altitude_b,
        "altitude_difference_km": abs(altitude_a - altitude_b),
    }
