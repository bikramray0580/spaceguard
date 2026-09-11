"""Coarse pair screen. Candidates require detailed TCA refinement."""
from __future__ import annotations
from datetime import datetime, timedelta
from itertools import combinations
from typing import Protocol, Sequence
from .models import ScreeningCandidate, ScreeningResult
from ..models import StateVector
from ..relative_velocity.calculator import norm, subtract

class MultiStatePropagator(Protocol):
    def state_at(self, object_id: str, when: datetime) -> StateVector: ...

def broad_screen(propagator: MultiStatePropagator, object_ids: Sequence[str], start: datetime, end: datetime,
                 *, sampling_interval_seconds: float, distance_threshold_km: float) -> ScreeningResult:
    if sampling_interval_seconds <= 0 or distance_threshold_km < 0: raise ValueError("screening interval must be positive and threshold non-negative")
    if start.tzinfo is None or end.tzinfo is None or end <= start: raise ValueError("screening times must be ordered UTC-aware datetimes")
    count = int((end-start).total_seconds() // sampling_interval_seconds) + 1
    times = [start + timedelta(seconds=index * sampling_interval_seconds) for index in range(count)]
    if times[-1] != end: times.append(end)
    candidates: list[ScreeningCandidate] = []
    for a_id, b_id in combinations(object_ids, 2):
        distances = []
        for when in times:
            a, b = propagator.state_at(a_id, when), propagator.state_at(b_id, when)
            if a.reference_frame != b.reference_frame: raise ValueError("screening states must share a reference frame")
            distances.append(norm(subtract(a.position_km, b.position_km)))
        index = min(range(len(times)), key=distances.__getitem__)
        if distances[index] <= distance_threshold_km:
            left, right = times[max(0,index-1)], times[min(len(times)-1,index+1)]
            candidates.append(ScreeningCandidate(a_id, b_id, times[index], distances[index], left, right))
    return ScreeningResult(tuple(candidates), len(times), distance_threshold_km)
