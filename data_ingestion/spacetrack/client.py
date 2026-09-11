"""Load Space-Track-style TLE catalogs from local files or in-memory text."""

from __future__ import annotations

from pathlib import Path

from data_ingestion.models import NormalizedRecord
from data_ingestion.normalizer.normalize import ingest_path, ingest_text


def load_spacetrack_tles(source: str | Path) -> list[NormalizedRecord]:
    if isinstance(source, Path) or _is_existing_path(source):
        return ingest_path(source, source="spacetrack")
    return ingest_text(
        str(source),
        source="spacetrack",
        originator="Space-Track",
        raw_uri="spacetrack:gp",
        format_hint="tle",
    )


def _is_existing_path(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return Path(value).is_file()
    except OSError:
        return False
