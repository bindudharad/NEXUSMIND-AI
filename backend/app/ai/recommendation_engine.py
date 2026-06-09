from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

from app.schemas.recommendations import EmployeeProfile, TaskProfile


ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"
MODEL_PATH = ARTIFACT_DIR / "recommendation_ranker.joblib"
METRICS_PATH = ARTIFACT_DIR / "recommendation_metrics.json"


@dataclass(frozen=True)
class RankingResult:
    score: float
    confidence: float


class EnterpriseRecommendationEngine:
    """Hybrid recommendation engine: content matching plus trained impact ranking."""

    model_name = "Hybrid RandomForest Enterprise Recommender"
    feature_names = [
        "sender_overload",
        "receiver_available_ratio",
        "skill_match",
        "receiver_productivity",
        "receiver_collaboration",
        "task_priority",
        "stress_reduction",
        "overtime_reduction",
        "task_effort_ratio",
    ]

    def __init__(self) -> None:
        ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
        self.model: RandomForestRegressor | None = None
        self.metrics: dict[str, float | int | str] = {}
        self._load_or_train()

    @property
    def available(self) -> bool:
        return self.model is not None and MODEL_PATH.exists()

    def _load_or_train(self) -> None:
        if MODEL_PATH.exists() and METRICS_PATH.exists():
            self.model = joblib.load(MODEL_PATH)
            self.metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
            return
        self.train()

    def train(self) -> dict[str, float | int | str]:
        rng = np.random.default_rng(42)
        rows: list[list[float]] = []
        targets: list[float] = []
        for _ in range(3600):
            sender_overload = rng.uniform(0, 0.9)
            receiver_available_ratio = rng.uniform(0, 0.9)
            skill_match = rng.choice([0, 0.35, 0.7, 1.0], p=[0.12, 0.18, 0.28, 0.42])
            receiver_productivity = rng.uniform(0.45, 0.98)
            receiver_collaboration = rng.uniform(0.4, 0.98)
            task_priority = rng.integers(1, 6) / 5
            stress_reduction = rng.uniform(0, 0.9)
            overtime_reduction = rng.uniform(0, 1)
            task_effort_ratio = rng.uniform(0.05, 0.75)
            features = [
                sender_overload,
                receiver_available_ratio,
                skill_match,
                receiver_productivity,
                receiver_collaboration,
                task_priority,
                stress_reduction,
                overtime_reduction,
                task_effort_ratio,
            ]
            target = (
                22 * sender_overload
                + 18 * receiver_available_ratio
                + 20 * skill_match
                + 11 * receiver_productivity
                + 9 * receiver_collaboration
                + 8 * task_priority
                + 9 * stress_reduction
                + 6 * overtime_reduction
                - 7 * task_effort_ratio
                + rng.normal(0, 2.3)
            )
            rows.append(features)
            targets.append(float(np.clip(target, 0, 100)))

        x_train, x_test, y_train, y_test = train_test_split(np.array(rows), np.array(targets), test_size=0.22, random_state=7)
        self.model = RandomForestRegressor(n_estimators=180, max_depth=12, min_samples_leaf=4, random_state=7, n_jobs=-1)
        self.model.fit(x_train, y_train)
        predictions = self.model.predict(x_test)
        self.metrics = {
            "model": self.model_name,
            "training_examples": len(rows),
            "mae": round(float(mean_absolute_error(y_test, predictions)), 3),
            "r2": round(float(r2_score(y_test, predictions)), 3),
        }
        joblib.dump(self.model, MODEL_PATH)
        METRICS_PATH.write_text(json.dumps(self.metrics, indent=2), encoding="utf-8")
        return self.metrics

    def rank_reassignment(self, sender: EmployeeProfile, receiver: EmployeeProfile, task: TaskProfile) -> RankingResult:
        if self.model is None:
            self.train()
        features = np.array([self._features(sender, receiver, task)])
        prediction = float(self.model.predict(features)[0]) if self.model else 0.0
        skill_match = self._skill_match(receiver, task.required_skill)
        confidence = np.clip(0.62 + skill_match * 0.2 + receiver.collaboration_score * 0.12 - task.effort_hours / 240, 0.45, 0.95)
        return RankingResult(score=round(float(np.clip(prediction, 0, 100)), 2), confidence=round(float(confidence), 3))

    def break_score(self, employee: EmployeeProfile) -> RankingResult:
        utilization = employee.allocated_hours / employee.capacity_hours
        productivity_drag = max(0.0, 0.82 - employee.productivity)
        raw = 100 * (
            0.28 * employee.stress_score
            + 0.25 * employee.burnout_risk
            + 0.2 * min(employee.overtime_hours / 18, 1)
            + 0.17 * max(0, utilization - 1)
            + 0.1 * productivity_drag
        )
        confidence = np.clip(0.58 + employee.stress_score * 0.18 + employee.burnout_risk * 0.16 + min(employee.overtime_hours / 24, 0.12), 0.5, 0.94)
        return RankingResult(score=round(float(np.clip(raw, 0, 100)), 2), confidence=round(float(confidence), 3))

    def team_balance_score(self, employees: list[EmployeeProfile]) -> float:
        if not employees:
            return 0.0
        utilizations = np.array([employee.allocated_hours / employee.capacity_hours for employee in employees])
        stress = np.array([employee.stress_score for employee in employees])
        imbalance = np.std(utilizations) * 42 + np.mean(stress) * 28
        return round(float(np.clip(100 - imbalance, 0, 100)), 2)

    def _features(self, sender: EmployeeProfile, receiver: EmployeeProfile, task: TaskProfile) -> list[float]:
        sender_overload = max(0, sender.allocated_hours - sender.capacity_hours) / sender.capacity_hours
        receiver_available_ratio = max(0, receiver.capacity_hours - receiver.allocated_hours) / receiver.capacity_hours
        return [
            float(np.clip(sender_overload, 0, 1)),
            float(np.clip(receiver_available_ratio, 0, 1)),
            self._skill_match(receiver, task.required_skill),
            receiver.productivity,
            receiver.collaboration_score,
            task.priority / 5,
            max(0, sender.stress_score - receiver.stress_score),
            max(0, sender.overtime_hours - receiver.overtime_hours) / 24,
            min(task.effort_hours / max(receiver.capacity_hours, 1), 1),
        ]

    @staticmethod
    def _skill_match(employee: EmployeeProfile, required_skill: str) -> float:
        normalized = {skill.strip().lower() for skill in employee.skills}
        required = required_skill.strip().lower()
        if required in normalized:
            return 1.0
        return 0.45 if any(required in skill or skill in required for skill in normalized) else 0.0


recommendation_engine = EnterpriseRecommendationEngine()


if __name__ == "__main__":
    print(json.dumps(recommendation_engine.train(), indent=2))
