"""Unit tests for SGP4 propagation."""

from datetime import datetime, timedelta, timezone
import unittest
from unittest.mock import patch

from orbit_engine import (
    PropagationError,
    TLEValidationError,
    generate_time_steps,
    propagate_tle,
)

# Representative ISS TLE. Tests check the interface, not a specific ephemeris.
ISS_LINE_1 = "1 25544U 98067A   24001.50000000  .00010000  00000+0  18000-3 0  9999"
ISS_LINE_2 = "2 25544  51.6400  25.0000 0005000  60.0000 300.0000 15.50000000    01"
TIME = datetime(2024, 1, 2, 12, 0, tzinfo=timezone.utc)


class PropagatorTests(unittest.TestCase):
    def test_single_timestamp_returns_teme_state_vector(self) -> None:
        result = propagate_tle("ISS", ISS_LINE_1, ISS_LINE_2, TIME)

        self.assertEqual(result.object_id, "25544")
        self.assertEqual(result.coordinate_frame, "TEME")
        self.assertEqual(result.timestamp, TIME)
        self.assertTrue(all(isinstance(value, float) for value in result.position.__dict__.values()))
        self.assertTrue(all(isinstance(value, float) for value in result.velocity.__dict__.values()))
        self.assertEqual(result.to_dict()["timestamp"], "2024-01-02T12:00:00Z")

    def test_multiple_timestamps_return_multiple_results(self) -> None:
        timestamps = [TIME, TIME + timedelta(minutes=5)]
        results = propagate_tle("ISS", ISS_LINE_1, ISS_LINE_2, timestamps)

        self.assertEqual(len(results), 2)
        self.assertEqual([result.timestamp for result in results], timestamps)

    def test_time_step_generator_is_inclusive(self) -> None:
        steps = generate_time_steps(TIME, TIME + timedelta(minutes=10), 5)
        self.assertEqual(steps, [TIME, TIME + timedelta(minutes=5), TIME + timedelta(minutes=10)])

    def test_invalid_tle_has_clear_error(self) -> None:
        with self.assertRaisesRegex(TLEValidationError, "at least 69"):
            propagate_tle("bad", "not a TLE", "also not a TLE", TIME)

    def test_naive_timestamp_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            propagate_tle("ISS", ISS_LINE_1, ISS_LINE_2, TIME.replace(tzinfo=None))

    def test_sgp4_error_is_not_silenced(self) -> None:
        class FailingSatellite:
            satnum = 25544

            def sgp4(self, _julian_date: float, _fraction: float):
                return 6, (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)

        with patch("orbit_engine.propagator.parse_tle", return_value=FailingSatellite()):
            with self.assertRaisesRegex(PropagationError, "decayed"):
                propagate_tle("ISS", ISS_LINE_1, ISS_LINE_2, TIME)


if __name__ == "__main__":
    unittest.main()
