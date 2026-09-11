from data_ingestion.spacetrack.client import fetch_space_track_gp


if __name__ == "__main__":
    records = fetch_space_track_gp(25544)

    print(f"Received {len(records)} record(s).")

    if records:
        print("\nFirst Space-Track record:")
        print(records[0])