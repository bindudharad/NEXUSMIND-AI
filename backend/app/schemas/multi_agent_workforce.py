from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


AgentName = Literal[
    "HR Agent",
    "Security Agent",
    "Finance Agent",
    "Project Agent",
    "Productivity Agent",
    "Client Agent",
    "Knowledge Agent",
    "Executive Agent",
]
AgentStatus = Literal["active", "monitoring", "coordinating", "degraded"]
AgentMemoryType = Literal["short_term", "long_term", "context", "decision_history"]
AgentRiskLevel = Literal["low", "medium", "high", "critical"]
AgentWorkflowStatus = Literal["queued", "running", "completed", "escalated"]
AgentCouncilIntent = Literal["company_health", "burnout", "security", "project", "client", "simulation", "summary", "recommendation"]
AgentBoardroomPhase = Literal["thinking", "analysis", "challenge", "consensus"]
AgentBoardroomStatus = Literal["thinking", "speaking", "agreed", "escalated"]
AgentDebateResolution = Literal["resolved", "conditional", "escalated"]
AgentConsensusVoteType = Literal["support", "conditional_support", "oppose"]


class AgentWorkforceRequest(BaseModel):
    topic: str = Field(default="enterprise operating risk", max_length=220)
    risk_score: float = Field(default=76, ge=0, le=100)
    revenue_impact_percent: float = Field(default=-8.4, ge=-100, le=100)
    include_simulation: bool = True


class AgentCouncilRequest(BaseModel):
    question: str = Field(default="Why is company health declining?", min_length=2, max_length=800)
    session_id: str = "executive-agent-council"
    include_simulation: bool = True


class AgentSimulationRequest(BaseModel):
    question: str = Field(default="What happens if 20 engineers resign?", min_length=2, max_length=800)
    scenario_type: Literal["workforce_change", "revenue_change", "hiring_freeze", "security_incident", "client_churn"] = "workforce_change"
    resignation_count: int = Field(default=20, ge=0, le=500)
    workload_delta_percent: int = Field(default=20, ge=-50, le=150)
    budget_delta_percent: int = Field(default=0, ge=-80, le=200)
    security_incident: bool = False


class AgentProfile(BaseModel):
    agent_id: str
    name: AgentName
    role: str
    mission: str
    system_prompt: str
    status: AgentStatus
    deployable_endpoint: str
    memory_keys: list[str]
    tool_permissions: list[str]
    owned_workflows: list[str]
    context_management: list[str]
    decision_logic: list[str]
    output_validation: list[str]
    source_systems: list[str]


class AgentMemoryRecord(BaseModel):
    memory_id: str
    agent: AgentName
    memory_type: AgentMemoryType
    key: str
    value: str
    importance: float = Field(ge=0, le=1)
    created_at: datetime
    source_systems: list[str]


class AgentToolExecution(BaseModel):
    execution_id: str
    agent: AgentName
    tool_name: str
    input_summary: str
    output_summary: str
    latency_ms: int = Field(ge=0)
    success: bool
    permission_scope: str


class AgentMessage(BaseModel):
    message_id: str
    from_agent: AgentName
    to_agent: AgentName
    topic: str
    content: str
    evidence: list[str]
    created_at: datetime


class AgentCouncilTurn(BaseModel):
    agent: AgentName
    observation: str
    recommendation: str
    confidence: float = Field(ge=0, le=100)
    memory_keys: list[str]
    tool_calls: list[str]
    workflow_trigger: str
    depends_on: list[AgentName] = Field(default_factory=list)


class AgentTask(BaseModel):
    task_id: str
    owner: AgentName
    task: str
    trigger: str
    status: AgentWorkflowStatus
    priority: AgentRiskLevel
    expected_business_impact: str
    automation_ready: bool


class AgentWorkflowStep(BaseModel):
    step: int = Field(ge=1)
    agent: AgentName
    action: str
    input_context: list[str]
    output: str


class AgentWorkflow(BaseModel):
    workflow_id: str
    name: str
    trigger: str
    participants: list[AgentName]
    status: AgentWorkflowStatus
    steps: list[AgentWorkflowStep]
    final_recommendation: str
    expected_risk_reduction: float = Field(ge=0, le=100)


class AgentDecision(BaseModel):
    decision_id: str
    title: str
    risk_level: AgentRiskLevel
    recommendation: str
    rationale: str
    participating_agents: list[AgentName]
    confidence: float = Field(ge=0, le=100)
    action_plan: list[str]


class AgentSimulationResult(BaseModel):
    scenario_type: str
    question: str
    participating_agents: list[AgentName]
    productivity_impact: float
    revenue_impact_percent: float
    delay_probability: float = Field(ge=0, le=100)
    burnout_delta: float
    security_risk_delta: float
    client_risk_delta: float
    recommended_response: list[str]
    digital_twin_evidence: list[str]
    confidence: float = Field(ge=0, le=1)


class AgentBoardroomStage(BaseModel):
    stage: int = Field(ge=1)
    agent: AgentName
    phase: AgentBoardroomPhase
    status: AgentBoardroomStatus
    message: str
    recommendation: str
    confidence: float = Field(ge=0, le=100)
    evidence: list[str]
    depends_on: list[AgentName] = Field(default_factory=list)


class AgentCouncilConsensus(BaseModel):
    final_decision: str
    confidence: float = Field(ge=0, le=100)
    owner_agent: AgentName
    recommended_actions: list[str]
    dissenting_risks: list[str]
    digital_twin_evidence: list[str]
    simulation_evidence: list[str]
    majority_vote: str = "support"
    risk_weighted_score: float = Field(default=0, ge=0, le=100)
    agreement_level: Literal["low", "medium", "high", "unanimous"] = "high"
    conflict_resolution_summary: str = ""


