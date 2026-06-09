from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


EmotionPriority = Literal["low", "medium", "high", "critical"]
EmotionHealthStatus = Literal["healthy", "attention_needed", "overloaded", "critical"]
EmotionScope = Literal["employee", "team", "department", "project", "location"]
EmotionMetric = Literal["stress", "happiness", "burnout", "engagement", "motivation", "conflict", "morale"]
EmotionAssistantIntent = Literal[
    "stress",
    "burnout",
    "conflict",
    "morale",
    "happiness",
    "forecast",
    "motivation",
    "recommendation",
    "toxic",
    "silent",
    "summary",
]


class EmotionTextSignal(BaseModel):
    channel: Literal["survey", "feedback", "email", "chat", "meeting", "performance", "manager_note"] = "chat"
    text: str = Field(min_length=2, max_length=4000)
    timestamp: datetime | None = None


class EmployeeEmotionSignal(BaseModel):
    employee_id: str
    name: str
    team: str = "Platform"
    department: str = "Engineering"
    project: str = "Core Platform"
    location: str = "Remote"
    role: str = "Engineer"
    survey_score: float = Field(default=72, ge=0, le=100)
    communication_samples: list[EmotionTextSignal] = Field(default_factory=list, max_length=40)
    workload_hours: float = Field(default=40, ge=0, le=100)
    overtime_hours: float = Field(default=4, ge=0, le=80)
    meeting_hours: float = Field(default=8, ge=0, le=60)
    task_load: float = Field(default=70, ge=0, le=140)
    focus_hours: float = Field(default=5, ge=0, le=14)
    productivity_trend: float = Field(default=0, ge=-100, le=100)
    performance_trend: float = Field(default=0, ge=-100, le=100)
    recognition_count: int = Field(default=2, ge=0, le=100)
    learning_participation: float = Field(default=55, ge=0, le=100)
    collaboration_score: float = Field(default=74, ge=0, le=100)
    manager_support_score: float = Field(default=72, ge=0, le=100)
    conflict_events: int = Field(default=0, ge=0, le=100)
    negative_interactions: int = Field(default=1, ge=0, le=500)
    positive_interactions: int = Field(default=4, ge=0, le=500)
    attrition_risk: float = Field(default=28, ge=0, le=100)


class TeamInteractionSignal(BaseModel):
    source_team: str
    target_team: str
    department: str = "Engineering"
    sentiment_alignment: float = Field(default=0.5, ge=-1, le=1)
    unresolved_issues: int = Field(default=0, ge=0, le=100)
    escalation_count: int = Field(default=0, ge=0, le=100)
    communication_volume: int = Field(default=12, ge=0, le=1000)
    evidence: list[str] = Field(default_factory=list, max_length=12)


class CompanyEmotionMapRequest(BaseModel):
    cycle_name: str = "Realtime Organizational Emotion Review"
    horizon_days: int = Field(default=90, ge=30, le=365)
    employees: list[EmployeeEmotionSignal] = Field(default_factory=list, max_length=1000)
    interactions: list[TeamInteractionSignal] = Field(default_factory=list, max_length=500)
    realtime: bool = False


class EmployeeEmotionScore(BaseModel):
    employee_id: str
    name: str
    team: str
    department: str
    project: str
    location: str
    role: str
    happiness_score: float = Field(ge=0, le=100)
    stress_score: float = Field(ge=0, le=100)
    motivation_score: float = Field(ge=0, le=100)
    burnout_score: float = Field(ge=0, le=100)
    engagement_score: float = Field(ge=0, le=100)
    satisfaction_score: float = Field(ge=0, le=100)
    morale_score: float = Field(ge=0, le=100)
    psychological_risk: float = Field(ge=0, le=100)
    sentiment_score: float = Field(ge=-1, le=1)
    conflict_exposure: float = Field(ge=0, le=100)
    priority: EmotionPriority
    evidence: list[str]


class TeamEmotionScore(BaseModel):
    team: str
    department: str
    headcount: int = Field(ge=1)
    team_health_index: float = Field(ge=0, le=100)
    health_status: EmotionHealthStatus
    health_color: str
    happiness_score: float = Field(ge=0, le=100)
    stress_score: float = Field(ge=0, le=100)
    workload_score: float = Field(ge=0, le=100)
    collaboration_score: float = Field(ge=0, le=100)
    productivity_health_score: float = Field(ge=0, le=100)
    motivation_score: float = Field(ge=0, le=100)
    conflict_risk: float = Field(ge=0, le=100)
    burnout_risk: float = Field(ge=0, le=100)
    engagement_score: float = Field(ge=0, le=100)
    morale_score: float = Field(ge=0, le=100)
    retention_risk: float = Field(ge=0, le=100)
    priority: EmotionPriority
    trend: str
    recommendation: str


