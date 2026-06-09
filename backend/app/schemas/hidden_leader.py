from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


TalentReadinessLevel = Literal["emerging", "ready_soon", "ready_now", "executive_bench"]
TalentRiskLevel = Literal["low", "medium", "high", "critical"]
TalentAssistantIntent = Literal[
    "future_leaders",
    "top_leader",
    "influence",
    "promotion",
    "innovation",
    "knowledge",
    "problem_solving",
    "summary",
]


class HiddenLeaderRequest(BaseModel):
    cycle_name: str = "Realtime Hidden Leader Detection Review"
    horizon_months: int = Field(default=24, ge=3, le=36)
    min_candidate_score: float = Field(default=0, ge=0, le=100)
    include_organizational_graph: bool = True
    include_talent_marketplace: bool = True
    include_innovation_engine: bool = True


class HiddenLeaderAssistantRequest(BaseModel):
    question: str = Field(default="Who are our future leaders?", min_length=2, max_length=700)
    session_id: str = "hidden-leader-detection"
    horizon_months: int = Field(default=24, ge=3, le=36)


class TalentDataQualityReport(BaseModel):
    communication_activity: str
    collaboration_patterns: str
    project_contributions: str
    knowledge_sharing: str
    mentoring_activity: str
    problem_solving_history: str
    learning_activity: str
    innovation_contributions: str
    peer_recognition: str
    performance_trends: str
    quality_score: float = Field(ge=0, le=100)
    validation_notes: list[str]


class LeadershipScorecard(BaseModel):
    employee_id: str
    employee_name: str
    current_role: str
    department: str
    team: str
    leadership_potential_score: float = Field(ge=0, le=100)
    readiness_level: TalentReadinessLevel
    growth_trend: Literal["declining", "stable", "increasing", "accelerating"]
    confidence: float = Field(ge=0, le=1)
    initiative_taking: float = Field(ge=0, le=100)
    decision_making: float = Field(ge=0, le=100)
    team_coordination: float = Field(ge=0, le=100)
    conflict_resolution: float = Field(ge=0, le=100)
    communication_quality: float = Field(ge=0, le=100)
    accountability: float = Field(ge=0, le=100)
    reliability: float = Field(ge=0, le=100)
    influence: float = Field(ge=0, le=100)
    evidence: list[str]


class InfluenceAnalysisInsight(BaseModel):
    employee_id: str
    employee_name: str
    influence_score: float = Field(ge=0, le=100)
    consulted_by_teams: list[str]
    informal_advisor: bool
    connector_score: float = Field(ge=0, le=100)
    communication_hub_score: float = Field(ge=0, le=100)
    graph_evidence: list[str]


class ProblemSolvingTalentInsight(BaseModel):
    employee_id: str
    employee_name: str
    problem_solving_score: float = Field(ge=0, le=100)
    impact_score: float = Field(ge=0, le=100)
    innovation_score: float = Field(ge=0, le=100)
    strength: str
    evidence: list[str]


class InnovationLeaderInsight(BaseModel):
    employee_id: str
    employee_name: str
    innovation_score: float = Field(ge=0, le=100)
    creativity_score: float = Field(ge=0, le=100)
    strategic_thinking_score: float = Field(ge=0, le=100)
    adopted_idea_signal: float = Field(ge=0, le=100)
    evidence: list[str]


class KnowledgeLeaderInsight(BaseModel):
    employee_id: str
    employee_name: str
    knowledge_leadership_score: float = Field(ge=0, le=100)
    expertise_areas: list[str]
    documentation_contributions: int = Field(ge=0)
    mentorship_signal: float = Field(ge=0, le=100)
    internal_support_signal: float = Field(ge=0, le=100)
    evidence: list[str]


