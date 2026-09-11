import sqlite3
from pathlib import Path


DATABASE_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "spaceguard.db"
)


def get_connection():
    """Create a connection to the SpaceGuard SQLite database."""

    DATABASE_FILE.parent.mkdir(parents=True, exist_ok=True)

    return sqlite3.connect(DATABASE_FILE)


def create_tables():
    """Create the orbital TLE history table."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS orbital_objects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            object_id TEXT NOT NULL,
            name TEXT NOT NULL,
            tle_line1 TEXT NOT NULL,
            tle_line2 TEXT NOT NULL,
            epoch TEXT NOT NULL,
            source TEXT NOT NULL,
            fetched_at TEXT NOT NULL,
            UNIQUE(object_id, epoch)
        )
        """
    )

    connection.commit()
    connection.close()


def insert_orbital_object(
    
    object_id,
    name,
    line1,
    line2,
    epoch,
    source,
    fetched_at
):
    """Insert a validated orbital record into the database."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT OR IGNORE INTO orbital_objects
        (
            object_id,
            name,
            tle_line1,
            tle_line2,
            epoch,
            source,
            fetched_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            object_id,
            name,
            line1,
            line2,
            epoch,
            source,
            fetched_at
        )
    )

    connection.commit()
    connection.close()

def get_latest_orbital_data():
    """Return the latest TLE record for every orbital object."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT object_id, name, tle_line1, tle_line2, epoch, source, fetched_at
        FROM orbital_objects
        WHERE id IN (
            SELECT MAX(id)
            FROM orbital_objects
            GROUP BY object_id
        )
        ORDER BY object_id
        """
    )

    rows = cursor.fetchall()
    connection.close()

    return rows


def get_object_history(object_id):
    """Return all stored TLE records for a specific object."""

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT object_id, name, tle_line1, tle_line2, epoch, source, fetched_at
        FROM orbital_objects
        WHERE object_id = ?
        ORDER BY epoch DESC
        """,
        (object_id,)
    )

    rows = cursor.fetchall()
    connection.close()

    return rows

if __name__ == "__main__":
    create_tables()
    print(f"Database created at: {DATABASE_FILE}")