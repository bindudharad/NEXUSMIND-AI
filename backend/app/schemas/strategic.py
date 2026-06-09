from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.impact import ExecutiveImpactAnalysisPanel
from app.schemas.shadow_company import ShadowDecisionSimulationResponse
from app.schemas.what_if_decision import WhatIfSimulationResponse


RiskLevel = Literal["low", "medium", "high", "critical"]


class CompetitorSignalInput(BaseModel):
    name: str
    hiring_velocity: int = Field(ge=0, le=500)
    product_launches_90d: int = Field(ge=0, le=50)
    ai_mentions_30d: int = Field(ge=0, le=1000)
    funding_signal: float = Field(ge=0, le=1)
    security_incidents: int = Field(ge=0, le=50)
    technology_adoption_score: float = Field(ge=0, le=100)
    market_sentiment: float = Field(ge=-1, le=1)


class ClientSignalInput(BaseModel):
    client_id: str
    name: str
    contract_value: float = Field(ge=0, le=100_000_000)
    delivery_slippage_days: int = Field(ge=0, le=365)
    sentiment_score: float = Field(ge=-1, le=1)
    payment_delay_days: int = Field(ge=0, le=365)
    escalation_count: int = Field(ge=0, le=100)
    usage_trend_percent: float = Field(ge=-100, le=200)
    executive_engagement_score: float = Field(ge=0, le=100)


class TalentProfileInput(BaseModel):
    employee_id: str
    name: str
    role: str
    department: str
    skills: list[str] = Field(default_factory=list, max_length=80)
    mentor_topics: list[str] = Field(default_factory=list, max_length=40)
    capacity_hours: float = Field(ge=0, le=120)
    allocated_hours: float = Field(ge=0, le=160)
    stress_score: float = Field(ge=0, le=100)
    leadership_score: float = Field(ge=0, le=100)
    innovation_signals: int = Field(ge=0, le=100)


class ProjectOpportunityInput(BaseModel):
    project_id: str
    title: str
    department: str
    required_skills: list[str] = Field(default_factory=list, max_length=60)
    priority: int = Field(ge=1, le=5)
    revenue_impact: float = Field(ge=0, le=100_000_000)
    deadline_pressure: float = Field(ge=0, le=100)


class OrgUnitSignalInput(BaseModel):
    unit: str
    headcount: int = Field(ge=1, le=100_000)
    manager_count: int = Field(ge=1, le=10_000)
    dependency_load: float = Field(ge=0, le=100)
    stress_score: float = Field(ge=0, le=100)
    collaboration_score: float = Field(ge=0, le=100)
    decision_latency_days: float = Field(ge=0, le=120)
    critical_skills_gap: int = Field(ge=0, le=1000)


class StrategicIntelligenceRequest(BaseModel):
    competitors: list[CompetitorSignalInput] = Field(default_factory=list, max_length=25)
    clients: list[ClientSignalInput] = Field(default_factory=list, max_length=100)
    talent: list[TalentProfileInput] = Field(default_factory=list, max_length=500)
    projects: list[ProjectOpportunityInput] = Field(default_factory=list, max_length=100)
    org_units: list[OrgUnitSignalInput] = Field(default_factory=list, max_length=100)
    crisis_scenario: str = Field(default="enterprise operating pressure", max_length=300)


class CompetitorInsight(BaseModel):
    competitor: str
    market_pressure_score: float = Field(ge=0, le=100)
    threat_level: RiskLevel
    likely_moves: list[str]
    recommended_response: str
    evidence: list[str]


class ClientRiskInsight(BaseModel):
    client_id: str
    client_name: str
    revenue_at_risk: float
    churn_risk: float = Field(ge=0, le=100)
    payment_delay_risk: float = Field(ge=0, le=100)
    escalation_risk: float = Field(ge=0, le=100)
    relationship_health: float = Field(ge=0, le=100)
    intervention: str
    evidence: list[str]


class MarketplaceMatch(BaseModel):
    employee_id: str
    employee_name: str
    project_id: str
    project_title: str
    match_score: float = Field(ge=0, le=100)
    capacity_fit: float = Field(ge=0, le=100)
    rationale: str


class MentorMatch(BaseModel):
    mentor_id: str
    mentor_name: str
    mentee_id: str
    mentee_name: str
    topic: str
    match_score: float = Field(ge=0, le=100)


