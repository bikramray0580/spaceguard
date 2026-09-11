"""Prototype What-If maneuver propagation on top of the main pipeline.

The maneuver is applied in the target object's local RTN frame at the requested
execution epoch. Before the burn the target follows SGP4; after the burn its
state is propagated with a deterministic two-body RK4 model. The result is then
fed back through the existing conjunction and risk layers.

This is decision-support prototype physics, not flight-dynamics-grade maneuver
planning. No covariance or Probability of Collision is fabricated.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from math import sqrt

from conjunction import calculate_conjunction
from conjunction.models import StateVector
from orbit_propagation.sgp4.propagator import SGP4Propagator
from risk import assess_upstream_risk

from .data_service import find_object, list_objects

MU_EARTH_KM3_S2 = 398600.4418
DIRECTIONS = frozenset({
    "PROGRADE", "RETROGRADE", "RADIAL_OUT", "RADIAL_IN", "NORMAL", "ANTI_NORMAL",
})


def _norm(v):
    return sqrt(sum(x * x for x in v))


def _add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def _scale(a, s):
    return tuple(x * s for x in a)


def _cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _unit(v):
    n = _norm(v)
    if n <= 0:
        raise ValueError("cannot normalize a zero vector")
    return _scale(v, 1.0 / n)


def _rtn_delta_v(position, velocity, delta_v_m_s, direction):
    r_hat = _unit(position)
    h_hat = _unit(_cross(position, velocity))
    t_hat = _unit(_cross(h_hat, r_hat))
    basis = {
        "PROGRADE": t_hat,
        "RETROGRADE": _scale(t_hat, -1.0),
        "RADIAL_OUT": r_hat,
        "RADIAL_IN": _scale(r_hat, -1.0),
        "NORMAL": h_hat,
        "ANTI_NORMAL": _scale(h_hat, -1.0),
    }
    return _scale(basis[direction], float(delta_v_m_s) / 1000.0)


def _derivative(state):
    r = state[:3]
    v = state[3:]
    radius = _norm(r)
    if radius <= 0:
        raise ValueError("invalid propagated radius")
    acceleration = _scale(r, -MU_EARTH_KM3_S2 / radius**3)
    return (*v, *acceleration)


def _rk4_step(state, dt_seconds):
    k1 = _derivative(state)
    k2 = _derivative(_add(state, _scale(k1, dt_seconds / 2.0)))
    k3 = _derivative(_add(state, _scale(k2, dt_seconds / 2.0)))
    k4 = _derivative(_add(state, _scale(k3, dt_seconds)))
    return _add(state, _scale(_add(_add(k1, _scale(_add(k2, k3), 2.0)), k4), dt_seconds / 6.0))


def _two_body_propagate(position, velocity, seconds):
    state = (*position, *velocity)
    remaining = float(seconds)
    if remaining == 0:
        return position, velocity
    max_step = 30.0
    direction = 1.0 if remaining > 0 else -1.0
    while abs(remaining) > 1e-9:
        step = direction * min(max_step, abs(remaining))
        state = _rk4_step(state, step)
        remaining -= step
    return state[:3], state[3:]


class ManeuverPropagator:
    """Hybrid propagator: SGP4 until burn, two-body after burn for target."""

    def __init__(self, objects, target_id, execution_time, delta_v_m_s, direction):
        self.objects = objects
        self.target_id = target_id
        self.execution_time = execution_time
        self.delta_v_m_s = delta_v_m_s
        self.direction = direction
        self.sgp4 = SGP4Propagator()
        target = objects[target_id]
        burn = self.sgp4.propagate(target.line1, target.line2, execution_time)
        dv = _rtn_delta_v(burn.position, burn.velocity, delta_v_m_s, direction)
        self.burn_position = burn.position
        self.burn_velocity = _add(burn.velocity, dv)

    def state_at(self, object_id: str, when: datetime) -> StateVector:
        obj = self.objects[object_id]
        when = when.astimezone(timezone.utc) if when.tzinfo else when.replace(tzinfo=timezone.utc)
        if object_id != self.target_id or when <= self.execution_time:
            state = self.sgp4.propagate(obj.line1, obj.line2, when)
            return StateVector(object_id, state.timestamp, state.position, state.velocity, state.frame)

        position, velocity = _two_body_propagate(
            self.burn_position,
            self.burn_velocity,
            (when - self.execution_time).total_seconds(),
        )
        return StateVector(object_id, when, position, velocity, "TEME")


def _event_payload(result, assessment):
    return {
        "object_a": result.object_a_id,
        "object_b": result.object_b_id,
        "time_of_closest_approach": result.tca,
        "miss_distance_km": result.miss_distance_km,
        "relative_velocity_km_s": result.relative_speed_km_s,
        "risk_level": assessment.risk_level.value,
        "risk_reason": assessment.explanation,
        "ml_prediction": None,
        "trend": assessment.trend.value,
        "recommended_action": assessment.recommended_action.value,
        "confidence": assessment.confidence.value,
        "pc": assessment.pc,
        "pc_status": assessment.pc_status.value,
        "covariance_status": assessment.quality_status,
        "provenance": dict(assessment.provenance),
    }


def evaluate_maneuver(
    object_a: str,
    object_b: str,
    object_id: str,
    start: datetime,
    end: datetime,
    delta_v_m_s: float,
    direction: str,
    execution_time: datetime,
):
    objects = {obj.object_id: obj for obj in list_objects()}
    for object_value in (object_a, object_b, object_id):
        if object_value not in objects:
            raise KeyError(f"object {object_value!r} was not found")
    if object_a == object_b:
        raise ValueError("object_a and object_b must be different")
    if object_id not in (object_a, object_b):
        raise ValueError("object_id must be one of the conjunction participants")
    if direction not in DIRECTIONS:
        raise ValueError(f"unsupported maneuver direction: {direction}")
    if delta_v_m_s <= 0 or delta_v_m_s > 1000:
        raise ValueError("delta_v_m_s must be greater than 0 and no more than 1000 m/s")
    if end <= start:
        raise ValueError("end must be later than start")
    if execution_time < start or execution_time >= end:
        raise ValueError("execution_time must fall inside the screening window")

    nominal_propagator = __import__("backend.services.orbit_service", fromlist=["ConjunctionPropagator"]).ConjunctionPropagator(objects)
    before = calculate_conjunction(nominal_propagator, object_a, object_b, start, end)
    before_assessment = assess_upstream_risk(before, None)

    maneuver_propagator = ManeuverPropagator(
        objects, object_id, execution_time, delta_v_m_s, direction
    )
    after = calculate_conjunction(maneuver_propagator, object_a, object_b, start, end)
    after_assessment = assess_upstream_risk(after, None)

    before_payload = _event_payload(before, before_assessment)
    after_payload = _event_payload(after, after_assessment)
    return {
        "before": before_payload,
        "after": after_payload,
        "risk_change": {
            "before": before_assessment.risk_level.value,
            "after": after_assessment.risk_level.value,
            "miss_distance_delta_km": after.miss_distance_km - before.miss_distance_km,
            "relative_velocity_delta_km_s": after.relative_speed_km_s - before.relative_speed_km_s,
        },
        "maneuver": {
            "object_id": object_id,
            "delta_v_m_s": delta_v_m_s,
            "direction": direction,
            "execution_time": execution_time,
            "model": "SGP4 pre-burn + impulsive RTN + two-body RK4 post-burn",
            "prototype": True,
        },
    }
