"""Risk trend calculation."""

from .models import RiskInput, Trend


def calculate_trend(current: RiskInput) -> Trend:
    """Compare the current event with its immediately previous assessment.

    Trend is deliberately UNKNOWN when no comparable prior observation exists.
    Lower miss distance or higher authoritative Pc is treated as worsening.
    """
    previous = current.previous
    if previous is None:
        return Trend.UNKNOWN

    if (
        current.pc is not None
        and previous.pc is not None
        and current.pc_status.value == "AUTHORITATIVE"
        and previous.pc_status.value == "AUTHORITATIVE"
    ):
        if current.pc > previous.pc:
            return Trend.WORSENING
        if current.pc < previous.pc:
            return Trend.IMPROVING

    if current.miss_distance_km < previous.miss_distance_km:
        return Trend.WORSENING
    if current.miss_distance_km > previous.miss_distance_km:
        return Trend.IMPROVING
    return Trend.STABLE