class DepartmentEmotionScore(BaseModel):
    department: str
    headcount: int = Field(ge=1)
    department_health_index: float = Field(ge=0, le=100)
    health_status: EmotionHealthStatus
    health_color: str
    morale_score: float = Field(ge=0, le=100)
    burnout_score: float = Field(ge=0, le=100)
    stress_index: float = Field(ge=0, le=100)
    motivation_index: float = Field(ge=0, le=100)
    retention_risk: float = Field(ge=0, le=100)
    happiness_score: float = Field(ge=0, le=100)
    engagement_score: float = Field(ge=0, le=100)
    conflict_risk: float = Field(ge=0, le=100)
    priority: EmotionPriority
    recommendation: str


class EmotionHeatmapPoint(BaseModel):
    scope: EmotionScope
    entity_id: str
    label: str
    department: str
    metric: EmotionMetric
    value: float = Field(ge=0, le=100)
    risk_score: float = Field(ge=0, le=100)
    intensity: float = Field(ge=0, le=100)
    priority: EmotionPriority
    color: str


class EmotionHeatmapZone(BaseModel):
    scope: Literal["company", "department", "team"]
    entity_id: str
    label: str
    department: str
    health_index: float = Field(ge=0, le=100)
    health_status: EmotionHealthStatus
    color: str
    stress_score: float = Field(ge=0, le=100)
    burnout_score: float = Field(ge=0, le=100)
    workload_score: float = Field(ge=0, le=100)
    morale_score: float = Field(ge=0, le=100)
    collaboration_score: float = Field(ge=0, le=100)
    productivity_health_score: float = Field(ge=0, le=100)
    conflict_risk: float = Field(ge=0, le=100)
    forecast_30d_burnout: float = Field(ge=0, le=100)
    forecast_90d_burnout: float = Field(ge=0, le=100)
    attrition_risk: float = Field(ge=0, le=100)
    trend: Literal["improving", "stable", "declining", "critical"]
    explanation: str
    recommendations: list[str]
    twin_evidence: list[str]
    agent_evidence: list[str]


class ConflictRiskInsight(BaseModel):
    source_entity: str
    target_entity: str
    scope: Literal["employee", "team", "department"]
    conflict_probability: float = Field(ge=0, le=100)
    communication_breakdown_risk: float = Field(ge=0, le=100)
    toxic_interaction_index: float = Field(ge=0, le=100)
    reason: str
    evidence: list[str]
    recommended_action: str


class BurnoutPrediction(BaseModel):
    entity_id: str
    label: str
    scope: Literal["employee", "team", "department"]
    burnout_probability: float = Field(ge=0, le=100)
    overwork_risk: float = Field(ge=0, le=100)
    fatigue_trend: float = Field(ge=-100, le=100)
    mental_workload_pressure: float = Field(ge=0, le=100)
    forecast_30d: float = Field(ge=0, le=100)
    forecast_90d: float = Field(ge=0, le=100)
    recommendation: str


class MotivationTrend(BaseModel):
    entity_id: str
    label: str
    scope: Literal["employee", "team", "department"]
    motivation_score: float = Field(ge=0, le=100)
    trend_delta: float = Field(ge=-100, le=100)
    drivers: list[str]
    recommendation: str


class EmotionForecastPoint(BaseModel):
    period: Literal["30_days", "90_days", "6_months", "1_year"]
    metric: EmotionMetric
    scope: EmotionScope
    entity_id: str
    label: str
    projected_score: float = Field(ge=0, le=100)
    risk_probability: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    driver: str


class EmotionRecommendation(BaseModel):
    title: str
    category: Literal["workload", "conflict", "wellness", "motivation", "engagement", "manager_intervention", "team_structure", "retention"]
    priority: EmotionPriority
    action: str
    rationale: str
    expected_improvement: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    triggered_workflow: str


