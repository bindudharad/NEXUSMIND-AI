from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


TalentRiskLevel = Literal["low", "medium", "high", "critical"]
TalentAssistantIntent = Literal["projects", "mentors", "skills", "jobs", "experts", "learning", "badges", "summary", "search"]
TalentBadgeLevel = Literal["foundation", "advanced", "expert", "principal", "gold"]


class TalentMarketplaceProfile(BaseModel):
    employee_id: str
    employee_name: str
    role: str
    department: str
    location: str = "Remote"
    skills: list[str] = Field(default_factory=list, max_length=80)
    experience_years: float = Field(default=3, ge=0, le=60)
    certifications: list[str] = Field(default_factory=list, max_length=40)
    projects: list[str] = Field(default_factory=list, max_length=80)
    achievements: list[str] = Field(default_factory=list, max_length=80)
    interests: list[str] = Field(default_factory=list, max_length=60)
    career_goals: list[str] = Field(default_factory=list, max_length=40)
    learning_goals: list[str] = Field(default_factory=list, max_length=40)
    expertise_areas: list[str] = Field(default_factory=list, max_length=60)
    offered_expertise: list[str] = Field(default_factory=list, max_length=60)
    wants_mentorship: bool = True
    wants_projects: bool = True
    wants_internal_roles: bool = True
    capacity_hours: float = Field(default=40, ge=0, le=120)
    allocated_hours: float = Field(default=30, ge=0, le=160)
    performance_score: float = Field(default=78, ge=0, le=100)
    learning_velocity: float = Field(default=0.55, ge=0, le=1)
    mentorship_hours: float = Field(default=0, ge=0, le=500)
    knowledge_contributions: int = Field(default=0, ge=0, le=500)
    reputation_events: int = Field(default=0, ge=0, le=500)


class MarketplaceProjectOpportunity(BaseModel):
    project_id: str
    title: str
    department: str
    description: str = ""
    required_skills: list[str] = Field(default_factory=list, max_length=60)
    stretch_skills: list[str] = Field(default_factory=list, max_length=40)
    priority: int = Field(default=3, ge=1, le=5)
    duration_weeks: int = Field(default=8, ge=1, le=104)
    open_slots: int = Field(default=2, ge=1, le=100)
    reputation_boost: float = Field(default=8, ge=0, le=100)
    business_impact: float = Field(default=50, ge=0, le=100)


class InternalRoleOpportunity(BaseModel):
    role_id: str
    title: str
    department: str
    level: str = "Senior"
    required_skills: list[str] = Field(default_factory=list, max_length=60)
    preferred_skills: list[str] = Field(default_factory=list, max_length=60)
    career_track: str = "individual_contributor"
    growth_score: float = Field(default=70, ge=0, le=100)
    vacancy_urgency: float = Field(default=50, ge=0, le=100)


class MarketplaceLearningResource(BaseModel):
    resource_id: str
    title: str
    provider: str = "Internal Academy"
    target_skills: list[str] = Field(default_factory=list, max_length=30)
    duration_hours: int = Field(default=12, ge=1, le=400)
    difficulty: Literal["foundation", "intermediate", "advanced", "expert"] = "intermediate"
    certification: str = ""


class TalentMarketplaceRequest(BaseModel):
    profiles: list[TalentMarketplaceProfile] = Field(default_factory=list, max_length=500)
    projects: list[MarketplaceProjectOpportunity] = Field(default_factory=list, max_length=150)
    internal_roles: list[InternalRoleOpportunity] = Field(default_factory=list, max_length=150)
    learning_catalog: list[MarketplaceLearningResource] = Field(default_factory=list, max_length=300)
    focus_skills: list[str] = Field(default_factory=list, max_length=80)
    query: str = Field(default="", max_length=300)


class SkillIntelligencePoint(BaseModel):
    employee_id: str
    employee_name: str
    skill: str
    proficiency_score: float = Field(ge=0, le=100)
    evidence: list[str]
    hidden_skill: bool = False
    market_relevance: float = Field(ge=0, le=100)
    gap_to_goal: bool = False


class ProjectMatch(BaseModel):
    employee_id: str
    employee_name: str
    project_id: str
    project_title: str
    match_score: float = Field(ge=0, le=100)
    skill_coverage: float = Field(ge=0, le=100)
    capacity_fit: float = Field(ge=0, le=100)
    growth_fit: float = Field(ge=0, le=100)
    missing_skills: list[str]
    rationale: str


