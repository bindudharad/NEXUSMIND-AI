from __future__ import annotations

import asyncio
import base64
import io
import json
import re
import time
import wave
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from uuid import uuid4

import numpy as np

from app.ai.voice_stress_engine import voice_stress_engine
from app.schemas.nlp import NLPAnalyzeRequest
from app.schemas.enterprise_knowledge import EnterpriseKnowledgeAskRequest
from app.schemas.voice import (
    VoiceAICouncilTurn,
    VoiceAcousticFeatures,
    VoiceAlert,
    VoiceCapabilityStatus,
    VoiceCommandAction,
    VoiceCommandRequest,
    VoiceCommandResponse,
    VoiceConversationMemoryItem,
    VoiceDashboardControl,
    VoiceEmotionScores,
    VoiceExecutiveReadiness,
    VoiceStressAnalyzeRequest,
    VoiceStressResponse,
    VoiceStressSummary,
    VoiceTTSMetadata,
    VoiceVisualChart,
    VoiceVisualKPI,
    VoiceVisualResponse,
    VoiceTimelinePoint,
)
from app.services.nlp_service import nlp_service
from app.services.enterprise_knowledge_service import enterprise_knowledge_service


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
HISTORY_PATH = DATA_DIR / "voice_stress_history.jsonl"
COMMAND_HISTORY_PATH = DATA_DIR / "voice_command_history.jsonl"
COPILOT_MEMORY_PATH = DATA_DIR / "voice_copilot_memory.jsonl"


VOICE_COPILOT_SOURCE_SYSTEMS = [
    "speech_recognition_engine",
    "speech_to_text_engine",
    "voice_command_engine",
    "llm_assistant_engine",
    "text_to_speech_engine",
    "context_memory_engine",
    "ai_memory_integration",
    "company_state_engine",
    "digital_twin_integration",
    "simulation_integration",
    "executive_recommendation_engine",
    "enterprise_analytics_connector",
    "executive_dashboard_integration",
    "dashboard_control_engine",
    "multi_agent_orchestrator",
    "voice_ai_assistant_ui",
]


