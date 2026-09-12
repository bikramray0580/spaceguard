"""Conjunction screening endpoints."""
from fastapi import APIRouter, HTTPException
from ..schemas.conjunction import (
    CatalogueScreenRequest,
    CatalogueScreenResponse,
    ConjunctionResponse,
    ScreeningCandidateResponse,
    ScreenRequest,
)
from ..services.conjunction_service import screen_catalogue, screen_conjunction

router = APIRouter(prefix="/api/conjunctions", tags=["conjunctions"])


def _conjunction_response(result, assessment) -> ConjunctionResponse:
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


@router.post("/screen", response_model=ConjunctionResponse)
def screen(request: ScreenRequest):
    try:
        result, assessment = screen_conjunction(
            request.object_a,
            request.object_b,
            request.start,
            request.end,
            request.step_minutes,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return _conjunction_response(result, assessment)


@router.post("/catalogue-screen", response_model=CatalogueScreenResponse)
def catalogue_screen(request: CatalogueScreenRequest):
    try:
        object_ids, catalogue_count, pair_count, result, assessments = screen_catalogue(
            request.start,
            request.end,
            request.object_ids,
            request.step_minutes,
            request.distance_threshold_km,
            request.max_objects,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return CatalogueScreenResponse(
        object_ids=list(object_ids),
        object_count=len(object_ids),
        catalogue_object_count=catalogue_count,
        pair_count=pair_count,
        candidate_count=len(result.candidates),
        sample_count=result.sample_count,
        threshold_km=result.threshold_km,
        candidates=[
            ScreeningCandidateResponse(
                object_a=candidate.object_a_id,
                object_b=candidate.object_b_id,
                closest_sample_time=candidate.closest_sample_time,
                closest_sample_distance_km=candidate.closest_sample_distance_km,
                bracket_start=candidate.bracket_start,
                bracket_end=candidate.bracket_end,
            )
            for candidate in result.candidates
        ],
        assessments=[_conjunction_response(result, assessment) for result, assessment in assessments],
    )
