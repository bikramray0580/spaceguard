from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from ..models import TcaQuality

@dataclass(frozen=True)
class TcaSearchResult:
    tca: datetime
    quality: TcaQuality
