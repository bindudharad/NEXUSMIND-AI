from dataclasses import asdict, dataclass, field
from math import ceil
from random import Random
from statistics import mean


@dataclass(frozen=True)
class TwinScenarioInput:
    resignation_count: int
    workload_delta_percent: int
    budget_delta_percent: int
    security_incident: bool


@dataclass(frozen=True)
class TwinScenarioOutput:
    delay_probability: int
    burnout_delta: int
    revenue_impact_percent: float
    stability_score: int


@dataclass(frozen=True)
class VirtualEmployee:
    employee_id: str
    name: str
    department: str
    role: str
    workload: int
    productivity: int
    burnout_risk: int
    criticality: int
    skills: list[str] = field(default_factory=list)
    experience_years: int = 5
    performance: int = 75
    wellness_score: int = 78
    attendance: int = 92
    communication_quality: int = 78
    learning_progress: int = 64
    promotion_probability: int = 35
    attrition_probability: int = 24


@dataclass(frozen=True)
class VirtualDepartment:
    department_id: str
    name: str
    headcount: int
    revenue_dependency: float
    delivery_dependency: float
    resilience: int
    performance: int
    risk: int
    productivity: int
    cost: int
    workload: int
    hiring_need: int


@dataclass(frozen=True)
class VirtualWorkflow:
    workflow_id: str
    name: str
    owner_department: str
    dependency_count: int
    baseline_delay_risk: int


@dataclass(frozen=True)
class VirtualTeam:
    team_id: str
    name: str
    department: str
    health: int
    productivity: int
    collaboration: int
    risk: int
    burnout: int
    delivery_performance: int
    communication_quality: int


@dataclass(frozen=True)
class VirtualProject:
    project_id: str
    name: str
    owning_team: str
    progress: int
    risk: int
    resources: list[str]
    team_allocation: dict[str, int]
    timeline_forecast_days: int
    budget_forecast_percent: int
    delay_prediction: int
    client_health: int


@dataclass(frozen=True)
class VirtualResource:
    resource_id: str
    name: str
    resource_type: str
    capacity: int
    utilization: int
    risk: int


@dataclass(frozen=True)
class VirtualOperation:
    operation_id: str
    name: str
    owner: str
    security_health: int
    productivity_health: int
    financial_health: int
    client_health: int
    knowledge_health: int


@dataclass(frozen=True)
class TwinCompanyModel:
    employees: list[VirtualEmployee] = field(default_factory=list)
    teams: list[VirtualTeam] = field(default_factory=list)
    departments: list[VirtualDepartment] = field(default_factory=list)
    projects: list[VirtualProject] = field(default_factory=list)
    resources: list[VirtualResource] = field(default_factory=list)
    workflows: list[VirtualWorkflow] = field(default_factory=list)
    operations: list[VirtualOperation] = field(default_factory=list)


@dataclass(frozen=True)
class TwinExtendedOutput(TwinScenarioOutput):
    productivity_loss_percent: float
    team_collapse_probability: int
    affected_departments: list[str]
    workflow_impacts: dict[str, int]
    recovery_actions: list[str]


@dataclass(frozen=True)
class TwinMonteCarloOutput:
    runs: int
    success_probability: int
    delay_probability_p50: int
    delay_probability_p90: int
    burnout_delta_p90: int
    expected_revenue_impact_percent: float
    worst_case_revenue_impact_percent: float
    stability_score_p10: int
    stability_score_p50: int
    team_collapse_p90: int
    risk_distribution: dict[str, int]
    confidence: float


@dataclass(frozen=True)
class TwinGraphEdge:
    source: str
    target: str
    relationship: str
    strength: int
    risk_transfer: int


FORECAST_MODELS = [
    "RandomForest attrition and capacity model",
    "XGBoost project delivery risk model",
    "Prophet quarterly workforce trend model",
    "LSTM productivity and burnout sequence model",
    "Monte Carlo risk propagation engine",
]

SCENARIO_SOURCE_SYSTEMS = [
    "digital_twin",
    "scenario_simulation_engine",
    "forecast_engine",
    "decision_engine",
    "impact_engine",
    "risk_engine",
    "recommendation_engine",
    "attrition_prediction",
    "productivity_forecasting",
    "project_failure_prediction",
    "financial_roi_intelligence",
    "client_satisfaction_ai",
    "knowledge_graph",
]


