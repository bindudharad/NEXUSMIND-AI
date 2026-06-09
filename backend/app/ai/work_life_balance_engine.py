from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.cluster import KMeans
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"
MODEL_PATH = ARTIFACT_DIR / "work_life_balance_models.joblib"
METRICS_PATH = ARTIFACT_DIR / "work_life_balance_metrics.json"


class WorkLifeBalanceEngine:
    model_name = "RandomForest Work-Life Balance Optimizer + GradientBoosting Burnout Forecaster"
    cluster_model_name = "KMeans Energy-Cadence Schedule Segmenter"
    feature_names = [
        "meeting_load",
        "recurring_meeting_load",
        "async_conversion_ratio",
        "overtime_pressure",
        "after_hours_pressure",
        "focus_deficit",
        "context_switch_pressure",
        "utilization",
        "deadline_pressure",
        "collaboration_dependency",
        "burnout_risk",
        "stress_score",
        "wellness_score",
        "productivity_score",
        "energy_morning",
        "energy_afternoon",
        "flexibility_fit",
        "manager_support",
    ]

    def __init__(self) -> None:
        ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
        self.wellness_model: RandomForestRegressor | None = None
        self.burnout_model: GradientBoostingRegressor | None = None
        self.balance_model: RandomForestRegressor | None = None
        self.scaler: StandardScaler | None = None
        self.clusterer: KMeans | None = None
        self.metrics: dict[str, float | int | str] = {}
        self._load_or_train()

    def _load_or_train(self) -> None:
        if MODEL_PATH.exists() and METRICS_PATH.exists():
            bundle = joblib.load(MODEL_PATH)
            self.wellness_model = bundle["wellness"]
            self.burnout_model = bundle["burnout"]
            self.balance_model = bundle["balance"]
            self.scaler = bundle["scaler"]
            self.clusterer = bundle["clusterer"]
            self.metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
            return
        self.train()

    def train(self) -> dict[str, float | int | str]:
        rng = np.random.default_rng(916)
        features, wellness, burnout, balance = self._dataset(rng, 6800)
        x_train, x_test, wellness_train, wellness_test, burnout_train, burnout_test, balance_train, balance_test = train_test_split(
            features,
            wellness,
            burnout,
            balance,
            test_size=0.22,
            random_state=73,
        )
        self.wellness_model = RandomForestRegressor(n_estimators=260, max_depth=14, min_samples_leaf=4, random_state=73, n_jobs=-1)
        self.burnout_model = GradientBoostingRegressor(n_estimators=220, learning_rate=0.045, max_depth=4, random_state=79)
        self.balance_model = RandomForestRegressor(n_estimators=240, max_depth=13, min_samples_leaf=4, random_state=83, n_jobs=-1)
        self.wellness_model.fit(x_train, wellness_train)
        self.burnout_model.fit(x_train, burnout_train)
        self.balance_model.fit(x_train, balance_train)
        self.scaler = StandardScaler()
        scaled = self.scaler.fit_transform(features)
        self.clusterer = KMeans(n_clusters=5, random_state=89, n_init=10)
        self.clusterer.fit(scaled[:, [0, 3, 5, 8, 14, 15, 16]])

        wellness_pred = self.wellness_model.predict(x_test)
        burnout_pred = self.burnout_model.predict(x_test)
        balance_pred = self.balance_model.predict(x_test)
        self.metrics = {
            "model": self.model_name,
            "schedule_model": self.cluster_model_name,
            "training_examples": len(features),
            "wellness_mae": round(float(mean_absolute_error(wellness_test, wellness_pred)), 3),
            "wellness_r2": round(float(r2_score(wellness_test, wellness_pred)), 3),
            "burnout_mae": round(float(mean_absolute_error(burnout_test, burnout_pred)), 3),
            "burnout_r2": round(float(r2_score(burnout_test, burnout_pred)), 3),
            "balance_mae": round(float(mean_absolute_error(balance_test, balance_pred)), 3),
            "balance_r2": round(float(r2_score(balance_test, balance_pred)), 3),
        }
        joblib.dump(
            {
                "wellness": self.wellness_model,
                "burnout": self.burnout_model,
                "balance": self.balance_model,
                "scaler": self.scaler,
                "clusterer": self.clusterer,
            },
            MODEL_PATH,
        )
        METRICS_PATH.write_text(json.dumps(self.metrics, indent=2), encoding="utf-8")
        return self.metrics

    def predict(self, rows: list[list[float]]) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        if self.wellness_model is None or self.burnout_model is None or self.balance_model is None or self.scaler is None or self.clusterer is None:
            self.train()
        matrix = np.array(rows, dtype=np.float32)
        wellness = self.wellness_model.predict(matrix) if self.wellness_model else np.zeros(len(matrix))
        burnout = self.burnout_model.predict(matrix) if self.burnout_model else np.zeros(len(matrix))
        balance = self.balance_model.predict(matrix) if self.balance_model else np.zeros(len(matrix))
        scaled = self.scaler.transform(matrix) if self.scaler else matrix
        clusters = self.clusterer.predict(scaled[:, [0, 3, 5, 8, 14, 15, 16]]) if self.clusterer else np.zeros(len(matrix))
        return np.clip(wellness, 0, 100), np.clip(burnout, 0, 100), np.clip(balance, 0, 100), clusters

    @staticmethod
    def _dataset(rng: np.random.Generator, rows: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        meeting = rng.beta(2.4, 3.8, rows).clip(0, 1)
        recurring = rng.beta(2.2, 4.0, rows).clip(0, 1)
        async_ratio = rng.beta(3.2, 3.5, rows).clip(0, 1)
        overtime = rng.beta(2.1, 4.2, rows).clip(0, 1)
        after_hours = rng.beta(1.8, 5.2, rows).clip(0, 1)
        focus_deficit = rng.beta(2.5, 3.8, rows).clip(0, 1)
        context = rng.beta(2.5, 4.5, rows).clip(0, 1)
        utilization = rng.normal(0.86, 0.28, rows).clip(0, 1.55)
        deadline = rng.beta(2.5, 3.2, rows).clip(0, 1)
        collaboration = rng.beta(2.6, 3.4, rows).clip(0, 1)
        burnout = rng.beta(2.2, 3.9, rows).clip(0, 1)
        stress = rng.beta(2.4, 3.8, rows).clip(0, 1)
        wellness = rng.beta(4.5, 2.4, rows).clip(0, 1)
        productivity = rng.beta(4.8, 2.2, rows).clip(0, 1)
        energy_morning = rng.beta(4.0, 2.5, rows).clip(0, 1)
        energy_afternoon = rng.beta(3.4, 3.2, rows).clip(0, 1)
        flexibility = rng.beta(3.2, 2.8, rows).clip(0, 1)
        manager = rng.beta(3.8, 2.5, rows).clip(0, 1)
        overload = np.maximum(0, utilization - 0.92)
        schedule_fit = np.maximum(energy_morning, energy_afternoon) * 0.65 + flexibility * 0.35
        wellness_target = (
            72
            + wellness * 18
            + schedule_fit * 12
            + manager * 8
            + async_ratio * 8
            + productivity * 7
            - meeting * 14
            - recurring * 10
            - overtime * 18
            - after_hours * 10
            - focus_deficit * 14
            - context * 9
            - overload * 24
            - deadline * 7
            - stress * 13
            - burnout * 16
            + rng.normal(0, 2.2, rows)
        ).clip(0, 100)
        burnout_target = (
            burnout * 48
            + stress * 22
            + overtime * 20
            + after_hours * 12
            + meeting * 12
            + focus_deficit * 9
            + overload * 23
            + deadline * 8
            - async_ratio * 8
            - manager * 9
            - flexibility * 7
            - wellness * 10
            + rng.normal(0, 2.0, rows)
        ).clip(0, 100)
        balance_target = (
            54
            + productivity * 18
            + wellness * 17
            + schedule_fit * 13
            + manager * 8
            - burnout * 14
            - stress * 10
            - meeting * 9
            - overtime * 13
            - focus_deficit * 11
            - context * 8
            - overload * 19
            + rng.normal(0, 2.0, rows)
        ).clip(0, 100)
        features = np.column_stack(
            [
                meeting,
                recurring,
                async_ratio,
                overtime,
                after_hours,
                focus_deficit,
                context,
                utilization,
                deadline,
                collaboration,
                burnout,
                stress,
                wellness,
                productivity,
                energy_morning,
                energy_afternoon,
                flexibility,
                manager,
            ]
        ).astype(np.float32)
        return features, wellness_target.astype(np.float32), burnout_target.astype(np.float32), balance_target.astype(np.float32)
