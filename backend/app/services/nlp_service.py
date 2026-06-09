from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

from app.ai.nlp_engine import nlp_emotion_engine
from app.schemas.nlp import (
    EmotionScores,
    NLPAnalyzeRequest,
    NLPAnalyzeResponse,
    NLPBatchRequest,
    NLPBatchResponse,
    NLPTrendPoint,
    NLPTrendsResponse,
)


HISTORY_PATH = Path(__file__).resolve().parents[1] / "data" / "nlp_predictions.jsonl"


class NLPHistoryRepository:
    def __init__(self) -> None:
        self._lock = Lock()
        HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)

    def append(self, record: dict[str, object]) -> None:
        with self._lock:
            with HISTORY_PATH.open("a", encoding="utf-8") as file:
                file.write(json.dumps(record) + "\n")

    def read(self) -> list[dict[str, object]]:
        if not HISTORY_PATH.exists():
            return []
        with self._lock:
            records: list[dict[str, object]] = []
            for line in HISTORY_PATH.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(record, dict):
                    records.append(record)
            return records


class NLPService:
    def __init__(self) -> None:
        self._history = NLPHistoryRepository()

    def analyze(self, payload: NLPAnalyzeRequest) -> NLPAnalyzeResponse:
        raw = nlp_emotion_engine.analyze(payload.text)
        response = NLPAnalyzeResponse(
            employee_id=payload.employee_id,
            department=payload.department,
            channel=payload.channel,
            sentiment=str(raw["sentiment"]),
            primary_emotion=str(raw["primary_emotion"]),
            confidence=float(raw["confidence"]),
            sentiment_score=float(raw["sentiment_score"]),
            emotion_scores=EmotionScores(**raw["emotion_scores"]),
            burnout_indicators=list(raw["burnout_indicators"]),
            recommendation=str(raw["recommendation"]),
            model=str(raw["model"]),
            tokens=list(raw["tokens"]),
        )
        self._history.append(
            response.model_dump()
            | {
                "text": payload.text,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        return response

    def batch(self, payload: NLPBatchRequest) -> NLPBatchResponse:
        results = [self.analyze(message) for message in payload.messages]
        team_sentiment = round(sum(result.sentiment_score for result in results) / len(results), 3)
        high_risk_count = sum(
            1
            for result in results
            if result.emotion_scores.burnout >= 0.45 or result.emotion_scores.toxicity >= 0.45 or result.emotion_scores.stress >= 0.6
        )
        recommendation = "Communication is stable."
        if high_risk_count:
            recommendation = "Prioritize high-risk employees for manager review and workload intervention."
        return NLPBatchResponse(
            results=results,
            team_sentiment_score=team_sentiment,
            high_risk_count=high_risk_count,
            recommendation=recommendation,
        )

    def trends(self) -> NLPTrendsResponse:
        records = self._history.read()
        grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
        for record in records:
            if isinstance(record.get("emotion_scores"), dict) and "sentiment_score" in record:
                grouped[str(record.get("department", "Unknown"))].append(record)
        trends: list[NLPTrendPoint] = []
        for department, rows in grouped.items():
            trends.append(
                NLPTrendPoint(
                    department=department,
                    average_sentiment=round(sum(float(row["sentiment_score"]) for row in rows) / len(rows), 3),
                    stress_index=round(sum(float(row["emotion_scores"]["stress"]) for row in rows) / len(rows), 3),
                    toxicity_index=round(sum(float(row["emotion_scores"]["toxicity"]) for row in rows) / len(rows), 3),
                    burnout_index=round(sum(float(row["emotion_scores"]["burnout"]) for row in rows) / len(rows), 3),
                    messages_analyzed=len(rows),
                )
            )
        return NLPTrendsResponse(trends=trends, storage=str(HISTORY_PATH))


nlp_service = NLPService()
