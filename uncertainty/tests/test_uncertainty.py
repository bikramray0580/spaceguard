from datetime import datetime, timedelta, timezone
import unittest
import numpy as np

from conjunction.engine import ConjunctionEngine
from conjunction.models import StateVector
from uncertainty import Covariance, CrossCovariance, UncertaintyStatus, assess_uncertainty
from uncertainty.covariance_parser import parse_covariance
from uncertainty.covariance_propagation import propagate_covariance
from uncertainty.encounter_frame import project_position_covariance
from uncertainty.relative_covariance import relative_covariance
from uncertainty.visualization import covariance_ellipse

T0 = datetime(2030, 1, 1, tzinfo=timezone.utc)

class Linear:
    def state_at(self, object_id, when):
        states = {"A": ((10., 5., 0.), (-2., 0., 0.)), "B": ((0., 0., 0.), (0., 0., 0.))}
        p, v = states[object_id]; dt = (when - T0).total_seconds()
        return StateVector(object_id, when, tuple(p[i] + dt * v[i] for i in range(3)), v, "GCRF")

def conjunction():
    return ConjunctionEngine(Linear()).assess("A", "B", T0, T0 + timedelta(seconds=10))

class CovarianceTests(unittest.TestCase):
    def test_valid_blocks_and_sigmas(self):
        c = Covariance(np.diag([4, 9, 16, 1, 4, 9]), T0, "GCRF", "test")
        self.assertEqual(c.position.shape, (3, 3)); self.assertEqual(c.velocity.shape, (3, 3))
        self.assertTrue(np.array_equal(c.position_velocity, np.zeros((3, 3))))
        self.assertTrue(np.array_equal(c.standard_deviations, [2, 3, 4, 1, 2, 3]))

    def test_invalid_matrices_are_rejected(self):
        for matrix, text in [(np.eye(5), "shape"), (np.full((6, 6), np.nan), "finite"),
                             (np.eye(6) + np.triu(np.ones((6, 6)), 1), "symmetric"),
                             (np.diag([1, 1, 1, 1, 1, -1]), "positive")]:
            with self.subTest(text=text), self.assertRaises(ValueError): Covariance(matrix, T0, "GCRF", "test")

    def test_parser_formats(self):
        for values, format in [(np.eye(6), "matrix"), (np.eye(6).reshape(-1), "flat"), ([1] * 6, "diagonal_variance"), ([2] * 6, "standard_deviation")]:
            parsed = parse_covariance(values, epoch=T0, reference_frame="GCRF", source="test", format=format)
            self.assertEqual(parsed.matrix.shape, (6, 6))
        self.assertEqual(parse_covariance([2] * 6, epoch=T0, reference_frame="GCRF", format="standard_deviation").matrix[0, 0], 4)

    def test_propagation_identity_and_noise(self):
        c = Covariance(np.eye(6), T0, "GCRF", "test")
        self.assertTrue(np.array_equal(propagate_covariance(c, np.eye(6)).matrix, np.eye(6)))
        forward = propagate_covariance(c, np.eye(6), 2 * np.eye(6), evaluation_epoch=T0 + timedelta(seconds=10))
        self.assertTrue(np.array_equal(forward.matrix, 3 * np.eye(6)))
        self.assertEqual((forward.propagation_duration_seconds, forward.propagation_direction), (10., "forward"))
        with self.assertRaises(ValueError): propagate_covariance(c, np.eye(5))

    def test_propagation_validates_noise_phi_and_epochs(self):
        c = Covariance(np.eye(6), T0, "GCRF", "test")
        with self.assertRaises(ValueError): propagate_covariance(c, np.eye(6), -2 * np.eye(6))
        with self.assertRaises(ValueError): propagate_covariance(c, np.eye(6), np.triu(np.ones((6, 6)), 1))
        with self.assertRaises(ValueError): propagate_covariance(c, np.eye(6), np.full((6, 6), np.nan))
        with self.assertRaises(ValueError): propagate_covariance(c, np.full((6, 6), np.inf))
        with self.assertRaises(ValueError): propagate_covariance(c, 2 * np.eye(6))
        with self.assertRaises(ValueError): propagate_covariance(c, 2 * np.eye(6), evaluation_epoch=T0)
        backward = propagate_covariance(c, np.eye(6), evaluation_epoch=T0 - timedelta(seconds=4))
        self.assertEqual((backward.propagation_duration_seconds, backward.propagation_direction), (-4., "backward"))

    def test_relative_and_cross_covariance(self):
        a, b = Covariance(np.eye(6), T0, "GCRF", "a"), Covariance(2 * np.eye(6), T0, "GCRF", "b")
        self.assertTrue(np.array_equal(relative_covariance(a, b), 3 * np.eye(6)))
        cross = CrossCovariance(.5 * np.eye(6), "GCRF", T0, "joint source")
        self.assertTrue(np.array_equal(relative_covariance(a, b, cross), 2 * np.eye(6)))

    def test_relative_covariance_rejects_incompatible_or_invalid_cross_terms(self):
        a = Covariance(np.eye(6), T0, "GCRF", "a")
        with self.assertRaises(ValueError): relative_covariance(a, Covariance(np.eye(6), T0, "TEME", "b"))
        with self.assertRaises(ValueError): relative_covariance(a, Covariance(np.eye(6), T0 + timedelta(seconds=1), "GCRF", "b"))
        with self.assertRaises(ValueError): relative_covariance(a, a, np.eye(6))
        with self.assertRaises(ValueError): relative_covariance(a, a, CrossCovariance(np.eye(6), "TEME", T0, "joint"))
        with self.assertRaises(ValueError): relative_covariance(a, a, CrossCovariance(2 * np.eye(6), "GCRF", T0, "joint"))
        with self.assertRaises(ValueError): CrossCovariance(np.full((6, 6), np.nan), "GCRF", T0, "joint")
        with self.assertRaises(ValueError): CrossCovariance(np.eye(6), "GCRF", T0, "joint", state_order=("vx", "vy", "vz", "x", "y", "z"))

    def test_encounter_projection(self):
        projected, h = project_position_covariance(np.diag([1., 4., 9.]), (1., 0., 0.), (0., 1., 0.))
        self.assertTrue(np.array_equal(h, [[1., 0., 0.], [0., 1., 0.]]))
        self.assertTrue(np.array_equal(projected, [[1., 0.], [0., 4.]]))

