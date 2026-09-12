from __future__ import annotations

import json
import unittest
from datetime import datetime, timedelta, timezone
from itertools import combinations
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.main import app
from backend.models.object import SpaceObject
from backend.services.conjunction_service import screen_catalogue
from conjunction.screening import ScreeningCandidate, ScreeningResult

REPO_ROOT = Path(__file__).resolve().parents[2]
ORBITAL_CATALOGUE = REPO_ROOT / "data" / "orbital_data.json"
ISS_TLE_PATH = REPO_ROOT / "shared" / "data" / "sample" / "iss.tle"

SCREEN_START = datetime(2026, 8, 25, 21, 0, tzinfo=timezone.utc)
SCREEN_END = SCREEN_START + timedelta(minutes=10)
STEP_MINUTES = 5.0
DISTANCE_THRESHOLD_KM = 20_000.0


def _load_catalogue_objects() -> list[SpaceObject]:
    payload = json.loads(ORBITAL_CATALOGUE.read_text(encoding="utf-8"))
    return [SpaceObject.from_json(item) for item in payload["objects"]]


def _load_iss_object() -> SpaceObject:
    lines = [line.strip() for line in ISS_TLE_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    return SpaceObject(
        object_id="25544",
        name="ISS",
        line1=lines[1],
        line2=lines[2],
        epoch="2026-08-25T21:00:00Z",
    )


def _three_object_catalogue() -> tuple[SpaceObject, ...]:
    objects = _load_catalogue_objects()
    objects.append(_load_iss_object())
    return tuple(objects)


class CatalogueScreenBackendTests(unittest.TestCase):
    def test_screen_catalogue_returns_all_pairs_from_sample_objects(self) -> None:
        catalogue = _three_object_catalogue()
        object_ids = tuple(obj.object_id for obj in catalogue)
        self.assertEqual(object_ids, ("00900", "00902", "25544"))
        expected_pairs = tuple(combinations(object_ids, 2))
        self.assertEqual(len(expected_pairs), 3)

        with patch("backend.services.conjunction_service.list_objects", return_value=catalogue):
            selected_ids, catalogue_count, pair_count, result = screen_catalogue(
                SCREEN_START,
                SCREEN_END,
                object_ids=list(object_ids),
                step_minutes=STEP_MINUTES,
                distance_threshold_km=DISTANCE_THRESHOLD_KM,
            )

        self.assertEqual(selected_ids, object_ids)
        self.assertEqual(catalogue_count, 3)
        self.assertEqual(pair_count, 3)
        self.assertIsInstance(result, ScreeningResult)
        self.assertEqual(result.threshold_km, DISTANCE_THRESHOLD_KM)
        self.assertGreaterEqual(result.sample_count, 2)
        self.assertEqual(len(result.candidates), 3)
        self.assertTrue(all(isinstance(candidate, ScreeningCandidate) for candidate in result.candidates))

        observed_pairs = tuple((candidate.object_a_id, candidate.object_b_id) for candidate in result.candidates)
        self.assertEqual(observed_pairs, expected_pairs)

        for candidate in result.candidates:
            self.assertIn(candidate.object_a_id, object_ids)
            self.assertIn(candidate.object_b_id, object_ids)
            self.assertNotEqual(candidate.object_a_id, candidate.object_b_id)
            self.assertLessEqual(candidate.closest_sample_distance_km, DISTANCE_THRESHOLD_KM)
            self.assertGreaterEqual(candidate.closest_sample_time, SCREEN_START)
            self.assertLessEqual(candidate.closest_sample_time, SCREEN_END)

    def test_screen_catalogue_uses_available_catalogue_when_ids_omitted(self) -> None:
        catalogue = _three_object_catalogue()

        with patch("backend.services.conjunction_service.list_objects", return_value=catalogue):
            selected_ids, catalogue_count, pair_count, result = screen_catalogue(
                SCREEN_START,
                SCREEN_END,
                object_ids=None,
                step_minutes=STEP_MINUTES,
                distance_threshold_km=DISTANCE_THRESHOLD_KM,
            )

        self.assertEqual(selected_ids, ("00900", "00902", "25544"))
        self.assertEqual(catalogue_count, 3)
        self.assertEqual(pair_count, 3)
        self.assertEqual(len(result.candidates), 3)

    def test_screen_catalogue_rejects_unknown_object(self) -> None:
        catalogue = _three_object_catalogue()

        with patch("backend.services.conjunction_service.list_objects", return_value=catalogue):
            with self.assertRaises(KeyError):
                screen_catalogue(
                    SCREEN_START,
                    SCREEN_END,
                    object_ids=["00900", "missing"],
                    step_minutes=STEP_MINUTES,
                    distance_threshold_km=DISTANCE_THRESHOLD_KM,
                )


class CatalogueScreenApiTests(unittest.TestCase):
    def test_catalogue_screen_endpoint_returns_candidate_pairs(self) -> None:
        catalogue = _three_object_catalogue()
        payload = {
            "object_ids": ["00900", "00902", "25544"],
            "start": SCREEN_START.isoformat(),
            "end": SCREEN_END.isoformat(),
            "step_minutes": STEP_MINUTES,
            "distance_threshold_km": DISTANCE_THRESHOLD_KM,
        }

        with patch("backend.services.conjunction_service.list_objects", return_value=catalogue):
            response = TestClient(app).post("/api/conjunctions/catalogue-screen", json=payload)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["object_ids"], ["00900", "00902", "25544"])
        self.assertEqual(body["object_count"], 3)
        self.assertEqual(body["pair_count"], 3)
        self.assertEqual(body["candidate_count"], 3)
        self.assertEqual(len(body["candidates"]), 3)
        self.assertEqual(
            [(item["object_a"], item["object_b"]) for item in body["candidates"]],
            [("00900", "00902"), ("00900", "25544"), ("00902", "25544")],
        )

    def test_pairwise_screen_endpoint_remains_available(self) -> None:
        catalogue = _three_object_catalogue()
        payload = {
            "object_a": "00900",
            "object_b": "00902",
            "start": SCREEN_START.isoformat(),
            "end": SCREEN_END.isoformat(),
            "step_minutes": STEP_MINUTES,
        }

        with patch("backend.services.conjunction_service.list_objects", return_value=catalogue):
            response = TestClient(app).post("/api/conjunctions/screen", json=payload)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["object_a"], "00900")
        self.assertEqual(body["object_b"], "00902")
        self.assertIn("time_of_closest_approach", body)
        self.assertIn("miss_distance_km", body)
        self.assertIn("risk_level", body)


if __name__ == "__main__":
    unittest.main()
