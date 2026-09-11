from pathlib import Path
from typing import Mapping

import joblib
import pandas as pd

from .features import FEATURES

MODEL_PATH = Path(__file__).resolve().parent / "models" / "risk_model.pkl"


def predict_features(features: Mapping[str, float], *, model_path: Path = MODEL_PATH) -> dict[str, object]:
    """Score a feature dictionary created by ``ml.features.build_features``."""
    missing = [name for name in FEATURES if name not in features]
    if missing:
        raise ValueError(f"missing ML features: {', '.join(missing)}")
    if not model_path.exists():
        raise FileNotFoundError(f"trained model not found: {model_path}. Run `python -m ml.train_model` first.")
    model = joblib.load(model_path)
    data = pd.DataFrame([{name: features[name] for name in FEATURES}])
    probabilities = model.predict_proba(data)[0]
    classes = list(model.classes_)
    positive_index = classes.index(1) if 1 in classes else classes.index("RISK")
    probability = float(probabilities[positive_index])

    risk_score = round(probability * 100)

    if risk_score >= 70:
        category = "HIGH"
    elif risk_score >= 40:
        category = "MEDIUM"
    else:
        category = "LOW"

    return {
        "risk_probability": round(float(probability), 4),
        "risk_score": risk_score,
        "risk_category": category
    }


if __name__ == "__main__":

    print("Use predict_features() with the output of ml.features.build_features().")
