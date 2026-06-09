from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


PlatformCapabilityStatus = Literal["ready", "configured", "warning", "missing", "error"]


class PlatformCapability(BaseModel):
    id: str
    name: str
    category: str
    status: PlatformCapabilityStatus
    score: float = Field(ge=0, le=100)
    details: str
    evidence: list[str]
    recommendation: str
    source_systems: list[str]


class PlatformMetric(BaseModel):
    label: str
    value: float
    unit: str
    delta: float
    severity: str


class PlatformSummary(BaseModel):
    total_capabilities: int
    ready: int
    configured: int
    warnings: int
    missing: int
    errors: int
    platform_score: float = Field(ge=0, le=100)
    executive_score: float = Field(ge=0, le=100)
    realtime_streams: int
    cloud_native_score: float = Field(ge=0, le=100)


class CompletePlatformResponse(BaseModel):
    model: str
    generated_at: datetime
    summary: PlatformSummary
    metrics: list[PlatformMetric]
    capabilities: list[PlatformCapability]
    dashboards: list[str]
    ai_stack: list[str]
    data_stack: list[str]
    devops_stack: list[str]
    executive_brief: str
    storage: str


class EcosystemAuditSection(BaseModel):
    title: str
    items: list[str]


class EcosystemCoreStatus(BaseModel):
    one_login: bool
    one_database_ecosystem: bool
    one_ai_core: bool
    one_dashboard_ecosystem: bool
    one_agent_orchestration_layer: bool
    orchestration_engines: list[str]
    connected_domains: list[str]
    evidence: list[str]


class EcosystemAuditResponse(BaseModel):
    model: str
    generated_at: datetime
    existing_features: list[str]
    missing_features: list[str]
    broken_features: list[str]
    placeholder_features: list[str]
    infrastructure_problems: list[str]
    ai_core: EcosystemCoreStatus
    sections: list[EcosystemAuditSection]
    summary: PlatformSummary
    verdict: str
