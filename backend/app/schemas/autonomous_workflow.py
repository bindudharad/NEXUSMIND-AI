from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.resource_allocation import ResourceDependencySignal, ResourceEmployeeProfile, ResourceTaskProfile


WorkflowPriority = Literal["low", "medium", "high", "critical"]
WorkflowStatus = Literal["queued", "in_progress", "approved", "rejected", "scheduled", "escalated", "completed"]
ApprovalType = Literal["leave", "budget", "purchase", "access", "training"]
ApprovalDecisionValue = Literal["approved", "rejected", "needs_review"]
OperationsMode = Literal["default", "pressure", "crisis"]


class WorkflowApprovalRequest(BaseModel):
    request_id: str
    request_type: ApprovalType
    requester_id: str
    requester_name: str
    team: str = "Operations"
    amount: float = Field(default=0, ge=0, le=25_000_000)
    days: float = Field(default=0, ge=0, le=90)
    requested_access_level: str = "standard"
    policy_limit: float = Field(default=50_000, ge=0, le=50_000_000)
    business_impact: float = Field(default=0.5, ge=0, le=1)
    urgency: WorkflowPriority = "medium"
    justification: str = ""


class WorkflowMeetingRequest(BaseModel):
    meeting_id: str
    title: str
    purpose: str = ""
    required_attendees: list[str] = Field(default_factory=list, min_length=1, max_length=20)
    optional_attendees: list[str] = Field(default_factory=list, max_length=20)
    duration_minutes: int = Field(default=30, ge=10, le=240)
    priority: WorkflowPriority = "medium"
    preferred_windows: list[str] = Field(default_factory=list, max_length=12)
    attendee_availability: dict[str, list[str]] = Field(default_factory=dict)
    deadline_hours: int = Field(default=72, ge=1, le=720)


class AutonomousWorkflowRequest(BaseModel):
    mode: OperationsMode = "default"
    department: str = "Engineering"
    sprint_name: str = "Sprint 5 Reliability Recovery"
    planning_horizon_days: int = Field(default=14, ge=1, le=90)
    employees: list[ResourceEmployeeProfile] = Field(default_factory=list, max_length=60)
    tasks: list[ResourceTaskProfile] = Field(default_factory=list, max_length=80)
    dependencies: list[ResourceDependencySignal] = Field(default_factory=list, max_length=140)
    approval_requests: list[WorkflowApprovalRequest] = Field(default_factory=list, max_length=30)
    meeting_requests: list[WorkflowMeetingRequest] = Field(default_factory=list, max_length=20)
    completed_task_ids: list[str] = Field(default_factory=list, max_length=40)
    realtime: bool = True


class OperationsAssistantRequest(BaseModel):
    question: str = Field(min_length=2, max_length=600)
    session_id: str = "virtual-operations-manager"
    context: AutonomousWorkflowRequest | None = None


class TaskAssignmentDecision(BaseModel):
    task_id: str
    task_title: str
    assigned_employee_id: str
    assigned_employee_name: str
    team: str
    assignment_score: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    skill_match_score: float = Field(ge=0, le=100)
    utilization_after: float = Field(ge=0, le=250)
    delivery_success_probability: float = Field(ge=0, le=100)
    workflow_status: WorkflowStatus
    rationale: str
    alternatives: list[str] = Field(default_factory=list)
    source_systems: list[str] = Field(default_factory=list)


class ApprovalDecision(BaseModel):
    request_id: str
    request_type: ApprovalType
    requester_name: str
    decision: ApprovalDecisionValue
    confidence: float = Field(ge=0, le=1)
    policy_score: float = Field(ge=0, le=100)
    capacity_impact: float = Field(ge=0, le=100)
    risk_score: float = Field(ge=0, le=100)
    workflow_status: WorkflowStatus
    rationale: str
    next_steps: list[str] = Field(default_factory=list)
    source_systems: list[str] = Field(default_factory=list)


class MeetingScheduleDecision(BaseModel):
    meeting_id: str
    title: str
    scheduled_time: str
    duration_minutes: int
    attendees: list[str]
    conflict_score: float = Field(ge=0, le=100)
    priority_score: float = Field(ge=0, le=100)
    workflow_status: WorkflowStatus
    rationale: str
    source_systems: list[str] = Field(default_factory=list)


class ReminderEvent(BaseModel):
    reminder_id: str
    title: str
    recipient: str
    due_in_hours: int = Field(ge=0, le=8760)
    urgency: WorkflowPriority
    channel: str
    message: str
    source_workflow: str


class WorkloadBalanceAction(BaseModel):
    action_id: str
    from_employee: str
    to_employee: str
    task_title: str
    hours: float = Field(ge=0, le=160)
    utilization_delta: float
    burnout_risk_reduction: float = Field(ge=0, le=100)
    status: WorkflowStatus
    rationale: str
    source_systems: list[str] = Field(default_factory=list)


class WorkflowAutomationEvent(BaseModel):
    event_id: str
    trigger: str
    condition: str
    action: str
    affected_entities: list[str] = Field(default_factory=list)
    severity: WorkflowPriority
    confidence: float = Field(ge=0, le=1)
    workflow_status: WorkflowStatus
    source_systems: list[str] = Field(default_factory=list)


class AgentWorkflowAction(BaseModel):
    agent: str
    observation: str
    action: str
    shared_context_keys: list[str] = Field(default_factory=list)
    triggered_workflows: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)


class EscalationEvent(BaseModel):
    escalation_id: str
    category: str
    title: str
    severity: WorkflowPriority
    owner: str
    routing: list[str] = Field(default_factory=list)
    rationale: str
    sla_hours: int = Field(ge=1, le=720)
    status: WorkflowStatus


class OperationsRecommendation(BaseModel):
    title: str
    category: str
    priority: WorkflowPriority
    action: str
    rationale: str
    expected_impact: str
    confidence: float = Field(ge=0, le=1)


class WorkflowSummary(BaseModel):
    active_workflows: int = Field(ge=0)
    pending_approvals: int = Field(ge=0)
    scheduled_meetings: int = Field(ge=0)
    reminders_created: int = Field(ge=0)
    escalations_open: int = Field(ge=0)
    automation_events: int = Field(ge=0)
    workload_balance_actions: int = Field(ge=0)
    operations_readiness_score: float = Field(ge=0, le=100)
    average_assignment_confidence: float = Field(ge=0, le=1)
    policy_automation_rate: float = Field(ge=0, le=100)
    stream_sequence: int = 1


class AutonomousWorkflowResponse(BaseModel):
    model: str
    generated_at: datetime
    mode: OperationsMode
    summary: WorkflowSummary
    task_assignments: list[TaskAssignmentDecision]
    approval_decisions: list[ApprovalDecision]
    meeting_schedules: list[MeetingScheduleDecision]
    reminders: list[ReminderEvent]
    workload_balancing: list[WorkloadBalanceAction]
    automation_events: list[WorkflowAutomationEvent]
    agent_actions: list[AgentWorkflowAction]
    escalations: list[EscalationEvent]
    recommendations: list[OperationsRecommendation]
    supported_questions: list[str]
    source_systems: list[str]
    storage: str


class OperationsAssistantResponse(BaseModel):
    model: str
    generated_at: datetime
    question: str
    intent: str
    answer: str
    triggered_actions: list[str] = Field(default_factory=list)
    cited_workflows: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    source_systems: list[str] = Field(default_factory=list)
    storage: str
