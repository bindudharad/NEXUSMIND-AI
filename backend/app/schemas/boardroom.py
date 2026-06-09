from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


BoardroomSeverity = Literal["low", "medium", "high", "critical"]
BoardroomStatus = Literal["excellent", "healthy", "watch", "risk", "critical"]
BoardroomAssistantIntent = Literal[
    "health",
    "risk",
    "forecast",
    "burnout",
    "client",
    "simulation",
    "security",
    "innovation",
    "recommendation",
    "summary",
]


class BoardroomKPI(BaseModel):
    label: str
    value: str
    score: float = Field(ge=0, le=100)
    trend: float
    status: BoardroomStatus
    source: str


class CompanyHealthPanel(BaseModel):
    score: float = Field(ge=0, le=100)
    status: BoardroomStatus
    trend: str
    drivers: list[str]
    historical_trend: list[float]
    source_systems: list[str]


class ExecutiveRiskItem(BaseModel):
    risk_id: str
    category: str
    title: str
    affected_area: str
    probability: float = Field(ge=0, le=100)
    impact_score: float = Field(ge=0, le=100)
    severity: BoardroomSeverity
    recommendation: str
    evidence: list[str] = Field(default_factory=list)
    source_systems: list[str] = Field(default_factory=list)


class FinancialPredictionPanel(BaseModel):
    current_revenue: float
    next_quarter_revenue: float
    annual_revenue_forecast: float
    revenue_growth_rate: float
    profit_forecast: float
    cost_forecast: float
    forecast_confidence: float = Field(ge=0, le=1)
    monthly_forecast: list[float]
    quarterly_forecast: list[float]
    annual_forecast: list[float]
    forecast_models: list[str]


class WorkforceIntelligencePanel(BaseModel):
    employee_health_score: float = Field(ge=0, le=100)
    burnout_hotspots: list[str]
    attrition_risk: float = Field(ge=0, le=100)
    productivity_trend: float
    top_innovator: str
    hidden_talent_count: int = Field(ge=0)
    future_leaders_count: int = Field(ge=0)
    source_systems: list[str]


class CybersecurityPanel(BaseModel):
    security_score: float = Field(ge=0, le=100)
    threat_level: BoardroomSeverity
    active_threats: int = Field(ge=0)
    insider_threat_risk: float = Field(ge=0, le=100)
    data_leakage_risk: float = Field(ge=0, le=100)
    suspicious_activity: list[str]
    recommendations: list[str]
    source_systems: list[str]


class ProjectIntelligencePanel(BaseModel):
    project_health_score: float = Field(ge=0, le=100)
    completion_confidence: float = Field(ge=0, le=100)
    highest_risk_project: str
    delivery_risk: float = Field(ge=0, le=100)
    resource_gaps: list[str]
    delivery_forecast: list[float]
    source_systems: list[str]


class ClientIntelligencePanel(BaseModel):
    average_client_health: float = Field(ge=0, le=100)
    highest_churn_risk_client: str
    churn_risk: float = Field(ge=0, le=100)
    payment_risk_accounts: int = Field(ge=0)
    upsell_opportunity_revenue: float
    relationship_status: str
    recommended_actions: list[str]
    source_systems: list[str]


class CompetitiveIntelligencePanel(BaseModel):
    threat_score: float = Field(ge=0, le=100)
    top_threat: str
    market_trends: list[str]
    industry_risks: list[str]
    strategic_opportunities: list[str]
    recommendations: list[str]
    source_systems: list[str]


class InnovationIntelligencePanel(BaseModel):
    hidden_talent_count: int = Field(ge=0)
    future_leaders_count: int = Field(ge=0)
    innovation_champions: list[str]
    skill_growth_trend: float = Field(ge=0, le=100)
    promotion_recommendations: list[str]
    source_systems: list[str]


class DigitalTwinCommandCenter(BaseModel):
    company_twin_status: str
    active_simulations: int = Field(ge=0)
    recommended_scenario: str
    highest_risk_scenario: str
    future_forecasts: list[str]
    organizational_status: list[str]
    source_systems: list[str]


class BoardroomAlert(BaseModel):
    alert_id: str
    category: str
    severity: BoardroomSeverity
    title: str
    probability: float = Field(ge=0, le=100)
    recommendation: str
    source_systems: list[str]


class ExecutiveRecommendation(BaseModel):
    recommendation_id: str
    category: str
    priority: BoardroomSeverity
    action: str
    reason: str
    expected_benefit: str
    confidence: float = Field(ge=0, le=1)
    source_systems: list[str]


class BoardroomSummary(BaseModel):
    company_health_score: float = Field(ge=0, le=100)
    overall_risk_score: float = Field(ge=0, le=100)
    executive_confidence: float = Field(ge=0, le=1)
    critical_risks: int = Field(ge=0)
    active_alerts: int = Field(ge=0)
    recommended_actions: int = Field(ge=0)
    realtime_streams: int = Field(ge=0)
    connected_engines: int = Field(ge=0)
    stream_sequence: int = 1


class BoardroomDashboardResponse(BaseModel):
    model: str
    generated_at: datetime
    dashboard_name: str
    kpis: list[BoardroomKPI]
    company_health: CompanyHealthPanel
    executive_risks: list[ExecutiveRiskItem]
    financial_predictions: FinancialPredictionPanel
    workforce: WorkforceIntelligencePanel
    cybersecurity: CybersecurityPanel
    projects: ProjectIntelligencePanel
    clients: ClientIntelligencePanel
    competitive: CompetitiveIntelligencePanel
    innovation: InnovationIntelligencePanel
    digital_twin: DigitalTwinCommandCenter
    alerts: list[BoardroomAlert]
    recommendations: list[ExecutiveRecommendation]
    executive_summary: list[str]
    supported_questions: list[str]
    source_systems: list[str]
    summary: BoardroomSummary
    storage: str


class BoardroomAssistantRequest(BaseModel):
    question: str = Field(min_length=2, max_length=700)
    session_id: str = "ai-boardroom-dashboard"


class BoardroomAssistantResponse(BaseModel):
    model: str
    generated_at: datetime
    question: str
    intent: BoardroomAssistantIntent
    answer: str
    confidence: float = Field(ge=0, le=1)
    cited_panels: list[str]
    cited_evidence: list[str]
    recommended_actions: list[str]
    source_systems: list[str]
    storage: str
