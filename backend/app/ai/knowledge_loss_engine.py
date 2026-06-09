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
LOSS_MODEL_PATH = ARTIFACT_DIR / "knowledge_loss_random_forest.joblib"
RISK_MODEL_PATH = ARTIFACT_DIR / "knowledge_loss_gradient_boost.joblib"
METRICS_PATH = ARTIFACT_DIR / "knowledge_loss_metrics.json"

FEATURE_NAMES = [
    "expertise_depth",
    "criticality",
    "attrition_risk",
    "documentation_gap",
    "redundancy_gap",
    "recency_pressure",
    "incident_ownership",
    "commit_ownership",
    "meeting_dependency",
    "handoff_gap",
    "seniority",
    "business_criticality",
]


@dataclass(frozen=True)
class KnowledgeLossMetrics:
    loss_mae: float
    loss_r2: float
    disruption_mae: float
    disruption_r2: float
    transfer_mae: float
    transfer_r2: float
    trained_samples: int
    model_family: str


def _clip(value: float, lower: float = 0, upper: float = 100) -> float:
    return float(np.clip(value, lower, upper))


def _score_loss(row: dict[str, float]) -> float:
    return _clip(
        row["criticality"] * 18
        + row["attrition_risk"] * 18
        + row["documentation_gap"] * 15
        + row["redundancy_gap"] * 16
        + row["recency_pressure"] * 6
        + row["incident_ownership"] * 8
        + row["meeting_dependency"] * 5
        + row["handoff_gap"] * 12
        + row["business_criticality"] * 10
        + row["expertise_depth"] * row["redundancy_gap"] * 10
    )


def _score_disruption(row: dict[str, float]) -> float:
    return _clip(
        row["criticality"] * 18
        + row["business_criticality"] * 16
        + row["incident_ownership"] * 13
        + row["commit_ownership"] * 7
        + row["documentation_gap"] * 12
        + row["redundancy_gap"] * 14
        + row["attrition_risk"] * 10
        + row["handoff_gap"] * 10
    )


def _score_transfer(row: dict[str, float]) -> float:
    return _clip(
        (1 - row["documentation_gap"]) * 24
        + (1 - row["handoff_gap"]) * 20
        + (1 - row["recency_pressure"]) * 9
        + (1 - row["redundancy_gap"]) * 14
        + row["expertise_depth"] * 11
        + row["seniority"] * 8
        + (1 - row["attrition_risk"]) * 8
    )


def _training_rows() -> list[dict[str, float]]:
    rng = np.random.default_rng(2206)
    rows: list[dict[str, float]] = []
    for _ in range(6200):
        criticality = rng.choice([0.22, 0.42, 0.66, 0.88], p=[0.18, 0.32, 0.32, 0.18])
        documentation = rng.choice([0.28, 0.48, 0.7, 0.88], p=[0.2, 0.32, 0.32, 0.16])
        redundancy = rng.choice([0.05, 0.28, 0.58, 0.86], p=[0.24, 0.32, 0.28, 0.16])
        ownership = float(np.clip(rng.normal(criticality, 0.16), 0, 1))
        row = {
            "expertise_depth": float(np.clip(rng.normal(0.48 + ownership * 0.45, 0.14), 0, 1)),
            "criticality": float(np.clip(rng.normal(criticality, 0.12), 0, 1)),
            "attrition_risk": float(np.clip(rng.beta(2.2, 4.0) + criticality * 0.08, 0, 1)),
            "documentation_gap": float(np.clip(1 - documentation + rng.normal(0, 0.08), 0, 1)),
            "redundancy_gap": float(np.clip(1 - redundancy + rng.normal(0, 0.08), 0, 1)),
            "recency_pressure": float(np.clip(rng.beta(2.0, 4.2) + (1 - documentation) * 0.14, 0, 1)),
            "incident_ownership": float(np.clip(rng.normal(ownership, 0.16), 0, 1)),
            "commit_ownership": float(np.clip(rng.normal(ownership * 0.82, 0.16), 0, 1)),
            "meeting_dependency": float(np.clip(rng.normal(ownership * 0.62, 0.16), 0, 1)),
            "handoff_gap": float(np.clip(1 - documentation * 0.65 - redundancy * 0.25 + rng.normal(0, 0.08), 0, 1)),
            "seniority": float(np.clip(rng.normal(0.5 + ownership * 0.38, 0.14), 0, 1)),
            "business_criticality": float(np.clip(rng.normal(criticality, 0.13), 0, 1)),
        }
        rows.append(row)
    return rows


