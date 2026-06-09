from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


ShadowScenarioType = Literal[
    "hiring",
    "revenue_drop",
    "client_loss",
    "executive_resignation",
    "engineering_resignation",
    "budget_reduction",
    "market_expansion",
    "security_incident",
    "custom",
]
ShadowRiskLevel = Literal["low", "medium", "high", "critical"]
ShadowSyncStatus = Literal["synced", "projected", "watch"]
ShadowRealityCase = Literal[
    "best_case",
    "expected_case",
    "worst_case",
    "optimistic_case",
    "pessimistic_case",
    "ai_recommended_case",
]


class ShadowDecisionSimulationRequest(BaseModel):
    scenario_id: str = Field(default="shadow-hire-100-engineers", max_length=140)
    scenario_name: str = Field(default="Hire 100 engineers in the Shadow Company", max_length=180)
    question: str = Field(default="What if we hire 100 engineers?", min_length=4, max_length=800)
    scenario_type: ShadowScenarioType = "hiring"
    horizon_months: int = Field(default=12, ge=1, le=36)
    employee_delta: int = Field(default=100, ge=-1000, le=2000)
    workload_delta_percent: float = Field(default=0, ge=-90, le=200)
    budget_delta_percent: float = Field(default=0, ge=-90, le=200)
    revenue_delta_percent: float = Field(default=0, ge=-90, le=200)
    client_loss_percent: float = Field(default=0, ge=0, le=100)
    target_department: str = Field(default="Engineering", max_length=120)
    target_market: str = Field(default="Global", max_length=120)
    security_incident: bool = False
    notes: str = Field(default="", max_length=1200)


class ShadowMirrorSummary(BaseModel):
    real_time_mirroring_status: Literal["active", "degraded", "missing"]
    sync_completeness: float = Field(ge=0, le=100)
    employees_mirrored: int = Field(ge=0)
    teams_mirrored: int = Field(ge=0)
    departments_mirrored: int = Field(ge=0)
    projects_mirrored: int = Field(ge=0)
    clients_mirrored: int = Field(ge=0)
    workflows_mirrored: int = Field(ge=0)
    revenue_modeled: float
    costs_modeled: float
    productivity_modeled: float = Field(ge=0, le=100)
    risks_modeled: int = Field(ge=0)
    knowledge_network_nodes: int = Field(ge=0)
    communication_network_edges: int = Field(ge=0)
    last_sync_at: datetime
    production_readiness_score: float = Field(ge=0, le=100)
    innovation_score: float = Field(ge=0, le=100)
    judge_wow_factor_score: float = Field(ge=0, le=100)
    stream_sequence: int = 1


class ShadowCompanyState(BaseModel):
    state_id: str
    label: str
    employees: int = Field(ge=0)
    teams: int = Field(ge=0)
    departments: int = Field(ge=0)
    projects: int = Field(ge=0)
    clients: int = Field(ge=0)
    revenue: float
    costs: float
    productivity: float = Field(ge=0, le=100)
    workforce_health: float = Field(ge=0, le=100)
    risk_score: float = Field(ge=0, le=100)
    growth_score: float = Field(ge=0, le=100)
    explanation: str


class ShadowEmployee(BaseModel):
    employee_id: str
    name: str
    role: str
    department: str
    skills: list[str]
    productivity_score: float = Field(ge=0, le=100)
    burnout_risk: float = Field(ge=0, le=100)
    growth_potential: float = Field(ge=0, le=100)
    attrition_risk: float = Field(ge=0, le=100)
    leadership_influence: float = Field(ge=0, le=100)
    future_readiness: float = Field(ge=0, le=100)
    twin_status: ShadowSyncStatus = "synced"


class ShadowProject(BaseModel):
    project_id: str
    name: str
    owning_team: str
    timeline_risk: float = Field(ge=0, le=100)
    budget_risk: float = Field(ge=0, le=100)
    dependency_risk: float = Field(ge=0, le=100)
    resource_shortage_risk: float = Field(ge=0, le=100)
    delivery_confidence: float = Field(ge=0, le=100)
    predicted_delay_weeks: float = Field(ge=0)
    twin_status: ShadowSyncStatus = "synced"


class ShadowDepartment(BaseModel):
    department_id: str
    name: str
    performance_score: float = Field(ge=0, le=100)
    morale_score: float = Field(ge=0, le=100)
    productivity_score: float = Field(ge=0, le=100)
    capacity_score: float = Field(ge=0, le=100)
    communication_health: float = Field(ge=0, le=100)
    risk_score: float = Field(ge=0, le=100)
    twin_status: ShadowSyncStatus = "synced"


class ShadowFutureState(BaseModel):
    horizon_label: Literal["30_days", "90_days", "6_months", "12_months"]
    scenario_name: str
    probability: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    revenue_forecast: float
    cost_forecast: float
    productivity_forecast: float = Field(ge=0, le=100)
    workforce_health: float = Field(ge=0, le=100)
    risk_score: float = Field(ge=0, le=100)
    growth_score: float = Field(ge=0, le=100)
    recommendation: str
    drivers: list[str]


