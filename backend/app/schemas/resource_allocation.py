from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


ResourceSeverity = Literal["low", "medium", "high", "critical"]
AllocationPriority = Literal["balanced", "delivery_speed", "burnout_safe", "skill_depth", "cost_efficiency"]


class ResourceEmployeeProfile(BaseModel):
    employee_id: str
    name: str
    role: str
    team: str
    department: str
    skills: list[str] = Field(default_factory=list, min_length=1, max_length=24)
    capacity_hours: float = Field(gt=0, le=80)
    current_hours: float = Field(ge=0, le=120)
    availability: float = Field(default=1.0, ge=0, le=1)
    productivity: float = Field(ge=0, le=1)
    historical_delivery_speed: float = Field(ge=0, le=1)
    collaboration_score: float = Field(ge=0, le=1)
    learning_agility: float = Field(ge=0, le=1)
    burnout_risk: float = Field(ge=0, le=1)
    stress_score: float = Field(ge=0, le=1)
    focus_score: float = Field(ge=0, le=1)
    hourly_cost: float = Field(default=85, gt=0, le=500)


class ResourceTaskProfile(BaseModel):
    task_id: str
    title: str
    project: str
    description: str = ""
    required_skills: list[str] = Field(default_factory=list, min_length=1, max_length=18)
    effort_hours: float = Field(gt=0, le=120)
    complexity: float = Field(ge=0, le=1)
    priority: int = Field(ge=1, le=5)
    deadline_days: float = Field(gt=0, le=365)
    revenue_impact: float = Field(default=0, ge=0, le=50000000)
    dependency_task_ids: list[str] = Field(default_factory=list, max_length=12)
    preferred_team: str | None = None
    cognitive_load: float = Field(default=0.5, ge=0, le=1)


class ResourceDependencySignal(BaseModel):
    source_task_id: str
    target_task_id: str
    blocker_type: str = "delivery_dependency"
    risk_weight: float = Field(default=0.5, ge=0, le=1)


class ResourceAllocationRequest(BaseModel):
    department: str = "Engineering"
    sprint_name: str = "Sprint 5 Reliability Recovery"
    planning_horizon_days: int = Field(default=14, ge=1, le=90)
    objective: AllocationPriority = "balanced"
    employees: list[ResourceEmployeeProfile] = Field(default_factory=list, max_length=40)
    tasks: list[ResourceTaskProfile] = Field(default_factory=list, max_length=60)
    dependencies: list[ResourceDependencySignal] = Field(default_factory=list, max_length=120)
    realtime: bool = False


class AssignmentRecommendation(BaseModel):
    task_id: str
    task_title: str
    employee_id: str
    employee_name: str
    team: str
    assignment_score: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    skill_match_score: float = Field(ge=0, le=100)
    capacity_after_assignment: float = Field(ge=0, le=250)
    delivery_success_probability: float = Field(ge=0, le=100)
    delay_risk: float = Field(ge=0, le=100)
    burnout_risk_after_assignment: float = Field(ge=0, le=100)
    graph_bottleneck_score: float = Field(ge=0, le=100)
    rationale: str
    alternatives: list[str] = Field(default_factory=list)
    optimization_model: str


class WorkloadBalanceItem(BaseModel):
    employee_id: str
    name: str
    team: str
    current_utilization: float = Field(ge=0, le=250)
    optimized_utilization: float = Field(ge=0, le=250)
    hours_delta: float
    overload_risk: float = Field(ge=0, le=100)
    action: str
    rationale: str


class CapacityForecastPoint(BaseModel):
    sprint: str
    capacity_utilization: float = Field(ge=0, le=250)
    available_hours: float = Field(ge=0, le=5000)
    committed_hours: float = Field(ge=0, le=5000)
    delivery_probability: float = Field(ge=0, le=100)
    shortage_hours: float = Field(ge=0, le=5000)
    burnout_pressure: float = Field(ge=0, le=100)
    bottleneck_risk: float = Field(ge=0, le=100)


class SprintPlanningRecommendation(BaseModel):
    title: str
    action: str
    expected_impact: str
    priority: ResourceSeverity
    confidence: float = Field(ge=0, le=1)


class ResourceRiskAlert(BaseModel):
    severity: ResourceSeverity
    title: str
    probability: float = Field(ge=0, le=100)
    affected_entities: list[str]
    intervention: str


class WorkforceDependencyEdge(BaseModel):
    source: str
    target: str
    edge_type: str
    weight: float = Field(ge=0, le=1)
    bottleneck_score: float = Field(ge=0, le=100)


class ResourceOptimizationSummary(BaseModel):
    employees_analyzed: int
    tasks_analyzed: int
    assignments_generated: int
    capacity_utilization: float = Field(ge=0, le=250)
    overload_reduction: float = Field(ge=0, le=100)
    delivery_success_probability: float = Field(ge=0, le=100)
    sprint_completion_probability: float = Field(ge=0, le=100)
    projected_delay_days: float = Field(ge=0, le=90)
    estimated_cost_avoidance: float = Field(ge=0, le=50000000)
    stream_sequence: int = 1


class ResourceAllocationResponse(BaseModel):
    model: str
    generated_at: datetime
    department: str
    sprint_name: str
    planning_horizon_days: int
    ml_model: str
    optimization_model: str
    graph_model: str
    assignments: list[AssignmentRecommendation]
    workload_balance: list[WorkloadBalanceItem]
    capacity_forecast: list[CapacityForecastPoint]
    sprint_plan: list[SprintPlanningRecommendation]
    dependency_graph: list[WorkforceDependencyEdge]
    risk_alerts: list[ResourceRiskAlert]
    executive_insights: list[str]
    summary: ResourceOptimizationSummary
    storage: str
