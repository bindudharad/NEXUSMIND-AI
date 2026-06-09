from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.hiring import HiringCandidateInput, HiringRoleInput


InterviewType = Literal["technical", "behavioral", "system_design", "coding", "ai_ml", "cloud", "database", "cybersecurity"]
InterviewDifficulty = Literal["junior", "mid", "senior", "staff", "principal"]
InterviewRiskLevel = Literal["low", "medium", "high", "critical"]
HiringDecision = Literal["strong_hire", "hire", "consider", "reject"]


class InterviewAnswerInput(BaseModel):
    question_id: str
    question: str
    answer: str = Field(default="", max_length=10000)
    interview_type: InterviewType = "technical"
    difficulty: InterviewDifficulty = "senior"
    response_time_seconds: float = Field(default=180, ge=0, le=7200)


class VoiceMetricsInput(BaseModel):
    words_per_minute: float = Field(default=132, ge=0, le=360)
    hesitation_count: int = Field(default=2, ge=0, le=300)
    pitch_variance: float = Field(default=0.28, ge=0, le=1)
    pause_ratio: float = Field(default=0.14, ge=0, le=1)
    volume_stability: float = Field(default=0.74, ge=0, le=1)


class CheatingEventInput(BaseModel):
    event_type: Literal["copy_paste", "tab_switch", "suspicious_speed", "external_assistance", "repeated_similarity", "identity_mismatch"]
    timestamp_offset_seconds: float = Field(default=0, ge=0, le=7200)
    severity_weight: float = Field(default=0.35, ge=0, le=1)
    details: str = Field(default="", max_length=500)


class SmartInterviewCandidateInput(HiringCandidateInput):
    answers: list[InterviewAnswerInput] = Field(default_factory=list, max_length=50)
    voice_metrics: VoiceMetricsInput | None = None
    audio_signal: list[float] = Field(default_factory=list, max_length=1000)
    monitoring_events: list[CheatingEventInput] = Field(default_factory=list, max_length=100)


class SmartInterviewRequest(BaseModel):
    role: HiringRoleInput
    candidates: list[SmartInterviewCandidateInput] = Field(default_factory=list, max_length=80)
    interview_types: list[InterviewType] = Field(default_factory=lambda: ["technical", "behavioral", "system_design"])
    realtime: bool = True


class SmartInterviewAssistantRequest(BaseModel):
    question: str = Field(min_length=2, max_length=700)
    session_id: str = "smart-interviewer-panel"
    candidate_id: str | None = None


class ResumeAnalysis(BaseModel):
    candidate_id: str
    candidate_name: str
    extracted_skills: list[str]
    education: list[str]
    certifications: list[str]
    experience_years: float
    projects: list[str]
    summary: str
    skill_gap_analysis: list[str]
    resume_quality_score: float = Field(ge=0, le=100)


class GeneratedInterviewQuestion(BaseModel):
    question_id: str
    interview_type: InterviewType
    difficulty: InterviewDifficulty
    question: str
    target_skills: list[str]
    follow_up_questions: list[str]
    evaluation_rubric: list[str]


class TechnicalEvaluation(BaseModel):
    candidate_id: str
    score: float = Field(ge=0, le=100)
    strengths: list[str]
    weaknesses: list[str]
    follow_up_questions: list[str]
    answer_evidence: list[str]


class BehavioralEvaluation(BaseModel):
    candidate_id: str
    leadership_score: float = Field(ge=0, le=100)
    communication_score: float = Field(ge=0, le=100)
    teamwork_score: float = Field(ge=0, le=100)
    problem_solving_score: float = Field(ge=0, le=100)
    adaptability_score: float = Field(ge=0, le=100)
    ownership_score: float = Field(ge=0, le=100)
    overall_score: float = Field(ge=0, le=100)
    evidence: list[str]


class VoiceConfidenceAnalysis(BaseModel):
    candidate_id: str
    confidence_score: float = Field(ge=0, le=100)
    communication_score: float = Field(ge=0, le=100)
    clarity_score: float = Field(ge=0, le=100)
    hesitation_frequency: float = Field(ge=0)
    speaking_speed_wpm: float = Field(ge=0, le=360)
    voice_stability: float = Field(ge=0, le=100)
    evidence: list[str]


class CheatingDetectionReport(BaseModel):
    candidate_id: str
    cheating_risk_score: float = Field(ge=0, le=100)
    risk_level: InterviewRiskLevel
    suspicious_events: list[str]
    copy_paste_events: int = Field(ge=0)
    tab_switch_events: int = Field(ge=0)
    external_assistance_signals: int = Field(ge=0)
    repeated_similarity_score: float = Field(ge=0, le=100)
    recommendation: str


class SkillProficiencyScore(BaseModel):
    skill: str
    score: float = Field(ge=0, le=100)
    evidence: str


class HiringRecommendation(BaseModel):
    decision: HiringDecision
    strengths: list[str]
    weaknesses: list[str]
    risks: list[str]
    development_areas: list[str]
    rationale: str
    confidence: float = Field(ge=0, le=1)


class InterviewReportArtifact(BaseModel):
    candidate_id: str
    title: str
    pdf_path: str
    docx_path: str
    sections: list[str]
    generated_at: datetime


class CandidateInterviewRanking(BaseModel):
    rank: int = Field(ge=1)
    candidate_id: str
    candidate_name: str
    overall_score: float = Field(ge=0, le=100)
    technical_score: float = Field(ge=0, le=100)
    behavioral_score: float = Field(ge=0, le=100)
    communication_score: float = Field(ge=0, le=100)
    voice_confidence_score: float = Field(ge=0, le=100)
    skill_match_score: float = Field(ge=0, le=100)
    experience_relevance_score: float = Field(ge=0, le=100)
    cheating_risk_score: float = Field(ge=0, le=100)
    recommendation: HiringRecommendation
    skill_scores: list[SkillProficiencyScore]
    resume_analysis: ResumeAnalysis
    technical_evaluation: TechnicalEvaluation
    behavioral_evaluation: BehavioralEvaluation
    voice_analysis: VoiceConfidenceAnalysis
    cheating_report: CheatingDetectionReport
    report: InterviewReportArtifact
    model_scores: dict[str, float]


class SmartInterviewerSummary(BaseModel):
    active_interviews: int = Field(ge=0)
    top_candidate: str
    average_overall_score: float = Field(ge=0, le=100)
    strong_hire_count: int = Field(ge=0)
    high_risk_candidates: int = Field(ge=0)
    report_count: int = Field(ge=0)
    stream_sequence: int = 1


class SmartInterviewerResponse(BaseModel):
    model: str
    generated_at: datetime
    role_title: str
    summary: SmartInterviewerSummary
    generated_questions: list[GeneratedInterviewQuestion]
    candidate_rankings: list[CandidateInterviewRanking]
    recommendations: list[HiringRecommendation]
    supported_questions: list[str]
    source_systems: list[str]
    storage: str


class SmartInterviewAssistantResponse(BaseModel):
    model: str
    generated_at: datetime
    question: str
    intent: str
    answer: str
    confidence: float = Field(ge=0, le=1)
    candidate_ids: list[str]
    cited_evidence: list[str]
    report_artifacts: list[InterviewReportArtifact]
    source_systems: list[str]
    storage: str
