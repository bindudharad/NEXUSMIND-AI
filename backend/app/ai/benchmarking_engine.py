from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import joblib
import numpy as np
from sklearn.cluster import KMeans
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"
BENCHMARK_MODEL_PATH = ARTIFACT_DIR / "benchmarking_random_forest.joblib"
MATURITY_MODEL_PATH = ARTIFACT_DIR / "benchmarking_gradient_boost.joblib"
CLUSTER_MODEL_PATH = ARTIFACT_DIR / "benchmarking_cluster_bundle.joblib"
METRICS_PATH = ARTIFACT_DIR / "benchmarking_metrics.json"

FEATURE_NAMES = [
    "productivity_score",
    "burnout_inverse",
    "retention_rate",
    "team_efficiency",
    "delivery_stability",
    "workforce_happiness",
    "innovation_output",
    "collaboration_quality",
    "project_success_rate",
    "communication_health",
    "learning_growth",
    "operational_stability",
    "sprint_velocity",
    "overtime_inverse",
    "incident_inverse",
    "ai_adoption",
    "size_index",
]


@dataclass(frozen=True)
class BenchmarkingMetrics:
    benchmark_mae: float
    benchmark_r2: float
    maturity_mae: float
    maturity_r2: float
    stability_risk_mae: float
    stability_risk_r2: float
    trained_samples: int
    cluster_count: int
    model_family: str


def _clip(value: float, lower: float = 0, upper: float = 100) -> float:
    return float(np.clip(value, lower, upper))


def _score_benchmark(row: dict[str, float]) -> float:
    performance = (
        row["productivity_score"] * 15
        + row["retention_rate"] * 12
        + row["team_efficiency"] * 9
        + row["delivery_stability"] * 11
        + row["workforce_happiness"] * 9
        + row["innovation_output"] * 9
        + row["collaboration_quality"] * 9
        + row["project_success_rate"] * 10
        + row["communication_health"] * 7
        + row["learning_growth"] * 6
        + row["operational_stability"] * 12
        + row["sprint_velocity"] * 5
        + row["ai_adoption"] * 5
    )
    pressure = (
        (1 - row["burnout_inverse"]) * 11
        + (1 - row["overtime_inverse"]) * 6
        + (1 - row["incident_inverse"]) * 7
        + max(0, 0.55 - row["retention_rate"]) * 10
    )
    return _clip(performance - pressure)


def _score_maturity(row: dict[str, float]) -> float:
    return _clip(
        row["operational_stability"] * 18
        + row["delivery_stability"] * 14
        + row["project_success_rate"] * 12
        + row["collaboration_quality"] * 10
        + row["communication_health"] * 9
        + row["learning_growth"] * 8
        + row["innovation_output"] * 8
        + row["ai_adoption"] * 9
        + row["team_efficiency"] * 8
        + row["retention_rate"] * 8
        + row["size_index"] * 4
        - (1 - row["incident_inverse"]) * 7
        - (1 - row["burnout_inverse"]) * 5
    )


def _score_stability_risk(row: dict[str, float]) -> float:
    return _clip(
        (1 - row["delivery_stability"]) * 17
        + (1 - row["retention_rate"]) * 15
        + (1 - row["operational_stability"]) * 14
        + (1 - row["project_success_rate"]) * 12
        + (1 - row["communication_health"]) * 8
        + (1 - row["collaboration_quality"]) * 8
        + (1 - row["burnout_inverse"]) * 16
        + (1 - row["overtime_inverse"]) * 7
        + (1 - row["incident_inverse"]) * 10
    )


