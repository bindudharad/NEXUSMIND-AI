from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split


ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"
SUITABILITY_MODEL_PATH = ARTIFACT_DIR / "decision_assistant_random_forest.joblib"
FORECAST_MODEL_PATH = ARTIFACT_DIR / "decision_assistant_gradient_boost.joblib"
METRICS_PATH = ARTIFACT_DIR / "decision_assistant_metrics.json"

FEATURE_NAMES = [
    "skill_similarity",
    "historical_success_rate",
    "productivity_score",
    "current_workload",
    "capacity_available",
    "sprint_velocity",
    "communication_quality",
    "collaboration_score",
    "burnout_risk",
    "attrition_risk",
    "delivery_consistency",
    "innovation_score",
    "deadline_pressure",
    "complexity",
    "dependency_pressure",
    "security_sensitivity",
    "scope_volatility",
    "executive_visibility",
]


@dataclass(frozen=True)
class DecisionAssistantMetrics:
    suitability_mae: float
    suitability_r2: float
    completion_mae: float
    completion_r2: float
    risk_mae: float
    risk_r2: float
    trained_samples: int
    model_family: str


def _clip(value: float, lower: float = 0, upper: float = 100) -> float:
    return float(np.clip(value, lower, upper))


def _score_suitability(row: dict[str, float]) -> float:
    overload = max(0, row["current_workload"] - 0.88)
    deadline_penalty = row["deadline_pressure"] * row["complexity"] * 14
    return _clip(
        row["skill_similarity"] * 27
        + row["historical_success_rate"] * 15
        + row["productivity_score"] * 13
        + row["capacity_available"] * 13
        + row["sprint_velocity"] * 10
        + row["communication_quality"] * 7
        + row["collaboration_score"] * 7
        + row["delivery_consistency"] * 10
        + row["innovation_score"] * row["executive_visibility"] * 5
        - row["burnout_risk"] * 16
        - row["attrition_risk"] * 8
        - overload * 29
        - row["dependency_pressure"] * 9
        - row["scope_volatility"] * 7
        - deadline_penalty
    )


def _score_completion_days(row: dict[str, float]) -> float:
    base = 9 + row["complexity"] * 42 + row["dependency_pressure"] * 18 + row["security_sensitivity"] * 9
    acceleration = row["skill_similarity"] * 13 + row["sprint_velocity"] * 9 + row["capacity_available"] * 7 + row["delivery_consistency"] * 8
    pressure = max(0, row["current_workload"] - 0.8) * 18 + row["burnout_risk"] * 8 + row["scope_volatility"] * 10
    return float(np.clip(base - acceleration + pressure, 3, 180))


def _score_risk(row: dict[str, float]) -> float:
    skill_gap = 1 - row["skill_similarity"]
    capacity_gap = 1 - row["capacity_available"]
    communication_gap = 1 - row["communication_quality"]
    deadline_load = row["deadline_pressure"] * row["complexity"]
    return _clip(
        skill_gap * 20
        + capacity_gap * 13
        + max(0, row["current_workload"] - 0.82) * 24
        + row["burnout_risk"] * 18
        + row["attrition_risk"] * 10
        + communication_gap * 9
        + row["dependency_pressure"] * 11
        + row["security_sensitivity"] * 6
        + row["scope_volatility"] * 10
        + deadline_load * 17
        + (1 - row["delivery_consistency"]) * 13
    )


def _training_rows() -> list[dict[str, float]]:
    rng = np.random.default_rng(90210)
    rows: list[dict[str, float]] = []
    for _ in range(6400):
        capability_regime = rng.choice([0.32, 0.52, 0.72, 0.87], p=[0.16, 0.28, 0.36, 0.20])
        pressure_regime = rng.choice([0.2, 0.42, 0.66, 0.84], p=[0.25, 0.35, 0.27, 0.13])
        skill = float(np.clip(rng.normal(capability_regime, 0.13), 0, 1))
        success = float(np.clip(rng.normal(capability_regime + 0.03, 0.11), 0, 1))
        productivity = float(np.clip(rng.normal(capability_regime + 0.02, 0.12), 0, 1))
        workload = float(np.clip(rng.normal(pressure_regime, 0.2), 0, 1.55))
        capacity = float(np.clip(rng.normal(1 - pressure_regime * 0.72, 0.16), 0, 1))
        row = {
            "skill_similarity": skill,
            "historical_success_rate": success,
            "productivity_score": productivity,
            "current_workload": workload,
            "capacity_available": capacity,
            "sprint_velocity": float(np.clip(rng.normal(capability_regime, 0.13), 0, 1)),
            "communication_quality": float(np.clip(rng.normal(capability_regime, 0.15), 0, 1)),
            "collaboration_score": float(np.clip(rng.normal(capability_regime, 0.14), 0, 1)),
            "burnout_risk": float(np.clip(rng.normal(pressure_regime, 0.15), 0, 1)),
            "attrition_risk": float(np.clip(rng.normal(pressure_regime * 0.72, 0.15), 0, 1)),
            "delivery_consistency": float(np.clip(rng.normal(capability_regime + 0.01, 0.13), 0, 1)),
            "innovation_score": float(np.clip(rng.normal(capability_regime, 0.18), 0, 1)),
            "deadline_pressure": float(np.clip(rng.beta(2.3, 3.1), 0, 1)),
            "complexity": float(np.clip(rng.beta(2.6, 2.4), 0, 1)),
            "dependency_pressure": float(np.clip(rng.beta(2.2, 3.8), 0, 1)),
            "security_sensitivity": float(np.clip(rng.beta(2.0, 3.1), 0, 1)),
            "scope_volatility": float(np.clip(rng.beta(2.0, 4.0), 0, 1)),
            "executive_visibility": float(np.clip(rng.beta(2.5, 2.4), 0, 1)),
        }
        rows.append(row)
    return rows


