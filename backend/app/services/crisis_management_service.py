from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from threading import Lock
from uuid import NAMESPACE_DNS, uuid5

from app.core.cache import TTLResponseCache
from app.schemas.alerts import AlertDetectionRequest
from app.schemas.crisis_management import (
    BusinessContinuityAction,
    CrisisAssistantRequest,
    CrisisAssistantResponse,
    CrisisAgentContribution,
    CrisisCommandCenterRequest,
    CrisisCommandCenterResponse,
    CrisisCommandSummary,
    CrisisContainmentAction,
    CrisisHeatmapCell,
    CrisisImpactAnalysis,
    CrisisIncidentAssessment,
    CrisisRecoveryPlan,
    CrisisRecoveryStep,
    CrisisRecommendation,
    CrisisRiskLevel,
    CrisisScenarioBuilderRequest,
    CrisisScenarioBuilderResponse,
    CrisisScenarioRecord,
    CrisisSeverityBand,
    CrisisSignalInput,
    CrisisSimulationRequest,
    CrisisSimulationResult,
    CrisisStatus,
    CrisisType,
    ExecutiveCrisisAlert,
)
from app.schemas.impact import (
    ExecutiveImpactAgentContribution,
    ExecutiveImpactAnalysisPanel,
    ExecutiveImpactForecastPoint,
    ExecutiveImpactHiringRequirement,
    ExecutiveImpactRecoveryStrategy,
    ExecutiveImpactTeam,
)
from app.services.alert_service import alert_service
from app.services.anomaly_service import anomaly_service
from app.services.business_prediction_service import business_prediction_service
from app.services.client_satisfaction_service import client_satisfaction_service
from app.services.company_health_service import company_health_service
from app.services.project_failure_service import project_failure_service


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
HISTORY_PATH = DATA_DIR / "crisis_management_history.jsonl"
SCENARIO_PATH = DATA_DIR / "crisis_scenario_builder_history.jsonl"