class HiddenLeaderCandidate(BaseModel):
    employee_id: str
    employee_name: str
    current_role: str
    recommended_future_role: str
    leadership_readiness: TalentReadinessLevel
    hidden_leader_score: float = Field(ge=0, le=100)
    hidden_talent_score: float = Field(ge=0, le=100)
    influence_score: float = Field(ge=0, le=100)
    innovation_score: float = Field(ge=0, le=100)
    knowledge_leadership_score: float = Field(ge=0, le=100)
    promotion_recommendation: str
    why_hidden: str
    evidence: list[str]


class LeadershipForecastPoint(BaseModel):
    employee_id: str
    employee_name: str
    forecast_month: int = Field(ge=0, le=36)
    team_lead_potential: float = Field(ge=0, le=100)
    manager_potential: float = Field(ge=0, le=100)
    director_potential: float = Field(ge=0, le=100)
    executive_potential: float = Field(ge=0, le=100)
    readiness_score: float = Field(ge=0, le=100)


class TalentPromotionRecommendation(BaseModel):
    recommendation_id: str
    employee_id: str
    employee_name: str
    priority: TalentRiskLevel
    target_track: str
    action: str
    reason: str
    expected_business_impact: str
    confidence: float = Field(ge=0, le=1)


class TalentGraphIntegration(BaseModel):
    communication_graph_status: str
    collaboration_graph_status: str
    knowledge_graph_status: str
    organizational_brain_status: str
    influence_relationships_analyzed: int = Field(ge=0)
    knowledge_relationships_analyzed: int = Field(ge=0)
    graph_evidence: list[str]


class TalentDigitalTwinSync(BaseModel):
    twin: Literal["employee", "team", "department", "company", "executive_dashboard"]
    status: Literal["synced", "projected", "watch"]
    update: str
    entity_count: int = Field(ge=0)


class TalentAgentContribution(BaseModel):
    agent: str
    role: str
    finding: str
    recommendation: str
    confidence: float = Field(ge=0, le=1)
    source_systems: list[str]


class HiddenLeaderDashboardSummary(BaseModel):
    employees_analyzed: int = Field(ge=0)
    hidden_leaders_found: int = Field(ge=0)
    future_manager_candidates: int = Field(ge=0)
    future_executive_candidates: int = Field(ge=0)
    innovation_leaders: int = Field(ge=0)
    knowledge_leaders: int = Field(ge=0)
    average_leadership_potential: float = Field(ge=0, le=100)
    production_readiness_score: float = Field(ge=0, le=100)
    innovation_score: float = Field(ge=0, le=100)
    judge_wow_factor_score: float = Field(ge=0, le=100)
    stream_sequence: int = 1


class HiddenLeaderDetectionResponse(BaseModel):
    model: str
    generated_at: datetime
    cycle_name: str
    summary: HiddenLeaderDashboardSummary
    data_quality: TalentDataQualityReport
    leadership_scorecards: list[LeadershipScorecard]
    hidden_leader_candidates: list[HiddenLeaderCandidate]
    influence_analysis: list[InfluenceAnalysisInsight]
    problem_solving_intelligence: list[ProblemSolvingTalentInsight]
    innovation_leaders: list[InnovationLeaderInsight]
    knowledge_leaders: list[KnowledgeLeaderInsight]
    leadership_forecast: list[LeadershipForecastPoint]
    promotion_recommendations: list[TalentPromotionRecommendation]
    graph_integration: TalentGraphIntegration
    digital_twin_sync: list[TalentDigitalTwinSync]
    agent_council: list[TalentAgentContribution]
    supported_questions: list[str]
    executive_insights: list[str]
    source_systems: list[str]
    storage: str
    final_verdict: str


class HiddenLeaderAssistantResponse(BaseModel):
    model: str
    generated_at: datetime
    question: str
    intent: TalentAssistantIntent
    answer: str
    confidence: float = Field(ge=0, le=1)
    cited_employees: list[str]
    recommended_actions: list[str]
    evidence: list[str]
    source_systems: list[str]
    storage: str
