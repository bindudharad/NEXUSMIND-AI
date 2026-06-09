from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


InnovationPriority = Literal["low", "medium", "high", "critical"]
IdeaChannel = Literal["chat", "email", "meeting", "proposal", "ticket", "research"]
AdoptionStage = Literal["submitted", "reviewing", "piloting", "adopted", "rejected"]
TalentPotential = Literal["moderate", "high", "very_high", "exceptional"]
TalentRiskLevel = Literal["low", "medium", "high", "critical"]
InnovationAssistantIntent = Literal["leaders", "hidden_talent", "innovation", "promotion", "problem_solving", "risk", "growth", "summary"]


class InnovationIdeaSignal(BaseModel):
    idea_id: str
    employee_id: str
    employee_name: str
    department: str = "Engineering"
    team: str = "Platform"
    channel: IdeaChannel = "chat"
    text: str = Field(min_length=8, max_length=6000)
    timestamp: datetime | None = None
    adoption_stage: AdoptionStage = "submitted"
    reactions_count: int = Field(default=0, ge=0, le=5000)
    cross_team_votes: int = Field(default=0, ge=0, le=5000)
    collaboration_mentions: int = Field(default=0, ge=0, le=5000)
    implementation_progress: float = Field(default=0, ge=0, le=1)
    estimated_hours_saved: float = Field(default=0, ge=0, le=100000)
    estimated_cost_saving: float = Field(default=0, ge=0, le=100000000)
    estimated_revenue_impact: float = Field(default=0, ge=0, le=100000000)
    feasibility_signal: float = Field(default=0.55, ge=0, le=1)
    strategic_alignment: float = Field(default=0.55, ge=0, le=1)
    novelty_claim: float = Field(default=0.5, ge=0, le=1)


class EmployeeInnovationProfile(BaseModel):
    employee_id: str
    employee_name: str
    department: str = "Engineering"
    team: str = "Platform"
    role: str = "Engineer"
    performance_history: list[float] = Field(default_factory=list, max_length=18)
    learning_activity: float = Field(default=0.55, ge=0, le=1)
    project_contributions: int = Field(default=2, ge=0, le=100)
    peer_recognition: int = Field(default=2, ge=0, le=1000)
    knowledge_sharing: int = Field(default=1, ge=0, le=1000)
    mentorship_participation: int = Field(default=0, ge=0, le=1000)
    ownership_score: float = Field(default=0.55, ge=0, le=1)
    communication_effectiveness: float = Field(default=0.62, ge=0, le=1)
    decision_quality: float = Field(default=0.56, ge=0, le=1)
    incident_resolution_count: int = Field(default=0, ge=0, le=1000)
    root_cause_analyses: int = Field(default=0, ge=0, le=1000)
    strategic_thinking_score: float = Field(default=0.5, ge=0, le=1)
    engagement_score: float = Field(default=0.7, ge=0, le=1)
    burnout_risk: float = Field(default=0.24, ge=0, le=1)
    retention_risk: float = Field(default=0.22, ge=0, le=1)
    manager_visibility: float = Field(default=0.55, ge=0, le=1)
    promotion_readiness: float = Field(default=0.5, ge=0, le=1)


class InnovationRequest(BaseModel):
    cycle_name: str = "Realtime Innovation Scoring Review"
    horizon_days: int = Field(default=90, ge=7, le=365)
    ideas: list[InnovationIdeaSignal] = Field(default_factory=list, max_length=400)
    employee_profiles: list[EmployeeInnovationProfile] = Field(default_factory=list, max_length=1000)
    realtime: bool = False


class IdeaMiningInsight(BaseModel):
    idea_id: str
    employee_id: str
    employee_name: str
    department: str
    team: str
    channel: str
    idea_category: str
    extracted_theme: str
    originality_score: float = Field(ge=0, le=100)
    feasibility_score: float = Field(ge=0, le=100)
    impact_score: float = Field(ge=0, le=100)
    adoption_probability: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    evidence: list[str]
    extracted_keywords: list[str]
    recommendation: str


class EmployeeInnovationScore(BaseModel):
    employee_id: str
    employee_name: str
    department: str
    team: str
    innovation_score: float = Field(ge=0, le=100)
    originality_score: float = Field(ge=0, le=100)
    idea_impact_score: float = Field(ge=0, le=100)
    contribution_frequency: int = Field(ge=0)
    adoption_rate: float = Field(ge=0, le=100)
    collaboration_influence: float = Field(ge=0, le=100)
    creativity_rank: int = Field(ge=1)
    top_idea: str
    evidence: list[str]


class HiddenTalentInsight(BaseModel):
    employee_id: str
    employee_name: str
    department: str
    team: str
    hidden_talent_score: float = Field(ge=0, le=100)
    potential: TalentPotential
    under_recognized_gap: float = Field(ge=0, le=100)
    growth_trajectory_score: float = Field(ge=0, le=100)
    emerging_expertise_score: float = Field(ge=0, le=100)
    reason: str
    evidence: list[str]


class LeadershipPotentialInsight(BaseModel):
    employee_id: str
    employee_name: str
    department: str
    team: str
    leadership_potential: float = Field(ge=0, le=100)
    team_influence: float = Field(ge=0, le=100)
    decision_making_ability: float = Field(ge=0, le=100)
    communication_effectiveness: float = Field(ge=0, le=100)
    ownership_mindset: float = Field(ge=0, le=100)
    future_manager_probability: float = Field(ge=0, le=100)
    future_architect_probability: float = Field(ge=0, le=100)
    future_executive_probability: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    recommended_track: str
    reason: str


