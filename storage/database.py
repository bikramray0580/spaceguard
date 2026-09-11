"""SQLite connection helper for SpaceGuard."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from storage.create_tables import create_tables

DEFAULT_DB_PATH = Path("storage/spaceguard.db")


def get_db_path() -> Path:
    raw = os.getenv("SPACEGUARD_DB_PATH", "").strip()
    if raw:
        return Path(raw)
    return DEFAULT_DB_PATH


def get_connection(db_path: str | Path | None = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path is not None else get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    create_tables(connection)
    return connection
