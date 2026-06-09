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
HEALTH_MODEL_PATH = ARTIFACT_DIR / "client_satisfaction_random_forest.joblib"
RISK_MODEL_PATH = ARTIFACT_DIR / "client_satisfaction_gradient_boost.joblib"
METRICS_PATH = ARTIFACT_DIR / "client_satisfaction_metrics.json"

FEATURE_NAMES = [
    "delay_pressure",
    "missed_milestone_pressure",
    "sla_pressure",
    "bug_pressure",
    "incident_pressure",
    "qa_quality",
    "rework_ratio",
    "issue_resolution_pressure",
    "escalation_pressure",
    "sentiment_negativity",
    "interaction_decline",
    "feedback_risk",
    "nps_decline",
    "renewal_pressure",
    "delivery_consistency",
    "sponsor_engagement",
    "critical_issue_pressure",
    "contract_value_pressure",
]


@dataclass(frozen=True)
class ClientSatisfactionMetrics:
    health_mae: float
    health_r2: float
    churn_mae: float
    churn_r2: float
    escalation_mae: float
    escalation_r2: float
    trained_samples: int
    model_family: str


def _clip(value: float, lower: float = 0, upper: float = 100) -> float:
    return float(np.clip(value, lower, upper))


def _score_health(row: dict[str, float]) -> float:
    operating_quality = (
        row["qa_quality"] * 14
        + (1 - row["bug_pressure"]) * 9
        + (1 - row["incident_pressure"]) * 8
        + (1 - row["delay_pressure"]) * 11
        + (1 - row["sla_pressure"]) * 8
        + (1 - row["issue_resolution_pressure"]) * 8
        + (1 - row["sentiment_negativity"]) * 12
        + (1 - row["interaction_decline"]) * 6
        + (1 - row["feedback_risk"]) * 9
        + (1 - row["nps_decline"]) * 6
        + row["delivery_consistency"] * 11
        + row["sponsor_engagement"] * 8
    )
    pressure = (
        row["escalation_pressure"] * 11
        + row["critical_issue_pressure"] * 8
        + row["rework_ratio"] * 6
        + row["renewal_pressure"] * 5
        + row["contract_value_pressure"] * max(row["delay_pressure"], row["escalation_pressure"]) * 5
    )
    return _clip(operating_quality - pressure)


def _score_churn(row: dict[str, float]) -> float:
    return _clip(
        row["delay_pressure"] * 13
        + row["missed_milestone_pressure"] * 10
        + row["sla_pressure"] * 11
        + row["bug_pressure"] * 7
        + row["incident_pressure"] * 8
        + (1 - row["qa_quality"]) * 9
        + row["rework_ratio"] * 8
        + row["issue_resolution_pressure"] * 10
        + row["escalation_pressure"] * 14
        + row["sentiment_negativity"] * 15
        + row["interaction_decline"] * 7
        + row["feedback_risk"] * 12
        + row["nps_decline"] * 8
        + row["renewal_pressure"] * 8
        + (1 - row["delivery_consistency"]) * 11
        + (1 - row["sponsor_engagement"]) * 6
        + row["critical_issue_pressure"] * 10
    )


def _score_escalation(row: dict[str, float]) -> float:
    return _clip(
        row["escalation_pressure"] * 21
        + row["sla_pressure"] * 13
        + row["issue_resolution_pressure"] * 13
        + row["sentiment_negativity"] * 14
        + row["critical_issue_pressure"] * 12
        + row["delay_pressure"] * 10
        + row["missed_milestone_pressure"] * 8
        + row["incident_pressure"] * 8
        + row["contract_value_pressure"] * 6
        + (1 - row["sponsor_engagement"]) * 5
    )


def _training_rows() -> list[dict[str, float]]:
    rng = np.random.default_rng(1904)
    rows: list[dict[str, float]] = []
    for _ in range(6400):
        pressure = rng.choice([0.16, 0.34, 0.58, 0.82], p=[0.26, 0.36, 0.25, 0.13])
        quality = rng.choice([0.86, 0.72, 0.58, 0.42], p=[0.26, 0.36, 0.25, 0.13])
        sentiment = float(np.clip(rng.normal(pressure, 0.16), 0, 1))
        row = {
            "delay_pressure": float(np.clip(rng.normal(pressure, 0.15), 0, 1)),
            "missed_milestone_pressure": float(np.clip(rng.normal(pressure * 0.9, 0.17), 0, 1)),
            "sla_pressure": float(np.clip(rng.normal(pressure * 0.86, 0.17), 0, 1)),
            "bug_pressure": float(np.clip(rng.normal(1 - quality, 0.14), 0, 1)),
            "incident_pressure": float(np.clip(rng.normal(pressure * 0.72, 0.16), 0, 1)),
            "qa_quality": float(np.clip(rng.normal(quality, 0.11), 0, 1)),
            "rework_ratio": float(np.clip(rng.normal(pressure * 0.62, 0.14), 0, 1)),
            "issue_resolution_pressure": float(np.clip(rng.normal(pressure, 0.17), 0, 1)),
            "escalation_pressure": float(np.clip(rng.normal(pressure * 0.92, 0.18), 0, 1)),
            "sentiment_negativity": sentiment,
            "interaction_decline": float(np.clip(rng.normal(pressure * 0.62, 0.16), 0, 1)),
            "feedback_risk": float(np.clip(rng.normal(pressure * 0.84, 0.16), 0, 1)),
            "nps_decline": float(np.clip(rng.normal(pressure * 0.72, 0.16), 0, 1)),
            "renewal_pressure": float(np.clip(rng.beta(2.3, 3.8), 0, 1)),
            "delivery_consistency": float(np.clip(rng.normal(quality, 0.13), 0, 1)),
            "sponsor_engagement": float(np.clip(rng.normal(1 - pressure * 0.45, 0.16), 0, 1)),
            "critical_issue_pressure": float(np.clip(rng.normal(pressure * 0.68, 0.18), 0, 1)),
            "contract_value_pressure": float(np.clip(rng.beta(2.0, 3.2), 0, 1)),
        }
        rows.append(row)
    return rows


