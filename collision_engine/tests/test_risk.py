"""Tests for project demonstration risk thresholds."""

import unittest

from collision_engine import classify_risk


class RiskTests(unittest.TestCase):
    def test_high_medium_low_thresholds(self) -> None:
        self.assertEqual(classify_risk(1.0), "HIGH")
        self.assertEqual(classify_risk(1.1), "MEDIUM")
        self.assertEqual(classify_risk(10.0), "MEDIUM")
        self.assertEqual(classify_risk(10.1), "LOW")

    def test_invalid_distance_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "cannot be negative"):
            classify_risk(-1.0)
