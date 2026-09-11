"""End-to-end Orbit -> Collision -> ML risk analysis."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from collision_engine import OrbitalState, find_closest_approach
from orbit_engine import propagate_tle

from .features import build_features
from .predict import predict_features


def analyze_tle_pair(*, object_a_name: str, object_a_line1: str, object_a_line2: str, object_b_name: str, object_b_line1: str, object_b_line2: str, timestamps: list[datetime]) -> dict[str, object]:
    """Collect both orbit series in parallel, then derive collision and ML output.

    Collision detection necessarily follows propagation because it consumes the
    two propagated state series.  The returned payload preserves both sources
    so the caller can display or store orbit and collision data together.
    """
    if not timestamps:
        raise ValueError("timestamps cannot be empty")
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_a = executor.submit(
            propagate_tle, object_a_name, object_a_line1, object_a_line2, timestamps
        )
        future_b = executor.submit(
            propagate_tle, object_b_name, object_b_line1, object_b_line2, timestamps
        )
        propagated_a = future_a.result()
        propagated_b = future_b.result()
    states_a = [OrbitalState.from_propagation_result(result) for result in propagated_a]
    states_b = [OrbitalState.from_propagation_result(result) for result in propagated_b]
    event = find_closest_approach(states_a, states_b)
    features = build_features(event, states_a, states_b, analysis_time=timestamps[0])
    return {
        "orbit_engine": {
            "object_a_states": [result.to_dict() for result in propagated_a],
            "object_b_states": [result.to_dict() for result in propagated_b],
        },
        "collision_engine": event.to_dict(),
        "ml_features": features,
        "ml_prediction": predict_features(features),
    }
