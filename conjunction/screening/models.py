from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class ScreeningCandidate:
    object_a_id: str
    object_b_id: str
    closest_sample_time: datetime
    closest_sample_distance_km: float
    bracket_start: datetime
    bracket_end: datetime

@dataclass(frozen=True)
class ScreeningResult:
    candidates: tuple[ScreeningCandidate, ...]
    sample_count: int
    threshold_km: float
