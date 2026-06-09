from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, mean_absolute_error
from sklearn.model_selection import train_test_split


ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"
INNOVATION_VECTOR_PATH = ARTIFACT_DIR / "innovation_tfidf_vectorizer.joblib"
CATEGORY_MODEL_PATH = ARTIFACT_DIR / "innovation_category_classifier.joblib"
ORIGINALITY_MODEL_PATH = ARTIFACT_DIR / "innovation_originality_regressor.joblib"
IMPACT_MODEL_PATH = ARTIFACT_DIR / "innovation_impact_regressor.joblib"
ADOPTION_MODEL_PATH = ARTIFACT_DIR / "innovation_adoption_regressor.joblib"
METRICS_PATH = ARTIFACT_DIR / "innovation_scoring_metrics.json"


@dataclass(frozen=True)
class InnovationModelMetrics:
    category_accuracy: float
    originality_mae: float
    impact_mae: float
    adoption_mae: float
    trained_samples: int
    model_family: str


def _training_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    groups = {
        "architecture": [
            ("Create an event-driven service mesh to reduce API coupling and improve deployment resilience.", 0.86, 0.84, 0.72),
            ("Move critical workloads to a shared platform layer with typed contracts and automated rollback.", 0.78, 0.8, 0.68),
            ("Use graph-based dependency analysis to predict release bottlenecks before sprint planning.", 0.9, 0.83, 0.65),
        ],
        "automation": [
            ("Automate regression triage with AI summaries so QA can focus on high-risk scenarios.", 0.72, 0.76, 0.8),
            ("Build a deployment optimizer that batches low-risk changes and flags risky diffs.", 0.8, 0.82, 0.74),
            ("Introduce self-healing runbooks that restore known incident states without manual paging.", 0.84, 0.79, 0.7),
        ],
        "product": [
            ("Add a customer-facing insight panel that explains why productivity risks are increasing.", 0.76, 0.86, 0.7),
            ("Launch a manager copilot that converts workforce signals into weekly intervention plans.", 0.82, 0.88, 0.76),
            ("Package attrition and wellness intelligence into a board-ready executive report generator.", 0.7, 0.78, 0.82),
        ],
        "research": [
            ("Prototype a causal impact model that links meeting overload to delivery risk and burnout.", 0.92, 0.81, 0.58),
            ("Run vector retrieval over postmortems to discover recurring failure patterns and novel mitigations.", 0.88, 0.83, 0.64),
            ("Experiment with multi-agent critique loops to improve risk forecast explanations.", 0.9, 0.77, 0.55),
        ],
        "process": [
            ("Create a decision log template to reduce repeated review discussions and clarify owners.", 0.5, 0.58, 0.86),
            ("Rotate facilitation roles during sprint planning to increase cross-team participation.", 0.46, 0.52, 0.75),
            ("Add lightweight retrospectives after incidents so follow-up actions do not disappear.", 0.48, 0.6, 0.82),
        ],
        "low_signal": [
            ("We should have more meetings to discuss ideas later.", 0.18, 0.16, 0.2),
            ("Maybe update the dashboard color and rename a few labels.", 0.16, 0.14, 0.28),
            ("Someone should improve the process when they have time.", 0.12, 0.1, 0.16),
        ],
    }
    for category, samples in groups.items():
        for text, originality, impact, adoption in samples:
            variants = [
                text,
                f"{text} Proposed during engineering planning with sponsor feedback.",
                f"{text} The idea includes implementation notes, measurable impact, and cross-team adoption path.",
                f"{text} It could improve delivery speed, reduce cost, and create reusable company knowledge.",
            ]
            for index, variant in enumerate(variants):
                rows.append(
                    {
                        "text": variant,
                        "category": category,
                        "originality": min(1.0, originality + index * 0.015),
                        "impact": min(1.0, impact + index * 0.02),
                        "adoption": min(1.0, adoption + index * 0.018),
                    }
                )
    return rows


