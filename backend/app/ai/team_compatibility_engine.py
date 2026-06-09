from __future__ import annotations

import json
import os
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "8")

import joblib
import numpy as np
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, mean_absolute_error, r2_score, roc_auc_score
from sklearn.model_selection import train_test_split

from app.schemas.team_compatibility import TeamEmployeeProfile, TeamInteractionSignal


ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"
COMPATIBILITY_MODEL_PATH = ARTIFACT_DIR / "team_compatibility_regressor.joblib"
CONFLICT_MODEL_PATH = ARTIFACT_DIR / "team_conflict_classifier.joblib"
CLUSTER_MODEL_PATH = ARTIFACT_DIR / "team_workstyle_clusterer.joblib"
METRICS_PATH = ARTIFACT_DIR / "team_compatibility_metrics.json"

CLUSTER_LABELS = {
    0: "stabilizer",
    1: "connector",
    2: "pressure-absorber",
    3: "execution-driver",
}

WORKSTYLE_COMPATIBILITY = {
    ("focused", "supportive"): 0.88,
    ("focused", "analytical"): 0.9,
    ("focused", "collaborative"): 0.76,
    ("focused", "creative"): 0.72,
    ("focused", "decisive"): 0.7,
    ("collaborative", "supportive"): 0.93,
    ("collaborative", "creative"): 0.84,
    ("collaborative", "decisive"): 0.78,
    ("collaborative", "analytical"): 0.74,
    ("decisive", "supportive"): 0.8,
    ("decisive", "analytical"): 0.83,
    ("decisive", "creative"): 0.69,
    ("supportive", "analytical"): 0.78,
    ("supportive", "creative"): 0.82,
    ("analytical", "creative"): 0.76,
}


@dataclass(frozen=True)
class PairPrediction:
    compatibility_score: float
    conflict_probability: float
    confidence: float


