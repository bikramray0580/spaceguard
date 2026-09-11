from datetime import timezone

import pytest
from pydantic import ValidationError

from backend.schemas.maneuver import ManeuverRequest


def valid_payload():
    return {
        "object_a": "00900",
        "object_b": "00902",
        "object_id": "00900",
        "start": "2026-09-11T00:00:00+05:30",
        "end": "2026-09-11T02:00:00+05:30",
        "step_minutes": 5,
        "delta_v_m_s": 12.5,
        "direction": "PROGRADE",
        "execution_time": "2026-09-11T00:30:00+05:30",
    }


def test_timestamps_are_normalized_to_utc():
    request = ManeuverRequest.model_validate(valid_payload())

    assert request.start.tzinfo == timezone.utc
    assert request.end.tzinfo == timezone.utc
    assert request.execution_time.tzinfo == timezone.utc
    assert request.execution_time.isoformat() == "2026-09-10T19:00:00+00:00"


def test_target_must_belong_to_conjunction_pair():
    payload = valid_payload()
    payload["object_id"] = "NOT_IN_PAIR"

    with pytest.raises(ValidationError, match="object_id must be one of object_a or object_b"):
        ManeuverRequest.model_validate(payload)


def test_execution_time_must_be_before_window_end():
    payload = valid_payload()
    payload["execution_time"] = "2026-09-11T03:00:00+05:30"

    with pytest.raises(ValidationError, match="execution_time must be within the screening window"):
        ManeuverRequest.model_validate(payload)