class OrgOptimizationInsight(BaseModel):
    unit: str
    optimization_pressure: float = Field(ge=0, le=100)
    reporting_change: str
    communication_flow: str
    expected_latency_reduction_days: float
    evidence: list[str]


class CrisisResponsePlan(BaseModel):
    scenario: str
    severity_score: float = Field(ge=0, le=100)
    risk_level: RiskLevel
    recovery_priorities: list[str]
    command_center_actions: list[str]
    expected_recovery_days: int


class InnovationSignal(BaseModel):
    employee_id: str
    employee_name: str
    innovation_score: float = Field(ge=0, le=100)
    leadership_potential: float = Field(ge=0, le=100)
    sponsorship_action: str
    evidence: list[str]


class StrategicIntelligenceSummary(BaseModel):
    competitor_threats: int
    high_risk_clients: int
    marketplace_matches: int
    mentor_matches: int
    org_units_to_restructure: int
    innovation_leaders: int
    crisis_severity: float = Field(ge=0, le=100)
    strategic_readiness_score: float = Field(ge=0, le=100)
    top_market_risk: str
    top_client_risk: str


class StrategicIntelligenceResponse(BaseModel):
    model: str
    generated_at: datetime
    summary: StrategicIntelligenceSummary
    competitive_intelligence: list[CompetitorInsight]
    client_relationship_intelligence: list[ClientRiskInsight]
    internal_marketplace_matches: list[MarketplaceMatch]
    mentor_matches: list[MentorMatch]
    organization_optimizations: list[OrgOptimizationInsight]
    crisis_response: CrisisResponsePlan
    innovation_signals: list[InnovationSignal]
    executive_brief: str
    storage: str


class StrategicDecisionRequest(BaseModel):
    question: str = Field(default="Should we reduce workforce by 20%?", min_length=4, max_length=800)
    session_id: str = Field(default="strategic-decision-demo", max_length=120)
    horizon_months: int = Field(default=12, ge=1, le=36)


class StrategicChainReactionStep(BaseModel):
    step: int = Field(ge=1)
    title: str
    baseline: float
    projected: float
    delta: float
    severity: RiskLevel
    explanation: str
    source_systems: list[str] = Field(default_factory=list)


class StrategicDecisionOption(BaseModel):
    option_id: str
    title: str
    description: str
    risk_score: float = Field(ge=0, le=100)
    revenue_impact_percent: float
    cost_impact_percent: float
    burnout_impact_points: float
    productivity_impact_percent: float
    client_impact_score: float = Field(ge=0, le=100)
    decision_readiness_score: float = Field(ge=0, le=100)
    recommendation: str
    recommended: bool = False


class StrategicBoardroomFinding(BaseModel):
    agent: str
    perspective: str
    finding: str
    recommendation: str
    confidence: float = Field(ge=0, le=1)
    evidence: list[str] = Field(default_factory=list)


class StrategicDecisionScores(BaseModel):
    strategic_intelligence_score: float = Field(ge=0, le=100)
    innovation_score: float = Field(ge=0, le=100)
    enterprise_value_score: float = Field(ge=0, le=100)
    technical_complexity_score: float = Field(ge=0, le=100)
    judge_wow_factor_score: float = Field(ge=0, le=100)
    production_readiness_score: float = Field(ge=0, le=100)


class StrategicDecisionResponse(BaseModel):
    model: str
    generated_at: datetime
    question: str
    decision_intent: str
    executive_answer: str
    recommended_action: str
    confidence_score: float = Field(ge=0, le=100)
    strategic_risk_score: float = Field(ge=0, le=100)
    future_simulation_status: Literal["working", "partial", "missing"]
    digital_twin_status: Literal["working", "partial", "missing"]
    chain_reaction_status: Literal["working", "partial", "missing"]
    boardroom_status: Literal["working", "partial", "missing"]
    shadow_company_status: Literal["working", "partial", "missing"]
    demo_mode_status: Literal["working", "partial", "missing"]
    decision_options: list[StrategicDecisionOption]
    chain_reaction: list[StrategicChainReactionStep]
    boardroom_findings: list[StrategicBoardroomFinding]
    impact_panel: ExecutiveImpactAnalysisPanel
    what_if_simulation: WhatIfSimulationResponse
    shadow_company_simulation: ShadowDecisionSimulationResponse
    source_systems: list[str]
    scores: StrategicDecisionScores
    storage: str
    final_verdict: str
