from data_ingestion.spacetrack.client import fetch_space_track_cdm


if __name__ == "__main__":
    records = fetch_space_track_cdm()

    print(f"Received {len(records)} CDM record(s).")

    if records:
        print("\nFirst CDM record:")
        print(records[0])
    else:
        print("\nNo CDM records were returned.")