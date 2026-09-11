"""Deterministic integration-layer tests with the propagation boundary mocked."""

from datetime import datetime, timezone
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from collision_engine import OrbitalState
from integration import generate_shared_timestamps, load_orbital_data, run_pipeline
from orbit_engine.models import Position, PropagationResult, Velocity


FETCHED_AT = "2026-08-23T16:27:57Z"
START = datetime(2026, 8, 23, 16, 30, tzinfo=timezone.utc)


def tle_record(object_id: str, name: str) -> dict[str, object]:
    return {
        "object_id": object_id,
        "name": name,
        "tle": {
            "line1": f"1 {object_id}U 24001A   26235.00000000  .00000000  00000+0  00000+0 0  9991",
            "line2": f"2 {object_id}  90.0000  10.0000 0010000  20.0000  30.0000 13.00000000    01",
        },
        "epoch": "2026-08-23T00:00:00Z",
    }


def write_snapshot(directory: str, objects: list[dict[str, object]]) -> Path:
    path = Path(directory) / "orbital_data.json"
    path.write_text(json.dumps({"source": "CelesTrak", "fetched_at": FETCHED_AT, "objects": objects}), encoding="utf-8")
    return path


def fake_propagate(name: str, line1: str, _line2: str, timestamps: tuple[datetime, ...]):
    """Return predictable Person B-shaped results while retaining the mock boundary."""
    satnum = str(int(line1[2:7]))
    offset = float(int(satnum) % 10)
    return [
        PropagationResult(
            object_id=satnum,
            object_name=name,
            timestamp=timestamp,
            position=Position(offset + index, 7000.0, 0.0),
            velocity=Velocity(0.01, 7.5, 0.0),
        )
        for index, timestamp in enumerate(timestamps)
    ]


class PipelineTests(unittest.TestCase):
    def test_loads_valid_orbital_json(self) -> None:
        with TemporaryDirectory() as directory:
            path = write_snapshot(directory, [tle_record("00900", "CALSPHERE 1")])
            loaded = load_orbital_data(path)
        self.assertEqual(loaded.source, "CelesTrak")
        self.assertEqual(loaded.objects[0].object_id, "00900")
        self.assertEqual(loaded.objects[0].line1[2:7], "00900")

    def test_missing_tle_is_rejected(self) -> None:
        invalid = tle_record("00900", "CALSPHERE 1")
        del invalid["tle"]
        with TemporaryDirectory() as directory:
            path = write_snapshot(directory, [invalid])
            with self.assertRaisesRegex(ValueError, "tle must be an object"):
                load_orbital_data(path)

    def test_shared_timestamps_are_aware_and_inclusive(self) -> None:
        timestamps = generate_shared_timestamps(START, duration_minutes=10, step_seconds=300)
        self.assertEqual(len(timestamps), 3)
        self.assertTrue(all(timestamp.tzinfo is timezone.utc for timestamp in timestamps))

    @patch("integration.pipeline.propagate_tle", side_effect=fake_propagate)
    def test_pipeline_uses_one_grid_converts_states_and_preserves_ids(self, mocked_propagate) -> None:
        with TemporaryDirectory() as directory:
            path = write_snapshot(
                directory,
                [tle_record("00900", "CALSPHERE 1"), tle_record("00902", "CALSPHERE 2"), tle_record("01361", "LCS 1")],
            )
            run = run_pipeline(path, START, duration_minutes=10, step_seconds=300, max_objects=3)

        self.assertEqual(run.object_ids, ("00900", "00902", "01361"))
        self.assertEqual(len(run.propagated_by_object), 3)
        self.assertEqual(run.pair_count, 3)
        self.assertEqual(len(run.conjunctions), 3)
        self.assertEqual(mocked_propagate.call_count, 3)
        self.assertTrue(all(call.args[3] == run.timestamps for call in mocked_propagate.call_args_list))
        self.assertEqual(run.propagated_by_object["00900"][0].object_id, "00900")
        self.assertIsInstance(run.states_by_object["00900"][0], OrbitalState)
        self.assertEqual(run.states_by_object["00900"][0].object_id, "00900")
        self.assertTrue(all(event.object_a != event.object_b for event in run.conjunctions))

    @patch("integration.pipeline.propagate_tle", side_effect=fake_propagate)
    def test_selects_real_source_ids_without_hardcoded_satellites(self, _mocked_propagate) -> None:
        with TemporaryDirectory() as directory:
            path = write_snapshot(directory, [tle_record("00900", "A"), tle_record("00902", "B"), tle_record("01361", "C")])
            run = run_pipeline(path, START, 5, 300, object_ids=["01361", "00900"])
        self.assertEqual(run.object_ids, ("01361", "00900"))
        self.assertEqual(run.pair_count, 1)


if __name__ == "__main__":
    unittest.main()
