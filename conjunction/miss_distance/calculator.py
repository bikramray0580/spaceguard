"""Nominal geometry only; this module never calculates collision probability."""
from __future__ import annotations
from dataclasses import dataclass
from ..models import Vector3
from ..relative_velocity.calculator import norm, subtract, unit

@dataclass(frozen=True)
class MissDistance:
    relative_position_km: Vector3
    vector_km: Vector3
    distance_km: float
    direction: Vector3 | None

def calculate_miss_distance(position_a_km: Vector3, position_b_km: Vector3) -> MissDistance:
    """Calculate ||r_A-r_B|| in km and its direction when defined."""
    vector = subtract(position_a_km, position_b_km)
    return MissDistance(vector, vector, norm(vector), unit(vector))
