from data_engine.database import (
    get_latest_orbital_data,
    get_object_history
)


def _row_to_dict(row):
    """Convert a database row into a backend-friendly dictionary."""

    return {
        "object_id": row[0],
        "name": row[1],
        "tle_line1": row[2],
        "tle_line2": row[3],
        "epoch": row[4],
        "source": row[5],
        "fetched_at": row[6]
    }


def get_current_objects():
    """Return the latest orbital record for every tracked object."""

    rows = get_latest_orbital_data()

    return [_row_to_dict(row) for row in rows]


def get_object_history_data(object_id):
    """Return historical orbital records for a specific object."""

    rows = get_object_history(object_id)

    return [_row_to_dict(row) for row in rows]


def get_data_status():
    """Return basic information about the current orbital dataset."""

    objects = get_current_objects()

    if not objects:
        return {
            "status": "empty",
            "object_count": 0,
            "last_updated": None,
            "source": None
        }

    latest_update = max(
        obj["fetched_at"]
        for obj in objects
        if obj["fetched_at"]
    )

    return {
        "status": "healthy",
        "object_count": len(objects),
        "last_updated": latest_update,
        "source": objects[0]["source"]
    }
