"""Tests for orbital and conjunction data ingestion."""

from __future__ import annotations

import unittest
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from data_ingestion.cdm.client import load_cdms
from data_ingestion.celestrak.client import load_celestrak_tles
from data_ingestion.models import QUALITY_COMPLETE, QUALITY_PARTIAL, NormalizedRecord
from data_ingestion.normalizer.normalize import ingest_path, ingest_text
from data_ingestion.parsers.cdm import parse_cdm_text
from data_ingestion.parsers.tle import parse_tle_text
from data_ingestion.spacetrack.client import load_spacetrack_tles

ISS_TLE = """ISS (ZARYA)
1 25544U 98067A   26001.50000000  .00016717  00000-0  10270-3 0  9001
2 25544  51.6392 341.0845 0006273  86.2769  23.7481 15.49903450260619
"""

CDM_KVN = """CCSDS_CDM_VERS = 1.0
CREATION_DATE = 2026-01-01T00:00:00.000
ORIGINATOR = SPACE-TRACK
MESSAGE_ID = CDM_2026_0001
TCA = 2026-01-02T12:00:00.000
MISS_DISTANCE = 250.0 [m]
RELATIVE_SPEED = 10500.0 [m/s]
OBJECT = OBJECT1
OBJECT_DESIGNATOR = 25544
OBJECT_NAME = ISS (ZARYA)
CR_R = 12.5
OBJECT = OBJECT2
OBJECT_DESIGNATOR = 43013
OBJECT_NAME = DEBRIS
CT_T = 8.1
"""

CDM_JSON = """
{
  "MESSAGE_ID": "CDM_JSON_1",
  "TCA": "2026-01-03T08:15:00Z",
  "SAT_1_ID": "25544",
  "SAT_1_NAME": "ISS (ZARYA)",
  "SAT_2_ID": "99999",
  "SAT_2_NAME": "UNKNOWN DEBRIS",
  "MISS_DISTANCE": 1200.0,
  "RELATIVE_SPEED": 8500.0
}
"""


class TestTLEParser(unittest.TestCase):
    def test_parses_named_tle_pair(self) -> None:
        records = parse_tle_text(ISS_TLE, source="celestrak")
        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record.norad_id, 25544)
        self.assertEqual(record.name, "ISS (ZARYA)")
        self.assertEqual(record.provenance.source, "celestrak")
        self.assertIn(record.quality.status, {QUALITY_COMPLETE, "DEGRADED"})
        self.assertAlmostEqual(record.inclination_deg, 51.6392)
        self.assertAlmostEqual(record.eccentricity, 0.0006273)
        self.assertEqual(record.epoch.year, 2026)

    def test_rejects_checksum_mismatch(self) -> None:
        bad = ISS_TLE.replace("9001", "9000")
        records = parse_tle_text(bad, source="local")
        self.assertEqual(records[0].quality.status, "INVALID")
        self.assertTrue(any("checksum" in reason for reason in records[0].quality.reasons))

    def test_rejects_empty_text(self) -> None:
        with self.assertRaises(ValueError):
            parse_tle_text("   ")


class TestCDMParser(unittest.TestCase):
    def test_parses_kvn_cdm(self) -> None:
        records = parse_cdm_text(CDM_KVN, source="cdm")
        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record.message_id, "CDM_2026_0001")
        self.assertEqual(record.object1_id, "25544")
        self.assertEqual(record.object2_id, "43013")
        self.assertEqual(record.miss_distance_m, 250.0)
        self.assertTrue(record.has_covariance)
        self.assertEqual(record.quality.status, QUALITY_PARTIAL)
        self.assertTrue(any("collision probability" in reason for reason in record.quality.reasons))

    def test_parses_json_cdm_without_covariance(self) -> None:
        records = parse_cdm_text(CDM_JSON, source="cdm")
        record = records[0]
        self.assertEqual(record.object1_id, "25544")
        self.assertEqual(record.object2_id, "99999")
        self.assertFalse(record.has_covariance)
        self.assertIsNone(record.collision_probability)
        self.assertEqual(record.quality.status, QUALITY_PARTIAL)
        self.assertTrue(
            any("covariance is unavailable" in reason for reason in record.quality.reasons)
        )


class TestNormalizer(unittest.TestCase):
    def test_tle_normalizes_to_common_schema(self) -> None:
        records = ingest_text(ISS_TLE, source="celestrak")
        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertIsInstance(record, NormalizedRecord)
        self.assertEqual(record.record_type, "orbital_element")
        self.assertEqual(record.object_id, "25544")
        self.assertEqual(record.frame, "TEME")
        self.assertEqual(record.data["format"], "TLE")
        self.assertEqual(record.provenance.source, "celestrak")
        self.assertIsInstance(record.provenance.ingested_at, datetime)
        self.assertIn(record.quality.status, {QUALITY_COMPLETE, "DEGRADED"})

    def test_cdm_normalizes_without_presenting_heuristic_pc(self) -> None:
        records = ingest_text(CDM_JSON, source="cdm", format_hint="cdm")
        record = records[0]
        self.assertEqual(record.record_type, "conjunction")
        self.assertEqual(record.object_id, "25544")
        self.assertFalse(record.data["pc_is_authoritative"])
        self.assertIsNone(record.data["collision_probability"])
        self.assertEqual(record.quality.status, QUALITY_PARTIAL)

    def test_ingest_path_reads_tle_file(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.tle"
            path.write_text(ISS_TLE, encoding="utf-8")
            records = ingest_path(path, source="celestrak")
        self.assertEqual(records[0].object_id, "25544")
        self.assertEqual(records[0].provenance.raw_uri, str(path))


class TestSourceLoaders(unittest.TestCase):
    def test_celestrak_loader(self) -> None:
        records = load_celestrak_tles(ISS_TLE)
        self.assertEqual(records[0].provenance.source, "celestrak")
        self.assertEqual(records[0].provenance.originator, "CelesTrak")

    def test_spacetrack_loader(self) -> None:
        records = load_spacetrack_tles(ISS_TLE)
        self.assertEqual(records[0].provenance.source, "spacetrack")
        self.assertEqual(records[0].provenance.originator, "Space-Track")

    def test_cdm_loader(self) -> None:
        records = load_cdms(CDM_KVN)
        self.assertEqual(records[0].record_type, "conjunction")
        self.assertEqual(records[0].data["message_id"], "CDM_2026_0001")


class TestProvenanceContract(unittest.TestCase):
    def test_normalized_records_carry_required_metadata(self) -> None:
        records = ingest_text(ISS_TLE, source="celestrak") + ingest_text(
            CDM_KVN, source="cdm", format_hint="cdm"
        )
        for record in records:
            self.assertTrue(record.provenance.source)
            self.assertIsInstance(record.provenance.ingested_at, datetime)
            self.assertEqual(record.provenance.ingested_at.tzinfo, timezone.utc)
            self.assertTrue(record.quality.status)
            self.assertTrue(record.object_id)
            self.assertTrue(record.epoch)


if __name__ == "__main__":
    unittest.main()
