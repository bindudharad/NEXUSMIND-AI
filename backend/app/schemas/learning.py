from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


LearningPriority = Literal["low", "medium", "high", "critical"]


class LearningEmployeeProfile(BaseModel):
    employee_id: str
    employee_name: str
    role: str
    department: str = "Engineering"
    team: str = "Platform"
    current_skills: list[str] = Field(default_factory=list, max_length=30)
    target_role: str = ""
    career_goal: str = ""
    project_requirements: list[str] = Field(default_factory=list, max_length=30)
    future_project_skills: list[str] = Field(default_factory=list, max_length=30)
    interests: list[str] = Field(default_factory=list, max_length=20)
    certifications: list[str] = Field(default_factory=list, max_length=20)
    completed_courses: list[str] = Field(default_factory=list, max_length=40)
    performance_score: float = Field(default=78, ge=0, le=100)
    productivity_score: float = Field(default=76, ge=0, le=100)
    assessment_score: float = Field(default=72, ge=0, le=100)
    promotion_readiness: float = Field(default=0.42, ge=0, le=1)
    learning_velocity: float = Field(default=0.55, ge=0, le=1)
    learning_hours_last_90d: float = Field(default=18, ge=0, le=300)
    courses_completed_last_year: int = Field(default=2, ge=0, le=80)
    manager_priority: float = Field(default=0.5, ge=0, le=1)
    market_alignment: float = Field(default=0.52, ge=0, le=1)
    attrition_risk: float = Field(default=0.24, ge=0, le=1)
    burnout_risk: float = Field(default=0.28, ge=0, le=1)


class LearningRequest(BaseModel):
    cycle_name: str = "FY2026 Workforce Learning Plan"
    horizon_months: int = Field(default=6, ge=1, le=24)
    company_roadmap_skills: list[str] = Field(default_factory=lambda: ["kubernetes", "mlops", "security", "system design", "rag"], max_length=40)
    employees: list[LearningEmployeeProfile] = Field(default_factory=list, max_length=120)
    realtime: bool = False


class SkillGapInsight(BaseModel):
    employee_id: str
    employee_name: str
    role: str
    department: str
    missing_skills: list[str]
    gap_score: float = Field(ge=0, le=100)
    future_criticality: float = Field(ge=0, le=100)
    promotion_blocker_score: float = Field(ge=0, le=100)
    rationale: str


class CourseRecommendation(BaseModel):
    employee_id: str
    employee_name: str
    course_id: str
    title: str
    provider: Literal["Coursera", "Udemy", "LinkedIn Learning"]
    target_skill: str
    category: str
    difficulty: Literal["foundation", "intermediate", "advanced", "expert"]
    duration_hours: int = Field(ge=1, le=240)
    certification: str
    recommendation_score: float = Field(ge=0, le=100)
    completion_probability: float = Field(ge=0, le=100)
    career_impact: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    rationale: str
    source_model: str


class CareerRoadmapStep(BaseModel):
    employee_id: str
    employee_name: str
    month: int = Field(ge=1, le=24)
    title: str
    focus_skills: list[str]
    learning_actions: list[str]
    expected_outcome: str
    confidence: float = Field(ge=0, le=1)


class ProgressForecast(BaseModel):
    employee_id: str
    employee_name: str
    target_skill: str
    mastery_probability: float = Field(ge=0, le=100)
    certification_completion_probability: float = Field(ge=0, le=100)
    estimated_months_to_proficiency: float = Field(ge=0.5, le=24)
    productivity_lift_estimate: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)


class TeamUpskillingHeatmapPoint(BaseModel):
    department: str
    skill: str
    gap_score: float = Field(ge=0, le=100)
    demand_score: float = Field(ge=0, le=100)
    readiness_score: float = Field(ge=0, le=100)
    employees_impacted: int = Field(ge=0)
    priority: LearningPriority


class FutureSkillForecast(BaseModel):
    skill: str
    demand_score: float = Field(ge=0, le=100)
    current_readiness: float = Field(ge=0, le=100)
    shortage_risk: float = Field(ge=0, le=100)
    forecast: list[float] = Field(default_factory=list)
    rationale: str


class LearningAlert(BaseModel):
    title: str
    priority: LearningPriority
    probability: float = Field(ge=0, le=100)
    impact: str
    recommendation: str


class LearningSummary(BaseModel):
    employees_analyzed: int
    recommendations_generated: int
    critical_skill_gaps: int
    average_gap_score: float = Field(ge=0, le=100)
    average_completion_probability: float = Field(ge=0, le=100)
    promotion_roadmaps: int
    workforce_readiness_score: float = Field(ge=0, le=100)
    stream_sequence: int = 1


class LearningResponse(BaseModel):
    model: str
    generated_at: datetime
    cycle_name: str
    horizon_months: int
    skill_gaps: list[SkillGapInsight]
    course_recommendations: list[CourseRecommendation]
    career_roadmaps: list[CareerRoadmapStep]
    progress_forecasts: list[ProgressForecast]
    team_upskilling_heatmap: list[TeamUpskillingHeatmapPoint]
    future_skill_forecasts: list[FutureSkillForecast]
    learning_alerts: list[LearningAlert]
    executive_insights: list[str]
    summary: LearningSummary
    source_systems: list[str]
    storage: str
