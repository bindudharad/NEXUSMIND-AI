from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

from app.core.cache import TTLResponseCache
from app.ai.manager_analytics_engine import manager_analytics_engine
from app.schemas.manager_dashboard import (
    DelayPrediction,
    EmployeeWorkloadInput,
    ManagerDashboardRequest,
    ManagerDashboardResponse,
    ManagerDashboardSummary,
    ManagerTrendPoint,
    OverloadedEmployee,
    ProjectDeliveryInput,
    RiskSeverity,
    RiskyTeam,
    TeamAnalyticsInput,
)


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
HISTORY_PATH = DATA_DIR / "manager_dashboard_history.jsonl"


class ManagerDashboardService:
    def __init__(self) -> None:
        self._default_cache: TTLResponseCache[ManagerDashboardResponse] = TTLResponseCache(ttl_seconds=8)

    def analyze(self, payload: ManagerDashboardRequest | None = None) -> ManagerDashboardResponse:
        if payload is None:
            return self._default_cache.get_or_set(self._analyze_uncached)
        return self._analyze_uncached(payload)

    def _analyze_uncached(self, payload: ManagerDashboardRequest | None = None) -> ManagerDashboardResponse:
        request = payload or ManagerDashboardRequest()
        teams = request.teams or self.default_teams()
        employees = request.employees or self.default_employees()
        projects = request.projects or self.default_projects()
        team_threshold = 46 + (1 - request.sensitivity) * 14
        overload_threshold = 50 + (1 - request.sensitivity) * 14
        delay_threshold = 45 + (1 - request.sensitivity) * 16

        risky_teams = [
            self._team_item(team, manager_analytics_engine.predict_team_risk(team).value)
            for team in teams
        ]
        overloaded = [
            self._employee_item(employee, manager_analytics_engine.predict_overload(employee).value)
            for employee in employees
        ]
        delays = [
            self._delay_item(project, manager_analytics_engine.predict_delay(project).value)
            for project in projects
        ]
        risky_teams.sort(key=lambda item: item.risk_score, reverse=True)
        overloaded.sort(key=lambda item: item.overload_score, reverse=True)
        delays.sort(key=lambda item: item.delay_probability, reverse=True)

        visible_teams = [item for item in risky_teams if item.risk_score >= team_threshold]
        visible_overloaded = [item for item in overloaded if item.overload_score >= overload_threshold]
        visible_delays = [item for item in delays if item.delay_probability >= delay_threshold]
        if not visible_teams and risky_teams:
            visible_teams = risky_teams[:1]
        if not visible_overloaded and overloaded:
            visible_overloaded = overloaded[:1]
        if not visible_delays and delays:
            visible_delays = delays[:1]

        average_team_risk = self._avg([item.risk_score for item in risky_teams])
        average_delay = self._avg([item.delay_probability for item in delays])
        response = ManagerDashboardResponse(
            manager_id=request.manager_id,
            manager_name=request.manager_name,
            generated_at=datetime.now(timezone.utc),
            model=manager_analytics_engine.model_name,
            summary=ManagerDashboardSummary(
                teams_at_risk=len(visible_teams),
                overloaded_employees=len(visible_overloaded),
                projects_at_delay_risk=len(visible_delays),
                average_team_risk=average_team_risk,
                average_delay_probability=average_delay,
            ),
            risky_teams=visible_teams[:5],
            overloaded_employees=visible_overloaded[:6],
            delay_predictions=visible_delays[:5],
            trend=self._trend(average_team_risk, self._avg([item.overload_score for item in overloaded]), average_delay),
            recommendations=self._recommendations(visible_teams, visible_overloaded, visible_delays),
            storage=str(HISTORY_PATH),
        )
        self._append_jsonl(HISTORY_PATH, response.model_dump(mode="json"))
        return response

    @staticmethod
    def default_teams() -> list[TeamAnalyticsInput]:
        wave = (datetime.now(timezone.utc).minute % 10) / 50
        return [
            TeamAnalyticsInput(
                team_id="team-dev",
                team_name="Development Team",
                department="Engineering",
                member_count=18,
                burnout_probability=min(1, 0.8 + wave),
                productivity_decline=min(1, 0.48 + wave),
                average_stress=min(1, 0.84 + wave),
                toxicity_ratio=0.24,
                overload_ratio=min(1, 0.76 + wave),
                missed_deadlines=8,
                attendance_rate=0.84,
                collaboration_score=0.58,
                overtime_escalation=min(1, 0.72 + wave),
                dependency_bottlenecks=9,
            ),
            TeamAnalyticsInput(
                team_id="team-platform",
                team_name="Platform Reliability",
                department="Engineering",
                member_count=12,
                burnout_probability=0.52,
                productivity_decline=0.24,
                average_stress=0.6,
                toxicity_ratio=0.08,
                overload_ratio=0.42,
                missed_deadlines=3,
                attendance_rate=0.93,
                collaboration_score=0.76,
                overtime_escalation=0.36,
                dependency_bottlenecks=4,
            ),
            TeamAnalyticsInput(
                team_id="team-success",
                team_name="Customer Success",
                department="Revenue",
                member_count=15,
                burnout_probability=0.45,
                productivity_decline=0.18,
                average_stress=0.53,
                toxicity_ratio=0.11,
                overload_ratio=0.34,
                missed_deadlines=2,
                attendance_rate=0.94,
                collaboration_score=0.81,
                overtime_escalation=0.28,
                dependency_bottlenecks=2,
            ),
        ]

    @staticmethod
    def default_employees() -> list[EmployeeWorkloadInput]:
        wave = (datetime.now(timezone.utc).second % 12) / 60
        return [
            EmployeeWorkloadInput(
                employee_id="emp-mgr-1",
                employee_name="Ishan Verma",
                team_name="Development Team",
                role="Backend Lead",
                active_tasks=19,
                overtime_hours=16 + wave * 4,
                meeting_hours=13,
                productivity_score=0.58,
                work_intensity=0.9,
                deadline_pressure=0.88,
                multi_project_allocation=5,
                stress_score=0.86,
                task_completion_ratio=0.56,
            ),
            EmployeeWorkloadInput(
                employee_id="emp-mgr-2",
                employee_name="Lina Kapoor",
                team_name="Development Team",
                role="Frontend Engineer",
                active_tasks=15,
                overtime_hours=12,
                meeting_hours=9,
                productivity_score=0.68,
                work_intensity=0.78,
                deadline_pressure=0.74,
                multi_project_allocation=4,
                stress_score=0.7,
                task_completion_ratio=0.64,
            ),
            EmployeeWorkloadInput(
                employee_id="emp-mgr-3",
                employee_name="Mateo Cruz",
                team_name="Platform Reliability",
                role="SRE",
                active_tasks=11,
                overtime_hours=8,
                meeting_hours=7,
                productivity_score=0.78,
                work_intensity=0.68,
                deadline_pressure=0.62,
                multi_project_allocation=3,
                stress_score=0.58,
                task_completion_ratio=0.76,
            ),
        ]

    @staticmethod
    def default_projects() -> list[ProjectDeliveryInput]:
        wave = (datetime.now(timezone.utc).minute % 8) / 40
        return [
            ProjectDeliveryInput(
                project_id="proj-alpha",
                project_name="Project Alpha",
                team_name="Development Team",
                task_completion_speed=0.42 - wave / 3,
                team_productivity_trend=-0.52 - wave / 2,
                historical_delivery_rate=0.58,
                burnout_growth=0.72 + wave,
                team_overload=0.82 + wave,
                dependency_bottlenecks=9,
                resource_shortage=0.58,
                communication_efficiency=0.48,
                scope_change_rate=0.55,
                days_to_deadline=12,
            ),
            ProjectDeliveryInput(
                project_id="proj-control-room",
                project_name="3D Control Room",
                team_name="Platform Reliability",
                task_completion_speed=0.68,
                team_productivity_trend=-0.12,
                historical_delivery_rate=0.78,
                burnout_growth=0.34,
                team_overload=0.48,
                dependency_bottlenecks=4,
                resource_shortage=0.24,
                communication_efficiency=0.72,
                scope_change_rate=0.28,
                days_to_deadline=31,
            ),
        ]

    @staticmethod
    def _team_item(team: TeamAnalyticsInput, score: float) -> RiskyTeam:
        return RiskyTeam(
            team_id=team.team_id,
            team_name=team.team_name,
            department=team.department,
            risk_score=score,
            severity=ManagerDashboardService._severity(score),
            member_count=team.member_count,
            drivers=ManagerDashboardService._team_drivers(team),
            recommendation=ManagerDashboardService._team_recommendation(team, score),
        )

    @staticmethod
    def _employee_item(employee: EmployeeWorkloadInput, score: float) -> OverloadedEmployee:
        return OverloadedEmployee(
            employee_id=employee.employee_id,
            employee_name=employee.employee_name,
            team_name=employee.team_name,
            role=employee.role,
            overload_score=score,
            severity=ManagerDashboardService._severity(score),
            drivers=ManagerDashboardService._employee_drivers(employee),
            recommendation=ManagerDashboardService._employee_recommendation(employee, score),
        )

    @staticmethod
    def _delay_item(project: ProjectDeliveryInput, score: float) -> DelayPrediction:
        projected_days = round(score / 100 * max(7, 45 - min(project.days_to_deadline, 45)) + project.dependency_bottlenecks * 0.7)
        return DelayPrediction(
            project_id=project.project_id,
            project_name=project.project_name,
            team_name=project.team_name,
            delay_probability=score,
            severity=ManagerDashboardService._severity(score),
            projected_delay_days=max(0, int(projected_days)),
            bottlenecks=ManagerDashboardService._project_bottlenecks(project),
            recommendation=ManagerDashboardService._project_recommendation(project, score),
        )

    @staticmethod
    def _severity(score: float) -> RiskSeverity:
        if score >= 82:
            return "critical"
        if score >= 66:
            return "high"
        if score >= 48:
            return "medium"
        return "low"

    @staticmethod
    def _team_drivers(team: TeamAnalyticsInput) -> list[str]:
        drivers: list[str] = []
        if team.burnout_probability >= 0.55:
            drivers.append(f"{round(team.burnout_probability * 100)}% burnout probability")
        if team.overload_ratio >= 0.45:
            drivers.append(f"{round(team.overload_ratio * 100)}% team overload")
        if team.average_stress >= 0.65:
            drivers.append(f"{round(team.average_stress * 100)}% average stress")
        if team.productivity_decline >= 0.25:
            drivers.append("productivity decline accelerating")
        if team.dependency_bottlenecks >= 4:
            drivers.append(f"{team.dependency_bottlenecks} dependency bottlenecks")
        if team.missed_deadlines >= 4:
            drivers.append(f"{team.missed_deadlines} missed deadlines")
        return drivers or ["team operating within expected bounds"]

    @staticmethod
    def _employee_drivers(employee: EmployeeWorkloadInput) -> list[str]:
        drivers: list[str] = []
        if employee.active_tasks >= 15:
            drivers.append(f"{employee.active_tasks} active tasks")
        if employee.overtime_hours >= 10:
            drivers.append(f"{employee.overtime_hours:.1f} overtime hours")
        if employee.meeting_hours >= 10:
            drivers.append(f"{employee.meeting_hours:.1f} meeting hours")
        if employee.deadline_pressure >= 0.72:
            drivers.append("deadline pressure elevated")
        if employee.multi_project_allocation >= 4:
            drivers.append(f"{employee.multi_project_allocation} concurrent projects")
        if employee.task_completion_ratio <= 0.65:
            drivers.append("task completion slowing")
        return drivers or ["workload within capacity"]

    @staticmethod
    def _project_bottlenecks(project: ProjectDeliveryInput) -> list[str]:
        bottlenecks: list[str] = []
        if project.task_completion_speed <= 0.58:
            bottlenecks.append("task completion speed below plan")
        if project.team_productivity_trend <= -0.25:
            bottlenecks.append("team productivity trend declining")
        if project.burnout_growth >= 0.5:
            bottlenecks.append("burnout growth pressure")
        if project.team_overload >= 0.6:
            bottlenecks.append("team overload")
        if project.dependency_bottlenecks >= 5:
            bottlenecks.append(f"{project.dependency_bottlenecks} dependency bottlenecks")
        if project.scope_change_rate >= 0.35:
            bottlenecks.append("scope change rate rising")
        return bottlenecks or ["delivery indicators are stable"]

    @staticmethod
    def _team_recommendation(team: TeamAnalyticsInput, score: float) -> str:
        if score >= 75:
            return f"Move non-critical work out of {team.team_name}, reduce meetings, and start a manager recovery protocol."
        if score >= 55:
            return f"Rebalance workload in {team.team_name} and review dependency bottlenecks this week."
        return f"Keep {team.team_name} on passive monitoring."

    @staticmethod
    def _employee_recommendation(employee: EmployeeWorkloadInput, score: float) -> str:
        if score >= 76:
            return f"Reassign two tasks from {employee.employee_name} and protect focus time for critical delivery."
        if score >= 55:
            return f"Reduce meeting load for {employee.employee_name} and inspect deadline blockers."
        return f"Maintain current workload for {employee.employee_name}."

    @staticmethod
    def _project_recommendation(project: ProjectDeliveryInput, score: float) -> str:
        if score >= 72:
            return f"Escalate {project.project_name}, freeze scope, and add temporary capacity for dependency resolution."
        if score >= 52:
            return f"Review {project.project_name} milestones and reduce dependency wait time."
        return f"Keep {project.project_name} on normal delivery cadence."

    @staticmethod
    def _recommendations(teams: list[RiskyTeam], employees: list[OverloadedEmployee], projects: list[DelayPrediction]) -> list[str]:
        recommendations: list[str] = []
        if teams:
            recommendations.append(f"Prioritize {teams[0].team_name}: risk score {round(teams[0].risk_score)}/100.")
        if employees:
            recommendations.append(f"Rebalance workload away from {employees[0].employee_name} before the next sprint checkpoint.")
        if projects:
            recommendations.append(f"Protect {projects[0].project_name}: delay probability {round(projects[0].delay_probability)}%.")
        recommendations.append("Run a manager review combining workload, delivery, and burnout signals every 15 minutes.")
        return recommendations

    @staticmethod
    def _trend(team_risk: float, overload: float, delay: float) -> list[ManagerTrendPoint]:
        rng = np.random.default_rng(88)
        now = datetime.now(timezone.utc)
        points: list[ManagerTrendPoint] = []
        for index in range(14):
            drift = index / 13
            points.append(
                ManagerTrendPoint(
                    timestamp=now - timedelta(days=13 - index),
                    average_team_risk=round(float(np.clip(team_risk - 11 + drift * 11 + rng.normal(0, 1.5), 0, 100)), 2),
                    overload_pressure=round(float(np.clip(overload - 9 + drift * 9 + rng.normal(0, 1.4), 0, 100)), 2),
                    delay_risk=round(float(np.clip(delay - 10 + drift * 10 + rng.normal(0, 1.6), 0, 100)), 2),
                )
            )
        return points

    @staticmethod
    def _avg(values: list[float]) -> float:
        return round(sum(values) / len(values), 2) if values else 0

    @staticmethod
    def _append_jsonl(path: Path, payload: dict[str, object]) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload) + "\n")


manager_dashboard_service = ManagerDashboardService()
