from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

from app.schemas.employee_dashboard import EmployeeActivityPoint


ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"
STRESS_MODEL_PATH = ARTIFACT_DIR / "employee_stress_regressor.joblib"
PRODUCTIVITY_MODEL_PATH = ARTIFACT_DIR / "employee_productivity_regressor.joblib"
METRICS_PATH = ARTIFACT_DIR / "employee_dashboard_metrics.json"


@dataclass(frozen=True)
class EmployeeAnalyticsPrediction:
    stress_score: float
    productivity_score: float


class EmployeeAnalyticsEngine:
    model_name = "RandomForest Employee Analytics + Burnout Ensemble"
    feature_names = [
        "overtime_hours",
        "workload_intensity",
        "meeting_hours",
        "sentiment_score",
        "task_completion_ratio",
        "attendance_rate",
        "focus_hours",
        "collaboration_score",
        "activity_variance",
        "negative_message_ratio",
        "toxic_message_count",
        "absence_days",
    ]

    def __init__(self) -> None:
        ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
        self.stress_model: RandomForestRegressor | None = None
        self.productivity_model: RandomForestRegressor | None = None
        self.metrics: dict[str, float | int | str] = {}
        self._load_or_train()

    @property
    def available(self) -> bool:
        return self.stress_model is not None and self.productivity_model is not None

    def _load_or_train(self) -> None:
        if STRESS_MODEL_PATH.exists() and PRODUCTIVITY_MODEL_PATH.exists() and METRICS_PATH.exists():
            self.stress_model = joblib.load(STRESS_MODEL_PATH)
            self.productivity_model = joblib.load(PRODUCTIVITY_MODEL_PATH)
            self.metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
            return
        self.train()

    def train(self) -> dict[str, float | int | str]:
        rng = np.random.default_rng(91)
        features, stress_target, productivity_target = self._dataset(rng, 4200)
        x_train, x_test, stress_train, stress_test, productivity_train, productivity_test = train_test_split(
            features,
            stress_target,
            productivity_target,
            test_size=0.22,
            random_state=19,
        )
        self.stress_model = RandomForestRegressor(n_estimators=220, max_depth=13, min_samples_leaf=4, random_state=19, n_jobs=-1)
        self.productivity_model = RandomForestRegressor(n_estimators=220, max_depth=12, min_samples_leaf=4, random_state=23, n_jobs=-1)
        self.stress_model.fit(x_train, stress_train)
        self.productivity_model.fit(x_train, productivity_train)
        stress_predictions = self.stress_model.predict(x_test)
        productivity_predictions = self.productivity_model.predict(x_test)
        self.metrics = {
            "model": self.model_name,
            "training_examples": len(features),
            "stress_mae": round(float(mean_absolute_error(stress_test, stress_predictions)), 3),
            "stress_r2": round(float(r2_score(stress_test, stress_predictions)), 3),
            "productivity_mae": round(float(mean_absolute_error(productivity_test, productivity_predictions)), 3),
            "productivity_r2": round(float(r2_score(productivity_test, productivity_predictions)), 3),
        }
        joblib.dump(self.stress_model, STRESS_MODEL_PATH)
        joblib.dump(self.productivity_model, PRODUCTIVITY_MODEL_PATH)
        METRICS_PATH.write_text(json.dumps(self.metrics, indent=2), encoding="utf-8")
        return self.metrics

    def predict(self, point: EmployeeActivityPoint) -> EmployeeAnalyticsPrediction:
        if not self.available:
            self.train()
        vector = np.array([self.vectorize(point)], dtype=np.float32)
        stress = float(self.stress_model.predict(vector)[0]) if self.stress_model else 0.0
        productivity = float(self.productivity_model.predict(vector)[0]) if self.productivity_model else 0.0
        return EmployeeAnalyticsPrediction(
            stress_score=round(float(np.clip(stress, 0, 100)), 2),
            productivity_score=round(float(np.clip(productivity, 0, 100)), 2),
        )

    def predict_many(self, points: list[EmployeeActivityPoint]) -> list[EmployeeAnalyticsPrediction]:
        if not points:
            return []
        if not self.available:
            self.train()
        vectors = np.array([self.vectorize(point) for point in points], dtype=np.float32)
        stress_values = self.stress_model.predict(vectors) if self.stress_model else np.zeros(len(points))
        productivity_values = self.productivity_model.predict(vectors) if self.productivity_model else np.zeros(len(points))
        return [
            EmployeeAnalyticsPrediction(
                stress_score=round(float(np.clip(stress, 0, 100)), 2),
                productivity_score=round(float(np.clip(productivity, 0, 100)), 2),
            )
            for stress, productivity in zip(stress_values, productivity_values)
        ]

    def vectorize(self, point: EmployeeActivityPoint) -> list[float]:
        return [
            point.overtime_hours,
            point.workload_intensity,
            point.meeting_hours,
            point.sentiment_score,
            point.task_completion_ratio,
            point.attendance_rate,
            point.focus_hours,
            point.collaboration_score,
            point.activity_variance,
            point.negative_message_ratio,
            point.toxic_message_count,
            point.absence_days,
        ]

    @staticmethod
    def _dataset(rng: np.random.Generator, rows: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        overtime = rng.normal(7.4, 5.2, rows).clip(0, 32)
        workload = rng.normal(64, 18, rows).clip(15, 100)
        meetings = rng.normal(8.2, 4.6, rows).clip(0, 22)
        sentiment = rng.normal(0.04, 0.45, rows).clip(-1, 1)
        completion = rng.normal(0.78, 0.16, rows).clip(0.22, 1)
        attendance = rng.normal(0.94, 0.07, rows).clip(0.55, 1)
        focus = rng.normal(5.1, 2.1, rows).clip(0, 12)
        collaboration = rng.normal(0.78, 0.16, rows).clip(0.18, 1)
        variance = rng.beta(2.2, 4.2, rows).clip(0, 1)
        negative_ratio = rng.beta(2.0, 7.5, rows).clip(0, 1)
        toxic = rng.poisson(0.8, rows).clip(0, 18)
        absences = rng.poisson(1.8, rows).clip(0, 14)

        stress = (
            overtime * 1.55
            + workload * 0.32
            + meetings * 1.15
            + (1 - np.clip((sentiment + 1) / 2, 0, 1)) * 16
            + (1 - completion) * 13
            + (1 - attendance) * 12
            + variance * 11
            + negative_ratio * 14
            + toxic * 1.6
            + absences * 1.2
            - focus * 1.15
            + rng.normal(0, 3.1, rows)
        ).clip(0, 100)
        productivity = (
            completion * 38
            + attendance * 18
            + focus * 4.2
            + collaboration * 15
            + np.clip((sentiment + 1) / 2, 0, 1) * 10
            - np.maximum(0, meetings - 8) * 1.1
            - np.maximum(0, overtime - 10) * 1.25
            - variance * 8
            - negative_ratio * 10
            - toxic * 1.4
            + rng.normal(0, 2.7, rows)
        ).clip(0, 100)

        features = np.column_stack(
            [
                overtime,
                workload,
                meetings,
                sentiment,
                completion,
                attendance,
                focus,
                collaboration,
                variance,
                negative_ratio,
                toxic,
                absences,
            ]
        ).astype(np.float32)
        return features, stress.astype(np.float32), productivity.astype(np.float32)


employee_analytics_engine = EmployeeAnalyticsEngine()


if __name__ == "__main__":
    print(json.dumps(employee_analytics_engine.train(), indent=2))
