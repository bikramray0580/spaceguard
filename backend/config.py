"""Backend configuration."""
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "orbital_data.json"
DEFAULT_STEP_MINUTES = 5.0
DEFAULT_DISTANCE_THRESHOLD_KM = 1000.0
DEFAULT_MAX_SCREEN_OBJECTS = 25