from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


CompensationSeverity = Literal["low", "medium", "high", "critical"]


class CompensationEmployeeProfile(BaseModel):
    employee_id: str
    employee_name: str
    role: str
    level: int = Field(ge=1, le=8, default=3)
    department: str = "Engineering"
    location: str = "United States"
    annual_salary: float = Field(gt=0, le=1_500_000, default=125_000)
    experience_years: float = Field(ge=0, le=45, default=6)
    performance_score: float = Field(ge=0, le=100, default=78)
    productivity_score: float = Field(ge=0, le=100, default=76)
    skill_growth: float = Field(ge=0, le=1, default=0.42)
    skill_scarcity: float = Field(ge=0, le=1, default=0.46)
    leadership_score: float = Field(ge=0, le=1, default=0.44)
    delivery_consistency: float = Field(ge=0, le=1, default=0.74)
    collaboration_score: float = Field(ge=0, le=1, default=0.72)
    innovation_score: float = Field(ge=0, le=1, default=0.38)
    learning_velocity: float = Field(ge=0, le=1, default=0.52)
    attrition_probability: float = Field(ge=0, le=1, default=0.32)
    burnout_risk: float = Field(ge=0, le=1, default=0.34)
    salary_satisfaction: float = Field(ge=0, le=1, default=0.68)
    peer_compa_ratio: float = Field(ge=0.45, le=1.8, default=0.98)
    last_raise_months: int = Field(ge=0, le=96, default=12)
    promotion_delay_months: int = Field(ge=0, le=96, default=8)
    criticality_score: float = Field(ge=0, le=1, default=0.52)
    market_multiplier: float = Field(ge=0.55, le=2.2, default=1.0)
    skills: list[str] = Field(default_factory=list, max_length=20)


class CompensationRequest(BaseModel):
    cycle_name: str = "FY2026 Compensation Review"
    budget_pool: float = Field(gt=0, le=100_000_000, default=1_250_000)
    employees: list[CompensationEmployeeProfile] = Field(default_factory=list, max_length=100)
    realtime: bool = False


class MarketBenchmark(BaseModel):
    employee_id: str
    employee_name: str
    role: str
    market_min: float = Field(gt=0)
    market_mid: float = Field(gt=0)
    market_max: float = Field(gt=0)
    market_gap_percent: float = Field(ge=-100, le=200)
    market_competitiveness: float = Field(ge=0, le=100)
    skill_scarcity_index: float = Field(ge=0, le=100)


class CompensationRecommendation(BaseModel):
    employee_id: str
    employee_name: str
    role: str
    current_salary: float = Field(gt=0)
    recommended_salary_min: float = Field(gt=0)
    recommended_salary_mid: float = Field(gt=0)
    recommended_salary_max: float = Field(gt=0)
    recommended_adjustment_percent: float = Field(ge=-20, le=60)
    recommended_adjustment_amount: float
    bonus_recommendation: float = Field(ge=0)
    bonus_percent: float = Field(ge=0, le=60)
    promotion_eligibility: float = Field(ge=0, le=100)
    promotion_track: str
    retention_impact: float = Field(ge=0, le=100)
    fairness_score: float = Field(ge=0, le=100)
    compensation_risk_score: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    rationale: str
    actions: list[str]
    source_systems: list[str] = Field(default_factory=list)


class CompensationFairnessPoint(BaseModel):
    department: str
    average_fairness_score: float = Field(ge=0, le=100)
    average_market_gap: float = Field(ge=-100, le=200)
    high_risk_count: int = Field(ge=0)
    recommended_budget: float = Field(ge=0)


class CompensationAlert(BaseModel):
    title: str
    severity: CompensationSeverity
    probability: float = Field(ge=0, le=100)
    impact: str
    intervention: str


class CompensationSummary(BaseModel):
    employees_analyzed: int
    total_recommended_adjustment: float = Field(ge=0)
    budget_utilization: float = Field(ge=0, le=200)
    average_market_gap: float = Field(ge=-100, le=200)
    promotion_candidates: int
    retention_risk_reduced: float = Field(ge=0, le=100)
    fairness_score: float = Field(ge=0, le=100)
    stream_sequence: int = 1


class CompensationResponse(BaseModel):
    model: str
    generated_at: datetime
    cycle_name: str
    recommendations: list[CompensationRecommendation]
    market_benchmarks: list[MarketBenchmark]
    fairness_heatmap: list[CompensationFairnessPoint]
    alerts: list[CompensationAlert]
    executive_insights: list[str]
    summary: CompensationSummary
    storage: str
