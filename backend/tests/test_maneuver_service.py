from types import SimpleNamespace

from backend.services import maneuver_service
from backend.schemas.maneuver import ManeuverRequest


def _request():
    return ManeuverRequest.model_validate(
        {
            "object_a": "A",
            "object_b": "B",
            "object_id": "A",
            "start": "2026-09-11T00:00:00Z",
            "end": "2026-09-11T02:00:00Z",
            "step_minutes": 5,
            "delta_v_m_s": 10,
            "direction": "PROGRADE",
            "execution_time": "2026-09-11T00:30:00Z",
        }
    )


def _conjunction(distance, velocity, level):
    return {
        "object_a": "A",
        "object_b": "B",
        "time_of_closest_approach": "2026-09-11T01:00:00Z",
        "miss_distance_km": distance,
        "relative_velocity_km_s": velocity,
        "risk_level": level,
        "risk_reason": "test",
        "risk_explanation": {
            "summary": "test",
            "factors": [],
            "primary_risk_drivers": [],
        },
        "ml_prediction": {
            "risk_probability": 0.5,
            "risk_score": 50,
            "risk_category": level,
        },
    }


def test_risk_change_marks_high_to_low_as_improved():
    result = maneuver_service._build_risk_change(
        _conjunction(100, 7, "HIGH"),
        _conjunction(500, 6, "LOW"),
        "HIGH",
        "LOW",
    )

    assert result["improved"] is True
    assert result["worsened"] is False
    assert result["unchanged"] is False
    assert result["miss_distance_delta_km"] == 400
    assert result["relative_velocity_delta_km_s"] == -1


def test_risk_change_marks_low_to_high_as_worsened():
    result = maneuver_service._build_risk_change(
        _conjunction(500, 6, "LOW"),
        _conjunction(100, 7, "HIGH"),
        "LOW",
        "HIGH",
    )

    assert result["improved"] is False
    assert result["worsened"] is True
    assert result["unchanged"] is False


def test_run_maneuver_returns_explicit_frame_metadata(monkeypatch):
    before = _conjunction(100, 7, "HIGH")
    after = _conjunction(500, 6, "LOW")

    monkeypatch.setattr(maneuver_service, "screen_conjunction", lambda *args: before)
    monkeypatch.setattr(maneuver_service, "_validate_execution_against_before", lambda *args: None)
    monkeypatch.setattr(maneuver_service, "_screen_modified_conjunction", lambda *args: after)

    object_a = SimpleNamespace(object_id="A")
    object_b = SimpleNamespace(object_id="B")

    result = maneuver_service.run_maneuver(object_a, object_b, _request())

    assert result["maneuver"]["state_frame"] == "TEME"
    assert result["maneuver"]["maneuver_frame"] == "RTN"
    assert result["risk_change"]["improved"] is True
