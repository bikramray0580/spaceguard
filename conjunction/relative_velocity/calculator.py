"""Nominal relative velocity calculations (km/s)."""
from __future__ import annotations
from dataclasses import dataclass
from math import sqrt
from ..models import Vector3

def dot(a: Vector3, b: Vector3) -> float: return sum(x * y for x, y in zip(a, b))
def norm(a: Vector3) -> float: return sqrt(dot(a, a))
def subtract(a: Vector3, b: Vector3) -> Vector3: return (a[0]-b[0], a[1]-b[1], a[2]-b[2])
def unit(a: Vector3) -> Vector3 | None:
    length = norm(a)
    return None if length == 0 else (a[0]/length, a[1]/length, a[2]/length)

@dataclass(frozen=True)
class RelativeVelocity:
    vector_km_s: Vector3
    speed_km_s: float
    motion_direction: Vector3 | None
    closing_rate_km_s: float

def calculate_relative_velocity(position_a_km: Vector3, velocity_a_km_s: Vector3,
                                position_b_km: Vector3, velocity_b_km_s: Vector3) -> RelativeVelocity:
    """Return v_A-v_B and radial closing rate; positive means approaching."""
    relative_position = subtract(position_a_km, position_b_km)
    vector = subtract(velocity_a_km_s, velocity_b_km_s)
    distance, speed = norm(relative_position), norm(vector)
    closing = 0.0 if distance == 0 else -dot(relative_position, vector) / distance
    return RelativeVelocity(vector, speed, unit(vector), closing)
