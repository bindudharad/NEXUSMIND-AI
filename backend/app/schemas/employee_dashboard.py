from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


ScoreStatus = Literal["optimal", "stable", "watch", "high_risk"]


class EmployeeActivityPoint(BaseModel):
    timestamp: datetime
    overtime_hours: float = Field(ge=0, le=40)
    workload_intensity: float = Field(ge=0, le=100)
    meeting_hours: float = Field(ge=0, le=24)
    sentiment_score: float = Field(ge=-1, le=1)
    task_completion_ratio: float = Field(ge=0, le=1)
    attendance_rate: float = Field(ge=0, le=1)
    focus_hours: float = Field(ge=0, le=16)
    collaboration_score: float = Field(ge=0, le=1)
    activity_variance: float = Field(ge=0, le=1)
    negative_message_ratio: float = Field(ge=0, le=1)
    toxic_message_count: int = Field(ge=0, le=100)
    absence_days: float = Field(ge=0, le=20)


class EmployeeDashboardRequest(BaseModel):
    employee_id: str = "emp-live-001"
    employee_name: str = "Aarav Mehta"
    department: str = "Engineering"
    role: str = "Senior Backend Engineer"
    current: EmployeeActivityPoint | None = None
    history: list[EmployeeActivityPoint] = Field(default_factory=list)


class EmployeeScore(BaseModel):
    label: str
    value: float = Field(ge=0, le=100)
    status: ScoreStatus
    trend_delta: float
    drivers: list[str]


class EmployeeTrendPoint(BaseModel):
    timestamp: datetime
    stress_score: float = Field(ge=0, le=100)
    productivity_score: float = Field(ge=0, le=100)
    burnout_probability: float = Field(ge=0, le=100)
    workload_intensity: float = Field(ge=0, le=100)
    sentiment_score: float = Field(ge=-1, le=1)


class EmployeeDashboardResponse(BaseModel):
    employee_id: str
    employee_name: str
    department: str
    role: str
    generated_at: datetime
    model: str
    stress: EmployeeScore
    productivity: EmployeeScore
    burnout_probability: EmployeeScore
    history: list[EmployeeTrendPoint]
    recommendations: list[str]
    model_probabilities: dict[str, float]
    storage: str
