"""Nominal basis for later covariance projection; no uncertainty or Pc."""
from __future__ import annotations
from dataclasses import dataclass
from math import sqrt
from ..models import Vector3
from ..relative_velocity.calculator import dot, unit

def cross(a: Vector3, b: Vector3) -> Vector3:
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])

@dataclass(frozen=True)
class EncounterGeometry:
    relative_motion_direction: Vector3 | None
    miss_distance_direction: Vector3 | None
    plane_x: Vector3 | None
    plane_y: Vector3 | None
    nominal_coordinates_km: tuple[float, float] | None
    degenerate: bool

def calculate_encounter_geometry(relative_position_km: Vector3, relative_velocity_km_s: Vector3) -> EncounterGeometry:
    """Make an orthonormal plane normal to relative velocity when possible."""
    normal = unit(relative_velocity_km_s)
    line_of_sight = unit(relative_position_km)
    if normal is None:
        return EncounterGeometry(None, line_of_sight, None, None, None, True)
    projected = tuple(relative_position_km[i] - dot(relative_position_km, normal)*normal[i] for i in range(3))
    x_axis = unit(projected)  # closest-approach geometry naturally supplies this axis
    if x_axis is None:
        # Pick a reproducible vector not parallel to the normal.
        seed = (1., 0., 0.) if abs(normal[0]) < 0.9 else (0., 1., 0.)
        x_axis = unit(cross(normal, seed))
        return EncounterGeometry(normal, line_of_sight, x_axis, unit(cross(normal, x_axis)), (0., 0.), True)
    y_axis = unit(cross(normal, x_axis))
    return EncounterGeometry(normal, line_of_sight, x_axis, y_axis,
                             (dot(relative_position_km, x_axis), dot(relative_position_km, y_axis)), False)
