from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


UnifiedStatus = Literal["connected", "partial", "disconnected"]
UnifiedVerdict = Literal[
    "TRUE AUTONOMOUS AI-DRIVEN ENTERPRISE INTELLIGENCE SYSTEM",
    "UNIFICATION GAPS REMAIN",
]


class UnifiedScorecard(BaseModel):
    unified_platform_score: float = Field(ge=0, le=100)
    enterprise_architecture_score: float = Field(ge=0, le=100)
    integration_score: float = Field(ge=0, le=100)
    automation_score: float = Field(ge=0, le=100)
    ai_intelligence_score: float = Field(ge=0, le=100)
    production_readiness_score: float = Field(ge=0, le=100)
    minimum_score: float = Field(ge=0, le=100)


class UnifiedModuleStatus(BaseModel):
    module: str
    status: UnifiedStatus
    score: float = Field(ge=0, le=100)
    evidence: list[str]
    shared_data: list[str]
    api_routes: list[str]
    boardroom_visible: bool
    agent_accessible: bool
    workflow_connected: bool


class UnifiedDataLayerItem(BaseModel):
    entity: str
    status: UnifiedStatus
    source_of_truth: str
    producers: list[str]
    consumers: list[str]
    evidence: list[str]


class CrossModuleWorkflow(BaseModel):
    name: str
    status: UnifiedStatus
    trigger: str
    chain: list[str]
    autonomous_action: str
    evidence: list[str]


class AgentCollaborationAudit(BaseModel):
    status: UnifiedStatus
    agents: list[str]
    messages: int
    shared_memory_records: int
    workflows: int
    decisions: int
    simulations: int
    evidence: list[str]


class ExecutiveExperienceAudit(BaseModel):
    status: UnifiedStatus
    dashboard: str
    panels: list[str]
    visible_domains: list[str]
    voice_commands: list[str]
    evidence: list[str]


class UnifiedEnterpriseResponse(BaseModel):
    model: str
    generated_at: datetime
    scorecard: UnifiedScorecard
    modules_connected: list[str]
    modules_disconnected: list[str]
    module_status: list[UnifiedModuleStatus]
    single_source_of_truth: list[UnifiedDataLayerItem]
    cross_module_workflows: list[CrossModuleWorkflow]
    autonomous_actions: list[CrossModuleWorkflow]
    digital_twin_sync_sources: list[str]
    knowledge_brain_sources: list[str]
    agent_collaboration: AgentCollaborationAudit
    executive_experience: ExecutiveExperienceAudit
    missing_components: list[str]
    fixed_components: list[str]
    regenerated_components: list[str]
    executive_experience_rating: str
    final_verdict: UnifiedVerdict
    proof_statement: str
    source_systems: list[str]
    storage: str
    stream_sequence: int = 1
