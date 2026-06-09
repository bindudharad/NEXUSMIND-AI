from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


UltimateStatus = Literal["ready", "partial", "missing", "failed"]
UltimateVerdict = Literal[
    "COMPLETE AUTONOMOUS ENTERPRISE INTELLIGENCE & SIMULATION PLATFORM",
    "ULTIMATE PLATFORM GAPS REMAIN",
]


class PlatformAuditMap(BaseModel):
    backend_files: int = Field(ge=0)
    frontend_files: int = Field(ge=0)
    api_route_modules: int = Field(ge=0)
    service_modules: int = Field(ge=0)
    schema_modules: int = Field(ge=0)
    ai_modules: int = Field(ge=0)
    dashboard_components: int = Field(ge=0)
    persisted_data_stores: int = Field(ge=0)
    dependency_files: list[str]
    api_map: list[str]
    database_map: list[str]
    frontend_component_map: list[str]
    ai_module_map: list[str]


class UltimateFeatureAudit(BaseModel):
    feature_id: int = Field(ge=1, le=15)
    name: str
    status: UltimateStatus
    present: bool
    working: bool
    connected: bool
    tested: bool
    production_ready: bool
    score: float = Field(ge=0, le=100)
    evidence: list[str]
    integrations: list[str]
    endpoints: list[str]
    dashboards: list[str]


class IntegrationAuditLink(BaseModel):
    source: str
    target: str
    status: UltimateStatus
    evidence: list[str]


class VirtualEmployeeProfile(BaseModel):
    employee_id: str
    name: str
    role: str
    department: str
    behavior_model: str
    work_pattern: str
    productivity_profile: float = Field(ge=0, le=100)
    collaboration_profile: float = Field(ge=0, le=100)
    stress_propagation_risk: float = Field(ge=0, le=100)
    leadership_effect: float = Field(ge=0, le=100)


class TimeMachineScenario(BaseModel):
    question: str
    horizon_months: int = Field(ge=1, le=36)
    burnout_forecast: float = Field(ge=0, le=100)
    revenue_impact_percent: float
    productivity_impact_percent: float
    attrition_risk: float = Field(ge=0, le=100)
    project_delay_probability: float = Field(ge=0, le=100)
    team_health_score: float = Field(ge=0, le=100)
    recommendation: str


class GlobalRiskSignal(BaseModel):
    risk: str
    category: str
    severity: Literal["low", "medium", "high", "critical"]
    score: float = Field(ge=0, le=100)
    strategic_insight: str
    recommended_action: str
    source_systems: list[str]


class ProductionReadinessReport(BaseModel):
    score: float = Field(ge=0, le=100)
    authentication: UltimateStatus
    authorization: UltimateStatus
    logging: UltimateStatus
    monitoring: UltimateStatus
    error_handling: UltimateStatus
    ci_cd: UltimateStatus
    evidence: list[str]


class UltimatePlatformScorecard(BaseModel):
    judge_wow_factor_score: float = Field(ge=0, le=100)
    innovation_score: float = Field(ge=0, le=100)
    enterprise_score: float = Field(ge=0, le=100)
    integration_score: float = Field(ge=0, le=100)
    security_score: float = Field(ge=0, le=100)
    performance_score: float = Field(ge=0, le=100)
    production_readiness_score: float = Field(ge=0, le=100)
    minimum_score: float = Field(ge=0, le=100)


class UltimatePlatformResponse(BaseModel):
    model: str
    generated_at: datetime
    audit_map: PlatformAuditMap
    feature_coverage_report: list[UltimateFeatureAudit]
    integration_report: list[IntegrationAuditLink]
    error_report: list[str]
    security_report: list[str]
    performance_report: list[str]
    production_readiness_report: ProductionReadinessReport
    virtual_employees: list[VirtualEmployeeProfile]
    time_machine_scenarios: list[TimeMachineScenario]
    global_risk_signals: list[GlobalRiskSignal]
    scorecard: UltimatePlatformScorecard
    missing_components: list[str]
    fixed_components: list[str]
    regenerated_components: list[str]
    final_verdict: UltimateVerdict
    source_systems: list[str]
    storage: str
    stream_sequence: int = 1