def train_innovation_models() -> InnovationModelMetrics:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    rows = _training_rows()
    texts = [str(row["text"]) for row in rows]
    categories = np.array([str(row["category"]) for row in rows])
    originality = np.array([float(row["originality"]) for row in rows])
    impact = np.array([float(row["impact"]) for row in rows])
    adoption = np.array([float(row["adoption"]) for row in rows])

    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_features=1200)
    features = vectorizer.fit_transform(texts)
    indices = np.arange(len(texts))
    train_idx, test_idx = train_test_split(indices, test_size=0.25, random_state=42, stratify=categories)

    category_model = LogisticRegression(max_iter=700, class_weight="balanced", random_state=42)
    category_model.fit(features[train_idx], categories[train_idx])
    originality_model = RandomForestRegressor(n_estimators=160, max_depth=9, random_state=42)
    originality_model.fit(features[train_idx], originality[train_idx])
    impact_model = GradientBoostingRegressor(random_state=42, max_depth=3)
    impact_model.fit(features[train_idx], impact[train_idx])
    adoption_model = RandomForestRegressor(n_estimators=140, max_depth=8, random_state=7)
    adoption_model.fit(features[train_idx], adoption[train_idx])

    metrics = InnovationModelMetrics(
        category_accuracy=round(float(accuracy_score(categories[test_idx], category_model.predict(features[test_idx]))), 3),
        originality_mae=round(float(mean_absolute_error(originality[test_idx], originality_model.predict(features[test_idx]))), 3),
        impact_mae=round(float(mean_absolute_error(impact[test_idx], impact_model.predict(features[test_idx]))), 3),
        adoption_mae=round(float(mean_absolute_error(adoption[test_idx], adoption_model.predict(features[test_idx]))), 3),
        trained_samples=len(rows),
        model_family="TF-IDF + LogisticRegression + RandomForest + GradientBoosting",
    )
    joblib.dump(vectorizer, INNOVATION_VECTOR_PATH)
    joblib.dump(category_model, CATEGORY_MODEL_PATH)
    joblib.dump(originality_model, ORIGINALITY_MODEL_PATH)
    joblib.dump(impact_model, IMPACT_MODEL_PATH)
    joblib.dump(adoption_model, ADOPTION_MODEL_PATH)
    METRICS_PATH.write_text(json.dumps(asdict(metrics), indent=2), encoding="utf-8")
    return metrics


class InnovationScoringEngine:
    model_name = "PyTorch TextEmotionNet + TF-IDF Innovation Impact Ensemble"

    def __init__(self) -> None:
        self._vectorizer: TfidfVectorizer | None = None
        self._category_model: LogisticRegression | None = None
        self._originality_model: RandomForestRegressor | None = None
        self._impact_model: GradientBoostingRegressor | None = None
        self._adoption_model: RandomForestRegressor | None = None

    @property
    def available(self) -> bool:
        return all(
            path.exists()
            for path in [
                INNOVATION_VECTOR_PATH,
                CATEGORY_MODEL_PATH,
                ORIGINALITY_MODEL_PATH,
                IMPACT_MODEL_PATH,
                ADOPTION_MODEL_PATH,
                METRICS_PATH,
            ]
        )

    def ensure_artifacts(self) -> None:
        if not self.available:
            train_innovation_models()

    def metrics(self) -> dict[str, object]:
        self.ensure_artifacts()
        return json.loads(METRICS_PATH.read_text(encoding="utf-8"))

    def _load(self) -> None:
        self.ensure_artifacts()
        if self._vectorizer is None:
            self._vectorizer = joblib.load(INNOVATION_VECTOR_PATH)
            self._category_model = joblib.load(CATEGORY_MODEL_PATH)
            self._originality_model = joblib.load(ORIGINALITY_MODEL_PATH)
            self._impact_model = joblib.load(IMPACT_MODEL_PATH)
            self._adoption_model = joblib.load(ADOPTION_MODEL_PATH)

    def predict_text(self, text: str) -> dict[str, object]:
        self._load()
        assert self._vectorizer is not None
        assert self._category_model is not None
        assert self._originality_model is not None
        assert self._impact_model is not None
        assert self._adoption_model is not None
        features = self._vectorizer.transform([text])
        probabilities = self._category_model.predict_proba(features)[0]
        category_index = int(np.argmax(probabilities))
        category = str(self._category_model.classes_[category_index])
        category_confidence = float(probabilities[category_index])
        originality = float(np.clip(self._originality_model.predict(features)[0], 0, 1))
        impact = float(np.clip(self._impact_model.predict(features)[0], 0, 1))
        adoption = float(np.clip(self._adoption_model.predict(features)[0], 0, 1))
        confidence = float(np.clip(0.44 + category_confidence * 0.22 + max(originality, impact, adoption) * 0.32, 0.5, 0.96))
        return {
            "category": category,
            "category_confidence": round(category_confidence, 4),
            "originality_probability": round(originality, 4),
            "impact_probability": round(impact, 4),
            "adoption_probability": round(adoption, 4),
            "confidence": round(confidence, 4),
        }


innovation_scoring_engine = InnovationScoringEngine()
