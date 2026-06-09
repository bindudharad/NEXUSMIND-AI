from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


VoiceSourceFormat = Literal["pcm", "wav", "webm", "mp3", "ogg", "browser_pcm"]
VoiceAlertSeverity = Literal["low", "medium", "high", "critical"]
VoiceCommandIntent = Literal[
    "highest_risk_department",
    "productivity_forecast",
    "crisis_dashboard",
    "security_posture",
    "digital_twin_simulation",
    "department_failure_forecast",
    "company_threat",
    "client_risk",
    "company_health",
    "revenue_forecast",
    "project_risk",
    "boardroom_priority",
    "competitive_threat",
    "innovation_opportunity",
    "memory_query",
    "recommendation",
    "follow_up_explanation",
]
VoiceCommandPriority = Literal["low", "medium", "high", "critical"]
VoiceAssistantStatus = Literal["ready", "degraded", "missing"]
VoiceAssistantVerdict = Literal["AI CEO ASSISTANT COMPLETE", "AI CEO ASSISTANT GAPS REMAIN"]


class VoiceStressAnalyzeRequest(BaseModel):
    employee_id: str = "voice-employee-001"
    speaker: str = "Employee X"
    department: str = "Engineering"
    transcript: str | None = Field(default=None, max_length=5000)
    source_format: VoiceSourceFormat = "browser_pcm"
    sample_rate: int = Field(default=16000, ge=8000, le=48000)
    duration_seconds: float | None = Field(default=None, ge=0.1, le=600)
    audio_samples: list[float] = Field(default_factory=list, max_length=200000)
    audio_base64: str | None = Field(default=None, max_length=5_000_000)


class VoiceAcousticFeatures(BaseModel):
    rms_energy: float = Field(ge=0)
    peak_amplitude: float = Field(ge=0)
    zero_crossing_rate: float = Field(ge=0)
    pause_ratio: float = Field(ge=0, le=1)
    pitch_mean_hz: float = Field(ge=0)
    pitch_variation: float = Field(ge=0)
    intensity_variability: float = Field(ge=0)
    jitter_proxy: float = Field(ge=0)
    tremor_proxy: float = Field(ge=0)
    speech_rate_wpm: float = Field(ge=0)
    vocal_tension: float = Field(ge=0)


class VoiceEmotionScores(BaseModel):
    stress: float = Field(ge=0, le=1)
    frustration: float = Field(ge=0, le=1)
    anger: float = Field(ge=0, le=1)
    anxiety: float = Field(ge=0, le=1)
    fatigue: float = Field(ge=0, le=1)
    calmness: float = Field(ge=0, le=1)
    motivation: float = Field(ge=0, le=1)


class VoiceAlert(BaseModel):
    category: str
    severity: VoiceAlertSeverity
    score: float = Field(ge=0, le=100)
    message: str
    evidence: list[str] = Field(default_factory=list)
    recommendation: str


class VoiceTimelinePoint(BaseModel):
    second: float = Field(ge=0)
    stress: float = Field(ge=0, le=100)
    intensity: float = Field(ge=0)
    pitch_hz: float = Field(ge=0)


class VoiceStressSummary(BaseModel):
    average_stress: float = Field(ge=0, le=100)
    peak_stress: float = Field(ge=0, le=100)
    alert_count: int = Field(ge=0)
    stream_sequence: int = 1


class VoiceStressResponse(BaseModel):
    model: str
    generated_at: datetime
    employee_id: str
    speaker: str
    department: str
    source_format: VoiceSourceFormat
    duration_seconds: float
    transcript: str | None = None
    primary_emotion: str
    confidence: float = Field(ge=0, le=1)
    stress_score: float = Field(ge=0, le=100)
    burnout_risk: float = Field(ge=0, le=100)
    conflict_intensity: float = Field(ge=0, le=100)
    communication_pressure: float = Field(ge=0, le=100)
    acoustic_features: VoiceAcousticFeatures
    emotion_scores: VoiceEmotionScores
    fusion_evidence: list[str] = Field(default_factory=list)
    alerts: list[VoiceAlert]
    recommendations: list[str]
    timeline: list[VoiceTimelinePoint]
    summary: VoiceStressSummary
    storage: str


