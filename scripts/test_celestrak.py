from data_ingestion.celestrak.client import fetch_celestrak_data


if __name__ == "__main__":
    records = fetch_celestrak_data()

    print()
    print(f"Total records received: {len(records)}")

    if records:
        print("\nFirst record:")
        print(records[0])

        if records[0].get("SOURCE") == "local_fallback":
            print("\nWARNING: This is fallback data, not live CelesTrak data.")
        else:
            print("\nSUCCESS: Live CelesTrak data received.")