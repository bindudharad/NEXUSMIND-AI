from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


OrgRiskLevel = Literal["low", "medium", "high", "critical"]
OrgNodeType = Literal["employee", "manager", "team", "department", "project", "location", "skill"]
OrgEdgeType = Literal["reports_to", "collaborates_with", "works_on", "mentors", "communicates_with", "belongs_to", "has_skill"]
OrgScenarioType = Literal["split_team", "merge_teams", "reduce_layers", "create_department", "rebalance_leadership"]
OrgAssistantIntent = Literal["bottlenecks", "manager_overload", "reporting_structure", "communication_gaps", "simulation", "skills", "recommendation", "summary"]


class OrgEmployeeInput(BaseModel):
    employee_id: str
    name: str
    role: str
    department: str
    team: str
    manager_id: str | None = None
    location: str = "Bangalore"
    skills: list[str] = Field(default_factory=list, max_length=30)
    projects: list[str] = Field(default_factory=list, max_length=20)
    communicates_with: list[str] = Field(default_factory=list, max_length=50)
    mentors: list[str] = Field(default_factory=list, max_length=20)
    workload: float = Field(default=0.65, ge=0, le=1.5)
    stress_score: float = Field(default=35, ge=0, le=100)
    collaboration_score: float = Field(default=72, ge=0, le=100)
    leadership_score: float = Field(default=55, ge=0, le=100)
    productivity_score: float = Field(default=72, ge=0, le=100)


class OrgTeamInput(BaseModel):
    team_id: str
    name: str
    department: str
    manager_id: str
    location: str = "Bangalore"
    strategic_importance: float = Field(default=0.65, ge=0, le=1)
    delivery_pressure: float = Field(default=45, ge=0, le=100)


class OrganizationalOptimizerRequest(BaseModel):
    cycle_name: str = "Realtime Organizational Design Review"
    employees: list[OrgEmployeeInput] = Field(default_factory=list, max_length=2000)
    teams: list[OrgTeamInput] = Field(default_factory=list, max_length=300)
    horizon_months: int = Field(default=12, ge=3, le=36)
    realtime: bool = True


class OrganizationalSimulationRequest(BaseModel):
    scenario_type: OrgScenarioType = "split_team"
    question: str = "What happens if Engineering Platform splits into 3 teams?"
    target_team: str = "Engineering Platform"
    merge_with_team: str | None = None
    new_team_count: int = Field(default=3, ge=1, le=12)
    management_layers_removed: int = Field(default=1, ge=0, le=5)
    new_department_name: str = "Platform Reliability"
    horizon_months: int = Field(default=12, ge=3, le=36)


class OrganizationalAssistantRequest(BaseModel):
    question: str = Field(min_length=2, max_length=700)
    session_id: str = "organizational-optimizer"
    horizon_months: int = Field(default=12, ge=3, le=36)


class OrgGraphNode(BaseModel):
    id: str
    label: str
    node_type: OrgNodeType
    department: str | None = None
    team: str | None = None
    risk_score: float = Field(default=0, ge=0, le=100)
    centrality: float = Field(default=0, ge=0, le=1)
    metadata: dict[str, str | float | int] = Field(default_factory=dict)


class OrgGraphEdge(BaseModel):
    source: str
    target: str
    edge_type: OrgEdgeType
    weight: float = Field(default=1, ge=0, le=10)
    risk: float = Field(default=0, ge=0, le=100)
    evidence: str


class ManagerLoadInsight(BaseModel):
    manager_id: str
    manager_name: str
    department: str
    direct_reports: int = Field(ge=0)
    span_of_control: float = Field(ge=0)
    overload_risk: float = Field(ge=0, le=100)
    leadership_bottleneck_score: float = Field(ge=0, le=100)
    recommendation: str
    evidence: list[str]


class ReportingStructureInsight(BaseModel):
    unit: str
    hierarchy_depth: int = Field(ge=0)
    excessive_layers: bool
    leadership_bottleneck: str
    reporting_risk: float = Field(ge=0, le=100)
    recommendation: str
    evidence: list[str]


