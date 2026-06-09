from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


WorkStyle = Literal["focused", "collaborative", "decisive", "supportive", "analytical", "creative"]
ConflictSeverity = Literal["low", "medium", "high", "critical"]


class TeamEmployeeProfile(BaseModel):
    employee_id: str
    name: str
    role: str
    department: str
    skills: list[str] = Field(default_factory=list, min_length=1, max_length=12)
    work_style: WorkStyle = "collaborative"
    productivity_history: list[float] = Field(default_factory=list, max_length=30)
    stress_history: list[float] = Field(default_factory=list, max_length=30)
    sentiment_trend: float = Field(ge=-1, le=1, default=0)
    task_completion_rate: float = Field(ge=0, le=1, default=0.78)
    meeting_participation: float = Field(ge=0, le=1, default=0.5)
    collaboration_frequency: float = Field(ge=0, le=1, default=0.5)
    leadership_score: float = Field(ge=0, le=1, default=0.5)
    burnout_risk: float = Field(ge=0, le=1, default=0.35)
    current_workload: float = Field(ge=0, le=1, default=0.58)
    focus_ratio: float = Field(ge=0, le=1, default=0.55)
    timezone_overlap: float = Field(ge=0, le=1, default=0.92)


class TeamInteractionSignal(BaseModel):
    source_id: str
    target_id: str
    collaboration_frequency: float = Field(ge=0, le=1, default=0.5)
    past_success_rate: float = Field(ge=0, le=1, default=0.6)
    sentiment_alignment: float = Field(ge=0, le=1, default=0.6)
    conflict_incidents: int = Field(ge=0, le=20, default=0)
    meetings_together: int = Field(ge=0, le=200, default=8)


class TeamCompatibilityRequest(BaseModel):
    project_name: str = "Project Alpha Recovery"
    required_skills: list[str] = Field(default_factory=lambda: ["python", "api", "mlops", "security"], min_length=1, max_length=16)
    target_team_size: int = Field(default=4, ge=2, le=8)
    employees: list[TeamEmployeeProfile] = Field(default_factory=list, max_length=24)
    interactions: list[TeamInteractionSignal] = Field(default_factory=list, max_length=160)
    realtime: bool = False


class TeamCompatibilityPair(BaseModel):
    source_id: str
    source_name: str
    target_id: str
    target_name: str
    compatibility_score: float = Field(ge=0, le=100)
    collaboration_success_probability: float = Field(ge=0, le=100)
    conflict_probability: float = Field(ge=0, le=100)
    productivity_synergy: float = Field(ge=0, le=100)
    communication_compatibility: float = Field(ge=0, le=100)
    leadership_compatibility: float = Field(ge=0, le=100)
    burnout_propagation_risk: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    chemistry_label: str
    evidence: list[str] = Field(default_factory=list)
    recommendation: str


class TeamGraphNode(BaseModel):
    employee_id: str
    name: str
    role: str
    department: str
    cluster: str
    influence_score: float = Field(ge=0, le=100)
    stress_index: float = Field(ge=0, le=100)
    skill_count: int = Field(ge=0)


class TeamGraphEdge(BaseModel):
    source_id: str
    target_id: str
    compatibility_score: float = Field(ge=0, le=100)
    conflict_probability: float = Field(ge=0, le=100)


class TeamRecommendation(BaseModel):
    team_id: str
    title: str
    members: list[str]
    leader: str
    compatibility_score: float = Field(ge=0, le=100)
    chemistry_score: float = Field(ge=0, le=100)
    skill_coverage: float = Field(ge=0, le=100)
    conflict_risk: float = Field(ge=0, le=100)
    burnout_balance: float = Field(ge=0, le=100)
    projected_velocity: float = Field(ge=0, le=100)
    rationale: str
    warnings: list[str] = Field(default_factory=list)


class LeadershipMatch(BaseModel):
    leader_id: str
    leader_name: str
    team_scope: str
    compatibility_score: float = Field(ge=0, le=100)
    rationale: str
    watchouts: list[str] = Field(default_factory=list)


class TeamConflictWarning(BaseModel):
    severity: ConflictSeverity
    probability: float = Field(ge=0, le=100)
    employees: list[str]
    message: str
    intervention: str


class TeamCompatibilitySummary(BaseModel):
    employees_analyzed: int
    pairs_analyzed: int
    average_compatibility: float = Field(ge=0, le=100)
    average_conflict_probability: float = Field(ge=0, le=100)
    highest_compatibility_pair: str
    highest_risk_pair: str
    recommended_team_score: float = Field(ge=0, le=100)
    stream_sequence: int = 1


class TeamCompatibilityResponse(BaseModel):
    model: str
    generated_at: datetime
    project_name: str
    required_skills: list[str]
    pair_scores: list[TeamCompatibilityPair]
    graph_nodes: list[TeamGraphNode]
    graph_edges: list[TeamGraphEdge]
    team_recommendations: list[TeamRecommendation]
    conflict_warnings: list[TeamConflictWarning]
    leadership_matches: list[LeadershipMatch]
    chemistry_insights: list[str]
    optimization_suggestions: list[str]
    summary: TeamCompatibilitySummary
    storage: str