def train_client_satisfaction_models() -> ClientSatisfactionMetrics:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    rows = _training_rows()
    features = np.array([[row[name] for name in FEATURE_NAMES] for row in rows], dtype=np.float32)
    health = np.array([_score_health(row) for row in rows], dtype=np.float32)
    churn = np.array([_score_churn(row) for row in rows], dtype=np.float32)
    escalation = np.array([_score_escalation(row) for row in rows], dtype=np.float32)
    train_x, test_x, train_health, test_health, train_churn, test_churn, train_escalation, test_escalation = train_test_split(
        features,
        health,
        churn,
        escalation,
        test_size=0.22,
        random_state=57,
    )
    health_model = RandomForestRegressor(n_estimators=260, max_depth=12, min_samples_leaf=3, random_state=57, n_jobs=-1)
    churn_model = GradientBoostingRegressor(random_state=58, max_depth=3, n_estimators=220)
    escalation_model = GradientBoostingRegressor(random_state=59, max_depth=3, n_estimators=220)
    health_model.fit(train_x, train_health)
    churn_model.fit(train_x, train_churn)
    escalation_model.fit(train_x, train_escalation)
    health_pred = health_model.predict(test_x)
    churn_pred = churn_model.predict(test_x)
    escalation_pred = escalation_model.predict(test_x)
    metrics = ClientSatisfactionMetrics(
        health_mae=round(float(mean_absolute_error(test_health, health_pred)), 3),
        health_r2=round(float(r2_score(test_health, health_pred)), 3),
        churn_mae=round(float(mean_absolute_error(test_churn, churn_pred)), 3),
        churn_r2=round(float(r2_score(test_churn, churn_pred)), 3),
        escalation_mae=round(float(mean_absolute_error(test_escalation, escalation_pred)), 3),
        escalation_r2=round(float(r2_score(test_escalation, escalation_pred)), 3),
        trained_samples=len(rows),
        model_family="RandomForest client health + GradientBoosting churn and escalation forecasters",
    )
    joblib.dump(health_model, HEALTH_MODEL_PATH)
    joblib.dump({"churn": churn_model, "escalation": escalation_model}, RISK_MODEL_PATH)
    METRICS_PATH.write_text(json.dumps(asdict(metrics), indent=2), encoding="utf-8")
    return metrics


class ClientSatisfactionEngine:
    model_name = "RandomForest Client Health + GradientBoosting Churn Risk Forecaster"

    def __init__(self) -> None:
        self._health_model: RandomForestRegressor | None = None
        self._churn_model: GradientBoostingRegressor | None = None
        self._escalation_model: GradientBoostingRegressor | None = None

    @property
    def available(self) -> bool:
        return HEALTH_MODEL_PATH.exists() and RISK_MODEL_PATH.exists() and METRICS_PATH.exists()

    def ensure_artifacts(self) -> None:
        if not self.available:
            train_client_satisfaction_models()

    def metrics(self) -> dict[str, object]:
        self.ensure_artifacts()
        return json.loads(METRICS_PATH.read_text(encoding="utf-8"))

    def _load(self) -> None:
        self.ensure_artifacts()
        if self._health_model is None:
            self._health_model = joblib.load(HEALTH_MODEL_PATH)
            bundle = joblib.load(RISK_MODEL_PATH)
            self._churn_model = bundle["churn"]
            self._escalation_model = bundle["escalation"]

    def predict(self, rows: list[dict[str, float]]) -> list[dict[str, float]]:
        self._load()
        assert self._health_model is not None
        assert self._churn_model is not None
        assert self._escalation_model is not None
        matrix = np.array([[float(row[name]) for name in FEATURE_NAMES] for row in rows], dtype=np.float32)
        health_ml = self._health_model.predict(matrix)
        churn_ml = self._churn_model.predict(matrix)
        escalation_ml = self._escalation_model.predict(matrix)
        predictions: list[dict[str, float]] = []
        for index, row in enumerate(rows):
            health_formula = _score_health(row)
            churn_formula = _score_churn(row)
            escalation_formula = _score_escalation(row)
            health = _clip(float(health_ml[index]) * 0.73 + health_formula * 0.27)
            churn = _clip(float(churn_ml[index]) * 0.73 + churn_formula * 0.27)
            escalation = _clip(float(escalation_ml[index]) * 0.73 + escalation_formula * 0.27)
            disagreement = abs(health - (100 - max(churn, escalation)))
            confidence = float(np.clip(0.93 - disagreement / 260 - row["sentiment_negativity"] * 0.04, 0.68, 0.94))
            predictions.append(
                {
                    "client_health_score": round(health, 3),
                    "churn_risk": round(churn, 3),
                    "escalation_probability": round(escalation, 3),
                    "confidence": round(confidence, 3),
                }
            )
        return predictions


client_satisfaction_engine = ClientSatisfactionEngine()
