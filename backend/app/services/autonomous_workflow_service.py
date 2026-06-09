from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from threading import Lock
from uuid import NAMESPACE_DNS, uuid5

from app.core.cache import TTLResponseCache
from app.schemas.alerts import AlertDetectionRequest
from app.schemas.autonomous_workflow import (
    AgentWorkflowAction,
    ApprovalDecision,
    AutonomousWorkflowRequest,
    AutonomousWorkflowResponse,
    EscalationEvent,
    MeetingScheduleDecision,
    OperationsAssistantRequest,
    OperationsAssistantResponse,
    OperationsRecommendation,
    ReminderEvent,
    TaskAssignmentDecision,
    WorkflowApprovalRequest,
    WorkflowAutomationEvent,
    WorkflowMeetingRequest,
    WorkflowSummary,
    WorkloadBalanceAction,
)
from app.schemas.recommendations import RecommendationRequest
from app.schemas.resource_allocation import ResourceAllocationRequest, ResourceEmployeeProfile, ResourceTaskProfile
from app.schemas.suggestions import SmartSuggestionRequest
from app.services.alert_service import alert_service
from app.services.recommendation_service import recommendation_service
from app.services.resource_allocation_service import resource_allocation_service
from app.services.suggestion_service import smart_suggestion_service


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
HISTORY_PATH = DATA_DIR / "autonomous_workflow_history.jsonl"


