from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from threading import Lock

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.ai.client_satisfaction_engine import client_satisfaction_engine
from app.core.cache import TTLResponseCache
from app.schemas.client_satisfaction import (
    ClientAssistantRequest,
    ClientAssistantResponse,
    ClientAccountSignal,
    ClientEngagementAnalyticsPoint,
    ClientForecastPoint,
    ClientHealthHeatmapPoint,
    ClientOpportunityInsight,
    ClientPaymentRiskPoint,
    ClientProjectRiskPoint,
    ClientRecoveryRecommendation,
    ClientRiskPriority,
    ClientSatisfactionAlert,
    ClientSatisfactionPrediction,
    ClientSatisfactionRequest,
    ClientSatisfactionResponse,
    ClientSatisfactionSummary,
    CommunicationSentimentPoint,
    DeliveryRiskPoint,
)


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
HISTORY_PATH = DATA_DIR / "client_satisfaction_history.jsonl"


class ClientSatisfactionService:
    model_name = "Predictive Client Satisfaction AI System"
    source_systems = [
        "client_health_engine",
        "churn_prediction_engine",
        "payment_risk_engine",
        "project_risk_engine",
        "communication_intelligence_engine",
        "sentiment_analysis_engine",
        "client_recommendation_engine",
        "client_dashboard",
        "ai_client_assistant",
        "crm_engagement_analytics",
        "opportunity_detection_engine",
        "project_failure_prediction",
        "communication_quality_analyzer",
        "support_escalation_analytics",
        "delivery_quality_intelligence",
        "tfidf_client_sentiment_model",
        "random_forest_client_health_model",
        "gradient_boosting_churn_forecaster",
        "client_satisfaction_history_jsonl",
    ]

    def __init__(self) -> None:
        self._cache: TTLResponseCache[ClientSatisfactionResponse] = TTLResponseCache(ttl_seconds=8)
        self._lock = Lock()
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def predict(self, payload: ClientSatisfactionRequest | None = None) -> ClientSatisfactionResponse:
        if payload is None:
            return self._cache.get_or_set(self._default_uncached)
        return self._predict_uncached(payload)

    def _default_uncached(self) -> ClientSatisfactionResponse:
        return self._predict_uncached(self.default_request())

    def _predict_uncached(self, payload: ClientSatisfactionRequest) -> ClientSatisfactionResponse:
        request = payload if payload.clients else self.default_request()
        rows = [self._feature_row(client) for client in request.clients]
        model_predictions = client_satisfaction_engine.predict(rows)
        predictions = [
            self._client_prediction(request, client, row, model_prediction)
            for client, row, model_prediction in zip(request.clients, rows, model_predictions)
        ]
        predictions.sort(key=lambda item: (item.churn_risk, item.escalation_probability, item.revenue_at_risk), reverse=True)
        heatmap = self._heatmap(predictions)
        sentiment = self._sentiment_points(request.clients, predictions)
        delivery = self._delivery_risks(request.clients, predictions)
        payment = self._payment_risks(request.clients, predictions)
        project = self._project_risks(request.clients, predictions)
        engagement = self._engagement_analytics(request.clients, predictions)
        opportunities = self._opportunity_pipeline(request.clients, predictions)
        recommendations = self._recommendations(predictions)
        alerts = self._alerts(predictions)
        response = ClientSatisfactionResponse(
            model=client_satisfaction_engine.model_name,
            generated_at=datetime.now(timezone.utc),
            cycle_name=request.cycle_name,
            horizon_days=request.horizon_days,
            predictions=predictions,
            heatmap=heatmap,
            communication_sentiment=sentiment,
            delivery_risks=delivery,
            payment_risks=payment,
            project_risks=project,
            engagement_analytics=engagement,
            opportunity_pipeline=opportunities,
            recommendations=recommendations,
            alerts=alerts,
            executive_insights=self._executive_insights(predictions),
            supported_questions=self.supported_questions(),
            summary=self._summary(predictions),
            source_systems=self.source_systems,
            storage=str(HISTORY_PATH),
        )
        self._append_jsonl(response.model_dump(mode="json"))
        return response

    async def stream(self, payload: ClientSatisfactionRequest | None = None):
        base = payload or self.default_request()
        scenarios = [
            base,
            self._scenario_variant(base, delay_delta=1.5, sentiment_delta=-0.08, escalation_delta=1),
            self._scenario_variant(base, delay_delta=3.5, sentiment_delta=-0.18, escalation_delta=2),
        ]
        for sequence, scenario in enumerate(scenarios, start=1):
            response = self.predict(scenario)
            data = response.model_dump(mode="json")
            data["summary"]["stream_sequence"] = sequence
            yield f"event: client_satisfaction\ndata: {json.dumps(data)}\n\n"
            await asyncio.sleep(0.8)

    def ask(self, payload: ClientAssistantRequest | None = None) -> ClientAssistantResponse:
        request = payload or ClientAssistantRequest()
        analysis = self.predict()
        intent = self._assistant_intent(request.question)
        answer, cited_clients, evidence, actions, confidence = self._assistant_answer(intent, analysis)
        return ClientAssistantResponse(
            model="AI Client Relationship Intelligence Assistant",
            generated_at=datetime.now(timezone.utc),
            question=request.question,
            intent=intent,
            answer=answer,
            confidence=round(confidence, 3),
            cited_clients=cited_clients,
            cited_evidence=evidence,
            recommended_actions=actions,
            source_systems=self.source_systems,
            storage=str(HISTORY_PATH),
        )

    @staticmethod
    def supported_questions() -> list[str]:
        return [
            "Which clients may leave?",
            "Which clients may pay late?",
            "Show highest-risk accounts.",
            "Why is Client A unhappy?",
            "Which projects are at risk?",
            "Show upsell opportunities.",
            "What actions should customer success take this week?",
        ]

    @staticmethod
    def _assistant_intent(question: str) -> str:
        text = question.lower()
        if any(token in text for token in ["pay", "invoice", "collection", "late"]):
            return "payment"
        if any(token in text for token in ["project", "delivery", "fail", "budget", "delay"]):
            return "project"
        if any(token in text for token in ["unhappy", "sentiment", "tone", "frustrated", "complaint"]):
            return "sentiment"
        if any(token in text for token in ["upsell", "cross-sell", "expansion", "opportun"]):
            return "opportunity"
        if any(token in text for token in ["recommend", "action", "intervention", "what should"]):
            return "recommendation"
        if any(token in text for token in ["leave", "churn", "renewal"]):
            return "churn"
        if any(token in text for token in ["risk", "highest", "critical", "at risk"]):
            return "risk"
        return "summary"

    def _assistant_answer(
        self,
        intent: str,
        analysis: ClientSatisfactionResponse,
    ) -> tuple[str, list[str], list[str], list[str], float]:
        top = analysis.predictions[0]
        payment = analysis.payment_risks[0]
        project = analysis.project_risks[0]
        opportunity = analysis.opportunity_pipeline[0]
        sentiment = analysis.communication_sentiment[0]
        recommendation_actions = [item.action for item in analysis.recommendations[:3]]
        if intent == "payment":
            answer = (
                f"{payment.client_name} is the most likely late payer with {round(payment.payment_delay_risk)}% payment-delay risk, "
                f"{round(payment.predicted_delay_days)} predicted delay days, and {round(payment.collection_risk)}% collection risk."
            )
            return answer, [payment.client_name], [
                f"Overdue invoice exposure: {round(payment.overdue_invoice_amount):,}.",
                f"Payment priority: {payment.priority}.",
            ], recommendation_actions, 0.91
        if intent == "project":
            answer = (
                f"{project.project_name} for {project.client_name} is the highest project-risk account with "
                f"{round(project.project_failure_risk)}% failure risk. Primary cause: {project.primary_cause}."
            )
            return answer, [project.client_name], [
                f"Delay risk {round(project.delay_risk)}%.",
                f"Budget-overrun risk {round(project.budget_overrun_risk)}%.",
                f"Dissatisfaction risk {round(project.dissatisfaction_risk)}%.",
            ], recommendation_actions, 0.9
        if intent == "sentiment":
            answer = (
                f"{sentiment.client_name} has the weakest relationship tone: {sentiment.label} sentiment, "
                f"{round(sentiment.negativity_risk)}% negativity risk, and {round(sentiment.trust_risk)}% trust risk."
            )
            return answer, [sentiment.client_name], [
                "Email and meeting text are scored with TF-IDF semantic risk prototypes plus lexicon evidence.",
                f"Sentiment score: {sentiment.sentiment_score}.",
            ], recommendation_actions, 0.89
        if intent == "opportunity":
            answer = (
                f"{opportunity.client_name} has the strongest expansion opportunity: {opportunity.opportunity} at "
                f"{round(opportunity.probability)}% probability and {round(opportunity.potential_revenue):,} modeled revenue potential."
            )
            return answer, [opportunity.client_name], [opportunity.rationale, opportunity.recommended_action], recommendation_actions, 0.88
        if intent == "recommendation":
            answer = (
                f"Top action: {analysis.recommendations[0].action} "
                f"Expected impact: {analysis.recommendations[0].expected_impact}"
            )
            return answer, analysis.recommendations[0].affected_clients, [
                item.expected_impact for item in analysis.recommendations[:3]
            ], recommendation_actions, 0.9
        if intent == "churn":
            answer = (
                f"{top.client_name} is the most likely churn risk with {round(top.churn_risk)}% churn probability, "
                f"{round(top.renewal_probability)}% renewal probability, and {round(top.revenue_at_risk):,} revenue at risk."
            )
            return answer, [top.client_name], top.risk_drivers[:4], top.recovery_actions[:3], 0.92
        if intent == "risk":
            answer = (
                f"Highest-risk account is {top.client_name}: {round(top.churn_risk)}% churn, "
                f"{round(top.payment_delay_risk)}% payment-delay, {round(top.project_failure_risk)}% project-failure, "
                f"and {round(top.intervention_priority_score)}% intervention priority."
            )
            return answer, [top.client_name], top.risk_drivers[:5], top.recovery_actions[:3], 0.92
        answer = (
            f"Portfolio health is {round(analysis.summary.average_client_health_score)}% across "
            f"{analysis.summary.clients_analyzed} accounts. Revenue at risk is {round(analysis.summary.revenue_at_risk):,}, "
            f"payment-risk accounts: {analysis.summary.payment_risk_accounts}, project-risk accounts: {analysis.summary.project_risk_accounts}, "
            f"and expansion pipeline: {round(analysis.summary.opportunity_revenue):,}."
        )
        return answer, [analysis.summary.highest_risk_client, analysis.summary.best_upsell_client], analysis.executive_insights[:4], recommendation_actions, 0.88

    def _client_prediction(
        self,
        request: ClientSatisfactionRequest,
        client: ClientAccountSignal,
        row: dict[str, float],
        model_prediction: dict[str, float],
    ) -> ClientSatisfactionPrediction:
        sentiment = 1 - row["sentiment_negativity"] * 2
        communication_health = self._clip((1 - row["sentiment_negativity"]) * 64 + client.interaction_frequency * 22 + client.executive_sponsor_engagement * 14)
        delivery_health = self._clip(client.delivery_consistency * 44 + (1 - row["delay_pressure"]) * 24 + (1 - row["sla_pressure"]) * 16 + client.qa_pass_rate * 16)
        quality_risk = self._clip(row["bug_pressure"] * 34 + row["incident_pressure"] * 26 + row["rework_ratio"] * 22 + (1 - client.qa_pass_rate) * 32)
        trust_decline = self._clip(row["sentiment_negativity"] * 34 + row["delay_pressure"] * 20 + row["escalation_pressure"] * 24 + row["nps_decline"] * 18)
        renewal_risk = self._clip(model_prediction["churn_risk"] * 0.58 + row["renewal_pressure"] * 30 + row["feedback_risk"] * 12)
        health = self._clip(model_prediction["client_health_score"] * 0.66 + communication_health * 0.14 + delivery_health * 0.16 + (100 - quality_risk) * 0.04)
        dissatisfaction = self._clip(100 - health + trust_decline * 0.18 + row["feedback_risk"] * 13)
        churn = self._clip(model_prediction["churn_risk"] + max(0, renewal_risk - 55) * 0.14 + row["contract_value_pressure"] * 2)
        escalation = self._clip(model_prediction["escalation_probability"] + client.open_critical_issues * 0.8)
        payment_delay_risk = self._payment_delay_risk(client, row, churn)
        predicted_payment_delay_days = self._predicted_payment_delay_days(client, payment_delay_risk)
        invoice_collection_risk = self._clip(
            payment_delay_risk * 0.54
            + row["invoice_dispute_pressure"] * 24
            + row["overdue_invoice_pressure"] * 28
            + row["sentiment_negativity"] * 10
        )
        project_failure_risk = self._project_failure_risk(client, row, delivery_health, quality_risk, escalation)
        budget_overrun_risk = self._clip(row["rework_ratio"] * 32 + row["delay_pressure"] * 24 + row["incident_pressure"] * 16 + row["critical_issue_pressure"] * 18)
        engagement_score = self._engagement_score(client, row)
        opportunity_score = self._opportunity_score(client, row, health, churn)
        upsell_revenue_potential = client.contract_value * opportunity_score / 100 * 0.22
        intervention_priority = self._clip(max(churn, escalation, payment_delay_risk, project_failure_risk) * 0.72 + (100 - engagement_score) * 0.16 + row["contract_value_pressure"] * 12)
        revenue_at_risk = client.contract_value * max(churn, escalation * 0.72) / 100
        forecast = self._forecast(request.horizon_days, health, churn, escalation, delivery_health, row, model_prediction["confidence"])
        return ClientSatisfactionPrediction(
            client_id=client.client_id,
            client_name=client.client_name,
            industry=client.industry,
            account_tier=client.account_tier,
            project_name=client.project_name,
            client_health_score=round(health, 2),
            satisfaction_score=round(self._clip(100 - dissatisfaction * 0.72), 2),
            dissatisfaction_probability=round(dissatisfaction, 2),
            churn_risk=round(churn, 2),
            escalation_probability=round(escalation, 2),
            relationship_stability=round(self._clip(100 - max(churn, escalation) * 0.72 - trust_decline * 0.18), 2),
            communication_health=round(communication_health, 2),
            delivery_health=round(delivery_health, 2),
            quality_risk=round(quality_risk, 2),
            trust_decline=round(trust_decline, 2),
            renewal_risk=round(renewal_risk, 2),
            renewal_probability=round(self._clip(100 - renewal_risk + client.executive_sponsor_engagement * 5), 2),
            payment_delay_risk=round(payment_delay_risk, 2),
            predicted_payment_delay_days=round(predicted_payment_delay_days, 2),
            invoice_collection_risk=round(invoice_collection_risk, 2),
            project_failure_risk=round(project_failure_risk, 2),
            budget_overrun_risk=round(budget_overrun_risk, 2),
            client_dissatisfaction_risk=round(dissatisfaction, 2),
            engagement_score=round(engagement_score, 2),
            engagement_trend=self._engagement_trend(client, row),
            upsell_opportunity_score=round(opportunity_score, 2),
            upsell_revenue_potential=round(upsell_revenue_potential, 2),
            intervention_priority_score=round(intervention_priority, 2),
            revenue_at_risk=round(revenue_at_risk, 2),
            sentiment_label=self._sentiment_label(sentiment),
            confidence=round(float(model_prediction["confidence"]), 3),
            risk_drivers=self._risk_drivers(client, row, churn, escalation, trust_decline),
            recovery_actions=self._recovery_actions(client, churn, escalation, quality_risk, trust_decline),
            forecast=forecast,
        )

    def _feature_row(self, client: ClientAccountSignal) -> dict[str, float]:
        sentiment_score = self._communication_sentiment(client)
        sentiment_negativity = self._clip01((1 - sentiment_score) / 2)
        return {
            "delay_pressure": self._clip01(client.delivery_delay_days / 28),
            "missed_milestone_pressure": self._clip01(client.missed_milestones / 8),
            "sla_pressure": self._clip01(client.sla_breach_count / 8),
            "bug_pressure": self._clip01(client.bug_frequency),
            "incident_pressure": self._clip01(client.production_incidents / 8),
            "qa_quality": self._clip01(client.qa_pass_rate),
            "rework_ratio": self._clip01(client.rework_ratio),
            "issue_resolution_pressure": self._clip01(client.issue_resolution_hours / 120),
            "escalation_pressure": self._clip01(client.escalation_count / 7),
            "sentiment_negativity": sentiment_negativity,
            "interaction_decline": self._clip01(1 - client.interaction_frequency),
            "feedback_risk": self._clip01(1 - client.feedback_score),
            "nps_decline": self._clip01(max(0, -client.nps_delta) / 45),
            "renewal_pressure": self._clip01(max(0, 120 - client.renewal_days) / 120),
            "delivery_consistency": self._clip01(client.delivery_consistency),
            "sponsor_engagement": self._clip01(client.executive_sponsor_engagement),
            "critical_issue_pressure": self._clip01(client.open_critical_issues / 6),
            "contract_value_pressure": self._clip01(client.contract_value / 5000000),
            "payment_delay_pressure": self._clip01(client.average_payment_delay_days / max(client.payment_terms_days * 1.4, 1)),
            "overdue_invoice_pressure": self._clip01(client.overdue_invoice_amount / max(client.contract_value * 0.18, 1)),
            "invoice_dispute_pressure": self._clip01(client.invoice_dispute_count / 5),
            "meeting_absence_pressure": self._clip01(1 - client.meeting_attendance_rate),
            "email_latency_pressure": self._clip01(client.email_response_hours / 96),
            "usage_decline_pressure": self._clip01(1 - client.platform_usage_score),
            "feature_adoption_gap": self._clip01(1 - client.feature_adoption_score),
            "support_ticket_pressure": self._clip01(client.support_ticket_count / 35),
            "stakeholder_change_pressure": self._clip01(client.stakeholder_change_count / 5),
            "upsell_signal": self._clip01(client.upsell_signal_score),
            "expansion_budget_signal": self._clip01(client.expansion_budget_signal),
        }

    def _communication_sentiment(self, client: ClientAccountSignal) -> float:
        texts = [*client.meeting_transcripts, *client.email_threads]
        if not texts:
            return client.communication_sentiment
        joined = " ".join(texts).lower()
        negative_proto = (
            "frustrated disappointed delayed escalation unresolved breach missed trust angry unacceptable "
            "blocked waiting issue incident broken churn risk unhappy renewal concern"
        )
        positive_proto = (
            "satisfied clear delivered reliable trusted aligned proactive resolved improving confident "
            "appreciate partnership successful milestone quality"
        )
        try:
            matrix = TfidfVectorizer(ngram_range=(1, 2)).fit_transform([joined, negative_proto, positive_proto])
            negative_similarity = float(cosine_similarity(matrix[0], matrix[1])[0][0])
            positive_similarity = float(cosine_similarity(matrix[0], matrix[2])[0][0])
        except ValueError:
            negative_similarity = 0.0
            positive_similarity = 0.0
        lexicon_negative = sum(joined.count(token) for token in ["frustrated", "delay", "blocked", "unresolved", "breach", "angry", "unacceptable", "risk", "escalat"])
        lexicon_positive = sum(joined.count(token) for token in ["thanks", "clear", "resolved", "confident", "appreciate", "delivered", "stable", "trust"])
        lexical = np.clip((lexicon_positive - lexicon_negative) / 12, -1, 1)
        semantic = np.clip((positive_similarity - negative_similarity) * 2.4, -1, 1)
        return float(np.clip(client.communication_sentiment * 0.42 + semantic * 0.4 + lexical * 0.18, -1, 1))

    @staticmethod
    def _payment_delay_risk(client: ClientAccountSignal, row: dict[str, float], churn: float) -> float:
        return ClientSatisfactionService._clip(
            row["payment_delay_pressure"] * 30
            + row["overdue_invoice_pressure"] * 24
            + row["invoice_dispute_pressure"] * 18
            + row["feedback_risk"] * 10
            + row["sentiment_negativity"] * 8
            + row["renewal_pressure"] * 6
            + min(12, churn * 0.12)
            + (8 if client.account_tier in {"enterprise", "global"} and row["overdue_invoice_pressure"] > 0.2 else 0)
        )

    @staticmethod
    def _predicted_payment_delay_days(client: ClientAccountSignal, payment_delay_risk: float) -> float:
        return ClientSatisfactionService._clip(
            client.average_payment_delay_days * 0.72
            + payment_delay_risk * 0.28
            + client.invoice_dispute_count * 2.4
            + (client.overdue_invoice_amount / max(client.contract_value, 1)) * 45,
            upper=365,
        )

    @staticmethod
    def _project_failure_risk(
        client: ClientAccountSignal,
        row: dict[str, float],
        delivery_health: float,
        quality_risk: float,
        escalation: float,
    ) -> float:
        return ClientSatisfactionService._clip(
            (100 - delivery_health) * 0.34
            + quality_risk * 0.24
            + row["delay_pressure"] * 18
            + row["critical_issue_pressure"] * 16
            + row["missed_milestone_pressure"] * 14
            + escalation * 0.12
            + client.open_critical_issues * 1.5
        )

    @staticmethod
    def _engagement_score(client: ClientAccountSignal, row: dict[str, float]) -> float:
        return ClientSatisfactionService._clip(
            client.interaction_frequency * 18
            + client.executive_sponsor_engagement * 18
            + client.meeting_attendance_rate * 18
            + (1 - row["email_latency_pressure"]) * 14
            + client.platform_usage_score * 16
            + client.feature_adoption_score * 12
            + (1 - row["support_ticket_pressure"]) * 4
        )

    @staticmethod
    def _engagement_trend(client: ClientAccountSignal, row: dict[str, float]) -> str:
        pressure = row["meeting_absence_pressure"] + row["email_latency_pressure"] + row["usage_decline_pressure"] + row["support_ticket_pressure"]
        lift = client.platform_usage_score + client.feature_adoption_score + client.executive_sponsor_engagement
        if pressure >= 1.65 or client.interaction_frequency < 0.45:
            return "declining"
        if lift >= 2.2 and client.nps_delta >= 0:
            return "improving"
        return "stable"

    @staticmethod
    def _opportunity_score(client: ClientAccountSignal, row: dict[str, float], health: float, churn: float) -> float:
        return ClientSatisfactionService._clip(
            client.upsell_signal_score * 28
            + client.expansion_budget_signal * 26
            + client.feature_adoption_score * 16
            + client.platform_usage_score * 12
            + max(0, health - 45) * 0.24
            + max(0, 65 - churn) * 0.14
            + (8 if client.account_tier in {"enterprise", "global"} else 3)
            - row["escalation_pressure"] * 8
            - row["payment_delay_pressure"] * 6
        )

    @staticmethod
    def _forecast(
        horizon_days: int,
        health: float,
        churn: float,
        escalation: float,
        delivery_health: float,
        row: dict[str, float],
        confidence: float,
    ) -> list[ClientForecastPoint]:
        points: list[ClientForecastPoint] = []
        pressure = row["delay_pressure"] * 5 + row["sentiment_negativity"] * 4 + row["escalation_pressure"] * 5 + row["critical_issue_pressure"] * 3
        for index in range(6):
            day = max(1, round((index + 1) * horizon_days / 6))
            drift = index * pressure
            future_health = ClientSatisfactionService._clip(health - drift + row["sponsor_engagement"] * index * 1.1)
            future_churn = ClientSatisfactionService._clip(churn + drift * 0.78 + row["renewal_pressure"] * index * 1.9)
            future_escalation = ClientSatisfactionService._clip(escalation + drift * 0.92)
            future_delivery = ClientSatisfactionService._clip(delivery_health - row["delay_pressure"] * index * 2.8 - row["sla_pressure"] * index * 1.9)
            points.append(
                ClientForecastPoint(
                    day=day,
                    client_health_score=round(future_health, 2),
                    churn_risk=round(future_churn, 2),
                    escalation_probability=round(future_escalation, 2),
                    delivery_confidence=round(future_delivery, 2),
                    confidence=round(ClientSatisfactionService._clip01(confidence - index * 0.02), 3),
                )
            )
        return points

    def _heatmap(self, predictions: list[ClientSatisfactionPrediction]) -> list[ClientHealthHeatmapPoint]:
        points: list[ClientHealthHeatmapPoint] = []
        for prediction in predictions:
            metrics = {
                "Client-health dashboard": 100 - prediction.client_health_score,
                "Satisfaction heatmaps": prediction.dissatisfaction_probability,
                "Churn-risk visualizations": prediction.churn_risk,
                "Escalation-warning panels": prediction.escalation_probability,
                "Delivery-risk analytics": 100 - prediction.delivery_health,
                "Communication-sentiment graphs": 100 - prediction.communication_health,
            }
            for metric, risk in metrics.items():
                points.append(
                    ClientHealthHeatmapPoint(
                        client_name=prediction.client_name,
                        metric=metric,
                        score=round(self._clip(risk), 2),
                        priority=self._severity(risk),
                    )
                )
        return sorted(points, key=lambda item: item.score, reverse=True)[:28]

    def _sentiment_points(
        self,
        clients: list[ClientAccountSignal],
        predictions: list[ClientSatisfactionPrediction],
    ) -> list[CommunicationSentimentPoint]:
        prediction_by_id = {prediction.client_id: prediction for prediction in predictions}
        points: list[CommunicationSentimentPoint] = []
        for client in clients:
            sentiment = self._communication_sentiment(client)
            prediction = prediction_by_id[client.client_id]
            negativity = self._clip((1 - sentiment) * 50)
            points.append(
                CommunicationSentimentPoint(
                    client_name=client.client_name,
                    label=prediction.sentiment_label,
                    sentiment_score=round(sentiment, 3),
                    negativity_risk=round(negativity, 2),
                    trust_risk=prediction.trust_decline,
                )
            )
        return sorted(points, key=lambda item: item.negativity_risk, reverse=True)

    @staticmethod
    def _delivery_risks(
        clients: list[ClientAccountSignal],
        predictions: list[ClientSatisfactionPrediction],
    ) -> list[DeliveryRiskPoint]:
        prediction_by_id = {prediction.client_id: prediction for prediction in predictions}
        points: list[DeliveryRiskPoint] = []
        for client in clients:
            prediction = prediction_by_id[client.client_id]
            points.append(
                DeliveryRiskPoint(
                    client_name=client.client_name,
                    delay_risk=round(ClientSatisfactionService._clip(client.delivery_delay_days / 28 * 100 + client.missed_milestones * 4), 2),
                    sla_risk=round(ClientSatisfactionService._clip(client.sla_breach_count * 12 + client.open_critical_issues * 4), 2),
                    quality_risk=prediction.quality_risk,
                    issue_resolution_risk=round(ClientSatisfactionService._clip(client.issue_resolution_hours / 120 * 100), 2),
                )
            )
        return sorted(points, key=lambda item: max(item.delay_risk, item.sla_risk, item.quality_risk), reverse=True)

    @staticmethod
    def _payment_risks(
        clients: list[ClientAccountSignal],
        predictions: list[ClientSatisfactionPrediction],
    ) -> list[ClientPaymentRiskPoint]:
        prediction_by_id = {prediction.client_id: prediction for prediction in predictions}
        points: list[ClientPaymentRiskPoint] = []
        for client in clients:
            prediction = prediction_by_id[client.client_id]
            points.append(
                ClientPaymentRiskPoint(
                    client_name=client.client_name,
                    payment_delay_risk=prediction.payment_delay_risk,
                    predicted_delay_days=prediction.predicted_payment_delay_days,
                    collection_risk=prediction.invoice_collection_risk,
                    overdue_invoice_amount=round(client.overdue_invoice_amount, 2),
                    priority=ClientSatisfactionService._severity(max(prediction.payment_delay_risk, prediction.invoice_collection_risk)),
                )
            )
        return sorted(points, key=lambda item: max(item.payment_delay_risk, item.collection_risk, item.predicted_delay_days), reverse=True)

    @staticmethod
    def _project_risks(
        clients: list[ClientAccountSignal],
        predictions: list[ClientSatisfactionPrediction],
    ) -> list[ClientProjectRiskPoint]:
        prediction_by_id = {prediction.client_id: prediction for prediction in predictions}
        points: list[ClientProjectRiskPoint] = []
        for client in clients:
            prediction = prediction_by_id[client.client_id]
            delay_risk = ClientSatisfactionService._clip(client.delivery_delay_days / 28 * 100 + client.missed_milestones * 4)
            cause = "Resource and milestone instability"
            if client.open_critical_issues >= 2:
                cause = "Open critical issues"
            elif prediction.quality_risk >= 55:
                cause = "Quality and rework pressure"
            elif client.delivery_delay_days >= 10:
                cause = "Delivery timeline slippage"
            elif prediction.communication_health < 55:
                cause = "Client communication breakdown"
            points.append(
                ClientProjectRiskPoint(
                    client_name=client.client_name,
                    project_name=client.project_name,
                    project_failure_risk=prediction.project_failure_risk,
                    delay_risk=round(delay_risk, 2),
                    budget_overrun_risk=prediction.budget_overrun_risk,
                    dissatisfaction_risk=prediction.client_dissatisfaction_risk,
                    primary_cause=cause,
                    priority=ClientSatisfactionService._severity(
                        max(prediction.project_failure_risk, prediction.budget_overrun_risk, prediction.client_dissatisfaction_risk)
                    ),
                )
            )
        return sorted(points, key=lambda item: max(item.project_failure_risk, item.delay_risk, item.dissatisfaction_risk), reverse=True)

    @staticmethod
    def _engagement_analytics(
        clients: list[ClientAccountSignal],
        predictions: list[ClientSatisfactionPrediction],
    ) -> list[ClientEngagementAnalyticsPoint]:
        prediction_by_id = {prediction.client_id: prediction for prediction in predictions}
        points: list[ClientEngagementAnalyticsPoint] = []
        for client in clients:
            prediction = prediction_by_id[client.client_id]
            points.append(
                ClientEngagementAnalyticsPoint(
                    client_name=client.client_name,
                    engagement_score=prediction.engagement_score,
                    trend=prediction.engagement_trend,
                    meeting_participation=round(client.meeting_attendance_rate * 100, 2),
                    email_responsiveness=round(ClientSatisfactionService._clip(100 - client.email_response_hours / 96 * 100), 2),
                    platform_usage=round(client.platform_usage_score * 100, 2),
                    feature_adoption=round(client.feature_adoption_score * 100, 2),
                    support_pressure=round(ClientSatisfactionService._clip(client.support_ticket_count / 35 * 100), 2),
                )
            )
        return sorted(points, key=lambda item: item.engagement_score)

    @staticmethod
    def _opportunity_pipeline(
        clients: list[ClientAccountSignal],
        predictions: list[ClientSatisfactionPrediction],
    ) -> list[ClientOpportunityInsight]:
        prediction_by_id = {prediction.client_id: prediction for prediction in predictions}
        opportunities: list[ClientOpportunityInsight] = []
        for client in clients:
            prediction = prediction_by_id[client.client_id]
            opportunity = "Advanced Analytics Package"
            if client.industry.lower().startswith("financial"):
                opportunity = "Risk Intelligence Expansion"
            elif "health" in client.industry.lower():
                opportunity = "Patient Operations AI Add-on"
            elif "retail" in client.industry.lower():
                opportunity = "Omnichannel Optimization Suite"
            elif "logistics" in client.industry.lower():
                opportunity = "Fleet Forecasting Expansion"
            opportunities.append(
                ClientOpportunityInsight(
                    client_name=client.client_name,
                    opportunity=opportunity,
                    probability=prediction.upsell_opportunity_score,
                    potential_revenue=prediction.upsell_revenue_potential,
                    rationale=(
                        f"{client.client_name} shows {round(client.platform_usage_score * 100)}% platform usage, "
                        f"{round(client.feature_adoption_score * 100)}% feature adoption, and "
                        f"{round(client.expansion_budget_signal * 100)}% budget expansion signal."
                    ),
                    recommended_action=f"Package {opportunity} with roadmap proof and executive sponsor validation.",
                    priority=ClientSatisfactionService._severity(prediction.upsell_opportunity_score),
                )
            )
        return sorted(opportunities, key=lambda item: (item.probability, item.potential_revenue), reverse=True)

    def _recommendations(self, predictions: list[ClientSatisfactionPrediction]) -> list[ClientRecoveryRecommendation]:
        recommendations: list[ClientRecoveryRecommendation] = []
        highest = predictions[0]
        recommendations.append(
            ClientRecoveryRecommendation(
                title="Launch executive client recovery lane",
                category="executive",
                priority=self._severity(max(highest.churn_risk, highest.escalation_probability)),
                action=f"Assign an executive sponsor to {highest.client_name}, publish a recovery plan, and review open blockers twice weekly.",
                expected_impact=f"Targets {round(highest.revenue_at_risk):,} revenue at risk and stabilizes trust decline.",
                confidence=highest.confidence,
                affected_clients=[highest.client_name],
            )
        )
        delivery_risk = max(predictions, key=lambda item: 100 - item.delivery_health)
        if delivery_risk.delivery_health < 72:
            recommendations.append(
                ClientRecoveryRecommendation(
                    title="Stabilize delivery commitments",
                    category="delivery",
                    priority=self._severity(100 - delivery_risk.delivery_health),
                    action=f"Move {delivery_risk.client_name} to milestone-level delivery tracking with named owners for each SLA blocker.",
                    expected_impact="Reduces missed commitment risk and protects client trust.",
                    confidence=0.84,
                    affected_clients=[delivery_risk.client_name],
                )
            )
        sentiment_risk = max(predictions, key=lambda item: 100 - item.communication_health)
        if sentiment_risk.communication_health < 74:
            recommendations.append(
                ClientRecoveryRecommendation(
                    title="Increase client communication frequency",
                    category="communication",
                    priority=self._severity(100 - sentiment_risk.communication_health),
                    action=f"Schedule weekly executive-status meetings for {sentiment_risk.client_name} and send written decision logs after each deployment discussion.",
                    expected_impact="Reverses communication negativity and clarifies ownership before escalation.",
                    confidence=0.82,
                    affected_clients=[sentiment_risk.client_name],
                )
            )
        quality_risk = max(predictions, key=lambda item: item.quality_risk)
        if quality_risk.quality_risk >= 42:
            recommendations.append(
                ClientRecoveryRecommendation(
                    title="Create quality recovery sprint",
                    category="quality",
                    priority=self._severity(quality_risk.quality_risk),
                    action=f"Reserve a dedicated QA and defect-burn-down lane for {quality_risk.client_name}.",
                    expected_impact="Improves delivery reliability and reduces support dissatisfaction.",
                    confidence=0.83,
                    affected_clients=[quality_risk.client_name],
                )
            )
        payment_risk = max(predictions, key=lambda item: item.payment_delay_risk)
        if payment_risk.payment_delay_risk >= 42:
            recommendations.append(
                ClientRecoveryRecommendation(
                    title="Start payment-risk prevention workflow",
                    category="payment",
                    priority=self._severity(payment_risk.payment_delay_risk),
                    action=f"Open finance and account-owner follow-up for {payment_risk.client_name} before the next invoice cycle.",
                    expected_impact=f"Reduces modeled payment-delay risk of {round(payment_risk.payment_delay_risk)}% and protects cash-flow timing.",
                    confidence=0.84,
                    affected_clients=[payment_risk.client_name],
                )
            )
        opportunity = max(predictions, key=lambda item: item.upsell_opportunity_score)
        if opportunity.upsell_opportunity_score >= 58:
            recommendations.append(
                ClientRecoveryRecommendation(
                    title="Advance expansion opportunity",
                    category="opportunity",
                    priority=self._severity(opportunity.upsell_opportunity_score),
                    action=f"Prepare an expansion proposal for {opportunity.client_name} using usage, adoption, and sponsor-engagement evidence.",
                    expected_impact=f"Creates modeled expansion potential of {round(opportunity.upsell_revenue_potential):,}.",
                    confidence=0.82,
                    affected_clients=[opportunity.client_name],
                )
            )
        return recommendations[:5]

    def _alerts(self, predictions: list[ClientSatisfactionPrediction]) -> list[ClientSatisfactionAlert]:
        alerts: list[ClientSatisfactionAlert] = []
        for prediction in predictions:
            score = max(
                prediction.churn_risk,
                prediction.escalation_probability,
                prediction.dissatisfaction_probability,
                prediction.payment_delay_risk,
                prediction.project_failure_risk,
            )
            if score >= 45:
                alerts.append(
                    ClientSatisfactionAlert(
                        title=f"{prediction.client_name} customer-health degradation",
                        severity=self._severity(score),
                        probability=round(score, 2),
                        impact=f"{prediction.client_name} has {round(prediction.churn_risk)}% churn risk, {round(prediction.escalation_probability)}% escalation probability, and {round(prediction.revenue_at_risk):,} revenue at risk.",
                        recommendation=prediction.recovery_actions[0] if prediction.recovery_actions else "Open a customer-success recovery lane.",
                    )
                )
        if not alerts and predictions:
            best = predictions[0]
            alerts.append(
                ClientSatisfactionAlert(
                    title="Client portfolio inside operating threshold",
                    severity="low",
                    probability=round(max(best.churn_risk, best.escalation_probability), 2),
                    impact="No account is currently above the critical churn threshold.",
                    recommendation="Maintain realtime monitoring and continue normal client-success cadence.",
                )
            )
        return alerts[:6]

    @staticmethod
    def _summary(predictions: list[ClientSatisfactionPrediction]) -> ClientSatisfactionSummary:
        if not predictions:
            return ClientSatisfactionSummary(
                clients_analyzed=0,
                average_client_health_score=0,
                average_churn_risk=0,
                average_escalation_probability=0,
                high_risk_clients=0,
                revenue_at_risk=0,
                payment_risk_accounts=0,
                project_risk_accounts=0,
                opportunity_revenue=0,
                highest_risk_client="None",
                best_upsell_client="None",
            )
        return ClientSatisfactionSummary(
            clients_analyzed=len(predictions),
            average_client_health_score=round(mean([item.client_health_score for item in predictions]), 2),
            average_churn_risk=round(mean([item.churn_risk for item in predictions]), 2),
            average_escalation_probability=round(mean([item.escalation_probability for item in predictions]), 2),
            high_risk_clients=sum(1 for item in predictions if item.churn_risk >= 55 or item.escalation_probability >= 55),
            revenue_at_risk=round(sum(item.revenue_at_risk for item in predictions), 2),
            payment_risk_accounts=sum(1 for item in predictions if item.payment_delay_risk >= 55),
            project_risk_accounts=sum(1 for item in predictions if item.project_failure_risk >= 55),
            opportunity_revenue=round(sum(item.upsell_revenue_potential for item in predictions if item.upsell_opportunity_score >= 50), 2),
            highest_risk_client=predictions[0].client_name,
            best_upsell_client=max(predictions, key=lambda item: item.upsell_opportunity_score).client_name,
        )

    @staticmethod
    def _executive_insights(predictions: list[ClientSatisfactionPrediction]) -> list[str]:
        if not predictions:
            return ["No client accounts were available for satisfaction analysis."]
        top = predictions[0]
        healthiest = max(predictions, key=lambda item: item.client_health_score)
        payment = max(predictions, key=lambda item: item.payment_delay_risk)
        project = max(predictions, key=lambda item: item.project_failure_risk)
        opportunity = max(predictions, key=lambda item: item.upsell_opportunity_score)
        return [
            f"{top.client_name} is the highest-risk account with {round(top.churn_risk)}% churn risk and {round(top.escalation_probability)}% escalation probability.",
            f"Portfolio average client health is {round(mean([item.client_health_score for item in predictions]))}% across {len(predictions)} monitored accounts.",
            f"{payment.client_name} has the highest payment-delay risk at {round(payment.payment_delay_risk)}% with a predicted {round(payment.predicted_payment_delay_days)} day delay.",
            f"{project.client_name} has the highest project-failure risk at {round(project.project_failure_risk)}% for {project.project_name}.",
            f"{opportunity.client_name} is the strongest expansion candidate with {round(opportunity.upsell_opportunity_score)}% upsell probability and {round(opportunity.upsell_revenue_potential):,} modeled potential.",
            f"{healthiest.client_name} is the healthiest relationship at {round(healthiest.client_health_score)}% client health.",
            f"Realtime client intelligence combines delivery delays, SLA breaches, sentiment, quality, escalation history, renewal timing, and contract exposure.",
        ]

    @staticmethod
    def _risk_drivers(
        client: ClientAccountSignal,
        row: dict[str, float],
        churn: float,
        escalation: float,
        trust_decline: float,
    ) -> list[str]:
        drivers = []
        if row["delay_pressure"] >= 0.32:
            drivers.append("Repeated delivery delays are reducing client confidence")
        if row["sentiment_negativity"] >= 0.42:
            drivers.append("Communication sentiment is trending negative")
        if row["sla_pressure"] >= 0.25:
            drivers.append("SLA breach frequency is pressuring satisfaction")
        if row["issue_resolution_pressure"] >= 0.45:
            drivers.append("Issue-resolution time exceeds customer-success threshold")
        if client.open_critical_issues > 0:
            drivers.append("Open critical issues increase escalation probability")
        if row["payment_delay_pressure"] >= 0.32 or row["overdue_invoice_pressure"] >= 0.2:
            drivers.append("Payment behavior indicates cash-collection risk")
        if row["meeting_absence_pressure"] >= 0.35 or row["email_latency_pressure"] >= 0.45:
            drivers.append("Engagement decline is visible in meetings and email responsiveness")
        if row["feature_adoption_gap"] >= 0.5:
            drivers.append("Feature adoption is below expansion and retention threshold")
        if churn >= 55:
            drivers.append("Churn-risk model indicates renewal instability")
        if escalation >= 55:
            drivers.append("Escalation model detects executive attention risk")
        if trust_decline < 32:
            drivers.append("Trust indicators remain inside modeled tolerance")
        return drivers[:6]

    @staticmethod
    def _recovery_actions(
        client: ClientAccountSignal,
        churn: float,
        escalation: float,
        quality_risk: float,
        trust_decline: float,
    ) -> list[str]:
        actions = [
            f"Publish a client recovery plan for {client.client_name} with named owners for each open blocker.",
        ]
        if churn >= 48:
            actions.append("Run renewal-risk review and quantify contract commitments before the next steering meeting.")
        if escalation >= 48:
            actions.append("Increase executive communication frequency and document decisions after each status call.")
        if quality_risk >= 42:
            actions.append("Open a defect burn-down lane and add QA signoff for client-visible deployments.")
        if trust_decline >= 42:
            actions.append("Send proactive trust-rebuilding update with resolved issues, ETA confidence, and escalation path.")
        if client.average_payment_delay_days > client.payment_terms_days * 0.45 or client.overdue_invoice_amount > 0:
            actions.append("Coordinate finance follow-up with the account owner before invoice aging crosses the collection threshold.")
        if client.platform_usage_score >= 0.72 and client.upsell_signal_score >= 0.55:
            actions.append("Prepare an expansion proposal tied to adoption evidence and executive sponsor priorities.")
        return actions[:5]

    @staticmethod
    def _sentiment_label(score: float) -> str:
        if score <= -0.35:
            return "negative"
        if score <= 0.08:
            return "watch"
        if score <= 0.42:
            return "stable"
        return "positive"

    @staticmethod
    def default_request() -> ClientSatisfactionRequest:
        return ClientSatisfactionRequest(
            cycle_name="Realtime Client Satisfaction Review",
            horizon_days=45,
            clients=[
                ClientAccountSignal(
                    client_id="client-northstar",
                    client_name="Northstar Retail",
                    industry="Retail",
                    account_tier="enterprise",
                    project_name="Omnichannel Commerce Migration",
                    contract_value=3400000,
                    renewal_days=72,
                    delivery_delay_days=13,
                    missed_milestones=4,
                    sla_breach_count=3,
                    bug_frequency=0.42,
                    production_incidents=3,
                    qa_pass_rate=0.68,
                    rework_ratio=0.34,
                    issue_resolution_hours=96,
                    escalation_count=4,
                    communication_sentiment=-0.28,
                    interaction_frequency=0.42,
                    feedback_score=0.48,
                    nps_delta=-24,
                    delivery_consistency=0.52,
                    relationship_tenure_months=20,
                    executive_sponsor_engagement=0.38,
                    open_critical_issues=3,
                    average_payment_delay_days=19,
                    overdue_invoice_amount=420000,
                    invoice_dispute_count=3,
                    meeting_attendance_rate=0.48,
                    email_response_hours=72,
                    platform_usage_score=0.44,
                    feature_adoption_score=0.38,
                    support_ticket_count=24,
                    upsell_signal_score=0.24,
                    expansion_budget_signal=0.18,
                    stakeholder_change_count=2,
                    meeting_transcripts=[
                        "The deployment delay is frustrating, and the same checkout defect keeps coming back without a clear owner.",
                        "We need executive escalation because trust is dropping and the release date moved again.",
                    ],
                    email_threads=[
                        "Several SLA commitments were missed and the team is still waiting for resolution details.",
                    ],
                ),
                ClientAccountSignal(
                    client_id="client-acme",
                    client_name="Acme Bank",
                    industry="Financial Services",
                    account_tier="global",
                    project_name="Risk Analytics Modernization",
                    contract_value=5200000,
                    renewal_days=164,
                    delivery_delay_days=3,
                    missed_milestones=1,
                    sla_breach_count=0,
                    bug_frequency=0.12,
                    production_incidents=0,
                    qa_pass_rate=0.92,
                    rework_ratio=0.08,
                    issue_resolution_hours=18,
                    escalation_count=0,
                    communication_sentiment=0.46,
                    interaction_frequency=0.82,
                    feedback_score=0.86,
                    nps_delta=7,
                    delivery_consistency=0.88,
                    relationship_tenure_months=42,
                    executive_sponsor_engagement=0.84,
                    average_payment_delay_days=2,
                    overdue_invoice_amount=0,
                    invoice_dispute_count=0,
                    meeting_attendance_rate=0.9,
                    email_response_hours=10,
                    platform_usage_score=0.88,
                    feature_adoption_score=0.82,
                    support_ticket_count=3,
                    upsell_signal_score=0.82,
                    expansion_budget_signal=0.74,
                    meeting_transcripts=["The risk analytics release is stable, communication is clear, and the team resolved open questions quickly."],
                    email_threads=["Thanks for the proactive status note. We are confident in the migration plan."],
                ),
                ClientAccountSignal(
                    client_id="client-helio",
                    client_name="Helio Health",
                    industry="Healthcare",
                    account_tier="enterprise",
                    project_name="Patient Operations AI",
                    contract_value=2100000,
                    renewal_days=118,
                    delivery_delay_days=6,
                    missed_milestones=1,
                    sla_breach_count=1,
                    bug_frequency=0.22,
                    production_incidents=1,
                    qa_pass_rate=0.81,
                    rework_ratio=0.16,
                    issue_resolution_hours=34,
                    escalation_count=1,
                    communication_sentiment=0.18,
                    interaction_frequency=0.68,
                    feedback_score=0.74,
                    nps_delta=-4,
                    delivery_consistency=0.76,
                    relationship_tenure_months=28,
                    executive_sponsor_engagement=0.72,
                    open_critical_issues=1,
                    average_payment_delay_days=5,
                    overdue_invoice_amount=35000,
                    invoice_dispute_count=0,
                    meeting_attendance_rate=0.78,
                    email_response_hours=22,
                    platform_usage_score=0.76,
                    feature_adoption_score=0.7,
                    support_ticket_count=7,
                    upsell_signal_score=0.64,
                    expansion_budget_signal=0.58,
                    meeting_transcripts=["The platform is improving, but the integration delay needs a clearer mitigation plan."],
                ),
                ClientAccountSignal(
                    client_id="client-vertex",
                    client_name="Vertex Logistics",
                    industry="Logistics",
                    account_tier="strategic",
                    project_name="Fleet Intelligence Platform",
                    contract_value=1600000,
                    renewal_days=52,
                    delivery_delay_days=8,
                    missed_milestones=2,
                    sla_breach_count=2,
                    bug_frequency=0.28,
                    production_incidents=2,
                    qa_pass_rate=0.75,
                    rework_ratio=0.21,
                    issue_resolution_hours=58,
                    escalation_count=2,
                    communication_sentiment=-0.08,
                    interaction_frequency=0.56,
                    feedback_score=0.62,
                    nps_delta=-12,
                    delivery_consistency=0.68,
                    relationship_tenure_months=14,
                    executive_sponsor_engagement=0.56,
                    open_critical_issues=1,
                    average_payment_delay_days=12,
                    overdue_invoice_amount=120000,
                    invoice_dispute_count=1,
                    meeting_attendance_rate=0.62,
                    email_response_hours=42,
                    platform_usage_score=0.61,
                    feature_adoption_score=0.54,
                    support_ticket_count=13,
                    upsell_signal_score=0.48,
                    expansion_budget_signal=0.44,
                    email_threads=["The latest defect fix helped, but the client still wants more frequent release notes and ETA confidence."],
                ),
            ],
        )

    @staticmethod
    def _scenario_variant(
        base: ClientSatisfactionRequest,
        delay_delta: float,
        sentiment_delta: float,
        escalation_delta: int,
    ) -> ClientSatisfactionRequest:
        clients = [
            client.model_copy(
                update={
                    "delivery_delay_days": min(180, client.delivery_delay_days + delay_delta * (1.3 if client.delivery_delay_days > 7 else 0.7)),
                    "missed_milestones": min(80, client.missed_milestones + (1 if delay_delta >= 3 else 0)),
                    "escalation_count": min(100, client.escalation_count + escalation_delta if client.communication_sentiment < 0.1 else client.escalation_count),
                    "communication_sentiment": max(-1, client.communication_sentiment + sentiment_delta),
                    "issue_resolution_hours": min(720, client.issue_resolution_hours + delay_delta * 6),
                    "feedback_score": max(0, client.feedback_score + sentiment_delta * 0.35),
                    "nps_delta": max(-100, client.nps_delta + sentiment_delta * 30),
                    "delivery_consistency": max(0, client.delivery_consistency - delay_delta * 0.018),
                    "average_payment_delay_days": min(180, client.average_payment_delay_days + delay_delta * 0.9),
                    "overdue_invoice_amount": min(100_000_000, client.overdue_invoice_amount + max(0, delay_delta) * client.contract_value * 0.006),
                    "invoice_dispute_count": min(50, client.invoice_dispute_count + (1 if sentiment_delta <= -0.12 else 0)),
                    "meeting_attendance_rate": max(0, client.meeting_attendance_rate + sentiment_delta * 0.18),
                    "email_response_hours": min(720, client.email_response_hours + delay_delta * 5),
                    "platform_usage_score": max(0, client.platform_usage_score + sentiment_delta * 0.14),
                    "feature_adoption_score": max(0, client.feature_adoption_score + sentiment_delta * 0.1),
                }
            )
            for client in base.clients
        ]
        return base.model_copy(update={"clients": clients, "realtime": True})

    @staticmethod
    def _severity(score: float) -> ClientRiskPriority:
        if score >= 78:
            return "critical"
        if score >= 58:
            return "high"
        if score >= 36:
            return "medium"
        return "low"

    @staticmethod
    def _clip(value: float, lower: float = 0, upper: float = 100) -> float:
        return float(max(lower, min(upper, value)))

    @staticmethod
    def _clip01(value: float) -> float:
        return float(max(0, min(1, value)))

    def _append_jsonl(self, payload: dict[str, object]) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with self._lock:
            with HISTORY_PATH.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload) + "\n")


client_satisfaction_service = ClientSatisfactionService()
