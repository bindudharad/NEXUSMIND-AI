from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


UniverseStatus = Literal["complete", "working", "partial", "missing"]
UniverseWorkflowStatus = Literal["connected", "partial", "disconnected"]
UniverseVerdict = Literal[
    "AI-POWERED VIRTUAL ENTERPRISE UNIVERSE COMPLETE",
    "VIRTUAL ENTERPRISE UNIVERSE GAPS REMAIN",
]


class UniverseScorecard(BaseModel):
    architecture_score: float = Field(ge=0, le=100)
    ai_innovation_score: float = Field(ge=0, le=100)
    digital_twin_score: float = Field(ge=0, le=100)
    multi_agent_score: float = Field(ge=0, le=100)
    simulation_score: float = Field(ge=0, le=100)
    knowledge_brain_score: float = Field(ge=0, le=100)
    executive_intelligence_score: float = Field(ge=0, le=100)
    metaverse_score: float = Field(ge=0, le=100)
    dashboard_score: float = Field(ge=0, le=100)
    security_score: float = Field(ge=0, le=100)
    performance_score: float = Field(ge=0, le=100)
    production_readiness_score: float = Field(ge=0, le=100)
    competition_readiness_score: float = Field(ge=0, le=100)
    judge_wow_factor_score: float = Field(ge=0, le=100)
    minimum_score: float = Field(ge=0, le=100)


class UniverseModuleAudit(BaseModel):
    module: str
    status: UniverseStatus
    score: float = Field(ge=0, le=100)
    api_routes: list[str]
    dashboard_surface: str
    source_systems: list[str]
    integration_evidence: list[str]
    production_ready: bool


class UniverseConnectivityWorkflow(BaseModel):
    name: str
    status: UniverseWorkflowStatus
    trigger: str
    chain: list[str]
    propagated_updates: list[str]
    executive_output: str
    evidence: list[str]


class UniverseDigitalTwinAudit(BaseModel):
    twin: Literal["employee", "team", "department", "project", "client", "company"]
    status: UniverseWorkflowStatus
    source_of_truth: str
    producers: list[str]
    consumers: list[str]
    propagation_example: str
    evidence: list[str]


class UniverseAgentAudit(BaseModel):
    agent: str
    status: UniverseStatus
    responsibilities: list[str]
    memory_keys: list[str]
    tools: list[str]
    collaboration_evidence: list[str]


class UniverseDashboardAudit(BaseModel):
    dashboard: str
    status: UniverseStatus
    realtime: bool
    responsive: bool
    connected_modules: list[str]
    evidence: list[str]


class UniverseSecurityAudit(BaseModel):
    control: str
    status: UniverseStatus
    evidence: str
    fixed: bool


class UniversePerformanceAudit(BaseModel):
    area: str
    metric: str
    value: float
    target: float
    status: UniverseStatus


class VirtualEnterpriseUniverseResponse(BaseModel):
    model: str
    generated_at: datetime
    executive_summary: str
    scorecard: UniverseScorecard
    module_audit: list[UniverseModuleAudit]
    connectivity_workflows: list[UniverseConnectivityWorkflow]
    digital_twin_audit: list[UniverseDigitalTwinAudit]
    agent_ecosystem: list[UniverseAgentAudit]
    knowledge_brain_audit: list[UniverseModuleAudit]
    organizational_brain_audit: list[UniverseModuleAudit]
    simulation_audit: list[UniverseModuleAudit]
    global_intelligence_audit: list[UniverseModuleAudit]
    metaverse_audit: list[UniverseModuleAudit]
    dashboard_audit: list[UniverseDashboardAudit]
    security_audit: list[UniverseSecurityAudit]
    performance_audit: list[UniversePerformanceAudit]
    missing_features: list[str]
    fixed_features: list[str]
    errors_found: list[str]
    errors_fixed: list[str]
    production_readiness_score: float = Field(ge=0, le=100)
    competition_readiness_score: float = Field(ge=0, le=100)
    judge_wow_factor_score: float = Field(ge=0, le=100)
    final_verdict: UniverseVerdict
    final_evaluation: str
    source_systems: list[str]
    storage: str
    stream_sequence: int = 1
