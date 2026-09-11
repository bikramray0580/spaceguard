"""What-If maneuver analysis built on the existing orbital pipeline.

The existing project propagates TLEs with SGP4. A hypothetical impulsive burn
cannot be represented by changing a TLE directly, so this service:

1. Uses SGP4 to obtain the real state at the requested burn time.
2. Applies an impulsive delta-v in the local RTN frame.
3. Propagates the modified state forward with a two-body RK4 propagator.
4. Re-screens the maneuvered trajectory against the unchanged participant.
5. Reuses the existing deterministic risk and ML assessment pipeline.

The result is explicitly a hypothetical trajectory, not a replacement TLE.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from math import sqrt

from collision_engine import OrbitalState, Vector3, find_closest_approach
from orbit_engine import PropagationError, TLEValidationError, generate_time_steps, propagate_tle

from ..models.object import SpaceObject
from ..services.collision_service import screen_conjunction
from ..services.ml_service import predict_event_risk
from ..schemas.maneuver import ManeuverRequest


EARTH_MU_KM3_S2 = 398600.4418
MAX_INTEGRATION_STEP_SECONDS = 30.0


class ManeuverError(ValueError):
    """Raised when a What-If maneuver cannot be evaluated."""


@dataclass(frozen=True)
class StateVector:
    """Position in km and velocity in km/s in TEME coordinates."""

    position: tuple[float, float, float]
    velocity: tuple[float, float, float]


def _utc(value: datetime) -> datetime:
    """Return an aware datetime normalized to UTC."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ManeuverError("timestamp must be timezone-aware")
    return value.astimezone(timezone.utc)


def _norm(vector: tuple[float, float, float]) -> float:
    return sqrt(sum(component * component for component in vector))


def _normalize(vector: tuple[float, float, float]) -> tuple[float, float, float]:
    magnitude = _norm(vector)
    if magnitude == 0:
        raise ManeuverError("cannot build a maneuver frame from a zero-length vector")
    return tuple(component / magnitude for component in vector)


def _cross(
    left: tuple[float, float, float],
    right: tuple[float, float, float],
) -> tuple[float, float, float]:
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def _add(
    left: tuple[float, float, float],
    right: tuple[float, float, float],
) -> tuple[float, float, float]:
    return tuple(a + b for a, b in zip(left, right))


def _scale(vector: tuple[float, float, float], factor: float) -> tuple[float, float, float]:
    return tuple(component * factor for component in vector)


def _acceleration(position: tuple[float, float, float]) -> tuple[float, float, float]:
    radius = _norm(position)
    if radius <= 0:
        raise ManeuverError("modified trajectory reached an invalid zero-radius state")
    factor = -EARTH_MU_KM3_S2 / (radius**3)
    return _scale(position, factor)


def _derivative(state: StateVector) -> StateVector:
    return StateVector(position=state.velocity, velocity=_acceleration(state.position))


def _rk4_step(state: StateVector, step_seconds: float) -> StateVector:
    k1 = _derivative(state)
    k2 = _derivative(
        StateVector(
            position=_add(state.position, _scale(k1.position, step_seconds / 2)),
            velocity=_add(state.velocity, _scale(k1.velocity, step_seconds / 2)),
        )
    )
    k3 = _derivative(
        StateVector(
            position=_add(state.position, _scale(k2.position, step_seconds / 2)),
            velocity=_add(state.velocity, _scale(k2.velocity, step_seconds / 2)),
        )
    )
    k4 = _derivative(
        StateVector(
            position=_add(state.position, _scale(k3.position, step_seconds)),
            velocity=_add(state.velocity, _scale(k3.velocity, step_seconds)),
        )
    )

    position_increment = _scale(
        _add(
            _add(k1.position, _scale(_add(k2.position, k3.position), 2)),
            k4.position,
        ),
        step_seconds / 6,
    )
    velocity_increment = _scale(
        _add(
            _add(k1.velocity, _scale(_add(k2.velocity, k3.velocity), 2)),
            k4.velocity,
        ),
        step_seconds / 6,
    )

    return StateVector(
        position=_add(state.position, position_increment),
        velocity=_add(state.velocity, velocity_increment),
    )


def _propagate_two_body(state: StateVector, seconds: float) -> StateVector:
    """Propagate by RK4 using at most MAX_INTEGRATION_STEP_SECONDS per step."""
    if seconds < 0:
        raise ManeuverError("trajectory propagation cannot run backwards")

    current = state
    remaining = float(seconds)

    while remaining > 0:
        step = min(MAX_INTEGRATION_STEP_SECONDS, remaining)
        current = _rk4_step(current, step)
        remaining -= step

    return current


def _rtn_basis(state: StateVector) -> tuple[
    tuple[float, float, float],
    tuple[float, float, float],
    tuple[float, float, float],
]:
    """Return radial, along-track, and normal unit vectors."""
    radial = _normalize(state.position)
    angular_momentum = _cross(state.position, state.velocity)
    normal = _normalize(angular_momentum)
    along_track = _normalize(_cross(normal, radial))
    return radial, along_track, normal


def _maneuver_unit_vector(
    state: StateVector,
    direction: str,
) -> tuple[float, float, float]:
    radial, along_track, normal = _rtn_basis(state)

    vectors = {
        "PROGRADE": along_track,
        "RETROGRADE": _scale(along_track, -1),
        "RADIAL_OUT": radial,
        "RADIAL_IN": _scale(radial, -1),
        "NORMAL": normal,
        "ANTI_NORMAL": _scale(normal, -1),
    }
    try:
        return vectors[direction]
    except KeyError as error:
        raise ManeuverError(f"unsupported maneuver direction: {direction}") from error