class ShadowRealitySimulation(BaseModel):
    case_name: ShadowRealityCase
    probability: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    risk_score: float = Field(ge=0, le=100)
    growth_score: float = Field(ge=0, le=100)
    revenue_delta_percent: float
    workforce_delta_percent: float
    summary: str
    actions: list[str]


class ShadowImpactDelta(BaseModel):
    label: str
    baseline: float
    projected: float
    delta: float
    unit: str
    explanation: str


class ShadowAgentContribution(BaseModel):
    agent: str
    role: str
    finding: str
    action: str
    confidence: float = Field(ge=0, le=1)
    source_systems: list[str] = Field(default_factory=list)


class ShadowIntegrationSignal(BaseModel):
    system: str
    status: Literal["connected", "projected", "watch"]
    update: str
    evidence: list[str] = Field(default_factory=list)


class ShadowRealityVisualization(BaseModel):
    engine: str
    status: Literal["ready", "degraded", "missing"]
    real_company_nodes: int = Field(ge=0)
    shadow_company_nodes: int = Field(ge=0)
    future_branches: int = Field(ge=0)
    risk_paths: int = Field(ge=0)
    growth_paths: int = Field(ge=0)
    decision_tree_depth: int = Field(ge=0)
    rendering_strategy: str


class ShadowCompanyStatusReport(BaseModel):
    shadow_company_status: Literal["working", "partial", "missing"]
    synchronization_engine_status: Literal["working", "partial", "missing"]
    employee_shadow_status: Literal["working", "partial", "missing"]
    project_shadow_status: Literal["working", "partial", "missing"]
    department_shadow_status: Literal["working", "partial", "missing"]
    future_state_generator_status: Literal["working", "partial", "missing"]
    decision_testing_status: Literal["working", "partial", "missing"]
    multi_reality_simulation_status: Literal["working", "partial", "missing"]
    ai_agent_ecosystem_status: Literal["working", "partial", "missing"]
    knowledge_brain_integration_status: Literal["working", "partial", "missing"]
    organizational_brain_integration_status: Literal["working", "partial", "missing"]
    dashboard_status: Literal["working", "partial", "missing"]
    visualization_status: Literal["working", "partial", "missing"]
    digital_twin_integration_status: Literal["working", "partial", "missing"]
    missing_components: list[str]
    fixed_components: list[str]
    errors_found: list[str]
    errors_fixed: list[str]
    performance_metrics: dict[str, float]
    production_readiness_score: float = Field(ge=0, le=100)
    innovation_score: float = Field(ge=0, le=100)
    judge_wow_factor_score: float = Field(ge=0, le=100)
    final_verdict: str


class ShadowDecisionSimulationResponse(BaseModel):
    model: str
    generated_at: datetime
    scenario: ShadowDecisionSimulationRequest
    executive_summary: str
    baseline_outcome: ShadowCompanyState
    simulated_outcome: ShadowCompanyState
    impact_delta: list[ShadowImpactDelta]
    risk_level: ShadowRiskLevel
    success_probability: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    recommendations: list[str]
    agent_contributions: list[ShadowAgentContribution]
    future_states: list[ShadowFutureState]
    multi_reality_simulations: list[ShadowRealitySimulation]
    integration_signals: list[ShadowIntegrationSignal]
    source_systems: list[str]
    storage: str
    final_verdict: str


class ShadowCompanyDashboardResponse(BaseModel):
    model: str
    generated_at: datetime
    dashboard_name: str
    executive_brief: str
    summary: ShadowMirrorSummary
    real_company_state: ShadowCompanyState
    shadow_company_state: ShadowCompanyState
    shadow_employees: list[ShadowEmployee]
    shadow_projects: list[ShadowProject]
    shadow_departments: list[ShadowDepartment]
    future_states: list[ShadowFutureState]
    multi_reality_simulations: list[ShadowRealitySimulation]
    decision_testing_templates: list[ShadowDecisionSimulationRequest]
    latest_decision_test: ShadowDecisionSimulationResponse
    integration_signals: list[ShadowIntegrationSignal]
    agent_ecosystem: list[ShadowAgentContribution]
    shadow_reality_visualization: ShadowRealityVisualization
    status_report: ShadowCompanyStatusReport
    supported_questions: list[str]
    source_systems: list[str]
    storage: str
    final_verdict: str


class ShadowCompanyAssistantRequest(BaseModel):
    question: str = Field(default="Show the most likely company future.", min_length=4, max_length=800)
    session_id: str = Field(default="shadow-company-assistant", max_length=120)
    horizon_months: int = Field(default=12, ge=1, le=36)


class ShadowCompanyAssistantResponse(BaseModel):
    model: str
    generated_at: datetime
    question: str
    answer: str
    intent: ShadowScenarioType
    simulation: ShadowDecisionSimulationResponse
    recommended_actions: list[str]
    cited_evidence: list[str]
    source_systems: list[str]
    storage: str
    final_verdict: str
