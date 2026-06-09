from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from threading import Lock

import numpy as np

from app.ai.communication_engine import communication_quality_engine
from app.core.cache import TTLResponseCache
from app.schemas.communication import (
    CommunicationAlert,
    CommunicationInteractionSignal,
    CommunicationMessage,
    CommunicationPriority,
    CommunicationRecommendation,
    CommunicationRequest,
    CommunicationResponse,
    CommunicationSummary,
    ConflictForecast,
    InteractionGraphEdge,
    IsolationRiskInsight,
    MessageRiskInsight,
    TeamCommunicationHeatmapPoint,
)
from app.schemas.nlp import NLPAnalyzeRequest
from app.services.nlp_service import nlp_service


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
HISTORY_PATH = DATA_DIR / "communication_quality_history.jsonl"


class CommunicationQualityService:
    model_name = "PyTorch TextEmotionNet + TF-IDF Communication Risk Ensemble"

    def __init__(self) -> None:
        self._default_cache: TTLResponseCache[CommunicationResponse] = TTLResponseCache(ttl_seconds=8)
        self._lock = Lock()
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def analyze(self, payload: CommunicationRequest | None = None) -> CommunicationResponse:
        if payload is None:
            return self._default_cache.get_or_set(self._analyze_default_uncached)
        return self._analyze_uncached(payload)

    def _analyze_default_uncached(self) -> CommunicationResponse:
        return self._analyze_uncached(self.default_request())

    def _analyze_uncached(self, payload: CommunicationRequest) -> CommunicationResponse:
        request = payload if payload.messages else payload.model_copy(update={"messages": self.default_request().messages, "interactions": self.default_request().interactions})
        message_risks = [self._message_risk(message) for message in request.messages]
        graph = [self._interaction_edge(interaction) for interaction in request.interactions]
        heatmap = self._heatmap(request, message_risks, graph)
        conflicts = self._conflict_forecasts(heatmap, request.horizon_days)
        isolation = self._isolation_risks(request.interactions)
        recommendations = self._recommendations(message_risks, graph, heatmap, isolation)
        alerts = self._alerts(message_risks, heatmap, isolation)
        response = CommunicationResponse(
            model=self.model_name,
            generated_at=datetime.now(timezone.utc),
            cycle_name=request.cycle_name,
            horizon_days=request.horizon_days,
            message_risks=sorted(message_risks, key=lambda item: item.conflict_escalation_score, reverse=True),
            team_heatmap=sorted(heatmap, key=lambda item: max(item.toxicity_risk, item.conflict_probability, item.isolation_risk), reverse=True),
            interaction_graph=sorted(graph, key=lambda item: item.conflict_probability, reverse=True),
            conflict_forecasts=sorted(conflicts, key=lambda item: item.conflict_probability, reverse=True),
            isolation_risks=sorted(isolation, key=lambda item: item.isolation_risk, reverse=True),
            recommendations=recommendations,
            alerts=alerts,
            executive_insights=self._executive_insights(message_risks, heatmap, graph, isolation),
            summary=self._summary(message_risks, graph, heatmap, isolation),
            source_systems=["pytorch_text_emotion_net", "tfidf_toxicity_classifier", "random_forest_aggression_classifier", "behavioral_interaction_graph", "conflict_forecaster"],
            storage=str(HISTORY_PATH),
        )
        self._append_jsonl(response.model_dump(mode="json"))
        return response

    async def stream(self, payload: CommunicationRequest | None = None):
        base = payload or self.default_request()
        scenarios = [
            base,
            self._scenario_variant(base, conflict_delta=1, sentiment_delta=-0.08, response_delay_factor=1.18),
            self._scenario_variant(base, conflict_delta=2, sentiment_delta=-0.16, response_delay_factor=1.36),
        ]
        for sequence, scenario in enumerate(scenarios, start=1):
            response = self.analyze(scenario)
            data = response.model_dump(mode="json")
            data["summary"]["stream_sequence"] = sequence
            yield f"event: communication_quality\ndata: {json.dumps(data)}\n\n"
            await asyncio.sleep(0.8)

    @staticmethod
    def default_request() -> CommunicationRequest:
        messages = [
            CommunicationMessage(
                message_id="comm-001",
                employee_id="eng-lead",
                employee_name="Aarav Mehta",
                department="Engineering",
                team="Backend Platform",
                channel="review",
                thread_id="release-api",
                text="This API migration keeps breaking and the review is becoming frustrating. We are repeating the same blocker without a clear owner.",
                response_delay_minutes=145,
                expected_response_minutes=45,
                unresolved=True,
                recipient_ids=["qa-lead", "devops-lead"],
            ),
            CommunicationMessage(
                message_id="comm-002",
                employee_id="qa-lead",
                employee_name="Rina Shah",
                department="Engineering",
                team="Quality",
                channel="chat",
                thread_id="release-api",
                text="The tone in the release thread is tense, but QA can help isolate the regression if ownership is clarified.",
                response_delay_minutes=38,
                expected_response_minutes=60,
                recipient_ids=["eng-lead"],
            ),
            CommunicationMessage(
                message_id="comm-003",
                employee_id="ops-manager",
                employee_name="Omar Singh",
                department="Operations",
                team="Incident Response",
                channel="meeting",
                thread_id="incident-review",
                text="Stop making excuses. This handoff is unacceptable and the team keeps blaming others instead of fixing the incident.",
                response_delay_minutes=12,
                expected_response_minutes=30,
                unresolved=True,
                recipient_ids=["eng-lead", "devops-lead"],
            ),
            CommunicationMessage(
                message_id="comm-004",
                employee_id="design-partner",
                employee_name="Maya Iyer",
                department="Experience",
                team="Design Systems",
                channel="email",
                thread_id="design-copy",
                text="I have not heard back on the design review for days, and the conversation has become silent despite repeated follow ups.",
                response_delay_minutes=380,
                expected_response_minutes=90,
                unresolved=True,
                recipient_ids=["product-owner"],
            ),
            CommunicationMessage(
                message_id="comm-005",
                employee_id="product-owner",
                employee_name="Devika Nair",
                department="Product",
                team="AI Products",
                channel="ticket",
                thread_id="design-copy",
                text="Thanks for the review. The dashboard copy feedback is clear and I will update the ticket before standup.",
                response_delay_minutes=22,
                expected_response_minutes=120,
                recipient_ids=["design-partner"],
            ),
        ]
        interactions = [
            CommunicationInteractionSignal(source_id="eng-lead", source_name="Aarav Mehta", target_id="qa-lead", target_name="Rina Shah", department="Engineering", team="Release Squad", messages_sent=34, messages_received=28, average_response_minutes=82, baseline_response_minutes=45, collaboration_frequency=0.62, sentiment_alignment=0.36, conflict_incidents=3, unanswered_threads=2, participation_delta=-0.14),
            CommunicationInteractionSignal(source_id="ops-manager", source_name="Omar Singh", target_id="eng-lead", target_name="Aarav Mehta", department="Operations", team="Incident Response", messages_sent=26, messages_received=18, average_response_minutes=96, baseline_response_minutes=40, collaboration_frequency=0.48, sentiment_alignment=0.18, conflict_incidents=5, unanswered_threads=3, participation_delta=-0.2),
            CommunicationInteractionSignal(source_id="design-partner", source_name="Maya Iyer", target_id="product-owner", target_name="Devika Nair", department="Experience", team="Product Design", messages_sent=14, messages_received=4, average_response_minutes=310, baseline_response_minutes=75, collaboration_frequency=0.28, sentiment_alignment=0.42, conflict_incidents=1, unanswered_threads=6, participation_delta=-0.46),
            CommunicationInteractionSignal(source_id="product-owner", source_name="Devika Nair", target_id="design-partner", target_name="Maya Iyer", department="Product", team="AI Products", messages_sent=18, messages_received=20, average_response_minutes=36, baseline_response_minutes=70, collaboration_frequency=0.78, sentiment_alignment=0.76, conflict_incidents=0, unanswered_threads=0, participation_delta=0.05),
        ]
        return CommunicationRequest(
            cycle_name="Realtime Communication Quality Review",
            horizon_days=30,
            messages=messages,
            interactions=interactions,
        )

    def _message_risk(self, message: CommunicationMessage) -> MessageRiskInsight:
        nlp = nlp_service.analyze(
            NLPAnalyzeRequest(
                employee_id=message.employee_id,
                department=message.department,
                channel=message.channel,
                text=message.text,
            )
        )
        model = communication_quality_engine.predict_text(message.text)
        delay_pressure = self._response_delay_pressure(message.response_delay_minutes, message.expected_response_minutes)
        toxicity = float(np.clip(max(nlp.emotion_scores.toxicity * 100, model["toxicity_probability"] * 100), 0, 100))
        aggression = float(np.clip(model["aggression_probability"] * 70 + nlp.emotion_scores.frustration * 18 + nlp.emotion_scores.toxicity * 12, 0, 100))
        conflict = float(
            np.clip(
                model["conflict_probability"] * 54
                + aggression * 0.2
                + toxicity * 0.16
                + delay_pressure * 0.08
                + (12 if message.unresolved else 0),
                0,
                100,
            )
        )
        quality = float(np.clip(100 - toxicity * 0.26 - aggression * 0.22 - conflict * 0.24 - max(0, -nlp.sentiment_score) * 18 - delay_pressure * 0.1, 0, 100))
        evidence = [
            f"sentiment={nlp.sentiment} score={nlp.sentiment_score}",
            f"toxicity_model={round(model['toxicity_probability'] * 100)}%",
            f"aggression_model={round(model['aggression_probability'] * 100)}%",
            f"response_delay_pressure={round(delay_pressure)}%",
        ]
        if message.unresolved:
            evidence.append("thread unresolved")
        return MessageRiskInsight(
            message_id=message.message_id,
            employee_id=message.employee_id,
            employee_name=message.employee_name,
            department=message.department,
            team=message.team,
            channel=message.channel,
            sentiment=nlp.sentiment,
            primary_emotion=nlp.primary_emotion,
            sentiment_score=nlp.sentiment_score,
            toxicity_score=round(toxicity, 2),
            aggression_score=round(aggression, 2),
            conflict_escalation_score=round(conflict, 2),
            communication_quality_score=round(quality, 2),
            confidence=round(max(float(model["confidence"]), nlp.confidence), 3),
            evidence=evidence,
            recommendation=self._message_recommendation(toxicity, aggression, conflict, delay_pressure),
        )

    def _interaction_edge(self, interaction: CommunicationInteractionSignal) -> InteractionGraphEdge:
        response_pressure = self._response_delay_pressure(interaction.average_response_minutes, interaction.baseline_response_minutes)
        participation_balance = min(interaction.messages_sent, interaction.messages_received) / max(max(interaction.messages_sent, interaction.messages_received), 1)
        sentiment_alignment = np.clip((interaction.sentiment_alignment + 1) / 2 * 100, 0, 100)
        isolation = float(
            np.clip(
                max(0, -interaction.participation_delta) * 50
                + interaction.unanswered_threads * 7
                + response_pressure * 0.24
                + (1 - interaction.collaboration_frequency) * 26,
                0,
                100,
            )
        )
        conflict = float(
            np.clip(
                interaction.conflict_incidents * 11
                + (100 - sentiment_alignment) * 0.32
                + response_pressure * 0.18
                + (1 - interaction.collaboration_frequency) * 18,
                0,
                100,
            )
        )
        response_health = float(np.clip(100 - response_pressure, 0, 100))
        collaboration = float(
            np.clip(
                interaction.collaboration_frequency * 42
                + participation_balance * 20
                + sentiment_alignment * 0.22
                + response_health * 0.16
                - conflict * 0.12,
                0,
                100,
            )
        )
        return InteractionGraphEdge(
            source_id=interaction.source_id,
            source_name=interaction.source_name,
            target_id=interaction.target_id,
            target_name=interaction.target_name,
            department=interaction.department,
            team=interaction.team,
            collaboration_score=round(collaboration, 2),
            response_health=round(response_health, 2),
            sentiment_alignment=round(float(sentiment_alignment), 2),
            conflict_probability=round(conflict, 2),
            isolation_signal=round(isolation, 2),
            recommendation=self._edge_recommendation(conflict, isolation, collaboration),
        )

    def _heatmap(
        self,
        request: CommunicationRequest,
        messages: list[MessageRiskInsight],
        graph: list[InteractionGraphEdge],
    ) -> list[TeamCommunicationHeatmapPoint]:
        grouped_messages: dict[tuple[str, str], list[MessageRiskInsight]] = defaultdict(list)
        for message in messages:
            grouped_messages[(message.department, message.team)].append(message)
        grouped_edges: dict[tuple[str, str], list[InteractionGraphEdge]] = defaultdict(list)
        for edge in graph:
            grouped_edges[(edge.department, edge.team)].append(edge)
        keys = set(grouped_messages) | set(grouped_edges)
        heatmap: list[TeamCommunicationHeatmapPoint] = []
        for department, team in sorted(keys):
            rows = grouped_messages.get((department, team), [])
            edges = grouped_edges.get((department, team), [])
            toxicity = mean([row.toxicity_score for row in rows] or [0])
            conflict = max(mean([row.conflict_escalation_score for row in rows] or [0]), mean([edge.conflict_probability for edge in edges] or [0]))
            collaboration = mean([edge.collaboration_score for edge in edges] or [mean([row.communication_quality_score for row in rows] or [72])])
            isolation = mean([edge.isolation_signal for edge in edges] or [0])
            sentiment = mean([row.sentiment_score for row in rows] or [0])
            morale = float(np.clip(72 + sentiment * 22 - toxicity * 0.18 - conflict * 0.14 - isolation * 0.1 + collaboration * 0.08, 0, 100))
            heatmap.append(
                TeamCommunicationHeatmapPoint(
                    department=department,
                    team=team,
                    toxicity_risk=round(toxicity, 2),
                    morale_score=round(morale, 2),
                    collaboration_quality=round(collaboration, 2),
                    conflict_probability=round(conflict, 2),
                    isolation_risk=round(isolation, 2),
                    messages_analyzed=len(rows),
                    priority=self._priority(max(toxicity, conflict, isolation, 100 - morale)),
                )
            )
        return heatmap

    def _conflict_forecasts(self, heatmap: list[TeamCommunicationHeatmapPoint], horizon_days: int) -> list[ConflictForecast]:
        forecasts: list[ConflictForecast] = []
        for item in heatmap:
            base = max(item.conflict_probability, item.toxicity_risk * 0.72, item.isolation_risk * 0.65)
            trend = np.clip((100 - item.morale_score) * 0.035 + item.toxicity_risk * 0.018 + item.isolation_risk * 0.012, 0.2, 4.2)
            series = [round(float(np.clip(base + trend * step * horizon_days / 30, 0, 100)), 2) for step in range(1, 7)]
            drivers = []
            if item.toxicity_risk >= 45:
                drivers.append("elevated toxicity")
            if item.isolation_risk >= 45:
                drivers.append("interaction withdrawal")
            if item.collaboration_quality < 55:
                drivers.append("collaboration quality below threshold")
            if item.morale_score < 55:
                drivers.append("morale decline")
            forecasts.append(
                ConflictForecast(
                    department=item.department,
                    team=item.team,
                    conflict_probability=round(float(np.clip(series[-1], 0, 100)), 2),
                    projected_productivity_loss_hours=round(float(max(0, series[-1] - 35) * max(1, item.messages_analyzed) * 0.42), 2),
                    confidence=round(float(np.clip(0.68 + max(item.toxicity_risk, item.isolation_risk, item.conflict_probability) / 340, 0.68, 0.94)), 3),
                    drivers=drivers or ["normal interaction variance"],
                    forecast=series,
                )
            )
        return forecasts

    def _isolation_risks(self, interactions: list[CommunicationInteractionSignal]) -> list[IsolationRiskInsight]:
        by_employee: dict[tuple[str, str, str, str], list[CommunicationInteractionSignal]] = defaultdict(list)
        for interaction in interactions:
            by_employee[(interaction.source_id, interaction.source_name, interaction.department, interaction.team)].append(interaction)
            by_employee[(interaction.target_id, interaction.target_name, interaction.department, interaction.team)].append(interaction)
        risks: list[IsolationRiskInsight] = []
        for (employee_id, name, department, team), rows in by_employee.items():
            drop = mean([max(0, -row.participation_delta) * 100 for row in rows])
            delay = mean([self._response_delay_pressure(row.average_response_minutes, row.baseline_response_minutes) for row in rows])
            unanswered = int(sum(row.unanswered_threads for row in rows))
            frequency = mean([row.collaboration_frequency for row in rows])
            risk = float(np.clip(drop * 0.36 + delay * 0.24 + unanswered * 5.5 + (1 - frequency) * 34, 0, 100))
            if risk < 22 and unanswered == 0:
                continue
            risks.append(
                IsolationRiskInsight(
                    employee_id=employee_id,
                    employee_name=name,
                    department=department,
                    team=team,
                    isolation_risk=round(risk, 2),
                    interaction_drop=round(drop, 2),
                    response_delay_pressure=round(delay, 2),
                    unanswered_threads=unanswered,
                    recommendation="Re-establish explicit ownership, add a manager check-in, and rebalance discussion load." if risk >= 55 else "Monitor participation and clarify response expectations.",
                )
            )
        return risks

    def _recommendations(
        self,
        messages: list[MessageRiskInsight],
        graph: list[InteractionGraphEdge],
        heatmap: list[TeamCommunicationHeatmapPoint],
        isolation: list[IsolationRiskInsight],
    ) -> list[CommunicationRecommendation]:
        recommendations: list[CommunicationRecommendation] = []
        top_message = max(messages, key=lambda item: max(item.toxicity_score, item.aggression_score, item.conflict_escalation_score), default=None)
        if top_message and max(top_message.toxicity_score, top_message.aggression_score) >= 42:
            recommendations.append(
                CommunicationRecommendation(
                    title="De-escalate toxic communication pattern",
                    category="toxicity",
                    priority=self._priority(max(top_message.toxicity_score, top_message.aggression_score)),
                    impact_score=round(max(top_message.toxicity_score, top_message.aggression_score), 2),
                    action=f"Coach {top_message.employee_name} and moderate the {top_message.channel} thread before the next delivery review.",
                    rationale=top_message.recommendation,
                    confidence=top_message.confidence,
                )
            )
        weak_team = min(heatmap, key=lambda item: item.collaboration_quality, default=None)
        if weak_team and weak_team.collaboration_quality < 64:
            recommendations.append(
                CommunicationRecommendation(
                    title="Repair collaboration quality",
                    category="collaboration",
                    priority=self._priority(100 - weak_team.collaboration_quality),
                    impact_score=round(100 - weak_team.collaboration_quality, 2),
                    action=f"Run a structured decision review for {weak_team.department} / {weak_team.team} with clear owners and async summaries.",
                    rationale=f"Collaboration quality is {round(weak_team.collaboration_quality)} with conflict probability {round(weak_team.conflict_probability)}.",
                    confidence=0.82,
                )
            )
        top_isolation = max(isolation, key=lambda item: item.isolation_risk, default=None)
        if top_isolation and top_isolation.isolation_risk >= 38:
            recommendations.append(
                CommunicationRecommendation(
                    title="Reduce isolation risk",
                    category="isolation",
                    priority=self._priority(top_isolation.isolation_risk),
                    impact_score=top_isolation.isolation_risk,
                    action=f"Schedule a direct check-in for {top_isolation.employee_name} and assign a visible response owner.",
                    rationale=f"Interaction drop {round(top_isolation.interaction_drop)}%, response pressure {round(top_isolation.response_delay_pressure)}%, unanswered threads {top_isolation.unanswered_threads}.",
                    confidence=0.8,
                )
            )
        top_conflict = max(graph, key=lambda item: item.conflict_probability, default=None)
        if top_conflict and top_conflict.conflict_probability >= 45:
            recommendations.append(
                CommunicationRecommendation(
                    title="Prevent conflict escalation",
                    category="conflict",
                    priority=self._priority(top_conflict.conflict_probability),
                    impact_score=top_conflict.conflict_probability,
                    action=f"Separate decision ownership between {top_conflict.source_name} and {top_conflict.target_name}; use a neutral facilitator for high-pressure reviews.",
                    rationale=top_conflict.recommendation,
                    confidence=0.83,
                )
            )
        if not recommendations:
            recommendations.append(
                CommunicationRecommendation(
                    title="Maintain healthy communication norms",
                    category="morale",
                    priority="low",
                    impact_score=24,
                    action="Keep current review cadence and preserve async decision logs.",
                    rationale="No severe toxicity, conflict, or isolation signal crossed intervention thresholds.",
                    confidence=0.78,
                )
            )
        return recommendations[:6]

    def _alerts(
        self,
        messages: list[MessageRiskInsight],
        heatmap: list[TeamCommunicationHeatmapPoint],
        isolation: list[IsolationRiskInsight],
    ) -> list[CommunicationAlert]:
        alerts: list[CommunicationAlert] = []
        for message in messages[:4]:
            probability = max(message.toxicity_score, message.aggression_score, message.conflict_escalation_score)
            if probability >= 45:
                alerts.append(
                    CommunicationAlert(
                        title=f"{message.department} communication risk detected",
                        priority=self._priority(probability),
                        probability=round(probability, 2),
                        impact=f"{message.employee_name} message shows {round(message.toxicity_score)} toxicity, {round(message.aggression_score)} aggression, and {round(message.conflict_escalation_score)} conflict risk.",
                        recommendation=message.recommendation,
                    )
                )
        for item in heatmap[:3]:
            probability = max(item.conflict_probability, item.isolation_risk, item.toxicity_risk)
            if probability >= 45:
                alerts.append(
                    CommunicationAlert(
                        title=f"{item.team} morale heatmap warning",
                        priority=self._priority(probability),
                        probability=round(probability, 2),
                        impact=f"{item.department} / {item.team} morale is {round(item.morale_score)} with collaboration quality {round(item.collaboration_quality)}.",
                        recommendation="Review communication norms and rebalance decision ownership.",
                    )
                )
        for risk in isolation[:2]:
            if risk.isolation_risk >= 55:
                alerts.append(
                    CommunicationAlert(
                        title=f"{risk.employee_name} isolation risk",
                        priority=self._priority(risk.isolation_risk),
                        probability=risk.isolation_risk,
                        impact=f"Interaction drop {round(risk.interaction_drop)}% and {risk.unanswered_threads} unanswered thread(s).",
                        recommendation=risk.recommendation,
                    )
                )
        return alerts[:8]

    def _executive_insights(
        self,
        messages: list[MessageRiskInsight],
        heatmap: list[TeamCommunicationHeatmapPoint],
        graph: list[InteractionGraphEdge],
        isolation: list[IsolationRiskInsight],
    ) -> list[str]:
        insights: list[str] = []
        riskiest = max(messages, key=lambda item: item.conflict_escalation_score, default=None)
        if riskiest:
            insights.append(
                f"{riskiest.department} has the highest message-level escalation signal at {round(riskiest.conflict_escalation_score)}%, driven by {riskiest.primary_emotion} tone and response pressure."
            )
        weak = min(heatmap, key=lambda item: item.morale_score, default=None)
        if weak:
            insights.append(f"{weak.department} / {weak.team} morale heatmap is {round(weak.morale_score)} with {round(weak.conflict_probability)}% conflict probability.")
        pair = max(graph, key=lambda item: item.conflict_probability, default=None)
        if pair:
            insights.append(f"{pair.source_name} to {pair.target_name} is the highest-risk interaction edge at {round(pair.conflict_probability)}% conflict probability.")
        if isolation:
            top = max(isolation, key=lambda item: item.isolation_risk)
            insights.append(f"{top.employee_name} shows {round(top.isolation_risk)}% isolation risk from delayed responses and unanswered collaboration threads.")
        insights.append("Communication quality combines PyTorch emotion inference, TF-IDF toxicity/aggression classifiers, response-delay pressure, and interaction-graph behavior.")
        return insights

    def _summary(
        self,
        messages: list[MessageRiskInsight],
        graph: list[InteractionGraphEdge],
        heatmap: list[TeamCommunicationHeatmapPoint],
        isolation: list[IsolationRiskInsight],
    ) -> CommunicationSummary:
        return CommunicationSummary(
            messages_analyzed=len(messages),
            interactions_analyzed=len(graph),
            high_toxicity_alerts=sum(1 for message in messages if max(message.toxicity_score, message.aggression_score) >= 55),
            isolation_risks=sum(1 for item in isolation if item.isolation_risk >= 45),
            average_quality_score=round(mean([message.communication_quality_score for message in messages] or [0]), 2),
            average_collaboration_quality=round(mean([edge.collaboration_score for edge in graph] or [0]), 2),
            conflict_probability=round(mean([item.conflict_probability for item in heatmap] or [0]), 2),
            morale_score=round(mean([item.morale_score for item in heatmap] or [0]), 2),
        )

    @staticmethod
    def _message_recommendation(toxicity: float, aggression: float, conflict: float, delay_pressure: float) -> str:
        if max(toxicity, aggression) >= 65:
            return "Pause the thread, restate working norms, and route the discussion through a neutral manager."
        if conflict >= 55:
            return "Convert the conversation into a decision log with explicit owners and moderation."
        if delay_pressure >= 65:
            return "Clarify response expectations and assign a visible owner for pending questions."
        return "Maintain current cadence and continue constructive async updates."

    @staticmethod
    def _edge_recommendation(conflict: float, isolation: float, collaboration: float) -> str:
        if conflict >= 58:
            return "High-conflict edge; use neutral facilitation and separate approval authority."
        if isolation >= 58:
            return "Isolation edge; increase direct check-ins and response ownership."
        if collaboration < 50:
            return "Low collaboration edge; clarify dependency handoffs and expected response times."
        return "Interaction is stable; preserve current collaboration cadence."

    @staticmethod
    def _response_delay_pressure(actual: float, baseline: float) -> float:
        return float(np.clip((actual / max(baseline, 1) - 1) * 55, 0, 100))

    @staticmethod
    def _priority(score: float) -> CommunicationPriority:
        if score >= 78:
            return "critical"
        if score >= 58:
            return "high"
        if score >= 34:
            return "medium"
        return "low"

    def _scenario_variant(self, base: CommunicationRequest, conflict_delta: int, sentiment_delta: float, response_delay_factor: float) -> CommunicationRequest:
        source = base if base.messages else self.default_request()
        messages = []
        for message in source.messages:
            text = message.text
            if conflict_delta >= 2 and message.channel in {"review", "meeting"}:
                text = f"{text} The escalation is becoming more aggressive and trust is dropping."
            messages.append(
                message.model_copy(
                    update={
                        "text": text,
                        "response_delay_minutes": min(10080, message.response_delay_minutes * response_delay_factor),
                        "unresolved": message.unresolved or response_delay_factor > 1.25,
                    }
                )
            )
        interactions = [
            interaction.model_copy(
                update={
                    "conflict_incidents": min(100, interaction.conflict_incidents + conflict_delta),
                    "sentiment_alignment": max(-1, interaction.sentiment_alignment + sentiment_delta),
                    "average_response_minutes": min(10080, interaction.average_response_minutes * response_delay_factor),
                    "participation_delta": max(-1, interaction.participation_delta + sentiment_delta * 0.7),
                    "unanswered_threads": min(200, interaction.unanswered_threads + conflict_delta),
                }
            )
            for interaction in source.interactions
        ]
        return source.model_copy(update={"messages": messages, "interactions": interactions, "realtime": True})

    def _append_jsonl(self, payload: dict[str, object]) -> None:
        with self._lock:
            with HISTORY_PATH.open("a", encoding="utf-8") as file:
                file.write(json.dumps(payload) + "\n")


communication_quality_service = CommunicationQualityService()