def _propagation_to_orbital_states(
    obj: SpaceObject,
    timestamps: list[datetime],
) -> list[OrbitalState]:
    results = propagate_tle(obj.name, obj.line1, obj.line2, timestamps)
    return [OrbitalState.from_propagation_result(result) for result in results]


def _state_from_propagation(result) -> StateVector:
    return StateVector(
        position=(
            result.position.x_km,
            result.position.y_km,
            result.position.z_km,
        ),
        velocity=(
            result.velocity.x_km_s,
            result.velocity.y_km_s,
            result.velocity.z_km_s,
        ),
    )


def _modified_target_states(
    target: SpaceObject,
    timestamps: list[datetime],
    execution_time: datetime,
    delta_v_m_s: float,
    direction: str,
) -> list[OrbitalState]:
    execution_result = propagate_tle(
        target.name,
        target.line1,
        target.line2,
        execution_time,
    )
    pre_burn = _state_from_propagation(execution_result)

    direction_vector = _maneuver_unit_vector(pre_burn, direction)
    delta_v_km_s = delta_v_m_s / 1000.0
    post_burn = StateVector(
        position=pre_burn.position,
        velocity=_add(
            pre_burn.velocity,
            _scale(direction_vector, delta_v_km_s),
        ),
    )

    states: list[OrbitalState] = []

    for timestamp in timestamps:
        timestamp = _utc(timestamp)

        if timestamp < execution_time:
            result = propagate_tle(
                target.name,
                target.line1,
                target.line2,
                timestamp,
            )
            states.append(OrbitalState.from_propagation_result(result))
            continue

        state = _propagate_two_body(
            post_burn,
            (timestamp - execution_time).total_seconds(),
        )
        states.append(
            OrbitalState(
                object_id=target.object_id,
                timestamp=timestamp,
                position_km=Vector3(*state.position),
                velocity_km_s=Vector3(*state.velocity),
                coordinate_frame="TEME",
            )
        )

    return states


def _screen_modified_conjunction(
    object_a: SpaceObject,
    object_b: SpaceObject,
    request: ManeuverRequest,
) -> dict:
    timestamps = generate_time_steps(
        request.start,
        request.end,
        request.step_minutes,
    )

    if request.object_id == object_a.object_id:
        modified_a = _modified_target_states(
            object_a,
            timestamps,
            request.execution_time,
            request.delta_v_m_s,
            request.direction,
        )
        states_a = modified_a
        states_b = _propagation_to_orbital_states(object_b, timestamps)
    else:
        states_a = _propagation_to_orbital_states(object_a, timestamps)
        modified_b = _modified_target_states(
            object_b,
            timestamps,
            request.execution_time,
            request.delta_v_m_s,
            request.direction,
        )
        states_b = modified_b

    event = find_closest_approach(
        states_a,
        states_b,
        analysis_time=request.start,
    )

    data = event.to_dict()
    data["object_a"] = object_a.object_id
    data["object_b"] = object_b.object_id
    data["ml_prediction"] = predict_event_risk(
        event,
        states_a,
        states_b,
        analysis_time=request.start,
    )
    return data


def _validate_execution_against_before(
    before: dict,
    request: ManeuverRequest,
) -> None:
    tca = before["time_of_closest_approach"]

    if isinstance(tca, str):
        tca_dt = datetime.fromisoformat(tca.replace("Z", "+00:00"))
    else:
        tca_dt = tca

    if request.execution_time >= tca_dt:
        raise ManeuverError(
            "execution_time must be earlier than the current closest-approach time"
        )


def run_maneuver(
    object_a: SpaceObject,
    object_b: SpaceObject,
    request: ManeuverRequest,
) -> dict:
    """Evaluate a real conjunction before and after a hypothetical impulse."""
    if request.object_a != object_a.object_id or request.object_b != object_b.object_id:
        raise ManeuverError("request object IDs do not match the loaded objects")

    before = screen_conjunction(
        object_a,
        object_b,
        request.start,
        request.end,
        request.step_minutes,
    )

    _validate_execution_against_before(before, request)

    after = _screen_modified_conjunction(
        object_a,
        object_b,
        request,
    )

    before_level = str(before["risk_level"]).upper()
    after_level = str(after["risk_level"]).upper()

    risk_change = _build_risk_change(before, after, before_level, after_level)

    return {
        "status": "complete",
        "maneuver": {
            "object_id": request.object_id,
            "delta_v_m_s": request.delta_v_m_s,
            "direction": request.direction,
            "execution_time": _utc(request.execution_time),
            "state_frame": "TEME",
            "maneuver_frame": "RTN",
        },
        "before": before,
        "after": after,
        "risk_change": risk_change,
    }


def _risk_rank(level: str) -> int:
    """Return a severity rank where HIGH is most severe."""
    return {
        "LOW": 0,
        "MEDIUM": 1,
        "HIGH": 2,
    }.get(level, -1)


def _build_risk_change(
    before: dict,
    after: dict,
    before_level: str,
    after_level: str,
) -> dict:
    """Build an explicit, correctly oriented risk delta summary."""
    rank_before = _risk_rank(before_level)
    rank_after = _risk_rank(after_level)

    if rank_before < 0 or rank_after < 0:
        raise ManeuverError(
            f"unsupported risk level comparison: {before_level!r} -> {after_level!r}"
        )

    improved = rank_after < rank_before
    worsened = rank_after > rank_before

    return {
        "before": before_level,
        "after": after_level,
        "improved": improved,
        "worsened": worsened,
        "unchanged": not improved and not worsened,
        "miss_distance_delta_km": (
            float(after["miss_distance_km"]) - float(before["miss_distance_km"])
        ),
        "relative_velocity_delta_km_s": (
            float(after["relative_velocity_km_s"])
            - float(before["relative_velocity_km_s"])
        ),
    }
