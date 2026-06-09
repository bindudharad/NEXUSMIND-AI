from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


LearningStatus = Literal["ready", "learning", "degraded", "missing"]
AdaptiveVerdict = Literal[
    "SELF-EVOLVING AI SYSTEM COMPLETE",
    "ADAPTIVE ENTERPRISE INTELLIGENCE SYSTEM COMPLETE",
    "SELF-LEARNING GAPS REMAIN",
]


class SelfLearningScorecard(BaseModel):
    learning_engine_score: float = Field(ge=0, le=100)
    adaptive_recommendation_score: float = Field(ge=0, le=100)
    feedback_loop_score: float = Field(ge=0, le=100)
    knowledge_evolution_score: float = Field(ge=0, le=100)
    agent_learning_score: float = Field(ge=0, le=100)
    digital_twin_learning_score: float = Field(ge=0, le=100)
    prediction_improvement_score: float = Field(ge=0, le=100)
    production_readiness_score: float = Field(ge=0, le=100)
    minimum_score: float = Field(ge=0, le=100)


class LearningComponentStatus(BaseModel):
    component: str
    status: LearningStatus
    score: float = Field(ge=0, le=100)
    learning_signal_count: int = Field(ge=0)
    evidence: list[str]
    source_systems: list[str]


class LearnedPattern(BaseModel):
    domain: Literal["culture", "employee_behavior", "business_pattern"]
    pattern: str
    confidence: float = Field(ge=0, le=100)
    evidence: list[str]
    adaptation: str


class DecisionOutcomeLearning(BaseModel):
    decision: str
    outcome: str
    outcome_score: float = Field(ge=0, le=100)
    confidence_delta: float
    learned_rule: str
    source_systems: list[str]


class FeedbackLoopStatus(BaseModel):
    loop: str
    status: LearningStatus
    records: int = Field(ge=0)
    average_learning_signal: float = Field(ge=0, le=1)
    confidence_delta: float
    adaptation: str
    storage: str


class AdaptiveRecommendationLearning(BaseModel):
    recommendation: str
    previous_confidence: float = Field(ge=0, le=100)
    adapted_confidence: float = Field(ge=0, le=100)
    confidence_delta: float
    learned_from: list[str]
    action: str


class PredictionAccuracyMetric(BaseModel):
    metric: str
    baseline_accuracy: float = Field(ge=0, le=100)
    current_accuracy: float = Field(ge=0, le=100)
    improvement_percent: float
    evidence: list[str]


class PredictionErrorRecord(BaseModel):
    prediction_id: str
    model_name: str
    domain: Literal["revenue", "burnout", "attrition", "project_delay", "risk", "simulation"]
    predicted_value: float
    actual_value: float
    absolute_error: float = Field(ge=0)
    error_percent: float = Field(ge=0)
    observed_at: datetime
    source_systems: list[str]


class ModelEvaluationMetric(BaseModel):
    model_name: str
    model_type: Literal["forecasting", "recommendation", "risk", "burnout", "attrition", "simulation"]
    version: str
    accuracy: float = Field(ge=0, le=100)
    precision: float = Field(ge=0, le=100)
    recall: float = Field(ge=0, le=100)
    f1_score: float = Field(ge=0, le=100)
    mae: float = Field(ge=0)
    rmse: float = Field(ge=0)
    status: LearningStatus
    retraining_required: bool
    evaluated_at: datetime
    evidence: list[str]


class DriftDetectionSignal(BaseModel):
    drift_type: Literal["data_drift", "concept_drift", "feature_drift", "behavioral_drift"]
    domain: str
    drift_score: float = Field(ge=0, le=100)
    threshold: float = Field(ge=0, le=100)
    status: Literal["stable", "watch", "retrain"]
    retraining_triggered: bool
    evidence: list[str]


class RetrainingEvent(BaseModel):
    event_id: str
    model_name: str
    trigger: Literal["accuracy_drop", "new_data", "model_drift", "performance_degradation", "scheduled_refresh"]
    previous_version: str
    new_version: str
    previous_accuracy: float = Field(ge=0, le=100)
    new_accuracy: float = Field(ge=0, le=100)
    accuracy_delta: float
    status: Literal["completed", "scheduled", "skipped"]
    started_at: datetime
    completed_at: datetime | None = None
    training_records: int = Field(ge=0)
    evidence: list[str]


class CompanyConditionChange(BaseModel):
    metric: str
    before_value: float
    after_value: float
    change_percent: float
    source_system: str


class StrategyEvolutionRecord(BaseModel):
    old_strategy: str
    new_strategy: str
    reason: str
    expected_improvement: float = Field(ge=0, le=100)
    evidence: list[str]


class SelfLearningDemoStage(BaseModel):
    stage: int
    title: str
    status: Literal["completed", "active", "queued"]
    explanation: str
    evidence: list[str]


class SelfLearningDemoState(BaseModel):
    demo_id: str
    scenario: str
    initial_prediction: float = Field(ge=0, le=100)
    adapted_prediction: float = Field(ge=0, le=100)
    prediction_delta: float
    detected_changes: list[CompanyConditionChange]
    active_drift_types: list[str]
    retrained_models: list[str]
    previous_strategy: str
    evolved_strategy: str
    strategy_evolution: list[StrategyEvolutionRecord]
    digital_twin_signals: list[str]
    agent_learning_updates: list[str]
    executive_explanation: str
    stages: list[SelfLearningDemoStage]
    completed: bool


