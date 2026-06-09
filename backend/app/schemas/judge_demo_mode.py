from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


DemoStatus = Literal["complete", "running", "partial", "missing"]
DemoVerdict = Literal["NEXUSMIND AI COMPLETE", "NEXUSMIND AI DEMO GAPS REMAIN"]


class JudgeDemoMetric(BaseModel):
    label: str
    value: str
    status: DemoStatus
    evidence: str


class JudgeDemoStep(BaseModel):
    order: int = Field(ge=1)
    title: str
    cue: str
    action: str
    systems: list[str]
    api_routes: list[str]
    visual_surface: str
    output: str
    judge_signal: str
    duration_seconds: float = Field(ge=0)
    status: DemoStatus


class JudgeDemoFeatureStatus(BaseModel):
    feature: str
    status: DemoStatus
    evidence: list[str]
    api_routes: list[str]


class JudgeDemoTransformation(BaseModel):
    entity: str
    baseline: str
    projected: str
    severity: Literal["healthy", "warning", "critical"]
    evidence: str


class JudgeDemoAgentLine(BaseModel):
    agent: str
    line: str
    confidence: float = Field(ge=0, le=1)
    source_system: str


class JudgeDemoShadowStage(BaseModel):
    stage: str
    title: str
    signal: str
    status: DemoStatus


class JudgeDemoRecommendation(BaseModel):
    action: str
    impact: str
    owner_agent: str
    priority: Literal["low", "medium", "high", "critical"]


class JudgeDemoImpossibleMoment(BaseModel):
    scenario_question: str
    one_button_label: str
    user_action: str
    visual_transformations: list[JudgeDemoTransformation]
    agent_council: list[JudgeDemoAgentLine]
    shadow_company: list[JudgeDemoShadowStage]
    executive_recommendations: list[JudgeDemoRecommendation]
    judge_understands_in_seconds: int = Field(ge=1, le=30)


class JudgeDemoModeResponse(BaseModel):
    model: str
    generated_at: datetime
    headline: str
    executive_narrative: str
    impossible_moment: JudgeDemoImpossibleMoment
    demo_sequence: list[JudgeDemoStep]
    feature_status: list[JudgeDemoFeatureStatus]
    live_metrics: list[JudgeDemoMetric]
    missing_features_fixed: list[str]
    runtime_errors_fixed: list[str]
    api_issues_fixed: list[str]
    dashboard_issues_fixed: list[str]
    simulation_issues_fixed: list[str]
    agent_issues_fixed: list[str]
    performance_improvements: list[str]
    security_improvements: list[str]
    errors_found: list[str]
    production_readiness_score: float = Field(ge=0, le=100)
    innovation_score: float = Field(ge=0, le=100)
    judge_wow_factor_score: float = Field(ge=0, le=100)
    demo_readiness_score: float = Field(ge=0, le=100)
    final_verdict: DemoVerdict
    source_systems: list[str]
    storage: str
