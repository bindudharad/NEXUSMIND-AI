from __future__ import annotations

import asyncio
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from itertools import combinations
from math import log, sqrt
from pathlib import Path
from statistics import mean, pstdev

from app.ai.nlp_engine import tokenize
from app.schemas.meetings import (
    MeetingActionItem,
    MeetingAnalysisResponse,
    MeetingAnalysisSummary,
    MeetingAnalyzeRequest,
    MeetingNecessityAssessment,
    MeetingOverloadAnalytics,
    MeetingProductivityInsight,
    MeetingRiskSignal,
    MeetingSpeakerAnalytics,
    MeetingTopicCluster,
    MeetingTranscriptTurn,
    MeetingWasteEconomics,
)
from app.schemas.nlp import NLPAnalyzeRequest
from app.services.nlp_service import nlp_service


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
HISTORY_PATH = DATA_DIR / "meeting_analysis_history.jsonl"

ACTION_PATTERNS = [
    re.compile(
        r"(?P<owner>[A-Z][a-zA-Z]+)\s+(?:will|must|should|needs to|has to)\s+(?P<task>[^.?!]+?)(?:\s+(?:by|before|on)\s+(?P<deadline>Friday|Monday|Tuesday|Wednesday|Thursday|today|tomorrow|next week|end of week|EOW|Q[1-4]))?[.?!]",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:assign|route|give)\s+(?P<task>[^.?!]+?)\s+to\s+(?P<owner>[A-Z][a-zA-Z]+)(?:\s+(?:by|before|on)\s+(?P<deadline>Friday|Monday|Tuesday|Wednesday|Thursday|today|tomorrow|next week|end of week|EOW|Q[1-4])(?:\s+[^.?!]*)?)?[.?!]",
        re.IGNORECASE,
    ),
]

BLOCKER_TERMS = {"blocked", "blocker", "delay", "risk", "dependency", "waiting", "stuck", "issue", "incident", "latency"}
DECISION_TERMS = {"decided", "decision", "agreed", "approved", "we will", "let's", "we need to", "commit to"}
PRODUCTIVITY_LOOP_TERMS = {"again", "rework", "repeat", "same issue", "still discussing", "no owner", "unclear", "loop"}
TOPIC_STOPWORDS = {
    "action",
    "again",
    "because",
    "daily",
    "decision",
    "meeting",
    "meetings",
    "need",
    "needs",
    "owner",
    "project",
    "sync",
    "team",
    "will",
    "work",
}


