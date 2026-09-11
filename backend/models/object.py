"""Canonical API object model backed by the checked-in orbital catalogue."""
from dataclasses import dataclass


@dataclass(frozen=True)
class SpaceObject:
    object_id: str
    name: str
    line1: str
    line2: str
    epoch: str

    @classmethod
    def from_json(cls, item: dict) -> "SpaceObject":
        tle = item["tle"]
        return cls(
            object_id=str(item["object_id"]),
            name=str(item["name"]),
            line1=str(tle["line1"]),
            line2=str(tle["line2"]),
            epoch=str(item["epoch"]),
        )

    def to_dict(self) -> dict:
        return {
            "object_id": self.object_id,
            "name": self.name,
            "tle": {"line1": self.line1, "line2": self.line2},
            "epoch": self.epoch,
        }
