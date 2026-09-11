"""Run CelesTrak and Space-Track ingestion into SQLite."""

from __future__ import annotations

from data_ingestion.celestrak.client import fetch_celestrak_data
from data_ingestion.spacetrack.client import fetch_space_track_gp_batch
from data_ingestion.validate import validate_records
from storage.database import get_connection
from storage.repositories import insert_gp_records


def run_pipeline(
    celestrak_limit: int = 250,
    spacetrack_limit: int = 250,
) -> list[dict]:
    """Fetch, validate, and save records from both sources."""

    print("Fetching CelesTrak records...")
    celestrak_records = fetch_celestrak_data(limit=celestrak_limit)

    print("Fetching Space-Track records...")
    spacetrack_records = fetch_space_track_gp_batch(limit=spacetrack_limit)

    print(f"CelesTrak fetched: {len(celestrak_records)}")
    print(f"Space-Track fetched: {len(spacetrack_records)}")

    all_records = celestrak_records + spacetrack_records

    valid, skipped = validate_records(all_records)

    print(f"Total valid records: {len(valid)}")
    print(f"Skipped records: {skipped}")

    connection = get_connection()

    try:
        saved = insert_gp_records(valid, connection)
    finally:
        connection.close()

    print(f"Saved/updated records: {saved}")

    return valid


def main() -> None:
    run_pipeline()


if __name__ == "__main__":
    main()