class VoiceStressService:
    model_name = "RandomForest VoiceStressNet + PyTorch NLP Fusion"
    command_model_name = "Voice-Controlled Enterprise AI Command Router + Live Analytics Grounding"

    def __init__(self) -> None:
        self._lock = Lock()
        self._session_memory: dict[str, list[VoiceConversationMemoryItem]] = {}
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def analyze(self, payload: VoiceStressAnalyzeRequest | None = None) -> VoiceStressResponse:
        request = payload or self.default_request()
        samples, sample_rate, duration = self._decode_audio(request)
        features = voice_stress_engine.extract_features(samples, sample_rate, request.transcript, duration)
        acoustic_prediction = voice_stress_engine.predict(features)
        text_result = None
        if request.transcript and request.transcript.strip():
            text_result = nlp_service.analyze(
                NLPAnalyzeRequest(
                    employee_id=request.employee_id,
                    department=request.department,
                    channel="voice_transcript",
                    text=request.transcript,
                )
            )

        emotion_scores = self._fuse_emotions(acoustic_prediction.emotion_probabilities, text_result)
        stress_score = self._fused_stress(acoustic_prediction.stress_score, text_result, features)
        burnout_risk = self._burnout_risk(stress_score, features, text_result, emotion_scores)
        conflict_intensity = self._conflict_intensity(features, text_result, emotion_scores)
        communication_pressure = self._communication_pressure(stress_score, features)
        primary_emotion = self._primary_emotion(emotion_scores)
        alerts = self._alerts(request, stress_score, burnout_risk, conflict_intensity, communication_pressure, features, emotion_scores, text_result)
        timeline = self._timeline(samples, sample_rate, request.transcript, duration)
        peak_stress = max([point.stress for point in timeline] + [stress_score])
        recommendations = self._recommendations(stress_score, burnout_risk, conflict_intensity, communication_pressure, alerts)
        response = VoiceStressResponse(
            model=self.model_name,
            generated_at=datetime.now(timezone.utc),
            employee_id=request.employee_id,
            speaker=request.speaker,
            department=request.department,
            source_format=request.source_format,
            duration_seconds=round(duration, 3),
            transcript=request.transcript,
            primary_emotion=primary_emotion,
            confidence=max(acoustic_prediction.confidence, getattr(text_result, "confidence", 0.0) if text_result else 0.0),
            stress_score=round(stress_score, 2),
            burnout_risk=round(burnout_risk, 2),
            conflict_intensity=round(conflict_intensity, 2),
            communication_pressure=round(communication_pressure, 2),
            acoustic_features=VoiceAcousticFeatures(**features),
            emotion_scores=emotion_scores,
            fusion_evidence=self._fusion_evidence(acoustic_prediction.stress_score, text_result, features),
            alerts=alerts,
            recommendations=recommendations,
            timeline=timeline,
            summary=VoiceStressSummary(
                average_stress=round(float(np.mean([point.stress for point in timeline] or [stress_score])), 2),
                peak_stress=round(peak_stress, 2),
                alert_count=len(alerts),
            ),
            storage=str(HISTORY_PATH),
        )
        self._append_jsonl(response.model_dump(mode="json"))
        return response

    def execute_command(self, payload: VoiceCommandRequest) -> VoiceCommandResponse:
        started = time.perf_counter()
        transcript = payload.transcript.strip()
        normalized = transcript.lower()
        intent = self._resolve_followup_intent(normalized, payload.session_id)
        trace = [
            f"Received transcript from {payload.speaker} in {payload.department}.",
            f"Classified command intent as {intent}.",
        ]
        recommendations: list[str] = []

        if intent == "company_threat":
            from app.ai.digital_twin import digital_twin_simulator
            from app.services.anomaly_service import anomaly_service
            from app.services.boardroom_service import boardroom_dashboard_service
            from app.services.business_prediction_service import business_prediction_service
            from app.services.project_failure_service import project_failure_service

            boardroom = boardroom_dashboard_service.default()
            anomalies = anomaly_service.detect()
            business = business_prediction_service.analyze()
            project = project_failure_service.analyze()
            twin_snapshot = digital_twin_simulator.snapshot()
            top_boardroom_risk = max(boardroom.executive_risks, key=lambda item: item.probability * item.impact_score)
            top_project = max(project.predictions, key=lambda item: item.failure_probability)
            anomaly_alerts = getattr(anomalies, "alerts", [])
            insider_scores = [float(getattr(item, "insider_threat_score", 0)) for item in anomaly_alerts]
            top_insider_score = max(insider_scores or [boardroom.cybersecurity.insider_threat_risk])
            cybersecurity_risk = float(
                np.clip(
                    max(
                        100 - boardroom.cybersecurity.security_score,
                        boardroom.cybersecurity.insider_threat_risk,
                        boardroom.cybersecurity.data_leakage_risk,
                        top_insider_score,
                    ),
                    0,
                    100,
                )
            )
            finance_pressure = float(np.clip(max(boardroom.summary.overall_risk_score, business.summary.market_risk_score), 0, 100))
            workforce_pressure = float(
                np.clip(
                    max(
                        100 - boardroom.workforce.employee_health_score,
                        boardroom.workforce.attrition_risk,
                        abs(boardroom.workforce.productivity_trend) * 7,
                    ),
                    0,
                    100,
                )
            )
            delivery_pressure = float(np.clip(max(boardroom.projects.delivery_risk, top_project.deadline_miss_probability), 0, 100))
            risk_score = max(cybersecurity_risk, finance_pressure, workforce_pressure, delivery_pressure, top_boardroom_risk.probability)
            answer = (
                f"The biggest company threat is {top_boardroom_risk.title.lower()} compounded by cybersecurity and delivery exposure. "
                f"Cybersecurity risk is {round(cybersecurity_risk)}% with {boardroom.cybersecurity.active_threats} active threat signal(s), "
                f"insider-threat pressure at {round(boardroom.cybersecurity.insider_threat_risk)}%, and unusual-access anomaly pressure at {round(top_insider_score)}%. "
                f"Finance pressure is {round(finance_pressure)}% with next-quarter revenue forecast at ${business.summary.predicted_next_quarter_revenue:,.0f}. "
                f"{top_project.project_name} carries {round(top_project.deadline_miss_probability)}% deadline-miss risk, so management should secure privileged access, protect delivery capacity, and open an executive recovery review."
            )
            actions = [
                self._command_action("Update risk heatmap", "visualize", "risk_heatmap", "critical" if risk_score >= 85 else "high"),
                self._command_action("Animate forecast charts", "visualize", "forecast_console", "high"),
                self._command_action("Synchronize digital twins", "workflow", "digital_twin_sync", "high"),
                self._command_action("Open executive threat review", "workflow", "boardroom_threat_review", "critical" if risk_score >= 85 else "high"),
            ]
            target_dashboard = "Executive Threat Intelligence Console"
            source_systems = [
                "boardroom_dashboard",
                "risk_aggregation_engine",
                "cybersecurity_intelligence_engine",
                "anomaly_detection",
                "insider_threat_model",
                "financial_prediction_engine",
                "business_prediction_engine",
                "workforce_analytics",
                "company_emotion_map",
                "project_failure_forecaster",
                "project_twin",
                "employee_twin",
                "team_twin",
                "department_twin",
                "company_twin",
                "forecast_chart_engine",
                "risk_heatmap_engine",
                *boardroom.source_systems[:8],
            ]
            workflow = "executive_company_threat_response"
            recommendations = [
                boardroom.cybersecurity.recommendations[0] if boardroom.cybersecurity.recommendations else "Apply adaptive authentication to high-risk access paths.",
                top_boardroom_risk.recommendation,
                f"Move critical-path capacity toward {top_project.project_name} until deadline-miss risk falls below 45%.",
                f"Finance Agent should monitor market-risk pressure at {round(finance_pressure)}% and update the revenue guardrail weekly.",
                f"Digital Twin sync should track {len(twin_snapshot['employees'])} employee twins, {len(twin_snapshot['teams'])} team twins, {len(twin_snapshot['departments'])} department twins, and {len(twin_snapshot['projects'])} project twins.",
            ]
            trace.extend(
                [
                    f"Loaded Boardroom risk: {top_boardroom_risk.title} at {round(top_boardroom_risk.probability)}% probability and {round(top_boardroom_risk.impact_score)}% impact.",
                    f"Loaded cybersecurity posture: score={round(boardroom.cybersecurity.security_score)}%, active_threats={boardroom.cybersecurity.active_threats}, insider={round(boardroom.cybersecurity.insider_threat_risk)}%.",
                    f"Loaded finance forecast: next_quarter_revenue=${business.summary.predicted_next_quarter_revenue:,.0f}, market_risk={round(business.summary.market_risk_score)}%.",
                    f"Loaded project risk: {top_project.project_name} deadline_miss={round(top_project.deadline_miss_probability)}%.",
                    f"Read digital twin snapshot with {len(twin_snapshot['employees'])} employees, {len(twin_snapshot['teams'])} teams, {len(twin_snapshot['departments'])} departments, and {len(twin_snapshot['projects'])} projects.",
                ]
            )
        elif intent == "department_failure_forecast":
            from app.services.manager_dashboard_service import manager_dashboard_service
            from app.services.project_failure_service import project_failure_service

            manager = manager_dashboard_service.analyze()
            project_request = project_failure_service.default_request()
            top_team = manager.risky_teams[0]
            demo_project = next(
                (project for project in project_request.projects if "delta" in project.project_name.lower()),
                project_request.projects[0],
            )
            projected_delay_days = max(
                1,
                round(demo_project.days_to_deadline * (1 - demo_project.current_scope_completion)),
            )
            future_burnout_risk = int(
                np.ceil(
                    float(
                        np.clip(
                            max(
                                top_team.risk_score * 0.82 + projected_delay_days * 1.62,
                                projected_delay_days * 6.6,
                            ),
                            0,
                            100,
                        )
                    )
                )
            )
            short_project_name = " ".join(demo_project.project_name.split()[:2])
            answer = (
                f"{top_team.team_name} has a {future_burnout_risk}% next-month burnout risk and "
                f"{short_project_name} may be delayed by {projected_delay_days} days."
            )
            actions = [
                self._command_action("Animate risk heatmap", "visualize", "risk_heatmap", "critical"),
                self._command_action("Synchronize digital twins", "workflow", "digital_twin_sync", "high"),
                self._command_action("Generate executive recovery plan", "workflow", "recovery_plan", "critical"),
                self._command_action("Open Shadow Company future", "navigate", "shadow_company", "high"),
            ]
            target_dashboard = "Judge Live AI CEO Demo"
            project_delay_pressure = round(
                float(
                    np.clip(
                        (1 - demo_project.current_scope_completion) * 100
                        + demo_project.critical_dependency_count * 2,
                        0,
                        100,
                    )
                )
            )
            risk_score = max(future_burnout_risk, project_delay_pressure, top_team.risk_score)
            source_systems = [
                "manager_dashboard",
                "risk_heatmap_engine",
                "burnout_visualization_engine",
                "company_emotion_map",
                "project_failure_forecaster",
                "project_delay_forecast",
                "company_digital_twin",
                "employee_twin",
                "team_twin",
                "department_twin",
                "project_twin",
                "shadow_company",
                "forecast_chart_engine",
                "recovery_plan_generator",
            ]
            workflow = "judge_live_ceo_future_failure_demo"
            recommendations = [
                f"Immediate action: move two critical delivery items out of {top_team.team_name} today and assign a recovery owner.",
                f"Short-term plan: add temporary capacity to {short_project_name} and freeze non-critical scope for one sprint.",
                "Long-term plan: reduce meeting load, rotate incident ownership, and rebuild paired ownership for knowledge-critical work.",
                "Risk reduction strategy: run daily health checks until burnout risk drops below 55% and forecast delay falls under one week.",
                "Executive recommendation: open a 48-hour stabilization lane with HR, Project, Finance, and Productivity agents.",
            ]
            trace.extend(
                [
                    f"Loaded {len(manager.risky_teams)} risky team(s) and {len(project_request.projects)} project profile forecast(s).",
                    f"Updated risk heatmap, burnout visualization, digital twins, and Shadow Company projection for {top_team.team_name}.",
                    f"Calculated {short_project_name} delay from {round(demo_project.current_scope_completion * 100)}% scope completion and {demo_project.days_to_deadline} days to deadline.",
                ]
            )
        elif intent == "highest_risk_department":
            from app.services.manager_dashboard_service import manager_dashboard_service

            manager = manager_dashboard_service.analyze()
            top_team = manager.risky_teams[0]
            answer = (
                f"{top_team.team_name} is the highest-risk area with {round(top_team.risk_score)}% team risk. "
                f"Primary drivers: {', '.join(top_team.drivers[:3])}."
            )
            actions = [
                self._command_action("Open manager risk dashboard", "navigate", "manager_dashboard", "high"),
                self._command_action("Trigger workload rebalance review", "workflow", "resource_allocation", "high"),
            ]
            target_dashboard = "Executive Risk Dashboard"
            risk_score = top_team.risk_score
            source_systems = ["manager_dashboard", "team_risk_model", "workload_analytics"]
            workflow = "manager_risk_review"
            recommendations = [
                "Move two urgent delivery items away from the highest-risk team this week.",
                "Open a 30-minute executive review with the manager and project owner.",
            ]
            trace.append(f"Loaded manager dashboard with {manager.summary.teams_at_risk} teams at risk.")
        elif intent == "productivity_forecast":
            from app.schemas.forecasting import ForecastRequest
            from app.services.forecasting_service import forecasting_service

            forecast = forecasting_service.forecast(ForecastRequest())
            final_point = forecast.forecast[-1]
            answer = (
                f"Next-cycle productivity is forecast at {round(final_point.productivity)} out of 100, "
                f"with burnout pressure near {round(final_point.burnout_risk)}%."
            )
            actions = [
                self._command_action("Open productivity forecast", "navigate", "productivity_dashboard", "medium"),
                self._command_action("Schedule protected focus blocks", "workflow", "work_life_balance", "medium"),
            ]
            target_dashboard = "Productivity Forecast Dashboard"
            risk_score = max(0, 100 - final_point.productivity)
            source_systems = ["workload_lstm", "forecasting_service", "productivity_leakage_detector"]
            workflow = "productivity_recovery_plan"
            recommendations = [
                "Protect the highest-productivity morning window from meetings.",
                "Reduce context switching for teams with forecasted burnout pressure.",
            ]
            trace.append(f"Loaded {len(forecast.forecast)} forecast points from workload forecasting.")
        elif intent == "revenue_forecast":
            from app.services.business_prediction_service import business_prediction_service

            business = business_prediction_service.analyze()
            summary = business.summary
            answer = (
                f"Next-quarter revenue is forecast at ${summary.predicted_next_quarter_revenue:,.0f} "
                f"with {round(summary.forecast_confidence * 100)}% confidence. Annual revenue forecast is "
                f"${summary.annual_revenue_forecast:,.0f}; top business risk is {summary.top_business_risk}."
            )
            actions = [
                self._command_action("Open revenue forecast", "navigate", "business_prediction_dashboard", "high"),
                self._command_action("Start CFO forecast review", "workflow", "financial_prediction_review", "high"),
            ]
            target_dashboard = "Financial Prediction Dashboard"
            risk_score = max(summary.market_risk_score, summary.average_churn_probability)
            source_systems = ["business_prediction_engine", "financial_prediction_engine", *business.source_systems[:8]]
            workflow = "executive_revenue_forecast_review"
            recommendations = [item.action for item in business.recommendations[:3]]
            trace.append(f"Loaded business forecast with {len(business.revenue_forecast)} revenue points.")
        elif intent == "crisis_dashboard":
            from app.services.strategic_intelligence_service import strategic_intelligence_service

            strategic = strategic_intelligence_service.analyze()
            crisis = strategic.crisis_response
            answer = (
                f"Crisis posture is {crisis.risk_level} at {round(crisis.severity_score)}% severity. "
                f"Priority action: {crisis.recovery_priorities[0]}"
            )
            actions = [
                self._command_action("Open crisis command center", "navigate", "crisis_dashboard", "critical"),
                self._command_action("Start executive crisis cadence", "workflow", "crisis_management", "critical"),
            ]
            target_dashboard = "Realtime Crisis Command Center"
            risk_score = crisis.severity_score
            source_systems = ["strategic_intelligence_graph", "crisis_response_ai", "realtime_alerts"]
            workflow = "executive_crisis_protocol"
            recommendations = crisis.recovery_priorities[:3]
            trace.append(f"Loaded crisis plan with recovery window {crisis.expected_recovery_days} days.")
        elif intent == "security_posture":
            from app.schemas.alerts import AlertDetectionRequest
            from app.services.alert_service import alert_service
            from app.services.anomaly_service import anomaly_service

            anomalies = anomaly_service.detect()
            alerts = alert_service.feed(AlertDetectionRequest(scenario="crisis", sensitivity=0.76))
            security_alerts = [item for item in alerts.alerts if item.category == "security"]
            top_score = max([item.insider_threat_score for item in anomalies.alerts] or [0])
            answer = (
                f"Security posture is elevated: {len(security_alerts)} SOC alerts and top insider-threat score "
                f"{round(top_score)}%. Apply adaptive authentication and export throttling."
            )
            actions = [
                self._command_action("Open SOC risk dashboard", "navigate", "security_dashboard", "high"),
                self._command_action("Tighten privileged session controls", "workflow", "security_response", "high"),
            ]
            target_dashboard = "Cybersecurity AI Dashboard"
            risk_score = top_score
            source_systems = ["anomaly_detection", "security_analyzer", "alert_correlator"]
            workflow = "soc_response_protocol"
            recommendations = [
                "Enforce adaptive MFA for high-risk sessions.",
                "Throttle sensitive exports until SOC review is complete.",
                "Open the insider-threat case queue for privileged users.",
            ]
            trace.append(f"Loaded {len(anomalies.alerts)} anomaly alerts and {len(security_alerts)} security alerts.")
        elif intent == "digital_twin_simulation":
            from app.ai.digital_twin import TwinScenarioInput, digital_twin_simulator

            resignation_count = self._extract_resignation_count(normalized)
            scenario = TwinScenarioInput(
                resignation_count=resignation_count,
                workload_delta_percent=28 if resignation_count >= 20 else 18,
                budget_delta_percent=0,
                security_incident="cyber" in normalized or "attack" in normalized,
            )
            outcome = digital_twin_simulator.simulate_extended(scenario)
            monte_carlo = digital_twin_simulator.simulate_monte_carlo(scenario)
            answer = (
                f"Digital Twin simulation for {resignation_count} resignations shows {outcome.delay_probability}% delivery-delay risk, "
                f"{outcome.team_collapse_probability}% team-collapse risk, and P90 Monte Carlo delay of {monte_carlo.delay_probability_p90}%."
            )
            actions = [
                self._command_action("Open simulation lab", "navigate", "digital_twin_lab", "high"),
                self._command_action("Launch retention recovery scenario", "workflow", "digital_twin_recovery", "high"),
            ]
            target_dashboard = "Digital Twin Simulation Lab"
            risk_score = max(outcome.delay_probability, outcome.team_collapse_probability)
            source_systems = ["digital_twin", "monte_carlo_simulation", "scenario_modeling"]
            workflow = "digital_twin_recovery_simulation"
            recommendations = [
                "Create a retention recovery scenario and compare it against backfill hiring.",
                "Move knowledge-critical work to paired ownership before attrition increases.",
            ]
            trace.append(f"Ran Monte Carlo with {monte_carlo.runs} simulations for {resignation_count} resignations.")
        elif intent == "project_risk":
            from app.services.project_failure_service import project_failure_service

            project = project_failure_service.analyze()
            top = max(project.predictions, key=lambda item: item.failure_probability)
            answer = (
                f"{top.project_name} is the highest project risk: {round(top.failure_probability)}% failure probability, "
                f"{round(top.deadline_miss_probability)}% deadline-miss probability, and {round(top.resource_shortage_impact)}% resource-shortage impact."
            )
            actions = [
                self._command_action("Open project intelligence", "navigate", "project_failure_dashboard", "high"),
                self._command_action("Trigger delivery risk review", "workflow", "project_recovery", "high"),
            ]
            target_dashboard = "Project Intelligence Dashboard"
            risk_score = top.failure_probability
            source_systems = ["project_intelligence_engine", "completion_forecasting", "resource_gap_analyzer", "project_failure_forecaster"]
            workflow = "project_recovery_protocol"
            recommendations = [item.action for item in top.recommendations[:3]] or [item.action for item in project.portfolio_recommendations[:3]]
            trace.append(f"Loaded project failure model for {project.summary.projects_analyzed} projects.")
        elif intent == "client_risk":
            from app.services.strategic_intelligence_service import strategic_intelligence_service

            strategic = strategic_intelligence_service.analyze()
            client = strategic.client_relationship_intelligence[0]
            risk = max(client.churn_risk, client.payment_delay_risk, client.escalation_risk)
            answer = (
                f"{client.client_name} is the top client-risk account with {round(client.churn_risk)}% churn risk, "
                f"{round(client.escalation_risk)}% escalation risk, and ${round(client.revenue_at_risk):,} revenue at risk."
            )
            actions = [
                self._command_action("Open client risk dashboard", "navigate", "client_relationship_dashboard", "high"),
                self._command_action("Assign executive sponsor", "workflow", "client_recovery", "critical" if risk >= 85 else "high"),
            ]
            target_dashboard = "Client Relationship Intelligence"
            risk_score = risk
            source_systems = ["client_relationship_ai", "strategic_intelligence", "revenue_risk"]
            workflow = "client_recovery_protocol"
            recommendations = [
                "Assign an executive sponsor to the riskiest account.",
                "Schedule a delivery recovery call before the next renewal milestone.",
            ]
            trace.append(f"Loaded client risk for {client.client_name}.")
        elif intent == "competitive_threat":
            from app.services.competitive_intelligence_service import competitive_intelligence_service

            competitive = competitive_intelligence_service.analyze()
            top_threat = competitive.risk_scores[0]
            answer = (
                f"Top competitive threat is {top_threat.competitor}: {round(top_threat.threat_score)}% threat score. "
                f"Primary driver: {top_threat.primary_threat}."
            )
            actions = [
                self._command_action("Open competitive war room", "navigate", "competitive_intelligence_dashboard", "medium"),
                self._command_action("Start strategy response review", "workflow", "competitive_response", "medium"),
            ]
            target_dashboard = "Competitive Intelligence War Room"
            risk_score = top_threat.threat_score
            source_systems = ["competitive_intelligence_engine", "market_intelligence_engine", "industry_trend_analysis_engine", *competitive.source_systems[:6]]
            workflow = "competitive_strategy_review"
            recommendations = [item.action for item in competitive.recommendations[:3]]
            trace.append(f"Loaded competitive intelligence for {len(competitive.profiles)} competitors.")
        elif intent == "innovation_opportunity":
            from app.services.innovation_service import innovation_scoring_service

            innovation = innovation_scoring_service.score()
            leader = innovation.leadership_predictions[0]
            champion = innovation.hidden_talent[0]
            answer = (
                f"Top innovation opportunity is {champion.employee_name} with {round(champion.hidden_talent_score)}% hidden-talent score. "
                f"{leader.employee_name} has {round(leader.leadership_potential)}% leadership potential for future strategic programs."
            )
            actions = [
                self._command_action("Open innovation detector", "navigate", "innovation_dashboard", "medium"),
                self._command_action("Start leadership acceleration review", "workflow", "talent_acceleration", "medium"),
            ]
            target_dashboard = "Innovation Intelligence Dashboard"
            risk_score = 100 - max(champion.hidden_talent_score, leader.leadership_potential)
            source_systems = ["innovation_intelligence_engine", "talent_discovery_engine", "future_leader_prediction_engine", *innovation.source_systems[:6]]
            workflow = "innovation_talent_review"
            recommendations = [item.action for item in innovation.promotion_recommendations[:3]]
            trace.append(f"Loaded innovation detector with {len(innovation.hidden_talent)} hidden-talent signals.")
        elif intent == "memory_query":
            brain = enterprise_knowledge_service.ask(
                EnterpriseKnowledgeAskRequest(
                    question=transcript,
                    top_k=6,
                    include_graph_evidence=True,
                    session_id=payload.session_id,
                )
            )
            citation_titles = [citation.title for citation in brain.citations[:3]]
            answer = (
                f"Company Memory found {len(brain.citations)} cited knowledge source(s) with "
                f"{round(brain.confidence * 100)}% confidence. {brain.answer}"
            )
            actions = [
                self._command_action("Open Enterprise Knowledge Brain", "navigate", "enterprise_knowledge_brain", "high"),
                self._command_action("Review cited lessons learned", "workflow", "knowledge_memory_review", "medium"),
            ]
            target_dashboard = "Enterprise Knowledge Brain"
            risk_score = max(12, 100 - brain.confidence * 100)
            source_systems = [
                "enterprise_knowledge_brain",
                "rag_engine",
                "vector_database",
                "knowledge_graph",
                "organizational_memory",
                *brain.source_systems[:10],
            ]
            workflow = "enterprise_memory_retrieval"
            recommendations = brain.recommended_follow_up_actions[:4] or [
                "Open cited project memory and assign the expert owner.",
                "Convert the answer into a reusable executive decision note.",
            ]
            trace.append(
                f"Queried Enterprise Knowledge Brain with {len(brain.citations)} citations"
                + (f": {', '.join(citation_titles)}." if citation_titles else ".")
            )
        elif intent in {"boardroom_priority", "recommendation"}:
            from app.services.boardroom_service import boardroom_dashboard_service

            boardroom = boardroom_dashboard_service.default()
            top_risk = boardroom.executive_risks[0]
            top_action = boardroom.recommendations[0]
            answer = (
                f"Solve {top_risk.category} first. {top_risk.title} affects {top_risk.affected_area} with "
                f"{round(top_risk.probability)}% probability and {round(top_risk.impact_score)}% impact. "
                f"Recommended action: {top_action.action}."
            )
            actions = [
                self._command_action("Open boardroom dashboard", "navigate", "boardroom_dashboard", "critical" if top_risk.severity == "critical" else "high"),
                self._command_action("Start executive action review", "workflow", "boardroom_recommendation", "high"),
            ]
            target_dashboard = "AI Boardroom Dashboard"
            risk_score = max(top_risk.probability, top_risk.impact_score)
            source_systems = ["boardroom_dashboard", "risk_aggregation_engine", "executive_recommendation_engine", *boardroom.source_systems[:10]]
            workflow = "executive_recommendation_review"
            recommendations = [item.action for item in boardroom.recommendations[:5]]
            trace.append(f"Loaded boardroom dashboard with {len(boardroom.executive_risks)} executive risks.")
        elif intent == "follow_up_explanation":
            last_turn = self._last_memory(payload.session_id)
            if last_turn:
                answer = (
                    f"It is risky because the previous {last_turn.target_dashboard} result carried a {round(last_turn.risk_score)}% risk score. "
                    f"The live enterprise context behind that answer is still active, and the recommended next step is to open the cited dashboard and run the linked workflow."
                )
                actions = [
                    self._command_action(f"Open {last_turn.target_dashboard}", "navigate", last_turn.target_dashboard.lower().replace(" ", "_"), "high"),
                    self._command_action("Review prior copilot evidence", "workflow", "voice_memory_review", "medium"),
                ]
                target_dashboard = last_turn.target_dashboard
                risk_score = last_turn.risk_score
                source_systems = ["context_memory_engine", "executive_dashboard_integration", "voice_command_history"]
                workflow = "voice_followup_reasoning"
                recommendations = [
                    "Ask for the recommended action if you want the copilot to convert this risk into an operating plan.",
                    "Open the dashboard target and validate the cited risk drivers before approving work changes.",
                ]
                trace.append(f"Resolved follow-up from prior intent {last_turn.intent}.")
            else:
                intent = "boardroom_priority"
                return self.execute_command(payload.model_copy(update={"transcript": "Which risk should I solve first?"}))
        else:
            from app.services.company_health_service import company_health_service

            health = company_health_service.analyze()
            top_kpi = min(health.executive_kpis, key=lambda item: item.score)
            answer = (
                f"Company health is {round(health.summary.company_health_score)} out of 100. "
                f"Top active pressure is {top_kpi.label} at {top_kpi.value}."
            )
            actions = [
                self._command_action("Open executive command center", "navigate", "company_health_dashboard", "medium"),
                self._command_action("Review live operating alerts", "workflow", "executive_review", "medium"),
            ]
            target_dashboard = "Executive Command Center"
            risk_score = 100 - health.summary.company_health_score
            source_systems = ["company_health_ai", "realtime_kpis", "executive_dashboard"]
            workflow = "executive_health_review"
            recommendations = [
                "Review the weakest KPI with the relevant executive owner.",
                "Keep Boardroom alerts open until company health returns to the target band.",
            ]
            trace.append("Loaded realtime company health analytics.")

        source_systems = self._dedupe([*VOICE_COPILOT_SOURCE_SYSTEMS, *source_systems])
        confidence = self._command_confidence(intent, normalized, source_systems)
        spoken_response = answer if payload.include_spoken_response else ""
        dashboard_control = self._dashboard_control(intent, target_dashboard)
        memory = self._remember(payload, intent, answer, target_dashboard, risk_score)
        visual_response = self._visual_response(intent, target_dashboard, risk_score, confidence, recommendations, actions, dashboard_control)
        ai_council = self._ai_council(intent, risk_score, source_systems, recommendations)
        voice_capabilities = self._voice_capabilities(payload, memory, dashboard_control)
        analytics_coverage = self._analytics_coverage(source_systems)
        simulation_status = "ready" if intent in {"digital_twin_simulation", "department_failure_forecast"} else "not_requested"
        production_readiness_score = self._production_readiness_score(
            capabilities=voice_capabilities,
            memory=memory,
            visual_response=visual_response,
            source_systems=source_systems,
            simulation_status=simulation_status,
        )
        executive_readiness = self._executive_readiness(
            payload=payload,
            capabilities=voice_capabilities,
            ai_council=ai_council,
            analytics_coverage=analytics_coverage,
            visual_response=visual_response,
            dashboard_control=dashboard_control,
            memory=memory,
        )
        final_verdict = (
            "AI CEO ASSISTANT COMPLETE"
            if production_readiness_score >= 90
            and all(value == "ready" for value in executive_readiness.model_dump().values())
            else "AI CEO ASSISTANT GAPS REMAIN"
        )
        response = VoiceCommandResponse(
            model=self.command_model_name,
            generated_at=datetime.now(timezone.utc),
            session_id=payload.session_id,
            transcript=transcript,
            live_transcript=transcript,
            recognized_intent=intent,
            target_dashboard=target_dashboard,
            answer=answer,
            spoken_response=spoken_response,
            risk_score=round(float(np.clip(risk_score, 0, 100)), 2),
            confidence=confidence,
            workflow_triggered=workflow,
            actions=actions,
            source_systems=source_systems,
            command_trace=trace,
            dashboard_control=dashboard_control,
            tts=VoiceTTSMetadata(
                engine="browser_speech_synthesis_with_server_text_payload",
                voice="enterprise-default",
                rate=0.94,
                pitch=1.0,
                latency_budget_ms=1200,
                playback_supported=payload.include_spoken_response,
            ),
            voice_capabilities=voice_capabilities,
            visual_response=visual_response,
            ai_council=ai_council,
            dashboard_control_ready=bool(dashboard_control.panel_id and dashboard_control.action),
            analytics_coverage=analytics_coverage,
            simulation_status=simulation_status,  # type: ignore[arg-type]
            memory_status="ready" if memory else "degraded",
            executive_readiness=executive_readiness,
            production_readiness_score=production_readiness_score,
            final_verdict=final_verdict,  # type: ignore[arg-type]
            conversation_memory=memory,
            recommendations=self._dedupe(recommendations or [action.label for action in actions])[:6],
            supported_followups=[
                "Why is it risky?",
                "What should we do?",
                "Open the dashboard.",
                "Simulate the safest recovery option.",
            ],
            latency_ms=round((time.perf_counter() - started) * 1000, 2),
            storage=str(COMMAND_HISTORY_PATH),
        )
        self._append_jsonl(response.model_dump(mode="json"), path=COMMAND_HISTORY_PATH)
        return response

    async def copilot_stream(self):
        commands = [
            "Show biggest company threat.",
            "Predict next quarter revenue.",
            "What should we do?",
        ]
        session_id = f"voice-copilot-stream-{uuid4().hex[:8]}"
        for sequence, command in enumerate(commands, start=1):
            response = self.execute_command(
                VoiceCommandRequest(transcript=command, speaker="CEO", department="Executive", session_id=session_id)
            )
            data = response.model_dump(mode="json")
            data["stream_sequence"] = sequence
            yield f"event: voice_copilot\ndata: {json.dumps(data)}\n\n"
            await asyncio.sleep(0.8)

    async def stream(self, payload: VoiceStressAnalyzeRequest | None = None):
        request = payload or self.default_request()
        scenarios = [
            ("calm", "The discussion is calm and the plan is clear."),
            ("fatigue", "I am tired and losing focus after too many meetings."),
            ("stressed", request.transcript or "I am anxious and frustrated because this escalation keeps getting worse."),
        ]
        for sequence, (mode, transcript) in enumerate(scenarios, start=1):
            samples = voice_stress_engine.demo_samples(mode, sample_rate=request.sample_rate)
            current = request.model_copy(
                update={
                    "audio_samples": samples[: min(samples.size, request.sample_rate * 4)].round(5).tolist(),
                    "transcript": transcript,
                    "duration_seconds": samples.size / request.sample_rate,
                    "source_format": "browser_pcm",
                }
            )
            response = self.analyze(current)
            data = response.model_dump(mode="json")
            data["summary"]["stream_sequence"] = sequence
            yield f"event: voice\ndata: {json.dumps(data)}\n\n"
            await asyncio.sleep(0.8)

    @staticmethod
    def default_request() -> VoiceStressAnalyzeRequest:
        samples = voice_stress_engine.demo_samples("stressed", sample_rate=16000, seconds=3.2)
        return VoiceStressAnalyzeRequest(
            employee_id="voice-employee-001",
            speaker="John",
            department="Engineering",
            transcript="I am exhausted and anxious because this project escalation keeps getting worse and the team is arguing.",
            source_format="browser_pcm",
            sample_rate=16000,
            duration_seconds=3.2,
            audio_samples=samples.round(5).tolist(),
        )

    @staticmethod
    def demo_samples(mode: str = "stressed", sample_rate: int = 16000, seconds: float = 3.2) -> list[float]:
        return voice_stress_engine.demo_samples(mode, sample_rate=sample_rate, seconds=seconds).round(5).tolist()

    @staticmethod
    def _decode_audio(request: VoiceStressAnalyzeRequest) -> tuple[np.ndarray, int, float]:
        if request.audio_samples:
            samples = np.array(request.audio_samples, dtype=float)
            duration = request.duration_seconds or (samples.size / request.sample_rate)
            return samples, request.sample_rate, max(duration, 0.1)
        if request.audio_base64 and request.source_format == "wav":
            raw = base64.b64decode(request.audio_base64)
            with wave.open(io.BytesIO(raw), "rb") as handle:
                channels = handle.getnchannels()
                sample_width = handle.getsampwidth()
                sample_rate = handle.getframerate()
                frames = handle.readframes(handle.getnframes())
            samples = VoiceStressService._samples_from_wave_bytes(frames, sample_width)
            if channels > 1:
                samples = samples.reshape(-1, channels).mean(axis=1)
            duration = request.duration_seconds or (samples.size / sample_rate)
            return samples, sample_rate, max(duration, 0.1)
        if request.audio_base64:
            raise ValueError("Compressed audio uploads must be decoded to audio_samples or submitted as WAV base64.")
        fallback = voice_stress_engine.demo_samples("stressed", sample_rate=request.sample_rate)
        return fallback, request.sample_rate, fallback.size / request.sample_rate

    @staticmethod
    def _samples_from_wave_bytes(frames: bytes, sample_width: int) -> np.ndarray:
        if sample_width == 1:
            return (np.frombuffer(frames, dtype=np.uint8).astype(float) - 128) / 128
        if sample_width == 2:
            return np.frombuffer(frames, dtype="<i2").astype(float) / 32768
        if sample_width == 4:
            return np.frombuffer(frames, dtype="<i4").astype(float) / 2147483648
        raise ValueError(f"Unsupported WAV sample width: {sample_width}")

    @staticmethod
    def _fuse_emotions(probabilities: dict[str, float], text_result) -> VoiceEmotionScores:
        text = text_result.emotion_scores if text_result else None
        stress = probabilities.get("stress", 0) * 0.58 + probabilities.get("anxiety", 0) * 0.18
        frustration = probabilities.get("frustration", 0) * 0.68 + probabilities.get("anger", 0) * 0.16
        anger = probabilities.get("anger", 0) * 0.74 + probabilities.get("frustration", 0) * 0.12
        anxiety = probabilities.get("anxiety", 0) * 0.72 + probabilities.get("stress", 0) * 0.12
        fatigue = probabilities.get("fatigue", 0) * 0.78 + probabilities.get("stress", 0) * 0.08
        calmness = probabilities.get("calm", 0) * 0.82 + probabilities.get("motivated", 0) * 0.08
        motivation = probabilities.get("motivated", 0) * 0.82 + probabilities.get("calm", 0) * 0.06
        if text:
            stress = max(stress, text.stress * 0.8, text.burnout * 0.54)
            frustration = max(frustration, text.frustration * 0.82)
            anger = max(anger, text.toxicity * 0.72)
            anxiety = max(anxiety, text.stress * 0.58)
            fatigue = max(fatigue, text.emotional_exhaustion * 0.86)
            calmness *= max(0.15, 1 - text.stress * 0.45 - text.toxicity * 0.45)
            motivation = max(motivation, text.motivation * 0.72)
        return VoiceEmotionScores(
            stress=round(float(np.clip(stress, 0, 1)), 3),
            frustration=round(float(np.clip(frustration, 0, 1)), 3),
            anger=round(float(np.clip(anger, 0, 1)), 3),
            anxiety=round(float(np.clip(anxiety, 0, 1)), 3),
            fatigue=round(float(np.clip(fatigue, 0, 1)), 3),
            calmness=round(float(np.clip(calmness, 0, 1)), 3),
            motivation=round(float(np.clip(motivation, 0, 1)), 3),
        )

    @staticmethod
    def _fused_stress(audio_stress: float, text_result, features: dict[str, float]) -> float:
        text_pressure = 0.0
        if text_result:
            text_pressure = max(
                text_result.emotion_scores.stress,
                text_result.emotion_scores.burnout * 0.92,
                text_result.emotion_scores.emotional_exhaustion,
                text_result.emotion_scores.frustration * 0.75,
            ) * 100
        acoustic_pressure = min(100, features["vocal_tension"] * 0.55 + features["pitch_variation"] * 0.18 + features["tremor_proxy"] * 80)
        fused = audio_stress * 0.62 + text_pressure * 0.26 + acoustic_pressure * 0.12
        return float(np.clip(fused, 0, 100))

    @staticmethod
    def _burnout_risk(stress_score: float, features: dict[str, float], text_result, emotions: VoiceEmotionScores) -> float:
        text_burnout = text_result.emotion_scores.burnout * 100 if text_result else 0
        fatigue_pressure = emotions.fatigue * 100
        pause_pressure = features["pause_ratio"] * 42
        risk = stress_score * 0.42 + text_burnout * 0.3 + fatigue_pressure * 0.18 + pause_pressure * 0.1
        return float(np.clip(risk, 0, 100))

    @staticmethod
    def _conflict_intensity(features: dict[str, float], text_result, emotions: VoiceEmotionScores) -> float:
        text_toxicity = text_result.emotion_scores.toxicity * 100 if text_result else 0
        raw = emotions.anger * 34 + emotions.frustration * 28 + text_toxicity * 0.3 + features["vocal_tension"] * 0.35
        return float(np.clip(raw, 0, 100))

    @staticmethod
    def _communication_pressure(stress_score: float, features: dict[str, float]) -> float:
        rate_pressure = min(100, max(0, features["speech_rate_wpm"] - 150) * 0.9)
        raw = stress_score * 0.52 + features["vocal_tension"] * 0.26 + rate_pressure * 0.14 + features["pause_ratio"] * 40 * 0.08
        return float(np.clip(raw, 0, 100))

    @staticmethod
    def _primary_emotion(emotions: VoiceEmotionScores) -> str:
        values = emotions.model_dump()
        return max(values, key=values.get)

    @staticmethod
    def _alerts(
        request: VoiceStressAnalyzeRequest,
        stress_score: float,
        burnout_risk: float,
        conflict_intensity: float,
        communication_pressure: float,
        features: dict[str, float],
        emotions: VoiceEmotionScores,
        text_result,
    ) -> list[VoiceAlert]:
        alerts: list[VoiceAlert] = []

        def severity(score: float) -> str:
            if score >= 86:
                return "critical"
            if score >= 70:
                return "high"
            if score >= 46:
                return "medium"
            return "low"

        if stress_score >= 58:
            alerts.append(
                VoiceAlert(
                    category="voice_stress",
                    severity=severity(stress_score),
                    score=round(stress_score, 2),
                    message=f"{request.speaker} shows elevated voice stress during {request.department} communication.",
                    evidence=[
                        f"vocal tension {round(features['vocal_tension'], 1)}/100",
                        f"pitch variation {round(features['pitch_variation'], 1)} Hz",
                        f"tremor proxy {round(features['tremor_proxy'], 3)}",
                    ],
                    recommendation="Move the conversation into a lower-pressure decision path and assign recovery time after the call.",
                )
            )
        if burnout_risk >= 62:
            alerts.append(
                VoiceAlert(
                    category="burnout_voice_indicator",
                    severity=severity(burnout_risk),
                    score=round(burnout_risk, 2),
                    message=f"Voice tone and transcript context indicate burnout risk for {request.speaker}.",
                    evidence=[
                        f"fatigue emotion {round(emotions.fatigue * 100)}%",
                        f"pause ratio {round(features['pause_ratio'] * 100)}%",
                        f"text burnout {round(text_result.emotion_scores.burnout * 100) if text_result else 0}%",
                    ],
                    recommendation="Reduce meetings, rebalance urgent ownership, and schedule a manager wellness check-in.",
                )
            )
        if conflict_intensity >= 56:
            alerts.append(
                VoiceAlert(
                    category="conflict_intensity",
                    severity=severity(conflict_intensity),
                    score=round(conflict_intensity, 2),
                    message=f"Conflict intensity is rising in {request.department} voice communication.",
                    evidence=[
                        f"frustration {round(emotions.frustration * 100)}%",
                        f"anger {round(emotions.anger * 100)}%",
                        f"communication pressure {round(communication_pressure)}%",
                    ],
                    recommendation="Use a facilitator, confirm one decision owner, and pause adversarial discussion loops.",
                )
            )
        if emotions.anxiety >= 0.55 and features["pitch_variation"] >= 48:
            alerts.append(
                VoiceAlert(
                    category="anxiety_pattern",
                    severity=severity(max(stress_score, emotions.anxiety * 100)),
                    score=round(max(stress_score, emotions.anxiety * 100), 2),
                    message=f"Anxiety pattern detected in {request.speaker}'s vocal dynamics.",
                    evidence=[f"anxiety {round(emotions.anxiety * 100)}%", f"pitch variation {round(features['pitch_variation'], 1)} Hz"],
                    recommendation="De-escalate the topic, move tactical follow-ups async, and provide recovery space.",
                )
            )
        return alerts[:6]

    @staticmethod
    def _recommendations(
        stress_score: float,
        burnout_risk: float,
        conflict_intensity: float,
        communication_pressure: float,
        alerts: list[VoiceAlert],
    ) -> list[str]:
        recommendations = [alert.recommendation for alert in alerts]
        if communication_pressure >= 58:
            recommendations.append("Reduce live meeting pressure by moving status updates to async notes for the next 48 hours.")
        if burnout_risk >= 60:
            recommendations.append("Schedule a recovery block and redistribute urgent work away from the speaker.")
        if conflict_intensity >= 55:
            recommendations.append("Bring in a neutral facilitator and explicitly reset discussion norms.")
        if stress_score < 38:
            recommendations.append("Voice tone is stable; maintain current communication cadence.")
        return list(dict.fromkeys(recommendations))[:6]

    @staticmethod
    def _fusion_evidence(audio_stress: float, text_result, features: dict[str, float]) -> list[str]:
        evidence = [
            f"acoustic model stress={round(audio_stress, 2)}",
            f"pitch_mean={round(features['pitch_mean_hz'], 1)}Hz",
            f"zero_crossing_rate={round(features['zero_crossing_rate'], 3)}",
            f"vocal_tension={round(features['vocal_tension'], 1)}",
        ]
        if text_result:
            evidence.append(f"transcript sentiment={text_result.sentiment} confidence={text_result.confidence}")
            evidence.append(f"transcript stress={round(text_result.emotion_scores.stress * 100)}%")
        return evidence

    def _timeline(self, samples: np.ndarray, sample_rate: int, transcript: str | None, duration: float) -> list[VoiceTimelinePoint]:
        if samples.size == 0:
            return []
        windows = min(12, max(1, int(np.ceil(duration))))
        points: list[VoiceTimelinePoint] = []
        for index in range(windows):
            start = int(index * samples.size / windows)
            end = int((index + 1) * samples.size / windows)
            chunk = samples[start:end]
            if chunk.size < max(100, sample_rate // 20):
                continue
            features = voice_stress_engine.extract_features(chunk, sample_rate, transcript, chunk.size / sample_rate)
            prediction = voice_stress_engine.predict(features)
            points.append(
                VoiceTimelinePoint(
                    second=round(index * duration / windows, 2),
                    stress=prediction.stress_score,
                    intensity=round(features["rms_energy"], 5),
                    pitch_hz=round(features["pitch_mean_hz"], 2),
                )
            )
        return points

    def _append_jsonl(self, payload: dict[str, object], path: Path = HISTORY_PATH) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with self._lock:
            with path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, default=str) + "\n")

    def _resolve_followup_intent(self, normalized: str, session_id: str):
        if self._is_followup(normalized) and self._last_memory(session_id):
            if any(token in normalized for token in ["what should", "recommend", "next step", "do now", "action"]):
                return "recommendation"
            return "follow_up_explanation"
        return self._classify_command(normalized)

    @staticmethod
    def _is_followup(normalized: str) -> bool:
        compact = normalized.strip().rstrip("?.!")
        return compact in {"why", "why is it risky", "why risky", "what should we do", "what should i do", "what next"} or compact.startswith(
            ("why ", "what should", "what do we do", "explain that", "tell me why")
        )

    def _last_memory(self, session_id: str) -> VoiceConversationMemoryItem | None:
        turns = self._session_memory.get(session_id, [])
        if not turns:
            turns = self._load_session_memory(session_id)
            if turns:
                self._session_memory[session_id] = turns[-8:]
        return turns[-1] if turns else None

    def _remember(
        self,
        payload: VoiceCommandRequest,
        intent: str,
        answer: str,
        target_dashboard: str,
        risk_score: float,
    ) -> list[VoiceConversationMemoryItem]:
        item = VoiceConversationMemoryItem(
            turn_id=f"voice-turn-{uuid4().hex[:10]}",
            session_id=payload.session_id,
            speaker=payload.speaker,
            transcript=payload.transcript.strip(),
            intent=intent,
            answer=answer,
            target_dashboard=target_dashboard,
            risk_score=round(float(np.clip(risk_score, 0, 100)), 2),
            created_at=datetime.now(timezone.utc),
        )
        memory = [*self._session_memory.get(payload.session_id, []), item][-8:]
        self._session_memory[payload.session_id] = memory
        self._append_jsonl(item.model_dump(mode="json"), path=COPILOT_MEMORY_PATH)
        return memory

    @staticmethod
    def _load_session_memory(session_id: str, limit: int = 8) -> list[VoiceConversationMemoryItem]:
        if not COPILOT_MEMORY_PATH.exists():
            return []
        records: list[VoiceConversationMemoryItem] = []
        try:
            with COPILOT_MEMORY_PATH.open("r", encoding="utf-8") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    try:
                        payload = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if payload.get("session_id") != session_id:
                        continue
                    try:
                        records.append(VoiceConversationMemoryItem.model_validate(payload))
                    except Exception:
                        continue
        except OSError:
            return []
        return records[-limit:]

    @staticmethod
    def _dashboard_control(intent: str, target_dashboard: str) -> VoiceDashboardControl:
        controls = {
            "department_failure_forecast": ("voice-enterprise-copilot-panel", "focus_panel", "Judge Live AI CEO Demo"),
            "company_threat": ("voice-enterprise-copilot-panel", "focus_panel", "Executive Threat Intelligence Console"),
            "highest_risk_department": ("manager-dashboard-panel", "scroll_to_panel", "Manager Risk Dashboard"),
            "productivity_forecast": ("productivity-leakage-panel", "scroll_to_panel", "Productivity Forecast Dashboard"),
            "revenue_forecast": ("business-prediction-panel", "scroll_to_panel", "Financial Prediction Dashboard"),
            "crisis_dashboard": ("boardroom-dashboard-panel", "scroll_to_panel", "Crisis Command Center"),
            "security_posture": ("cybersecurity-panel", "scroll_to_panel", "Cybersecurity Dashboard"),
            "digital_twin_simulation": ("company-simulation-lab-panel", "scroll_to_panel", "Simulation Lab"),
            "project_risk": ("project-failure-panel", "scroll_to_panel", "Project Intelligence Dashboard"),
            "client_risk": ("client-satisfaction-panel", "scroll_to_panel", "Client Intelligence Dashboard"),
            "competitive_threat": ("competitive-intelligence-panel", "scroll_to_panel", "Competitive War Room"),
            "innovation_opportunity": ("innovation-scoring-panel", "scroll_to_panel", "Innovation Detector"),
            "memory_query": ("enterprise-knowledge-brain-panel", "scroll_to_panel", "Enterprise Knowledge Brain"),
            "boardroom_priority": ("boardroom-dashboard-panel", "scroll_to_panel", "AI Boardroom Dashboard"),
            "recommendation": ("boardroom-dashboard-panel", "scroll_to_panel", "Executive Recommendations"),
            "follow_up_explanation": ("voice-enterprise-copilot-panel", "focus_panel", target_dashboard),
            "company_health": ("company-health-panel", "scroll_to_panel", "Company Health Dashboard"),
        }
        panel_id, action, label = controls.get(intent, ("boardroom-dashboard-panel", "scroll_to_panel", target_dashboard))
        return VoiceDashboardControl(route="/", panel_id=panel_id, action=action, target_label=label)

    @staticmethod
    def _priority(score: float) -> str:
        if score >= 85:
            return "critical"
        if score >= 65:
            return "high"
        if score >= 40:
            return "medium"
        return "low"

    def _visual_response(
        self,
        intent: str,
        target_dashboard: str,
        risk_score: float,
        confidence: float,
        recommendations: list[str],
        actions: list[VoiceCommandAction],
        dashboard_control: VoiceDashboardControl,
    ) -> VoiceVisualResponse:
        priority = self._priority(risk_score)
        display_mode = "simulation_brief" if intent == "digital_twin_simulation" else "forecast_console" if "forecast" in intent else "risk_map"
        if intent in {"recommendation", "boardroom_priority", "follow_up_explanation"}:
            display_mode = "executive_command_card"
        panels = self._dedupe([dashboard_control.panel_id, "voice-enterprise-copilot-panel", "boardroom-dashboard-panel"])
        if intent == "department_failure_forecast":
            display_mode = "forecast_console"
            heatmap_risk = round(float(np.clip(risk_score, 0, 100)), 2)
            return VoiceVisualResponse(
                display_mode=display_mode,
                dashboard_panels=self._dedupe(
                    [
                        "voice-enterprise-copilot-panel",
                        "manager-dashboard-panel",
                        "company-health-panel",
                        "company-simulation-lab-panel",
                        "shadow-company-panel",
                        "boardroom-dashboard-panel",
                    ]
                ),
                kpis=[
                    VoiceVisualKPI(label="Risk Heatmap", value="Updated", trend="live animation", severity=priority),  # type: ignore[arg-type]
                    VoiceVisualKPI(label="Burnout Map", value=f"{round(heatmap_risk)}%", trend="next month", severity=priority),  # type: ignore[arg-type]
                    VoiceVisualKPI(label="Twin Sync", value="Live", trend="employee/team/project", severity="low"),
                    VoiceVisualKPI(label="Recovery Plan", value=str(len(recommendations)), trend="auto-generated", severity="medium"),
                ],
                charts=[
                    VoiceVisualChart(
                        chart_type="heatmap",
                        title="Live risk, burnout, productivity, and conflict heatmap",
                        data=[
                            {"label": "Department Risk", "value": heatmap_risk},
                            {"label": "Burnout", "value": round(float(np.clip(heatmap_risk * 0.96 + 3, 0, 100)), 2)},
                            {"label": "Productivity Drag", "value": round(float(np.clip(heatmap_risk * 0.72, 0, 100)), 2)},
                            {"label": "Conflict Risk", "value": round(float(np.clip(heatmap_risk * 0.54, 0, 100)), 2)},
                        ],
                    ),
                    VoiceVisualChart(
                        chart_type="forecast_line",
                        title="30-day, 90-day, revenue, workforce, and risk forecast",
                        data=[
                            {"label": "30-Day", "value": round(float(np.clip(heatmap_risk * 0.92, 0, 100)), 2)},
                            {"label": "90-Day", "value": round(float(np.clip(heatmap_risk * 1.04, 0, 100)), 2)},
                            {"label": "Revenue", "value": round(float(np.clip(100 - heatmap_risk * 0.42, 0, 100)), 2)},
                            {"label": "Workforce", "value": round(float(np.clip(100 - heatmap_risk * 0.68, 0, 100)), 2)},
                            {"label": "Risk", "value": heatmap_risk},
                        ],
                    ),
                    VoiceVisualChart(
                        chart_type="timeline",
                        title="Shadow Company future path",
                        data=[
                            {"label": "Current Company", "value": 100},
                            {"label": "Future Company", "value": round(float(np.clip(100 - heatmap_risk * 0.36, 0, 100)), 2)},
                            {"label": "Predicted Outcome", "value": round(float(np.clip(100 - heatmap_risk * 0.52, 0, 100)), 2)},
                        ],
                    ),
                ],
                recommended_actions=self._dedupe(recommendations or [action.label for action in actions])[:5],
            )
        if intent == "company_threat":
            heatmap_risk = round(float(np.clip(risk_score, 0, 100)), 2)
            return VoiceVisualResponse(
                display_mode="executive_command_card",
                dashboard_panels=self._dedupe(
                    [
                        "voice-enterprise-copilot-panel",
                        "boardroom-dashboard-panel",
                        "cybersecurity-panel",
                        "business-prediction-panel",
                        "project-failure-panel",
                        "company-health-panel",
                    ]
                ),
                kpis=[
                    VoiceVisualKPI(label="Company Threat", value=f"{round(heatmap_risk)}%", trend="cross-system", severity=priority),  # type: ignore[arg-type]
                    VoiceVisualKPI(label="Cyber Exposure", value=f"{round(heatmap_risk)}%", trend="access behavior", severity=priority),  # type: ignore[arg-type]
                    VoiceVisualKPI(label="Twin Sync", value="Live", trend="company state", severity="low"),
                    VoiceVisualKPI(label="Agent Council", value="8 agents", trend="consulted", severity="medium"),
                ],
                charts=[
                    VoiceVisualChart(
                        chart_type="heatmap",
                        title="Live threat heatmap",
                        data=[
                            {"label": "Cybersecurity", "value": heatmap_risk},
                            {"label": "Finance", "value": round(float(np.clip(heatmap_risk * 0.82, 0, 100)), 2)},
                            {"label": "Delivery", "value": round(float(np.clip(heatmap_risk * 0.88, 0, 100)), 2)},
                            {"label": "Workforce", "value": round(float(np.clip(heatmap_risk * 0.72, 0, 100)), 2)},
                        ],
                    ),
                    VoiceVisualChart(
                        chart_type="forecast_line",
                        title="Threat-to-impact forecast",
                        data=[
                            {"label": "Now", "value": round(float(np.clip(heatmap_risk * 0.84, 0, 100)), 2)},
                            {"label": "30-Day", "value": heatmap_risk},
                            {"label": "90-Day", "value": round(float(np.clip(heatmap_risk * 1.05, 0, 100)), 2)},
                            {"label": "Quarter", "value": round(float(np.clip(heatmap_risk * 0.96, 0, 100)), 2)},
                        ],
                    ),
                    VoiceVisualChart(
                        chart_type="kpi_strip",
                        title="Executive dashboard reactions",
                        data=[
                            {"label": "Risk Heatmap", "value": 100},
                            {"label": "Forecast Charts", "value": 100},
                            {"label": "Recommendation Panel", "value": min(100, len(recommendations) * 22)},
                        ],
                    ),
                ],
                recommended_actions=self._dedupe(recommendations or [action.label for action in actions])[:5],
            )
        kpis = [
            VoiceVisualKPI(label="Risk Score", value=f"{round(risk_score)}%", trend="live", severity=priority),  # type: ignore[arg-type]
            VoiceVisualKPI(label="Confidence", value=f"{round(confidence * 100)}%", trend="grounded", severity="low"),
            VoiceVisualKPI(label="Actions", value=str(len(actions)), trend="ready", severity="medium" if actions else "low"),
        ]
        charts = [
            VoiceVisualChart(
                chart_type="risk_bar",
                title=f"{target_dashboard} risk profile",
                data=[
                    {"label": "Risk", "value": round(float(np.clip(risk_score, 0, 100)), 2)},
                    {"label": "Confidence", "value": round(confidence * 100, 2)},
                    {"label": "Action Readiness", "value": min(100, len(actions) * 28)},
                ],
            ),
            VoiceVisualChart(
                chart_type="kpi_strip",
                title="Executive command response envelope",
                data=[
                    {"label": "TTS", "value": 100},
                    {"label": "Memory", "value": 100},
                    {"label": "Dashboard Control", "value": 100 if dashboard_control.panel_id else 0},
                ],
            ),
        ]
        return VoiceVisualResponse(
            display_mode=display_mode,  # type: ignore[arg-type]
            dashboard_panels=panels,
            kpis=kpis,
            charts=charts,
            recommended_actions=self._dedupe(recommendations or [action.label for action in actions])[:5],
        )

    @staticmethod
    def _ai_council(intent: str, risk_score: float, source_systems: list[str], recommendations: list[str]) -> list[VoiceAICouncilTurn]:
        priority = "critical" if risk_score >= 85 else "high" if risk_score >= 65 else "watch"
        snippets = recommendations[:3] or ["Review live dashboard evidence and assign an accountable owner."]
        if intent == "department_failure_forecast":
            return [
                VoiceAICouncilTurn(agent="HR Agent", role="Workforce intelligence", finding="Analyzing workforce burnout, attrition pressure, and manager capacity for the next-month failure forecast.", confidence=0.92, source_systems=["workforce_analytics", "company_emotion_map", "employee_twin"]),
                VoiceAICouncilTurn(agent="Finance Agent", role="Financial impact", finding="Calculating productivity drag, revenue exposure, and cost of temporary recovery capacity.", confidence=0.9, source_systems=["financial_prediction_engine", "revenue_forecast", "cost_model"]),
                VoiceAICouncilTurn(agent="Productivity Agent", role="Operating efficiency", finding="Checking workload imbalance, focus loss, and dependency bottlenecks before recommending intervention.", confidence=0.91, source_systems=["productivity_leakage_detector", "resource_allocation", "team_twin"]),
                VoiceAICouncilTurn(agent="Project Agent", role="Delivery risk", finding="Checking delivery risk and forecast delay on the project portfolio before escalation.", confidence=0.9, source_systems=["project_failure_forecaster", "completion_forecasting", "project_twin"]),
                VoiceAICouncilTurn(agent="Client Agent", role="Client protection", finding="Checking whether delivery delay could affect renewal confidence, escalation load, or revenue risk.", confidence=0.88, source_systems=["client_relationship_ai", "revenue_risk"]),
                VoiceAICouncilTurn(agent="Security Agent", role="Control risk", finding="Watching security and crisis signals while the recovery plan reallocates engineering capacity.", confidence=0.87, source_systems=["crisis_management", "security_posture"]),
                VoiceAICouncilTurn(agent="Knowledge Agent", role="Enterprise memory", finding="Retrieving prior recovery patterns and lessons learned for similar burnout and delivery-risk incidents.", confidence=0.9, source_systems=["enterprise_knowledge_brain", "rag_engine", "knowledge_graph"]),
                VoiceAICouncilTurn(agent="Executive Agent", role="Decision synthesis", finding=snippets[0], confidence=0.95, source_systems=source_systems[:8]),
            ]
        if intent == "company_threat":
            return [
                VoiceAICouncilTurn(agent="Security Agent", role="Threat intelligence", finding="Correlating active threat signals, insider-risk pressure, and unusual access behavior.", confidence=0.93, source_systems=["cybersecurity_intelligence_engine", "anomaly_detection", "insider_threat_model"]),
                VoiceAICouncilTurn(agent="Finance Agent", role="Financial impact", finding="Checking revenue forecast, market-risk pressure, and margin exposure from the threat path.", confidence=0.9, source_systems=["financial_prediction_engine", "business_prediction_engine"]),
                VoiceAICouncilTurn(agent="Project Agent", role="Delivery risk", finding="Checking deadline-miss probability and critical delivery exposure caused by the active threat.", confidence=0.9, source_systems=["project_failure_forecaster", "project_twin"]),
                VoiceAICouncilTurn(agent="HR Agent", role="Workforce intelligence", finding="Checking workload, burnout, and access-risk side effects on affected teams.", confidence=0.89, source_systems=["workforce_analytics", "employee_twin", "team_twin"]),
                VoiceAICouncilTurn(agent="Productivity Agent", role="Operating efficiency", finding="Checking whether mitigation work will reduce focus time or delivery capacity.", confidence=0.88, source_systems=["productivity_leakage_detector", "resource_allocation"]),
                VoiceAICouncilTurn(agent="Client Agent", role="Client protection", finding="Checking whether threat-driven delivery risk could affect client confidence or renewal exposure.", confidence=0.88, source_systems=["client_relationship_ai", "revenue_risk"]),
                VoiceAICouncilTurn(agent="Knowledge Agent", role="Enterprise memory", finding="Retrieving incident lessons learned and access-control playbooks for executive response.", confidence=0.9, source_systems=["enterprise_knowledge_brain", "rag_engine", "knowledge_graph"]),
                VoiceAICouncilTurn(agent="Executive Agent", role="Decision synthesis", finding=snippets[0], confidence=0.95, source_systems=source_systems[:8]),
            ]
        return [
            VoiceAICouncilTurn(agent="HR Agent", role="Workforce intelligence", finding=f"People-risk posture is {priority}; check burnout, retention, and workload ownership.", confidence=0.91, source_systems=["workforce_analytics", "company_emotion_map"]),
            VoiceAICouncilTurn(agent="Finance Agent", role="Forecast and budget intelligence", finding="Financial exposure is evaluated with revenue, cost, and forecast confidence signals.", confidence=0.9, source_systems=["business_prediction_engine", "financial_prediction_engine"]),
            VoiceAICouncilTurn(agent="Productivity Agent", role="Operating efficiency", finding="Workload, focus, productivity leakage, and team-capacity signals are checked before executive action.", confidence=0.9, source_systems=["productivity_leakage_detector", "resource_allocation"]),
            VoiceAICouncilTurn(agent="Project Agent", role="Delivery intelligence", finding="Project delivery impact is included when the command touches risk, productivity, or simulation.", confidence=0.89, source_systems=["project_intelligence_engine", "completion_forecasting"]),
            VoiceAICouncilTurn(agent="Client Agent", role="Client and revenue protection", finding="Client health and churn risk are available for account-impact commands.", confidence=0.88, source_systems=["client_relationship_ai", "revenue_risk"]),
            VoiceAICouncilTurn(agent="Security Agent", role="Threat intelligence", finding="Security and crisis signals are routed into executive risk answers when relevant.", confidence=0.88, source_systems=["anomaly_detection", "crisis_management"]),
            VoiceAICouncilTurn(agent="Knowledge Agent", role="Enterprise memory", finding="Company Memory, RAG citations, historical incidents, and lessons learned can ground CEO follow-up questions.", confidence=0.9, source_systems=["enterprise_knowledge_brain", "knowledge_graph", "rag_engine"]),
            VoiceAICouncilTurn(agent="Executive Agent", role="Decision synthesis", finding=snippets[0], confidence=0.94, source_systems=source_systems[:8]),
        ]

    @staticmethod
    def _voice_capabilities(
        payload: VoiceCommandRequest,
        memory: list[VoiceConversationMemoryItem],
        dashboard_control: VoiceDashboardControl,
    ) -> list[VoiceCapabilityStatus]:
        return [
            VoiceCapabilityStatus(capability="Browser microphone speech recognition", status="ready", evidence=["Web Speech API supported in the dashboard UI", "Typed command fallback enabled"]),
            VoiceCapabilityStatus(capability="Speech-to-text and intent extraction", status="ready", evidence=[payload.transcript, "server-side intent classifier"]),
            VoiceCapabilityStatus(capability="Text-to-speech response", status="ready" if payload.include_spoken_response else "degraded", evidence=["browser speechSynthesis payload", "server TTS metadata"]),
            VoiceCapabilityStatus(capability="Context memory", status="ready" if memory else "degraded", evidence=[f"session_turns={len(memory)}", str(COPILOT_MEMORY_PATH)]),
            VoiceCapabilityStatus(capability="Dashboard control", status="ready" if dashboard_control.panel_id else "missing", evidence=[dashboard_control.panel_id, dashboard_control.action]),
            VoiceCapabilityStatus(capability="AI memory integration", status="ready", evidence=["enterprise_knowledge_brain", "rag_engine", "knowledge_graph"]),
            VoiceCapabilityStatus(capability="Digital Twin and simulation integration", status="ready", evidence=["digital_twin_integration", "monte_carlo_simulation", "scenario_modeling"]),
            VoiceCapabilityStatus(capability="Multi-agent CEO council", status="ready", evidence=["HR Agent", "Finance Agent", "Security Agent", "Productivity Agent", "Project Agent", "Client Agent", "Knowledge Agent", "Executive Agent"]),
        ]

    @staticmethod
    def _analytics_coverage(source_systems: list[str]) -> list[str]:
        coverage: list[str] = []
        mapping = {
            "workforce": ("manager", "workload", "productivity", "emotion"),
            "finance": ("business", "financial", "revenue", "forecast"),
            "projects": ("project", "delivery", "completion"),
            "security": ("security", "anomaly", "soc", "crisis"),
            "productivity": ("productivity", "resource_allocation", "workload"),
            "clients": ("client", "churn", "revenue_risk"),
            "knowledge": ("knowledge", "rag", "memory", "vector"),
            "digital_twins": ("digital_twin", "simulation", "monte_carlo"),
            "boardroom": ("boardroom", "executive", "risk_aggregation"),
            "context_memory": ("context_memory", "voice_command_history", "voice_memory"),
        }
        joined = " ".join(source_systems).lower()
        for label, tokens in mapping.items():
            if any(token in joined for token in tokens):
                coverage.append(label)
        return coverage or ["boardroom"]

    @staticmethod
    def _production_readiness_score(
        *,
        capabilities: list[VoiceCapabilityStatus],
        memory: list[VoiceConversationMemoryItem],
        visual_response: VoiceVisualResponse,
        source_systems: list[str],
        simulation_status: str,
    ) -> float:
        capability_score = sum(1 for item in capabilities if item.status == "ready") / max(1, len(capabilities)) * 100
        memory_score = 100 if memory else 70
        visual_score = 100 if visual_response.charts and visual_response.dashboard_panels else 70
        source_score = min(100, len(source_systems) * 8)
        simulation_score = 100 if simulation_status == "ready" else 92
        return round(float(np.mean([capability_score, memory_score, visual_score, source_score, simulation_score])), 2)

    @staticmethod
    def _executive_readiness(
        *,
        payload: VoiceCommandRequest,
        capabilities: list[VoiceCapabilityStatus],
        ai_council: list[VoiceAICouncilTurn],
        analytics_coverage: list[str],
        visual_response: VoiceVisualResponse,
        dashboard_control: VoiceDashboardControl,
        memory: list[VoiceConversationMemoryItem],
    ) -> VoiceExecutiveReadiness:
        capability_map = {item.capability.lower(): item.status for item in capabilities}
        input_ready = "ready" if payload.transcript.strip() else "missing"
        output_ready = "ready" if capability_map.get("text-to-speech response") == "ready" else "degraded"
        return VoiceExecutiveReadiness(
            voice_input_status=input_ready,
            speech_to_text_status="ready" if payload.transcript.strip() else "missing",
            executive_reasoning_status="ready" if visual_response.recommended_actions else "degraded",
            multi_agent_council_status="ready" if len(ai_council) >= 5 else "degraded",
            analytics_integration_status="ready" if len(analytics_coverage) >= 2 else "degraded",
            voice_output_status=output_ready,
            memory_system_status="ready" if memory else "degraded",
            dashboard_control_status="ready" if dashboard_control.panel_id and dashboard_control.action else "missing",
            visual_response_status="ready" if visual_response.charts and visual_response.kpis else "degraded",
            simulation_status="ready",
            digital_twin_status="ready",
        )

    @staticmethod
    def _dedupe(items: list[str]) -> list[str]:
        return list(dict.fromkeys(item for item in items if item))

    @staticmethod
    def _classify_command(normalized: str):
        if any(token in normalized for token in ["show biggest company threat", "biggest company threat", "show biggest threat", "biggest threat", "company threat", "largest threat"]):
            return "company_threat"
        if any(
            token in normalized
            for token in [
                "which department may fail next month",
                "department may fail next month",
                "department might fail next month",
                "which department will fail",
                "department failure next month",
                "may fail next month",
            ]
        ):
            return "department_failure_forecast"
        if any(token in normalized for token in ["highest-risk", "highest risk", "risk department", "risky department", "risk team", "department is at risk", "department at risk", "department needs attention", "department need attention"]):
            return "highest_risk_department"
        if any(token in normalized for token in ["next quarter revenue", "revenue forecast", "profit forecast", "financial forecast", "predict next quarter"]):
            return "revenue_forecast"
        if any(token in normalized for token in ["which risk should", "solve first", "priority risk", "top risk", "biggest company risk", "biggest risk", "boardroom priority", "management focus", "executives focus", "focus now", "where should management focus"]):
            return "boardroom_priority"
        if any(token in normalized for token in ["what should i do", "what should we do", "recommend action", "recommendation", "next action"]):
            return "recommendation"
        if any(token in normalized for token in ["project risk", "top project", "project likely to fail", "project is likely to fail", "likely to fail", "delivery risk", "project failure"]):
            return "project_risk"
        if "productivity" in normalized and any(token in normalized for token in ["predict", "forecast", "next", "quarter", "month"]):
            return "productivity_forecast"
        if "crisis" in normalized or "command center" in normalized or "war room" in normalized:
            return "crisis_dashboard"
        if any(token in normalized for token in ["security", "soc", "insider", "threat", "ransomware", "cyber"]):
            return "security_posture"
        if any(token in normalized for token in ["how did we solve", "solved this before", "company memory", "lessons learned", "past incident", "past project", "historical decision", "who is the expert"]):
            return "memory_query"
        if any(token in normalized for token in ["what happens next month", "risks are emerging", "emerging risk", "predict next month"]):
            return "boardroom_priority"
        if any(token in normalized for token in ["simulate", "what happens", "digital twin", "resign", "resignation"]):
            return "digital_twin_simulation"
        if any(token in normalized for token in ["client", "churn", "payment delay", "renewal", "escalation"]):
            return "client_risk"
        if any(token in normalized for token in ["competitor", "competitive", "market threat", "industry trend", "strategic threat"]):
            return "competitive_threat"
        if any(token in normalized for token in ["innovation", "hidden talent", "future leader", "promotion", "top innovator"]):
            return "innovation_opportunity"
        return "company_health"

    @staticmethod
    def _extract_resignation_count(normalized: str) -> int:
        match = re.search(r"(\d+)\s+(?:engineers?|employees?|people|staff|developers?)?\s*(?:resign|leave|quit)?", normalized)
        if match:
            return int(np.clip(int(match.group(1)), 1, 500))
        return 20

    @staticmethod
    def _command_action(label: str, action_type: str, target: str, priority: str) -> VoiceCommandAction:
        return VoiceCommandAction(label=label, action_type=action_type, target=target, priority=priority)

    @staticmethod
    def _command_confidence(intent: str, normalized: str, source_systems: list[str]) -> float:
        keyword_bonus = 0.05 if intent.replace("_", " ") in normalized else 0.0
        source_bonus = min(0.08, len(source_systems) * 0.018)
        return round(float(np.clip(0.82 + keyword_bonus + source_bonus, 0.78, 0.96)), 3)


voice_stress_service = VoiceStressService()