class ProblemSolvingInsight(BaseModel):
    employee_id: str
    employee_name: str
    department: str
    team: str
    problem_solving_score: float = Field(ge=0, le=100)
    complex_issue_resolution: float = Field(ge=0, le=100)
    incident_handling: float = Field(ge=0, le=100)
    root_cause_analysis: float = Field(ge=0, le=100)
    strategic_thinking: float = Field(ge=0, le=100)
    strength: str
    evidence: list[str]


class GrowthTrajectoryForecast(BaseModel):
    employee_id: str
    employee_name: str
    current_role: str
    expected_future_role: str
    growth_forecast: TalentPotential
    skill_growth_3_months: float = Field(ge=0, le=100)
    career_growth_6_months: float = Field(ge=0, le=100)
    leadership_growth_1_year: float = Field(ge=0, le=100)
    innovation_growth_3_years: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    drivers: list[str]


class TalentRiskInsight(BaseModel):
    employee_id: str
    employee_name: str
    department: str
    team: str
    critical_talent_risk: TalentRiskLevel
    flight_risk: float = Field(ge=0, le=100)
    retention_risk: float = Field(ge=0, le=100)
    burnout_risk: float = Field(ge=0, le=100)
    risk_reason: str
    retention_action: str


class PromotionRecommendation(BaseModel):
    employee_id: str
    employee_name: str
    target_program: str
    priority: InnovationPriority
    readiness_score: float = Field(ge=0, le=100)
    action: str
    reason: str
    expected_impact: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)


class TeamInnovationHeatmapPoint(BaseModel):
    department: str
    team: str
    innovation_score: float = Field(ge=0, le=100)
    creativity_density: float = Field(ge=0, le=100)
    adoption_velocity: float = Field(ge=0, le=100)
    cross_functional_influence: float = Field(ge=0, le=100)
    idea_count: int = Field(ge=0)
    priority: InnovationPriority


class IdeaImpactForecast(BaseModel):
    idea_id: str
    title: str
    department: str
    team: str
    predicted_business_impact: float = Field(ge=0, le=100)
    productivity_lift_percent: float = Field(ge=0, le=100)
    cost_saving_estimate: float = Field(ge=0)
    adoption_probability: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    drivers: list[str]
    forecast: list[float] = Field(default_factory=list)


class InnovationTrendPoint(BaseModel):
    label: str
    idea_volume: int = Field(ge=0)
    average_impact: float = Field(ge=0, le=100)
    average_originality: float = Field(ge=0, le=100)
    adoption_probability: float = Field(ge=0, le=100)


class InnovationRecommendation(BaseModel):
    title: str
    category: Literal["idea_sponsorship", "prototype", "collaboration", "research", "process", "recognition"]
    priority: InnovationPriority
    impact_score: float = Field(ge=0, le=100)
    action: str
    rationale: str
    confidence: float = Field(ge=0, le=1)


class InnovationAlert(BaseModel):
    title: str
    priority: InnovationPriority
    probability: float = Field(ge=0, le=100)
    impact: str
    recommendation: str


class InnovationSummary(BaseModel):
    ideas_analyzed: int
    employees_ranked: int
    high_impact_ideas: int
    adopted_or_piloting_ideas: int
    average_innovation_score: float = Field(ge=0, le=100)
    average_originality_score: float = Field(ge=0, le=100)
    forecasted_business_impact: float = Field(ge=0, le=100)
    hidden_talent_count: int = Field(default=0, ge=0)
    future_leaders_count: int = Field(default=0, ge=0)
    promotion_candidates: int = Field(default=0, ge=0)
    critical_talent_risks: int = Field(default=0, ge=0)
    average_leadership_potential: float = Field(default=0, ge=0, le=100)
    average_growth_velocity: float = Field(default=0, ge=0, le=100)
    stream_sequence: int = 1


class InnovationResponse(BaseModel):
    model: str
    generated_at: datetime
    cycle_name: str
    horizon_days: int
    idea_insights: list[IdeaMiningInsight]
    employee_scores: list[EmployeeInnovationScore]
    hidden_talent: list[HiddenTalentInsight]
    leadership_predictions: list[LeadershipPotentialInsight]
    problem_solving_insights: list[ProblemSolvingInsight]
    growth_forecasts: list[GrowthTrajectoryForecast]
    talent_risks: list[TalentRiskInsight]
    promotion_recommendations: list[PromotionRecommendation]
    team_heatmap: list[TeamInnovationHeatmapPoint]
    impact_forecasts: list[IdeaImpactForecast]
    trend_points: list[InnovationTrendPoint]
    recommendations: list[InnovationRecommendation]
    alerts: list[InnovationAlert]
    executive_insights: list[str]
    summary: InnovationSummary
    source_systems: list[str]
    digital_twin_updates: list[str] = Field(default_factory=list)
    marketplace_updates: list[str] = Field(default_factory=list)
    storage: str


class InnovationAssistantRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)


class InnovationAssistantResponse(BaseModel):
    model: str
    generated_at: datetime
    question: str
    intent: InnovationAssistantIntent
    answer: str
    confidence: float = Field(ge=0, le=1)
    cited_employees: list[str]
    recommended_actions: list[str]
    evidence: list[str]
    source_systems: list[str]
    storage: str
