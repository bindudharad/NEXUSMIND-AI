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
HEALTH_MODEL_PATH = ARTIFACT_DIR / "company_health_random_forest.joblib"
RISK_MODEL_PATH = ARTIFACT_DIR / "company_health_gradient_boost.joblib"
METRICS_PATH = ARTIFACT_DIR / "company_health_metrics.json"

FEATURE_NAMES = [
    "employee_happiness_score",
    "productivity_score",
    "burnout_risk",
    "attrition_risk",
    "project_health",
    "collaboration_quality",
    "delivery_stability",
    "resource_utilization",
    "innovation_score",
    "security_risk",
    "communication_health",
    "meeting_efficiency",
    "workforce_engagement",
    "open_project_risks",
    "active_incidents",
]


@dataclass(frozen=True)
class CompanyHealthModelMetrics:
    health_mae: float
    risk_mae: float
    health_r2: float
    risk_r2: float
    trained_samples: int
    model_family: str


def _clip100(value: float) -> float:
    return float(np.clip(value, 0, 100))


def _score_health(row: dict[str, float]) -> float:
    utilization_stability = _clip100(100 - abs(row["resource_utilization"] - 82) * 1.35)
    operating_quality = (
        row["employee_happiness_score"] * 0.1
        + row["productivity_score"] * 0.12
        + row["project_health"] * 0.12
        + row["collaboration_quality"] * 0.09
        + row["delivery_stability"] * 0.12
        + row["innovation_score"] * 0.05
        + row["communication_health"] * 0.08
        + row["meeting_efficiency"] * 0.05
        + row["workforce_engagement"] * 0.1
        + (100 - row["burnout_risk"]) * 0.08
        + (100 - row["attrition_risk"]) * 0.08
        + (100 - row["security_risk"]) * 0.05
        + utilization_stability * 0.04
    )
    incident_penalty = row["open_project_risks"] * 0.8 + row["active_incidents"] * 2.2
    return _clip100(operating_quality - incident_penalty)


def _score_risk(row: dict[str, float]) -> float:
    utilization_pressure = max(0, row["resource_utilization"] - 88) * 1.55
    return _clip100(
        row["burnout_risk"] * 0.18
        + row["attrition_risk"] * 0.18
        + (100 - row["project_health"]) * 0.12
        + (100 - row["delivery_stability"]) * 0.12
        + (100 - row["communication_health"]) * 0.08
        + (100 - row["workforce_engagement"]) * 0.08
        + row["security_risk"] * 0.09
        + utilization_pressure
        + row["open_project_risks"] * 1.7
        + row["active_incidents"] * 3.1
    )


def _training_rows() -> list[dict[str, float]]:
    rng = np.random.default_rng(2026)
    regimes = [
        {"count": 140, "positive": 86, "risk": 18, "utilization": 80, "risks": 2, "incidents": 0},
        {"count": 140, "positive": 72, "risk": 36, "utilization": 86, "risks": 5, "incidents": 1},
        {"count": 140, "positive": 58, "risk": 58, "utilization": 94, "risks": 10, "incidents": 3},
        {"count": 100, "positive": 42, "risk": 78, "utilization": 104, "risks": 18, "incidents": 6},
    ]
    rows: list[dict[str, float]] = []
    positive_features = [
        "employee_happiness_score",
        "productivity_score",
        "project_health",
        "collaboration_quality",
        "delivery_stability",
        "innovation_score",
        "communication_health",
        "meeting_efficiency",
        "workforce_engagement",
    ]
    risk_features = ["burnout_risk", "attrition_risk", "security_risk"]
    for regime in regimes:
        for _ in range(int(regime["count"])):
            row: dict[str, float] = {}
            for feature in positive_features:
                row[feature] = _clip100(float(rng.normal(float(regime["positive"]), 9.5)))
            for feature in risk_features:
                row[feature] = _clip100(float(rng.normal(float(regime["risk"]), 10.5)))
            row["resource_utilization"] = float(np.clip(rng.normal(float(regime["utilization"]), 8.5), 25, 130))
            row["open_project_risks"] = float(np.clip(round(rng.normal(float(regime["risks"]), 2.6)), 0, 120))
            row["active_incidents"] = float(np.clip(round(rng.normal(float(regime["incidents"]), 1.5)), 0, 80))
            rows.append(row)
    return rows


