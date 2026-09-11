"""What-If maneuver API."""
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..services.maneuver_service import evaluate_maneuver

router = APIRouter(prefix="/api/simulation", tags=["simulation"])


class ManeuverRequest(BaseModel):
    object_a: str
    object_b: str
    object_id: str
    start: datetime
    end: datetime
    step_minutes: float = Field(default=5, gt=0, le=60)
    delta_v_m_s: float = Field(gt=0, le=1000)
    direction: str
    execution_time: datetime


@router.post("/maneuver")
def maneuver(request: ManeuverRequest):
    try:
        return evaluate_maneuver(
            request.object_a,
            request.object_b,
            request.object_id,
            request.start,
            request.end,
            request.delta_v_m_s,
            request.direction,
            request.execution_time,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"maneuver evaluation failed: {exc}") from exc
