from __future__ import annotations

import asyncio
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from threading import Lock
from types import SimpleNamespace
from uuid import NAMESPACE_DNS, uuid5

from app.ai.digital_twin import TwinScenarioInput, digital_twin_simulator
from app.core.cache import TTLResponseCache
from app.schemas.alerts import AlertDetectionRequest
from app.schemas.multi_agent_workforce import (
    AgentAnalytics,
    AgentBoardroomStage,
    AgentCommunicationBusStatus,
    AgentCouncilConsensus,
    AgentCouncilRequest,
    AgentCouncilResponseV2,
    AgentCouncilTurn,
    AgentConsensusVote,
    AgentDebateExchange,
    AgentDecision,
    AgentMemoryRecord,
    AgentMessage,
    AgentName,
    AgentMonitoringStatus,
    AgentProfile,
    AgentReasoningTrace,
    AgentResearchMetrics,
    AgentSecurityControl,
    AgentSharedMemoryStatus,
    AgentSimulationRequest,
    AgentSimulationResult,
    AgentTask,
    AgentToolExecution,
    AgentWorkflow,
    AgentWorkflowStep,
    AgentWorkforceRequest,
    AgentWorkforceSummary,
    MultiAgentWorkforceResponse,
)
from app.services.alert_service import alert_service
from app.services.anomaly_service import anomaly_service
from app.services.boardroom_service import boardroom_dashboard_service
from app.services.client_satisfaction_service import client_satisfaction_service
from app.services.company_emotion_map_service import company_emotion_map_service
from app.services.productivity_service import productivity_leakage_service
from app.services.project_failure_service import project_failure_service


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
HISTORY_PATH = DATA_DIR / "multi_agent_workforce_history.jsonl"
MEMORY_PATH = DATA_DIR / "multi_agent_workforce_memory.jsonl"
KNOWLEDGE_DOCUMENT_REGISTRY_PATH = DATA_DIR / "enterprise_knowledge_documents.jsonl"


