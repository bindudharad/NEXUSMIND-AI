from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from uuid import uuid4

from app.core.cache import TTLResponseCache
from app.ai.recommendation_engine import recommendation_engine
from app.schemas.recommendations import (
    EmployeeProfile,
    RecommendationFeedbackRequest,
    RecommendationFeedbackResponse,
    RecommendationItem,
    RecommendationPriority,
    RecommendationRequest,
    RecommendationResponse,
    TaskProfile,
)


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
HISTORY_PATH = DATA_DIR / "recommendation_history.jsonl"
FEEDBACK_PATH = DATA_DIR / "recommendation_feedback.jsonl"


class RecommendationService:
    def __init__(self) -> None:
        self._default_cache: TTLResponseCache[RecommendationResponse] = TTLResponseCache(ttl_seconds=8)

    def generate(self, payload: RecommendationRequest | None = None) -> RecommendationResponse:
        if payload is None:
            return self._default_cache.get_or_set(self._generate_uncached)
        return self._generate_uncached(payload)

    def _generate_uncached(self, payload: RecommendationRequest | None = None) -> RecommendationResponse:
        request = payload or RecommendationRequest()
        employees = request.employees or self.default_employees()
        tasks = request.tasks or self.default_tasks()
        feedback_signal = self._feedback_signal()
        recommendations = self._work_redistribution(employees, tasks, request.feedback_weight, feedback_signal)
        recommendations.extend(self._break_interventions(employees, feedback_signal))
        recommendations.extend(self._team_balancing(employees, feedback_signal))
        recommendations.sort(key=lambda item: (item.impact_score, item.confidence), reverse=True)
        response = RecommendationResponse(
            model=recommendation_engine.model_name,
            generated_at=datetime.now(timezone.utc),
            employees_analyzed=len(employees),
            tasks_analyzed=len(tasks),
            team_balance_score=recommendation_engine.team_balance_score(employees),
            recommendations=recommendations[:8],
            storage=str(HISTORY_PATH),
        )
        self._append_jsonl(HISTORY_PATH, response.model_dump(mode="json"))
        return response

    def record_feedback(self, payload: RecommendationFeedbackRequest) -> RecommendationFeedbackResponse:
        self._default_cache.clear()
        signal = (payload.usefulness_score / 5) if payload.accepted else max(0.05, payload.usefulness_score / 12)
        record = {
            "recommendation_id": payload.recommendation_id,
            "accepted": payload.accepted,
            "usefulness_score": payload.usefulness_score,
            "notes": payload.notes,
            "learning_signal": round(signal, 3),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._append_jsonl(FEEDBACK_PATH, record)
        return RecommendationFeedbackResponse(
            recommendation_id=payload.recommendation_id,
            learning_signal=round(signal, 3),
            message="Recommendation feedback captured for adaptive ranking.",
            storage=str(FEEDBACK_PATH),
        )

    def _work_redistribution(
        self,
        employees: list[EmployeeProfile],
        tasks: list[TaskProfile],
        feedback_weight: float,
        feedback_signal: float,
    ) -> list[RecommendationItem]:
        overloaded = sorted(
            [employee for employee in employees if employee.allocated_hours / employee.capacity_hours > 1.05],
            key=lambda employee: employee.allocated_hours / employee.capacity_hours,
            reverse=True,
        )
        receivers = sorted(
            [employee for employee in employees if employee.allocated_hours / employee.capacity_hours < 0.92],
            key=lambda employee: employee.allocated_hours / employee.capacity_hours,
        )
        items: list[RecommendationItem] = []
        for sender in overloaded[:3]:
            best: tuple[float, EmployeeProfile, TaskProfile, float] | None = None
            for receiver in receivers:
                if receiver.employee_id == sender.employee_id:
                    continue
                for task in tasks:
                    rank = recommendation_engine.rank_reassignment(sender, receiver, task)
                    adaptive_score = rank.score * (1 - feedback_weight) + rank.score * feedback_signal * feedback_weight
                    if best is None or adaptive_score > best[0]:
                        best = (adaptive_score, receiver, task, rank.confidence)
            if best:
                impact, receiver, task, confidence = best
                overload_percent = round(((sender.allocated_hours / sender.capacity_hours) - 1) * 100)
                items.append(
                    RecommendationItem(
                        recommendation_id=f"rec-{uuid4().hex[:10]}",
                        category="work_redistribution",
                        title=f"Reassign {task.title} to {receiver.name}",
                        action=f"Move {task.effort_hours:g}h of {task.required_skill} work from {sender.name} to {receiver.name}.",
                        rationale=(
                            f"{sender.name} is overloaded by {overload_percent}% while {receiver.name} has matching skill "
                            f"coverage and {round((receiver.capacity_hours - receiver.allocated_hours), 1)}h available."
                        ),
                        confidence=confidence,
                        impact_score=round(min(100, impact), 2),
                        priority=self._priority(impact),
                        affected_employees=[sender.employee_id, receiver.employee_id],
                        source_model=recommendation_engine.model_name,
                    )
                )
        return items

    def _break_interventions(self, employees: list[EmployeeProfile], feedback_signal: float) -> list[RecommendationItem]:
        items: list[RecommendationItem] = []
        for employee in employees:
            score = recommendation_engine.break_score(employee)
            adjusted = min(100, score.score * (0.88 + feedback_signal * 0.2))
            if adjusted < 34:
                continue
            minutes = 20 if adjusted < 58 else 35 if adjusted < 78 else 50
            meeting_reduction = 2 if adjusted < 58 else 4 if adjusted < 78 else 6
            items.append(
                RecommendationItem(
                    recommendation_id=f"rec-{uuid4().hex[:10]}",
                    category="break",
                    title=f"Recovery window for {employee.name}",
                    action=f"Schedule a {minutes}-minute recovery block today and remove {meeting_reduction}h of meetings this week.",
                    rationale=(
                        f"Stress {round(employee.stress_score * 100)}%, burnout risk {round(employee.burnout_risk * 100)}%, "
                        f"and {employee.overtime_hours:g} overtime hours indicate fatigue accumulation."
                    ),
                    confidence=score.confidence,
                    impact_score=round(adjusted, 2),
                    priority=self._priority(adjusted),
                    affected_employees=[employee.employee_id],
                    source_model="Fatigue threshold model + feedback adapter",
                )
            )
        return items

    def _team_balancing(self, employees: list[EmployeeProfile], feedback_signal: float) -> list[RecommendationItem]:
        by_team: dict[str, list[EmployeeProfile]] = defaultdict(list)
        for employee in employees:
            by_team[employee.team].append(employee)
        if len(by_team) < 2:
            return []
        team_load = {
            team: mean([employee.allocated_hours / employee.capacity_hours for employee in members])
            for team, members in by_team.items()
        }
        overloaded_team = max(team_load, key=team_load.get)
        underused_team = min(team_load, key=team_load.get)
        gap = team_load[overloaded_team] - team_load[underused_team]
        if gap < 0.18:
            return []
        source = max(by_team[overloaded_team], key=lambda employee: employee.allocated_hours / employee.capacity_hours)
        target = max(by_team[underused_team], key=lambda employee: employee.productivity + employee.collaboration_score)
        impact = min(100, 42 + gap * 80 + feedback_signal * 8)
        shared_skills = sorted(set(source.skills).intersection(set(target.skills)))
        skill_phrase = f"shared {', '.join(shared_skills[:2])} coverage" if shared_skills else "adjacent delivery skills"
        return [
            RecommendationItem(
                recommendation_id=f"rec-{uuid4().hex[:10]}",
                category="team_balancing",
                title=f"Balance {overloaded_team} with {underused_team}",
                action=f"Move one sprint lane from {overloaded_team} to {underused_team} with {target.name} as execution owner.",
                rationale=(
                    f"{overloaded_team} utilization is {round(team_load[overloaded_team] * 100)}% versus "
                    f"{round(team_load[underused_team] * 100)}% for {underused_team}; {target.name} has {skill_phrase}."
                ),
                confidence=round(float(min(0.93, 0.62 + gap * 0.6)), 3),
                impact_score=round(impact, 2),
                priority=self._priority(impact),
                affected_employees=[source.employee_id, target.employee_id],
                source_model="Team utilization optimizer",
            )
        ]

    @staticmethod
    def default_employees() -> list[EmployeeProfile]:
        return [
            EmployeeProfile(
                employee_id="emp-a",
                name="Aarav Mehta",
                role="Senior Backend Engineer",
                team="Platform",
                skills=["python", "kubernetes", "incident-response"],
                current_tasks=11,
                capacity_hours=40,
                allocated_hours=57,
                productivity=0.71,
                overtime_hours=13,
                stress_score=0.82,
                burnout_risk=0.76,
                collaboration_score=0.72,
            ),
            EmployeeProfile(
                employee_id="emp-b",
                name="Bianca Shah",
                role="Backend Engineer",
                team="Automation",
                skills=["python", "workflow", "kubernetes"],
                current_tasks=5,
                capacity_hours=40,
                allocated_hours=28,
                productivity=0.88,
                overtime_hours=2,
                stress_score=0.28,
                burnout_risk=0.18,
                collaboration_score=0.9,
            ),
            EmployeeProfile(
                employee_id="emp-c",
                name="Chen Rao",
                role="Data Scientist",
                team="Intelligence",
                skills=["forecasting", "python", "mlops"],
                current_tasks=8,
                capacity_hours=38,
                allocated_hours=44,
                productivity=0.77,
                overtime_hours=8,
                stress_score=0.61,
                burnout_risk=0.54,
                collaboration_score=0.81,
            ),
            EmployeeProfile(
                employee_id="emp-d",
                name="Devika Nair",
                role="ML Engineer",
                team="Intelligence",
                skills=["mlops", "python", "rag"],
                current_tasks=4,
                capacity_hours=40,
                allocated_hours=30,
                productivity=0.91,
                overtime_hours=1,
                stress_score=0.24,
                burnout_risk=0.16,
                collaboration_score=0.86,
            ),
        ]

    @staticmethod
    def default_tasks() -> list[TaskProfile]:
        return [
            TaskProfile(task_id="task-1", title="incident automation runbook", required_skill="python", effort_hours=10, priority=5, project="Autonomous Ops"),
            TaskProfile(task_id="task-2", title="Kubernetes rollout guardrails", required_skill="kubernetes", effort_hours=12, priority=4, project="Platform Reliability"),
            TaskProfile(task_id="task-3", title="forecast drift monitor", required_skill="mlops", effort_hours=8, priority=4, project="AI Stability"),
        ]

    @staticmethod
    def _priority(score: float) -> RecommendationPriority:
        if score >= 78:
            return "critical"
        if score >= 58:
            return "high"
        if score >= 38:
            return "medium"
        return "low"

    @staticmethod
    def _append_jsonl(path: Path, payload: dict[str, object]) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload) + "\n")

    @staticmethod
    def _feedback_signal() -> float:
        if not FEEDBACK_PATH.exists():
            return 0.65
        records: list[float] = []
        for line in FEEDBACK_PATH.read_text(encoding="utf-8").splitlines()[-40:]:
            try:
                records.append(float(json.loads(line).get("learning_signal", 0.65)))
            except json.JSONDecodeError:
                continue
        return round(mean(records), 3) if records else 0.65


recommendation_service = RecommendationService()
