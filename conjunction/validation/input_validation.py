from __future__ import annotations
from datetime import datetime
from ..models import StateVector

def validate_assessment_input(object_a_id: str, object_b_id: str, start: datetime, end: datetime) -> None:
    if not object_a_id or not object_b_id or object_a_id == object_b_id: raise ValueError("two distinct, non-empty object IDs are required")
    if any(value.tzinfo is None or value.utcoffset() is None for value in (start, end)): raise ValueError("start and end must be UTC-aware datetimes")
    if end <= start: raise ValueError("end must be later than start")

def validate_state_pair(a: StateVector, b: StateVector, object_a_id: str, object_b_id: str, when: datetime) -> None:
    if a.object_id != object_a_id or b.object_id != object_b_id: raise ValueError("propagator returned state for an unexpected object")
    if a.epoch != when or b.epoch != when: raise ValueError("propagator returned a state at an unexpected epoch")
    if a.reference_frame != b.reference_frame: raise ValueError(f"inconsistent reference frames: {a.reference_frame} and {b.reference_frame}")
