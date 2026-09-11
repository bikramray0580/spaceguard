"""Manual demonstration of deterministic sampled conjunction detection.

Run from the project root with:
    python -m collision_engine.demo_conjunction
"""

from datetime import datetime, timedelta, timezone

from collision_engine import OrbitalState, Vector3, find_closest_approach


START = datetime(2026, 8, 22, 12, 0, tzinfo=timezone.utc)


def make_series(object_id: str, x_positions_km: list[float], velocity_x_km_s: float) -> list[OrbitalState]:
    """Build deterministic TEME states at five-minute intervals for the demo."""
    return [
        OrbitalState(
            object_id=object_id,
            timestamp=START + timedelta(minutes=index * 5),
            position_km=Vector3(x_km, 7000.0, 20.0),
            velocity_km_s=Vector3(velocity_x_km_s, 7.5, 0.01),
            coordinate_frame="TEME",
        )
        for index, x_km in enumerate(x_positions_km)
    ]


def main() -> None:
    """Print a sampled closest-approach result from deterministic state data."""
    object_a = make_series("SAT-001", [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], 0.00)
    object_b = make_series("SAT-002", [15.0, 8.0, 3.0, 0.7, 4.0, 9.0, 16.0], 0.02)
    event = find_closest_approach(object_a, object_b)

    print("SPACEGUARD CONJUNCTION DETECTION")
    print("Sampled pipeline: propagated TEME states -> separation -> closest approach")
    print()
    print(f"Object A: {event.object_a}")
    print(f"Object B: {event.object_b}")
    print(f"Time of closest approach: {event.to_dict()['time_of_closest_approach']}")
    print(f"Miss distance: {event.miss_distance_km:.3f} km")
    print(f"Relative velocity: {event.relative_velocity_km_s:.3f} km/s")
    print(f"Risk: {event.risk_level}")
    print(event.risk_reason)


if __name__ == "__main__":
    main()
