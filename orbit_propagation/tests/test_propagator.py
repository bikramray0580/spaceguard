"""Tests for single-timestamp SGP4 TLE propagation."""

import unittest
from datetime import datetime, timedelta, timezone

from orbit_propagation.sgp4.propagator import SGP4Propagator
from orbit_propagation.state_propagation.models import PropagatedState

ISS_TLE_LINE1 = "1 25544U 98067A   19343.69339541  .00001764  00000-0  38792-4 0  9991"
ISS_TLE_LINE2 = "2 25544  51.6439 211.2001 0007417  17.6667  85.6398 15.50103472202482"
ISS_EPOCH = datetime(2019, 12, 9, 16, 38, 30, tzinfo=timezone.utc)


class TestSGP4Propagator(unittest.TestCase):
    def setUp(self):
        self.propagator = SGP4Propagator()

    def test_valid_tle_propagation(self):
        state = self.propagator.propagate(ISS_TLE_LINE1, ISS_TLE_LINE2, ISS_EPOCH)
        self.assertIsInstance(state, PropagatedState)
        self.assertEqual(state.timestamp, ISS_EPOCH)
        self.assertEqual(state.frame, "TEME")
        self.assertEqual(state.position_units, "km")
        self.assertEqual(state.velocity_units, "km/s")

    def test_invalid_tle_input(self):
        with self.assertRaises(ValueError):
            self.propagator.propagate("not a tle", "also not a tle", ISS_EPOCH)

    def test_invalid_timestamp_input(self):
        with self.assertRaises(TypeError):
            self.propagator.propagate(
                ISS_TLE_LINE1,
                ISS_TLE_LINE2,
                "2019-12-09T16:38:30Z",
            )

    def test_returned_position_has_three_components(self):
        state = self.propagator.propagate(ISS_TLE_LINE1, ISS_TLE_LINE2, ISS_EPOCH)
        self.assertEqual(len(state.position), 3)

    def test_returned_velocity_has_three_components(self):
        state = self.propagator.propagate(ISS_TLE_LINE1, ISS_TLE_LINE2, ISS_EPOCH)
        self.assertEqual(len(state.velocity), 3)

    def test_valid_window_returns_multiple_states(self):
        end_time = ISS_EPOCH + timedelta(seconds=60)
        states = self.propagator.propagate_window(
            ISS_TLE_LINE1,
            ISS_TLE_LINE2,
            ISS_EPOCH,
            end_time,
            20,
        )
        self.assertGreater(len(states), 1)

    def test_window_states_are_chronological(self):
        end_time = ISS_EPOCH + timedelta(seconds=60)
        states = self.propagator.propagate_window(
            ISS_TLE_LINE1,
            ISS_TLE_LINE2,
            ISS_EPOCH,
            end_time,
            20,
        )
        timestamps = [state.timestamp for state in states]
        self.assertEqual(timestamps, sorted(timestamps))

    def test_window_states_are_propagated_state_objects(self):
        end_time = ISS_EPOCH + timedelta(seconds=40)
        states = self.propagator.propagate_window(
            ISS_TLE_LINE1,
            ISS_TLE_LINE2,
            ISS_EPOCH,
            end_time,
            20,
        )
        self.assertTrue(states)
        self.assertTrue(all(isinstance(state, PropagatedState) for state in states))

    def test_window_step_size_is_respected(self):
        end_time = ISS_EPOCH + timedelta(seconds=60)
        states = self.propagator.propagate_window(
            ISS_TLE_LINE1,
            ISS_TLE_LINE2,
            ISS_EPOCH,
            end_time,
            20,
        )
        expected = [
            ISS_EPOCH,
            ISS_EPOCH + timedelta(seconds=20),
            ISS_EPOCH + timedelta(seconds=40),
            ISS_EPOCH + timedelta(seconds=60),
        ]
        self.assertEqual([state.timestamp for state in states], expected)

    def test_exact_end_time_is_included(self):
        end_time = ISS_EPOCH + timedelta(seconds=30)
        states = self.propagator.propagate_window(
            ISS_TLE_LINE1,
            ISS_TLE_LINE2,
            ISS_EPOCH,
            end_time,
            10,
        )
        self.assertEqual(states[-1].timestamp, end_time)

    def test_non_aligned_end_time_is_not_overshot(self):
        end_time = ISS_EPOCH + timedelta(seconds=25)
        states = self.propagator.propagate_window(
            ISS_TLE_LINE1,
            ISS_TLE_LINE2,
            ISS_EPOCH,
            end_time,
            10,
        )
        timestamps = [state.timestamp for state in states]
        self.assertEqual(
            timestamps,
            [
                ISS_EPOCH,
                ISS_EPOCH + timedelta(seconds=10),
                ISS_EPOCH + timedelta(seconds=20),
            ],
        )
        self.assertNotIn(ISS_EPOCH + timedelta(seconds=30), timestamps)
        self.assertTrue(all(ts <= end_time for ts in timestamps))

    def test_end_time_before_start_time_is_rejected(self):
        with self.assertRaises(ValueError):
            self.propagator.propagate_window(
                ISS_TLE_LINE1,
                ISS_TLE_LINE2,
                ISS_EPOCH,
                ISS_EPOCH - timedelta(seconds=1),
                10,
            )

    def test_zero_or_negative_step_is_rejected(self):
        end_time = ISS_EPOCH + timedelta(seconds=60)
        with self.assertRaises(ValueError):
            self.propagator.propagate_window(
                ISS_TLE_LINE1,
                ISS_TLE_LINE2,
                ISS_EPOCH,
                end_time,
                0,
            )
        with self.assertRaises(ValueError):
            self.propagator.propagate_window(
                ISS_TLE_LINE1,
                ISS_TLE_LINE2,
                ISS_EPOCH,
                end_time,
                -5,
            )


if __name__ == "__main__":
    unittest.main()

