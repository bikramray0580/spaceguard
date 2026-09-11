"""Tests for live CelesTrak fetching, validation, and SQLite insertion."""

from __future__ import annotations

import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from requests.exceptions import ConnectTimeout

from data_ingestion.celestrak.client import CelesTrakFetchError, fetch_celestrak_data
from data_ingestion.pipeline import run_pipeline
from data_ingestion.validate import validate_records
from storage.database import get_connection
from storage.repositories import insert_gp_records


SAMPLE_GP = [
    {
        "OBJECT_NAME": "ISS (ZARYA)",
        "OBJECT_ID": "1998-067A",
        "NORAD_CAT_ID": 25544,
        "EPOCH": "2026-09-11T04:13:00.214752",
        "MEAN_MOTION": 15.49076359,
        "ECCENTRICITY": 0.00049932,
        "INCLINATION": 51.6305,
    }
]


class _FakeResponse:
    def __init__(self, status_code: int, text: str) -> None:
        self.status_code = status_code
        self.text = text


class TestCelesTrakFetcher(unittest.TestCase):
    def test_live_success_returns_gp_records(self) -> None:
        fake = _FakeResponse(200, json.dumps(SAMPLE_GP))
        with patch("data_ingestion.celestrak.client.requests.get", return_value=fake):
            records = fetch_celestrak_data()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["NORAD_CAT_ID"], 25544)
        self.assertNotIn("SOURCE_NOTE", records[0])

    def test_timeout_falls_back_to_local_sample(self) -> None:
        with patch(
            "data_ingestion.celestrak.client.requests.get",
            side_effect=ConnectTimeout("Connection timed out. (connect timeout=10)"),
        ), patch("data_ingestion.celestrak.client.time.sleep"):
            records = fetch_celestrak_data()
        self.assertGreaterEqual(len(records), 2)
        self.assertEqual(records[0]["SOURCE"], "local_fallback")
        self.assertIn("development fallback", records[0]["SOURCE_NOTE"])

    def test_http_403_does_not_retry_and_falls_back(self) -> None:
        fake = _FakeResponse(403, "GP data has not updated since your last successful download")
        with patch("data_ingestion.celestrak.client.requests.get", return_value=fake) as mocked:
            records = fetch_celestrak_data()
        self.assertEqual(mocked.call_count, 1)
        self.assertEqual(records[0]["SOURCE"], "local_fallback")

    def test_empty_json_falls_back(self) -> None:
        fake = _FakeResponse(200, "[]")
        with patch("data_ingestion.celestrak.client.requests.get", return_value=fake):
            records = fetch_celestrak_data()
        self.assertEqual(records[0]["SOURCE"], "local_fallback")

    def test_malformed_json_falls_back(self) -> None:
        fake = _FakeResponse(200, "<html>blocked</html>")
        with patch("data_ingestion.celestrak.client.requests.get", return_value=fake):
            records = fetch_celestrak_data()
        self.assertEqual(records[0]["SOURCE"], "local_fallback")

    def test_parse_error_is_visible(self) -> None:
        from data_ingestion.celestrak.client import _parse_gp_payload

        with self.assertRaises(CelesTrakFetchError):
            _parse_gp_payload("")


class TestPipelinePersistence(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "spaceguard.db"
        self.env = patch.dict(os.environ, {"SPACEGUARD_DB_PATH": str(self.db_path)})
        self.env.start()

    def tearDown(self) -> None:
        self.env.stop()
        self.tmp.cleanup()

    def test_pipeline_inserts_valid_gp_records(self) -> None:
        fake = _FakeResponse(200, json.dumps(SAMPLE_GP + [{"OBJECT_NAME": "BAD"}]))
        with patch("data_ingestion.celestrak.client.requests.get", return_value=fake):
            saved = run_pipeline()
        self.assertEqual(len(saved), 1)
        connection = sqlite3.connect(self.db_path)
        try:
            rows = connection.execute(
                "SELECT norad_cat_id, source, source_note FROM gp_records"
            ).fetchall()
        finally:
            connection.close()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0], 25544)
        self.assertEqual(rows[0][1], "celestrak")
        self.assertIsNone(rows[0][2])

    def test_fallback_records_are_labeled_in_database(self) -> None:
        with patch(
            "data_ingestion.celestrak.client.requests.get",
            side_effect=ConnectTimeout("Connection timed out."),
        ), patch("data_ingestion.celestrak.client.time.sleep"):
            saved = run_pipeline()
        self.assertGreaterEqual(len(saved), 2)
        connection = sqlite3.connect(self.db_path)
        try:
            rows = connection.execute(
                "SELECT source, source_note FROM gp_records"
            ).fetchall()
        finally:
            connection.close()
        self.assertGreaterEqual(len(rows), 2)
        for source, note in rows:
            self.assertEqual(source, "local_fallback")
            self.assertIn("development fallback", note)


class TestStorageLayer(unittest.TestCase):
    def test_insert_gp_records_writes_json_not_tle_lines(self) -> None:
        db_path = Path(tempfile.mkdtemp()) / "test.db"
        connection = get_connection(db_path)
        try:
            valid, skipped = validate_records(SAMPLE_GP)
            self.assertEqual(skipped, 0)
            written = insert_gp_records(valid, connection)
            self.assertEqual(written, 1)
            row = connection.execute("SELECT * FROM gp_records").fetchone()
            self.assertEqual(row["norad_cat_id"], 25544)
            payload = json.loads(row["raw_json"])
            self.assertIn("MEAN_MOTION", payload)
            self.assertNotIn("line1", payload)
            self.assertNotIn("TLE_LINE1", payload)
        finally:
            connection.close()

    def test_validate_records_normalizes_numeric_strings(self) -> None:
        raw = [
            {
                "OBJECT_NAME": "ISS (ZARYA)",
                "NORAD_CAT_ID": "25544",
                "EPOCH": "2026-09-11T04:13:00.214752",
                "MEAN_MOTION": "15.49076359",
                "ECCENTRICITY": "0.00049932",
                "INCLINATION": "51.6305",
            }
        ]
        valid, skipped = validate_records(raw)
        self.assertEqual(skipped, 0)
        self.assertEqual(valid[0]["NORAD_CAT_ID"], 25544)
        self.assertEqual(valid[0]["MEAN_MOTION"], 15.49076359)
        self.assertEqual(valid[0]["INCLINATION"], 51.6305)

    def test_validate_records_skips_bad_ranges_and_dates(self) -> None:
        invalid_records = [
            {**SAMPLE_GP[0], "NORAD_CAT_ID": 0},
            {**SAMPLE_GP[0], "EPOCH": "not-a-date"},
            {**SAMPLE_GP[0], "MEAN_MOTION": 0},
            {**SAMPLE_GP[0], "ECCENTRICITY": 1.5},
            {**SAMPLE_GP[0], "INCLINATION": 181},
        ]
        valid, skipped = validate_records(invalid_records)
        self.assertEqual(valid, [])
        self.assertEqual(skipped, len(invalid_records))


if __name__ == "__main__":
    unittest.main()
