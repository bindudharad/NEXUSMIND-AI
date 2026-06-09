from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


EvaluatorName = Literal[
    "College Project Judge",
    "Hackathon Judge",
    "Startup Investor",
    "Enterprise CTO",
    "Enterprise CIO",
    "Product Manager",
    "AI Researcher",
    "Recruiter",
]
JudgeImpactStatus = Literal["elite", "strong", "needs_work", "weak"]
JudgeVerdict = Literal["WORLD-CLASS ENTERPRISE AI PLATFORM", "NEEDS PRODUCT HARDENING"]


class EvaluatorAudit(BaseModel):
    evaluator: EvaluatorName
    innovation_score: float = Field(ge=0, le=100)
    enterprise_readiness_score: float = Field(ge=0, le=100)
    technical_complexity_score: float = Field(ge=0, le=100)
    product_maturity_score: float = Field(ge=0, le=100)
    market_potential_score: float = Field(ge=0, le=100)
    impressive: list[str]
    weak: list[str]
    unfinished: list[str]
    fake_signals: list[str]
    enterprise_grade: list[str]
    production_belief: str
    status: JudgeImpactStatus


class JudgeImpactScorecard(BaseModel):
    innovation_score: float = Field(ge=0, le=100)
    enterprise_readiness_score: float = Field(ge=0, le=100)
    product_maturity_score: float = Field(ge=0, le=100)
    startup_potential_score: float = Field(ge=0, le=100)
    technical_complexity_score: float = Field(ge=0, le=100)
    judge_wow_factor_score: float = Field(ge=0, le=100)
    recruiter_impact_score: float = Field(ge=0, le=100)
    production_readiness_score: float = Field(ge=0, le=100)
    minimum_score: float = Field(ge=0, le=100)


class ProductAuditDimension(BaseModel):
    name: str
    score: float = Field(ge=0, le=100)
    status: JudgeImpactStatus
    evidence: list[str]
    improvements: list[str]


class ProductDifferentiation(BaseModel):
    question: str
    answer: str
    proof_points: list[str]


class IntegrationAuditItem(BaseModel):
    integration: str
    status: Literal["connected", "partial", "disconnected"]
    evidence: list[str]


class JudgeImpactValidationResponse(BaseModel):
    model: str
    generated_at: datetime
    scorecard: JudgeImpactScorecard
    evaluator_audits: list[EvaluatorAudit]
    product_audit: list[ProductAuditDimension]
    differentiation_report: list[ProductDifferentiation]
    integration_status: list[IntegrationAuditItem]
    missing_components: list[str]
    fixed_components: list[str]
    regenerated_components: list[str]
    residual_risks: list[str]
    production_readiness_evidence: list[str]
    final_verdict: JudgeVerdict
    executive_summary: str
    source_systems: list[str]
    storage: str
    stream_sequence: int = 1
