from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


ProjectRiskSeverity = Literal["low", "medium", "high", "critical"]


class ProjectMetricPoint(BaseModel):
    timestamp: datetime
    sprint_velocity: float = Field(ge=0, le=1, default=0.72)
    task_completion_rate: float = Field(ge=0, le=1, default=0.74)
    scope_change_rate: float = Field(ge=0, le=1, default=0.18)
    defect_rate: float = Field(ge=0, le=1, default=0.16)
    rework_ratio: float = Field(ge=0, le=1, default=0.14)
    dependency_bottlenecks: int = Field(ge=0, le=30, default=2)
    resource_allocation: float = Field(ge=0, le=1, default=0.76)
    budget_burn_rate: float = Field(ge=0, le=1.5, default=0.72)
    meeting_load: float = Field(ge=0, le=1, default=0.38)
    communication_score: float = Field(ge=0, le=1, default=0.78)
    team_burnout: float = Field(ge=0, le=1, default=0.34)
    team_compatibility: float = Field(ge=0, le=1, default=0.72)
    open_risks: int = Field(ge=0, le=60, default=4)


class ProjectProfile(BaseModel):
    project_id: str
    project_name: str
    department: str = "Engineering"
    team_name: str = "Delivery Team"
    days_to_deadline: int = Field(ge=1, le=365, default=35)
    budget_utilization: float = Field(ge=0, le=1.6, default=0.62)
    required_skills: list[str] = Field(default_factory=list, max_length=16)
    available_skills: list[str] = Field(default_factory=list, max_length=24)
    team_size: int = Field(ge=1, le=200, default=10)
    critical_dependency_count: int = Field(ge=0, le=30, default=3)
    historical_delivery_rate: float = Field(ge=0, le=1, default=0.78)
    current_scope_completion: float = Field(ge=0, le=1, default=0.58)
    executive_visibility: float = Field(ge=0, le=1, default=0.58)
    history: list[ProjectMetricPoint] = Field(default_factory=list, max_length=120)


class ProjectFailureRequest(BaseModel):
    horizon_days: int = Field(ge=7, le=90, default=21)
    projects: list[ProjectProfile] = Field(default_factory=list, max_length=24)
    realtime: bool = False


class ProjectRiskForecastPoint(BaseModel):
    day: int = Field(ge=1)
    failure_probability: float = Field(ge=0, le=100)
    delay_probability: float = Field(ge=0, le=100)
    budget_overrun_probability: float = Field(ge=0, le=100)
    sprint_completion_probability: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)


class ProjectRiskSignal(BaseModel):
    category: str
    severity: ProjectRiskSeverity
    score: float = Field(ge=0, le=100)
    evidence: str
    recommendation: str


class ProjectRecommendation(BaseModel):
    recommendation_id: str
    category: str
    title: str
    action: str
    rationale: str
    impact_score: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    affected_projects: list[str]
    source_systems: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class ProjectFailurePrediction(BaseModel):
    project_id: str
    project_name: str
    department: str
    team_name: str
    failure_probability: float = Field(ge=0, le=100)
    deadline_miss_probability: float = Field(ge=0, le=100)
    budget_overrun_probability: float = Field(ge=0, le=100)
    team_collapse_risk: float = Field(ge=0, le=100)
    productivity_slowdown: float = Field(ge=0, le=100)
    resource_shortage_impact: float = Field(ge=0, le=100)
    burnout_impact: float = Field(ge=0, le=100)
    communication_bottleneck_risk: float = Field(ge=0, le=100)
    dependency_failure_impact: float = Field(ge=0, le=100)
    operational_instability: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    health_score: float = Field(ge=0, le=100)
    forecast: list[ProjectRiskForecastPoint]
    risk_signals: list[ProjectRiskSignal]
    recommendations: list[ProjectRecommendation]


class ProjectFailureSummary(BaseModel):
    projects_analyzed: int
    average_failure_probability: float = Field(ge=0, le=100)
    average_delay_probability: float = Field(ge=0, le=100)
    critical_projects: int
    highest_risk_project: str
    average_health_score: float = Field(ge=0, le=100)
    stream_sequence: int = 1


class ProjectFailureResponse(BaseModel):
    model: str
    generated_at: datetime
    horizon_days: int
    predictions: list[ProjectFailurePrediction]
    portfolio_recommendations: list[ProjectRecommendation]
    heatmap: list[dict[str, float | str]]
    summary: ProjectFailureSummary
    storage: str
