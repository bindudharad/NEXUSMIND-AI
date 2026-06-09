from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "8")

import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split


ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"
ROI_MODEL_PATH = ARTIFACT_DIR / "roi_savings_rf.joblib"
METRICS_PATH = ARTIFACT_DIR / "roi_intelligence_metrics.json"


@dataclass(frozen=True)
class RoiModelPrediction:
    savings_capture_rate: float
    confidence: float


class RoiIntelligenceEngine:
    model_name = "RandomForest Workforce Economics ROI Engine"
    feature_names = [
        "avg_attrition_probability",
        "avg_burnout_probability",
        "avg_productivity_gap",
        "avg_stress",
        "meeting_load_index",
        "overtime_index",
        "knowledge_criticality",
        "project_delay_probability",
        "project_failure_probability",
        "budget_pressure",
        "retention_improvement",
        "productivity_recovery",
        "meeting_reduction",
        "overtime_reduction",
        "delay_risk_reduction",
        "intervention_intensity",
    ]

    def __init__(self) -> None:
        ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
        self.model: RandomForestRegressor | None = None
        self.metrics_data: dict[str, object] = {}
        self._load_or_train()

    @property
    def available(self) -> bool:
        return self.model is not None and ROI_MODEL_PATH.exists()

    def _load_or_train(self) -> None:
        if ROI_MODEL_PATH.exists() and METRICS_PATH.exists():
            self.model = joblib.load(ROI_MODEL_PATH)
            self.model.n_jobs = 1
            self.metrics_data = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
            return
        self.train()

    def train(self) -> dict[str, object]:
        rng = np.random.default_rng(9911)
        rows: list[list[float]] = []
        targets: list[float] = []
        for _ in range(5200):
            avg_attrition = rng.beta(2.0, 4.0)
            avg_burnout = rng.beta(2.3, 3.5)
            productivity_gap = rng.beta(2.4, 3.2)
            avg_stress = rng.beta(2.2, 3.4)
            meeting_load = rng.beta(2.0, 4.0)
            overtime = rng.beta(1.8, 4.4)
            knowledge = rng.beta(2.7, 2.5)
            delay = rng.beta(2.2, 3.2)
            failure = rng.beta(1.9, 3.5)
            budget = rng.beta(2.1, 3.3)
            retention = rng.uniform(0.05, 0.48)
            productivity = rng.uniform(0.04, 0.36)
            meeting_reduction = rng.uniform(0.02, 0.42)
            overtime_reduction = rng.uniform(0.02, 0.46)
            delay_reduction = rng.uniform(0.03, 0.42)
            intervention = rng.beta(2.2, 2.8)
            features = [
                avg_attrition,
                avg_burnout,
                productivity_gap,
                avg_stress,
                meeting_load,
                overtime,
                knowledge,
                delay,
                failure,
                budget,
                retention,
                productivity,
                meeting_reduction,
                overtime_reduction,
                delay_reduction,
                intervention,
            ]
            risk_surface = (
                avg_attrition * 0.16
                + avg_burnout * 0.15
                + productivity_gap * 0.12
                + avg_stress * 0.08
                + meeting_load * 0.07
                + overtime * 0.07
                + knowledge * 0.07
                + delay * 0.1
                + failure * 0.1
                + budget * 0.08
            )
            intervention_fit = (
                retention * avg_attrition * 0.34
                + productivity * productivity_gap * 0.24
                + meeting_reduction * meeting_load * 0.14
                + overtime_reduction * overtime * 0.12
                + delay_reduction * delay * 0.16
            )
            capture = np.clip(0.18 + risk_surface * 0.38 + intervention_fit * 1.45 - intervention * 0.08 + rng.normal(0, 0.025), 0.08, 0.82)
            rows.append(features)
            targets.append(float(capture))

        x_train, x_test, y_train, y_test = train_test_split(np.array(rows), np.array(targets), test_size=0.22, random_state=97)
        self.model = RandomForestRegressor(
            n_estimators=220,
            max_depth=15,
            min_samples_leaf=4,
            random_state=97,
            n_jobs=1,
        )
        self.model.fit(x_train, y_train)
        predictions = self.model.predict(x_test)
        self.metrics_data = {
            "model": self.model_name,
            "training_examples": len(rows),
            "features": self.feature_names,
            "mae": round(float(mean_absolute_error(y_test, predictions)), 4),
            "r2": round(float(r2_score(y_test, predictions)), 3),
        }
        joblib.dump(self.model, ROI_MODEL_PATH)
        METRICS_PATH.write_text(json.dumps(self.metrics_data, indent=2), encoding="utf-8")
        return self.metrics_data

    def predict_capture_rate(self, features: list[float]) -> RoiModelPrediction:
        if self.model is None:
            self.train()
        assert self.model is not None
        vector = np.array([[float(np.clip(value, 0, 1)) for value in features]])
        prediction = float(np.clip(self.model.predict(vector)[0], 0.08, 0.82))
        confidence = float(np.clip(0.62 + prediction * 0.3 + abs(prediction - 0.35) * 0.12, 0.58, 0.95))
        return RoiModelPrediction(savings_capture_rate=round(prediction, 4), confidence=round(confidence, 3))

    def metrics(self) -> dict[str, object]:
        if not self.metrics_data:
            self._load_or_train()
        return self.metrics_data


roi_intelligence_engine = RoiIntelligenceEngine()


if __name__ == "__main__":
    print(json.dumps(roi_intelligence_engine.train(), indent=2))
