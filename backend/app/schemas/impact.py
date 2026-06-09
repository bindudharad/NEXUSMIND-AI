from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class EnterpriseImpactSummary(BaseModel):
    net_savings: float = Field(ge=0)
    baseline_annual_loss: float = Field(ge=0)
    roi_percent: float
    payback_months: float = Field(ge=0)
    platform_score: float = Field(ge=0, le=100)
    capabilities_ready: int = Field(ge=0)
    capabilities_total: int = Field(ge=0)
    realtime_streams: int = Field(ge=0)
    recruiter_score: float = Field(ge=0, le=100)
    judge_wow_score: float = Field(ge=0, le=100)
    residual_risk_level: Literal["low", "medium", "high"]


class EnterpriseImpactResponse(BaseModel):
    model: str
    generated_at: datetime
    summary: EnterpriseImpactSummary
    top_business_insight: str
    strongest_signal: str
    proof_points: list[str]
    source_histories: list[str]


class ExecutiveImpactTeam(BaseModel):
    team_name: str
    department: str
    impact_score: float = Field(ge=0, le=100)
    shortage_score: float = Field(ge=0, le=100)
    delay_risk: float = Field(ge=0, le=100)
    burnout_risk: float = Field(ge=0, le=100)
    knowledge_loss_risk: float = Field(ge=0, le=100)
    reason: str


class ExecutiveImpactRecoveryStrategy(BaseModel):
    immediate_actions: list[str]
    short_term_recovery: list[str]
    long_term_recovery: list[str]
    risk_reduction_actions: list[str]
    executive_recommendations: list[str]


class ExecutiveImpactHiringRequirement(BaseModel):
    required_hires: int = Field(ge=0)
    priority: Literal["low", "medium", "high", "critical"]
    skills_needed: list[str]
    target_teams: list[str]
    urgency_days: int = Field(ge=0)
    rationale: str


class ExecutiveImpactAgentContribution(BaseModel):
    agent: str
    responsibility: str
    finding: str
    recommendation: str
    confidence: float = Field(ge=0, le=1)


class ExecutiveImpactForecastPoint(BaseModel):
    label: str
    financial_loss: float = Field(ge=0)
    delay_probability: float = Field(ge=0, le=100)
    workforce_capacity: float = Field(ge=0, le=100)
    recovery_progress: float = Field(ge=0, le=100)


class ExecutiveImpactAnalysisPanel(BaseModel):
    panel_title: str = "Executive Impact Analysis"
    trigger_type: Literal[
        "what_if_simulation",
        "crisis_simulation",
        "workforce_event",
        "revenue_event",
        "risk_event",
        "strategic_decision",
    ]
    scenario_name: str
    generated_at: datetime
    financial_loss: float = Field(ge=0)
    revenue_impact_percent: float
    profit_impact_percent: float
    cost_increase: float = Field(ge=0)
    productivity_cost: float = Field(ge=0)
    delay_probability: float = Field(ge=0, le=100)
    most_affected_teams: list[ExecutiveImpactTeam]
    recovery_strategy: ExecutiveImpactRecoveryStrategy
    hiring_requirements: ExecutiveImpactHiringRequirement
    risk_level: Literal["low", "medium", "high", "critical"]
    confidence_score: float = Field(ge=0, le=100)
    twin_updates: list[str]
    agent_council: list[ExecutiveImpactAgentContribution]
    forecast_points: list[ExecutiveImpactForecastPoint]
    source_systems: list[str]
    final_verdict: str = "EXECUTIVE IMPACT ANALYSIS COMPLETE"
