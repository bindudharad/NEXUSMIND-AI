from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


SimulationScenarioType = Literal[
    "work_from_home_policy",
    "hiring_freeze",
    "employee_resignation",
    "department_restructure",
    "budget_reduction",
    "meeting_reduction",
    "hiring_growth",
    "revenue_change",
    "client_loss",
    "market_expansion",
]
SimulationRiskLevel = Literal["low", "medium", "high", "critical"]
SimulationMode = Literal["default", "stress", "optimistic"]
FutureBranchName = Literal["best_case", "expected_case", "worst_case", "optimistic_case", "pessimistic_case", "ai_recommended_case"]


class CompanySimulationScenarioRequest(BaseModel):
    scenario_id: str = "hybrid-policy-shift"
    scenario_type: SimulationScenarioType = "work_from_home_policy"
    question: str = "What happens if work-from-home is reduced from 5 days to 2 days?"
    mode: SimulationMode = "default"
    horizon_months: int = Field(default=12, ge=3, le=36)
    remote_days_before: int = Field(default=5, ge=0, le=5)
    remote_days_after: int = Field(default=2, ge=0, le=5)
    hiring_freeze_months: int = Field(default=6, ge=0, le=36)
    resignation_count: int = Field(default=20, ge=0, le=500)
    resignation_seniority: str = Field(default="mixed", max_length=40)
    source_department: str = Field(default="Engineering", max_length=120)
    target_department: str = Field(default="Security", max_length=120)
    restructure_type: str = Field(default="merge", max_length=80)
    budget_reduction_percent: float = Field(default=20, ge=0, le=80)
    meeting_reduction_percent: float = Field(default=50, ge=0, le=90)
    hiring_count: int = Field(default=50, ge=0, le=1000)
    revenue_change_percent: float = Field(default=-20, ge=-90, le=200)
    client_loss_percent: float = Field(default=20, ge=0, le=100)
    office_count: int = Field(default=1, ge=0, le=20)
    expansion_cost_percent: float = Field(default=12, ge=0, le=80)
    affected_roles: list[str] = Field(default_factory=list, max_length=20)


class CompanySimulationLabRequest(BaseModel):
    lab_name: str = "Executive Business Flight Simulator"
    horizon_months: int = Field(default=12, ge=3, le=36)
    scenarios: list[CompanySimulationScenarioRequest] = Field(default_factory=list, max_length=12)
    compare: bool = True


class CompanySimulationAssistantRequest(BaseModel):
    question: str = Field(min_length=2, max_length=700)
    session_id: str = "company-simulation-lab"
    horizon_months: int = Field(default=12, ge=3, le=36)


class SimulationImpactVector(BaseModel):
    productivity_change: float
    employee_happiness_change: float
    attrition_risk_change: float
    burnout_change: float
    recruitment_difficulty_change: float
    collaboration_change: float
    financial_impact: float
    revenue_impact: float
    delivery_delay_days: float = Field(ge=0)
    operational_risk_change: float
    growth_impact: float


class SimulationMetricForecast(BaseModel):
    metric: str
    baseline: float
    projected: float
    delta: float
    unit: str
    confidence: float = Field(ge=0, le=1)
    model: str


class SimulationRiskHeatmapItem(BaseModel):
    domain: str
    risk_score: float = Field(ge=0, le=100)
    risk_level: SimulationRiskLevel
    driver: str
    mitigation: str


class SimulationRecommendation(BaseModel):
    title: str
    priority: SimulationRiskLevel
    action: str
    rationale: str
    expected_benefit: str
    confidence: float = Field(ge=0, le=1)


class EmployeeMovementFrame(BaseModel):
    month: int = Field(ge=0)
    label: str
    hires: int = Field(ge=0)
    exits: int = Field(ge=0)
    transfers: int = Field(ge=0)
    net_headcount_change: int
    explanation: str


class TeamStressFrame(BaseModel):
    team: str
    baseline_stress: float = Field(ge=0, le=100)
    projected_stress: float = Field(ge=0, le=100)
    risk_level: SimulationRiskLevel
    color: str
    explanation: str


