from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


DecisionPriority = Literal["low", "medium", "high", "critical"]
DecisionCategory = Literal["routing", "risk", "timeline", "capacity", "burnout", "cost", "skills"]


class DecisionProjectSignal(BaseModel):
    project_id: str
    project_name: str
    description: str = ""
    required_skills: list[str] = Field(default_factory=list, min_length=1, max_length=24)
    complexity: float = Field(default=0.62, ge=0, le=1)
    deadline_days: int = Field(default=30, ge=1, le=365)
    budget: float = Field(default=500000, ge=0, le=100000000)
    revenue_impact: float = Field(default=1000000, ge=0, le=250000000)
    dependency_count: int = Field(default=3, ge=0, le=50)
    security_sensitivity: float = Field(default=0.45, ge=0, le=1)
    innovation_requirement: float = Field(default=0.5, ge=0, le=1)
    scope_volatility: float = Field(default=0.28, ge=0, le=1)
    executive_visibility: float = Field(default=0.55, ge=0, le=1)


class DecisionTeamOption(BaseModel):
    team_id: str
    team_name: str
    department: str
    skills: list[str] = Field(default_factory=list, min_length=1, max_length=32)
    member_count: int = Field(default=8, ge=1, le=200)
    historical_success_rate: float = Field(default=0.74, ge=0, le=1)
    productivity_score: float = Field(default=0.76, ge=0, le=1)
    current_workload: float = Field(default=0.74, ge=0, le=1.6)
    capacity_available: float = Field(default=0.28, ge=0, le=1)
    sprint_velocity: float = Field(default=0.72, ge=0, le=1)
    communication_quality: float = Field(default=0.76, ge=0, le=1)
    collaboration_score: float = Field(default=0.74, ge=0, le=1)
    burnout_risk: float = Field(default=0.34, ge=0, le=1)
    attrition_risk: float = Field(default=0.26, ge=0, le=1)
    delivery_consistency: float = Field(default=0.74, ge=0, le=1)
    innovation_score: float = Field(default=0.62, ge=0, le=1)
    hourly_cost: float = Field(default=95, gt=0, le=800)
    active_incidents: int = Field(default=1, ge=0, le=60)


class DecisionAssistantRequest(BaseModel):
    question: str = "Which team should handle Project Atlas?"
    project: DecisionProjectSignal
    teams: list[DecisionTeamOption] = Field(default_factory=list, min_length=1, max_length=32)
    horizon_days: int = Field(default=45, ge=7, le=180)
    realtime: bool = False


class TeamDecisionRanking(BaseModel):
    rank: int = Field(ge=1)
    team_id: str
    team_name: str
    department: str
    suitability_score: float = Field(ge=0, le=100)
    skill_compatibility: float = Field(ge=0, le=100)
    capacity_score: float = Field(ge=0, le=100)
    workload_impact: float = Field(ge=0, le=160)
    burnout_risk: float = Field(ge=0, le=100)
    delivery_success_probability: float = Field(ge=0, le=100)
    estimated_completion_days: float = Field(ge=1, le=365)
    estimated_cost: float = Field(ge=0, le=250000000)
    risk_score: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    rationale: str
    capability_drivers: list[str] = Field(default_factory=list)
    risk_drivers: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)


class DecisionRiskHeatmapPoint(BaseModel):
    team_name: str
    metric: str
    score: float = Field(ge=0, le=100)
    severity: DecisionPriority


class DecisionTimelineForecastPoint(BaseModel):
    day: int = Field(ge=1)
    completion_probability: float = Field(ge=0, le=100)
    delay_risk: float = Field(ge=0, le=100)
    workload_pressure: float = Field(ge=0, le=160)
    confidence: float = Field(ge=0, le=1)


class DecisionCapabilityForecast(BaseModel):
    team_name: str
    skill_fit: float = Field(ge=0, le=100)
    capacity_fit: float = Field(ge=0, le=100)
    delivery_fit: float = Field(ge=0, le=100)
    stability_fit: float = Field(ge=0, le=100)
    overall_capability: float = Field(ge=0, le=100)


class DecisionRecommendation(BaseModel):
    title: str
    category: DecisionCategory
    priority: DecisionPriority
    action: str
    expected_impact: str
    confidence: float = Field(ge=0, le=1)
    affected_teams: list[str] = Field(default_factory=list)


class DecisionAlert(BaseModel):
    title: str
    severity: DecisionPriority
    probability: float = Field(ge=0, le=100)
    impact: str
    mitigation: str


class DecisionSummary(BaseModel):
    recommended_team: str
    recommended_team_id: str
    best_team_score: float = Field(ge=0, le=100)
    success_probability: float = Field(ge=0, le=100)
    estimated_completion_days: float = Field(ge=1, le=365)
    delivery_risk: float = Field(ge=0, le=100)
    workload_impact: float = Field(ge=0, le=160)
    skill_gap_count: int = Field(ge=0, le=32)
    stream_sequence: int = 1


class DecisionAssistantResponse(BaseModel):
    model: str
    generated_at: datetime
    question: str
    project_name: str
    horizon_days: int
    rankings: list[TeamDecisionRanking]
    risk_heatmap: list[DecisionRiskHeatmapPoint]
    timeline_forecast: list[DecisionTimelineForecastPoint]
    capability_forecast: list[DecisionCapabilityForecast]
    recommendations: list[DecisionRecommendation]
    alerts: list[DecisionAlert]
    executive_insights: list[str]
    summary: DecisionSummary
    source_systems: list[str]
    storage: str