class AgentReasoningTrace(BaseModel):
    agent: AgentName
    perspective: str
    reasoning_summary: str
    evidence_used: list[str]
    assumptions: list[str]
    uncertainty: str
    conclusion: str
    confidence: float = Field(ge=0, le=100)


class AgentDebateExchange(BaseModel):
    exchange_id: str
    from_agent: AgentName
    to_agent: AgentName
    disagreement: str
    challenge: str
    response: str
    resolution: AgentDebateResolution
    disagreement_score: float = Field(ge=0, le=100)
    evidence: list[str]


class AgentConsensusVote(BaseModel):
    agent: AgentName
    vote: AgentConsensusVoteType
    risk_weight: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=100)
    rationale: str
    evidence: list[str]


class AgentResearchMetrics(BaseModel):
    perspective_diversity_score: float = Field(ge=0, le=100)
    evidence_coverage_score: float = Field(ge=0, le=100)
    disagreement_count: int = Field(ge=0)
    consensus_score: float = Field(ge=0, le=100)
    explainability_score: float = Field(ge=0, le=100)
    negotiation_rounds: int = Field(ge=0)
    conflict_resolution_status: Literal["resolved", "partially_resolved", "unresolved"]
    reasoning_abstraction_layer: str


class AgentAnalytics(BaseModel):
    agent: AgentName
    average_response_ms: int = Field(ge=0)
    usage_count: int = Field(ge=0)
    recommendation_count: int = Field(ge=0)
    success_rate: float = Field(ge=0, le=100)
    workload_score: float = Field(ge=0, le=100)
    health_score: float = Field(ge=0, le=100)


class AgentCommunicationBusStatus(BaseModel):
    bus_name: str
    protocol: str
    active_channels: list[str]
    message_count: int = Field(ge=0)
    average_latency_ms: int = Field(ge=0)
    persistence: str
    failure_recovery: list[str]
    status: Literal["ready", "degraded", "missing"] = "ready"


class AgentSharedMemoryStatus(BaseModel):
    memory_store: str
    persistent: bool
    records: int = Field(ge=0)
    memory_types: list[AgentMemoryType]
    retrieval_strategy: str
    latest_decision_keys: list[str]
    status: Literal["ready", "degraded", "missing"] = "ready"


class AgentMonitoringStatus(BaseModel):
    active_agents: int = Field(ge=0)
    average_response_ms: int = Field(ge=0)
    average_success_rate: float = Field(ge=0, le=100)
    monitored_metrics: list[str]
    realtime_stream: bool
    status: Literal["ready", "degraded", "missing"] = "ready"


class AgentSecurityControl(BaseModel):
    control: str
    status: Literal["enforced", "warning", "missing"]
    evidence: str


class AgentWorkforceSummary(BaseModel):
    active_agents: int = Field(ge=0)
    messages: int = Field(ge=0)
    workflows: int = Field(ge=0)
    autonomous_tasks: int = Field(ge=0)
    recommendations: int = Field(ge=0)
    shared_memory_records: int = Field(ge=0)
    average_agent_health: float = Field(ge=0, le=100)
    coordination_score: float = Field(ge=0, le=100)
    production_readiness_score: float = Field(default=0, ge=0, le=100)
    innovation_score: float = Field(default=0, ge=0, le=100)
    stream_sequence: int = 1


class MultiAgentWorkforceResponse(BaseModel):
    model: str
    generated_at: datetime
    topic: str
    summary: AgentWorkforceSummary
    agents: list[AgentProfile]
    council_turns: list[AgentCouncilTurn]
    messages: list[AgentMessage]
    memory: list[AgentMemoryRecord]
    tool_executions: list[AgentToolExecution]
    autonomous_tasks: list[AgentTask]
    workflows: list[AgentWorkflow]
    decisions: list[AgentDecision]
    simulations: list[AgentSimulationResult]
    boardroom_stages: list[AgentBoardroomStage]
    consensus: AgentCouncilConsensus
    reasoning_traces: list[AgentReasoningTrace]
    debate_exchanges: list[AgentDebateExchange]
    consensus_votes: list[AgentConsensusVote]
    research_metrics: AgentResearchMetrics
    analytics: list[AgentAnalytics]
    communication_bus: AgentCommunicationBusStatus
    shared_memory_status: AgentSharedMemoryStatus
    monitoring: AgentMonitoringStatus
    security_controls: list[AgentSecurityControl]
    executive_brief: str
    supported_questions: list[str]
    source_systems: list[str]
    final_verdict: str = "AUTONOMOUS AI MANAGERS COMPLETE"
    storage: str


class AgentCouncilResponseV2(BaseModel):
    model: str
    generated_at: datetime
    question: str
    intent: AgentCouncilIntent
    answer: str
    participating_agents: list[AgentName]
    council_turns: list[AgentCouncilTurn]
    messages: list[AgentMessage]
    decisions: list[AgentDecision]
    simulation: AgentSimulationResult | None = None
    boardroom_stages: list[AgentBoardroomStage]
    consensus: AgentCouncilConsensus
    reasoning_traces: list[AgentReasoningTrace]
    debate_exchanges: list[AgentDebateExchange]
    consensus_votes: list[AgentConsensusVote]
    research_metrics: AgentResearchMetrics
    confidence: float = Field(ge=0, le=1)
    final_verdict: str = "AUTONOMOUS AI MANAGERS COMPLETE"
    source_systems: list[str]
    storage: str
