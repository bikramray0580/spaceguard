"""Data models used only to connect ingestion, propagation, and conjunctions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from collision_engine.models import ConjunctionEvent, OrbitalState
from orbit_engine.models import PropagationResult


@dataclass(frozen=True)
class SatelliteTLE:
    """A validated TLE record from Person A's orbital-data JSON snapshot."""

    object_id: str
    name: str
    line1: str
    line2: str
    epoch: datetime


@dataclass(frozen=True)
class LoadedOrbitalData:
    """Validated metadata and records read from an orbital-data snapshot."""

    source: str
    fetched_at: datetime
    objects: tuple[SatelliteTLE, ...]


@dataclass(frozen=True)
class PipelineRun:
    """Results of propagating a bounded object set and analyzing every pair."""

    source: str
    fetched_at: datetime
    timestamps: tuple[datetime, ...]
    propagated_by_object: dict[str, tuple[PropagationResult, ...]]
    states_by_object: dict[str, tuple[OrbitalState, ...]]
    conjunctions: tuple[ConjunctionEvent, ...]

    @property
    def object_ids(self) -> tuple[str, ...]:
        """Return selected source object IDs in propagation order."""
        return tuple(self.propagated_by_object)

    @property
    def pair_count(self) -> int:
        """Return the number of object pairs analyzed."""
        object_count = len(self.propagated_by_object)
        return object_count * (object_count - 1) // 2
