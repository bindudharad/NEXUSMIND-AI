from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor

from app.schemas.manager_dashboard import EmployeeWorkloadInput, ProjectDeliveryInput, TeamAnalyticsInput


ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"
TEAM_RISK_PATH = ARTIFACT_DIR / "manager_team_risk_rf.joblib"
OVERLOAD_PATH = ARTIFACT_DIR / "manager_overload_xgb.joblib"
DELAY_PATH = ARTIFACT_DIR / "manager_delay_rf.joblib"
METRICS_PATH = ARTIFACT_DIR / "manager_dashboard_metrics.json"


@dataclass(frozen=True)
class ManagerPrediction:
    value: float


class ManagerAnalyticsEngine:
    model_name = "RandomForest/XGBoost Manager Risk Intelligence"

    def __init__(self) -> None:
        ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
        self.team_risk_model: RandomForestRegressor | None = None
        self.overload_model: XGBRegressor | None = None
        self.delay_model: RandomForestRegressor | None = None
        self.metrics: dict[str, float | int | str] = {}
        self._load_or_train()

    @property
    def available(self) -> bool:
        return all(model is not None for model in [self.team_risk_model, self.overload_model, self.delay_model])

    def _load_or_train(self) -> None:
        if TEAM_RISK_PATH.exists() and OVERLOAD_PATH.exists() and DELAY_PATH.exists() and METRICS_PATH.exists():
            self.team_risk_model = joblib.load(TEAM_RISK_PATH)
            self.overload_model = joblib.load(OVERLOAD_PATH)
            self.delay_model = joblib.load(DELAY_PATH)
            self.metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
            return
        self.train()

    def train(self) -> dict[str, float | int | str]:
        rng = np.random.default_rng(144)
        team_x, team_y = self._team_dataset(rng, 3600)
        employee_x, employee_y = self._employee_dataset(rng, 3600)
        project_x, project_y = self._project_dataset(rng, 3600)

        self.team_risk_model, team_metrics = self._fit_random_forest(team_x, team_y, "team_risk", 31)
        self.overload_model, overload_metrics = self._fit_xgboost(employee_x, employee_y, "employee_overload")
        self.delay_model, delay_metrics = self._fit_random_forest(project_x, project_y, "delay_prediction", 41)
        self.metrics = {
            "model": self.model_name,
            "training_examples": int(len(team_x) + len(employee_x) + len(project_x)),
            **team_metrics,
            **overload_metrics,
            **delay_metrics,
        }
        joblib.dump(self.team_risk_model, TEAM_RISK_PATH)
        joblib.dump(self.overload_model, OVERLOAD_PATH)
        joblib.dump(self.delay_model, DELAY_PATH)
        METRICS_PATH.write_text(json.dumps(self.metrics, indent=2), encoding="utf-8")
        return self.metrics

    def predict_team_risk(self, team: TeamAnalyticsInput) -> ManagerPrediction:
        if not self.available:
            self.train()
        value = float(self.team_risk_model.predict(np.array([self.team_vector(team)], dtype=np.float32))[0]) if self.team_risk_model else 0
        return ManagerPrediction(round(float(np.clip(value, 0, 100)), 2))

    def predict_overload(self, employee: EmployeeWorkloadInput) -> ManagerPrediction:
        if not self.available:
            self.train()
        value = float(self.overload_model.predict(np.array([self.employee_vector(employee)], dtype=np.float32))[0]) if self.overload_model else 0
        return ManagerPrediction(round(float(np.clip(value, 0, 100)), 2))

    def predict_delay(self, project: ProjectDeliveryInput) -> ManagerPrediction:
        if not self.available:
            self.train()
        value = float(self.delay_model.predict(np.array([self.project_vector(project)], dtype=np.float32))[0]) if self.delay_model else 0
        return ManagerPrediction(round(float(np.clip(value, 0, 100)), 2))

    @staticmethod
    def team_vector(team: TeamAnalyticsInput) -> list[float]:
        return [
            team.burnout_probability,
            team.productivity_decline,
            team.average_stress,
            team.toxicity_ratio,
            team.overload_ratio,
            min(team.missed_deadlines / 12, 1),
            team.attendance_rate,
            team.collaboration_score,
            team.overtime_escalation,
            min(team.dependency_bottlenecks / 12, 1),
        ]

    @staticmethod
    def employee_vector(employee: EmployeeWorkloadInput) -> list[float]:
        return [
            min(employee.active_tasks / 24, 1),
            min(employee.overtime_hours / 24, 1),
            min(employee.meeting_hours / 18, 1),
            employee.productivity_score,
            employee.work_intensity,
            employee.deadline_pressure,
            min(employee.multi_project_allocation / 8, 1),
            employee.stress_score,
            employee.task_completion_ratio,
        ]

    @staticmethod
    def project_vector(project: ProjectDeliveryInput) -> list[float]:
        return [
            project.task_completion_speed,
            project.team_productivity_trend,
            project.historical_delivery_rate,
            project.burnout_growth,
            project.team_overload,
            min(project.dependency_bottlenecks / 12, 1),
            project.resource_shortage,
            project.communication_efficiency,
            project.scope_change_rate,
            min(project.days_to_deadline / 120, 1),
        ]

    @staticmethod
    def _fit_random_forest(features: np.ndarray, target: np.ndarray, prefix: str, seed: int) -> tuple[RandomForestRegressor, dict[str, float]]:
        x_train, x_test, y_train, y_test = train_test_split(features, target, test_size=0.22, random_state=seed)
        model = RandomForestRegressor(n_estimators=220, max_depth=13, min_samples_leaf=4, random_state=seed, n_jobs=-1)
        model.fit(x_train, y_train)
        predictions = model.predict(x_test)
        return model, {
            f"{prefix}_mae": round(float(mean_absolute_error(y_test, predictions)), 3),
            f"{prefix}_r2": round(float(r2_score(y_test, predictions)), 3),
        }

    @staticmethod
    def _fit_xgboost(features: np.ndarray, target: np.ndarray, prefix: str) -> tuple[XGBRegressor, dict[str, float]]:
        x_train, x_test, y_train, y_test = train_test_split(features, target, test_size=0.22, random_state=37)
        model = XGBRegressor(
            n_estimators=160,
            max_depth=4,
            learning_rate=0.055,
            subsample=0.9,
            colsample_bytree=0.9,
            objective="reg:squarederror",
            random_state=37,
            n_jobs=-1,
        )
        model.fit(x_train, y_train)
        predictions = model.predict(x_test)
        return model, {
            f"{prefix}_mae": round(float(mean_absolute_error(y_test, predictions)), 3),
            f"{prefix}_r2": round(float(r2_score(y_test, predictions)), 3),
        }

    @staticmethod
    def _team_dataset(rng: np.random.Generator, rows: int) -> tuple[np.ndarray, np.ndarray]:
        burnout = rng.beta(2.3, 2.5, rows)
        productivity_decline = rng.beta(2.1, 3.4, rows)
        stress = rng.beta(2.5, 2.4, rows)
        toxicity = rng.beta(1.3, 7.5, rows)
        overload = rng.beta(2.2, 3.0, rows)
        missed = rng.poisson(2.4, rows).clip(0, 14) / 12
        attendance = rng.normal(0.93, 0.08, rows).clip(0.55, 1)
        collaboration = rng.normal(0.78, 0.16, rows).clip(0.25, 1)
        overtime = rng.beta(2.0, 3.0, rows)
        bottlenecks = rng.poisson(2.1, rows).clip(0, 14) / 12
        target = (
            burnout * 22
            + productivity_decline * 15
            + stress * 16
            + toxicity * 12
            + overload * 18
            + missed * 9
            + (1 - attendance) * 12
            + (1 - collaboration) * 9
            + overtime * 8
            + bottlenecks * 11
            + rng.normal(0, 2.7, rows)
        ).clip(0, 100)
        return np.column_stack([burnout, productivity_decline, stress, toxicity, overload, missed, attendance, collaboration, overtime, bottlenecks]).astype(np.float32), target.astype(np.float32)

    @staticmethod
    def _employee_dataset(rng: np.random.Generator, rows: int) -> tuple[np.ndarray, np.ndarray]:
        active_tasks = rng.normal(10, 5, rows).clip(0, 30) / 24
        overtime = rng.normal(8, 6, rows).clip(0, 30) / 24
        meetings = rng.normal(7, 4, rows).clip(0, 20) / 18
        productivity = rng.normal(0.77, 0.17, rows).clip(0.2, 1)
        intensity = rng.beta(2.8, 2.2, rows)
        deadline = rng.beta(2.6, 2.3, rows)
        projects = rng.poisson(2.5, rows).clip(1, 10) / 8
        stress = rng.beta(2.5, 2.4, rows)
        completion = rng.normal(0.76, 0.18, rows).clip(0.2, 1)
        target = (
            active_tasks * 17
            + overtime * 18
            + meetings * 10
            + (1 - productivity) * 13
            + intensity * 18
            + deadline * 14
            + projects * 9
            + stress * 16
            + (1 - completion) * 12
            + rng.normal(0, 2.5, rows)
        ).clip(0, 100)
        return np.column_stack([active_tasks, overtime, meetings, productivity, intensity, deadline, projects, stress, completion]).astype(np.float32), target.astype(np.float32)

    @staticmethod
    def _project_dataset(rng: np.random.Generator, rows: int) -> tuple[np.ndarray, np.ndarray]:
        completion_speed = rng.normal(0.75, 0.18, rows).clip(0.1, 1)
        productivity_trend = rng.normal(-0.05, 0.38, rows).clip(-1, 1)
        delivery_rate = rng.normal(0.8, 0.15, rows).clip(0.25, 1)
        burnout_growth = rng.beta(2.0, 3.0, rows)
        overload = rng.beta(2.4, 2.7, rows)
        bottlenecks = rng.poisson(2.5, rows).clip(0, 16) / 12
        shortage = rng.beta(1.8, 3.5, rows)
        communication = rng.normal(0.78, 0.16, rows).clip(0.2, 1)
        scope = rng.beta(1.7, 4.0, rows)
        deadline = rng.integers(5, 130, rows) / 120
        target = (
            (1 - completion_speed) * 18
            + np.clip(-productivity_trend, 0, 1) * 12
            + (1 - delivery_rate) * 14
            + burnout_growth * 14
            + overload * 15
            + bottlenecks * 13
            + shortage * 12
            + (1 - communication) * 8
            + scope * 9
            + (1 - deadline) * 7
            + rng.normal(0, 2.8, rows)
        ).clip(0, 100)
        return np.column_stack([completion_speed, productivity_trend, delivery_rate, burnout_growth, overload, bottlenecks, shortage, communication, scope, deadline]).astype(np.float32), target.astype(np.float32)


manager_analytics_engine = ManagerAnalyticsEngine()


if __name__ == "__main__":
    print(json.dumps(manager_analytics_engine.train(), indent=2))
