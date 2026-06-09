from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


RecommendationCategory = Literal["work_redistribution", "break", "team_balancing"]
RecommendationPriority = Literal["critical", "high", "medium", "low"]


class EmployeeProfile(BaseModel):
    employee_id: str
    name: str
    role: str
    team: str
    skills: list[str] = Field(default_factory=list)
    current_tasks: int = Field(ge=0)
    capacity_hours: float = Field(gt=0, le=80)
    allocated_hours: float = Field(ge=0, le=120)
    productivity: float = Field(ge=0, le=1)
    overtime_hours: float = Field(ge=0, le=40)
    stress_score: float = Field(ge=0, le=1)
    burnout_risk: float = Field(ge=0, le=1)
    collaboration_score: float = Field(ge=0, le=1)


class TaskProfile(BaseModel):
    task_id: str
    title: str
    required_skill: str
    effort_hours: float = Field(gt=0, le=80)
    priority: int = Field(ge=1, le=5)
    project: str
    dependency_team: str | None = None


class RecommendationRequest(BaseModel):
    employees: list[EmployeeProfile] = Field(default_factory=list)
    tasks: list[TaskProfile] = Field(default_factory=list)
    feedback_weight: float = Field(default=0.35, ge=0, le=1)


class RecommendationItem(BaseModel):
    recommendation_id: str
    category: RecommendationCategory
    title: str
    action: str
    rationale: str
    confidence: float = Field(ge=0, le=1)
    impact_score: float = Field(ge=0, le=100)
    priority: RecommendationPriority
    affected_employees: list[str]
    source_model: str


class RecommendationResponse(BaseModel):
    model: str
    generated_at: datetime
    employees_analyzed: int
    tasks_analyzed: int
    team_balance_score: float = Field(ge=0, le=100)
    recommendations: list[RecommendationItem]
    storage: str


class RecommendationFeedbackRequest(BaseModel):
    recommendation_id: str
    accepted: bool
    usefulness_score: int = Field(ge=1, le=5)
    notes: str = ""


class RecommendationFeedbackResponse(BaseModel):
    recommendation_id: str
    learning_signal: float = Field(ge=0, le=1)
    message: str
    storage: str
