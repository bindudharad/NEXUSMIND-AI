from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


BusinessRiskLevel = Literal["low", "medium", "high", "critical"]
BusinessRecommendationPriority = Literal["low", "medium", "high", "critical"]


class BusinessScenarioRequest(BaseModel):
    scenario_id: str = "default-business-scenario"
    scenario: str = "What happens if churn increases by 15%?"
    horizon_months: int = Field(default=12, ge=3, le=36)
    revenue_delta_percent: float = Field(default=0, ge=-80, le=120)
    churn_delta_percent: float = Field(default=0, ge=-80, le=120)
    cost_delta_percent: float = Field(default=0, ge=-80, le=120)
    hiring_freeze_months: int = Field(default=0, ge=0, le=36)
    market_risk_delta: float = Field(default=0, ge=-50, le=50)


class BusinessPredictionRequest(BaseModel):
    cycle_name: str = "Executive Future Prediction Review"
    horizon_months: int = Field(default=12, ge=3, le=36)
    scenario: BusinessScenarioRequest | None = None


class BusinessAssistantRequest(BaseModel):
    question: str = Field(min_length=2)
    horizon_months: int = Field(default=12, ge=3, le=36)
    scenario: BusinessScenarioRequest | None = None
    session_id: str = "business-prediction-dashboard"


class BusinessForecastPoint(BaseModel):
    month: str
    revenue: float
    lower_bound: float
    upper_bound: float
    growth_rate: float
    revenue_risk: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)


class ClientChurnForecast(BaseModel):
    client_id: str
    client_name: str
    churn_probability: float = Field(ge=0, le=100)
    renewal_probability: float = Field(ge=0, le=100)
    revenue_at_risk: float
    contract_value: float
    reasons: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)


class MarketRiskPrediction(BaseModel):
    risk_id: str
    category: str
    risk_score: float = Field(ge=0, le=100)
    trend: Literal["declining", "stable", "rising"]
    forecast: str
    drivers: list[str] = Field(default_factory=list)
    strategic_warning: str


class EmployeeGrowthForecast(BaseModel):
    department: str
    current_headcount: int = Field(ge=0)
    forecast_headcount: int = Field(ge=0)
    growth_percent: float
    productivity_capacity: float = Field(ge=0, le=120)
    skill_demand: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)


class HiringDemandForecast(BaseModel):
    role: str
    department: str
    required_count: int = Field(ge=0)
    urgency: BusinessRiskLevel
    skills: list[str] = Field(default_factory=list)
    justification: str
    revenue_linked: float


class ProjectProfitabilityForecast(BaseModel):
    project_id: str
    project_name: str
    estimated_cost: float
    expected_revenue: float
    roi_percent: float
    budget_efficiency: float = Field(ge=0, le=120)
    overrun_probability: float = Field(ge=0, le=100)
    risk_level: BusinessRiskLevel
    confidence: float = Field(ge=0, le=1)


class CompanyHealthFuture(BaseModel):
    score: float = Field(ge=0, le=100)
    risk_level: BusinessRiskLevel
    forecast: str
    revenue_health: float = Field(ge=0, le=100)
    workforce_health: float = Field(ge=0, le=100)
    client_health: float = Field(ge=0, le=100)
    delivery_health: float = Field(ge=0, le=100)
    productivity_health: float = Field(ge=0, le=100)
    security_health: float = Field(ge=0, le=100)


class BusinessScenarioResult(BaseModel):
    scenario_id: str
    scenario: str
    financial_impact: float
    revenue_after_impact: float
    churn_delta: float
    workforce_impact: str
    profitability_impact: float
    growth_impact: float
    risk_impact: float = Field(ge=0, le=100)
    success_probability: float = Field(ge=0, le=100)
    recommendations: list[str] = Field(default_factory=list)


class BusinessRecommendation(BaseModel):
    title: str
    priority: BusinessRecommendationPriority
    action: str
    rationale: str
    expected_financial_impact: float
    confidence: float = Field(ge=0, le=1)


class BusinessEvidence(BaseModel):
    source: str
    signal: str
    value: str
    weight: float = Field(ge=0, le=1)


class BusinessModelStatus(BaseModel):
    model: str
    status: str
    detail: str


class BusinessPredictionSummary(BaseModel):
    current_revenue: float
    predicted_next_quarter_revenue: float
    annual_revenue_forecast: float
    revenue_growth_rate: float
    average_churn_probability: float = Field(ge=0, le=100)
    revenue_at_risk: float
    hiring_needed: int = Field(ge=0)
    company_health_score: float = Field(ge=0, le=100)
    market_risk_score: float = Field(ge=0, le=100)
    profitability_index: float = Field(ge=0, le=100)
    top_business_risk: str
    forecast_confidence: float = Field(ge=0, le=1)
    stream_sequence: int = 1


class BusinessPredictionResponse(BaseModel):
    model: str
    generated_at: datetime
    cycle_name: str
    horizon_months: int
    summary: BusinessPredictionSummary
    revenue_forecast: list[BusinessForecastPoint]
    churn_predictions: list[ClientChurnForecast]
    market_risks: list[MarketRiskPrediction]
    employee_growth_forecast: list[EmployeeGrowthForecast]
    hiring_demand: list[HiringDemandForecast]
    project_profitability: list[ProjectProfitabilityForecast]
    company_health_forecast: CompanyHealthFuture
    scenario_simulations: list[BusinessScenarioResult]
    recommendations: list[BusinessRecommendation]
    evidence: list[BusinessEvidence]
    model_status: list[BusinessModelStatus]
    supported_questions: list[str]
    source_systems: list[str]
    storage: str


class BusinessAssistantResponse(BaseModel):
    model: str
    generated_at: datetime
    question: str
    intent: str
    answer: str
    confidence: float = Field(ge=0, le=1)
    cited_evidence: list[BusinessEvidence]
    scenario: BusinessScenarioResult | None = None
    recommended_actions: list[str]
    source_systems: list[str]
    storage: str


class BusinessPredictionSearchRequest(BaseModel):
    query: str = Field(min_length=2)
    top_k: int = Field(default=5, ge=1, le=20)

    @model_validator(mode="before")
    @classmethod
    def normalize_limit(cls, data):
        if isinstance(data, dict):
            requested_limit = data.get("top_k") or data.get("topK") or data.get("limit")
            if requested_limit is not None:
                data = {**data, "top_k": requested_limit}
        return data
