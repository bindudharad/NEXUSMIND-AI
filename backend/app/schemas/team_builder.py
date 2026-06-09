from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.team_compatibility import TeamEmployeeProfile, TeamInteractionSignal


TeamBuilderPriority = Literal["balanced", "delivery_speed", "low_conflict", "skill_coverage", "burnout_safe"]
RiskSeverity = Literal["low", "medium", "high", "critical"]


class TeamBuilderRequest(BaseModel):
    project_name: str = "AI Revenue Platform"
    project_type: str = "platform_ai"
    required_skills: list[str] = Field(default_factory=lambda: ["python", "api", "mlops", "security", "testing"], min_length=1, max_length=18)
    target_team_size: int = Field(default=5, ge=2, le=8)
    priority: TeamBuilderPriority = "balanced"
    deadline_pressure: float = Field(default=0.58, ge=0, le=1)
    employees: list[TeamEmployeeProfile] = Field(default_factory=list, max_length=28)
    interactions: list[TeamInteractionSignal] = Field(default_factory=list, max_length=180)
    realtime: bool = False


class TeamBuilderMember(BaseModel):
    employee_id: str
    name: str
    role: str
    department: str
    work_style: str
    skills: list[str]
    graph_cluster: str
    graph_compatibility_projection: float = Field(ge=0, le=100)
    graph_burnout_spread_risk: float = Field(ge=0, le=100)
    leadership_influence: float = Field(ge=0, le=100)


class SkillBalanceItem(BaseModel):
    skill: str
    coverage_score: float = Field(ge=0, le=100)
    owners: list[str]
    gap_risk: RiskSeverity
    recommendation: str


class ChemistryHeatmapCell(BaseModel):
    source: str
    target: str
    compatibility_score: float = Field(ge=0, le=100)
    communication_score: float = Field(ge=0, le=100)
    conflict_probability: float = Field(ge=0, le=100)
    burnout_spread_risk: float = Field(ge=0, le=100)
    graph_attention: float = Field(ge=0, le=1)


class LeadershipRecommendation(BaseModel):
    leader_name: str
    leadership_score: float = Field(ge=0, le=100)
    scope: str
    rationale: str
    watchouts: list[str] = Field(default_factory=list)


class TeamBuilderRiskAlert(BaseModel):
    severity: RiskSeverity
    probability: float = Field(ge=0, le=100)
    title: str
    members: list[str]
    intervention: str


class OptimizedTeam(BaseModel):
    team_id: str
    title: str
    members: list[TeamBuilderMember]
    leader: str
    compatibility_score: float = Field(ge=0, le=100)
    skill_coverage: float = Field(ge=0, le=100)
    chemistry_score: float = Field(ge=0, le=100)
    conflict_probability: float = Field(ge=0, le=100)
    burnout_balance: float = Field(ge=0, le=100)
    leadership_balance: float = Field(ge=0, le=100)
    projected_delivery_success: float = Field(ge=0, le=100)
    graph_confidence: float = Field(ge=0, le=1)
    missing_skills: list[str]
    role_mix: list[str]
    rationale: str
    recommendations: list[str]
    warnings: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class TeamBuilderSummary(BaseModel):
    employees_analyzed: int
    combinations_evaluated: int
    best_team_score: float = Field(ge=0, le=100)
    best_team_name: str
    average_conflict_probability: float = Field(ge=0, le=100)
    graph_nodes: int
    graph_edges: int
    stream_sequence: int = 1


class TeamBuilderResponse(BaseModel):
    model: str
    generated_at: datetime
    project_name: str
    project_type: str
    required_skills: list[str]
    optimized_teams: list[OptimizedTeam]
    skill_balance: list[SkillBalanceItem]
    chemistry_heatmap: list[ChemistryHeatmapCell]
    leadership_recommendations: list[LeadershipRecommendation]
    risk_alerts: list[TeamBuilderRiskAlert]
    collaboration_analytics: list[str]
    graph_model_metrics: dict[str, object]
    summary: TeamBuilderSummary
    storage: str
