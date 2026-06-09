from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


GlobalRiskLevel = Literal["low", "medium", "high", "critical"]
GlobalSignalType = Literal["news", "economic", "competitor", "regulatory", "technology", "cyber", "supply_chain", "geopolitical"]
GlobalAssistantIntent = Literal["global_risks", "competitor", "inflation", "market_trends", "regulations", "cyber", "summary"]
GlobalTrend = Literal["declining", "stable", "rising"]


class ExternalEventInput(BaseModel):
    event_id: str
    source_type: GlobalSignalType
    title: str = Field(min_length=3, max_length=240)
    source_name: str = Field(default="External intelligence adapter", max_length=140)
    region: str = Field(default="Global", max_length=80)
    industry: str = Field(default="Enterprise AI Software", max_length=140)
    published_at: datetime | None = None
    summary: str = Field(default="", max_length=1600)
    sentiment_score: float = Field(default=0, ge=-1, le=1)
    severity: float = Field(default=50, ge=0, le=100)
    relevance: float = Field(default=60, ge=0, le=100)
    opportunity_score: float = Field(default=30, ge=0, le=100)
    keywords: list[str] = Field(default_factory=list, max_length=30)
    source_url: str = Field(default="", max_length=600)


class GlobalRiskScannerRequest(BaseModel):
    cycle_name: str = "Realtime Global Risk Scanner Review"
    horizon_days: int = Field(default=365, ge=30, le=730)
    company_industries: list[str] = Field(default_factory=lambda: ["Enterprise AI Software", "Workforce Analytics", "Cybersecurity"], max_length=20)
    target_regions: list[str] = Field(default_factory=lambda: ["United States", "India", "Singapore", "UAE", "European Union"], max_length=25)
    events: list[ExternalEventInput] = Field(default_factory=list, max_length=200)
    use_live_sources: bool = False


class GlobalRiskAssistantRequest(BaseModel):
    question: str = Field(default="What global risks affect us?", min_length=2, max_length=700)
    session_id: str = "global-risk-scanner"
    horizon_days: int = Field(default=365, ge=30, le=730)


class ExternalIntelligenceSignal(BaseModel):
    event_id: str
    signal_type: GlobalSignalType
    title: str
    source_name: str
    region: str
    industry: str
    sentiment_score: float = Field(ge=-1, le=1)
    risk_score: float = Field(ge=0, le=100)
    opportunity_score: float = Field(ge=0, le=100)
    risk_level: GlobalRiskLevel
    industry_relevance: float = Field(ge=0, le=100)
    company_relevance: float = Field(ge=0, le=100)
    interpretation: str
    evidence: list[str]
    source_url: str


class EconomicIndicatorSignal(BaseModel):
    indicator: str
    region: str
    current_signal: str
    risk_score: float = Field(ge=0, le=100)
    opportunity_score: float = Field(ge=0, le=100)
    predicted_company_impact: str
    evidence: list[str]


class CompetitorGlobalThreat(BaseModel):
    competitor: str
    threat_score: float = Field(ge=0, le=100)
    opportunity_score: float = Field(ge=0, le=100)
    threat_level: GlobalRiskLevel
    primary_threat: str
    predicted_client_churn_delta: float
    evidence: list[str]


class RegulatoryRiskSignal(BaseModel):
    regulation: str
    region: str
    compliance_risk: float = Field(ge=0, le=100)
    cost_impact_percent: float
    operational_impact: float = Field(ge=0, le=100)
    recommended_action: str
    evidence: list[str]


class TechnologyTrendSignal(BaseModel):
    trend: str
    category: str
    opportunity_score: float = Field(ge=0, le=100)
    technology_risk: float = Field(ge=0, le=100)
    strategic_window: str
    recommended_action: str
    evidence: list[str]


class CyberThreatSignal(BaseModel):
    threat: str
    threat_score: float = Field(ge=0, le=100)
    business_impact: str
    affected_capabilities: list[str]
    recommended_action: str
    evidence: list[str]


