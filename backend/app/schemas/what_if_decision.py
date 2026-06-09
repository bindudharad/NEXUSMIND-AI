from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.impact import ExecutiveImpactAnalysisPanel


WhatIfScenarioType = Literal[
    "hiring",
    "layoff",
    "budget_reduction",
    "major_client_loss",
    "international_expansion",
    "engineer_resignation",
    "new_product_launch",
    "department_restructure",
    "revenue_drop",
    "custom",
]
WhatIfRiskLevel = Literal["low", "medium", "high", "critical"]
WhatIfFutureBranchName = Literal[
    "best_case",
    "expected_case",
    "worst_case",
    "optimistic_case",
    "pessimistic_case",
    "ai_recommended_case",
]


class WhatIfScenarioRequest(BaseModel):
    scenario_id: str = Field(default="hire-50-employees", max_length=140)
    scenario_name: str = Field(default="Hire 50 employees", max_length=180)
    question: str = Field(default="What happens if we hire 50 employees?", min_length=4, max_length=800)
    scenario_type: WhatIfScenarioType = "hiring"
    horizon_months: int = Field(default=12, ge=1, le=36)
    employee_delta: int = Field(default=50, ge=-1000, le=1000)
    target_department: str = Field(default="Engineering", max_length=120)
    target_region: str = Field(default="Global", max_length=120)
    budget_delta_percent: float = Field(default=0, ge=-90, le=200)
    revenue_delta_percent: float = Field(default=0, ge=-90, le=200)
    client_loss_percent: float = Field(default=0, ge=0, le=100)
    expansion_investment: float = Field(default=0, ge=0, le=250_000_000)
    new_product_investment: float = Field(default=0, ge=0, le=250_000_000)
    affected_client: str = Field(default="Largest client", max_length=160)
    notes: str = Field(default="", max_length=1200)


class WhatIfScenarioRecord(BaseModel):
    created_at: datetime
    scenario: WhatIfScenarioRequest
    simulation: "WhatIfSimulationResponse"


class WhatIfImpactMetric(BaseModel):
    label: str
    baseline: float
    projected: float
    delta: float
    unit: str
    confidence: float = Field(ge=0, le=1)
    explanation: str


class WhatIfRiskItem(BaseModel):
    risk_id: str
    category: Literal["financial", "workforce", "delivery", "client", "operational", "strategic"]
    title: str
    probability: float = Field(ge=0, le=100)
    impact: float = Field(ge=0, le=100)
    level: WhatIfRiskLevel
    mitigation: str


class WhatIfRecommendation(BaseModel):
    recommendation_id: str
    action: str
    category: str
    priority: WhatIfRiskLevel
    reason: str
    expected_benefit: str
    owner_agent: str
    confidence: float = Field(ge=0, le=1)


class WhatIfScenarioComparison(BaseModel):
    scenario_id: str
    scenario_name: str
    risk_score: float = Field(ge=0, le=100)
    upside_score: float = Field(ge=0, le=100)
    cost_score: float = Field(ge=0, le=100)
    readiness_score: float = Field(ge=0, le=100)
    recommendation: str


class WhatIfFutureBranch(BaseModel):
    case_name: WhatIfFutureBranchName
    probability: float = Field(ge=0, le=100)
    success_probability: float = Field(ge=0, le=100)
    risk_score: float = Field(ge=0, le=100)
    revenue_delta: float
    productivity_delta: float
    burnout_delta: float
    delivery_confidence: float = Field(ge=0, le=100)
    readiness_score: float = Field(ge=0, le=100)
    recommendation: str
    explanation: str


class WhatIfTimelinePoint(BaseModel):
    month: int = Field(ge=0, le=36)
    revenue: float
    cost: float
    profit: float
    productivity: float = Field(ge=0, le=100)
    burnout: float = Field(ge=0, le=100)
    delivery_confidence: float = Field(ge=0, le=100)
    risk_score: float = Field(ge=0, le=100)


class WhatIfCapacityPlan(BaseModel):
    workstations: int = Field(ge=0)
    meeting_rooms: int = Field(ge=0)
    software_licenses: int = Field(ge=0)
    cloud_cost_delta: float
    equipment_cost: float
    office_capacity_risk: float = Field(ge=0, le=100)
    plan: list[str] = Field(default_factory=list)


class WhatIfAgentContribution(BaseModel):
    agent: str
    role: str
    finding: str
    recommendation: str
    confidence: float = Field(ge=0, le=1)
    source_systems: list[str] = Field(default_factory=list)


class WhatIfDigitalTwinSync(BaseModel):
    twin: Literal["employee", "team", "department", "project", "company"]
    entity_count: int = Field(ge=0)
    update: str
    status: Literal["synced", "projected", "watch"]


class WhatIfSimulationResponse(BaseModel):
    model: str
    generated_at: datetime
    scenario: WhatIfScenarioRequest
    executive_summary: str
    risk_level: WhatIfRiskLevel
    success_probability: float = Field(ge=0, le=100)
    decision_readiness_score: float = Field(ge=0, le=100)
    financial_impact: list[WhatIfImpactMetric]
    workforce_impact: list[WhatIfImpactMetric]
    productivity_impact: list[WhatIfImpactMetric]
    burnout_impact: list[WhatIfImpactMetric]
    infrastructure_impact: WhatIfCapacityPlan
    risk_analysis: list[WhatIfRiskItem]
    recommendations: list[WhatIfRecommendation]
    timeline: list[WhatIfTimelinePoint]
    scenario_comparison: list[WhatIfScenarioComparison]
    future_branches: list[WhatIfFutureBranch]
    executive_impact_analysis: ExecutiveImpactAnalysisPanel
    digital_twin_sync: list[WhatIfDigitalTwinSync]
    agent_council: list[WhatIfAgentContribution]
    explanation: list[str]
    forecast_models: list[str]
    source_systems: list[str]
    storage: str
    final_verdict: str


class WhatIfDashboardSummary(BaseModel):
    scenario_count: int = Field(ge=0)
    highest_risk_scenario: str
    recommended_strategy: str
    average_readiness: float = Field(ge=0, le=100)
    production_readiness_score: float = Field(ge=0, le=100)
    innovation_score: float = Field(ge=0, le=100)
    judge_wow_factor_score: float = Field(ge=0, le=100)
    stream_sequence: int = 1


class WhatIfDecisionDashboardResponse(BaseModel):
    model: str
    generated_at: datetime
    dashboard_name: str
    summary: WhatIfDashboardSummary
    scenarios: list[WhatIfSimulationResponse]
    scenario_builder_templates: list[WhatIfScenarioRequest]
    supported_questions: list[str]
    component_status: dict[str, str]
    digital_twin_status: list[WhatIfDigitalTwinSync]
    multi_agent_status: str
    forecast_models: list[str]
    source_systems: list[str]
    storage: str
    final_verdict: str


class WhatIfAssistantRequest(BaseModel):
    question: str = Field(min_length=4, max_length=800)
    session_id: str = Field(default="what-if-strategy-assistant", max_length=120)
    horizon_months: int = Field(default=12, ge=1, le=36)


class WhatIfAssistantResponse(BaseModel):
    model: str
    generated_at: datetime
    question: str
    answer: str
    intent: WhatIfScenarioType
    simulation: WhatIfSimulationResponse
    recommended_actions: list[str]
    cited_evidence: list[str]
    source_systems: list[str]
    storage: str


WhatIfScenarioRecord.model_rebuild()
