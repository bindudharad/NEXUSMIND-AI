from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


WorkLifeSeverity = Literal["low", "medium", "high", "critical"]
WorkLifeCategory = Literal["flexible_timing", "meeting_reduction", "task_redistribution", "burnout_prevention", "focus_time", "productivity_balance", "executive"]


class WorkLifeEmployeeSignal(BaseModel):
    employee_id: str
    name: str
    department: str
    team: str
    role: str
    timezone: str = "Asia/Kolkata"
    meeting_hours_per_week: float = Field(default=12, ge=0, le=60)
    recurring_meeting_hours: float = Field(default=7, ge=0, le=60)
    async_candidate_hours: float = Field(default=3, ge=0, le=40)
    overtime_hours_30d: float = Field(default=18, ge=0, le=140)
    after_hours_messages_30d: int = Field(default=34, ge=0, le=800)
    focus_hours_per_day: float = Field(default=3.2, ge=0, le=12)
    context_switches_per_hour: float = Field(default=18, ge=0, le=120)
    task_load_hours: float = Field(default=42, ge=0, le=140)
    capacity_hours: float = Field(default=40, gt=0, le=90)
    deadline_pressure: float = Field(default=0.55, ge=0, le=1)
    collaboration_dependency: float = Field(default=0.55, ge=0, le=1)
    burnout_risk: float = Field(default=0.45, ge=0, le=1)
    stress_score: float = Field(default=0.48, ge=0, le=1)
    wellness_score: float = Field(default=0.62, ge=0, le=1)
    productivity_score: float = Field(default=0.74, ge=0, le=1)
    energy_morning: float = Field(default=0.72, ge=0, le=1)
    energy_afternoon: float = Field(default=0.58, ge=0, le=1)
    flexibility_fit: float = Field(default=0.62, ge=0, le=1)
    manager_support: float = Field(default=0.64, ge=0, le=1)


class WorkLifeBalanceRequest(BaseModel):
    cycle_name: str = "Sustainable Productivity Recovery"
    target_department: str = "Engineering"
    horizon_days: int = Field(default=45, ge=7, le=180)
    employees: list[WorkLifeEmployeeSignal] = Field(default_factory=list, max_length=80)
    realtime: bool = False


class WorkLifeEmployeePlan(BaseModel):
    employee_id: str
    name: str
    team: str
    role: str
    current_wellness_score: float = Field(ge=0, le=100)
    optimized_wellness_score: float = Field(ge=0, le=100)
    burnout_risk_before: float = Field(ge=0, le=100)
    burnout_risk_after: float = Field(ge=0, le=100)
    meeting_reduction_percent: float = Field(ge=0, le=100)
    recurring_hours_to_async: float = Field(ge=0, le=60)
    focus_block: str
    flexible_schedule: str
    task_redistribution_hours: float = Field(ge=0, le=80)
    productivity_wellness_balance: float = Field(ge=0, le=100)
    sustainability_score: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    rationale: str
    evidence: list[str]


class WorkLifeTeamBalance(BaseModel):
    team: str
    employees: int = Field(ge=1)
    wellness_score: float = Field(ge=0, le=100)
    burnout_risk: float = Field(ge=0, le=100)
    meeting_overload: float = Field(ge=0, le=100)
    workload_imbalance: float = Field(ge=0, le=100)
    focus_protection_score: float = Field(ge=0, le=100)
    recommended_policy: str


class WorkLifeScheduleRecommendation(BaseModel):
    category: WorkLifeCategory
    priority: WorkLifeSeverity
    title: str
    action: str
    expected_impact: str
    confidence: float = Field(ge=0, le=1)
    affected_employees: list[str] = Field(default_factory=list)
    affected_teams: list[str] = Field(default_factory=list)


class WorkLifeFocusBlock(BaseModel):
    team: str
    block: str
    protected_hours: float = Field(ge=0, le=30)
    expected_focus_gain: float = Field(ge=0, le=100)
    meeting_conflict_reduction: float = Field(ge=0, le=100)
    rationale: str


class MeetingReductionPlan(BaseModel):
    team: str
    current_meeting_hours: float = Field(ge=0, le=500)
    recommended_meeting_hours: float = Field(ge=0, le=500)
    reduction_percent: float = Field(ge=0, le=100)
    async_conversion_hours: float = Field(ge=0, le=500)
    productivity_recovery_hours: float = Field(ge=0, le=500)
    recommendation: str


class WorkloadRedistributionPlan(BaseModel):
    source_employee: str
    target_employee: str
    team: str
    hours_to_shift: float = Field(ge=0, le=80)
    burnout_reduction: float = Field(ge=0, le=100)
    delivery_risk_change: float
    rationale: str


class WorkLifeForecastPoint(BaseModel):
    day: int
    wellness_score: float = Field(ge=0, le=100)
    burnout_risk: float = Field(ge=0, le=100)
    productivity_score: float = Field(ge=0, le=100)
    meeting_load: float = Field(ge=0, le=100)
    focus_time_score: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)


class WorkLifeHeatmapCell(BaseModel):
    team: str
    metric: str
    score: float = Field(ge=0, le=100)
    severity: WorkLifeSeverity
    recommendation: str


class WorkLifeRiskAlert(BaseModel):
    category: WorkLifeCategory
    severity: WorkLifeSeverity
    score: float = Field(ge=0, le=100)
    message: str
    evidence: list[str]
    intervention: str


class WorkLifeBalanceSummary(BaseModel):
    employees_analyzed: int
    team_count: int
    wellness_score: float = Field(ge=0, le=100)
    burnout_risk: float = Field(ge=0, le=100)
    projected_burnout_reduction: float = Field(ge=0, le=100)
    meeting_reduction_percent: float = Field(ge=0, le=100)
    focus_time_gain_hours: float = Field(ge=0, le=1000)
    task_redistribution_hours: float = Field(ge=0, le=1000)
    productivity_wellness_balance: float = Field(ge=0, le=100)
    sustainable_productivity_score: float = Field(ge=0, le=100)
    stream_sequence: int = 1


class WorkLifeBalanceResponse(BaseModel):
    model: str
    generated_at: datetime
    cycle_name: str
    target_department: str
    horizon_days: int
    ml_model: str
    forecasting_model: str
    optimization_model: str
    source_systems: list[str]
    summary: WorkLifeBalanceSummary
    employee_plans: list[WorkLifeEmployeePlan]
    team_balance: list[WorkLifeTeamBalance]
    focus_blocks: list[WorkLifeFocusBlock]
    meeting_plan: list[MeetingReductionPlan]
    workload_redistribution: list[WorkloadRedistributionPlan]
    recommendations: list[WorkLifeScheduleRecommendation]
    forecast: list[WorkLifeForecastPoint]
    heatmap: list[WorkLifeHeatmapCell]
    risk_alerts: list[WorkLifeRiskAlert]
    executive_insights: list[str]
    storage: str
