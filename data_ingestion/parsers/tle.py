"""Two-line element set parser."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from data_ingestion.models import (
    QUALITY_COMPLETE,
    QUALITY_DEGRADED,
    QUALITY_INVALID,
    QUALITY_PARTIAL,
    Provenance,
    QualityStatus,
    TLERecord,
)

TLE_MAX_AGE_DAYS = 7.0


def _tle_checksum(line: str) -> int:
    total = 0
    for char in line[:-1]:
        if char.isdigit():
            total += int(char)
        elif char == "-":
            total += 1
    return total % 10


def _checksum_ok(line: str) -> bool:
    if len(line) != 69 or not line[-1].isdigit():
        return False
    return _tle_checksum(line) == int(line[-1])


def _parse_tle_scientific(field: str) -> float:
    text = field.strip()
    if not text:
        return 0.0
    sign = 1.0
    if text[0] == "-":
        sign = -1.0
        text = text[1:]
    elif text[0] == "+":
        text = text[1:]
    exp_index = None
    for index, char in enumerate(text):
        if char in "+-" and index > 0:
            exp_index = index
            break
    if exp_index is None:
        mantissa = text
        exponent = 0
    else:
        mantissa = text[:exp_index]
        exponent = int(text[exp_index:])
    mantissa = mantissa.replace(".", "")
    if not mantissa:
        return 0.0
    return sign * float("0." + mantissa) * (10 ** exponent)


def _tle_epoch_to_datetime(epoch_field: str) -> datetime:
    text = epoch_field.strip()
    if len(text) < 5:
        raise ValueError("TLE epoch is malformed")
    year = int(text[:2])
    day = float(text[2:])
    full_year = 2000 + year if year < 57 else 1900 + year
    return datetime(full_year, 1, 1, tzinfo=timezone.utc) + timedelta(days=day - 1.0)


def _as_int(field: str, name: str) -> int:
    try:
        return int(field.strip())
    except ValueError as exc:
        raise ValueError(f"{name} is not an integer") from exc


def _as_float(field: str, name: str) -> float:
    try:
        return float(field.strip())
    except ValueError as exc:
        raise ValueError(f"{name} is not numeric") from exc


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _quality_for_tle(
    line1: str,
    line2: str,
    name: str,
    epoch: datetime,
    ingested_at: datetime,
) -> QualityStatus:
    reasons: list[str] = []
    status = QUALITY_COMPLETE
    if len(line1) != 69 or len(line2) != 69:
        reasons.append("TLE line length is not 69 characters")
        status = QUALITY_INVALID
    if not _checksum_ok(line1):
        reasons.append("line1 checksum mismatch")
        status = QUALITY_INVALID
    if not _checksum_ok(line2):
        reasons.append("line2 checksum mismatch")
        status = QUALITY_INVALID
    if status == QUALITY_INVALID:
        return QualityStatus(status=status, reasons=tuple(reasons))
    age_days = (ingested_at - epoch).total_seconds() / 86400.0
    if age_days > TLE_MAX_AGE_DAYS:
        reasons.append(f"epoch is {age_days:.1f} days older than ingest time")
        status = QUALITY_DEGRADED
    if epoch > ingested_at + timedelta(days=1):
        reasons.append("epoch is in the future")
        status = QUALITY_DEGRADED
    if name.startswith("NORAD "):
        reasons.append("object name was not provided")
        if status == QUALITY_COMPLETE:
            status = QUALITY_PARTIAL
    return QualityStatus(status=status, reasons=tuple(reasons))


def parse_tle_pair(
    line1: str,
    line2: str,
    name: str = "",
    *,
    source: str = "local",
    source_id: str = "",
    originator: str = "",
    raw_uri: str = "",
    ingested_at: datetime | None = None,
) -> TLERecord:
    line1 = line1.strip()
    line2 = line2.strip()
    if not line1.startswith("1 ") or not line2.startswith("2 "):
        raise ValueError("TLE lines must start with '1 ' and '2 '")
    if len(line1) < 69 or len(line2) < 69:
        raise ValueError("TLE lines must be 69 characters")
    line1 = line1[:69]
    line2 = line2[:69]
    norad_1 = _as_int(line1[2:7], "line1 catalog number")
    norad_2 = _as_int(line2[2:7], "line2 catalog number")
    if norad_1 != norad_2:
        raise ValueError("TLE catalog numbers do not match")
    name = name.strip() or f"NORAD {norad_1}"
    epoch = _tle_epoch_to_datetime(line1[18:32])
    ingested = ingested_at or _utcnow()
    provenance = Provenance(
        source=source,
        ingested_at=ingested,
        source_id=source_id or str(norad_1),
        originator=originator,
        raw_uri=raw_uri,
    )
    quality = _quality_for_tle(line1, line2, name, epoch, ingested)
    eccentricity_field = line2[26:33].strip()
    eccentricity = float("0." + eccentricity_field) if eccentricity_field else 0.0
    return TLERecord(
        norad_id=norad_1,
        name=name,
        line1=line1,
        line2=line2,
        epoch=epoch,
        classification=line1[7:8].strip() or "U",
        intl_designator=line1[9:17].strip(),
        inclination_deg=_as_float(line2[8:16], "inclination"),
        raan_deg=_as_float(line2[17:25], "raan"),
        eccentricity=eccentricity,
        arg_perigee_deg=_as_float(line2[34:42], "arg_perigee"),
        mean_anomaly_deg=_as_float(line2[43:51], "mean_anomaly"),
        mean_motion_rev_per_day=_as_float(line2[52:63], "mean_motion"),
        bstar=_parse_tle_scientific(line1[53:61]),
        provenance=provenance,
        quality=quality,
    )


def parse_tle_text(
    text: str,
    *,
    source: str = "local",
    originator: str = "",
    raw_uri: str = "",
    ingested_at: datetime | None = None,
) -> list[TLERecord]:
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    lines = [line.rstrip("\n\r") for line in text.splitlines()]
    records: list[TLERecord] = []
    index = 0
    pending_name = ""
    while index < len(lines):
        line = lines[index].strip()
        if not line:
            index += 1
            continue
        if line.startswith("1 "):
            if index + 1 >= len(lines):
                raise ValueError("TLE line1 is missing a matching line2")
            line2 = lines[index + 1].strip()
            if not line2.startswith("2 "):
                raise ValueError("TLE line1 is not followed by line2")
            records.append(
                parse_tle_pair(
                    line,
                    line2,
                    pending_name,
                    source=source,
                    originator=originator,
                    raw_uri=raw_uri,
                    ingested_at=ingested_at,
                )
            )
            pending_name = ""
            index += 2
            continue
        if line.startswith("2 "):
            raise ValueError("TLE line2 appeared without line1")
        pending_name = line
        index += 1
    if pending_name and not records:
        raise ValueError("no TLE line pairs were found")
    if not records:
        raise ValueError("no TLE line pairs were found")
    return records