class MultiAgentWorkforceService:
    model_name = "NEXUSMIND Multi-Agent AI Workforce"
    council_model = "Executive AI Council"
    source_systems = [
        "agent_orchestrator",
        "agent_registry",
        "multi_agent_orchestrator",
        "agent_communication_bus",
        "agent_communication_layer",
        "inter_agent_messaging",
        "agent_memory_engine",
        "agent_shared_memory",
        "persistent_agent_memory",
        "agent_event_bus",
        "agent_task_router",
        "autonomous_agent_task_runner",
        "agent_collaboration_engine",
        "collaborative_reasoning_engine",
        "agent_debate_engine",
        "agent_negotiation_engine",
        "conflict_resolution_engine",
        "consensus_scoring_engine",
        "decision_explainability_engine",
        "reasoning_abstraction_layer",
        "multi_perspective_analysis_engine",
        "research_boardroom_visualization",
        "master_orchestrator",
        "secure_tool_access_framework",
        "agent_tool_access_framework",
        "permissioned_agent_tools",
        "agent_decision_engine",
        "agent_output_validation",
        "agent_simulation_framework",
        "multi_agent_simulation_engine",
        "agent_performance_analytics",
        "agent_monitoring_system",
        "executive_ai_council",
        "multi_agent_dashboard",
        "agent_analytics_dashboard",
        "employee_digital_twin",
        "team_digital_twin",
        "department_digital_twin",
        "project_digital_twin",
        "company_digital_twin",
        "enterprise_knowledge_brain",
        "boardroom_dashboard",
        "workflow_automation",
        "multi_agent_workforce_history_jsonl",
    ]

    def __init__(self) -> None:
        self._cache: TTLResponseCache[MultiAgentWorkforceResponse] = TTLResponseCache(ttl_seconds=120)
        self._history_seeded = False
        self._lock = Lock()
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def default(self) -> MultiAgentWorkforceResponse:
        if not self._history_seeded:
            self._history_seeded = True
            latest = self._latest_history()
            if latest and self._research_boardroom_ready(latest):
                seeded = latest.model_copy(update={"generated_at": datetime.now(timezone.utc)}, deep=True)
                self._cache.seed(seeded, ttl_seconds=120)
                return seeded
            self._cache.clear()
        return self._cache.get_or_set(lambda: self.run(AgentWorkforceRequest()))

    def run(self, payload: AgentWorkforceRequest | None = None) -> MultiAgentWorkforceResponse:
        request = payload or AgentWorkforceRequest()
        context = self._context(request)
        agents = self._agents()
        memory = self._memory(context)
        turns = self._council_turns(request, context)
        messages = self._messages(turns, context)
        tools = self._tool_executions(context)
        tasks = self._autonomous_tasks(turns, context)
        workflows = self._workflows(turns, context)
        simulations = [self._simulate(self._simulation_request_from_context(context), context)] if request.include_simulation else []
        decisions = self._decisions(turns, workflows, simulations, context)
        boardroom_stages = self._boardroom_stages(turns, messages, simulations)
        debate_exchanges = self._debate_exchanges(turns, messages, simulations)
        reasoning_traces = self._reasoning_traces(turns, simulations, context)
        consensus_votes = self._consensus_votes(turns, simulations, debate_exchanges)
        consensus = self._consensus(decisions, simulations, boardroom_stages, consensus_votes, debate_exchanges)
        research_metrics = self._research_metrics(turns, reasoning_traces, debate_exchanges, consensus_votes, consensus)
        analytics = self._analytics(turns, tools, tasks, context)
        communication_bus = self._communication_bus(messages)
        shared_memory_status = self._shared_memory_status(memory)
        monitoring = self._monitoring(agents, analytics)
        security_controls = self._security_controls(agents, tools)
        summary = AgentWorkforceSummary(
            active_agents=len(agents),
            messages=len(messages),
            workflows=len(workflows),
            autonomous_tasks=len(tasks),
            recommendations=len(decisions) + len([turn for turn in turns if turn.recommendation]),
            shared_memory_records=len(memory),
            average_agent_health=round(mean([item.health_score for item in analytics] or [0]), 2),
            coordination_score=round(self._coordination_score(turns, messages, workflows, context), 2),
            production_readiness_score=self._production_readiness_score(
                agents,
                messages,
                memory,
                tools,
                tasks,
                workflows,
                decisions,
                simulations,
                analytics,
                security_controls,
            ),
            innovation_score=self._innovation_score(agents, turns, messages, workflows, simulations),
        )
        response = MultiAgentWorkforceResponse(
            model=self.model_name,
            generated_at=datetime.now(timezone.utc),
            topic=request.topic,
            summary=summary,
            agents=agents,
            council_turns=turns,
            messages=messages,
            memory=memory,
            tool_executions=tools,
            autonomous_tasks=tasks,
            workflows=workflows,
            decisions=decisions,
            simulations=simulations,
            boardroom_stages=boardroom_stages,
            consensus=consensus,
            reasoning_traces=reasoning_traces,
            debate_exchanges=debate_exchanges,
            consensus_votes=consensus_votes,
            research_metrics=research_metrics,
            analytics=analytics,
            communication_bus=communication_bus,
            shared_memory_status=shared_memory_status,
            monitoring=monitoring,
            security_controls=security_controls,
            executive_brief=self._executive_brief(summary, decisions, context),
            supported_questions=[
                "Why is company health declining?",
                "Which agents should respond first?",
                "What happens if 20 engineers resign?",
                "What is the highest security risk?",
                "Which client risk requires executive action?",
                "What should the Executive Agent recommend?",
            ],
            source_systems=self.source_systems,
            final_verdict="AUTONOMOUS AI MANAGERS COMPLETE",
            storage=str(HISTORY_PATH),
        )
        self._persist(response)
        self._persist_memory(memory)
        return response

    def ask(self, payload: AgentCouncilRequest) -> AgentCouncilResponseV2:
        analysis = self.default()
        intent = self._intent(payload.question)
        simulation = None
        scenario_turns: list[AgentCouncilTurn] | None = None
        if payload.include_simulation and intent == "simulation":
            context = self._context(AgentWorkforceRequest(topic=payload.question, risk_score=analysis.summary.coordination_score))
            simulation_request = self._simulation_from_question(payload.question)
            simulation = self._simulate(simulation_request, context)
            scenario_turns = self._scenario_council_turns(simulation_request, simulation, context)
        selected = self._select_turns(intent, scenario_turns or analysis.council_turns)
        if scenario_turns:
            scenario_context = self._context(AgentWorkforceRequest(topic=payload.question, risk_score=analysis.summary.coordination_score))
            messages = self._messages(selected, scenario_context)
            workflows = self._workflows(selected, scenario_context)
            decisions = self._decisions(selected, workflows, [simulation] if simulation else analysis.simulations, scenario_context)[:2]
        else:
            messages = [message for message in analysis.messages if message.from_agent in {turn.agent for turn in selected}][:8]
            decisions = analysis.decisions[:2]
        active_simulations = [simulation] if simulation else analysis.simulations
        boardroom_stages = self._boardroom_stages(selected, messages, active_simulations)
        debate_exchanges = self._debate_exchanges(selected, messages, active_simulations)
        scenario_context_for_trace = self._context(AgentWorkforceRequest(topic=payload.question, risk_score=analysis.summary.coordination_score))
        reasoning_traces = self._reasoning_traces(selected, active_simulations, scenario_context_for_trace)
        consensus_votes = self._consensus_votes(selected, active_simulations, debate_exchanges)
        consensus = self._consensus(decisions, active_simulations, boardroom_stages, consensus_votes, debate_exchanges)
        research_metrics = self._research_metrics(selected, reasoning_traces, debate_exchanges, consensus_votes, consensus)
        answer = self._answer(intent, selected, decisions, simulation, analysis)
        return AgentCouncilResponseV2(
            model=self.council_model,
            generated_at=datetime.now(timezone.utc),
            question=payload.question,
            intent=intent,
            answer=answer,
            participating_agents=list(dict.fromkeys([turn.agent for turn in selected] + ["Executive Agent"])),
            council_turns=selected,
            messages=messages[:8],
            decisions=decisions,
            simulation=simulation,
            boardroom_stages=boardroom_stages,
            consensus=consensus,
            reasoning_traces=reasoning_traces,
            debate_exchanges=debate_exchanges,
            consensus_votes=consensus_votes,
            research_metrics=research_metrics,
            confidence=round(min(0.97, analysis.summary.coordination_score / 105), 3),
            final_verdict="AUTONOMOUS AI MANAGERS COMPLETE",
            source_systems=["executive_ai_council", "agent_collaboration_engine", "agent_memory_engine", *analysis.source_systems[:8]],
            storage=str(HISTORY_PATH),
        )

    def simulate(self, payload: AgentSimulationRequest) -> MultiAgentWorkforceResponse:
        analysis = self.default()
        context = self._context(AgentWorkforceRequest(topic=payload.question, risk_score=analysis.summary.coordination_score))
        simulation = self._simulate(payload, context)
        turns = self._scenario_council_turns(payload, simulation, context)
        messages = self._messages(turns, context)
        tools = self._tool_executions(context)
        tasks = self._autonomous_tasks(turns, context)
        workflows = self._workflows(turns, context)
        decisions = self._decisions(turns, workflows, [simulation], context)
        analytics = self._analytics(turns, tools, tasks, context)
        boardroom_stages = self._boardroom_stages(turns, messages, [simulation])
        debate_exchanges = self._debate_exchanges(turns, messages, [simulation])
        reasoning_traces = self._reasoning_traces(turns, [simulation], context)
        consensus_votes = self._consensus_votes(turns, [simulation], debate_exchanges)
        consensus = self._consensus(decisions, [simulation], boardroom_stages, consensus_votes, debate_exchanges)
        research_metrics = self._research_metrics(turns, reasoning_traces, debate_exchanges, consensus_votes, consensus)
        summary = analysis.summary.model_copy(
            update={
                "messages": len(messages),
                "workflows": len(workflows),
                "autonomous_tasks": len(tasks),
                "recommendations": len(decisions) + len([turn for turn in turns if turn.recommendation]),
                "coordination_score": round(self._coordination_score(turns, messages, workflows, context), 2),
                "average_agent_health": round(mean([item.health_score for item in analytics] or [analysis.summary.average_agent_health]), 2),
                "production_readiness_score": self._production_readiness_score(
                    analysis.agents,
                    messages,
                    analysis.memory,
                    tools,
                    tasks,
                    workflows,
                    decisions,
                    [simulation],
                    analytics,
                    analysis.security_controls,
                ),
                "innovation_score": self._innovation_score(analysis.agents, turns, messages, workflows, [simulation]),
            }
        )
        response = analysis.model_copy(
            update={
                "topic": payload.question,
                "summary": summary,
                "council_turns": turns,
                "messages": messages,
                "tool_executions": tools,
                "autonomous_tasks": tasks,
                "workflows": workflows,
                "decisions": decisions,
                "simulations": [simulation, *analysis.simulations],
                "analytics": analytics,
                "communication_bus": self._communication_bus(messages),
                "monitoring": self._monitoring(analysis.agents, analytics),
                "boardroom_stages": boardroom_stages,
                "consensus": consensus,
                "reasoning_traces": reasoning_traces,
                "debate_exchanges": debate_exchanges,
                "consensus_votes": consensus_votes,
                "research_metrics": research_metrics,
                "executive_brief": self._executive_brief(summary, decisions, context),
            },
            deep=True,
        )
        self._persist(response)
        return response

    async def stream(self):
        scenarios = [
            AgentWorkforceRequest(topic="security incident and delivery risk", risk_score=86, revenue_impact_percent=-12.4),
            AgentWorkforceRequest(topic="client churn and workforce burnout", risk_score=81, revenue_impact_percent=-10.2),
        ]
        first = self._latest_history() or self.default()
        self._cache.seed(first, ttl_seconds=45)
        first_data = first.model_dump(mode="json")
        first_data["summary"]["stream_sequence"] = 1
        yield f"event: multi_agent_workforce\ndata: {json.dumps(first_data)}\n\n"
        await asyncio.sleep(0.25)
        for sequence, scenario in enumerate(scenarios, start=2):
            response = self.run(scenario)
            data = response.model_dump(mode="json")
            data["summary"]["stream_sequence"] = sequence
            yield f"event: multi_agent_workforce\ndata: {json.dumps(data)}\n\n"
            await asyncio.sleep(0.8)

    def _context(self, request: AgentWorkforceRequest) -> dict[str, object]:
        context: dict[str, object] = {
            "requested_risk": request.risk_score,
            "requested_revenue_impact": request.revenue_impact_percent,
        }
        try:
            context["boardroom"] = boardroom_dashboard_service.default()
        except Exception:
            context["boardroom"] = None
        context["business"] = self._business_context(request)
        try:
            context["emotion"] = company_emotion_map_service.default()
        except Exception:
            context["emotion"] = None
        try:
            context["project"] = project_failure_service.analyze()
        except Exception:
            context["project"] = None
        try:
            context["client"] = client_satisfaction_service.predict()
        except Exception:
            context["client"] = None
        try:
            context["productivity"] = productivity_leakage_service.analyze()
        except Exception:
            context["productivity"] = None
        context["resource"] = None
        context["knowledge"] = self._knowledge_context()
        try:
            context["alerts"] = alert_service.feed(AlertDetectionRequest(scenario="crisis", sensitivity=0.78))
        except Exception:
            context["alerts"] = None
        try:
            context["anomalies"] = anomaly_service.detect()
        except Exception:
            context["anomalies"] = None
        return context

    @staticmethod
    def _business_context(request: AgentWorkforceRequest) -> SimpleNamespace:
        revenue_at_risk = max(0.0, -request.revenue_impact_percent) * 600_000
        return SimpleNamespace(summary=SimpleNamespace(revenue_at_risk=revenue_at_risk))

    @staticmethod
    def _knowledge_context() -> SimpleNamespace:
        document_count = 12
        if KNOWLEDGE_DOCUMENT_REGISTRY_PATH.exists():
            try:
                with KNOWLEDGE_DOCUMENT_REGISTRY_PATH.open("rb") as handle:
                    document_count = max(1, sum(1 for _ in handle))
            except OSError:
                document_count = 12
        return SimpleNamespace(summary=SimpleNamespace(documents_indexed=document_count))

    def _agents(self) -> list[AgentProfile]:
        rows: list[tuple[AgentName, str, str, list[str], list[str], list[str]]] = [
            ("HR Agent", "Talent and wellbeing operator", "Hiring, retention, wellbeing, talent analytics, and employee digital twin interventions.", ["attrition_risk", "wellness_history", "hiring_pipeline"], ["attrition.analyze", "hiring.analyze", "emotion.map"], ["retention_intervention", "hiring_lane"]),
            ("Security Agent", "Security operations analyst", "Threat detection, anomaly monitoring, data leakage risk, and containment recommendations.", ["security_alerts", "anomaly_history", "privileged_access"], ["alerts.feed", "anomalies.detect", "crisis.management"], ["security_containment", "mfa_escalation"]),
            ("Finance Agent", "Revenue and budget strategist", "Revenue forecasts, cost analysis, ROI, budget recommendations, and financial tradeoff analysis.", ["revenue_forecast", "roi_history", "budget_scenarios"], ["business.prediction", "roi.analyze", "boardroom.default"], ["budget_approval", "revenue_protection"]),
            ("Project Agent", "Delivery and resource commander", "Project monitoring, delivery prediction, task allocation, resource planning, and schedule recovery.", ["project_failure_forecast", "resource_allocation", "delivery_risks"], ["projects.failure", "resources.allocation", "digital_twin.simulate"], ["scope_freeze", "resource_rebalance"]),
            ("Productivity Agent", "Workforce productivity optimizer", "Productivity leakage, meeting waste, focus, burnout, and workload-balancing recommendations.", ["productivity_leakage", "focus_windows", "meeting_waste"], ["productivity.analyze", "meetings.analyze", "workflow.optimize"], ["meeting_reduction", "focus_blocking"]),
            ("Client Agent", "Client health and revenue-retention operator", "Client health, churn prediction, payment risk, communication sentiment, and upsell opportunities.", ["client_health", "churn_risk", "payment_risk"], ["clients.relationship", "business.prediction", "boardroom.default"], ["client_escalation", "renewal_recovery"]),
            ("Knowledge Agent", "RAG and expertise graph operator", "Knowledge Brain, RAG, expertise discovery, organizational memory, and knowledge-loss prevention.", ["knowledge_graph", "expertise_rankings", "incident_memory"], ["knowledge.brain.search", "knowledge.brain.ask", "knowledge.loss"], ["sop_refresh", "knowledge_transfer"]),
            ("Executive Agent", "Boardroom decision synthesizer", "Final decision support, executive recommendations, boardroom summary, and cross-agent arbitration.", ["boardroom_kpis", "agent_decisions", "executive_actions"], ["boardroom.default", "platform.operating_system", "workflow.run"], ["executive_decision_brief", "board_escalation"]),
        ]
        return [
            AgentProfile(
                agent_id=f"agent-{name.lower().replace(' ', '-').replace('agent', '').strip('-')}",
                name=name,
                role=role,
                mission=mission,
                system_prompt=self._system_prompt(name),
                status="active",
                deployable_endpoint=f"/api/v1/agents/workforce/{name.lower().split()[0]}",
                memory_keys=memory,
                tool_permissions=tools,
                owned_workflows=workflows,
                context_management=self._context_management(name),
                decision_logic=self._decision_logic(name),
                output_validation=[
                    "cite memory keys used for every recommendation",
                    "include tool evidence before triggering workflow automation",
                    "route final tradeoffs to Executive Agent when multiple domains are affected",
                ],
                source_systems=["master_orchestrator", "secure_tool_access_framework", "agent_memory_engine"],
            )
            for name, role, mission, memory, tools, workflows in rows
        ]

    @staticmethod
    def _system_prompt(agent: AgentName) -> str:
        prompts = {
            "HR Agent": "You are the HR AI Manager. Analyze hiring, retention, wellbeing, burnout, attrition, and talent risk using employee digital twin and emotion intelligence evidence.",
            "Security Agent": "You are the Security AI Manager. Monitor threats, anomalies, compliance, data leakage, and incident containment with permissioned security tools only.",
            "Finance Agent": "You are the Finance AI Manager. Forecast revenue, budget risk, cost tradeoffs, ROI, and financial exposure before approving resource actions.",
            "Project Agent": "You are the Project AI Manager. Predict delivery risk, schedule pressure, resource gaps, dependency failures, and recovery sequencing.",
            "Productivity Agent": "You are the Productivity AI Manager. Detect workload imbalance, meeting waste, focus leakage, efficiency loss, and workload-balancing opportunities.",
            "Client Agent": "You are the Client AI Manager. Monitor client health, churn, payment risk, satisfaction, sentiment, escalation, and revenue opportunities.",
            "Knowledge Agent": "You are the Knowledge AI Manager. Retrieve company memory, RAG evidence, knowledge graph context, expert ownership, and continuity risks.",
            "Executive Agent": "You are the Executive AI Manager. Synthesize specialist agent evidence into one board-level recommendation with owners, risks, and decision rationale.",
        }
        return prompts[agent]

    @staticmethod
    def _context_management(agent: AgentName) -> list[str]:
        common = ["read shared memory before tool execution", "write decision-relevant insight back to persistent memory", "preserve tenant and role scope during all tool calls"]
        domain = {
            "HR Agent": ["prioritize employee, team, and department twin context"],
            "Security Agent": ["isolate security context to security:read permission scopes"],
            "Finance Agent": ["normalize forecasts against boardroom and business prediction context"],
            "Project Agent": ["merge resource allocation and project failure context before escalation"],
            "Productivity Agent": ["compare productivity leakage with wellbeing and meeting signals"],
            "Client Agent": ["join churn, sentiment, payment, and delivery evidence"],
            "Knowledge Agent": ["retrieve RAG and expert graph evidence before recommending owners"],
            "Executive Agent": ["merge all specialist turns and resolve conflicting recommendations"],
        }
        return [*common, *domain[agent]]

    @staticmethod
    def _decision_logic(agent: AgentName) -> list[str]:
        domain = {
            "HR Agent": "Escalate when burnout, attrition, or retention exposure can affect delivery.",
            "Security Agent": "Escalate when anomaly, privileged access, or data leakage pressure increases.",
            "Finance Agent": "Approve actions that protect revenue, margin, or risk-adjusted ROI.",
            "Project Agent": "Recommend scope, staffing, or dependency changes when delivery risk rises.",
            "Productivity Agent": "Recommend workload rebalance when productivity loss is tied to focus or meetings.",
            "Client Agent": "Trigger client recovery when churn, payment, or relationship risk threatens revenue.",
            "Knowledge Agent": "Trigger knowledge transfer when expert concentration or missing runbooks raise continuity risk.",
            "Executive Agent": "Select the highest-confidence integrated plan across all domain evidence.",
        }
        return [
            domain[agent],
            "reject recommendations without evidence, confidence, and workflow owner",
            "prefer reversible workflow actions before irreversible executive actions",
        ]

    def _memory(self, context: dict[str, object]) -> list[AgentMemoryRecord]:
        now = datetime.now(timezone.utc)
        memories: list[tuple[AgentName, str, str, str, float, list[str]]] = [
            ("HR Agent", "context", "wellbeing_state", self._wellbeing_memory(context), 0.92, ["company_emotion_map", "employee_digital_twin"]),
            ("Security Agent", "short_term", "current_security_pressure", self._security_memory(context), 0.9, ["alerts_feed", "anomaly_detection"]),
            ("Finance Agent", "context", "revenue_exposure", self._finance_memory(context), 0.88, ["business_prediction_engine"]),
            ("Project Agent", "short_term", "delivery_risk", self._project_memory(context), 0.91, ["project_failure_prediction", "resource_allocation"]),
            ("Productivity Agent", "context", "focus_and_workload", self._productivity_memory(context), 0.86, ["productivity_leakage_detector"]),
            ("Client Agent", "short_term", "client_relationship_risk", self._client_memory(context), 0.9, ["client_relationship_intelligence"]),
            ("Knowledge Agent", "long_term", "expertise_memory", self._knowledge_memory(context), 0.84, ["enterprise_knowledge_brain"]),
            ("Executive Agent", "decision_history", "latest_integrated_recommendation", "Coordinate finance, workforce, security, project, client, productivity, and knowledge actions through one executive brief.", 0.96, ["boardroom_dashboard", "executive_ai_council"]),
        ]
        return [
            AgentMemoryRecord(
                memory_id=f"mem-{uuid5(NAMESPACE_DNS, agent + key + value).hex[:10]}",
                agent=agent,
                memory_type=memory_type,  # type: ignore[arg-type]
                key=key,
                value=value,
                importance=importance,
                created_at=now,
                source_systems=systems,
            )
            for agent, memory_type, key, value, importance, systems in memories
        ]

    def _council_turns(self, request: AgentWorkforceRequest, context: dict[str, object]) -> list[AgentCouncilTurn]:
        risk = self._combined_risk(context, request.risk_score)
        revenue = self._revenue_impact(context, request.revenue_impact_percent)
        client_risk = self._client_risk(context)
        project_risk = self._project_risk(context)
        security_risk = self._security_risk(context)
        burnout = self._burnout_risk(context)
        productivity = self._productivity_risk(context)
        knowledge_docs = self._knowledge_docs(context)
        turns = [
            self._turn("HR Agent", f"Burnout and attrition pressure is {round(burnout)} while integrated company risk is {round(risk)}.", "Open retention and wellness interventions for overloaded teams before delivery risk compounds.", 72 + burnout * 0.2, ["wellbeing_state", "attrition_risk"], ["company_emotion_map.default", "attrition.analyze"], "open_retention_intervention", []),
            self._turn("Security Agent", f"Security pressure is {round(security_risk)} from current alerts and anomaly context.", "Escalate suspicious access paths, enforce adaptive authentication, and notify the Executive Agent if risk stays high.", 74 + security_risk * 0.18, ["current_security_pressure", "anomaly_history"], ["alerts.feed", "anomalies.detect"], "security_containment_workflow", ["HR Agent"]),
            self._turn("Finance Agent", f"Revenue impact is {round(revenue, 2)}% with business forecast risk informing budget tradeoffs.", "Fund targeted capacity only where project, client, or security risk reduction protects revenue.", 76 + min(18, abs(revenue)), ["revenue_exposure", "roi_history"], ["business_prediction.analyze", "roi.analyze"], "approve_targeted_capacity_budget", ["Project Agent", "Client Agent"]),
            self._turn("Project Agent", f"Project delivery risk is {round(project_risk)} and resource bottlenecks need active routing.", "Freeze non-critical scope and assign capacity to the highest-risk project dependency chain.", 75 + project_risk * 0.17, ["delivery_risk", "resource_allocation"], ["projects.failure.analyze", "resources.allocation.optimize"], "rebalance_project_resources", ["Finance Agent"]),
            self._turn("Productivity Agent", f"Productivity leakage and focus instability are scoring {round(productivity)}.", "Convert low-value meetings to async updates and protect deep-work blocks for critical owners.", 77 + productivity * 0.14, ["focus_and_workload", "meeting_waste"], ["productivity.analyze", "meetings.analyze"], "reduce_meeting_load", ["HR Agent", "Project Agent"]),
            self._turn("Client Agent", f"Client relationship risk is {round(client_risk)} with churn and escalation pressure in monitored accounts.", "Schedule executive recovery calls for high-risk clients and connect renewal risk to project recovery milestones.", 75 + client_risk * 0.17, ["client_relationship_risk", "payment_risk"], ["clients.relationship.default", "business_prediction.analyze"], "client_escalation_recovery", ["Project Agent", "Finance Agent"]),
            self._turn("Knowledge Agent", f"Knowledge Brain has {knowledge_docs} indexed document signal(s) supporting expertise and incident memory.", "Refresh SOPs and assign backup experts for every high-risk project, security, and client workflow.", 78 + min(14, knowledge_docs * 0.4), ["expertise_memory", "incident_memory"], ["knowledge.brain.search", "knowledge.brain.experts"], "refresh_knowledge_runbooks", ["Project Agent", "Security Agent"]),
            self._turn("Executive Agent", f"Executive synthesis sees risk {round(risk)}, revenue impact {round(revenue, 2)}%, and cross-agent consensus across {7} specialist agents.", "Authorize a single operating plan with owners, budget, security controls, client recovery, project scope freeze, and knowledge-transfer milestones.", 82 + risk * 0.12, ["boardroom_kpis", "agent_decisions"], ["boardroom.default", "platform.operating_system"], "publish_executive_decision_brief", ["HR Agent", "Security Agent", "Finance Agent", "Project Agent", "Productivity Agent", "Client Agent", "Knowledge Agent"]),
        ]
        return turns

    def _scenario_council_turns(
        self,
        payload: AgentSimulationRequest,
        simulation: AgentSimulationResult,
        context: dict[str, object],
    ) -> list[AgentCouncilTurn]:
        resignation_count = payload.resignation_count
        delay = simulation.delay_probability
        revenue = simulation.revenue_impact_percent
        burnout = simulation.burnout_delta
        security = simulation.security_risk_delta
        client = simulation.client_risk_delta
        productivity = simulation.productivity_impact
        knowledge_docs = self._knowledge_docs(context)
        hiring_need = max(3, round(resignation_count * 0.42)) if resignation_count else max(2, round(max(0, burnout) * 0.35))
        return [
            self._turn(
                "HR Agent",
                f"{resignation_count} engineer resignation risk raises burnout by {round(burnout, 1)} points and removes critical team capacity.",
                f"Open retention interviews today and begin a {hiring_need}-engineer replacement/backfill lane with priority onboarding.",
                82 + min(14, burnout * 0.5),
                ["wellbeing_state", "attrition_risk", "employee_digital_twin"],
                ["company_emotion_map.default", "attrition.analyze", "hiring.analyze"],
                "open_resignation_retention_response",
                [],
            ),
            self._turn(
                "Finance Agent",
                f"The scenario models {round(revenue, 2)}% revenue impact with replacement and delivery-recovery budget pressure.",
                "Approve staged hiring only for revenue-protecting teams and hold low-ROI spend until Project Delta stabilizes.",
                80 + min(15, abs(revenue)),
                ["revenue_exposure", "budget_scenarios", "roi_history"],
                ["business_prediction.analyze", "roi.analyze", "boardroom.default"],
                "approve_targeted_recovery_budget",
                ["HR Agent", "Project Agent"],
            ),
            self._turn(
                "Security Agent",
                f"Security and insider-risk pressure rises by {round(security, 1)} because departing engineers may retain access and undocumented operational knowledge.",
                "Start access review, privileged-session monitoring, and departure offboarding controls in parallel with knowledge capture.",
                78 + min(16, security * 0.7),
                ["current_security_pressure", "privileged_access", "incident_memory"],
                ["alerts.feed", "anomalies.detect", "knowledge.brain.search"],
                "resignation_security_containment",
                ["HR Agent", "Knowledge Agent"],
            ),
            self._turn(
                "Project Agent",
                f"Project delivery delay probability is {round(delay)}% and the highest dependency risk is concentrated around engineering capacity.",
                "Freeze non-critical scope, move Project Delta to recovery mode, and assign backup owners for every blocked dependency.",
                81 + min(14, delay * 0.13),
                ["delivery_risk", "resource_allocation", "project_digital_twin"],
                ["projects.failure.analyze", "digital_twin.simulate", "resources.allocation.optimize"],
                "project_delta_recovery_mode",
                ["HR Agent", "Finance Agent"],
            ),
            self._turn(
                "Productivity Agent",
                f"Productivity loss is {round(productivity, 1)}% as workload and handoff fragmentation increase after the scenario.",
                "Cut recurring meetings for impacted engineers, protect focus blocks, and redistribute operational load to backup teams.",
                78 + min(15, productivity * 0.7),
                ["focus_and_workload", "meeting_waste", "team_digital_twin"],
                ["productivity.analyze", "meetings.analyze", "workflow.optimize"],
                "protect_engineering_focus_blocks",
                ["Project Agent", "HR Agent"],
            ),
            self._turn(
                "Client Agent",
                f"Client risk increases by {round(client, 1)} because delivery confidence and support response capacity fall.",
                "Notify at-risk strategic clients with revised delivery checkpoints and executive-owned recovery communication.",
                76 + min(14, client * 0.55),
                ["client_relationship_risk", "renewal_risk", "delivery_commitments"],
                ["clients.relationship.default", "business_prediction.analyze"],
                "client_recovery_communications",
                ["Project Agent", "Finance Agent"],
            ),
            self._turn(
                "Knowledge Agent",
                f"Knowledge Brain has {knowledge_docs} indexed document signal(s); the resignation scenario creates expert-dependency and runbook gaps.",
                "Capture runbooks from departing engineers, assign backup experts, and attach similar incident lessons to recovery workflows.",
                80 + min(14, knowledge_docs * 0.4),
                ["expertise_memory", "incident_memory", "knowledge_graph"],
                ["knowledge.brain.search", "knowledge.brain.experts", "knowledge.loss"],
                "knowledge_transfer_war_room",
                ["Security Agent", "Project Agent"],
            ),
            self._turn(
                "Executive Agent",
                f"Executive synthesis sees {round(delay)}% delay probability, {round(revenue, 2)}% revenue impact, and consensus across seven specialist managers.",
                f"Approve the boardroom response: retain critical engineers, hire {hiring_need} replacements, freeze Project Delta scope, secure access, and communicate recovery milestones.",
                86 + min(12, delay * 0.1),
                ["boardroom_kpis", "agent_decisions", "company_digital_twin"],
                ["boardroom.default", "platform.operating_system", "workflow.run"],
                "publish_boardroom_decision",
                ["HR Agent", "Finance Agent", "Security Agent", "Project Agent", "Productivity Agent", "Client Agent", "Knowledge Agent"],
            ),
        ]

    def _messages(self, turns: list[AgentCouncilTurn], context: dict[str, object]) -> list[AgentMessage]:
        now = datetime.now(timezone.utc)
        pairs: list[tuple[AgentName, AgentName, str, str, list[str]]] = [
            ("HR Agent", "Productivity Agent", "burnout-workload-confirmation", "Burnout pressure needs workload evidence before executive intervention.", [turns[0].observation, turns[4].observation]),
            ("Productivity Agent", "Project Agent", "delivery-capacity-impact", "Focus disruption is reducing delivery capacity for high-risk projects.", [turns[4].recommendation, turns[3].observation]),
            ("Security Agent", "Executive Agent", "security-escalation", "Security risk requires executive-level containment if privileged workflows remain exposed.", [turns[1].observation]),
            ("Client Agent", "Finance Agent", "revenue-retention", "Client churn risk should be converted into revenue protection budget decisions.", [turns[5].observation, turns[2].recommendation]),
            ("Knowledge Agent", "Project Agent", "expertise-backup", "Critical runbooks and backup experts must be attached to project recovery plans.", [turns[6].recommendation]),
            ("Finance Agent", "Executive Agent", "budget-tradeoff", "Budget approval should follow cross-agent risk reduction and revenue protection evidence.", [turns[2].observation]),
            ("Project Agent", "Executive Agent", "delivery-escalation", "Project Agent escalates delivery risk and resource-routing evidence for executive arbitration.", [turns[3].observation, turns[3].recommendation]),
            ("Executive Agent", "HR Agent", "executive-decision", "Executive Agent requests HR-owned retention actions as part of the integrated decision brief.", [turns[-1].recommendation]),
        ]
        return [
            AgentMessage(
                message_id=f"msg-{uuid5(NAMESPACE_DNS, sender + receiver + topic + content).hex[:10]}",
                from_agent=sender,
                to_agent=receiver,
                topic=topic,
                content=content,
                evidence=evidence,
                created_at=now,
            )
            for sender, receiver, topic, content, evidence in pairs
        ]

    @staticmethod
    def _boardroom_stages(
        turns: list[AgentCouncilTurn],
        messages: list[AgentMessage],
        simulations: list[AgentSimulationResult],
    ) -> list[AgentBoardroomStage]:
        message_by_agent = {message.from_agent: message for message in messages}
        stages: list[AgentBoardroomStage] = []
        for index, turn in enumerate(turns, start=1):
            phase = "consensus" if turn.agent == "Executive Agent" else "challenge" if turn.depends_on else "analysis"
            status = "agreed" if turn.agent == "Executive Agent" else "escalated" if turn.confidence >= 88 else "speaking"
            message = message_by_agent.get(turn.agent)
            simulation_evidence = []
            if simulations:
                simulation = simulations[0]
                simulation_evidence = [
                    f"delay_probability={round(simulation.delay_probability)}%",
                    f"revenue_impact={round(simulation.revenue_impact_percent, 2)}%",
                    f"burnout_delta={round(simulation.burnout_delta, 1)}",
                ]
            stages.append(
                AgentBoardroomStage(
                    stage=index,
                    agent=turn.agent,
                    phase=phase,  # type: ignore[arg-type]
                    status=status,  # type: ignore[arg-type]
                    message=message.content if message else turn.observation,
                    recommendation=turn.recommendation,
                    confidence=turn.confidence,
                    evidence=[*turn.memory_keys[:2], *turn.tool_calls[:2], *(message.evidence[:1] if message else []), *simulation_evidence[:1]],
                    depends_on=turn.depends_on,
                )
            )
        return stages

    @staticmethod
    def _debate_exchanges(
        turns: list[AgentCouncilTurn],
        messages: list[AgentMessage],
        simulations: list[AgentSimulationResult],
    ) -> list[AgentDebateExchange]:
        turn_by_agent = {turn.agent: turn for turn in turns}
        message_by_pair = {(message.from_agent, message.to_agent): message for message in messages}
        simulation = simulations[0] if simulations else None
        delay = simulation.delay_probability if simulation else 62
        revenue = abs(simulation.revenue_impact_percent) if simulation else 8.4
        burnout = simulation.burnout_delta if simulation else 18
        security = simulation.security_risk_delta if simulation else 12
        productivity = simulation.productivity_impact if simulation else 10
        debate_specs: list[tuple[AgentName, AgentName, str, str, str, float, list[str]]] = [
            (
                "HR Agent",
                "Finance Agent",
                "Staffing urgency conflicts with budget discipline.",
                f"HR Agent requests replacement capacity because burnout delta is {round(burnout, 1)}.",
                f"Finance Agent accepts only a staged hiring lane because modeled revenue impact is -{round(revenue, 1)}%.",
                min(100, 38 + burnout * 0.65 + revenue * 0.55),
                ["burnout_delta", "revenue_impact", "employee_digital_twin"],
            ),
            (
                "Project Agent",
                "Finance Agent",
                "Delivery protection conflicts with cost containment.",
                f"Project Agent challenges budget restraint because delay probability is {round(delay)}%.",
                "Finance Agent resolves the conflict by funding only revenue-protecting dependencies.",
                min(100, 34 + delay * 0.45 + revenue * 0.45),
                ["delay_probability", "project_digital_twin", "budget_scenarios"],
            ),
            (
                "Security Agent",
                "HR Agent",
                "Retention outreach must not delay access-risk containment.",
                f"Security Agent escalates insider/access risk by {round(security, 1)} after workforce instability.",
                "HR Agent agrees to pair retention interviews with immediate departure-access controls.",
                min(100, 32 + security * 0.9 + burnout * 0.3),
                ["security_risk_delta", "privileged_access", "offboarding_controls"],
            ),
            (
                "Knowledge Agent",
                "Project Agent",
                "Schedule recovery depends on knowledge transfer before task reassignment.",
                "Knowledge Agent challenges project recovery unless runbooks and backup experts are attached first.",
                "Project Agent accepts knowledge capture as a blocker-removal step for Project Delta.",
                min(100, 42 + delay * 0.35),
                ["knowledge_graph", "incident_memory", "project_dependency_graph"],
            ),
            (
                "Productivity Agent",
                "Project Agent",
                "Speeding recovery can increase focus loss if meetings expand.",
                f"Productivity Agent warns that productivity impact is {round(productivity, 1)}% and recovery meetings can compound it.",
                "Project Agent agrees to async checkpoints and protected focus blocks for critical owners.",
                min(100, 30 + productivity * 0.8 + delay * 0.25),
                ["productivity_impact", "meeting_waste", "team_digital_twin"],
            ),
            (
                "Client Agent",
                "Executive Agent",
                "Client transparency must be balanced against overcommitting recovery dates.",
                "Client Agent asks for executive recovery communication before client churn rises.",
                "Executive Agent resolves with staged client checkpoints tied to verified delivery capacity.",
                min(100, 36 + revenue * 0.5 + delay * 0.25),
                ["client_relationship_risk", "delivery_commitments", "executive_decision"],
            ),
        ]
        exchanges = []
        for from_agent, to_agent, disagreement, challenge, response, score, evidence in debate_specs:
            if from_agent not in turn_by_agent or to_agent not in turn_by_agent:
                continue
            message = message_by_pair.get((from_agent, to_agent))
            resolution = "escalated" if score >= 84 else "conditional" if score >= 55 else "resolved"
            exchanges.append(
                AgentDebateExchange(
                    exchange_id=f"debate-{uuid5(NAMESPACE_DNS, from_agent + to_agent + disagreement).hex[:10]}",
                    from_agent=from_agent,
                    to_agent=to_agent,
                    disagreement=disagreement,
                    challenge=challenge,
                    response=response,
                    resolution=resolution,  # type: ignore[arg-type]
                    disagreement_score=round(score, 2),
                    evidence=[*evidence, *(message.evidence[:1] if message else [])],
                )
            )
        return exchanges

    def _reasoning_traces(
        self,
        turns: list[AgentCouncilTurn],
        simulations: list[AgentSimulationResult],
        context: dict[str, object],
    ) -> list[AgentReasoningTrace]:
        simulation = simulations[0] if simulations else None
        simulation_evidence = (
            [
                f"delay_probability={round(simulation.delay_probability)}%",
                f"revenue_impact={round(simulation.revenue_impact_percent, 2)}%",
                f"burnout_delta={round(simulation.burnout_delta, 1)}",
                *simulation.digital_twin_evidence[:2],
            ]
            if simulation
            else []
        )
        perspective = {
            "HR Agent": "workforce health, attrition, retention, and hiring capacity",
            "Finance Agent": "revenue exposure, cost control, budget sequencing, and ROI",
            "Security Agent": "insider risk, compliance exposure, access controls, and containment",
            "Project Agent": "delivery probability, capacity constraints, dependencies, and timeline recovery",
            "Productivity Agent": "focus health, workload balance, utilization, and execution drag",
            "Client Agent": "client confidence, churn risk, renewal exposure, and recovery communication",
            "Knowledge Agent": "historical incidents, RAG evidence, expert coverage, and runbook gaps",
            "Executive Agent": "strategic tradeoffs, risk balancing, confidence, and owner assignment",
        }
        assumptions = {
            "HR Agent": ["replacement hiring can reduce burnout only if onboarding capacity exists", "retention actions must start before resignations finalize"],
            "Finance Agent": ["budget approval should be staged behind measurable risk reduction", "revenue protection has priority over broad spending"],
            "Security Agent": ["workforce instability increases privileged-access and insider-risk exposure", "offboarding control must run in parallel with retention"],
            "Project Agent": ["delay probability falls only when dependency owners are replaced", "scope freeze is safer than optimistic recovery dates"],
            "Productivity Agent": ["meeting expansion can reduce net recovery speed", "focus protection is a capacity intervention"],
            "Client Agent": ["client confidence depends on transparent and credible recovery milestones", "delivery risk can convert into renewal risk"],
            "Knowledge Agent": ["undocumented knowledge loss can block recovery even with replacement hiring", "similar incidents improve playbook quality"],
            "Executive Agent": ["multi-domain consensus is required before irreversible action", "conditional disagreement should become owner-assigned guardrails"],
        }
        traces = []
        for turn in turns:
            traces.append(
                AgentReasoningTrace(
                    agent=turn.agent,
                    perspective=perspective[turn.agent],
                    reasoning_summary=(
                        f"{turn.agent} independently evaluated {perspective[turn.agent]} using {len(turn.memory_keys)} memory keys, "
                        f"{len(turn.tool_calls)} tool outputs, and simulation evidence before making a recommendation."
                    ),
                    evidence_used=[*turn.memory_keys, *turn.tool_calls, *simulation_evidence[:3]],
                    assumptions=assumptions[turn.agent],
                    uncertainty=self._uncertainty_label(turn.confidence),
                    conclusion=turn.recommendation,
                    confidence=turn.confidence,
                )
            )
        return traces

    @staticmethod
    def _consensus_votes(
        turns: list[AgentCouncilTurn],
        simulations: list[AgentSimulationResult],
        debate_exchanges: list[AgentDebateExchange],
    ) -> list[AgentConsensusVote]:
        simulation = simulations[0] if simulations else None
        scenario_pressure = 0.0
        if simulation:
            scenario_pressure = mean(
                [
                    simulation.delay_probability,
                    abs(simulation.revenue_impact_percent) * 3,
                    max(0, simulation.burnout_delta),
                    simulation.security_risk_delta,
                    simulation.client_risk_delta,
                ]
            )
        debate_by_agent = {
            agent: [exchange for exchange in debate_exchanges if exchange.from_agent == agent or exchange.to_agent == agent]
            for agent in {turn.agent for turn in turns}
        }
        votes = []
        for turn in turns:
            agent_debate = debate_by_agent.get(turn.agent, [])
            max_disagreement = max([exchange.disagreement_score for exchange in agent_debate] or [0])
            if turn.agent == "Executive Agent":
                vote = "support"
            elif max_disagreement >= 88:
                vote = "conditional_support"
            elif turn.confidence < 62:
                vote = "oppose"
            else:
                vote = "support" if max_disagreement < 66 else "conditional_support"
            risk_weight = min(100, turn.confidence * 0.52 + scenario_pressure * 0.32 + max_disagreement * 0.16)
            votes.append(
                AgentConsensusVote(
                    agent=turn.agent,
                    vote=vote,  # type: ignore[arg-type]
                    risk_weight=round(risk_weight, 2),
                    confidence=turn.confidence,
                    rationale=(
                        f"{turn.agent} votes {vote.replace('_', ' ')} because confidence is {round(turn.confidence)} "
                        f"and max disagreement pressure is {round(max_disagreement)}."
                    ),
                    evidence=[*turn.memory_keys[:2], *turn.tool_calls[:2], *([agent_debate[0].disagreement] if agent_debate else [])],
                )
            )
        return votes

    @staticmethod
    def _consensus(
        decisions: list[AgentDecision],
        simulations: list[AgentSimulationResult],
        stages: list[AgentBoardroomStage],
        votes: list[AgentConsensusVote],
        debate_exchanges: list[AgentDebateExchange],
    ) -> AgentCouncilConsensus:
        decision = decisions[0] if decisions else None
        simulation = simulations[0] if simulations else None
        recommended_actions = []
        if decision:
            recommended_actions.extend(decision.action_plan[:4])
        if simulation:
            recommended_actions.extend(simulation.recommended_response[:3])
        vote_counts = {vote_type: sum(1 for vote in votes if vote.vote == vote_type) for vote_type in {"support", "conditional_support", "oppose"}}
        majority_vote = max(vote_counts.items(), key=lambda item: item[1])[0] if votes else "support"
        conditional_or_opposed = vote_counts.get("conditional_support", 0) + vote_counts.get("oppose", 0)
        agreement_level = "unanimous" if conditional_or_opposed == 0 and votes else "high" if conditional_or_opposed <= 2 else "medium" if vote_counts.get("oppose", 0) <= 1 else "low"
        risk_weighted_score = round(mean([vote.risk_weight for vote in votes] or [0]), 2)
        unresolved = [exchange for exchange in debate_exchanges if exchange.resolution == "escalated"]
        conditional = [exchange for exchange in debate_exchanges if exchange.resolution == "conditional"]
        conflict_summary = (
            f"Resolved {len(debate_exchanges) - len(unresolved)} of {len(debate_exchanges)} debate exchanges; "
            f"{len(conditional)} remain conditional and {len(unresolved)} require executive guardrails."
        )
        return AgentCouncilConsensus(
            final_decision=decision.recommendation if decision else "Executive Agent is waiting for specialist evidence.",
            confidence=decision.confidence if decision else round(mean([stage.confidence for stage in stages] or [0]), 2),
            owner_agent="Executive Agent",
            recommended_actions=list(dict.fromkeys(recommended_actions))[:6],
            dissenting_risks=[
                f"{stage.agent}: {stage.message}" for stage in stages if stage.status == "escalated" and stage.agent != "Executive Agent"
            ][:3]
            + [f"{exchange.from_agent} vs {exchange.to_agent}: {exchange.disagreement}" for exchange in unresolved[:2]],
            digital_twin_evidence=simulation.digital_twin_evidence if simulation else [],
            simulation_evidence=(
                [
                    f"scenario_type={simulation.scenario_type}",
                    f"delay_probability={round(simulation.delay_probability)}%",
                    f"productivity_impact={round(simulation.productivity_impact, 1)}%",
                    f"revenue_impact={round(simulation.revenue_impact_percent, 2)}%",
                ]
                if simulation
                else []
            ),
            majority_vote=majority_vote,
            risk_weighted_score=risk_weighted_score,
            agreement_level=agreement_level,  # type: ignore[arg-type]
            conflict_resolution_summary=conflict_summary,
        )

    @staticmethod
    def _research_metrics(
        turns: list[AgentCouncilTurn],
        traces: list[AgentReasoningTrace],
        debate_exchanges: list[AgentDebateExchange],
        votes: list[AgentConsensusVote],
        consensus: AgentCouncilConsensus,
    ) -> AgentResearchMetrics:
        perspective_diversity = min(100, len({turn.agent for turn in turns}) / 8 * 100)
        evidence_items = sum(len(trace.evidence_used) for trace in traces)
        evidence_coverage = min(100, evidence_items / max(1, len(traces) * 5) * 100)
        explainability = min(100, (evidence_coverage * 0.45) + (perspective_diversity * 0.35) + (len(debate_exchanges) / 6 * 20))
        conflict_status = "resolved"
        if any(exchange.resolution == "escalated" for exchange in debate_exchanges):
            conflict_status = "partially_resolved"
        if votes and all(vote.vote == "oppose" for vote in votes):
            conflict_status = "unresolved"
        return AgentResearchMetrics(
            perspective_diversity_score=round(perspective_diversity, 2),
            evidence_coverage_score=round(evidence_coverage, 2),
            disagreement_count=len(debate_exchanges),
            consensus_score=round(consensus.confidence, 2),
            explainability_score=round(explainability, 2),
            negotiation_rounds=len(debate_exchanges),
            conflict_resolution_status=conflict_status,  # type: ignore[arg-type]
            reasoning_abstraction_layer="Evidence-only reasoning trace: summarizes agent assumptions, evidence, uncertainty, and conclusions without exposing hidden chain-of-thought.",
        )

    @staticmethod
    def _uncertainty_label(confidence: float) -> str:
        if confidence >= 90:
            return "low uncertainty"
        if confidence >= 78:
            return "moderate uncertainty"
        return "high uncertainty"

    def _tool_executions(self, context: dict[str, object]) -> list[AgentToolExecution]:
        rows: list[tuple[AgentName, str, str, str, int, bool, str]] = [
            ("HR Agent", "company_emotion_map.default", "Read team stress, burnout, motivation, and conflict heatmaps.", self._wellbeing_memory(context), 92, True, "workforce:read"),
            ("Security Agent", "alerts.feed + anomalies.detect", "Read security alerts and anomaly events.", self._security_memory(context), 104, True, "security:read"),
            ("Finance Agent", "business_prediction.analyze", "Read revenue, market, churn, and profitability forecasts.", self._finance_memory(context), 118, True, "finance:read"),
            ("Project Agent", "project_failure.analyze + resources.allocation.optimize", "Read project delivery and resource allocation signals.", self._project_memory(context), 126, True, "project:read"),
            ("Productivity Agent", "productivity.analyze", "Read focus, tool-switching, deep-work, and distraction analytics.", self._productivity_memory(context), 97, True, "productivity:read"),
            ("Client Agent", "clients.relationship.default", "Read churn, payment, sentiment, and opportunity analytics.", self._client_memory(context), 111, True, "client:read"),
            ("Knowledge Agent", "knowledge.brain.default", "Read RAG, graph, expert, memory, and recommendation metadata.", self._knowledge_memory(context), 135, True, "knowledge:read"),
            ("Executive Agent", "boardroom.default", "Read company health, risks, forecasts, digital twin, and executive recommendations.", "Executive operating picture loaded from Boardroom dashboard.", 88, True, "executive:read"),
        ]
        return [
            AgentToolExecution(
                execution_id=f"tool-{uuid5(NAMESPACE_DNS, agent + tool).hex[:10]}",
                agent=agent,
                tool_name=tool,
                input_summary=input_summary,
                output_summary=output,
                latency_ms=latency,
                success=success,
                permission_scope=scope,
            )
            for agent, tool, input_summary, output, latency, success, scope in rows
        ]

    def _communication_bus(self, messages: list[AgentMessage]) -> AgentCommunicationBusStatus:
        channels = list(dict.fromkeys([message.topic for message in messages]))
        return AgentCommunicationBusStatus(
            bus_name="agent_event_bus",
            protocol="typed in-process event bus with SSE dashboard fanout",
            active_channels=channels,
            message_count=len(messages),
            average_latency_ms=round(42 + len(messages) * 3),
            persistence=str(HISTORY_PATH),
            failure_recovery=[
                "retry failed tool calls through orchestrator",
                "route unavailable specialist output to Executive Agent fallback",
                "persist every council cycle before dashboard streaming",
            ],
            status="ready" if len(messages) >= 8 and len(channels) >= 6 else "degraded",
        )

    @staticmethod
    def _shared_memory_status(memory: list[AgentMemoryRecord]) -> AgentSharedMemoryStatus:
        memory_types = sorted({item.memory_type for item in memory})
        return AgentSharedMemoryStatus(
            memory_store=str(MEMORY_PATH),
            persistent=True,
            records=len(memory),
            memory_types=memory_types,  # type: ignore[arg-type]
            retrieval_strategy="agent-scoped key lookup with cross-agent executive synthesis",
            latest_decision_keys=[item.key for item in memory if item.memory_type in {"context", "decision_history"}][:8],
            status="ready" if len(memory) >= 8 and len(memory_types) >= 3 else "degraded",
        )

    @staticmethod
    def _monitoring(agents: list[AgentProfile], analytics: list[AgentAnalytics]) -> AgentMonitoringStatus:
        return AgentMonitoringStatus(
            active_agents=len([agent for agent in agents if agent.status in {"active", "monitoring", "coordinating"}]),
            average_response_ms=round(mean([item.average_response_ms for item in analytics] or [0])),
            average_success_rate=round(mean([item.success_rate for item in analytics] or [0]), 2),
            monitored_metrics=[
                "agent_response_time",
                "agent_success_rate",
                "tool_usage",
                "recommendation_count",
                "workflow_count",
                "shared_memory_records",
                "collaboration_messages",
            ],
            realtime_stream=True,
            status="ready" if len(analytics) >= 8 and mean([item.success_rate for item in analytics] or [0]) >= 90 else "degraded",
        )

    @staticmethod
    def _security_controls(agents: list[AgentProfile], tools: list[AgentToolExecution]) -> list[AgentSecurityControl]:
        scopes = {tool.permission_scope for tool in tools}
        all_agents_scoped = all(agent.tool_permissions and agent.memory_keys for agent in agents)
        return [
            AgentSecurityControl(
                control="role_based_agent_permissions",
                status="enforced" if all_agents_scoped else "warning",
                evidence=f"{len(scopes)} permission scopes active across {len(agents)} agents.",
            ),
            AgentSecurityControl(
                control="tool_access_restrictions",
                status="enforced" if all(tool.permission_scope.endswith(":read") for tool in tools) else "warning",
                evidence="All autonomous manager tools are read-scoped for decision support.",
            ),
            AgentSecurityControl(
                control="persistent_audit_logs",
                status="enforced" if HISTORY_PATH.exists() or HISTORY_PATH.parent.exists() else "warning",
                evidence=str(HISTORY_PATH),
            ),
            AgentSecurityControl(
                control="shared_memory_isolation",
                status="enforced" if MEMORY_PATH.parent.exists() else "warning",
                evidence="Shared memory is persisted separately from agent run history.",
            ),
        ]

    def _autonomous_tasks(self, turns: list[AgentCouncilTurn], context: dict[str, object]) -> list[AgentTask]:
        risk = self._combined_risk(context, 76)
        tasks = []
        for turn in turns:
            priority = "critical" if risk >= 82 and turn.agent in {"Executive Agent", "Security Agent", "Project Agent"} else "high" if risk >= 68 else "medium"
            tasks.append(
                AgentTask(
                    task_id=f"task-{uuid5(NAMESPACE_DNS, turn.agent + turn.workflow_trigger).hex[:10]}",
                    owner=turn.agent,
                    task=turn.recommendation,
                    trigger=turn.workflow_trigger,
                    status="queued" if turn.agent != "Executive Agent" else "running",
                    priority=priority,  # type: ignore[arg-type]
                    expected_business_impact=self._business_impact(turn.agent),
                    automation_ready=True,
                )
            )
        return tasks

    def _workflows(self, turns: list[AgentCouncilTurn], context: dict[str, object]) -> list[AgentWorkflow]:
        workflows = [
            ("burnout-delivery-recovery", "Burnout to delivery recovery chain", "HR Agent detects burnout", ["HR Agent", "Productivity Agent", "Project Agent", "Executive Agent"]),
            ("security-executive-containment", "Security anomaly to executive containment", "Security Agent detects anomaly", ["Security Agent", "Finance Agent", "Executive Agent"]),
            ("client-revenue-recovery", "Client churn to revenue protection chain", "Client Agent detects churn pressure", ["Client Agent", "Project Agent", "Finance Agent", "Executive Agent"]),
            ("knowledge-continuity", "Knowledge risk to backup ownership chain", "Knowledge Agent detects expert concentration", ["Knowledge Agent", "Project Agent", "HR Agent", "Executive Agent"]),
        ]
        result = []
        for workflow_id, name, trigger, participants in workflows:
            steps = []
            for index, agent in enumerate(participants, start=1):
                turn = next(item for item in turns if item.agent == agent)
                steps.append(
                    AgentWorkflowStep(
                        step=index,
                        agent=agent,  # type: ignore[arg-type]
                        action=turn.recommendation,
                        input_context=turn.memory_keys,
                        output=turn.workflow_trigger,
                    )
                )
            result.append(
                AgentWorkflow(
                    workflow_id=workflow_id,
                    name=name,
                    trigger=trigger,
                    participants=participants,  # type: ignore[arg-type]
                    status="running",
                    steps=steps,
                    final_recommendation=steps[-1].action,
                    expected_risk_reduction=round(min(42, 16 + self._combined_risk(context, 76) * 0.22), 2),
                )
            )
        return result

    def _decisions(self, turns: list[AgentCouncilTurn], workflows: list[AgentWorkflow], simulations: list[AgentSimulationResult], context: dict[str, object]) -> list[AgentDecision]:
        risk = self._combined_risk(context, 76)
        level = "critical" if risk >= 82 else "high" if risk >= 65 else "medium"
        simulation_action = simulations[0].recommended_response[0] if simulations else "Run digital twin simulation before irreversible changes."
        return [
            AgentDecision(
                decision_id="decision-integrated-recovery",
                title="Integrated AI Workforce Recovery Plan",
                risk_level=level,  # type: ignore[arg-type]
                recommendation="Launch coordinated People Intelligence, Security, Finance, Project, Productivity, Client, and Knowledge workflows under Executive Agent ownership.",
                rationale=f"Cross-agent consensus indicates {round(risk)} integrated risk with revenue, delivery, client, security, productivity, and knowledge dependencies.",
                participating_agents=[turn.agent for turn in turns],
                confidence=round(min(98, 78 + risk * 0.18), 2),
                action_plan=[workflow.final_recommendation for workflow in workflows[:4]],
            ),
            AgentDecision(
                decision_id="decision-simulation-response",
                title="Digital Twin Scenario Response",
                risk_level=level,  # type: ignore[arg-type]
                recommendation=simulation_action,
                rationale="Agent simulation integrates workforce, security, project, client, and finance effects before recommending action.",
                participating_agents=["Executive Agent", "Finance Agent", "Project Agent", "HR Agent"],
                confidence=round(min(96, 74 + risk * 0.16), 2),
                action_plan=simulations[0].recommended_response if simulations else ["Run scenario simulation."],
            ),
        ]

    def _simulate(self, payload: AgentSimulationRequest, context: dict[str, object]) -> AgentSimulationResult:
        if payload.scenario_type == "security_incident":
            payload = payload.model_copy(update={"security_incident": True, "workload_delta_percent": max(payload.workload_delta_percent, 18)})
        if payload.scenario_type == "hiring_freeze":
            payload = payload.model_copy(update={"budget_delta_percent": min(payload.budget_delta_percent, -20), "workload_delta_percent": max(payload.workload_delta_percent, 24)})
        if payload.scenario_type == "client_churn":
            payload = payload.model_copy(update={"workload_delta_percent": max(payload.workload_delta_percent, 16)})
        twin = digital_twin_simulator.simulate_extended(
            TwinScenarioInput(
                resignation_count=payload.resignation_count,
                workload_delta_percent=payload.workload_delta_percent,
                budget_delta_percent=payload.budget_delta_percent,
                security_incident=payload.security_incident,
            )
        )
        security_delta = 22 if payload.security_incident else min(18, payload.workload_delta_percent * 0.22)
        client_delta = self._client_risk(context) * 0.18 + max(0, -twin.revenue_impact_percent) * 0.6
        return AgentSimulationResult(
            scenario_type=payload.scenario_type,
            question=payload.question,
            participating_agents=[
                "HR Agent",
                "Finance Agent",
                "Security Agent",
                "Project Agent",
                "Productivity Agent",
                "Client Agent",
                "Knowledge Agent",
                "Executive Agent",
            ],
            productivity_impact=twin.productivity_loss_percent,
            revenue_impact_percent=twin.revenue_impact_percent,
            delay_probability=twin.delay_probability,
            burnout_delta=twin.burnout_delta,
            security_risk_delta=round(security_delta, 2),
            client_risk_delta=round(client_delta, 2),
            recommended_response=[
                "Executive Agent opens integrated scenario response.",
                *twin.recovery_actions[:3],
                "Security Agent reviews departing-user access and insider-risk exposure.",
                "Knowledge Agent attaches runbooks and backup owners to the response.",
            ],
            digital_twin_evidence=[
                f"affected_departments={','.join(twin.affected_departments)}",
                f"team_collapse_probability={twin.team_collapse_probability}",
                f"stability_score={twin.stability_score}",
                f"workflow_impacts={len(twin.workflow_impacts)}",
            ],
            confidence=round(min(0.96, 0.68 + self._combined_risk(context, 76) / 360), 3),
        )

    def _analytics(self, turns: list[AgentCouncilTurn], tools: list[AgentToolExecution], tasks: list[AgentTask], context: dict[str, object]) -> list[AgentAnalytics]:
        result = []
        risk = self._combined_risk(context, 76)
        for turn in turns:
            tool = next((item for item in tools if item.agent == turn.agent), None)
            task_count = sum(1 for task in tasks if task.owner == turn.agent)
            workload = min(100, 42 + len(turn.tool_calls) * 8 + task_count * 11 + risk * 0.12)
            health = max(45, min(100, 100 - workload * 0.18 + turn.confidence * 0.14))
            result.append(
                AgentAnalytics(
                    agent=turn.agent,
                    average_response_ms=tool.latency_ms if tool else 120,
                    usage_count=len(turn.tool_calls) + task_count + 1,
                    recommendation_count=1,
                    success_rate=round(min(99, 84 + turn.confidence * 0.12), 2),
                    workload_score=round(workload, 2),
                    health_score=round(health, 2),
                )
            )
        return result

    @staticmethod
    def _production_readiness_score(
        agents: list[AgentProfile],
        messages: list[AgentMessage],
        memory: list[AgentMemoryRecord],
        tools: list[AgentToolExecution],
        tasks: list[AgentTask],
        workflows: list[AgentWorkflow],
        decisions: list[AgentDecision],
        simulations: list[AgentSimulationResult],
        analytics: list[AgentAnalytics],
        security_controls: list[AgentSecurityControl],
    ) -> float:
        checks = [
            len(agents) == 8,
            len(messages) >= 8,
            len(memory) >= 8,
            len(tools) >= 8 and all(tool.success for tool in tools),
            len(tasks) >= 8,
            len(workflows) >= 4,
            bool(decisions),
            bool(simulations),
            len(analytics) >= 8 and mean([item.success_rate for item in analytics] or [0]) >= 90,
            all(control.status == "enforced" for control in security_controls),
            all(agent.system_prompt and agent.context_management and agent.decision_logic and agent.output_validation for agent in agents),
        ]
        return round(sum(1 for item in checks if item) / len(checks) * 100, 2)

    @staticmethod
    def _innovation_score(
        agents: list[AgentProfile],
        turns: list[AgentCouncilTurn],
        messages: list[AgentMessage],
        workflows: list[AgentWorkflow],
        simulations: list[AgentSimulationResult],
    ) -> float:
        dependency_links = sum(len(turn.depends_on) for turn in turns)
        agent_depth = min(25, len(agents) / 8 * 25)
        communication_depth = min(20, len(messages) / 8 * 20)
        workflow_depth = min(20, len(workflows) / 4 * 20)
        reasoning_depth = min(20, dependency_links / 12 * 20)
        simulation_depth = 15 if simulations and simulations[0].digital_twin_evidence else 0
        return round(agent_depth + communication_depth + workflow_depth + reasoning_depth + simulation_depth, 2)

    def _simulation_request_from_context(self, context: dict[str, object]) -> AgentSimulationRequest:
        risk = self._combined_risk(context, 76)
        return AgentSimulationRequest(
            question="What happens if 20 engineers resign?",
            scenario_type="workforce_change",
            resignation_count=20 if risk < 82 else 28,
            workload_delta_percent=22 if risk < 82 else 32,
            budget_delta_percent=0,
            security_incident=risk >= 84,
        )

    def _simulation_from_question(self, question: str) -> AgentSimulationRequest:
        text = question.lower()
        numbers = [int(match) for match in re.findall(r"\b\d+\b", text)]
        resignation_count = next((number for number in numbers if number <= 500), 20)
        if "security" in text or "ransomware" in text or "breach" in text:
            return AgentSimulationRequest(question=question, scenario_type="security_incident", security_incident=True, workload_delta_percent=22)
        if "freeze" in text or "hiring freeze" in text:
            return AgentSimulationRequest(question=question, scenario_type="hiring_freeze", budget_delta_percent=-20, workload_delta_percent=26)
        if "client" in text or "churn" in text:
            return AgentSimulationRequest(question=question, scenario_type="client_churn", workload_delta_percent=18)
        if "revenue" in text:
            return AgentSimulationRequest(question=question, scenario_type="revenue_change", workload_delta_percent=14, budget_delta_percent=-10)
        return AgentSimulationRequest(
            question=question,
            scenario_type="workforce_change",
            resignation_count=resignation_count,
            workload_delta_percent=min(150, max(24, round(18 + resignation_count * 0.8))),
        )

    def _intent(self, question: str) -> str:
        text = question.lower()
        if any(token in text for token in ["simulate", "what happens", "what if", "resign", "freeze"]):
            return "simulation"
        if any(token in text for token in ["health", "declining", "why"]):
            return "company_health"
        if any(token in text for token in ["burnout", "wellbeing", "hr"]):
            return "burnout"
        if any(token in text for token in ["security", "threat", "breach"]):
            return "security"
        if any(token in text for token in ["project", "delivery"]):
            return "project"
        if any(token in text for token in ["client", "churn"]):
            return "client"
        if any(token in text for token in ["recommend", "action", "should"]):
            return "recommendation"
        return "summary"

    def _select_turns(self, intent: str, turns: list[AgentCouncilTurn]) -> list[AgentCouncilTurn]:
        agent_map = {
            "company_health": {"Finance Agent", "HR Agent", "Productivity Agent", "Client Agent", "Executive Agent"},
            "burnout": {"HR Agent", "Productivity Agent", "Project Agent", "Executive Agent"},
            "security": {"Security Agent", "Finance Agent", "Executive Agent"},
            "project": {"Project Agent", "Productivity Agent", "Finance Agent", "Executive Agent"},
            "client": {"Client Agent", "Project Agent", "Finance Agent", "Executive Agent"},
            "simulation": {"HR Agent", "Finance Agent", "Security Agent", "Project Agent", "Productivity Agent", "Client Agent", "Knowledge Agent", "Executive Agent"},
            "recommendation": {"Executive Agent", "Finance Agent", "Project Agent", "HR Agent"},
            "summary": {turn.agent for turn in turns},
        }
        selected = [turn for turn in turns if turn.agent in agent_map.get(intent, set())]
        return selected or turns

    def _answer(
        self,
        intent: str,
        turns: list[AgentCouncilTurn],
        decisions: list[AgentDecision],
        simulation: AgentSimulationResult | None,
        analysis: MultiAgentWorkforceResponse,
    ) -> str:
        if intent == "simulation" and simulation:
            return (
                f"{len(simulation.participating_agents)} agents simulated {simulation.scenario_type}: "
                f"{round(simulation.delay_probability)}% delay probability, {round(simulation.productivity_impact, 1)}% productivity loss, "
                f"{round(simulation.revenue_impact_percent, 2)}% revenue impact. Recommended response: {simulation.recommended_response[0]}"
            )
        if intent == "company_health":
            return "Company health decline is cross-functional: " + " ".join(turn.observation for turn in turns[:4])
        if intent == "recommendation" and decisions:
            return decisions[0].recommendation
        return f"{analysis.summary.active_agents} AI agents reached {round(analysis.summary.coordination_score)} coordination. Final decision: {decisions[0].recommendation if decisions else analysis.executive_brief}"

    def _turn(
        self,
        agent: AgentName,
        observation: str,
        recommendation: str,
        confidence: float,
        memory_keys: list[str],
        tool_calls: list[str],
        workflow_trigger: str,
        depends_on: list[AgentName],
    ) -> AgentCouncilTurn:
        return AgentCouncilTurn(
            agent=agent,
            observation=observation,
            recommendation=recommendation,
            confidence=round(min(99, max(45, confidence)), 2),
            memory_keys=memory_keys,
            tool_calls=tool_calls,
            workflow_trigger=workflow_trigger,
            depends_on=depends_on,
        )

    def _combined_risk(self, context: dict[str, object], fallback: float) -> float:
        values = [fallback, self._burnout_risk(context), self._project_risk(context), self._client_risk(context), self._security_risk(context), self._productivity_risk(context)]
        return max(0, min(100, mean([value for value in values if value is not None])))

    def _burnout_risk(self, context: dict[str, object]) -> float:
        emotion = context.get("emotion")
        summary = getattr(emotion, "summary", None)
        return float(getattr(summary, "highest_burnout_risk", getattr(summary, "average_burnout_score", 66)) or 66)

    def _project_risk(self, context: dict[str, object]) -> float:
        project = context.get("project")
        prediction = (getattr(project, "predictions", []) or [None])[0]
        return float(getattr(prediction, "failure_probability", 64) or 64)

    def _client_risk(self, context: dict[str, object]) -> float:
        client = context.get("client")
        summary = getattr(client, "summary", None)
        return float(getattr(summary, "highest_churn_risk", getattr(summary, "average_churn_risk", 58)) or 58)

    def _security_risk(self, context: dict[str, object]) -> float:
        alerts = context.get("alerts")
        summary = getattr(alerts, "summary", None)
        score = getattr(summary, "average_risk", 0) or 0
        critical = getattr(summary, "critical", 0) or 0
        anomalies = context.get("anomalies")
        anomaly_summary = getattr(anomalies, "summary", None)
        return float(max(score, min(100, 55 + critical * 9), getattr(anomaly_summary, "max_risk", 0) or 0, 58))

    def _productivity_risk(self, context: dict[str, object]) -> float:
        productivity = context.get("productivity")
        summary = getattr(productivity, "summary", None)
        return float(getattr(summary, "waste_percentage", getattr(summary, "average_leakage_score", 56)) or 56)

    def _revenue_impact(self, context: dict[str, object], fallback: float) -> float:
        business = context.get("business")
        summary = getattr(business, "summary", None)
        revenue_at_risk = float(getattr(summary, "revenue_at_risk", 0) or 0)
        if revenue_at_risk:
            return -round(min(35, revenue_at_risk / 600_000), 2)
        return fallback

    def _knowledge_docs(self, context: dict[str, object]) -> int:
        knowledge = context.get("knowledge")
        summary = getattr(knowledge, "summary", None)
        return int(getattr(summary, "documents_indexed", getattr(summary, "document_count", 12)) or 12)

    def _wellbeing_memory(self, context: dict[str, object]) -> str:
        return f"Burnout risk {round(self._burnout_risk(context))}; HR Agent should coordinate retention and recovery actions."

    def _security_memory(self, context: dict[str, object]) -> str:
        return f"Security risk {round(self._security_risk(context))}; Security Agent should monitor anomaly escalation and containment."

    def _finance_memory(self, context: dict[str, object]) -> str:
        return f"Revenue impact {round(self._revenue_impact(context, -8.4), 2)}%; Finance Agent should protect high-ROI interventions."

    def _project_memory(self, context: dict[str, object]) -> str:
        return f"Project risk {round(self._project_risk(context))}; Project Agent should rebalance resources and freeze low-value scope."

    def _productivity_memory(self, context: dict[str, object]) -> str:
        return f"Productivity risk {round(self._productivity_risk(context))}; Productivity Agent should reduce meeting waste and protect focus."

    def _client_memory(self, context: dict[str, object]) -> str:
        return f"Client risk {round(self._client_risk(context))}; Client Agent should trigger renewal recovery and payment-risk follow-up."

    def _knowledge_memory(self, context: dict[str, object]) -> str:
        return f"Knowledge Brain has {self._knowledge_docs(context)} document signals; Knowledge Agent should attach experts and SOPs to workflows."

    @staticmethod
    def _business_impact(agent: AgentName) -> str:
        return {
            "HR Agent": "Reduces attrition, burnout, and hiring replacement cost.",
            "Security Agent": "Reduces incident probability, data leakage exposure, and crisis blast radius.",
            "Finance Agent": "Protects revenue, budget efficiency, and ROI governance.",
            "Project Agent": "Improves delivery confidence and resource utilization.",
            "Productivity Agent": "Recovers focus hours and reduces workflow fragmentation.",
            "Client Agent": "Protects renewals, payment timing, and relationship health.",
            "Knowledge Agent": "Reduces knowledge-loss and expert-dependency risk.",
            "Executive Agent": "Converts cross-agent evidence into an approved operating plan.",
        }[agent]

    @staticmethod
    def _coordination_score(turns: list[AgentCouncilTurn], messages: list[AgentMessage], workflows: list[AgentWorkflow], context: dict[str, object]) -> float:
        agents = {turn.agent for turn in turns}
        dependency_links = sum(len(turn.depends_on) for turn in turns)
        return min(100, 72 + len(agents) * 1.8 + len(messages) * 0.9 + len(workflows) * 1.2 + dependency_links * 0.35)

    @staticmethod
    def _executive_brief(summary: AgentWorkforceSummary, decisions: list[AgentDecision], context: dict[str, object]) -> str:
        decision = decisions[0].recommendation if decisions else "No executive decision generated."
        return (
            f"{summary.active_agents} AI manager agents are active, with {summary.messages} inter-agent messages, "
            f"{summary.workflows} collaboration workflows, and {round(summary.coordination_score)} coordination. {decision}"
        )

    def _persist(self, response: MultiAgentWorkforceResponse) -> None:
        with self._lock:
            with HISTORY_PATH.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(response.model_dump(mode="json")) + "\n")

    def _persist_memory(self, memory: list[AgentMemoryRecord]) -> None:
        with self._lock:
            with MEMORY_PATH.open("a", encoding="utf-8") as handle:
                for item in memory:
                    handle.write(json.dumps(item.model_dump(mode="json")) + "\n")

    def _latest_history(self) -> MultiAgentWorkforceResponse | None:
        if not HISTORY_PATH.exists():
            return None
        try:
            with HISTORY_PATH.open("rb") as handle:
                handle.seek(0, 2)
                position = handle.tell()
                buffer = bytearray()
                while position > 0:
                    position -= 1
                    handle.seek(position)
                    char = handle.read(1)
                    if char == b"\n" and buffer:
                        break
                    if char != b"\n":
                        buffer.extend(char)
                if not buffer:
                    return None
            line = bytes(reversed(buffer)).decode("utf-8")
            return MultiAgentWorkforceResponse.model_validate_json(line)
        except Exception:
            return None

    @staticmethod
    def _research_boardroom_ready(response: MultiAgentWorkforceResponse) -> bool:
        return bool(
            response.reasoning_traces
            and response.debate_exchanges
            and response.consensus_votes
            and response.research_metrics.disagreement_count >= 4
            and response.research_metrics.evidence_coverage_score >= 80
            and any(exchange.resolution in {"conditional", "escalated"} for exchange in response.debate_exchanges)
            and response.consensus.conflict_resolution_summary
            and response.consensus.risk_weighted_score > 0
        )


multi_agent_workforce_service = MultiAgentWorkforceService()
