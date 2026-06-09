from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.employee_dashboard import EmployeeActivityPoint


ProductivitySeverity = Literal["low", "medium", "high", "critical"]
AppCategory = Literal["productive", "communication", "planning", "development", "meeting", "research", "distraction"]


class ProductivityActivityWindow(BaseModel):
    hour: int = Field(ge=0, le=23)
    active_minutes: float = Field(default=50, ge=0, le=60)
    productive_minutes: float = Field(default=38, ge=0, le=60)
    idle_minutes: float = Field(default=5, ge=0, le=60)
    app_switches: int = Field(default=18, ge=0, le=600)
    tab_switches: int = Field(default=24, ge=0, le=900)
    notifications: int = Field(default=12, ge=0, le=500)
    meeting_minutes: float = Field(default=8, ge=0, le=60)
    deep_work_minutes: float = Field(default=28, ge=0, le=60)
    keyboard_events: int = Field(default=1400, ge=0, le=20000)
    mouse_events: int = Field(default=500, ge=0, le=20000)
    distraction_minutes: float = Field(default=4, ge=0, le=60)
    task_completion_ratio: float = Field(default=0.78, ge=0, le=1)
    focus_quality: float = Field(default=0.72, ge=0, le=1)


class AppUsageSegment(BaseModel):
    app_name: str = Field(min_length=1, max_length=80)
    category: AppCategory = "productive"
    minutes: float = Field(default=15, ge=0, le=600)
    switches: int = Field(default=4, ge=0, le=600)
    notification_count: int = Field(default=0, ge=0, le=500)
    productive: bool = True


class ProductivityMessage(BaseModel):
    text: str = Field(min_length=2, max_length=4000)
    channel: str = "chat"


class ProductivityAnalyzeRequest(BaseModel):
    employee_id: str = "emp-productivity-001"
    employee_name: str = "Aarav Mehta"
    department: str = "Engineering"
    role: str = "Senior Backend Engineer"
    windows: list[ProductivityActivityWindow] = Field(default_factory=list, max_length=48)
    app_usage: list[AppUsageSegment] = Field(default_factory=list, max_length=80)
    work_pattern: EmployeeActivityPoint | None = None
    messages: list[ProductivityMessage] = Field(default_factory=list, max_length=30)
    hourly_cost: float = Field(default=85, ge=5, le=1000)
    realtime: bool = False


class HourlyProductivityPoint(BaseModel):
    hour_label: str
    productivity_score: float = Field(ge=0, le=100)
    focus_score: float = Field(ge=0, le=100)
    efficiency_score: float = Field(ge=0, le=100)
    leakage_minutes: float = Field(ge=0, le=60)
    energy_score: float = Field(ge=0, le=100)
    deep_work_minutes: float = Field(ge=0, le=60)
    dominant_cause: str


class ToolSwitchingAnalytics(BaseModel):
    app_switches_per_hour: float = Field(ge=0)
    tab_switches_per_hour: float = Field(ge=0)
    context_switch_penalty: float = Field(ge=0, le=100)
    overloaded_tools: list[str]
    fatigue_score: float = Field(ge=0, le=100)
    productivity_loss_percent: float = Field(ge=0, le=100)
    insight: str


class DistractionAnalytics(BaseModel):
    distraction_score: float = Field(ge=0, le=100)
    idle_time_minutes: float = Field(ge=0)
    distraction_minutes: float = Field(ge=0)
    notification_pressure: float = Field(ge=0, le=100)
    top_distraction_sources: list[str]
    estimated_lost_hours: float = Field(ge=0)
    insight: str


class DeepWorkAnalytics(BaseModel):
    total_deep_work_hours: float = Field(ge=0)
    average_deep_work_block_minutes: float = Field(ge=0)
    interruption_frequency: float = Field(ge=0)
    stability_score: float = Field(ge=0, le=100)
    disruption_causes: list[str]
    insight: str


class EnergyForecastPoint(BaseModel):
    window: str
    energy_score: float = Field(ge=0, le=100)
    productivity_score: float = Field(ge=0, le=100)
    fatigue_risk: float = Field(ge=0, le=100)


class ProductivityHeatmapCell(BaseModel):
    window: str
    leakage_score: float = Field(ge=0, le=100)
    focus_score: float = Field(ge=0, le=100)
    productive_minutes: float = Field(ge=0, le=60)
    lost_minutes: float = Field(ge=0, le=60)
    dominant_cause: str


class ProductivityRecommendation(BaseModel):
    category: str
    priority: ProductivitySeverity
    action: str
    expected_impact: str
    confidence: float = Field(ge=0, le=1)


class ProductivityRiskAlert(BaseModel):
    category: str
    severity: ProductivitySeverity
    score: float = Field(ge=0, le=100)
    message: str
    evidence: list[str]
    recommendation: str


class ProductivitySummary(BaseModel):
    productivity_score: float = Field(ge=0, le=100)
    focus_score: float = Field(ge=0, le=100)
    efficiency_score: float = Field(ge=0, le=100)
    leakage_percent: float = Field(ge=0, le=100)
    lost_productive_hours: float = Field(ge=0)
    estimated_loss_cost: float = Field(ge=0)
    tool_switching_overload: float = Field(ge=0, le=100)
    distraction_score: float = Field(ge=0, le=100)
    deep_work_stability: float = Field(ge=0, le=100)
    low_focus_window_count: int = Field(ge=0)
    stream_sequence: int = 1


class ProductivityAnalysisResponse(BaseModel):
    model: str
    generated_at: datetime
    employee_id: str
    employee_name: str
    department: str
    role: str
    ml_model: str
    nlp_model: str
    behavioral_model: str
    summary: ProductivitySummary
    hourly_trend: list[HourlyProductivityPoint]
    tool_switching: ToolSwitchingAnalytics
    distraction_analytics: DistractionAnalytics
    deep_work_analytics: DeepWorkAnalytics
    energy_forecast: list[EnergyForecastPoint]
    leakage_heatmap: list[ProductivityHeatmapCell]
    recommendations: list[ProductivityRecommendation]
    risk_alerts: list[ProductivityRiskAlert]
    executive_insights: list[str]
    storage: str
