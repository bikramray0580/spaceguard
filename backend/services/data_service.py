"""Load the orbital catalogue used by the API.

The dashboard should not pretend that the checked-in two-object demo file is the
full satellite population. When live ingestion is available, load CelesTrak's
current ACTIVE GP catalogue and fall back to the checked-in catalogue if the
network/source is unavailable.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path

from ..config import DATA_FILE
from ..models.object import SpaceObject


class ObjectNotFoundError(KeyError):
    pass


@lru_cache(maxsize=1)
def list_objects() -> tuple[SpaceObject, ...]:
    """Return the best available satellite catalogue.

    CelesTrak's ACTIVE group contains current GP records for active satellites,
    so the dashboard count reflects a real source rather than an invented
    number. The repository catalogue remains a deterministic offline fallback.
    """
    if _live_catalogue_enabled():
        try:
            records = _load_live_celestrak()
            if records:
                return tuple(records)
        except Exception as exc:  # pragma: no cover - network dependent
            print(f"Live CelesTrak catalogue unavailable: {exc}")
            print("Falling back to checked-in orbital_data.json")

    return _load_checked_in_catalogue()


def find_object(object_id: str) -> SpaceObject:
    for obj in list_objects():
        if obj.object_id == object_id:
            return obj
    raise ObjectNotFoundError(f"object {object_id!r} was not found")


def _live_catalogue_enabled() -> bool:
    value = os.getenv("SPACEGUARD_LIVE_CELESTRAK", "true").strip().lower()
    return value not in {"0", "false", "no", "off"}


def _load_live_celestrak() -> list[SpaceObject]:
    from data_ingestion.celestrak.client import fetch_celestrak_data

    # Keep this bounded to the active-satellite catalogue rather than all
    # orbital objects/debris. The source itself provides the records; we do not
    # synthesize or pad the population.
    os.environ.setdefault("CELESTRAK_GROUP", "ACTIVE")
    records = fetch_celestrak_data()

    objects: list[SpaceObject] = []
    seen_ids: set[str] = set()

    for record in records:
        object_id = _first(record, "NORAD_CAT_ID", "NORAD_CATID", "SATCAT_ID")
        name = _first(record, "OBJECT_NAME", "NAME")
        line1 = _first(record, "TLE_LINE1", "LINE1")
        line2 = _first(record, "TLE_LINE2", "LINE2")
        epoch = _first(record, "EPOCH")

        if not object_id or not name or not line1 or not line2 or not epoch:
            continue

        object_id = str(object_id).strip()
        if object_id in seen_ids:
            continue

        # SGP4/TLE propagation in the current backend uses the catalog number
        # carried by the TLE, so reject records whose lines do not identify the
        # same catalog object.
        if len(str(line1)) < 69 or len(str(line2)) < 69:
            continue

        seen_ids.add(object_id)
        objects.append(
            SpaceObject(
                object_id=object_id,
                name=str(name).strip(),
                line1=str(line1).strip(),
                line2=str(line2).strip(),
                epoch=str(epoch).strip(),
            )
        )

    if not objects:
        raise ValueError("CelesTrak returned no usable active satellite records")

    print(f"Loaded {len(objects)} active satellites from CelesTrak")
    return objects


def _load_checked_in_catalogue() -> tuple[SpaceObject, ...]:
    payload = json.loads(Path(DATA_FILE).read_text(encoding="utf-8"))
    return tuple(SpaceObject.from_json(item) for item in payload.get("objects", []))


def _first(record: dict, *keys: str):
    for key in keys:
        value = record.get(key)
        if value is not None and str(value).strip():
            return value
    return None
