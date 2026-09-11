"""Manually verify the TLE -> SGP4 -> TEME position/velocity pipeline.

Run from the project root with:
    python -m orbit_engine.demo_propagation
"""

from datetime import datetime, timedelta, timezone

from orbit_engine import generate_time_steps, propagate_tle


OBJECT_NAME = "ISS (ZARYA)"
# Representative ISS TLE used for a reproducible demonstration timestamp.
ISS_LINE_1 = "1 25544U 98067A   24001.50000000  .00010000  00000+0  18000-3 0  9999"
ISS_LINE_2 = "2 25544  51.6400  25.0000 0005000  60.0000 300.0000 15.50000000    01"
START_TIME = datetime(2024, 1, 2, 12, 0, tzinfo=timezone.utc)


def print_state(timestamp: datetime) -> None:
    """Propagate and print one clearly labelled TEME state vector."""
    result = propagate_tle(OBJECT_NAME, ISS_LINE_1, ISS_LINE_2, timestamp)

    print(f"Timestamp: {result.to_dict()['timestamp']}")
    print(f"Coordinate frame: {result.coordinate_frame}")
    print("Position:")
    print(f"  X: {result.position.x_km:.3f} km")
    print(f"  Y: {result.position.y_km:.3f} km")
    print(f"  Z: {result.position.z_km:.3f} km")
    print("Velocity:")
    print(f"  VX: {result.velocity.x_km_s:.6f} km/s")
    print(f"  VY: {result.velocity.y_km_s:.6f} km/s")
    print(f"  VZ: {result.velocity.z_km_s:.6f} km/s")


def main() -> None:
    """Run one propagation and a 30-minute, five-minute-step series."""
    print("Orbit propagation pipeline: TLE -> SGP4 -> TEME position/velocity")
    print()
    print(f"Satellite/object name: {OBJECT_NAME}")
    print("Input TLE:")
    print(f"  {ISS_LINE_1}")
    print(f"  {ISS_LINE_2}")
    print()

    print("Single propagation:")
    print_state(START_TIME)
    print()

    print("Propagation series (every 5 minutes for 30 minutes):")
    timestamps = generate_time_steps(START_TIME, START_TIME + timedelta(minutes=30), 5)
    for timestamp in timestamps:
        print_state(timestamp)
        print()


if __name__ == "__main__":
    main()
