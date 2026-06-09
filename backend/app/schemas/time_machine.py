from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


TimeMachineScenarioType = Literal[
    "workload_increase",
    "hiring_freeze",
    "revenue_drop",
    "engineer_resignation",
    "market_expansion",
    "budget_reduction",
    "major_client_loss",
    "custom",
]
TimeMachineRiskLevel = Literal["low", "medium", "high", "critical"]


class TimeMachineScenarioRequest(BaseModel):
    scenario_id: str = Field(default="workload-plus-30", max_length=120)
    scenario_name: str = Field(default="Workload increase +30%", max_length=180)
    question: str = Field(default="What will happen in 6 months if employee workload increases by 30%?", min_length=4, max_length=700)
    scenario_type: TimeMachineScenarioType = "workload_increase"
    horizon_months: int = Field(default=6, ge=1, le=36)
    workload_delta_percent: float = Field(default=30, ge=-50, le=150)
    hiring_freeze_months: int = Field(default=0, ge=0, le=36)
    revenue_delta_percent: float = Field(default=0, ge=-90, le=200)
    resignation_count: int = Field(default=0, ge=0, le=500)
    budget_delta_percent: float = Field(default=0, ge=-80, le=200)
    market_expansion_investment: float = Field(default=0, ge=0, le=100_000_000)
    client_loss_percent: float = Field(default=0, ge=0, le=100)
    affected_department: str = Field(default="Engineering", max_length=120)
    notes: str = Field(default="", max_length=1000)


class TimeMachineAssistantRequest(BaseModel):
    question: str = Field(min_length=4, max_length=700)
    session_id: str = Field(default="company-time-machine", max_length=120)
    horizon_months: int = Field(default=6, ge=1, le=36)


class TimeMachineImpactBlock(BaseModel):
    domain: Literal["workforce", "financial", "project", "client"]
    baseline: float
    projected: float
    delta: float
    unit: str
    risk_score: float = Field(ge=0, le=100)
    explanation: str


class TimeMachineTimelinePoint(BaseModel):
    month: int = Field(ge=0, le=36)
    burnout_risk: float = Field(ge=0, le=100)
    productivity: float = Field(ge=0, le=100)
    attrition_risk: float = Field(ge=0, le=100)
    revenue: float
    profit: float
    project_delay_probability: float = Field(ge=0, le=100)
    client_churn_risk: float = Field(ge=0, le=100)
    team_health: float = Field(ge=0, le=100)


class TimeMachineRiskPrediction(BaseModel):
    risk: str
    domain: str
    probability: float = Field(ge=0, le=100)
    level: TimeMachineRiskLevel
    driver: str
    mitigation: str


class TimeMachineRecommendation(BaseModel):
    action: str
    priority: TimeMachineRiskLevel
    expected_impact: str
    owner_agent: str
    confidence: float = Field(ge=0, le=1)


class TimeMachineExplanation(BaseModel):
    summary: str
    causal_drivers: list[str]
    model_evidence: list[str]
    assumptions: list[str]


class TimeMachineAgentContribution(BaseModel):
    agent: str
    focus: str
    finding: str
    confidence: float = Field(ge=0, le=1)


class TimeMachineSimulationResponse(BaseModel):
    model: str
    generated_at: datetime
    scenario: TimeMachineScenarioRequest
    confidence: float = Field(ge=0, le=1)
    risk_level: TimeMachineRiskLevel
    success_probability: float = Field(ge=0, le=100)
    workforce_impact: TimeMachineImpactBlock
    financial_impact: TimeMachineImpactBlock
    project_impact: TimeMachineImpactBlock
    client_impact: TimeMachineImpactBlock
    timeline: list[TimeMachineTimelinePoint]
    risks: list[TimeMachineRiskPrediction]
    recommendations: list[TimeMachineRecommendation]
    explanation: TimeMachineExplanation
    agent_contributions: list[TimeMachineAgentContribution]
    digital_twin_evidence: list[str]
    forecast_models: list[str]
    source_systems: list[str]
    storage: str


class TimeMachineScenarioRecord(BaseModel):
    created_at: datetime
    scenario: TimeMachineScenarioRequest
    simulation: TimeMachineSimulationResponse


class TimeMachineDashboardSummary(BaseModel):
    scenario_count: int = Field(ge=0)
    highest_risk_scenario: str
    strongest_recommendation: str
    average_confidence: float = Field(ge=0, le=1)
    production_readiness_score: float = Field(ge=0, le=100)
    stream_sequence: int = 1


class TimeMachineDashboardResponse(BaseModel):
    model: str
    generated_at: datetime
    dashboard_name: str
    summary: TimeMachineDashboardSummary
    scenarios: list[TimeMachineSimulationResponse]
    scenario_builder_templates: list[TimeMachineScenarioRequest]
    supported_questions: list[str]
    digital_twin_status: dict[str, object]
    forecast_models: list[str]
    source_systems: list[str]
    storage: str


class TimeMachineAssistantResponse(BaseModel):
    model: str
    generated_at: datetime
    question: str
    intent: TimeMachineScenarioType
    answer: str
    simulation: TimeMachineSimulationResponse
    cited_evidence: list[str]
    recommended_actions: list[str]
    source_systems: list[str]
    storage: str