class VoiceCommandRequest(BaseModel):
    transcript: str = Field(default="Show highest-risk department.", min_length=3, max_length=500)
    speaker: str = "Executive Operator"
    department: str = "Executive"
    include_spoken_response: bool = True
    session_id: str = Field(default="executive-voice-session", min_length=3, max_length=120)
    context_turns: list[str] = Field(default_factory=list, max_length=12)


class VoiceCommandAction(BaseModel):
    label: str
    action_type: str
    target: str
    priority: VoiceCommandPriority


class VoiceDashboardControl(BaseModel):
    route: str
    panel_id: str
    action: str
    target_label: str


class VoiceTTSMetadata(BaseModel):
    engine: str
    voice: str
    rate: float = Field(ge=0.5, le=2)
    pitch: float = Field(ge=0, le=2)
    latency_budget_ms: int = Field(ge=100, le=10000)
    playback_supported: bool


class VoiceCapabilityStatus(BaseModel):
    capability: str
    status: Literal["ready", "degraded", "missing"]
    evidence: list[str] = Field(default_factory=list)


class VoiceVisualKPI(BaseModel):
    label: str
    value: str
    trend: str
    severity: VoiceCommandPriority


class VoiceVisualChart(BaseModel):
    chart_type: Literal["risk_bar", "forecast_line", "heatmap", "kpi_strip", "timeline"]
    title: str
    data: list[dict[str, str | float]]


class VoiceVisualResponse(BaseModel):
    display_mode: Literal["executive_command_card", "forecast_console", "risk_map", "simulation_brief"]
    dashboard_panels: list[str]
    kpis: list[VoiceVisualKPI]
    charts: list[VoiceVisualChart]
    recommended_actions: list[str]


class VoiceAICouncilTurn(BaseModel):
    agent: str
    role: str
    finding: str
    confidence: float = Field(ge=0, le=1)
    source_systems: list[str] = Field(default_factory=list)


class VoiceExecutiveReadiness(BaseModel):
    voice_input_status: VoiceAssistantStatus
    speech_to_text_status: VoiceAssistantStatus
    executive_reasoning_status: VoiceAssistantStatus
    multi_agent_council_status: VoiceAssistantStatus
    analytics_integration_status: VoiceAssistantStatus
    voice_output_status: VoiceAssistantStatus
    memory_system_status: VoiceAssistantStatus
    dashboard_control_status: VoiceAssistantStatus
    visual_response_status: VoiceAssistantStatus
    simulation_status: VoiceAssistantStatus
    digital_twin_status: VoiceAssistantStatus


class VoiceConversationMemoryItem(BaseModel):
    turn_id: str
    session_id: str
    speaker: str
    transcript: str
    intent: VoiceCommandIntent
    answer: str
    target_dashboard: str
    risk_score: float = Field(ge=0, le=100)
    created_at: datetime


class VoiceCommandResponse(BaseModel):
    model: str
    generated_at: datetime
    session_id: str
    transcript: str
    live_transcript: str
    recognized_intent: VoiceCommandIntent
    target_dashboard: str
    answer: str
    spoken_response: str
    risk_score: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    workflow_triggered: str
    actions: list[VoiceCommandAction]
    source_systems: list[str]
    command_trace: list[str]
    dashboard_control: VoiceDashboardControl
    tts: VoiceTTSMetadata
    voice_capabilities: list[VoiceCapabilityStatus] = Field(default_factory=list)
    visual_response: VoiceVisualResponse | None = None
    ai_council: list[VoiceAICouncilTurn] = Field(default_factory=list)
    dashboard_control_ready: bool = True
    analytics_coverage: list[str] = Field(default_factory=list)
    simulation_status: Literal["ready", "not_requested", "degraded"] = "not_requested"
    memory_status: Literal["ready", "degraded", "missing"] = "ready"
    executive_readiness: VoiceExecutiveReadiness | None = None
    production_readiness_score: float = Field(default=0, ge=0, le=100)
    final_verdict: VoiceAssistantVerdict = "AI CEO ASSISTANT GAPS REMAIN"
    conversation_memory: list[VoiceConversationMemoryItem]
    recommendations: list[str]
    supported_followups: list[str]
    latency_ms: float = Field(ge=0)
    storage: str
