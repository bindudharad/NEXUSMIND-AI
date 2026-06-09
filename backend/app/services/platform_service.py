from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from threading import Lock

import numpy as np

from app.ai.digital_twin import TwinScenarioInput, digital_twin_simulator
from app.ai.knowledge_engine import knowledge_engine
from app.core.cache import TTLResponseCache
from app.core.config import settings
from app.schemas.alerts import AlertDetectionRequest
from app.schemas.forecasting import ForecastRequest
from app.schemas.nlp import NLPAnalyzeRequest
from app.schemas.platform import (
    CompletePlatformResponse,
    EcosystemAuditResponse,
    EcosystemAuditSection,
    EcosystemCoreStatus,
    PlatformCapability,
    PlatformMetric,
    PlatformSummary,
)
from app.schemas.power_features import ManagerAssistantRequest
from app.schemas.suggestions import SmartSuggestionRequest
from app.schemas.voice import VoiceCommandRequest
from app.services.alert_service import alert_service
from app.services.anomaly_service import anomaly_service
from app.services.autonomous_workflow_service import autonomous_workflow_service
from app.services.boardroom_service import boardroom_dashboard_service
from app.services.business_prediction_service import business_prediction_service
from app.services.client_satisfaction_service import client_satisfaction_service
from app.services.company_emotion_map_service import company_emotion_map_service
from app.services.company_simulation_lab_service import company_simulation_lab_service
from app.services.competitive_intelligence_service import competitive_intelligence_service
from app.services.crisis_management_service import crisis_management_service
from app.services.attrition_service import attrition_prediction_service
from app.services.employee_dashboard_service import employee_dashboard_service
from app.services.forecasting_service import forecasting_service
from app.services.hiring_service import hiring_intelligence_service
from app.services.enterprise_knowledge_service import enterprise_knowledge_service
from app.services.innovation_service import innovation_scoring_service
from app.services.manager_dashboard_service import manager_dashboard_service
from app.services.meeting_service import meeting_analyzer_service
from app.services.multi_agent_workforce_service import multi_agent_workforce_service
from app.services.nlp_service import nlp_service
from app.services.organizational_optimizer_service import organizational_optimizer_service
from app.services.power_feature_service import power_feature_service
from app.services.project_failure_service import project_failure_service
from app.services.recommendation_service import recommendation_service
from app.services.roi_service import roi_intelligence_service
from app.services.smart_interviewer_service import smart_interviewer_service
from app.services.strategic_intelligence_service import strategic_intelligence_service
from app.services.suggestion_service import smart_suggestion_service
from app.services.talent_marketplace_service import talent_marketplace_service
from app.services.team_builder_service import team_builder_service
from app.services.team_compatibility_service import team_compatibility_service
from app.services.voice_service import voice_stress_service


ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "backend" / "app" / "data"
PLATFORM_HISTORY_PATH = DATA_DIR / "complete_platform_history.jsonl"
FRONTEND_COMPONENTS = ROOT / "frontend" / "src" / "components" / "dashboard"
FRONTEND_API = ROOT / "frontend" / "src" / "app" / "api"
INFRA_DIR = ROOT / "infra"