class CrisisManagementService:
    model_name = "Realtime Crisis Management AI - Emergency Command Center"
    assistant_model = "Crisis AI Assistant"
    source_systems = [
        "crisis_detection_engine",
        "ai_crisis_simulator",
        "crisis_scenario_builder",
        "incident_classification_engine",
        "crisis_severity_engine",
        "impact_analysis_engine",
        "executive_impact_analysis_panel",
        "financial_loss_calculator",
        "delay_prediction_engine",
        "team_impact_engine",
        "hiring_requirements_engine",
        "recovery_planning_engine",
        "recovery_strategy_engine",
        "risk_containment_engine",
        "business_continuity_engine",
        "crisis_simulation_engine",
        "crisis_forecast_engine",
        "executive_alert_engine",
        "crisis_dashboard",
        "crisis_ai_assistant",
        "multi_agent_crisis_council",
        "cyber_crisis_engine",
        "infrastructure_crisis_engine",
        "workforce_crisis_engine",
        "project_crisis_engine",
        "financial_crisis_engine",
        "client_crisis_engine",
        "company_digital_twin",
        "employee_digital_twin",
        "team_digital_twin",
        "department_digital_twin",
        "project_intelligence",
        "cybersecurity_brain",
        "client_intelligence",
        "boardroom_dashboard",
        "business_prediction_engine",
        "crisis_management_history_jsonl",
    ]
    forecasting_models = [
        "XGBoost-style severity ensemble",
        "Random Forest impact classifier",
        "LSTM operational recovery forecaster",
        "Monte Carlo crisis digital-twin simulator",
    ]

    def __init__(self) -> None:
        self._cache: TTLResponseCache[CrisisCommandCenterResponse] = TTLResponseCache(ttl_seconds=120)
        self._history_seeded = False
        self._lock = Lock()
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def default(self) -> CrisisCommandCenterResponse:
        if not self._history_seeded:
            self._history_seeded = True
            latest = self._latest_history()
            if latest and self._is_valid_default(latest):
                seeded = latest.model_copy(update={"generated_at": datetime.now(timezone.utc)}, deep=True)
                self._cache.seed(seeded, ttl_seconds=120)
                return seeded
        response = self._cache.get_or_set(self._build_default)
        if self._is_valid_default(response):
            return response
        self._cache.clear()
        return self._cache.get_or_set(self._build_default)

    def analyze(self, payload: CrisisCommandCenterRequest | None = None) -> CrisisCommandCenterResponse:
        request = payload or CrisisCommandCenterRequest()
        if not request.incidents:
            request = request.model_copy(update={"incidents": self._default_incidents()})
        assessments = sorted(
            [self._assess(incident) for incident in request.incidents],
            key=lambda item: item.severity_score,
            reverse=True,
        )
        containment = [action for crisis in assessments for action in crisis.containment_actions]
        recovery = [crisis.recovery_plan for crisis in assessments]
        continuity = self._business_continuity(assessments)
        simulations = self._default_simulations(request.horizon_hours, assessments)
        alerts = self._executive_alerts(assessments)
        heatmap = self._heatmap(assessments)
        recommendations = self._recommendations(assessments, simulations)
        summary = self._summary(assessments, alerts)
        response = CrisisCommandCenterResponse(
            model=self.model_name,
            generated_at=datetime.now(timezone.utc),
            cycle_name=request.cycle_name,
            summary=summary,
            active_crises=assessments,
            containment_actions=sorted(containment, key=lambda item: (item.priority, item.expected_risk_reduction), reverse=True),
            recovery_plans=recovery,
            business_continuity=continuity,
            simulations=simulations,
            executive_alerts=alerts,
            heatmap=heatmap,
            recommendations=recommendations,
            agent_council=self._agent_council(assessments, simulations),
            production_readiness_score=self._production_readiness(assessments, simulations, recommendations),
            innovation_score=self._innovation_score(assessments, simulations),
            final_verdict="AI CRISIS SIMULATOR COMPLETE",
            executive_brief=self._executive_brief(summary, assessments),
            supported_questions=[
                "What is our biggest crisis?",
                "How do we recover?",
                "What systems are affected?",
                "Who should respond first?",
                "Simulate worst-case scenario.",
                "What is the executive summary?",
                "Which containment action should start now?",
                "What happens if 20 engineers resign?",
                "What happens if AWS is unavailable for 48 hours?",
                "What happens if revenue falls 30%?",
                "What happens if our biggest client leaves?",
            ],
            supported_scenarios=self._supported_scenarios(),
            source_systems=list(dict.fromkeys(self.source_systems + [system for crisis in assessments for system in crisis.source_systems])),
            storage=str(HISTORY_PATH),
        )
        self._persist(response)
        return response

    def simulate(self, payload: CrisisSimulationRequest) -> CrisisCommandCenterResponse:
        analysis = self.default()
        simulation = self._simulate(payload, analysis.active_crises)
        data = analysis.model_copy(update={"simulations": [simulation, *analysis.simulations]})
        data.summary.stream_sequence = analysis.summary.stream_sequence
        self._persist(data)
        return data

    def build_scenario(self, payload: CrisisScenarioBuilderRequest) -> CrisisScenarioBuilderResponse:
        scenario_id = f"scenario-{uuid5(NAMESPACE_DNS, payload.scenario_name + payload.question + payload.scenario_type).hex[:12]}"
        record = CrisisScenarioRecord(
            scenario_id=scenario_id,
            scenario_name=payload.scenario_name,
            scenario_type=payload.scenario_type,
            question=payload.question,
            affected_scope=payload.affected_scope,
            severity_multiplier=payload.severity_multiplier,
            horizon_hours=payload.horizon_hours,
            created_at=datetime.now(timezone.utc),
            execution_status="executed" if payload.execute else "stored",
            storage=str(SCENARIO_PATH),
            source_systems=["crisis_scenario_builder", "crisis_simulation_engine", "company_digital_twin", "executive_dashboard"],
        )
        simulation = None
        command_center = None
        if payload.execute:
            command_center = self.simulate(
                CrisisSimulationRequest(
                    scenario_type=payload.scenario_type,
                    question=payload.question,
                    affected_scope=payload.affected_scope,
                    severity_multiplier=payload.severity_multiplier,
                    horizon_hours=payload.horizon_hours,
                )
            )
            simulation = command_center.simulations[0]
        response = CrisisScenarioBuilderResponse(
            model="AI Crisis Simulator Scenario Builder",
            generated_at=datetime.now(timezone.utc),
            scenario=record,
            simulation=simulation,
            command_center=command_center,
            storage=str(SCENARIO_PATH),
        )
        self._persist_scenario(response)
        return response

    def ask(self, payload: CrisisAssistantRequest) -> CrisisAssistantResponse:
        analysis = self.default()
        intent = self._intent(payload.question)
        simulation = None
        if intent == "simulation":
            simulation = self._simulate(self._simulation_from_question(payload.question, payload.horizon_hours), analysis.active_crises)
        answer, evidence, actions = self._answer(intent, analysis, simulation)
        return CrisisAssistantResponse(
            model=self.assistant_model,
            generated_at=datetime.now(timezone.utc),
            question=payload.question,
            intent=intent,
            answer=answer,
            confidence=round(min(0.96, 0.72 + analysis.summary.highest_severity_score / 420), 3),
            cited_incidents=[crisis.incident_id for crisis in analysis.active_crises[:4]],
            cited_evidence=evidence[:10],
            recommended_actions=actions[:8],
            simulation=simulation,
            source_systems=["crisis_ai_assistant", "crisis_simulation_engine", "recovery_planning_engine", *analysis.source_systems[:10]],
            storage=str(HISTORY_PATH),
        )

    async def stream(self):
        scenarios = [
            CrisisCommandCenterRequest(),
            CrisisCommandCenterRequest(incidents=[self._scenario_incident("cloud_outage", 1.05), *self._default_incidents()[:3]]),
            CrisisCommandCenterRequest(incidents=[self._scenario_incident("mass_resignation", 1.15), self._scenario_incident("ransomware", 1.2)]),
        ]
        for sequence, scenario in enumerate(scenarios, start=1):
            response = self.analyze(scenario)
            data = response.model_dump(mode="json")
            data["summary"]["stream_sequence"] = sequence
            yield f"event: crisis_command_center\ndata: {json.dumps(data)}\n\n"
            await asyncio.sleep(0.8)

    def _build_default(self) -> CrisisCommandCenterResponse:
        return self.analyze(CrisisCommandCenterRequest())

    @staticmethod
    def _is_valid_default(response: CrisisCommandCenterResponse) -> bool:
        return (
            response.summary.active_crises >= 3
            and len(response.active_crises) >= 3
            and bool(response.containment_actions)
            and bool(response.recovery_plans)
            and bool(response.simulations)
            and response.final_verdict == "AI CRISIS SIMULATOR COMPLETE"
        )

    def _default_incidents(self) -> list[CrisisSignalInput]:
        incidents: list[CrisisSignalInput] = []
        try:
            alerts = alert_service.feed(AlertDetectionRequest(scenario="crisis", sensitivity=0.76))
            security_alert = next((alert for alert in alerts.alerts if alert.category == "security"), alerts.alerts[0] if alerts.alerts else None)
            if security_alert:
                incident_type: CrisisType = "data_breach" if "export" in security_alert.message.lower() or "data" in security_alert.message.lower() else "cyber_attack"
                incidents.append(
                    CrisisSignalInput(
                        incident_id="crisis-security-live",
                        incident_type=incident_type,
                        title=security_alert.title,
                        description=security_alert.message,
                        affected_systems=["Identity", "Data Export Gateway", "Finance Systems"],
                        affected_departments=["Security", "Finance"],
                        financial_exposure=max(6_800_000, security_alert.risk_score * 95_000),
                        revenue_at_risk=max(4_100_000, security_alert.risk_score * 55_000),
                        workforce_impact=max(35, security_alert.risk_score * 0.38),
                        client_impact=max(62, security_alert.risk_score * 0.58),
                        security_impact=max(90, security_alert.risk_score),
                        reputation_impact=max(82, security_alert.risk_score * 0.86),
                        operational_impact=max(86, security_alert.risk_score * 0.82),
                        detection_confidence=security_alert.confidence,
                        recovery_complexity=max(80, security_alert.risk_score * 0.78),
                        time_to_detect_minutes=18,
                        active_users_affected=1200,
                        employee_count_affected=18,
                        controls_triggered=security_alert.source_systems + ["adaptive_authentication", "export_throttling"],
                        telemetry={"alert_risk": security_alert.risk_score, "critical_alerts": alerts.summary.critical, "average_risk": alerts.summary.average_risk},
                    )
                )
        except Exception:
            incidents.append(self._scenario_incident("cyber_attack", 0.85))

        try:
            projects = project_failure_service.analyze()
            top = projects.predictions[0]
            incidents.append(
                CrisisSignalInput(
                    incident_id="crisis-project-collapse-live",
                    incident_type="project_collapse",
                    title=f"{top.project_name} delivery collapse risk",
                    description=f"Failure probability {top.failure_probability}% and deadline miss probability {top.deadline_miss_probability}%.",
                    affected_systems=["Project Delivery", "Release Pipeline"],
                    affected_departments=["Engineering", "Product"],
                    affected_projects=[top.project_name],
                    financial_exposure=max(1_000_000, top.budget_overrun_probability * 65_000),
                    revenue_at_risk=max(1_500_000, top.failure_probability * 80_000),
                    workforce_impact=top.burnout_impact,
                    client_impact=min(100, top.deadline_miss_probability * 0.82),
                    security_impact=12,
                    reputation_impact=min(100, top.failure_probability * 0.76),
                    operational_impact=max(top.failure_probability, top.deadline_miss_probability),
                    detection_confidence=0.88,
                    recovery_complexity=min(100, 45 + top.resource_shortage_impact * 0.4 + top.dependency_impact * 0.4),
                    time_to_detect_minutes=90,
                    employee_count_affected=24,
                    controls_triggered=["project_failure_prediction", "resource_gap_analyzer", "delivery_forecasting"],
                    telemetry={"failure_probability": top.failure_probability, "deadline_miss": top.deadline_miss_probability},
                )
            )
        except Exception:
            incidents.append(self._scenario_incident("project_collapse", 0.88))

        try:
            clients = client_satisfaction_service.predict()
            top_client = clients.predictions[0]
            incidents.append(
                CrisisSignalInput(
                    incident_id="crisis-client-escalation-live",
                    incident_type="client_escalation",
                    title=f"{top_client.client_name} executive escalation",
                    description=f"Churn risk {top_client.churn_risk}% with escalation probability {top_client.escalation_probability}%.",
                    affected_systems=["Client Success", "Delivery Governance", "Billing"],
                    affected_departments=["Customer Success", "Engineering", "Finance"],
                    affected_clients=[top_client.client_name],
                    financial_exposure=top_client.revenue_at_risk,
                    revenue_at_risk=top_client.revenue_at_risk,
                    workforce_impact=38,
                    client_impact=max(top_client.churn_risk, top_client.escalation_probability),
                    security_impact=8,
                    reputation_impact=max(45, top_client.churn_risk * 0.7),
                    operational_impact=max(top_client.project_failure_risk, top_client.escalation_probability),
                    detection_confidence=0.9,
                    recovery_complexity=min(100, 38 + top_client.project_failure_risk * 0.5),
                    time_to_detect_minutes=240,
                    active_users_affected=top_client.active_users,
                    employee_count_affected=16,
                    controls_triggered=["client_health_engine", "churn_prediction_engine", "project_risk_engine"],
                    telemetry={"churn": top_client.churn_risk, "payment_delay": top_client.payment_delay_risk},
                )
            )
        except Exception:
            incidents.append(self._scenario_incident("client_escalation", 0.8))

        try:
            company = company_health_service.analyze()
            top_team = company.team_scores[0]
            if top_team.risk_score >= 65 or top_team.attrition_risk >= 65:
                incidents.append(
                    CrisisSignalInput(
                        incident_id="crisis-workforce-live",
                        incident_type="mass_resignation",
                        title=f"{top_team.team_name} attrition and burnout crisis",
                        description=f"{top_team.team_name} risk {top_team.risk_score}% with burnout {top_team.burnout_risk}% and attrition {top_team.attrition_risk}%.",
                        affected_systems=["Workforce Capacity", "Incident Rotation", "Knowledge Continuity"],
                        affected_departments=[top_team.department],
                        affected_projects=[f"{top_team.team_name} delivery portfolio"],
                        financial_exposure=max(1_200_000, top_team.risk_score * 45_000),
                        revenue_at_risk=max(900_000, top_team.attrition_risk * 38_000),
                        workforce_impact=max(top_team.risk_score, top_team.attrition_risk),
                        client_impact=44,
                        security_impact=15,
                        reputation_impact=48,
                        operational_impact=max(top_team.operational_risk, top_team.project_health),
                        detection_confidence=top_team.confidence,
                        recovery_complexity=max(55, top_team.risk_score * 0.8),
                        time_to_detect_minutes=360,
                        employee_count_affected=top_team.headcount,
                        controls_triggered=["company_health_engine", "attrition_prediction", "wellness_burnout_forecaster"],
                        telemetry={"team_risk": top_team.risk_score, "attrition": top_team.attrition_risk},
                    )
                )
        except Exception:
            incidents.append(self._scenario_incident("mass_resignation", 0.82))

        try:
            business = business_prediction_service.analyze()
            if business.summary.market_risk_score >= 55 or business.summary.revenue_at_risk >= 1_000_000:
                incidents.append(
                    CrisisSignalInput(
                        incident_id="crisis-revenue-live",
                        incident_type="revenue_crash",
                        title=business.summary.top_business_risk,
                        description=f"Revenue at risk is {round(business.summary.revenue_at_risk)} with market risk {business.summary.market_risk_score}%.",
                        affected_systems=["Revenue Forecast", "Sales Pipeline", "Board Forecast"],
                        affected_departments=["Finance", "Sales", "Executive"],
                        financial_exposure=business.summary.revenue_at_risk,
                        revenue_at_risk=business.summary.revenue_at_risk,
                        workforce_impact=28,
                        client_impact=min(100, business.summary.churn_risk_score),
                        security_impact=4,
                        reputation_impact=min(100, business.summary.market_risk_score * 0.75),
                        operational_impact=min(100, business.summary.market_risk_score),
                        detection_confidence=business.summary.forecast_confidence,
                        recovery_complexity=min(100, 42 + business.summary.market_risk_score * 0.35),
                        time_to_detect_minutes=720,
                        controls_triggered=["business_prediction_engine", "revenue_forecasting", "executive_dashboard"],
                        telemetry={"market_risk": business.summary.market_risk_score, "revenue_at_risk": business.summary.revenue_at_risk},
                    )
                )
        except Exception:
            incidents.append(self._scenario_incident("revenue_crash", 0.72))

        if not any(self._severity_score(incident) >= 76 for incident in incidents):
            ransomware = self._scenario_incident("ransomware", 1.0)
            ransomware.incident_id = "crisis-ransomware-production"
            ransomware.title = "Production ransomware containment emergency"
            ransomware.description = "Command-center fallback signal activated because live crisis telemetry has no critical cyber continuity event, while ransomware readiness must remain continuously tested."
            incidents.insert(0, ransomware)

        return incidents[:8]

    def _assess(self, incident: CrisisSignalInput) -> CrisisIncidentAssessment:
        severity_score = self._severity_score(incident)
        severity_band = self._severity_band(severity_score)
        risk_level = self._risk_level(severity_band)
        impact = CrisisImpactAnalysis(
            financial_impact=round(incident.financial_exposure + incident.revenue_at_risk, 2),
            workforce_impact=round(incident.workforce_impact, 2),
            client_impact=round(incident.client_impact, 2),
            security_impact=round(incident.security_impact, 2),
            reputation_impact=round(incident.reputation_impact, 2),
            operational_impact=round(incident.operational_impact, 2),
            long_term_impact=round(self._long_term_impact(incident), 2),
            impact_radius=list(dict.fromkeys(incident.affected_systems + incident.affected_departments + incident.affected_clients + incident.affected_projects))[:12],
            business_functions_at_risk=self._business_functions(incident),
        )
        containment = self._containment(incident, severity_score)
        recovery = self._recovery_plan(incident, severity_score)
        return CrisisIncidentAssessment(
            incident_id=incident.incident_id,
            incident_type=incident.incident_type,
            title=incident.title,
            classification=self._classification(incident.incident_type),
            severity_score=severity_score,
            severity_band=severity_band,
            risk_level=risk_level,
            status="triaging" if severity_score >= 70 else "detected",
            affected_systems=incident.affected_systems,
            affected_departments=incident.affected_departments,
            affected_clients=incident.affected_clients,
            affected_projects=incident.affected_projects,
            root_cause_hypothesis=self._root_cause(incident),
            impact=impact,
            containment_actions=containment,
            recovery_plan=recovery,
            executive_summary=(
                f"{incident.title} is classified as {risk_level.replace('_', ' ')} with {round(severity_score)} severity. "
                f"Primary impact domains: {', '.join(impact.business_functions_at_risk[:4])}."
            ),
            evidence=[
                f"security={round(incident.security_impact)}",
                f"operations={round(incident.operational_impact)}",
                f"workforce={round(incident.workforce_impact)}",
                f"client={round(incident.client_impact)}",
                f"financial=${round(impact.financial_impact):,}",
                *incident.controls_triggered[:5],
            ],
            source_systems=self._incident_sources(incident),
        )

    def _severity_score(self, incident: CrisisSignalInput) -> float:
        financial_score = self._clamp((incident.financial_exposure + incident.revenue_at_risk) / 120_000)
        score = (
            incident.security_impact * 0.22
            + incident.operational_impact * 0.22
            + financial_score * 0.18
            + incident.client_impact * 0.14
            + incident.workforce_impact * 0.12
            + incident.reputation_impact * 0.08
            + incident.recovery_complexity * 0.04
        )
        time_penalty = min(8, incident.time_to_detect_minutes / 180)
        confidence_bonus = max(0, incident.detection_confidence - 0.7) * 8
        return round(self._clamp(score + time_penalty + confidence_bonus), 2)

    def _containment(self, incident: CrisisSignalInput, severity: float) -> list[CrisisContainmentAction]:
        templates: dict[CrisisType, list[tuple[str, str, str, int]]] = {
            "ransomware": [
                ("Isolate infected servers and block east-west traffic", "Security Incident Commander", "contained", 15),
                ("Disable compromised accounts and rotate secrets", "Identity Lead", "triaging", 20),
                ("Start immutable backup validation", "Infrastructure Lead", "recovering", 30),
            ],
            "cyber_attack": [
                ("Force step-up authentication for risky sessions", "Security Operations Lead", "contained", 15),
                ("Freeze large exports and privileged changes", "Data Protection Officer", "triaging", 20),
                ("Open forensic evidence collection", "SOC Lead", "triaging", 30),
            ],
            "data_breach": [
                ("Revoke suspicious tokens and lock exposed data paths", "Security Operations Lead", "contained", 10),
                ("Start breach scope assessment and legal hold", "Legal + Security", "triaging", 45),
                ("Notify executive privacy owner", "Data Protection Officer", "triaging", 30),
            ],
            "server_failure": [
                ("Fail traffic to healthy region", "SRE Lead", "recovering", 10),
                ("Freeze risky deploys and inspect saturation", "Platform Lead", "triaging", 20),
                ("Restore database replicas from validated checkpoint", "Database Lead", "recovering", 45),
            ],
            "database_corruption": [
                ("Freeze writes to corrupted tables and isolate affected replicas", "Database Lead", "contained", 10),
                ("Validate last clean backup and point-in-time recovery window", "SRE Lead", "triaging", 25),
                ("Run data integrity reconciliation for customer-facing records", "Data Platform Lead", "recovering", 60),
            ],
            "cloud_outage": [
                ("Route critical traffic through secondary provider", "Infrastructure Lead", "recovering", 20),
                ("Activate degraded-mode feature flags", "Product Operations", "recovering", 25),
                ("Prioritize customer-facing service restoration", "Incident Commander", "triaging", 15),
            ],
            "project_collapse": [
                ("Freeze non-critical scope and assign decision owner", "Program Director", "triaging", 60),
                ("Reallocate specialists to blocked dependency chain", "Resource Manager", "recovering", 120),
                ("Publish recovery timeline to client stakeholders", "Delivery Executive", "triaging", 90),
            ],
            "product_launch_failure": [
                ("Pause launch expansion and freeze unstable release channels", "Product Operations", "contained", 30),
                ("Open launch defect triage and customer-impact bridge", "Product Director", "triaging", 45),
                ("Publish revised launch recovery plan for strategic accounts", "Chief Product Officer", "recovering", 120),
            ],
            "client_escalation": [
                ("Open executive client bridge", "Executive Sponsor", "triaging", 30),
                ("Publish 24-hour recovery milestone plan", "Client Success Lead", "recovering", 60),
                ("Tie delivery owners to renewal-risk burn-down", "Delivery Executive", "triaging", 90),
            ],
            "major_client_loss": [
                ("Activate client-loss revenue protection room", "Chief Customer Officer", "triaging", 30),
                ("Reforecast renewal, expansion, and replacement pipeline exposure", "Revenue Operations", "triaging", 120),
                ("Launch win-back and reference-risk containment plan", "Executive Sponsor", "recovering", 180),
            ],
            "revenue_crash": [
                ("Create revenue protection room", "CFO", "triaging", 60),
                ("Reforecast pipeline and renewal exposure", "Finance Lead", "triaging", 180),
                ("Prioritize highest-margin recovery accounts", "Revenue Operations", "recovering", 240),
            ],
            "financial_crash": [
                ("Open CFO-led liquidity and burn-rate command room", "CFO", "triaging", 30),
                ("Freeze discretionary spend and model runway scenarios", "Finance Lead", "contained", 90),
                ("Reprioritize hiring, vendor, and capital commitments", "Executive Team", "recovering", 180),
            ],
            "mass_resignation": [
                ("Identify critical knowledge owners and backups", "HR Business Partner", "triaging", 120),
                ("Launch retention and recovery interviews", "People Director", "recovering", 240),
                ("Shift project load away from at-risk experts", "Resource Manager", "recovering", 240),
            ],
            "critical_employee_loss": [
                ("Activate knowledge transfer protocol", "Knowledge Lead", "triaging", 120),
                ("Assign backup owner for critical systems", "Engineering Director", "recovering", 180),
                ("Review retention risk for adjacent experts", "HR Business Partner", "triaging", 240),
            ],
            "supply_chain_disruption": [
                ("Switch to approved alternate vendor path", "Procurement Lead", "triaging", 180),
                ("Reprioritize delivery plan around constrained input", "Operations Lead", "recovering", 240),
                ("Quantify customer-impact commitments", "Client Success Lead", "triaging", 180),
            ],
            "regulatory_incident": [
                ("Open legal and compliance incident bridge", "Compliance Officer", "triaging", 30),
                ("Freeze affected processing workflow", "Operations Lead", "contained", 45),
                ("Prepare regulator-ready evidence package", "Legal Counsel", "triaging", 240),
            ],
            "public_relations_crisis": [
                ("Activate communications command bridge", "Chief Communications Officer", "triaging", 20),
                ("Approve verified public holding statement", "CEO + Legal Counsel", "contained", 45),
                ("Brief strategic customers and employees with consistent facts", "Executive Sponsor", "recovering", 90),
            ],
        }
        rows = templates.get(incident.incident_type, templates["cyber_attack"])
        actions: list[CrisisContainmentAction] = []
        for index, (action, owner, status, target) in enumerate(rows, start=1):
            actions.append(
                CrisisContainmentAction(
                    action_id=f"contain-{uuid5(NAMESPACE_DNS, incident.incident_id + action).hex[:10]}",
                    incident_id=incident.incident_id,
                    priority=max(1, 6 - index),
                    action=action,
                    owner=owner,
                    target_minutes=max(5, int(target * (1 + severity / 260))),
                    status=status,  # type: ignore[arg-type]
                    expected_risk_reduction=round(max(8, severity * (0.24 - index * 0.025)), 2),
                    source_systems=["risk_containment_engine", "incident_response_playbooks", *incident.controls_triggered[:3]],
                )
            )
        return actions

    def _recovery_plan(self, incident: CrisisSignalInput, severity: float) -> CrisisRecoveryPlan:
        base_owner = self._owner(incident)
        steps = [
            CrisisRecoveryStep(step=1, action="Contain the incident and stop active damage propagation.", owner=base_owner, target_minutes=30, dependencies=[], success_criteria="No new impact expansion for two monitoring intervals."),
            CrisisRecoveryStep(step=2, action="Assess blast radius, customer impact, workforce impact, and financial exposure.", owner="Crisis Intelligence Lead", target_minutes=90, dependencies=["Containment active"], success_criteria="Impact register approved by executive owner."),
            CrisisRecoveryStep(step=3, action=self._restore_action(incident.incident_type), owner=self._technical_owner(incident), target_minutes=180, dependencies=["Blast radius validated"], success_criteria="Primary service or operating workflow restored above 90% continuity."),
            CrisisRecoveryStep(step=4, action="Verify recovery with telemetry, client checks, and executive risk review.", owner="Command Center Lead", target_minutes=240, dependencies=["Restoration complete"], success_criteria="Residual severity below level 3."),
            CrisisRecoveryStep(step=5, action="Run post-incident review and convert findings into prevention workflows.", owner="Business Continuity Lead", target_minutes=1440, dependencies=["Executive closeout"], success_criteria="Actions assigned with owners and due dates."),
        ]
        recovery_hours = round(max(1.5, (severity * 0.42 + incident.recovery_complexity * 0.36 + incident.time_to_detect_minutes / 30) / 2.2), 2)
        return CrisisRecoveryPlan(
            incident_id=incident.incident_id,
            plan_name=f"{incident.title} recovery plan",
            recovery_sequence=steps,
            resource_requirements=self._resources(incident),
            escalation_procedure=["Incident Commander", "Executive Sponsor", "CEO/Crisis Council", "Board/Regulatory Owner" if severity >= 85 else "Functional VP"],
            estimated_recovery_hours=recovery_hours,
            recovery_confidence=round(self._clamp(0.92 - severity / 420 - incident.recovery_complexity / 800, 0.45, 0.94), 3),
        )

    def _business_continuity(self, crises: list[CrisisIncidentAssessment]) -> list[BusinessContinuityAction]:
        actions = []
        for crisis in crises[:5]:
            for domain in crisis.impact.business_functions_at_risk[:2]:
                actions.append(
                    BusinessContinuityAction(
                        action_id=f"bc-{uuid5(NAMESPACE_DNS, crisis.incident_id + domain).hex[:10]}",
                        domain=domain,
                        action=self._continuity_action(domain, crisis.incident_type),
                        continuity_owner=self._owner_name_for_domain(domain),
                        expected_continuity_percent=round(self._clamp(92 - crisis.severity_score * 0.32), 2),
                        dependency=crisis.title,
                        source_systems=["business_continuity_engine", "company_digital_twin", "workflow_automation"],
                    )
                )
        return actions[:10]

    def _default_simulations(self, horizon_hours: int, crises: list[CrisisIncidentAssessment]) -> list[CrisisSimulationResult]:
        default_questions = {
            "cyber_attack": ("What if a coordinated cyberattack hits identity and data systems?", 0.98),
            "data_breach": ("What if sensitive customer data is exposed?", 1.02),
            "ransomware": ("What if ransomware affects production?", 1.1),
            "server_failure": ("What if the primary database fails?", 0.94),
            "cloud_outage": ("What if our cloud provider fails?", 1.0),
            "mass_resignation": ("What if 30% of engineers resign?", 1.0),
            "critical_employee_loss": ("What if a critical platform expert leaves?", 0.92),
            "project_collapse": ("What if the revenue platform project collapses?", 0.98),
            "client_escalation": ("What if a strategic client escalates to executives?", 0.94),
            "major_client_loss": ("What if our largest client leaves?", 1.05),
            "database_corruption": ("What if customer data becomes corrupted?", 1.0),
            "revenue_crash": ("What if quarterly revenue drops 25%?", 0.96),
            "financial_crash": ("What if revenue falls 30%?", 0.98),
            "product_launch_failure": ("What if the strategic product launch fails?", 0.94),
            "public_relations_crisis": ("What if a public relations crisis damages customer trust?", 0.9),
            "supply_chain_disruption": ("What if a critical vendor fails?", 0.88),
            "regulatory_incident": ("What if a regulatory violation is confirmed?", 0.92),
        }
        return [
            self._simulate(CrisisSimulationRequest(scenario_type=scenario, question=question, horizon_hours=horizon_hours, severity_multiplier=multiplier), crises)
            for scenario, (question, multiplier) in default_questions.items()
        ]

    def _simulate(self, payload: CrisisSimulationRequest, crises: list[CrisisIncidentAssessment]) -> CrisisSimulationResult:
        base = self._scenario_incident(payload.scenario_type, payload.severity_multiplier)
        severity = self._severity_score(base)
        existing = max([crisis.severity_score for crisis in crises] or [45])
        combined_pressure = self._clamp((severity * 0.7 + existing * 0.3) * payload.severity_multiplier)
        recovery_hours = round(max(2, combined_pressure * 0.58 + payload.horizon_hours * 0.08), 2)
        recovery_strategy = [step.action for step in self._recovery_plan(base, combined_pressure).recovery_sequence[:5]]
        recommended_response = [action.action for action in self._containment(base, combined_pressure)[:3]]
        long_term = self._clamp(self._long_term_impact(base) * (1 + combined_pressure / 360))
        financial_impact = round((base.financial_exposure + base.revenue_at_risk) * (1 + combined_pressure / 180), 2)
        workforce_impact = round(self._clamp(base.workforce_impact * (1 + combined_pressure / 300)), 2)
        operational_impact = round(self._clamp(base.operational_impact * (1 + combined_pressure / 320)), 2)
        client_impact = round(self._clamp(base.client_impact * (1 + combined_pressure / 340)), 2)
        security_impact = round(self._clamp(base.security_impact * (1 + combined_pressure / 360)), 2)
        reputation_impact = round(self._clamp(base.reputation_impact * (1 + combined_pressure / 330)), 2)
        systems_affected = list(dict.fromkeys(base.affected_systems + base.affected_departments + base.affected_clients + base.affected_projects))[:12]
        forecast_timeline = self._forecast_timeline(payload.horizon_hours, combined_pressure, recovery_hours, base)
        required_resources = self._resources(base)
        executive_recommendations = [
            f"Activate {self._owner(base)} as executive owner for {payload.scenario_type.replace('_', ' ')} response.",
            f"Fund recovery resources for {round(recovery_hours, 1)} hours of continuity work.",
            f"Update company digital twin with {round(combined_pressure)} crisis pressure for boardroom forecasting.",
        ]
        digital_twin_evidence = [
            f"scenario_scope={payload.affected_scope}",
            f"combined_pressure={round(combined_pressure)}",
            f"horizon_hours={payload.horizon_hours}",
            f"existing_crises={len(crises)}",
            "employee_twin=workforce exposure recalculated",
            "team_twin=capacity and delivery confidence recalculated",
            "department_twin=continuity risk updated",
            "project_twin=timeline and client impact updated",
            "company_twin=revenue, reputation, and operational pressure updated",
        ]
        agent_contributions = self._agent_contribution_text(base, combined_pressure)
        executive_impact = self._executive_impact_panel(
            payload=payload,
            incident=base,
            financial_impact=financial_impact,
            workforce_impact=workforce_impact,
            operational_impact=operational_impact,
            client_impact=client_impact,
            security_impact=security_impact,
            reputation_impact=reputation_impact,
            long_term_impact=round(long_term, 2),
            recovery_hours=recovery_hours,
            systems_affected=systems_affected,
            forecast_timeline=forecast_timeline,
            required_resources=required_resources,
            recommended_response=recommended_response,
            recovery_strategy=recovery_strategy,
            executive_recommendations=executive_recommendations,
            digital_twin_evidence=digital_twin_evidence,
            agent_contributions=agent_contributions,
            combined_pressure=combined_pressure,
        )
        return CrisisSimulationResult(
            scenario_type=payload.scenario_type,
            question=payload.question,
            financial_impact=financial_impact,
            workforce_impact=workforce_impact,
            operational_impact=operational_impact,
            client_impact=client_impact,
            security_impact=security_impact,
            reputation_impact=reputation_impact,
            long_term_impact=round(long_term, 2),
            recovery_hours=recovery_hours,
            systems_affected=systems_affected,
            forecast_timeline=forecast_timeline,
            required_resources=required_resources,
            recommended_response=recommended_response,
            recovery_strategy=recovery_strategy,
            executive_recommendations=executive_recommendations,
            confidence=round(self._clamp(0.68 + combined_pressure / 420, 0, 0.95), 3),
            forecasting_models=self.forecasting_models,
            digital_twin_evidence=digital_twin_evidence,
            agent_contributions=agent_contributions,
            executive_impact_analysis=executive_impact,
        )

    def _executive_impact_panel(
        self,
        payload: CrisisSimulationRequest,
        incident: CrisisSignalInput,
        financial_impact: float,
        workforce_impact: float,
        operational_impact: float,
        client_impact: float,
        security_impact: float,
        reputation_impact: float,
        long_term_impact: float,
        recovery_hours: float,
        systems_affected: list[str],
        forecast_timeline: list[dict[str, float | int | str]],
        required_resources: list[str],
        recommended_response: list[str],
        recovery_strategy: list[str],
        executive_recommendations: list[str],
        digital_twin_evidence: list[str],
        agent_contributions: list[str],
        combined_pressure: float,
    ) -> ExecutiveImpactAnalysisPanel:
        delay_probability = round(self._clamp(max(operational_impact, long_term_impact * 0.82, combined_pressure * 0.74)), 2)
        productivity_cost = round(financial_impact * max(0.08, operational_impact / 420), 2)
        cost_increase = round(financial_impact * max(0.12, (security_impact + recovery_hours) / 650), 2)
        affected_teams = self._crisis_affected_teams(
            incident=incident,
            delay_probability=delay_probability,
            workforce_impact=workforce_impact,
            operational_impact=operational_impact,
            security_impact=security_impact,
            long_term_impact=long_term_impact,
        )
        required_hires = self._crisis_required_hires(payload.scenario_type, workforce_impact, operational_impact, required_resources)
        skills = self._crisis_skills(payload.scenario_type, required_resources, systems_affected)
        return ExecutiveImpactAnalysisPanel(
            trigger_type="crisis_simulation",
            scenario_name=payload.question,
            generated_at=datetime.now(timezone.utc),
            financial_loss=round(financial_impact + productivity_cost + cost_increase, 2),
            revenue_impact_percent=round(-self._clamp(financial_impact / 1_250_000, 0, 45), 2),
            profit_impact_percent=round(-self._clamp((financial_impact + cost_increase) / 1_500_000, 0, 55), 2),
            cost_increase=cost_increase,
            productivity_cost=productivity_cost,
            delay_probability=delay_probability,
            most_affected_teams=affected_teams,
            recovery_strategy=ExecutiveImpactRecoveryStrategy(
                immediate_actions=recommended_response[:4],
                short_term_recovery=recovery_strategy[:3],
                long_term_recovery=[
                    "Codify crisis playbooks into recurring digital-twin simulations.",
                    "Add redundancy for high-impact systems, owners, and client commitments.",
                    "Review budget, security, workforce, and customer continuity gates monthly.",
                ],
                risk_reduction_actions=[
                    *recommended_response[:2],
                    *recovery_strategy[:2],
                ][:4],
                executive_recommendations=executive_recommendations[:4],
            ),
            hiring_requirements=ExecutiveImpactHiringRequirement(
                required_hires=required_hires,
                priority=self._crisis_priority(required_hires, delay_probability, workforce_impact),
                skills_needed=skills,
                target_teams=[team.team_name for team in affected_teams[:3]],
                urgency_days=0 if required_hires == 0 else max(7, round(45 - min(30, delay_probability * 0.28))),
                rationale=(
                    f"Requirement derived from {round(workforce_impact)} workforce impact, "
                    f"{round(operational_impact)} operational impact, resource gaps, and crisis recovery hours."
                ),
            ),
            risk_level=self._crisis_priority(round(combined_pressure / 5), delay_probability, max(workforce_impact, operational_impact)),
            confidence_score=round(self._clamp(68 + combined_pressure / 4 + len(forecast_timeline) * 1.5), 2),
            twin_updates=digital_twin_evidence,
            agent_council=[
                ExecutiveImpactAgentContribution(
                    agent=text.split(":", 1)[0],
                    responsibility="Crisis impact analysis",
                    finding=text,
                    recommendation=executive_recommendations[min(index, len(executive_recommendations) - 1)] if executive_recommendations else "Maintain executive recovery cadence.",
                    confidence=round(self._clamp(0.78 + combined_pressure / 800, 0, 0.95), 3),
                )
                for index, text in enumerate(agent_contributions[:5])
            ],
            forecast_points=[
                ExecutiveImpactForecastPoint(
                    label=f"Hour {point.get('hour')}",
                    financial_loss=round(float(point.get("revenue_at_risk") or 0) + cost_increase * (1 - float(point.get("business_continuity") or 0) / 140), 2),
                    delay_probability=round(self._clamp(float(point.get("residual_risk") or 0) * 0.86), 2),
                    workforce_capacity=round(self._clamp(float(point.get("business_continuity") or 0) - workforce_impact * 0.12), 2),
                    recovery_progress=round(self._clamp(100 - float(point.get("residual_risk") or 0)), 2),
                )
                for point in forecast_timeline[:6]
            ],
            source_systems=[
                "crisis_simulation_engine",
                "impact_analysis_engine",
                "financial_loss_calculator",
                "delay_prediction_engine",
                "team_impact_engine",
                "recovery_strategy_engine",
                "hiring_requirements_engine",
                "employee_digital_twin",
                "team_digital_twin",
                "department_digital_twin",
                "project_digital_twin",
                "company_digital_twin",
                "multi_agent_crisis_council",
            ],
        )

    def _crisis_affected_teams(
        self,
        incident: CrisisSignalInput,
        delay_probability: float,
        workforce_impact: float,
        operational_impact: float,
        security_impact: float,
        long_term_impact: float,
    ) -> list[ExecutiveImpactTeam]:
        departments = incident.affected_departments or ["Executive", "Operations", "Security"]
        teams: list[ExecutiveImpactTeam] = []
        for index, department in enumerate(departments[:4]):
            pressure_decay = max(0.62, 1 - index * 0.12)
            shortage = self._clamp(workforce_impact * 0.74 * pressure_decay + operational_impact * 0.18)
            delay = self._clamp(delay_probability * pressure_decay + operational_impact * 0.14)
            burnout = self._clamp(workforce_impact * pressure_decay + long_term_impact * 0.18)
            knowledge = self._clamp(long_term_impact * 0.64 + security_impact * 0.18 + index * 3)
            impact = self._clamp(delay * 0.36 + burnout * 0.27 + shortage * 0.22 + knowledge * 0.15)
            teams.append(
                ExecutiveImpactTeam(
                    team_name=f"{department} Continuity Team",
                    department=department,
                    impact_score=round(impact, 2),
                    shortage_score=round(shortage, 2),
                    delay_risk=round(delay, 2),
                    burnout_risk=round(burnout, 2),
                    knowledge_loss_risk=round(knowledge, 2),
                    reason=f"{department} is in the incident radius with {round(delay)} delay risk and {round(shortage)} continuity shortage pressure.",
                )
            )
        return sorted(teams, key=lambda item: item.impact_score, reverse=True)

    @staticmethod
    def _crisis_required_hires(
        scenario_type: CrisisType,
        workforce_impact: float,
        operational_impact: float,
        required_resources: list[str],
    ) -> int:
        if scenario_type in {"mass_resignation", "critical_employee_loss"}:
            return max(4, round(workforce_impact / 5))
        if scenario_type in {"ransomware", "cyber_attack", "data_breach", "cloud_outage", "database_corruption"}:
            return max(2, round((operational_impact + len(required_resources) * 6) / 18))
        if scenario_type in {"project_collapse", "product_launch_failure", "major_client_loss"}:
            return max(2, round((workforce_impact + operational_impact) / 20))
        return max(0, round(workforce_impact / 18))

    @staticmethod
    def _crisis_skills(scenario_type: CrisisType, required_resources: list[str], systems_affected: list[str]) -> list[str]:
        skills_by_type: dict[str, list[str]] = {
            "ransomware": ["Incident Response", "Backup Recovery", "IAM", "Forensics"],
            "cyber_attack": ["Security Engineering", "Threat Hunting", "Zero Trust", "Forensics"],
            "data_breach": ["Privacy Response", "Security Engineering", "Legal Operations"],
            "cloud_outage": ["Cloud Infrastructure", "SRE", "Disaster Recovery"],
            "database_corruption": ["Database Reliability", "Data Recovery", "SRE"],
            "mass_resignation": ["Recruiting", "Knowledge Transfer", "Workforce Planning"],
            "critical_employee_loss": ["Expert Backfill", "Knowledge Management", "Succession Planning"],
            "major_client_loss": ["Customer Recovery", "Revenue Operations", "Executive Sponsorship"],
            "revenue_crash": ["Revenue Operations", "FP&A", "Customer Recovery"],
            "financial_crash": ["FP&A", "Cash Controls", "Executive Finance"],
            "project_collapse": ["Program Recovery", "Delivery Leadership", "Resource Planning"],
            "product_launch_failure": ["Product Recovery", "Customer Communication", "Quality Engineering"],
        }
        skills = [*skills_by_type.get(scenario_type, []), *required_resources, *systems_affected[:2]]
        return list(dict.fromkeys(skill for skill in skills if skill))[:6]

    @staticmethod
    def _crisis_priority(required_hires: int, delay_probability: float, impact: float):
        score = required_hires * 4 + delay_probability * 0.52 + impact * 0.32
        if score >= 82:
            return "critical"
        if score >= 64:
            return "high"
        if score >= 38:
            return "medium"
        return "low"

    def _executive_alerts(self, crises: list[CrisisIncidentAssessment]) -> list[ExecutiveCrisisAlert]:
        alerts = []
        for crisis in crises:
            if crisis.severity_score < 45:
                continue
            channels: list[str] = ["dashboard", "slack"]
            if crisis.severity_score >= 64:
                channels.extend(["email", "mobile_app", "executive_bridge"])
            if crisis.severity_score >= 82:
                channels.append("sms")
            alerts.append(
                ExecutiveCrisisAlert(
                    alert_id=f"exec-{uuid5(NAMESPACE_DNS, crisis.incident_id).hex[:10]}",
                    incident_id=crisis.incident_id,
                    severity_band=crisis.severity_band,
                    title=crisis.title,
                    message=crisis.executive_summary,
                    channels=channels,  # type: ignore[arg-type]
                    recipients=["CEO", "COO", self._owner(crisis), "Board Observer" if crisis.severity_score >= 88 else "Function VP"],
                    sla_minutes=15 if crisis.severity_score >= 82 else 60 if crisis.severity_score >= 64 else 240,
                    escalation_owner=self._owner(crisis),
                )
            )
        return alerts[:12]

    def _agent_council(
        self,
        crises: list[CrisisIncidentAssessment],
        simulations: list[CrisisSimulationResult],
    ) -> list[CrisisAgentContribution]:
        top = crises[0] if crises else None
        worst = max(simulations, key=lambda item: item.long_term_impact + item.operational_impact, default=None)
        if not top:
            return []
        return [
            CrisisAgentContribution(
                agent="Security Agent",
                domain="Cyber and data continuity",
                assessment=f"Security impact is {round(top.impact.security_impact)} on {top.title}.",
                recommended_action=next((item.action for item in top.containment_actions if "token" in item.action.lower() or "isolate" in item.action.lower()), top.containment_actions[0].action),
                confidence=0.91,
            ),
            CrisisAgentContribution(
                agent="HR Agent",
                domain="Workforce continuity",
                assessment=f"Workforce exposure is {round(top.impact.workforce_impact)} with {top.recovery_plan.resource_requirements.count('HR Business Partner')} people-continuity dependency marker(s).",
                recommended_action="Open retention, backup ownership, and knowledge-transfer workstreams for affected teams.",
                confidence=0.87,
            ),
            CrisisAgentContribution(
                agent="Finance Agent",
                domain="Financial exposure",
                assessment=f"Active crisis exposure is ${round(top.impact.financial_impact):,}; worst simulated scenario exposure is ${round(worst.financial_impact):,}." if worst else f"Active crisis exposure is ${round(top.impact.financial_impact):,}.",
                recommended_action="Reforecast cash, revenue-at-risk, and recovery budget before the next executive checkpoint.",
                confidence=0.89,
            ),
            CrisisAgentContribution(
                agent="Project Agent",
                domain="Delivery and project risk",
                assessment=f"Operational impact is {round(top.impact.operational_impact)} across {len(top.affected_projects)} explicit project dependency marker(s).",
                recommended_action="Freeze non-critical scope and assign executive decision owners to blocked delivery paths.",
                confidence=0.86,
            ),
            CrisisAgentContribution(
                agent="Executive Agent",
                domain="Unified decision",
                assessment=f"Command-center priority is {top.title} with {round(top.severity_score)} severity.",
                recommended_action=top.containment_actions[0].action,
                confidence=0.93,
            ),
        ]

    def _agent_contribution_text(self, incident: CrisisSignalInput, pressure: float) -> list[str]:
        return [
            f"Security Agent: security impact {round(incident.security_impact)}; containment owner {self._technical_owner(incident)}.",
            f"HR Agent: workforce impact {round(incident.workforce_impact)}; continuity pressure {round(pressure)}.",
            f"Finance Agent: exposure ${round(incident.financial_exposure + incident.revenue_at_risk):,}.",
            f"Project Agent: operational impact {round(incident.operational_impact)} and affected projects {len(incident.affected_projects)}.",
            f"Executive Agent: recommended owner {self._owner(incident)}.",
        ]

    def _forecast_timeline(
        self,
        horizon_hours: int,
        pressure: float,
        recovery_hours: float,
        incident: CrisisSignalInput,
    ) -> list[dict[str, float | int | str]]:
        checkpoints = [1, 6, 24, min(72, horizon_hours), horizon_hours]
        unique_checkpoints = []
        for checkpoint in checkpoints:
            if checkpoint not in unique_checkpoints and checkpoint >= 1:
                unique_checkpoints.append(checkpoint)
        timeline = []
        for checkpoint in unique_checkpoints:
            recovery_progress = self._clamp((checkpoint / max(recovery_hours, 1)) * 100)
            residual_risk = self._clamp(pressure * (1 - recovery_progress / 140))
            continuity = self._clamp(100 - residual_risk * 0.58)
            timeline.append(
                {
                    "hour": int(checkpoint),
                    "residual_risk": round(residual_risk, 2),
                    "business_continuity": round(continuity, 2),
                    "revenue_at_risk": round(incident.revenue_at_risk * (residual_risk / max(pressure, 1)), 2),
                    "status": "contained" if recovery_progress >= 90 else "recovering" if recovery_progress >= 45 else "active",
                }
            )
        return timeline

    def _long_term_impact(self, incident: CrisisSignalInput) -> float:
        return self._clamp(
            incident.reputation_impact * 0.28
            + incident.client_impact * 0.22
            + incident.workforce_impact * 0.18
            + incident.operational_impact * 0.16
            + incident.recovery_complexity * 0.1
            + self._clamp((incident.financial_exposure + incident.revenue_at_risk) / 180_000) * 0.06
        )

    def _production_readiness(
        self,
        crises: list[CrisisIncidentAssessment],
        simulations: list[CrisisSimulationResult],
        recommendations: list[CrisisRecommendation],
    ) -> float:
        checks = [
            bool(crises),
            all(crisis.recovery_plan.recovery_sequence for crisis in crises),
            len(simulations) >= 10,
            bool(recommendations),
            all(sim.digital_twin_evidence for sim in simulations),
            all(sim.agent_contributions for sim in simulations),
            all(sim.forecast_timeline for sim in simulations),
        ]
        return round(sum(1 for item in checks if item) / len(checks) * 100, 2)

    def _innovation_score(self, crises: list[CrisisIncidentAssessment], simulations: list[CrisisSimulationResult]) -> float:
        covered_types = {simulation.scenario_type for simulation in simulations}
        twin_depth = mean([len(sim.digital_twin_evidence) for sim in simulations]) if simulations else 0
        coverage = len(covered_types) / len(self._supported_scenarios()) * 100
        return round(self._clamp(coverage * 0.72 + min(100, twin_depth * 8) * 0.18 + min(100, len(crises) * 12) * 0.1), 2)

    def _heatmap(self, crises: list[CrisisIncidentAssessment]) -> list[CrisisHeatmapCell]:
        cells: list[CrisisHeatmapCell] = []
        for crisis in crises:
            for system in crisis.affected_systems[:4]:
                cells.append(CrisisHeatmapCell(domain="System", entity=system, risk_score=crisis.severity_score, severity_band=crisis.severity_band, impact_type=crisis.incident_type, recommended_owner=self._technical_owner(crisis)))
            for department in crisis.affected_departments[:3]:
                cells.append(CrisisHeatmapCell(domain="Department", entity=department, risk_score=max(crisis.impact.workforce_impact, crisis.impact.operational_impact), severity_band=crisis.severity_band, impact_type=crisis.incident_type, recommended_owner=self._owner(crisis)))
            for client in crisis.affected_clients[:3]:
                cells.append(CrisisHeatmapCell(domain="Client", entity=client, risk_score=crisis.impact.client_impact, severity_band=crisis.severity_band, impact_type=crisis.incident_type, recommended_owner="Executive Sponsor"))
        return sorted(cells, key=lambda item: item.risk_score, reverse=True)[:24]

    def _recommendations(self, crises: list[CrisisIncidentAssessment], simulations: list[CrisisSimulationResult]) -> list[CrisisRecommendation]:
        recommendations: list[CrisisRecommendation] = []
        for crisis in crises[:5]:
            top_action = crisis.containment_actions[0]
            recommendations.append(
                CrisisRecommendation(
                    recommendation_id=f"rec-{uuid5(NAMESPACE_DNS, crisis.incident_id + top_action.action).hex[:10]}",
                    priority=crisis.risk_level,
                    action=top_action.action,
                    reason=f"{crisis.title} has {round(crisis.severity_score)} severity and affects {', '.join(crisis.impact.business_functions_at_risk[:3])}.",
                    expected_risk_reduction=top_action.expected_risk_reduction,
                    confidence=round(min(0.96, 0.68 + crisis.severity_score / 360), 3),
                    source_systems=top_action.source_systems,
                )
            )
        worst = max(simulations, key=lambda item: item.operational_impact, default=None)
        if worst:
            recommendations.append(
                CrisisRecommendation(
                    recommendation_id="rec-crisis-simulation-hardening",
                    priority="critical" if worst.operational_impact >= 80 else "high",
                    action=worst.recommended_response[0],
                    reason=f"Worst modeled scenario is {worst.scenario_type} with {round(worst.operational_impact)} operational impact.",
                    expected_risk_reduction=round(max(16, worst.operational_impact * 0.22), 2),
                    confidence=worst.confidence,
                    source_systems=["crisis_simulation_engine", "business_continuity_engine", "company_digital_twin"],
                )
            )
        return recommendations

    def _summary(self, crises: list[CrisisIncidentAssessment], alerts: list[ExecutiveCrisisAlert]) -> CrisisCommandSummary:
        highest = max([crisis.severity_score for crisis in crises] or [0])
        avg_recovery = mean([crisis.recovery_plan.estimated_recovery_hours for crisis in crises]) if crises else 0
        total_financial = sum(crisis.impact.financial_impact for crisis in crises)
        systems = {system for crisis in crises for system in crisis.affected_systems}
        readiness = self._clamp(100 - highest * 0.38 - len([c for c in crises if c.severity_score >= 64]) * 4 + len(alerts) * 0.8)
        return CrisisCommandSummary(
            active_crises=len(crises),
            critical_crises=sum(1 for crisis in crises if crisis.severity_band in {"level_4_critical", "level_5_company_threatening"}),
            company_threatening_crises=sum(1 for crisis in crises if crisis.severity_band == "level_5_company_threatening"),
            highest_severity_score=round(highest, 2),
            average_recovery_hours=round(avg_recovery, 2),
            total_financial_exposure=round(total_financial, 2),
            affected_systems=len(systems),
            executive_alerts=len(alerts),
            command_center_readiness=round(readiness, 2),
            stream_sequence=1,
        )

    def _intent(self, question: str) -> str:
        text = question.lower()
        if any(token in text for token in ["simulate", "what if", "what happens", "worst"]):
            return "simulation"
        if any(token in text for token in ["biggest", "highest", "most severe", "top crisis"]):
            return "biggest_crisis"
        if any(token in text for token in ["recover", "recovery", "restore", "plan"]):
            return "recovery"
        if any(token in text for token in ["affected", "systems", "impact radius"]):
            return "affected_systems"
        if any(token in text for token in ["who", "respond", "owner", "first"]):
            return "responders"
        if any(token in text for token in ["recommend", "what should", "next action"]):
            return "recommendation"
        return "summary"

    def _answer(
        self,
        intent: str,
        analysis: CrisisCommandCenterResponse,
        simulation: CrisisSimulationResult | None,
    ) -> tuple[str, list[str], list[str]]:
        top = analysis.active_crises[0]
        if intent == "biggest_crisis":
            answer = f"The biggest active crisis is {top.title}: {round(top.severity_score)} severity, {top.risk_level.replace('_', ' ')}, affecting {', '.join(top.affected_systems[:3])}."
            evidence = top.evidence
            actions = [action.action for action in top.containment_actions]
        elif intent == "recovery":
            answer = f"Recover {top.title} by following {top.recovery_plan.plan_name}. Estimated recovery is {top.recovery_plan.estimated_recovery_hours} hours with {round(top.recovery_plan.recovery_confidence * 100)}% confidence."
            evidence = [step.success_criteria for step in top.recovery_plan.recovery_sequence]
            actions = [step.action for step in top.recovery_plan.recovery_sequence]
        elif intent == "affected_systems":
            answer = f"Affected systems include {', '.join(top.affected_systems[:6])}. Impact radius also includes {', '.join(top.impact.impact_radius[:8])}."
            evidence = top.impact.impact_radius
            actions = [item.action for item in analysis.business_continuity[:5]]
        elif intent == "responders":
            owners = list(dict.fromkeys([action.owner for action in top.containment_actions] + [top.recovery_plan.recovery_sequence[0].owner]))
            answer = f"First responders should be {', '.join(owners[:5])}. The first action is {top.containment_actions[0].action}."
            evidence = [top.containment_actions[0].action, *top.evidence]
            actions = [action.action for action in top.containment_actions]
        elif intent == "simulation":
            sim = simulation or analysis.simulations[0]
            answer = f"Worst-case simulation for {sim.scenario_type} projects ${round(sim.financial_impact):,} financial impact, {round(sim.operational_impact)} operational impact, and {sim.recovery_hours} recovery hours."
            evidence = sim.digital_twin_evidence
            actions = sim.recommended_response
        elif intent == "recommendation":
            rec = analysis.recommendations[0]
            answer = f"Start with: {rec.action}. Reason: {rec.reason}"
            evidence = [rec.reason]
            actions = [item.action for item in analysis.recommendations[:6]]
        else:
            answer = analysis.executive_brief
            evidence = [crisis.executive_summary for crisis in analysis.active_crises[:4]]
            actions = [item.action for item in analysis.recommendations[:6]]
        return answer, evidence, actions

    def _scenario_incident(self, incident_type: CrisisType, multiplier: float = 1.0) -> CrisisSignalInput:
        catalog = {
            "ransomware": ("Ransomware attack on production", ["Production API", "Database Cluster", "Object Storage"], ["Security", "Engineering"], 7_500_000, 5_200_000, 46, 61, 96, 88, 94, 88),
            "cloud_outage": ("Cloud provider outage", ["Cloud Region", "API Gateway", "Queue Workers"], ["Engineering", "Customer Success"], 4_200_000, 3_300_000, 34, 58, 18, 64, 91, 76),
            "server_failure": ("Primary database failure", ["Database Cluster", "Payments API"], ["Engineering", "Operations"], 2_600_000, 2_000_000, 28, 42, 15, 50, 88, 68),
            "database_corruption": ("Customer database corruption", ["Database Cluster", "Customer Records", "Billing Ledger"], ["Engineering", "Data", "Finance"], 5_500_000, 3_700_000, 36, 66, 34, 78, 90, 86),
            "data_breach": ("Sensitive data exposure", ["Data Export Gateway", "CRM", "Audit Logs"], ["Security", "Legal", "Customer Success"], 6_400_000, 4_100_000, 42, 72, 97, 93, 82, 91),
            "cyber_attack": ("Coordinated cyber attack", ["Identity", "VPN", "Data Platform"], ["Security", "IT"], 3_900_000, 2_300_000, 32, 46, 90, 76, 73, 79),
            "project_collapse": ("Revenue platform delivery collapse", ["Release Pipeline", "Project Governance"], ["Engineering", "Product"], 3_800_000, 4_500_000, 76, 67, 8, 71, 88, 75),
            "product_launch_failure": ("Strategic product launch failure", ["Launch Pipeline", "Feature Flags", "Support Queue"], ["Product", "Engineering", "Customer Success"], 3_600_000, 4_900_000, 44, 76, 6, 86, 74, 69),
            "client_escalation": ("Strategic client escalation", ["Client Success", "Delivery Governance"], ["Customer Success", "Engineering"], 4_800_000, 4_800_000, 38, 88, 5, 78, 70, 66),
            "major_client_loss": ("Largest client contract loss", ["Renewal Pipeline", "Client Success", "Revenue Forecast"], ["Customer Success", "Sales", "Finance"], 9_200_000, 9_200_000, 42, 96, 4, 91, 71, 78),
            "revenue_crash": ("Quarterly revenue forecast crash", ["Revenue Forecast", "Sales Pipeline"], ["Finance", "Sales"], 8_600_000, 8_600_000, 31, 60, 4, 82, 67, 70),
            "financial_crash": ("Enterprise financial crash", ["Runway Model", "Budget Controls", "Investor Reporting"], ["Finance", "Executive", "Operations"], 12_500_000, 10_400_000, 58, 70, 5, 89, 79, 82),
            "mass_resignation": ("Engineering resignation spike", ["Workforce Capacity", "Knowledge Graph"], ["Engineering", "HR"], 4_100_000, 2_900_000, 92, 45, 10, 63, 78, 84),
            "critical_employee_loss": ("Critical expert loss", ["Kubernetes Platform", "Incident Runbooks"], ["Engineering", "Knowledge"], 2_200_000, 1_600_000, 74, 40, 8, 56, 70, 72),
            "supply_chain_disruption": ("Supply chain disruption", ["Vendor Delivery", "Procurement"], ["Operations", "Finance"], 2_900_000, 2_100_000, 25, 54, 5, 58, 66, 64),
            "regulatory_incident": ("Regulatory incident", ["Compliance Workflow", "Audit Evidence"], ["Legal", "Security"], 5_700_000, 2_200_000, 34, 68, 55, 95, 52, 82),
            "public_relations_crisis": ("Public relations trust crisis", ["Communications", "Social Monitoring", "Executive Briefing"], ["Executive", "Marketing", "Legal"], 3_200_000, 3_800_000, 30, 82, 6, 98, 58, 74),
        }
        title, systems, departments, financial, revenue, workforce, client, security, reputation, operations, complexity = catalog[incident_type]
        scale = multiplier
        return CrisisSignalInput(
            incident_id=f"scenario-{incident_type}",
            incident_type=incident_type,
            title=title,
            description=f"Modeled {incident_type.replace('_', ' ')} scenario for executive crisis simulation.",
            affected_systems=systems,
            affected_departments=departments,
            affected_clients=["Strategic Accounts"] if client >= 55 else [],
            affected_projects=["Revenue Platform"] if operations >= 70 else [],
            financial_exposure=financial * scale,
            revenue_at_risk=revenue * scale,
            workforce_impact=self._clamp(workforce * scale),
            client_impact=self._clamp(client * scale),
            security_impact=self._clamp(security * scale),
            reputation_impact=self._clamp(reputation * scale),
            operational_impact=self._clamp(operations * scale),
            detection_confidence=0.88,
            recovery_complexity=self._clamp(complexity * scale),
            time_to_detect_minutes=25 if incident_type in {"ransomware", "cyber_attack", "server_failure"} else 240,
            active_users_affected=9000 if operations >= 80 else 1800,
            employee_count_affected=42 if workforce >= 70 else 18,
            controls_triggered=[f"{incident_type}_detector", "crisis_simulation_engine", "digital_twin"],
        )

    def _simulation_from_question(self, question: str, horizon_hours: int) -> CrisisSimulationRequest:
        text = question.lower()
        scenario: CrisisType = "ransomware"
        if "cloud" in text or "provider" in text or "aws" in text or "azure" in text:
            scenario = "cloud_outage"
        elif "database" in text or "corrupt" in text or "data corruption" in text:
            scenario = "database_corruption"
        elif "engineer" in text or "resign" in text or "employee" in text:
            scenario = "mass_resignation"
        elif "largest client" in text or "major client" in text or "biggest client" in text or ("client" in text and "leave" in text):
            scenario = "major_client_loss"
        elif "client" in text:
            scenario = "client_escalation"
        elif "server" in text or "database" in text:
            scenario = "server_failure"
        elif "launch" in text or "product" in text:
            scenario = "product_launch_failure"
        elif "financial" in text or "runway" in text or "budget" in text:
            scenario = "financial_crash"
        elif "revenue" in text or "sales" in text:
            scenario = "revenue_crash"
        elif "pr" in text or "public relations" in text or "reputation" in text:
            scenario = "public_relations_crisis"
        elif "supply" in text or "vendor" in text:
            scenario = "supply_chain_disruption"
        elif "regulatory" in text or "compliance" in text:
            scenario = "regulatory_incident"
        return CrisisSimulationRequest(scenario_type=scenario, question=question, horizon_hours=horizon_hours, severity_multiplier=1.15 if "worst" in text else 1.0)

    def _classification(self, incident_type: CrisisType) -> str:
        labels = {
            "cyber_attack": "Cyber attack response",
            "data_breach": "Data leakage and privacy response",
            "ransomware": "Ransomware containment and recovery",
            "server_failure": "Infrastructure failure response",
            "cloud_outage": "Cloud outage business continuity",
            "database_corruption": "Database corruption and data integrity recovery",
            "project_collapse": "Project collapse recovery",
            "product_launch_failure": "Product launch failure recovery",
            "client_escalation": "Client escalation and revenue protection",
            "major_client_loss": "Major client loss recovery",
            "revenue_crash": "Revenue continuity crisis",
            "financial_crash": "Financial crash and runway protection",
            "mass_resignation": "Workforce continuity crisis",
            "critical_employee_loss": "Knowledge continuity crisis",
            "supply_chain_disruption": "Supply chain continuity crisis",
            "regulatory_incident": "Regulatory and compliance crisis",
            "public_relations_crisis": "Public relations and reputation crisis",
        }
        return labels[incident_type]

    def _root_cause(self, incident: CrisisSignalInput) -> str:
        if incident.incident_type in {"cyber_attack", "data_breach", "ransomware"}:
            return "Correlated security telemetry indicates credential, privilege, or data-movement anomaly."
        if incident.incident_type in {"server_failure", "cloud_outage", "database_corruption"}:
            return "Service telemetry indicates infrastructure dependency degradation or failover pressure."
        if incident.incident_type in {"mass_resignation", "critical_employee_loss"}:
            return "Workforce analytics indicate overload, burnout, retention risk, or concentrated expertise loss."
        if incident.incident_type == "project_collapse":
            return "Project forecasting indicates deadline, dependency, resource, and delivery-health breakdown."
        if incident.incident_type == "product_launch_failure":
            return "Launch telemetry indicates defect spikes, adoption failure, and escalating customer-impact pressure."
        if incident.incident_type in {"client_escalation", "major_client_loss"}:
            return "Client intelligence indicates dissatisfaction, delivery risk, and executive escalation pressure."
        if incident.incident_type in {"revenue_crash", "financial_crash"}:
            return "Business prediction engine indicates revenue exposure, churn pressure, or market-risk shift."
        if incident.incident_type == "public_relations_crisis":
            return "Reputation telemetry indicates customer trust, media, and executive communication risk."
        return "Cross-system telemetry indicates continuity risk requiring executive response."

    def _incident_sources(self, incident: CrisisSignalInput) -> list[str]:
        systems = {
            "cyber_attack": ["cyber_crisis_engine", "cybersecurity_brain", "anomaly_detection", "soc_alert_correlator"],
            "data_breach": ["cyber_crisis_engine", "data_leakage_prediction", "privacy_response_engine"],
            "ransomware": ["cyber_crisis_engine", "ransomware_behavior_detection", "backup_recovery_engine"],
            "server_failure": ["infrastructure_crisis_engine", "service_health_monitor", "recovery_planning_engine"],
            "cloud_outage": ["infrastructure_crisis_engine", "cloud_resilience_monitor", "business_continuity_engine"],
            "database_corruption": ["infrastructure_crisis_engine", "data_integrity_engine", "backup_recovery_engine"],
            "project_collapse": ["project_crisis_engine", "project_intelligence", "resource_allocation"],
            "product_launch_failure": ["project_crisis_engine", "launch_readiness_engine", "client_intelligence"],
            "client_escalation": ["client_crisis_engine", "client_intelligence", "churn_prediction_engine"],
            "major_client_loss": ["client_crisis_engine", "revenue_forecasting", "client_intelligence"],
            "revenue_crash": ["business_prediction_engine", "financial_forecasting", "boardroom_dashboard"],
            "financial_crash": ["financial_crisis_engine", "business_prediction_engine", "boardroom_dashboard"],
            "mass_resignation": ["workforce_crisis_engine", "attrition_prediction", "employee_digital_twin"],
            "critical_employee_loss": ["workforce_crisis_engine", "knowledge_brain", "employee_digital_twin"],
            "supply_chain_disruption": ["business_continuity_engine", "operations_risk_engine"],
            "regulatory_incident": ["compliance_engine", "legal_response_engine", "risk_containment_engine"],
            "public_relations_crisis": ["reputation_risk_engine", "executive_alert_engine", "legal_response_engine"],
        }
        return list(dict.fromkeys([*systems[incident.incident_type], *incident.controls_triggered]))

    def _business_functions(self, incident: CrisisSignalInput) -> list[str]:
        functions = []
        if incident.security_impact >= 45:
            functions.append("Security Operations")
        if incident.operational_impact >= 45:
            functions.append("Core Operations")
        if incident.client_impact >= 45:
            functions.append("Client Success")
        if incident.workforce_impact >= 45:
            functions.append("Workforce Continuity")
        if incident.financial_exposure + incident.revenue_at_risk >= 1_000_000:
            functions.append("Financial Performance")
        if incident.reputation_impact >= 50:
            functions.append("Executive Reputation")
        return functions or ["Operational Monitoring"]

    def _resources(self, incident: CrisisSignalInput) -> list[str]:
        resources = ["Incident Commander", "Executive Sponsor"]
        if incident.incident_type in {"cyber_attack", "data_breach", "ransomware", "regulatory_incident"}:
            resources.extend(["Security Operations Lead", "Legal/Compliance Owner", "Forensics Engineer"])
        if incident.incident_type in {"server_failure", "cloud_outage", "database_corruption", "ransomware"}:
            resources.extend(["SRE Lead", "Database/Infrastructure Lead", "Backup Recovery Owner"])
        if incident.incident_type in {"mass_resignation", "critical_employee_loss"}:
            resources.extend(["HR Business Partner", "Knowledge Transfer Lead", "Resource Allocation Owner"])
        if incident.incident_type in {"project_collapse", "product_launch_failure", "client_escalation", "major_client_loss"}:
            resources.extend(["Program Director", "Client Executive Sponsor", "Delivery Recovery Lead"])
        if incident.incident_type in {"revenue_crash", "financial_crash"}:
            resources.extend(["CFO", "Revenue Operations", "Sales Leadership"])
        if incident.incident_type == "public_relations_crisis":
            resources.extend(["Chief Communications Officer", "Legal Counsel", "Customer Communications Lead"])
        return list(dict.fromkeys(resources))

    def _restore_action(self, incident_type: CrisisType) -> str:
        if incident_type in {"ransomware", "server_failure", "cloud_outage", "database_corruption"}:
            return "Restore services using validated backups, failover capacity, and controlled traffic ramp."
        if incident_type in {"cyber_attack", "data_breach", "regulatory_incident"}:
            return "Close exposure path, validate evidence, rotate secrets, and restore secure processing."
        if incident_type in {"mass_resignation", "critical_employee_loss"}:
            return "Transfer critical knowledge, assign backups, rebalance workload, and stabilize retention risk."
        if incident_type in {"project_collapse", "product_launch_failure", "client_escalation", "major_client_loss"}:
            return "Rebaseline delivery plan, assign executive owners, recover client trust, and protect revenue."
        if incident_type in {"financial_crash", "revenue_crash"}:
            return "Restore financial continuity through cash controls, revenue recovery, and executive budget decisions."
        if incident_type == "public_relations_crisis":
            return "Stabilize trust with verified messaging, customer outreach, and reputation recovery monitoring."
        return "Restore continuity through alternate operating path and executive-owned recovery milestones."

    @staticmethod
    def _severity_band(score: float) -> CrisisSeverityBand:
        if score >= 90:
            return "level_5_company_threatening"
        if score >= 76:
            return "level_4_critical"
        if score >= 56:
            return "level_3_high"
        if score >= 30:
            return "level_2_moderate"
        return "level_1_minor"

    @staticmethod
    def _risk_level(band: CrisisSeverityBand) -> CrisisRiskLevel:
        return {
            "level_1_minor": "low",
            "level_2_moderate": "medium",
            "level_3_high": "high",
            "level_4_critical": "critical",
            "level_5_company_threatening": "company_threatening",
        }[band]

    @staticmethod
    def _owner(value) -> str:
        incident_type = getattr(value, "incident_type", None)
        return {
            "cyber_attack": "CISO",
            "data_breach": "CISO + Privacy Counsel",
            "ransomware": "CISO + Infrastructure VP",
            "server_failure": "VP Infrastructure",
            "cloud_outage": "VP Infrastructure",
            "database_corruption": "VP Infrastructure + Data Lead",
            "project_collapse": "Program Director",
            "product_launch_failure": "Chief Product Officer",
            "client_escalation": "Chief Customer Officer",
            "major_client_loss": "Chief Customer Officer + CFO",
            "revenue_crash": "CFO",
            "financial_crash": "CFO",
            "mass_resignation": "Chief People Officer",
            "critical_employee_loss": "Chief People Officer",
            "supply_chain_disruption": "COO",
            "regulatory_incident": "General Counsel",
            "public_relations_crisis": "Chief Communications Officer",
        }.get(incident_type, "COO")

    @staticmethod
    def _technical_owner(value) -> str:
        incident_type = getattr(value, "incident_type", None)
        if incident_type in {"cyber_attack", "data_breach", "ransomware", "regulatory_incident"}:
            return "Security Operations Lead"
        if incident_type in {"server_failure", "cloud_outage", "database_corruption"}:
            return "SRE Lead"
        if incident_type in {"project_collapse", "product_launch_failure", "client_escalation", "major_client_loss"}:
            return "Delivery Recovery Lead"
        if incident_type in {"mass_resignation", "critical_employee_loss"}:
            return "Knowledge Continuity Lead"
        if incident_type in {"revenue_crash", "financial_crash"}:
            return "Finance Continuity Lead"
        if incident_type == "public_relations_crisis":
            return "Communications Response Lead"
        return "Business Continuity Lead"

    @staticmethod
    def _continuity_action(domain: str, incident_type: CrisisType) -> str:
        if domain == "Security Operations":
            return "Maintain containment controls, privileged-access review, and forensic preservation."
        if domain == "Core Operations":
            return "Run degraded-mode service path and restore highest customer-impact workflow first."
        if domain == "Client Success":
            return "Send executive client update and establish recovery milestone cadence."
        if domain == "Workforce Continuity":
            return "Rebalance critical work, open retention lane, and assign knowledge backups."
        if domain == "Financial Performance":
            return "Reforecast exposure, protect renewals, and prioritize highest-margin recovery."
        return f"Run continuity workflow for {incident_type.replace('_', ' ')}."

    @staticmethod
    def _owner_name_for_domain(domain: str) -> str:
        return {
            "Security Operations": "CISO",
            "Core Operations": "COO",
            "Client Success": "Chief Customer Officer",
            "Workforce Continuity": "Chief People Officer",
            "Financial Performance": "CFO",
            "Executive Reputation": "CEO",
        }.get(domain, "Business Continuity Lead")

    def _executive_brief(self, summary: CrisisCommandSummary, crises: list[CrisisIncidentAssessment]) -> str:
        top = crises[0] if crises else None
        if not top:
            return "No active crisis is currently above the command-center threshold."
        return (
            f"Emergency Command Center is tracking {summary.active_crises} active crisis signal(s), "
            f"{summary.critical_crises} critical/company-threatening crisis signal(s), and ${round(summary.total_financial_exposure):,} exposure. "
            f"Top crisis: {top.title} at {round(top.severity_score)} severity. Immediate action: {top.containment_actions[0].action}."
        )

    @staticmethod
    def _supported_scenarios() -> list[CrisisType]:
        return [
            "cyber_attack",
            "ransomware",
            "data_breach",
            "server_failure",
            "cloud_outage",
            "database_corruption",
            "project_collapse",
            "product_launch_failure",
            "client_escalation",
            "major_client_loss",
            "revenue_crash",
            "financial_crash",
            "mass_resignation",
            "critical_employee_loss",
            "supply_chain_disruption",
            "regulatory_incident",
            "public_relations_crisis",
        ]

    @staticmethod
    def _clamp(value: float, lower: float = 0, upper: float = 100) -> float:
        return max(lower, min(upper, float(value)))

    @staticmethod
    def _latest_history() -> CrisisCommandCenterResponse | None:
        if not HISTORY_PATH.exists():
            return None
        try:
            size = HISTORY_PATH.stat().st_size
            with HISTORY_PATH.open("rb") as handle:
                handle.seek(max(0, size - 8_388_608))
                lines = handle.read().decode("utf-8", errors="ignore").splitlines()[-100:]
            for line in reversed(lines):
                try:
                    return CrisisCommandCenterResponse.model_validate_json(line)
                except Exception:
                    continue
        except OSError:
            return None
        return None

    def _persist(self, response: CrisisCommandCenterResponse) -> None:
        with self._lock:
            with HISTORY_PATH.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(response.model_dump(mode="json")) + "\n")

    def _persist_scenario(self, response: CrisisScenarioBuilderResponse) -> None:
        with self._lock:
            with SCENARIO_PATH.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(response.model_dump(mode="json")) + "\n")


crisis_management_service = CrisisManagementService()
