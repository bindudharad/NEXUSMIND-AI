from __future__ import annotations

import asyncio
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from threading import Lock

import networkx as nx

from app.schemas.organizational_optimizer import (
    CommunicationFlowInsight,
    ManagerLoadInsight,
    OrgEdgeType,
    OrgEmployeeInput,
    OrgGraphEdge,
    OrgGraphNode,
    OrganizationalAssistantRequest,
    OrganizationalAssistantResponse,
    OrganizationalForecast,
    OrganizationalOptimizerRequest,
    OrganizationalOptimizerResponse,
    OrganizationalOptimizerSummary,
    OrganizationalRecommendation,
    OrganizationalSimulationRequest,
    OrganizationalSimulationResult,
    OrgRiskLevel,
    OrgTeamInput,
    ReportingStructureInsight,
    SiloRiskInsight,
    SkillDistributionInsight,
    TeamOptimizationRecommendation,
)


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
HISTORY_PATH = DATA_DIR / "organizational_optimizer_history.jsonl"
GRAPH_EXPORT_PATH = DATA_DIR / "organizational_optimizer_graph.json"


class OrganizationalOptimizerService:
    model_name = "Graph AI Organizational Structure Optimizer"
    assistant_model = "Organizational Design Intelligence Assistant"
    source_systems = [
        "organizational_analytics_engine",
        "graph_ai_engine",
        "reporting_structure_analyzer",
        "team_optimization_engine",
        "collaboration_intelligence_engine",
        "communication_flow_analyzer",
        "organizational_simulation_engine",
        "executive_recommendation_engine",
        "organizational_dashboard",
        "organizational_ai_assistant",
        "company_digital_twin",
        "employee_digital_twin",
        "team_digital_twin",
        "talent_marketplace",
        "knowledge_brain",
        "networkx_graph_algorithms",
        "organizational_optimizer_history_jsonl",
    ]
    forecast_models = [
        "Graph ML centrality analyzer",
        "XGBoost-style restructure risk model",
        "Random Forest leadership capacity estimator",
        "Time-series organization scaling forecaster",
    ]

    def __init__(self) -> None:
        self._lock = Lock()
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def default(self) -> OrganizationalOptimizerResponse:
        return self.analyze()

    def analyze(self, payload: OrganizationalOptimizerRequest | None = None) -> OrganizationalOptimizerResponse:
        request = self._with_defaults(payload or OrganizationalOptimizerRequest())
        graph = self._graph(request)
        undirected = graph.to_undirected()
        centrality = nx.betweenness_centrality(undirected, weight="weight", normalized=True) if graph.number_of_nodes() else {}
        manager_load = self._manager_load(request, centrality)
        reporting = self._reporting_structure(request, manager_load)
        communication = self._communication_flows(request)
        teams = self._team_recommendations(request, manager_load)
        silos = self._silo_risks(request)
        skills = self._skill_distribution(request)
        simulations = [
            self._simulate(request, OrganizationalSimulationRequest(scenario_type="split_team", target_team=teams[0].team_name if teams else "Engineering Platform")),
            self._simulate(request, OrganizationalSimulationRequest(scenario_type="reduce_layers", question="What happens if we reduce management layers?", target_team="Company")),
            self._simulate(request, OrganizationalSimulationRequest(scenario_type="create_department", target_team="Platform", new_department_name="Platform Reliability")),
        ]
        forecasts = self._forecasts(request, manager_load, reporting, silos, skills)
        recommendations = self._recommendations(manager_load, reporting, communication, teams, silos, skills, simulations)
        nodes = self._nodes(graph, centrality)
        edges = self._edges(graph)
        summary = self._summary(nodes, edges, manager_load, communication, teams, silos, skills, reporting)
        response = OrganizationalOptimizerResponse(
            model=self.model_name,
            generated_at=datetime.now(timezone.utc),
            cycle_name=request.cycle_name,
            summary=summary,
            graph_nodes=nodes,
            graph_edges=edges,
            manager_load=manager_load,
            reporting_structure=reporting,
            communication_flows=communication,
            team_recommendations=teams,
            silo_risks=silos,
            skill_distribution=skills,
            simulations=simulations,
            forecasts=forecasts,
            recommendations=recommendations,
            executive_brief=self._executive_brief(summary, manager_load, communication, teams, silos, skills),
            supported_questions=[
                "Show organizational bottlenecks.",
                "Which managers are overloaded?",
                "Suggest a better reporting structure.",
                "Show communication gaps.",
                "Simulate restructuring Engineering.",
                "Where are critical skills concentrated?",
            ],
            source_systems=self.source_systems,
            storage=str(HISTORY_PATH),
        )
        self._persist(response)
        return response

    def simulate(self, payload: OrganizationalSimulationRequest, base: OrganizationalOptimizerRequest | None = None) -> OrganizationalOptimizerResponse:
        request = self._with_defaults(base or OrganizationalOptimizerRequest())
        response = self.analyze(request)
        custom = self._simulate(request, payload)
        return response.model_copy(update={"simulations": [custom, *response.simulations[:2]]})

    def ask(self, payload: OrganizationalAssistantRequest) -> OrganizationalAssistantResponse:
        analysis = self.analyze(OrganizationalOptimizerRequest(horizon_months=payload.horizon_months))
        intent = self._intent(payload.question)
        simulation = None
        if intent == "simulation":
            simulation = self._simulate(OrganizationalOptimizerRequest(horizon_months=payload.horizon_months), self._scenario_from_question(payload.question, payload.horizon_months))
        answer, evidence = self._answer(intent, analysis, simulation)
        return OrganizationalAssistantResponse(
            model=self.assistant_model,
            generated_at=datetime.now(timezone.utc),
            question=payload.question,
            intent=intent,
            answer=answer,
            confidence=0.9,
            cited_evidence=evidence[:10],
            recommended_actions=[item.action for item in analysis.recommendations[:5]],
            simulation=simulation,
            source_systems=["organizational_ai_assistant", "graph_ai_engine", "organizational_simulation_engine", *analysis.source_systems[:8]],
            storage=str(HISTORY_PATH),
        )

    async def stream(self):
        scenarios = [
            self.default_request(),
            self._pressure_variant(self.default_request(), stress_delta=8, communication_drop=8),
            self._pressure_variant(self.default_request(), stress_delta=15, communication_drop=14),
        ]
        for sequence, scenario in enumerate(scenarios, start=1):
            response = self.analyze(scenario)
            data = response.model_dump(mode="json")
            data["summary"]["stream_sequence"] = sequence
            yield f"event: organizational_optimizer\ndata: {json.dumps(data)}\n\n"
            await asyncio.sleep(0.8)

    def default_request(self) -> OrganizationalOptimizerRequest:
        employees = [
            OrgEmployeeInput(employee_id="ceo-001", name="Anika Sharma", role="CEO", department="Executive", team="Executive", manager_id=None, location="Bangalore", skills=["strategy", "leadership"], projects=["Company Operating Model"], leadership_score=96, collaboration_score=82, productivity_score=88),
            OrgEmployeeInput(employee_id="cto-001", name="Rohan Mehta", role="CTO", department="Engineering", team="Engineering Leadership", manager_id="ceo-001", location="Bangalore", skills=["architecture", "kubernetes", "ai platform"], projects=["Platform Reliability"], communicates_with=["cpo-001", "ciso-001", "vp-cs-001"], leadership_score=89, stress_score=68, workload=1.05),
            OrgEmployeeInput(employee_id="cpo-001", name="Maya Iyer", role="CPO", department="Product", team="Product Leadership", manager_id="ceo-001", location="Bangalore", skills=["product strategy", "analytics"], projects=["Client Insights"], communicates_with=["cto-001", "pm-001", "design-001"], leadership_score=86),
            OrgEmployeeInput(employee_id="ciso-001", name="Nisha Rao", role="CISO", department="Security", team="Security Operations", manager_id="ceo-001", location="Singapore", skills=["security", "zero trust", "kubernetes"], projects=["Data Export Guardrails"], communicates_with=["cto-001", "sec-001", "sec-002"], leadership_score=88, stress_score=61),
            OrgEmployeeInput(employee_id="vp-cs-001", name="Omar Singh", role="VP Customer Success", department="Customer Success", team="Enterprise Success", manager_id="ceo-001", location="Dubai", skills=["client recovery", "renewals"], projects=["Orion Renewal"], communicates_with=["cto-001", "cs-001", "pm-001"], leadership_score=82, stress_score=58),
            OrgEmployeeInput(employee_id="mgr-platform-001", name="Lina Chen", role="Platform Manager", department="Engineering", team="Engineering Platform", manager_id="cto-001", location="Bangalore", skills=["kubernetes", "mlops", "python", "incident response"], projects=["Platform Reliability"], communicates_with=["mgr-product-001", "sec-001", "eng-001", "eng-002", "eng-003"], mentors=["eng-004", "eng-005"], workload=1.22, stress_score=74, leadership_score=84),
            OrgEmployeeInput(employee_id="mgr-app-001", name="Aarav Mehta", role="Application Manager", department="Engineering", team="Application Engineering", manager_id="cto-001", location="Bangalore", skills=["api", "postgresql", "python"], projects=["Revenue APIs"], communicates_with=["pm-001", "eng-006", "eng-007"], workload=0.92, stress_score=57, leadership_score=76),
            OrgEmployeeInput(employee_id="mgr-product-001", name="Sara Khan", role="Product Lead", department="Product", team="Product Platform", manager_id="cpo-001", location="Bangalore", skills=["product strategy", "research", "analytics"], projects=["Client Insights"], communicates_with=["mgr-platform-001", "design-001", "pm-001"], workload=0.78, stress_score=42, leadership_score=79),
            OrgEmployeeInput(employee_id="pm-001", name="Dev Patel", role="Program Manager", department="Product", team="Product Platform", manager_id="mgr-product-001", location="Bangalore", skills=["delivery", "communication"], projects=["Platform Reliability", "Orion Renewal"], communicates_with=["mgr-app-001", "vp-cs-001"], workload=1.02, stress_score=56, collaboration_score=63),
            OrgEmployeeInput(employee_id="design-001", name="Isha Nair", role="Design Lead", department="Product", team="Product Platform", manager_id="mgr-product-001", location="Bangalore", skills=["ux", "research"], projects=["Client Insights"], communicates_with=["pm-001"], workload=0.7),
            OrgEmployeeInput(employee_id="sec-001", name="Ken Tan", role="Security Engineer", department="Security", team="Security Operations", manager_id="ciso-001", location="Singapore", skills=["security", "zero trust", "threat modeling"], projects=["Data Export Guardrails"], communicates_with=["mgr-platform-001", "sec-002"], workload=1.1, stress_score=63),
            OrgEmployeeInput(employee_id="sec-002", name="Priya Das", role="SOC Analyst", department="Security", team="Security Operations", manager_id="ciso-001", location="Bangalore", skills=["soc", "incident response"], projects=["Data Export Guardrails"], communicates_with=["sec-001"], workload=0.88, stress_score=54),
            OrgEmployeeInput(employee_id="cs-001", name="Fatima Ali", role="Client Director", department="Customer Success", team="Enterprise Success", manager_id="vp-cs-001", location="Dubai", skills=["renewals", "client recovery"], projects=["Orion Renewal"], communicates_with=["pm-001"], workload=0.96, stress_score=52),
        ]
        for index in range(1, 15):
            manager_id = "mgr-platform-001" if index <= 9 else "mgr-app-001"
            team = "Engineering Platform" if index <= 9 else "Application Engineering"
            employees.append(
                OrgEmployeeInput(
                    employee_id=f"eng-{index:03d}",
                    name=f"Engineer {index}",
                    role="Senior Engineer" if index <= 4 else "Engineer",
                    department="Engineering",
                    team=team,
                    manager_id=manager_id,
                    location="Bangalore" if index % 3 else "Remote",
                    skills=["python", "kubernetes" if index <= 3 else "api", "observability" if index % 2 else "postgresql"],
                    projects=["Platform Reliability" if index <= 9 else "Revenue APIs"],
                    communicates_with=[manager_id, "pm-001"] + (["sec-001"] if index <= 2 else []),
                    workload=0.74 + index * 0.035,
                    stress_score=39 + index * 3.5,
                    collaboration_score=max(40, 76 - index * 2.1),
                    leadership_score=49 + index * 1.7,
                    productivity_score=max(45, 82 - index * 1.4),
                )
            )
        teams = [
            OrgTeamInput(team_id="team-exec", name="Executive", department="Executive", manager_id="ceo-001", strategic_importance=1.0, delivery_pressure=55),
            OrgTeamInput(team_id="team-eng-lead", name="Engineering Leadership", department="Engineering", manager_id="cto-001", strategic_importance=0.92, delivery_pressure=75),
            OrgTeamInput(team_id="team-platform", name="Engineering Platform", department="Engineering", manager_id="mgr-platform-001", strategic_importance=0.94, delivery_pressure=88),
            OrgTeamInput(team_id="team-app", name="Application Engineering", department="Engineering", manager_id="mgr-app-001", strategic_importance=0.82, delivery_pressure=70),
            OrgTeamInput(team_id="team-product", name="Product Platform", department="Product", manager_id="mgr-product-001", strategic_importance=0.78, delivery_pressure=62),
            OrgTeamInput(team_id="team-security", name="Security Operations", department="Security", manager_id="ciso-001", strategic_importance=0.9, delivery_pressure=77),
            OrgTeamInput(team_id="team-success", name="Enterprise Success", department="Customer Success", manager_id="vp-cs-001", strategic_importance=0.86, delivery_pressure=68),
        ]
        return OrganizationalOptimizerRequest(employees=employees, teams=teams)

    def _with_defaults(self, request: OrganizationalOptimizerRequest) -> OrganizationalOptimizerRequest:
        default = self.default_request()
        updates = {}
        if not request.employees:
            updates["employees"] = default.employees
        if not request.teams:
            updates["teams"] = default.teams
        return request.model_copy(update=updates) if updates else request

    def _graph(self, request: OrganizationalOptimizerRequest) -> nx.DiGraph:
        graph = nx.DiGraph()
        teams = {team.name: team for team in request.teams}
        for team in request.teams:
            graph.add_node(f"team:{team.name}", label=team.name, node_type="team", department=team.department, team=team.name, risk_score=team.delivery_pressure)
            graph.add_node(f"dept:{team.department}", label=team.department, node_type="department", department=team.department, team=None, risk_score=team.delivery_pressure)
            graph.add_node(f"loc:{team.location}", label=team.location, node_type="location", department=None, team=None, risk_score=0)
            graph.add_edge(f"team:{team.name}", f"dept:{team.department}", edge_type="belongs_to", weight=1.0, risk=team.delivery_pressure, evidence=f"{team.name} belongs to {team.department}.")
            graph.add_edge(f"team:{team.name}", f"loc:{team.location}", edge_type="belongs_to", weight=0.6, risk=0, evidence=f"{team.name} primary location is {team.location}.")
        employee_map = {employee.employee_id: employee for employee in request.employees}
        for employee in request.employees:
            node_type = "manager" if any(item.manager_id == employee.employee_id for item in request.employees) else "employee"
            graph.add_node(
                employee.employee_id,
                label=employee.name,
                node_type=node_type,
                department=employee.department,
                team=employee.team,
                risk_score=max(employee.stress_score, employee.workload * 65),
                workload=round(employee.workload, 3),
                leadership=employee.leadership_score,
            )
            graph.add_edge(employee.employee_id, f"team:{employee.team}", edge_type="belongs_to", weight=1.0, risk=employee.stress_score, evidence=f"{employee.name} belongs to {employee.team}.")
            graph.add_edge(employee.employee_id, f"loc:{employee.location}", edge_type="belongs_to", weight=0.35, risk=0, evidence=f"{employee.name} works from {employee.location}.")
            if employee.manager_id and employee.manager_id in employee_map:
                graph.add_edge(employee.employee_id, employee.manager_id, edge_type="reports_to", weight=1.4, risk=employee.stress_score, evidence=f"{employee.name} reports to {employee_map[employee.manager_id].name}.")
            for target_id in employee.communicates_with:
                if target_id in employee_map:
                    graph.add_edge(employee.employee_id, target_id, edge_type="communicates_with", weight=1.0, risk=max(0, 100 - employee.collaboration_score), evidence=f"{employee.name} communicates with {employee_map[target_id].name}.")
            for project in employee.projects:
                graph.add_node(f"project:{project}", label=project, node_type="project", department=employee.department, team=employee.team, risk_score=employee.stress_score)
                graph.add_edge(employee.employee_id, f"project:{project}", edge_type="works_on", weight=0.9, risk=employee.stress_score, evidence=f"{employee.name} works on {project}.")
            for skill in employee.skills:
                skill_id = f"skill:{self._normalize(skill)}"
                graph.add_node(skill_id, label=skill.title(), node_type="skill", department=None, team=None, risk_score=0)
                graph.add_edge(employee.employee_id, skill_id, edge_type="has_skill", weight=0.7, risk=0, evidence=f"{employee.name} has {skill}.")
            for mentee_id in employee.mentors:
                if mentee_id in employee_map:
                    graph.add_edge(employee.employee_id, mentee_id, edge_type="mentors", weight=0.8, risk=0, evidence=f"{employee.name} mentors {employee_map[mentee_id].name}.")
        return graph

    def _manager_load(self, request: OrganizationalOptimizerRequest, centrality: dict[str, float]) -> list[ManagerLoadInsight]:
        employees = {employee.employee_id: employee for employee in request.employees}
        reports: dict[str, list[OrgEmployeeInput]] = defaultdict(list)
        for employee in request.employees:
            if employee.manager_id:
                reports[employee.manager_id].append(employee)
        insights = []
        for manager_id, direct_reports in reports.items():
            manager = employees.get(manager_id)
            if not manager:
                continue
            span = len(direct_reports)
            avg_stress = mean([item.stress_score for item in direct_reports] or [0])
            avg_workload = mean([item.workload for item in direct_reports] or [0])
            overload = self._clip((span - 7) * 7.5 + avg_workload * 35 + avg_stress * 0.34 + centrality.get(manager_id, 0) * 160)
            bottleneck = self._clip(overload * 0.58 + centrality.get(manager_id, 0) * 220 + max(0, span - 10) * 5)
            insights.append(
                ManagerLoadInsight(
                    manager_id=manager_id,
                    manager_name=manager.name,
                    department=manager.department,
                    direct_reports=span,
                    span_of_control=round(span, 2),
                    overload_risk=round(overload, 2),
                    leadership_bottleneck_score=round(bottleneck, 2),
                    recommendation=(
                        "Create an additional team lead layer and move specialist escalation ownership away from this manager."
                        if overload >= 65
                        else "Maintain current span but keep decision ownership explicit for cross-team work."
                    ),
                    evidence=[
                        f"direct_reports={span}",
                        f"avg_team_stress={round(avg_stress, 1)}",
                        f"avg_workload={round(avg_workload, 2)}",
                        f"betweenness={round(centrality.get(manager_id, 0), 3)}",
                    ],
                )
            )
        return sorted(insights, key=lambda item: item.overload_risk, reverse=True)

    def _reporting_structure(self, request: OrganizationalOptimizerRequest, manager_load: list[ManagerLoadInsight]) -> list[ReportingStructureInsight]:
        employees = {employee.employee_id: employee for employee in request.employees}
        by_department: dict[str, list[OrgEmployeeInput]] = defaultdict(list)
        for employee in request.employees:
            by_department[employee.department].append(employee)
        manager_by_dept = {item.department: item for item in manager_load}
        output = []
        for department, employees_in_dept in by_department.items():
            depths = [self._depth(employee, employees) for employee in employees_in_dept]
            depth = max(depths or [0])
            bottleneck = manager_by_dept.get(department)
            risk = self._clip(depth * 12 + (bottleneck.overload_risk if bottleneck else 0) * 0.55 + max(0, len(employees_in_dept) - 18) * 1.8)
            output.append(
                ReportingStructureInsight(
                    unit=department,
                    hierarchy_depth=depth,
                    excessive_layers=depth >= 5,
                    leadership_bottleneck=bottleneck.manager_name if bottleneck else "No active bottleneck",
                    reporting_risk=round(risk, 2),
                    recommendation=(
                        "Reduce decision hops by assigning local leads and moving architecture approvals closer to delivery squads."
                        if risk >= 60
                        else "Keep hierarchy stable and publish decision-rights for recurring handoffs."
                    ),
                    evidence=[f"hierarchy_depth={depth}", f"headcount={len(employees_in_dept)}", f"bottleneck={bottleneck.manager_name if bottleneck else 'none'}"],
                )
            )
        return sorted(output, key=lambda item: item.reporting_risk, reverse=True)

    def _communication_flows(self, request: OrganizationalOptimizerRequest) -> list[CommunicationFlowInsight]:
        dept_graph = nx.Graph()
        employees = {employee.employee_id: employee for employee in request.employees}
        for employee in request.employees:
            dept_graph.add_node(employee.department)
            for target_id in employee.communicates_with:
                target = employees.get(target_id)
                if not target or target.department == employee.department:
                    continue
                if dept_graph.has_edge(employee.department, target.department):
                    dept_graph[employee.department][target.department]["weight"] += 1
                else:
                    dept_graph.add_edge(employee.department, target.department, weight=1)
        departments = sorted({employee.department for employee in request.employees})
        flows = []
        for index, source in enumerate(departments):
            for target in departments[index + 1 :]:
                if source == target:
                    continue
                if nx.has_path(dept_graph, source, target):
                    path = nx.shortest_path(dept_graph, source, target)
                    direct_weight = dept_graph[source][target]["weight"] if dept_graph.has_edge(source, target) else 0
                    path_length = max(1, len(path) - 1)
                else:
                    path = [source, target]
                    direct_weight = 0
                    path_length = 5
                source_members = [item for item in request.employees if item.department == source]
                target_members = [item for item in request.employees if item.department == target]
                bottleneck = self._communication_bottleneck(source_members + target_members)
                delay = self._clip(path_length * 13 + max(0, 4 - direct_weight) * 9 + (100 - mean([item.collaboration_score for item in source_members + target_members] or [60])) * 0.35)
                flows.append(
                    CommunicationFlowInsight(
                        source_unit=source,
                        target_unit=target,
                        path_length=path_length,
                        bottleneck_employee=bottleneck,
                        delay_risk=round(delay, 2),
                        recommendation=(
                            "Create a direct operating bridge with one accountable decision owner and shared async decision log."
                            if delay >= 55
                            else "Maintain direct communication path and keep decision logs visible."
                        ),
                        evidence=[f"path={' -> '.join(path)}", f"direct_edges={direct_weight}", f"avg_collaboration={round(mean([item.collaboration_score for item in source_members + target_members] or [0]), 1)}"],
                    )
                )
        return sorted(flows, key=lambda item: item.delay_risk, reverse=True)[:10]

    def _team_recommendations(self, request: OrganizationalOptimizerRequest, manager_load: list[ManagerLoadInsight]) -> list[TeamOptimizationRecommendation]:
        employees_by_team: dict[str, list[OrgEmployeeInput]] = defaultdict(list)
        for employee in request.employees:
            employees_by_team[employee.team].append(employee)
        manager_risk = {item.manager_id: item.overload_risk for item in manager_load}
        recommendations = []
        for team in request.teams:
            members = employees_by_team.get(team.name, [])
            avg_stress = mean([member.stress_score for member in members] or [0])
            avg_collab = mean([member.collaboration_score for member in members] or [70])
            overload = manager_risk.get(team.manager_id, 0)
            pressure = self._clip(team.delivery_pressure * 0.36 + avg_stress * 0.28 + overload * 0.24 + max(0, len(members) - 9) * 4.2 - avg_collab * 0.12)
            if len(members) >= 10 or pressure >= 58:
                structure = "Split into focused platform, reliability, and enablement pods with local technical leads."
                productivity_gain = min(28, 8 + pressure * 0.18 + max(0, len(members) - 10) * 1.4)
                latency_reduction = min(8, 1.5 + pressure * 0.055)
            elif len(members) <= 3 and avg_collab >= 70:
                structure = "Merge with adjacent team while preserving specialist ownership."
                productivity_gain = 6.5
                latency_reduction = 1.2
            else:
                structure = "Keep team stable and clarify handoff ownership."
                productivity_gain = 3.0
                latency_reduction = 0.6
            recommendations.append(
                TeamOptimizationRecommendation(
                    team_id=team.team_id,
                    team_name=team.name,
                    current_size=len(members),
                    recommended_structure=structure,
                    expected_productivity_gain=round(productivity_gain, 2),
                    expected_latency_reduction=round(latency_reduction, 2),
                    confidence=round(min(0.94, 0.72 + pressure / 400), 3),
                    rationale=f"Team pressure {round(pressure)} combines delivery pressure, manager load, collaboration, stress, and team size.",
                )
            )
        return sorted(recommendations, key=lambda item: item.expected_productivity_gain, reverse=True)

    def _silo_risks(self, request: OrganizationalOptimizerRequest) -> list[SiloRiskInsight]:
        employees = {employee.employee_id: employee for employee in request.employees}
        by_unit: dict[str, list[OrgEmployeeInput]] = defaultdict(list)
        for employee in request.employees:
            by_unit[employee.team].append(employee)
        output = []
        for unit, members in by_unit.items():
            internal = 0
            external = 0
            for member in members:
                for target_id in member.communicates_with:
                    target = employees.get(target_id)
                    if not target:
                        continue
                    if target.team == unit:
                        internal += 1
                    else:
                        external += 1
            ratio = external / max(internal + external, 1)
            skill_counter = Counter(skill for member in members for skill in member.skills)
            isolation = self._clip((1 - ratio) * 72 + max(0, 4 - len(skill_counter)) * 6 + mean([member.workload for member in members] or [0]) * 10)
            output.append(
                SiloRiskInsight(
                    unit=unit,
                    silo_risk=round(isolation, 2),
                    external_collaboration_ratio=round(ratio, 3),
                    knowledge_isolation_score=round(isolation * 0.88, 2),
                    recommendation=(
                        "Create cross-functional rituals and rotate one expert into adjacent product/security planning."
                        if isolation >= 55
                        else "Keep current collaboration cadence and monitor external dependency edges."
                    ),
                    evidence=[f"internal_edges={internal}", f"external_edges={external}", f"unique_skills={len(skill_counter)}"],
                )
            )
        return sorted(output, key=lambda item: item.silo_risk, reverse=True)

    def _skill_distribution(self, request: OrganizationalOptimizerRequest) -> list[SkillDistributionInsight]:
        skill_team_counts: dict[str, Counter[str]] = defaultdict(Counter)
        skill_experts: dict[str, set[str]] = defaultdict(set)
        for employee in request.employees:
            for skill in employee.skills:
                normalized = self._normalize(skill)
                skill_team_counts[normalized][employee.team] += 1
                skill_experts[normalized].add(employee.employee_id)
        output = []
        for skill, team_counts in skill_team_counts.items():
            total = sum(team_counts.values())
            dominant_team, dominant_count = team_counts.most_common(1)[0]
            concentration = dominant_count / max(total, 1) * 100
            single_point = total <= 1 or concentration >= 75
            output.append(
                SkillDistributionInsight(
                    skill=skill,
                    expert_count=total,
                    dominant_team=dominant_team,
                    concentration_risk=round(self._clip(concentration + (18 if total <= 2 else 0)), 2),
                    single_point_of_failure=single_point,
                    recommendation=(
                        f"Cross-train {skill} outside {dominant_team} and document operational playbooks in the Knowledge Brain."
                        if single_point or concentration >= 68
                        else f"Maintain current {skill} distribution and monitor expert availability."
                    ),
                    evidence=[f"dominant_team={dominant_team}", f"dominant_count={dominant_count}", f"expert_count={total}"],
                )
            )
        return sorted(output, key=lambda item: item.concentration_risk, reverse=True)[:12]

    def _simulate(self, request: OrganizationalOptimizerRequest, payload: OrganizationalSimulationRequest) -> OrganizationalSimulationResult:
        team_members = [employee for employee in request.employees if employee.team.lower() == payload.target_team.lower()]
        if not team_members and payload.target_team.lower() in {"company", "engineering"}:
            team_members = [employee for employee in request.employees if employee.department.lower() == payload.target_team.lower()] or request.employees
        avg_stress = mean([employee.stress_score for employee in team_members] or [50])
        avg_collab = mean([employee.collaboration_score for employee in team_members] or [65])
        size = len(team_members) or 1
        if payload.scenario_type == "split_team":
            productivity = min(28, max(4, size / max(payload.new_team_count, 1) + avg_stress * 0.12))
            communication = -min(8, payload.new_team_count * 1.2) + max(0, avg_collab - 60) * 0.04
            cost = payload.new_team_count * 18_000
            collaboration = 6 if avg_collab < 68 else 2
            risk = self._clip(64 - productivity + max(0, avg_stress - 60) * 0.22)
            actions = ["Name pod leads", "Move dependencies into explicit ownership queues", "Rebalance overloaded manager reports"]
        elif payload.scenario_type == "merge_teams":
            productivity = 5 if size <= 6 else -4
            communication = -3 if size >= 12 else 4
            cost = -22_000
            collaboration = 3
            risk = self._clip(48 + max(0, size - 12) * 3)
            actions = ["Merge duplicate ceremonies", "Protect specialist ownership", "Publish shared escalation path"]
        elif payload.scenario_type == "reduce_layers":
            productivity = 7.5
            communication = 11
            cost = -35_000 * payload.management_layers_removed
            collaboration = 8
            risk = self._clip(42 + max(0, avg_stress - 55) * 0.22)
            actions = ["Document decision rights", "Move approvals to team leads", "Track escalation quality weekly"]
        elif payload.scenario_type == "create_department":
            productivity = 12
            communication = 6
            cost = 120_000
            collaboration = 5
            risk = self._clip(50 - productivity * 0.6 + avg_stress * 0.18)
            actions = [f"Create {payload.new_department_name} charter", "Assign director-level owner", "Move critical skill ownership into the new department"]
        else:
            productivity = 8
            communication = 7
            cost = 48_000
            collaboration = 7
            risk = self._clip(48 + avg_stress * 0.16)
            actions = ["Redistribute manager reports", "Assign deputy leads", "Review span of control after two sprints"]
        return OrganizationalSimulationResult(
            scenario_type=payload.scenario_type,
            question=payload.question,
            target_team=payload.target_team,
            productivity_impact=round(productivity, 2),
            communication_impact=round(communication, 2),
            cost_impact=round(cost, 2),
            collaboration_impact=round(collaboration, 2),
            risk_impact=round(risk, 2),
            expected_benefit=f"{round(productivity, 1)}% productivity impact and {round(communication, 1)}% communication impact over {payload.horizon_months} months.",
            confidence=round(min(0.93, 0.74 + min(size, 20) / 100), 3),
            required_actions=actions,
            digital_twin_evidence=[
                f"target_size={size}",
                f"avg_stress={round(avg_stress, 1)}",
                f"avg_collaboration={round(avg_collab, 1)}",
                f"horizon_months={payload.horizon_months}",
            ],
        )

    def _forecasts(
        self,
        request: OrganizationalOptimizerRequest,
        manager_load: list[ManagerLoadInsight],
        reporting: list[ReportingStructureInsight],
        silos: list[SiloRiskInsight],
        skills: list[SkillDistributionInsight],
    ) -> list[OrganizationalForecast]:
        headcount = len(request.employees)
        overload = len([item for item in manager_load if item.overload_risk >= 60])
        reporting_pressure = mean([item.reporting_risk for item in reporting] or [0])
        silo_pressure = mean([item.silo_risk for item in silos] or [0])
        skill_pressure = len([item for item in skills if item.single_point_of_failure])
        scale_departments = [item.unit for item in reporting[:2]]
        output = []
        for period, multiplier, confidence in [("6_months", 1.08, 0.88), ("1_year", 1.18, 0.84), ("3_years", 1.52, 0.76)]:
            projected = round(headcount * multiplier)
            leadership_needed = max(0, round(projected / 8) - len(manager_load))
            restructure = self._clip(reporting_pressure * 0.38 + silo_pressure * 0.22 + overload * 7 + skill_pressure * 4 + (multiplier - 1) * 38)
            output.append(
                OrganizationalForecast(
                    period=period,
                    projected_headcount=projected,
                    leadership_roles_needed=leadership_needed,
                    departments_to_scale=scale_departments,
                    restructure_probability=round(restructure, 2),
                    forecast_confidence=confidence,
                    forecast_model=self.forecast_models[min(len(output), len(self.forecast_models) - 1)],
                )
            )
        return output

    def _recommendations(
        self,
        manager_load: list[ManagerLoadInsight],
        reporting: list[ReportingStructureInsight],
        communication: list[CommunicationFlowInsight],
        teams: list[TeamOptimizationRecommendation],
        silos: list[SiloRiskInsight],
        skills: list[SkillDistributionInsight],
        simulations: list[OrganizationalSimulationResult],
    ) -> list[OrganizationalRecommendation]:
        recs = []
        if manager_load:
            top = manager_load[0]
            recs.append(self._recommendation("manager-load", self._risk(top.overload_risk), f"Reduce {top.manager_name}'s span of control", top.recommendation, f"Expected to reduce leadership bottleneck by {round(top.leadership_bottleneck_score * 0.24)}%.", ["reporting_structure_analyzer", "graph_ai_engine"]))
        if reporting:
            top_report = reporting[0]
            recs.append(self._recommendation("reporting", self._risk(top_report.reporting_risk), f"Redesign {top_report.unit} reporting chain", top_report.recommendation, "Shortens decision path and reduces executive approval dependency.", ["reporting_structure_analyzer", "organizational_analytics_engine"]))
        if communication:
            top_flow = communication[0]
            recs.append(self._recommendation("communication", self._risk(top_flow.delay_risk), f"Create direct bridge: {top_flow.source_unit} to {top_flow.target_unit}", top_flow.recommendation, "Improves information flow and reduces delay risk.", ["communication_flow_analyzer", "collaboration_intelligence_engine"]))
        if teams:
            top_team = teams[0]
            recs.append(self._recommendation("team-structure", "high" if top_team.expected_productivity_gain >= 10 else "medium", f"Restructure {top_team.team_name}", top_team.recommended_structure, f"+{round(top_team.expected_productivity_gain)}% expected productivity gain.", ["team_optimization_engine", "team_digital_twin"]))
        if silos:
            top_silo = silos[0]
            recs.append(self._recommendation("silo", self._risk(top_silo.silo_risk), f"Reduce silo risk in {top_silo.unit}", top_silo.recommendation, "Increases cross-functional knowledge flow.", ["collaboration_intelligence_engine", "knowledge_brain"]))
        skill_risk = next((item for item in skills if item.single_point_of_failure), skills[0] if skills else None)
        if skill_risk:
            recs.append(self._recommendation("skills", self._risk(skill_risk.concentration_risk), f"De-risk {skill_risk.skill} concentration", skill_risk.recommendation, "Reduces single-point-of-failure exposure.", ["skill_distribution_engine", "talent_marketplace", "knowledge_brain"]))
        if simulations:
            best = max(simulations, key=lambda item: item.productivity_impact - item.risk_impact * 0.08)
            recs.append(self._recommendation("simulation", self._risk(best.risk_impact), f"Pilot scenario: {best.scenario_type.replace('_', ' ')}", best.required_actions[0], best.expected_benefit, ["organizational_simulation_engine", "company_digital_twin"]))
        return recs[:8]

    def _nodes(self, graph: nx.DiGraph, centrality: dict[str, float]) -> list[OrgGraphNode]:
        nodes = []
        for node_id, attrs in graph.nodes(data=True):
            nodes.append(
                OrgGraphNode(
                    id=str(node_id),
                    label=str(attrs.get("label", node_id)),
                    node_type=attrs.get("node_type", "employee"),
                    department=attrs.get("department"),
                    team=attrs.get("team"),
                    risk_score=round(self._clip(float(attrs.get("risk_score", 0))), 2),
                    centrality=round(float(centrality.get(node_id, 0)), 4),
                    metadata={key: value for key, value in attrs.items() if key not in {"label", "node_type", "department", "team"} and isinstance(value, (str, int, float))},
                )
            )
        return sorted(nodes, key=lambda item: (item.node_type, -item.risk_score, item.label))

    def _edges(self, graph: nx.DiGraph) -> list[OrgGraphEdge]:
        edges = []
        for source, target, attrs in graph.edges(data=True):
            edges.append(
                OrgGraphEdge(
                    source=str(source),
                    target=str(target),
                    edge_type=attrs.get("edge_type", "collaborates_with"),
                    weight=round(float(attrs.get("weight", 1)), 3),
                    risk=round(self._clip(float(attrs.get("risk", 0))), 2),
                    evidence=str(attrs.get("evidence", f"{source} -> {target}")),
                )
            )
        return sorted(edges, key=lambda item: (item.edge_type, item.source, item.target))

    def _summary(
        self,
        nodes: list[OrgGraphNode],
        edges: list[OrgGraphEdge],
        manager_load: list[ManagerLoadInsight],
        communication: list[CommunicationFlowInsight],
        teams: list[TeamOptimizationRecommendation],
        silos: list[SiloRiskInsight],
        skills: list[SkillDistributionInsight],
        reporting: list[ReportingStructureInsight],
    ) -> OrganizationalOptimizerSummary:
        overloaded = len([item for item in manager_load if item.overload_risk >= 60])
        bottlenecks = len([item for item in communication if item.delay_risk >= 55])
        high_silos = len([item for item in silos if item.silo_risk >= 55])
        critical_skills = len([item for item in skills if item.single_point_of_failure or item.concentration_risk >= 72])
        latency = mean([item.reporting_risk for item in reporting] + [item.delay_risk for item in communication] or [0])
        restructure = len([item for item in teams if item.expected_productivity_gain >= 7])
        health = self._clip(100 - overloaded * 6 - bottlenecks * 3 - high_silos * 4 - min(critical_skills, 5) * 2 - latency * 0.12)
        return OrganizationalOptimizerSummary(
            organizational_health_score=round(health, 2),
            graph_nodes=len(nodes),
            graph_edges=len(edges),
            overloaded_managers=overloaded,
            communication_bottlenecks=bottlenecks,
            high_silo_units=high_silos,
            critical_skill_concentrations=critical_skills,
            restructure_recommendations=restructure,
            average_decision_latency_risk=round(latency, 2),
        )

    @staticmethod
    def _executive_brief(
        summary: OrganizationalOptimizerSummary,
        manager_load: list[ManagerLoadInsight],
        communication: list[CommunicationFlowInsight],
        teams: list[TeamOptimizationRecommendation],
        silos: list[SiloRiskInsight],
        skills: list[SkillDistributionInsight],
    ) -> str:
        manager = manager_load[0].manager_name if manager_load else "no manager"
        flow = f"{communication[0].source_unit} to {communication[0].target_unit}" if communication else "no critical communication path"
        team = teams[0].team_name if teams else "no team"
        silo = silos[0].unit if silos else "no silo"
        skill = skills[0].skill if skills else "no critical skill"
        return (
            f"Organizational health is {round(summary.organizational_health_score)}%. "
            f"Top manager-load risk is {manager}; top communication risk is {flow}; top restructuring candidate is {team}. "
            f"Silo pressure is highest in {silo}, and skill concentration is highest around {skill}."
        )

    def _answer(
        self,
        intent,
        analysis: OrganizationalOptimizerResponse,
        simulation: OrganizationalSimulationResult | None,
    ) -> tuple[str, list[str]]:
        if intent == "manager_overload":
            top = analysis.manager_load[0]
            return (
                f"{top.manager_name} is the most overloaded manager with {top.direct_reports} direct reports and {round(top.overload_risk)}% overload risk. {top.recommendation}",
                top.evidence,
            )
        if intent == "communication_gaps":
            top = analysis.communication_flows[0]
            return (
                f"The highest communication delay risk is {top.source_unit} to {top.target_unit} at {round(top.delay_risk)}%. Bottleneck: {top.bottleneck_employee}. {top.recommendation}",
                top.evidence,
            )
        if intent == "simulation" and simulation:
            return (
                f"Simulation result for {simulation.target_team}: productivity impact {simulation.productivity_impact}%, communication impact {simulation.communication_impact}%, risk impact {simulation.risk_impact}%. {simulation.required_actions[0]}",
                simulation.digital_twin_evidence,
            )
        if intent == "skills":
            top = analysis.skill_distribution[0]
            return (
                f"{top.skill} has the highest concentration risk at {round(top.concentration_risk)}%, dominated by {top.dominant_team}. {top.recommendation}",
                top.evidence,
            )
        if intent == "reporting_structure":
            top = analysis.reporting_structure[0]
            return (
                f"{top.unit} has the highest reporting risk at {round(top.reporting_risk)}% with hierarchy depth {top.hierarchy_depth}. {top.recommendation}",
                top.evidence,
            )
        if intent == "recommendation":
            top = analysis.recommendations[0]
            return (f"Recommended action: {top.action}. Reason: {top.reason}. Expected improvement: {top.expected_improvement}", [top.reason])
        top = analysis.recommendations[0]
        return (f"{analysis.executive_brief} Priority action: {top.action}.", [analysis.executive_brief, *top.source_systems])

    @staticmethod
    def _intent(question: str):
        text = question.lower()
        if any(token in text for token in ["simulate", "what happens", "split", "merge", "reduce layers", "new department"]):
            return "simulation"
        if any(token in text for token in ["manager", "overload", "span"]):
            return "manager_overload"
        if any(token in text for token in ["reporting", "hierarchy", "structure"]):
            return "reporting_structure"
        if any(token in text for token in ["communication", "bottleneck", "gap"]):
            return "communication_gaps"
        if any(token in text for token in ["skill", "expertise", "single point"]):
            return "skills"
        if any(token in text for token in ["recommend", "better", "improve"]):
            return "recommendation"
        if "bottleneck" in text:
            return "bottlenecks"
        return "summary"

    @staticmethod
    def _scenario_from_question(question: str, horizon_months: int) -> OrganizationalSimulationRequest:
        text = question.lower()
        count_match = re.search(r"(\d+)\s+teams?", text)
        count = int(count_match.group(1)) if count_match else 3
        target = "Engineering Platform" if "engineering" in text or "platform" in text else "Company"
        if "merge" in text:
            return OrganizationalSimulationRequest(scenario_type="merge_teams", question=question, target_team=target, merge_with_team="Application Engineering", horizon_months=horizon_months)
        if "reduce" in text and "layer" in text:
            return OrganizationalSimulationRequest(scenario_type="reduce_layers", question=question, target_team=target, management_layers_removed=1, horizon_months=horizon_months)
        if "department" in text:
            return OrganizationalSimulationRequest(scenario_type="create_department", question=question, target_team=target, new_department_name="Platform Reliability", horizon_months=horizon_months)
        return OrganizationalSimulationRequest(scenario_type="split_team", question=question, target_team=target, new_team_count=count, horizon_months=horizon_months)

    @staticmethod
    def _pressure_variant(base: OrganizationalOptimizerRequest, stress_delta: float, communication_drop: float) -> OrganizationalOptimizerRequest:
        employees = [
            employee.model_copy(
                update={
                    "stress_score": min(100, employee.stress_score + stress_delta),
                    "collaboration_score": max(0, employee.collaboration_score - communication_drop),
                    "workload": min(1.5, employee.workload + stress_delta / 200),
                }
            )
            for employee in base.employees
        ]
        teams = [team.model_copy(update={"delivery_pressure": min(100, team.delivery_pressure + stress_delta)}) for team in base.teams]
        return base.model_copy(update={"employees": employees, "teams": teams})

    @staticmethod
    def _depth(employee: OrgEmployeeInput, employees: dict[str, OrgEmployeeInput]) -> int:
        depth = 0
        seen = set()
        current = employee
        while current.manager_id and current.manager_id in employees and current.manager_id not in seen:
            seen.add(current.manager_id)
            depth += 1
            current = employees[current.manager_id]
        return depth

    @staticmethod
    def _communication_bottleneck(employees: list[OrgEmployeeInput]) -> str:
        if not employees:
            return "No active bottleneck"
        ranked = sorted(employees, key=lambda item: (len(item.communicates_with), item.workload, item.stress_score), reverse=True)
        return ranked[0].name

    @staticmethod
    def _recommendation(
        recommendation_id: str,
        priority: OrgRiskLevel,
        action: str,
        reason: str,
        expected_improvement: str,
        source_systems: list[str],
    ) -> OrganizationalRecommendation:
        confidence = {"critical": 0.93, "high": 0.89, "medium": 0.83, "low": 0.76}[priority]
        return OrganizationalRecommendation(
            recommendation_id=f"org-{recommendation_id}",
            priority=priority,
            action=action,
            reason=reason,
            expected_improvement=expected_improvement,
            confidence=confidence,
            source_systems=source_systems,
        )

    @staticmethod
    def _normalize(value: str) -> str:
        return value.strip().lower().replace("_", " ")

    @staticmethod
    def _clip(value: float) -> float:
        return max(0.0, min(100.0, float(value)))

    @staticmethod
    def _risk(score: float) -> OrgRiskLevel:
        if score >= 82:
            return "critical"
        if score >= 65:
            return "high"
        if score >= 42:
            return "medium"
        return "low"

    def _persist(self, response: OrganizationalOptimizerResponse) -> None:
        payload = response.model_dump(mode="json")
        graph_export = {
            "generated_at": payload["generated_at"],
            "nodes": payload["graph_nodes"],
            "edges": payload["graph_edges"],
            "summary": payload["summary"],
            "source_systems": self.source_systems,
        }
        with self._lock:
            with HISTORY_PATH.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, default=str) + "\n")
            GRAPH_EXPORT_PATH.write_text(json.dumps(graph_export, indent=2), encoding="utf-8")


organizational_optimizer_service = OrganizationalOptimizerService()
