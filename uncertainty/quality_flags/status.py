from __future__ import annotations
from dataclasses import dataclass
from enum import Enum


class UncertaintyStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    ESTIMATED = "ESTIMATED"
    UNAVAILABLE = "UNAVAILABLE"
    INVALID = "INVALID"


@dataclass(frozen=True)
class UncertaintyQuality:
    status: UncertaintyStatus
    reason: str
    warnings: tuple[str, ...] = ()

    @property
    def pc_authoritative(self) -> bool:
        """Uncertainty availability alone never asserts that Pc was calculated."""
        return False
