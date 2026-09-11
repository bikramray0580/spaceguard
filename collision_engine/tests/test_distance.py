"""Tests for relative-vector calculations."""

from datetime import datetime, timezone
import unittest

from collision_engine import (
    OrbitalState,
    Vector3,
    relative_position_km,
    relative_velocity_km_s,
    relative_velocity_magnitude_km_s,
    separation_distance_km,
)

TIME = datetime(2026, 8, 22, 12, 0, tzinfo=timezone.utc)


def state(object_id: str, position: tuple[float, float, float], velocity: tuple[float, float, float], *, timestamp: datetime = TIME, frame: str = "TEME") -> OrbitalState:
    return OrbitalState(object_id, timestamp, Vector3(*position), Vector3(*velocity), frame)


class DistanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.a = state("A", (1, 2, 3), (1, 1, 1))
        self.b = state("B", (4, 6, 3), (4, 5, 1))

    def test_relative_position_and_distance(self) -> None:
        self.assertEqual(relative_position_km(self.a, self.b), Vector3(3, 4, 0))
        self.assertEqual(separation_distance_km(self.a, self.b), 5.0)

    def test_relative_velocity_and_magnitude(self) -> None:
        self.assertEqual(relative_velocity_km_s(self.a, self.b), Vector3(3, 4, 0))
        self.assertEqual(relative_velocity_magnitude_km_s(self.a, self.b), 5.0)

    def test_same_position_is_zero_distance(self) -> None:
        self.assertEqual(separation_distance_km(self.a, state("B", (1, 2, 3), (0, 0, 0))), 0.0)

    def test_mismatched_timestamp_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "same timestamp"):
            separation_distance_km(self.a, state("B", (4, 6, 3), (4, 5, 1), timestamp=TIME.replace(minute=1)))

    def test_mismatched_frame_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "same coordinate frame"):
            separation_distance_km(self.a, state("B", (4, 6, 3), (4, 5, 1), frame="ITRF"))
