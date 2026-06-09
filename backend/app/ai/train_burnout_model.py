from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split


MODEL_PATH = Path(__file__).resolve().parent / "artifacts" / "burnout_classifier.joblib"


def build_dataset(seed: int = 42) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    samples = 900
    overtime = rng.normal(9, 5, samples).clip(0, 30)
    meetings = rng.normal(14, 7, samples).clip(0, 40)
    sentiment = rng.normal(0.05, 0.45, samples).clip(-1, 1)
    completion = rng.normal(0.78, 0.18, samples).clip(0.2, 1)
    absences = rng.poisson(2.2, samples).clip(0, 14)
    pressure = overtime * 0.08 + meetings * 0.04 - sentiment * 1.1 - completion * 1.4 + absences * 0.12
    probability = 1 / (1 + np.exp(-(pressure - 1.6)))
    labels = (probability > 0.58).astype(int)
    features = np.column_stack([overtime, meetings, sentiment, completion, absences])
    return features, labels


def train() -> dict[str, float | str]:
    features, labels = build_dataset()
    x_train, x_test, y_train, y_test = train_test_split(features, labels, test_size=0.22, random_state=7)
    model = GradientBoostingClassifier(random_state=7)
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)
    probabilities = model.predict_proba(x_test)[:, 1]
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    return {
        "model_path": str(MODEL_PATH),
        "accuracy": round(float(accuracy_score(y_test, predictions)), 3),
        "roc_auc": round(float(roc_auc_score(y_test, probabilities)), 3),
    }


if __name__ == "__main__":
    print(train())
