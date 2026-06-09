from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


ImpressionStatus = Literal["elite", "strong", "needs_work", "weak"]


class ImpressionMetric(BaseModel):
    label: str
    value: str
    explanation: str


class ImpressionDimension(BaseModel):
    name: str
    category: str
    score: float = Field(ge=0, le=100)
    status: ImpressionStatus
    verdict: str
    evidence: list[str] = Field(default_factory=list)
    proof_points: list[str] = Field(default_factory=list)
    upgrade_actions: list[str] = Field(default_factory=list)


class DemoMoment(BaseModel):
    title: str
    narrative: str
    proof: str
    route: str
    component: str


class RecruiterImpressionSummary(BaseModel):
    overall_score: float = Field(ge=0, le=100)
    startup_score: float = Field(ge=0, le=100)
    industry_score: float = Field(ge=0, le=100)
    research_score: float = Field(ge=0, le=100)
    recruiter_score: float = Field(ge=0, le=100)
    judge_wow_score: float = Field(ge=0, le=100)
    verdict: str
    strongest_signal: str
    residual_risk_level: Literal["low", "medium", "high"]
    stream_sequence: int = 1


class RecruiterImpressionResponse(BaseModel):
    model: str
    generated_at: datetime
    summary: RecruiterImpressionSummary
    dimensions: list[ImpressionDimension]
    metrics: list[ImpressionMetric]
    demo_moments: list[DemoMoment]
    technical_proof: list[str]
    residual_risks: list[str]
    storage: str
