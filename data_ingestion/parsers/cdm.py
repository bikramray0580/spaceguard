"""Conjunction Data Message parser for KVN and JSON encodings."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Mapping

from data_ingestion.models import (
    QUALITY_COMPLETE,
    QUALITY_INVALID,
    QUALITY_PARTIAL,
    ConjunctionRecord,
    Provenance,
    QualityStatus,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_datetime(value: object) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    text = str(value).strip()
    if not text:
        return None
    text = text.replace("Z", "+00:00")
    if " " in text and "T" not in text:
        text = text.replace(" ", "T", 1)
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
            try:
                parsed = datetime.strptime(text.split("+")[0], fmt)
                break
            except ValueError:
                parsed = None
        if parsed is None:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _as_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _lookup(data: Mapping[str, Any], *keys: str) -> Any:
    upper_map = {str(key).upper(): value for key, value in data.items()}
    for key in keys:
        if key.upper() in upper_map:
            value = upper_map[key.upper()]
            if value is not None and str(value).strip() != "":
                return value
    return None


def _quality_for_cdm(
    miss_distance_m: float | None,
    relative_speed_m_s: float | None,
    has_covariance: bool,
    collision_probability: float | None,
) -> QualityStatus:
    reasons: list[str] = []
    status = QUALITY_COMPLETE
    if miss_distance_m is None:
        reasons.append("miss distance is unavailable")
        status = QUALITY_PARTIAL
    if relative_speed_m_s is None:
        reasons.append("relative speed is unavailable")
        status = QUALITY_PARTIAL
    if not has_covariance:
        reasons.append("authoritative covariance is unavailable")
        status = QUALITY_PARTIAL
    if collision_probability is None:
        reasons.append("collision probability was not provided by the source")
        if status == QUALITY_COMPLETE:
            status = QUALITY_PARTIAL
    return QualityStatus(status=status, reasons=tuple(reasons))


def _record_from_fields(
    fields: Mapping[str, Any],
    object1: Mapping[str, Any],
    object2: Mapping[str, Any],
    *,
    source: str,
    originator: str,
    raw_uri: str,
    ingested_at: datetime | None,
) -> ConjunctionRecord:
    message_id = _lookup(fields, "MESSAGE_ID", "CDM_ID", "ID")
    tca = _parse_datetime(_lookup(fields, "TCA", "TIME_CLOSEST_APPROACH"))
    object1_id = str(
        _lookup(object1, "OBJECT_DESIGNATOR", "CATALOG_NAME", "OBJECT_ID", "SAT_1_ID")
        or _lookup(fields, "SAT_1_ID", "SAT1_OBJECT_DESIGNATOR", "OBJECT1_ID")
        or ""
    ).strip()
    object2_id = str(
        _lookup(object2, "OBJECT_DESIGNATOR", "CATALOG_NAME", "OBJECT_ID", "SAT_2_ID")
        or _lookup(fields, "SAT_2_ID", "SAT2_OBJECT_DESIGNATOR", "OBJECT2_ID")
        or ""
    ).strip()
    object1_name = str(
        _lookup(object1, "OBJECT_NAME", "SAT_1_NAME")
        or _lookup(fields, "SAT_1_NAME", "OBJECT1_NAME")
        or object1_id
        or "OBJECT1"
    ).strip()
    object2_name = str(
        _lookup(object2, "OBJECT_NAME", "SAT_2_NAME")
        or _lookup(fields, "SAT_2_NAME", "OBJECT2_NAME")
        or object2_id
        or "OBJECT2"
    ).strip()
    miss_distance_m = _as_float(_lookup(fields, "MISS_DISTANCE", "MISS_DISTANCE_M"))
    relative_speed_m_s = _as_float(
        _lookup(fields, "RELATIVE_SPEED", "RELATIVE_SPEED_M_S", "RELATIVE_VELOCITY")
    )
    collision_probability = _as_float(
        _lookup(fields, "COLLISION_PROBABILITY", "PC", "PROBABILITY")
    )
    has_covariance = bool(
        _lookup(
            object1,
            "CR_R",
            "CT_T",
            "CN_N",
            "COVARIANCE_METHOD",
        )
        or _lookup(
            object2,
            "CR_R",
            "CT_T",
            "CN_N",
            "COVARIANCE_METHOD",
        )
        or _lookup(fields, "HAS_COVARIANCE")
    )
    creation_date = _parse_datetime(_lookup(fields, "CREATION_DATE", "CREATED"))
    originator_value = str(_lookup(fields, "ORIGINATOR") or originator or "").strip()
    ingested = ingested_at or _utcnow()
    if not message_id:
        message_id = f"cdm-{object1_id}-{object2_id}-{ingested.strftime('%Y%m%dT%H%M%S')}"
    if tca is None or not object1_id or not object2_id:
        quality = QualityStatus(
            status=QUALITY_INVALID,
            reasons=("TCA or object identifiers are missing",),
        )
        if tca is None:
            tca = ingested
        if not object1_id:
            object1_id = "UNKNOWN-1"
        if not object2_id:
            object2_id = "UNKNOWN-2"
    else:
        quality = _quality_for_cdm(
            miss_distance_m,
            relative_speed_m_s,
            has_covariance,
            collision_probability,
        )
    return ConjunctionRecord(
        message_id=str(message_id).strip(),
        tca=tca,
        object1_id=object1_id,
        object2_id=object2_id,
        object1_name=object1_name,
        object2_name=object2_name,
        miss_distance_m=miss_distance_m,
        relative_speed_m_s=relative_speed_m_s,
        collision_probability=collision_probability,
        has_covariance=has_covariance,
        creation_date=creation_date,
        provenance=Provenance(
            source=source,
            ingested_at=ingested,
            source_id=str(message_id).strip(),
            originator=originator_value,
            raw_uri=raw_uri,
        ),
        quality=quality,
    )


def _parse_kvn(text: str) -> list[dict[str, Any]]:
    header: dict[str, Any] = {}
    object1: dict[str, Any] = {}
    object2: dict[str, Any] = {}
    current = header
    object_count = 0
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("COMMENT"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip().upper()
        value = value.strip()
        if "[" in value and value.endswith("]"):
            value = value[: value.rfind("[")].strip()
        if key == "OBJECT":
            object_count += 1
            label = value.upper()
            if "2" in label or object_count >= 2:
                current = object2
            else:
                current = object1
            current["OBJECT"] = value
            continue
        current[key] = value
    if not header and not object1 and not object2:
        return []
    return [{"fields": header, "object1": object1, "object2": object2}]


def _object_from_json(data: Mapping[str, Any], prefix: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    prefix = prefix.upper()
    for key, value in data.items():
        upper = str(key).upper()
        if upper.startswith(prefix):
            trimmed = upper[len(prefix) :].lstrip("_")
            result[trimmed] = value
            if trimmed in {"ID", "DESIGNATOR"}:
                result["OBJECT_ID"] = value
                result["OBJECT_DESIGNATOR"] = value
            if trimmed == "NAME":
                result["OBJECT_NAME"] = value
        elif upper.startswith("SAT" + prefix[-1]):
            trimmed = upper[len("SAT" + prefix[-1]) :].lstrip("_")
            result[trimmed] = value
    for key in ("OBJECT_DESIGNATOR", "OBJECT_NAME", "CR_R", "CT_T", "CN_N"):
        prefixed = f"{prefix}_{key}"
        if prefixed in {str(item).upper() for item in data}:
            result[key] = _lookup(data, prefixed)
    return result


def _parse_json_document(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, Mapping):
        items = payload.get("cdms") or payload.get("CDM") or payload.get("data")
        if isinstance(items, list):
            payload = items
        else:
            payload = [payload]
    if not isinstance(payload, list):
        raise ValueError("CDM JSON must be an object or an array")
    parsed: list[dict[str, Any]] = []
    for item in payload:
        if not isinstance(item, Mapping):
            continue
        object1 = _object_from_json(item, "SAT_1")
        object2 = _object_from_json(item, "SAT_2")
        if not object1:
            object1 = _object_from_json(item, "OBJECT1")
        if not object2:
            object2 = _object_from_json(item, "OBJECT2")
        parsed.append({"fields": dict(item), "object1": object1, "object2": object2})
    return parsed


def parse_cdm_text(
    text: str,
    *,
    source: str = "cdm",
    originator: str = "",
    raw_uri: str = "",
    ingested_at: datetime | None = None,
) -> list[ConjunctionRecord]:
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    stripped = text.strip()
    if not stripped:
        raise ValueError("CDM text is empty")
    if stripped[0] in "[{":
        try:
            groups = _parse_json_document(json.loads(stripped))
        except json.JSONDecodeError as exc:
            raise ValueError("CDM JSON is malformed") from exc
    else:
        groups = _parse_kvn(stripped)
    if not groups:
        raise ValueError("no CDM records were found")
    records = [
        _record_from_fields(
            group["fields"],
            group["object1"],
            group["object2"],
            source=source,
            originator=originator,
            raw_uri=raw_uri,
            ingested_at=ingested_at,
        )
        for group in groups
    ]
    return records
