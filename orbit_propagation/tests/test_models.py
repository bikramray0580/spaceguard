"""Tests for propagated orbital state models."""

import unittest
from datetime import datetime, timezone

from orbit_propagation.state_propagation.models import PropagatedState


def _valid_kwargs(**overrides):
    data = {
        "timestamp": datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        "position": (7000.0, 0.0, 0.0),
        "velocity": (0.0, 7.5, 0.0),
        "frame": "TEME",
        "position_units": "km",
        "velocity_units": "km/s",
    }
    data.update(overrides)
    return data


class TestPropagatedState(unittest.TestCase):
    def test_valid_state_can_be_created(self):
        state = PropagatedState(**_valid_kwargs())
        self.assertIsInstance(state, PropagatedState)
        self.assertEqual(state.frame, "TEME")
        self.assertEqual(state.position_units, "km")
        self.assertEqual(state.velocity_units, "km/s")

    def test_position_and_velocity_have_three_components(self):
        state = PropagatedState(**_valid_kwargs())
        self.assertEqual(len(state.position), 3)
        self.assertEqual(len(state.velocity), 3)
        self.assertEqual(state.position, (7000.0, 0.0, 0.0))
        self.assertEqual(state.velocity, (0.0, 7.5, 0.0))

    def test_required_fields_are_present(self):
        state = PropagatedState(**_valid_kwargs())
        self.assertIsNotNone(state.timestamp)
        self.assertIsNotNone(state.position)
        self.assertIsNotNone(state.velocity)
        self.assertIsNotNone(state.frame)
        self.assertIsNotNone(state.position_units)
        self.assertIsNotNone(state.velocity_units)
        self.assertTrue(hasattr(state, "timestamp"))
        self.assertTrue(hasattr(state, "position"))
        self.assertTrue(hasattr(state, "velocity"))
        self.assertTrue(hasattr(state, "frame"))
        self.assertTrue(hasattr(state, "position_units"))
        self.assertTrue(hasattr(state, "velocity_units"))

    def test_invalid_position_length_is_rejected(self):
        with self.assertRaises(ValueError):
            PropagatedState(**_valid_kwargs(position=(1.0, 2.0)))

    def test_invalid_velocity_length_is_rejected(self):
        with self.assertRaises(ValueError):
            PropagatedState(**_valid_kwargs(velocity=(1.0, 2.0, 3.0, 4.0)))

    def test_invalid_timestamp_is_rejected(self):
        with self.assertRaises(TypeError):
            PropagatedState(**_valid_kwargs(timestamp="2026-01-01T12:00:00Z"))

    def test_empty_frame_is_rejected(self):
        with self.assertRaises(ValueError):
            PropagatedState(**_valid_kwargs(frame=""))

    def test_non_numeric_position_is_rejected(self):
        with self.assertRaises(TypeError):
            PropagatedState(**_valid_kwargs(position=("x", "y", "z")))

    def test_missing_required_field_is_rejected(self):
        kwargs = _valid_kwargs()
        del kwargs["velocity"]
        with self.assertRaises(TypeError):
            PropagatedState(**kwargs)


if __name__ == "__main__":
    unittest.main()
