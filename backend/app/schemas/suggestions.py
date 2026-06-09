from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


SmartSuggestionCategory = Literal[
    "meeting_reduction",
    "workload_redistribution",
    "wellness_break",
    "team_optimization",
    "productivity_improvement",
]
SmartSuggestionPriority = Literal["critical", "high", "medium", "low"]
SmartSuggestionScenario = Literal["default", "crisis"]


class SmartSuggestionRequest(BaseModel):
    scenario: SmartSuggestionScenario = "default"
    sensitivity: float = Field(default=0.66, ge=0, le=1)
    feedback_weight: float = Field(default=0.32, ge=0, le=1)


class SmartSuggestion(BaseModel):
    suggestion_id: str
    category: SmartSuggestionCategory
    title: str
    action: str
    rationale: str
    priority: SmartSuggestionPriority
    confidence: float = Field(ge=0, le=1)
    impact_score: float = Field(ge=0, le=100)
    estimated_gain: str
    time_to_impact_hours: int = Field(ge=1, le=720)
    affected_employees: list[str]
    source_systems: list[str]
    evidence: list[str]
    created_at: datetime
    feedback_state: Literal["new", "accepted", "dismissed"] = "new"


class SmartSuggestionSummary(BaseModel):
    total: int
    critical: int
    high: int
    average_impact: float = Field(ge=0, le=100)
    average_confidence: float = Field(ge=0, le=1)
    stream_sequence: int


class SmartSuggestionResponse(BaseModel):
    model: str
    generated_at: datetime
    scenario: SmartSuggestionScenario
    adaptive_threshold: float = Field(ge=0, le=100)
    suggestions: list[SmartSuggestion]
    summary: SmartSuggestionSummary
    storage: str


class SmartSuggestionFeedbackRequest(BaseModel):
    suggestion_id: str
    accepted: bool
    usefulness_score: int = Field(ge=1, le=5)
    notes: str = Field(default="", max_length=500)


class SmartSuggestionFeedbackResponse(BaseModel):
    suggestion_id: str
    learning_signal: float = Field(ge=0, le=1)
    message: str
    storage: str