class TeamCompatibilityEngine:
    model_name = "Graph-aware RandomForest Team Compatibility Engine"
    feature_names = [
        "skill_overlap",
        "productivity_alignment",
        "stress_alignment",
        "stress_mean",
        "sentiment_alignment",
        "communication_alignment",
        "workstyle_fit",
        "task_completion_alignment",
        "collaboration_signal",
        "past_success_rate",
        "timezone_overlap",
        "leadership_fit",
        "burnout_mean",
        "conflict_incident_ratio",
        "workload_balance",
    ]

    def __init__(self) -> None:
        ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
        self.compatibility_model: RandomForestRegressor | None = None
        self.conflict_model: RandomForestClassifier | None = None
        self.cluster_model: KMeans | None = None
        self.metrics_data: dict[str, object] = {}
        self._load_or_train()

    @property
    def available(self) -> bool:
        return (
            self.compatibility_model is not None
            and self.conflict_model is not None
            and self.cluster_model is not None
            and COMPATIBILITY_MODEL_PATH.exists()
        )

    def _load_or_train(self) -> None:
        if COMPATIBILITY_MODEL_PATH.exists() and CONFLICT_MODEL_PATH.exists() and CLUSTER_MODEL_PATH.exists() and METRICS_PATH.exists():
            self.compatibility_model = joblib.load(COMPATIBILITY_MODEL_PATH)
            self.conflict_model = joblib.load(CONFLICT_MODEL_PATH)
            self.cluster_model = joblib.load(CLUSTER_MODEL_PATH)
            self.compatibility_model.n_jobs = 1
            self.conflict_model.n_jobs = 1
            self.metrics_data = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
            return
        self.train()

    def train(self) -> dict[str, object]:
        rng = np.random.default_rng(5150)
        rows: list[list[float]] = []
        targets: list[float] = []
        conflict_labels: list[int] = []
        cluster_rows: list[list[float]] = []

        for _ in range(6200):
            skill_overlap = rng.beta(2.5, 2.2)
            productivity_alignment = rng.beta(4, 1.8)
            stress_alignment = rng.beta(3.4, 2.4)
            stress_mean = rng.beta(2.1, 3.1)
            sentiment_alignment = rng.beta(3.2, 2.1)
            communication_alignment = rng.beta(3, 2.2)
            workstyle_fit = rng.beta(3.5, 2.0)
            task_completion_alignment = rng.beta(3.3, 2.2)
            collaboration_signal = rng.beta(2.9, 2.2)
            past_success_rate = rng.beta(2.6, 2.2)
            timezone_overlap = rng.beta(6, 1.4)
            leadership_fit = rng.beta(2.8, 2.4)
            burnout_mean = rng.beta(2.0, 3.8)
            conflict_incident_ratio = rng.beta(1.3, 7.0)
            workload_balance = rng.beta(3.4, 2.0)
            features = [
                skill_overlap,
                productivity_alignment,
                stress_alignment,
                stress_mean,
                sentiment_alignment,
                communication_alignment,
                workstyle_fit,
                task_completion_alignment,
                collaboration_signal,
                past_success_rate,
                timezone_overlap,
                leadership_fit,
                burnout_mean,
                conflict_incident_ratio,
                workload_balance,
            ]
            score = 100 * (
                0.14 * skill_overlap
                + 0.11 * productivity_alignment
                + 0.07 * stress_alignment
                + 0.11 * sentiment_alignment
                + 0.11 * communication_alignment
                + 0.1 * workstyle_fit
                + 0.08 * task_completion_alignment
                + 0.1 * collaboration_signal
                + 0.09 * past_success_rate
                + 0.05 * timezone_overlap
                + 0.05 * leadership_fit
                + 0.06 * workload_balance
                - 0.09 * stress_mean
                - 0.12 * burnout_mean
                - 0.14 * conflict_incident_ratio
            )
            score = float(np.clip(score + rng.normal(0, 4.0), 0, 100))
            conflict = int(
                score < 48
                or conflict_incident_ratio > 0.42
                or (burnout_mean > 0.72 and communication_alignment < 0.45)
                or (sentiment_alignment < 0.38 and stress_mean > 0.64)
            )
            rows.append(features)
            targets.append(score)
            conflict_labels.append(conflict)
            cluster_rows.append(
                [
                    rng.beta(3, 2),
                    rng.beta(2.4, 2.8),
                    rng.beta(2.8, 2.4),
                    rng.beta(2.2, 2.9),
                    rng.beta(2.7, 2.3),
                    rng.beta(2.6, 2.4),
                ]
            )

        x_train, x_test, y_train, y_test, conflict_train, conflict_test = train_test_split(
            np.array(rows),
            np.array(targets),
            np.array(conflict_labels),
            test_size=0.22,
            random_state=29,
            stratify=np.array(conflict_labels),
        )
        self.compatibility_model = RandomForestRegressor(
            n_estimators=260,
            max_depth=14,
            min_samples_leaf=3,
            random_state=29,
            n_jobs=1,
        )
        self.conflict_model = RandomForestClassifier(
            n_estimators=240,
            max_depth=12,
            min_samples_leaf=4,
            class_weight="balanced",
            random_state=31,
            n_jobs=1,
        )
        self.cluster_model = KMeans(n_clusters=4, random_state=33, n_init=12)
        self.compatibility_model.fit(x_train, y_train)
        self.conflict_model.fit(x_train, conflict_train)
        self.cluster_model.fit(np.array(cluster_rows))
        predictions = self.compatibility_model.predict(x_test)
        conflict_predictions = self.conflict_model.predict(x_test)
        conflict_probabilities = self.conflict_model.predict_proba(x_test)[:, 1]
        self.metrics_data = {
            "model": self.model_name,
            "training_examples": len(rows),
            "mae": round(float(mean_absolute_error(y_test, predictions)), 3),
            "r2": round(float(r2_score(y_test, predictions)), 3),
            "conflict_accuracy": round(float(accuracy_score(conflict_test, conflict_predictions)), 3),
            "conflict_roc_auc": round(float(roc_auc_score(conflict_test, conflict_probabilities)), 3),
            "clusters": CLUSTER_LABELS,
            "features": self.feature_names,
        }
        joblib.dump(self.compatibility_model, COMPATIBILITY_MODEL_PATH)
        joblib.dump(self.conflict_model, CONFLICT_MODEL_PATH)
        joblib.dump(self.cluster_model, CLUSTER_MODEL_PATH)
        METRICS_PATH.write_text(json.dumps(self.metrics_data, indent=2), encoding="utf-8")
        return self.metrics_data

    def metrics(self) -> dict[str, object]:
        if not self.metrics_data:
            self._load_or_train()
        return self.metrics_data

    def predict_pair(
        self,
        first: TeamEmployeeProfile,
        second: TeamEmployeeProfile,
        interaction: TeamInteractionSignal | None = None,
    ) -> PairPrediction:
        if self.compatibility_model is None or self.conflict_model is None:
            self.train()
        vector = np.array([self.pair_features(first, second, interaction)])
        assert self.compatibility_model is not None
        assert self.conflict_model is not None
        compatibility = round(float(np.clip(self.compatibility_model.predict(vector)[0], 0, 100)), 2)
        conflict_probability = round(float(np.clip(self.conflict_model.predict_proba(vector)[0][1] * 100, 0, 100)), 2)
        confidence = round(float(np.clip(0.6 + abs(compatibility - 50) / 155 + abs(conflict_probability - 50) / 220, 0.55, 0.96)), 3)
        return PairPrediction(
            compatibility_score=compatibility,
            conflict_probability=conflict_probability,
            confidence=confidence,
        )

    def pair_features(
        self,
        first: TeamEmployeeProfile,
        second: TeamEmployeeProfile,
        interaction: TeamInteractionSignal | None = None,
    ) -> list[float]:
        first_skills = {skill.lower().strip() for skill in first.skills}
        second_skills = {skill.lower().strip() for skill in second.skills}
        union = first_skills | second_skills
        skill_overlap = len(first_skills & second_skills) / max(len(union), 1)
        productivity_alignment = 1 - abs(self._avg(first.productivity_history, first.task_completion_rate) - self._avg(second.productivity_history, second.task_completion_rate))
        first_stress = self._avg(first.stress_history, first.burnout_risk)
        second_stress = self._avg(second.stress_history, second.burnout_risk)
        stress_alignment = 1 - abs(first_stress - second_stress)
        stress_mean = (first_stress + second_stress) / 2
        sentiment_alignment = 1 - abs(first.sentiment_trend - second.sentiment_trend) / 2
        communication_alignment = 1 - abs(first.meeting_participation - second.meeting_participation)
        workstyle_fit = self.workstyle_fit(first.work_style, second.work_style)
        task_completion_alignment = 1 - abs(first.task_completion_rate - second.task_completion_rate)
        collaboration_signal = interaction.collaboration_frequency if interaction else (first.collaboration_frequency + second.collaboration_frequency) / 2
        past_success_rate = interaction.past_success_rate if interaction else collaboration_signal * 0.72 + sentiment_alignment * 0.28
        timezone_overlap = min(first.timezone_overlap, second.timezone_overlap)
        leadership_fit = max(first.leadership_score, second.leadership_score) * 0.7 + (1 - abs(first.leadership_score - second.leadership_score)) * 0.3
        burnout_mean = (first.burnout_risk + second.burnout_risk) / 2
        conflict_incident_ratio = min((interaction.conflict_incidents if interaction else 0) / 8, 1)
        workload_balance = 1 - abs(first.current_workload - second.current_workload)
        return [
            float(np.clip(skill_overlap, 0, 1)),
            float(np.clip(productivity_alignment, 0, 1)),
            float(np.clip(stress_alignment, 0, 1)),
            float(np.clip(stress_mean, 0, 1)),
            float(np.clip(sentiment_alignment, 0, 1)),
            float(np.clip(communication_alignment, 0, 1)),
            float(np.clip(workstyle_fit, 0, 1)),
            float(np.clip(task_completion_alignment, 0, 1)),
            float(np.clip(collaboration_signal, 0, 1)),
            float(np.clip(past_success_rate, 0, 1)),
            float(np.clip(timezone_overlap, 0, 1)),
            float(np.clip(leadership_fit, 0, 1)),
            float(np.clip(burnout_mean, 0, 1)),
            float(np.clip(conflict_incident_ratio, 0, 1)),
            float(np.clip(workload_balance, 0, 1)),
        ]

    def cluster_employee(self, employee: TeamEmployeeProfile) -> str:
        if self.cluster_model is None:
            self.train()
        assert self.cluster_model is not None
        vector = np.array(
            [[
                self._avg(employee.productivity_history, employee.task_completion_rate),
                self._avg(employee.stress_history, employee.burnout_risk),
                employee.meeting_participation,
                employee.leadership_score,
                employee.focus_ratio,
                (employee.sentiment_trend + 1) / 2,
            ]]
        )
        label = int(self.cluster_model.predict(vector)[0])
        return CLUSTER_LABELS.get(label, "connector")

    @staticmethod
    def workstyle_fit(first: str, second: str) -> float:
        if first == second:
            return 0.82
        return WORKSTYLE_COMPATIBILITY.get((first, second), WORKSTYLE_COMPATIBILITY.get((second, first), 0.68))

    @staticmethod
    def best_team_combinations(employees: list[TeamEmployeeProfile], target_size: int) -> list[tuple[TeamEmployeeProfile, ...]]:
        if len(employees) <= target_size:
            return [tuple(employees)]
        return list(combinations(employees, target_size))[:260]

    @staticmethod
    def _avg(values: list[float], fallback: float) -> float:
        return float(np.clip(np.mean(values) if values else fallback, 0, 1))


team_compatibility_engine = TeamCompatibilityEngine()


if __name__ == "__main__":
    print(json.dumps(team_compatibility_engine.train(), indent=2))
