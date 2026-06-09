from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


BrainComponentStatus = Literal["active", "watch", "degraded", "missing"]
BrainVerdict = Literal["LIVING AI COMPANY BRAIN COMPLETE", "LIVING AI COMPANY BRAIN GAPS REMAIN"]


class BrainComponentSignal(BaseModel):
    component: str
    status: BrainComponentStatus
    score: float = Field(ge=0, le=100)
    summary: str
    evidence: list[str] = Field(default_factory=list)
    source_systems: list[str] = Field(default_factory=list)


class CompanyAwarenessSnapshot(BaseModel):
    employees_mirrored: int = Field(ge=0)
    teams_mirrored: int = Field(ge=0)
    departments_mirrored: int = Field(ge=0)
    projects_mirrored: int = Field(ge=0)
    clients_mirrored: int = Field(ge=0)
    current_revenue: float
    company_health_score: float = Field(ge=0, le=100)
    productivity_score: float = Field(ge=0, le=100)
    burnout_risk: float = Field(ge=0, le=100)
    attrition_risk: float = Field(ge=0, le=100)
    top_risk_team: str
    top_risk_score: float = Field(ge=0, le=100)
    active_alerts: int = Field(ge=0)
    source_systems: list[str] = Field(default_factory=list)


class MemorySnapshot(BaseModel):
    documents_indexed: int = Field(ge=0)
    chunks_indexed: int = Field(ge=0)
    graph_nodes: int = Field(ge=0)
    graph_edges: int = Field(ge=0)
    experts_detected: int = Field(ge=0)
    incidents_detected: int = Field(ge=0)
    solutions_detected: int = Field(ge=0)
    sample_question: str
    sample_answer: str
    citations: list[str] = Field(default_factory=list)
    final_verdict: str
    source_systems: list[str] = Field(default_factory=list)


class CausalReasoningStep(BaseModel):
    step: int = Field(ge=1)
    cause: str
    effect: str
    metric: str
    confidence: float = Field(ge=0, le=1)
    evidence: list[str] = Field(default_factory=list)


class BrainPredictionSignal(BaseModel):
    domain: Literal["burnout", "attrition", "project_delay", "revenue", "client_risk", "operational_risk"]
    current_value: float
    projected_value: float
    delta: float
    unit: str
    confidence: float = Field(ge=0, le=1)
    explanation: str
    source_systems: list[str] = Field(default_factory=list)


class SimulationSnapshot(BaseModel):
    scenario: str
    success_probability: float = Field(ge=0, le=100)
    risk_score: float = Field(ge=0, le=100)
    revenue_impact: float
    burnout_change: float
    delivery_delay_days: float = Field(ge=0)
    ai_explanation: str
    risk_propagation_path: list[str] = Field(default_factory=list)
    digital_twin_evidence: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    source_systems: list[str] = Field(default_factory=list)


class AgentCouncilSnapshot(BaseModel):
    active_agents: int = Field(ge=0)
    messages: int = Field(ge=0)
    workflows: int = Field(ge=0)
    shared_memory_records: int = Field(ge=0)
    coordination_score: float = Field(ge=0, le=100)
    average_response_ms: int = Field(ge=0)
    executive_brief: str
    council_discussion: list[str] = Field(default_factory=list)
    decisions: list[str] = Field(default_factory=list)
    source_systems: list[str] = Field(default_factory=list)


class LearningSnapshot(BaseModel):
    learning_engine_status: str
    recommendation_accuracy: float = Field(ge=0, le=100)
    forecast_accuracy: float = Field(ge=0, le=100)
    learning_maturity_score: float = Field(ge=0, le=100)
    drift_signals: int = Field(ge=0)
    retraining_events: int = Field(ge=0)
    feedback_loops: int = Field(ge=0)
    evidence: list[str] = Field(default_factory=list)
    source_systems: list[str] = Field(default_factory=list)


class DigitalTwinBrainSnapshot(BaseModel):
    company_twin_status: str
    active_simulations: int = Field(ge=0)
    recommended_scenario: str
    highest_risk_scenario: str
    mirror_sync_completeness: float = Field(ge=0, le=100)
    employees_mirrored: int = Field(ge=0)
    teams_mirrored: int = Field(ge=0)
    departments_mirrored: int = Field(ge=0)
    projects_mirrored: int = Field(ge=0)
    twin_updates: list[str] = Field(default_factory=list)
    source_systems: list[str] = Field(default_factory=list)


class ExecutiveIntelligenceSnapshot(BaseModel):
    answer: str
    confidence: float = Field(ge=0, le=1)
    recommended_actions: list[str] = Field(default_factory=list)
    cited_evidence: list[str] = Field(default_factory=list)
    current_company_focus: list[str] = Field(default_factory=list)
    source_systems: list[str] = Field(default_factory=list)


class BrainIntegrationEdge(BaseModel):
    source: str
    target: str
    event: str
    evidence: list[str] = Field(default_factory=list)


class LivingCompanyBrainResponse(BaseModel):
    model: str
    generated_at: datetime
    company_brain_status: BrainComponentStatus
    organism_score: float = Field(ge=0, le=100)
    awareness: CompanyAwarenessSnapshot
    memory: MemorySnapshot
    reasoning_chain: list[CausalReasoningStep]
    predictions: list[BrainPredictionSignal]
    simulation: SimulationSnapshot
    multi_agent: AgentCouncilSnapshot
    learning: LearningSnapshot
    digital_twin: DigitalTwinBrainSnapshot
    executive_intelligence: ExecutiveIntelligenceSnapshot
    component_signals: list[BrainComponentSignal]
    integration_graph: list[BrainIntegrationEdge]
    missing_components: list[str]
    fixed_components: list[str]
    errors_found: list[str]
    errors_fixed: list[str]
    performance_notes: dict[str, float | int]
    production_readiness_score: float = Field(ge=0, le=100)
    innovation_score: float = Field(ge=0, le=100)
    judge_wow_factor_score: float = Field(ge=0, le=100)
    final_verdict: BrainVerdict
    source_systems: list[str]
    storage: str


class LivingCompanyBrainAskRequest(BaseModel):
    question: str = Field(default="What is the biggest risk?", min_length=2, max_length=800)
    session_id: str = Field(default="living-company-brain", max_length=120)
    horizon_months: int = Field(default=3, ge=1, le=36)


class LivingCompanyBrainAnswerResponse(BaseModel):
    model: str
    generated_at: datetime
    question: str
    answer: str
    mode: Literal["executive_intelligence", "enterprise_memory", "future_simulation"]
    confidence: float = Field(ge=0, le=1)
    recommended_actions: list[str] = Field(default_factory=list)
    cited_evidence: list[str] = Field(default_factory=list)
    consulted_engines: list[str] = Field(default_factory=list)
    brain_status: BrainComponentStatus
    organism_score: float = Field(ge=0, le=100)
    final_verdict: BrainVerdict
    storage: str
