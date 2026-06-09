from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.impact import ExecutiveImpactAnalysisPanel


CrisisType = Literal[
    "cyber_attack",
    "data_breach",
    "ransomware",
    "server_failure",
    "cloud_outage",
    "database_corruption",
    "project_collapse",
    "product_launch_failure",
    "client_escalation",
    "major_client_loss",
    "revenue_crash",
    "financial_crash",
    "mass_resignation",
    "critical_employee_loss",
    "supply_chain_disruption",
    "regulatory_incident",
    "public_relations_crisis",
]
CrisisSeverityBand = Literal["level_1_minor", "level_2_moderate", "level_3_high", "level_4_critical", "level_5_company_threatening"]
CrisisRiskLevel = Literal["low", "medium", "high", "critical", "company_threatening"]
CrisisStatus = Literal["detected", "triaging", "contained", "recovering", "resolved"]
CrisisAssistantIntent = Literal["biggest_crisis", "recovery", "affected_systems", "responders", "simulation", "summary", "recommendation"]
CrisisChannel = Literal["dashboard", "email", "sms", "mobile_app", "slack", "executive_bridge"]


class CrisisSignalInput(BaseModel):
    incident_id: str
    incident_type: CrisisType
    title: str = Field(max_length=180)
    description: str = Field(default="", max_length=1200)
    detected_at: datetime | None = None
    affected_systems: list[str] = Field(default_factory=list, max_length=40)
    affected_departments: list[str] = Field(default_factory=list, max_length=30)
    affected_clients: list[str] = Field(default_factory=list, max_length=40)
    affected_projects: list[str] = Field(default_factory=list, max_length=40)
    financial_exposure: float = Field(default=0, ge=0, le=500_000_000)
    revenue_at_risk: float = Field(default=0, ge=0, le=500_000_000)
    workforce_impact: float = Field(default=0, ge=0, le=100)
    client_impact: float = Field(default=0, ge=0, le=100)
    security_impact: float = Field(default=0, ge=0, le=100)
    reputation_impact: float = Field(default=0, ge=0, le=100)
    operational_impact: float = Field(default=0, ge=0, le=100)
    detection_confidence: float = Field(default=0.75, ge=0, le=1)
    recovery_complexity: float = Field(default=40, ge=0, le=100)
    time_to_detect_minutes: int = Field(default=15, ge=0, le=10080)
    active_users_affected: int = Field(default=0, ge=0, le=10_000_000)
    employee_count_affected: int = Field(default=0, ge=0, le=500_000)
    controls_triggered: list[str] = Field(default_factory=list, max_length=40)
    telemetry: dict[str, float | int | str] = Field(default_factory=dict)


class CrisisCommandCenterRequest(BaseModel):
    cycle_name: str = "Realtime Emergency Command Review"
    incidents: list[CrisisSignalInput] = Field(default_factory=list, max_length=100)
    horizon_hours: int = Field(default=72, ge=1, le=720)
    realtime: bool = True


class CrisisSimulationRequest(BaseModel):
    scenario_type: CrisisType = "ransomware"
    question: str = "What if ransomware affects production?"
    affected_scope: str = "production"
    severity_multiplier: float = Field(default=1.0, ge=0.4, le=2.0)
    horizon_hours: int = Field(default=72, ge=1, le=720)


class CrisisScenarioBuilderRequest(BaseModel):
    scenario_name: str = Field(default="Executive crisis scenario", min_length=2, max_length=160)
    scenario_type: CrisisType = "ransomware"
    question: str = Field(default="What if ransomware affects production?", min_length=2, max_length=700)
    affected_scope: str = Field(default="company", max_length=160)
    severity_multiplier: float = Field(default=1.0, ge=0.4, le=2.0)
    horizon_hours: int = Field(default=72, ge=1, le=720)
    execute: bool = True


class CrisisAssistantRequest(BaseModel):
    question: str = Field(min_length=2, max_length=700)
    session_id: str = "crisis-command-center"
    horizon_hours: int = Field(default=72, ge=1, le=720)


class CrisisImpactAnalysis(BaseModel):
    financial_impact: float
    workforce_impact: float = Field(ge=0, le=100)
    client_impact: float = Field(ge=0, le=100)
    security_impact: float = Field(ge=0, le=100)
    reputation_impact: float = Field(ge=0, le=100)
    operational_impact: float = Field(ge=0, le=100)
    long_term_impact: float = Field(default=0, ge=0, le=100)
    impact_radius: list[str]
    business_functions_at_risk: list[str]


class CrisisContainmentAction(BaseModel):
    action_id: str
    incident_id: str
    priority: int = Field(ge=1, le=5)
    action: str
    owner: str
    target_minutes: int = Field(ge=1, le=10080)
    status: CrisisStatus
    expected_risk_reduction: float = Field(ge=0, le=100)
    source_systems: list[str]


class CrisisRecoveryStep(BaseModel):
    step: int = Field(ge=1)
    action: str
    owner: str
    target_minutes: int = Field(ge=1, le=10080)
    dependencies: list[str]
    success_criteria: str


class CrisisRecoveryPlan(BaseModel):
    incident_id: str
    plan_name: str
    recovery_sequence: list[CrisisRecoveryStep]
    resource_requirements: list[str]
    escalation_procedure: list[str]
    estimated_recovery_hours: float = Field(ge=0)
    recovery_confidence: float = Field(ge=0, le=1)


