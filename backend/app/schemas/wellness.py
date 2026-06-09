from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.employee_dashboard import EmployeeActivityPoint
from app.schemas.voice import VoiceStressAnalyzeRequest


WellnessSeverity = Literal["low", "medium", "high", "critical"]


class WellnessMessage(BaseModel):
    text: str = Field(min_length=2, max_length=4000)
    channel: str = "chat"
    timestamp: datetime | None = None


class TypingTelemetryPoint(BaseModel):
    timestamp: datetime | None = None
    typing_speed_cpm: float = Field(default=275, ge=0, le=1200)
    backspace_rate: float = Field(default=0.08, ge=0, le=1)
    error_rate: float = Field(default=0.05, ge=0, le=1)
    pause_ratio: float = Field(default=0.22, ge=0, le=1)
    burstiness: float = Field(default=0.34, ge=0, le=1)
    after_hours: bool = False


class WellnessTeamMember(BaseModel):
    employee_id: str
    name: str
    department: str
    stress_score: float = Field(ge=0, le=100)
    burnout_probability: float = Field(ge=0, le=100)
    sentiment_score: float = Field(ge=-1, le=1)
    meeting_hours: float = Field(ge=0, le=40)
    overtime_hours: float = Field(ge=0, le=80)


class WellnessAnalyzeRequest(BaseModel):
    employee_id: str = "emp-wellness-001"
    employee_name: str = "Aarav Mehta"
    department: str = "Engineering"
    role: str = "Senior Backend Engineer"
    messages: list[WellnessMessage] = Field(default_factory=list, max_length=40)
    voice: VoiceStressAnalyzeRequest | None = None
    work_pattern: EmployeeActivityPoint | None = None
    work_history: list[EmployeeActivityPoint] = Field(default_factory=list, max_length=60)
    typing_samples: list[TypingTelemetryPoint] = Field(default_factory=list, max_length=120)
    team_members: list[WellnessTeamMember] = Field(default_factory=list, max_length=80)
    realtime: bool = False


class TypingBehaviorAnalytics(BaseModel):
    stress_score: float = Field(ge=0, le=100)
    instability_score: float = Field(ge=0, le=100)
    cognitive_load_score: float = Field(ge=0, le=100)
    fatigue_score: float = Field(ge=0, le=100)
    aggressive_typing_score: float = Field(ge=0, le=100)
    evidence: list[str]


class WorkPatternWellnessAnalytics(BaseModel):
    overtime_pressure: float = Field(ge=0, le=100)
    meeting_overload: float = Field(ge=0, le=100)
    productivity_decline: float = Field(ge=0, le=100)
    focus_deficit: float = Field(ge=0, le=100)
    collaboration_risk: float = Field(ge=0, le=100)
    forecast: str


class WellnessHeatmapCell(BaseModel):
    department: str
    stress_score: float = Field(ge=0, le=100)
    burnout_probability: float = Field(ge=0, le=100)
    emotional_exhaustion: float = Field(ge=0, le=100)
    morale_score: float = Field(ge=0, le=100)
    headcount: int = Field(ge=1)
    recommendation: str


class WellnessRecommendation(BaseModel):
    category: str
    priority: WellnessSeverity
    action: str
    expected_impact: str
    confidence: float = Field(ge=0, le=1)


class WellnessRiskAlert(BaseModel):
    category: str
    severity: WellnessSeverity
    score: float = Field(ge=0, le=100)
    message: str
    evidence: list[str]
    recommendation: str


class WellnessSummary(BaseModel):
    wellness_score: float = Field(ge=0, le=100)
    stress_score: float = Field(ge=0, le=100)
    burnout_probability: float = Field(ge=0, le=100)
    emotional_exhaustion_probability: float = Field(ge=0, le=100)
    frustration_score: float = Field(ge=0, le=100)
    anxiety_score: float = Field(ge=0, le=100)
    motivation_decline: float = Field(ge=0, le=100)
    communication_fatigue: float = Field(ge=0, le=100)
    mental_overload: float = Field(ge=0, le=100)
    high_risk_team_count: int = Field(ge=0)
    stream_sequence: int = 1


class WellnessAnalysisResponse(BaseModel):
    model: str
    generated_at: datetime
    employee_id: str
    employee_name: str
    department: str
    role: str
    nlp_model: str
    voice_model: str
    behavioral_model: str
    summary: WellnessSummary
    sentiment_summary: dict[str, float | int | str]
    typing_analytics: TypingBehaviorAnalytics
    work_pattern_analytics: WorkPatternWellnessAnalytics
    emotional_heatmap: list[WellnessHeatmapCell]
    recommendations: list[WellnessRecommendation]
    risk_alerts: list[WellnessRiskAlert]
    executive_insights: list[str]
    storage: str
