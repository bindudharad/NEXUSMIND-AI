from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


VirtualEmployeeScenarioType = Literal[
    "baseline",
    "hiring_impact",
    "leadership_change",
    "organizational_change",
    "project_outcome",
    "stress_propagation",
]
VirtualEmployeeRiskLevel = Literal["low", "medium", "high", "critical"]
VirtualEmployeeExperienceLevel = Literal["junior", "mid", "senior", "lead", "principal"]


class VirtualEmployeeGenerationRequest(BaseModel):
    count: int = Field(default=18, ge=1, le=250)
    department: str = Field(default="Engineering", max_length=120)
    role_family: str = Field(default="Software Engineering", max_length=140)
    experience_mix: Literal["balanced", "junior_heavy", "senior_heavy", "leadership_heavy"] = "balanced"
    seed: int = Field(default=1024, ge=1, le=10_000_000)
    scenario_context: str = Field(default="baseline digital workforce", max_length=500)


class WorkforceSimulationRequest(BaseModel):
    question: str = Field(default="Simulate hiring 5 engineers.", min_length=4, max_length=800)
    scenario_type: VirtualEmployeeScenarioType = "hiring_impact"
    employee_count: int = Field(default=18, ge=4, le=250)
    hiring_count: int = Field(default=5, ge=0, le=100)
    manager_count: int = Field(default=1, ge=0, le=25)
    resignation_count: int = Field(default=0, ge=0, le=150)
    workload_delta_percent: float = Field(default=15, ge=-50, le=150)
    leadership_style: Literal["supportive", "directive", "hands_off", "transformational"] = "supportive"
    restructure_intensity: float = Field(default=20, ge=0, le=100)
    project_complexity: float = Field(default=62, ge=0, le=100)
    horizon_weeks: int = Field(default=12, ge=1, le=104)
    seed: int = Field(default=2048, ge=1, le=10_000_000)


class VirtualEmployeeAssistantRequest(BaseModel):
    question: str = Field(default="What happens if we hire 5 engineers?", min_length=4, max_length=800)
    session_id: str = Field(default="virtual-workforce-simulator", max_length=120)
    horizon_weeks: int = Field(default=12, ge=1, le=104)


class VirtualEmployeeIdentity(BaseModel):
    employee_id: str
    name: str
    department: str
    role: str
    experience_level: VirtualEmployeeExperienceLevel
    experience_years: int = Field(ge=0, le=45)


class VirtualEmployeeSkills(BaseModel):
    technical_skills: dict[str, float] = Field(description="Skill proficiency from 0-100.")
    soft_skills: dict[str, float] = Field(description="Soft skill proficiency from 0-100.")
    leadership_skills: dict[str, float] = Field(description="Leadership skill proficiency from 0-100.")


class BigFivePersonality(BaseModel):
    openness: float = Field(ge=0, le=100)
    conscientiousness: float = Field(ge=0, le=100)
    extraversion: float = Field(ge=0, le=100)
    agreeableness: float = Field(ge=0, le=100)
    neuroticism: float = Field(ge=0, le=100)


class VirtualEmployeePersonality(BaseModel):
    big_five: BigFivePersonality
    introversion_extroversion: str
    collaborative_level: float = Field(ge=0, le=100)
    risk_tolerance: float = Field(ge=0, le=100)
    learning_speed: float = Field(ge=0, le=100)
    communication_style: str
    team_collaboration_preference: str
    leadership_tendency: float = Field(ge=0, le=100)


class VirtualEmployeeWorkCharacteristics(BaseModel):
    productivity_pattern: str
    focus_pattern: str
    burnout_sensitivity: float = Field(ge=0, le=100)
    adaptability: float = Field(ge=0, le=100)
    preferred_workload: float = Field(ge=0, le=100)
    context_switching_tolerance: float = Field(ge=0, le=100)


class VirtualEmployeeBehaviorState(BaseModel):
    work_completion: float = Field(ge=0, le=100)
    collaboration: float = Field(ge=0, le=100)
    learning_progress: float = Field(ge=0, le=100)
    escalation_likelihood: float = Field(ge=0, le=100)
    conflict_likelihood: float = Field(ge=0, le=100)
    innovation_likelihood: float = Field(ge=0, le=100)
    stress_level: float = Field(ge=0, le=100)
    burnout_risk: float = Field(ge=0, le=100)
    productivity_score: float = Field(ge=0, le=100)
    output_quality: float = Field(ge=0, le=100)


