import joblib
from pathlib import Path
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

from .features import FEATURES

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "training_data.csv"
MODEL_PATH = BASE_DIR / "models" / "risk_model.pkl"


def train(data_path: Path = DATA_PATH, model_path: Path = MODEL_PATH) -> float:
    """Train on engine-derived feature rows and a binary ``risk`` target."""
    df = pd.read_csv(data_path)
    missing = (set(FEATURES) | {"risk"}) - set(df.columns)
    if missing:
        raise ValueError(f"training data is missing columns: {', '.join(sorted(missing))}")
    X, y = df[list(FEATURES)], df["risk"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    model = RandomForestClassifier(n_estimators=200, random_state=42, class_weight="balanced")
    model.fit(X_train, y_train)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)
    return float(model.score(X_test, y_test))

if __name__ == "__main__":
    print(f"Accuracy: {train():.3f}")