def _training_rows() -> list[dict[str, float]]:
    rng = np.random.default_rng(2718)
    rows: list[dict[str, float]] = []
    for _ in range(7200):
        maturity = rng.choice([0.34, 0.52, 0.69, 0.84], p=[0.16, 0.34, 0.34, 0.16])
        pressure = rng.choice([0.18, 0.34, 0.52, 0.74], p=[0.26, 0.38, 0.26, 0.1])
        innovation = float(np.clip(rng.normal(maturity * 0.86 + 0.08, 0.14), 0, 1))
        row = {
            "productivity_score": float(np.clip(rng.normal(maturity, 0.13), 0, 1)),
            "burnout_inverse": float(np.clip(1 - rng.normal(pressure, 0.15), 0, 1)),
            "retention_rate": float(np.clip(rng.normal(1 - pressure * 0.42, 0.12), 0, 1)),
            "team_efficiency": float(np.clip(rng.normal(maturity * 0.9 + 0.05, 0.13), 0, 1)),
            "delivery_stability": float(np.clip(rng.normal(maturity * 0.88 + 0.07, 0.14), 0, 1)),
            "workforce_happiness": float(np.clip(rng.normal(1 - pressure * 0.5, 0.15), 0, 1)),
            "innovation_output": innovation,
            "collaboration_quality": float(np.clip(rng.normal(maturity * 0.82 + 0.1, 0.14), 0, 1)),
            "project_success_rate": float(np.clip(rng.normal(maturity * 0.9 + 0.05, 0.13), 0, 1)),
            "communication_health": float(np.clip(rng.normal(maturity * 0.78 + 0.12, 0.15), 0, 1)),
            "learning_growth": float(np.clip(rng.normal(innovation * 0.7 + maturity * 0.25, 0.13), 0, 1)),
            "operational_stability": float(np.clip(rng.normal(maturity, 0.12), 0, 1)),
            "sprint_velocity": float(np.clip(rng.normal(maturity * 0.86 + 0.06, 0.15), 0, 1)),
            "overtime_inverse": float(np.clip(1 - rng.normal(pressure * 0.88, 0.16), 0, 1)),
            "incident_inverse": float(np.clip(1 - rng.normal((1 - maturity) * 0.58, 0.17), 0, 1)),
            "ai_adoption": float(np.clip(rng.normal(maturity * 0.66 + innovation * 0.24, 0.16), 0, 1)),
            "size_index": float(np.clip(rng.beta(2.2, 3.4), 0, 1)),
        }
        rows.append(row)
    return rows


def train_benchmarking_models() -> BenchmarkingMetrics:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    rows = _training_rows()
    features = np.array([[row[name] for name in FEATURE_NAMES] for row in rows], dtype=np.float32)
    benchmark = np.array([_score_benchmark(row) for row in rows], dtype=np.float32)
    maturity = np.array([_score_maturity(row) for row in rows], dtype=np.float32)
    stability = np.array([_score_stability_risk(row) for row in rows], dtype=np.float32)
    train_x, test_x, train_benchmark, test_benchmark, train_maturity, test_maturity, train_stability, test_stability = train_test_split(
        features,
        benchmark,
        maturity,
        stability,
        test_size=0.22,
        random_state=91,
    )
    benchmark_model = RandomForestRegressor(n_estimators=280, max_depth=12, min_samples_leaf=4, random_state=91, n_jobs=-1)
    maturity_model = GradientBoostingRegressor(random_state=92, max_depth=3, n_estimators=240)
    stability_model = GradientBoostingRegressor(random_state=93, max_depth=3, n_estimators=240)
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features)
    cluster_model = KMeans(n_clusters=6, n_init=15, random_state=94)
    cluster_model.fit(scaled_features)
    benchmark_model.fit(train_x, train_benchmark)
    maturity_model.fit(train_x, train_maturity)
    stability_model.fit(train_x, train_stability)
    benchmark_pred = benchmark_model.predict(test_x)
    maturity_pred = maturity_model.predict(test_x)
    stability_pred = stability_model.predict(test_x)
    metrics = BenchmarkingMetrics(
        benchmark_mae=round(float(mean_absolute_error(test_benchmark, benchmark_pred)), 3),
        benchmark_r2=round(float(r2_score(test_benchmark, benchmark_pred)), 3),
        maturity_mae=round(float(mean_absolute_error(test_maturity, maturity_pred)), 3),
        maturity_r2=round(float(r2_score(test_maturity, maturity_pred)), 3),
        stability_risk_mae=round(float(mean_absolute_error(test_stability, stability_pred)), 3),
        stability_risk_r2=round(float(r2_score(test_stability, stability_pred)), 3),
        trained_samples=len(rows),
        cluster_count=6,
        model_family="RandomForest benchmark scoring + GradientBoosting maturity/stability + KMeans cohort clustering",
    )
    joblib.dump(benchmark_model, BENCHMARK_MODEL_PATH)
    joblib.dump({"maturity": maturity_model, "stability": stability_model}, MATURITY_MODEL_PATH)
    joblib.dump({"scaler": scaler, "clusters": cluster_model}, CLUSTER_MODEL_PATH)
    METRICS_PATH.write_text(json.dumps(asdict(metrics), indent=2), encoding="utf-8")
    return metrics