class EmotionDataPipelineStatus(BaseModel):
    source: Literal["survey", "feedback", "meeting", "chat", "email_metadata", "performance_review", "engagement", "workload", "project_activity", "attendance"]
    signals_processed: int = Field(ge=0)
    privacy_control: str
    permission_scope: str
    status: Literal["active", "limited", "blocked"] = "active"


class TeamEmotionClassification(BaseModel):
    team: str
    department: str
    classification: Literal["happy", "healthy", "watch", "toxic"]
    score: float = Field(ge=0, le=100)
    reason: str
    drivers: list[str]
    recommended_action: str


class SilentEmployeeRisk(BaseModel):
    employee_id: str
    name: str
    team: str
    department: str
    isolation_risk: float = Field(ge=0, le=100)
    participation_delta: float = Field(ge=-100, le=100)
    communication_withdrawal_score: float = Field(ge=0, le=100)
    reason: str
    recommended_action: str


class Emotion3DNode(BaseModel):
    node_id: str
    label: str
    scope: EmotionScope
    department: str
    x: float
    y: float
    z: float
    stress: float = Field(ge=0, le=100)
    burnout: float = Field(ge=0, le=100)
    morale: float = Field(ge=0, le=100)
    conflict: float = Field(ge=0, le=100)
    intensity: float = Field(ge=0, le=100)
    color: str


class EmotionAgentContribution(BaseModel):
    agent: str
    domain: str
    finding: str
    recommended_action: str
    confidence: float = Field(ge=0, le=1)


class CompanyEmotionMapSummary(BaseModel):
    employees_analyzed: int = Field(ge=0)
    teams_analyzed: int = Field(ge=0)
    departments_analyzed: int = Field(ge=0)
    high_stress_hotspots: int = Field(ge=0)
    high_burnout_hotspots: int = Field(ge=0)
    high_conflict_zones: int = Field(ge=0)
    average_happiness: float = Field(ge=0, le=100)
    average_stress: float = Field(ge=0, le=100)
    average_burnout: float = Field(ge=0, le=100)
    average_motivation: float = Field(ge=0, le=100)
    average_engagement: float = Field(ge=0, le=100)
    morale_forecast_90d: float = Field(ge=0, le=100)
    organizational_health_score: float = Field(ge=0, le=100)
    company_health_status: EmotionHealthStatus = "healthy"
    company_health_color: str = "#7CF0A6"
    toxic_teams: int = Field(default=0, ge=0)
    happy_teams: int = Field(default=0, ge=0)
    silent_employee_risks: int = Field(default=0, ge=0)
    production_readiness_score: float = Field(default=0, ge=0, le=100)
    innovation_score: float = Field(default=0, ge=0, le=100)
    stream_sequence: int = 1


class CompanyEmotionMapResponse(BaseModel):
    model: str
    generated_at: datetime
    cycle_name: str
    horizon_days: int
    employee_scores: list[EmployeeEmotionScore]
    team_scores: list[TeamEmotionScore]
    department_scores: list[DepartmentEmotionScore]
    heatmap: list[EmotionHeatmapPoint]
    heatmap_zones: list[EmotionHeatmapZone]
    conflict_risks: list[ConflictRiskInsight]
    burnout_predictions: list[BurnoutPrediction]
    motivation_trends: list[MotivationTrend]
    forecasts: list[EmotionForecastPoint]
    recommendations: list[EmotionRecommendation]
    data_pipeline: list[EmotionDataPipelineStatus]
    privacy_controls: list[str]
    toxic_team_risks: list[TeamEmotionClassification]
    happy_team_signals: list[TeamEmotionClassification]
    silent_employee_risks: list[SilentEmployeeRisk]
    emotion_3d_nodes: list[Emotion3DNode]
    agent_council: list[EmotionAgentContribution]
    assistant_prompts: list[str]
    executive_insights: list[str]
    summary: CompanyEmotionMapSummary
    source_systems: list[str]
    digital_twin_updates: list[str]
    workflow_triggers: list[str]
    final_verdict: str = "AI EMOTION RADAR COMPLETE"
    storage: str


class EmotionAssistantRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)


class EmotionAssistantResponse(BaseModel):
    model: str
    generated_at: datetime
    question: str
    intent: EmotionAssistantIntent
    answer: str
    confidence: float = Field(ge=0, le=1)
    cited_entities: list[str]
    recommended_actions: list[str]
    evidence: list[str]
    source_systems: list[str]
    storage: str
