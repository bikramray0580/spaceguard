from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_PATH = DATA_DIR / "training_data.csv"


def generate_training_data(n_samples=1000):
    rng = np.random.default_rng(42)

    miss_distance = rng.uniform(0.1, 50.0, n_samples)
    relative_velocity = rng.uniform(0.01, 15.0, n_samples)
    time_to_tca = rng.uniform(0.01, 48.0, n_samples)
    altitude_a = rng.uniform(300.0, 2000.0, n_samples)
    altitude_b = rng.uniform(300.0, 2000.0, n_samples)

    altitude_difference = abs(altitude_a - altitude_b)

    risk = (
        (miss_distance <= 1.0)
        | (
            (miss_distance <= 10.0)
            & (relative_velocity >= 5.0)
        )
        | (
            (miss_distance <= 20.0)
            & (time_to_tca <= 6.0)
            & (altitude_difference <= 50.0)
        )
    ).astype(int)

    df = pd.DataFrame({
        "miss_distance_km": miss_distance,
        "relative_velocity_km_s": relative_velocity,
        "time_to_tca_hours": time_to_tca,
        "object_a_altitude_km": altitude_a,
        "object_b_altitude_km": altitude_b,
        "altitude_difference_km": altitude_difference,
        "risk": risk
    })

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(DATA_PATH, index=False)

    print(f"Generated {len(df)} training samples.")
    print(f"Saved to: {DATA_PATH}")


if __name__ == "__main__":
    generate_training_data()