from datetime import datetime, timedelta, timezone
import unittest

from collision_engine import OrbitalState, Vector3, find_closest_approach
from ml.features import FEATURES, build_features


TIME = datetime(2026, 8, 24, 12, 0, tzinfo=timezone.utc)


def state(object_id: str, minute: int, x: float) -> OrbitalState:
    return OrbitalState(
        object_id=object_id,
        timestamp=TIME + timedelta(minutes=minute),
        position_km=Vector3(x, 7000, 0),
        velocity_km_s=Vector3(0, 7.5, 0),
        coordinate_frame="TEME",
    )


class FeatureExtractionTests(unittest.TestCase):
    def test_features_are_created_from_conjunction_and_orbital_states(self) -> None:
        states_a = [state("A", minute, 0) for minute in range(3)]
        states_b = [state("B", 0, 10), state("B", 1, 2), state("B", 2, 5)]
        event = find_closest_approach(states_a, states_b)

        features = build_features(event, states_a, states_b, analysis_time=TIME)

        self.assertEqual(tuple(features), FEATURES)
        self.assertEqual(features["miss_distance_km"], 2)
        self.assertEqual(features["time_to_tca_hours"], 1 / 60)
        self.assertAlmostEqual(features["object_a_altitude_km"], 629.0)
        # The radial altitude changes very slightly when x changes by 2 km.
        self.assertAlmostEqual(features["altitude_difference_km"], 0.000286, places=6)


if __name__ == "__main__":
    unittest.main()
