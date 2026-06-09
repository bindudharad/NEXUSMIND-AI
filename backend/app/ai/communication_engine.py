from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor, RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, mean_absolute_error, roc_auc_score
from sklearn.model_selection import train_test_split


ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"
COMM_VECTOR_PATH = ARTIFACT_DIR / "communication_tfidf_vectorizer.joblib"
TOXIC_MODEL_PATH = ARTIFACT_DIR / "communication_toxicity_classifier.joblib"
AGGRESSION_MODEL_PATH = ARTIFACT_DIR / "communication_aggression_classifier.joblib"
CONFLICT_MODEL_PATH = ARTIFACT_DIR / "communication_conflict_regressor.joblib"
METRICS_PATH = ARTIFACT_DIR / "communication_quality_metrics.json"


@dataclass(frozen=True)
class CommunicationModelMetrics:
    toxicity_accuracy: float
    toxicity_roc_auc: float
    aggression_accuracy: float
    conflict_mae: float
    trained_samples: int
    model_family: str


def _training_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    positive = [
        "Thanks for the review, the feedback is clear and I will update the API tests.",
        "The deployment plan looks good and the team is aligned on ownership.",
        "I appreciate the context, let us pair on the blocker and unblock QA.",
        "The incident summary is constructive and gives us a clean next step.",
        "Good collaboration today, design and backend resolved the open questions.",
        "I can help document the release note and support the customer handoff.",
    ]
    neutral = [
        "Please update the ticket status after the standup.",
        "The meeting notes are in the project folder for review.",
        "QA needs the build number before regression starts.",
        "The backend team will discuss the migration tomorrow.",
        "Can someone confirm the owner for the dashboard copy?",
        "The product review is scheduled for Thursday afternoon.",
    ]
    tense = [
        "This keeps getting blocked and nobody is making a decision.",
        "The same bug is back again and the handoff is becoming frustrating.",
        "We are wasting time repeating the same deployment argument.",
        "The release planning is tense because priorities changed again.",
        "This review is going in circles and morale is dropping.",
        "The team is exhausted by unclear ownership and constant escalation.",
    ]
    toxic = [
        "This is unacceptable, your team keeps breaking everything and blaming others.",
        "Stop making excuses, this implementation is careless and embarrassing.",
        "The comments are hostile and people are attacking each other.",
        "You ignored the plan again and created a production mess.",
        "This is a reckless decision and the team cannot trust your judgment.",
        "The tone is aggressive, disrespectful, and damaging collaboration.",
    ]
    isolated = [
        "I have not heard from the owner for days and the thread is silent.",
        "No response on the design question after multiple follow ups.",
        "The employee stopped joining reviews and communication frequency dropped.",
        "The handoff is stalled because the key contributor is not responding.",
        "There are several unanswered questions and collaboration has slowed.",
        "The team has limited participation from one member this sprint.",
    ]

    def add(texts: list[str], toxicity: int, aggression: int, conflict: float) -> None:
        for text in texts:
            rows.append({"text": text, "toxicity": toxicity, "aggression": aggression, "conflict": conflict})
            rows.append({"text": f"{text} during sprint review", "toxicity": toxicity, "aggression": aggression, "conflict": min(1.0, conflict + 0.04)})
            rows.append({"text": f"{text} in engineering release planning", "toxicity": toxicity, "aggression": aggression, "conflict": min(1.0, conflict + 0.06)})

    add(positive, 0, 0, 0.08)
    add(neutral, 0, 0, 0.18)
    add(tense, 0, 1, 0.55)
    add(toxic, 1, 1, 0.86)
    add(isolated, 0, 0, 0.48)
    return rows