class MentorMatch(BaseModel):
    mentor_id: str
    mentor_name: str
    mentee_id: str
    mentee_name: str
    topic: str
    match_score: float = Field(ge=0, le=100)
    rationale: str


class InternalRoleMatch(BaseModel):
    employee_id: str
    employee_name: str
    role_id: str
    role_title: str
    match_score: float = Field(ge=0, le=100)
    promotion_readiness: float = Field(ge=0, le=100)
    missing_skills: list[str]
    rationale: str


class LearningPathRecommendation(BaseModel):
    employee_id: str
    employee_name: str
    target_skill: str
    resource_id: str
    title: str
    duration_hours: int
    recommendation_score: float = Field(ge=0, le=100)
    estimated_weeks_to_proficiency: float = Field(ge=0.5, le=104)
    rationale: str


class ExpertRanking(BaseModel):
    skill: str
    employee_id: str
    employee_name: str
    score: float = Field(ge=0, le=100)
    evidence: list[str]


class ReputationScore(BaseModel):
    employee_id: str
    employee_name: str
    contribution_score: float = Field(ge=0, le=100)
    knowledge_score: float = Field(ge=0, le=100)
    mentorship_score: float = Field(ge=0, le=100)
    innovation_score: float = Field(ge=0, le=100)
    total_reputation: float = Field(ge=0, le=100)


class SkillBadge(BaseModel):
    employee_id: str
    employee_name: str
    badge: str
    level: TalentBadgeLevel
    score: float = Field(ge=0, le=100)
    evidence: list[str]


class MarketplaceGraphNode(BaseModel):
    id: str
    label: str
    type: Literal["employee", "skill", "project", "role", "mentor", "learning", "badge"]
    score: float = Field(default=0, ge=0, le=100)


class MarketplaceGraphEdge(BaseModel):
    source: str
    target: str
    relationship: str
    weight: float = Field(default=0, ge=0, le=100)


class TalentRecommendation(BaseModel):
    title: str
    category: Literal["project", "mentor", "learning", "role", "reputation", "skill_gap", "expertise"]
    priority: TalentRiskLevel
    action: str
    expected_impact: str
    evidence: list[str]


class TalentMarketplaceSummary(BaseModel):
    profiles: int
    skills_detected: int
    hidden_skills_detected: int
    project_matches: int
    mentor_matches: int
    internal_role_matches: int
    learning_paths: int
    badges_awarded: int
    average_reputation: float = Field(ge=0, le=100)
    marketplace_health_score: float = Field(ge=0, le=100)
    top_expert: str
    top_project_match: str
    stream_sequence: int = 1


class TalentMarketplaceResponse(BaseModel):
    model: str
    generated_at: datetime
    profiles: list[TalentMarketplaceProfile]
    skill_intelligence: list[SkillIntelligencePoint]
    project_matches: list[ProjectMatch]
    mentor_matches: list[MentorMatch]
    internal_role_matches: list[InternalRoleMatch]
    learning_paths: list[LearningPathRecommendation]
    expert_rankings: list[ExpertRanking]
    reputation_scores: list[ReputationScore]
    badges: list[SkillBadge]
    graph_nodes: list[MarketplaceGraphNode]
    graph_edges: list[MarketplaceGraphEdge]
    recommendations: list[TalentRecommendation]
    assistant_prompts: list[str]
    summary: TalentMarketplaceSummary
    source_systems: list[str]
    storage: str


class TalentSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=300)
    limit: int = Field(default=8, ge=1, le=25)


class TalentSearchResult(BaseModel):
    entity_id: str
    entity_type: Literal["employee", "project", "role", "learning", "skill"]
    title: str
    score: float = Field(ge=0, le=100)
    matched_skills: list[str]
    summary: str


class TalentSearchResponse(BaseModel):
    model: str
    generated_at: datetime
    query: str
    results: list[TalentSearchResult]
    source_systems: list[str]


class TalentAssistantRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    employee_id: str | None = None


class TalentAssistantResponse(BaseModel):
    model: str
    generated_at: datetime
    question: str
    intent: TalentAssistantIntent
    answer: str
    confidence: float = Field(ge=0, le=1)
    cited_profiles: list[str]
    cited_opportunities: list[str]
    recommended_actions: list[str]
    evidence: list[str]
    source_systems: list[str]
    storage: str
