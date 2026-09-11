"""Conjunction screening endpoint."""
from fastapi import APIRouter, HTTPException
from ..schemas.conjunction import ConjunctionResponse
from ..schemas.conjunction import ScreenRequest
from ..services.conjunction_service import screen_conjunction

router = APIRouter(prefix="/api/conjunctions", tags=["conjunctions"])


@router.post("/screen", response_model=ConjunctionResponse)
def screen(request: ScreenRequest):
    try:
        result, assessment = screen_conjunction(
            request.object_a, request.object_b, request.start, request.end
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return ConjunctionResponse(
        object_a=result.object_a_id,
        object_b=result.object_b_id,
        time_of_closest_approach=result.tca,
        miss_distance_km=result.miss_distance_km,
        relative_velocity_km_s=result.relative_speed_km_s,
        risk_level=assessment.risk_level.value,
        risk_reason=assessment.explanation,
        ml_prediction=None,
        trend=assessment.trend.value,
        recommended_action=assessment.recommended_action.value,
        confidence=assessment.confidence.value,
        pc=assessment.pc,
        pc_status=assessment.pc_status.value,
        covariance_status=assessment.quality_status,
        provenance=dict(assessment.provenance),
    )
