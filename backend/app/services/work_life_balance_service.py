from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, pstdev
from threading import Lock

import numpy as np

from app.ai.work_life_balance_engine import WorkLifeBalanceEngine
from app.core.cache import TTLResponseCache
from app.schemas.work_life_balance import (
    MeetingReductionPlan,
    WorkLifeBalanceRequest,
    WorkLifeBalanceResponse,
    WorkLifeBalanceSummary,
    WorkLifeEmployeePlan,
    WorkLifeEmployeeSignal,
    WorkLifeFocusBlock,
    WorkLifeForecastPoint,
    WorkLifeHeatmapCell,
    WorkLifeRiskAlert,
    WorkLifeScheduleRecommendation,
    WorkLifeTeamBalance,
    WorkloadRedistributionPlan,
)


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
HISTORY_PATH = DATA_DIR / "work_life_balance_history.jsonl"


class WorkLifeBalanceService:
    model_name = "AI Work-Life Balance Optimizer"
    forecasting_model = "Burnout-aware sustainable productivity time-series forecaster"
    optimization_model = "Constraint optimizer for focus blocks, meeting reduction, flexible timing, and workload redistribution"
    source_systems = [
        "calendar_meeting_analytics",
        "employee_wellness_ai",
        "productivity_leakage_detector",
        "resource_allocation_optimizer",
        "random_forest_work_life_model",
        "gradient_boosting_burnout_forecaster",
        "kmeans_energy_schedule_segmenter",
        "work_life_balance_history_jsonl",
    ]

    def __init__(self) -> None:
        self._cache: TTLResponseCache[WorkLifeBalanceResponse] = TTLResponseCache(ttl_seconds=8)
        self._lock = Lock()
        self._engine = WorkLifeBalanceEngine()
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def optimize(self, payload: WorkLifeBalanceRequest | None = None) -> WorkLifeBalanceResponse:
        if payload is None:
            return self._cache.get_or_set(self._default_uncached)
        return self._optimize_uncached(payload)

    def _default_uncached(self) -> WorkLifeBalanceResponse:
        return self._optimize_uncached(self.default_request())

    def _optimize_uncached(self, payload: WorkLifeBalanceRequest) -> WorkLifeBalanceResponse:
        request = payload or self.default_request()
        employees = request.employees or self.default_request().employees
        features = [self._features(employee) for employee in employees]
        predicted_wellness, predicted_burnout, predicted_balance, schedule_clusters = self._engine.predict(features)
        employee_plans = self._employee_plans(employees, predicted_wellness, predicted_burnout, predicted_balance, schedule_clusters)
        team_balance = self._team_balance(employees, employee_plans)
        meeting_plan = self._meeting_plan(employees, employee_plans)
        workload_redistribution = self._workload_redistribution(employees, employee_plans)
        focus_blocks = self._focus_blocks(employees, employee_plans)
        summary = self._summary(employees, employee_plans, team_balance, meeting_plan, workload_redistribution)
        recommendations = self._recommendations(summary, team_balance, employee_plans, meeting_plan, workload_redistribution, focus_blocks)
        forecast = self._forecast(request.horizon_days, summary)
        heatmap = self._heatmap(team_balance)
        alerts = self._risk_alerts(employees, employee_plans, team_balance)
        insights = self._executive_insights(request, summary, team_balance, recommendations)
        response = WorkLifeBalanceResponse(
            model=self.model_name,
            generated_at=datetime.now(timezone.utc),
            cycle_name=request.cycle_name,
            target_department=request.target_department,
            horizon_days=request.horizon_days,
            ml_model=str(self._engine.metrics.get("model", WorkLifeBalanceEngine.model_name)),
            forecasting_model=self.forecasting_model,
            optimization_model=self.optimization_model,
            source_systems=self.source_systems,
            summary=summary,
            employee_plans=employee_plans,
            team_balance=team_balance,
            focus_blocks=focus_blocks,
            meeting_plan=meeting_plan,
            workload_redistribution=workload_redistribution,
            recommendations=recommendations,
            forecast=forecast,
            heatmap=heatmap,
            risk_alerts=alerts,
            executive_insights=insights,
            storage=str(HISTORY_PATH),
        )
        self._append_jsonl(response.model_dump(mode="json"))
        return response

    async def stream(self, payload: WorkLifeBalanceRequest | None = None):
        base = payload or self.default_request()
        scenarios = [
            base,
            self._scenario_variant(base, meeting_delta=2.5, overtime_delta=4.5, focus_delta=-0.45, stress_delta=0.05),
            self._scenario_variant(base, meeting_delta=-3.2, overtime_delta=-5.5, focus_delta=0.7, stress_delta=-0.08),
        ]
        for sequence, scenario in enumerate(scenarios, start=1):
            response = self.optimize(scenario)
            data = response.model_dump(mode="json")
            data["summary"]["stream_sequence"] = sequence
            yield f"event: work_life_balance\ndata: {json.dumps(data)}\n\n"
            await asyncio.sleep(0.8)

    @staticmethod
    def default_request() -> WorkLifeBalanceRequest:
        return WorkLifeBalanceRequest(
            cycle_name="Release Week Sustainable Productivity Recovery",
            target_department="Engineering",
            horizon_days=60,
            employees=[
                WorkLifeEmployeeSignal(
                    employee_id="wlb-aarav",
                    name="Aarav Mehta",
                    department="Engineering",
                    team="Platform Reliability",
                    role="Senior Backend Engineer",
                    meeting_hours_per_week=18,
                    recurring_meeting_hours=11,
                    async_candidate_hours=6,
                    overtime_hours_30d=54,
                    after_hours_messages_30d=116,
                    focus_hours_per_day=2.1,
                    context_switches_per_hour=31,
                    task_load_hours=55,
                    capacity_hours=40,
                    deadline_pressure=0.82,
                    collaboration_dependency=0.74,
                    burnout_risk=0.72,
                    stress_score=0.76,
                    wellness_score=0.42,
                    productivity_score=0.78,
                    energy_morning=0.86,
                    energy_afternoon=0.48,
                    flexibility_fit=0.72,
                    manager_support=0.64,
                ),
                WorkLifeEmployeeSignal(
                    employee_id="wlb-nisha",
                    name="Nisha Rao",
                    department="Engineering",
                    team="Platform Reliability",
                    role="DevOps Lead",
                    meeting_hours_per_week=16,
                    recurring_meeting_hours=9,
                    async_candidate_hours=5,
                    overtime_hours_30d=46,
                    after_hours_messages_30d=92,
                    focus_hours_per_day=2.4,
                    context_switches_per_hour=27,
                    task_load_hours=50,
                    capacity_hours=40,
                    deadline_pressure=0.74,
                    collaboration_dependency=0.67,
                    burnout_risk=0.64,
                    stress_score=0.66,
                    wellness_score=0.5,
                    productivity_score=0.81,
                    energy_morning=0.78,
                    energy_afternoon=0.58,
                    flexibility_fit=0.68,
                    manager_support=0.7,
                ),
                WorkLifeEmployeeSignal(
                    employee_id="wlb-maya",
                    name="Maya Iyer",
                    department="Engineering",
                    team="Automation",
                    role="Automation Engineer",
                    meeting_hours_per_week=7,
                    recurring_meeting_hours=4,
                    async_candidate_hours=2,
                    overtime_hours_30d=11,
                    after_hours_messages_30d=18,
                    focus_hours_per_day=5.4,
                    context_switches_per_hour=11,
                    task_load_hours=31,
                    capacity_hours=40,
                    deadline_pressure=0.35,
                    collaboration_dependency=0.42,
                    burnout_risk=0.2,
                    stress_score=0.28,
                    wellness_score=0.82,
                    productivity_score=0.88,
                    energy_morning=0.67,
                    energy_afternoon=0.76,
                    flexibility_fit=0.82,
                    manager_support=0.86,
                ),
                WorkLifeEmployeeSignal(
                    employee_id="wlb-bianca",
                    name="Bianca Shah",
                    department="Engineering",
                    team="Automation",
                    role="SRE Manager",
                    meeting_hours_per_week=13,
                    recurring_meeting_hours=8,
                    async_candidate_hours=4,
                    overtime_hours_30d=28,
                    after_hours_messages_30d=42,
                    focus_hours_per_day=3.8,
                    context_switches_per_hour=17,
                    task_load_hours=42,
                    capacity_hours=42,
                    deadline_pressure=0.55,
                    collaboration_dependency=0.62,
                    burnout_risk=0.39,
                    stress_score=0.44,
                    wellness_score=0.66,
                    productivity_score=0.84,
                    energy_morning=0.72,
                    energy_afternoon=0.68,
                    flexibility_fit=0.7,
                    manager_support=0.78,
                ),
                WorkLifeEmployeeSignal(
                    employee_id="wlb-rina",
                    name="Rina Shah",
                    department="Customer Success",
                    team="Enterprise Accounts",
                    role="Client Success Lead",
                    meeting_hours_per_week=22,
                    recurring_meeting_hours=13,
                    async_candidate_hours=7,
                    overtime_hours_30d=38,
                    after_hours_messages_30d=74,
                    focus_hours_per_day=1.9,
                    context_switches_per_hour=34,
                    task_load_hours=47,
                    capacity_hours=40,
                    deadline_pressure=0.69,
                    collaboration_dependency=0.83,
                    burnout_risk=0.61,
                    stress_score=0.63,
                    wellness_score=0.48,
                    productivity_score=0.76,
                    energy_morning=0.56,
                    energy_afternoon=0.74,
                    flexibility_fit=0.76,
                    manager_support=0.66,
                ),
                WorkLifeEmployeeSignal(
                    employee_id="wlb-omar",
                    name="Omar Khan",
                    department="Finance",
                    team="Revenue Ops",
                    role="Finance Analyst",
                    meeting_hours_per_week=6,
                    recurring_meeting_hours=3,
                    async_candidate_hours=1.5,
                    overtime_hours_30d=8,
                    after_hours_messages_30d=12,
                    focus_hours_per_day=5.6,
                    context_switches_per_hour=9,
                    task_load_hours=30,
                    capacity_hours=40,
                    deadline_pressure=0.31,
                    collaboration_dependency=0.36,
                    burnout_risk=0.18,
                    stress_score=0.24,
                    wellness_score=0.86,
                    productivity_score=0.9,
                    energy_morning=0.81,
                    energy_afternoon=0.66,
                    flexibility_fit=0.78,
                    manager_support=0.84,
                ),
            ],
        )

    @staticmethod
    def _features(employee: WorkLifeEmployeeSignal) -> list[float]:
        return [
            min(1.0, employee.meeting_hours_per_week / 40),
            min(1.0, employee.recurring_meeting_hours / 28),
            min(1.0, employee.async_candidate_hours / max(employee.meeting_hours_per_week, 1)),
            min(1.0, employee.overtime_hours_30d / 90),
            min(1.0, employee.after_hours_messages_30d / 240),
            min(1.0, max(0, 5.5 - employee.focus_hours_per_day) / 5.5),
            min(1.0, employee.context_switches_per_hour / 50),
            min(1.55, employee.task_load_hours / max(employee.capacity_hours, 1)),
            employee.deadline_pressure,
            employee.collaboration_dependency,
            employee.burnout_risk,
            employee.stress_score,
            employee.wellness_score,
            employee.productivity_score,
            employee.energy_morning,
            employee.energy_afternoon,
            employee.flexibility_fit,
            employee.manager_support,
        ]

    @staticmethod
    def _employee_plans(
        employees: list[WorkLifeEmployeeSignal],
        predicted_wellness: np.ndarray,
        predicted_burnout: np.ndarray,
        predicted_balance: np.ndarray,
        clusters: np.ndarray,
    ) -> list[WorkLifeEmployeePlan]:
        plans: list[WorkLifeEmployeePlan] = []
        for index, employee in enumerate(employees):
            meeting_pressure = min(1.0, employee.meeting_hours_per_week / 28)
            overtime_pressure = min(1.0, employee.overtime_hours_30d / 70)
            focus_deficit = min(1.0, max(0, 5.5 - employee.focus_hours_per_day) / 5.5)
            utilization = employee.task_load_hours / max(employee.capacity_hours, 1)
            async_ratio = employee.async_candidate_hours / max(employee.meeting_hours_per_week, 1)
            meeting_reduction = min(42.0, max(8.0, employee.recurring_meeting_hours * 2.7 + meeting_pressure * 18 + async_ratio * 12))
            async_hours = min(employee.async_candidate_hours, employee.recurring_meeting_hours * 0.72)
            redistribution = max(0.0, employee.task_load_hours - employee.capacity_hours * 0.92)
            redistribution += max(0.0, employee.burnout_risk - 0.58) * 12 + max(0.0, employee.stress_score - 0.62) * 8
            redistribution = min(32.0, redistribution)
            recovery_gain = meeting_reduction * 0.18 + async_hours * 1.5 + redistribution * 0.42 + employee.flexibility_fit * 4.5
            current_wellness = np.clip(employee.wellness_score * 100 - focus_deficit * 10 - overtime_pressure * 8, 0, 100)
            optimized_wellness = np.clip(predicted_wellness[index] + recovery_gain, current_wellness, 100)
            before_burnout = np.clip(employee.burnout_risk * 100 + overtime_pressure * 9 + meeting_pressure * 6 + max(0, utilization - 1) * 22, 0, 100)
            after_burnout = np.clip(predicted_burnout[index] - recovery_gain * 0.88, 0, before_burnout)
            balance = np.clip(predicted_balance[index] + recovery_gain * 0.42, 0, 100)
            sustainability = np.clip(balance * 0.48 + optimized_wellness * 0.34 + (100 - after_burnout) * 0.18, 0, 100)
            focus_block = WorkLifeBalanceService._focus_block(employee, int(clusters[index]))
            schedule = WorkLifeBalanceService._flex_schedule(employee, int(clusters[index]))
            evidence = [
                f"meeting_hours={round(employee.meeting_hours_per_week, 1)}",
                f"overtime_30d={round(employee.overtime_hours_30d, 1)}",
                f"focus_hours={round(employee.focus_hours_per_day, 1)}",
                f"context_switches={round(employee.context_switches_per_hour, 1)}",
                f"utilization={round(utilization * 100, 1)}%",
            ]
            rationale = (
                f"{employee.name} needs {round(async_hours, 1)}h of recurring meetings moved async, "
                f"{round(redistribution, 1)}h redistributed, and protected focus time in {focus_block}."
            )
            plans.append(
                WorkLifeEmployeePlan(
                    employee_id=employee.employee_id,
                    name=employee.name,
                    team=employee.team,
                    role=employee.role,
                    current_wellness_score=round(float(current_wellness), 2),
                    optimized_wellness_score=round(float(optimized_wellness), 2),
                    burnout_risk_before=round(float(before_burnout), 2),
                    burnout_risk_after=round(float(after_burnout), 2),
                    meeting_reduction_percent=round(float(meeting_reduction), 2),
                    recurring_hours_to_async=round(float(async_hours), 2),
                    focus_block=focus_block,
                    flexible_schedule=schedule,
                    task_redistribution_hours=round(float(redistribution), 2),
                    productivity_wellness_balance=round(float(balance), 2),
                    sustainability_score=round(float(sustainability), 2),
                    confidence=round(float(0.72 + employee.manager_support * 0.12 + employee.flexibility_fit * 0.1 + min(0.06, len(evidence) * 0.01)), 3),
                    rationale=rationale,
                    evidence=evidence,
                )
            )
        return sorted(plans, key=lambda plan: (plan.burnout_risk_before - plan.burnout_risk_after, plan.sustainability_score), reverse=True)

    @staticmethod
    def _focus_block(employee: WorkLifeEmployeeSignal, cluster: int) -> str:
        if employee.energy_morning >= employee.energy_afternoon + 0.08:
            return "10:00-13:00"
        if employee.energy_afternoon >= employee.energy_morning + 0.08:
            return "14:00-17:00"
        if cluster in {1, 3}:
            return "09:30-12:00"
        return "11:00-14:00"

    @staticmethod
    def _flex_schedule(employee: WorkLifeEmployeeSignal, cluster: int) -> str:
        if employee.energy_afternoon > employee.energy_morning + 0.08:
            return "10:30-18:30 flexible start"
        if employee.energy_morning > employee.energy_afternoon + 0.08:
            return "08:30-16:30 early focus schedule"
        if cluster in {2, 4}:
            return "09:30-17:30 staggered collaboration"
        return "09:00-17:00 standard protected focus"

    @staticmethod
    def _team_balance(employees: list[WorkLifeEmployeeSignal], plans: list[WorkLifeEmployeePlan]) -> list[WorkLifeTeamBalance]:
        by_team: dict[str, list[WorkLifeEmployeeSignal]] = defaultdict(list)
        plan_by_employee = {plan.employee_id: plan for plan in plans}
        for employee in employees:
            by_team[employee.team].append(employee)
        rows: list[WorkLifeTeamBalance] = []
        for team, team_employees in by_team.items():
            team_plans = [plan_by_employee[employee.employee_id] for employee in team_employees if employee.employee_id in plan_by_employee]
            wellness = mean([plan.optimized_wellness_score for plan in team_plans])
            burnout = mean([plan.burnout_risk_after for plan in team_plans])
            meeting = min(100, mean([employee.meeting_hours_per_week for employee in team_employees]) * 4.1)
            utilization = [employee.task_load_hours / max(employee.capacity_hours, 1) * 100 for employee in team_employees]
            imbalance = min(100, pstdev(utilization) * 1.6 if len(utilization) > 1 else max(0, utilization[0] - 92))
            focus = np.clip(mean([employee.focus_hours_per_day for employee in team_employees]) / 5.5 * 100, 0, 100)
            policy = "Maintain current schedule."
            if burnout >= 65 or meeting >= 70:
                policy = "Adopt no-meeting Wednesday, cap recurring meetings, and redistribute high-load sprint work."
            elif focus < 58:
                policy = "Protect two shared focus blocks each week and defer low-signal syncs."
            rows.append(
                WorkLifeTeamBalance(
                    team=team,
                    employees=len(team_employees),
                    wellness_score=round(float(wellness), 2),
                    burnout_risk=round(float(burnout), 2),
                    meeting_overload=round(float(meeting), 2),
                    workload_imbalance=round(float(imbalance), 2),
                    focus_protection_score=round(float(focus), 2),
                    recommended_policy=policy,
                )
            )
        return sorted(rows, key=lambda item: (item.burnout_risk + item.meeting_overload + item.workload_imbalance), reverse=True)

    @staticmethod
    def _meeting_plan(employees: list[WorkLifeEmployeeSignal], plans: list[WorkLifeEmployeePlan]) -> list[MeetingReductionPlan]:
        by_team: dict[str, list[WorkLifeEmployeeSignal]] = defaultdict(list)
        plans_by_employee = {plan.employee_id: plan for plan in plans}
        for employee in employees:
            by_team[employee.team].append(employee)
        rows = []
        for team, team_employees in by_team.items():
            current = sum(employee.meeting_hours_per_week for employee in team_employees)
            async_hours = sum(plans_by_employee[employee.employee_id].recurring_hours_to_async for employee in team_employees if employee.employee_id in plans_by_employee)
            reduction = min(current * 0.42, async_hours + sum(max(0, employee.meeting_hours_per_week - 12) * 0.32 for employee in team_employees))
            recommended = max(0, current - reduction)
            productivity_recovery = reduction * 0.68
            rows.append(
                MeetingReductionPlan(
                    team=team,
                    current_meeting_hours=round(current, 2),
                    recommended_meeting_hours=round(recommended, 2),
                    reduction_percent=round(float(reduction / max(current, 1) * 100), 2),
                    async_conversion_hours=round(async_hours, 2),
                    productivity_recovery_hours=round(productivity_recovery, 2),
                    recommendation="Convert status syncs to async updates and reserve meetings for decisions and conflict resolution.",
                )
            )
        return sorted(rows, key=lambda row: row.reduction_percent, reverse=True)

    @staticmethod
    def _workload_redistribution(employees: list[WorkLifeEmployeeSignal], plans: list[WorkLifeEmployeePlan]) -> list[WorkloadRedistributionPlan]:
        employee_by_id = {employee.employee_id: employee for employee in employees}
        overloaded = [plan for plan in plans if plan.task_redistribution_hours >= 2.0]
        underloaded = sorted(
            [employee for employee in employees if employee.task_load_hours < employee.capacity_hours * 0.86 and employee.burnout_risk <= 0.45],
            key=lambda employee: (employee.capacity_hours - employee.task_load_hours, employee.productivity_score),
            reverse=True,
        )
        rows: list[WorkloadRedistributionPlan] = []
        for plan in overloaded[:6]:
            source = employee_by_id[plan.employee_id]
            target = next((employee for employee in underloaded if employee.team == source.team and employee.employee_id != source.employee_id), None)
            if target is None:
                target = next((employee for employee in underloaded if employee.employee_id != source.employee_id), None)
            if target is None:
                continue
            hours = min(plan.task_redistribution_hours, max(1.0, target.capacity_hours * 0.92 - target.task_load_hours), 10.0)
            if hours <= 0:
                continue
            rows.append(
                WorkloadRedistributionPlan(
                    source_employee=source.name,
                    target_employee=target.name,
                    team=source.team,
                    hours_to_shift=round(float(hours), 2),
                    burnout_reduction=round(float(min(28, hours * 1.9 + source.burnout_risk * 10)), 2),
                    delivery_risk_change=round(float(-min(18, hours * 0.8 + target.productivity_score * 3)), 2),
                    rationale=f"Shift execution load from {source.name} to {target.name} to reduce overload while preserving delivery confidence.",
                )
            )
        return rows

    @staticmethod
    def _focus_blocks(employees: list[WorkLifeEmployeeSignal], plans: list[WorkLifeEmployeePlan]) -> list[WorkLifeFocusBlock]:
        by_team: dict[str, list[WorkLifeEmployeeSignal]] = defaultdict(list)
        for employee in employees:
            by_team[employee.team].append(employee)
        plan_by_employee = {plan.employee_id: plan for plan in plans}
        rows: list[WorkLifeFocusBlock] = []
        for team, team_employees in by_team.items():
            team_plans = [plan_by_employee[employee.employee_id] for employee in team_employees if employee.employee_id in plan_by_employee]
            block = max([plan.focus_block for plan in team_plans], key=[plan.focus_block for plan in team_plans].count)
            current_focus = mean([employee.focus_hours_per_day for employee in team_employees])
            protected = min(15.0, max(6.0, (5.5 - min(current_focus, 5.5)) * len(team_employees) + 4.0))
            conflict = min(100, mean([employee.meeting_hours_per_week for employee in team_employees]) * 2.8)
            gain = min(100, protected * 4.2 + conflict * 0.28)
            rows.append(
                WorkLifeFocusBlock(
                    team=team,
                    block=block,
                    protected_hours=round(float(protected), 2),
                    expected_focus_gain=round(float(gain), 2),
                    meeting_conflict_reduction=round(float(conflict), 2),
                    rationale=f"{team} has {round(current_focus, 1)} average focus hours per day; protect {block} for deep work.",
                )
            )
        return sorted(rows, key=lambda row: row.expected_focus_gain, reverse=True)

    @staticmethod
    def _summary(
        employees: list[WorkLifeEmployeeSignal],
        plans: list[WorkLifeEmployeePlan],
        team_balance: list[WorkLifeTeamBalance],
        meeting_plan: list[MeetingReductionPlan],
        redistribution: list[WorkloadRedistributionPlan],
    ) -> WorkLifeBalanceSummary:
        wellness = mean([plan.optimized_wellness_score for plan in plans])
        burnout_before = mean([plan.burnout_risk_before for plan in plans])
        burnout_after = mean([plan.burnout_risk_after for plan in plans])
        current_meetings = sum(row.current_meeting_hours for row in meeting_plan)
        recommended_meetings = sum(row.recommended_meeting_hours for row in meeting_plan)
        meeting_reduction = (current_meetings - recommended_meetings) / max(current_meetings, 1) * 100
        focus_gain = sum(row.productivity_recovery_hours for row in meeting_plan)
        redistribution_hours = sum(row.hours_to_shift for row in redistribution)
        balance = mean([plan.productivity_wellness_balance for plan in plans])
        sustainable = np.clip(balance * 0.4 + wellness * 0.38 + (100 - burnout_after) * 0.22, 0, 100)
        return WorkLifeBalanceSummary(
            employees_analyzed=len(employees),
            team_count=len(team_balance),
            wellness_score=round(float(wellness), 2),
            burnout_risk=round(float(burnout_after), 2),
            projected_burnout_reduction=round(float(max(0, burnout_before - burnout_after)), 2),
            meeting_reduction_percent=round(float(meeting_reduction), 2),
            focus_time_gain_hours=round(float(focus_gain), 2),
            task_redistribution_hours=round(float(redistribution_hours), 2),
            productivity_wellness_balance=round(float(balance), 2),
            sustainable_productivity_score=round(float(sustainable), 2),
        )

    @staticmethod
    def _recommendations(
        summary: WorkLifeBalanceSummary,
        team_balance: list[WorkLifeTeamBalance],
        plans: list[WorkLifeEmployeePlan],
        meeting_plan: list[MeetingReductionPlan],
        redistribution: list[WorkloadRedistributionPlan],
        focus_blocks: list[WorkLifeFocusBlock],
    ) -> list[WorkLifeScheduleRecommendation]:
        recs: list[WorkLifeScheduleRecommendation] = []
        if meeting_plan:
            top_meeting = meeting_plan[0]
            recs.append(
                WorkLifeScheduleRecommendation(
                    category="meeting_reduction",
                    priority="high" if top_meeting.reduction_percent >= 25 else "medium",
                    title="Reduce unnecessary recurring meetings",
                    action=f"Reduce {top_meeting.team} meeting load by {round(top_meeting.reduction_percent)}% and move {top_meeting.async_conversion_hours:.1f}h to async updates.",
                    expected_impact=f"Recover {top_meeting.productivity_recovery_hours:.1f} focus hours each week.",
                    confidence=0.89,
                    affected_teams=[top_meeting.team],
                )
            )
        if focus_blocks:
            top_focus = focus_blocks[0]
            recs.append(
                WorkLifeScheduleRecommendation(
                    category="focus_time",
                    priority="high",
                    title="Protect deep-work focus blocks",
                    action=f"Protect {top_focus.block} for {top_focus.team} with no meetings or non-urgent chat escalation.",
                    expected_impact=f"Expected focus gain {round(top_focus.expected_focus_gain)}%.",
                    confidence=0.87,
                    affected_teams=[top_focus.team],
                )
            )
        if redistribution:
            top_shift = redistribution[0]
            recs.append(
                WorkLifeScheduleRecommendation(
                    category="task_redistribution",
                    priority="high",
                    title="Redistribute overload before burnout escalates",
                    action=f"Shift {top_shift.hours_to_shift:.1f}h from {top_shift.source_employee} to {top_shift.target_employee}.",
                    expected_impact=f"Burnout pressure reduction {round(top_shift.burnout_reduction)}%.",
                    confidence=0.84,
                    affected_teams=[top_shift.team],
                )
            )
        top_burnout = max(plans, key=lambda plan: plan.burnout_risk_before)
        if top_burnout.burnout_risk_before >= 65:
            recs.append(
                WorkLifeScheduleRecommendation(
                    category="burnout_prevention",
                    priority="critical" if top_burnout.burnout_risk_before >= 82 else "high",
                    title="Apply burnout prevention intervention",
                    action=f"Give {top_burnout.name} a recovery sprint lane, remove after-hours ownership, and cap meetings at 10h/week.",
                    expected_impact=f"Projected burnout risk falls from {round(top_burnout.burnout_risk_before)}% to {round(top_burnout.burnout_risk_after)}%.",
                    confidence=top_burnout.confidence,
                    affected_employees=[top_burnout.employee_id],
                    affected_teams=[top_burnout.team],
                )
            )
        flexible = [plan for plan in plans if "flexible" in plan.flexible_schedule or "early" in plan.flexible_schedule]
        if flexible:
            recs.append(
                WorkLifeScheduleRecommendation(
                    category="flexible_timing",
                    priority="medium",
                    title="Adopt energy-aware flexible timing",
                    action=f"Roll out personalized flexible timing for {len(flexible)} employees based on energy and focus peaks.",
                    expected_impact="Improves wellness-productivity balance without reducing delivery capacity.",
                    confidence=0.82,
                    affected_employees=[plan.employee_id for plan in flexible[:8]],
                )
            )
        if team_balance:
            top_team = team_balance[0]
            recs.append(
                WorkLifeScheduleRecommendation(
                    category="productivity_balance",
                    priority="high" if top_team.workload_imbalance >= 40 else "medium",
                    title="Balance productivity against sustainability",
                    action=top_team.recommended_policy,
                    expected_impact=f"Raises sustainable productivity score toward {round(summary.sustainable_productivity_score)}%.",
                    confidence=0.86,
                    affected_teams=[top_team.team],
                )
            )
        return recs[:7]

    @staticmethod
    def _forecast(horizon_days: int, summary: WorkLifeBalanceSummary) -> list[WorkLifeForecastPoint]:
        points: list[WorkLifeForecastPoint] = []
        for day in [7, 14, 30, 45, horizon_days]:
            progress = min(1.0, day / max(horizon_days, 1))
            wellness = np.clip(summary.wellness_score + summary.projected_burnout_reduction * 0.28 * progress, 0, 100)
            burnout = np.clip(summary.burnout_risk - summary.projected_burnout_reduction * 0.38 * progress, 0, 100)
            productivity = np.clip(summary.productivity_wellness_balance + summary.focus_time_gain_hours * 0.16 * progress, 0, 100)
            meeting = np.clip(100 - summary.meeting_reduction_percent * progress, 0, 100)
            focus = np.clip(summary.sustainable_productivity_score + summary.focus_time_gain_hours * 0.1 * progress, 0, 100)
            points.append(
                WorkLifeForecastPoint(
                    day=int(day),
                    wellness_score=round(float(wellness), 2),
                    burnout_risk=round(float(burnout), 2),
                    productivity_score=round(float(productivity), 2),
                    meeting_load=round(float(meeting), 2),
                    focus_time_score=round(float(focus), 2),
                    confidence=round(float(max(0.74, 0.94 - progress * 0.14)), 3),
                )
            )
        unique: dict[int, WorkLifeForecastPoint] = {}
        for point in points:
            unique[point.day] = point
        return list(unique.values())

    @staticmethod
    def _heatmap(team_balance: list[WorkLifeTeamBalance]) -> list[WorkLifeHeatmapCell]:
        rows: list[WorkLifeHeatmapCell] = []
        for team in team_balance:
            metric_rows = [
                ("Burnout risk", team.burnout_risk, "Reduce overload and protect recovery capacity."),
                ("Meeting overload", team.meeting_overload, "Move recurring updates async and consolidate decision meetings."),
                ("Workload imbalance", team.workload_imbalance, "Redistribute sprint work from overloaded owners."),
                ("Focus protection", 100 - team.focus_protection_score, "Create protected deep-work blocks."),
            ]
            for metric, score, recommendation in metric_rows:
                severity: WorkLifeSeverity = "low"
                if score >= 78:
                    severity = "critical"
                elif score >= 62:
                    severity = "high"
                elif score >= 42:
                    severity = "medium"
                rows.append(
                    WorkLifeHeatmapCell(
                        team=team.team,
                        metric=metric,
                        score=round(float(score), 2),
                        severity=severity,
                        recommendation=recommendation,
                    )
                )
        return sorted(rows, key=lambda row: row.score, reverse=True)

    @staticmethod
    def _risk_alerts(employees: list[WorkLifeEmployeeSignal], plans: list[WorkLifeEmployeePlan], team_balance: list[WorkLifeTeamBalance]) -> list[WorkLifeRiskAlert]:
        alerts: list[WorkLifeRiskAlert] = []
        for plan in plans:
            if plan.burnout_risk_before >= 72:
                alerts.append(
                    WorkLifeRiskAlert(
                        category="burnout_prevention",
                        severity="critical" if plan.burnout_risk_before >= 84 else "high",
                        score=plan.burnout_risk_before,
                        message=f"{plan.name} has elevated burnout risk under current schedule.",
                        evidence=plan.evidence,
                        intervention=f"Apply {plan.focus_block} focus protection and shift {plan.task_redistribution_hours:.1f}h of workload.",
                    )
                )
        for employee in employees:
            if employee.meeting_hours_per_week >= 18 or employee.context_switches_per_hour >= 30:
                alerts.append(
                    WorkLifeRiskAlert(
                        category="meeting_reduction",
                        severity="high" if employee.meeting_hours_per_week >= 20 else "medium",
                        score=round(min(100, employee.meeting_hours_per_week * 4.1 + employee.context_switches_per_hour), 2),
                        message=f"{employee.name} is losing focus time to meeting and context-switching pressure.",
                        evidence=[f"meeting_hours={employee.meeting_hours_per_week}", f"context_switches={employee.context_switches_per_hour}"],
                        intervention="Move low-signal recurring updates async and protect a 3h focus block.",
                    )
                )
        for team in team_balance:
            if team.workload_imbalance >= 55:
                alerts.append(
                    WorkLifeRiskAlert(
                        category="task_redistribution",
                        severity="high",
                        score=team.workload_imbalance,
                        message=f"{team.team} workload imbalance is threatening sustainable productivity.",
                        evidence=[f"imbalance={team.workload_imbalance}", f"burnout={team.burnout_risk}", f"meetings={team.meeting_overload}"],
                        intervention=team.recommended_policy,
                    )
                )
        return alerts[:8]

    @staticmethod
    def _executive_insights(
        request: WorkLifeBalanceRequest,
        summary: WorkLifeBalanceSummary,
        team_balance: list[WorkLifeTeamBalance],
        recommendations: list[WorkLifeScheduleRecommendation],
    ) -> list[str]:
        top_team = team_balance[0].team if team_balance else request.target_department
        top_action = recommendations[0].action if recommendations else "Maintain current sustainable productivity controls."
        return [
            f"{request.cycle_name} analyzes {summary.employees_analyzed} employees across {summary.team_count} teams with {summary.sustainable_productivity_score:.0f}% sustainable productivity.",
            f"Projected burnout risk reduction is {summary.projected_burnout_reduction:.1f}% after meeting reduction, focus protection, and workload redistribution.",
            f"{top_team} is the highest-priority team for work-life balance intervention.",
            f"Executive action: {top_action}",
        ]

    @staticmethod
    def _scenario_variant(
        base: WorkLifeBalanceRequest,
        meeting_delta: float,
        overtime_delta: float,
        focus_delta: float,
        stress_delta: float,
    ) -> WorkLifeBalanceRequest:
        employees = []
        for employee in base.employees:
            employees.append(
                employee.model_copy(
                    update={
                        "meeting_hours_per_week": float(np.clip(employee.meeting_hours_per_week + meeting_delta, 0, 60)),
                        "recurring_meeting_hours": float(np.clip(employee.recurring_meeting_hours + meeting_delta * 0.55, 0, 60)),
                        "overtime_hours_30d": float(np.clip(employee.overtime_hours_30d + overtime_delta, 0, 140)),
                        "focus_hours_per_day": float(np.clip(employee.focus_hours_per_day + focus_delta, 0, 12)),
                        "stress_score": float(np.clip(employee.stress_score + stress_delta, 0, 1)),
                        "burnout_risk": float(np.clip(employee.burnout_risk + stress_delta * 0.8, 0, 1)),
                    }
                )
            )
        return base.model_copy(update={"employees": employees})

    def _append_jsonl(self, payload: dict) -> None:
        with self._lock:
            with HISTORY_PATH.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload) + "\n")


work_life_balance_service = WorkLifeBalanceService()
