"""Integration tests for the real conjunction -> uncertainty -> risk handoff."""

import unittest
from datetime import datetime, timezone

from conjunction.models import ConjunctionResult, TcaQuality
from risk import assess_upstream_risk, risk_input_from_upstream
from risk.models import PcStatus, RiskLevel
from uncertainty.assessment import UncertaintyAssessment, UncertaintyProvenance
from uncertainty.quality_flags import UncertaintyQuality, UncertaintyStatus


class UpstreamAdapterTests(unittest.TestCase):
    def make_conjunction(self):
        tca = datetime(2026, 9, 12, tzinfo=timezone.utc)
        return ConjunctionResult(
            object_a_id="A",
            object_b_id="B",
            tca=tca,
            relative_position_km=(0.4, 0.0, 0.0),
            relative_velocity_km_s=(0.0, 0.01, 0.0),
            miss_distance_vector_km=(0.4, 0.0, 0.0),
            miss_distance_km=0.4,
            relative_speed_km_s=0.01,
            closing_rate_km_s=0.0,
            relative_motion_direction=(0.0, 1.0, 0.0),
            miss_distance_direction=(1.0, 0.0, 0.0),
            reference_frame="GCRF",
            tca_quality=TcaQuality(
                sample_count=5,
                bracket_start=datetime(2026, 9, 11, 23, 0, tzinfo=timezone.utc),
                bracket_end=datetime(2026, 9, 12, 1, 0, tzinfo=timezone.utc),
                residual_km2_s=0.0,
                converged=True,
                boundary_minimum=False,
            ),
            status="success",
        )

    def test_real_upstream_contracts_feed_person5(self):
        conjunction = self.make_conjunction()
        uncertainty = UncertaintyAssessment(
            conjunction=conjunction,
            quality=UncertaintyQuality(
                UncertaintyStatus.UNAVAILABLE,
                "Pc not authoritative / unavailable because covariance is unavailable.",
            ),
            provenance=UncertaintyProvenance(
                source_a="source-a",
                source_b="source-b",
                covariance_epoch_a=None,
                covariance_epoch_b=None,
                evaluation_time=conjunction.tca,
                reference_frame=conjunction.reference_frame,
            ),
            pc_authoritative=False,
        )

        event = risk_input_from_upstream(conjunction, uncertainty)
        self.assertEqual(event.object_a, "A")
        self.assertEqual(event.object_b, "B")
        self.assertEqual(event.miss_distance_km, 0.4)
        self.assertEqual(event.relative_velocity_km_s, 0.01)
        self.assertEqual(event.pc_status, PcStatus.UNAVAILABLE)
        self.assertEqual(event.covariance_status, "UNAVAILABLE")
        self.assertEqual(event.provenance["reference_frame"], "GCRF")

        result = assess_upstream_risk(conjunction, uncertainty)
        self.assertEqual(result.risk_level, RiskLevel.HIGH)
        self.assertIsNone(result.pc)
        self.assertEqual(result.pc_status, PcStatus.UNAVAILABLE)
        self.assertTrue(result.alert)


if __name__ == "__main__":
    unittest.main()