class AssessmentTests(unittest.TestCase):
    def test_projection_ellipse_and_pc_interface_shape(self):
        result = conjunction(); a = Covariance(np.eye(6), result.tca, "GCRF", "a", authoritative=True)
        assessment = assess_uncertainty(result, a, Covariance(np.eye(6), result.tca, "GCRF", "b", authoritative=True))
        self.assertEqual(assessment.covariance_status, UncertaintyStatus.AVAILABLE)
        self.assertEqual(assessment.encounter_position_covariance_km2.shape, (2, 2))
        self.assertTrue(np.allclose(assessment.encounter_position_covariance_km2, 2 * np.eye(2)))
        self.assertEqual(len(assessment.collision_probability_covariance_km2), 2)
        self.assertFalse(assessment.pc_authoritative)
        self.assertEqual(assessment.to_collision_probability_input().combined_position_covariance_km2, assessment.collision_probability_covariance_km2)

    def test_ellipse_axes(self):
        ellipse = covariance_ellipse([[9, 0], [0, 4]], confidence_level=.5)
        self.assertGreater(ellipse.semi_major_axis_km, ellipse.semi_minor_axis_km)
        self.assertAlmostEqual(ellipse.orientation_rad, 0.0)

    def test_quality_frame_epoch_missing_and_estimated(self):
        result = conjunction(); good = Covariance(np.eye(6), result.tca, "GCRF", "a", authoritative=True)
        self.assertEqual(assess_uncertainty(result, None, good).covariance_status, UncertaintyStatus.UNAVAILABLE)
        self.assertEqual(assess_uncertainty(result, good, Covariance(np.eye(6), result.tca, "TEME", "b")).covariance_status, UncertaintyStatus.INVALID)
        self.assertEqual(assess_uncertainty(result, good, Covariance(np.eye(6), T0, "GCRF", "b")).covariance_status, UncertaintyStatus.INVALID)
        self.assertEqual(assess_uncertainty(result, good, Covariance(np.eye(6), result.tca, "GCRF", "b", estimated=True)).covariance_status, UncertaintyStatus.ESTIMATED)
        self.assertEqual(assess_uncertainty(result, good, Covariance(np.eye(6), result.tca, "GCRF", "unknown")).covariance_status, UncertaintyStatus.ESTIMATED)

    def test_covariance_defensively_copies_and_freezes_matrices(self):
        original = np.eye(6); covariance = Covariance(original, T0, "GCRF", "a")
        original[0, 0] = 99
        self.assertEqual(covariance.matrix[0, 0], 1)
        with self.assertRaises(ValueError): covariance.matrix[0, 0] = 2

    def test_degenerate_encounter_plane_warns_but_preserves_geometry(self):
        class Parallel(Linear):
            def state_at(self, object_id, when):
                states = {"A": ((10., 0., 0.), (-2., 0., 0.)), "B": ((0., 0., 0.), (0., 0., 0.))}
                p, v = states[object_id]; dt = (when - T0).total_seconds()
                return StateVector(object_id, when, tuple(p[i] + dt * v[i] for i in range(3)), v, "GCRF")
        result = ConjunctionEngine(Parallel()).assess("A", "B", T0, T0 + timedelta(seconds=10))
        assessment = assess_uncertainty(result, Covariance(np.eye(6), result.tca, "GCRF", "a", authoritative=True), Covariance(np.eye(6), result.tca, "GCRF", "b", authoritative=True))
        self.assertEqual(assessment.covariance_status, UncertaintyStatus.AVAILABLE)
        self.assertTrue(assessment.quality.warnings)

    def test_zero_relative_velocity_remains_invalid_for_projection(self):
        class Static(Linear):
            def state_at(self, object_id, when):
                return StateVector(object_id, when, (0., 0., 0.), (0., 0., 0.), "GCRF")
        result = ConjunctionEngine(Static()).assess("A", "B", T0, T0 + timedelta(seconds=1))
        assessment = assess_uncertainty(result, Covariance(np.eye(6), result.tca, "GCRF", "a", authoritative=True), Covariance(np.eye(6), result.tca, "GCRF", "b", authoritative=True))
        self.assertEqual(assessment.covariance_status, UncertaintyStatus.INVALID)

if __name__ == "__main__": unittest.main()
