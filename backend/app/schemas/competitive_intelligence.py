from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


CompetitiveRiskLevel = Literal["low", "medium", "high", "critical"]
CompetitiveSignalType = Literal[
    "product_launch",
    "hiring_trend",
    "technology_adoption",
    "market_expansion",
    "funding_activity",
    "acquisition",
    "partnership",
    "pricing_change",
    "customer_sentiment",
    "industry_trend",
]


class CompetitorProfileInput(BaseModel):
    company_name: str = Field(min_length=2, max_length=160)
    industry: str = Field(default="Enterprise AI Software", max_length=120)
    products: list[str] = Field(default_factory=list, max_length=20)
    market_position: str = Field(default="challenger", max_length=80)
    revenue_estimate_millions: float = Field(default=100, ge=0, le=100_000)
    employee_count: int = Field(default=500, ge=1, le=1_000_000)
    technology_stack: list[str] = Field(default_factory=list, max_length=40)
    regions: list[str] = Field(default_factory=list, max_length=25)
    job_roles: list[str] = Field(default_factory=list, max_length=30)
    hiring_growth_percent: float = Field(default=12, ge=-50, le=300)
    product_launches_90d: int = Field(default=1, ge=0, le=80)
    ai_mentions_30d: int = Field(default=30, ge=0, le=5000)
    funding_signal: float = Field(default=0.2, ge=0, le=1)
    acquisition_signal: float = Field(default=0.0, ge=0, le=1)
    partnership_signal: float = Field(default=0.1, ge=0, le=1)
    pricing_pressure: float = Field(default=0.25, ge=0, le=1)
    customer_sentiment: float = Field(default=0.1, ge=-1, le=1)
    market_share_growth: float = Field(default=2, ge=-30, le=80)
    technology_adoption_score: float = Field(default=55, ge=0, le=100)
    product_velocity_score: float = Field(default=50, ge=0, le=100)
    recent_activities: list[str] = Field(default_factory=list, max_length=40)


class CompetitiveIntelligenceRequest(BaseModel):
    horizon_months: int = Field(default=12, ge=1, le=36)
    competitors: list[CompetitorProfileInput] = Field(default_factory=list, max_length=25)
    focus_markets: list[str] = Field(default_factory=list, max_length=20)
    realtime: bool = True


class CompetitiveAssistantRequest(BaseModel):
    question: str = Field(min_length=2, max_length=700)
    session_id: str = "competitive-war-room"
    horizon_months: int = Field(default=12, ge=1, le=36)


class CompetitorProfile(BaseModel):
    competitor_id: str
    company_name: str
    industry: str
    products: list[str]
    market_position: str
    revenue_estimate_millions: float
    employee_count: int
    technology_stack: list[str]
    recent_activities: list[str]
    strategic_risks: list[str]
    rank: int = Field(ge=1)
    threat_score: float = Field(ge=0, le=100)
    threat_level: CompetitiveRiskLevel
    source_signals: list[CompetitiveSignalType]


class ProductLaunchSignal(BaseModel):
    competitor: str
    launch_name: str
    category: str
    release_window: str
    launch_frequency_score: float = Field(ge=0, le=100)
    product_strategy_shift: str
    impact: str
    risk_level: CompetitiveRiskLevel
    evidence: list[str]


class HiringTrendSignal(BaseModel):
    competitor: str
    hiring_growth_percent: float
    focus: str
    roles: list[str]
    departments_expanding: list[str]
    geographic_hiring: list[str]
    skill_demand: list[str]
    forecast: str
    strategic_interpretation: str
    risk_level: CompetitiveRiskLevel


class TechnologyAdoptionSignal(BaseModel):
    competitor: str
    technologies: list[str]
    adoption_score: float = Field(ge=0, le=100)
    investment_signal: float = Field(ge=0, le=100)
    strategic_insight: str
    risk_level: CompetitiveRiskLevel


class MarketExpansionSignal(BaseModel):
    competitor: str
    regions: list[str]
    expansion_score: float = Field(ge=0, le=100)
    customer_acquisition_signal: float = Field(ge=0, le=100)
    potential_market_threat: CompetitiveRiskLevel
    strategic_interpretation: str


class IndustryTrendSignal(BaseModel):
    trend: str
    traction_score: float = Field(ge=0, le=100)
    forecast_impact: str
    likely_time_horizon: str
    opportunity: str
    risk: str


class CompetitiveRiskScore(BaseModel):
    competitor: str
    threat_score: float = Field(ge=0, le=100)
    threat_level: CompetitiveRiskLevel
    market_disruption_risk: float = Field(ge=0, le=100)
    innovation_risk: float = Field(ge=0, le=100)
    talent_acquisition_risk: float = Field(ge=0, le=100)
    technology_risk: float = Field(ge=0, le=100)
    primary_threat: str
    evidence: list[str]


class CompetitorComparisonMetric(BaseModel):
    metric: str
    company_score: float = Field(ge=0, le=100)
    competitor_score: float = Field(ge=0, le=100)
    delta: float
    interpretation: str


class CompetitorComparisonCard(BaseModel):
    competitor: str
    rank: int = Field(ge=1)
    overall_score: float = Field(ge=0, le=100)
    metrics: list[CompetitorComparisonMetric]


class StrategicRecommendation(BaseModel):
    title: str
    priority: CompetitiveRiskLevel
    action: str
    reason: str
    expected_competitive_benefit: str
    confidence: float = Field(ge=0, le=1)
    related_competitors: list[str]


class CompetitiveDashboardSummary(BaseModel):
    competitor_count: int = Field(ge=0)
    high_threat_competitors: int = Field(ge=0)
    top_competitor_threat: str
    average_threat_score: float = Field(ge=0, le=100)
    product_launches_tracked: int = Field(ge=0)
    aggressive_hiring_competitors: int = Field(ge=0)
    technologies_tracked: int = Field(ge=0)
    markets_expanding: int = Field(ge=0)
    strategic_readiness_score: float = Field(ge=0, le=100)
    stream_sequence: int = 1


class CompetitiveIntelligenceResponse(BaseModel):
    model: str
    generated_at: datetime
    horizon_months: int
    summary: CompetitiveDashboardSummary
    profiles: list[CompetitorProfile]
    product_launches: list[ProductLaunchSignal]
    hiring_trends: list[HiringTrendSignal]
    technology_adoption: list[TechnologyAdoptionSignal]
    market_expansions: list[MarketExpansionSignal]
    risk_scores: list[CompetitiveRiskScore]
    industry_trends: list[IndustryTrendSignal]
    comparison: list[CompetitorComparisonCard]
    recommendations: list[StrategicRecommendation]
    supported_questions: list[str]
    source_systems: list[str]
    storage: str


class CompetitiveAssistantResponse(BaseModel):
    model: str
    generated_at: datetime
    question: str
    intent: str
    answer: str
    confidence: float = Field(ge=0, le=1)
    cited_evidence: list[str]
    competitors: list[str]
    recommendations: list[StrategicRecommendation]
    source_systems: list[str]
    storage: str
