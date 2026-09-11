"""Conjunction screening endpoints."""
 
from fastapi import APIRouter, HTTPException
 
from orbit_engine import PropagationError, TLEValidationError
 
from ..schemas.conjunction import ConjunctionResponse, ScreenRequest
from ..services.collision_service import screen_conjunction
from ..services.data_service import ObjectNotFoundError, find_object
from ..services.ml_service import MLServiceError
 
router = APIRouter(prefix="/api/conjunctions", tags=["conjunctions"])
 
 
@router.post("/screen", response_model=ConjunctionResponse)
def screen(request: ScreenRequest) -> ConjunctionResponse:
    try:
        object_a = find_object(request.object_a)
        object_b = find_object(request.object_b)
    except ObjectNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    try:
        result = screen_conjunction(
            object_a,
            object_b,
            request.start,
            request.end,
            request.step_minutes,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except TLEValidationError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except PropagationError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
    except MLServiceError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    return result