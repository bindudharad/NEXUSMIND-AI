from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


CommunicationPriority = Literal["low", "medium", "high", "critical"]


class CommunicationMessage(BaseModel):
    message_id: str
    employee_id: str
    employee_name: str
    department: str = "Engineering"
    team: str = "Platform"
    channel: Literal["chat", "email", "meeting", "review", "ticket"] = "chat"
    text: str = Field(min_length=2, max_length=5000)
    timestamp: datetime | None = None
    thread_id: str = "general"
    recipient_ids: list[str] = Field(default_factory=list, max_length=20)
    response_delay_minutes: float = Field(default=15, ge=0, le=10080)
    expected_response_minutes: float = Field(default=60, ge=1, le=10080)
    unresolved: bool = False


class CommunicationInteractionSignal(BaseModel):
    source_id: str
    source_name: str
    target_id: str
    target_name: str
    department: str = "Engineering"
    team: str = "Platform"
    messages_sent: int = Field(default=12, ge=0, le=5000)
    messages_received: int = Field(default=10, ge=0, le=5000)
    average_response_minutes: float = Field(default=45, ge=0, le=10080)
    baseline_response_minutes: float = Field(default=50, ge=1, le=10080)
    collaboration_frequency: float = Field(default=0.65, ge=0, le=1)
    sentiment_alignment: float = Field(default=0.58, ge=-1, le=1)
    conflict_incidents: int = Field(default=0, ge=0, le=100)
    unanswered_threads: int = Field(default=0, ge=0, le=200)
    participation_delta: float = Field(default=0, ge=-1, le=1)


class CommunicationRequest(BaseModel):
    cycle_name: str = "Realtime Communication Quality Review"
    horizon_days: int = Field(default=30, ge=1, le=180)
    messages: list[CommunicationMessage] = Field(default_factory=list, max_length=250)
    interactions: list[CommunicationInteractionSignal] = Field(default_factory=list, max_length=400)
    realtime: bool = False


class MessageRiskInsight(BaseModel):
    message_id: str
    employee_id: str
    employee_name: str
    department: str
    team: str
    channel: str
    sentiment: str
    primary_emotion: str
    sentiment_score: float = Field(ge=-1, le=1)
    toxicity_score: float = Field(ge=0, le=100)
    aggression_score: float = Field(ge=0, le=100)
    conflict_escalation_score: float = Field(ge=0, le=100)
    communication_quality_score: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    evidence: list[str]
    recommendation: str


class TeamCommunicationHeatmapPoint(BaseModel):
    department: str
    team: str
    toxicity_risk: float = Field(ge=0, le=100)
    morale_score: float = Field(ge=0, le=100)
    collaboration_quality: float = Field(ge=0, le=100)
    conflict_probability: float = Field(ge=0, le=100)
    isolation_risk: float = Field(ge=0, le=100)
    messages_analyzed: int = Field(ge=0)
    priority: CommunicationPriority


class InteractionGraphEdge(BaseModel):
    source_id: str
    source_name: str
    target_id: str
    target_name: str
    department: str
    team: str
    collaboration_score: float = Field(ge=0, le=100)
    response_health: float = Field(ge=0, le=100)
    sentiment_alignment: float = Field(ge=0, le=100)
    conflict_probability: float = Field(ge=0, le=100)
    isolation_signal: float = Field(ge=0, le=100)
    recommendation: str


class ConflictForecast(BaseModel):
    department: str
    team: str
    conflict_probability: float = Field(ge=0, le=100)
    projected_productivity_loss_hours: float = Field(ge=0, le=10000)
    confidence: float = Field(ge=0, le=1)
    drivers: list[str]
    forecast: list[float] = Field(default_factory=list)


class IsolationRiskInsight(BaseModel):
    employee_id: str
    employee_name: str
    department: str
    team: str
    isolation_risk: float = Field(ge=0, le=100)
    interaction_drop: float = Field(ge=0, le=100)
    response_delay_pressure: float = Field(ge=0, le=100)
    unanswered_threads: int = Field(ge=0)
    recommendation: str


class CommunicationRecommendation(BaseModel):
    title: str
    category: Literal["toxicity", "aggression", "collaboration", "isolation", "conflict", "morale"]
    priority: CommunicationPriority
    impact_score: float = Field(ge=0, le=100)
    action: str
    rationale: str
    confidence: float = Field(ge=0, le=1)


class CommunicationAlert(BaseModel):
    title: str
    priority: CommunicationPriority
    probability: float = Field(ge=0, le=100)
    impact: str
    recommendation: str


class CommunicationSummary(BaseModel):
    messages_analyzed: int
    interactions_analyzed: int
    high_toxicity_alerts: int
    isolation_risks: int
    average_quality_score: float = Field(ge=0, le=100)
    average_collaboration_quality: float = Field(ge=0, le=100)
    conflict_probability: float = Field(ge=0, le=100)
    morale_score: float = Field(ge=0, le=100)
    stream_sequence: int = 1


class CommunicationResponse(BaseModel):
    model: str
    generated_at: datetime
    cycle_name: str
    horizon_days: int
    message_risks: list[MessageRiskInsight]
    team_heatmap: list[TeamCommunicationHeatmapPoint]
    interaction_graph: list[InteractionGraphEdge]
    conflict_forecasts: list[ConflictForecast]
    isolation_risks: list[IsolationRiskInsight]
    recommendations: list[CommunicationRecommendation]
    alerts: list[CommunicationAlert]
    executive_insights: list[str]
    summary: CommunicationSummary
    source_systems: list[str]
    storage: str