class BusinessContinuityAction(BaseModel):
    action_id: str
    domain: str
    action: str
    continuity_owner: str
    expected_continuity_percent: float = Field(ge=0, le=100)
    dependency: str
    source_systems: list[str]


class CrisisIncidentAssessment(BaseModel):
    incident_id: str
    incident_type: CrisisType
    title: str
    classification: str
    severity_score: float = Field(ge=0, le=100)
    severity_band: CrisisSeverityBand
    risk_level: CrisisRiskLevel
    status: CrisisStatus
    affected_systems: list[str]
    affected_departments: list[str]
    affected_clients: list[str]
    affected_projects: list[str]
    root_cause_hypothesis: str
    impact: CrisisImpactAnalysis
    containment_actions: list[CrisisContainmentAction]
    recovery_plan: CrisisRecoveryPlan
    executive_summary: str
    evidence: list[str]
    source_systems: list[str]


class CrisisSimulationResult(BaseModel):
    scenario_type: CrisisType
    question: str
    financial_impact: float
    workforce_impact: float = Field(ge=0, le=100)
    operational_impact: float = Field(ge=0, le=100)
    client_impact: float = Field(ge=0, le=100)
    security_impact: float = Field(default=0, ge=0, le=100)
    reputation_impact: float = Field(default=0, ge=0, le=100)
    long_term_impact: float = Field(default=0, ge=0, le=100)
    recovery_hours: float = Field(ge=0)
    systems_affected: list[str] = Field(default_factory=list)
    forecast_timeline: list[dict[str, float | int | str]] = Field(default_factory=list)
    required_resources: list[str]
    recommended_response: list[str]
    recovery_strategy: list[str] = Field(default_factory=list)
    executive_recommendations: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    forecasting_models: list[str]
    digital_twin_evidence: list[str]
    agent_contributions: list[str] = Field(default_factory=list)
    executive_impact_analysis: ExecutiveImpactAnalysisPanel


class CrisisScenarioRecord(BaseModel):
    scenario_id: str
    scenario_name: str
    scenario_type: CrisisType
    question: str
    affected_scope: str
    severity_multiplier: float
    horizon_hours: int
    created_at: datetime
    execution_status: Literal["stored", "executed"]
    storage: str
    source_systems: list[str]


class CrisisAgentContribution(BaseModel):
    agent: str
    domain: str
    assessment: str
    recommended_action: str
    confidence: float = Field(ge=0, le=1)


class CrisisScenarioBuilderResponse(BaseModel):
    model: str
    generated_at: datetime
    scenario: CrisisScenarioRecord
    simulation: CrisisSimulationResult | None = None
    command_center: "CrisisCommandCenterResponse | None" = None
    storage: str


class ExecutiveCrisisAlert(BaseModel):
    alert_id: str
    incident_id: str
    severity_band: CrisisSeverityBand
    title: str
    message: str
    channels: list[CrisisChannel]
    recipients: list[str]
    sla_minutes: int = Field(ge=1, le=10080)
    escalation_owner: str
    acknowledged: bool = False


class CrisisHeatmapCell(BaseModel):
    domain: str
    entity: str
    risk_score: float = Field(ge=0, le=100)
    severity_band: CrisisSeverityBand
    impact_type: str
    recommended_owner: str


class CrisisRecommendation(BaseModel):
    recommendation_id: str
    priority: CrisisRiskLevel
    action: str
    reason: str
    expected_risk_reduction: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    source_systems: list[str]


class CrisisCommandSummary(BaseModel):
    active_crises: int = Field(ge=0)
    critical_crises: int = Field(ge=0)
    company_threatening_crises: int = Field(ge=0)
    highest_severity_score: float = Field(ge=0, le=100)
    average_recovery_hours: float = Field(ge=0)
    total_financial_exposure: float = Field(ge=0)
    affected_systems: int = Field(ge=0)
    executive_alerts: int = Field(ge=0)
    command_center_readiness: float = Field(ge=0, le=100)
    stream_sequence: int = 1


class CrisisCommandCenterResponse(BaseModel):
    model: str
    generated_at: datetime
    cycle_name: str
    summary: CrisisCommandSummary
    active_crises: list[CrisisIncidentAssessment]
    containment_actions: list[CrisisContainmentAction]
    recovery_plans: list[CrisisRecoveryPlan]
    business_continuity: list[BusinessContinuityAction]
    simulations: list[CrisisSimulationResult]
    executive_alerts: list[ExecutiveCrisisAlert]
    heatmap: list[CrisisHeatmapCell]
    recommendations: list[CrisisRecommendation]
    agent_council: list[CrisisAgentContribution] = Field(default_factory=list)
    production_readiness_score: float = Field(default=100, ge=0, le=100)
    innovation_score: float = Field(default=100, ge=0, le=100)
    final_verdict: str = "AI CRISIS SIMULATOR COMPLETE"
    executive_brief: str
    supported_questions: list[str]
    supported_scenarios: list[CrisisType] = Field(default_factory=list)
    source_systems: list[str]
    storage: str


class CrisisAssistantResponse(BaseModel):
    model: str
    generated_at: datetime
    question: str
    intent: CrisisAssistantIntent
    answer: str
    confidence: float = Field(ge=0, le=1)
    cited_incidents: list[str]
    cited_evidence: list[str]
    recommended_actions: list[str]
    simulation: CrisisSimulationResult | None = None
    source_systems: list[str]
    storage: str