class ProjectHealthFrame(BaseModel):
    project: str
    baseline_state: str
    projected_state: str
    delay_days: float = Field(ge=0)
    risk_score: float = Field(ge=0, le=100)
    color: str
    explanation: str


class RevenueEvolutionPoint(BaseModel):
    month: int = Field(ge=0)
    current: float
    best_case: float
    expected_case: float
    worst_case: float


class RiskPropagationStep(BaseModel):
    step: int = Field(ge=1)
    title: str
    source: str
    target: str
    risk_score: float = Field(ge=0, le=100)
    explanation: str


class MultiFutureBranch(BaseModel):
    case_name: FutureBranchName
    probability: float = Field(ge=0, le=100)
    success_probability: float = Field(ge=0, le=100)
    risk_score: float = Field(ge=0, le=100)
    revenue_impact: float
    workforce_health_delta: float
    summary: str


class SimulationAgentContribution(BaseModel):
    agent: str
    role: str
    finding: str
    recommendation: str
    confidence: float = Field(ge=0, le=1)
    source_systems: list[str] = Field(default_factory=list)


class ShadowCompanyStage(BaseModel):
    stage: str
    label: str
    health_score: float = Field(ge=0, le=100)
    risk_score: float = Field(ge=0, le=100)
    revenue: float
    workforce: int = Field(ge=0)
    explanation: str


class ScenarioSimulationResult(BaseModel):
    scenario_id: str
    scenario_type: SimulationScenarioType
    question: str
    executive_summary: str
    confidence: float = Field(ge=0, le=1)
    success_probability: float = Field(ge=0, le=100)
    impact: SimulationImpactVector
    forecasts: list[SimulationMetricForecast]
    risk_heatmap: list[SimulationRiskHeatmapItem]
    recommendations: list[SimulationRecommendation]
    required_actions: list[str]
    resource_adjustments: list[str]
    staffing_changes: list[str]
    employee_movement: list[EmployeeMovementFrame]
    team_stress_evolution: list[TeamStressFrame]
    project_health_visualization: list[ProjectHealthFrame]
    revenue_evolution: list[RevenueEvolutionPoint]
    risk_propagation_path: list[RiskPropagationStep]
    multi_future_branches: list[MultiFutureBranch]
    agent_council: list[SimulationAgentContribution]
    shadow_company_stages: list[ShadowCompanyStage]
    ai_explanation: str
    visualization_engine_status: Literal["ready", "degraded"] = "ready"
    digital_twin_evidence: list[str]
    source_systems: list[str]
    forecast_models: list[str]
    comparison_score: float = Field(ge=0, le=100)


class ScenarioComparisonItem(BaseModel):
    rank: int = Field(ge=1)
    scenario_id: str
    scenario_type: SimulationScenarioType
    label: str
    score: float = Field(ge=0, le=100)
    success_probability: float = Field(ge=0, le=100)
    risk_level: SimulationRiskLevel
    tradeoff_summary: str


class SimulationDashboardSummary(BaseModel):
    scenario_count: int = Field(ge=0)
    recommended_scenario: str
    safest_scenario: str
    highest_risk_scenario: str
    average_confidence: float = Field(ge=0, le=1)
    decision_readiness_score: float = Field(ge=0, le=100)
    top_risk: str
    stream_sequence: int = 1


class CompanySimulationLabResponse(BaseModel):
    model: str
    generated_at: datetime
    lab_name: str
    horizon_months: int
    summary: SimulationDashboardSummary
    scenarios: list[ScenarioSimulationResult]
    comparison: list[ScenarioComparisonItem]
    executive_recommendations: list[SimulationRecommendation]
    supported_questions: list[str]
    source_systems: list[str]
    forecast_models: list[str]
    storage: str


class CompanySimulationAssistantResponse(BaseModel):
    model: str
    generated_at: datetime
    question: str
    intent: str
    answer: str
    confidence: float = Field(ge=0, le=1)
    scenario: ScenarioSimulationResult | None = None
    comparison: list[ScenarioComparisonItem] = Field(default_factory=list)
    recommended_actions: list[str]
    cited_evidence: list[str]
    source_systems: list[str]
    storage: str
