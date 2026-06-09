from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


PowerFeatureStatus = Literal["ready", "warning", "missing", "error"]
PowerSeverity = Literal["low", "medium", "high", "critical"]
ExplanationTarget = Literal["burnout", "project_delay", "team_compatibility", "productivity", "recommendation"]


class PowerFeatureCheck(BaseModel):
    name: str
    category: str
    status: PowerFeatureStatus
    details: str
    evidence: list[str] = Field(default_factory=list)
    remediation: str | None = None


class PowerFeatureSummary(BaseModel):
    total: int
    ready: int
    warnings: int
    missing: int
    errors: int
    power_score: float = Field(ge=0, le=100)


class PowerFeatureAuditResponse(BaseModel):
    model: str
    generated_at: datetime
    summary: PowerFeatureSummary
    checks: list[PowerFeatureCheck]
    verdict: str


class RealtimeKPI(BaseModel):
    label: str
    value: float
    unit: str
    delta: float
    severity: PowerSeverity
    source_system: str


class RealtimeEvent(BaseModel):
    event_id: str
    title: str
    message: str
    severity: PowerSeverity
    source_systems: list[str]
    created_at: datetime


class RealtimeAnalyticsResponse(BaseModel):
    model: str
    generated_at: datetime
    sequence: int
    mode: Literal["default", "pressure", "crisis"] = "default"
    kpis: list[RealtimeKPI]
    events: list[RealtimeEvent]
    source_systems: list[str]
    sync_status: Literal["streaming", "ready", "degraded"]
    storage: str


class FeatureAttribution(BaseModel):
    feature: str
    value: float
    contribution: float
    direction: Literal["increases_risk", "reduces_risk", "neutral"]
    importance: float = Field(ge=0, le=1)
    evidence: str


class CounterfactualAction(BaseModel):
    action: str
    expected_prediction: float
    impact: float
    rationale: str


class XAIExplanationRequest(BaseModel):
    target: ExplanationTarget = "burnout"
    features: dict[str, float] = Field(default_factory=dict)
    scenario: Literal["default", "crisis"] = "default"


class XAIExplanationResponse(BaseModel):
    model: str
    generated_at: datetime
    target: ExplanationTarget
    prediction: float = Field(ge=0, le=100)
    baseline_prediction: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    methods: list[str]
    shap_values: list[FeatureAttribution]
    lime_weights: list[FeatureAttribution]
    explanation: str
    counterfactuals: list[CounterfactualAction]
    decision_trace: list[str]
    source_systems: list[str]
    storage: str


class GNNNode(BaseModel):
    employee_id: str
    name: str
    department: str
    embedding: list[float] = Field(default_factory=list, min_length=4, max_length=8)
    influence_score: float = Field(ge=0, le=100)
    burnout_spread_risk: float = Field(ge=0, le=100)
    compatibility_projection: float = Field(ge=0, le=100)
    conflict_projection: float = Field(ge=0, le=100)
    leadership_influence: float = Field(ge=0, le=100)


class GNNEdge(BaseModel):
    source_id: str
    target_id: str
    attention_weight: float = Field(ge=0, le=1)
    collaboration_strength: float = Field(ge=0, le=100)
    burnout_transmission: float = Field(ge=0, le=100)
    conflict_probability: float = Field(ge=0, le=100)
    explanation: str


class GNNTeamRelationResponse(BaseModel):
    model: str
    generated_at: datetime
    architecture: str
    training_metrics: dict[str, float | int | str]
    nodes: list[GNNNode]
    edges: list[GNNEdge]
    propagation_alerts: list[str]
    recommendations: list[str]
    storage: str
    stream_sequence: int = 1


class ManagerAssistantRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    manager_id: str = "mgr-001"
    include_realtime: bool = True


class AssistantContextSource(BaseModel):
    system: str
    title: str
    snippet: str
    confidence: float = Field(ge=0, le=1)


class ManagerAssistantResponse(BaseModel):
    model: str
    generated_at: datetime
    question: str
    answer: str
    risk_summary: str
    recommended_actions: list[str]
    context_sources: list[AssistantContextSource]
    reasoning_trace: list[str]
    confidence: float = Field(ge=0, le=1)
    storage: str
    stream_sequence: int = 1
