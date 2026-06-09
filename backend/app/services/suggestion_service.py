from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from uuid import NAMESPACE_DNS, uuid5

from app.core.cache import TTLResponseCache
from app.ai.burnout_model import BurnoutFeatures
from app.ai.employee_analytics_engine import employee_analytics_engine
from app.ai.enterprise_models import enterprise_model_registry
from app.ai.recommendation_engine import recommendation_engine
from app.schemas.employee_dashboard import EmployeeActivityPoint
from app.schemas.forecasting import ForecastRequest
from app.schemas.manager_dashboard import EmployeeWorkloadInput, ManagerDashboardRequest, ProjectDeliveryInput, TeamAnalyticsInput
from app.schemas.nlp import NLPAnalyzeRequest, NLPBatchRequest
from app.schemas.recommendations import EmployeeProfile, RecommendationRequest, TaskProfile
from app.schemas.suggestions import (
    SmartSuggestion,
    SmartSuggestionFeedbackRequest,
    SmartSuggestionFeedbackResponse,
    SmartSuggestionRequest,
    SmartSuggestionResponse,
    SmartSuggestionSummary,
)
from app.services.employee_dashboard_service import employee_dashboard_service
from app.services.forecasting_service import forecasting_service
from app.services.manager_dashboard_service import manager_dashboard_service
from app.services.nlp_service import nlp_service
from app.services.recommendation_service import recommendation_service


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
HISTORY_PATH = DATA_DIR / "smart_suggestion_history.jsonl"
FEEDBACK_PATH = DATA_DIR / "smart_suggestion_feedback.jsonl"


@dataclass(frozen=True)
class SuggestionScore:
    value: float
    drivers: list[str]
    trend_delta: float = 0


@dataclass(frozen=True)
class EmployeeSuggestionInsight:
    employee_id: str
    employee_name: str
    model: str
    stress: SuggestionScore
    productivity: SuggestionScore
    burnout_probability: SuggestionScore


@dataclass(frozen=True)
class SuggestionRecommendation:
    category: str
    title: str
    action: str
    rationale: str
    confidence: float
    impact_score: float
    affected_employees: list[str]


@dataclass(frozen=True)
class SuggestionRecommendationContext:
    model: str
    team_balance_score: float
    recommendations: list[SuggestionRecommendation]


