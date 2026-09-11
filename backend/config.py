"""Backend configuration."""

from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "orbital_data.json"

DEFAULT_STEP_MINUTES = 5.0
