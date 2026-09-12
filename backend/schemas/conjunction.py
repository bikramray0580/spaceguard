"""Conjunction screening API schemas."""
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

from ..config import (
    DEFAULT_DISTANCE_THRESHOLD_KM,
    DEFAULT_MAX_SCREEN_OBJECTS,
    DEFAULT_STEP_MINUTES,
)


class ScreenRequest(BaseModel):
    object_a: str
    object_b: str
    start: datetime
    end: datetime
    step_minutes: float = Field(default=DEFAULT_STEP_MINUTES, gt=0, le=60)

    @field_validator("start", "end")
    @classmethod
    def require_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must be timezone-aware (use UTC)")
        return value


class CatalogueScreenRequest(BaseModel):
    start: datetime
    end: datetime
    object_ids: list[str] | None = None
    step_minutes: float = Field(default=DEFAULT_STEP_MINUTES, gt=0, le=60)
    distance_threshold_km: float = Field(default=DEFAULT_DISTANCE_THRESHOLD_KM, ge=0)
    max_objects: int = Field(default=DEFAULT_MAX_SCREEN_OBJECTS, ge=2, le=100)

    @field_validator("start", "end")
    @classmethod
    def require_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must be timezone-aware (use UTC)")
        return value


class MLPrediction(BaseModel):
    risk_probability: float | None = None
    risk_score: int | None = None
    risk_category: str | None = None


class ConjunctionResponse(BaseModel):
    object_a: str
    object_b: str
    time_of_closest_approach: datetime
    miss_distance_km: float
    relative_velocity_km_s: float
    risk_level: str
    risk_reason: str
    ml_prediction: MLPrediction | None = None
    trend: str
    recommended_action: str
    confidence: str
    pc: float | None
    pc_status: str
    covariance_status: str
    provenance: dict


class ScreeningCandidateResponse(BaseModel):
    object_a: str
    object_b: str
    closest_sample_time: datetime
    closest_sample_distance_km: float
    bracket_start: datetime
    bracket_end: datetime


class CatalogueScreenResponse(BaseModel):
    object_ids: list[str]
    object_count: int
    catalogue_object_count: int
    pair_count: int
    candidate_count: int
    sample_count: int
    threshold_km: float
    candidates: list[ScreeningCandidateResponse]
    assessments: list[ConjunctionResponse]