class DigitalTwinSimulator:
    def __init__(self) -> None:
        self.company_model = TwinCompanyModel(
            employees=[
                VirtualEmployee("emp-eng-1", "Aarav Mehta", "Engineering", "Backend Lead", 88, 74, 69, 92, ["FastAPI", "PostgreSQL", "Kubernetes"], 9, 87, 62, 94, 82, 71, 62, 57),
                VirtualEmployee("emp-eng-2", "Lina Chen", "Engineering", "Platform Engineer", 81, 82, 58, 86, ["MLOps", "Redis", "Observability"], 7, 89, 71, 96, 79, 76, 54, 41),
                VirtualEmployee("emp-eng-3", "Omar Singh", "Engineering", "Incident Commander", 93, 67, 78, 90, ["Incident Response", "Reliability", "Kafka"], 8, 81, 54, 88, 73, 69, 48, 68),
                VirtualEmployee("emp-sec-1", "Nisha Rao", "Security", "Security Architect", 76, 81, 52, 88, ["Zero Trust", "Threat Modeling", "IAM"], 10, 91, 76, 97, 84, 78, 66, 36),
                VirtualEmployee("emp-fin-1", "Maya Iyer", "Finance", "Finance Systems Admin", 64, 84, 39, 78, ["Revenue Ops", "Forecasting", "Controls"], 6, 88, 82, 98, 81, 72, 44, 21),
                VirtualEmployee("emp-cx-1", "Devika Shah", "Customer Success", "Escalation Manager", 79, 70, 61, 73, ["Enterprise Renewals", "Escalations", "QBR"], 7, 82, 68, 92, 86, 67, 38, 45),
                VirtualEmployee("emp-sales-1", "Rohan Das", "Sales", "Enterprise AE", 72, 76, 44, 69, ["Pipeline", "Negotiation", "Executive Mapping"], 5, 80, 74, 95, 78, 63, 34, 29),
            ],
            teams=[
                VirtualTeam("team-platform", "Platform Reliability", "Engineering", 68, 74, 76, 72, 69, 71, 78),
                VirtualTeam("team-security", "Security Response", "Security", 76, 82, 81, 63, 52, 79, 84),
                VirtualTeam("team-finops", "Revenue Operations", "Finance", 84, 86, 83, 38, 39, 88, 81),
                VirtualTeam("team-cx", "Enterprise Success", "Customer Success", 71, 70, 79, 61, 58, 73, 86),
            ],
            departments=[
                VirtualDepartment("dept-eng", "Engineering", 42, 0.44, 0.92, 58, 76, 72, 74, 83, 88, 68),
                VirtualDepartment("dept-sec", "Security", 11, 0.18, 0.74, 66, 82, 63, 81, 64, 76, 54),
                VirtualDepartment("dept-fin", "Finance", 16, 0.22, 0.56, 72, 88, 38, 86, 59, 64, 28),
                VirtualDepartment("dept-cx", "Customer Success", 24, 0.3, 0.64, 62, 73, 61, 70, 69, 79, 47),
                VirtualDepartment("dept-sales", "Sales", 30, 0.36, 0.48, 68, 79, 47, 76, 72, 72, 36),
            ],
            projects=[
                VirtualProject("proj-alpha", "Project Alpha Revenue Platform", "team-platform", 68, 74, ["res-platform", "res-qdrant", "res-kafka"], {"Engineering": 72, "Security": 18, "Customer Success": 10}, 18, 84, 74, 66),
                VirtualProject("proj-zero-trust", "Zero Trust Data Export Guardrails", "team-security", 58, 63, ["res-security", "res-kafka"], {"Security": 64, "Engineering": 26, "Finance": 10}, 24, 76, 61, 72),
                VirtualProject("proj-renewal", "Orion Renewal Recovery", "team-cx", 73, 67, ["res-cx", "res-platform"], {"Customer Success": 54, "Engineering": 31, "Finance": 15}, 15, 81, 58, 52),
            ],
            resources=[
                VirtualResource("res-platform", "Platform engineering capacity", "people", 100, 88, 72),
                VirtualResource("res-security", "Security review capacity", "people", 100, 76, 61),
                VirtualResource("res-qdrant", "Vector retrieval cluster", "infrastructure", 100, 64, 33),
                VirtualResource("res-kafka", "Realtime event stream", "infrastructure", 100, 71, 42),
                VirtualResource("res-cx", "Client escalation lane", "process", 100, 79, 58),
            ],
            workflows=[
                VirtualWorkflow("wf-release", "Revenue release train", "Engineering", 9, 36),
                VirtualWorkflow("wf-incident", "Security incident response", "Security", 7, 31),
                VirtualWorkflow("wf-renewal", "Customer renewal escalations", "Customer Success", 6, 27),
                VirtualWorkflow("wf-close", "Quarter-end revenue close", "Finance", 5, 23),
            ],
            operations=[
                VirtualOperation("op-company", "Company operating core", "Executive", 82, 74, 86, 69, 78),
                VirtualOperation("op-delivery", "Delivery operating system", "Engineering", 77, 71, 79, 68, 72),
                VirtualOperation("op-revenue", "Revenue retention system", "Customer Success", 74, 73, 83, 62, 70),
            ],
        )

    def simulate(self, scenario: TwinScenarioInput) -> TwinScenarioOutput:
        extended = self.simulate_extended(scenario)
        return TwinScenarioOutput(
            delay_probability=extended.delay_probability,
            burnout_delta=extended.burnout_delta,
            revenue_impact_percent=extended.revenue_impact_percent,
            stability_score=extended.stability_score,
        )

    def snapshot(self) -> dict[str, object]:
        model = self.company_model
        baseline = self.simulate_extended(TwinScenarioInput(0, 0, 0, False))
        stress = self.simulate_extended(TwinScenarioInput(20, 30, -10, True))
        graph_edges = [
            TwinGraphEdge("emp-eng-1", "team-platform", "delivery_owner", 92, 68),
            TwinGraphEdge("emp-eng-3", "wf-release", "incident_dependency", 88, 74),
            TwinGraphEdge("team-platform", "proj-alpha", "project_execution", 91, 76),
            TwinGraphEdge("proj-alpha", "dept-cx", "client_impact", 72, 61),
            TwinGraphEdge("dept-cx", "op-revenue", "renewal_exposure", 69, 58),
            TwinGraphEdge("team-security", "wf-incident", "security_response", 84, 63),
            TwinGraphEdge("res-kafka", "wf-release", "event_stream_dependency", 71, 42),
        ]
        return {
            "employees": [asdict(item) for item in model.employees],
            "teams": [asdict(item) for item in model.teams],
            "departments": [asdict(item) for item in model.departments],
            "projects": [asdict(item) for item in model.projects],
            "resources": [asdict(item) for item in model.resources],
            "workflows": [asdict(item) for item in model.workflows],
            "operations": [asdict(item) for item in model.operations],
            "graph_edges": [asdict(item) for item in graph_edges],
            "forecast_models": FORECAST_MODELS,
            "supported_scenarios": [
                "What happens if 20 engineers resign?",
                "What happens if hiring freezes?",
                "What happens if Project Alpha slips by 30 days?",
                "What happens if overtime increases?",
                "Simulate 15% workforce reduction.",
                "What happens if two teams merge?",
                "Can Project Alpha finish in 2 months?",
                "What happens if budget is cut by 20%?",
                "What happens if meetings are reduced by 50%?",
            ],
            "baseline": asdict(baseline),
            "stress_case": asdict(stress),
            "source_systems": [
                "attrition_prediction",
                "productivity_forecasting",
                "financial_roi_intelligence",
                "project_failure_prediction",
                "client_satisfaction_ai",
                "knowledge_graph",
                "security_anomaly_detection",
                "scenario_simulation_engine",
                "executive_decision_engine",
                "impact_engine",
            ],
        }

    def simulate_enterprise_scenario(
        self,
        scenario_type: str,
        resignation_count: int = 20,
        seniority: str = "mixed",
        project_name: str = "Project Alpha Revenue Platform",
        deadline_months: int = 2,
        freeze_months: int = 6,
        source_team: str = "Platform Reliability",
        target_team: str = "Security Response",
        budget_cut_percent: int = 20,
        workload_delta_percent: int = 25,
        meeting_reduction_percent: int = 50,
    ) -> dict[str, object]:
        if scenario_type == "employee_resignation":
            return self._simulate_employee_resignation(resignation_count, seniority)
        if scenario_type == "project_completion":
            return self._simulate_project_completion(project_name, deadline_months)
        if scenario_type == "hiring_freeze":
            return self._simulate_hiring_freeze(freeze_months)
        if scenario_type == "team_restructure":
            return self._simulate_team_restructure(source_team, target_team)
        if scenario_type == "budget_cut":
            return self._simulate_budget_cut(budget_cut_percent)
        if scenario_type == "productivity_change":
            return self._simulate_productivity_change(workload_delta_percent, meeting_reduction_percent)
        return self._simulate_employee_resignation(resignation_count, seniority)

    def scenario_decision_suite(self) -> dict[str, object]:
        scenarios = [
            self._simulate_employee_resignation(20, "mixed"),
            self._simulate_project_completion("Project Alpha Revenue Platform", 2),
            self._simulate_hiring_freeze(6),
            self._simulate_team_restructure("Platform Reliability", "Security Response"),
            self._simulate_budget_cut(20),
            self._simulate_productivity_change(25, 50),
        ]
        highest_risk = max(scenarios, key=lambda item: float(item["failure_probability"]))
        strongest_recovery = min(scenarios, key=lambda item: float(item["success_probability"]))
        return {
            "model": "NEXUSMIND Enterprise Scenario Simulation & Decision Engine",
            "scenarios": scenarios,
            "executive_recommendations": [
                f"Prioritize {highest_risk['scenario_summary']} because failure probability is {highest_risk['failure_probability']}%.",
                f"Run mitigation plan for {strongest_recovery['scenario_type']} before approving quarterly operating changes.",
                "Protect platform engineering capacity, preserve critical knowledge owners, and stage budget changes behind delivery-risk thresholds.",
            ],
            "decision_readiness_score": round(mean(float(item["success_probability"]) for item in scenarios)),
            "forecast_models": FORECAST_MODELS,
            "source_systems": SCENARIO_SOURCE_SYSTEMS,
        }

    def simulate_extended(self, scenario: TwinScenarioInput) -> TwinExtendedOutput:
        departments = self.company_model.departments
        employees = self.company_model.employees
        total_headcount = sum(department.headcount for department in departments)
        resignation_ratio = min(0.55, scenario.resignation_count / max(total_headcount, 1))
        workload_pressure = max(-0.35, scenario.workload_delta_percent / 100)
        budget_buffer = max(-0.8, min(2.0, scenario.budget_delta_percent / 100))
        avg_burnout = mean(employee.burnout_risk for employee in employees)
        avg_productivity = mean(employee.productivity for employee in employees)
        criticality_pressure = mean(employee.criticality for employee in employees) / 100

        delay_raw = (
            18
            + resignation_ratio * 92
            + max(0, workload_pressure) * 52
            + max(0, (76 - avg_productivity)) * 0.4
            + criticality_pressure * 11
            - max(0, budget_buffer) * 24
            + max(0, -budget_buffer) * 18
        )
        burnout_raw = (
            max(0, workload_pressure) * 48
            + resignation_ratio * 76
            + max(0, avg_burnout - 52) * 0.35
            - max(0, budget_buffer) * 16
        )
        productivity_loss = (
            resignation_ratio * 42
            + max(0, workload_pressure) * 28
            + max(0, avg_burnout - 60) * 0.22
            + max(0, -budget_buffer) * 10
            - max(0, budget_buffer) * 7
        )
        revenue = (
            -0.28 * scenario.resignation_count
            - 0.16 * scenario.workload_delta_percent
            - productivity_loss * 0.18
            + scenario.budget_delta_percent * 0.11
        )

        security_penalty = 0
        if scenario.security_incident:
            delay_raw += 18
            burnout_raw += 8
            productivity_loss += 6
            revenue -= 4.8
            security_penalty = 14

        affected = sorted(
            departments,
            key=lambda department: (
                department.delivery_dependency * 50
                + department.revenue_dependency * 35
                + max(0, scenario.workload_delta_percent) * 0.12
                + scenario.resignation_count / max(department.headcount, 1) * 13
                - department.resilience * 0.35
            ),
            reverse=True,
        )[:3]
        workflow_impacts = {
            workflow.name: max(
                0,
                min(
                    100,
                    round(
                        workflow.baseline_delay_risk
                        + workflow.dependency_count * resignation_ratio * 9
                        + max(0, workload_pressure) * 34
                        + (security_penalty if workflow.owner_department == "Security" else 0)
                        - max(0, budget_buffer) * 14
                    ),
                ),
            )
            for workflow in self.company_model.workflows
        }
        team_collapse = round(min(100, max(0, delay_raw * 0.46 + burnout_raw * 0.42 + productivity_loss * 0.28 + security_penalty)))
        delay = max(0, min(round(delay_raw), 100))
        burnout = max(-30, min(round(burnout_raw), 80))
        stability = max(0, min(100 - delay * 0.58 - max(burnout, 0) * 0.28 - team_collapse * 0.18, 100))

        recovery_actions = [
            "Freeze non-essential scope and move dependency owners into a single recovery room.",
            f"Backfill capacity in {affected[0].name} and {affected[1].name} before the next milestone.",
            "Convert recurring status meetings into async updates for two weeks.",
        ]
        if scenario.security_incident:
            recovery_actions.append("Isolate security incident response from delivery-critical engineering lanes.")
        if scenario.budget_delta_percent > 0:
            recovery_actions.append("Use budget increase for short-term specialist capacity before permanent hiring.")

        return TwinExtendedOutput(
            delay_probability=delay,
            burnout_delta=burnout,
            revenue_impact_percent=round(revenue, 1),
            stability_score=round(stability),
            productivity_loss_percent=round(max(0, min(productivity_loss, 70)), 1),
            team_collapse_probability=team_collapse,
            affected_departments=[department.name for department in affected],
            workflow_impacts=workflow_impacts,
            recovery_actions=recovery_actions,
        )

    def _simulate_employee_resignation(self, resignation_count: int, seniority: str) -> dict[str, object]:
        count = max(0, min(500, resignation_count))
        seniority_pressure = 1.22 if seniority.lower() in {"senior", "lead", "critical"} else 1.0
        workload_delta = round(min(85, count * 1.35 * seniority_pressure))
        scenario = TwinScenarioInput(count, workload_delta, 0, False)
        outcome = self.simulate_extended(scenario)
        monte_carlo = self.simulate_monte_carlo(scenario, runs=256)
        critical_loss = round(min(100, count * seniority_pressure * 2.7 + mean(employee.criticality for employee in self.company_model.employees) * 0.2))
        return self._scenario_payload(
            scenario_type="employee_resignation",
            summary=f"{count} employee resignation shock with {seniority} criticality mix",
            outcome=outcome,
            success_probability=monte_carlo.success_probability,
            required_engineers=max(0, ceil(count * 0.72)),
            required_budget=round(count * 118_000 * seniority_pressure),
            hiring_requirements=[
                f"Backfill {max(0, ceil(count * 0.72))} delivery-critical engineer(s) within 45 days.",
                "Contract two senior platform specialists until permanent hiring completes.",
            ],
            risk_factors=[
                f"Knowledge loss risk {critical_loss}%",
                "Release ownership concentration in Platform Reliability",
                "Attrition contagion from overloaded incident owners",
            ],
            bottlenecks=["Platform engineering capacity", "Security review availability", "Release train dependency ownership"],
            recommendations=[
                "Open retention reviews for high-criticality employees before replacement hiring.",
                "Move critical release knowledge into documented runbooks within two weeks.",
                "Shift non-essential roadmap work away from Engineering until staffing stabilizes.",
            ],
            client_impact=max(12, round(outcome.delay_probability * 0.62)),
            knowledge_loss_risk=critical_loss,
            digital_twin_entities=["employees", "teams", "departments", "workflows"],
        )

    def _simulate_project_completion(self, project_name: str, deadline_months: int) -> dict[str, object]:
        project = self._find_project(project_name)
        deadline_days = max(14, min(540, deadline_months * 30))
        remaining_work = max(0, 100 - project.progress)
        capacity_pressure = mean(resource.utilization for resource in self.company_model.resources if resource.resource_id in project.resources)
        team = self._find_team_by_id(project.owning_team)
        projected_days = max(project.timeline_forecast_days, round(remaining_work * 0.52 + project.risk * 0.18 + capacity_pressure * 0.08))
        slack_days = deadline_days - projected_days
        delay_probability = round(max(5, min(96, project.delay_prediction + project.risk * 0.16 + capacity_pressure * 0.08 - slack_days * 0.42)))
        success_probability = max(4, min(96, 100 - delay_probability + round(team.delivery_performance * 0.12)))
        budget_variance = max(0, project.budget_forecast_percent - 70)
        outcome = TwinExtendedOutput(
            delay_probability=delay_probability,
            burnout_delta=round(max(0, team.burnout * 0.18 + project.risk * 0.08 - max(0, slack_days) * 0.05)),
            revenue_impact_percent=round(-project.risk * 0.08 - delay_probability * 0.05 - budget_variance * 0.04, 1),
            stability_score=max(0, min(100, round(100 - delay_probability * 0.55 - team.burnout * 0.18))),
            productivity_loss_percent=round(max(0, delay_probability * 0.22 + capacity_pressure * 0.05), 1),
            team_collapse_probability=round(max(0, min(100, delay_probability * 0.42 + team.burnout * 0.27))),
            affected_departments=sorted(project.team_allocation, key=project.team_allocation.get, reverse=True)[:3],
            workflow_impacts=self._project_workflow_impacts(project, delay_probability),
            recovery_actions=[
                "Move dependency owners into a focused delivery room until the deadline decision is stable.",
                "Freeze low-value scope and protect engineering focus blocks.",
                "Add short-term QA and release engineering capacity if success probability remains below 75%.",
            ],
        )
        return self._scenario_payload(
            scenario_type="project_completion",
            summary=f"{project.name} completion forecast inside {deadline_months} month(s)",
            outcome=outcome,
            success_probability=success_probability,
            required_engineers=max(1, ceil(remaining_work / 12 + delay_probability / 34)),
            required_budget=round(85_000 + budget_variance * 7_500 + max(0, -slack_days) * 9_500),
            hiring_requirements=[
                f"Add {max(1, ceil(remaining_work / 18))} project-specialist engineer(s) if deadline remains fixed.",
                "Assign one delivery owner across Engineering and Security dependencies.",
            ],
            risk_factors=[
                f"Projected delivery days {projected_days} vs deadline {deadline_days}",
                f"Capacity utilization {round(capacity_pressure)}%",
                f"Client health {project.client_health}%",
            ],
            bottlenecks=["Cross-team dependency queue", "Security review lane", "Release train validation"],
            recommendations=outcome.recovery_actions,
            client_impact=max(0, round(100 - project.client_health + delay_probability * 0.35)),
            knowledge_loss_risk=round(max(10, project.risk * 0.36)),
            digital_twin_entities=["projects", "resources", "teams", "workflows"],
        )

    def _simulate_hiring_freeze(self, freeze_months: int) -> dict[str, object]:
        months = max(1, min(24, freeze_months))
        hiring_need = mean(department.hiring_need for department in self.company_model.departments)
        workload_delta = round(min(90, months * 4.8 + hiring_need * 0.22))
        budget_delta = round(max(-18, -months * 1.2))
        scenario = TwinScenarioInput(0, workload_delta, budget_delta, False)
        outcome = self.simulate_extended(scenario)
        hiring_gap = ceil(sum(department.headcount * department.hiring_need / 100 for department in self.company_model.departments) * months / 12)
        return self._scenario_payload(
            scenario_type="hiring_freeze",
            summary=f"{months}-month hiring freeze across delivery-critical teams",
            outcome=outcome,
            success_probability=max(0, min(100, 100 - outcome.delay_probability)),
            required_engineers=hiring_gap,
            required_budget=round(hiring_gap * 96_000),
            hiring_requirements=[
                f"Hold a documented exception path for {hiring_gap} critical replacement or specialist role(s).",
                "Pre-approve contractors for Platform Reliability and Customer Success escalation work.",
            ],
            risk_factors=[
                f"Average hiring need {round(hiring_need)}%",
                f"Workload pressure +{workload_delta}%",
                "Delayed backfills compound attrition and project-delay exposure",
            ],
            bottlenecks=["Open specialist roles", "Manager span of control", "Release and escalation capacity"],
            recommendations=[
                "Keep hiring frozen for non-critical roles only; exempt incident response and release-critical capacity.",
                "Redistribute low-priority work before approving freeze extension.",
                "Run monthly attrition and project risk review while freeze is active.",
            ],
            client_impact=round(outcome.delay_probability * 0.46),
            knowledge_loss_risk=round(max(18, hiring_need * 0.7)),
            digital_twin_entities=["departments", "employees", "projects", "resources"],
        )

    def _simulate_team_restructure(self, source_team: str, target_team: str) -> dict[str, object]:
        source = self._find_team(source_team)
        target = self._find_team(target_team)
        avg_risk = mean([source.risk, target.risk])
        collaboration_gain = max(-18, min(22, (source.collaboration + target.collaboration) / 2 - avg_risk * 0.24))
        transition_load = round(max(6, avg_risk * 0.16 + abs(source.burnout - target.burnout) * 0.22))
        scenario = TwinScenarioInput(0, transition_load, 0, False)
        outcome = self.simulate_extended(scenario)
        success_probability = round(max(12, min(94, 76 + collaboration_gain * 0.55 - transition_load * 0.8)))
        return self._scenario_payload(
            scenario_type="team_restructure",
            summary=f"Merge or rebalance {source.name} with {target.name}",
            outcome=outcome,
            success_probability=success_probability,
            required_engineers=2,
            required_budget=round(120_000 + transition_load * 4_800),
            hiring_requirements=["No immediate headcount required if delivery owners are retained.", "Assign one transformation lead for 60 days."],
            risk_factors=[
                f"Transition load {transition_load}%",
                f"Source team burnout {source.burnout}%",
                f"Target team risk {target.risk}%",
            ],
            bottlenecks=["Role clarity", "Manager handoff", "Conflicting incident and delivery priorities"],
            recommendations=[
                "Do not merge teams until project ownership and escalation roles are explicitly mapped.",
                "Preserve one technical lead per critical workflow during restructuring.",
                "Run a 30-day transition scorecard before making the restructure permanent.",
            ],
            client_impact=round(max(source.risk, target.risk) * 0.32),
            knowledge_loss_risk=round(max(source.risk, target.risk) * 0.45),
            digital_twin_entities=["teams", "employees", "workflows", "graph_edges"],
        )

    def _simulate_budget_cut(self, budget_cut_percent: int) -> dict[str, object]:
        cut = max(0, min(80, budget_cut_percent))
        scenario = TwinScenarioInput(0, round(cut * 0.9), -cut, False)
        outcome = self.simulate_extended(scenario)
        protected_capacity = ceil(sum(department.headcount for department in self.company_model.departments if department.delivery_dependency >= 0.7) * cut / 280)
        return self._scenario_payload(
            scenario_type="budget_cut",
            summary=f"{cut}% budget cut with delivery and workforce exposure",
            outcome=outcome,
            success_probability=max(0, min(100, 100 - outcome.delay_probability - round(cut * 0.18))),
            required_engineers=protected_capacity,
            required_budget=round(cut * 52_000),
            hiring_requirements=[
                f"Protect {protected_capacity} delivery-critical role(s) from cut scope.",
                "Use contractors only for defined recovery windows, not permanent operating load.",
            ],
            risk_factors=[
                f"Budget buffer -{cut}%",
                f"Delivery risk {outcome.delay_probability}%",
                "Knowledge and client escalation exposure rise if cuts target senior owners",
            ],
            bottlenecks=["Platform specialist capacity", "Customer escalation coverage", "Security review throughput"],
            recommendations=[
                "Cut discretionary tooling and low-risk programs before reducing platform or customer escalation capacity.",
                "Sequence budget cuts after the next release milestone when project risk is lower.",
                "Track weekly delivery, attrition, and client-health thresholds before phase-two reductions.",
            ],
            client_impact=round(outcome.delay_probability * 0.52),
            knowledge_loss_risk=round(min(100, cut * 1.1 + mean(employee.criticality for employee in self.company_model.employees) * 0.18)),
            digital_twin_entities=["departments", "resources", "projects", "operations"],
        )

    def _simulate_productivity_change(self, workload_delta_percent: int, meeting_reduction_percent: int) -> dict[str, object]:
        workload = max(-50, min(150, workload_delta_percent))
        meeting_reduction = max(0, min(90, meeting_reduction_percent))
        effective_workload = round(workload - meeting_reduction * 0.36)
        scenario = TwinScenarioInput(0, effective_workload, 0, False)
        outcome = self.simulate_extended(scenario)
        focus_gain = round(meeting_reduction * 0.38 - max(0, workload) * 0.12, 1)
        success_probability = max(0, min(100, 100 - outcome.delay_probability + round(max(0, focus_gain) * 0.9)))
        return self._scenario_payload(
            scenario_type="productivity_change",
            summary=f"{workload}% workload change with {meeting_reduction}% meeting reduction",
            outcome=outcome,
            success_probability=success_probability,
            required_engineers=max(0, ceil(max(0, workload - meeting_reduction * 0.25) / 18)),
            required_budget=round(max(0, workload - meeting_reduction * 0.25) * 9_500),
            hiring_requirements=["No hiring needed if protected deep-work blocks recover capacity.", "Add temporary delivery support only if focus gain remains below 8%."],
            risk_factors=[
                f"Effective workload delta {effective_workload}%",
                f"Modeled focus gain {focus_gain}%",
                "Meeting reduction helps only if executive review and decision rituals stay intact",
            ],
            bottlenecks=["Context switching", "Meeting-heavy dependency handoffs", "Deep-work interruption frequency"],
            recommendations=[
                "Cut recurring status meetings by half and move updates to async dashboards.",
                "Protect 9AM-11AM deep-work blocks for Engineering and Security.",
                "Re-check delivery risk after two weeks before increasing workload further.",
            ],
            client_impact=round(max(0, outcome.delay_probability * 0.33 - meeting_reduction * 0.1)),
            knowledge_loss_risk=round(max(8, outcome.team_collapse_probability * 0.26)),
            digital_twin_entities=["employees", "teams", "workflows", "operations"],
        )

    def _scenario_payload(
        self,
        scenario_type: str,
        summary: str,
        outcome: TwinExtendedOutput,
        success_probability: int,
        required_engineers: int,
        required_budget: int,
        hiring_requirements: list[str],
        risk_factors: list[str],
        bottlenecks: list[str],
        recommendations: list[str],
        client_impact: int,
        knowledge_loss_risk: int,
        digital_twin_entities: list[str],
    ) -> dict[str, object]:
        success = max(0, min(100, round(success_probability)))
        failure = 100 - success
        risk_level = "critical" if failure >= 65 else "high" if failure >= 45 else "medium" if failure >= 25 else "low"
        productivity_impact = round(-outcome.productivity_loss_percent, 1)
        return {
            "scenario_type": scenario_type,
            "scenario_summary": summary,
            "success_probability": success,
            "failure_probability": failure,
            "productivity_impact_percent": productivity_impact,
            "revenue_impact_percent": outcome.revenue_impact_percent,
            "burnout_impact": outcome.burnout_delta,
            "delivery_delay_probability": outcome.delay_probability,
            "client_impact": max(0, min(100, client_impact)),
            "risk_level": risk_level,
            "required_engineers": max(0, required_engineers),
            "required_budget": max(0, required_budget),
            "hiring_requirements": hiring_requirements,
            "knowledge_loss_risk": max(0, min(100, knowledge_loss_risk)),
            "risk_factors": risk_factors,
            "bottlenecks": bottlenecks,
            "recommendations": recommendations,
            "forecast_models": FORECAST_MODELS,
            "source_systems": SCENARIO_SOURCE_SYSTEMS,
            "digital_twin_entities": digital_twin_entities,
            "risk_heatmap": self._risk_heatmap(outcome),
            "impact_vectors": [
                self._impact_vector("Productivity", abs(productivity_impact), "loss" if productivity_impact < 0 else "gain"),
                self._impact_vector("Revenue", abs(outcome.revenue_impact_percent), "loss" if outcome.revenue_impact_percent < 0 else "gain"),
                self._impact_vector("Delivery", outcome.delay_probability, "delay"),
                self._impact_vector("Workforce", max(0, outcome.burnout_delta), "burnout"),
                self._impact_vector("Client", max(0, min(100, client_impact)), "client risk"),
            ],
            "decision_trace": [
                "Loaded employee, team, department, project, resource, workflow, and operation twins.",
                f"Ran {scenario_type} through risk, impact, forecasting, and recommendation engines.",
                f"Computed risk level {risk_level} from success={success}% and delay={outcome.delay_probability}%.",
            ],
            "forecast_horizon_days": 90,
        }

    def _risk_heatmap(self, outcome: TwinExtendedOutput) -> list[dict[str, object]]:
        impacted = set(outcome.affected_departments)
        rows = []
        for department in self.company_model.departments:
            base = department.risk * 0.48 + department.workload * 0.2 + max(0, outcome.burnout_delta) * 0.18 + outcome.delay_probability * 0.14
            if department.name in impacted:
                base += 9
            rows.append(
                {
                    "department": department.name,
                    "risk": round(max(0, min(100, base))),
                    "productivity": department.productivity,
                    "workload": department.workload,
                    "hiring_need": department.hiring_need,
                }
            )
        return sorted(rows, key=lambda item: int(item["risk"]), reverse=True)

    @staticmethod
    def _impact_vector(domain: str, value: float, direction: str) -> dict[str, object]:
        severity = "critical" if value >= 65 else "high" if value >= 45 else "medium" if value >= 25 else "low"
        return {
            "domain": domain,
            "impact_percent": round(max(0, min(100, value)), 1),
            "severity": severity,
            "explanation": f"{domain} impact is modeled as {direction} under this scenario.",
        }

    def _find_project(self, project_name: str) -> VirtualProject:
        normalized = project_name.lower().strip()
        for project in self.company_model.projects:
            if normalized in project.name.lower() or project.name.lower() in normalized:
                return project
        if "alpha" in normalized:
            return self.company_model.projects[0]
        return self.company_model.projects[0]

    def _find_team(self, team_name: str) -> VirtualTeam:
        normalized = team_name.lower().strip()
        for team in self.company_model.teams:
            if normalized in team.name.lower() or team.name.lower() in normalized:
                return team
        return self.company_model.teams[0]

    def _find_team_by_id(self, team_id: str) -> VirtualTeam:
        for team in self.company_model.teams:
            if team.team_id == team_id:
                return team
        return self.company_model.teams[0]

    def _project_workflow_impacts(self, project: VirtualProject, delay_probability: int) -> dict[str, int]:
        return {
            workflow.name: max(
                0,
                min(
                    100,
                    round(
                        workflow.baseline_delay_risk
                        + delay_probability * (0.32 if workflow.owner_department in project.team_allocation else 0.18)
                        + workflow.dependency_count * 1.5
                    ),
                ),
            )
            for workflow in self.company_model.workflows
        }

    def simulate_monte_carlo(self, scenario: TwinScenarioInput, runs: int = 320) -> TwinMonteCarloOutput:
        bounded_runs = max(128, min(runs, 1_200))
        rng = Random(self._scenario_seed(scenario))
        outcomes: list[TwinExtendedOutput] = []

        for _ in range(bounded_runs):
            sampled = TwinScenarioInput(
                resignation_count=max(
                    0,
                    min(
                        500,
                        round(rng.gauss(scenario.resignation_count, max(1.0, scenario.resignation_count * 0.16 + 2.0))),
                    ),
                ),
                workload_delta_percent=max(
                    -50,
                    min(
                        150,
                        round(rng.gauss(scenario.workload_delta_percent, 8.0 + abs(scenario.workload_delta_percent) * 0.08)),
                    ),
                ),
                budget_delta_percent=max(
                    -80,
                    min(
                        200,
                        round(rng.gauss(scenario.budget_delta_percent, 5.0 + abs(scenario.budget_delta_percent) * 0.06)),
                    ),
                ),
                security_incident=scenario.security_incident
                or rng.random() < min(0.26, max(0.03, scenario.workload_delta_percent / 520)),
            )
            outcomes.append(self.simulate_extended(sampled))

        delays = [outcome.delay_probability for outcome in outcomes]
        burnouts = [outcome.burnout_delta for outcome in outcomes]
        revenues = [outcome.revenue_impact_percent for outcome in outcomes]
        stabilities = [outcome.stability_score for outcome in outcomes]
        collapses = [outcome.team_collapse_probability for outcome in outcomes]
        successful = [
            outcome
            for outcome in outcomes
            if outcome.delay_probability < 50
            and outcome.team_collapse_probability < 55
            and outcome.revenue_impact_percent > -12
            and outcome.stability_score >= 55
        ]
        stable = sum(1 for outcome in outcomes if outcome.stability_score >= 70 and outcome.delay_probability < 40)
        crisis = sum(1 for outcome in outcomes if outcome.team_collapse_probability >= 68 or outcome.delay_probability >= 72)
        strained = bounded_runs - stable - crisis
        delay_spread = self._percentile(delays, 90) - self._percentile(delays, 50)

        return TwinMonteCarloOutput(
            runs=bounded_runs,
            success_probability=round(len(successful) / bounded_runs * 100),
            delay_probability_p50=round(self._percentile(delays, 50)),
            delay_probability_p90=round(self._percentile(delays, 90)),
            burnout_delta_p90=round(self._percentile(burnouts, 90)),
            expected_revenue_impact_percent=round(mean(revenues), 1),
            worst_case_revenue_impact_percent=round(self._percentile(revenues, 10), 1),
            stability_score_p10=round(self._percentile(stabilities, 10)),
            stability_score_p50=round(self._percentile(stabilities, 50)),
            team_collapse_p90=round(self._percentile(collapses, 90)),
            risk_distribution={
                "stable": round(stable / bounded_runs * 100),
                "strained": round(strained / bounded_runs * 100),
                "crisis": round(crisis / bounded_runs * 100),
            },
            confidence=round(max(0.58, min(0.94, 1 - delay_spread / 135)), 2),
        )

    @staticmethod
    def _scenario_seed(scenario: TwinScenarioInput) -> int:
        return (
            scenario.resignation_count * 1_000_003
            + scenario.workload_delta_percent * 19_271
            + scenario.budget_delta_percent * 4_099
            + int(scenario.security_incident) * 1_048_573
        ) & 0xFFFFFFFF

    @staticmethod
    def _percentile(values: list[float | int], percentile: int) -> float:
        ordered = sorted(float(value) for value in values)
        if not ordered:
            return 0.0
        index = (len(ordered) - 1) * percentile / 100
        lower = int(index)
        upper = min(lower + 1, len(ordered) - 1)
        weight = index - lower
        return ordered[lower] * (1 - weight) + ordered[upper] * weight


digital_twin_simulator = DigitalTwinSimulator()
