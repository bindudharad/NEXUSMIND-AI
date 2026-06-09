from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


HiringRiskLevel = Literal["low", "medium", "high", "critical"]


class HiringRoleInput(BaseModel):
    role_id: str = "role-platform-backend"
    title: str = "Senior Backend Platform Engineer"
    job_description: str
    required_skills: list[str] = Field(default_factory=list, max_length=40)
    preferred_skills: list[str] = Field(default_factory=list, max_length=40)
    seniority: Literal["junior", "mid", "senior", "staff", "principal"] = "senior"
    team_context: str = "Platform reliability, secure APIs, MLOps, Kubernetes operations, and incident response."
    culture_values: list[str] = Field(default_factory=list, max_length=20)
    domain_keywords: list[str] = Field(default_factory=list, max_length=30)


class HiringCandidateInput(BaseModel):
    candidate_id: str
    candidate_name: str
    resume_text: str = Field(min_length=30, max_length=16000)
    interview_transcript: str = Field(default="", max_length=12000)
    portfolio_summary: str = Field(default="", max_length=8000)
    years_experience: float = Field(ge=0, le=45, default=4)
    expected_salary: float = Field(ge=0, le=1_500_000, default=0)
    location: str = "Remote"
    current_title: str = "Candidate"
    certifications: list[str] = Field(default_factory=list, max_length=30)
    declared_skills: list[str] = Field(default_factory=list, max_length=80)


class HiringAnalyzeRequest(BaseModel):
    role: HiringRoleInput
    candidates: list[HiringCandidateInput] = Field(default_factory=list, max_length=100)
    realtime: bool = False


class SkillGap(BaseModel):
    skill: str
    severity: Literal["low", "medium", "high"]
    recommendation: str


class HiringFraudSignal(BaseModel):
    signal: str
    severity: HiringRiskLevel
    evidence: str


class InterviewInsight(BaseModel):
    label: str
    score: float = Field(ge=0, le=100)
    evidence: str


class CandidateRanking(BaseModel):
    rank: int = Field(ge=1)
    candidate_id: str
    candidate_name: str
    compatibility_score: float = Field(ge=0, le=100)
    hiring_recommendation: Literal["strong_hire", "hire", "hold", "reject"]
    confidence: float = Field(ge=0, le=1)
    resume_quality_score: float = Field(ge=0, le=100)
    semantic_match_score: float = Field(ge=0, le=100)
    skill_match_score: float = Field(ge=0, le=100)
    culture_fit_score: float = Field(ge=0, le=100)
    learning_potential_score: float = Field(ge=0, le=100)
    communication_quality_score: float = Field(ge=0, le=100)
    experience_quality_score: float = Field(ge=0, le=100)
    project_relevance_score: float = Field(ge=0, le=100)
    leadership_signal_score: float = Field(ge=0, le=100)
    hiring_risk_score: float = Field(ge=0, le=100)
    matched_skills: list[str]
    missing_skills: list[str]
    skill_gaps: list[SkillGap]
    fraud_signals: list[HiringFraudSignal]
    interview_insights: list[InterviewInsight]
    ranking_explanation: list[str]
    model_scores: dict[str, float]


class RecruiterRecommendation(BaseModel):
    recommendation_id: str
    title: str
    action: str
    rationale: str
    impact_score: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    candidate_ids: list[str]


class HiringTrend(BaseModel):
    label: str
    value: float = Field(ge=0, le=100)
    severity: HiringRiskLevel
    explanation: str


class HiringSummary(BaseModel):
    candidates_analyzed: int
    average_compatibility: float = Field(ge=0, le=100)
    top_candidate: str
    strong_hire_count: int
    skill_gap_count: int
    fraud_risk_count: int
    stream_sequence: int = 1


class HiringResponse(BaseModel):
    model: str
    generated_at: datetime
    role_title: str
    rankings: list[CandidateRanking]
    recommendations: list[RecruiterRecommendation]
    recruiter_trends: list[HiringTrend]
    skill_gap_heatmap: list[dict[str, float | str]]
    summary: HiringSummary
    storage: str
