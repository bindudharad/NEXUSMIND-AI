from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "8")

import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

from app.schemas.project_failure import ProjectMetricPoint, ProjectProfile

try:
    from xgboost import XGBRegressor
except Exception:  # pragma: no cover - production image includes xgboost, fallback keeps local dev stable.
    XGBRegressor = None  # type: ignore[assignment]


ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"
FAILURE_MODEL_PATH = ARTIFACT_DIR / "project_failure_rf.joblib"
DELAY_MODEL_PATH = ARTIFACT_DIR / "project_delay_xgb.joblib"
BUDGET_MODEL_PATH = ARTIFACT_DIR / "project_budget_rf.joblib"
METRICS_PATH = ARTIFACT_DIR / "project_failure_metrics.json"


@dataclass(frozen=True)
class ProjectRiskPrediction:
    failure_probability: float
    delay_probability: float
    budget_overrun_probability: float
    confidence: float
    features: dict[str, float]


class ProjectFailureEngine:
    model_name = "RandomForest/XGBoost Project Failure Forecaster"
    feature_names = [
        "days_to_deadline_norm",
        "deadline_pressure",
        "budget_utilization",
        "budget_burn_rate",
        "scope_completion_gap",
        "velocity_current",
        "velocity_trend",
        "completion_rate",
        "completion_trend",
        "scope_change_rate",
        "defect_rate",
        "rework_ratio",
        "dependency_pressure",
        "resource_allocation",
        "meeting_load",
        "communication_score",
        "team_burnout",
        "team_compatibility",
        "open_risk_pressure",
        "historical_delivery_rate",
        "skill_coverage",
        "executive_visibility",
    ]

    def __init__(self) -> None:
        ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
        self.failure_model: RandomForestRegressor | None = None
        self.delay_model: object | None = None
        self.budget_model: RandomForestRegressor | None = None
        self.metrics_data: dict[str, object] = {}
        self._load_or_train()

    @property
    def available(self) -> bool:
        return (
            self.failure_model is not None
            and self.delay_model is not None
            and self.budget_model is not None
            and FAILURE_MODEL_PATH.exists()
            and DELAY_MODEL_PATH.exists()
            and BUDGET_MODEL_PATH.exists()
        )

    def _load_or_train(self) -> None:
        if FAILURE_MODEL_PATH.exists() and DELAY_MODEL_PATH.exists() and BUDGET_MODEL_PATH.exists() and METRICS_PATH.exists():
            self.failure_model = joblib.load(FAILURE_MODEL_PATH)
            self.delay_model = joblib.load(DELAY_MODEL_PATH)
            self.budget_model = joblib.load(BUDGET_MODEL_PATH)
            if hasattr(self.failure_model, "n_jobs"):
                self.failure_model.n_jobs = 1
            if hasattr(self.budget_model, "n_jobs"):
                self.budget_model.n_jobs = 1
            self.metrics_data = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
            return
        self.train()

    def train(self) -> dict[str, object]:
        rng = np.random.default_rng(8407)
        rows: list[list[float]] = []
        failure_targets: list[float] = []
        delay_targets: list[float] = []
        budget_targets: list[float] = []

        for _ in range(5800):
            days_to_deadline_norm = rng.beta(2.2, 3.8)
            deadline_pressure = 1 - days_to_deadline_norm
            budget_utilization = min(1.6, rng.gamma(4.2, 0.17))
            budget_burn_rate = min(1.5, rng.gamma(3.7, 0.18))
            scope_completion_gap = rng.beta(2.1, 2.9)
            velocity_current = rng.beta(3.2, 2.2)
            velocity_trend = rng.normal(0.0, 0.32)
            completion_rate = rng.beta(3.1, 2.3)
            completion_trend = rng.normal(0.02, 0.27)
            scope_change_rate = rng.beta(1.6, 5.8)
            defect_rate = rng.beta(1.7, 6.2)
            rework_ratio = rng.beta(1.8, 6.0)
            dependency_pressure = rng.beta(1.9, 4.6)
            resource_allocation = rng.beta(4.0, 1.9)
            meeting_load = rng.beta(2.0, 4.2)
            communication_score = rng.beta(4.0, 1.9)
            team_burnout = rng.beta(2.1, 3.4)
            team_compatibility = rng.beta(4.2, 2.0)
            open_risk_pressure = rng.beta(1.8, 4.0)
            historical_delivery_rate = rng.beta(4.0, 2.0)
            skill_coverage = rng.beta(4.4, 1.8)
            executive_visibility = rng.beta(2.6, 2.8)
            features = [
                days_to_deadline_norm,
                deadline_pressure,
                min(budget_utilization / 1.25, 1),
                min(budget_burn_rate / 1.2, 1),
                scope_completion_gap,
                velocity_current,
                np.clip((velocity_trend + 1) / 2, 0, 1),
                completion_rate,
                np.clip((completion_trend + 1) / 2, 0, 1),
                scope_change_rate,
                defect_rate,
                rework_ratio,
                dependency_pressure,
                resource_allocation,
                meeting_load,
                communication_score,
                team_burnout,
                team_compatibility,
                open_risk_pressure,
                historical_delivery_rate,
                skill_coverage,
                executive_visibility,
            ]
            delivery_drag = (
                0.14 * deadline_pressure
                + 0.1 * scope_completion_gap
                + 0.1 * max(0, -velocity_trend)
                + 0.09 * max(0, -completion_trend)
                + 0.09 * scope_change_rate
                + 0.08 * defect_rate
                + 0.07 * rework_ratio
                + 0.1 * dependency_pressure
                + 0.1 * (1 - resource_allocation)
                + 0.07 * meeting_load
                + 0.09 * (1 - communication_score)
                + 0.1 * team_burnout
                + 0.07 * (1 - team_compatibility)
                + 0.07 * open_risk_pressure
                + 0.09 * (1 - historical_delivery_rate)
                + 0.05 * (1 - skill_coverage)
            )
            failure = np.clip(100 * (delivery_drag - 0.14) + rng.normal(0, 4.5), 0, 100)
            delay = np.clip(
                100
                * (
                    delivery_drag * 0.58
                    + deadline_pressure * 0.18
                    + dependency_pressure * 0.12
                    + max(0, -velocity_trend) * 0.08
                    + scope_change_rate * 0.06
                    - 0.1
                )
                + rng.normal(0, 4.0),
                0,
                100,
            )
            budget = np.clip(
                100
                * (
                    min(budget_utilization / 1.18, 1) * 0.26
                    + min(budget_burn_rate / 1.1, 1) * 0.23
                    + scope_change_rate * 0.16
                    + rework_ratio * 0.1
                    + defect_rate * 0.08
                    + (1 - resource_allocation) * 0.1
                    + delay / 100 * 0.15
                    - 0.12
                )
                + rng.normal(0, 4.2),
                0,
                100,
            )
            rows.append([float(np.clip(value, 0, 1)) for value in features])
            failure_targets.append(float(failure))
            delay_targets.append(float(delay))
            budget_targets.append(float(budget))

        x_train, x_test, failure_train, failure_test, delay_train, delay_test, budget_train, budget_test = train_test_split(
            np.array(rows),
            np.array(failure_targets),
            np.array(delay_targets),
            np.array(budget_targets),
            test_size=0.22,
            random_state=67,
        )
        self.failure_model = RandomForestRegressor(
            n_estimators=220,
            max_depth=15,
            min_samples_leaf=3,
            random_state=67,
            n_jobs=1,
        )
        self.budget_model = RandomForestRegressor(
            n_estimators=190,
            max_depth=14,
            min_samples_leaf=4,
            random_state=71,
            n_jobs=1,
        )
        if XGBRegressor is not None:
            self.delay_model = XGBRegressor(
                n_estimators=190,
                max_depth=4,
                learning_rate=0.055,
                subsample=0.86,
                colsample_bytree=0.9,
                objective="reg:squarederror",
                random_state=73,
                n_jobs=1,
                verbosity=0,
            )
        else:
            self.delay_model = GradientBoostingRegressor(n_estimators=210, max_depth=4, random_state=73)

        self.failure_model.fit(x_train, failure_train)
        self.delay_model.fit(x_train, delay_train)  # type: ignore[union-attr]
        self.budget_model.fit(x_train, budget_train)
        failure_pred = self.failure_model.predict(x_test)
        delay_pred = self.delay_model.predict(x_test)  # type: ignore[union-attr]
        budget_pred = self.budget_model.predict(x_test)
        self.metrics_data = {
            "model": self.model_name,
            "training_examples": len(rows),
            "features": self.feature_names,
            "failure_mae": round(float(mean_absolute_error(failure_test, failure_pred)), 3),
            "failure_r2": round(float(r2_score(failure_test, failure_pred)), 3),
            "delay_mae": round(float(mean_absolute_error(delay_test, delay_pred)), 3),
            "delay_r2": round(float(r2_score(delay_test, delay_pred)), 3),
            "budget_mae": round(float(mean_absolute_error(budget_test, budget_pred)), 3),
            "budget_r2": round(float(r2_score(budget_test, budget_pred)), 3),
            "delay_model": "XGBoost" if XGBRegressor is not None else "GradientBoostingRegressor",
        }
        joblib.dump(self.failure_model, FAILURE_MODEL_PATH)
        joblib.dump(self.delay_model, DELAY_MODEL_PATH)
        joblib.dump(self.budget_model, BUDGET_MODEL_PATH)
        METRICS_PATH.write_text(json.dumps(self.metrics_data, indent=2), encoding="utf-8")
        return self.metrics_data

    def metrics(self) -> dict[str, object]:
        if not self.metrics_data:
            self._load_or_train()
        return self.metrics_data

    def predict(self, project: ProjectProfile) -> ProjectRiskPrediction:
        if self.failure_model is None or self.delay_model is None or self.budget_model is None:
            self.train()
        vector = np.array([self.project_features(project)])
        assert self.failure_model is not None
        assert self.delay_model is not None
        assert self.budget_model is not None
        failure = float(np.clip(self.failure_model.predict(vector)[0], 0, 100))
        delay = float(np.clip(self.delay_model.predict(vector)[0], 0, 100))  # type: ignore[union-attr]
        budget = float(np.clip(self.budget_model.predict(vector)[0], 0, 100))
        spread = float(np.std([failure, delay, budget]))
        confidence = float(np.clip(0.9 - spread / 320 + max(failure, delay, budget) / 620, 0.58, 0.96))
        return ProjectRiskPrediction(
            failure_probability=round(failure, 2),
            delay_probability=round(delay, 2),
            budget_overrun_probability=round(budget, 2),
            confidence=round(confidence, 3),
            features=dict(zip(self.feature_names, self.project_features(project), strict=True)),
        )

    def project_features(self, project: ProjectProfile) -> list[float]:
        history = project.history
        latest = history[-1] if history else ProjectMetricPoint(timestamp=_now())
        days_norm = float(np.clip(project.days_to_deadline / 90, 0, 1))
        deadline_pressure = 1 - days_norm
        completion_gap = 1 - project.current_scope_completion
        required = {skill.lower().strip() for skill in project.required_skills}
        available = {skill.lower().strip() for skill in project.available_skills}
        skill_coverage = len(required & available) / max(len(required), 1) if required else 0.75
        dependency_pressure = float(np.clip((latest.dependency_bottlenecks + project.critical_dependency_count) / 28, 0, 1))
        open_risk_pressure = float(np.clip(latest.open_risks / 36, 0, 1))
        velocity_trend = self._trend([point.sprint_velocity for point in history])
        completion_trend = self._trend([point.task_completion_rate for point in history])
        return [
            days_norm,
            float(np.clip(deadline_pressure, 0, 1)),
            float(np.clip(project.budget_utilization / 1.25, 0, 1)),
            float(np.clip(latest.budget_burn_rate / 1.2, 0, 1)),
            float(np.clip(completion_gap, 0, 1)),
            float(np.clip(latest.sprint_velocity, 0, 1)),
            float(np.clip((velocity_trend + 1) / 2, 0, 1)),
            float(np.clip(latest.task_completion_rate, 0, 1)),
            float(np.clip((completion_trend + 1) / 2, 0, 1)),
            float(np.clip(latest.scope_change_rate, 0, 1)),
            float(np.clip(latest.defect_rate, 0, 1)),
            float(np.clip(latest.rework_ratio, 0, 1)),
            dependency_pressure,
            float(np.clip(latest.resource_allocation, 0, 1)),
            float(np.clip(latest.meeting_load, 0, 1)),
            float(np.clip(latest.communication_score, 0, 1)),
            float(np.clip(latest.team_burnout, 0, 1)),
            float(np.clip(latest.team_compatibility, 0, 1)),
            open_risk_pressure,
            float(np.clip(project.historical_delivery_rate, 0, 1)),
            float(np.clip(skill_coverage, 0, 1)),
            float(np.clip(project.executive_visibility, 0, 1)),
        ]

    @staticmethod
    def _trend(values: list[float]) -> float:
        if len(values) < 2:
            return 0.0
        x_axis = np.arange(len(values))
        slope = float(np.polyfit(x_axis, np.array(values), 1)[0])
        return float(np.clip(slope * 8, -1, 1))


def _now():
    from datetime import datetime, timezone

    return datetime.now(timezone.utc)


project_failure_engine = ProjectFailureEngine()


if __name__ == "__main__":
    print(json.dumps(project_failure_engine.train(), indent=2))
