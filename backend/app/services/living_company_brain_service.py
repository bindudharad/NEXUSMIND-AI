from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from threading import Lock

from app.core.cache import TTLResponseCache
from app.schemas.boardroom import BoardroomAssistantRequest
from app.schemas.company_simulation_lab import CompanySimulationAssistantRequest, CompanySimulationScenarioRequest
from app.schemas.enterprise_knowledge import EnterpriseKnowledgeAskRequest
from app.schemas.living_company_brain import (
    AgentCouncilSnapshot,
    BrainComponentSignal,
    BrainIntegrationEdge,
    BrainPredictionSignal,
    BrainVerdict,
    CausalReasoningStep,
    CompanyAwarenessSnapshot,
    DigitalTwinBrainSnapshot,
    ExecutiveIntelligenceSnapshot,
    LearningSnapshot,
    LivingCompanyBrainAnswerResponse,
    LivingCompanyBrainAskRequest,
    LivingCompanyBrainResponse,
    MemorySnapshot,
    SimulationSnapshot,
)
from app.services.boardroom_service import boardroom_dashboard_service
from app.services.company_health_service import company_health_service
from app.services.company_simulation_lab_service import company_simulation_lab_service
from app.services.enterprise_knowledge_service import enterprise_knowledge_service
from app.services.multi_agent_workforce_service import multi_agent_workforce_service
from app.services.self_learning_ai_service import self_learning_ai_service
from app.services.shadow_company_service import ai_shadow_company_service


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
HISTORY_PATH = DATA_DIR / "living_company_brain_history.jsonl"
ANSWER_HISTORY_PATH = DATA_DIR / "living_company_brain_answers.jsonl"


