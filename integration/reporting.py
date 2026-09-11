"""Human-readable presentation of completed A -> B -> C pipeline results."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone

from collision_engine.models import ConjunctionEvent

from .models import PipelineRun


RISK_PRESENTATION = {
    "LOW": "🟢 LOW RISK",
    "MEDIUM": "🟡 MEDIUM RISK",
    "HIGH": "🔴 HIGH RISK",
}


def _format_timestamp(timestamp: datetime, *, include_at: bool = False) -> str:
    """Format an existing aware timestamp in a portable, UTC-only display form."""
    utc_timestamp = timestamp.astimezone(timezone.utc)
    separator = " at " if include_at else " "
    return (
        f"{utc_timestamp.strftime('%B')} {utc_timestamp.day}, {utc_timestamp.year}"
        f"{separator}{utc_timestamp.strftime('%H:%M')} UTC"
    )


def _format_distance(distance_km: float) -> str:
    """Format an existing miss distance without changing its value."""
    if abs(distance_km) >= 100.0:
        return f"{distance_km:,.0f} km"
    return f"{distance_km:,.2f} km"


def _risk_explanation(event: ConjunctionEvent) -> str:
    """Explain the existing classification using only its existing values."""
    distance = _format_distance(event.miss_distance_km)
    if event.risk_level == "HIGH":
        return (
            f"The predicted separation of {distance} is within the project's high-risk "
            "screening threshold. This pair should be flagged for further orbital analysis."
        )
    if event.risk_level == "MEDIUM":
        return (
            f"The predicted separation of {distance} falls within the project's medium-risk "
            "screening range. Further review is recommended."
        )
    return (
        f"The two satellites remained {distance} apart at their closest sampled approach. "
        "No immediate collision concern was detected by this screening run."
    )


def _format_pair(event: ConjunctionEvent) -> str:
    """Render one existing ConjunctionEvent without recalculating it."""
    risk = RISK_PRESENTATION.get(event.risk_level, f"{event.risk_level} RISK")
    return "\n".join(
        (
            f"🛰️ Satellite pair: {event.object_a} ↔ {event.object_b}",
            "",
            "Closest approach:",
            _format_timestamp(event.time_of_closest_approach, include_at=True),
            "",
            "Minimum separation:",
            _format_distance(event.miss_distance_km),
            "",
            "Relative speed:",
            f"{event.relative_velocity_km_s:.2f} km/s",
            "",
            "Risk assessment:",
            risk,
            "",
            "Explanation:",
            _risk_explanation(event),
        )
    )


def render_safety_report(run: PipelineRun) -> str:
    """Return a human-readable report from existing pipeline results.

    This function is presentation-only: it performs no propagation, conjunction
    search, risk classification, or numerical recalculation.
    """
    risk_counts = Counter(event.risk_level for event in run.conjunctions)
    divider = "=" * 50
    section_divider = "-" * 50
    lines = [
        divider,
        "SPACEGUARD",
        "ORBITAL SAFETY REPORT",
        divider,
        "",
        f"Data source: {run.source}",
        f"Data fetched: {_format_timestamp(run.fetched_at)}",
        f"Objects analyzed: {len(run.object_ids)}",
        f"Satellite pairs screened: {run.pair_count}",
        "",
        section_divider,
        "SAFETY SUMMARY",
        section_divider,
        "",
        f"🟢 LOW RISK       {risk_counts['LOW']}",
        f"🟡 MEDIUM RISK    {risk_counts['MEDIUM']}",
        f"🔴 HIGH RISK      {risk_counts['HIGH']}",
        "",
        section_divider,
        "PAIR ANALYSIS",
        section_divider,
        "",
    ]
    for index, event in enumerate(run.conjunctions):
        lines.append(_format_pair(event))
        if index != len(run.conjunctions) - 1:
            lines.extend(("", section_divider, ""))
    return "\n".join(lines)


def render_debug_report(run: PipelineRun) -> str:
    """Return the previous compact diagnostic output as an alternate mode."""
    lines = [
        "SPACEGUARD A -> B -> C PIPELINE",
        f"Snapshot source: {run.source}",
        f"Snapshot fetched at: {run.fetched_at.isoformat().replace('+00:00', 'Z')}",
        "Note: this is the stored CelesTrak snapshot, not live data.",
        f"Objects propagated: {len(run.object_ids)} ({', '.join(run.object_ids)})",
        f"Pairs analyzed: {run.pair_count}",
        f"Satellite pairs screened: {run.pair_count}",
    ]
    for event in run.conjunctions:
        lines.extend(
            (
                "",
                f"{event.object_a} <-> {event.object_b}",
                f"  Closest approach: {event.time_of_closest_approach.isoformat().replace('+00:00', 'Z')}",
                f"  Miss distance: {event.miss_distance_km:.3f} km",
                f"  Relative velocity: {event.relative_velocity_km_s:.3f} km/s",
                f"  Risk: {event.risk_level}",
            )
        )
    return "\n".join(lines)
