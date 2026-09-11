"""Orbit result domain model."""

from dataclasses import dataclass


@dataclass
class OrbitResult:
    """Propagated TEME states for one space object."""

    object_id: str
    object_name: str
    states: list[dict]

    def to_dict(self) -> dict:
        return {
            "object_id": self.object_id,
            "object_name": self.object_name,
            "states": self.states,
        }