class CompanyImpactPrediction(BaseModel):
    event_id: str
    title: str
    category: GlobalSignalType
    revenue_impact_percent: float
    workforce_impact_score: float = Field(ge=0, le=100)
    client_impact_score: float = Field(ge=0, le=100)
    operational_impact_score: float = Field(ge=0, le=100)
    project_impact_score: float = Field(ge=0, le=100)
    strategic_impact_score: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    explanation: str


class GlobalRiskForecastPoint(BaseModel):
    horizon_label: Literal["30_days", "90_days", "6_months", "12_months"]
    horizon_days: int = Field(ge=1)
    risk_score: float = Field(ge=0, le=100)
    opportunity_score: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    trend: GlobalTrend
    top_drivers: list[str]


class GlobalRiskAlert(BaseModel):
    alert_id: str
    title: str
    category: GlobalSignalType
    risk_level: GlobalRiskLevel
    potential_revenue_impact: float
    recommended_action: str
    urgency_hours: int = Field(ge=1, le=720)
    evidence: list[str]


class GlobalRiskRecommendation(BaseModel):
    recommendation_id: str
    title: str
    priority: GlobalRiskLevel
    action: str
    rationale: str
    expected_impact: str
    confidence: float = Field(ge=0, le=1)
    owner_agent: str


class GlobalRiskDigitalTwinSync(BaseModel):
    twin: Literal["company", "department", "workforce", "revenue_forecast", "crisis_simulator", "executive_dashboard"]
    status: Literal["synced", "projected", "watch"]
    update: str
    entity_count: int = Field(ge=0)


class GlobalRiskAgentContribution(BaseModel):
    agent: str
    role: str
    finding: str
    recommendation: str
    confidence: float = Field(ge=0, le=1)
    source_systems: list[str]


class GlobalRiskDashboardSummary(BaseModel):
    events_analyzed: int = Field(ge=0)
    high_risk_events: int = Field(ge=0)
    critical_alerts: int = Field(ge=0)
    economic_risk_score: float = Field(ge=0, le=100)
    competitive_threat_score: float = Field(ge=0, le=100)
    regulatory_risk_score: float = Field(ge=0, le=100)
    technology_opportunity_score: float = Field(ge=0, le=100)
    cyber_threat_score: float = Field(ge=0, le=100)
    average_company_impact: float = Field(ge=0, le=100)
    production_readiness_score: float = Field(ge=0, le=100)
    innovation_score: float = Field(ge=0, le=100)
    judge_wow_factor_score: float = Field(ge=0, le=100)
    stream_sequence: int = 1


class GlobalRiskScannerResponse(BaseModel):
    model: str
    generated_at: datetime
    cycle_name: str
    horizon_days: int
    summary: GlobalRiskDashboardSummary
    news_intelligence: list[ExternalIntelligenceSignal]
    economic_intelligence: list[EconomicIndicatorSignal]
    competitor_intelligence: list[CompetitorGlobalThreat]
    regulatory_intelligence: list[RegulatoryRiskSignal]
    technology_intelligence: list[TechnologyTrendSignal]
    cyber_threat_intelligence: list[CyberThreatSignal]
    impact_predictions: list[CompanyImpactPrediction]
    risk_forecasts: list[GlobalRiskForecastPoint]
    alerts: list[GlobalRiskAlert]
    recommendations: list[GlobalRiskRecommendation]
    digital_twin_sync: list[GlobalRiskDigitalTwinSync]
    agent_council: list[GlobalRiskAgentContribution]
    supported_questions: list[str]
    executive_insights: list[str]
    live_source_adapters: list[str]
    source_systems: list[str]
    storage: str
    final_verdict: str


class GlobalRiskAssistantResponse(BaseModel):
    model: str
    generated_at: datetime
    question: str
    intent: GlobalAssistantIntent
    answer: str
    confidence: float = Field(ge=0, le=1)
    cited_events: list[str]
    recommended_actions: list[str]
    evidence: list[str]
    source_systems: list[str]
    storage: str
