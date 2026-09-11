"""Minimal Space-Track GP test client."""

from __future__ import annotations

import os

from dotenv import load_dotenv
from spacetrack import SpaceTrackClient

load_dotenv()


def fetch_space_track_gp(norad_cat_id: int = 25544) -> list[dict]:
    username = os.getenv("SPACETRACK_USERNAME")
    password = os.getenv("SPACETRACK_PASSWORD")

    if not username or not password:
        raise RuntimeError(
            "Missing SPACETRACK_USERNAME or SPACETRACK_PASSWORD in .env"
        )

    client = SpaceTrackClient(
        identity=username,
        password=password,
    )

    try:
        records = client.gp(norad_cat_id=norad_cat_id)
        return records
    finally:
        client.close()