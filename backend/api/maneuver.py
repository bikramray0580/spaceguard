"""What-If API boundary.

The main branch currently exposes the real maneuver client contract in the
frontend, but the maneuver physics implementation is intentionally kept out
of this integration commit rather than returning fabricated post-burn data.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/simulation", tags=["simulation"])


class ManeuverRequest(BaseModel):
    object_a: str
    object_b: str
    object_id: str
    start: str
    end: str
    step_minutes: float = 5
    delta_v_m_s: float
    direction: str
    execution_time: str


@router.post("/maneuver")
def maneuver(_: ManeuverRequest):
    raise HTTPException(
        status_code=501,
        detail="What-If maneuver physics is not yet wired to the main-branch integration API; no fabricated scenario is returned.",
    )
