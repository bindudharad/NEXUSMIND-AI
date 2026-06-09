from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from pathlib import Path

import joblib
import numpy as np
import torch
from sklearn.preprocessing import MinMaxScaler


ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"
FORECAST_MODEL_PATH = ARTIFACT_DIR / "workload_lstm.pt"
FORECAST_SCALER_PATH = ARTIFACT_DIR / "workload_scaler.joblib"
FORECAST_METRICS_PATH = ARTIFACT_DIR / "workload_lstm_metrics.json"
SEQUENCE_LENGTH = 14
FEATURES = [
    "workload",
    "productivity",
    "overtime_hours",
    "attendance_rate",
    "task_completion_rate",
    "burnout_risk",
    "delay_probability",
]


class WorkloadLSTM(torch.nn.Module):
    def __init__(self, features: int) -> None:
        super().__init__()
        self.lstm = torch.nn.LSTM(input_size=features, hidden_size=32, num_layers=1, batch_first=True)
        self.head = torch.nn.Sequential(torch.nn.Linear(32, 24), torch.nn.ReLU(), torch.nn.Linear(24, features))

    def forward(self, sequence: torch.Tensor) -> torch.Tensor:
        output, _ = self.lstm(sequence)
        return self.head(output[:, -1, :])


@dataclass(frozen=True)
class ForecastMetric:
    model: str
    train_sequences: int
    validation_mae: float
    features: list[str]


def synthetic_history(seed: int = 13, days: int = 180) -> np.ndarray:
    rng = np.random.default_rng(seed)
    rows = []
    workload = 55.0
    productivity = 86.0
    burnout = 0.22
    delay = 0.18
    for index in range(days):
        season = math.sin(index / 7 * math.pi) * 4
        workload = np.clip(workload + 0.08 + rng.normal(0, 2.0) + season * 0.08, 20, 98)
        overtime = np.clip((workload - 50) / 5 + rng.normal(1.5, 1.2), 0, 18)
        productivity = np.clip(productivity - max(workload - 72, 0) * 0.08 + rng.normal(0, 1.4), 45, 98)
        attendance = np.clip(0.97 - burnout * 0.08 + rng.normal(0, 0.015), 0.78, 1)
        completion = np.clip(productivity / 100 - overtime * 0.006 + rng.normal(0, 0.018), 0.45, 1)
        burnout = np.clip(burnout + (workload - 62) * 0.002 + overtime * 0.006 - completion * 0.01 + rng.normal(0, 0.02), 0.02, 0.96)
        delay = np.clip(delay + (1 - completion) * 0.05 + burnout * 0.012 + rng.normal(0, 0.025), 0.02, 0.94)
        rows.append([workload, productivity, overtime, attendance, completion, burnout, delay])
    return np.array(rows, dtype=np.float32)


def make_sequences(data: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    x, y = [], []
    for index in range(SEQUENCE_LENGTH, len(data)):
        x.append(data[index - SEQUENCE_LENGTH : index])
        y.append(data[index])
    return np.array(x, dtype=np.float32), np.array(y, dtype=np.float32)


def train_forecaster() -> ForecastMetric:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    raw = np.vstack([synthetic_history(seed=seed, days=190) for seed in range(11, 18)])
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(raw)
    x, y = make_sequences(scaled)
    split = int(len(x) * 0.82)
    x_train, x_test = torch.tensor(x[:split]), torch.tensor(x[split:])
    y_train, y_test = torch.tensor(y[:split]), torch.tensor(y[split:])
    model = WorkloadLSTM(features=len(FEATURES))
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    criterion = torch.nn.L1Loss()
    model.train()
    for _ in range(85):
        optimizer.zero_grad()
        loss = criterion(model(x_train), y_train)
        loss.backward()
        optimizer.step()
    model.eval()
    with torch.no_grad():
        predictions = model(x_test)
        mae = float(torch.mean(torch.abs(predictions - y_test)).item())
    torch.save(model.state_dict(), FORECAST_MODEL_PATH)
    joblib.dump(scaler, FORECAST_SCALER_PATH)
    metric = ForecastMetric(
        model="PyTorch WorkloadLSTM",
        train_sequences=len(x_train),
        validation_mae=round(mae, 4),
        features=FEATURES,
    )
    FORECAST_METRICS_PATH.write_text(json.dumps(asdict(metric), indent=2), encoding="utf-8")
    return metric


class TimeSeriesForecaster:
    def __init__(self) -> None:
        self._model: WorkloadLSTM | None = None
        self._scaler: MinMaxScaler | None = None

    @property
    def available(self) -> bool:
        return FORECAST_MODEL_PATH.exists() and FORECAST_SCALER_PATH.exists() and FORECAST_METRICS_PATH.exists()

    def ensure_artifacts(self) -> None:
        if not self.available:
            train_forecaster()

    def metrics(self) -> dict[str, object]:
        self.ensure_artifacts()
        return json.loads(FORECAST_METRICS_PATH.read_text(encoding="utf-8"))

    def _load(self) -> None:
        self.ensure_artifacts()
        if self._scaler is None:
            self._scaler = joblib.load(FORECAST_SCALER_PATH)
        if self._model is None:
            self._model = WorkloadLSTM(features=len(FEATURES))
            self._model.load_state_dict(torch.load(FORECAST_MODEL_PATH, map_location="cpu", weights_only=True))
            self._model.eval()

    def forecast(self, history: np.ndarray, horizon: int) -> np.ndarray:
        self._load()
        assert self._model is not None
        assert self._scaler is not None
        if len(history) < SEQUENCE_LENGTH:
            raise ValueError(f"At least {SEQUENCE_LENGTH} history points are required")
        scaled_history = self._scaler.transform(history.astype(np.float32)).tolist()
        predictions = []
        for _ in range(horizon):
            window = torch.tensor([scaled_history[-SEQUENCE_LENGTH:]], dtype=torch.float32)
            with torch.no_grad():
                prediction = self._model(window).numpy()[0]
            prediction = np.clip(prediction, 0, 1)
            scaled_history.append(prediction.tolist())
            predictions.append(prediction)
        return self._scaler.inverse_transform(np.array(predictions, dtype=np.float32))


time_series_forecaster = TimeSeriesForecaster()


if __name__ == "__main__":
    print(train_forecaster())