class AutonomousWorkflowService:
    model_name = "Virtual Operations Manager AI - Autonomous Workflow Automation System"
    source_systems = [
        "workflow_engine",
        "automation_engine",
        "approval_engine",
        "task_assignment_engine",
        "scheduling_engine",
        "notification_engine",
        "workload_balancing_engine",
        "multi_agent_orchestrator",
        "escalation_engine",
        "ai_operations_assistant",
        "resource_allocation_optimizer",
        "alert_correlator",
        "smart_suggestion_engine",
        "recommendation_engine",
        "autonomous_workflow_history_jsonl",
    ]

    def __init__(self) -> None:
        self._cache: TTLResponseCache[AutonomousWorkflowResponse] = TTLResponseCache(ttl_seconds=8)
        self._lock = Lock()
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def run(self, payload: AutonomousWorkflowRequest | None = None) -> AutonomousWorkflowResponse:
        if payload is None:
            return self._cache.get_or_set(lambda: self._run_uncached(self.default_request()))
        return self._run_uncached(payload)

    def _run_uncached(self, payload: AutonomousWorkflowRequest) -> AutonomousWorkflowResponse:
        request = self._normalize_request(payload)
        now = datetime.now(timezone.utc)
        allocation = resource_allocation_service.optimize(
            ResourceAllocationRequest(
                department=request.department,
                sprint_name=request.sprint_name,
                planning_horizon_days=request.planning_horizon_days,
                objective="balanced",
                employees=request.employees,
                tasks=request.tasks,
                dependencies=request.dependencies,
                realtime=True,
            )
        )
        crisis_mode = request.mode == "crisis"
        alerts = alert_service.feed(AlertDetectionRequest(scenario="crisis" if crisis_mode else "default", sensitivity=0.76 if crisis_mode else 0.64))
        suggestions = smart_suggestion_service.generate(SmartSuggestionRequest(scenario="crisis" if crisis_mode else "default", sensitivity=0.76 if crisis_mode else 0.64))
        recommendations_context = recommendation_service.generate(
            RecommendationRequest(
                feedback_weight=0.15 if crisis_mode else 0.05,
                employees=recommendation_service.default_employees(),
                tasks=recommendation_service.default_tasks(),
            )
        )

        assignments = self._task_assignments(allocation)
        approvals = self._approval_decisions(request.approval_requests, request.employees, allocation)
        meetings = self._meeting_schedules(request.meeting_requests)
        workload = self._workload_actions(request.tasks, allocation)
        automation_events = self._automation_events(request, allocation, alerts, approvals)
        agent_actions = self._agent_actions(assignments, approvals, meetings, workload, automation_events, alerts, suggestions)
        escalations = self._escalations(allocation, alerts, approvals, automation_events)
        reminders = self._reminders(assignments, approvals, meetings, escalations, request)
        recommendations = self._recommendations(assignments, approvals, workload, escalations, suggestions, recommendations_context)
        summary = self._summary(assignments, approvals, meetings, reminders, workload, automation_events, escalations)

        response = AutonomousWorkflowResponse(
            model=self.model_name,
            generated_at=now,
            mode=request.mode,
            summary=summary,
            task_assignments=assignments,
            approval_decisions=approvals,
            meeting_schedules=meetings,
            reminders=reminders,
            workload_balancing=workload,
            automation_events=automation_events,
            agent_actions=agent_actions,
            escalations=escalations,
            recommendations=recommendations,
            supported_questions=[
                "Assign this task.",
                "Who should work on Project X?",
                "Schedule a review meeting.",
                "Show overloaded employees.",
                "Recommend workload balancing.",
                "Approve this leave request.",
                "Escalate critical workflow risks.",
            ],
            source_systems=self.source_systems,
            storage=str(HISTORY_PATH),
        )
        self._append_jsonl(response.model_dump(mode="json"))
        return response

    def ask(self, payload: OperationsAssistantRequest) -> OperationsAssistantResponse:
        workflow = self.run(payload.context)
        question = payload.question.lower()
        intent = self._intent(question)
        answer, actions, cited = self._assistant_answer(intent, workflow)
        return OperationsAssistantResponse(
            model="AI Operations Assistant",
            generated_at=datetime.now(timezone.utc),
            question=payload.question,
            intent=intent,
            answer=answer,
            triggered_actions=actions,
            cited_workflows=cited,
            recommended_actions=[item.action for item in workflow.recommendations[:4]],
            confidence=round(min(0.97, 0.74 + workflow.summary.operations_readiness_score / 500), 3),
            source_systems=["ai_operations_assistant", *workflow.source_systems[:8]],
            storage=str(HISTORY_PATH),
        )

    async def stream(self, payload: AutonomousWorkflowRequest | None = None):
        base = payload or self.default_request()
        scenarios = [
            base.model_copy(update={"mode": "default"}),
            self._pressure_variant(base, mode="pressure", workload_delta=5.5, urgency_delta=0.12),
            self._pressure_variant(base, mode="crisis", workload_delta=12.0, urgency_delta=0.28),
        ]
        for sequence, scenario in enumerate(scenarios, start=1):
            response = self.run(scenario)
            data = response.model_dump(mode="json")
            data["summary"]["stream_sequence"] = sequence
            yield f"event: autonomous_workflow\ndata: {json.dumps(data)}\n\n"
            await asyncio.sleep(0.8)

    def _normalize_request(self, payload: AutonomousWorkflowRequest) -> AutonomousWorkflowRequest:
        default = self.default_request()
        return payload.model_copy(
            update={
                "employees": payload.employees or default.employees,
                "tasks": payload.tasks or default.tasks,
                "dependencies": payload.dependencies or default.dependencies,
                "approval_requests": payload.approval_requests or default.approval_requests,
                "meeting_requests": payload.meeting_requests or default.meeting_requests,
            }
        )

    def _task_assignments(self, allocation) -> list[TaskAssignmentDecision]:
        output: list[TaskAssignmentDecision] = []
        for item in allocation.assignments:
            output.append(
                TaskAssignmentDecision(
                    task_id=item.task_id,
                    task_title=item.task_title,
                    assigned_employee_id=item.employee_id,
                    assigned_employee_name=item.employee_name,
                    team=item.team,
                    assignment_score=item.assignment_score,
                    confidence=item.confidence,
                    skill_match_score=item.skill_match_score,
                    utilization_after=item.capacity_after_assignment,
                    delivery_success_probability=item.delivery_success_probability,
                    workflow_status="in_progress" if item.delivery_success_probability >= 70 else "queued",
                    rationale=item.rationale,
                    alternatives=item.alternatives,
                    source_systems=["resource_allocation_optimizer", "task_assignment_engine", "skill_matching_engine"],
                )
            )
        return output

    def _approval_decisions(
        self,
        requests: list[WorkflowApprovalRequest],
        employees: list[ResourceEmployeeProfile],
        allocation,
    ) -> list[ApprovalDecision]:
        employees_by_id = {employee.employee_id: employee for employee in employees}
        balance_by_id = {item.employee_id: item for item in allocation.workload_balance}
        average_utilization = mean([item.optimized_utilization for item in allocation.workload_balance]) if allocation.workload_balance else 82
        output: list[ApprovalDecision] = []
        for request in requests:
            employee = employees_by_id.get(request.requester_id)
            balance = balance_by_id.get(request.requester_id)
            utilization = balance.optimized_utilization if balance else average_utilization
            burnout = (employee.burnout_risk * 100 if employee else 35) + max(0, utilization - 96) * 0.7
            policy_score = self._policy_score(request, utilization, burnout)
            risk_score = self._approval_risk(request, utilization, burnout)
            capacity_impact = self._capacity_impact(request, utilization, average_utilization)
            decision = self._approval_decision_value(request, policy_score, risk_score, capacity_impact, burnout)
            output.append(
                ApprovalDecision(
                    request_id=request.request_id,
                    request_type=request.request_type,
                    requester_name=request.requester_name,
                    decision=decision,
                    confidence=round(min(0.95, 0.58 + abs(policy_score - risk_score) / 180 + request.business_impact * 0.12), 3),
                    policy_score=round(policy_score, 2),
                    capacity_impact=round(capacity_impact, 2),
                    risk_score=round(risk_score, 2),
                    workflow_status="approved" if decision == "approved" else "rejected" if decision == "rejected" else "escalated",
                    rationale=self._approval_rationale(request, decision, utilization, burnout, policy_score, risk_score),
                    next_steps=self._approval_next_steps(request, decision),
                    source_systems=["approval_engine", "policy_engine", "capacity_forecasting", "workload_balancing_engine"],
                )
            )
        return sorted(output, key=lambda item: (item.decision == "needs_review", item.risk_score), reverse=True)

    def _meeting_schedules(self, requests: list[WorkflowMeetingRequest]) -> list[MeetingScheduleDecision]:
        output: list[MeetingScheduleDecision] = []
        for request in requests:
            windows = request.preferred_windows or ["Tue 10:00", "Tue 15:00", "Wed 11:00", "Thu 14:00"]
            attendees = list(dict.fromkeys([*request.required_attendees, *request.optional_attendees]))
            best_window = windows[0]
            best_available = -1
            for window in windows:
                available = sum(1 for attendee in request.required_attendees if window in request.attendee_availability.get(attendee, windows))
                if available > best_available:
                    best_available = available
                    best_window = window
            required_count = max(len(request.required_attendees), 1)
            conflict_score = self._clip((required_count - best_available) / required_count * 100)
            priority_score = self._priority_score(request.priority) - conflict_score * 0.25 + max(0, 72 - request.deadline_hours) * 0.08
            output.append(
                MeetingScheduleDecision(
                    meeting_id=request.meeting_id,
                    title=request.title,
                    scheduled_time=best_window,
                    duration_minutes=request.duration_minutes,
                    attendees=attendees,
                    conflict_score=round(conflict_score, 2),
                    priority_score=round(self._clip(priority_score), 2),
                    workflow_status="scheduled" if conflict_score <= 40 else "queued",
                    rationale=(
                        f"{best_window} maximizes required attendee availability at {best_available}/{required_count} "
                        f"and preserves the {request.priority} priority SLA."
                    ),
                    source_systems=["scheduling_engine", "calendar_availability_optimizer", "notification_engine"],
                )
            )
        return sorted(output, key=lambda item: item.priority_score, reverse=True)

    def _workload_actions(self, tasks: list[ResourceTaskProfile], allocation) -> list[WorkloadBalanceAction]:
        overloaded = [item for item in allocation.workload_balance if item.optimized_utilization >= 96 or item.overload_risk >= 50]
        receivers = [item for item in allocation.workload_balance if item.optimized_utilization <= 98 or item.current_utilization <= 75]
        output: list[WorkloadBalanceAction] = []
        for index, source in enumerate(overloaded[:4]):
            if not receivers:
                break
            receiver_candidates = [
                item for item in receivers if item.name != source.name and item.optimized_utilization < source.optimized_utilization
            ]
            if not receiver_candidates:
                continue
            receiver = min(receiver_candidates, key=lambda item: item.optimized_utilization)
            candidate = next(
                (assignment for assignment in allocation.assignments if assignment.employee_name == source.name and assignment.delay_risk < 55),
                allocation.assignments[index % len(allocation.assignments)] if allocation.assignments else None,
            )
            if candidate is None:
                continue
            task = next((item for item in tasks if item.task_id == candidate.task_id), None)
            hours = round((task.effort_hours if task else 8) * 0.45, 1)
            utilization_delta = round(min(source.optimized_utilization - receiver.optimized_utilization, hours * 1.8), 2)
            burnout_reduction = round(self._clip(source.overload_risk * 0.18 + utilization_delta * 0.12), 2)
            output.append(
                WorkloadBalanceAction(
                    action_id=self._id("workload", source.employee_id, receiver.employee_id, candidate.task_id),
                    from_employee=source.name,
                    to_employee=receiver.name,
                    task_title=candidate.task_title,
                    hours=hours,
                    utilization_delta=utilization_delta,
                    burnout_risk_reduction=burnout_reduction,
                    status="in_progress",
                    rationale=(
                        f"Move {hours:g}h from {source.name} ({round(source.optimized_utilization)}% utilization) "
                        f"to {receiver.name} ({round(receiver.optimized_utilization)}%) to reduce overload propagation."
                    ),
                    source_systems=["workload_balancing_engine", "resource_allocation_optimizer", "burnout_safety_model"],
                )
            )
        if not output and allocation.workload_balance and receivers and tasks:
            source = max(allocation.workload_balance, key=lambda item: (item.current_utilization, item.overload_risk))
            receiver = min(receivers, key=lambda item: item.optimized_utilization)
            task = max(tasks, key=lambda item: (item.priority, item.effort_hours, item.cognitive_load))
            hours = round(min(10, max(3, task.effort_hours * 0.4)), 1)
            utilization_delta = round(max(4, min(source.current_utilization - receiver.optimized_utilization, hours * 1.8)), 2)
            burnout_reduction = round(self._clip(source.overload_risk * 0.16 + utilization_delta * 0.18 + task.cognitive_load * 6), 2)
            output.append(
                WorkloadBalanceAction(
                    action_id=self._id("workload", source.employee_id, receiver.employee_id, task.task_id, "standby"),
                    from_employee=source.name,
                    to_employee=receiver.name,
                    task_title=f"{task.title} standby load",
                    hours=hours,
                    utilization_delta=utilization_delta,
                    burnout_risk_reduction=burnout_reduction,
                    status="in_progress",
                    rationale=(
                        f"Shift {hours:g}h of standby and review work from {source.name} ({round(source.current_utilization)}% current utilization) "
                        f"to {receiver.name} ({round(receiver.optimized_utilization)}% optimized utilization) to preserve incident-lead recovery capacity."
                    ),
                    source_systems=["workload_balancing_engine", "capacity_monitor", "burnout_safety_model"],
                )
            )
        if not output and allocation.workload_balance:
            top = allocation.workload_balance[0]
            output.append(
                WorkloadBalanceAction(
                    action_id=self._id("workload", top.employee_id, "capacity-protection"),
                    from_employee=top.name,
                    to_employee="Operations buffer",
                    task_title="Capacity guardrail",
                    hours=0,
                    utilization_delta=0,
                    burnout_risk_reduction=round(self._clip(top.overload_risk * 0.08), 2),
                    status="queued",
                    rationale=f"{top.name} is monitored as the highest workload-risk owner; no reassignment is required until utilization rises.",
                    source_systems=["workload_balancing_engine", "capacity_monitor"],
                )
            )
        return output

    def _automation_events(self, request: AutonomousWorkflowRequest, allocation, alerts, approvals: list[ApprovalDecision]) -> list[WorkflowAutomationEvent]:
        events: list[WorkflowAutomationEvent] = []
        top_overload = max(allocation.workload_balance, key=lambda item: item.overload_risk, default=None)
        if top_overload and top_overload.overload_risk >= 45:
            events.append(
                self._event(
                    "high_burnout_risk",
                    f"{top_overload.name} overload risk reached {round(top_overload.overload_risk)}%.",
                    "Trigger workload redistribution and manager wellness review.",
                    [top_overload.name],
                    "critical" if top_overload.overload_risk >= 75 else "high",
                    top_overload.overload_risk / 100,
                    "workload_balancing_engine",
                )
            )
        for risk in allocation.risk_alerts[:3]:
            events.append(
                self._event(
                    risk.title.lower().replace(" ", "_"),
                    f"{risk.title}: {round(risk.probability)}% probability.",
                    risk.intervention,
                    risk.affected_entities,
                    risk.severity,
                    risk.probability / 100,
                    "resource_allocation_optimizer",
                )
            )
        for approval in approvals:
            if approval.decision == "needs_review":
                events.append(
                    self._event(
                        f"{approval.request_type}_approval_review",
                        f"{approval.requester_name} {approval.request_type} request exceeded automation confidence.",
                        "Route to responsible executive with policy and capacity evidence.",
                        [approval.requester_name],
                        "high",
                        approval.confidence,
                        "approval_engine",
                    )
                )
        if request.completed_task_ids:
            events.append(
                self._event(
                    "task_completed",
                    f"{len(request.completed_task_ids)} task(s) completed.",
                    "Notify project owner and update sprint progress forecast.",
                    request.completed_task_ids,
                    "medium",
                    0.86,
                    "workflow_engine",
                )
            )
        security_alert = next((item for item in alerts.alerts if item.category == "security"), None)
        if security_alert:
            events.append(
                self._event(
                    "security_incident",
                    security_alert.title,
                    security_alert.recommendation,
                    security_alert.evidence[:3],
                    "critical",
                    security_alert.confidence,
                    "alert_correlator",
                )
            )
        return events[:10]

    def _agent_actions(
        self,
        assignments: list[TaskAssignmentDecision],
        approvals: list[ApprovalDecision],
        meetings: list[MeetingScheduleDecision],
        workload: list[WorkloadBalanceAction],
        events: list[WorkflowAutomationEvent],
        alerts,
        suggestions,
    ) -> list[AgentWorkflowAction]:
        top_assignment = assignments[0] if assignments else None
        pending_approval = next((item for item in approvals if item.decision == "needs_review"), approvals[0] if approvals else None)
        critical_alert = alerts.alerts[0] if alerts.alerts else None
        suggestion = suggestions.suggestions[0] if suggestions.suggestions else None
        return [
            AgentWorkflowAction(
                agent="HR Agent",
                observation=pending_approval.rationale if pending_approval else "No HR policy exceptions detected.",
                action=pending_approval.next_steps[0] if pending_approval and pending_approval.next_steps else "Keep wellness and approval policy monitoring active.",
                shared_context_keys=["approval_decisions", "workload_risk", "employee_capacity"],
                triggered_workflows=[pending_approval.request_id] if pending_approval else [],
                confidence=pending_approval.confidence if pending_approval else 0.78,
            ),
            AgentWorkflowAction(
                agent="Project Agent",
                observation=top_assignment.rationale if top_assignment else "No unassigned critical task detected.",
                action=f"Commit owner for {top_assignment.task_title}." if top_assignment else "Monitor project backlog for new critical tasks.",
                shared_context_keys=["task_assignments", "capacity_forecast", "delivery_risk"],
                triggered_workflows=[top_assignment.task_id] if top_assignment else [],
                confidence=top_assignment.confidence if top_assignment else 0.76,
            ),
            AgentWorkflowAction(
                agent="Productivity Agent",
                observation=suggestion.rationale if suggestion else "No productivity intervention exceeded threshold.",
                action=suggestion.action if suggestion else "Maintain current focus-time guardrails.",
                shared_context_keys=["smart_suggestions", "workload_balancing", "meeting_schedules"],
                triggered_workflows=[workload[0].action_id] if workload else [],
                confidence=suggestion.confidence if suggestion else 0.77,
            ),
            AgentWorkflowAction(
                agent="Security Agent",
                observation=critical_alert.message if critical_alert else "Security workflow remains within normal bounds.",
                action=critical_alert.recommendation if critical_alert else "Continue adaptive security monitoring.",
                shared_context_keys=["alerts", "access_approvals", "security_events"],
                triggered_workflows=[event.event_id for event in events if event.trigger == "security_incident"],
                confidence=critical_alert.confidence if critical_alert else 0.8,
            ),
            AgentWorkflowAction(
                agent="Executive Agent",
                observation=f"{len(events)} automation event(s), {len(meetings)} meeting(s), and {len(workload)} workload action(s) require operating review.",
                action="Prioritize escalations, approve high-confidence automation, and hold capacity review for open risks.",
                shared_context_keys=["automation_events", "escalations", "operations_recommendations"],
                triggered_workflows=[event.event_id for event in events[:4]],
                confidence=0.88,
            ),
        ]

    def _escalations(self, allocation, alerts, approvals: list[ApprovalDecision], events: list[WorkflowAutomationEvent]) -> list[EscalationEvent]:
        output: list[EscalationEvent] = []
        for event in events:
            if event.severity in {"high", "critical"}:
                output.append(
                    EscalationEvent(
                        escalation_id=self._id("escalation", event.event_id),
                        category=event.trigger,
                        title=f"Escalate {event.trigger.replace('_', ' ')}",
                        severity=event.severity,
                        owner="Operations Director" if event.severity == "high" else "Executive Sponsor",
                        routing=["Project Director", "HR Business Partner"] if "burnout" in event.trigger or "workload" in event.trigger else ["Security Lead", "COO"] if "security" in event.trigger else ["Program Lead", "COO"],
                        rationale=event.condition,
                        sla_hours=4 if event.severity == "critical" else 24,
                        status="escalated",
                    )
                )
        for approval in approvals:
            if approval.decision == "needs_review":
                output.append(
                    EscalationEvent(
                        escalation_id=self._id("escalation", approval.request_id),
                        category="approval",
                        title=f"Approval review for {approval.requester_name}",
                        severity="high" if approval.risk_score >= 62 else "medium",
                        owner="Operations Director",
                        routing=["Finance", "HR", "Line Manager"] if approval.request_type in {"budget", "leave"} else ["Security Lead", "System Owner"],
                        rationale=approval.rationale,
                        sla_hours=12,
                        status="escalated",
                    )
                )
        return output[:8]

    def _reminders(
        self,
        assignments: list[TaskAssignmentDecision],
        approvals: list[ApprovalDecision],
        meetings: list[MeetingScheduleDecision],
        escalations: list[EscalationEvent],
        request: AutonomousWorkflowRequest,
    ) -> list[ReminderEvent]:
        tasks_by_id = {task.task_id: task for task in request.tasks}
        reminders: list[ReminderEvent] = []
        for assignment in assignments[:5]:
            task = tasks_by_id.get(assignment.task_id)
            due_hours = int(max(6, (task.deadline_days if task else 5) * 24 - 12))
            urgency = "critical" if due_hours <= 36 else "high" if due_hours <= 96 else "medium"
            reminders.append(
                ReminderEvent(
                    reminder_id=self._id("reminder", assignment.task_id, assignment.assigned_employee_id),
                    title=f"{assignment.task_title} owner checkpoint",
                    recipient=assignment.assigned_employee_name,
                    due_in_hours=due_hours,
                    urgency=urgency,
                    channel="Slack + email",
                    message=f"Confirm blockers and progress for {assignment.task_title} before the next sprint checkpoint.",
                    source_workflow=assignment.task_id,
                )
            )
        for approval in approvals:
            if approval.decision == "needs_review":
                reminders.append(
                    ReminderEvent(
                        reminder_id=self._id("reminder", approval.request_id),
                        title=f"{approval.request_type.title()} approval needs review",
                        recipient="Operations Director",
                        due_in_hours=8,
                        urgency="high",
                        channel="Workflow inbox",
                        message=f"Review {approval.requester_name}'s request with policy score {round(approval.policy_score)} and risk {round(approval.risk_score)}.",
                        source_workflow=approval.request_id,
                    )
                )
        for meeting in meetings[:3]:
            reminders.append(
                ReminderEvent(
                    reminder_id=self._id("reminder", meeting.meeting_id),
                    title=f"{meeting.title} agenda reminder",
                    recipient=", ".join(meeting.attendees[:3]),
                    due_in_hours=24,
                    urgency="medium" if meeting.priority_score < 78 else "high",
                    channel="Calendar",
                    message=f"Send agenda and decision owner list before {meeting.scheduled_time}.",
                    source_workflow=meeting.meeting_id,
                )
            )
        for escalation in escalations[:3]:
            reminders.append(
                ReminderEvent(
                    reminder_id=self._id("reminder", escalation.escalation_id),
                    title=escalation.title,
                    recipient=escalation.owner,
                    due_in_hours=escalation.sla_hours,
                    urgency=escalation.severity,
                    channel="Executive escalation queue",
                    message=f"Resolve or update escalation within {escalation.sla_hours} hours.",
                    source_workflow=escalation.escalation_id,
                )
            )
        return reminders[:14]

    def _recommendations(self, assignments, approvals, workload, escalations, suggestions, recommendations_context) -> list[OperationsRecommendation]:
        output: list[OperationsRecommendation] = []
        if assignments:
            best = assignments[0]
            output.append(
                OperationsRecommendation(
                    title="Commit AI task assignment",
                    category="task_assignment",
                    priority="high" if best.delivery_success_probability < 78 else "medium",
                    action=f"Assign {best.task_title} to {best.assigned_employee_name} and track delivery confidence daily.",
                    rationale=best.rationale,
                    expected_impact=f"{round(best.delivery_success_probability)}% delivery success probability.",
                    confidence=best.confidence,
                )
            )
        if workload:
            action = workload[0]
            output.append(
                OperationsRecommendation(
                    title="Balance workload before overload compounds",
                    category="workload_balancing",
                    priority="high",
                    action=f"Move {action.hours:g}h from {action.from_employee} to {action.to_employee}.",
                    rationale=action.rationale,
                    expected_impact=f"{round(action.burnout_risk_reduction, 1)} point burnout-risk reduction.",
                    confidence=0.84,
                )
            )
        review = next((item for item in approvals if item.decision == "needs_review"), None)
        if review:
            output.append(
                OperationsRecommendation(
                    title="Clear pending approval exception",
                    category="approval",
                    priority="high",
                    action=review.next_steps[0] if review.next_steps else "Route approval exception to Operations Director.",
                    rationale=review.rationale,
                    expected_impact="Avoids policy drift while keeping operations moving.",
                    confidence=review.confidence,
                )
            )
        if escalations:
            output.append(
                OperationsRecommendation(
                    title="Resolve critical escalations",
                    category="escalation",
                    priority=escalations[0].severity,
                    action=f"Route {escalations[0].title} to {', '.join(escalations[0].routing)}.",
                    rationale=escalations[0].rationale,
                    expected_impact=f"SLA {escalations[0].sla_hours}h for executive action.",
                    confidence=0.87,
                )
            )
        for suggestion in suggestions.suggestions[:2]:
            output.append(
                OperationsRecommendation(
                    title=suggestion.title,
                    category=suggestion.category,
                    priority=suggestion.priority,
                    action=suggestion.action,
                    rationale=suggestion.rationale,
                    expected_impact=suggestion.estimated_gain,
                    confidence=suggestion.confidence,
                )
            )
        for recommendation in recommendations_context.recommendations[:2]:
            output.append(
                OperationsRecommendation(
                    title=recommendation.title,
                    category=recommendation.category,
                    priority=recommendation.priority,
                    action=recommendation.action,
                    rationale=recommendation.rationale,
                    expected_impact=f"{round(recommendation.impact_score)} impact score.",
                    confidence=recommendation.confidence,
                )
            )
        return output[:8]

    def _summary(self, assignments, approvals, meetings, reminders, workload, events, escalations) -> WorkflowSummary:
        average_confidence = mean([item.confidence for item in assignments]) if assignments else 0
        automated = sum(1 for item in approvals if item.decision in {"approved", "rejected"})
        policy_rate = automated / max(len(approvals), 1) * 100
        risk_pressure = len(escalations) * 4.8 + len([event for event in events if event.severity == "critical"]) * 5.5
        readiness = self._clip(92 - risk_pressure + average_confidence * 8 + policy_rate * 0.04)
        return WorkflowSummary(
            active_workflows=len(assignments) + len(workload) + len(events),
            pending_approvals=sum(1 for item in approvals if item.decision == "needs_review"),
            scheduled_meetings=sum(1 for item in meetings if item.workflow_status == "scheduled"),
            reminders_created=len(reminders),
            escalations_open=len(escalations),
            automation_events=len(events),
            workload_balance_actions=len(workload),
            operations_readiness_score=round(readiness, 2),
            average_assignment_confidence=round(average_confidence, 3),
            policy_automation_rate=round(policy_rate, 2),
        )

    def _assistant_answer(self, intent: str, workflow: AutonomousWorkflowResponse) -> tuple[str, list[str], list[str]]:
        if intent == "assignment" and workflow.task_assignments:
            top = workflow.task_assignments[0]
            return (
                f"Assign {top.task_title} to {top.assigned_employee_name}. The optimizer scored the match at {top.assignment_score}% with {top.skill_match_score}% skill fit and {top.delivery_success_probability}% delivery probability.",
                [f"assign:{top.task_id}:{top.assigned_employee_id}"],
                [top.task_id],
            )
        if intent == "schedule" and workflow.meeting_schedules:
            meeting = workflow.meeting_schedules[0]
            return (
                f"Schedule {meeting.title} at {meeting.scheduled_time}. Conflict score is {meeting.conflict_score}% and priority score is {meeting.priority_score}%.",
                [f"schedule:{meeting.meeting_id}:{meeting.scheduled_time}"],
                [meeting.meeting_id],
            )
        if intent == "approval" and workflow.approval_decisions:
            approval = workflow.approval_decisions[0]
            return (
                f"{approval.requester_name}'s {approval.request_type} request is {approval.decision}. Policy score is {approval.policy_score}% and risk score is {approval.risk_score}%.",
                [f"approval:{approval.request_id}:{approval.decision}"],
                [approval.request_id],
            )
        if intent == "overload" and workflow.workload_balancing:
            action = workflow.workload_balancing[0]
            return (
                f"{action.from_employee} is the primary workload concern. Move {action.hours:g}h of {action.task_title} to {action.to_employee}; expected burnout-risk reduction is {action.burnout_risk_reduction} points.",
                [f"rebalance:{action.action_id}"],
                [action.action_id],
            )
        if intent == "escalation" and workflow.escalations:
            escalation = workflow.escalations[0]
            return (
                f"Escalate {escalation.title} to {escalation.owner} with SLA {escalation.sla_hours}h. Routing: {', '.join(escalation.routing)}.",
                [f"escalate:{escalation.escalation_id}"],
                [escalation.escalation_id],
            )
        recommendation = workflow.recommendations[0]
        return (
            f"Recommended action: {recommendation.action} Expected impact: {recommendation.expected_impact}",
            [f"recommend:{recommendation.category}"],
            [recommendation.title],
        )

    @staticmethod
    def _intent(question: str) -> str:
        if any(token in question for token in ["assign", "who should work", "owner", "task"]):
            return "assignment"
        if any(token in question for token in ["schedule", "meeting", "calendar", "review"]):
            return "schedule"
        if any(token in question for token in ["approve", "approval", "leave", "budget", "access"]):
            return "approval"
        if any(token in question for token in ["overload", "workload", "balance", "redistribute"]):
            return "overload"
        if any(token in question for token in ["escalate", "critical", "risk"]):
            return "escalation"
        return "recommendation"

    @staticmethod
    def default_request() -> AutonomousWorkflowRequest:
        resource = resource_allocation_service.default_request()
        approval_requests = [
            WorkflowApprovalRequest(
                request_id="approval-leave-john",
                request_type="leave",
                requester_id="res-risk",
                requester_name="John Rivera",
                team="Platform",
                days=2,
                business_impact=0.74,
                urgency="high",
                justification="Recovery leave after sustained incident escalation and weekend overtime.",
            ),
            WorkflowApprovalRequest(
                request_id="approval-budget-k8s",
                request_type="budget",
                requester_id="res-devops",
                requester_name="Bianca Shah",
                team="Platform",
                amount=42_000,
                policy_limit=50_000,
                business_impact=0.86,
                urgency="high",
                justification="Deployment guardrail automation for Kubernetes rollout safety.",
            ),
            WorkflowApprovalRequest(
                request_id="approval-access-incident",
                request_type="access",
                requester_id="res-backend",
                requester_name="Aarav Mehta",
                team="Platform",
                requested_access_level="temporary-production-read",
                business_impact=0.68,
                urgency="medium",
                justification="Need temporary production-read access to verify API resilience metrics.",
            ),
        ]
        availability = {
            "Aarav Mehta": ["Tue 15:00", "Wed 11:00", "Thu 14:00"],
            "Bianca Shah": ["Tue 10:00", "Tue 15:00", "Thu 14:00"],
            "Devika Nair": ["Tue 15:00", "Wed 11:00", "Thu 14:00"],
            "Maya Iyer": ["Tue 10:00", "Wed 11:00", "Thu 14:00"],
            "John Rivera": ["Wed 11:00", "Thu 14:00"],
        }
        meeting_requests = [
            WorkflowMeetingRequest(
                meeting_id="meeting-reliability-review",
                title="Reliability recovery review",
                purpose="Clear blockers for API resilience and rollout guardrails.",
                required_attendees=["Aarav Mehta", "Bianca Shah", "Maya Iyer", "John Rivera"],
                optional_attendees=["Devika Nair"],
                duration_minutes=45,
                priority="high",
                preferred_windows=["Tue 10:00", "Tue 15:00", "Wed 11:00", "Thu 14:00"],
                attendee_availability=availability,
                deadline_hours=48,
            ),
            WorkflowMeetingRequest(
                meeting_id="meeting-exec-capacity",
                title="Executive capacity risk review",
                purpose="Approve workload redistribution and policy exceptions.",
                required_attendees=["John Rivera", "Bianca Shah", "Devika Nair"],
                optional_attendees=["Nina Kapoor"],
                duration_minutes=30,
                priority="critical",
                preferred_windows=["Tue 15:00", "Wed 11:00", "Thu 14:00"],
                attendee_availability=availability,
                deadline_hours=24,
            ),
        ]
        return AutonomousWorkflowRequest(
            mode="default",
            department=resource.department,
            sprint_name=resource.sprint_name,
            planning_horizon_days=resource.planning_horizon_days,
            employees=resource.employees,
            tasks=resource.tasks,
            dependencies=resource.dependencies,
            approval_requests=approval_requests,
            meeting_requests=meeting_requests,
            completed_task_ids=["task-observability"],
        )

    def _pressure_variant(self, base: AutonomousWorkflowRequest, mode: str, workload_delta: float, urgency_delta: float) -> AutonomousWorkflowRequest:
        normalized = self._normalize_request(base)
        employees = [
            employee.model_copy(
                update={
                    "current_hours": min(120, employee.current_hours + workload_delta * (1.35 if employee.burnout_risk >= 0.5 else 0.7)),
                    "burnout_risk": min(1, employee.burnout_risk + urgency_delta * (1.1 if employee.current_hours >= employee.capacity_hours else 0.55)),
                    "stress_score": min(1, employee.stress_score + urgency_delta * 0.72),
                    "availability": max(0.45, employee.availability - urgency_delta * 0.16),
                }
            )
            for employee in normalized.employees
        ]
        tasks = [
            task.model_copy(
                update={
                    "deadline_days": max(1, task.deadline_days * (1 - urgency_delta)),
                    "complexity": min(1, task.complexity + urgency_delta * 0.12),
                    "cognitive_load": min(1, task.cognitive_load + urgency_delta * 0.1),
                }
            )
            for task in normalized.tasks
        ]
        approvals = [
            approval.model_copy(
                update={
                    "amount": approval.amount * (1 + urgency_delta if approval.amount else 0),
                    "business_impact": min(1, approval.business_impact + urgency_delta * 0.18),
                    "urgency": "critical" if mode == "crisis" and approval.urgency == "high" else approval.urgency,
                }
            )
            for approval in normalized.approval_requests
        ]
        return normalized.model_copy(update={"mode": mode, "employees": employees, "tasks": tasks, "approval_requests": approvals})

    def _policy_score(self, request: WorkflowApprovalRequest, utilization: float, burnout: float) -> float:
        if request.request_type == "leave":
            recovery_need = min(100, burnout + max(0, utilization - 86) * 0.5)
            team_capacity = max(0, 100 - max(0, utilization - 82) * 0.8)
            return self._clip(recovery_need * 0.62 + team_capacity * 0.26 + request.business_impact * 12)
        if request.request_type in {"budget", "purchase"}:
            budget_fit = 100 if request.amount <= request.policy_limit else max(0, 100 - (request.amount - request.policy_limit) / max(request.policy_limit, 1) * 80)
            return self._clip(budget_fit * 0.64 + request.business_impact * 36)
        if request.request_type == "access":
            limited = "read" in request.requested_access_level or "temporary" in request.requested_access_level
            return self._clip((78 if limited else 42) + request.business_impact * 18 - max(0, utilization - 100) * 0.25)
        if request.request_type == "training":
            return self._clip(62 + request.business_impact * 28 - max(0, utilization - 96) * 0.3)
        return 55

    def _approval_risk(self, request: WorkflowApprovalRequest, utilization: float, burnout: float) -> float:
        if request.request_type == "leave":
            return self._clip(max(0, utilization - 92) * 0.75 + request.days * 3.2 - burnout * 0.22)
        if request.request_type in {"budget", "purchase"}:
            overage = max(0, request.amount - request.policy_limit) / max(request.policy_limit, 1) * 100
            return self._clip(overage * 0.7 + (1 - request.business_impact) * 35)
        if request.request_type == "access":
            admin_risk = 52 if "admin" in request.requested_access_level.lower() else 18
            return self._clip(admin_risk + max(0, utilization - 102) * 0.3)
        return self._clip(28 + max(0, utilization - 104) * 0.35)

    @staticmethod
    def _capacity_impact(request: WorkflowApprovalRequest, utilization: float, average_utilization: float) -> float:
        if request.request_type == "leave":
            return min(100, request.days * 7 + max(0, average_utilization - 86) * 0.8)
        if request.request_type in {"budget", "purchase"}:
            return max(0, 38 - request.business_impact * 22)
        if request.request_type == "training":
            return min(100, 22 + max(0, utilization - 88) * 0.35)
        return min(100, 18 + max(0, utilization - 92) * 0.2)

    @staticmethod
    def _approval_decision_value(request: WorkflowApprovalRequest, policy_score: float, risk_score: float, capacity_impact: float, burnout: float) -> str:
        if request.request_type == "leave" and burnout >= 72 and capacity_impact <= 62:
            return "approved"
        if policy_score >= 68 and risk_score <= 48 and capacity_impact <= 68:
            return "approved"
        if request.request_type == "access" and risk_score >= 62:
            return "rejected"
        if policy_score < 42 and risk_score >= 68:
            return "rejected"
        return "needs_review"

    @staticmethod
    def _approval_rationale(request: WorkflowApprovalRequest, decision: str, utilization: float, burnout: float, policy_score: float, risk_score: float) -> str:
        return (
            f"{request.request_type.title()} request {decision}: policy score {round(policy_score)}%, risk score {round(risk_score)}%, "
            f"requester utilization {round(utilization)}%, burnout pressure {round(burnout)}%, and business impact {round(request.business_impact * 100)}%."
        )

    @staticmethod
    def _approval_next_steps(request: WorkflowApprovalRequest, decision: str) -> list[str]:
        if decision == "approved":
            if request.request_type == "leave":
                return ["Notify manager, update capacity plan, and rebalance committed tasks."]
            if request.request_type in {"budget", "purchase"}:
                return ["Create purchase workflow and attach budget-impact evidence."]
            if request.request_type == "access":
                return ["Grant least-privilege temporary access with expiry and audit logging."]
            return ["Approve request and track expected business outcome."]
        if decision == "rejected":
            return ["Send decision with risk rationale and offer a lower-risk alternative."]
        return ["Route to Operations Director with policy, capacity, and risk evidence."]

    def _event(self, trigger: str, condition: str, action: str, entities: list[str], severity: str, confidence: float, source: str) -> WorkflowAutomationEvent:
        return WorkflowAutomationEvent(
            event_id=self._id("event", trigger, condition),
            trigger=trigger,
            condition=condition,
            action=action,
            affected_entities=entities,
            severity=severity,
            confidence=round(min(0.98, max(0.52, confidence)), 3),
            workflow_status="escalated" if severity in {"high", "critical"} else "in_progress",
            source_systems=["automation_engine", "workflow_rules_engine", source],
        )

    @staticmethod
    def _priority_score(priority: str) -> float:
        return {"low": 42, "medium": 62, "high": 80, "critical": 94}.get(priority, 62)

    @staticmethod
    def _clip(value: float, low: float = 0, high: float = 100) -> float:
        return float(max(low, min(high, value)))

    @staticmethod
    def _id(*parts: str) -> str:
        return f"wf-{uuid5(NAMESPACE_DNS, ':'.join(str(part) for part in parts)).hex[:12]}"

    def _append_jsonl(self, payload: dict[str, object]) -> None:
        with self._lock:
            with HISTORY_PATH.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, default=str) + "\n")


autonomous_workflow_service = AutonomousWorkflowService()
