"""Print a quick quality report for ingested CelesTrak GP records."""

from __future__ import annotations

from storage.database import get_connection


def check_data_quality() -> None:
    connection = get_connection()

    total_records = connection.execute(
        "SELECT COUNT(*) FROM gp_records"
    ).fetchone()[0]

    unique_objects = connection.execute(
        "SELECT COUNT(DISTINCT norad_cat_id) FROM gp_records"
    ).fetchone()[0]

    missing_names = connection.execute(
        """
        SELECT COUNT(*)
        FROM gp_records
        WHERE object_name IS NULL OR TRIM(object_name) = ''
        """
    ).fetchone()[0]

    missing_epochs = connection.execute(
        """
        SELECT COUNT(*)
        FROM gp_records
        WHERE epoch IS NULL OR TRIM(epoch) = ''
        """
    ).fetchone()[0]

    missing_mean_motion = connection.execute(
        """
        SELECT COUNT(*)
        FROM gp_records
        WHERE mean_motion IS NULL OR mean_motion <= 0
        """
    ).fetchone()[0]

    local_fallback_records = connection.execute(
        """
        SELECT COUNT(*)
        FROM gp_records
        WHERE source = 'local_fallback'
        """
    ).fetchone()[0]

    connection.close()

    print("Data Quality Report")
    print("-------------------")
    print(f"Total records: {total_records}")
    print(f"Unique objects: {unique_objects}")
    print(f"Missing object names: {missing_names}")
    print(f"Missing epochs: {missing_epochs}")
    print(f"Missing/invalid mean motion: {missing_mean_motion}")
    print(f"Local fallback records: {local_fallback_records}")


if __name__ == "__main__":
    check_data_quality()
