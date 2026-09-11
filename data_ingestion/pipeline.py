"""Run CelesTrak fetch -> validate -> insert GP JSON into SQLite."""

from __future__ import annotations

from data_ingestion.celestrak.client import fetch_celestrak_data
from data_ingestion.validate import validate_records
from storage.database import get_connection
from storage.repositories import insert_gp_records


def run_pipeline() -> list[dict]:
    records = fetch_celestrak_data()
    valid, skipped = validate_records(records)
    print(f"Valid records: {len(valid)}")
    print(f"Skipped records: {skipped}")
    connection = get_connection()
    try:
        saved = insert_gp_records(valid, connection)
    finally:
        connection.close()
    print(f"Saved records: {saved}")
    fallback_count = sum(1 for item in valid if item.get("SOURCE") == "local_fallback")
    if fallback_count:
        print(
            f"Note: {fallback_count} saved records are labeled local_fallback "
            "(development data, not live CelesTrak)."
        )
    return valid


def main() -> None:
    run_pipeline()


if __name__ == "__main__":
    main()
