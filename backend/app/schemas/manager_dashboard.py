from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


RiskSeverity = Literal["critical", "high", "medium", "low"]


class TeamAnalyticsInput(BaseModel):
    team_id: str
    team_name: str
    department: str
    member_count: int = Field(ge=1, le=500)
    burnout_probability: float = Field(ge=0, le=1)
    productivity_decline: float = Field(ge=0, le=1)
    average_stress: float = Field(ge=0, le=1)
    toxicity_ratio: float = Field(ge=0, le=1)
    overload_ratio: float = Field(ge=0, le=1)
    missed_deadlines: int = Field(ge=0, le=80)
    attendance_rate: float = Field(ge=0, le=1)
    collaboration_score: float = Field(ge=0, le=1)
    overtime_escalation: float = Field(ge=0, le=1)
    dependency_bottlenecks: int = Field(ge=0, le=80)


class EmployeeWorkloadInput(BaseModel):
    employee_id: str
    employee_name: str
    team_name: str
    role: str
    active_tasks: int = Field(ge=0, le=120)
    overtime_hours: float = Field(ge=0, le=40)
    meeting_hours: float = Field(ge=0, le=30)
    productivity_score: float = Field(ge=0, le=1)
    work_intensity: float = Field(ge=0, le=1)
    deadline_pressure: float = Field(ge=0, le=1)
    multi_project_allocation: int = Field(ge=1, le=20)
    stress_score: float = Field(ge=0, le=1)
    task_completion_ratio: float = Field(ge=0, le=1)


class ProjectDeliveryInput(BaseModel):
    project_id: str
    project_name: str
    team_name: str
    task_completion_speed: float = Field(ge=0, le=1)
    team_productivity_trend: float = Field(ge=-1, le=1)
    historical_delivery_rate: float = Field(ge=0, le=1)
    burnout_growth: float = Field(ge=0, le=1)
    team_overload: float = Field(ge=0, le=1)
    dependency_bottlenecks: int = Field(ge=0, le=80)
    resource_shortage: float = Field(ge=0, le=1)
    communication_efficiency: float = Field(ge=0, le=1)
    scope_change_rate: float = Field(ge=0, le=1)
    days_to_deadline: int = Field(ge=1, le=365)


class ManagerDashboardRequest(BaseModel):
    manager_id: str = "mgr-001"
    manager_name: str = "Priya Raman"
    teams: list[TeamAnalyticsInput] = Field(default_factory=list)
    employees: list[EmployeeWorkloadInput] = Field(default_factory=list)
    projects: list[ProjectDeliveryInput] = Field(default_factory=list)
    sensitivity: float = Field(default=0.62, ge=0, le=1)


class RiskyTeam(BaseModel):
    team_id: str
    team_name: str
    department: str
    risk_score: float = Field(ge=0, le=100)
    severity: RiskSeverity
    member_count: int
    drivers: list[str]
    recommendation: str


class OverloadedEmployee(BaseModel):
    employee_id: str
    employee_name: str
    team_name: str
    role: str
    overload_score: float = Field(ge=0, le=100)
    severity: RiskSeverity
    drivers: list[str]
    recommendation: str


class DelayPrediction(BaseModel):
    project_id: str
    project_name: str
    team_name: str
    delay_probability: float = Field(ge=0, le=100)
    severity: RiskSeverity
    projected_delay_days: int = Field(ge=0, le=180)
    bottlenecks: list[str]
    recommendation: str


class ManagerTrendPoint(BaseModel):
    timestamp: datetime
    average_team_risk: float = Field(ge=0, le=100)
    overload_pressure: float = Field(ge=0, le=100)
    delay_risk: float = Field(ge=0, le=100)


class ManagerDashboardSummary(BaseModel):
    teams_at_risk: int
    overloaded_employees: int
    projects_at_delay_risk: int
    average_team_risk: float = Field(ge=0, le=100)
    average_delay_probability: float = Field(ge=0, le=100)


class ManagerDashboardResponse(BaseModel):
    manager_id: str
    manager_name: str
    generated_at: datetime
    model: str
    summary: ManagerDashboardSummary
    risky_teams: list[RiskyTeam]
    overloaded_employees: list[OverloadedEmployee]
    delay_predictions: list[DelayPrediction]
    trend: list[ManagerTrendPoint]
    recommendations: list[str]
    storage: str
