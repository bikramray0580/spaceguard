"""SQLite storage for ingested CelesTrak GP JSON records."""

from storage.database import get_connection
from storage.repositories import insert_gp_records

__all__ = ["get_connection", "insert_gp_records"]
