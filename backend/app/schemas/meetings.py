from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class MeetingTranscriptTurn(BaseModel):
    speaker: str = Field(min_length=1, max_length=80)
    text: str = Field(min_length=1, max_length=3000)
    timestamp: str | None = None
    duration_seconds: float | None = Field(default=None, ge=0, le=7200)


class MeetingAnalyzeRequest(BaseModel):
    meeting_id: str = "meeting-live-001"
    title: str = "Project Alpha Recovery Sync"
    duration_minutes: float = Field(default=42, ge=1, le=480)
    transcript: str | None = Field(default=None, max_length=20000)
    turns: list[MeetingTranscriptTurn] = Field(default_factory=list, max_length=120)
    department: str = "Engineering"
    participant_count: int | None = Field(default=None, ge=1, le=500)
    average_hourly_cost: float = Field(default=95, ge=1, le=1000)
    weekly_recurrence: int = Field(default=3, ge=1, le=30)
    realtime: bool = False


class MeetingActionItem(BaseModel):
    owner: str
    task: str
    deadline: str | None = None
    confidence: float = Field(ge=0, le=1)
    evidence: str


class MeetingSpeakerAnalytics(BaseModel):
    speaker: str
    utterances: int = Field(ge=0)
    word_count: int = Field(ge=0)
    participation_percent: float = Field(ge=0, le=100)
    sentiment_score: float = Field(ge=-1, le=1)
    stress_score: float = Field(ge=0, le=1)
    toxicity_score: float = Field(ge=0, le=1)
    burnout_score: float = Field(ge=0, le=1)
    participation_flag: Literal["dominant", "silent", "balanced"]


class MeetingProductivityInsight(BaseModel):
    label: str
    score: float = Field(ge=0, le=100)
    details: str
    recommendation: str


class MeetingRiskSignal(BaseModel):
    category: str
    severity: Literal["low", "medium", "high", "critical"]
    score: float = Field(ge=0, le=100)
    evidence: list[str] = Field(default_factory=list)
    recommendation: str


class MeetingTopicCluster(BaseModel):
    topic_id: str
    label: str
    turn_indices: list[int]
    speakers: list[str]
    mentions: int = Field(ge=1)
    semantic_repetition_score: float = Field(ge=0, le=100)
    unresolved: bool
    representative_phrases: list[str]


class MeetingNecessityAssessment(BaseModel):
    verdict: Literal["synchronous_required", "async_preferred", "could_have_been_email"]
    confidence: float = Field(ge=0, le=1)
    rationale: str
    signals: list[str]
    async_recommendation: str


class MeetingWasteEconomics(BaseModel):
    currency: str = "USD"
    participant_count: int = Field(ge=1)
    average_hourly_cost: float = Field(ge=1)
    employee_hours_spent: float = Field(ge=0)
    wasted_hours: float = Field(ge=0)
    meeting_cost: float = Field(ge=0)
    wasted_cost: float = Field(ge=0)
    opportunity_cost: float = Field(ge=0)
    weekly_waste_hours_estimate: float = Field(ge=0)
    weekly_waste_cost_estimate: float = Field(ge=0)


class MeetingOverloadAnalytics(BaseModel):
    department: str
    meeting_load_score: float = Field(ge=0, le=100)
    overload_percent: float = Field(ge=0, le=100)
    burnout_correlation: float = Field(ge=0, le=1)
    productivity_drag_percent: float = Field(ge=0, le=100)
    recommended_reduction_minutes: float = Field(ge=0)
    forecast: str


class MeetingAnalysisSummary(BaseModel):
    sentiment_score: float = Field(ge=-1, le=1)
    stress_index: float = Field(ge=0, le=1)
    toxicity_index: float = Field(ge=0, le=1)
    burnout_index: float = Field(ge=0, le=1)
    participation_imbalance: float = Field(ge=0, le=100)
    productivity_score: float = Field(ge=0, le=100)
    efficiency_score: float = Field(ge=0, le=100)
    waste_percentage: float = Field(ge=0, le=100)
    actionability_score: float = Field(ge=0, le=100)
    repeated_topic_rate: float = Field(ge=0, le=100)
    estimated_waste_hours: float = Field(ge=0)
    estimated_waste_cost: float = Field(ge=0)
    action_item_count: int = Field(ge=0)
    blocker_count: int = Field(ge=0)
    stream_sequence: int = 1


class MeetingAnalysisResponse(BaseModel):
    model: str
    generated_at: datetime
    meeting_id: str
    title: str
    duration_minutes: float
    transcript_turns: int
    summary_text: str
    key_points: list[str]
    decisions: list[str]
    action_items: list[MeetingActionItem]
    blockers: list[str]
    speaker_analytics: list[MeetingSpeakerAnalytics]
    productivity_insights: list[MeetingProductivityInsight]
    topic_clusters: list[MeetingTopicCluster]
    necessity_assessment: MeetingNecessityAssessment
    waste_economics: MeetingWasteEconomics
    overload_analytics: MeetingOverloadAnalytics
    risk_signals: list[MeetingRiskSignal]
    recommendations: list[str]
    summary: MeetingAnalysisSummary
    storage: str
