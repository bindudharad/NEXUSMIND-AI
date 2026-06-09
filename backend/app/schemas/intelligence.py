from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class BurnoutSignal(BaseModel):
    department: str
    burnout: int = Field(ge=0, le=100)
    stress: int = Field(ge=0, le=100)
    attrition: int = Field(ge=0, le=100)
    meeting_load: int = Field(ge=0, le=100)
    recommendation: str


class BurnoutPredictionRequest(BaseModel):
    department: str = "Engineering"
    overtime_hours: float = Field(ge=0, le=80)
    meeting_hours: float = Field(ge=0, le=80)
    sentiment_score: float = Field(ge=-1, le=1)
    task_completion_ratio: float = Field(ge=0, le=1)
    absence_days: float = Field(ge=0, le=31)


class BurnoutPredictionResponse(BaseModel):
    department: str
    burnout_score: int = Field(ge=0, le=100)
    stress_score: int = Field(ge=0, le=100)
    resignation_probability: float = Field(ge=0, le=1)
    productivity_drop_probability: float = Field(ge=0, le=1)
    recommendation: str
    model_probabilities: dict[str, float] = {}


class ModelMetric(BaseModel):
    model: str
    accuracy: float
    roc_auc: float
    f1: float
    trained_samples: int


class ModelValidationResponse(BaseModel):
    available: bool
    metrics: list[ModelMetric]
    prediction_sample: dict[str, float]


class SecurityEvent(BaseModel):
    id: str
    title: str
    actor: str
    threat_score: int = Field(ge=0, le=100)
    status: str
    response: str


class SimulationScenario(BaseModel):
    id: str
    scenario: str
    revenue_impact: str
    delay_probability: int = Field(ge=0, le=100)
    burnout_delta: int
    recovery_plan: str


class SimulationRequest(BaseModel):
    resignation_count: int = Field(ge=0, le=500)
    workload_delta_percent: int = Field(ge=-50, le=150)
    budget_delta_percent: int = Field(ge=-80, le=200)
    security_incident: bool = False


class SimulationMonteCarloResponse(BaseModel):
    runs: int = Field(ge=128, le=1200)
    success_probability: int = Field(ge=0, le=100)
    delay_probability_p50: int = Field(ge=0, le=100)
    delay_probability_p90: int = Field(ge=0, le=100)
    burnout_delta_p90: int
    expected_revenue_impact_percent: float
    worst_case_revenue_impact_percent: float
    stability_score_p10: int = Field(ge=0, le=100)
    stability_score_p50: int = Field(ge=0, le=100)
    team_collapse_p90: int = Field(ge=0, le=100)
    risk_distribution: dict[str, int] = Field(default_factory=dict)
    confidence: float = Field(ge=0, le=1)


class SimulationResponse(BaseModel):
    delay_probability: int = Field(ge=0, le=100)
    burnout_delta: int
    revenue_impact_percent: float
    stability_score: int = Field(ge=0, le=100)
    recovery_plan: str
    productivity_loss_percent: float = Field(default=0, ge=0, le=100)
    team_collapse_probability: int = Field(default=0, ge=0, le=100)
    affected_departments: list[str] = Field(default_factory=list)
    workflow_impacts: dict[str, int] = Field(default_factory=dict)
    recovery_actions: list[str] = Field(default_factory=list)
    risk_propagation_path: list[str] = Field(default_factory=list)
    forecast_models: list[str] = Field(default_factory=list)
    source_systems: list[str] = Field(default_factory=list)
    monte_carlo: SimulationMonteCarloResponse


ScenarioType = Literal[
    "employee_resignation",
    "project_completion",
    "hiring_freeze",
    "team_restructure",
    "budget_cut",
    "productivity_change",
]


class ScenarioSimulationRequest(BaseModel):
    scenario_type: ScenarioType = "employee_resignation"
    resignation_count: int = Field(default=20, ge=0, le=500)
    seniority: str = Field(default="mixed", max_length=40)
    project_name: str = Field(default="Project Alpha Revenue Platform", max_length=160)
    deadline_months: int = Field(default=2, ge=1, le=18)
    freeze_months: int = Field(default=6, ge=1, le=24)
    source_team: str = Field(default="Platform Reliability", max_length=160)
    target_team: str = Field(default="Security Response", max_length=160)
    budget_cut_percent: int = Field(default=20, ge=0, le=80)
    workload_delta_percent: int = Field(default=25, ge=-50, le=150)
    meeting_reduction_percent: int = Field(default=50, ge=0, le=90)


