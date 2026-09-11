"""Schemas for orbit propagation requests and responses."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from ..config import DEFAULT_STEP_MINUTES


class PropagateRequest(BaseModel):
    """Propagate one object, a list of objects, or all objects (default)."""

    object_id: str | list[str] | None = None
    start: datetime
    end: datetime
    step_minutes: float = Field(default=DEFAULT_STEP_MINUTES, gt=0)

    @field_validator("start", "end")
    @classmethod
    def require_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must be timezone-aware (use UTC)")
        return value


class Position(BaseModel):
    x_km: float
    y_km: float
    z_km: float


class Velocity(BaseModel):
    x_km_s: float
    y_km_s: float
    z_km_s: float


class PropagationResult(BaseModel):
    object_id: str
    object_name: str
    timestamp: datetime
    position: Position
    velocity: Velocity
    coordinate_frame: str


class OrbitResult(BaseModel):
    object_id: str
    object_name: str
    states: list[PropagationResult]
