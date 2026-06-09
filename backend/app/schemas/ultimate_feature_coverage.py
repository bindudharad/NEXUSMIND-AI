from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


FeatureGroupStatus = Literal["present", "missing", "partial", "broken", "fixed"]
IntegrationWorkflowStatus = Literal["connected", "partial", "disconnected"]
UltimateFeatureVerdict = Literal["NEXUSMIND AI COMPLETE", "NEXUSMIND AI FEATURE COVERAGE GAPS REMAIN"]


class UltimateFeatureGroupAudit(BaseModel):
    group_key: str
    feature_group: str
    status: FeatureGroupStatus
    present: bool
    coverage_percent: float = Field(ge=0, le=100)
    required_capabilities: list[str]
    verified_components: list[str]
    backend_systems: list[str]
    frontend_surfaces: list[str]
    api_routes: list[str]
    integration_links: list[str]
    evidence: list[str]
    fixed_components: list[str]
    production_ready: bool


class UltimateIntegrationWorkflow(BaseModel):
    name: str
    status: IntegrationWorkflowStatus
    trigger: str
    chain: list[str]
    evidence: list[str]
    executive_outcome: str


class UltimateFeatureCoverageResponse(BaseModel):
    model: str
    generated_at: datetime
    platform_positioning: str
    executive_summary: str
    feature_status_table: list[UltimateFeatureGroupAudit]
    integration_workflows: list[UltimateIntegrationWorkflow]
    missing_components: list[str]
    fixed_components: list[str]
    new_components_added: list[str]
    integration_issues_found: list[str]
    integration_issues_fixed: list[str]
    runtime_errors_fixed: list[str]
    build_errors_fixed: list[str]
    api_errors_fixed: list[str]
    dashboard_errors_fixed: list[str]
    agent_errors_fixed: list[str]
    simulation_errors_fixed: list[str]
    overall_coverage_percent: float = Field(ge=0, le=100)
    ai_innovation_score: float = Field(ge=0, le=100)
    technical_complexity_score: float = Field(ge=0, le=100)
    research_score: float = Field(ge=0, le=100)
    startup_potential_score: float = Field(ge=0, le=100)
    enterprise_readiness_score: float = Field(ge=0, le=100)
    judge_wow_factor_score: float = Field(ge=0, le=100)
    demo_wow_factor_assessment: str
    final_verdict: UltimateFeatureVerdict
    source_systems: list[str]
    storage: str
