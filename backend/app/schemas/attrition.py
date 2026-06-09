from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


AttritionRiskLevel = Literal["low", "medium", "high", "critical"]


class AttritionEmployeeInput(BaseModel):
    employee_id: str
    employee_name: str
    department: str = "Engineering"
    team_name: str = "Platform"
    role: str = "Employee"
    burnout_score: float = Field(ge=0, le=100, default=42)
    productivity_score: float = Field(ge=0, le=100, default=76)
    productivity_trend: float = Field(ge=-1, le=1, default=-0.08)
    overtime_hours_30d: float = Field(ge=0, le=240, default=24)
    meeting_hours_weekly: float = Field(ge=0, le=80, default=8)
    salary_satisfaction: float = Field(ge=0, le=1, default=0.68)
    sentiment_score: float = Field(ge=-1, le=1, default=0)
    manager_compatibility: float = Field(ge=0, le=1, default=0.72)
    team_stress: float = Field(ge=0, le=1, default=0.42)
    promotion_delay_months: int = Field(ge=0, le=96, default=6)
    work_life_balance: float = Field(ge=0, le=1, default=0.64)
    attendance_rate: float = Field(ge=0, le=1, default=0.94)
    absences_90d: float = Field(ge=0, le=60, default=2)
    tenure_months: int = Field(ge=1, le=480, default=28)
    knowledge_criticality: float = Field(ge=0, le=1, default=0.55)
    annual_salary: float = Field(gt=0, le=1_500_000, default=125_000)
    billable_revenue_per_day: float = Field(ge=0, le=100_000, default=1_400)


class AttritionAnalyzeRequest(BaseModel):
    horizon_days: int = Field(ge=30, le=365, default=90)
    sensitivity: float = Field(ge=0, le=1, default=0.62)
    employees: list[AttritionEmployeeInput] = Field(default_factory=list, max_length=200)
    realtime: bool = False


class AttritionFeatureAttribution(BaseModel):
    feature: str
    value: float
    contribution: float
    direction: Literal["increases_attrition", "reduces_attrition", "neutral"]
    evidence: str


class AttritionForecastPoint(BaseModel):
    day: int = Field(ge=1)
    resignation_probability: float = Field(ge=0, le=100)
    workforce_stability: float = Field(ge=0, le=100)


class AttritionPrediction(BaseModel):
    employee_id: str
    employee_name: str
    department: str
    team_name: str
    role: str
    resignation_probability: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    risk_level: AttritionRiskLevel
    estimated_departure_window: str
    primary_reasons: list[str]
    feature_attributions: list[AttritionFeatureAttribution]
    burnout_correlation_multiplier: float
    replacement_cost_exposure: float
    recommended_interventions: list[str]
    model_probabilities: dict[str, float]
    forecast: list[AttritionForecastPoint]


class TeamAttritionTrend(BaseModel):
    team_name: str
    department: str
    employees_analyzed: int
    average_attrition_probability: float = Field(ge=0, le=100)
    high_risk_count: int = Field(ge=0)
    turnover_pressure: float = Field(ge=0, le=100)
    chain_reaction_risk: float = Field(ge=0, le=100)
    morale_signal: Literal["stable", "watch", "unstable", "critical"]
    recommendation: str


class AttritionRecommendation(BaseModel):
    recommendation_id: str
    category: str
    title: str
    action: str
    rationale: str
    impact_score: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    affected_employees: list[str]
    evidence: list[str]


class AttritionSummary(BaseModel):
    employees_analyzed: int
    average_resignation_probability: float = Field(ge=0, le=100)
    high_risk_employees: int
    critical_risk_employees: int
    workforce_stability_score: float = Field(ge=0, le=100)
    top_risk_employee: str
    estimated_replacement_exposure: float
    stream_sequence: int = 1


class AttritionResponse(BaseModel):
    model: str
    generated_at: datetime
    horizon_days: int
    predictions: list[AttritionPrediction]
    team_trends: list[TeamAttritionTrend]
    heatmap: list[dict[str, float | str]]
    recommendations: list[AttritionRecommendation]
    summary: AttritionSummary
    storage: str