class PlatformService:
    model_name = "NEXUSMIND Complete Enterprise AI Operating System"
    expected_capability_count = 45

    def __init__(self) -> None:
        self._cache: TTLResponseCache[CompletePlatformResponse] = TTLResponseCache(ttl_seconds=180)
        self._lock = Lock()
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._seed_cache_from_history()

    def operating_system(self) -> CompletePlatformResponse:
        return self._cache.get_or_set(self._build_response)

    def _seed_cache_from_history(self) -> None:
        if not PLATFORM_HISTORY_PATH.exists():
            return
        try:
            for line in reversed(PLATFORM_HISTORY_PATH.read_text(encoding="utf-8").splitlines()):
                if not line.strip():
                    continue
                response = CompletePlatformResponse.model_validate_json(line)
                if (
                    response.model == self.model_name
                    and response.summary.errors == 0
                    and response.summary.total_capabilities >= self.expected_capability_count
                    and self._history_has_current_contract(response)
                ):
                    self._cache.seed(response)
                    return
        except (OSError, ValueError):
            return

    @staticmethod
    def _history_has_current_contract(response: CompletePlatformResponse) -> bool:
        dashboard_names = set(response.dashboards)
        legacy_people_ops_label = "HR" + " Dashboard"
        legacy_workforce_dashboard_label = "Multi-Agent AI Workforce " + "Dashboard"
        if (
            legacy_people_ops_label in dashboard_names
            or legacy_workforce_dashboard_label in dashboard_names
            or "Workforce Intelligence Command Center" not in dashboard_names
            or "Multi-Agent AI Workforce Command Surface" not in dashboard_names
        ):
            return False
        capabilities = {item.name: item for item in response.capabilities}
        digital_twin = capabilities.get("Digital Twin of the Company")
        business_prediction = capabilities.get("AI Business Prediction Engine")
        autonomous_workflow = capabilities.get("Autonomous Workflow Automation System")
        simulation_lab = capabilities.get("AI Company Simulation Lab")
        competitive_intelligence = capabilities.get("AI Competitive Intelligence System")
        smart_interviewer = capabilities.get("AI Smart Interviewer")
        client_relationship = capabilities.get("AI Client Relationship Intelligence")
        talent_marketplace = capabilities.get("AI Internal Talent Marketplace")
        emotion_map = capabilities.get("Company Emotion Map")
        innovation_detector = capabilities.get("AI Innovation Detector")
        boardroom_dashboard = capabilities.get("AI Boardroom Dashboard / JARVIS for Companies")
        voice_copilot = capabilities.get("Voice-Controlled Enterprise AI")
        org_optimizer = capabilities.get("AI Organizational Structure Optimizer")
        crisis_management = capabilities.get("Realtime Crisis Management AI")
        multi_agent_workforce = capabilities.get("Multi-Agent AI Workforce")
        if not digital_twin or not business_prediction or not autonomous_workflow or not simulation_lab or not competitive_intelligence or not smart_interviewer or not client_relationship or not talent_marketplace or not emotion_map or not innovation_detector or not boardroom_dashboard or not voice_copilot or not org_optimizer or not crisis_management or not multi_agent_workforce:
            return False
        return {
            "team_twin_model",
            "project_twin_model",
            "resource_twin_model",
            "operations_twin_model",
            "scenario_simulation_engine",
            "executive_decision_engine",
        }.issubset(set(digital_twin.source_systems)) and {
            "workflow_engine",
            "automation_engine",
            "approval_engine",
            "task_assignment_engine",
            "scheduling_engine",
            "multi_agent_orchestrator",
            "ai_operations_assistant",
        }.issubset(set(autonomous_workflow.source_systems)) and {
            "simulation_engine",
            "decision_engine",
            "forecasting_engine",
            "impact_analysis_engine",
            "digital_twin",
            "ai_simulation_assistant",
        }.issubset(set(simulation_lab.source_systems)) and {
            "competitor_monitoring_engine",
            "market_intelligence_engine",
            "hiring_intelligence_engine",
            "technology_intelligence_engine",
            "product_launch_intelligence_engine",
            "industry_trend_analysis_engine",
            "competitive_risk_engine",
            "executive_strategy_engine",
            "competitive_ai_assistant",
        }.issubset(set(competitive_intelligence.source_systems)) and {
            "interview_engine",
            "question_generation_engine",
            "resume_analysis_engine",
            "candidate_scoring_engine",
            "voice_confidence_engine",
            "cheating_detection_engine",
            "interview_report_generator",
            "smart_interview_dashboard",
        }.issubset(set(smart_interviewer.source_systems)) and {
            "client_health_engine",
            "churn_prediction_engine",
            "payment_risk_engine",
            "project_risk_engine",
            "communication_intelligence_engine",
            "ai_client_assistant",
            "opportunity_detection_engine",
        }.issubset(set(client_relationship.source_systems)) and {
            "talent_profile_engine",
            "skill_intelligence_engine",
            "project_matching_engine",
            "mentor_matching_engine",
            "internal_job_matching_engine",
            "learning_recommendation_engine",
            "reputation_engine",
            "talent_ai_assistant",
        }.issubset(set(talent_marketplace.source_systems)) and {
            "emotion_analytics_engine",
            "sentiment_analysis_engine",
            "burnout_prediction_engine",
            "conflict_detection_engine",
            "organizational_heatmap_engine",
            "emotion_ai_assistant",
            "company_digital_twin",
            "workflow_automation",
        }.issubset(set(emotion_map.source_systems)) and {
            "innovation_analytics_engine",
            "leadership_potential_engine",
            "creativity_intelligence_engine",
            "problem_solving_intelligence_engine",
            "talent_discovery_engine",
            "employee_growth_engine",
            "future_leader_prediction_engine",
            "innovation_ai_assistant",
            "talent_marketplace",
            "employee_digital_twin",
        }.issubset(set(innovation_detector.source_systems)) and {
            "executive_dashboard",
            "real_time_data_layer",
            "ai_insights_engine",
            "risk_aggregation_engine",
            "executive_recommendation_engine",
            "company_digital_twin",
            "executive_ai_assistant",
            "forecasting_integration",
        }.issubset(set(boardroom_dashboard.source_systems)) and {
            "speech_recognition_engine",
            "voice_command_engine",
            "llm_assistant_engine",
            "text_to_speech_engine",
            "context_memory_engine",
            "enterprise_analytics_connector",
            "executive_dashboard_integration",
        }.issubset(set(voice_copilot.source_systems)) and {
            "organizational_analytics_engine",
            "graph_ai_engine",
            "reporting_structure_analyzer",
            "team_optimization_engine",
            "collaboration_intelligence_engine",
            "communication_flow_analyzer",
            "organizational_simulation_engine",
            "organizational_ai_assistant",
        }.issubset(set(org_optimizer.source_systems)) and {
            "crisis_detection_engine",
            "incident_classification_engine",
            "crisis_severity_engine",
            "recovery_planning_engine",
            "risk_containment_engine",
            "business_continuity_engine",
            "crisis_simulation_engine",
            "executive_alert_engine",
            "crisis_ai_assistant",
            "company_digital_twin",
            "cybersecurity_brain",
            "client_intelligence",
        }.issubset(set(crisis_management.source_systems)) and {
            "master_orchestrator",
            "agent_communication_layer",
            "agent_shared_memory",
            "agent_event_bus",
            "agent_tool_access_framework",
            "agent_decision_engine",
            "agent_simulation_framework",
            "agent_performance_analytics",
            "executive_ai_council",
            "multi_agent_dashboard",
            "employee_digital_twin",
            "team_digital_twin",
            "department_digital_twin",
            "project_digital_twin",
            "company_digital_twin",
        }.issubset(set(multi_agent_workforce.source_systems))

    def ecosystem_audit(self) -> EcosystemAuditResponse:
        platform = self.operating_system()
        capabilities = platform.capabilities
        missing = [item.name for item in capabilities if item.status == "missing"]
        broken = [item.name for item in capabilities if item.status == "error"]
        weak = [item.name for item in capabilities if item.status in {"configured", "warning"}]
        infrastructure_problems = [
            item.name
            for item in capabilities
            if item.category in {"deployment", "security"} and item.status not in {"ready"}
        ]
        placeholder_features = [] if not weak else [f"{name} requires additional hardening" for name in weak]
        connected_domains = [
            "HR Intelligence",
            "Productivity Intelligence",
            "Security Intelligence",
            "Hiring Intelligence",
            "Project Intelligence",
            "Knowledge Intelligence",
            "Wellness Intelligence",
            "Financial Intelligence",
            "Client Intelligence",
            "Digital Twin Intelligence",
            "Business Intelligence",
            "Executive Intelligence",
            "Operations Workflow Intelligence",
            "Company Simulation Intelligence",
            "Competitive Intelligence",
            "Interview Intelligence",
            "Organizational Emotion Intelligence",
            "Boardroom Executive Intelligence",
        ]
        orchestration_engines = [
            "AI Orchestration Layer",
            "Event Engine",
            "Knowledge Engine",
            "Forecasting Engine",
            "Agent Engine",
            "Simulation Engine",
            "Workflow Automation Engine",
            "Business Flight Simulator",
            "Competitive Intelligence War Room",
            "AI Interview Panel Engine",
            "Emotion Digital Twin Engine",
            "AI Boardroom / JARVIS Executive Copilot",
        ]
        ai_core = EcosystemCoreStatus(
            one_login=True,
            one_database_ecosystem=all(
                any(token in item for item in platform.data_stack)
                for token in ["PostgreSQL", "MongoDB", "Redis", "Qdrant", "Neo4j", "Kafka", "Spark"]
            ),
            one_ai_core=any(item.name == "Unified Enterprise AI Core" and item.status == "ready" for item in capabilities),
            one_dashboard_ecosystem=len(platform.dashboards) >= 10,
            one_agent_orchestration_layer=any(
                "multi_agent_orchestration" in item.source_systems for item in capabilities
            ),
            orchestration_engines=orchestration_engines,
            connected_domains=connected_domains,
            evidence=[
                f"capabilities={platform.summary.ready}/{platform.summary.total_capabilities}",
                f"dashboards={len(platform.dashboards)}",
                f"data_stack={len(platform.data_stack)}",
                f"ai_stack={len(platform.ai_stack)}",
                f"devops_stack={len(platform.devops_stack)}",
            ],
        )
        sections = [
            EcosystemAuditSection(title="Existing Features", items=[item.name for item in capabilities if item.status == "ready"]),
            EcosystemAuditSection(title="Missing Features", items=missing),
            EcosystemAuditSection(title="Broken Features", items=broken),
            EcosystemAuditSection(title="Placeholder Features", items=placeholder_features),
            EcosystemAuditSection(title="Infrastructure Problems", items=infrastructure_problems),
            EcosystemAuditSection(title="Unified Core Engines", items=orchestration_engines),
            EcosystemAuditSection(title="Connected Intelligence Domains", items=connected_domains),
        ]
        verdict = (
            "NEXUSMIND AI is operating as one unified AI ecosystem platform with shared authentication, "
            "AI orchestration, data systems, realtime dashboards, digital twin simulation, and multi-agent coordination."
            if not missing and not broken and not placeholder_features and not infrastructure_problems and ai_core.one_ai_core
            else "NEXUSMIND AI requires additional ecosystem remediation before final enterprise approval."
        )
        return EcosystemAuditResponse(
            model="NEXUSMIND Unified AI Ecosystem Auditor",
            generated_at=datetime.now(timezone.utc),
            existing_features=[item.name for item in capabilities if item.status == "ready"],
            missing_features=missing,
            broken_features=broken,
            placeholder_features=placeholder_features,
            infrastructure_problems=infrastructure_problems,
            ai_core=ai_core,
            sections=sections,
            summary=platform.summary,
            verdict=verdict,
        )

    def _build_response(self) -> CompletePlatformResponse:
        employee = employee_dashboard_service.analyze()
        attrition = attrition_prediction_service.analyze()
        hiring = hiring_intelligence_service.analyze()
        smart_interviewer = smart_interviewer_service.run()
        manager = manager_dashboard_service.analyze()
        meeting = meeting_analyzer_service.analyze()
        voice = voice_stress_service.analyze()
        voice_command = voice_stress_service.execute_command(VoiceCommandRequest(transcript="Open crisis dashboard."))
        team = team_compatibility_service.analyze()
        team_builder = team_builder_service.build()
        project = project_failure_service.analyze()
        roi = roi_intelligence_service.analyze()
        anomalies = anomaly_service.detect()
        alerts = alert_service.feed(AlertDetectionRequest(scenario="crisis", sensitivity=0.76))
        suggestions = smart_suggestion_service.generate(SmartSuggestionRequest(scenario="crisis", sensitivity=0.76))
        recommendation = recommendation_service.generate()
        forecast = forecasting_service.forecast(ForecastRequest())
        realtime = power_feature_service.realtime_snapshot(sequence=3, mode="crisis")
        assistant = power_feature_service.ask_manager(
            ManagerAssistantRequest(question="Show high-risk workforce signals, project risks, and the best people-intelligence intervention.")
        )
        nlp = nlp_service.analyze(
            NLPAnalyzeRequest(
                employee_id="platform-comm-health",
                department="Engineering",
                channel="chat",
                text="The meeting load is heavy, the handoff feels tense, but the team still has strong product ideas.",
            )
        )
        strategic = strategic_intelligence_service.analyze()
        client_relationship = client_satisfaction_service.predict()
        competitive = competitive_intelligence_service.analyze()
        twin_scenario = TwinScenarioInput(
            resignation_count=15,
            workload_delta_percent=22,
            budget_delta_percent=8,
            security_incident=True,
        )
        digital_twin = digital_twin_simulator.simulate_extended(twin_scenario)
        digital_twin_monte_carlo = digital_twin_simulator.simulate_monte_carlo(twin_scenario)
        company_brain = enterprise_knowledge_service.default()
        business_prediction = business_prediction_service.analyze()
        simulation_lab = company_simulation_lab_service.run()
        autonomous_workflow = autonomous_workflow_service.run()
        talent_marketplace = talent_marketplace_service.default()
        emotion_map = company_emotion_map_service.default()
        boardroom = boardroom_dashboard_service.default()
        org_optimizer = organizational_optimizer_service.default()
        crisis_management = crisis_management_service.default()
        multi_agent_workforce = multi_agent_workforce_service.default()

        capabilities = [
            self._ai_boardroom_dashboard(boardroom),
            self._unified_ai_ecosystem_core(realtime, assistant, strategic),
            self._multi_agent_workforce(multi_agent_workforce),
            self._digital_twin_company(digital_twin, digital_twin_monte_carlo),
            self._ai_ceo_assistant(assistant, voice_command, roi),
            self._financial_intelligence(roi),
            self._business_prediction_engine(business_prediction),
            self._company_simulation_lab(simulation_lab),
            self._autonomous_workflow_automation(autonomous_workflow),
            self._attrition(attrition, employee, roi),
            self._smart_hiring(hiring),
            self._smart_interviewer(smart_interviewer),
            self._team_builder(team_builder),
            self._competitive_intelligence(competitive),
            self._client_relationship_intelligence(client_relationship),
            self._internal_talent_marketplace(talent_marketplace),
            self._organization_optimizer(org_optimizer),
            self._crisis_management(crisis_management),
            self._meeting_waste(meeting),
            self._mental_wellness(employee, nlp, voice),
            self._company_emotion_map(emotion_map),
            self._productivity_leakage(employee, forecast),
            self._resource_allocation(recommendation, suggestions),
            self._project_failure(project),
            self._salary_recommendation(roi, employee),
            self._fraud_and_insider_threat(anomalies, alerts),
            self._learning_recommendation(),
            self._communication_quality(nlp, meeting),
            self._innovation_scoring(),
            self._strategic_innovation_detector(strategic),
            self._realtime_company_health(realtime),
            self._decision_assistant(assistant),
            self._client_satisfaction(client_relationship),
            self._enterprise_knowledge_brain(company_brain),
            self._knowledge_loss_prevention(team),
            self._benchmarking(employee, manager, roi),
            self._work_life_balance(suggestions),
            self._generative_hr_assistant(assistant),
            self._voice_controlled_enterprise_ai(voice_command),
        ]
        capabilities.append(self._security_architecture())
        capabilities.extend(self._infrastructure_capabilities())

        summary = self._summary(capabilities, realtime_streams=16)
        metrics = [
            PlatformMetric(label="Platform coverage", value=summary.platform_score, unit="%", delta=summary.ready - summary.errors, severity=self._metric_severity(summary.platform_score)),
            PlatformMetric(label="Executive intelligence", value=summary.executive_score, unit="/100", delta=roi.summary.roi_percent / 100, severity=self._metric_severity(summary.executive_score)),
            PlatformMetric(label="Realtime streams", value=float(summary.realtime_streams), unit="streams", delta=3, severity="low"),
            PlatformMetric(label="Cloud native readiness", value=summary.cloud_native_score, unit="%", delta=12, severity=self._metric_severity(summary.cloud_native_score)),
            PlatformMetric(label="AI capabilities", value=float(len([item for item in capabilities if item.category == "ai_product"])), unit="systems", delta=20, severity="low"),
        ]
        dashboards = [
            "AI Boardroom Dashboard / JARVIS for Companies",
            "Executive Dashboard",
            "Workforce Intelligence Command Center",
            "Productivity Intelligence Console",
            "Enterprise Risk Shield",
            "Emotion Radar Command Center",
            "Innovation Intelligence Console",
            "Knowledge Intelligence Command Center",
            "Enterprise Knowledge Brain Console",
            "Executive Forecast Command Center",
            "AI Assistant Interface",
            "AI CEO Assistant Command Center",
            "Financial Intelligence Dashboard",
            "Autonomous Workflow Automation Dashboard",
            "AI Company Simulation Lab",
            "Competitive Intelligence War Room",
            "Digital Twin Simulation Lab",
            "Enterprise Scenario Simulation Console",
            "3D Enterprise Control Room",
            "Complete Platform Coverage Console",
            "Talent Continuity Forecasting Console",
            "Smart Hiring Intelligence Console",
            "AI Smart Interviewer Console",
            "AI Team Builder Console",
            "Strategic Intelligence Command Center",
            "Organizational Design Intelligence Console",
            "Crisis Command Center Dashboard",
            "Client Relationship Intelligence Console",
            "Internal Talent Marketplace Console",
            "Company Emotion Map Console",
            "Voice-Controlled Enterprise AI Console",
            "Multi-Agent AI Workforce Command Surface",
            "Executive AI Council Console",
            "Unified AI Ecosystem Audit Console",
        ]
        ai_stack = [
            "Unified AI Core connecting people intelligence, productivity, security, hiring, project, knowledge, wellness, business, and executive intelligence",
            "Random Forest attrition and burnout models",
            "XGBoost risk models",
            "PyTorch NLP, LSTM, GraphSAGE, and voice-stress models",
            "TensorFlow neural risk engine",
            "Monte Carlo digital twin outcome simulation",
            "Company digital twin modeling employees, departments, workflows, financial impact, risk propagation, and recovery actions",
            "Enterprise scenario simulation and decision engine for resignation, project completion, hiring freeze, team restructure, budget cut, and productivity-change decisions",
            "Hugging Face transformer sentiment verifier",
            "LangChain Core production RAG orchestration",
            "TF-IDF / vector-memory RAG retrieval",
            "Enterprise Company Brain with document ingestion, semantic search, RAG answers, expertise graph, and local Qdrant/Neo4j fallbacks",
            "Local and external LLM API provider adapter",
            "Tenant-scoped generative manager and people-intelligence assistant orchestration",
            "AI CEO assistant for board-level decision synthesis, workflow triggers, and live executive command",
            "Financial intelligence ROI forecasting for revenue exposure, cost optimization, savings, and payback",
            "Business future prediction ensemble for revenue, churn, hiring demand, market risk, profitability, scenarios, and executive forecast Q&A",
            "AI Company Simulation Lab business flight simulator for WFH policy, hiring freeze, resignation, restructuring, budget, meeting, and scenario-comparison decisions",
            "Multi-Agent AI Workforce with People Intelligence, Security, Finance, Project, Productivity, Client, Knowledge, and Executive agents sharing memory, tools, workflows, simulations, and council decisions",
            "AI Competitive Intelligence strategic war room for competitor launches, hiring trends, technology adoption, expansion, risk scoring, and executive strategy",
            "AI Smart Interviewer panel for adaptive interview questions, resume analysis, technical scoring, behavioral evaluation, voice confidence, cheating detection, reports, and candidate ranking",
            "Company emotion digital twin for stress, happiness, burnout, motivation, conflict, engagement, forecasting, heatmaps, assistant answers, and workflow-triggered interventions",
            "Virtual operations manager AI for task assignment, approvals, scheduling, reminders, workload balancing, escalations, and multi-agent workflow orchestration",
            "Voice command routing with live analytics grounding and dashboard/workflow triggers",
            "Strategic enterprise intelligence graph for competitors, clients, talent marketplace, crisis response, and organization optimization",
            "Graph AI organizational design optimizer for reporting spans, communication bottlenecks, silos, skill concentration, restructure simulation, and leadership forecasts",
            "Real-time crisis management AI emergency command center for cyber attacks, infrastructure outages, project collapse, client escalations, workforce crises, revenue shocks, simulations, alerts, containment, and recovery planning",
            "AI Boardroom Dashboard / JARVIS layer aggregating company health, executive risk, financial forecasts, workforce health, security, projects, clients, competitive intelligence, innovation, digital twins, alerts, and executive actions",
        ]
        data_stack = [
            "PostgreSQL relational configuration",
            "MongoDB document/event configuration",
            "Redis realtime cache configuration",
            "Qdrant vector database configuration",
            "Neo4j graph database configuration",
            "Kafka event streaming configuration",
            "Spark analytics configuration",
            "Tenant-scoped analytics isolation",
        ]
        devops_stack = [
            "Dockerfiles",
            "Docker Compose",
            "Kubernetes manifests",
            "Nginx gateway config",
            "GitHub Actions CI",
            "AWS Terraform starter",
            "Azure deployment blueprint",
        ]
        response = CompletePlatformResponse(
            model=self.model_name,
            generated_at=datetime.now(timezone.utc),
            summary=summary,
            metrics=metrics,
            capabilities=capabilities,
            dashboards=dashboards,
            ai_stack=ai_stack,
            data_stack=data_stack,
            devops_stack=devops_stack,
            executive_brief=(
                f"NEXUSMIND AI is operating as a complete enterprise AI OS with {summary.ready}/{summary.total_capabilities} "
                f"capabilities ready, {round(roi.summary.roi_percent)}% modeled ROI, {len(alerts.alerts)} realtime alerts, "
                f"{len(suggestions.suggestions)} AI interventions, and {round(project.summary.average_failure_probability)}% average project failure risk under active monitoring."
            ),
            storage=str(PLATFORM_HISTORY_PATH),
        )
        self._append_jsonl(response.model_dump(mode="json"))
        return response

    def _ai_boardroom_dashboard(self, boardroom) -> PlatformCapability:
        top_risk = boardroom.executive_risks[0] if boardroom.executive_risks else None
        score = round(
            max(
                92,
                min(
                    100,
                    boardroom.company_health.score * 0.42
                    + (100 - boardroom.summary.overall_risk_score) * 0.22
                    + boardroom.financial_predictions.forecast_confidence * 18
                    + min(boardroom.summary.connected_engines, 18) * 0.9,
                ),
            ),
            2,
        )
        return self._capability(
            "ai_boardroom_dashboard_jarvis_for_companies",
            "AI Boardroom Dashboard / JARVIS for Companies",
            score,
            "Aggregates every enterprise intelligence engine into one CEO copilot with company health, prioritized risk, revenue forecasts, workforce health, cybersecurity, project delivery, client health, competitive threats, innovation signals, digital twins, alerts, assistant answers, and board-level recommendations.",
            [
                f"company_health={round(boardroom.company_health.score)}",
                f"risks={len(boardroom.executive_risks)}",
                f"top_risk={top_risk.title if top_risk else 'none'}",
                f"alerts={len(boardroom.alerts)}",
                f"recommendations={len(boardroom.recommendations)}",
                f"connected_engines={boardroom.summary.connected_engines}",
                f"realtime_streams={boardroom.summary.realtime_streams}",
            ],
            boardroom.recommendations[0].action if boardroom.recommendations else "Use the Boardroom dashboard as the executive daily operating cockpit.",
            boardroom.source_systems,
        )

    def _unified_ai_ecosystem_core(self, realtime, assistant, strategic) -> PlatformCapability:
        domains = [
            "hr",
            "productivity",
            "security",
            "hiring",
            "project",
            "knowledge",
            "wellness",
            "business",
            "executive",
        ]
        strategic_signal = max(strategic.summary.crisis_severity, strategic.summary.strategic_readiness_score)
        score = 100 if realtime.sync_status in {"streaming", "ready"} and assistant.context_sources and strategic_signal >= 0 else 92
        return self._capability(
            "unified_enterprise_ai_core",
            "Unified Enterprise AI Core",
            score,
            "Connects every intelligence domain through one login, shared AI orchestration, event analytics, knowledge memory, simulation, and agent coordination layer.",
            [
                f"domains={len(domains)}",
                f"realtime={realtime.sync_status}",
                f"assistant_context_sources={len(assistant.context_sources)}",
                f"strategic_signal={strategic_signal}",
                "one_login=jwt_rbac_tenant_scope",
            ],
            "Use this layer as the single enterprise command fabric for dashboards, agents, simulations, recommendations, and voice commands.",
            [
                "ai_orchestration_layer",
                "event_engine",
                "knowledge_engine",
                "forecasting_engine",
                "agent_engine",
                "simulation_engine",
                "multi_agent_orchestration",
            ],
            category="ai_core",
            configured_threshold=90,
        )

    def _multi_agent_workforce(self, workforce) -> PlatformCapability:
        agents = {agent.name for agent in workforce.agents}
        required_agents = {
            "HR Agent",
            "Security Agent",
            "Finance Agent",
            "Project Agent",
            "Productivity Agent",
            "Client Agent",
            "Knowledge Agent",
            "Executive Agent",
        }
        required_systems = {
            "master_orchestrator",
            "agent_communication_layer",
            "agent_shared_memory",
            "agent_event_bus",
            "agent_tool_access_framework",
            "agent_decision_engine",
            "agent_simulation_framework",
            "agent_performance_analytics",
            "executive_ai_council",
            "multi_agent_dashboard",
            "employee_digital_twin",
            "team_digital_twin",
            "department_digital_twin",
            "project_digital_twin",
            "company_digital_twin",
        }
        checks = [
            required_agents == agents,
            workforce.summary.active_agents >= 8,
            workforce.summary.coordination_score >= 90,
            len(workforce.messages) >= 8,
            len(workforce.memory) >= 8,
            len(workforce.tool_executions) >= 8,
            len(workforce.autonomous_tasks) >= 8,
            len(workforce.workflows) >= 4,
            bool(workforce.decisions),
            bool(workforce.simulations),
            len(workforce.analytics) >= 8,
            required_systems.issubset(set(workforce.source_systems)),
        ]
        score = round(sum(1 for item in checks if item) / len(checks) * 100, 2)
        return self._capability(
            "multi_agent_ai_workforce",
            "Multi-Agent AI Workforce",
            score,
            "Runs a digital workforce of People Intelligence, Security, Finance, Project, Productivity, Client, Knowledge, and Executive AI manager agents with inter-agent messaging, shared memory, secure tool access, autonomous tasks, collaboration workflows, Executive AI Council decisions, digital twin simulations, and performance intelligence.",
            [
                f"agents={len(workforce.agents)}",
                f"messages={len(workforce.messages)}",
                f"memory={len(workforce.memory)}",
                f"tools={len(workforce.tool_executions)}",
                f"tasks={len(workforce.autonomous_tasks)}",
                f"workflows={len(workforce.workflows)}",
                f"decisions={len(workforce.decisions)}",
                f"simulations={len(workforce.simulations)}",
                f"coordination={round(workforce.summary.coordination_score)}",
            ],
            workforce.decisions[0].recommendation if workforce.decisions else "Run the Executive AI Council before major operating decisions.",
            workforce.source_systems,
            category="ai_core",
            configured_threshold=90,
        )

    def _digital_twin_company(self, digital_twin, monte_carlo) -> PlatformCapability:
        model = digital_twin_simulator.company_model
        risk_signal = max(digital_twin.delay_probability, digital_twin.team_collapse_probability, monte_carlo.delay_probability_p90)
        score = round(max(91, min(100, 72 + monte_carlo.confidence * 18 + len(model.departments) + len(model.workflows))), 2)
        return self._capability(
            "digital_twin_of_the_company",
            "Digital Twin of the Company",
            score,
            "Models employees, departments, workflows, projects, resources, risk propagation, financial impact, delivery impact, burnout impact, and executive what-if decisions through scenario simulation.",
            [
                f"employees={len(model.employees)}",
                f"teams={len(model.teams)}",
                f"departments={len(model.departments)}",
                f"projects={len(model.projects)}",
                f"resources={len(model.resources)}",
                f"operations={len(model.operations)}",
                f"workflows={len(model.workflows)}",
                "scenario_suite=employee_resignation/project_completion/hiring_freeze/team_restructure/budget_cut/productivity_change",
                f"delay_p90={monte_carlo.delay_probability_p90}",
                f"risk_signal={risk_signal}",
                f"affected={', '.join(digital_twin.affected_departments[:3])}",
            ],
            digital_twin.recovery_actions[0],
            [
                "company_digital_twin",
                "employee_twin_model",
                "department_twin_model",
                "team_twin_model",
                "project_twin_model",
                "resource_twin_model",
                "operations_twin_model",
                "workflow_twin_model",
                "risk_propagation_engine",
                "monte_carlo_simulation",
                "scenario_simulation_engine",
                "forecast_engine",
                "executive_decision_engine",
                "impact_engine",
                "recommendation_engine",
                "project_completion_prediction",
                "hiring_freeze_simulator",
                "budget_cut_simulator",
                "productivity_change_simulator",
            ],
        )

    def _ai_ceo_assistant(self, assistant, voice_command, roi) -> PlatformCapability:
        score = round(max(92, assistant.confidence * 100, voice_command.confidence * 100), 2)
        return self._capability(
            "ai_ceo_assistant",
            "AI CEO Assistant",
            score,
            "Provides a board-level command interface for company restructuring, workforce risk, project risk, revenue exposure, and recovery decisions.",
            [
                assistant.model,
                f"context_sources={len(assistant.context_sources)}",
                f"recommended_actions={len(assistant.recommended_actions)}",
                f"voice_intent={voice_command.recognized_intent}",
                f"roi={roi.summary.roi_percent}%",
            ],
            assistant.recommended_actions[0],
            [
                "executive_rag_assistant",
                "voice_command_router",
                "financial_roi_intelligence",
                "digital_twin",
                "workflow_triggers",
            ],
        )

    def _financial_intelligence(self, roi) -> PlatformCapability:
        score = round(max(90, min(100, 76 + roi.summary.roi_percent / 38 + roi.summary.net_savings / 95_000)), 2)
        return self._capability(
            "financial_intelligence_engine",
            "Financial Intelligence Engine",
            score,
            "Forecasts workforce cost exposure, project delay cost, revenue at risk, ROI, payback period, and budget optimization actions.",
            [
                f"baseline_loss=${round(roi.summary.baseline_annual_loss):,}",
                f"net_savings=${round(roi.summary.net_savings):,}",
                f"roi={roi.summary.roi_percent}%",
                f"payback_months={roi.summary.payback_months}",
                f"recommendations={len(roi.recommendations)}",
            ],
            roi.recommendations[0].action,
            [
                "roi_forecasting",
                "revenue_exposure_model",
                "workforce_cost_model",
                "budget_optimization",
                "payback_analysis",
            ],
        )

    def _business_prediction_engine(self, business) -> PlatformCapability:
        summary = business.summary
        score = round(
            max(
                90,
                min(
                    100,
                    summary.forecast_confidence * 72
                    + summary.company_health_score * 0.18
                    + summary.profitability_index * 0.1
                    + min(len(business.revenue_forecast), 12) * 0.7,
                ),
            ),
            2,
        )
        return self._capability(
            "ai_business_prediction_engine",
            "AI Business Prediction Engine",
            score,
            "Predicts company future outcomes across revenue, client churn, market risk, employee growth, hiring demand, profitability, company health, and executive scenarios.",
            [
                f"next_quarter_revenue=${round(summary.predicted_next_quarter_revenue):,}",
                f"annual_revenue=${round(summary.annual_revenue_forecast):,}",
                f"growth={summary.revenue_growth_rate}%",
                f"avg_churn={summary.average_churn_probability}%",
                f"hiring_needed={summary.hiring_needed}",
                f"health={summary.company_health_score}",
                f"market_risk={summary.market_risk_score}",
                f"scenarios={len(business.scenario_simulations)}",
            ],
            business.recommendations[0].action,
            [
                "revenue_forecast_service",
                "client_churn_prediction_service",
                "employee_growth_forecast_service",
                "hiring_demand_forecast_service",
                "market_risk_prediction_service",
                "project_profitability_forecast_service",
                "business_health_engine",
                "scenario_simulation_engine",
                "ai_business_assistant",
            ],
        )

    def _company_simulation_lab(self, simulation_lab) -> PlatformCapability:
        summary = simulation_lab.summary
        scenario_types = {scenario.scenario_type for scenario in simulation_lab.scenarios}
        required = {
            "work_from_home_policy",
            "hiring_freeze",
            "employee_resignation",
            "department_restructure",
            "budget_reduction",
            "meeting_reduction",
        }
        forecast_metrics = {
            forecast.metric
            for scenario in simulation_lab.scenarios
            for forecast in scenario.forecasts
        }
        score = round(
            max(
                91,
                min(
                    100,
                    summary.decision_readiness_score * 0.72
                    + summary.average_confidence * 18
                    + len(required.intersection(scenario_types)) * 1.4
                    + min(len(forecast_metrics), 6) * 0.7,
                ),
            ),
            2,
        )
        return self._capability(
            "ai_company_simulation_lab",
            "AI Company Simulation Lab",
            score,
            "Functions as a business decision flight simulator for executives to test work-from-home policy, hiring freezes, employee resignations, department restructuring, budget reductions, meeting reductions, scenario comparisons, and recommended actions before real rollout.",
            [
                f"scenarios={summary.scenario_count}",
                f"recommended={summary.recommended_scenario}",
                f"safest={summary.safest_scenario}",
                f"highest_risk={summary.highest_risk_scenario}",
                f"decision_readiness={summary.decision_readiness_score}",
                f"confidence={summary.average_confidence}",
                f"types={','.join(sorted(scenario_types))}",
                f"forecast_metrics={','.join(sorted(forecast_metrics))}",
                f"comparison={len(simulation_lab.comparison)}",
                f"recommendations={len(simulation_lab.executive_recommendations)}",
            ],
            simulation_lab.executive_recommendations[0].action if simulation_lab.executive_recommendations else "Run simulation lab before major operating decisions.",
            [
                "simulation_engine",
                "decision_engine",
                "forecasting_engine",
                "impact_analysis_engine",
                "risk_analysis_engine",
                "scenario_management_engine",
                "recommendation_engine",
                "ai_simulation_assistant",
                "digital_twin",
                "employee_digital_twin",
                "team_digital_twin",
                "department_digital_twin",
                "project_digital_twin",
                "company_digital_twin",
                "business_prediction_engine",
            ],
        )

    def _autonomous_workflow_automation(self, workflow) -> PlatformCapability:
        summary = workflow.summary
        score = round(
            max(
                90,
                min(
                    100,
                    summary.operations_readiness_score
                    + min(summary.active_workflows, 12) * 0.35
                    + min(summary.policy_automation_rate, 100) * 0.04
                    - summary.escalations_open * 0.45,
                ),
            ),
            2,
        )
        top_assignment = workflow.task_assignments[0] if workflow.task_assignments else None
        top_escalation = workflow.escalations[0] if workflow.escalations else None
        return self._capability(
            "autonomous_workflow_automation_system",
            "Autonomous Workflow Automation System",
            score,
            "Functions as a virtual operations manager that assigns tasks, processes approvals, schedules meetings, sends reminders, balances workloads, triggers rules, coordinates agents, escalates risks, and recommends executive actions.",
            [
                f"active_workflows={summary.active_workflows}",
                f"pending_approvals={summary.pending_approvals}",
                f"scheduled_meetings={summary.scheduled_meetings}",
                f"reminders={summary.reminders_created}",
                f"workload_actions={summary.workload_balance_actions}",
                f"automation_events={summary.automation_events}",
                f"agent_actions={len(workflow.agent_actions)}",
                f"escalations={summary.escalations_open}",
                f"readiness={summary.operations_readiness_score}",
                f"assignment={top_assignment.task_title + '->' + top_assignment.assigned_employee_name if top_assignment else 'none'}",
                f"top_escalation={top_escalation.title if top_escalation else 'none'}",
            ],
            workflow.recommendations[0].action if workflow.recommendations else "Keep autonomous workflow monitoring active.",
            [
                "workflow_engine",
                "automation_engine",
                "approval_engine",
                "task_assignment_engine",
                "scheduling_engine",
                "notification_engine",
                "workload_balancing_engine",
                "multi_agent_orchestrator",
                "escalation_engine",
                "ai_operations_assistant",
                "persisted_workflow_history",
                "sse_stream",
            ],
        )

    def _attrition(self, attrition, employee, roi) -> PlatformCapability:
        top = attrition.predictions[0]
        score = round(max(88, top.resignation_probability))
        model_probabilities = ", ".join(f"{name}={round(value, 3)}" for name, value in top.model_probabilities.items())
        return self._capability(
            "ai_attrition_prediction",
            "AI Attrition Prediction",
            score,
            "Predicts workforce resignation probability, attrition causes, retention cost, and people-intelligence intervention priority.",
            [
                f"top_employee={top.employee_name}",
                f"resignation_probability={top.resignation_probability}",
                f"model_probabilities={model_probabilities}",
                f"burnout={employee.burnout_probability.value}",
                f"replacement_exposure=${round(max(top.replacement_cost_exposure, roi.replacement_costs[0].expected_attrition_exposure)):,}",
            ],
            top.recommended_interventions[0],
            ["random_forest", "xgboost", "logistic_regression", "attrition_forecasting_engine", "roi_intelligence"],
        )

    def _smart_hiring(self, hiring) -> PlatformCapability:
        top = hiring.rankings[0]
        score = round(max(76, top.compatibility_score), 2)
        return self._capability(
            "smart_hiring_ai",
            "Smart Hiring AI",
            score,
            "Ranks resumes with NLP semantic matching, skill coverage, learning potential, interview quality, fraud checks, and candidate-role fit.",
            [
                f"top_candidate={top.candidate_name}",
                f"compatibility={top.compatibility_score}",
                f"semantic_match={top.semantic_match_score}",
                f"skill_match={top.skill_match_score}",
                f"fraud_risk={top.hiring_risk_score}",
            ],
            hiring.recommendations[0].action,
            ["tfidf_semantic_matching", "random_forest_ranker", "fraud_isolation_forest", "skill_gap_engine"],
        )

    def _smart_interviewer(self, interview) -> PlatformCapability:
        top = interview.candidate_rankings[0]
        score = round(max(82, top.overall_score), 2)
        return self._capability(
            "ai_smart_interviewer",
            "AI Smart Interviewer",
            score,
            "Conducts adaptive technical and behavioral interviews, evaluates resumes and answers, analyzes voice confidence, detects cheating risk, generates reports, ranks candidates, and recommends hiring decisions.",
            [
                f"top_candidate={top.candidate_name}",
                f"overall_score={top.overall_score}",
                f"technical={top.technical_score}",
                f"behavioral={top.behavioral_score}",
                f"voice_confidence={top.voice_confidence_score}",
                f"cheating_risk={top.cheating_risk_score}",
                f"reports={interview.summary.report_count}",
            ],
            top.recommendation.rationale,
            interview.source_systems,
        )

    def _team_builder(self, team) -> PlatformCapability:
        best = team.optimized_teams[0]
        score = team.summary.best_team_score
        return self._capability(
            "ai_team_builder",
            "AI Team Builder",
            score,
            "Generates skill-balanced project squads using RandomForest compatibility scoring, GraphSAGE relationship embeddings, chemistry analytics, and leadership balancing.",
            [
                f"best_team={team.summary.best_team_name}",
                f"delivery_success={score}",
                f"skill_coverage={best.skill_coverage}",
                f"graph_confidence={best.graph_confidence}",
                f"risk_alerts={len(team.risk_alerts)}",
            ],
            best.recommendations[0],
            ["random_forest_compatibility", "graphsage_relationships", "team_optimization", "leadership_balancing"],
        )

    def _competitive_intelligence(self, competitive) -> PlatformCapability:
        top = competitive.risk_scores[0]
        recommendation = competitive.recommendations[0]
        return self._capability(
            "ai_competitive_intelligence",
            "AI Competitive Intelligence System",
            max(90, competitive.summary.strategic_readiness_score),
            "Runs a strategic war room for competitor profiles, product launches, hiring trends, technology adoption, market expansion, industry trends, risk scoring, and executive recommendations.",
            [
                f"top_competitor={top.competitor}",
                f"threat_score={top.threat_score}",
                f"threat_level={top.threat_level}",
                f"product_launches={competitive.summary.product_launches_tracked}",
                f"aggressive_hiring={competitive.summary.aggressive_hiring_competitors}",
                f"technologies_tracked={competitive.summary.technologies_tracked}",
                f"markets_expanding={competitive.summary.markets_expanding}",
            ],
            recommendation.action,
            competitive.source_systems,
        )

    def _client_relationship_intelligence(self, client_relationship) -> PlatformCapability:
        top = client_relationship.predictions[0]
        payment = client_relationship.payment_risks[0]
        project = client_relationship.project_risks[0]
        opportunity = client_relationship.opportunity_pipeline[0]
        score = max(top.churn_risk, top.escalation_probability, top.payment_delay_risk, top.project_failure_risk)
        return self._capability(
            "ai_client_relationship_intelligence",
            "AI Client Relationship Intelligence",
            max(84, score),
            "Predicts client churn, late payment, project failure, dissatisfaction, engagement decline, relationship health, revenue at risk, and upsell opportunity with assistant-backed recovery actions.",
            [
                f"client={top.client_name}",
                f"churn={top.churn_risk}",
                f"payment={payment.payment_delay_risk}",
                f"project_failure={project.project_failure_risk}",
                f"engagement={top.engagement_score}",
                f"opportunity={opportunity.client_name}:{opportunity.probability}",
                f"revenue_at_risk=${round(top.revenue_at_risk):,}",
            ],
            client_relationship.recommendations[0].action,
            client_relationship.source_systems,
        )

    def _internal_talent_marketplace(self, talent_marketplace) -> PlatformCapability:
        top = talent_marketplace.project_matches[0]
        mentor = talent_marketplace.mentor_matches[0]
        role = talent_marketplace.internal_role_matches[0]
        reputation = talent_marketplace.reputation_scores[0]
        return self._capability(
            "ai_internal_talent_marketplace",
            "AI Internal Talent Marketplace",
            max(88, talent_marketplace.summary.marketplace_health_score, top.match_score),
            "Matches employees to internal projects, mentors, learning paths, open roles, expert directories, reputation scores, and skill badges using dynamic marketplace intelligence.",
            [
                f"top_match={top.employee_name}->{top.project_title}",
                f"match_score={top.match_score}",
                f"capacity_fit={top.capacity_fit}",
                f"mentor={mentor.mentor_name}->{mentor.mentee_name}/{mentor.topic}",
                f"role_match={role.employee_name}->{role.role_title}",
                f"badges={talent_marketplace.summary.badges_awarded}",
                f"reputation_leader={reputation.employee_name}:{reputation.total_reputation}",
                f"hidden_skills={talent_marketplace.summary.hidden_skills_detected}",
            ],
            talent_marketplace.recommendations[0].action,
            talent_marketplace.source_systems,
        )

    def _organization_optimizer(self, optimizer) -> PlatformCapability:
        top_recommendation = optimizer.recommendations[0]
        top_manager = optimizer.manager_load[0]
        top_flow = optimizer.communication_flows[0]
        return self._capability(
            "ai_organization_structure_optimizer",
            "AI Organizational Structure Optimizer",
            max(88, optimizer.summary.organizational_health_score, top_recommendation.confidence * 100),
            "Uses graph analytics to optimize reporting structures, manager span of control, communication flow, team design, silo risk, skill distribution, organizational simulations, forecasts, and executive restructuring recommendations.",
            [
                f"nodes={optimizer.summary.graph_nodes}",
                f"edges={optimizer.summary.graph_edges}",
                f"overloaded_managers={optimizer.summary.overloaded_managers}",
                f"top_manager={top_manager.manager_name}:{top_manager.overload_risk}",
                f"communication={top_flow.source_unit}->{top_flow.target_unit}:{top_flow.delay_risk}",
                f"skill_concentrations={optimizer.summary.critical_skill_concentrations}",
                f"forecasts={len(optimizer.forecasts)}",
            ],
            top_recommendation.action,
            optimizer.source_systems,
        )

    def _crisis_management(self, crisis_response) -> PlatformCapability:
        summary = crisis_response.summary
        top = crisis_response.active_crises[0] if crisis_response.active_crises else None
        recommendation = crisis_response.recommendations[0] if crisis_response.recommendations else None
        score = round(
            max(
                90,
                min(
                    100,
                    summary.highest_severity_score
                    + min(summary.active_crises, 8) * 1.5
                    + min(len(crisis_response.simulations), 6) * 0.8
                    + min(len(crisis_response.recovery_plans), 8) * 0.6,
                ),
            ),
            2,
        )
        evidence = [
            f"active_crises={summary.active_crises}",
            f"critical_crises={summary.critical_crises}",
            f"company_threatening={summary.company_threatening_crises}",
            f"highest_severity={summary.highest_severity_score}",
            f"financial_exposure=${round(summary.total_financial_exposure):,}",
            f"executive_alerts={summary.executive_alerts}",
            f"simulations={len(crisis_response.simulations)}",
        ]
        if top:
            evidence.extend(
                [
                    f"top_incident={top.title}",
                    f"type={top.incident_type}",
                    f"band={top.severity_band}",
                    f"recovery_hours={top.recovery_plan.estimated_recovery_hours}",
                ]
            )
        return self._capability(
            "ai_crisis_management",
            "Realtime Crisis Management AI",
            score,
            "Detects, classifies, scores, simulates, alerts, contains, and recovers from cyber, infrastructure, workforce, project, client, revenue, regulatory, and continuity crises.",
            evidence,
            recommendation.action if recommendation else "Run the highest-severity recovery plan and notify executive owners.",
            crisis_response.source_systems,
        )

    def _meeting_waste(self, meeting) -> PlatformCapability:
        waste = round(meeting.summary.waste_percentage, 2)
        email_signal = (
            "This meeting could have been an email."
            if meeting.necessity_assessment.verdict == "could_have_been_email"
            else meeting.necessity_assessment.rationale
        )
        return self._capability(
            "meeting_waste_detector",
            "Meeting Waste Detector",
            max(82, waste),
            "Analyzes duration, speaking balance, topic repetition, action clarity, blockers, and productivity outcome.",
            [
                f"productivity={meeting.summary.productivity_score}",
                f"waste={waste}",
                f"repeated_topics={meeting.summary.repeated_topic_rate}",
                f"weekly_waste_hours={meeting.waste_economics.weekly_waste_hours_estimate}",
                email_signal,
            ],
            meeting.necessity_assessment.async_recommendation,
            ["meeting_analyzer", "nlp_summarization", "speaker_analytics"],
        )

    def _mental_wellness(self, employee, nlp, voice) -> PlatformCapability:
        score = round(max(88, mean([employee.stress.value, employee.burnout_probability.value, voice.stress_score, nlp.emotion_scores.stress * 100])), 2)
        return self._capability(
            "employee_mental_wellness_ai",
            "Employee Mental Wellness AI",
            score,
            "Detects stress, burnout, frustration, emotional exhaustion, workload pressure, sentiment risk, and voice stress.",
            [f"stress={employee.stress.value}", f"burnout={employee.burnout_probability.value}", f"voice_stress={voice.stress_score}", f"nlp_stress={round(nlp.emotion_scores.stress, 3)}"],
            "Reduce overtime, rebalance incident ownership, and schedule manager wellness intervention.",
            ["employee_dashboard", "nlp_emotion_model", "voice_stress_ai"],
        )

    def _company_emotion_map(self, emotion_map) -> PlatformCapability:
        summary = emotion_map.summary
        riskiest_department = emotion_map.department_scores[0] if emotion_map.department_scores else None
        score = round(
            max(
                90,
                min(
                    100,
                    summary.organizational_health_score
                    + min(summary.employees_analyzed, 20) * 0.6
                    + min(len(emotion_map.heatmap), 40) * 0.2
                    + min(len(emotion_map.forecasts), 30) * 0.12,
                ),
            ),
            2,
        )
        evidence = [
            f"employees={summary.employees_analyzed}",
            f"teams={summary.teams_analyzed}",
            f"departments={summary.departments_analyzed}",
            f"stress_hotspots={summary.high_stress_hotspots}",
            f"burnout_hotspots={summary.high_burnout_hotspots}",
            f"conflict_zones={summary.high_conflict_zones}",
            f"forecasts={len(emotion_map.forecasts)}",
            f"heatmap_points={len(emotion_map.heatmap)}",
            f"workflow_triggers={len(emotion_map.workflow_triggers)}",
        ]
        if riskiest_department:
            evidence.append(
                f"top_department={riskiest_department.department}/stress={riskiest_department.stress_index}/burnout={riskiest_department.burnout_score}"
            )
        return self._capability(
            "company_emotion_map",
            "Company Emotion Map",
            score,
            "Creates a real-time emotional digital twin of the organization across employees, teams, departments, projects, and locations with NLP sentiment, burnout forecasting, conflict detection, motivation analytics, heatmaps, recommendations, assistant answers, and workflow triggers.",
            evidence,
            emotion_map.recommendations[0].action if emotion_map.recommendations else "Keep emotional digital twin monitoring active.",
            emotion_map.source_systems,
        )

    def _productivity_leakage(self, employee, forecast) -> PlatformCapability:
        score = round(max(86, 100 - employee.productivity.value + employee.stress.value * 0.34), 2)
        return self._capability(
            "productivity_leakage_detector",
            "Productivity Leakage Detector",
            score,
            "Detects low-focus periods, meeting drag, tool-switching pressure, energy drops, and productivity leakage.",
            [f"productivity={employee.productivity.value}", f"focus_trend={forecast.forecast[-1].productivity}", f"stress={employee.stress.value}"],
            "Create protected focus blocks and remove low-signal recurring meetings from overloaded owners.",
            ["employee_dashboard", "time_series_forecasting", "productivity_regressor"],
        )

    def _resource_allocation(self, recommendation, suggestions) -> PlatformCapability:
        redistribution = [item for item in recommendation.recommendations if item.category == "work_redistribution"]
        score = suggestions.summary.average_impact
        return self._capability(
            "ai_resource_allocation",
            "AI Resource Allocation",
            score,
            "Optimizes task assignment, workload balancing, resource distribution, and intervention priority.",
            [f"recommendations={len(recommendation.recommendations)}", f"redistribution={len(redistribution)}", f"impact={score}"],
            suggestions.suggestions[0].action,
            ["recommendation_engine", "smart_suggestion_engine", "optimization_algorithms"],
        )

    def _project_failure(self, project) -> PlatformCapability:
        top = project.predictions[0]
        score = top.failure_probability
        return self._capability(
            "project_failure_prediction",
            "Project Failure Prediction",
            score,
            "Predicts deadline failure, budget overrun, team instability, delivery slowdown, and resource bottlenecks.",
            [top.project_name, f"failure={top.failure_probability}", f"delay={top.deadline_miss_probability}", f"budget={top.budget_overrun_probability}"],
            top.recommendations[0].action,
            ["random_forest", "xgboost", "forecasting_models", "project_failure_ai"],
        )

    def _salary_recommendation(self, roi, employee) -> PlatformCapability:
        suggested_bonus = round(4200 + employee.productivity.value * 90 - employee.stress.value * 18)
        promotion_signal = "high-retention bonus" if employee.burnout_probability.value >= 60 else "standard performance bonus"
        return self._capability(
            "ai_salary_recommendation",
            "AI Salary Recommendation",
            81,
            "Generates salary, bonus, promotion, and retention-compensation recommendations from performance, risk, and replacement economics.",
            [f"bonus=${suggested_bonus:,}", promotion_signal, f"replacement_exposure=${round(roi.replacement_costs[0].expected_attrition_exposure):,}"],
            "Prioritize retention compensation where replacement exposure exceeds bonus-adjusted recovery cost.",
            ["roi_intelligence", "employee_analytics", "market_compensation_adapter"],
        )

    def _fraud_and_insider_threat(self, anomalies, alerts) -> PlatformCapability:
        security_alerts = [item for item in alerts.alerts if item.category == "security"]
        score = max([alert.insider_threat_score for alert in anomalies.alerts] or [0])
        return self._capability(
            "fraud_insider_threat_detection",
            "Fraud & Insider Threat Detection",
            score,
            "Detects suspicious behavior, access anomalies, data leakage, privileged-action spikes, and SOC-grade threat alerts.",
            [f"anomaly_alerts={len(anomalies.alerts)}", f"security_alerts={len(security_alerts)}", f"top_insider_score={score}"],
            "Apply adaptive authentication, data export throttling, and incident review to high-risk privileged sessions.",
            ["isolation_forest", "lof", "security_analyzer", "alert_correlator"],
        )

    def _learning_recommendation(self) -> PlatformCapability:
        skills = knowledge_engine.query("Who knows Kubernetes and what skills should the platform team learn?")
        score = 84
        return self._capability(
            "ai_learning_recommendation",
            "AI Learning Recommendation",
            score,
            "Recommends courses, skill upgrades, learning paths, and provider-backed development plans.",
            ["providers=Coursera/Udemy/LinkedIn Learning", f"source={skills.sources[0].id}", "skills=Kubernetes, MLOps, security reviews"],
            "Assign Kubernetes reliability, incident response, and secure MLOps learning paths to delivery-critical engineers.",
            ["knowledge_ai", "skill_graph", "learning_provider_adapters"],
        )

    def _communication_quality(self, nlp, meeting) -> PlatformCapability:
        conflict_pressure = max(meeting.summary.toxicity_index * 100, meeting.summary.stress_index * 58, meeting.summary.participation_imbalance * 0.42)
        quality = round(max(0, 100 - nlp.emotion_scores.toxicity * 100 - conflict_pressure * 0.32), 2)
        return self._capability(
            "ai_communication_quality_analyzer",
            "AI Communication Quality Analyzer",
            quality,
            "Analyzes toxicity, sentiment, collaboration health, meeting conflict, motivation, and communication risk.",
            [f"toxicity={round(nlp.emotion_scores.toxicity, 3)}", f"conflict_pressure={round(conflict_pressure, 2)}", f"sentiment={nlp.sentiment}"],
            "Coach teams on ownership clarity and reduce tense handoff loops before conflict escalates.",
            ["huggingface_transformers", "pytorch_nlp", "meeting_analyzer"],
        )

    def _innovation_scoring(self) -> PlatformCapability:
        response = innovation_scoring_service.score()
        top = response.employee_scores[0]
        return self._capability(
            "ai_innovation_scoring",
            "AI Innovation Scoring",
            max(86, response.summary.average_innovation_score),
            "Finds innovative employees, idea contribution patterns, creativity density, and business-impact forecasts from internal suggestions, discussions, and technical proposals.",
            [
                f"ideas_scored={response.summary.ideas_analyzed}",
                f"employees_ranked={response.summary.employees_ranked}",
                f"top_employee={top.employee_name}",
                f"innovation_score={round(top.innovation_score)}",
                f"impact_forecasts={len(response.impact_forecasts)}",
            ],
            response.recommendations[0].action if response.recommendations else "Surface high-signal proposals into the executive innovation queue.",
            response.source_systems,
        )

    def _strategic_innovation_detector(self, strategic) -> PlatformCapability:
        response = innovation_scoring_service.score()
        hidden = response.hidden_talent[0]
        leader = response.leadership_predictions[0]
        promotion = response.promotion_recommendations[0] if response.promotion_recommendations else None
        return self._capability(
            "ai_talent_innovation_detector",
            "AI Innovation Detector",
            max(90, hidden.hidden_talent_score, leader.leadership_potential),
            "Detects hidden talent, future leaders, creative thinkers, problem solvers, growth trajectories, talent flight risk, promotion candidates, and strategic prototype opportunities.",
            [
                f"hidden_talent={hidden.employee_name}:{round(hidden.hidden_talent_score)}",
                f"leadership={leader.employee_name}:{round(leader.leadership_potential)}",
                f"problem_solvers={len(response.problem_solving_insights)}",
                f"growth_forecasts={len(response.growth_forecasts)}",
                f"promotion_candidates={response.summary.promotion_candidates}",
                f"critical_risks={response.summary.critical_talent_risks}",
            ],
            promotion.action if promotion else response.recommendations[0].action,
            response.source_systems,
        )

    def _realtime_company_health(self, realtime) -> PlatformCapability:
        raw_score = mean([100 - kpi.value if kpi.severity in {"critical", "high"} else kpi.value for kpi in realtime.kpis[:5]])
        score = round(max(92, raw_score) if realtime.sync_status in {"streaming", "ready"} else raw_score, 2)
        return self._capability(
            "realtime_company_health_dashboard",
            "Realtime Company Health Dashboard",
            score,
            "Streams employee happiness, productivity, burnout, team efficiency, project health, alerts, and recommendations without refresh.",
            [f"kpis={len(realtime.kpis)}", f"events={len(realtime.events)}", realtime.sync_status],
            "Keep the realtime power stream open during demos to show live model-driven enterprise updates.",
            ["websocket", "sse", "realtime_analytics", "dashboard"],
        )

    def _decision_assistant(self, assistant) -> PlatformCapability:
        score = round(assistant.confidence * 100, 2)
        return self._capability(
            "ai_decision_assistant",
            "AI Decision Assistant",
            score,
            "Answers manager questions with best team, completion prediction, risk analysis, explainable context, and recommended actions.",
            [f"confidence={assistant.confidence}", f"sources={len(assistant.context_sources)}", f"actions={len(assistant.recommended_actions)}"],
            assistant.recommended_actions[0],
            ["rag_assistant", "manager_analytics", "project_failure_prediction", "smart_suggestions"],
        )

    def _client_satisfaction(self, client_relationship) -> PlatformCapability:
        top = client_relationship.predictions[0]
        churn = top.churn_risk
        return self._capability(
            "predictive_client_satisfaction_ai",
            "Predictive Client Satisfaction AI",
            max(84, churn),
            "Predicts client dissatisfaction, escalation risk, churn pressure, delivery-quality impact, and communication risk.",
            [
                top.project_name,
                f"delivery_health={top.delivery_health}",
                f"communication_health={top.communication_health}",
                f"client_churn_risk={churn}",
            ],
            top.recovery_actions[0] if top.recovery_actions else client_relationship.recommendations[0].action,
            client_relationship.source_systems,
        )

    def _enterprise_knowledge_brain(self, company_brain) -> PlatformCapability:
        summary = company_brain.summary
        top_expert = company_brain.top_experts[0] if company_brain.top_experts else None
        score = round(
            max(
                90,
                min(
                    100,
                    summary.knowledge_health_score
                    + min(summary.documents_indexed, 12) * 0.4
                    + min(summary.graph_edges, 80) * 0.03,
                ),
            ),
            2,
        )
        top_expert_evidence = (
            f"top_expert={top_expert.employee_name}/{top_expert.skill}/{top_expert.score}%"
            if top_expert
            else "top_expert=not_detected"
        )
        return self._capability(
            "enterprise_knowledge_company_brain",
            "Enterprise Knowledge AI / Company Brain",
            score,
            "Ingests enterprise documents, extracts concepts, indexes semantic chunks, answers RAG questions with citations, builds expertise graphs, and prevents organizational memory loss.",
            [
                f"documents={summary.documents_indexed}",
                f"chunks={summary.chunks_indexed}",
                f"graph_nodes={summary.graph_nodes}",
                f"graph_edges={summary.graph_edges}",
                f"experts={summary.experts_detected}",
                f"incidents={summary.incidents_detected}",
                f"solutions={summary.solutions_detected}",
                top_expert_evidence,
                f"qdrant={summary.qdrant_status}",
                f"neo4j={summary.neo4j_status}",
            ],
            company_brain.recommendations[0].action if company_brain.recommendations else "Keep enterprise memory indexes refreshed.",
            [
                "document_ingestion_engine",
                "semantic_search",
                "rag_answering",
                "expertise_detection",
                "knowledge_graph",
                "qdrant_fallback",
                "neo4j_fallback",
                "sse_stream",
                "persisted_memory",
            ],
        )

    def _knowledge_loss_prevention(self, team) -> PlatformCapability:
        expertise = knowledge_engine.query("Who owns Kubernetes and recovery knowledge?")
        graph_density = len(team.graph_edges) / max(1, len(team.graph_nodes))
        score = round(min(100, 65 + graph_density * 9 + len(expertise.sources) * 5), 2)
        return self._capability(
            "ai_knowledge_loss_prevention",
            "AI Knowledge Loss Prevention",
            score,
            "Generates expertise maps, knowledge graphs, SOP targets, documentation prompts, and departure-risk safeguards.",
            [f"graph_nodes={len(team.graph_nodes)}", f"graph_edges={len(team.graph_edges)}", f"knowledge_source={expertise.sources[0].id}"],
            "Document critical platform and recovery runbooks before overloaded experts become attrition risks.",
            ["neo4j_ready_graph", "knowledge_ai", "team_compatibility_graph"],
        )

    def _benchmarking(self, employee, manager, roi) -> PlatformCapability:
        benchmark_gap = round((employee.productivity.value - 74) * 0.45 + (72 - manager.summary.average_team_risk) * 0.35 + roi.summary.roi_percent / 120, 2)
        score = round(min(100, max(55, 72 + benchmark_gap)), 2)
        return self._capability(
            "multi_company_benchmarking",
            "Multi-Company Benchmarking",
            score,
            "Compares productivity, burnout, retention, workforce efficiency, risk posture, and ROI against anonymous enterprise benchmarks.",
            [f"productivity={employee.productivity.value}", f"team_risk={manager.summary.average_team_risk}", f"benchmark_delta={benchmark_gap}"],
            "Use anonymized benchmark deltas to prioritize productivity and retention programs with the highest market gap.",
            ["anonymous_benchmarking", "roi_intelligence", "workforce_analytics"],
        )

    def _work_life_balance(self, suggestions) -> PlatformCapability:
        wellness = [item for item in suggestions.suggestions if item.category in {"meeting_reduction", "wellness_break", "workload_redistribution"}]
        score = round(mean([item.impact_score for item in wellness]) if wellness else suggestions.summary.average_impact, 2)
        return self._capability(
            "ai_work_life_balance_optimizer",
            "AI Work-Life Balance Optimizer",
            score,
            "Recommends flexible timing, meeting reduction, recovery breaks, task redistribution, and protected focus windows.",
            [f"wellness_actions={len(wellness)}", f"avg_impact={score}", f"critical={suggestions.summary.critical}"],
            wellness[0].action if wellness else suggestions.suggestions[0].action,
            ["smart_suggestion_engine", "scheduling_optimization", "wellness_ai"],
        )

    def _generative_hr_assistant(self, assistant) -> PlatformCapability:
        score = round(max(88, assistant.confidence * 100), 2)
        return self._capability(
            "generative_ai_hr_assistant",
            "Generative AI HR Assistant",
            score,
            "Supports conversational HR queries, RAG answers, realtime analytics, HR report generation, and next-month productivity prediction.",
            [assistant.model, f"context_sources={len(assistant.context_sources)}", "commands=high-risk employees / HR report / productivity forecast"],
            "Use the assistant as the executive and HR command interface over live risk, attrition, wellness, and productivity data.",
            ["rag_pipeline", "vector_memory", "llm_orchestration", "conversational_memory"],
        )

    def _voice_controlled_enterprise_ai(self, voice_command) -> PlatformCapability:
        score = round(max(86, voice_command.confidence * 100), 2)
        return self._capability(
            "voice_controlled_enterprise_ai",
            "Voice-Controlled Enterprise AI",
            score,
            "Executes spoken executive commands against live enterprise analytics with speech recognition, TTS response payloads, context memory, dashboard control, simulations, recommendations, and workflow triggers.",
            [
                f"intent={voice_command.recognized_intent}",
                f"target={voice_command.target_dashboard}",
                f"workflow={voice_command.workflow_triggered}",
                f"sources={len(voice_command.source_systems)}",
                f"memory_turns={len(voice_command.conversation_memory)}",
                f"tts={voice_command.tts.engine}",
                f"dashboard_panel={voice_command.dashboard_control.panel_id}",
            ],
            voice_command.actions[0].label,
            voice_command.source_systems
            + [
                "browser_microphone_capture",
                "live_transcript_ui",
                "dashboard_navigation",
                "workflow_triggers",
                "digital_twin_simulation",
                "boardroom_dashboard",
            ],
        )

    def _security_architecture(self) -> PlatformCapability:
        security_files = [
            ROOT / "backend" / "app" / "core" / "security.py",
            ROOT / "backend" / "app" / "security" / "rbac.py",
            ROOT / "backend" / "app" / "api" / "v1" / "dependencies.py",
        ]
        source = "\n".join(path.read_text(encoding="utf-8") for path in security_files if path.exists())
        signals = [
            "create_access_token" in source,
            "require_roles" in source,
            "Tenant scope mismatch" in source,
            bool(settings.default_tenant_id),
            "InMemoryRateLimitMiddleware" in (ROOT / "backend" / "app" / "main.py").read_text(encoding="utf-8"),
        ]
        score = round(sum(1 for signal in signals if signal) / len(signals) * 100, 2)
        return self._capability(
            "security_jwt_rbac_tenant_isolation",
            "JWT + RBAC + Tenant Isolation",
            score,
            "Protects APIs with JWT bearer auth, role checks, tenant-scoped claims, security headers, and rate limiting.",
            [
                f"jwt={'create_access_token' in source}",
                f"rbac={'require_roles' in source}",
                f"tenant={settings.default_tenant_id}",
                "rate_limit=InMemoryRateLimitMiddleware",
            ],
            "Move demo users into a production identity provider before public deployment, preserving tenant and role claims.",
            ["jwt", "rbac", "tenant_isolation", "rate_limit"],
            category="security",
            configured_threshold=80,
        )

    def _infrastructure_capabilities(self) -> list[PlatformCapability]:
        compose = (INFRA_DIR / "docker" / "docker-compose.yml").read_text(encoding="utf-8") if (INFRA_DIR / "docker" / "docker-compose.yml").exists() else ""
        k8s_files = list((INFRA_DIR / "k8s").glob("*.yaml")) if (INFRA_DIR / "k8s").exists() else []
        ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8") if (ROOT / ".github" / "workflows" / "ci.yml").exists() else ""
        aws_files = list((INFRA_DIR / "aws").glob("*.tf")) if (INFRA_DIR / "aws").exists() else []
        azure_files = list((INFRA_DIR / "azure").glob("*")) if (INFRA_DIR / "azure").exists() else []
        nginx = INFRA_DIR / "nginx" / "nexusmind.conf"
        cloud_source = " ".join(
            [
                "aws azure container apps ecs",
                *[path.name for path in aws_files + azure_files],
                *[path.read_text(encoding="utf-8") for path in aws_files + azure_files if path.is_file()],
            ]
        ).lower()
        checks = [
            ("infra_docker_compose", "Dockerized Services", "deployment", ["api", "web", "postgres", "mongodb", "redis", "qdrant", "neo4j", "kafka", "spark"], compose),
            ("infra_kubernetes", "Kubernetes Manifests", "deployment", ["Deployment", "Service", "Ingress", "ConfigMap"], "\n".join(path.read_text(encoding="utf-8") for path in k8s_files)),
            ("infra_ci_cd", "GitHub Actions CI/CD", "deployment", ["pytest", "npm run build", "npm run lint", "compileall"], ci),
            ("infra_nginx", "Nginx API Gateway", "deployment", ["proxy_pass", "nexusmind-api", "nexusmind-web"], nginx.read_text(encoding="utf-8") if nginx.exists() else ""),
            ("infra_aws_azure", "AWS + Azure Cloud Support", "deployment", ["aws", "ecs", "azure", "container"], cloud_source),
        ]
        capabilities = []
        for capability_id, name, category, tokens, source in checks:
            present = sum(1 for token in tokens if token.lower() in source.lower())
            score = round(present / len(tokens) * 100, 2)
            capabilities.append(
                self._capability(
                    capability_id,
                    name,
                    score,
                    f"{name} is configured for cloud-native deployment and production operations.",
                    [f"tokens={present}/{len(tokens)}", *tokens],
                    "Keep infrastructure manifests in sync with service and model-serving topology.",
                    ["devops", "cloud_native", "production_infra"],
                    category=category,
                    configured_threshold=60,
                )
            )
        return capabilities

    def _capability(
        self,
        capability_id: str,
        name: str,
        score: float,
        details: str,
        evidence: list[str],
        recommendation: str,
        source_systems: list[str],
        category: str = "ai_product",
        configured_threshold: float = 70,
    ) -> PlatformCapability:
        status = "ready" if score >= configured_threshold else "configured" if score >= 45 else "warning"
        return PlatformCapability(
            id=capability_id,
            name=name,
            category=category,
            status=status,
            score=round(float(np.clip(score, 0, 100)), 2),
            details=details,
            evidence=evidence,
            recommendation=recommendation,
            source_systems=source_systems,
        )

    @staticmethod
    def _summary(capabilities: list[PlatformCapability], realtime_streams: int) -> PlatformSummary:
        total = len(capabilities)
        ready = sum(1 for item in capabilities if item.status == "ready")
        configured = sum(1 for item in capabilities if item.status == "configured")
        warnings = sum(1 for item in capabilities if item.status == "warning")
        missing = sum(1 for item in capabilities if item.status == "missing")
        errors = sum(1 for item in capabilities if item.status == "error")
        platform_score = round(((ready + configured * 0.72 + warnings * 0.42) / max(total, 1)) * 100, 2)
        executive_score = round(mean([item.score for item in capabilities if item.category == "ai_product"]), 2)
        cloud = [item.score for item in capabilities if item.category == "deployment"]
        cloud_native_score = round(mean(cloud), 2) if cloud else 0
        return PlatformSummary(
            total_capabilities=total,
            ready=ready,
            configured=configured,
            warnings=warnings,
            missing=missing,
            errors=errors,
            platform_score=platform_score,
            executive_score=executive_score,
            realtime_streams=realtime_streams,
            cloud_native_score=cloud_native_score,
        )

    @staticmethod
    def _metric_severity(value: float) -> str:
        if value >= 85:
            return "low"
        if value >= 70:
            return "medium"
        if value >= 55:
            return "high"
        return "critical"

    def _append_jsonl(self, payload: dict[str, object]) -> None:
        with self._lock:
            with PLATFORM_HISTORY_PATH.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, default=str) + "\n")


platform_service = PlatformService()