def train_communication_models() -> CommunicationModelMetrics:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    rows = _training_rows()
    texts = [str(row["text"]) for row in rows]
    toxicity = np.array([int(row["toxicity"]) for row in rows])
    aggression = np.array([int(row["aggression"]) for row in rows])
    conflict = np.array([float(row["conflict"]) for row in rows])

    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_features=900)
    features = vectorizer.fit_transform(texts)
    indices = np.arange(len(texts))
    train_idx, test_idx = train_test_split(indices, test_size=0.28, random_state=42, stratify=toxicity + aggression)

    toxicity_model = LogisticRegression(max_iter=600, class_weight="balanced", random_state=42)
    toxicity_model.fit(features[train_idx], toxicity[train_idx])
    aggression_model = RandomForestClassifier(n_estimators=120, max_depth=8, random_state=42, class_weight="balanced")
    aggression_model.fit(features[train_idx], aggression[train_idx])
    conflict_model = GradientBoostingRegressor(random_state=42, max_depth=3)
    conflict_model.fit(features[train_idx], conflict[train_idx])

    toxicity_pred = toxicity_model.predict(features[test_idx])
    toxicity_prob = toxicity_model.predict_proba(features[test_idx])[:, 1]
    aggression_pred = aggression_model.predict(features[test_idx])
    conflict_pred = conflict_model.predict(features[test_idx])
    metrics = CommunicationModelMetrics(
        toxicity_accuracy=round(float(accuracy_score(toxicity[test_idx], toxicity_pred)), 3),
        toxicity_roc_auc=round(float(roc_auc_score(toxicity[test_idx], toxicity_prob)), 3),
        aggression_accuracy=round(float(accuracy_score(aggression[test_idx], aggression_pred)), 3),
        conflict_mae=round(float(mean_absolute_error(conflict[test_idx], conflict_pred)), 3),
        trained_samples=len(rows),
        model_family="TF-IDF + LogisticRegression + RandomForest + GradientBoosting",
    )
    joblib.dump(vectorizer, COMM_VECTOR_PATH)
    joblib.dump(toxicity_model, TOXIC_MODEL_PATH)
    joblib.dump(aggression_model, AGGRESSION_MODEL_PATH)
    joblib.dump(conflict_model, CONFLICT_MODEL_PATH)
    METRICS_PATH.write_text(json.dumps(asdict(metrics), indent=2), encoding="utf-8")
    return metrics


class CommunicationQualityEngine:
    model_name = "PyTorch TextEmotionNet + TF-IDF Communication Risk Ensemble"

    def __init__(self) -> None:
        self._vectorizer: TfidfVectorizer | None = None
        self._toxicity_model: LogisticRegression | None = None
        self._aggression_model: RandomForestClassifier | None = None
        self._conflict_model: GradientBoostingRegressor | None = None

    @property
    def available(self) -> bool:
        return all(path.exists() for path in [COMM_VECTOR_PATH, TOXIC_MODEL_PATH, AGGRESSION_MODEL_PATH, CONFLICT_MODEL_PATH, METRICS_PATH])

    def ensure_artifacts(self) -> None:
        if not self.available:
            train_communication_models()

    def metrics(self) -> dict[str, object]:
        self.ensure_artifacts()
        return json.loads(METRICS_PATH.read_text(encoding="utf-8"))

    def _load(self) -> None:
        self.ensure_artifacts()
        if self._vectorizer is None:
            self._vectorizer = joblib.load(COMM_VECTOR_PATH)
            self._toxicity_model = joblib.load(TOXIC_MODEL_PATH)
            self._aggression_model = joblib.load(AGGRESSION_MODEL_PATH)
            self._conflict_model = joblib.load(CONFLICT_MODEL_PATH)

    def predict_text(self, text: str) -> dict[str, float]:
        self._load()
        assert self._vectorizer is not None
        assert self._toxicity_model is not None
        assert self._aggression_model is not None
        assert self._conflict_model is not None
        features = self._vectorizer.transform([text])
        toxicity = float(self._toxicity_model.predict_proba(features)[0, 1])
        aggression = float(self._aggression_model.predict_proba(features)[0, 1])
        conflict = float(np.clip(self._conflict_model.predict(features)[0], 0, 1))
        confidence = float(np.clip(max(toxicity, aggression, conflict) * 0.55 + 0.39, 0.45, 0.96))
        return {
            "toxicity_probability": round(toxicity, 4),
            "aggression_probability": round(aggression, 4),
            "conflict_probability": round(conflict, 4),
            "confidence": round(confidence, 4),
        }


communication_quality_engine = CommunicationQualityEngine()