class CommunicationFlowInsight(BaseModel):
    source_unit: str
    target_unit: str
    path_length: int = Field(ge=0)
    bottleneck_employee: str
    delay_risk: float = Field(ge=0, le=100)
    recommendation: str
    evidence: list[str]


class TeamOptimizationRecommendation(BaseModel):
    team_id: str
    team_name: str
    current_size: int = Field(ge=0)
    recommended_structure: str
    expected_productivity_gain: float
    expected_latency_reduction: float
    confidence: float = Field(ge=0, le=1)
    rationale: str


class SiloRiskInsight(BaseModel):
    unit: str
    silo_risk: float = Field(ge=0, le=100)
    external_collaboration_ratio: float = Field(ge=0, le=1)
    knowledge_isolation_score: float = Field(ge=0, le=100)
    recommendation: str
    evidence: list[str]


class SkillDistributionInsight(BaseModel):
    skill: str
    expert_count: int = Field(ge=0)
    dominant_team: str
    concentration_risk: float = Field(ge=0, le=100)
    single_point_of_failure: bool
    recommendation: str
    evidence: list[str]


class OrganizationalSimulationResult(BaseModel):
    scenario_type: OrgScenarioType
    question: str
    target_team: str
    productivity_impact: float
    communication_impact: float
    cost_impact: float
    collaboration_impact: float
    risk_impact: float = Field(ge=0, le=100)
    expected_benefit: str
    confidence: float = Field(ge=0, le=1)
    required_actions: list[str]
    digital_twin_evidence: list[str]


class OrganizationalForecast(BaseModel):
    period: Literal["6_months", "1_year", "3_years"]
    projected_headcount: int = Field(ge=0)
    leadership_roles_needed: int = Field(ge=0)
    departments_to_scale: list[str]
    restructure_probability: float = Field(ge=0, le=100)
    forecast_confidence: float = Field(ge=0, le=1)
    forecast_model: str


class OrganizationalRecommendation(BaseModel):
    recommendation_id: str
    priority: OrgRiskLevel
    action: str
    reason: str
    expected_improvement: str
    confidence: float = Field(ge=0, le=1)
    source_systems: list[str]


class OrganizationalOptimizerSummary(BaseModel):
    organizational_health_score: float = Field(ge=0, le=100)
    graph_nodes: int = Field(ge=0)
    graph_edges: int = Field(ge=0)
    overloaded_managers: int = Field(ge=0)
    communication_bottlenecks: int = Field(ge=0)
    high_silo_units: int = Field(ge=0)
    critical_skill_concentrations: int = Field(ge=0)
    restructure_recommendations: int = Field(ge=0)
    average_decision_latency_risk: float = Field(ge=0, le=100)
    stream_sequence: int = 1


class OrganizationalOptimizerResponse(BaseModel):
    model: str
    generated_at: datetime
    cycle_name: str
    summary: OrganizationalOptimizerSummary
    graph_nodes: list[OrgGraphNode]
    graph_edges: list[OrgGraphEdge]
    manager_load: list[ManagerLoadInsight]
    reporting_structure: list[ReportingStructureInsight]
    communication_flows: list[CommunicationFlowInsight]
    team_recommendations: list[TeamOptimizationRecommendation]
    silo_risks: list[SiloRiskInsight]
    skill_distribution: list[SkillDistributionInsight]
    simulations: list[OrganizationalSimulationResult]
    forecasts: list[OrganizationalForecast]
    recommendations: list[OrganizationalRecommendation]
    executive_brief: str
    supported_questions: list[str]
    source_systems: list[str]
    storage: str


class OrganizationalAssistantResponse(BaseModel):
    model: str
    generated_at: datetime
    question: str
    intent: OrgAssistantIntent
    answer: str
    confidence: float = Field(ge=0, le=1)
    cited_evidence: list[str]
    recommended_actions: list[str]
    simulation: OrganizationalSimulationResult | None = None
    source_systems: list[str]
    storage: str
