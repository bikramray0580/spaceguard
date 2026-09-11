"""Tests for presentation-only pipeline reporting."""

from datetime import datetime, timezone
import unittest

from collision_engine.models import ConjunctionEvent
from integration.models import PipelineRun
from integration.reporting import render_safety_report


TIME = datetime(2026, 8, 23, 16, 27, tzinfo=timezone.utc)


class ReportingTests(unittest.TestCase):
    def test_report_summarizes_existing_event_values_without_changing_them(self) -> None:
        high_event = ConjunctionEvent("00900", "00902", TIME, 0.70, 0.02, "HIGH", "existing")
        low_event = ConjunctionEvent("00900", "01361", TIME, 13271.136, 13.972, "LOW", "existing")
        run = PipelineRun(
            source="CelesTrak",
            fetched_at=TIME,
            timestamps=(TIME,),
            propagated_by_object={"00900": (), "00902": (), "01361": ()},
            states_by_object={"00900": (), "00902": (), "01361": ()},
            conjunctions=(high_event, low_event),
        )

        report = render_safety_report(run)

        self.assertIn("Objects analyzed: 3", report)
        self.assertIn("Satellite pairs screened: 3", report)
        self.assertIn("🟢 LOW RISK       1", report)
        self.assertIn("🔴 HIGH RISK      1", report)
        self.assertIn("0.70 km", report)
        self.assertIn("13,271 km", report)
        self.assertIn("high-risk screening threshold", report)
        self.assertEqual(high_event.miss_distance_km, 0.70)
        self.assertEqual(low_event.relative_velocity_km_s, 13.972)


if __name__ == "__main__":
    unittest.main()