class ForecastLearningStatus(BaseModel):
    status: LearningStatus
    tracked_metrics: list[str]
    mean_absolute_error: float = Field(ge=0)
    rmse: float = Field(ge=0)
    forecast_accuracy: float = Field(ge=0, le=100)
    calibration_factor: float
    learned_adjustments: list[str]
    evidence: list[str]


class SimulationLearningStatus(BaseModel):
    status: LearningStatus
    simulation_accuracy: float = Field(ge=0, le=100)
    calibration_delta: float
    scenarios_calibrated: int = Field(ge=0)
    learned_adjustments: list[str]
    evidence: list[str]


class KnowledgeEvolutionStatus(BaseModel):
    status: LearningStatus
    documents_indexed: int = Field(ge=0)
    chunks_indexed: int = Field(ge=0)
    graph_nodes: int = Field(ge=0)
    graph_edges: int = Field(ge=0)
    experts_detected: int = Field(ge=0)
    incidents_detected: int = Field(ge=0)
    solutions_detected: int = Field(ge=0)
    stale_assumptions_retired: int = Field(ge=0)
    new_best_practices: list[str]
    evidence: list[str]


class AgentLearningStatus(BaseModel):
    status: LearningStatus
    agents: list[str]
    shared_memory_records: int = Field(ge=0)
    messages: int = Field(ge=0)
    workflows: int = Field(ge=0)
    learned_patterns: list[str]
    propagated_insights: list[str]
    evidence: list[str]


class DigitalTwinLearningStatus(BaseModel):
    status: LearningStatus
    twin_entities: list[str]
    adaptation_signals: list[str]
    scenario_accuracy: float = Field(ge=0, le=100)
    simulation_accuracy: float = Field(ge=0, le=100)
    evidence: list[str]


class SelfLearningFeedbackRequest(BaseModel):
    source_system: str = Field(default="executive_dashboard", max_length=120)
    signal_type: Literal["recommendation", "forecast", "risk", "simulation", "knowledge", "agent"] = "recommendation"
    accepted: bool = True
    usefulness_score: int = Field(default=5, ge=1, le=5)
    outcome: str = Field(default="validated by operator", max_length=400)
    notes: str = Field(default="", max_length=600)
    prediction_id: str | None = Field(default=None, max_length=120)
    model_name: str | None = Field(default=None, max_length=160)
    predicted_value: float | None = None
    actual_value: float | None = None


class SelfLearningFeedbackResponse(BaseModel):
    feedback_id: str
    learning_signal: float = Field(ge=0, le=1)
    retraining_triggered: bool = False
    message: str
    storage: str


class SelfLearningAssistantRequest(BaseModel):
    question: str = Field(min_length=2, max_length=600)
    context: dict[str, str | float | int | bool] = Field(default_factory=dict)


class SelfLearningAssistantResponse(BaseModel):
    answer: str
    confidence: float = Field(ge=0, le=1)
    actions: list[str]
    cited_engines: list[str]
    learning_evidence: list[str]


class SelfLearningAIResponse(BaseModel):
    model: str
    generated_at: datetime
    learning_engine_status: LearningStatus
    adaptive_ai_status: LearningStatus
    recommendation_accuracy: float = Field(ge=0, le=100)
    forecast_accuracy: float = Field(ge=0, le=100)
    knowledge_evolution_status: LearningStatus
    agent_learning_status: LearningStatus
    digital_twin_learning_status: LearningStatus
    scorecard: SelfLearningScorecard
    components: list[LearningComponentStatus]
    culture_insights: list[LearnedPattern]
    employee_behavior_insights: list[LearnedPattern]
    business_pattern_insights: list[LearnedPattern]
    decision_outcomes: list[DecisionOutcomeLearning]
    feedback_loops: list[FeedbackLoopStatus]
    adaptive_recommendations: list[AdaptiveRecommendationLearning]
    prediction_errors: list[PredictionErrorRecord] = Field(default_factory=list)
    model_evaluations: list[ModelEvaluationMetric] = Field(default_factory=list)
    drift_signals: list[DriftDetectionSignal] = Field(default_factory=list)
    retraining_events: list[RetrainingEvent] = Field(default_factory=list)
    demo_state: SelfLearningDemoState | None = None
    forecast_learning: ForecastLearningStatus | None = None
    simulation_learning: SimulationLearningStatus | None = None
    knowledge_evolution: KnowledgeEvolutionStatus
    agent_learning: AgentLearningStatus
    digital_twin_learning: DigitalTwinLearningStatus
    prediction_improvements: list[PredictionAccuracyMetric]
    learning_timeline: list[str]
    missing_components: list[str]
    fixed_components: list[str]
    regenerated_components: list[str]
    production_readiness_score: float = Field(ge=0, le=100)
    learning_maturity_score: float = Field(default=0, ge=0, le=100)
    final_verdict: AdaptiveVerdict
    source_systems: list[str]
    storage: dict[str, str]
    stream_sequence: int = 1
