from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


StackStatus = Literal["complete", "working", "partial", "missing"]
WorkflowStatus = Literal["connected", "partial", "missing"]
FinalInnovationVerdict = Literal[
    "JUDGE-WINNING INNOVATION STACK COMPLETE",
    "JUDGE-WINNING INNOVATION STACK GAPS REMAIN",
]


class InnovationStackCapabilityAudit(BaseModel):
    capability: str
    status: StackStatus
    score: float = Field(ge=0, le=100)
    required_systems: list[str]
    verified_systems: list[str]
    api_routes: list[str]
    integration_evidence: list[str]
    dynamic_outputs: bool
    production_ready: bool


class InnovationStackWorkflow(BaseModel):
    name: str
    status: WorkflowStatus
    trigger: str
    chain: list[str]
    propagation: list[str]
    executive_outcome: str
    evidence: list[str]


class EnterpriseProblemSolvingAudit(BaseModel):
    problem: str
    status: StackStatus
    decision_support: str
    systems: list[str]
    evidence: list[str]


class InnovationStackPerformanceMetric(BaseModel):
    metric: str
    value: float
    target: float
    unit: str
    status: StackStatus


class CompetitionComparison(BaseModel):
    comparator: str
    verdict: str
    evidence: list[str]


class InnovationStackScorecard(BaseModel):
    ai_innovation: float = Field(ge=0, le=100)
    technical_complexity: float = Field(ge=0, le=100)
    research_value: float = Field(ge=0, le=100)
    business_value: float = Field(ge=0, le=100)
    visual_impact: float = Field(ge=0, le=100)
    industry_relevance: float = Field(ge=0, le=100)
    scalability: float = Field(ge=0, le=100)
    judge_appeal: float = Field(ge=0, le=100)
    production_readiness: float = Field(ge=0, le=100)
    startup_potential: float = Field(ge=0, le=100)
    minimum_score: float = Field(ge=0, le=100)


class JudgeWinningInnovationStackResponse(BaseModel):
    model: str
    generated_at: datetime
    executive_summary: str
    ai_status: StackStatus
    prediction_status: StackStatus
    simulation_status: StackStatus
    multi_agent_status: StackStatus
    digital_twin_status: StackStatus
    self_learning_status: StackStatus
    analytics_status: StackStatus
    ui_status: StackStatus
    integration_status: StackStatus
    scorecard: InnovationStackScorecard
    capability_audit: list[InnovationStackCapabilityAudit]
    integration_workflows: list[InnovationStackWorkflow]
    enterprise_problem_solving: list[EnterpriseProblemSolvingAudit]
    competition_comparison: list[CompetitionComparison]
    missing_components: list[str]
    fixed_components: list[str]
    errors_found: list[str]
    errors_fixed: list[str]
    performance_metrics: list[InnovationStackPerformanceMetric]
    production_readiness_score: float = Field(ge=0, le=100)
    innovation_score: float = Field(ge=0, le=100)
    research_score: float = Field(ge=0, le=100)
    startup_potential_score: float = Field(ge=0, le=100)
    judge_wow_factor_score: float = Field(ge=0, le=100)
    final_verdict: FinalInnovationVerdict
    final_answer: str
    source_systems: list[str]
    storage: str
