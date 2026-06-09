from dataclasses import asdict
from datetime import datetime, timezone

from app.ai.burnout_model import BurnoutFeatures, burnout_model
from app.ai.digital_twin import FORECAST_MODELS, TwinScenarioInput, digital_twin_simulator
from app.ai.agent_orchestrator import agent_orchestrator
from app.ai.knowledge_engine import knowledge_engine
from app.ai.model_registry import model_registry
from app.ai.enterprise_models import enterprise_model_registry
from app.ai.security_analyzer import security_analyzer
from app.schemas.intelligence import (
    AgentCouncilResponse,
    BurnoutSignal,
    BurnoutPredictionRequest,
    BurnoutPredictionResponse,
    DigitalTwinSnapshotResponse,
    ExecutiveDirective,
    IntelligenceOverview,
    KnowledgeAnswer,
    ModelValidationResponse,
    OrgBrainResponse,
    OrgGraphEdge,
    OrgGraphNode,
    SecurityEvent,
    SecurityAnalysisRequest,
    SecurityAnalysisResponse,
    ScenarioDecisionSuiteResponse,
    ScenarioSimulationRequest,
    ScenarioSimulationResponse,
    SimulationRequest,
    SimulationResponse,
    SimulationScenario,
    WorkflowOptimizationRequest,
    WorkflowOptimizationResponse,
)