def train_decision_assistant_models() -> DecisionAssistantMetrics:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    rows = _training_rows()
    features = np.array([[row[name] for name in FEATURE_NAMES] for row in rows], dtype=np.float32)
    suitability = np.array([_score_suitability(row) for row in rows], dtype=np.float32)
    completion = np.array([_score_completion_days(row) for row in rows], dtype=np.float32)
    risk = np.array([_score_risk(row) for row in rows], dtype=np.float32)
    train_x, test_x, train_suitability, test_suitability, train_completion, test_completion, train_risk, test_risk = train_test_split(
        features,
        suitability,
        completion,
        risk,
        test_size=0.22,
        random_state=88,
    )
    suitability_model = RandomForestRegressor(n_estimators=260, max_depth=13, min_samples_leaf=3, random_state=88, n_jobs=-1)
    forecast_model = GradientBoostingRegressor(random_state=91, max_depth=3, n_estimators=210)
    risk_model = GradientBoostingRegressor(random_state=93, max_depth=3, n_estimators=220)
    suitability_model.fit(train_x, train_suitability)
    forecast_model.fit(train_x, train_completion)
    risk_model.fit(train_x, train_risk)
    suitability_pred = suitability_model.predict(test_x)
    completion_pred = forecast_model.predict(test_x)
    risk_pred = risk_model.predict(test_x)
    metrics = DecisionAssistantMetrics(
        suitability_mae=round(float(mean_absolute_error(test_suitability, suitability_pred)), 3),
        suitability_r2=round(float(r2_score(test_suitability, suitability_pred)), 3),
        completion_mae=round(float(mean_absolute_error(test_completion, completion_pred)), 3),
        completion_r2=round(float(r2_score(test_completion, completion_pred)), 3),
        risk_mae=round(float(mean_absolute_error(test_risk, risk_pred)), 3),
        risk_r2=round(float(r2_score(test_risk, risk_pred)), 3),
        trained_samples=len(rows),
        model_family="RandomForest team suitability + GradientBoosting timeline and delivery-risk forecasters",
    )
    joblib.dump(suitability_model, SUITABILITY_MODEL_PATH)
    joblib.dump({"completion": forecast_model, "risk": risk_model}, FORECAST_MODEL_PATH)
    METRICS_PATH.write_text(json.dumps(asdict(metrics), indent=2), encoding="utf-8")
    return metrics


class DecisionAssistantEngine:
    model_name = "RandomForest Decision Router + GradientBoosting Timeline Risk Forecaster"

    def __init__(self) -> None:
        self._suitability_model: RandomForestRegressor | None = None
        self._completion_model: GradientBoostingRegressor | None = None
        self._risk_model: GradientBoostingRegressor | None = None

    @property
    def available(self) -> bool:
        return SUITABILITY_MODEL_PATH.exists() and FORECAST_MODEL_PATH.exists() and METRICS_PATH.exists()

    def ensure_artifacts(self) -> None:
        if not self.available:
            train_decision_assistant_models()

    def metrics(self) -> dict[str, object]:
        self.ensure_artifacts()
        return json.loads(METRICS_PATH.read_text(encoding="utf-8"))

    def _load(self) -> None:
        self.ensure_artifacts()
        if self._suitability_model is None:
            self._suitability_model = joblib.load(SUITABILITY_MODEL_PATH)
            bundle = joblib.load(FORECAST_MODEL_PATH)
            self._completion_model = bundle["completion"]
            self._risk_model = bundle["risk"]

    def predict(self, rows: list[dict[str, float]]) -> list[dict[str, float]]:
        self._load()
        assert self._suitability_model is not None
        assert self._completion_model is not None
        assert self._risk_model is not None
        matrix = np.array([[float(row[name]) for name in FEATURE_NAMES] for row in rows], dtype=np.float32)
        suitability_ml = self._suitability_model.predict(matrix)
        completion_ml = self._completion_model.predict(matrix)
        risk_ml = self._risk_model.predict(matrix)
        predictions: list[dict[str, float]] = []
        for index, row in enumerate(rows):
            formula_suitability = _score_suitability(row)
            formula_completion = _score_completion_days(row)
            formula_risk = _score_risk(row)
            suitability = _clip(float(suitability_ml[index]) * 0.74 + formula_suitability * 0.26)
            completion = float(np.clip(float(completion_ml[index]) * 0.72 + formula_completion * 0.28, 3, 180))
            risk = _clip(float(risk_ml[index]) * 0.72 + formula_risk * 0.28)
            confidence = float(np.clip(0.93 - abs(suitability - (100 - risk)) / 280 - row["scope_volatility"] * 0.06, 0.68, 0.94))
            predictions.append(
                {
                    "suitability_score": round(suitability, 3),
                    "estimated_completion_days": round(completion, 3),
                    "risk_score": round(risk, 3),
                    "confidence": round(confidence, 3),
                }
            )
        return predictions


decision_assistant_engine = DecisionAssistantEngine()
