from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


AlertSeverity = Literal["critical", "high", "medium", "low"]
AlertCategory = Literal[
    "burnout",
    "productivity",
    "overload",
    "delay",
    "security",
    "toxicity",
    "attendance",
    "revenue",
    "operations",
]
AlertScenario = Literal["default", "crisis"]


class AlertDetectionRequest(BaseModel):
    scenario: AlertScenario = "default"
    sensitivity: float = Field(default=0.68, ge=0, le=1)
    include_recommendations: bool = True


class AIAlert(BaseModel):
    alert_id: str
    category: AlertCategory
    title: str
    message: str
    severity: AlertSeverity
    risk_score: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    source_systems: list[str]
    evidence: list[str]
    recommendation: str
    created_at: datetime
    acknowledged: bool = False
    group_key: str
    priority_rank: int


class AlertSummary(BaseModel):
    total: int
    critical: int
    high: int
    unacknowledged: int
    average_risk: float = Field(ge=0, le=100)
    stream_sequence: int


class AlertFeedResponse(BaseModel):
    model: str
    generated_at: datetime
    scenario: AlertScenario
    adaptive_threshold: float = Field(ge=0, le=100)
    alerts: list[AIAlert]
    summary: AlertSummary
    storage: str


class AlertAckRequest(BaseModel):
    alert_id: str
    acknowledged: bool = True
    notes: str = Field(default="", max_length=500)


class AlertAckResponse(BaseModel):
    alert_id: str
    acknowledged: bool
    message: str
    storage: str
