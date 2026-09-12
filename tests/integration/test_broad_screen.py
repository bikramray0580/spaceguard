from __future__ import annotations

import json
import unittest
from datetime import datetime, timedelta, timezone
from itertools import combinations
from math import isfinite
from pathlib import Path

from conjunction.models import StateVector
from conjunction.screening import ScreeningCandidate, ScreeningResult, broad_screen
from orbit_propagation.sgp4.propagator import SGP4Propagator

REPO_ROOT = Path(__file__).resolve().parents[2]
ORBITAL_CATALOGUE = REPO_ROOT / "data" / "orbital_data.json"
ISS_TLE_PATH = REPO_ROOT / "shared" / "data" / "sample" / "iss.tle"

SCREEN_START = datetime(2026, 8, 25, 21, 0, tzinfo=timezone.utc)
SCREEN_END = SCREEN_START + timedelta(minutes=10)
SAMPLE_INTERVAL_SECONDS = 300.0
DISTANCE_THRESHOLD_KM = 20_000.0


def _load_catalogue_tles() -> dict[str, tuple[str, str]]:
    payload = json.loads(ORBITAL_CATALOGUE.read_text(encoding="utf-8"))
    objects: dict[str, tuple[str, str]] = {}
    for item in payload["objects"]:
        objects[str(item["object_id"])] = (item["tle"]["line1"], item["tle"]["line2"])
    return objects


def _load_iss_tle() -> tuple[str, str]:
    lines = [line.strip() for line in ISS_TLE_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    return lines[1], lines[2]


class SampleTleSgp4Propagator:
    def __init__(self, tles: dict[str, tuple[str, str]]) -> None:
        self._tles = tles
        self._sgp4 = SGP4Propagator()
        self.calls: list[tuple[str, datetime]] = []

    def state_at(self, object_id: str, when: datetime) -> StateVector:
        self.calls.append((object_id, when))
        line1, line2 = self._tles[object_id]
        state = self._sgp4.propagate(line1, line2, when)
        return StateVector(
            object_id,
            state.timestamp,
            state.position,
            state.velocity,
            state.frame,
        )


class BroadScreenIntegrationTests(unittest.TestCase):
    def test_broad_screen_processes_all_pairs_from_sample_tles(self) -> None:
        tles = _load_catalogue_tles()
        tles["25544"] = _load_iss_tle()
        object_ids = ("00900", "00902", "25544")
        self.assertEqual(len(object_ids), 3)
        self.assertTrue(all(object_id in tles for object_id in object_ids))

        expected_pairs = tuple(combinations(object_ids, 2))
        self.assertEqual(len(expected_pairs), 3)

        propagator = SampleTleSgp4Propagator(tles)
        result = broad_screen(
            propagator,
            object_ids,
            SCREEN_START,
            SCREEN_END,
            sampling_interval_seconds=SAMPLE_INTERVAL_SECONDS,
            distance_threshold_km=DISTANCE_THRESHOLD_KM,
        )

        self.assertIsInstance(result, ScreeningResult)
        self.assertIsInstance(result.candidates, tuple)
        self.assertEqual(result.threshold_km, DISTANCE_THRESHOLD_KM)
        self.assertGreaterEqual(result.sample_count, 2)
        self.assertTrue(all(isinstance(candidate, ScreeningCandidate) for candidate in result.candidates))

        observed_pairs = tuple((candidate.object_a_id, candidate.object_b_id) for candidate in result.candidates)
        self.assertEqual(observed_pairs, expected_pairs)
        self.assertEqual(len(observed_pairs), 3)
        self.assertEqual(len(set(observed_pairs)), 3)

        queried_ids = {object_id for object_id, _when in propagator.calls}
        self.assertEqual(queried_ids, set(object_ids))
        self.assertGreaterEqual(len(propagator.calls), result.sample_count * len(object_ids))

        for candidate in result.candidates:
            self.assertIn(candidate.object_a_id, object_ids)
            self.assertIn(candidate.object_b_id, object_ids)
            self.assertNotEqual(candidate.object_a_id, candidate.object_b_id)
            self.assertTrue(isfinite(candidate.closest_sample_distance_km))
            self.assertGreaterEqual(candidate.closest_sample_distance_km, 0.0)
            self.assertLessEqual(candidate.closest_sample_distance_km, DISTANCE_THRESHOLD_KM)
            self.assertEqual(candidate.closest_sample_time.tzinfo, timezone.utc)
            self.assertLessEqual(candidate.bracket_start, candidate.closest_sample_time)
            self.assertLessEqual(candidate.closest_sample_time, candidate.bracket_end)
            self.assertGreaterEqual(candidate.closest_sample_time, SCREEN_START)
            self.assertLessEqual(candidate.closest_sample_time, SCREEN_END)


if __name__ == "__main__":
    unittest.main()
