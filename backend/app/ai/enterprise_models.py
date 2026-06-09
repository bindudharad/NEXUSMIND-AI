from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import joblib
import numpy as np
import torch
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

from app.ai.burnout_model import BurnoutFeatures


ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"
RF_PATH = ARTIFACT_DIR / "random_forest_burnout.joblib"
XGB_PATH = ARTIFACT_DIR / "xgboost_burnout.joblib"
SCALER_PATH = ARTIFACT_DIR / "neural_scaler.joblib"
NN_PATH = ARTIFACT_DIR / "torch_burnout.pt"
METRICS_PATH = ARTIFACT_DIR / "enterprise_model_metrics.json"


@dataclass(frozen=True)
class ModelMetrics:
    model: str
    accuracy: float
    roc_auc: float
    f1: float
    trained_samples: int


class BurnoutNet(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.network = torch.nn.Sequential(
            torch.nn.Linear(5, 16),
            torch.nn.ReLU(),
            torch.nn.Dropout(0.05),
            torch.nn.Linear(16, 8),
            torch.nn.ReLU(),
            torch.nn.Linear(8, 1),
            torch.nn.Sigmoid(),
        )

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return self.network(features)


def build_enterprise_dataset(seed: int = 42, samples: int = 1400) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    overtime = rng.normal(9.5, 5.4, samples).clip(0, 34)
    meetings = rng.normal(15, 7.5, samples).clip(0, 42)
    sentiment = rng.normal(0.03, 0.48, samples).clip(-1, 1)
    completion = rng.normal(0.77, 0.18, samples).clip(0.2, 1)
    absences = rng.poisson(2.4, samples).clip(0, 15)
    pressure = (
        overtime * 0.09
        + meetings * 0.045
        - sentiment * 1.2
        - completion * 1.55
        + absences * 0.13
        + np.where((overtime > 18) & (meetings > 22), 0.7, 0)
    )
    probability = 1 / (1 + np.exp(-(pressure - 1.75)))
    labels = (probability > 0.44).astype(np.int64)
    features = np.column_stack([overtime, meetings, sentiment, completion, absences]).astype(np.float32)
    return features, labels


def _score_model(name: str, y_test: np.ndarray, predictions: np.ndarray, probabilities: np.ndarray, samples: int) -> ModelMetrics:
    return ModelMetrics(
        model=name,
        accuracy=round(float(accuracy_score(y_test, predictions)), 3),
        roc_auc=round(float(roc_auc_score(y_test, probabilities)), 3),
        f1=round(float(f1_score(y_test, predictions)), 3),
        trained_samples=samples,
    )


def train_enterprise_models() -> list[ModelMetrics]:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    features, labels = build_enterprise_dataset()
    x_train, x_test, y_train, y_test = train_test_split(
        features,
        labels,
        test_size=0.22,
        random_state=11,
        stratify=labels,
    )

    random_forest = RandomForestClassifier(
        n_estimators=180,
        max_depth=9,
        min_samples_leaf=4,
        class_weight="balanced",
        random_state=11,
        n_jobs=-1,
    )
    random_forest.fit(x_train, y_train)
    rf_probabilities = random_forest.predict_proba(x_test)[:, 1]
    rf_metrics = _score_model("Random Forest", y_test, random_forest.predict(x_test), rf_probabilities, len(features))
    joblib.dump(random_forest, RF_PATH)

    positive_count = max(int(y_train.sum()), 1)
    negative_count = max(len(y_train) - positive_count, 1)
    xgboost = XGBClassifier(
        n_estimators=120,
        max_depth=4,
        learning_rate=0.06,
        subsample=0.88,
        colsample_bytree=0.9,
        objective="binary:logistic",
        eval_metric="logloss",
        scale_pos_weight=negative_count / positive_count,
        random_state=11,
    )
    xgboost.fit(x_train, y_train)
    xgb_probabilities = xgboost.predict_proba(x_test)[:, 1]
    xgb_metrics = _score_model("XGBoost", y_test, xgboost.predict(x_test), xgb_probabilities, len(features))
    joblib.dump(xgboost, XGB_PATH)

    scaler = StandardScaler()
    x_train_scaled = scaler.fit_transform(x_train).astype(np.float32)
    x_test_scaled = scaler.transform(x_test).astype(np.float32)
    network = BurnoutNet()
    optimizer = torch.optim.Adam(network.parameters(), lr=0.01)
    criterion = torch.nn.BCELoss()
    train_tensor = torch.tensor(x_train_scaled)
    label_tensor = torch.tensor(y_train.astype(np.float32)).reshape(-1, 1)
    network.train()
    for _ in range(90):
        optimizer.zero_grad()
        loss = criterion(network(train_tensor), label_tensor)
        loss.backward()
        optimizer.step()
    network.eval()
    with torch.no_grad():
        nn_probabilities = network(torch.tensor(x_test_scaled)).numpy().reshape(-1)
    nn_predictions = (nn_probabilities >= 0.5).astype(np.int64)
    nn_metrics = _score_model("PyTorch Neural Network", y_test, nn_predictions, nn_probabilities, len(features))
    joblib.dump(scaler, SCALER_PATH)
    torch.save(network.state_dict(), NN_PATH)

    metrics = [rf_metrics, xgb_metrics, nn_metrics]
    METRICS_PATH.write_text(json.dumps([asdict(metric) for metric in metrics], indent=2), encoding="utf-8")
    return metrics


class EnterpriseModelRegistry:
    def __init__(self) -> None:
        self._random_forest = None
        self._xgboost = None
        self._network: BurnoutNet | None = None
        self._scaler = None

    @property
    def available(self) -> bool:
        return all(path.exists() for path in [RF_PATH, XGB_PATH, SCALER_PATH, NN_PATH, METRICS_PATH])

    def ensure_artifacts(self) -> None:
        if not self.available:
            train_enterprise_models()

    def metrics(self) -> list[dict[str, float | int | str]]:
        self.ensure_artifacts()
        return json.loads(METRICS_PATH.read_text(encoding="utf-8"))

    def predict(self, features: BurnoutFeatures) -> dict[str, float]:
        self.ensure_artifacts()
        vector = np.array(
            [[
                features.overtime_hours,
                features.meeting_hours,
                features.sentiment_score,
                features.task_completion_ratio,
                features.absence_days,
            ]],
            dtype=np.float32,
        )
        if self._random_forest is None:
            self._random_forest = joblib.load(RF_PATH)
        if self._xgboost is None:
            self._xgboost = joblib.load(XGB_PATH)
        if self._scaler is None:
            self._scaler = joblib.load(SCALER_PATH)
        if self._network is None:
            self._network = BurnoutNet()
            self._network.load_state_dict(torch.load(NN_PATH, map_location="cpu", weights_only=True))
            self._network.eval()

        scaled = self._scaler.transform(vector).astype(np.float32)
        with torch.no_grad():
            neural_probability = float(self._network(torch.tensor(scaled)).item())
        predictions = {
            "random_forest": round(float(self._random_forest.predict_proba(vector)[0][1]), 3),
            "xgboost": round(float(self._xgboost.predict_proba(vector)[0][1]), 3),
            "neural_network": round(neural_probability, 3),
        }
        predictions["ensemble"] = round(sum(predictions.values()) / len(predictions), 3)
        return predictions


enterprise_model_registry = EnterpriseModelRegistry()


if __name__ == "__main__":
    print([asdict(metric) for metric in train_enterprise_models()])
