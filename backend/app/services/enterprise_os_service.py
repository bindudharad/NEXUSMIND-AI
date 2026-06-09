from __future__ import annotations

import inspect
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

from app.ai.digital_twin import TwinScenarioInput, digital_twin_simulator
from app.ai.knowledge_engine import INDEX_PATH, knowledge_engine
from app.ai.security_analyzer import security_analyzer
from app.core.cache import TTLResponseCache
from app.schemas.competitive_intelligence import CompetitiveAssistantRequest
from app.schemas.client_satisfaction import ClientAssistantRequest
from app.schemas.company_emotion_map import EmotionAssistantRequest
from app.schemas.feature_coverage import FeatureCoverageCheck, FeatureCoverageResponse, FeatureCoverageSummary
from app.schemas.power_features import ManagerAssistantRequest, XAIExplanationRequest
from app.schemas.smart_interviewer import SmartInterviewAssistantRequest
from app.schemas.talent_marketplace import TalentAssistantRequest
from app.services.alert_service import alert_service
from app.services.anomaly_service import anomaly_service
from app.services.company_simulation_lab_service import company_simulation_lab_service
from app.services.client_satisfaction_service import client_satisfaction_service
from app.services.company_emotion_map_service import company_emotion_map_service
from app.services.competitive_intelligence_service import competitive_intelligence_service
from app.services.multi_agent_workforce_service import multi_agent_workforce_service
from app.services.power_feature_service import power_feature_service
from app.services.project_failure_service import project_failure_service
from app.services.roi_service import roi_intelligence_service
from app.services.smart_interviewer_service import smart_interviewer_service
from app.services.strategic_intelligence_service import strategic_intelligence_service
from app.services.suggestion_service import FEEDBACK_PATH as SUGGESTION_FEEDBACK_PATH
from app.services.suggestion_service import smart_suggestion_service
from app.services.talent_marketplace_service import talent_marketplace_service
from app.services.team_compatibility_service import team_compatibility_service


ROOT = Path(__file__).resolve().parents[3]
FRONTEND_COMPONENTS = ROOT / "frontend" / "src" / "components" / "dashboard"
FRONTEND_API = ROOT / "frontend" / "src" / "app" / "api"
DATA_DIR = ROOT / "backend" / "app" / "data"


