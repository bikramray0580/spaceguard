from datetime import datetime, timedelta, timezone
import unittest
from conjunction.collision_probability import CollisionProbabilityResult, UnavailableWithoutCovarianceCalculator
from conjunction.encounter_plane import calculate_encounter_geometry
from conjunction.miss_distance import calculate_miss_distance
from conjunction.relative_velocity import calculate_relative_velocity
from conjunction.screening import broad_screen
from conjunction.models import StateVector

T0 = datetime(2030, 1, 1, tzinfo=timezone.utc)
class Linear:
    def state_at(self, object_id, when):
        data = {"A": ((10., 0., 0.), (-2., 0., 0.)), "B": ((0., 0., 0.), (0., 0., 0.)), "C": ((100., 0., 0.), (0., 0., 0.))}[object_id]
        seconds=(when-T0).total_seconds(); p,v=data
        return StateVector(object_id, when, tuple(p[i]+v[i]*seconds for i in range(3)), v, "GCRF")

class ComponentTests(unittest.TestCase):
    def test_screen_detects_candidate_and_rejects_far_pair(self):
        screen = broad_screen(Linear(), ["A", "B", "C"], T0, T0+timedelta(seconds=10), sampling_interval_seconds=1, distance_threshold_km=1)
        self.assertEqual([(x.object_a_id,x.object_b_id) for x in screen.candidates], [("A","B")])
    def test_screen_empty_input(self):
        self.assertEqual(broad_screen(Linear(), [], T0, T0+timedelta(seconds=1), sampling_interval_seconds=1, distance_threshold_km=1).candidates, ())
    def test_relative_velocity_and_closing_rate(self):
        answer=calculate_relative_velocity((10.,0.,0.),(-2.,0.,0.),(0.,0.,0.),(0.,0.,0.))
        self.assertEqual(answer.vector_km_s,(-2.,0.,0.)); self.assertEqual(answer.speed_km_s,2.); self.assertEqual(answer.closing_rate_km_s,2.)
    def test_zero_distance_closing_rate_is_safe(self):
        self.assertEqual(calculate_relative_velocity((0.,0.,0.),(1.,0.,0.),(0.,0.,0.),(0.,0.,0.)).closing_rate_km_s,0.)
    def test_miss_distance_vector_and_direction(self):
        answer=calculate_miss_distance((3.,4.,0.),(0.,0.,0.)); self.assertEqual(answer.distance_km,5.); self.assertEqual(answer.direction,(0.6,0.8,0.))
    def test_encounter_basis_is_orthogonal(self):
        geometry=calculate_encounter_geometry((0.,2.,0.),(1.,0.,0.))
        self.assertAlmostEqual(sum(a*b for a,b in zip(geometry.plane_x, geometry.plane_y)),0.); self.assertFalse(geometry.degenerate)
    def test_degenerate_encounter_geometry(self):
        self.assertTrue(calculate_encounter_geometry((1.,0.,0.),(0.,0.,0.)).degenerate)
    def test_pc_contract_refuses_to_invent_probability(self):
        self.assertIsNone(CollisionProbabilityResult().probability); self.assertEqual(CollisionProbabilityResult().status,"NOT_AVAILABLE_WITHOUT_COVARIANCE")
