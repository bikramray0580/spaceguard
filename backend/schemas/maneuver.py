"""Pydantic models for What-If orbital maneuver analysis."""

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from .conjunction import ConjunctionResponse

ManeuverDirection = Literal[
    "PROGRADE",
    "RETROGRADE",
    "RADIAL_OUT",
    "RADIAL_IN",
    "NORMAL",
    "ANTI_NORMAL",
]


class ManeuverRequest(BaseModel):
    """Request to apply one impulsive maneuver to a conjunction participant."""

    object_a: str = Field(min_length=1)
    object_b: str = Field(min_length=1)
    object_id: str = Field(min_length=1)
    start: datetime
    end: datetime
    step_minutes: float = Field(default=5.0, gt=0, le=60)
    delta_v_m_s: float = Field(gt=0, le=1000)
    direction: ManeuverDirection
    execution_time: datetime

    @field_validator("start", "end", "execution_time")
    @classmethod
    def normalize_to_utc(cls, value: datetime) -> datetime:
        """Require an aware timestamp and normalize it to UTC."""
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must be timezone-aware (use UTC)")
        return value.astimezone(timezone.utc)

    @model_validator(mode="after")
    def validate_request(self) -> "ManeuverRequest":
        if self.object_a == self.object_b:
            raise ValueError("object_a and object_b must be different")
        if self.object_id not in {self.object_a, self.object_b}:
            raise ValueError("object_id must be one of object_a or object_b")
        if self.end <= self.start:
            raise ValueError("end must be later than start")
        if not self.start <= self.execution_time < self.end:
            raise ValueError("execution_time must be within the screening window")
        return self


class ManeuverMetadata(BaseModel):
    """Applied maneuver details returned with the scenario result."""

    object_id: str
    delta_v_m_s: float
    direction: ManeuverDirection
    execution_time: datetime
    state_frame: Literal["TEME"] = "TEME"
    maneuver_frame: Literal["RTN"] = "RTN"


class RiskChange(BaseModel):
    """Summary of the deterministic risk change between scenarios."""

    before: str
    after: str
    improved: bool
    worsened: bool
    unchanged: bool
    miss_distance_delta_km: float
    relative_velocity_delta_km_s: float


class ManeuverScenarioResult(BaseModel):
    """Before/after conjunction assessment for a What-If maneuver."""

    status: Literal["complete"] = "complete"
    maneuver: ManeuverMetadata
    before: ConjunctionResponse
    after: ConjunctionResponse
    risk_change: RiskChange
