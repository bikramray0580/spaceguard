"""Deterministic unit tests for Person 5 risk/actionability logic."""

import unittest

from risk.decision_tables import RiskThresholds
from risk.engine import assess_risk
from risk.models import Confidence, PcStatus, RecommendedAction, RiskInput, RiskLevel, Trend


class RiskEngineTests(unittest.TestCase):
    def test_wire_format_pc_status_is_normalized(self):
        event = RiskInput(
            object_a="A", object_b="B", miss_distance_km=4.0,
            tca_utc="2026-09-12T00:00:00Z", pc=2e-4,
            pc_status="AUTHORITATIVE",  # type: ignore[arg-type]
        )
        result = assess_risk(event)
        self.assertEqual(event.pc_status, PcStatus.AUTHORITATIVE)
        self.assertEqual(result.pc, 2e-4)
        self.assertEqual(result.risk_level, RiskLevel.HIGH)

    def test_invalid_pc_status_is_rejected(self):
        with self.assertRaises(ValueError):
            RiskInput(
                object_a="A", object_b="B", miss_distance_km=4.0,
                tca_utc="2026-09-12T00:00:00Z",
                pc_status="NOT_A_STATUS",  # type: ignore[arg-type]
            )

    def test_negative_measurements_are_rejected(self):
        with self.assertRaises(ValueError):
            RiskInput(
                object_a="A", object_b="B", miss_distance_km=-1.0,
                tca_utc="2026-09-12T00:00:00Z",
            )
        with self.assertRaises(ValueError):
            RiskInput(
                object_a="A", object_b="B", miss_distance_km=1.0,
                tca_utc="2026-09-12T00:00:00Z", pc=-1e-6,
            )

    def test_high_risk_without_covariance_never_claims_pc(self):
        event = RiskInput(
            object_a="A", object_b="B", miss_distance_km=0.4,
            tca_utc="2026-09-12T00:00:00Z",
            covariance_status="UNAVAILABLE",
            historical_validation="UNKNOWN",
            propagation_quality="UNKNOWN",
        )
        result = assess_risk(event)
        self.assertEqual(result.risk_level, RiskLevel.HIGH)
        self.assertTrue(result.alert)
        self.assertEqual(result.recommended_action, RecommendedAction.PRIORITIZE_REVIEW)
        self.assertIsNone(result.pc)
        self.assertEqual(result.pc_status, PcStatus.UNAVAILABLE)

    def test_authoritative_pc_is_preserved(self):
        event = RiskInput(
            object_a="A", object_b="B", miss_distance_km=4.0,
            tca_utc="2026-09-12T00:00:00Z", pc=2e-4,
            pc_status=PcStatus.AUTHORITATIVE,
            covariance_status="AUTHORITATIVE",
            historical_validation="VALIDATED",
            propagation_quality="VALIDATED",
            epoch_age_hours=4,
        )
        result = assess_risk(event)
        self.assertEqual(result.pc, 2e-4)
        self.assertEqual(result.pc_status, PcStatus.AUTHORITATIVE)
        self.assertEqual(result.confidence, Confidence.HIGH)
        self.assertEqual(result.risk_level, RiskLevel.HIGH)

    def test_worsening_medium_event_triggers_reassessment(self):
        previous = RiskInput(
            object_a="A", object_b="B", miss_distance_km=4.0,
            tca_utc="2026-09-11T00:00:00Z", covariance_status="ESTIMATED",
        )
        current = RiskInput(
            object_a="A", object_b="B", miss_distance_km=3.0,
            tca_utc="2026-09-12T00:00:00Z", covariance_status="ESTIMATED",
            previous=previous,
        )
        result = assess_risk(current, RiskThresholds())
        self.assertEqual(result.risk_level, RiskLevel.MEDIUM)
        self.assertEqual(result.trend, Trend.WORSENING)
        self.assertEqual(result.recommended_action, RecommendedAction.REASSESS)
        self.assertEqual(result.alert_type, "WORSENING_RISK")

    def test_low_risk_stable_event_is_monitor_only(self):
        previous = RiskInput(
            object_a="A", object_b="B", miss_distance_km=20.0,
            tca_utc="2026-09-11T00:00:00Z", covariance_status="AUTHORITATIVE",
            historical_validation="VALIDATED", propagation_quality="VALIDATED",
        )
        current = RiskInput(
            object_a="A", object_b="B", miss_distance_km=20.0,
            tca_utc="2026-09-12T00:00:00Z", covariance_status="AUTHORITATIVE",
            historical_validation="VALIDATED", propagation_quality="VALIDATED",
            previous=previous,
        )
        result = assess_risk(current)
        self.assertEqual(result.risk_level, RiskLevel.LOW)
        self.assertEqual(result.trend, Trend.STABLE)
        self.assertFalse(result.alert)
        self.assertEqual(result.recommended_action, RecommendedAction.MONITOR)


if __name__ == "__main__":
    unittest.main()
