from pydantic import BaseModel, Field


class EnterpriseMetric(BaseModel):
    label: str
    value: str
    trend: float
    status: str


class RiskSignal(BaseModel):
    id: str
    name: str
    probability: float = Field(ge=0, le=1)
    impact: str
    recommendation: str


class DepartmentSignal(BaseModel):
    department: str
    productivity: int
    wellness: int
    security: int
    risk: int


class AgentMessage(BaseModel):
    agent: str
    message: str
    severity: str


class DashboardForecastPoint(BaseModel):
    label: str
    revenue: float
    risk: float
    productivity: float


class DashboardOverview(BaseModel):
    company_health: int
    prediction_confidence: int
    metrics: list[EnterpriseMetric]
    risk_signals: list[RiskSignal]
    departments: list[DepartmentSignal]
    agent_messages: list[AgentMessage]
    forecast_series: list[DashboardForecastPoint]