class IntelligenceService:
    def get_overview(self) -> IntelligenceOverview:
        engineering_score = burnout_model.predict_score(
            BurnoutFeatures(
                overtime_hours=16,
                meeting_hours=22,
                sentiment_score=-0.22,
                task_completion_ratio=0.78,
                absence_days=3,
            )
        )
        collapse = digital_twin_simulator.simulate_extended(
            TwinScenarioInput(
                resignation_count=18,
                workload_delta_percent=24,
                budget_delta_percent=8,
                security_incident=True,
            )
        )

        return IntelligenceOverview(
            burnout_signals=[
                BurnoutSignal(
                    department="Engineering",
                    burnout=engineering_score,
                    stress=82,
                    attrition=46,
                    meeting_load=88,
                    recommendation="Move release-critical work away from two overloaded squads.",
                ),
                BurnoutSignal(
                    department="Customer Success",
                    burnout=58,
                    stress=63,
                    attrition=31,
                    meeting_load=74,
                    recommendation="Reduce escalation rotations and add recovery windows.",
                ),
                BurnoutSignal(
                    department="Finance",
                    burnout=34,
                    stress=41,
                    attrition=18,
                    meeting_load=52,
                    recommendation="Maintain current workload distribution.",
                ),
                BurnoutSignal(
                    department="Sales",
                    burnout=49,
                    stress=57,
                    attrition=27,
                    meeting_load=66,
                    recommendation="Coach managers on late-stage deal pressure.",
                ),
            ],
            security_events=[
                SecurityEvent(
                    id="sec-001",
                    title="Privileged session anomaly",
                    actor="finance-admin-07",
                    threat_score=81,
                    status="contained",
                    response="Step-up authentication enforced and session replay queued.",
                ),
                SecurityEvent(
                    id="sec-002",
                    title="Unusual export pattern",
                    actor="ops-analyst-14",
                    threat_score=64,
                    status="investigating",
                    response="Data loss policy tightened for customer datasets.",
                ),
                SecurityEvent(
                    id="sec-003",
                    title="Lateral movement signature",
                    actor="unknown-service-token",
                    threat_score=72,
                    status="isolated",
                    response="Token rotation initiated for production automation.",
                ),
            ],
            simulations=[
                SimulationScenario(
                    id="sim-collapse",
                    scenario="18 resignations + 24% workload surge + security incident",
                    revenue_impact=f"{collapse.revenue_impact_percent}%",
                    delay_probability=collapse.delay_probability,
                    burnout_delta=collapse.burnout_delta,
                    recovery_plan=" ".join(collapse.recovery_actions[:2]),
                ),
                SimulationScenario(
                    id="sim-budget",
                    scenario="Budget increase + focused hiring sprint",
                    revenue_impact="+3.8%",
                    delay_probability=22,
                    burnout_delta=-11,
                    recovery_plan="Prioritize platform reliability, hiring, and manager enablement.",
                ),
            ],
            executive_directives=[
                ExecutiveDirective(
                    command="Show highest-risk department",
                    answer="Engineering is highest risk with elevated burnout, meeting load, and delivery pressure.",
                    confidence=93,
                    action="Open Engineering recovery protocol",
                ),
                ExecutiveDirective(
                    command="Simulate company collapse",
                    answer="The current worst-case scenario creates 67% delay probability and negative revenue impact.",
                    confidence=89,
                    action="Launch Shadow Company simulation",
                ),
                ExecutiveDirective(
                    command="Contain security risk",
                    answer="Finance privileged sessions are contained; token rotation remains the highest-priority action.",
                    confidence=91,
                    action="Escalate to Security Agent",
                ),
            ],
            agent_council=agent_orchestrator.run_council(
                topic="Engineering burnout and delivery risk",
                risk_score=engineering_score,
                revenue_impact=collapse.revenue_impact_percent,
            ),
            org_brain=self.get_org_brain(),
        )

    def predict_burnout(self, payload: BurnoutPredictionRequest) -> BurnoutPredictionResponse:
        features = BurnoutFeatures(
            overtime_hours=payload.overtime_hours,
            meeting_hours=payload.meeting_hours,
            sentiment_score=payload.sentiment_score,
            task_completion_ratio=payload.task_completion_ratio,
            absence_days=payload.absence_days,
        )
        burnout = burnout_model.predict_score(features)
        learned_probability = model_registry.predict_burnout_probability(features)
        model_probabilities = enterprise_model_registry.predict(features)
        resignation = burnout_model.predict_resignation_probability(features)
        productivity_drop = burnout_model.predict_productivity_drop_probability(features)
        stress = min(100, round(burnout * 0.72 + payload.meeting_hours * 1.1 + max(0, -payload.sentiment_score) * 12))
        recommendation = "Maintain current operating rhythm."
        if burnout >= 70:
            recommendation = "Immediately rebalance workload, reduce meetings, and schedule manager intervention."
        elif burnout >= 45:
            recommendation = "Reduce meeting load and monitor delivery velocity for the next two weeks."
        return BurnoutPredictionResponse(
            department=payload.department,
            burnout_score=burnout,
            stress_score=stress,
            resignation_probability=max(resignation, round(model_probabilities["ensemble"] * 0.82, 2)),
            productivity_drop_probability=productivity_drop,
            recommendation=recommendation,
            model_probabilities=model_probabilities | {"legacy_gradient_boosting": learned_probability},
        )

    def validate_models(self) -> ModelValidationResponse:
        sample = BurnoutFeatures(
            overtime_hours=17,
            meeting_hours=23,
            sentiment_score=-0.35,
            task_completion_ratio=0.7,
            absence_days=4,
        )
        return ModelValidationResponse(
            available=enterprise_model_registry.available,
            metrics=enterprise_model_registry.metrics(),
            prediction_sample=enterprise_model_registry.predict(sample),
        )

    def simulate(self, payload: SimulationRequest) -> SimulationResponse:
        scenario = TwinScenarioInput(
            resignation_count=payload.resignation_count,
            workload_delta_percent=payload.workload_delta_percent,
            budget_delta_percent=payload.budget_delta_percent,
            security_incident=payload.security_incident,
        )
        outcome = digital_twin_simulator.simulate_extended(scenario)
        monte_carlo = digital_twin_simulator.simulate_monte_carlo(scenario)
        recovery = "Maintain current operating plan."
        if outcome.delay_probability >= 60:
            recovery = "Freeze non-essential scope, rebalance staffing, and isolate incident response from delivery teams."
        elif outcome.delay_probability >= 35:
            recovery = "Add targeted capacity and reduce meeting load before the next milestone."
        return SimulationResponse(
            delay_probability=outcome.delay_probability,
            burnout_delta=outcome.burnout_delta,
            revenue_impact_percent=outcome.revenue_impact_percent,
            stability_score=outcome.stability_score,
            recovery_plan=recovery,
            productivity_loss_percent=outcome.productivity_loss_percent,
            team_collapse_probability=outcome.team_collapse_probability,
            affected_departments=outcome.affected_departments,
            workflow_impacts=outcome.workflow_impacts,
            recovery_actions=outcome.recovery_actions,
            risk_propagation_path=[
                "Employee capacity loss",
                "Team workload pressure",
                "Project timeline delay",
                "Client satisfaction decline",
                "Revenue impact",
            ],
            forecast_models=FORECAST_MODELS,
            source_systems=[
                "digital_twin",
                "attrition_prediction",
                "productivity_forecasting",
                "financial_roi_intelligence",
                "project_failure_prediction",
                "client_satisfaction_ai",
                "scenario_simulation_engine",
                "impact_engine",
            ],
            monte_carlo=asdict(monte_carlo),
        )

    def digital_twin_snapshot(self) -> DigitalTwinSnapshotResponse:
        snapshot = digital_twin_simulator.snapshot()
        return DigitalTwinSnapshotResponse(
            model="NEXUSMIND Company Digital Twin",
            generated_at=datetime.now(timezone.utc),
            employees=snapshot["employees"],
            teams=snapshot["teams"],
            departments=snapshot["departments"],
            projects=snapshot["projects"],
            resources=snapshot["resources"],
            workflows=snapshot["workflows"],
            operations=snapshot["operations"],
            graph_edges=snapshot["graph_edges"],
            forecast_models=snapshot["forecast_models"],
            supported_scenarios=snapshot["supported_scenarios"],
            baseline=snapshot["baseline"],
            stress_case=snapshot["stress_case"],
            source_systems=snapshot["source_systems"],
        )

    def simulate_enterprise_scenario(self, payload: ScenarioSimulationRequest) -> ScenarioSimulationResponse:
        result = digital_twin_simulator.simulate_enterprise_scenario(
            scenario_type=payload.scenario_type,
            resignation_count=payload.resignation_count,
            seniority=payload.seniority,
            project_name=payload.project_name,
            deadline_months=payload.deadline_months,
            freeze_months=payload.freeze_months,
            source_team=payload.source_team,
            target_team=payload.target_team,
            budget_cut_percent=payload.budget_cut_percent,
            workload_delta_percent=payload.workload_delta_percent,
            meeting_reduction_percent=payload.meeting_reduction_percent,
        )
        return ScenarioSimulationResponse(
            model="NEXUSMIND Enterprise Scenario Simulation & Decision Engine",
            generated_at=datetime.now(timezone.utc),
            **result,
        )

    def scenario_decision_suite(self) -> ScenarioDecisionSuiteResponse:
        suite = digital_twin_simulator.scenario_decision_suite()
        return ScenarioDecisionSuiteResponse(
            model=str(suite["model"]),
            generated_at=datetime.now(timezone.utc),
            scenarios=[
                ScenarioSimulationResponse(
                    model="NEXUSMIND Enterprise Scenario Simulation & Decision Engine",
                    generated_at=datetime.now(timezone.utc),
                    **scenario,
                )
                for scenario in suite["scenarios"]
                if isinstance(scenario, dict)
            ],
            executive_recommendations=list(suite["executive_recommendations"]),
            decision_readiness_score=int(suite["decision_readiness_score"]),
            forecast_models=list(suite["forecast_models"]),
            source_systems=list(suite["source_systems"]),
        )

    def run_agent_council(self, topic: str = "enterprise risk") -> AgentCouncilResponse:
        return agent_orchestrator.run_council(topic=topic, risk_score=72, revenue_impact=-8.4)

    def query_knowledge(self, question: str) -> KnowledgeAnswer:
        return knowledge_engine.query(question)

    def analyze_security(self, payload: SecurityAnalysisRequest) -> SecurityAnalysisResponse:
        return security_analyzer.analyze(
            failed_logins=payload.failed_logins,
            off_hours_accesses=payload.off_hours_accesses,
            data_export_mb=payload.data_export_mb,
            privileged_actions=payload.privileged_actions,
        )

    def optimize_workflow(self, payload: WorkflowOptimizationRequest) -> WorkflowOptimizationResponse:
        capacity_gain = min(40, payload.overloaded_people * 3 + payload.meeting_hours // 5)
        meeting_reduction = min(payload.meeting_hours, max(2, payload.meeting_hours // 4))
        return WorkflowOptimizationResponse(
            automation_plan=[
                f"Auto-assign {min(payload.open_tasks, payload.overloaded_people * 4)} tasks away from overloaded {payload.team} members.",
                f"Collapse recurring meetings by {meeting_reduction} hours this week.",
                "Create protected execution blocks for critical delivery owners.",
            ],
            expected_capacity_gain_percent=capacity_gain,
            meeting_reduction_hours=meeting_reduction,
        )

    def get_org_brain(self) -> OrgBrainResponse:
        return OrgBrainResponse(
            nodes=[
                OrgGraphNode(id="engineering", label="Engineering", risk=72),
                OrgGraphNode(id="platform", label="Platform", risk=54),
                OrgGraphNode(id="finance", label="Finance", risk=31),
                OrgGraphNode(id="security", label="Security", risk=63),
                OrgGraphNode(id="sales", label="Sales", risk=47),
            ],
            edges=[
                OrgGraphEdge(source="engineering", target="platform", strength=88),
                OrgGraphEdge(source="engineering", target="security", strength=71),
                OrgGraphEdge(source="finance", target="security", strength=64),
                OrgGraphEdge(source="sales", target="engineering", strength=53),
            ],
            bottlenecks=[
                "Engineering is the central delivery dependency for Sales and Platform.",
                "Security reviews are concentrated around two privileged-access owners.",
            ],
            recommendation="Create a platform enablement lane and distribute security review ownership across two more trained operators.",
        )


intelligence_service = IntelligenceService()