class ScenarioRiskHeatmapRow(BaseModel):
    department: str
    risk: int = Field(ge=0, le=100)
    productivity: int = Field(ge=0, le=100)
    workload: int = Field(ge=0, le=100)
    hiring_need: int = Field(ge=0, le=100)


class ScenarioImpactVector(BaseModel):
    domain: str
    impact_percent: float = Field(ge=0, le=100)
    severity: Literal["low", "medium", "high", "critical"]
    explanation: str


class ScenarioSimulationResponse(BaseModel):
    model: str
    generated_at: datetime
    scenario_type: ScenarioType
    scenario_summary: str
    success_probability: int = Field(ge=0, le=100)
    failure_probability: int = Field(ge=0, le=100)
    productivity_impact_percent: float
    revenue_impact_percent: float
    burnout_impact: int
    delivery_delay_probability: int = Field(ge=0, le=100)
    client_impact: int = Field(ge=0, le=100)
    risk_level: Literal["low", "medium", "high", "critical"]
    required_engineers: int = Field(ge=0)
    required_budget: int = Field(ge=0)
    hiring_requirements: list[str] = Field(default_factory=list)
    knowledge_loss_risk: int = Field(ge=0, le=100)
    risk_factors: list[str] = Field(default_factory=list)
    bottlenecks: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    forecast_models: list[str] = Field(default_factory=list)
    source_systems: list[str] = Field(default_factory=list)
    digital_twin_entities: list[str] = Field(default_factory=list)
    risk_heatmap: list[ScenarioRiskHeatmapRow] = Field(default_factory=list)
    impact_vectors: list[ScenarioImpactVector] = Field(default_factory=list)
    decision_trace: list[str] = Field(default_factory=list)
    forecast_horizon_days: int = Field(default=90, ge=1, le=730)


class ScenarioDecisionSuiteResponse(BaseModel):
    model: str
    generated_at: datetime
    scenarios: list[ScenarioSimulationResponse]
    executive_recommendations: list[str]
    decision_readiness_score: int = Field(ge=0, le=100)
    forecast_models: list[str]
    source_systems: list[str]


class DigitalTwinEmployee(BaseModel):
    employee_id: str
    name: str
    department: str
    role: str
    workload: int = Field(ge=0, le=100)
    productivity: int = Field(ge=0, le=100)
    burnout_risk: int = Field(ge=0, le=100)
    criticality: int = Field(ge=0, le=100)
    skills: list[str] = Field(default_factory=list)
    experience_years: int = Field(ge=0, le=60)
    performance: int = Field(ge=0, le=100)
    wellness_score: int = Field(ge=0, le=100)
    attendance: int = Field(ge=0, le=100)
    communication_quality: int = Field(ge=0, le=100)
    learning_progress: int = Field(ge=0, le=100)
    promotion_probability: int = Field(ge=0, le=100)
    attrition_probability: int = Field(ge=0, le=100)


class DigitalTwinTeam(BaseModel):
    team_id: str
    name: str
    department: str
    health: int = Field(ge=0, le=100)
    productivity: int = Field(ge=0, le=100)
    collaboration: int = Field(ge=0, le=100)
    risk: int = Field(ge=0, le=100)
    burnout: int = Field(ge=0, le=100)
    delivery_performance: int = Field(ge=0, le=100)
    communication_quality: int = Field(ge=0, le=100)


class DigitalTwinDepartment(BaseModel):
    department_id: str
    name: str
    headcount: int
    revenue_dependency: float
    delivery_dependency: float
    resilience: int = Field(ge=0, le=100)
    performance: int = Field(ge=0, le=100)
    risk: int = Field(ge=0, le=100)
    productivity: int = Field(ge=0, le=100)
    cost: int = Field(ge=0, le=100)
    workload: int = Field(ge=0, le=100)
    hiring_need: int = Field(ge=0, le=100)


class DigitalTwinProject(BaseModel):
    project_id: str
    name: str
    owning_team: str
    progress: int = Field(ge=0, le=100)
    risk: int = Field(ge=0, le=100)
    resources: list[str]
    team_allocation: dict[str, int]
    timeline_forecast_days: int
    budget_forecast_percent: int
    delay_prediction: int = Field(ge=0, le=100)
    client_health: int = Field(ge=0, le=100)


class DigitalTwinResource(BaseModel):
    resource_id: str
    name: str
    resource_type: str
    capacity: int = Field(ge=0, le=100)
    utilization: int = Field(ge=0, le=100)
    risk: int = Field(ge=0, le=100)


