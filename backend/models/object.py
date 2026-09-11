"""Space object domain model backed by the orbital data file."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SpaceObject:
    """One entry from data/orbital_data.json in its canonical form."""

    object_id: str
    name: str
    line1: str
    line2: str
    epoch: str

    @classmethod
    def from_json(cls, item: dict) -> "SpaceObject":
        return cls(
            object_id=item["object_id"],
            name=item["name"],
            line1=item["tle"]["line1"],
            line2=item["tle"]["line2"],
            epoch=item["epoch"],
        )

    def to_dict(self) -> dict:
        return {
            "object_id": self.object_id,
            "name": self.name,
            "tle": {"line1": self.line1, "line2": self.line2},
            "epoch": self.epoch,
        }
