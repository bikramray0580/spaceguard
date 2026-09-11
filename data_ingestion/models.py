"""Common ingestion schema with provenance and quality status."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping


QUALITY_COMPLETE = "COMPLETE"
QUALITY_PARTIAL = "PARTIAL"
QUALITY_DEGRADED = "DEGRADED"
QUALITY_INVALID = "INVALID"
_QUALITY_LEVELS = frozenset(
    {QUALITY_COMPLETE, QUALITY_PARTIAL, QUALITY_DEGRADED, QUALITY_INVALID}
)

RECORD_ORBITAL_ELEMENT = "orbital_element"
RECORD_CONJUNCTION = "conjunction"


def _require_non_empty_str(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


def _require_datetime(value: object, name: str) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError(f"{name} must be a datetime instance")
    return value


@dataclass(frozen=True)
class Provenance:
    """Origin metadata for an ingested record."""

    source: str
    ingested_at: datetime
    source_id: str = ""
    originator: str = ""
    raw_uri: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "source", _require_non_empty_str(self.source, "source"))
        object.__setattr__(self, "ingested_at", _require_datetime(self.ingested_at, "ingested_at"))
        if self.source_id is None:
            object.__setattr__(self, "source_id", "")
        else:
            object.__setattr__(self, "source_id", str(self.source_id).strip())
        if self.originator is None:
            object.__setattr__(self, "originator", "")
        else:
            object.__setattr__(self, "originator", str(self.originator).strip())
        if self.raw_uri is None:
            object.__setattr__(self, "raw_uri", "")
        else:
            object.__setattr__(self, "raw_uri", str(self.raw_uri).strip())


@dataclass(frozen=True)
class QualityStatus:
    """Data-quality assessment for an ingested record."""

    status: str
    reasons: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        status = _require_non_empty_str(self.status, "status").upper()
        if status not in _QUALITY_LEVELS:
            raise ValueError(f"status must be one of {sorted(_QUALITY_LEVELS)}")
        object.__setattr__(self, "status", status)
        reasons = self.reasons or ()
        if isinstance(reasons, str):
            reasons = (reasons,)
        cleaned = tuple(str(item).strip() for item in reasons if str(item).strip())
        object.__setattr__(self, "reasons", cleaned)


@dataclass(frozen=True)
class TLERecord:
    """Parsed two-line element set."""

    norad_id: int
    name: str
    line1: str
    line2: str
    epoch: datetime
    classification: str
    intl_designator: str
    inclination_deg: float
    raan_deg: float
    eccentricity: float
    arg_perigee_deg: float
    mean_anomaly_deg: float
    mean_motion_rev_per_day: float
    bstar: float
    provenance: Provenance
    quality: QualityStatus

    def __post_init__(self) -> None:
        if not isinstance(self.norad_id, int) or self.norad_id <= 0:
            raise ValueError("norad_id must be a positive integer")
        object.__setattr__(self, "name", _require_non_empty_str(self.name, "name"))
        object.__setattr__(self, "line1", _require_non_empty_str(self.line1, "line1"))
        object.__setattr__(self, "line2", _require_non_empty_str(self.line2, "line2"))
        object.__setattr__(self, "epoch", _require_datetime(self.epoch, "epoch"))
        if not isinstance(self.provenance, Provenance):
            raise TypeError("provenance must be a Provenance instance")
        if not isinstance(self.quality, QualityStatus):
            raise TypeError("quality must be a QualityStatus instance")


@dataclass(frozen=True)
class ConjunctionRecord:
    """Parsed conjunction data message."""

    message_id: str
    tca: datetime
    object1_id: str
    object2_id: str
    object1_name: str
    object2_name: str
    miss_distance_m: float | None
    relative_speed_m_s: float | None
    collision_probability: float | None
    has_covariance: bool
    creation_date: datetime | None
    provenance: Provenance
    quality: QualityStatus

    def __post_init__(self) -> None:
        object.__setattr__(self, "message_id", _require_non_empty_str(self.message_id, "message_id"))
        object.__setattr__(self, "tca", _require_datetime(self.tca, "tca"))
        object.__setattr__(self, "object1_id", _require_non_empty_str(self.object1_id, "object1_id"))
        object.__setattr__(self, "object2_id", _require_non_empty_str(self.object2_id, "object2_id"))
        if not isinstance(self.has_covariance, bool):
            raise TypeError("has_covariance must be a bool")
        if not isinstance(self.provenance, Provenance):
            raise TypeError("provenance must be a Provenance instance")
        if not isinstance(self.quality, QualityStatus):
            raise TypeError("quality must be a QualityStatus instance")
        if self.collision_probability is not None:
            try:
                pc = float(self.collision_probability)
            except (TypeError, ValueError) as exc:
                raise TypeError("collision_probability must be numeric") from exc
            if not 0.0 <= pc <= 1.0:
                raise ValueError("collision_probability must be between 0 and 1")
            object.__setattr__(self, "collision_probability", pc)


@dataclass(frozen=True)
class NormalizedRecord:
    """Common event schema exchanged with downstream modules."""

    record_type: str
    object_id: str
    epoch: datetime
    frame: str
    data: Mapping[str, Any]
    provenance: Provenance
    quality: QualityStatus
    name: str = ""

    def __post_init__(self) -> None:
        record_type = _require_non_empty_str(self.record_type, "record_type")
        if record_type not in {RECORD_ORBITAL_ELEMENT, RECORD_CONJUNCTION}:
            raise ValueError("record_type must be orbital_element or conjunction")
        object.__setattr__(self, "record_type", record_type)
        object.__setattr__(self, "object_id", _require_non_empty_str(self.object_id, "object_id"))
        object.__setattr__(self, "epoch", _require_datetime(self.epoch, "epoch"))
        object.__setattr__(self, "frame", _require_non_empty_str(self.frame, "frame"))
        if not isinstance(self.data, Mapping):
            raise TypeError("data must be a mapping")
        object.__setattr__(self, "data", dict(self.data))
        if not isinstance(self.provenance, Provenance):
            raise TypeError("provenance must be a Provenance instance")
        if not isinstance(self.quality, QualityStatus):
            raise TypeError("quality must be a QualityStatus instance")
        name = self.name if self.name is not None else ""
        object.__setattr__(self, "name", str(name).strip())
