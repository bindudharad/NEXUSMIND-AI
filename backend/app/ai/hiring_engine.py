from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.metrics.pairwise import cosine_similarity

from app.schemas.hiring import HiringCandidateInput, HiringRoleInput


ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"
VECTORIZER_PATH = ARTIFACT_DIR / "hiring_tfidf_vectorizer.joblib"
RANKER_PATH = ARTIFACT_DIR / "hiring_candidate_ranker.joblib"
FRAUD_MODEL_PATH = ARTIFACT_DIR / "hiring_fraud_isolation_forest.joblib"
METRICS_PATH = ARTIFACT_DIR / "hiring_metrics.json"


SKILL_ALIASES: dict[str, tuple[str, ...]] = {
    "python": ("python", "fastapi", "django", "flask"),
    "typescript": ("typescript", "react", "next.js", "nextjs", "node"),
    "kubernetes": ("kubernetes", "k8s", "helm", "eks", "aks"),
    "docker": ("docker", "container", "containers"),
    "api reliability": ("api reliability", "api", "latency", "rate limit", "observability"),
    "security": ("security", "oauth", "jwt", "zero trust", "threat", "soc2"),
    "mlops": ("mlops", "model serving", "feature store", "model monitoring"),
    "postgresql": ("postgresql", "postgres", "sql"),
    "redis": ("redis", "cache", "caching"),
    "aws": ("aws", "lambda", "ecs", "eks", "s3"),
    "leadership": ("lead", "mentor", "managed", "architected", "principal"),
    "incident response": ("incident response", "on-call", "postmortem", "sev"),
    "microservices": ("microservices", "distributed systems", "event-driven"),
    "testing": ("testing", "pytest", "jest", "ci/cd", "quality"),
}


@dataclass(frozen=True)
class HiringModelMetrics:
    model: str
    r2: float
    mae: float
    trained_samples: int