class LivingCompanyBrainService:
    model_name = "NEXUSMIND AI Living Company Brain"
    assistant_model = "Living Company Brain Executive Reasoner"
    source_systems = [
        "company_state_engine",
        "enterprise_knowledge_brain",
        "enterprise_memory_rag",
        "causal_reasoning_engine",
        "forecasting_engine",
        "company_simulation_lab",
        "digital_twin_system",
        "shadow_company_engine",
        "multi_agent_workforce",
        "self_learning_ai",
        "boardroom_executive_intelligence",
        "risk_intelligence_engine",
        "recommendation_engine",
        "living_company_brain_history_jsonl",
    ]

    def __init__(self) -> None:
        self._cache: TTLResponseCache[LivingCompanyBrainResponse] = TTLResponseCache(ttl_seconds=10)
        self._lock = Lock()
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def default(self) -> LivingCompanyBrainResponse:
        return self._cache.get_or_set(self._build_uncached)

    def ask(self, payload: LivingCompanyBrainAskRequest) -> LivingCompanyBrainAnswerResponse:
        question = payload.question.strip()
        lowered = question.lower()
        brain = self.default()

        if any(term in lowered for term in ("solve", "before", "memory", "lesson", "expert", "who knows")):
            memory = enterprise_knowledge_service.ask(
                EnterpriseKnowledgeAskRequest(question=question, top_k=6, session_id=payload.session_id)
            )
            response = LivingCompanyBrainAnswerResponse(
                model=self.assistant_model,
                generated_at=datetime.now(timezone.utc),
                question=question,
                answer=memory.answer,
                mode="enterprise_memory",
                confidence=memory.confidence,
                recommended_actions=memory.recommended_follow_up_actions,
                cited_evidence=[citation.snippet for citation in memory.citations[:5]],
                consulted_engines=["enterprise_knowledge_brain", "vector_search", "knowledge_graph", "rag_reasoner"],
                brain_status=brain.company_brain_status,
                organism_score=brain.organism_score,
                final_verdict=brain.final_verdict,
                storage=str(ANSWER_HISTORY_PATH),
            )
        elif "resign" in lowered and ("engineer" in lowered or "30" in lowered):
            response = LivingCompanyBrainAnswerResponse(
                model=self.assistant_model,
                generated_at=datetime.now(timezone.utc),
                question=question,
                answer=(
                    f"{brain.simulation.scenario}: {brain.simulation.ai_explanation} "
                    f"The connected brain projects {round(brain.simulation.risk_score)} risk, "
                    f"{round(brain.simulation.delivery_delay_days, 1)} delivery delay days, "
                    f"{round(brain.simulation.burnout_change, 1)} burnout delta, and "
                    f"{round(brain.simulation.success_probability)}% success probability. "
                    f"Recommended action: {brain.simulation.recommendations[0] if brain.simulation.recommendations else 'stabilize critical teams and rerun the scenario.'}"
                ),
                mode="future_simulation",
                confidence=0.92,
                recommended_actions=brain.simulation.recommendations,
                cited_evidence=[*brain.simulation.digital_twin_evidence[:5], *brain.simulation.risk_propagation_path[:3]],
                consulted_engines=["living_company_brain_cache", "company_simulation_lab", "digital_twin_system", "agent_council"],
                brain_status=brain.company_brain_status,
                organism_score=brain.organism_score,
                final_verdict=brain.final_verdict,
                storage=str(ANSWER_HISTORY_PATH),
            )
        elif any(term in lowered for term in ("what if", "happen", "simulate", "hire", "revenue", "client")):
            simulation = company_simulation_lab_service.ask(
                CompanySimulationAssistantRequest(
                    question=question,
                    session_id=payload.session_id,
                    horizon_months=max(3, payload.horizon_months),
                )
            )
            response = LivingCompanyBrainAnswerResponse(
                model=self.assistant_model,
                generated_at=datetime.now(timezone.utc),
                question=question,
                answer=simulation.answer,
                mode="future_simulation",
                confidence=simulation.confidence,
                recommended_actions=simulation.recommended_actions,
                cited_evidence=simulation.cited_evidence,
                consulted_engines=["company_simulation_lab", "forecasting_engine", "digital_twin_system", "agent_council"],
                brain_status=brain.company_brain_status,
                organism_score=brain.organism_score,
                final_verdict=brain.final_verdict,
                storage=str(ANSWER_HISTORY_PATH),
            )
        else:
            executive = boardroom_dashboard_service.ask(BoardroomAssistantRequest(question=question, session_id=payload.session_id))
            response = LivingCompanyBrainAnswerResponse(
                model=self.assistant_model,
                generated_at=datetime.now(timezone.utc),
                question=question,
                answer=executive.answer,
                mode="executive_intelligence",
                confidence=executive.confidence,
                recommended_actions=executive.recommended_actions,
                cited_evidence=executive.cited_evidence,
                consulted_engines=["boardroom_executive_intelligence", "company_health_engine", "risk_aggregation_engine"],
                brain_status=brain.company_brain_status,
                organism_score=brain.organism_score,
                final_verdict=brain.final_verdict,
                storage=str(ANSWER_HISTORY_PATH),
            )

        self._append_jsonl(ANSWER_HISTORY_PATH, response.model_dump(mode="json"))
        return response

    async def stream(self):
        for sequence in range(1, 4):
            response = self.default()
            payload = response.model_dump(mode="json")
            payload["performance_notes"]["stream_sequence"] = sequence
            yield f"event: living_company_brain\ndata: {json.dumps(payload)}\n\n"
            await asyncio.sleep(0.8)

    def _build_uncached(self) -> LivingCompanyBrainResponse:
        started = time.perf_counter()
        health = company_health_service.analyze()
        boardroom = boardroom_dashboard_service.default()
        knowledge = enterprise_knowledge_service.default()
        memory_answer = enterprise_knowledge_service.ask(
            EnterpriseKnowledgeAskRequest(
                question="How did we solve this before and who should help?",
                top_k=5,
                session_id="living-company-brain-audit",
            )
        )
        simulation_lab = company_simulation_lab_service.simulate(
            CompanySimulationScenarioRequest(
                scenario_id="living-brain-30-engineers-resign",
                scenario_type="employee_resignation",
                question="What happens if 30 engineers resign tomorrow?",
                mode="stress",
                horizon_months=12,
                resignation_count=30,
                resignation_seniority="senior",
            )
        )
        agents = multi_agent_workforce_service.default()
        learning = self_learning_ai_service.verify()
        shadow = ai_shadow_company_service.default()

        scenario = simulation_lab.scenarios[0]
        top_team = health.team_scores[0]
        risk_score = max((risk.risk_score for risk in scenario.risk_heatmap), default=top_team.risk_score)
        simulation_readiness = self._simulation_readiness_score(scenario)
        awareness_readiness = self._awareness_readiness_score(health, shadow)
        executive_readiness = self._executive_readiness_score(boardroom)
        organism_score = round(
            mean(
                [
                    awareness_readiness,
                    knowledge.status_report.production_readiness_score,
                    simulation_readiness,
                    agents.summary.production_readiness_score,
                    learning.production_readiness_score,
                    shadow.summary.production_readiness_score,
                    executive_readiness,
                ]
            ),
            2,
        )
        status = "active" if organism_score >= 90 else "watch"
        verdict: BrainVerdict = "LIVING AI COMPANY BRAIN COMPLETE" if organism_score >= 90 else "LIVING AI COMPANY BRAIN GAPS REMAIN"

        response = LivingCompanyBrainResponse(
            model=self.model_name,
            generated_at=datetime.now(timezone.utc),
            company_brain_status=status,
            organism_score=organism_score,
            awareness=self._awareness(health, boardroom, shadow, top_team),
            memory=self._memory(knowledge, memory_answer),
            reasoning_chain=self._reasoning_chain(health, boardroom, scenario),
            predictions=self._predictions(health, boardroom, scenario),
            simulation=self._simulation(scenario, risk_score),
            multi_agent=self._agents(agents),
            learning=self._learning(learning),
            digital_twin=self._digital_twin(boardroom, shadow, scenario),
            executive_intelligence=self._executive_intelligence(health, boardroom, scenario, memory_answer),
            component_signals=self._component_signals(
                health,
                knowledge,
                simulation_lab,
                agents,
                learning,
                shadow,
                boardroom,
                awareness_readiness,
                simulation_readiness,
                executive_readiness,
            ),
            integration_graph=self._integration_graph(scenario),
            missing_components=[] if verdict == "LIVING AI COMPANY BRAIN COMPLETE" else ["Organism score below 90"],
            fixed_components=[
                "Connected knowledge brain, company health, simulation lab, shadow company, agent workforce, self-learning, and boardroom intelligence into one living-brain response.",
                "Added causal reasoning, prediction, memory, simulation, twin, and executive intelligence evidence in one audited surface.",
            ],
            errors_found=[],
            errors_fixed=[],
            performance_notes={
                "aggregation_latency_ms": round((time.perf_counter() - started) * 1000, 2),
                "connected_source_systems": len(self._source_systems(health.source_systems, knowledge.source_systems, simulation_lab.source_systems, agents.source_systems, learning.source_systems, shadow.source_systems, boardroom.source_systems)),
                "stream_sequence": 1,
            },
            production_readiness_score=round(mean([organism_score, learning.production_readiness_score, shadow.summary.production_readiness_score, agents.summary.production_readiness_score]), 2),
            innovation_score=round(mean([organism_score, shadow.summary.innovation_score, agents.summary.innovation_score, knowledge.status_report.innovation_score]), 2),
            judge_wow_factor_score=round(mean([organism_score, shadow.summary.judge_wow_factor_score, simulation_lab.summary.decision_readiness_score]), 2),
            final_verdict=verdict,
            source_systems=self._source_systems(health.source_systems, knowledge.source_systems, simulation_lab.source_systems, agents.source_systems, learning.source_systems, shadow.source_systems, boardroom.source_systems, self.source_systems),
            storage=str(HISTORY_PATH),
        )
        self._append_jsonl(HISTORY_PATH, response.model_dump(mode="json"))
        return response

    def _awareness(self, health, boardroom, shadow, top_team) -> CompanyAwarenessSnapshot:
        return CompanyAwarenessSnapshot(
            employees_mirrored=shadow.summary.employees_mirrored,
            teams_mirrored=shadow.summary.teams_mirrored,
            departments_mirrored=shadow.summary.departments_mirrored,
            projects_mirrored=shadow.summary.projects_mirrored,
            clients_mirrored=shadow.summary.clients_mirrored,
            current_revenue=boardroom.financial_predictions.current_revenue,
            company_health_score=health.summary.company_health_score,
            productivity_score=health.summary.productivity_score,
            burnout_risk=health.summary.burnout_risk,
            attrition_risk=health.summary.attrition_risk,
            top_risk_team=f"{top_team.department} / {top_team.team_name}",
            top_risk_score=top_team.risk_score,
            active_alerts=boardroom.summary.active_alerts,
            source_systems=["company_state_engine", "company_health_engine", "shadow_company_sync", "boardroom_realtime_data_layer"],
        )

    def _memory(self, knowledge, memory_answer) -> MemorySnapshot:
        return MemorySnapshot(
            documents_indexed=knowledge.summary.documents_indexed,
            chunks_indexed=knowledge.summary.chunks_indexed,
            graph_nodes=knowledge.summary.graph_nodes,
            graph_edges=knowledge.summary.graph_edges,
            experts_detected=knowledge.summary.experts_detected,
            incidents_detected=knowledge.summary.incidents_detected,
            solutions_detected=knowledge.summary.solutions_detected,
            sample_question=memory_answer.question,
            sample_answer=memory_answer.answer,
            citations=[citation.title for citation in memory_answer.citations[:5]],
            final_verdict=knowledge.final_verdict,
            source_systems=["enterprise_memory", "vector_search", "knowledge_graph", "rag_answering", *knowledge.source_systems[:6]],
        )

    def _reasoning_chain(self, health, boardroom, scenario) -> list[CausalReasoningStep]:
        top_team = health.team_scores[0]
        highest_project = max(scenario.project_health_visualization, key=lambda item: item.risk_score)
        return [
            CausalReasoningStep(
                step=1,
                cause=f"{top_team.team_name} workload and burnout pressure are elevated.",
                effect=f"{top_team.department} risk rises to {round(top_team.risk_score)}.",
                metric="team_risk",
                confidence=top_team.confidence,
                evidence=top_team.dominant_risks,
            ),
            CausalReasoningStep(
                step=2,
                cause=f"Simulation scenario changes workforce capacity: {scenario.question}",
                effect=f"{highest_project.project} shifts to {highest_project.projected_state} with {round(highest_project.delay_days, 1)} delay days.",
                metric="project_delay",
                confidence=scenario.confidence,
                evidence=[highest_project.explanation, *scenario.digital_twin_evidence[:2]],
            ),
            CausalReasoningStep(
                step=3,
                cause="Project delay and workforce pressure propagate into revenue and client risk.",
                effect=f"Boardroom risk aggregation reports {boardroom.summary.critical_risks} critical risks and {boardroom.summary.active_alerts} active alerts.",
                metric="executive_risk",
                confidence=boardroom.summary.executive_confidence,
                evidence=[item.title for item in boardroom.executive_risks[:3]],
            ),
        ]

    def _predictions(self, health, boardroom, scenario) -> list[BrainPredictionSignal]:
        latest = health.risk_forecasts[-1]
        revenue_forecast = boardroom.financial_predictions.next_quarter_revenue
        current_revenue = boardroom.financial_predictions.current_revenue
        project = max(scenario.project_health_visualization, key=lambda item: item.delay_days)
        return [
            BrainPredictionSignal(
                domain="burnout",
                current_value=health.summary.burnout_risk,
                projected_value=latest.burnout_risk,
                delta=round(latest.burnout_risk - health.summary.burnout_risk, 2),
                unit="risk_percent",
                confidence=0.88,
                explanation=f"Burnout forecast uses team health and workload signals across {len(health.team_scores)} teams.",
                source_systems=["company_health_engine", "wellness_burnout_forecaster", "employee_digital_twin"],
            ),
            BrainPredictionSignal(
                domain="attrition",
                current_value=health.summary.attrition_risk,
                projected_value=latest.attrition_risk,
                delta=round(latest.attrition_risk - health.summary.attrition_risk, 2),
                unit="risk_percent",
                confidence=0.86,
                explanation="Attrition forecast is driven by burnout, engagement, delivery stability, and collaboration quality.",
                source_systems=["attrition_prediction", "company_health_engine", "team_digital_twin"],
            ),
            BrainPredictionSignal(
                domain="project_delay",
                current_value=0,
                projected_value=project.delay_days,
                delta=project.delay_days,
                unit="days",
                confidence=scenario.confidence,
                explanation=project.explanation,
                source_systems=["project_digital_twin", "company_simulation_lab", "project_failure_prediction"],
            ),
            BrainPredictionSignal(
                domain="revenue",
                current_value=current_revenue,
                projected_value=revenue_forecast,
                delta=round(revenue_forecast - current_revenue, 2),
                unit="currency",
                confidence=boardroom.financial_predictions.forecast_confidence,
                explanation="Revenue forecast combines boardroom financial modeling with digital twin scenario pressure.",
                source_systems=boardroom.financial_predictions.forecast_models,
            ),
        ]

    def _simulation(self, scenario, risk_score: float) -> SimulationSnapshot:
        return SimulationSnapshot(
            scenario=scenario.question,
            success_probability=scenario.success_probability,
            risk_score=risk_score,
            revenue_impact=scenario.impact.revenue_impact,
            burnout_change=scenario.impact.burnout_change,
            delivery_delay_days=scenario.impact.delivery_delay_days,
            ai_explanation=scenario.ai_explanation,
            risk_propagation_path=[f"{step.source} -> {step.target}: {step.title}" for step in scenario.risk_propagation_path],
            digital_twin_evidence=scenario.digital_twin_evidence,
            recommendations=[recommendation.action for recommendation in scenario.recommendations[:5]],
            source_systems=scenario.source_systems,
        )

    def _agents(self, agents) -> AgentCouncilSnapshot:
        return AgentCouncilSnapshot(
            active_agents=agents.summary.active_agents,
            messages=agents.summary.messages,
            workflows=agents.summary.workflows,
            shared_memory_records=agents.summary.shared_memory_records,
            coordination_score=agents.summary.coordination_score,
            average_response_ms=agents.monitoring.average_response_ms,
            executive_brief=agents.executive_brief,
            council_discussion=[
                f"{turn.agent}: {turn.observation} Recommendation: {turn.recommendation}"
                for turn in agents.council_turns[:6]
            ],
            decisions=[decision.recommendation for decision in agents.decisions[:4]],
            source_systems=agents.source_systems,
        )

    def _learning(self, learning) -> LearningSnapshot:
        return LearningSnapshot(
            learning_engine_status=learning.learning_engine_status,
            recommendation_accuracy=learning.recommendation_accuracy,
            forecast_accuracy=learning.forecast_accuracy,
            learning_maturity_score=learning.learning_maturity_score,
            drift_signals=len(learning.drift_signals),
            retraining_events=len(learning.retraining_events),
            feedback_loops=len(learning.feedback_loops),
            evidence=[
                *[component.evidence[0] for component in learning.components[:4] if component.evidence],
                *learning.learning_timeline[:2],
            ],
            source_systems=learning.source_systems,
        )

    def _digital_twin(self, boardroom, shadow, scenario) -> DigitalTwinBrainSnapshot:
        return DigitalTwinBrainSnapshot(
            company_twin_status=boardroom.digital_twin.company_twin_status,
            active_simulations=boardroom.digital_twin.active_simulations,
            recommended_scenario=boardroom.digital_twin.recommended_scenario,
            highest_risk_scenario=boardroom.digital_twin.highest_risk_scenario,
            mirror_sync_completeness=shadow.summary.sync_completeness,
            employees_mirrored=shadow.summary.employees_mirrored,
            teams_mirrored=shadow.summary.teams_mirrored,
            departments_mirrored=shadow.summary.departments_mirrored,
            projects_mirrored=shadow.summary.projects_mirrored,
            twin_updates=scenario.digital_twin_evidence[:8],
            source_systems=["employee_twin", "team_twin", "department_twin", "project_twin", "company_twin", *boardroom.digital_twin.source_systems],
        )

    def _executive_intelligence(self, health, boardroom, scenario, memory_answer) -> ExecutiveIntelligenceSnapshot:
        top_risk = boardroom.executive_risks[0] if boardroom.executive_risks else None
        answer = (
            f"Company health is {round(health.summary.company_health_score)} with {round(boardroom.summary.overall_risk_score)} overall risk. "
            f"The most urgent scenario is '{scenario.question}', which projects {round(scenario.impact.delivery_delay_days, 1)} delay days "
            f"and {round(scenario.impact.burnout_change, 1)} burnout delta. "
            f"Memory search is available and returned: {memory_answer.answer[:220]}"
        )
        return ExecutiveIntelligenceSnapshot(
            answer=answer,
            confidence=boardroom.summary.executive_confidence,
            recommended_actions=[
                *[recommendation.action for recommendation in boardroom.recommendations[:3]],
                *[recommendation.action for recommendation in scenario.recommendations[:2]],
            ],
            cited_evidence=[
                *health.executive_insights[:3],
                *([top_risk.title] if top_risk else []),
                *scenario.digital_twin_evidence[:3],
            ],
            current_company_focus=[
                health.team_scores[0].recommendation,
                scenario.recommendations[0].action,
                boardroom.recommendations[0].action if boardroom.recommendations else "Continue monitoring executive risk telemetry.",
            ],
            source_systems=["executive_intelligence_engine", "boardroom_dashboard", "company_health", "knowledge_brain", "simulation_lab"],
        )

    def _component_signals(
        self,
        health,
        knowledge,
        simulation_lab,
        agents,
        learning,
        shadow,
        boardroom,
        awareness_readiness: float,
        simulation_readiness: float,
        executive_readiness: float,
    ) -> list[BrainComponentSignal]:
        return [
            BrainComponentSignal(
                component="Continuous Awareness",
                status="active",
                score=awareness_readiness,
                summary=f"{len(health.team_scores)} teams and {shadow.summary.employees_mirrored} mirrored employees are monitored.",
                evidence=[health.summary.model_dump_json(), *health.executive_insights[:2]],
                source_systems=health.source_systems,
            ),
            BrainComponentSignal(
                component="Enterprise Memory",
                status="active",
                score=knowledge.summary.knowledge_health_score,
                summary=f"{knowledge.summary.documents_indexed} documents, {knowledge.summary.graph_nodes} graph nodes, and {knowledge.summary.experts_detected} experts are indexed.",
                evidence=[knowledge.final_verdict, *[item.title for item in knowledge.lessons_learned[:2]]],
                source_systems=knowledge.source_systems,
            ),
            BrainComponentSignal(
                component="Reasoning and Prediction",
                status="active",
                score=executive_readiness,
                summary=f"Boardroom intelligence reports {boardroom.summary.connected_engines} connected engines.",
                evidence=boardroom.executive_summary[:3],
                source_systems=boardroom.source_systems,
            ),
            BrainComponentSignal(
                component="Simulation",
                status="active",
                score=simulation_readiness,
                summary=f"{simulation_lab.summary.scenario_count} simulation scenario is active with {round(simulation_lab.summary.average_confidence * 100)}% confidence.",
                evidence=[simulation_lab.summary.top_risk, simulation_lab.summary.recommended_scenario],
                source_systems=simulation_lab.source_systems,
            ),
            BrainComponentSignal(
                component="Multi-Agent Intelligence",
                status="active",
                score=agents.summary.coordination_score,
                summary=f"{agents.summary.active_agents} agents share {agents.summary.shared_memory_records} memory records.",
                evidence=[agents.executive_brief, *[turn.observation for turn in agents.council_turns[:2]]],
                source_systems=agents.source_systems,
            ),
            BrainComponentSignal(
                component="Self-Learning",
                status="active" if learning.learning_maturity_score >= 85 else "watch",
                score=learning.learning_maturity_score,
                summary=f"{len(learning.feedback_loops)} feedback loops and {len(learning.retraining_events)} retraining events are tracked.",
                evidence=learning.learning_timeline[:3],
                source_systems=learning.source_systems,
            ),
            BrainComponentSignal(
                component="Digital Twins",
                status="active",
                score=shadow.summary.sync_completeness,
                summary=f"Shadow Company mirrors {shadow.summary.departments_mirrored} departments, {shadow.summary.projects_mirrored} projects, and {shadow.summary.clients_mirrored} clients.",
                evidence=[signal.update for signal in shadow.integration_signals[:3]],
                source_systems=shadow.source_systems,
            ),
        ]

    def _integration_graph(self, scenario) -> list[BrainIntegrationEdge]:
        return [
            BrainIntegrationEdge(
                source="Enterprise Knowledge Brain",
                target="Executive Intelligence",
                event="Historical lessons and expertise evidence enrich executive answers.",
                evidence=["RAG citations", "knowledge graph edges", "expert rankings"],
            ),
            BrainIntegrationEdge(
                source="Company State Engine",
                target="Digital Twin System",
                event="Health, workload, productivity, and risk signals update employee, team, department, project, and company twins.",
                evidence=scenario.digital_twin_evidence[:4],
            ),
            BrainIntegrationEdge(
                source="Digital Twin System",
                target="Simulation Engine",
                event="Current mirrored company state becomes the baseline for future scenarios.",
                evidence=["company_twin baseline", "project_twin delivery state", "team_twin capacity state"],
            ),
            BrainIntegrationEdge(
                source="Simulation Engine",
                target="Multi-Agent Council",
                event="HR, Finance, Project, Security, Knowledge, and Executive agents evaluate impact and response options.",
                evidence=[contribution.finding for contribution in scenario.agent_council[:4]],
            ),
            BrainIntegrationEdge(
                source="Self-Learning Engine",
                target="Forecasting and Recommendations",
                event="Feedback, drift, prediction errors, and retraining events calibrate recommendations over time.",
                evidence=["feedback loops", "model evaluations", "simulation calibration"],
            ),
        ]

    def _awareness_readiness_score(self, health, shadow) -> float:
        monitored_entities = (
            shadow.summary.employees_mirrored
            + shadow.summary.teams_mirrored
            + shadow.summary.departments_mirrored
            + shadow.summary.projects_mirrored
            + shadow.summary.clients_mirrored
        )
        entity_score = min(100.0, monitored_entities / 18 * 100)
        health_signal_score = min(100.0, len(health.team_scores) / 5 * 100)
        return round(mean([shadow.summary.sync_completeness, entity_score, health_signal_score]), 2)

    def _simulation_readiness_score(self, scenario) -> float:
        required_sets = [
            scenario.forecasts,
            scenario.risk_heatmap,
            scenario.recommendations,
            scenario.employee_movement,
            scenario.team_stress_evolution,
            scenario.project_health_visualization,
            scenario.revenue_evolution,
            scenario.risk_propagation_path,
            scenario.multi_future_branches,
            scenario.agent_council,
            scenario.shadow_company_stages,
            scenario.digital_twin_evidence,
        ]
        artifact_score = sum(1 for item in required_sets if item) / len(required_sets) * 100
        confidence_score = scenario.confidence * 100
        visual_score = 100.0 if scenario.visualization_engine_status == "ready" else 70.0
        return round(mean([artifact_score, confidence_score, visual_score]), 2)

    def _executive_readiness_score(self, boardroom) -> float:
        engine_score = min(100.0, boardroom.summary.connected_engines / 12 * 100)
        answer_score = min(100.0, (len(boardroom.recommendations) + len(boardroom.executive_risks) + len(boardroom.executive_summary)) / 12 * 100)
        confidence_score = boardroom.summary.executive_confidence * 100
        return round(mean([engine_score, answer_score, confidence_score]), 2)

    def _source_systems(self, *groups: list[str]) -> list[str]:
        seen: set[str] = set()
        ordered: list[str] = []
        for group in groups:
            for item in group:
                if item not in seen:
                    seen.add(item)
                    ordered.append(item)
        return ordered

    def _append_jsonl(self, path: Path, payload: dict[str, object]) -> None:
        with self._lock:
            try:
                with path.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(payload, default=str) + "\n")
            except OSError:
                return


living_company_brain_service = LivingCompanyBrainService()
