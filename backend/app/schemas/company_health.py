from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


CompanyHealthPriority = Literal["low", "medium", "high", "critical"]
CompanyHealthStatus = Literal["optimal", "stable", "watch", "risk", "critical"]


class CompanyHealthTeamSignal(BaseModel):
    team_id: str
    department: str = "Engineering"
    team_name: str = "Platform"
    headcount: int = Field(default=8, ge=1, le=10000)
    employee_happiness_score: float = Field(default=72, ge=0, le=100)
    productivity_score: float = Field(default=76, ge=0, le=100)
    burnout_risk: float = Field(default=38, ge=0, le=100)
    attrition_risk: float = Field(default=32, ge=0, le=100)
    project_health: float = Field(default=74, ge=0, le=100)
    collaboration_quality: float = Field(default=78, ge=0, le=100)
    delivery_stability: float = Field(default=76, ge=0, le=100)
    resource_utilization: float = Field(default=82, ge=0, le=130)
    innovation_score: float = Field(default=66, ge=0, le=100)
    security_risk: float = Field(default=18, ge=0, le=100)
    communication_health: float = Field(default=76, ge=0, le=100)
    meeting_efficiency: float = Field(default=70, ge=0, le=100)
    workforce_engagement: float = Field(default=74, ge=0, le=100)
    open_project_risks: int = Field(default=4, ge=0, le=120)
    active_incidents: int = Field(default=0, ge=0, le=80)


class CompanyHealthRequest(BaseModel):
    cycle_name: str = "Realtime Company Health Review"
    horizon_days: int = Field(default=30, ge=7, le=180)
    teams: list[CompanyHealthTeamSignal] = Field(default_factory=list, max_length=200)
    realtime: bool = False


class ExecutiveKPI(BaseModel):
    label: str
    value: str
    score: float = Field(ge=0, le=100)
    trend_delta: float
    status: CompanyHealthStatus
    source: str


class TeamHealthScore(BaseModel):
    team_id: str
    department: str
    team_name: str
    headcount: int = Field(ge=1)
    health_score: float = Field(ge=0, le=100)
    risk_score: float = Field(ge=0, le=100)
    happiness_score: float = Field(ge=0, le=100)
    productivity_score: float = Field(ge=0, le=100)
    burnout_risk: float = Field(ge=0, le=100)
    attrition_risk: float = Field(ge=0, le=100)
    project_health: float = Field(ge=0, le=100)
    team_efficiency: float = Field(ge=0, le=100)
    collaboration_quality: float = Field(ge=0, le=100)
    delivery_stability: float = Field(ge=0, le=100)
    operational_risk: float = Field(ge=0, le=100)
    priority: CompanyHealthPriority
    confidence: float = Field(ge=0, le=1)
    dominant_risks: list[str]
    recommendation: str


class CompanyHealthHeatmapPoint(BaseModel):
    department: str
    team_name: str
    metric: str
    health_score: float = Field(ge=0, le=100)
    risk_score: float = Field(ge=0, le=100)
    intensity: float = Field(ge=0, le=100)
    priority: CompanyHealthPriority


class ProductivityTrendPoint(BaseModel):
    label: str
    productivity_score: float = Field(ge=0, le=100)
    focus_stability: float = Field(ge=0, le=100)
    meeting_efficiency: float = Field(ge=0, le=100)
    delivery_stability: float = Field(ge=0, le=100)


class RiskForecastPoint(BaseModel):
    label: str
    company_health_score: float = Field(ge=0, le=100)
    burnout_risk: float = Field(ge=0, le=100)
    attrition_risk: float = Field(ge=0, le=100)
    project_failure_risk: float = Field(ge=0, le=100)
    operational_risk: float = Field(ge=0, le=100)


class ProjectHealthScorecard(BaseModel):
    project_id: str
    department: str
    team_name: str
    health_score: float = Field(ge=0, le=100)
    delay_probability: float = Field(ge=0, le=100)
    delivery_stability: float = Field(ge=0, le=100)
    productivity_risk: float = Field(ge=0, le=100)
    priority: CompanyHealthPriority
    risk_drivers: list[str]
    recommended_action: str


class ExecutiveCompanyRecommendation(BaseModel):
    title: str
    category: Literal["workforce", "productivity", "burnout", "attrition", "project", "communication", "security", "operational"]
    priority: CompanyHealthPriority
    expected_impact: float = Field(ge=0, le=100)
    action: str
    rationale: str
    confidence: float = Field(ge=0, le=1)


class CompanyHealthAlert(BaseModel):
    title: str
    category: str
    severity: CompanyHealthPriority
    probability: float = Field(ge=0, le=100)
    impact: str
    recommendation: str


class CompanyHealthSummary(BaseModel):
    company_health_score: float = Field(ge=0, le=100)
    employee_happiness_score: float = Field(ge=0, le=100)
    productivity_score: float = Field(ge=0, le=100)
    burnout_risk: float = Field(ge=0, le=100)
    attrition_risk: float = Field(ge=0, le=100)
    project_health_score: float = Field(ge=0, le=100)
    collaboration_quality: float = Field(ge=0, le=100)
    delivery_stability: float = Field(ge=0, le=100)
    workforce_engagement: float = Field(ge=0, le=100)
    operational_risk: float = Field(ge=0, le=100)
    high_risk_teams: int = Field(ge=0)
    critical_alerts: int = Field(ge=0)
    stream_sequence: int = 1


class CompanyHealthResponse(BaseModel):
    model: str
    generated_at: datetime
    cycle_name: str
    horizon_days: int
    executive_kpis: list[ExecutiveKPI]
    team_scores: list[TeamHealthScore]
    heatmap: list[CompanyHealthHeatmapPoint]
    productivity_trends: list[ProductivityTrendPoint]
    risk_forecasts: list[RiskForecastPoint]
    project_scorecards: list[ProjectHealthScorecard]
    recommendations: list[ExecutiveCompanyRecommendation]
    alerts: list[CompanyHealthAlert]
    executive_insights: list[str]
    summary: CompanyHealthSummary
    source_systems: list[str]
    storage: str
