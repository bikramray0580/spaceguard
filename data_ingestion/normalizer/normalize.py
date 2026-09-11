"""Convert parsed source records into the shared NormalizedRecord schema."""

from __future__ import annotations

from pathlib import Path

from data_ingestion.models import (
    RECORD_CONJUNCTION,
    RECORD_ORBITAL_ELEMENT,
    ConjunctionRecord,
    NormalizedRecord,
    TLERecord,
)
from data_ingestion.parsers.cdm import parse_cdm_text
from data_ingestion.parsers.tle import parse_tle_text


def normalize_tle(record: TLERecord) -> NormalizedRecord:
    if not isinstance(record, TLERecord):
        raise TypeError("record must be a TLERecord")
    return NormalizedRecord(
        record_type=RECORD_ORBITAL_ELEMENT,
        object_id=str(record.norad_id),
        name=record.name,
        epoch=record.epoch,
        frame="TEME",
        data={
            "format": "TLE",
            "line1": record.line1,
            "line2": record.line2,
            "classification": record.classification,
            "intl_designator": record.intl_designator,
            "inclination_deg": record.inclination_deg,
            "raan_deg": record.raan_deg,
            "eccentricity": record.eccentricity,
            "arg_perigee_deg": record.arg_perigee_deg,
            "mean_anomaly_deg": record.mean_anomaly_deg,
            "mean_motion_rev_per_day": record.mean_motion_rev_per_day,
            "bstar": record.bstar,
        },
        provenance=record.provenance,
        quality=record.quality,
    )


def normalize_cdm(record: ConjunctionRecord) -> NormalizedRecord:
    if not isinstance(record, ConjunctionRecord):
        raise TypeError("record must be a ConjunctionRecord")
    return NormalizedRecord(
        record_type=RECORD_CONJUNCTION,
        object_id=record.object1_id,
        name=record.object1_name,
        epoch=record.tca,
        frame="EME2000",
        data={
            "format": "CDM",
            "message_id": record.message_id,
            "object1_id": record.object1_id,
            "object2_id": record.object2_id,
            "object1_name": record.object1_name,
            "object2_name": record.object2_name,
            "miss_distance_m": record.miss_distance_m,
            "relative_speed_m_s": record.relative_speed_m_s,
            "collision_probability": record.collision_probability,
            "has_covariance": record.has_covariance,
            "creation_date": (
                record.creation_date.isoformat() if record.creation_date else None
            ),
            "pc_is_authoritative": record.has_covariance
            and record.collision_probability is not None,
        },
        provenance=record.provenance,
        quality=record.quality,
    )


def ingest_text(
    text: str,
    *,
    source: str = "local",
    originator: str = "",
    raw_uri: str = "",
    format_hint: str | None = None,
) -> list[NormalizedRecord]:
    hint = (format_hint or "").strip().lower()
    stripped = text.lstrip()
    if hint in {"tle", "3le"} or _looks_like_tle(stripped):
        return [
            normalize_tle(item)
            for item in parse_tle_text(
                text,
                source=source,
                originator=originator,
                raw_uri=raw_uri,
            )
        ]
    if hint in {"cdm", "json"} or _looks_like_cdm(stripped):
        return [
            normalize_cdm(item)
            for item in parse_cdm_text(
                text,
                source=source,
                originator=originator,
                raw_uri=raw_uri,
            )
        ]
    raise ValueError("unable to detect ingestion format")


_ORIGINATORS = {
    "celestrak": "CelesTrak",
    "spacetrack": "Space-Track",
    "cdm": "CDM",
}


def ingest_path(path: str | Path, *, source: str | None = None) -> list[NormalizedRecord]:
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8")
    suffix = file_path.suffix.lower()
    hint = None
    if suffix in {".tle", ".3le", ".txt"}:
        hint = "tle" if suffix != ".txt" else None
    elif suffix in {".cdm", ".kvn", ".json"}:
        hint = "cdm"
    resolved_source = source or file_path.parent.name or "local"
    return ingest_text(
        text,
        source=resolved_source,
        originator=_ORIGINATORS.get(resolved_source.lower(), ""),
        raw_uri=str(file_path),
        format_hint=hint,
    )


def _looks_like_tle(text: str) -> bool:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("1 ") and len(stripped) >= 69:
            return True
    return False


def _looks_like_cdm(text: str) -> bool:
    if not text:
        return False
    if text[0] in "[{":
        return True
    upper = text.upper()
    return "CCSDS_CDM_VERS" in upper or "TCA" in upper or "MESSAGE_ID" in upper