def train_company_health_models() -> CompanyHealthModelMetrics:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    rows = _training_rows()
    features = np.array([[row[name] for name in FEATURE_NAMES] for row in rows], dtype=float)
    health = np.array([_score_health(row) for row in rows], dtype=float)
    risk = np.array([_score_risk(row) for row in rows], dtype=float)
    train_x, test_x, train_health, test_health, train_risk, test_risk = train_test_split(
        features,
        health,
        risk,
        test_size=0.22,
        random_state=42,
    )
    health_model = RandomForestRegressor(n_estimators=180, max_depth=10, random_state=42)
    risk_model = GradientBoostingRegressor(random_state=19, max_depth=3, n_estimators=190)
    health_model.fit(train_x, train_health)
    risk_model.fit(train_x, train_risk)
    health_pred = health_model.predict(test_x)
    risk_pred = risk_model.predict(test_x)
    metrics = CompanyHealthModelMetrics(
        health_mae=round(float(mean_absolute_error(test_health, health_pred)), 3),
        risk_mae=round(float(mean_absolute_error(test_risk, risk_pred)), 3),
        health_r2=round(float(r2_score(test_health, health_pred)), 3),
        risk_r2=round(float(r2_score(test_risk, risk_pred)), 3),
        trained_samples=len(rows),
        model_family="RandomForestRegressor company health + GradientBoostingRegressor enterprise risk",
    )
    joblib.dump(health_model, HEALTH_MODEL_PATH)
    joblib.dump(risk_model, RISK_MODEL_PATH)
    METRICS_PATH.write_text(json.dumps(asdict(metrics), indent=2), encoding="utf-8")
    return metrics


class CompanyHealthEngine:
    model_name = "RandomForest Company Health + GradientBoosting KPI Forecast Engine"

    def __init__(self) -> None:
        self._health_model: RandomForestRegressor | None = None
        self._risk_model: GradientBoostingRegressor | None = None

    @property
    def available(self) -> bool:
        return HEALTH_MODEL_PATH.exists() and RISK_MODEL_PATH.exists() and METRICS_PATH.exists()

    def ensure_artifacts(self) -> None:
        if not self.available:
            train_company_health_models()

    def metrics(self) -> dict[str, object]:
        self.ensure_artifacts()
        return json.loads(METRICS_PATH.read_text(encoding="utf-8"))

    def _load(self) -> None:
        self.ensure_artifacts()
        if self._health_model is None:
            self._health_model = joblib.load(HEALTH_MODEL_PATH)
            self._risk_model = joblib.load(RISK_MODEL_PATH)

    def predict(self, features: dict[str, float]) -> dict[str, float]:
        self._load()
        assert self._health_model is not None
        assert self._risk_model is not None
        vector = np.array([[float(features[name]) for name in FEATURE_NAMES]], dtype=float)
        formula_health = _score_health(features)
        formula_risk = _score_risk(features)
        ml_health = float(self._health_model.predict(vector)[0])
        ml_risk = float(self._risk_model.predict(vector)[0])
        health = _clip100(ml_health * 0.72 + formula_health * 0.28)
        risk = _clip100(ml_risk * 0.72 + formula_risk * 0.28)
        disagreement = abs(health - (100 - risk))
        confidence = float(np.clip(0.91 - disagreement / 280, 0.68, 0.94))
        return {
            "health_score": round(health, 3),
            "risk_score": round(risk, 3),
            "confidence": round(confidence, 3),
            "formula_health": round(formula_health, 3),
            "formula_risk": round(formula_risk, 3),
        }


company_health_engine = CompanyHealthEngine()
