"""Run the real checked-in CelesTrak snapshot through the A -> B -> C pipeline.

Run from the project root with:
    python -m integration.demo_pipeline
"""

import argparse
from pathlib import Path

from .pipeline import load_orbital_data, run_pipeline
from .reporting import render_debug_report, render_safety_report


DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "orbital_data.json"


def main() -> None:
    """Print a bounded real-data snapshot analysis; no live network request occurs."""
    parser = argparse.ArgumentParser(description="Run the stored SpaceGuard A -> B -> C demo.")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="show the previous compact diagnostic output instead of the safety report",
    )
    args = parser.parse_args()
    snapshot = load_orbital_data(DATA_PATH)
    run = run_pipeline(
        DATA_PATH,
        start_time=snapshot.fetched_at,
        duration_minutes=30,
        step_seconds=300,
        max_objects=10,
    )
    report = render_debug_report(run) if args.debug else render_safety_report(run)
    print(report)


if __name__ == "__main__":
    main()