class DigitalTwinWorkflow(BaseModel):
    workflow_id: str
    name: str
    owner_department: str
    dependency_count: int
    baseline_delay_risk: int = Field(ge=0, le=100)


class DigitalTwinOperation(BaseModel):
    operation_id: str
    name: str
    owner: str
    security_health: int = Field(ge=0, le=100)
    productivity_health: int = Field(ge=0, le=100)
    financial_health: int = Field(ge=0, le=100)
    client_health: int = Field(ge=0, le=100)
    knowledge_health: int = Field(ge=0, le=100)


class DigitalTwinGraphEdge(BaseModel):
    source: str
    target: str
    relationship: str
    strength: int = Field(ge=0, le=100)
    risk_transfer: int = Field(ge=0, le=100)


class DigitalTwinScenarioPreview(BaseModel):
    delay_probability: int = Field(ge=0, le=100)
    burnout_delta: int
    revenue_impact_percent: float
    stability_score: int = Field(ge=0, le=100)
    productivity_loss_percent: float = Field(ge=0, le=100)
    team_collapse_probability: int = Field(ge=0, le=100)
    affected_departments: list[str]
    workflow_impacts: dict[str, int]
    recovery_actions: list[str]


class DigitalTwinSnapshotResponse(BaseModel):
    model: str
    generated_at: datetime
    employees: list[DigitalTwinEmployee]
    teams: list[DigitalTwinTeam]
    departments: list[DigitalTwinDepartment]
    projects: list[DigitalTwinProject]
    resources: list[DigitalTwinResource]
    workflows: list[DigitalTwinWorkflow]
    operations: list[DigitalTwinOperation]
    graph_edges: list[DigitalTwinGraphEdge]
    forecast_models: list[str]
    supported_scenarios: list[str]
    baseline: DigitalTwinScenarioPreview
    stress_case: DigitalTwinScenarioPreview
    source_systems: list[str]


class ExecutiveDirective(BaseModel):
    command: str
    answer: str
    confidence: int = Field(ge=0, le=100)
    action: str


class AgentTurn(BaseModel):
    agent: str
    observation: str
    recommendation: str
    confidence: int = Field(ge=0, le=100)
    memory_keys: list[str] = Field(default_factory=list)
    tool_calls: list[str] = Field(default_factory=list)
    workflow_trigger: str | None = None


class AgentCouncilResponse(BaseModel):
    topic: str
    shared_memory: list[str]
    turns: list[AgentTurn]
    decision: str
    workflow_triggers: list[str] = Field(default_factory=list)
    coordination_score: int = Field(default=0, ge=0, le=100)


class KnowledgeDocument(BaseModel):
    id: str
    title: str
    content: str
    tags: list[str] = []


class KnowledgeQueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)


class KnowledgeAnswer(BaseModel):
    answer: str
    confidence: int = Field(ge=0, le=100)
    sources: list[KnowledgeDocument]


class SecurityAnalysisRequest(BaseModel):
    failed_logins: int = Field(ge=0, le=1000)
    off_hours_accesses: int = Field(ge=0, le=1000)
    data_export_mb: float = Field(ge=0, le=100000)
    privileged_actions: int = Field(ge=0, le=1000)


class SecurityAnalysisResponse(BaseModel):
    threat_score: int = Field(ge=0, le=100)
    anomaly_type: str
    response_plan: str


class WorkflowOptimizationRequest(BaseModel):
    team: str
    open_tasks: int = Field(ge=0, le=10000)
    overloaded_people: int = Field(ge=0, le=1000)
    meeting_hours: int = Field(ge=0, le=1000)


class WorkflowOptimizationResponse(BaseModel):
    automation_plan: list[str]
    expected_capacity_gain_percent: int = Field(ge=0, le=100)
    meeting_reduction_hours: int = Field(ge=0, le=1000)


class OrgGraphNode(BaseModel):
    id: str
    label: str
    risk: int = Field(ge=0, le=100)


class OrgGraphEdge(BaseModel):
    source: str
    target: str
    strength: int = Field(ge=0, le=100)


class OrgBrainResponse(BaseModel):
    nodes: list[OrgGraphNode]
    edges: list[OrgGraphEdge]
    bottlenecks: list[str]
    recommendation: str


class IntelligenceOverview(BaseModel):
    burnout_signals: list[BurnoutSignal]
    security_events: list[SecurityEvent]
    simulations: list[SimulationScenario]
    executive_directives: list[ExecutiveDirective]
    agent_council: AgentCouncilResponse
    org_brain: OrgBrainResponse