def train_knowledge_loss_models() -> KnowledgeLossMetrics:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    rows = _training_rows()
    features = np.array([[row[name] for name in FEATURE_NAMES] for row in rows], dtype=np.float32)
    loss = np.array([_score_loss(row) for row in rows], dtype=np.float32)
    disruption = np.array([_score_disruption(row) for row in rows], dtype=np.float32)
    transfer = np.array([_score_transfer(row) for row in rows], dtype=np.float32)
    train_x, test_x, train_loss, test_loss, train_disruption, test_disruption, train_transfer, test_transfer = train_test_split(
        features,
        loss,
        disruption,
        transfer,
        test_size=0.22,
        random_state=81,
    )
    loss_model = RandomForestRegressor(n_estimators=240, max_depth=12, min_samples_leaf=3, random_state=81, n_jobs=-1)
    disruption_model = GradientBoostingRegressor(random_state=82, max_depth=3, n_estimators=210)
    transfer_model = GradientBoostingRegressor(random_state=83, max_depth=3, n_estimators=210)
    loss_model.fit(train_x, train_loss)
    disruption_model.fit(train_x, train_disruption)
    transfer_model.fit(train_x, train_transfer)
    loss_pred = loss_model.predict(test_x)
    disruption_pred = disruption_model.predict(test_x)
    transfer_pred = transfer_model.predict(test_x)
    metrics = KnowledgeLossMetrics(
        loss_mae=round(float(mean_absolute_error(test_loss, loss_pred)), 3),
        loss_r2=round(float(r2_score(test_loss, loss_pred)), 3),
        disruption_mae=round(float(mean_absolute_error(test_disruption, disruption_pred)), 3),
        disruption_r2=round(float(r2_score(test_disruption, disruption_pred)), 3),
        transfer_mae=round(float(mean_absolute_error(test_transfer, transfer_pred)), 3),
        transfer_r2=round(float(r2_score(test_transfer, transfer_pred)), 3),
        trained_samples=len(rows),
        model_family="RandomForest knowledge-loss + GradientBoosting disruption and transfer forecasters",
    )
    joblib.dump(loss_model, LOSS_MODEL_PATH)
    joblib.dump({"disruption": disruption_model, "transfer": transfer_model}, RISK_MODEL_PATH)
    METRICS_PATH.write_text(json.dumps(asdict(metrics), indent=2), encoding="utf-8")
    return metrics


class KnowledgeLossEngine:
    model_name = "TF-IDF Knowledge Graph + RandomForest Knowledge Loss Forecaster"

    def __init__(self) -> None:
        self._loss_model: RandomForestRegressor | None = None
        self._disruption_model: GradientBoostingRegressor | None = None
        self._transfer_model: GradientBoostingRegressor | None = None

    @property
    def available(self) -> bool:
        return LOSS_MODEL_PATH.exists() and RISK_MODEL_PATH.exists() and METRICS_PATH.exists()

    def ensure_artifacts(self) -> None:
        if not self.available:
            train_knowledge_loss_models()

    def metrics(self) -> dict[str, object]:
        self.ensure_artifacts()
        return json.loads(METRICS_PATH.read_text(encoding="utf-8"))

    def _load(self) -> None:
        self.ensure_artifacts()
        if self._loss_model is None:
            self._loss_model = joblib.load(LOSS_MODEL_PATH)
            bundle = joblib.load(RISK_MODEL_PATH)
            self._disruption_model = bundle["disruption"]
            self._transfer_model = bundle["transfer"]

    def predict(self, rows: list[dict[str, float]]) -> list[dict[str, float]]:
        self._load()
        assert self._loss_model is not None
        assert self._disruption_model is not None
        assert self._transfer_model is not None
        matrix = np.array([[float(row[name]) for name in FEATURE_NAMES] for row in rows], dtype=np.float32)
        loss_ml = self._loss_model.predict(matrix)
        disruption_ml = self._disruption_model.predict(matrix)
        transfer_ml = self._transfer_model.predict(matrix)
        predictions: list[dict[str, float]] = []
        for index, row in enumerate(rows):
            loss_formula = _score_loss(row)
            disruption_formula = _score_disruption(row)
            transfer_formula = _score_transfer(row)
            loss = _clip(float(loss_ml[index]) * 0.72 + loss_formula * 0.28)
            disruption = _clip(float(disruption_ml[index]) * 0.72 + disruption_formula * 0.28)
            transfer = _clip(float(transfer_ml[index]) * 0.72 + transfer_formula * 0.28)
            volatility = abs(loss - disruption) + abs(transfer - (100 - row["handoff_gap"] * 100)) * 0.25
            confidence = float(np.clip(0.94 - volatility / 310 - row["recency_pressure"] * 0.03, 0.7, 0.95))
            predictions.append(
                {
                    "knowledge_loss_probability": round(loss, 3),
                    "operational_disruption_risk": round(disruption, 3),
                    "transfer_completion_probability": round(transfer, 3),
                    "confidence": round(confidence, 3),
                }
            )
        return predictions


knowledge_loss_engine = KnowledgeLossEngine()
