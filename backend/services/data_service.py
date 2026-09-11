"""Load the demo orbital catalogue used by the API."""
from __future__ import annotations
import json
from functools import lru_cache
from pathlib import Path

from ..config import DATA_FILE
from ..models.object import SpaceObject


class ObjectNotFoundError(KeyError):
    pass


@lru_cache(maxsize=1)
def list_objects() -> tuple[SpaceObject, ...]:
    payload = json.loads(Path(DATA_FILE).read_text(encoding="utf-8"))
    return tuple(SpaceObject.from_json(item) for item in payload.get("objects", []))


def find_object(object_id: str) -> SpaceObject:
    for obj in list_objects():
        if obj.object_id == object_id:
            return obj
    raise ObjectNotFoundError(f"object {object_id!r} was not found")
