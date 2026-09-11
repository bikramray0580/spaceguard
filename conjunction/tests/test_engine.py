from __future__ import annotations

from datetime import datetime, timedelta, timezone
import unittest

from conjunction.engine import ConjunctionEngine, PropagationError
from conjunction.models import StateVector


T0 = datetime(2030, 1, 1, tzinfo=timezone.utc)


class LinearPropagator:
    """Deterministic km / km/s propagator for analytic conjunction tests."""

    def __init__(self, states: dict[str, tuple[tuple[float, float, float], tuple[float, float, float], str]]) -> None:
        self.states = states

    def state_at(self, object_id: str, when: datetime) -> StateVector:
        position, velocity, frame = self.states[object_id]
        seconds = (when - T0).total_seconds()
        return StateVector(object_id, when,
                           tuple(position[i] + velocity[i] * seconds for i in range(3)), velocity, frame)


def engine_for(r0=(10.0, 5.0, 0.0), velocity=(-2.0, 0.0, 0.0)) -> ConjunctionEngine:
    return ConjunctionEngine(LinearPropagator({"A": (r0, velocity, "GCRF"), "B": ((0., 0., 0.), (0., 0., 0.), "GCRF")}))


class ConjunctionEngineTests(unittest.TestCase):
    def test_analytic_tca_is_refined_beyond_sampling_grid(self) -> None:
        # t = -r0.v / |v|² = 5 s; 8 broad samples do not contain 5 s.
        result = ConjunctionEngine(engine_for().propagator, samples=8, tolerance_seconds=1e-5).assess("A", "B", T0, T0 + timedelta(seconds=10))
        self.assertAlmostEqual((result.tca - T0).total_seconds(), 5.0, places=4)
        self.assertAlmostEqual(result.miss_distance_km, 5.0, places=6)
        self.assertAlmostEqual(result.relative_speed_km_s, 2.0, places=8)
        self.assertLess(abs(result.tca_quality.residual_km2_s), 1e-4)

    def test_approaching_head_on_has_positive_closing_rate(self) -> None:
        result = engine_for((10., 0., 0.), (-2., 0., 0.)).assess("A", "B", T0, T0 + timedelta(seconds=4))
        self.assertAlmostEqual(result.closing_rate_km_s, 2.0)
        self.assertEqual(result.status, "boundary_minimum")

    def test_miss_vector_and_relative_velocity(self) -> None:
        result = engine_for().assess("A", "B", T0, T0 + timedelta(seconds=10))
        self.assertAlmostEqual(result.relative_position_km[0], 0.0, places=5)
        self.assertEqual(result.relative_velocity_km_s, (-2., 0., 0.))
        self.assertEqual(result.miss_distance_vector_km, result.relative_position_km)
        self.assertEqual(result.relative_motion_direction, (-1., 0., 0.))

    def test_identical_states_are_a_boundary_minimum(self) -> None:
        result = engine_for((0., 0., 0.), (0., 0., 0.)).assess("A", "B", T0, T0 + timedelta(seconds=10))
        self.assertEqual(result.miss_distance_km, 0.0)
        self.assertEqual(result.relative_speed_km_s, 0.0)
        self.assertEqual(result.closing_rate_km_s, 0.0)
        self.assertIsNone(result.miss_distance_direction)

    def test_large_separation(self) -> None:
        result = engine_for((1_000_000., 1_000_000., 0.), (0., -1., 0.)).assess("A", "B", T0, T0 + timedelta(seconds=100))
        self.assertGreater(result.miss_distance_km, 1_000_000.)

    def test_propagation_failure_is_not_silently_converted_to_zero(self) -> None:
        class Broken:
            def state_at(self, object_id, when):
                raise RuntimeError("no ephemeris")
        with self.assertRaises(PropagationError):
            ConjunctionEngine(Broken()).assess("A", "B", T0, T0 + timedelta(seconds=1))

    def test_invalid_input_and_frame_mismatch(self) -> None:
        with self.assertRaises(ValueError):
            engine_for().assess("A", "B", T0.replace(tzinfo=None), T0 + timedelta(seconds=1))
        bad = LinearPropagator({"A": ((0., 0., 0.), (0., 0., 0.), "GCRF"), "B": ((1., 0., 0.), (0., 0., 0.), "TEME")})
        with self.assertRaises(ValueError):
            ConjunctionEngine(bad).assess("A", "B", T0, T0 + timedelta(seconds=1))
        with self.assertRaises(ValueError):
            StateVector("A", T0, (float("nan"), 0., 0.), (0., 0., 0.), "GCRF")
        with self.assertRaises(ValueError):
            StateVector("A", T0, (0., 0., 0.), (0., 0., 0.), "RTN")

    def test_state_units_are_km_and_km_per_second_by_contract(self) -> None:
        state = LinearPropagator({"A": ((1.5, 0., 0.), (0.25, 0., 0.), "GCRF")}).state_at("A", T0 + timedelta(seconds=2))
        self.assertEqual(state.position_km[0], 2.0)
        self.assertEqual(state.velocity_km_s[0], 0.25)

    def test_invalid_interval_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            engine_for().assess("A", "B", T0, T0)

    def test_same_object_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            engine_for().assess("A", "A", T0, T0 + timedelta(seconds=1))

    def test_invalid_engine_settings_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ConjunctionEngine(engine_for().propagator, samples=2)
        with self.assertRaises(ValueError):
            ConjunctionEngine(engine_for().propagator, tolerance_seconds=0)

    def test_infinite_state_component_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            StateVector("A", T0, (float("inf"), 0., 0.), (0., 0., 0.), "GCRF")

    def test_reference_frame_metadata_is_preserved(self) -> None:
        self.assertEqual(engine_for().assess("A", "B", T0, T0 + timedelta(seconds=10)).reference_frame, "GCRF")

    def test_miss_distance_direction_is_normalized(self) -> None:
        direction = engine_for().assess("A", "B", T0, T0 + timedelta(seconds=10)).miss_distance_direction
        self.assertAlmostEqual(direction[0], 0.0, places=5)
        self.assertAlmostEqual(direction[1], 1.0, places=5)

    def test_relative_motion_direction_is_normalized(self) -> None:
        direction = engine_for().assess("A", "B", T0, T0 + timedelta(seconds=10)).relative_motion_direction
        self.assertAlmostEqual(sum(component * component for component in direction), 1.0)

    def test_wrong_epoch_from_propagator_is_rejected(self) -> None:
        class WrongEpoch(LinearPropagator):
            def state_at(self, object_id, when):
                state = super().state_at(object_id, when)
                return StateVector(state.object_id, T0, state.position_km, state.velocity_km_s, state.reference_frame)
        with self.assertRaises(PropagationError):
            ConjunctionEngine(WrongEpoch(engine_for().propagator.states)).assess("A", "B", T0, T0 + timedelta(seconds=1))

    def test_boundary_tca_is_exact_requested_endpoint(self) -> None:
        result = engine_for((10., 0., 0.), (-2., 0., 0.)).assess("A", "B", T0, T0 + timedelta(seconds=4))
        self.assertEqual(result.tca, T0 + timedelta(seconds=4))

    def test_serializable_contract_and_mocked_covariance_consumer(self) -> None:
        result = engine_for().assess("A", "B", T0, T0 + timedelta(seconds=10))
        payload = result.to_dict()
        self.assertEqual(payload["reference_frame"], "GCRF")
        self.assertIsInstance(payload["tca"], str)
        # This is deliberately all a covariance consumer needs from this module.
        consumed = (payload["object_a_id"], payload["object_b_id"], payload["tca"], payload["relative_position_km"])
        self.assertEqual(consumed[:2], ("A", "B"))


if __name__ == "__main__":
    unittest.main()