class SmartSuggestionService:
    model_name = "Smart Decision Intelligence Engine"

    def __init__(self) -> None:
        self._default_cache: TTLResponseCache[SmartSuggestionResponse] = TTLResponseCache(ttl_seconds=8)

    def generate(self, payload: SmartSuggestionRequest | None = None) -> SmartSuggestionResponse:
        if payload is None:
            return self._default_cache.get_or_set(self._generate_uncached)
        return self._generate_uncached(payload)

    def _generate_uncached(self, payload: SmartSuggestionRequest | None = None) -> SmartSuggestionResponse:
        request = payload or SmartSuggestionRequest()
        now = datetime.now(timezone.utc)
        feedback_signal = self._feedback_signal()
        threshold = self._adaptive_threshold(request.sensitivity, feedback_signal)

        current_activity = self._employee_activity(request)
        employee = self._employee_insight(current_activity, "Employee X" if request.scenario == "default" else "Employee John")
        manager = manager_dashboard_service.analyze(self._manager_request(request))
        recommendations = self._recommendation_context(request, feedback_signal)
        nlp = nlp_service.batch(self._nlp_request(request))
        forecast = forecasting_service.forecast(ForecastRequest(department="Engineering", horizon_days=14))

        suggestions = [
            self._meeting_reduction(employee, current_activity, nlp, feedback_signal, request.feedback_weight, now),
            self._workload_redistribution(recommendations, manager, feedback_signal, request.feedback_weight, now),
            self._wellness_break(employee, recommendations, feedback_signal, request.feedback_weight, now),
            self._team_optimization(manager, recommendations, feedback_signal, request.feedback_weight, now),
            self._productivity_improvement(employee, forecast, nlp, feedback_signal, request.feedback_weight, now),
        ]
        suggestions = [suggestion for suggestion in suggestions if suggestion.impact_score >= threshold * 0.55]
        suggestions.sort(key=lambda item: (item.impact_score, item.confidence), reverse=True)
        feedback_states = self._feedback_states()
        for suggestion in suggestions:
            state = feedback_states.get(suggestion.suggestion_id)
            if state is not None:
                suggestion.feedback_state = "accepted" if state else "dismissed"

        response = SmartSuggestionResponse(
            model=self.model_name,
            generated_at=now,
            scenario=request.scenario,
            adaptive_threshold=threshold,
            suggestions=suggestions,
            summary=self._summary(suggestions),
            storage=str(HISTORY_PATH),
        )
        self._append_jsonl(HISTORY_PATH, response.model_dump(mode="json"))
        return response

    def record_feedback(self, payload: SmartSuggestionFeedbackRequest) -> SmartSuggestionFeedbackResponse:
        self._default_cache.clear()
        signal = payload.usefulness_score / 5 if payload.accepted else max(0.05, payload.usefulness_score / 12)
        record = {
            "suggestion_id": payload.suggestion_id,
            "accepted": payload.accepted,
            "usefulness_score": payload.usefulness_score,
            "notes": payload.notes,
            "learning_signal": round(signal, 3),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._append_jsonl(FEEDBACK_PATH, record)
        return SmartSuggestionFeedbackResponse(
            suggestion_id=payload.suggestion_id,
            learning_signal=round(signal, 3),
            message="Smart suggestion feedback captured for adaptive decision scoring.",
            storage=str(FEEDBACK_PATH),
        )

    async def stream(self, payload: SmartSuggestionRequest | None = None):
        request = payload or SmartSuggestionRequest()
        for sequence in range(3):
            current = request.model_copy(update={"sensitivity": min(1, request.sensitivity + sequence * 0.02)})
            response = self.generate(current)
            data = response.model_dump(mode="json")
            data["summary"]["stream_sequence"] = sequence + 1
            yield f"event: suggestions\ndata: {json.dumps(data)}\n\n"
            await asyncio.sleep(0.8)

    def _meeting_reduction(self, employee, activity: EmployeeActivityPoint, nlp, feedback_signal: float, feedback_weight: float, now: datetime) -> SmartSuggestion:
        meeting_pressure = min(activity.meeting_hours / 16, 1)
        focus_pressure = max(0, 5 - activity.focus_hours) / 5
        sentiment_pressure = max(0, -activity.sentiment_score)
        raw_score = (
            employee.stress.value * 0.36
            + meeting_pressure * 32
            + focus_pressure * 18
            + sentiment_pressure * 12
            + max(0, 72 - employee.productivity.value) * 0.3
        )
        impact = self._adapt(raw_score, feedback_signal, feedback_weight)
        reduction_percent = int(min(40, max(15, round((activity.meeting_hours - 6) / max(activity.meeting_hours, 1) * 100 + employee.stress.value / 12))))
        hours = round(activity.meeting_hours * reduction_percent / 100, 1)
        return self._suggestion(
            "meeting_reduction",
            f"Reduce meetings for {employee.employee_name} by {reduction_percent}%",
            f"Cut {hours:g}h of recurring meetings this week and convert status syncs into async updates.",
            (
                f"{employee.employee_name} has {activity.meeting_hours:g} meeting hours, {activity.focus_hours:g} focus hours, "
                f"stress {round(employee.stress.value)}/100, and team sentiment score {nlp.team_sentiment_score}."
            ),
            impact,
            min(0.94, 0.58 + meeting_pressure * 0.2 + employee.stress.value / 400 + abs(nlp.team_sentiment_score) * 0.08),
            f"{hours:g}h focus time recovered",
            24,
            [employee.employee_id],
            ["employee_dashboard", employee.model, "nlp_sentiment", "meeting_optimizer"],
            employee.stress.drivers + employee.productivity.drivers,
            now,
            f"meeting:{employee.employee_id}",
        )

    def _workload_redistribution(self, recommendations, manager, feedback_signal: float, feedback_weight: float, now: datetime) -> SmartSuggestion:
        source = next((item for item in recommendations.recommendations if item.category == "work_redistribution"), None)
        overloaded = manager.overloaded_employees[0] if manager.overloaded_employees else None
        base = source.impact_score if source else overloaded.overload_score if overloaded else 45
        impact = self._adapt(base + (overloaded.overload_score * 0.1 if overloaded else 0), feedback_signal, feedback_weight)
        affected = source.affected_employees if source else [overloaded.employee_id] if overloaded else []
        action = source.action if source else f"Reassign two high-load tasks away from {overloaded.employee_name}."
        rationale = source.rationale if source else overloaded.recommendation
        return self._suggestion(
            "workload_redistribution",
            source.title if source else f"Rebalance workload away from {overloaded.employee_name}",
            action,
            rationale,
            impact,
            source.confidence if source else 0.78,
            "6-10h overload removed",
            48,
            affected,
            ["recommendation_engine", recommendations.model, "manager_dashboard", manager.model],
            (overloaded.drivers if overloaded else []) + [f"team balance score {round(recommendations.team_balance_score)}"],
            now,
            "workload:redistribution",
        )

    def _wellness_break(self, employee, recommendations, feedback_signal: float, feedback_weight: float, now: datetime) -> SmartSuggestion:
        source = next((item for item in recommendations.recommendations if item.category == "break"), None)
        raw = max(employee.stress.value, employee.burnout_probability.value, source.impact_score if source else 0)
        impact = self._adapt(raw, feedback_signal, feedback_weight)
        hours_until = 2 if impact >= 78 else 4 if impact >= 58 else 8
        return self._suggestion(
            "wellness_break",
            f"Recovery break for {employee.employee_name} within {hours_until} hours",
            source.action if source else f"Schedule a recovery break for {employee.employee_name} and pause non-critical interrupts.",
            (
                f"Stress {round(employee.stress.value)}/100, burnout probability {round(employee.burnout_probability.value)}%, "
                f"and productivity trend delta {employee.productivity.trend_delta:+.1f} indicate fatigue accumulation."
            ),
            impact,
            source.confidence if source else 0.81,
            "burnout risk reduced 8-14%",
            hours_until,
            [employee.employee_id],
            ["employee_dashboard", employee.model, "recommendation_engine", "fatigue_threshold_model"],
            employee.burnout_probability.drivers + employee.stress.drivers,
            now,
            f"wellness:{employee.employee_id}",
        )

    def _team_optimization(self, manager, recommendations, feedback_signal: float, feedback_weight: float, now: datetime) -> SmartSuggestion:
        source = next((item for item in recommendations.recommendations if item.category == "team_balancing"), None)
        team = manager.risky_teams[0] if manager.risky_teams else None
        raw = max(source.impact_score if source else 0, team.risk_score if team else 0, 45)
        impact = self._adapt(raw, feedback_signal, feedback_weight)
        return self._suggestion(
            "team_optimization",
            source.title if source else f"Optimize {team.team_name} capacity",
            source.action if source else f"Move one delivery lane out of {team.team_name} and add a dependency owner.",
            source.rationale if source else f"{team.team_name} has {round(team.risk_score)}% risk with {', '.join(team.drivers[:3])}.",
            impact,
            source.confidence if source else 0.76,
            "team risk reduced 10-18%",
            72,
            source.affected_employees if source else [],
            ["manager_dashboard", manager.model, "recommendation_engine", recommendations.model],
            (team.drivers if team else []) + [f"team balance score {round(recommendations.team_balance_score)}"],
            now,
            "team:optimization",
        )

    def _productivity_improvement(self, employee, forecast, nlp, feedback_signal: float, feedback_weight: float, now: datetime) -> SmartSuggestion:
        productivity_gap = max(0, 82 - employee.productivity.value)
        future_drop = max(0, forecast.history[-1].productivity - forecast.forecast[0].productivity) if forecast.history and forecast.forecast else 0
        communication_drag = max(0, -nlp.team_sentiment_score) * 20
        raw = productivity_gap * 1.4 + future_drop * 1.8 + communication_drag + employee.stress.value * 0.22
        impact = self._adapt(raw, feedback_signal, feedback_weight)
        multitask_reduction = int(min(30, max(10, productivity_gap / 1.4 + employee.stress.value / 10)))
        return self._suggestion(
            "productivity_improvement",
            f"Reduce multitasking load by {multitask_reduction}%",
            "Create two protected focus blocks, defer low-priority context switches, and batch project updates.",
            (
                f"Productivity score is {round(employee.productivity.value)}/100, forecast confidence is {forecast.confidence}, "
                f"and communication sentiment is {nlp.team_sentiment_score}."
            ),
            impact,
            min(0.93, 0.6 + forecast.confidence * 0.15 + abs(nlp.team_sentiment_score) * 0.08 + employee.stress.value / 500),
            "focus efficiency improved 9-16%",
            36,
            [employee.employee_id],
            ["employee_dashboard", employee.model, "time_series_forecasting", forecast.model, "nlp_sentiment"],
            employee.productivity.drivers + [f"{signal.metric} trend {signal.direction}" for signal in forecast.trend_signals],
            now,
            f"productivity:{employee.employee_id}",
        )

    def _suggestion(
        self,
        category,
        title: str,
        action: str,
        rationale: str,
        impact_score: float,
        confidence: float,
        estimated_gain: str,
        time_to_impact_hours: int,
        affected_employees: list[str],
        source_systems: list[str],
        evidence: list[str],
        created_at: datetime,
        group_key: str,
    ) -> SmartSuggestion:
        impact = round(float(min(100, max(0, impact_score))), 2)
        return SmartSuggestion(
            suggestion_id=f"sugg-{uuid5(NAMESPACE_DNS, group_key).hex[:12]}",
            category=category,
            title=title,
            action=action,
            rationale=rationale,
            priority=self._priority(impact),
            confidence=round(float(min(0.98, max(0.45, confidence))), 3),
            impact_score=impact,
            estimated_gain=estimated_gain,
            time_to_impact_hours=time_to_impact_hours,
            affected_employees=affected_employees,
            source_systems=list(dict.fromkeys(source_systems)),
            evidence=list(dict.fromkeys(evidence))[:7],
            created_at=created_at,
        )

    @staticmethod
    def _employee_insight(activity: EmployeeActivityPoint, employee_name: str) -> EmployeeSuggestionInsight:
        prediction = employee_analytics_engine.predict(activity)
        probabilities = enterprise_model_registry.predict(
            BurnoutFeatures(
                overtime_hours=activity.overtime_hours,
                meeting_hours=activity.meeting_hours,
                sentiment_score=activity.sentiment_score,
                task_completion_ratio=activity.task_completion_ratio,
                absence_days=activity.absence_days,
            )
        )
        stress_pressure = prediction.stress_score / 100
        productivity_pressure = max(0, 78 - prediction.productivity_score) / 78
        burnout = round(min(98, (probabilities["ensemble"] * 0.72 + stress_pressure * 0.18 + productivity_pressure * 0.1) * 100), 2)
        return EmployeeSuggestionInsight(
            employee_id="emp-suggestion-1",
            employee_name=employee_name,
            model=employee_analytics_engine.model_name,
            stress=SuggestionScore(value=prediction.stress_score, drivers=SmartSuggestionService._stress_drivers(activity)),
            productivity=SuggestionScore(
                value=prediction.productivity_score,
                drivers=SmartSuggestionService._productivity_drivers(activity),
                trend_delta=round(prediction.productivity_score - 74, 2),
            ),
            burnout_probability=SuggestionScore(value=burnout, drivers=SmartSuggestionService._burnout_drivers(activity, prediction.stress_score)),
        )

    @staticmethod
    def _stress_drivers(point: EmployeeActivityPoint) -> list[str]:
        drivers: list[str] = []
        if point.overtime_hours >= 10:
            drivers.append(f"{point.overtime_hours:.1f} overtime hours")
        if point.meeting_hours >= 9:
            drivers.append(f"{point.meeting_hours:.1f} meeting hours")
        if point.sentiment_score < -0.2:
            drivers.append("negative communication sentiment")
        if point.activity_variance >= 0.55:
            drivers.append("unstable activity rhythm")
        if point.negative_message_ratio >= 0.3:
            drivers.append("rising negative message ratio")
        return drivers or ["normal workload rhythm"]

    @staticmethod
    def _productivity_drivers(point: EmployeeActivityPoint) -> list[str]:
        drivers: list[str] = []
        if point.task_completion_ratio < 0.74:
            drivers.append("task completion slowing")
        if point.focus_hours < 4:
            drivers.append("low focus time")
        if point.attendance_rate < 0.92:
            drivers.append("availability inconsistency")
        if point.collaboration_score < 0.75:
            drivers.append("collaboration quality declining")
        if point.meeting_hours > 10:
            drivers.append("meeting load compressing work time")
        return drivers or ["healthy execution rhythm"]

    @staticmethod
    def _burnout_drivers(point: EmployeeActivityPoint, stress_score: float) -> list[str]:
        drivers = []
        if stress_score >= 70:
            drivers.append("high stress trajectory")
        if point.overtime_hours >= 12:
            drivers.append("overtime accumulation")
        if point.sentiment_score <= -0.35:
            drivers.append("negative sentiment pressure")
        if point.task_completion_ratio <= 0.68:
            drivers.append("delivery slowdown")
        if point.absence_days >= 3:
            drivers.append("absence pattern rising")
        return drivers or ["burnout risk remains controlled"]

    @staticmethod
    def _employee_activity(request: SmartSuggestionRequest) -> EmployeeActivityPoint:
        now = datetime.now(timezone.utc)
        if request.scenario == "crisis":
            return EmployeeActivityPoint(
                timestamp=now,
                overtime_hours=22,
                workload_intensity=94,
                meeting_hours=17,
                sentiment_score=-0.74,
                task_completion_ratio=0.46,
                attendance_rate=0.8,
                focus_hours=1.7,
                collaboration_score=0.5,
                activity_variance=0.88,
                negative_message_ratio=0.64,
                toxic_message_count=4,
                absence_days=6,
            )
        return employee_dashboard_service.default_current()

    @staticmethod
    def _manager_request(request: SmartSuggestionRequest) -> ManagerDashboardRequest | None:
        if request.scenario == "default":
            return None
        return ManagerDashboardRequest(
            manager_id="mgr-suggestion-crisis",
            manager_name="Priya Raman",
            sensitivity=request.sensitivity,
            teams=[
                TeamAnalyticsInput(
                    team_id="team-suggestion-dev",
                    team_name="Development Team",
                    department="Engineering",
                    member_count=21,
                    burnout_probability=0.91,
                    productivity_decline=0.72,
                    average_stress=0.9,
                    toxicity_ratio=0.3,
                    overload_ratio=0.88,
                    missed_deadlines=10,
                    attendance_rate=0.79,
                    collaboration_score=0.5,
                    overtime_escalation=0.86,
                    dependency_bottlenecks=11,
                )
            ],
            employees=[
                EmployeeWorkloadInput(
                    employee_id="emp-suggestion-john",
                    employee_name="Employee John",
                    team_name="Development Team",
                    role="Backend Lead",
                    active_tasks=24,
                    overtime_hours=22,
                    meeting_hours=17,
                    productivity_score=0.43,
                    work_intensity=0.96,
                    deadline_pressure=0.94,
                    multi_project_allocation=7,
                    stress_score=0.92,
                    task_completion_ratio=0.44,
                )
            ],
            projects=[
                ProjectDeliveryInput(
                    project_id="project-suggestion-alpha",
                    project_name="Project Alpha",
                    team_name="Development Team",
                    task_completion_speed=0.32,
                    team_productivity_trend=-0.7,
                    historical_delivery_rate=0.48,
                    burnout_growth=0.85,
                    team_overload=0.9,
                    dependency_bottlenecks=12,
                    resource_shortage=0.7,
                    communication_efficiency=0.4,
                    scope_change_rate=0.62,
                    days_to_deadline=10,
                )
            ],
        )

    @staticmethod
    def _recommendation_context(request: SmartSuggestionRequest, feedback_signal: float) -> SuggestionRecommendationContext:
        recommendation_request = SmartSuggestionService._recommendation_request(request, feedback_signal)
        employees = recommendation_request.employees or recommendation_service.default_employees()
        tasks = recommendation_request.tasks or recommendation_service.default_tasks()
        items: list[SuggestionRecommendation] = []

        overloaded = sorted(
            [employee for employee in employees if employee.allocated_hours / employee.capacity_hours > 1.03],
            key=lambda employee: employee.allocated_hours / employee.capacity_hours,
            reverse=True,
        )
        receivers = sorted(
            [employee for employee in employees if employee.allocated_hours / employee.capacity_hours < 0.93],
            key=lambda employee: employee.allocated_hours / employee.capacity_hours,
        )
        if overloaded and receivers and tasks:
            sender = overloaded[0]
            receiver = max(
                receivers,
                key=lambda employee: employee.productivity
                + employee.collaboration_score
                + max((1.0 if task.required_skill.lower() in {skill.lower() for skill in employee.skills} else 0.0) for task in tasks),
            )
            task = max(
                tasks,
                key=lambda item: item.priority
                + (1.0 if item.required_skill.lower() in {skill.lower() for skill in receiver.skills} else 0.0)
                - item.effort_hours / 80,
            )
            rank = recommendation_engine.rank_reassignment(sender, receiver, task)
            overload_percent = round(((sender.allocated_hours / sender.capacity_hours) - 1) * 100)
            items.append(
                SuggestionRecommendation(
                    category="work_redistribution",
                    title=f"Reassign {task.title} to {receiver.name}",
                    action=f"Move {task.effort_hours:g}h of {task.required_skill} work from {sender.name} to {receiver.name}.",
                    rationale=(
                        f"{sender.name} is overloaded by {overload_percent}% while {receiver.name} has matching skill "
                        f"coverage and {round(receiver.capacity_hours - receiver.allocated_hours, 1)}h available."
                    ),
                    confidence=rank.confidence,
                    impact_score=rank.score,
                    affected_employees=[sender.employee_id, receiver.employee_id],
                )
            )

        fatigue_candidate = max(employees, key=lambda employee: recommendation_engine.break_score(employee).score)
        fatigue = recommendation_engine.break_score(fatigue_candidate)
        items.append(
            SuggestionRecommendation(
                category="break",
                title=f"Recovery window for {fatigue_candidate.name}",
                action="Schedule a recovery block today and remove low-signal recurring meetings this week.",
                rationale=(
                    f"Stress {round(fatigue_candidate.stress_score * 100)}%, burnout risk {round(fatigue_candidate.burnout_risk * 100)}%, "
                    f"and {fatigue_candidate.overtime_hours:g} overtime hours indicate fatigue accumulation."
                ),
                confidence=fatigue.confidence,
                impact_score=fatigue.score,
                affected_employees=[fatigue_candidate.employee_id],
            )
        )

        by_team: dict[str, list[EmployeeProfile]] = {}
        for employee in employees:
            by_team.setdefault(employee.team, []).append(employee)
        team_balance_score = recommendation_engine.team_balance_score(employees)
        if len(by_team) >= 2:
            team_load = {
                team: mean([employee.allocated_hours / employee.capacity_hours for employee in members])
                for team, members in by_team.items()
            }
            overloaded_team = max(team_load, key=team_load.get)
            underused_team = min(team_load, key=team_load.get)
            gap = team_load[overloaded_team] - team_load[underused_team]
            source = max(by_team[overloaded_team], key=lambda employee: employee.allocated_hours / employee.capacity_hours)
            target = max(by_team[underused_team], key=lambda employee: employee.productivity + employee.collaboration_score)
            if gap >= 0.14:
                items.append(
                    SuggestionRecommendation(
                        category="team_balancing",
                        title=f"Balance {overloaded_team} with {underused_team}",
                        action=f"Move one sprint lane from {overloaded_team} to {underused_team} with {target.name} as execution owner.",
                        rationale=(
                            f"{overloaded_team} utilization is {round(team_load[overloaded_team] * 100)}% versus "
                            f"{round(team_load[underused_team] * 100)}% for {underused_team}."
                        ),
                        confidence=round(float(min(0.93, 0.62 + gap * 0.6)), 3),
                        impact_score=min(100, 42 + gap * 80 + feedback_signal * 8),
                        affected_employees=[source.employee_id, target.employee_id],
                    )
                )

        return SuggestionRecommendationContext(
            model=recommendation_engine.model_name,
            team_balance_score=team_balance_score,
            recommendations=items,
        )

    @staticmethod
    def _recommendation_request(request: SmartSuggestionRequest, feedback_signal: float) -> RecommendationRequest:
        if request.scenario == "default":
            return RecommendationRequest(feedback_weight=request.feedback_weight)
        return RecommendationRequest(
            feedback_weight=min(1, request.feedback_weight + feedback_signal * 0.1),
            employees=[
                EmployeeProfile(
                    employee_id="emp-suggestion-john",
                    name="Employee John",
                    role="Backend Lead",
                    team="Core Systems",
                    skills=["python", "api", "kubernetes"],
                    current_tasks=16,
                    capacity_hours=40,
                    allocated_hours=66,
                    productivity=0.62,
                    overtime_hours=22,
                    stress_score=0.92,
                    burnout_risk=0.86,
                    collaboration_score=0.68,
                ),
                EmployeeProfile(
                    employee_id="emp-suggestion-ready",
                    name="Employee B",
                    role="Platform Engineer",
                    team="Automation",
                    skills=["python", "api", "workflow"],
                    current_tasks=3,
                    capacity_hours=40,
                    allocated_hours=23,
                    productivity=0.94,
                    overtime_hours=1,
                    stress_score=0.16,
                    burnout_risk=0.11,
                    collaboration_score=0.92,
                ),
                EmployeeProfile(
                    employee_id="emp-suggestion-z",
                    name="Developer Z",
                    role="ML Engineer",
                    team="Intelligence",
                    skills=["mlops", "python", "workflow"],
                    current_tasks=4,
                    capacity_hours=40,
                    allocated_hours=26,
                    productivity=0.9,
                    overtime_hours=2,
                    stress_score=0.2,
                    burnout_risk=0.14,
                    collaboration_score=0.88,
                ),
            ],
            tasks=[
                TaskProfile(task_id="task-sugg-api", title="revenue API hardening", required_skill="python", effort_hours=9, priority=5, project="Revenue Platform"),
                TaskProfile(task_id="task-sugg-workflow", title="workflow rules engine", required_skill="workflow", effort_hours=8, priority=4, project="Autonomous Ops"),
            ],
        )

    @staticmethod
    def _nlp_request(request: SmartSuggestionRequest) -> NLPBatchRequest:
        if request.scenario == "crisis":
            texts = [
                "I am overloaded by meetings and context switching, and I cannot finish core work.",
                "The team is frustrated, exhausted, and the delivery thread is becoming hostile.",
            ]
        else:
            texts = [
                "The meeting load is heavy and focus time keeps getting interrupted.",
                "I am still motivated, but repeated rework is frustrating.",
            ]
        return NLPBatchRequest(
            messages=[
                NLPAnalyzeRequest(employee_id=f"emp-suggestion-nlp-{index}", department="Engineering", channel="chat", text=text)
                for index, text in enumerate(texts, start=1)
            ]
        )

    @staticmethod
    def _adapt(score: float, feedback_signal: float, feedback_weight: float) -> float:
        return min(100, max(0, score * (1 - feedback_weight) + score * (0.75 + feedback_signal * 0.35) * feedback_weight))

    @staticmethod
    def _priority(score: float):
        if score >= 82:
            return "critical"
        if score >= 64:
            return "high"
        if score >= 42:
            return "medium"
        return "low"

    @staticmethod
    def _summary(suggestions: list[SmartSuggestion]) -> SmartSuggestionSummary:
        return SmartSuggestionSummary(
            total=len(suggestions),
            critical=sum(1 for suggestion in suggestions if suggestion.priority == "critical"),
            high=sum(1 for suggestion in suggestions if suggestion.priority == "high"),
            average_impact=round(mean([suggestion.impact_score for suggestion in suggestions]), 2) if suggestions else 0,
            average_confidence=round(mean([suggestion.confidence for suggestion in suggestions]), 3) if suggestions else 0,
            stream_sequence=1,
        )

    @staticmethod
    def _adaptive_threshold(sensitivity: float, feedback_signal: float) -> float:
        return round(float(min(72, max(34, 66 - sensitivity * 24 - (feedback_signal - 0.5) * 8))), 2)

    @staticmethod
    def _append_jsonl(path: Path, payload: dict[str, object]) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, default=str) + "\n")

    @staticmethod
    def _feedback_signal() -> float:
        if not FEEDBACK_PATH.exists():
            return 0.65
        records: list[float] = []
        for line in FEEDBACK_PATH.read_text(encoding="utf-8").splitlines()[-50:]:
            try:
                records.append(float(json.loads(line).get("learning_signal", 0.65)))
            except json.JSONDecodeError:
                continue
        return round(mean(records), 3) if records else 0.65

    @staticmethod
    def _feedback_states() -> dict[str, bool]:
        if not FEEDBACK_PATH.exists():
            return {}
        states: dict[str, bool] = {}
        for line in FEEDBACK_PATH.read_text(encoding="utf-8").splitlines()[-200:]:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            states[str(record.get("suggestion_id"))] = bool(record.get("accepted", False))
        return states


smart_suggestion_service = SmartSuggestionService()
