"""Minimal Space-Track GP and CDM client."""

from __future__ import annotations

import os

from dotenv import load_dotenv
from spacetrack import SpaceTrackClient

load_dotenv()


def _get_client() -> SpaceTrackClient:
    username = os.getenv("SPACETRACK_USERNAME")
    password = os.getenv("SPACETRACK_PASSWORD")

    if not username or not password:
        raise RuntimeError(
            "Missing SPACETRACK_USERNAME or SPACETRACK_PASSWORD in .env"
        )

    return SpaceTrackClient(
        identity=username,
        password=password,
    )


def fetch_space_track_gp(norad_cat_id: int = 25544) -> list[dict]:
    """Fetch GP data for one object."""
    client = _get_client()

    try:
        records = client.gp(norad_cat_id=norad_cat_id)

        for record in records:
            record["SOURCE"] = "spacetrack"

        return records
    finally:
        client.close()


def fetch_space_track_gp_batch(limit: int = 250) -> list[dict]:
    """Fetch a batch of GP records from Space-Track."""
    if limit < 1:
        return []

    client = _get_client()

    try:
        records = client.gp(
            orderby="NORAD_CAT_ID asc",
            limit=limit,
        )

        for record in records:
            record["SOURCE"] = "spacetrack"

        return records
    finally:
        client.close()


def fetch_space_track_cdm() -> list[dict]:
    """Fetch available conjunction data messages.

    Returns an empty list when the account is not authorized
    to access the CDM endpoint.
    """
    client = _get_client()

    try:
        return client.cdm()
    except Exception as exc:
        message = str(exc)

        if "401" in message or "Not Authorized" in message:
            print("Space-Track CDM access is not authorized for this account.")
            return []

        raise
    finally:
        client.close()