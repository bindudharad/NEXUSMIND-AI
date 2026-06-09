from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors

from app.schemas.intelligence import KnowledgeAnswer, KnowledgeDocument


DOCUMENTS = [
    KnowledgeDocument(
        id="doc-alpha-recovery",
        title="Project Alpha Recovery Review",
        content="Project Alpha was recovered by freezing scope, adding QA capacity, and moving senior engineers away from meetings for two weeks.",
        tags=["project-alpha", "delivery", "qa", "recovery"],
    ),
    KnowledgeDocument(
        id="doc-kubernetes-experts",
        title="Platform Expertise Map",
        content="Kubernetes expertise is strongest in Platform Engineering: Nisha Rao, Omar Singh, and Lina Chen led production cluster upgrades.",
        tags=["kubernetes", "platform", "skills"],
    ),
    KnowledgeDocument(
        id="doc-security-playbook",
        title="Privileged Access Security Playbook",
        content="Suspicious admin activity requires step-up authentication, token rotation, session replay review, and data export throttling.",
        tags=["security", "access", "incident"],
    ),
    KnowledgeDocument(
        id="doc-meeting-load-policy",
        title="Meeting Load Recovery Policy",
        content="When meeting load exceeds ten hours per week for delivery owners, managers convert status meetings into async updates and protect focus blocks.",
        tags=["meetings", "productivity", "burnout"],
    ),
    KnowledgeDocument(
        id="doc-digital-twin-actions",
        title="Shadow Company Recovery Actions",
        content="Digital twin simulations recommend scope freeze, dependency recovery rooms, short-term specialist capacity, and isolated security response lanes.",
        tags=["digital-twin", "simulation", "operations"],
    ),
]

ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"
INDEX_PATH = ARTIFACT_DIR / "knowledge_vector_index.joblib"


@dataclass(frozen=True)
class VectorSearchHit:
    document: KnowledgeDocument
    score: float


class KnowledgeEngine:
    model_name = "TF-IDF Enterprise Vector Memory"

    def __init__(self) -> None:
        self.documents = DOCUMENTS
        self._corpus = [self._document_text(document) for document in self.documents]
        self._vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", sublinear_tf=True)
        self._matrix = self._vectorizer.fit_transform(self._corpus)
        self._index = NearestNeighbors(metric="cosine", algorithm="brute")
        self._index.fit(self._matrix)
        self._persist_index()

    @property
    def available(self) -> bool:
        return self._matrix.shape[0] == len(self.documents) and self._matrix.shape[1] > 0

    @property
    def vector_dimensions(self) -> int:
        return int(self._matrix.shape[1])

    def query(self, question: str) -> KnowledgeAnswer:
        hits = self.search(question, top_k=2)
        primary = hits[0]
        related = hits[1] if len(hits) > 1 else hits[0]
        confidence = round(min(96, max(58, 56 + primary.score * 42 + (primary.score - related.score) * 10)))
        answer = (
            f"{primary.document.title}: {primary.document.content} "
            f"Related memory: {related.document.title}. "
            f"Vector confidence {confidence}% from {self.model_name}."
        )
        return KnowledgeAnswer(answer=answer, confidence=confidence, sources=[hit.document for hit in hits])

    def search(self, question: str, top_k: int = 3) -> list[VectorSearchHit]:
        query_vector = self._vectorizer.transform([question])
        neighbors = min(max(top_k, 1), len(self.documents))
        distances, indices = self._index.kneighbors(query_vector, n_neighbors=neighbors)
        hits: list[VectorSearchHit] = []
        for distance, index in zip(distances[0], indices[0], strict=True):
            score = round(float(max(0, 1 - distance)), 4)
            hits.append(VectorSearchHit(document=self.documents[int(index)], score=score))
        return hits

    def _persist_index(self) -> None:
        ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
        payload = {
            "model": self.model_name,
            "documents": [document.model_dump() for document in self.documents],
            "vocabulary_size": self.vector_dimensions,
        }
        joblib.dump(payload, INDEX_PATH)

    @staticmethod
    def _document_text(document: KnowledgeDocument) -> str:
        return f"{document.title} {document.content} {' '.join(document.tags)}"


knowledge_engine = KnowledgeEngine()