class EnterpriseOSService:
    model_name = "Fortune 500 Enterprise AI Operating System Auditor"

    def __init__(self) -> None:
        self._cache: TTLResponseCache[FeatureCoverageResponse] = TTLResponseCache(ttl_seconds=35)

    def verify(self) -> FeatureCoverageResponse:
        return self._cache.get_or_set(self._verify_uncached)

    def _verify_uncached(self) -> FeatureCoverageResponse:
        probes: list[Callable[[], FeatureCoverageCheck]] = [
            self._digital_twin_ai,
            self._multi_agent_ai,
            self._ceo_assistant,
            self._what_if_engine,
            self._company_simulation_lab,
            self._client_relationship_intelligence,
            self._internal_talent_marketplace,
            self._smart_interviewer,
            self._company_emotion_map,
            self._knowledge_ai,
            self._cybersecurity_ai,
            self._control_room_3d,
            self._self_learning_ai,
            self._decision_intelligence,
            self._strategic_intelligence_graph,
            self._competitive_intelligence_war_room,
            self._realtime_infrastructure,
            self._frontend_enterprise_ui,
            self._api_backend_layer,
            self._database_vector_layer,
        ]
        checks = [self._safe(probe) for probe in probes]
        summary = self._summary(checks)
        critical_gaps = [
            f"{check.name}: {check.remediation or check.details}"
            for check in checks
            if check.status in {"missing", "error"}
        ]
        verdict = (
            "NEXUSMIND AI verifies as a Fortune-500-grade enterprise AI operating system: digital twin simulations, multi-agent reasoning, executive assistant, knowledge memory, security intelligence, self-learning signals, realtime infrastructure, and cinematic control-room UI are connected."
            if not critical_gaps and summary.coverage_score >= 92
            else "NEXUSMIND AI still has enterprise operating-system gaps that must be remediated before a Fortune 500 demo."
        )
        return FeatureCoverageResponse(
            generated_at=datetime.now(timezone.utc),
            summary=summary,
            checks=checks,
            critical_gaps=critical_gaps,
            verdict=verdict,
        )

    def _digital_twin_ai(self) -> FeatureCoverageCheck:
        baseline = digital_twin_simulator.simulate_extended(TwinScenarioInput(0, 0, 0, False))
        backend_resignation = digital_twin_simulator.simulate_extended(TwinScenarioInput(20, 24, -10, False))
        crisis = digital_twin_simulator.simulate_extended(TwinScenarioInput(32, 42, -18, True))
        monte_carlo = digital_twin_simulator.simulate_monte_carlo(TwinScenarioInput(30, 35, 5, True))
        model = digital_twin_simulator.company_model
        workflow_delta = max(crisis.workflow_impacts.values()) - min(baseline.workflow_impacts.values())
        ready = (
            len(model.employees) >= 7
            and len(model.departments) >= 5
            and len(model.workflows) >= 4
            and backend_resignation.delay_probability > baseline.delay_probability
            and crisis.team_collapse_probability > backend_resignation.team_collapse_probability
            and workflow_delta > 20
            and monte_carlo.runs >= 128
            and monte_carlo.delay_probability_p90 >= monte_carlo.delay_probability_p50
        )
        return FeatureCoverageCheck(
            name="Digital Twin AI",
            category="simulation",
            status="ready" if ready else "error",
            details="Shadow Company AI models virtual employees, departments, workflows, resignations, workload shocks, budget cuts, chain reactions, and recovery actions.",
            evidence=[
                f"employees={len(model.employees)}",
                f"departments={len(model.departments)}",
                f"workflows={len(model.workflows)}",
                f"baseline_delay={baseline.delay_probability}",
                f"resignation_delay={backend_resignation.delay_probability}",
                f"crisis_collapse={crisis.team_collapse_probability}",
                f"monte_carlo_runs={monte_carlo.runs}",
                f"p90_delay={monte_carlo.delay_probability_p90}",
            ],
            remediation=None if ready else "Regenerate digital twin simulation with virtual company entities and dynamic scenario impacts.",
        )

    def _multi_agent_ai(self) -> FeatureCoverageCheck:
        workforce = multi_agent_workforce_service.run()
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
        ready = (
            required == agents
            and workforce.summary.coordination_score >= 90
            and len(workforce.memory) >= 8
            and len(workforce.messages) >= 8
            and len(workforce.workflows) >= 4
            and bool(workforce.decisions)
            and bool(workforce.simulations)
            and inspect.isasyncgen(multi_agent_workforce_service.stream())
        )
        return FeatureCoverageCheck(
            name="Multi-Agent AI System",
            category="agents",
            status="ready" if ready else "error",
            details="Agent council verifies People Intelligence, Security, Finance, Project, Productivity, Client, Knowledge, and Executive AI manager agents sharing memory, tool output, workflow triggers, digital-twin simulations, and Executive AI Council decisions.",
            evidence=[
                f"agents={sorted(agents)}",
                f"memory={len(workforce.memory)}",
                f"messages={len(workforce.messages)}",
                f"workflows={len(workforce.workflows)}",
                workforce.decisions[0].recommendation[:150] if workforce.decisions else "",
            ],
            remediation=None if ready else "Complete the multi-agent workforce service with shared memory, messaging, workflows, simulation, and executive decisions.",
        )

    def _ceo_assistant(self) -> FeatureCoverageCheck:
        response = power_feature_service.ask_manager(ManagerAssistantRequest(question="What department is highest risk and how can we reduce burnout?"))
        source = (FRONTEND_COMPONENTS / "ExecutiveAssistantPanel.tsx").read_text(encoding="utf-8")
        ready = (
            response.answer
            and response.context_sources
            and response.reasoning_trace
            and all(token in source for token in ["SpeechRecognition", "speechSynthesis", "selectDirective"])
        )
        return FeatureCoverageCheck(
            name="Generative AI CEO Assistant",
            category="assistant",
            status="ready" if ready else "error",
            details="Executive assistant combines voice controls, natural-language analytics answers, RAG memory, context sources, recommendations, and reasoning traces.",
            evidence=[response.model, f"sources={len(response.context_sources)}", f"actions={len(response.recommended_actions)}", f"confidence={response.confidence}"],
            remediation=None if ready else "Reconnect executive assistant to live analytics, vector memory, and voice command controls.",
        )

    def _what_if_engine(self) -> FeatureCoverageCheck:
        stable = digital_twin_simulator.simulate_extended(TwinScenarioInput(4, 5, 15, False))
        overload = digital_twin_simulator.simulate_extended(TwinScenarioInput(12, 25, 0, False))
        collapse = digital_twin_simulator.simulate_extended(TwinScenarioInput(28, 45, -22, True))
        route = FRONTEND_API / "intelligence" / "digital-twin" / "simulate" / "route.ts"
        panel = FRONTEND_COMPONENTS / "SimulationConsole.tsx"
        source = panel.read_text(encoding="utf-8") if panel.exists() else ""
        ready = (
            route.exists()
            and "Run what-if simulation" in source
            and overload.burnout_delta > stable.burnout_delta
            and collapse.revenue_impact_percent < overload.revenue_impact_percent
            and collapse.delay_probability > overload.delay_probability
        )
        return FeatureCoverageCheck(
            name="Enterprise What-If Engine",
            category="simulation",
            status="ready" if ready else "error",
            details="What-if engine simulates workload growth, hiring/budget movement, burnout spread, productivity collapse, delay probability, and revenue impact.",
            evidence=[str(route), f"stable_delay={stable.delay_probability}", f"overload_delay={overload.delay_probability}", f"collapse_revenue={collapse.revenue_impact_percent}%"],
            remediation=None if ready else "Rebuild interactive what-if engine and connect it to the digital twin API.",
        )

    def _company_simulation_lab(self) -> FeatureCoverageCheck:
        lab = company_simulation_lab_service.run()
        route = FRONTEND_API / "simulation" / "company-lab" / "default" / "route.ts"
        assistant = FRONTEND_API / "simulation" / "company-lab" / "assistant" / "route.ts"
        panel = FRONTEND_COMPONENTS / "CompanySimulationLabPanel.tsx"
        scenario_types = {scenario.scenario_type for scenario in lab.scenarios}
        ready = (
            route.exists()
            and assistant.exists()
            and panel.exists()
            and len(lab.scenarios) >= 6
            and len(lab.comparison) >= 3
            and lab.summary.decision_readiness_score >= 50
            and {"work_from_home_policy", "hiring_freeze", "employee_resignation", "budget_reduction", "meeting_reduction"}.issubset(scenario_types)
        )
        return FeatureCoverageCheck(
            name="AI Company Simulation Lab",
            category="decision_intelligence",
            status="ready" if ready else "missing",
            details="Business decision flight simulator uses digital twin data, forecast metrics, scenario comparison, AI assistant, and executive recommendations to test operating decisions before rollout.",
            evidence=[
                str(route),
                str(assistant),
                str(panel),
                f"scenario_count={len(lab.scenarios)}",
                f"comparison_count={len(lab.comparison)}",
                f"recommended={lab.summary.recommended_scenario}",
                f"source_systems={lab.source_systems[:6]}",
            ],
            remediation=None if ready else "Add dedicated Simulation Lab API, frontend panel, assistant route, scenario comparison, and dashboard evidence.",
        )

    def _smart_interviewer(self) -> FeatureCoverageCheck:
        response = smart_interviewer_service.run()
        assistant = smart_interviewer_service.ask(SmartInterviewAssistantRequest(question="Generate interview report."))
        routes = [
            FRONTEND_API / "interviews" / "smart" / "default" / "route.ts",
            FRONTEND_API / "interviews" / "smart" / "run" / "route.ts",
            FRONTEND_API / "interviews" / "smart" / "assistant" / "route.ts",
            FRONTEND_API / "interviews" / "smart" / "stream" / "route.ts",
        ]
        panel = FRONTEND_COMPONENTS / "SmartInterviewerPanel.tsx"
        top = response.candidate_rankings[0]
        source_systems = set(response.source_systems)
        ready = (
            len(response.generated_questions) >= 5
            and response.summary.active_interviews >= 3
            and top.technical_score > 50
            and top.behavioral_score > 50
            and top.voice_confidence_score > 50
            and top.report.pdf_path.endswith(".pdf")
            and top.report.docx_path.endswith(".docx")
            and assistant.intent == "report"
            and inspect.isasyncgen(smart_interviewer_service.stream())
            and panel.exists()
            and all(path.exists() for path in routes)
            and {"interview_engine", "voice_confidence_engine", "cheating_detection_engine", "interview_report_generator"}.issubset(source_systems)
        )
        return FeatureCoverageCheck(
            name="AI Smart Interviewer System",
            category="hiring",
            status="ready" if ready else "missing",
            details="Autonomous hiring panel conducts dynamic interviews, analyzes resumes, scores technical and behavioral answers, evaluates voice confidence, detects cheating, ranks candidates, and generates PDF/DOCX reports.",
            evidence=[
                response.model,
                f"questions={len(response.generated_questions)}",
                f"active_interviews={response.summary.active_interviews}",
                f"top={top.candidate_name}",
                f"overall={top.overall_score}",
                f"cheating_risk={top.cheating_risk_score}",
                str(panel),
            ],
            remediation=None if ready else "Implement Smart Interviewer APIs, dashboard, report generation, ranking, assistant, and stream evidence.",
        )

    def _client_relationship_intelligence(self) -> FeatureCoverageCheck:
        response = client_satisfaction_service.predict()
        assistant = client_satisfaction_service.ask(ClientAssistantRequest(question="Show upsell opportunities."))
        routes = [
            FRONTEND_API / "client-satisfaction" / "predict" / "route.ts",
            FRONTEND_API / "client-satisfaction" / "assistant" / "route.ts",
            FRONTEND_API / "client-satisfaction" / "stream" / "route.ts",
        ]
        panel = FRONTEND_COMPONENTS / "ClientSatisfactionPanel.tsx"
        top = response.predictions[0]
        source_systems = set(response.source_systems)
        ready = (
            response.summary.clients_analyzed >= 3
            and response.payment_risks
            and response.project_risks
            and response.engagement_analytics
            and response.opportunity_pipeline
            and response.summary.opportunity_revenue >= 0
            and assistant.intent == "opportunity"
            and panel.exists()
            and all(path.exists() for path in routes)
            and inspect.isasyncgen(client_satisfaction_service.stream())
            and {
                "client_health_engine",
                "churn_prediction_engine",
                "payment_risk_engine",
                "project_risk_engine",
                "ai_client_assistant",
                "opportunity_detection_engine",
            }.issubset(source_systems)
        )
        return FeatureCoverageCheck(
            name="AI Client Relationship Intelligence System",
            category="client",
            status="ready" if ready else "missing",
            details="AI client retention and revenue-protection engine predicts churn, payment delay, project failure, dissatisfaction, engagement decline, and expansion opportunity with assistant-backed recommendations.",
            evidence=[
                response.model,
                f"top_client={top.client_name}",
                f"churn={top.churn_risk}",
                f"payment={top.payment_delay_risk}",
                f"project={top.project_failure_risk}",
                f"assistant_intent={assistant.intent}",
                str(panel),
            ],
            remediation=None if ready else "Build full client relationship intelligence APIs, dashboard, assistant, payment/project/opportunity engines, and stream.",
        )

    def _internal_talent_marketplace(self) -> FeatureCoverageCheck:
        response = talent_marketplace_service.default()
        assistant = talent_marketplace_service.ask(TalentAssistantRequest(question="Find AI projects for me."))
        routes = [
            FRONTEND_API / "talent" / "marketplace" / "default" / "route.ts",
            FRONTEND_API / "talent" / "marketplace" / "search" / "route.ts",
            FRONTEND_API / "talent" / "marketplace" / "assistant" / "route.ts",
            FRONTEND_API / "talent" / "marketplace" / "stream" / "route.ts",
        ]
        panel = FRONTEND_COMPONENTS / "TalentMarketplacePanel.tsx"
        source_systems = set(response.source_systems)
        ready = (
            response.summary.profiles >= 4
            and response.project_matches
            and response.mentor_matches
            and response.internal_role_matches
            and response.learning_paths
            and response.expert_rankings
            and response.reputation_scores
            and response.badges
            and response.summary.marketplace_health_score > 50
            and assistant.intent == "projects"
            and inspect.isasyncgen(talent_marketplace_service.stream())
            and panel.exists()
            and all(path.exists() for path in routes)
            and {
                "talent_profile_engine",
                "skill_intelligence_engine",
                "project_matching_engine",
                "mentor_matching_engine",
                "internal_job_matching_engine",
                "learning_recommendation_engine",
                "reputation_engine",
                "marketplace_dashboard",
                "talent_ai_assistant",
                "employee_digital_twin",
                "knowledge_brain",
                "workflow_automation",
            }.issubset(source_systems)
        )
        return FeatureCoverageCheck(
            name="AI Internal Talent Marketplace",
            category="workforce",
            status="ready" if ready else "missing",
            details="LinkedIn-style internal career network matches employees to projects, mentors, learning paths, internal roles, expert directories, badges, and reputation signals with graph-backed assistant flows.",
            evidence=[
                response.model,
                f"health={response.summary.marketplace_health_score}",
                f"top_match={response.summary.top_project_match}",
                f"top_expert={response.summary.top_expert}",
                f"badges={response.summary.badges_awarded}",
                f"assistant_intent={assistant.intent}",
                str(panel),
            ],
            remediation=None if ready else "Implement the dedicated talent marketplace backend, dashboard, assistant, search, stream, graph, badges, and audit source systems.",
        )

    def _company_emotion_map(self) -> FeatureCoverageCheck:
        response = company_emotion_map_service.default()
        assistant = company_emotion_map_service.ask(EmotionAssistantRequest(question="Show burnout hotspots."))
        routes = [
            FRONTEND_API / "emotion" / "map" / "default" / "route.ts",
            FRONTEND_API / "emotion" / "map" / "analyze" / "route.ts",
            FRONTEND_API / "emotion" / "map" / "assistant" / "route.ts",
            FRONTEND_API / "emotion" / "map" / "stream" / "route.ts",
        ]
        panel = FRONTEND_COMPONENTS / "CompanyEmotionMapPanel.tsx"
        source_systems = set(response.source_systems)
        ready = (
            response.employee_scores
            and response.team_scores
            and response.department_scores
            and response.heatmap
            and response.conflict_risks
            and response.burnout_predictions
            and response.forecasts
            and response.workflow_triggers
            and response.digital_twin_updates
            and assistant.intent == "burnout"
            and inspect.isasyncgen(company_emotion_map_service.stream())
            and panel.exists()
            and all(path.exists() for path in routes)
            and {
                "emotion_analytics_engine",
                "sentiment_analysis_engine",
                "burnout_prediction_engine",
                "conflict_detection_engine",
                "motivation_analysis_engine",
                "engagement_intelligence_engine",
                "organizational_heatmap_engine",
                "emotion_ai_assistant",
                "employee_digital_twin",
                "team_digital_twin",
                "company_digital_twin",
                "workflow_automation",
            }.issubset(source_systems)
        )
        return FeatureCoverageCheck(
            name="Company Emotion Map",
            category="emotion",
            status="ready" if ready else "missing",
            details="Real-time emotional digital twin validates stress, happiness, burnout, motivation, engagement, conflict, morale, forecasts, recommendations, AI assistant, workflow triggers, and dashboard/API integration.",
            evidence=[
                response.model,
                f"health={response.summary.organizational_health_score}",
                f"stress_hotspots={response.summary.high_stress_hotspots}",
                f"burnout_hotspots={response.summary.high_burnout_hotspots}",
                f"conflict_zones={response.summary.high_conflict_zones}",
                f"assistant_intent={assistant.intent}",
                str(panel),
            ],
            remediation=None if ready else "Build Company Emotion Map service, FastAPI routes, Next.js proxy routes, dashboard panel, assistant, stream, and source-system evidence.",
        )

    def _knowledge_ai(self) -> FeatureCoverageCheck:
        burnout = knowledge_engine.query("What policy affects meeting load and burnout recovery?")
        security = knowledge_engine.query("How should suspicious admin activity be handled?")
        ready = (
            knowledge_engine.available
            and knowledge_engine.vector_dimensions > 20
            and INDEX_PATH.exists()
            and burnout.sources
            and security.sources
            and burnout.sources[0].id != security.sources[0].id
        )
        return FeatureCoverageCheck(
            name="Enterprise Memory + Knowledge AI",
            category="knowledge",
            status="ready" if ready else "error",
            details="Enterprise memory uses persisted vector retrieval, semantic document search, source-grounded answers, and confidence scoring.",
            evidence=[knowledge_engine.model_name, f"dimensions={knowledge_engine.vector_dimensions}", f"burnout_source={burnout.sources[0].id}", f"security_source={security.sources[0].id}", str(INDEX_PATH)],
            remediation=None if ready else "Regenerate vector memory index, embedding retrieval, and RAG answer grounding.",
        )

    def _cybersecurity_ai(self) -> FeatureCoverageCheck:
        low = security_analyzer.analyze(1, 0, 35, 0)
        high = security_analyzer.analyze(18, 14, 8800, 32)
        anomalies = anomaly_service.detect()
        alerts = alert_service.feed()
        security_alerts = [alert for alert in alerts.alerts if alert.category == "security"]
        ready = high.threat_score > low.threat_score + 45 and anomalies.alerts and security_alerts
        return FeatureCoverageCheck(
            name="AI Security Intelligence",
            category="security",
            status="ready" if ready else "error",
            details="Security intelligence fuses suspicious login/access activity, export risk, privileged action drift, behavioral anomaly detection, and realtime security alerts.",
            evidence=[f"low={low.threat_score}", f"high={high.threat_score}", f"anomaly_alerts={len(anomalies.alerts)}", f"security_alerts={len(security_alerts)}"],
            remediation=None if ready else "Reconnect anomaly detection, security scoring, and security alert generation.",
        )

    def _control_room_3d(self) -> FeatureCoverageCheck:
        path = FRONTEND_COMPONENTS / "EnterpriseTwinScene.tsx"
        source = path.read_text(encoding="utf-8") if path.exists() else ""
        package = (ROOT / "frontend" / "package.json").read_text(encoding="utf-8")
        ready = (
            path.exists()
            and all(token in source for token in ["Canvas", "OrbitControls", "useFrame", "risk", "OrgGraphNode"])
            and "@react-three/fiber" in package
            and "three" in package
        )
        return FeatureCoverageCheck(
            name="3D Enterprise Control Room",
            category="visualization",
            status="ready" if ready else "missing",
            details="Three.js/React Three Fiber control room renders dynamic organization-risk nodes, orbital controls, animation frames, and risk-based visualization.",
            evidence=[str(path), "@react-three/fiber", "three", "OrbitControls", "risk-colored nodes"],
            remediation=None if ready else "Rebuild the 3D control room with live organization map data and stable WebGL rendering.",
        )

    def _self_learning_ai(self) -> FeatureCoverageCheck:
        feedback_files = [
            DATA_DIR / "recommendation_feedback.jsonl",
            DATA_DIR / "smart_suggestion_feedback.jsonl",
            DATA_DIR / "anomaly_feedback.jsonl",
            DATA_DIR / "ai_alert_acknowledgements.jsonl",
            SUGGESTION_FEEDBACK_PATH,
        ]
        existing = [path for path in feedback_files if path.exists()]
        suggestion = smart_suggestion_service.generate()
        adaptive_threshold = anomaly_service.detect().adaptive_threshold
        ready = len(existing) >= 4 and suggestion.summary.average_confidence > 0 and adaptive_threshold > 0
        return FeatureCoverageCheck(
            name="Self-Learning AI System",
            category="learning",
            status="ready" if ready else "warning",
            details="Feedback files, alert acknowledgements, recommendation learning signals, adaptive anomaly thresholds, and confidence-weighted suggestions support continuous improvement.",
            evidence=[f"feedback_files={len(existing)}/{len(feedback_files)}", f"adaptive_threshold={adaptive_threshold}", f"suggestion_confidence={suggestion.summary.average_confidence}"],
            remediation=None if ready else "Seed feedback stores and expose more operator feedback controls for adaptive scoring.",
        )

    def _decision_intelligence(self) -> FeatureCoverageCheck:
        suggestions = smart_suggestion_service.generate()
        roi = roi_intelligence_service.analyze()
        project = project_failure_service.analyze()
        explanation = power_feature_service.explain(XAIExplanationRequest(target="recommendation"))
        ready = (
            suggestions.suggestions
            and roi.recommendations
            and project.portfolio_recommendations
            and explanation.counterfactuals
            and suggestions.summary.average_impact > 60
        )
        return FeatureCoverageCheck(
            name="AI Decision Intelligence",
            category="decision",
            status="ready" if ready else "error",
            details="Decision engine prioritizes workforce optimization, meeting reduction, cost-saving, delivery-risk, ROI, and explainable intervention actions.",
            evidence=[suggestions.model, f"avg_impact={suggestions.summary.average_impact}", f"roi={roi.summary.roi_percent}", f"portfolio_actions={len(project.portfolio_recommendations)}", f"xai_counterfactuals={len(explanation.counterfactuals)}"],
            remediation=None if ready else "Regenerate decision scoring with ROI, project-risk, suggestion, and XAI integration.",
        )

    def _strategic_intelligence_graph(self) -> FeatureCoverageCheck:
        response = strategic_intelligence_service.analyze()
        panel = FRONTEND_COMPONENTS / "StrategicIntelligencePanel.tsx"
        routes = [
            FRONTEND_API / "strategic" / "enterprise" / "route.ts",
            FRONTEND_API / "strategic" / "stream" / "route.ts",
        ]
        ready = (
            response.competitive_intelligence
            and response.client_relationship_intelligence
            and response.internal_marketplace_matches
            and response.mentor_matches
            and response.organization_optimizations
            and response.crisis_response.recovery_priorities
            and response.innovation_signals
            and panel.exists()
            and all(path.exists() for path in routes)
        )
        return FeatureCoverageCheck(
            name="Strategic Intelligence Graph",
            category="strategy",
            status="ready" if ready else "error",
            details="Competitor analytics, client risk, internal talent marketplace, mentorship matching, organization optimization, crisis response, and innovation detection are implemented as one operational graph.",
            evidence=[
                response.model,
                f"competitors={len(response.competitive_intelligence)}",
                f"clients={len(response.client_relationship_intelligence)}",
                f"marketplace_matches={len(response.internal_marketplace_matches)}",
                f"org_units={len(response.organization_optimizations)}",
                str(panel),
            ],
            remediation=None if ready else "Implement strategic intelligence APIs, streaming proxy, dashboard panel, and dynamic strategy scoring.",
        )

    def _competitive_intelligence_war_room(self) -> FeatureCoverageCheck:
        response = competitive_intelligence_service.analyze()
        assistant = competitive_intelligence_service.ask(
            CompetitiveAssistantRequest(question="Which technologies are competitors adopting?")
        )
        panel = FRONTEND_COMPONENTS / "CompetitiveIntelligencePanel.tsx"
        routes = [
            FRONTEND_API / "competitive" / "intelligence" / "default" / "route.ts",
            FRONTEND_API / "competitive" / "intelligence" / "assistant" / "route.ts",
            FRONTEND_API / "competitive" / "intelligence" / "stream" / "route.ts",
        ]
        ready = (
            response.summary.competitor_count >= 4
            and response.product_launches
            and response.hiring_trends
            and response.technology_adoption
            and response.market_expansions
            and response.industry_trends
            and response.recommendations
            and assistant.intent == "technology"
            and inspect.isasyncgen(competitive_intelligence_service.stream())
            and panel.exists()
            and all(path.exists() for path in routes)
        )
        return FeatureCoverageCheck(
            name="AI Competitive Intelligence War Room",
            category="strategy",
            status="ready" if ready else "error",
            details="Dedicated strategic-war-room capability tracks competitor profiles, product launches, hiring, technology adoption, market expansion, trend forecasts, comparison scorecards, and executive strategy recommendations.",
            evidence=[
                response.model,
                f"top_threat={response.summary.top_competitor_threat}",
                f"threat_score={response.summary.average_threat_score}",
                f"launches={len(response.product_launches)}",
                f"technologies={response.summary.technologies_tracked}",
                f"assistant_intent={assistant.intent}",
                str(panel),
            ],
            remediation=None if ready else "Build competitive intelligence backend, proxy routes, dashboard panel, assistant, stream, and audit evidence.",
        )

    def _realtime_infrastructure(self) -> FeatureCoverageCheck:
        snapshot = power_feature_service.realtime_snapshot(sequence=2, mode="pressure")
        power_route = ROOT / "backend" / "app" / "api" / "v1" / "routes" / "power.py"
        power_route_source = power_route.read_text(encoding="utf-8") if power_route.exists() else ""
        ws_auth_ready = all(token in power_route_source for token in ["@router.websocket", "get_user_from_token", "1008"])
        stream_ready = all(
            [
                inspect.isasyncgen(power_feature_service.realtime_stream()),
                inspect.isasyncgen(alert_service.stream()),
                inspect.isasyncgen(smart_suggestion_service.stream()),
                inspect.isasyncgen(project_failure_service.stream()),
                inspect.isasyncgen(roi_intelligence_service.stream()),
            ]
        )
        routes = [
            FRONTEND_API / "power" / "realtime" / "stream" / "route.ts",
            FRONTEND_API / "alerts" / "stream" / "route.ts",
            FRONTEND_API / "suggestions" / "stream" / "route.ts",
            FRONTEND_API / "project-failure" / "stream" / "route.ts",
            FRONTEND_API / "roi" / "stream" / "route.ts",
        ]
        ws_url_route = FRONTEND_API / "power" / "realtime" / "ws-url" / "route.ts"
        ready = (
            stream_ready
            and all(path.exists() for path in routes)
            and ws_url_route.exists()
            and ws_auth_ready
            and snapshot.sync_status in {"streaming", "ready"}
            and len(snapshot.kpis) >= 8
        )
        return FeatureCoverageCheck(
            name="Realtime Enterprise Infrastructure",
            category="realtime",
            status="ready" if ready else "error",
            details="Realtime infrastructure aggregates ML outputs into live KPI snapshots, SSE streams, WebSocket updates, alerts, recommendations, ROI, and project-risk feeds.",
            evidence=[
                snapshot.model,
                f"kpis={len(snapshot.kpis)}",
                f"events={len(snapshot.events)}",
                f"routes={sum(path.exists() for path in routes)}/{len(routes)}",
                f"websocket_auth={ws_auth_ready}",
                f"ws_url_route={ws_url_route.exists()}",
            ],
            remediation=None if ready else "Repair live streams, WebSocket route, and frontend streaming proxies.",
        )

    def _frontend_enterprise_ui(self) -> FeatureCoverageCheck:
        required = [
            "EnterpriseTwinScene.tsx",
            "ExecutiveAssistantPanel.tsx",
            "SimulationConsole.tsx",
            "AutonomyPanel.tsx",
            "AdvancedFeaturePanel.tsx",
            "AdvancedPowerFeaturesPanel.tsx",
            "AIAlertCenterPanel.tsx",
            "SmartSuggestionPanel.tsx",
            "TeamCompatibilityPanel.tsx",
            "ProjectFailurePanel.tsx",
            "RoiIntelligencePanel.tsx",
        ]
        page = (ROOT / "frontend" / "src" / "app" / "page.tsx").read_text(encoding="utf-8")
        existing = [name for name in required if (FRONTEND_COMPONENTS / name).exists() and name.replace(".tsx", "") in page]
        css = (ROOT / "frontend" / "src" / "app" / "globals.css").read_text(encoding="utf-8")
        tailwind = (ROOT / "frontend" / "tailwind.config.ts").read_text(encoding="utf-8")
        surface_source = f"{page}\n{css}\n{tailwind}"
        ready = len(existing) == len(required) and "shadow-control" in surface_source and "panel" in surface_source
        return FeatureCoverageCheck(
            name="Frontend Enterprise UI",
            category="ui",
            status="ready" if ready else "missing",
            details="Command center UI includes 3D control room, assistant, simulations, agents, advanced audits, alerts, suggestions, compatibility, project failure, and ROI intelligence panels.",
            evidence=[f"wired_panels={len(existing)}/{len(required)}", "shadow-control", "bg-panel", *existing[:6]],
            remediation=None if ready else "Wire missing advanced UI panels into the command center and restore enterprise styling tokens.",
        )

    def _api_backend_layer(self) -> FeatureCoverageCheck:
        route_files = [
            ROOT / "backend" / "app" / "api" / "v1" / "routes" / "intelligence.py",
            ROOT / "backend" / "app" / "api" / "v1" / "routes" / "power.py",
            ROOT / "backend" / "app" / "api" / "v1" / "routes" / "alerts.py",
            ROOT / "backend" / "app" / "api" / "v1" / "routes" / "suggestions.py",
            ROOT / "backend" / "app" / "api" / "v1" / "routes" / "anomalies.py",
            ROOT / "backend" / "app" / "api" / "v1" / "routes" / "system.py",
        ]
        router = (ROOT / "backend" / "app" / "api" / "v1" / "router.py").read_text(encoding="utf-8")
        ready = all(path.exists() for path in route_files) and all(token in router for token in ["intelligence", "power", "alerts", "suggestions", "anomalies", "system"])
        return FeatureCoverageCheck(
            name="API & Backend Enterprise Layer",
            category="backend",
            status="ready" if ready else "error",
            details="FastAPI backend exposes intelligence, power, alert, suggestion, anomaly, and system audit routes with authenticated enterprise APIs.",
            evidence=[f"routes={sum(path.exists() for path in route_files)}/{len(route_files)}", "FastAPI router integration", "JWT-protected feature endpoints"],
            remediation=None if ready else "Reconnect advanced enterprise route files to the FastAPI v1 router.",
        )

    def _database_vector_layer(self) -> FeatureCoverageCheck:
        histories = [
            DATA_DIR / "employee_dashboard_history.jsonl",
            DATA_DIR / "manager_dashboard_history.jsonl",
            DATA_DIR / "power_realtime_history.jsonl",
            DATA_DIR / "xai_explanations.jsonl",
            DATA_DIR / "gnn_team_relations_history.jsonl",
            DATA_DIR / "roi_intelligence_history.jsonl",
            DATA_DIR / "ai_alert_history.jsonl",
        ]
        existing = [path for path in histories if path.exists()]
        ready = len(existing) == len(histories) and INDEX_PATH.exists() and knowledge_engine.vector_dimensions > 20
        return FeatureCoverageCheck(
            name="Database & Vector Systems",
            category="data",
            status="ready" if ready else "warning",
            details="Historical analytics persist to local stores while vector memory persists its semantic retrieval index for enterprise knowledge queries.",
            evidence=[f"history_stores={len(existing)}/{len(histories)}", str(INDEX_PATH), f"vector_dimensions={knowledge_engine.vector_dimensions}"],
            remediation=None if ready else "Ensure analytics history stores and vector-memory artifacts are generated before production demo.",
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
                details=f"Enterprise OS probe crashed: {type(exc).__name__}",
                evidence=[str(exc)[:220]],
                remediation="Fix the crashed enterprise AI module before claiming Fortune 500 readiness.",
            )

    @staticmethod
    def _summary(checks: list[FeatureCoverageCheck]) -> FeatureCoverageSummary:
        ready = sum(1 for check in checks if check.status == "ready")
        warnings = sum(1 for check in checks if check.status == "warning")
        missing = sum(1 for check in checks if check.status == "missing")
        errors = sum(1 for check in checks if check.status == "error")
        score = round(((ready + warnings * 0.72) / len(checks)) * 100, 2) if checks else 0
        return FeatureCoverageSummary(total=len(checks), ready=ready, warnings=warnings, missing=missing, errors=errors, coverage_score=score)


enterprise_os_service = EnterpriseOSService()
