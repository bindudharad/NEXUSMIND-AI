from datetime import date

from pydantic import BaseModel, Field


class WorkloadHistoryPoint(BaseModel):
    date: date
    workload: float = Field(ge=0, le=100)
    productivity: float = Field(ge=0, le=100)
    overtime_hours: float = Field(ge=0, le=24)
    attendance_rate: float = Field(ge=0, le=1)
    task_completion_rate: float = Field(ge=0, le=1)
    burnout_risk: float = Field(ge=0, le=1)
    delay_probability: float = Field(ge=0, le=1)


class ForecastRequest(BaseModel):
    department: str = "Engineering"
    horizon_days: int = Field(default=14, ge=3, le=45)
    history: list[WorkloadHistoryPoint] = Field(default_factory=list)


class ForecastPoint(BaseModel):
    date: date
    workload: float
    productivity: float
    burnout_risk: float
    overtime_hours: float
    delay_probability: float
    operational_instability: float
    lower_bound: float
    upper_bound: float


class TrendSignal(BaseModel):
    metric: str
    direction: str
    change: float
    severity: str


class ForecastResponse(BaseModel):
    department: str
    model: str
    horizon_days: int
    confidence: float = Field(ge=0, le=1)
    history: list[WorkloadHistoryPoint]
    forecast: list[ForecastPoint]
    trend_signals: list[TrendSignal]
    team_collapse_probability: float = Field(ge=0, le=1)
    recommendation: str
    storage: str
