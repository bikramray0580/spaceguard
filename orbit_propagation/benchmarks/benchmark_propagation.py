"""Reproducible runtime benchmark for SGP4 time-window propagation.

This harness measures wall-clock cost and throughput of
``SGP4Propagator.propagate_window``. It does not compare predicted
states against a later orbit solution.

Scientific prediction-error validation is not available in this
repository: there is no trusted reference/later orbit dataset to
compute position or velocity residuals.
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

from orbit_propagation.sgp4.propagator import SGP4Propagator

ISS_TLE_LINE1 = "1 25544U 98067A   19343.69339541  .00001764  00000-0  38792-4 0  9991"
ISS_TLE_LINE2 = "2 25544  51.6439 211.2001 0007417  17.6667  85.6398 15.50103472202482"
ISS_EPOCH = datetime(2019, 12, 9, 16, 38, 30, tzinfo=timezone.utc)

# Horizons are local, deterministic windows around the fixed TLE epoch.
SCENARIOS = (
    {"name": "5_min", "horizon_seconds": 300, "step_seconds": 60},
    {"name": "1_hour", "horizon_seconds": 3600, "step_seconds": 60},
    {"name": "6_hour", "horizon_seconds": 21600, "step_seconds": 60},
    {"name": "1_day", "horizon_seconds": 86400, "step_seconds": 300},
)


def _repeatability_ok(propagator: SGP4Propagator, start, end, step: float) -> bool:
    first = propagator.propagate_window(ISS_TLE_LINE1, ISS_TLE_LINE2, start, end, step)
    second = propagator.propagate_window(ISS_TLE_LINE1, ISS_TLE_LINE2, start, end, step)
    return first == second


def run_benchmarks() -> list[dict]:
    propagator = SGP4Propagator()
    results = []
    for scenario in SCENARIOS:
        start = ISS_EPOCH
        end = ISS_EPOCH + timedelta(seconds=scenario["horizon_seconds"])
        step = scenario["step_seconds"]

        t0 = time.perf_counter()
        states = propagator.propagate_window(
            ISS_TLE_LINE1,
            ISS_TLE_LINE2,
            start,
            end,
            step,
        )
        elapsed = time.perf_counter() - t0
        n_states = len(states)
        throughput = n_states / elapsed if elapsed > 0 else float("inf")

        results.append(
            {
                "name": scenario["name"],
                "horizon_seconds": scenario["horizon_seconds"],
                "step_seconds": step,
                "n_states": n_states,
                "runtime_seconds": elapsed,
                "states_per_second": throughput,
                "deterministic": _repeatability_ok(propagator, start, end, step),
            }
        )
    return results


def _format_row(result: dict) -> str:
    return (
        f"{result['name']:<10} "
        f"{result['horizon_seconds']:>10} "
        f"{result['step_seconds']:>10} "
        f"{result['n_states']:>10} "
        f"{result['runtime_seconds']:>12.6f} "
        f"{result['states_per_second']:>14.1f} "
        f"{str(result['deterministic']):>13}"
    )


def main() -> None:
    print("SGP4 time-window propagation benchmark")
    print("TLE fixture: ISS 25544 (2019-12-09), local only, no network")
    print("Reference orbit data: not present; accuracy residuals are not computed")
    print()
    header = (
        f"{'scenario':<10} "
        f"{'horizon_s':>10} "
        f"{'step_s':>10} "
        f"{'n_states':>10} "
        f"{'runtime_s':>12} "
        f"{'states/s':>14} "
        f"{'deterministic':>13}"
    )
    print(header)
    print("-" * len(header))
    for result in run_benchmarks():
        print(_format_row(result))
    print()
    print(
        "Note: these numbers measure runtime and throughput only. "
        "They are not a claim of orbital prediction accuracy."
    )


if __name__ == "__main__":
    main()
