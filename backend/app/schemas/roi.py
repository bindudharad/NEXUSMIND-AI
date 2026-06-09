from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


RoiSeverity = Literal["low", "medium", "high", "critical"]


class WorkforceCostInput(BaseModel):
    employee_id: str
    name: str
    role: str
    team_name: str
    annual_salary: float = Field(gt=0, le=1_000_000, default=120_000)
    fully_loaded_multiplier: float = Field(ge=1, le=2.5, default=1.32)
    attrition_probability: float = Field(ge=0, le=1, default=0.22)
    burnout_probability: float = Field(ge=0, le=1, default=0.38)
    productivity_score: float = Field(ge=0, le=1, default=0.76)
    stress_score: float = Field(ge=0, le=1, default=0.42)
    overtime_hours_monthly: float = Field(ge=0, le=220, default=18)
    meeting_hours_weekly: float = Field(ge=0, le=60, default=8)
    knowledge_criticality: float = Field(ge=0, le=1, default=0.55)
    billable_revenue_per_day: float = Field(ge=0, le=50_000, default=1_400)
    open_critical_tasks: int = Field(ge=0, le=200, default=6)


class ProjectFinancialInput(BaseModel):
    project_id: str
    project_name: str
    team_name: str
    forecasted_revenue: float = Field(ge=0, le=200_000_000, default=1_200_000)
    gross_margin: float = Field(ge=0, le=1, default=0.62)
    failure_probability: float = Field(ge=0, le=1, default=0.38)
    delay_probability: float = Field(ge=0, le=1, default=0.42)
    projected_delay_days: int = Field(ge=0, le=365, default=12)
    daily_burn_rate: float = Field(ge=0, le=500_000, default=12_500)
    delivery_penalty_per_day: float = Field(ge=0, le=250_000, default=4_000)
    client_churn_risk: float = Field(ge=0, le=1, default=0.18)
    budget_utilization: float = Field(ge=0, le=1.8, default=0.74)
    team_size: int = Field(ge=1, le=500, default=10)


class RoiScenarioRequest(BaseModel):
    horizon_months: int = Field(ge=3, le=36, default=12)
    intervention_budget: float = Field(gt=0, le=20_000_000, default=180_000)
    retention_improvement: float = Field(ge=0, le=0.8, default=0.24)
    productivity_recovery: float = Field(ge=0, le=0.6, default=0.16)
    meeting_reduction: float = Field(ge=0, le=0.7, default=0.18)
    overtime_reduction: float = Field(ge=0, le=0.7, default=0.22)
    delay_risk_reduction: float = Field(ge=0, le=0.7, default=0.2)
    employees: list[WorkforceCostInput] = Field(default_factory=list, max_length=200)
    projects: list[ProjectFinancialInput] = Field(default_factory=list, max_length=80)
    realtime: bool = False


class ReplacementCostAnalysis(BaseModel):
    employee_id: str
    employee_name: str
    team_name: str
    replacement_cost: float
    expected_attrition_exposure: float
    hiring_cost: float
    training_cost: float
    productivity_recovery_cost: float
    knowledge_transfer_loss: float
    team_disruption_cost: float
    revenue_at_risk: float
    prevention_savings: float
    severity: RoiSeverity


class ProductivityLossAnalysis(BaseModel):
    team_name: str
    employees_analyzed: int
    monthly_productivity_loss: float
    annualized_productivity_loss: float
    recoverable_value: float
    burnout_drag_percent: float = Field(ge=0, le=100)
    meeting_inefficiency_cost: float
    overtime_inefficiency_cost: float
    recommendation: str


class DelayCostAnalysis(BaseModel):
    project_id: str
    project_name: str
    team_name: str
    expected_delay_cost: float
    revenue_at_risk: float
    operational_cost_increase: float
    overtime_cost: float
    delivery_penalty_risk: float
    client_churn_cost: float
    mitigated_cost: float
    severity: RoiSeverity


class RoiForecastPoint(BaseModel):
    month: int = Field(ge=1)
    baseline_cost: float
    optimized_cost: float
    cumulative_savings: float
    roi_percent: float
    confidence: float = Field(ge=0, le=1)


class RoiRecommendation(BaseModel):
    recommendation_id: str
    category: str
    title: str
    action: str
    rationale: str
    expected_savings: float
    roi_multiplier: float
    confidence: float = Field(ge=0, le=1)
    source_systems: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class ExecutiveInsight(BaseModel):
    title: str
    message: str
    financial_impact: float
    severity: RoiSeverity
    confidence: float = Field(ge=0, le=1)


class RoiSummary(BaseModel):
    baseline_annual_loss: float
    optimized_annual_loss: float
    net_savings: float
    roi_percent: float
    payback_months: float
    replacement_cost_exposure: float
    productivity_loss_exposure: float
    project_delay_exposure: float
    hr_operational_savings: float
    stream_sequence: int = 1


class RoiResponse(BaseModel):
    model: str
    generated_at: datetime
    horizon_months: int
    replacement_costs: list[ReplacementCostAnalysis]
    productivity_losses: list[ProductivityLossAnalysis]
    delay_costs: list[DelayCostAnalysis]
    recommendations: list[RoiRecommendation]
    executive_insights: list[ExecutiveInsight]
    forecast: list[RoiForecastPoint]
    summary: RoiSummary
    storage: str
