from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


ResearchGradeStatus = Literal["fully_implemented", "partial", "missing", "broken"]
ResearchGradeVerdict = Literal[
    "RESEARCH-GRADE AUTONOMOUS ENTERPRISE INTELLIGENCE PLATFORM",
    "RESEARCH-GRADE GAPS REMAIN",
]


class ResearchGradeFeatureAudit(BaseModel):
    feature_id: int = Field(ge=1, le=17)
    name: str
    status: ResearchGradeStatus
    coverage_percent: float = Field(ge=0, le=100)
    present: bool
    working: bool
    connected: bool
    tested: bool
    production_ready: bool
    required_capabilities: list[str]
    evidence: list[str]
    integrations: list[str]
    endpoints: list[str]
    dashboards: list[str]


class ResearchGradeIntegrationLink(BaseModel):
    source: str
    target: str
    status: ResearchGradeStatus
    evidence: list[str]


class ResearchGradeScorecard(BaseModel):
    integration_score: float = Field(ge=0, le=100)
    innovation_score: float = Field(ge=0, le=100)
    enterprise_score: float = Field(ge=0, le=100)
    research_level_score: float = Field(ge=0, le=100)
    judge_wow_factor_score: float = Field(ge=0, le=100)
    production_readiness_score: float = Field(ge=0, le=100)
    minimum_score: float = Field(ge=0, le=100)


class ResearchGradePlatformResponse(BaseModel):
    model: str
    generated_at: datetime
    feature_coverage_matrix: list[ResearchGradeFeatureAudit]
    integration_audit: list[ResearchGradeIntegrationLink]
    scorecard: ResearchGradeScorecard
    errors_found: list[str]
    errors_fixed: list[str]
    missing_components: list[str]
    implemented_components: list[str]
    final_verdict: ResearchGradeVerdict
    source_systems: list[str]
    storage: str
    stream_sequence: int = 1
