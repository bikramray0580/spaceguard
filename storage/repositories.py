"""Insert validated CelesTrak GP JSON records into SQLite."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

INSERT_GP_SQL = """
INSERT INTO gp_records (
    norad_cat_id,
    object_name,
    object_id,
    epoch,
    mean_motion,
    eccentricity,
    inclination,
    ra_of_asc_node,
    arg_of_pericenter,
    mean_anomaly,
    ephemeris_type,
    classification_type,
    element_set_no,
    rev_at_epoch,
    bstar,
    mean_motion_dot,
    mean_motion_ddot,
    source,
    source_note,
    raw_json,
    ingested_at
) VALUES (
    :norad_cat_id,
    :object_name,
    :object_id,
    :epoch,
    :mean_motion,
    :eccentricity,
    :inclination,
    :ra_of_asc_node,
    :arg_of_pericenter,
    :mean_anomaly,
    :ephemeris_type,
    :classification_type,
    :element_set_no,
    :rev_at_epoch,
    :bstar,
    :mean_motion_dot,
    :mean_motion_ddot,
    :source,
    :source_note,
    :raw_json,
    :ingested_at
)
ON CONFLICT(norad_cat_id, epoch) DO UPDATE SET
    object_name=excluded.object_name,
    object_id=excluded.object_id,
    mean_motion=excluded.mean_motion,
    eccentricity=excluded.eccentricity,
    inclination=excluded.inclination,
    ra_of_asc_node=excluded.ra_of_asc_node,
    arg_of_pericenter=excluded.arg_of_pericenter,
    mean_anomaly=excluded.mean_anomaly,
    ephemeris_type=excluded.ephemeris_type,
    classification_type=excluded.classification_type,
    element_set_no=excluded.element_set_no,
    rev_at_epoch=excluded.rev_at_epoch,
    bstar=excluded.bstar,
    mean_motion_dot=excluded.mean_motion_dot,
    mean_motion_ddot=excluded.mean_motion_ddot,
    source=excluded.source,
    source_note=excluded.source_note,
    raw_json=excluded.raw_json,
    ingested_at=excluded.ingested_at
"""


def insert_gp_records(
    records: list[dict],
    connection: sqlite3.Connection,
) -> int:
    """Insert or update GP JSON records. Returns the number of rows written."""
    if not records:
        return 0
    ingested_at = datetime.now(timezone.utc).isoformat()
    rows = [_row_from_gp(record, ingested_at) for record in records]
    connection.executemany(INSERT_GP_SQL, rows)
    connection.commit()
    return len(rows)


def _row_from_gp(record: dict, ingested_at: str) -> dict:
    source = str(record.get("SOURCE") or "celestrak")
    source_note = record.get("SOURCE_NOTE")
    if source == "local_fallback" and not source_note:
        source_note = "development fallback; not live CelesTrak data"
    return {
        "norad_cat_id": int(record["NORAD_CAT_ID"]),
        "object_name": record.get("OBJECT_NAME"),
        "object_id": record.get("OBJECT_ID"),
        "epoch": str(record["EPOCH"]),
        "mean_motion": record.get("MEAN_MOTION"),
        "eccentricity": record.get("ECCENTRICITY"),
        "inclination": record.get("INCLINATION"),
        "ra_of_asc_node": record.get("RA_OF_ASC_NODE"),
        "arg_of_pericenter": record.get("ARG_OF_PERICENTER"),
        "mean_anomaly": record.get("MEAN_ANOMALY"),
        "ephemeris_type": record.get("EPHEMERIS_TYPE"),
        "classification_type": record.get("CLASSIFICATION_TYPE"),
        "element_set_no": record.get("ELEMENT_SET_NO"),
        "rev_at_epoch": record.get("REV_AT_EPOCH"),
        "bstar": record.get("BSTAR"),
        "mean_motion_dot": record.get("MEAN_MOTION_DOT"),
        "mean_motion_ddot": record.get("MEAN_MOTION_DDOT"),
        "source": source,
        "source_note": source_note,
        "raw_json": json.dumps(record, separators=(",", ":")),
        "ingested_at": ingested_at,
    }
