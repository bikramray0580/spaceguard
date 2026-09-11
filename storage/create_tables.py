"""Create SQLite tables for CelesTrak GP JSON records."""

from __future__ import annotations

import sqlite3

GP_RECORDS_TABLE = """
CREATE TABLE IF NOT EXISTS gp_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    norad_cat_id INTEGER NOT NULL,
    object_name TEXT,
    object_id TEXT,
    epoch TEXT NOT NULL,
    mean_motion REAL,
    eccentricity REAL,
    inclination REAL,
    ra_of_asc_node REAL,
    arg_of_pericenter REAL,
    mean_anomaly REAL,
    ephemeris_type INTEGER,
    classification_type TEXT,
    element_set_no INTEGER,
    rev_at_epoch INTEGER,
    bstar REAL,
    mean_motion_dot REAL,
    mean_motion_ddot REAL,
    source TEXT NOT NULL,
    source_note TEXT,
    raw_json TEXT NOT NULL,
    ingested_at TEXT NOT NULL,
    UNIQUE(norad_cat_id, epoch)
)
"""


def create_tables(connection: sqlite3.Connection) -> None:
    connection.execute(GP_RECORDS_TABLE)
    connection.commit()
