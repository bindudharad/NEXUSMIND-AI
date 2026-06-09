from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import r2_score
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

from app.schemas.learning import LearningEmployeeProfile


ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"
RANKER_PATH = ARTIFACT_DIR / "learning_recommendation_ranker.joblib"
COMPLETION_PATH = ARTIFACT_DIR / "learning_completion_forecaster.joblib"
SCALER_PATH = ARTIFACT_DIR / "learning_feature_scaler.joblib"
VECTORIZER_PATH = ARTIFACT_DIR / "learning_course_vectorizer.joblib"
NEIGHBORS_PATH = ARTIFACT_DIR / "learning_course_neighbors.joblib"
METRICS_PATH = ARTIFACT_DIR / "learning_metrics.json"


@dataclass(frozen=True)
class CourseCatalogItem:
    course_id: str
    title: str
    provider: str
    target_skill: str
    category: str
    difficulty: str
    duration_hours: int
    certification: str
    text: str


@dataclass(frozen=True)
class LearningPrediction:
    score: float
    completion_probability: float
    career_impact: float
    confidence: float
    semantic_similarity: float


COURSE_CATALOG = [
    CourseCatalogItem("crs-k8s-adv", "Advanced Kubernetes for Scalable Cloud Systems", "Coursera", "kubernetes", "Cloud Infrastructure", "advanced", 42, "Certified Kubernetes Administrator", "kubernetes cloud native deployment scaling helm observability reliability devops containers platform"),
    CourseCatalogItem("crs-aws-sa", "AWS Solutions Architect Professional Path", "LinkedIn Learning", "aws", "Cloud Architecture", "advanced", 38, "AWS Solutions Architect", "aws cloud architecture vpc iam compute storage serverless cost reliability enterprise"),
    CourseCatalogItem("crs-mlops", "Production MLOps and Model Monitoring", "Coursera", "mlops", "AI Infrastructure", "advanced", 46, "MLOps Specialization", "mlops model registry feature store monitoring drift kubernetes ci cd machine learning operations"),
    CourseCatalogItem("crs-rag", "Enterprise RAG and Vector Search Systems", "Udemy", "rag", "Generative AI", "advanced", 34, "RAG Systems Certificate", "retrieval augmented generation vector database embeddings langchain qdrant evaluation llm enterprise"),
    CourseCatalogItem("crs-sec", "Zero Trust Security and Threat Modeling", "LinkedIn Learning", "security", "Cybersecurity", "intermediate", 26, "Security Architecture Certificate", "security zero trust threat modeling oauth jwt soc2 access control risk incident response"),
    CourseCatalogItem("crs-system-design", "Distributed Systems and System Design Masterclass", "Udemy", "system design", "Architecture", "advanced", 40, "System Design Certificate", "distributed systems scalability caching queues databases architecture resilience reliability"),
    CourseCatalogItem("crs-data-eng", "Modern Data Engineering with Spark and Kafka", "Coursera", "data engineering", "Data Platform", "advanced", 44, "Data Engineering Professional", "spark kafka pipelines lakehouse streaming analytics data modeling"),
    CourseCatalogItem("crs-leadership", "Engineering Leadership and Mentorship", "LinkedIn Learning", "leadership", "Leadership", "intermediate", 18, "Engineering Leadership Certificate", "leadership mentoring feedback delegation roadmap stakeholder communication manager growth"),
    CourseCatalogItem("crs-frontend", "Enterprise Frontend Architecture with React", "Udemy", "frontend architecture", "Frontend", "advanced", 31, "React Architecture Certificate", "react nextjs frontend architecture performance accessibility design systems state management"),
    CourseCatalogItem("crs-product", "AI Product Strategy and Roadmapping", "Coursera", "product strategy", "Product", "intermediate", 22, "AI Product Strategy Certificate", "product strategy roadmap ai metrics discovery experimentation stakeholder outcomes"),
    CourseCatalogItem("crs-postgres", "PostgreSQL Performance and Reliability", "LinkedIn Learning", "postgresql", "Database", "advanced", 24, "PostgreSQL Performance Certificate", "postgresql indexing query optimization locks replication reliability schema database"),
    CourseCatalogItem("crs-python", "Advanced Python for Backend Systems", "Udemy", "python", "Backend", "intermediate", 28, "Python Backend Certificate", "python fastapi async performance testing backend api architecture typing"),
    CourseCatalogItem("crs-qa", "Automation Testing for Enterprise Platforms", "Coursera", "test automation", "Quality Engineering", "intermediate", 25, "Test Automation Certificate", "automation testing api regression playwright ci quality gates reliability"),
    CourseCatalogItem("crs-finops", "Cloud FinOps and Cost Governance", "LinkedIn Learning", "finops", "Cloud Operations", "intermediate", 16, "FinOps Practitioner", "finops cloud cost governance budgets forecasting optimization aws azure kubernetes"),
    CourseCatalogItem("crs-analytics", "Executive Analytics and KPI Storytelling", "Coursera", "analytics", "Business Intelligence", "intermediate", 20, "Analytics Storytelling Certificate", "analytics dashboards kpi executive insights storytelling forecasting decision intelligence"),
]


