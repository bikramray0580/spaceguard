"""Load and query space objects using the existing Data Engine."""
 
import json
from data_engine.database import create_tables, get_latest_orbital_data
from ..config import DATA_FILE
from ..models.object import SpaceObject
 
 
class ObjectNotFoundError(LookupError):
    """Raised when an object_id is not present in the orbital data."""
 
def _objects_from_data_engine() -> list[SpaceObject]:
    """Load the latest records from the Data Engine's SQLite store."""
    create_tables()
    return [
        SpaceObject(
            object_id=object_id,
            name=name,
            line1=tle_line1,
            line2=tle_line2,
            epoch=epoch,
        )
        for (
            object_id,
            name,
            tle_line1,
            tle_line2,
            epoch,
            _source,
            _fetched_at,
        ) in get_latest_orbital_data()
    ]
 
 
def _objects_from_snapshot() -> list[SpaceObject]:
    """Fall back to the Data Engine's latest JSON snapshot."""
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        payload = json.load(file)
    return [SpaceObject.from_json(item) for item in payload["objects"]]
 
 
def load_objects() -> list[SpaceObject]:
    """Load all space objects through the existing Data Engine.
 
    The Data Engine's SQLite store is the authoritative source. If it has not
    been populated yet (for example on a fresh checkout), fall back to the
    latest JSON snapshot the Data Engine writes to data/orbital_data.json.
    """
    objects = _objects_from_data_engine()
    if not objects:
        objects = _objects_from_snapshot()
    return objects
 
 
def list_objects() -> list[SpaceObject]:
    """Return all available space objects."""
    return load_objects()
 
 
def find_object(object_id: str) -> SpaceObject:
    """Return the object with the given canonical object_id."""
    for obj in load_objects():
        if obj.object_id == object_id:
            return obj
    raise ObjectNotFoundError(f"object not found: {object_id}")