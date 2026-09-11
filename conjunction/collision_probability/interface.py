from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, Literal
from ..models import ConjunctionResult

@dataclass(frozen=True)
class CollisionProbabilityInput:
    conjunction: ConjunctionResult
    combined_position_covariance_km2: tuple[tuple[float, float], tuple[float, float]] | None = None

@dataclass(frozen=True)
class CollisionProbabilityResult:
    status: Literal["NOT_AVAILABLE_WITHOUT_COVARIANCE"] = "NOT_AVAILABLE_WITHOUT_COVARIANCE"
    probability: None = None
    reason: str = "A scientifically valid Pc requires covariance/uncertainty input."

class CollisionProbabilityCalculator(Protocol):
    def calculate(self, input: CollisionProbabilityInput) -> CollisionProbabilityResult: ...

class UnavailableWithoutCovarianceCalculator:
    """Safe default until a covariance-aware implementation is supplied."""
    def calculate(self, input: CollisionProbabilityInput) -> CollisionProbabilityResult:
        return CollisionProbabilityResult()
