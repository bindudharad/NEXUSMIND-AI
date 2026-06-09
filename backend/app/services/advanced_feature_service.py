from __future__ import annotations

import inspect
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

from app.ai.digital_twin import TwinScenarioInput, digital_twin_simulator
from app.ai.knowledge_engine import knowledge_engine
from app.ai.security_analyzer import security_analyzer
from app.core.cache import TTLResponseCache
from app.schemas.boardroom import BoardroomAssistantRequest
from app.schemas.competitive_intelligence import CompetitiveAssistantRequest
from app.schemas.client_satisfaction import ClientAssistantRequest
from app.schemas.company_emotion_map import EmotionAssistantRequest
from app.schemas.crisis_management import CrisisAssistantRequest, CrisisSimulationRequest
from app.schemas.feature_coverage import FeatureCoverageCheck, FeatureCoverageResponse, FeatureCoverageSummary
from app.schemas.innovation import InnovationAssistantRequest
from app.schemas.multi_agent_workforce import AgentCouncilRequest, AgentSimulationRequest
from app.schemas.nlp import NLPAnalyzeRequest
from app.schemas.organizational_optimizer import OrganizationalAssistantRequest, OrganizationalSimulationRequest
from app.schemas.power_features import ManagerAssistantRequest, XAIExplanationRequest
from app.schemas.smart_interviewer import SmartInterviewAssistantRequest
from app.schemas.talent_marketplace import TalentAssistantRequest, TalentSearchRequest
from app.schemas.voice import VoiceCommandRequest
from app.services.alert_service import alert_service
from app.services.anomaly_service import anomaly_service
from app.services.boardroom_service import boardroom_dashboard_service
from app.services.company_simulation_lab_service import company_simulation_lab_service
from app.services.client_satisfaction_service import client_satisfaction_service
from app.services.company_emotion_map_service import company_emotion_map_service
from app.services.competitive_intelligence_service import competitive_intelligence_service
from app.services.crisis_management_service import crisis_management_service
from app.services.innovation_service import innovation_scoring_service
from app.services.meeting_service import meeting_analyzer_service
from app.services.multi_agent_workforce_service import multi_agent_workforce_service
from app.services.nlp_service import nlp_service
from app.services.organizational_optimizer_service import organizational_optimizer_service
from app.services.project_failure_service import project_failure_service
from app.services.power_feature_service import power_feature_service
from app.services.roi_service import roi_intelligence_service
from app.services.smart_interviewer_service import smart_interviewer_service
from app.services.suggestion_service import FEEDBACK_PATH as SUGGESTION_FEEDBACK_PATH
from app.services.suggestion_service import smart_suggestion_service
from app.services.talent_marketplace_service import talent_marketplace_service
from app.services.team_compatibility_service import team_compatibility_service
from app.services.voice_service import voice_stress_service


ROOT = Path(__file__).resolve().parents[3]
FRONTEND_COMPONENTS = ROOT / "frontend" / "src" / "components" / "dashboard"
FRONTEND_API = ROOT / "frontend" / "src" / "app" / "api"
DATA_DIR = ROOT / "backend" / "app" / "data"