class BenchmarkingEngine:
    model_name = "RandomForest Benchmark Intelligence + KMeans Anonymous Cohort Forecaster"

    def __init__(self) -> None:
        self._benchmark_model: RandomForestRegressor | None = None
        self._maturity_model: GradientBoostingRegressor | None = None
        self._stability_model: GradientBoostingRegressor | None = None
        self._scaler: StandardScaler | None = None
        self._cluster_model: KMeans | None = None

    @property
    def available(self) -> bool:
        return BENCHMARK_MODEL_PATH.exists() and MATURITY_MODEL_PATH.exists() and CLUSTER_MODEL_PATH.exists() and METRICS_PATH.exists()

    def ensure_artifacts(self) -> None:
        if not self.available:
            train_benchmarking_models()

    def metrics(self) -> dict[str, object]:
        self.ensure_artifacts()
        return json.loads(METRICS_PATH.read_text(encoding="utf-8"))

    def _load(self) -> None:
        self.ensure_artifacts()
        if self._benchmark_model is None:
            self._benchmark_model = joblib.load(BENCHMARK_MODEL_PATH)
            bundle = joblib.load(MATURITY_MODEL_PATH)
            self._maturity_model = bundle["maturity"]
            self._stability_model = bundle["stability"]
            cluster_bundle = joblib.load(CLUSTER_MODEL_PATH)
            self._scaler = cluster_bundle["scaler"]
            self._cluster_model = cluster_bundle["clusters"]

    def predict(self, rows: list[dict[str, float]]) -> list[dict[str, float]]:
        self._load()
        assert self._benchmark_model is not None
        assert self._maturity_model is not None
        assert self._stability_model is not None
        assert self._scaler is not None
        assert self._cluster_model is not None
        matrix = np.array([[float(row[name]) for name in FEATURE_NAMES] for row in rows], dtype=np.float32)
        benchmark_ml = self._benchmark_model.predict(matrix)
        maturity_ml = self._maturity_model.predict(matrix)
        stability_ml = self._stability_model.predict(matrix)
        clusters = self._cluster_model.predict(self._scaler.transform(matrix))
        predictions: list[dict[str, float]] = []
        for index, row in enumerate(rows):
            benchmark_formula = _score_benchmark(row)
            maturity_formula = _score_maturity(row)
            stability_formula = _score_stability_risk(row)
            benchmark = _clip(float(benchmark_ml[index]) * 0.72 + benchmark_formula * 0.28)
            maturity = _clip(float(maturity_ml[index]) * 0.72 + maturity_formula * 0.28)
            stability = _clip(float(stability_ml[index]) * 0.72 + stability_formula * 0.28)
            disagreement = abs(benchmark - benchmark_formula) + abs(maturity - maturity_formula) + abs(stability - stability_formula)
            confidence = float(np.clip(0.94 - disagreement / 360 - (1 - row["size_index"]) * 0.025, 0.7, 0.95))
            predictions.append(
                {
                    "benchmark_score": round(benchmark, 3),
                    "maturity_score": round(maturity, 3),
                    "stability_risk": round(stability, 3),
                    "cluster": float(clusters[index]),
                    "confidence": round(confidence, 3),
                }
            )
        return predictions


benchmarking_engine = BenchmarkingEngine()