class LearningRecommendationEngine:
    model_name = "RandomForest + TF-IDF Learning Recommendation Engine"
    feature_names = [
        "gap_strength",
        "semantic_similarity",
        "learning_velocity",
        "assessment_score",
        "promotion_readiness",
        "market_alignment",
        "manager_priority",
        "future_criticality",
        "burnout_drag",
        "course_duration_norm",
        "completed_courses_norm",
    ]

    def __init__(self) -> None:
        ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
        self.ranker: RandomForestRegressor | None = None
        self.completion_model: GradientBoostingRegressor | None = None
        self.scaler: StandardScaler | None = None
        self.vectorizer: TfidfVectorizer | None = None
        self.neighbors: NearestNeighbors | None = None
        self.metrics: dict[str, object] = {}
        self._load_or_train()

    def _load_or_train(self) -> None:
        paths = [RANKER_PATH, COMPLETION_PATH, SCALER_PATH, VECTORIZER_PATH, NEIGHBORS_PATH, METRICS_PATH]
        if all(path.exists() for path in paths):
            self.ranker = joblib.load(RANKER_PATH)
            self.completion_model = joblib.load(COMPLETION_PATH)
            self.scaler = joblib.load(SCALER_PATH)
            self.vectorizer = joblib.load(VECTORIZER_PATH)
            self.neighbors = joblib.load(NEIGHBORS_PATH)
            self.metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
            return
        self.train()

    def train(self) -> dict[str, object]:
        rng = np.random.default_rng(126)
        rows = 5200
        gap = rng.beta(3.8, 2.1, rows)
        semantic = rng.beta(4.2, 2.0, rows)
        velocity = rng.beta(3.2, 2.3, rows)
        assessment = rng.normal(0.72, 0.16, rows).clip(0.2, 0.99)
        promotion = rng.beta(2.6, 2.8, rows)
        market = rng.beta(3.1, 2.4, rows)
        priority = rng.beta(3.0, 2.2, rows)
        future = rng.beta(4.0, 1.9, rows)
        burnout = rng.beta(2.0, 4.2, rows)
        duration = rng.beta(2.5, 4.0, rows)
        completed = rng.beta(2.0, 5.0, rows)
        x = np.column_stack([gap, semantic, velocity, assessment, promotion, market, priority, future, burnout, duration, completed])
        score = (
            24
            + gap * 24
            + semantic * 18
            + velocity * 9
            + assessment * 8
            + promotion * 8
            + market * 8
            + priority * 10
            + future * 13
            - burnout * 7
            - duration * 4
            + completed * 3
            + rng.normal(0, 2.2, rows)
        ).clip(0, 100)
        completion = (
            18
            + velocity * 28
            + assessment * 24
            + completed * 14
            + semantic * 10
            - duration * 12
            - burnout * 8
            + rng.normal(0, 2.0, rows)
        ).clip(0, 100)

        self.scaler = StandardScaler()
        scaled = self.scaler.fit_transform(x)
        self.ranker = RandomForestRegressor(n_estimators=180, min_samples_leaf=4, random_state=126, n_jobs=-1)
        self.completion_model = GradientBoostingRegressor(n_estimators=180, learning_rate=0.05, max_depth=3, random_state=127)
        self.ranker.fit(scaled, score)
        self.completion_model.fit(scaled, completion)

        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
        matrix = self.vectorizer.fit_transform([course.text for course in COURSE_CATALOG])
        self.neighbors = NearestNeighbors(metric="cosine", algorithm="brute")
        self.neighbors.fit(matrix)

        prediction = self.ranker.predict(scaled[:900])
        completion_prediction = self.completion_model.predict(scaled[:900])
        self.metrics = {
            "model": self.model_name,
            "training_examples": rows,
            "course_catalog_size": len(COURSE_CATALOG),
            "ranker_r2": round(float(r2_score(score[:900], prediction)), 3),
            "completion_r2": round(float(r2_score(completion[:900], completion_prediction)), 3),
            "features": self.feature_names,
            "providers": ["Coursera", "Udemy", "LinkedIn Learning"],
        }
        joblib.dump(self.ranker, RANKER_PATH)
        joblib.dump(self.completion_model, COMPLETION_PATH)
        joblib.dump(self.scaler, SCALER_PATH)
        joblib.dump(self.vectorizer, VECTORIZER_PATH)
        joblib.dump(self.neighbors, NEIGHBORS_PATH)
        METRICS_PATH.write_text(json.dumps(self.metrics, indent=2), encoding="utf-8")
        return self.metrics

    def candidate_courses(self, query: str, top_k: int = 6) -> list[tuple[CourseCatalogItem, float]]:
        if self.vectorizer is None or self.neighbors is None:
            self.train()
        query_vector = self.vectorizer.transform([query]) if self.vectorizer else None
        distances, indices = self.neighbors.kneighbors(query_vector, n_neighbors=min(top_k, len(COURSE_CATALOG))) if self.neighbors else ([], [])
        return [(COURSE_CATALOG[int(index)], round(float(1 - distance), 3)) for distance, index in zip(distances[0], indices[0])]

    def predict(self, employee: LearningEmployeeProfile, skill: str, course: CourseCatalogItem, semantic_similarity: float, future_criticality: float, gap_strength: float) -> LearningPrediction:
        if self.ranker is None or self.completion_model is None or self.scaler is None:
            self.train()
        vector = np.array(
            [
                [
                    gap_strength,
                    semantic_similarity,
                    employee.learning_velocity,
                    employee.assessment_score / 100,
                    employee.promotion_readiness,
                    employee.market_alignment,
                    employee.manager_priority,
                    future_criticality,
                    employee.burnout_risk,
                    min(course.duration_hours / 80, 1),
                    min(employee.courses_completed_last_year / 8, 1),
                ]
            ]
        )
        scaled = self.scaler.transform(vector) if self.scaler else vector
        score = float(self.ranker.predict(scaled)[0]) if self.ranker else 0
        completion = float(self.completion_model.predict(scaled)[0]) if self.completion_model else 0
        career_impact = float(np.clip(score * 0.44 + future_criticality * 100 * 0.24 + employee.promotion_readiness * 100 * 0.18 + employee.market_alignment * 100 * 0.14, 0, 100))
        confidence = float(np.clip(0.58 + semantic_similarity * 0.18 + gap_strength * 0.12 + employee.learning_velocity * 0.1 + future_criticality * 0.08, 0.62, 0.97))
        return LearningPrediction(
            score=round(float(np.clip(score, 0, 100)), 2),
            completion_probability=round(float(np.clip(completion, 0, 100)), 2),
            career_impact=round(career_impact, 2),
            confidence=round(confidence, 3),
            semantic_similarity=semantic_similarity,
        )


learning_engine = LearningRecommendationEngine()