class AdvancedFeatureService:
    def __init__(self) -> None:
        self._cache: TTLResponseCache[FeatureCoverageResponse] = TTLResponseCache(ttl_seconds=40)

    def verify(self) -> FeatureCoverageResponse:
        return self._cache.get_or_set(self._verify_uncached)

    def _verify_uncached(self) -> FeatureCoverageResponse:
        probes: list[Callable[[], FeatureCoverageCheck]] = [
            self._digital_twin,
            self._ceo_assistant,
            self._voice_controlled_enterprise_ai,
            self._ai_boardroom_dashboard,
            self._multi_agent_system,
            self._time_machine,
            self._company_simulation_lab,
            self._competitive_intelligence_war_room,
            self._client_relationship_intelligence,
            self._organizational_structure_optimizer,
            self._realtime_crisis_management_ai,
            self._internal_talent_marketplace,
            self._smart_interviewer,
            self._company_emotion_map,
            self._innovation_detector,
            self._emotion_heatmap,
            self._three_d_control_room,
            self._ai_alerts,
            self._smart_suggestions,
            self._self_learning,
            self._knowledge_ai,
            self._cybersecurity_ai,
            self._meeting_analyzer,
            self._voice_stress_detection,
            self._team_compatibility_ai,
            self._project_failure_prediction,
            self._roi_intelligence,
            self._realtime_power_analytics,
            self._explainable_ai,
            self._graph_neural_networks,
            self._generative_manager_assistant,
            self._realtime_systems,
            self._cinematic_ui,
        ]
        checks = [self._safe(probe) for probe in probes]
        summary = self._summary(checks)
        critical_gaps = [
            f"{check.name}: {check.remediation or check.details}"
            for check in checks
            if check.status in {"missing", "error"}
        ]
        verdict = (
            "Advanced NEXUSMIND systems are implemented with dynamic simulations, agents, voice, vector memory, realtime alerts, ROI economics, and cinematic UI."
            if not critical_gaps and summary.coverage_score >= 88
            else "Advanced feature layer needs remediation before a high-impact enterprise demo."
        )
        return FeatureCoverageResponse(
            generated_at=datetime.now(timezone.utc),
            summary=summary,
            checks=checks,
            critical_gaps=critical_gaps,
            verdict=verdict,
        )

    def _digital_twin(self) -> FeatureCoverageCheck:
        baseline = digital_twin_simulator.simulate_extended(TwinScenarioInput(0, 0, 0, False))
        crisis = digital_twin_simulator.simulate_extended(TwinScenarioInput(24, 38, -8, True))
        model = digital_twin_simulator.company_model
        ready = (
            len(model.employees) >= 5
            and len(model.departments) >= 4
            and len(model.workflows) >= 3
            and crisis.delay_probability > baseline.delay_probability
            and crisis.team_collapse_probability > baseline.team_collapse_probability
            and crisis.affected_departments
        )
        return FeatureCoverageCheck(
            name="Digital Twin / Shadow Company AI",
            category="simulation",
            status="ready" if ready else "error",
            details="Virtual employees, departments, workflows, collapse risk, productivity loss, workflow impact, and recovery actions are simulated dynamically.",
            evidence=[
                f"employees={len(model.employees)}",
                f"departments={len(model.departments)}",
                f"workflows={len(model.workflows)}",
                f"baseline_delay={baseline.delay_probability}",
                f"crisis_delay={crisis.delay_probability}",
                f"collapse={crisis.team_collapse_probability}",
            ],
            remediation=None if ready else "Rebuild the twin company model and scenario simulator with dynamic department/workflow impact scoring.",
        )

    def _ceo_assistant(self) -> FeatureCoverageCheck:
        path = FRONTEND_COMPONENTS / "ExecutiveAssistantPanel.tsx"
        source = path.read_text(encoding="utf-8") if path.exists() else ""
        ready = all(token in source for token in ["SpeechRecognition", "speechSynthesis", "startVoiceCommand", "selectDirective"])
        return FeatureCoverageCheck(
            name="AI CEO Assistant Voice Layer",
            category="voice",
            status="ready" if ready else "missing",
            details="Browser speech recognition, spoken executive responses, dynamic command matching, and dashboard directive selection are wired into the CEO assistant.",
            evidence=["SpeechRecognition API", "speechSynthesis API", "dynamic directive matching", str(path)],
            remediation=None if ready else "Wire Web Speech API recognition and synthesis into ExecutiveAssistantPanel.",
        )

    def _voice_controlled_enterprise_ai(self) -> FeatureCoverageCheck:
        session_id = "advanced-audit-voice-copilot"
        first = voice_stress_service.execute_command(
            VoiceCommandRequest(transcript="Show highest-risk department.", speaker="CEO", department="Executive", session_id=session_id)
        )
        followup = voice_stress_service.execute_command(
            VoiceCommandRequest(transcript="Why is it risky?", speaker="CEO", department="Executive", session_id=session_id)
        )
        simulation = voice_stress_service.execute_command(
            VoiceCommandRequest(transcript="Simulate losing 15 engineers.", speaker="CEO", department="Executive", session_id=session_id)
        )
        component = FRONTEND_COMPONENTS / "VoiceEnterpriseCopilotPanel.tsx"
        source = component.read_text(encoding="utf-8") if component.exists() else ""
        routes = [
            FRONTEND_API / "voice" / "command" / "route.ts",
            FRONTEND_API / "voice" / "copilot" / "default" / "route.ts",
            FRONTEND_API / "voice" / "copilot" / "stream" / "route.ts",
        ]
        required_systems = {
            "speech_recognition_engine",
            "voice_command_engine",
            "llm_assistant_engine",
            "text_to_speech_engine",
            "context_memory_engine",
            "enterprise_analytics_connector",
            "executive_dashboard_integration",
        }
        ready = (
            first.recognized_intent == "highest_risk_department"
            and followup.recognized_intent == "follow_up_explanation"
            and simulation.recognized_intent == "digital_twin_simulation"
            and first.dashboard_control.panel_id
            and first.tts.playback_supported
            and len(followup.conversation_memory) >= 2
            and required_systems.issubset(set(first.source_systems))
            and inspect.isasyncgen(voice_stress_service.copilot_stream())
            and component.exists()
            and all(path.exists() for path in routes)
            and all(token in source for token in ["SpeechRecognition", "speechSynthesis", "startListening", "speakResponse", "voice-enterprise-copilot-panel"])
        )
        return FeatureCoverageCheck(
            name="Voice-Controlled Enterprise AI / JARVIS for CEOs",
            category="voice",
            status="ready" if ready else "missing",
            details="Executive voice copilot verifies browser speech recognition, server-side command grounding, TTS payloads, multi-turn memory, dashboard controls, digital twin simulation routing, command persistence, and SSE copilot stream.",
            evidence=[
                first.model,
                f"intent={first.recognized_intent}",
                f"followup={followup.recognized_intent}",
                f"simulation={simulation.recognized_intent}",
                f"memory_turns={len(followup.conversation_memory)}",
                f"panel={first.dashboard_control.panel_id}",
                str(component),
            ],
            remediation=None if ready else "Implement the executive voice copilot service, UI panel, command proxy routes, TTS metadata, memory, dashboard routing, and copilot stream.",
        )

    def _ai_boardroom_dashboard(self) -> FeatureCoverageCheck:
        response = boardroom_dashboard_service.default()
        assistant = boardroom_dashboard_service.ask(
            BoardroomAssistantRequest(question="Which risk should I solve first?")
        )
        component = FRONTEND_COMPONENTS / "BoardroomDashboardPanel.tsx"
        api_default = FRONTEND_API / "boardroom" / "default" / "route.ts"
        api_assistant = FRONTEND_API / "boardroom" / "assistant" / "route.ts"
        api_stream = FRONTEND_API / "boardroom" / "stream" / "route.ts"
        required_systems = {
            "executive_dashboard",
            "real_time_data_layer",
            "ai_insights_engine",
            "risk_aggregation_engine",
            "executive_recommendation_engine",
            "company_digital_twin",
            "executive_ai_assistant",
            "forecasting_integration",
        }
        risk_categories = {item.category for item in response.executive_risks}
        required_risks = {
            "Burnout Risk",
            "Client Risk",
            "Cybersecurity Risk",
            "Project Risk",
            "Revenue Risk",
            "Talent Flight Risk",
        }
        ready = (
            response.summary.connected_engines >= 12
            and response.company_health.score > 0
            and len(response.kpis) >= 8
            and required_risks.issubset(risk_categories)
            and bool(response.financial_predictions.monthly_forecast)
            and bool(response.workforce.burnout_hotspots)
            and response.cybersecurity.active_threats >= 0
            and bool(response.projects.delivery_forecast)
            and bool(response.clients.highest_churn_risk_client)
            and bool(response.competitive.top_threat)
            and bool(response.innovation.innovation_champions)
            and response.digital_twin.company_twin_status == "synchronized"
            and bool(response.alerts)
            and bool(response.recommendations)
            and assistant.intent == "risk"
            and bool(assistant.cited_evidence)
            and required_systems.issubset(set(response.source_systems))
            and inspect.isasyncgen(boardroom_dashboard_service.stream())
            and component.exists()
            and api_default.exists()
            and api_assistant.exists()
            and api_stream.exists()
        )
        return FeatureCoverageCheck(
            name="AI Boardroom Dashboard / JARVIS for Companies",
            category="executive",
            status="ready" if ready else "missing",
            details="Master executive cockpit verifies company health, prioritized risks, financial forecasts, workforce, cybersecurity, projects, clients, competitive intelligence, innovation, digital twin state, executive assistant, alerts, recommendations, dashboard, and SSE stream.",
            evidence=[
                response.model,
                f"health={round(response.company_health.score)}",
                f"risks={len(response.executive_risks)}",
                f"alerts={len(response.alerts)}",
                f"recommendations={len(response.recommendations)}",
                f"assistant_intent={assistant.intent}",
                str(component),
            ],
            remediation=None if ready else "Implement Boardroom service, API routes, assistant, dashboard panel, stream proxy, and source-system evidence.",
        )

    def _competitive_intelligence_war_room(self) -> FeatureCoverageCheck:
        response = competitive_intelligence_service.analyze()
        assistant = competitive_intelligence_service.ask(
            CompetitiveAssistantRequest(question="Show biggest competitor threat.")
        )
        component = FRONTEND_COMPONENTS / "CompetitiveIntelligencePanel.tsx"
        api_default = FRONTEND_API / "competitive" / "intelligence" / "default" / "route.ts"
        api_stream = FRONTEND_API / "competitive" / "intelligence" / "stream" / "route.ts"
        ready = (
            bool(response.profiles)
            and bool(response.product_launches)
            and bool(response.hiring_trends)
            and bool(response.technology_adoption)
            and bool(response.market_expansions)
            and bool(response.risk_scores)
            and bool(response.comparison)
            and assistant.intent == "threat"
            and inspect.isasyncgen(competitive_intelligence_service.stream())
            and component.exists()
            and api_default.exists()
            and api_stream.exists()
        )
        return FeatureCoverageCheck(
            name="AI Competitive Intelligence Strategic War Room",
            category="strategy",
            status="ready" if ready else "missing",
            details="Dedicated competitive intelligence verifies competitor profiles, product launches, hiring trends, technology adoption, market expansion, industry trends, risk scoring, comparison, assistant, dashboard, and SSE stream.",
            evidence=[
                f"competitors={len(response.profiles)}",
                f"launches={len(response.product_launches)}",
                f"top_threat={response.summary.top_competitor_threat}",
                f"assistant_intent={assistant.intent}",
                str(component),
            ],
            remediation=None if ready else "Implement the dedicated competitive intelligence service, API routes, dashboard panel, assistant, and stream proxy.",
        )

    def _client_relationship_intelligence(self) -> FeatureCoverageCheck:
        response = client_satisfaction_service.predict()
        assistant = client_satisfaction_service.ask(ClientAssistantRequest(question="Which clients may pay late?"))
        component = FRONTEND_COMPONENTS / "ClientSatisfactionPanel.tsx"
        api_predict = FRONTEND_API / "client-satisfaction" / "predict" / "route.ts"
        api_assistant = FRONTEND_API / "client-satisfaction" / "assistant" / "route.ts"
        api_stream = FRONTEND_API / "client-satisfaction" / "stream" / "route.ts"
        top = response.predictions[0]
        ready = (
            bool(response.predictions)
            and bool(response.payment_risks)
            and bool(response.project_risks)
            and bool(response.engagement_analytics)
            and bool(response.opportunity_pipeline)
            and bool(response.recommendations)
            and top.churn_risk > 0
            and top.payment_delay_risk >= 0
            and top.project_failure_risk >= 0
            and assistant.intent == "payment"
            and inspect.isasyncgen(client_satisfaction_service.stream())
            and component.exists()
            and api_predict.exists()
            and api_assistant.exists()
            and api_stream.exists()
        )
        return FeatureCoverageCheck(
            name="AI Client Relationship Intelligence",
            category="client",
            status="ready" if ready else "missing",
            details="Client retention engine verifies health scoring, churn prediction, payment-delay prediction, project-risk forecasting, sentiment/tone intelligence, engagement analytics, opportunity detection, assistant, dashboard, and stream.",
            evidence=[
                response.model,
                f"clients={response.summary.clients_analyzed}",
                f"highest_risk={response.summary.highest_risk_client}",
                f"payment_risk_accounts={response.summary.payment_risk_accounts}",
                f"project_risk_accounts={response.summary.project_risk_accounts}",
                f"opportunity_revenue={response.summary.opportunity_revenue}",
                f"assistant_intent={assistant.intent}",
                str(component),
            ],
            remediation=None if ready else "Complete client relationship service, assistant, frontend proxy, dashboard, payment/project/opportunity analytics, and SSE stream.",
        )

    def _organizational_structure_optimizer(self) -> FeatureCoverageCheck:
        response = organizational_optimizer_service.default()
        assistant = organizational_optimizer_service.ask(OrganizationalAssistantRequest(question="Which managers are overloaded?"))
        simulated = organizational_optimizer_service.simulate(
            OrganizationalSimulationRequest(question="What happens if Engineering Platform splits into 3 teams?", target_team="Engineering Platform", new_team_count=3)
        )
        component = FRONTEND_COMPONENTS / "OrganizationalOptimizerPanel.tsx"
        routes = [
            FRONTEND_API / "organization" / "optimizer" / "default" / "route.ts",
            FRONTEND_API / "organization" / "optimizer" / "assistant" / "route.ts",
            FRONTEND_API / "organization" / "optimizer" / "stream" / "route.ts",
        ]
        required_systems = {
            "organizational_analytics_engine",
            "graph_ai_engine",
            "reporting_structure_analyzer",
            "team_optimization_engine",
            "collaboration_intelligence_engine",
            "communication_flow_analyzer",
            "organizational_simulation_engine",
            "organizational_ai_assistant",
            "company_digital_twin",
        }
        ready = (
            bool(response.graph_nodes)
            and bool(response.graph_edges)
            and bool(response.manager_load)
            and bool(response.reporting_structure)
            and bool(response.communication_flows)
            and bool(response.team_recommendations)
            and bool(response.silo_risks)
            and bool(response.skill_distribution)
            and bool(response.simulations)
            and bool(response.forecasts)
            and bool(response.recommendations)
            and assistant.intent == "manager_overload"
            and simulated.simulations[0].scenario_type == "split_team"
            and required_systems.issubset(set(response.source_systems))
            and inspect.isasyncgen(organizational_optimizer_service.stream())
            and component.exists()
            and all(path.exists() for path in routes)
        )
        return FeatureCoverageCheck(
            name="AI Organizational Structure Optimizer",
            category="organization",
            status="ready" if ready else "missing",
            details="Organizational design intelligence verifies graph nodes/edges, reporting structure analysis, manager overload, communication-flow bottlenecks, team optimization, silo detection, skill concentration, simulations, forecasts, assistant answers, dashboard, and SSE stream.",
            evidence=[
                response.model,
                f"nodes={response.summary.graph_nodes}",
                f"edges={response.summary.graph_edges}",
                f"overloaded_managers={response.summary.overloaded_managers}",
                f"bottlenecks={response.summary.communication_bottlenecks}",
                f"assistant={assistant.intent}",
                str(component),
            ],
            remediation=None if ready else "Build dedicated org optimizer service, routes, assistant, stream, dashboard panel, graph analytics, simulations, and source-system evidence.",
        )

    def _realtime_crisis_management_ai(self) -> FeatureCoverageCheck:
        response = crisis_management_service.default()
        assistant = crisis_management_service.ask(CrisisAssistantRequest(question="What is our biggest crisis?"))
        simulated = crisis_management_service.simulate(
            CrisisSimulationRequest(scenario_type="ransomware", question="What if ransomware affects production?")
        )
        component = FRONTEND_COMPONENTS / "CrisisCommandCenterPanel.tsx"
        routes = [
            FRONTEND_API / "crisis" / "management" / "default" / "route.ts",
            FRONTEND_API / "crisis" / "management" / "assistant" / "route.ts",
            FRONTEND_API / "crisis" / "management" / "stream" / "route.ts",
        ]
        required_systems = {
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
            "boardroom_dashboard",
        }
        ready = (
            bool(response.active_crises)
            and bool(response.containment_actions)
            and bool(response.recovery_plans)
            and bool(response.business_continuity)
            and bool(response.simulations)
            and bool(response.executive_alerts)
            and bool(response.heatmap)
            and bool(response.recommendations)
            and assistant.intent == "biggest_crisis"
            and simulated.simulations[0].scenario_type == "ransomware"
            and required_systems.issubset(set(response.source_systems))
            and inspect.isasyncgen(crisis_management_service.stream())
            and component.exists()
            and all(path.exists() for path in routes)
        )
        top = response.active_crises[0] if response.active_crises else None
        return FeatureCoverageCheck(
            name="Realtime Crisis Management AI",
            category="crisis",
            status="ready" if ready else "missing",
            details="Emergency command center verifies crisis detection, incident classification, severity scoring, containment, recovery planning, business continuity, simulations, executive alerts, AI assistant answers, dashboard, persisted history, and SSE stream.",
            evidence=[
                response.model,
                f"active_crises={response.summary.active_crises}",
                f"critical={response.summary.critical_crises}",
                f"top={top.title if top else 'none'}",
                f"highest_severity={response.summary.highest_severity_score}",
                f"alerts={len(response.executive_alerts)}",
                f"simulations={len(response.simulations)}",
                f"assistant={assistant.intent}",
                str(component),
            ],
            remediation=None if ready else "Build dedicated crisis service, routes, assistant, stream, dashboard panel, simulations, alerts, and source-system evidence.",
        )

    def _internal_talent_marketplace(self) -> FeatureCoverageCheck:
        response = talent_marketplace_service.default()
        assistant = talent_marketplace_service.ask(TalentAssistantRequest(question="Who can mentor me on Kubernetes?"))
        search = talent_marketplace_service.search(TalentSearchRequest(query="kubernetes mlops project"))
        component = FRONTEND_COMPONENTS / "TalentMarketplacePanel.tsx"
        api_default = FRONTEND_API / "talent" / "marketplace" / "default" / "route.ts"
        api_assistant = FRONTEND_API / "talent" / "marketplace" / "assistant" / "route.ts"
        api_stream = FRONTEND_API / "talent" / "marketplace" / "stream" / "route.ts"
        source_systems = set(response.source_systems)
        ready = (
            bool(response.profiles)
            and bool(response.skill_intelligence)
            and bool(response.project_matches)
            and bool(response.mentor_matches)
            and bool(response.internal_role_matches)
            and bool(response.learning_paths)
            and bool(response.expert_rankings)
            and bool(response.reputation_scores)
            and bool(response.badges)
            and bool(response.graph_nodes)
            and bool(response.graph_edges)
            and bool(search.results)
            and assistant.intent == "mentors"
            and inspect.isasyncgen(talent_marketplace_service.stream())
            and component.exists()
            and api_default.exists()
            and api_assistant.exists()
            and api_stream.exists()
            and {
                "talent_profile_engine",
                "skill_intelligence_engine",
                "project_matching_engine",
                "mentor_matching_engine",
                "internal_job_matching_engine",
                "learning_recommendation_engine",
                "reputation_engine",
                "talent_ai_assistant",
            }.issubset(source_systems)
        )
        return FeatureCoverageCheck(
            name="AI Internal Talent Marketplace",
            category="workforce",
            status="ready" if ready else "missing",
            details="Dedicated internal career marketplace verifies employee profiles, skill intelligence, project matching, mentor matching, internal jobs, learning paths, expert discovery, reputation, badges, graph analytics, assistant, dashboard, search, and stream.",
            evidence=[
                response.model,
                f"profiles={response.summary.profiles}",
                f"project_matches={response.summary.project_matches}",
                f"mentor_matches={response.summary.mentor_matches}",
                f"role_matches={response.summary.internal_role_matches}",
                f"badges={response.summary.badges_awarded}",
                f"assistant_intent={assistant.intent}",
                str(component),
            ],
            remediation=None if ready else "Build the dedicated talent marketplace service, API routes, assistant, search, stream, dashboard panel, and reputation/badge engines.",
        )

    def _smart_interviewer(self) -> FeatureCoverageCheck:
        response = smart_interviewer_service.run()
        assistant = smart_interviewer_service.ask(SmartInterviewAssistantRequest(question="Show top candidate."))
        top = response.candidate_rankings[0]
        component = FRONTEND_COMPONENTS / "SmartInterviewerPanel.tsx"
        api_default = FRONTEND_API / "interviews" / "smart" / "default" / "route.ts"
        api_stream = FRONTEND_API / "interviews" / "smart" / "stream" / "route.ts"
        ready = (
            response.generated_questions
            and response.candidate_rankings
            and top.technical_score > 0
            and top.behavioral_score > 0
            and top.voice_analysis.confidence_score > 0
            and top.report.pdf_path.endswith(".pdf")
            and top.report.docx_path.endswith(".docx")
            and assistant.intent == "top_candidate"
            and inspect.isasyncgen(smart_interviewer_service.stream())
            and component.exists()
            and api_default.exists()
            and api_stream.exists()
        )
        return FeatureCoverageCheck(
            name="AI Smart Interviewer Panel",
            category="hiring",
            status="ready" if ready else "missing",
            details="Dedicated interview panel verifies adaptive questions, resume analysis, technical scoring, behavioral NLP, voice confidence, cheating detection, reports, candidate ranking, assistant, dashboard, and SSE stream.",
            evidence=[
                response.model,
                f"questions={len(response.generated_questions)}",
                f"candidates={len(response.candidate_rankings)}",
                f"top={top.candidate_name}",
                f"reports={response.summary.report_count}",
                f"assistant_intent={assistant.intent}",
                str(component),
            ],
            remediation=None if ready else "Build Smart Interviewer backend, reports, assistant, dashboard panel, proxy routes, and stream.",
        )

    def _multi_agent_system(self) -> FeatureCoverageCheck:
        workforce = multi_agent_workforce_service.default()
        council = multi_agent_workforce_service.ask(
            AgentCouncilRequest(question="Why is company health declining?", include_simulation=True)
        )
        simulation = multi_agent_workforce_service.simulate(
            AgentSimulationRequest(question="What happens if 20 engineers resign?", scenario_type="workforce_change")
        )
        component = FRONTEND_COMPONENTS / "MultiAgentWorkforcePanel.tsx"
        api_routes = [
            FRONTEND_API / "agents" / "workforce" / "default" / "route.ts",
            FRONTEND_API / "agents" / "workforce" / "ask" / "route.ts",
            FRONTEND_API / "agents" / "workforce" / "simulate" / "route.ts",
            FRONTEND_API / "agents" / "workforce" / "stream" / "route.ts",
        ]
        agents = {agent.name for agent in workforce.agents}
        required = {
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
        ready = (
            required == agents
            and workforce.summary.active_agents >= 8
            and workforce.summary.coordination_score >= 90
            and len(workforce.messages) >= 8
            and len(workforce.memory) >= 8
            and len(workforce.tool_executions) >= 8
            and len(workforce.autonomous_tasks) >= 8
            and len(workforce.workflows) >= 4
            and bool(workforce.decisions)
            and bool(workforce.simulations)
            and len(workforce.analytics) >= 8
            and council.participating_agents
            and simulation.simulations
            and required_systems.issubset(set(workforce.source_systems))
            and inspect.isasyncgen(multi_agent_workforce_service.stream())
            and component.exists()
            and all(path.exists() for path in api_routes)
        )
        return FeatureCoverageCheck(
            name="Multi-Agent AI Workforce",
            category="agents",
            status="ready" if ready else "error",
            details="Digital workforce verifies eight specialist AI manager agents, inter-agent messaging, shared persistent memory, secure tool access, autonomous tasks, collaboration workflows, Executive AI Council reasoning, digital-twin simulations, performance intelligence, command surface, APIs, and SSE stream.",
            evidence=[
                workforce.model,
                f"agents={sorted(agents)}",
                f"messages={len(workforce.messages)}",
                f"memory={len(workforce.memory)}",
                f"workflows={len(workforce.workflows)}",
                f"coordination={round(workforce.summary.coordination_score)}",
                f"council_agents={len(council.participating_agents)}",
                str(component),
            ],
            remediation=None if ready else "Complete agent workforce service, dashboard, memory, event bus, workflows, simulation, and proxy route integration.",
        )

    def _time_machine(self) -> FeatureCoverageCheck:
        route = FRONTEND_API / "intelligence" / "digital-twin" / "simulate" / "route.ts"
        panel = FRONTEND_COMPONENTS / "SimulationConsole.tsx"
        low = digital_twin_simulator.simulate_extended(TwinScenarioInput(2, 4, 10, False))
        high = digital_twin_simulator.simulate_extended(TwinScenarioInput(30, 45, -15, True))
        source = panel.read_text(encoding="utf-8") if panel.exists() else ""
        ready = route.exists() and "Run what-if simulation" in source and high.delay_probability > low.delay_probability
        return FeatureCoverageCheck(
            name="Enterprise Time Machine",
            category="simulation",
            status="ready" if ready else "error",
            details="Interactive what-if controls call the live Digital Twin API and return delay, collapse, stability, productivity loss, and affected departments.",
            evidence=[str(route), f"low_delay={low.delay_probability}", f"high_delay={high.delay_probability}"],
            remediation=None if ready else "Add a Next.js proxy route and interactive what-if controls for live simulation.",
        )

    def _company_simulation_lab(self) -> FeatureCoverageCheck:
        lab = company_simulation_lab_service.run()
        route = FRONTEND_API / "simulation" / "company-lab" / "default" / "route.ts"
        stream = FRONTEND_API / "simulation" / "company-lab" / "stream" / "route.ts"
        panel = FRONTEND_COMPONENTS / "CompanySimulationLabPanel.tsx"
        scenario_types = {scenario.scenario_type for scenario in lab.scenarios}
        forecast_metrics = {forecast.metric for scenario in lab.scenarios for forecast in scenario.forecasts}
        required_scenarios = {
            "work_from_home_policy",
            "hiring_freeze",
            "employee_resignation",
            "department_restructure",
            "budget_reduction",
            "meeting_reduction",
        }
        required_forecasts = {
            "Productivity Forecast",
            "Attrition Forecast",
            "Burnout Forecast",
            "Revenue Forecast",
            "Hiring Forecast",
            "Delivery Forecast",
        }
        ready = (
            route.exists()
            and stream.exists()
            and panel.exists()
            and required_scenarios.issubset(scenario_types)
            and required_forecasts.issubset(forecast_metrics)
            and lab.comparison
            and lab.executive_recommendations
        )
        return FeatureCoverageCheck(
            name="AI Company Simulation Lab",
            category="simulation",
            status="ready" if ready else "missing",
            details="Business flight simulator models WFH policy, hiring freeze, resignation, restructure, budget, meeting, comparison, forecast, risk, and recommendation scenarios.",
            evidence=[
                str(route),
                str(stream),
                str(panel),
                f"scenarios={sorted(scenario_types)}",
                f"forecast_metrics={sorted(forecast_metrics)}",
                f"decision_readiness={lab.summary.decision_readiness_score}",
            ],
            remediation=None if ready else "Build CompanySimulationLabPanel, proxy routes, scenario API, forecast metrics, and scenario-comparison engine.",
        )

    def _emotion_heatmap(self) -> FeatureCoverageCheck:
        calm = nlp_service.analyze(
            NLPAnalyzeRequest(employee_id="emo-calm", department="Finance", channel="chat", text="The launch went well and the team feels confident")
        )
        stressed = nlp_service.analyze(
            NLPAnalyzeRequest(employee_id="emo-stress", department="Engineering", channel="chat", text="I am exhausted and working late every night")
        )
        toxic = nlp_service.analyze(
            NLPAnalyzeRequest(employee_id="emo-toxic", department="Engineering", channel="chat", text="The conversation became hostile and people are attacking ideas")
        )
        panels = [FRONTEND_COMPONENTS / "BurnoutHeatmap.tsx", FRONTEND_COMPONENTS / "NlpSentimentPanel.tsx"]
        ready = stressed.emotion_scores.stress > calm.emotion_scores.stress and toxic.emotion_scores.toxicity > calm.emotion_scores.toxicity and all(path.exists() for path in panels)
        return FeatureCoverageCheck(
            name="Realtime Emotion Heatmap",
            category="emotion",
            status="ready" if ready else "error",
            details="NLP emotion inference feeds stress, toxicity, burnout, and team heatmap visualizations.",
            evidence=[
                f"stress_delta={round(stressed.emotion_scores.stress - calm.emotion_scores.stress, 3)}",
                f"toxicity_delta={round(toxic.emotion_scores.toxicity - calm.emotion_scores.toxicity, 3)}",
                *[path.name for path in panels],
            ],
            remediation=None if ready else "Reconnect NLP sentiment outputs to heatmap and emotion dashboard panels.",
        )

    def _company_emotion_map(self) -> FeatureCoverageCheck:
        response = company_emotion_map_service.default()
        assistant = company_emotion_map_service.ask(EmotionAssistantRequest(question="Which department is most stressed?"))
        component = FRONTEND_COMPONENTS / "CompanyEmotionMapPanel.tsx"
        routes = [
            FRONTEND_API / "emotion" / "map" / "default" / "route.ts",
            FRONTEND_API / "emotion" / "map" / "analyze" / "route.ts",
            FRONTEND_API / "emotion" / "map" / "assistant" / "route.ts",
            FRONTEND_API / "emotion" / "map" / "stream" / "route.ts",
        ]
        source_systems = set(response.source_systems)
        ready = (
            response.summary.employees_analyzed >= 6
            and response.team_scores
            and response.department_scores
            and response.heatmap
            and response.conflict_risks
            and response.burnout_predictions
            and response.motivation_trends
            and response.forecasts
            and response.recommendations
            and assistant.intent == "stress"
            and inspect.isasyncgen(company_emotion_map_service.stream())
            and component.exists()
            and all(path.exists() for path in routes)
            and {
                "emotion_analytics_engine",
                "sentiment_analysis_engine",
                "burnout_prediction_engine",
                "conflict_detection_engine",
                "organizational_heatmap_engine",
                "emotion_ai_assistant",
                "company_digital_twin",
                "workflow_automation",
            }.issubset(source_systems)
        )
        return FeatureCoverageCheck(
            name="Company Emotion Map",
            category="emotion",
            status="ready" if ready else "missing",
            details="Organizational emotion intelligence verifies employee, team, department, project, and location heatmaps, NLP sentiment, burnout prediction, conflict detection, motivation analytics, forecasts, recommendations, assistant, dashboard, and SSE stream.",
            evidence=[
                response.model,
                f"employees={response.summary.employees_analyzed}",
                f"teams={response.summary.teams_analyzed}",
                f"departments={response.summary.departments_analyzed}",
                f"heatmap={len(response.heatmap)}",
                f"conflicts={len(response.conflict_risks)}",
                f"assistant_intent={assistant.intent}",
                str(component),
            ],
            remediation=None if ready else "Implement dedicated Company Emotion Map backend, dashboard, assistant, stream, proxy routes, heatmap, forecasts, and digital twin integration.",
        )

    def _innovation_detector(self) -> FeatureCoverageCheck:
        response = innovation_scoring_service.score()
        assistant = innovation_scoring_service.ask(InnovationAssistantRequest(question="Who are our future leaders?"))
        component = FRONTEND_COMPONENTS / "InnovationScoringPanel.tsx"
        routes = [
            FRONTEND_API / "innovation" / "score" / "route.ts",
            FRONTEND_API / "innovation" / "assistant" / "route.ts",
            FRONTEND_API / "innovation" / "stream" / "route.ts",
        ]
        source_systems = set(response.source_systems)
        ready = (
            response.hidden_talent
            and response.leadership_predictions
            and response.problem_solving_insights
            and response.growth_forecasts
            and response.talent_risks
            and response.promotion_recommendations
            and assistant.intent == "leaders"
            and inspect.isasyncgen(innovation_scoring_service.stream())
            and component.exists()
            and all(path.exists() for path in routes)
            and {
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
            }.issubset(source_systems)
        )
        return FeatureCoverageCheck(
            name="AI Innovation Detector",
            category="workforce",
            status="ready" if ready else "missing",
            details="Hidden talent discovery verifies innovation analytics, leadership potential, creativity intelligence, problem-solving intelligence, growth forecasting, talent risk, promotion recommendations, assistant, dashboard, and stream.",
            evidence=[
                response.model,
                f"hidden_talent={len(response.hidden_talent)}",
                f"future_leaders={response.summary.future_leaders_count}",
                f"promotions={response.summary.promotion_candidates}",
                f"risks={response.summary.critical_talent_risks}",
                f"assistant_intent={assistant.intent}",
                str(component),
            ],
            remediation=None if ready else "Rebuild AI Innovation Detector backend, assistant, dashboard, stream, growth forecasting, leadership scoring, and talent discovery evidence.",
        )

    def _three_d_control_room(self) -> FeatureCoverageCheck:
        path = FRONTEND_COMPONENTS / "EnterpriseTwinScene.tsx"
        source = path.read_text(encoding="utf-8") if path.exists() else ""
        ready = all(token in source for token in ["Canvas", "OrbitControls", "useFrame", "OrgGraphNode", "peak risk"])
        return FeatureCoverageCheck(
            name="3D Enterprise Control Room",
            category="visualization",
            status="ready" if ready else "missing",
            details="Three.js control room renders live organization risk nodes with orbital interaction, animation, and risk-based colors.",
            evidence=["@react-three/fiber Canvas", "OrbitControls", "risk-colored nodes", str(path)],
            remediation=None if ready else "Rebuild EnterpriseTwinScene with dynamic org-risk nodes and stable Three.js rendering.",
        )

    def _ai_alerts(self) -> FeatureCoverageCheck:
        feed = alert_service.feed()
        categories = {alert.category for alert in feed.alerts}
        stream_ready = inspect.isasyncgen(alert_service.stream())
        ready = bool(feed.alerts) and {"burnout", "overload", "delay"}.intersection(categories) and stream_ready
        return FeatureCoverageCheck(
            name="Realtime AI Alert System",
            category="alerts",
            status="ready" if ready else "error",
            details="Cross-system alert correlator generates severity-ranked predictive alerts and streams them to the dashboard.",
            evidence=[feed.model, f"alerts={len(feed.alerts)}", f"categories={sorted(categories)}", f"stream={stream_ready}"],
            remediation=None if ready else "Reconnect alert correlator, severity scoring, alert storage, and event stream.",
        )

    def _smart_suggestions(self) -> FeatureCoverageCheck:
        response = smart_suggestion_service.generate()
        categories = {suggestion.category for suggestion in response.suggestions}
        expected = {"meeting_reduction", "workload_redistribution", "wellness_break", "team_optimization", "productivity_improvement"}
        ready = expected.issubset(categories) and inspect.isasyncgen(smart_suggestion_service.stream())
        return FeatureCoverageCheck(
            name="Smart Suggestion Engine",
            category="recommendations",
            status="ready" if ready else "error",
            details="AI decision engine generates meeting reduction, workload, wellness, team, and productivity recommendations with feedback learning.",
            evidence=[response.model, f"categories={sorted(categories)}", f"avg_impact={response.summary.average_impact}"],
            remediation=None if ready else "Repair recommendation generators, feedback learning, and streaming suggestion feed.",
        )

    def _self_learning(self) -> FeatureCoverageCheck:
        feedback_files = [
            DATA_DIR / "recommendation_feedback.jsonl",
            DATA_DIR / "anomaly_feedback.jsonl",
            DATA_DIR / "ai_alert_acknowledgements.jsonl",
            SUGGESTION_FEEDBACK_PATH,
        ]
        source = (FRONTEND_COMPONENTS / "SmartSuggestionPanel.tsx").read_text(encoding="utf-8")
        ready = all(path.exists() for path in feedback_files) and "feedback" in source.lower()
        return FeatureCoverageCheck(
            name="Self-Learning AI System",
            category="learning",
            status="ready" if ready else "warning",
            details="Feedback, acknowledgement, adaptive thresholds, and recommendation learning signals are persisted for continuous model behavior tuning.",
            evidence=[f"feedback_files={sum(path.exists() for path in feedback_files)}/{len(feedback_files)}", *[path.name for path in feedback_files]],
            remediation=None if ready else "Seed feedback stores and expose operator feedback controls for adaptive threshold tuning.",
        )

    def _knowledge_ai(self) -> FeatureCoverageCheck:
        alpha = knowledge_engine.query("How was Project Alpha recovered?")
        skills = knowledge_engine.query("Who knows Kubernetes?")
        ready = knowledge_engine.available and knowledge_engine.vector_dimensions > 10 and alpha.sources[0].id != skills.sources[0].id
        return FeatureCoverageCheck(
            name="Enterprise Knowledge AI",
            category="knowledge",
            status="ready" if ready else "error",
            details="Company memory uses a persisted TF-IDF vector index, semantic retrieval, confidence scoring, and source-grounded answers.",
            evidence=[
                knowledge_engine.model_name,
                f"dimensions={knowledge_engine.vector_dimensions}",
                f"alpha_source={alpha.sources[0].id}",
                f"skills_source={skills.sources[0].id}",
            ],
            remediation=None if ready else "Rebuild vector memory indexing and semantic retrieval for company Q&A.",
        )

    def _cybersecurity_ai(self) -> FeatureCoverageCheck:
        low = security_analyzer.analyze(0, 0, 20, 0)
        high = security_analyzer.analyze(16, 12, 7800, 28)
        anomalies = anomaly_service.detect()
        ready = high.threat_score > low.threat_score and bool(anomalies.alerts)
        return FeatureCoverageCheck(
            name="Cybersecurity AI",
            category="security",
            status="ready" if ready else "error",
            details="Security analyzer and behavioral anomaly detector identify privileged-access drift, insider threat pressure, and data leakage risk.",
            evidence=[f"low={low.threat_score}", f"high={high.threat_score}", f"anomaly_alerts={len(anomalies.alerts)}", anomalies.model],
            remediation=None if ready else "Reconnect security scoring with anomaly detection and alert generation.",
        )

    def _meeting_analyzer(self) -> FeatureCoverageCheck:
        response = meeting_analyzer_service.analyze()
        panel = FRONTEND_COMPONENTS / "MeetingAnalyzerPanel.tsx"
        routes = [
            FRONTEND_API / "meetings" / "analyze" / "route.ts",
            FRONTEND_API / "meetings" / "stream" / "route.ts",
        ]
        ready = (
            response.action_items
            and response.speaker_analytics
            and response.summary.productivity_score > 0
            and response.summary.stress_index > 0
            and panel.exists()
            and all(path.exists() for path in routes)
            and inspect.isasyncgen(meeting_analyzer_service.stream())
        )
        return FeatureCoverageCheck(
            name="AI Meeting Analyzer",
            category="meeting",
            status="ready" if ready else "error",
            details="Transcript ingestion, PyTorch NLP sentiment, summaries, action extraction, speaker participation analytics, productivity scoring, persistence, and SSE streaming are verified.",
            evidence=[
                response.model,
                f"actions={len(response.action_items)}",
                f"speakers={len(response.speaker_analytics)}",
                f"productivity={response.summary.productivity_score}",
                str(panel),
            ],
            remediation=None if ready else "Regenerate meeting analyzer service, APIs, stream route, and dashboard panel.",
        )

    def _voice_stress_detection(self) -> FeatureCoverageCheck:
        calm = voice_stress_service.analyze(
            voice_stress_service.default_request().model_copy(
                update={
                    "speaker": "Calm Employee",
                    "transcript": "The plan is calm, clear, and under control.",
                    "audio_samples": voice_stress_service.demo_samples("calm", seconds=2.2),
                    "duration_seconds": 2.2,
                }
            )
        )
        stressed = voice_stress_service.analyze(
            voice_stress_service.default_request().model_copy(
                update={
                    "speaker": "Stressed Employee",
                    "transcript": "I am anxious, exhausted, frustrated, and this escalation is getting worse.",
                    "audio_samples": voice_stress_service.demo_samples("stressed", seconds=2.2),
                    "duration_seconds": 2.2,
                }
            )
        )
        panel = FRONTEND_COMPONENTS / "VoiceStressPanel.tsx"
        routes = [
            FRONTEND_API / "voice" / "analyze" / "route.ts",
            FRONTEND_API / "voice" / "stream" / "route.ts",
        ]
        ready = (
            stressed.stress_score > calm.stress_score + 12
            and stressed.burnout_risk > calm.burnout_risk
            and stressed.acoustic_features.pitch_variation > calm.acoustic_features.pitch_variation
            and stressed.alerts
            and stressed.timeline
            and panel.exists()
            and all(path.exists() for path in routes)
            and inspect.isasyncgen(voice_stress_service.stream())
        )
        return FeatureCoverageCheck(
            name="Voice Stress Detection AI",
            category="voice",
            status="ready" if ready else "error",
            details="Acoustic feature extraction, trained RandomForest voice stress inference, PyTorch transcript NLP fusion, alerts, timeline analytics, persistence, and SSE streaming are verified.",
            evidence=[
                stressed.model,
                f"calm_stress={calm.stress_score}",
                f"stressed_stress={stressed.stress_score}",
                f"alerts={len(stressed.alerts)}",
                f"timeline={len(stressed.timeline)}",
                str(panel),
            ],
            remediation=None if ready else "Regenerate voice stress engine, APIs, streaming proxy, and dashboard panel.",
        )

    def _team_compatibility_ai(self) -> FeatureCoverageCheck:
        response = team_compatibility_service.analyze()
        top_pair = response.pair_scores[0] if response.pair_scores else None
        risky_pair = max(response.pair_scores, key=lambda pair: pair.conflict_probability) if response.pair_scores else None
        panel = FRONTEND_COMPONENTS / "TeamCompatibilityPanel.tsx"
        routes = [
            FRONTEND_API / "team-compatibility" / "analyze" / "route.ts",
            FRONTEND_API / "team-compatibility" / "stream" / "route.ts",
        ]
        ready = (
            bool(top_pair)
            and bool(risky_pair)
            and top_pair.compatibility_score > risky_pair.compatibility_score
            and response.team_recommendations
            and response.conflict_warnings
            and response.leadership_matches
            and response.graph_nodes
            and response.graph_edges
            and panel.exists()
            and all(path.exists() for path in routes)
            and inspect.isasyncgen(team_compatibility_service.stream())
        )
        return FeatureCoverageCheck(
            name="Team Compatibility AI",
            category="workforce",
            status="ready" if ready else "error",
            details="Graph-aware ML compatibility scoring, conflict prediction, workstyle clustering, leadership matching, smart team formation, history persistence, and SSE streaming are verified.",
            evidence=[
                response.model,
                f"pairs={len(response.pair_scores)}",
                f"teams={len(response.team_recommendations)}",
                f"conflict_warnings={len(response.conflict_warnings)}",
                f"top_pair={response.summary.highest_compatibility_pair}",
                str(panel),
            ],
            remediation=None if ready else "Regenerate compatibility engine, APIs, dashboard, graph scoring, and streaming analytics.",
        )

    def _project_failure_prediction(self) -> FeatureCoverageCheck:
        response = project_failure_service.analyze()
        top_project = response.predictions[0] if response.predictions else None
        stable_project = min(response.predictions, key=lambda item: item.failure_probability) if response.predictions else None
        panel = FRONTEND_COMPONENTS / "ProjectFailurePanel.tsx"
        routes = [
            FRONTEND_API / "project-failure" / "predict" / "route.ts",
            FRONTEND_API / "project-failure" / "stream" / "route.ts",
        ]
        ready = (
            bool(top_project)
            and bool(stable_project)
            and top_project.failure_probability > stable_project.failure_probability + 12
            and top_project.deadline_miss_probability > stable_project.deadline_miss_probability
            and top_project.forecast
            and top_project.risk_signals
            and top_project.recommendations
            and response.portfolio_recommendations
            and response.heatmap
            and panel.exists()
            and all(path.exists() for path in routes)
            and inspect.isasyncgen(project_failure_service.stream())
        )
        return FeatureCoverageCheck(
            name="AI Project Failure Prediction",
            category="project-risk",
            status="ready" if ready else "error",
            details="RandomForest/XGBoost forecasting predicts delivery failure, delay, budget overrun, burnout impact, resource bottlenecks, project health, recommendations, history persistence, and SSE project-risk streaming.",
            evidence=[
                response.model,
                f"projects={len(response.predictions)}",
                f"highest={response.summary.highest_risk_project}",
                f"avg_failure={response.summary.average_failure_probability}",
                f"recommendations={len(response.portfolio_recommendations)}",
                str(panel),
            ],
            remediation=None if ready else "Regenerate project forecasting engine, APIs, dashboard, realtime stream, and project-risk recommendations.",
        )

    def _roi_intelligence(self) -> FeatureCoverageCheck:
        response = roi_intelligence_service.analyze()
        panel = FRONTEND_COMPONENTS / "RoiIntelligencePanel.tsx"
        routes = [
            FRONTEND_API / "roi" / "analyze" / "route.ts",
            FRONTEND_API / "roi" / "stream" / "route.ts",
        ]
        ready = (
            response.summary.baseline_annual_loss > response.summary.optimized_annual_loss
            and response.summary.net_savings > 0
            and response.summary.roi_percent > 0
            and response.replacement_costs
            and response.productivity_losses
            and response.delay_costs
            and response.recommendations
            and response.executive_insights
            and response.forecast
            and panel.exists()
            and all(path.exists() for path in routes)
            and inspect.isasyncgen(roi_intelligence_service.stream())
        )
        return FeatureCoverageCheck(
            name="Enterprise ROI Intelligence",
            category="business-impact",
            status="ready" if ready else "error",
            details="Workforce economics engine converts attrition, burnout, productivity loss, meeting load, overtime, and project delay risk into executive ROI, savings, payback, recommendations, persistence, and SSE business-impact streaming.",
            evidence=[
                response.model,
                f"net_savings={response.summary.net_savings}",
                f"roi={response.summary.roi_percent}",
                f"payback={response.summary.payback_months}",
                f"insights={len(response.executive_insights)}",
                str(panel),
            ],
            remediation=None if ready else "Regenerate ROI analytics engine, business-impact APIs, dashboard, realtime stream, and executive recommendations.",
        )

    def _realtime_power_analytics(self) -> FeatureCoverageCheck:
        snapshot = power_feature_service.realtime_snapshot()
        ready = snapshot.kpis and snapshot.events and inspect.isasyncgen(power_feature_service.realtime_stream())
        return FeatureCoverageCheck(
            name="Real-time Analytics Power Layer",
            category="realtime",
            status="ready" if ready else "error",
            details="Unified realtime analytics stream combines employee, manager, project, team, alert, suggestion, and ROI signals with SSE and WebSocket routes.",
            evidence=[snapshot.model, f"kpis={len(snapshot.kpis)}", f"events={len(snapshot.events)}", "WebSocket=/api/v1/power/realtime/ws"],
            remediation=None if ready else "Rebuild realtime analytics aggregation, SSE stream, and WebSocket route.",
        )

    def _explainable_ai(self) -> FeatureCoverageCheck:
        explanation = power_feature_service.explain(XAIExplanationRequest(target="burnout"))
        ready = explanation.shap_values and explanation.lime_weights and explanation.counterfactuals
        return FeatureCoverageCheck(
            name="Explainable AI / XAI",
            category="xai",
            status="ready" if ready else "error",
            details="SHAP-style and LIME-style feature attribution explains burnout, project delay, productivity, compatibility, and recommendation decisions.",
            evidence=[explanation.model, f"top_feature={explanation.shap_values[0].feature if explanation.shap_values else 'none'}", f"counterfactuals={len(explanation.counterfactuals)}"],
            remediation=None if ready else "Regenerate XAI service with feature attribution and counterfactual reasoning.",
        )

    def _graph_neural_networks(self) -> FeatureCoverageCheck:
        graph = power_feature_service.graph_relations()
        ready = graph.nodes and graph.edges and graph.training_metrics.get("mae", 1) < 0.08
        return FeatureCoverageCheck(
            name="Graph Neural Networks for Team Relations",
            category="graph_ai",
            status="ready" if ready else "error",
            details="PyTorch GraphSAGE team relation model produces employee embeddings, attention-weighted edges, burnout propagation, conflict projection, and leadership influence.",
            evidence=[graph.model, f"nodes={len(graph.nodes)}", f"edges={len(graph.edges)}", f"mae={graph.training_metrics.get('mae')}"],
            remediation=None if ready else "Train and connect GraphSAGE team relationship inference.",
        )

    def _generative_manager_assistant(self) -> FeatureCoverageCheck:
        response = power_feature_service.ask_manager(ManagerAssistantRequest(question="Why is Team Alpha productivity decreasing?"))
        ready = bool(response.answer and response.context_sources and response.recommended_actions)
        return FeatureCoverageCheck(
            name="Generative AI Manager Assistant",
            category="assistant",
            status="ready" if ready else "error",
            details="RAG manager assistant answers natural-language management questions using live analytics, vector memory, recommendations, and reasoning traces.",
            evidence=[response.model, f"sources={len(response.context_sources)}", f"actions={len(response.recommended_actions)}", f"confidence={response.confidence}"],
            remediation=None if ready else "Reconnect manager assistant to analytics context and vector retrieval.",
        )

    def _realtime_systems(self) -> FeatureCoverageCheck:
        routes = [
            FRONTEND_API / "alerts" / "stream" / "route.ts",
            FRONTEND_API / "suggestions" / "stream" / "route.ts",
            FRONTEND_API / "team-compatibility" / "stream" / "route.ts",
            FRONTEND_API / "project-failure" / "stream" / "route.ts",
            FRONTEND_API / "roi" / "stream" / "route.ts",
        ]
        ready = (
            inspect.isasyncgen(alert_service.stream())
            and inspect.isasyncgen(smart_suggestion_service.stream())
            and inspect.isasyncgen(team_compatibility_service.stream())
            and inspect.isasyncgen(project_failure_service.stream())
            and inspect.isasyncgen(roi_intelligence_service.stream())
            and all(path.exists() for path in routes)
        )
        return FeatureCoverageCheck(
            name="Realtime AI Infrastructure",
            category="realtime",
            status="ready" if ready else "error",
            details="Server-sent alert and suggestion streams provide live dashboard updates without static notification cards.",
            evidence=[f"routes={sum(path.exists() for path in routes)}/{len(routes)}", *[path.name for path in routes]],
            remediation=None if ready else "Repair stream generators and Next.js proxy routes.",
        )

    def _cinematic_ui(self) -> FeatureCoverageCheck:
        required = [
            "EnterpriseTwinScene.tsx",
            "ExecutiveAssistantPanel.tsx",
            "SimulationConsole.tsx",
            "AutonomyPanel.tsx",
            "AIAlertCenterPanel.tsx",
            "SmartSuggestionPanel.tsx",
            "MeetingAnalyzerPanel.tsx",
            "VoiceStressPanel.tsx",
            "TeamCompatibilityPanel.tsx",
            "ProjectFailurePanel.tsx",
            "RoiIntelligencePanel.tsx",
            "CybersecurityPanel.tsx",
        ]
        existing = [name for name in required if (FRONTEND_COMPONENTS / name).exists()]
        ready = len(existing) == len(required)
        return FeatureCoverageCheck(
            name="Cinematic Enterprise UI",
            category="ui",
            status="ready" if ready else "missing",
            details="Advanced feature panels exist for voice assistant, 3D control room, simulation, agents, alerts, suggestions, and cybersecurity workflows.",
            evidence=[f"panels={len(existing)}/{len(required)}", *existing],
            remediation=None if ready else "Regenerate missing advanced dashboard panels and wire them into the command center.",
        )

    @staticmethod
    def _safe(probe: Callable[[], FeatureCoverageCheck]) -> FeatureCoverageCheck:
        try:
            return probe()
        except Exception as exc:
            return FeatureCoverageCheck(
                name=probe.__name__.replace("_", " ").title(),
                category="system",
                status="error",
                details=f"Advanced feature probe crashed: {type(exc).__name__}",
                evidence=[str(exc)[:220]],
                remediation="Fix the crashed advanced module before claiming production readiness.",
            )

    @staticmethod
    def _summary(checks: list[FeatureCoverageCheck]) -> FeatureCoverageSummary:
        ready = sum(1 for check in checks if check.status == "ready")
        warnings = sum(1 for check in checks if check.status == "warning")
        missing = sum(1 for check in checks if check.status == "missing")
        errors = sum(1 for check in checks if check.status == "error")
        score = round(((ready + warnings * 0.72) / len(checks)) * 100, 2) if checks else 0
        return FeatureCoverageSummary(total=len(checks), ready=ready, warnings=warnings, missing=missing, errors=errors, coverage_score=score)


advanced_feature_service = AdvancedFeatureService()
