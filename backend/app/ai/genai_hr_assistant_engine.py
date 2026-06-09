from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import NearestNeighbors
from sklearn.pipeline import Pipeline

from app.schemas.genai_hr_assistant import GenAIHRIntent


ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"
VECTOR_INDEX_PATH = ARTIFACT_DIR / "genai_hr_vector_index.joblib"
INTENT_MODEL_PATH = ARTIFACT_DIR / "genai_hr_intent_classifier.joblib"


@dataclass(frozen=True)
class GenAIKnowledgeDocument:
    doc_id: str
    system: str
    title: str
    content: str
    metadata: dict[str, str | float | int]


@dataclass(frozen=True)
class GenAIRetrievalHit:
    document: GenAIKnowledgeDocument
    score: float


class GenAIHRAssistantEngine:
    model_name = "Enterprise HR LLM Orchestrator + RAG Vector Retrieval"
    llm_provider = "OpenAI-compatible LLM API adapter with local retrieval-grounded fallback"
    rag_pipeline = "Intent classifier -> analytics tool calls -> TF-IDF embeddings -> vector retrieval -> grounded generation"
    vector_database = "Local FAISS-style NearestNeighbors vector store"

    def __init__(self) -> None:
        ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
        self.intent_model = self._load_or_train_intent_model()

    def classify_intent(self, question: str, memory_summary: str = "") -> GenAIHRIntent:
        text = f"{question}\n{memory_summary}".strip()
        prediction = self.intent_model.predict([text])[0]
        return prediction if prediction in self._intent_labels() else "general"

    def retrieve(self, question: str, documents: list[GenAIKnowledgeDocument], top_k: int = 7) -> tuple[list[GenAIRetrievalHit], str]:
        if not documents:
            return [], str(VECTOR_INDEX_PATH)
        corpus = [self._document_text(document) for document in documents]
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", sublinear_tf=True)
        matrix = vectorizer.fit_transform(corpus)
        index = NearestNeighbors(metric="cosine", algorithm="brute")
        index.fit(matrix)
        query = vectorizer.transform([question])
        neighbors = min(max(top_k, 1), len(documents))
        distances, indices = index.kneighbors(query, n_neighbors=neighbors)
        hits: list[GenAIRetrievalHit] = []
        for distance, index_id in zip(distances[0], indices[0], strict=True):
            score = round(float(max(0, 1 - distance)), 4)
            hits.append(GenAIRetrievalHit(document=documents[int(index_id)], score=score))
        payload = {
            "model": self.model_name,
            "vector_database": self.vector_database,
            "documents": len(documents),
            "vocabulary_size": int(matrix.shape[1]),
            "top_documents": [
                {
                    "doc_id": hit.document.doc_id,
                    "system": hit.document.system,
                    "title": hit.document.title,
                    "score": hit.score,
                }
                for hit in hits
            ],
        }
        joblib.dump(payload, VECTOR_INDEX_PATH)
        return hits, str(VECTOR_INDEX_PATH)

    def _load_or_train_intent_model(self) -> Pipeline:
        if INTENT_MODEL_PATH.exists():
            try:
                model = joblib.load(INTENT_MODEL_PATH)
                labels = set(getattr(model.named_steps.get("classifier"), "classes_", []))
                if self._intent_labels().issubset(labels):
                    return model
            except Exception:
                pass
        examples: list[tuple[str, GenAIHRIntent]] = [
            ("show high risk employees likely to resign next quarter", "attrition"),
            ("who is likely to resign in the next 3 months", "attrition"),
            ("explain attrition risk and retention actions", "attrition"),
            ("which team has highest burnout risk", "burnout"),
            ("why is morale declining and who needs wellness support", "burnout"),
            ("show stress and emotional exhaustion drivers", "burnout"),
            ("predict next month productivity", "productivity"),
            ("where are productivity leaks and focus problems", "productivity"),
            ("summarize deep work and context switching risk", "productivity"),
            ("which projects may fail next sprint", "project_risk"),
            ("forecast deadline failure and budget risk", "project_risk"),
            ("which delivery team is at risk of project failure", "project_risk"),
            ("which department needs hiring urgently", "hiring"),
            ("generate hiring demand and recruiter recommendation", "hiring"),
            ("where do we need backend staffing", "hiring"),
            ("summarize company health", "company_health"),
            ("show executive company health and workforce stability", "company_health"),
            ("what is the organization health score", "company_health"),
            ("simulate 15 percent workforce reduction", "digital_twin"),
            ("what happens if project alpha slips by 30 days", "digital_twin"),
            ("predict impact of hiring freeze using the company twin", "digital_twin"),
            ("forecast revenue cost roi and budget optimization", "financial"),
            ("show financial risk net savings payback and operating margin", "financial"),
            ("which interventions have the best roi and profitability impact", "financial"),
            ("generate executive workforce report", "report"),
            ("create HR board report", "report"),
            ("generate HR report with risks and recommendations", "report"),
            ("retrieve policy and knowledge graph context", "knowledge"),
            ("which expertise is at risk of knowledge loss", "knowledge"),
            ("show organizational memory and SOP gaps", "knowledge"),
            ("what should HR do next", "general"),
            ("give me recommended workforce actions", "general"),
            ("explain the current enterprise workforce state", "general"),
        ]
        model: Pipeline = Pipeline(
            [
                ("tfidf", TfidfVectorizer(ngram_range=(1, 2), stop_words="english", sublinear_tf=True)),
                ("classifier", LogisticRegression(max_iter=500, random_state=17)),
            ]
        )
        model.fit([text for text, _ in examples], [label for _, label in examples])
        joblib.dump(model, INTENT_MODEL_PATH)
        return model

    @staticmethod
    def _document_text(document: GenAIKnowledgeDocument) -> str:
        metadata_text = " ".join(f"{key}:{value}" for key, value in document.metadata.items())
        return f"{document.system} {document.title} {document.content} {metadata_text}"

    @staticmethod
    def _intent_labels() -> set[str]:
        return {
            "attrition",
            "burnout",
            "productivity",
            "project_risk",
            "hiring",
            "company_health",
            "digital_twin",
            "financial",
            "knowledge",
            "report",
            "general",
        }


genai_hr_assistant_engine = GenAIHRAssistantEngine()
