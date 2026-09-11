"""Relative-vector and distance operations for matching orbital states."""

from __future__ import annotations

from math import sqrt

from .models import OrbitalState, Vector3


def _validate_pair(state_a: OrbitalState, state_b: OrbitalState) -> None:
    if state_a.timestamp != state_b.timestamp:
        raise ValueError("orbital states must have the same timestamp")
    if state_a.coordinate_frame != state_b.coordinate_frame:
        raise ValueError("orbital states must have the same coordinate frame")


def relative_position_km(state_a: OrbitalState, state_b: OrbitalState) -> Vector3:
    """Return R_rel = R_B - R_A in kilometres."""
    _validate_pair(state_a, state_b)
    return Vector3(
        state_b.position_km.x - state_a.position_km.x,
        state_b.position_km.y - state_a.position_km.y,
        state_b.position_km.z - state_a.position_km.z,
    )


def relative_velocity_km_s(state_a: OrbitalState, state_b: OrbitalState) -> Vector3:
    """Return V_rel = V_B - V_A in kilometres per second."""
    _validate_pair(state_a, state_b)
    return Vector3(
        state_b.velocity_km_s.x - state_a.velocity_km_s.x,
        state_b.velocity_km_s.y - state_a.velocity_km_s.y,
        state_b.velocity_km_s.z - state_a.velocity_km_s.z,
    )


def vector_magnitude(vector: Vector3) -> float:
    """Return the Euclidean magnitude of a three-dimensional vector."""
    return sqrt(vector.x**2 + vector.y**2 + vector.z**2)


def separation_distance_km(state_a: OrbitalState, state_b: OrbitalState) -> float:
    """Return Euclidean separation distance in kilometres."""
    return vector_magnitude(relative_position_km(state_a, state_b))


def relative_velocity_magnitude_km_s(state_a: OrbitalState, state_b: OrbitalState) -> float:
    """Return relative-velocity magnitude in kilometres per second."""
    return vector_magnitude(relative_velocity_km_s(state_a, state_b))