class MeetingAnalyzerService:
    model_name = "PyTorch NLP Meeting Intelligence Engine"

    def analyze(self, payload: MeetingAnalyzeRequest | None = None) -> MeetingAnalysisResponse:
        request = payload or self.default_request()
        turns = self._normalize_turns(request)
        nlp_results = [
            nlp_service.analyze(
                NLPAnalyzeRequest(
                    employee_id=turn.speaker,
                    department=request.department,
                    channel="meeting",
                    text=turn.text,
                )
            )
            for turn in turns
        ]
        now = datetime.now(timezone.utc)
        action_items = self._extract_action_items(turns)
        blockers = self._extract_blockers(turns)
        decisions = self._extract_decisions(turns)
        key_points = self._key_points(turns, blockers, decisions)
        speakers = self._speaker_analytics(turns, nlp_results)
        topic_clusters = self._topic_clusters(turns, blockers, decisions)
        productivity = self._productivity_insights(request, turns, action_items, blockers, decisions, speakers, topic_clusters)
        efficiency_score = self._insight_score(productivity, "Meeting efficiency")
        actionability_score = self._actionability_score(request, action_items, decisions, blockers)
        repeated_topic_rate = self._repeated_topic_rate(topic_clusters, turns)
        productivity_score = mean(insight.score for insight in productivity) if productivity else 0
        waste_percentage = self._waste_percentage(
            request=request,
            productivity_score=productivity_score,
            efficiency_score=efficiency_score,
            actionability_score=actionability_score,
            repeated_topic_rate=repeated_topic_rate,
            speakers=speakers,
            blockers=blockers,
            decisions=decisions,
            action_items=action_items,
        )
        waste_economics = self._waste_economics(request, speakers, waste_percentage)
        overload_analytics = self._overload_analytics(request, nlp_results, waste_percentage, speakers)
        necessity = self._necessity_assessment(
            request=request,
            decisions=decisions,
            action_items=action_items,
            blockers=blockers,
            topic_clusters=topic_clusters,
            speakers=speakers,
            productivity_score=productivity_score,
            waste_percentage=waste_percentage,
            repeated_topic_rate=repeated_topic_rate,
        )
        risks = self._risk_signals(nlp_results, speakers, blockers, request, topic_clusters, waste_percentage, actionability_score)
        recommendations = self._recommendations(productivity, risks, action_items, speakers, necessity, topic_clusters, waste_economics)
        summary = self._summary(
            nlp_results,
            speakers,
            productivity,
            action_items,
            blockers,
            efficiency_score,
            actionability_score,
            repeated_topic_rate,
            waste_percentage,
            waste_economics,
        )
        response = MeetingAnalysisResponse(
            model=self.model_name,
            generated_at=now,
            meeting_id=request.meeting_id,
            title=request.title,
            duration_minutes=request.duration_minutes,
            transcript_turns=len(turns),
            summary_text=self._summary_text(request, key_points, decisions, action_items, blockers, summary),
            key_points=key_points,
            decisions=decisions,
            action_items=action_items,
            blockers=blockers,
            speaker_analytics=speakers,
            productivity_insights=productivity,
            topic_clusters=topic_clusters,
            necessity_assessment=necessity,
            waste_economics=waste_economics,
            overload_analytics=overload_analytics,
            risk_signals=risks,
            recommendations=recommendations,
            summary=summary,
            storage=str(HISTORY_PATH),
        )
        self._append_jsonl(response.model_dump(mode="json"))
        return response

    async def stream(self, payload: MeetingAnalyzeRequest | None = None):
        request = payload or self.default_request()
        base_turns = self._normalize_turns(request)
        for sequence in range(3):
            visible_turns = base_turns[: max(2, round(len(base_turns) * (sequence + 1) / 3))]
            current = request.model_copy(update={"turns": visible_turns, "transcript": None, "realtime": True})
            response = self.analyze(current)
            data = response.model_dump(mode="json")
            data["summary"]["stream_sequence"] = sequence + 1
            yield f"event: meeting\ndata: {json.dumps(data)}\n\n"
            await asyncio.sleep(0.8)

    @staticmethod
    def default_request() -> MeetingAnalyzeRequest:
        return MeetingAnalyzeRequest(
            meeting_id="meeting-alpha-recovery",
            title="Project Alpha Recovery Sync",
            duration_minutes=46,
            department="Engineering",
            turns=[
                MeetingTranscriptTurn(speaker="Priya", text="Project Alpha is delayed because the API latency work is still blocked by the data migration."),
                MeetingTranscriptTurn(speaker="John", text="I am exhausted and working late every night. The same incident keeps coming back and the release owner is unclear."),
                MeetingTranscriptTurn(speaker="Maya", text="We agreed to freeze non-essential scope and move QA capacity into the release lane."),
                MeetingTranscriptTurn(speaker="John", text="John will optimize API latency before Friday and share the benchmark report."),
                MeetingTranscriptTurn(speaker="Bianca", text="Assign migration validation to Bianca by tomorrow so Backend can focus on the release path."),
                MeetingTranscriptTurn(speaker="Omar", text="The conversation is becoming tense. We need one decision owner and fewer status meetings."),
                MeetingTranscriptTurn(speaker="Priya", text="Decision: Priya will run the dependency room daily and cancel low-signal recurring meetings this week."),
            ],
        )

    @staticmethod
    def _normalize_turns(request: MeetingAnalyzeRequest) -> list[MeetingTranscriptTurn]:
        if request.turns:
            return request.turns
        if not request.transcript:
            return MeetingAnalyzerService.default_request().turns
        turns: list[MeetingTranscriptTurn] = []
        for raw_line in request.transcript.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            match = re.match(r"^(?P<speaker>[A-Za-z][A-Za-z\s.'-]{0,60}):\s*(?P<text>.+)$", line)
            if match:
                speaker = " ".join(match.group("speaker").split())
                text = match.group("text").strip()
            else:
                speaker = "Unattributed"
                text = line
            turns.append(MeetingTranscriptTurn(speaker=speaker, text=text))
        if turns:
            return turns[:120]
        return [MeetingTranscriptTurn(speaker="Unattributed", text=request.transcript)]

    @staticmethod
    def _sentences(turns: list[MeetingTranscriptTurn]) -> list[str]:
        sentences: list[str] = []
        for turn in turns:
            for sentence in re.split(r"(?<=[.?!])\s+", turn.text.strip()):
                clean = sentence.strip()
                if clean:
                    sentences.append(clean)
        return sentences

    def _extract_action_items(self, turns: list[MeetingTranscriptTurn]) -> list[MeetingActionItem]:
        items: list[MeetingActionItem] = []
        seen: set[tuple[str, str]] = set()
        for turn in turns:
            text = f"{turn.text.strip()} "
            for pattern in ACTION_PATTERNS:
                for match in pattern.finditer(text):
                    owner = self._title_name(match.group("owner"))
                    task, deadline = self._split_deadline(match.group("task"), match.groupdict().get("deadline"))
                    key = (owner.lower(), task.lower())
                    if len(task) < 5 or key in seen:
                        continue
                    seen.add(key)
                    items.append(
                        MeetingActionItem(
                            owner=owner,
                            task=task,
                            deadline=deadline,
                            confidence=0.86 if owner.lower() in turn.speaker.lower() else 0.78,
                            evidence=turn.text,
                        )
                    )
        return items[:8]

    def _extract_blockers(self, turns: list[MeetingTranscriptTurn]) -> list[str]:
        blockers = []
        for sentence in self._sentences(turns):
            lower = sentence.lower()
            if any(term in lower for term in BLOCKER_TERMS):
                blockers.append(sentence)
        return list(dict.fromkeys(blockers))[:8]

    def _extract_decisions(self, turns: list[MeetingTranscriptTurn]) -> list[str]:
        decisions = []
        for sentence in self._sentences(turns):
            lower = sentence.lower()
            if any(term in lower for term in DECISION_TERMS):
                decisions.append(sentence)
        return list(dict.fromkeys(decisions))[:6]

    def _key_points(self, turns: list[MeetingTranscriptTurn], blockers: list[str], decisions: list[str]) -> list[str]:
        scored: list[tuple[int, str]] = []
        for sentence in self._sentences(turns):
            lower = sentence.lower()
            score = 0
            score += 3 if any(term in lower for term in BLOCKER_TERMS) else 0
            score += 3 if any(term in lower for term in DECISION_TERMS) else 0
            score += 2 if any(term in lower for term in ["project", "release", "customer", "deadline", "qa", "api"]) else 0
            score += 1 if len(sentence.split()) >= 8 else 0
            if score:
                scored.append((score, sentence))
        ordered = [sentence for _, sentence in sorted(scored, key=lambda item: item[0], reverse=True)]
        return list(dict.fromkeys([*decisions, *blockers, *ordered]))[:7]

    @staticmethod
    def _speaker_analytics(turns: list[MeetingTranscriptTurn], nlp_results) -> list[MeetingSpeakerAnalytics]:
        grouped: dict[str, list[int]] = defaultdict(list)
        word_counts: dict[str, int] = Counter()
        for index, turn in enumerate(turns):
            grouped[turn.speaker].append(index)
            word_counts[turn.speaker] += len(turn.text.split())
        total_words = max(sum(word_counts.values()), 1)
        analytics: list[MeetingSpeakerAnalytics] = []
        for speaker, indices in grouped.items():
            speaker_results = [nlp_results[index] for index in indices]
            participation = round(word_counts[speaker] / total_words * 100, 2)
            flag = "balanced"
            if participation >= 45 and len(grouped) > 1:
                flag = "dominant"
            elif participation <= max(5, 100 / max(len(grouped), 1) * 0.35):
                flag = "silent"
            analytics.append(
                MeetingSpeakerAnalytics(
                    speaker=speaker,
                    utterances=len(indices),
                    word_count=word_counts[speaker],
                    participation_percent=participation,
                    sentiment_score=round(mean(result.sentiment_score for result in speaker_results), 3),
                    stress_score=round(
                        mean(
                            max(
                                result.emotion_scores.stress,
                                result.emotion_scores.burnout * 0.72,
                                result.emotion_scores.emotional_exhaustion,
                            )
                            for result in speaker_results
                        ),
                        3,
                    ),
                    toxicity_score=round(mean(result.emotion_scores.toxicity for result in speaker_results), 3),
                    burnout_score=round(mean(result.emotion_scores.burnout for result in speaker_results), 3),
                    participation_flag=flag,
                )
            )
        return sorted(analytics, key=lambda item: item.participation_percent, reverse=True)

    @staticmethod
    def _productivity_insights(
        request: MeetingAnalyzeRequest,
        turns: list[MeetingTranscriptTurn],
        action_items: list[MeetingActionItem],
        blockers: list[str],
        decisions: list[str],
        speakers: list[MeetingSpeakerAnalytics],
        topic_clusters: list[MeetingTopicCluster],
    ) -> list[MeetingProductivityInsight]:
        words = sum(len(turn.text.split()) for turn in turns)
        decisions_per_hour = len(decisions) / max(request.duration_minutes / 60, 0.1)
        action_density = len(action_items) / max(request.duration_minutes / 30, 1)
        blocker_pressure = min(1, len(blockers) / 5)
        loop_count = sum(1 for turn in turns if any(term in turn.text.lower() for term in PRODUCTIVITY_LOOP_TERMS))
        participation_std = pstdev([speaker.participation_percent for speaker in speakers]) if len(speakers) > 1 else 0
        repeated_topic_rate = MeetingAnalyzerService._repeated_topic_rate(topic_clusters, turns)
        clarity_score = min(100, max(0, 48 + action_density * 18 + decisions_per_hour * 9 - blocker_pressure * 22 - loop_count * 5))
        efficiency_score = min(100, max(0, 92 - request.duration_minutes * 0.55 - blocker_pressure * 18 - participation_std * 0.35 + len(decisions) * 5))
        collaboration_score = min(100, max(0, 86 - participation_std * 0.75 - sum(1 for speaker in speakers if speaker.toxicity_score >= 0.45) * 14))
        repetition_score = min(100, max(0, 100 - repeated_topic_rate * 0.82 - loop_count * 9 - sum(1 for cluster in topic_clusters if cluster.unresolved) * 8))
        return [
            MeetingProductivityInsight(
                label="Decision clarity",
                score=round(clarity_score, 2),
                details=f"{len(decisions)} decisions and {len(action_items)} action items detected across {len(turns)} turns.",
                recommendation="Assign a single owner to every unresolved decision before the meeting closes.",
            ),
            MeetingProductivityInsight(
                label="Meeting efficiency",
                score=round(efficiency_score, 2),
                details=f"{round(request.duration_minutes)} minutes, {words} words, {len(blockers)} blockers, and {loop_count} repeated-discussion signals.",
                recommendation="Shorten the next sync, pre-read blockers asynchronously, and reserve live time for decisions.",
            ),
            MeetingProductivityInsight(
                label="Collaboration balance",
                score=round(collaboration_score, 2),
                details=f"Participation spread is {round(participation_std, 2)} points across {len(speakers)} speakers.",
                recommendation="Invite quieter speakers into ownership decisions and cap dominant updates.",
            ),
            MeetingProductivityInsight(
                label="Topic repetition",
                score=round(repetition_score, 2),
                details=f"{round(repeated_topic_rate)}% repeated-topic rate across {len(topic_clusters)} clustered discussion thread(s).",
                recommendation="Move repeated status loops into an async decision log with one owner per unresolved topic.",
            ),
        ]

    @staticmethod
    def _topic_clusters(
        turns: list[MeetingTranscriptTurn],
        blockers: list[str],
        decisions: list[str],
    ) -> list[MeetingTopicCluster]:
        sentence_rows: list[tuple[int, str, str, list[str]]] = []
        for turn_index, turn in enumerate(turns):
            for sentence in re.split(r"(?<=[.?!])\s+", turn.text.strip()):
                clean = sentence.strip()
                if not clean:
                    continue
                tokens = [token for token in tokenize(clean) if token not in TOPIC_STOPWORDS and len(token) > 2]
                if tokens:
                    sentence_rows.append((turn_index, turn.speaker, clean, tokens))
        if not sentence_rows:
            return []

        document_frequency = Counter(token for *_rest, tokens in sentence_rows for token in set(tokens))
        total_documents = len(sentence_rows)
        vectors = [MeetingAnalyzerService._tfidf_vector(tokens, document_frequency, total_documents) for *_rest, tokens in sentence_rows]
        clusters: list[list[int]] = []
        for index, vector in enumerate(vectors):
            target_cluster = None
            best_similarity = 0.0
            for cluster_index, cluster in enumerate(clusters):
                similarity = max(MeetingAnalyzerService._cosine(vector, vectors[member_index]) for member_index in cluster)
                token_overlap = max(
                    MeetingAnalyzerService._token_overlap(sentence_rows[index][3], sentence_rows[member_index][3])
                    for member_index in cluster
                )
                if similarity >= 0.32 or token_overlap >= 0.34:
                    if similarity + token_overlap > best_similarity:
                        target_cluster = cluster_index
                        best_similarity = similarity + token_overlap
            if target_cluster is None:
                clusters.append([index])
            else:
                clusters[target_cluster].append(index)

        blocker_text = " ".join(blockers).lower()
        decision_text = " ".join(decisions).lower()
        topic_clusters: list[MeetingTopicCluster] = []
        for cluster_number, cluster in enumerate(clusters, start=1):
            if len(cluster) == 1 and len(topic_clusters) >= 4:
                continue
            phrases = [sentence_rows[index][2] for index in cluster]
            token_counts = Counter(token for index in cluster for token in sentence_rows[index][3])
            label_tokens = [token for token, _ in token_counts.most_common(3)]
            label = " ".join(label_tokens).title() if label_tokens else f"Topic {cluster_number}"
            if len(cluster) > 1:
                pair_scores = [
                    MeetingAnalyzerService._cosine(vectors[first], vectors[second])
                    for first, second in combinations(cluster, 2)
                ]
                semantic_score = min(100, 48 + (len(cluster) - 1) * 16 + mean(pair_scores) * 30)
            else:
                semantic_score = 22
            lower_phrases = " ".join(phrases).lower()
            unresolved = any(term in lower_phrases for term in BLOCKER_TERMS) and not any(token in decision_text for token in label_tokens)
            if len(cluster) >= 2 or unresolved or any(phrase.lower() in blocker_text for phrase in phrases):
                topic_clusters.append(
                    MeetingTopicCluster(
                        topic_id=f"topic-{cluster_number}",
                        label=label,
                        turn_indices=sorted({sentence_rows[index][0] for index in cluster}),
                        speakers=sorted({sentence_rows[index][1] for index in cluster}),
                        mentions=len(cluster),
                        semantic_repetition_score=round(float(semantic_score), 2),
                        unresolved=unresolved,
                        representative_phrases=phrases[:4],
                    )
                )
        return sorted(topic_clusters, key=lambda item: (item.mentions, item.semantic_repetition_score), reverse=True)[:8]

    @staticmethod
    def _tfidf_vector(tokens: list[str], document_frequency: Counter[str], total_documents: int) -> Counter[str]:
        counts = Counter(tokens)
        vector: Counter[str] = Counter()
        for token, count in counts.items():
            inverse_frequency = log((1 + total_documents) / (1 + document_frequency[token])) + 1
            vector[token] = count * inverse_frequency
        return vector

    @staticmethod
    def _cosine(first: Counter[str], second: Counter[str]) -> float:
        numerator = sum(first[token] * second[token] for token in first.keys() & second.keys())
        first_norm = sqrt(sum(value * value for value in first.values()))
        second_norm = sqrt(sum(value * value for value in second.values()))
        if not first_norm or not second_norm:
            return 0.0
        return numerator / (first_norm * second_norm)

    @staticmethod
    def _token_overlap(first: list[str], second: list[str]) -> float:
        first_set = set(first)
        second_set = set(second)
        if not first_set or not second_set:
            return 0.0
        return len(first_set & second_set) / min(len(first_set), len(second_set))

    @staticmethod
    def _repeated_topic_rate(topic_clusters: list[MeetingTopicCluster], turns: list[MeetingTranscriptTurn]) -> float:
        total_sentences = max(len(MeetingAnalyzerService._sentences(turns)), 1)
        repeated_mentions = sum(max(0, cluster.mentions - 1) for cluster in topic_clusters)
        return round(min(100, repeated_mentions / total_sentences * 100), 2)

    @staticmethod
    def _insight_score(productivity: list[MeetingProductivityInsight], label: str) -> float:
        match = next((insight for insight in productivity if insight.label == label), None)
        return match.score if match else round(mean(insight.score for insight in productivity), 2) if productivity else 0

    @staticmethod
    def _actionability_score(
        request: MeetingAnalyzeRequest,
        action_items: list[MeetingActionItem],
        decisions: list[str],
        blockers: list[str],
    ) -> float:
        score = 22 + len(action_items) * 18 + len(decisions) * 16
        if blockers and action_items:
            score += 12
        score -= max(0, len(blockers) - len(action_items)) * 7
        score -= max(0, request.duration_minutes - 45) * 0.25
        return round(float(min(100, max(0, score))), 2)

    @staticmethod
    def _waste_percentage(
        *,
        request: MeetingAnalyzeRequest,
        productivity_score: float,
        efficiency_score: float,
        actionability_score: float,
        repeated_topic_rate: float,
        speakers: list[MeetingSpeakerAnalytics],
        blockers: list[str],
        decisions: list[str],
        action_items: list[MeetingActionItem],
    ) -> float:
        participation_std = pstdev([speaker.participation_percent for speaker in speakers]) if len(speakers) > 1 else 0
        dominant_penalty = sum(1 for speaker in speakers if speaker.participation_flag == "dominant") * 7
        silent_penalty = sum(1 for speaker in speakers if speaker.participation_flag == "silent") * 4
        waste = (
            (100 - productivity_score) * 0.36
            + (100 - efficiency_score) * 0.22
            + (100 - actionability_score) * 0.16
            + repeated_topic_rate * 0.36
            + max(0, request.duration_minutes - 35) * 0.38
            + participation_std * 0.16
            + len(blockers) * 2.8
            + dominant_penalty
            + silent_penalty
        )
        if not decisions:
            waste += 10
        if not action_items:
            waste += 9
        if len(decisions) >= 2 and len(action_items) >= 2:
            waste -= 10
        return round(float(min(100, max(0, waste))), 2)

    @staticmethod
    def _waste_economics(
        request: MeetingAnalyzeRequest,
        speakers: list[MeetingSpeakerAnalytics],
        waste_percentage: float,
    ) -> MeetingWasteEconomics:
        participant_count = request.participant_count or max(len(speakers), 1)
        employee_hours = request.duration_minutes / 60 * participant_count
        wasted_hours = employee_hours * waste_percentage / 100
        meeting_cost = employee_hours * request.average_hourly_cost
        wasted_cost = wasted_hours * request.average_hourly_cost
        opportunity_cost = wasted_cost * 1.35
        return MeetingWasteEconomics(
            participant_count=participant_count,
            average_hourly_cost=round(request.average_hourly_cost, 2),
            employee_hours_spent=round(employee_hours, 2),
            wasted_hours=round(wasted_hours, 2),
            meeting_cost=round(meeting_cost, 2),
            wasted_cost=round(wasted_cost, 2),
            opportunity_cost=round(opportunity_cost, 2),
            weekly_waste_hours_estimate=round(wasted_hours * request.weekly_recurrence, 2),
            weekly_waste_cost_estimate=round(wasted_cost * request.weekly_recurrence, 2),
        )

    @staticmethod
    def _overload_analytics(
        request: MeetingAnalyzeRequest,
        nlp_results,
        waste_percentage: float,
        speakers: list[MeetingSpeakerAnalytics],
    ) -> MeetingOverloadAnalytics:
        stress = (
            mean(
                max(result.emotion_scores.stress, result.emotion_scores.burnout * 0.72, result.emotion_scores.emotional_exhaustion)
                for result in nlp_results
            )
            if nlp_results
            else 0
        )
        participant_count = request.participant_count or max(len(speakers), 1)
        meeting_load = min(100, request.duration_minutes * 0.72 + participant_count * 1.8 + waste_percentage * 0.34 + stress * 24)
        overload_percent = max(0, meeting_load - 52)
        productivity_drag = min(100, waste_percentage * 0.32 + max(0, request.duration_minutes - 30) * 0.14 + stress * 11)
        reduction = max(0, min(request.duration_minutes * 0.45, request.duration_minutes * waste_percentage / 180))
        return MeetingOverloadAnalytics(
            department=request.department,
            meeting_load_score=round(float(meeting_load), 2),
            overload_percent=round(float(overload_percent), 2),
            burnout_correlation=round(float(min(1, stress * 0.68 + waste_percentage / 250)), 3),
            productivity_drag_percent=round(float(productivity_drag), 2),
            recommended_reduction_minutes=round(float(reduction), 1),
            forecast=(
                f"{request.department} meeting load is modeled at {round(meeting_load)}%; "
                f"cutting {round(reduction)} minutes or moving repeated status updates async should reduce productivity drag by about {round(productivity_drag * 0.42)}%."
            ),
        )

    @staticmethod
    def _necessity_assessment(
        *,
        request: MeetingAnalyzeRequest,
        decisions: list[str],
        action_items: list[MeetingActionItem],
        blockers: list[str],
        topic_clusters: list[MeetingTopicCluster],
        speakers: list[MeetingSpeakerAnalytics],
        productivity_score: float,
        waste_percentage: float,
        repeated_topic_rate: float,
    ) -> MeetingNecessityAssessment:
        participation_std = pstdev([speaker.participation_percent for speaker in speakers]) if len(speakers) > 1 else 0
        unresolved_topics = [cluster for cluster in topic_clusters if cluster.unresolved]
        signals = [
            f"{len(decisions)} explicit decision(s)",
            f"{len(action_items)} action item(s)",
            f"{round(repeated_topic_rate)}% repeated-topic rate",
            f"{round(waste_percentage)}% modeled waste",
            f"{round(participation_std)} point speaking-time spread",
            f"{len(blockers)} blocker signal(s)",
        ]
        if waste_percentage >= 60 and len(decisions) <= 1 and len(action_items) <= 1:
            verdict = "could_have_been_email"
            rationale = (
                "This meeting could have been an email because decision density and action ownership were low while "
                "repetition, duration, and participation imbalance consumed live collaboration time."
            )
            async_recommendation = "Replace the next occurrence with a written status update, decision log, and owner-tagged blocker thread."
        elif waste_percentage >= 42 or repeated_topic_rate >= 24 or unresolved_topics:
            verdict = "async_preferred"
            rationale = (
                "Live discussion is only partially justified; repeated or unresolved topics should move into async pre-read and owner-driven decision tracking."
            )
            async_recommendation = "Keep a short decision huddle only for unresolved blockers and move status repetition into async notes."
        else:
            verdict = "synchronous_required"
            rationale = "The meeting produced enough decisions, action ownership, and cross-functional risk handling to justify synchronous time."
            async_recommendation = "Preserve the live meeting but keep pre-reads and action tracking asynchronous."
        confidence = min(0.98, max(0.58, 0.55 + abs(waste_percentage - 42) / 120 + len(topic_clusters) * 0.025 + productivity_score / 500))
        return MeetingNecessityAssessment(
            verdict=verdict,
            confidence=round(float(confidence), 3),
            rationale=rationale,
            signals=signals,
            async_recommendation=async_recommendation,
        )

    @staticmethod
    def _risk_signals(
        nlp_results,
        speakers: list[MeetingSpeakerAnalytics],
        blockers: list[str],
        request: MeetingAnalyzeRequest,
        topic_clusters: list[MeetingTopicCluster],
        waste_percentage: float,
        actionability_score: float,
    ) -> list[MeetingRiskSignal]:
        stress = (
            mean(
                max(
                    result.emotion_scores.stress,
                    result.emotion_scores.burnout * 0.72,
                    result.emotion_scores.emotional_exhaustion,
                )
                for result in nlp_results
            )
            if nlp_results
            else 0
        )
        toxicity = mean(result.emotion_scores.toxicity for result in nlp_results) if nlp_results else 0
        burnout = mean(result.emotion_scores.burnout for result in nlp_results) if nlp_results else 0
        imbalance = pstdev([speaker.participation_percent for speaker in speakers]) if len(speakers) > 1 else 0
        signals = [
            MeetingAnalyzerService._risk("stress", stress * 100, [speaker.speaker for speaker in speakers if speaker.stress_score >= 0.5], "Reduce meeting load and route high-stress owners to recovery blocks."),
            MeetingAnalyzerService._risk("toxicity", toxicity * 100, [speaker.speaker for speaker in speakers if speaker.toxicity_score >= 0.35], "Use manager mediation and reset discussion norms."),
            MeetingAnalyzerService._risk("burnout", burnout * 100, [speaker.speaker for speaker in speakers if speaker.burnout_score >= 0.45], "Rebalance ownership away from burnout-risk speakers."),
            MeetingAnalyzerService._risk("blockers", min(100, len(blockers) * 18), blockers[:3], "Move blockers into a dependency room with named owners."),
            MeetingAnalyzerService._risk("participation_imbalance", min(100, imbalance * 2.2), [speaker.speaker for speaker in speakers if speaker.participation_flag != "balanced"], "Redistribute speaking time and explicitly ask quiet owners for risk updates."),
            MeetingAnalyzerService._risk("meeting_overload", min(100, max(0, request.duration_minutes - 35) * 2.5), [f"{request.duration_minutes:g} minute meeting"], "Compress recurring meetings and convert updates to async notes."),
            MeetingAnalyzerService._risk("topic_repetition", min(100, sum(cluster.semantic_repetition_score for cluster in topic_clusters) / max(len(topic_clusters), 1)), [cluster.label for cluster in topic_clusters[:3]], "Convert repeated topics into an async decision register with explicit owners and resolution dates."),
            MeetingAnalyzerService._risk("meeting_waste", waste_percentage, [f"{waste_percentage}% modeled waste", f"{actionability_score}% actionability"], "Cancel or shorten low-actionability meetings and require async pre-reads for status topics."),
        ]
        return [signal for signal in signals if signal.score >= 18]

    @staticmethod
    def _risk(category: str, score: float, evidence: list[str], recommendation: str) -> MeetingRiskSignal:
        bounded = round(min(100, max(0, score)), 2)
        if bounded >= 82:
            severity = "critical"
        elif bounded >= 64:
            severity = "high"
        elif bounded >= 38:
            severity = "medium"
        else:
            severity = "low"
        return MeetingRiskSignal(category=category, severity=severity, score=bounded, evidence=evidence[:5], recommendation=recommendation)

    @staticmethod
    def _recommendations(
        productivity: list[MeetingProductivityInsight],
        risks: list[MeetingRiskSignal],
        action_items: list[MeetingActionItem],
        speakers: list[MeetingSpeakerAnalytics],
        necessity: MeetingNecessityAssessment,
        topic_clusters: list[MeetingTopicCluster],
        waste_economics: MeetingWasteEconomics,
    ) -> list[str]:
        recommendations = [insight.recommendation for insight in productivity if insight.score < 72]
        recommendations.extend(risk.recommendation for risk in risks if risk.severity in {"high", "critical"})
        if necessity.verdict == "could_have_been_email":
            recommendations.append(necessity.async_recommendation)
        elif necessity.verdict == "async_preferred":
            recommendations.append("Split the meeting into async status updates plus a short blocker-resolution huddle.")
        if topic_clusters:
            recommendations.append(f"Resolve repeated topic '{topic_clusters[0].label}' outside the next live meeting.")
        if waste_economics.wasted_cost >= 500:
            recommendations.append(f"Reduce recurrence or attendance; modeled weekly waste is ${round(waste_economics.weekly_waste_cost_estimate):,}.")
        if not action_items:
            recommendations.append("Capture explicit action owners and deadlines before the meeting ends.")
        if any(speaker.participation_flag == "silent" for speaker in speakers):
            recommendations.append("Ask low-participation speakers for blockers and ownership confirmation.")
        return list(dict.fromkeys(recommendations))[:7]

    @staticmethod
    def _summary(
        nlp_results,
        speakers: list[MeetingSpeakerAnalytics],
        productivity: list[MeetingProductivityInsight],
        action_items: list[MeetingActionItem],
        blockers: list[str],
        efficiency_score: float,
        actionability_score: float,
        repeated_topic_rate: float,
        waste_percentage: float,
        waste_economics: MeetingWasteEconomics,
    ) -> MeetingAnalysisSummary:
        sentiment = mean(result.sentiment_score for result in nlp_results) if nlp_results else 0
        stress = (
            mean(
                max(
                    result.emotion_scores.stress,
                    result.emotion_scores.burnout * 0.72,
                    result.emotion_scores.emotional_exhaustion,
                )
                for result in nlp_results
            )
            if nlp_results
            else 0
        )
        toxicity = mean(result.emotion_scores.toxicity for result in nlp_results) if nlp_results else 0
        burnout = mean(result.emotion_scores.burnout for result in nlp_results) if nlp_results else 0
        imbalance = pstdev([speaker.participation_percent for speaker in speakers]) if len(speakers) > 1 else 0
        productivity_score = mean(insight.score for insight in productivity) if productivity else 0
        return MeetingAnalysisSummary(
            sentiment_score=round(sentiment, 3),
            stress_index=round(stress, 3),
            toxicity_index=round(toxicity, 3),
            burnout_index=round(burnout, 3),
            participation_imbalance=round(min(100, imbalance * 2.2), 2),
            productivity_score=round(productivity_score, 2),
            efficiency_score=round(efficiency_score, 2),
            waste_percentage=round(waste_percentage, 2),
            actionability_score=round(actionability_score, 2),
            repeated_topic_rate=round(repeated_topic_rate, 2),
            estimated_waste_hours=waste_economics.wasted_hours,
            estimated_waste_cost=waste_economics.wasted_cost,
            action_item_count=len(action_items),
            blocker_count=len(blockers),
        )

    @staticmethod
    def _summary_text(
        request: MeetingAnalyzeRequest,
        key_points: list[str],
        decisions: list[str],
        action_items: list[MeetingActionItem],
        blockers: list[str],
        summary: MeetingAnalysisSummary,
    ) -> str:
        anchor = key_points[0] if key_points else f"{request.title} covered operational updates."
        decision_text = decisions[0] if decisions else "No explicit decision was captured."
        action_text = (
            f"{action_items[0].owner} owns {action_items[0].task}"
            if action_items
            else "Action ownership remains unclear"
        )
        blocker_text = f"{len(blockers)} blockers were detected" if blockers else "No major blocker was detected"
        return (
            f"{request.title}: {anchor} {decision_text} {action_text}. "
            f"{blocker_text}; productivity score {round(summary.productivity_score)}/100, "
            f"waste {round(summary.waste_percentage)}%, repeated topics {round(summary.repeated_topic_rate)}%, "
            f"and stress index {round(summary.stress_index * 100)}%."
        )

    @staticmethod
    def _title_name(value: str) -> str:
        return " ".join(part.capitalize() for part in value.strip().split())

    @staticmethod
    def _split_deadline(task: str, deadline: str | None) -> tuple[str, str | None]:
        cleaned = MeetingAnalyzerService._clean_task(task)
        found_deadline = MeetingAnalyzerService._normalize_deadline(deadline)
        if found_deadline:
            return cleaned, found_deadline
        deadline_match = re.search(
            r"(?P<head>.*?)(?:\s+(?:by|before|on)\s+(?P<deadline>Friday|Monday|Tuesday|Wednesday|Thursday|today|tomorrow|next week|end of week|EOW))(?:\s+and\s+(?P<tail>.*))?$",
            cleaned,
            flags=re.IGNORECASE,
        )
        if not deadline_match:
            return cleaned, None
        head = deadline_match.group("head").strip()
        tail = (deadline_match.group("tail") or "").strip()
        task_without_deadline = f"{head} and {tail}" if tail else head
        return MeetingAnalyzerService._clean_task(task_without_deadline), MeetingAnalyzerService._normalize_deadline(deadline_match.group("deadline"))

    @staticmethod
    def _clean_task(task: str) -> str:
        cleaned = re.sub(r"\s+", " ", task).strip(" .")
        cleaned = re.sub(r"^(to|the)\s+", "", cleaned, flags=re.IGNORECASE)
        return cleaned[:180]

    @staticmethod
    def _normalize_deadline(value: str | None) -> str | None:
        if not value:
            return None
        normalized = value.strip()
        return "end of week" if normalized.lower() == "eow" else normalized

    @staticmethod
    def _append_jsonl(payload: dict[str, object]) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with HISTORY_PATH.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, default=str) + "\n")


meeting_analyzer_service = MeetingAnalyzerService()