class HiringIntelligenceEngine:
    model_name = "TF-IDF Semantic Matcher + RandomForest Hiring Ranker"

    feature_names = [
        "semantic_match",
        "skill_match",
        "resume_quality",
        "culture_fit",
        "learning_potential",
        "communication_quality",
        "experience_quality",
        "project_relevance",
        "leadership_signal",
        "fraud_risk",
    ]

    def __init__(self) -> None:
        ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
        self.vectorizer: TfidfVectorizer | None = None
        self.ranker: RandomForestRegressor | None = None
        self.fraud_model: IsolationForest | None = None

    @property
    def available(self) -> bool:
        return all(path.exists() for path in [VECTORIZER_PATH, RANKER_PATH, FRAUD_MODEL_PATH, METRICS_PATH])

    def ensure_artifacts(self) -> None:
        if not self.available:
            self.train()

    def train(self, rows: int = 3600, seed: int = 912) -> list[HiringModelMetrics]:
        rng = np.random.default_rng(seed)
        texts = self._training_corpus()
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", min_df=1)
        vectorizer.fit(texts)

        semantic = rng.beta(3.6, 2.1, rows)
        skill = rng.beta(3.2, 2.2, rows)
        resume_quality = rng.beta(3.3, 2.0, rows)
        culture = rng.beta(3.0, 2.4, rows)
        learning = rng.beta(3.4, 2.0, rows)
        communication = rng.beta(3.1, 2.3, rows)
        experience = rng.beta(3.1, 2.1, rows)
        project = rng.beta(3.0, 2.2, rows)
        leadership = rng.beta(2.5, 2.8, rows)
        fraud = rng.beta(1.5, 7.2, rows)
        features = np.column_stack(
            [semantic, skill, resume_quality, culture, learning, communication, experience, project, leadership, fraud]
        ).astype(np.float32)
        score = (
            semantic * 22
            + skill * 18
            + resume_quality * 10
            + culture * 9
            + learning * 9
            + communication * 8
            + experience * 10
            + project * 9
            + leadership * 7
            - fraud * 18
            + rng.normal(0, 2.8, rows)
        )
        score = np.clip(score, 0, 100)
        x_train, x_test, y_train, y_test = train_test_split(features, score, test_size=0.22, random_state=73)
        ranker = RandomForestRegressor(n_estimators=220, max_depth=12, min_samples_leaf=3, random_state=73, n_jobs=-1)
        ranker.fit(x_train, y_train)
        predictions = ranker.predict(x_test)
        ranker_metrics = HiringModelMetrics(
            model="RandomForest candidate ranking regressor",
            r2=round(float(r2_score(y_test, predictions)), 3),
            mae=round(float(mean_absolute_error(y_test, predictions)), 3),
            trained_samples=rows,
        )

        fraud_model = IsolationForest(n_estimators=180, contamination=0.12, random_state=73)
        fraud_model.fit(features)

        self.vectorizer = vectorizer
        self.ranker = ranker
        self.fraud_model = fraud_model
        joblib.dump(vectorizer, VECTORIZER_PATH)
        joblib.dump(ranker, RANKER_PATH)
        joblib.dump(fraud_model, FRAUD_MODEL_PATH)
        metrics = [ranker_metrics]
        METRICS_PATH.write_text(json.dumps([asdict(metric) for metric in metrics], indent=2), encoding="utf-8")
        return metrics

    def metrics(self) -> list[dict[str, float | int | str]]:
        self.ensure_artifacts()
        return json.loads(METRICS_PATH.read_text(encoding="utf-8"))

    def semantic_match(self, role: HiringRoleInput, candidate: HiringCandidateInput) -> float:
        self.ensure_artifacts()
        if self.vectorizer is None:
            self.vectorizer = joblib.load(VECTORIZER_PATH)
        role_text = " ".join([role.title, role.job_description, role.team_context, " ".join(role.required_skills), " ".join(role.preferred_skills)])
        candidate_text = self._candidate_text(candidate)
        matrix = self.vectorizer.transform([role_text, candidate_text])
        return round(float(cosine_similarity(matrix[0], matrix[1])[0][0]), 4)

    def rank_score(self, features: list[float]) -> dict[str, float]:
        self.ensure_artifacts()
        vector = np.array([features], dtype=np.float32)
        if self.ranker is None:
            self.ranker = joblib.load(RANKER_PATH)
        if self.fraud_model is None:
            self.fraud_model = joblib.load(FRAUD_MODEL_PATH)
        model_score = float(np.clip(self.ranker.predict(vector)[0], 0, 100))
        anomaly_raw = float(self.fraud_model.decision_function(vector)[0])
        anomaly_risk = float(np.clip((0.18 - anomaly_raw) * 140, 0, 100))
        return {"random_forest_ranker": round(model_score, 2), "fraud_anomaly_risk": round(anomaly_risk, 2)}

    @staticmethod
    def extract_skills(text: str, declared: list[str] | None = None) -> list[str]:
        lowered = f"{text} {' '.join(declared or [])}".lower()
        detected = []
        for skill, aliases in SKILL_ALIASES.items():
            if any(alias in lowered for alias in aliases):
                detected.append(skill)
        return sorted(set(detected))

    @staticmethod
    def _candidate_text(candidate: HiringCandidateInput) -> str:
        return " ".join(
            [
                candidate.current_title,
                candidate.resume_text,
                candidate.interview_transcript,
                candidate.portfolio_summary,
                " ".join(candidate.certifications),
                " ".join(candidate.declared_skills),
            ]
        )

    @staticmethod
    def _training_corpus() -> list[str]:
        return [
            "senior backend engineer python fastapi kubernetes api reliability security mlops incident response",
            "platform engineer docker kubernetes terraform observability distributed systems postgres redis",
            "frontend engineer react typescript next.js design systems accessibility performance",
            "data engineer spark kafka airflow python sql data quality platform reliability",
            "security engineer oauth jwt threat modeling soc2 incident response zero trust",
            "machine learning engineer model serving feature store monitoring pytorch tensorflow mlops",
            "engineering manager mentoring architecture cross functional communication roadmap delivery",
            "junior developer html css basic javascript coursework internship",
            "candidate resume project leadership measurable impact reliability migration cloud",
        ]


hiring_intelligence_engine = HiringIntelligenceEngine()