class VirtualEmployeeAgent(BaseModel):
    identity: VirtualEmployeeIdentity
    skills: VirtualEmployeeSkills
    personality: VirtualEmployeePersonality
    work_characteristics: VirtualEmployeeWorkCharacteristics
    behavior: VirtualEmployeeBehaviorState
    source_digital_twin: str


class StressPropagationEdge(BaseModel):
    source_employee_id: str
    target_employee_id: str
    relationship: Literal["manager_to_team", "peer_pressure", "dependency_owner", "mentor_support"]
    stress_transfer: float = Field(ge=-100, le=100)
    reason: str


class TeamInteractionResult(BaseModel):
    team_name: str
    collaboration_score: float = Field(ge=0, le=100)
    knowledge_sharing_score: float = Field(ge=0, le=100)
    communication_score: float = Field(ge=0, le=100)
    cohesion_score: float = Field(ge=0, le=100)
    conflict_risk: float = Field(ge=0, le=100)
    leadership_stability: float = Field(ge=0, le=100)
    explanation: str


class WorkforceImpactMetric(BaseModel):
    metric: str
    baseline: float
    projected: float
    delta: float
    unit: str
    risk_level: VirtualEmployeeRiskLevel


class WorkforceForecastPoint(BaseModel):
    week: int = Field(ge=0, le=104)
    productivity: float = Field(ge=0, le=100)
    stress: float = Field(ge=0, le=100)
    burnout_risk: float = Field(ge=0, le=100)
    collaboration: float = Field(ge=0, le=100)
    attrition_risk: float = Field(ge=0, le=100)
    delivery_confidence: float = Field(ge=0, le=100)


class ProjectOutcomeSimulation(BaseModel):
    project_name: str
    delivery_delay_weeks: float = Field(ge=0)
    delivery_confidence: float = Field(ge=0, le=100)
    quality_score: float = Field(ge=0, le=100)
    resource_risk: float = Field(ge=0, le=100)
    expected_completion_weeks: float = Field(ge=0)
    explanation: str


class WorkforceRecommendation(BaseModel):
    action: str
    priority: VirtualEmployeeRiskLevel
    expected_impact: str
    owner_agent: str
    confidence: float = Field(ge=0, le=1)


class VirtualWorkforceSummary(BaseModel):
    generated_employees: int = Field(ge=0)
    simulated_weeks: int = Field(ge=0)
    average_productivity: float = Field(ge=0, le=100)
    average_stress: float = Field(ge=0, le=100)
    burnout_risk: float = Field(ge=0, le=100)
    team_conflict_risk: float = Field(ge=0, le=100)
    delivery_confidence: float = Field(ge=0, le=100)
    readiness_score: float = Field(ge=0, le=100)
    stream_sequence: int = 1


class VirtualWorkforceAssistantResponse(BaseModel):
    model: str
    generated_at: datetime
    question: str
    intent: VirtualEmployeeScenarioType
    answer: str
    simulation: "VirtualWorkforceResponse"
    cited_evidence: list[str]
    recommended_actions: list[str]
    source_systems: list[str]
    storage: str


class VirtualWorkforceResponse(BaseModel):
    model: str
    generated_at: datetime
    scenario: WorkforceSimulationRequest
    summary: VirtualWorkforceSummary
    virtual_employees: list[VirtualEmployeeAgent]
    team_interactions: list[TeamInteractionResult]
    stress_propagation: list[StressPropagationEdge]
    impact_metrics: list[WorkforceImpactMetric]
    forecast: list[WorkforceForecastPoint]
    project_outcome: ProjectOutcomeSimulation
    recommendations: list[WorkforceRecommendation]
    assistant_summary: str
    integration_evidence: list[str]
    supported_questions: list[str]
    source_systems: list[str]
    forecast_models: list[str]
    storage: str


VirtualWorkforceAssistantResponse.model_rebuild()
