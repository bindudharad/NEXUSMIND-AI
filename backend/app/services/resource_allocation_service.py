from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, pstdev
from threading import Lock

import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import train_test_split

from app.core.cache import TTLResponseCache
from app.schemas.resource_allocation import (
    AssignmentRecommendation,
    CapacityForecastPoint,
    ResourceAllocationRequest,
    ResourceAllocationResponse,
    ResourceDependencySignal,
    ResourceEmployeeProfile,
    ResourceOptimizationSummary,
    ResourceRiskAlert,
    ResourceTaskProfile,
    SprintPlanningRecommendation,
    WorkforceDependencyEdge,
    WorkloadBalanceItem,
)


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
HISTORY_PATH = DATA_DIR / "resource_allocation_history.jsonl"
ARTIFACT_DIR = Path(__file__).resolve().parents[1] / "ai" / "artifacts"
MODEL_PATH = ARTIFACT_DIR / "resource_allocation_models.joblib"
METRICS_PATH = ARTIFACT_DIR / "resource_allocation_metrics.json"


class ResourceAllocationModel:
    model_name = "RandomForest Resource Allocation Optimizer"
    feature_names = [
        "skill_similarity",
        "available_ratio",
        "current_utilization",
        "burnout_risk",
        "stress_score",
        "productivity",
        "historical_delivery_speed",
        "collaboration_score",
        "learning_agility",
        "focus_score",
        "task_priority",
        "deadline_pressure",
        "task_complexity",
        "dependency_pressure",
        "revenue_impact",
    ]

    def __init__(self) -> None:
        ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
        self.match_model: RandomForestRegressor | None = None
        self.delay_model: RandomForestRegressor | None = None
        self.metrics: dict[str, float | int | str] = {}
        self._load_or_train()

    def _load_or_train(self) -> None:
        if MODEL_PATH.exists() and METRICS_PATH.exists():
            bundle = joblib.load(MODEL_PATH)
            self.match_model = bundle["match"]
            self.delay_model = bundle["delay"]
            self.metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
            return
        self.train()

    def train(self) -> dict[str, float | int | str]:
        rng = np.random.default_rng(712)
        features, match_target, delay_target = self._dataset(rng, 5600)
        x_train, x_test, match_train, match_test, delay_train, delay_test = train_test_split(
            features,
            match_target,
            delay_target,
            test_size=0.22,
            random_state=29,
        )
        self.match_model = RandomForestRegressor(n_estimators=260, max_depth=13, min_samples_leaf=4, random_state=29, n_jobs=-1)
        self.delay_model = RandomForestRegressor(n_estimators=220, max_depth=12, min_samples_leaf=4, random_state=31, n_jobs=-1)
        self.match_model.fit(x_train, match_train)
        self.delay_model.fit(x_train, delay_train)
        match_pred = self.match_model.predict(x_test)
        delay_pred = self.delay_model.predict(x_test)
        self.metrics = {
            "model": self.model_name,
            "training_examples": len(features),
            "match_mae": round(float(mean_absolute_error(match_test, match_pred)), 3),
            "match_r2": round(float(r2_score(match_test, match_pred)), 3),
            "delay_mae": round(float(mean_absolute_error(delay_test, delay_pred)), 3),
            "delay_r2": round(float(r2_score(delay_test, delay_pred)), 3),
        }
        joblib.dump({"match": self.match_model, "delay": self.delay_model}, MODEL_PATH)
        METRICS_PATH.write_text(json.dumps(self.metrics, indent=2), encoding="utf-8")
        return self.metrics

    def predict(self, rows: list[list[float]]) -> tuple[np.ndarray, np.ndarray]:
        if self.match_model is None or self.delay_model is None:
            self.train()
        matrix = np.array(rows, dtype=np.float32)
        match = self.match_model.predict(matrix) if self.match_model else np.zeros(len(matrix))
        delay = self.delay_model.predict(matrix) if self.delay_model else np.zeros(len(matrix))
        return np.clip(match, 0, 100), np.clip(delay, 0, 100)

    @staticmethod
    def _dataset(rng: np.random.Generator, rows: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        skill = rng.beta(4.2, 2.0, rows).clip(0, 1)
        available = rng.beta(3.8, 2.5, rows).clip(0, 1)
        utilization = rng.normal(0.76, 0.24, rows).clip(0, 1.45)
        burnout = rng.beta(2.0, 4.4, rows).clip(0, 1)
        stress = rng.beta(2.2, 4.0, rows).clip(0, 1)
        productivity = rng.beta(5.4, 2.0, rows).clip(0, 1)
        delivery = rng.beta(5.0, 2.2, rows).clip(0, 1)
        collaboration = rng.beta(4.5, 2.3, rows).clip(0, 1)
        learning = rng.beta(4.0, 2.4, rows).clip(0, 1)
        focus = rng.beta(4.2, 2.5, rows).clip(0, 1)
        priority = rng.integers(1, 6, rows) / 5
        deadline = rng.beta(2.8, 2.8, rows).clip(0, 1)
        complexity = rng.beta(2.8, 2.6, rows).clip(0, 1)
        dependency = rng.beta(2.1, 4.1, rows).clip(0, 1)
        revenue = rng.beta(1.5, 6.0, rows).clip(0, 1)

        overload = np.maximum(0, utilization - 1)
        match = (
            skill * 31
            + available * 16
            + productivity * 15
            + delivery * 13
            + collaboration * 8
            + learning * 6
            + focus * 6
            + priority * 7
            + revenue * 5
            - burnout * 17
            - stress * 10
            - overload * 24
            - complexity * np.maximum(0, 0.68 - skill) * 18
            + rng.normal(0, 2.5, rows)
        ).clip(0, 100)
        delay = (
            deadline * 24
            + complexity * 18
            + dependency * 17
            + overload * 28
            + burnout * 13
            + stress * 9
            - skill * 18
            - productivity * 10
            - delivery * 11
            - available * 8
            + rng.normal(0, 2.6, rows)
        ).clip(0, 100)
        features = np.column_stack(
            [
                skill,
                available,
                utilization,
                burnout,
                stress,
                productivity,
                delivery,
                collaboration,
                learning,
                focus,
                priority,
                deadline,
                complexity,
                dependency,
                revenue,
            ]
        ).astype(np.float32)
        return features, match.astype(np.float32), delay.astype(np.float32)


class ResourceAllocationService:
    model_name = "AI Resource Allocation System"
    optimization_model = "Deadline-aware greedy constraint optimizer with burnout safety penalties"
    graph_model = "Workforce dependency graph centrality and bottleneck propagation model"

    def __init__(self) -> None:
        self._cache: TTLResponseCache[ResourceAllocationResponse] = TTLResponseCache(ttl_seconds=8)
        self._lock = Lock()
        self._ml = ResourceAllocationModel()
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def optimize(self, payload: ResourceAllocationRequest | None = None) -> ResourceAllocationResponse:
        if payload is None:
            return self._cache.get_or_set(self._default_uncached)
        return self._optimize_uncached(payload)

    def _default_uncached(self) -> ResourceAllocationResponse:
        return self._optimize_uncached(self.default_request())

    def _optimize_uncached(self, payload: ResourceAllocationRequest) -> ResourceAllocationResponse:
        request = payload or self.default_request()
        employees = request.employees or self.default_request().employees
        tasks = request.tasks or self.default_request().tasks
        dependencies = request.dependencies or self.default_request().dependencies
        graph_edges, task_pressure = self._dependency_graph(tasks, dependencies)
        assignments, optimized_hours = self._assignments(request, employees, tasks, task_pressure)
        balance = self._workload_balance(employees, optimized_hours)
        summary = self._summary(request, employees, tasks, assignments, balance, optimized_hours)
        forecast = self._capacity_forecast(request, employees, tasks, balance, summary, task_pressure)
        sprint_plan = self._sprint_plan(summary, assignments, balance, forecast)
        alerts = self._risk_alerts(assignments, balance, forecast, graph_edges)
        insights = self._executive_insights(request, assignments, balance, forecast, summary)
        response = ResourceAllocationResponse(
            model=self.model_name,
            generated_at=datetime.now(timezone.utc),
            department=request.department,
            sprint_name=request.sprint_name,
            planning_horizon_days=request.planning_horizon_days,
            ml_model=str(self._ml.metrics.get("model", ResourceAllocationModel.model_name)),
            optimization_model=self.optimization_model,
            graph_model=self.graph_model,
            assignments=assignments,
            workload_balance=balance,
            capacity_forecast=forecast,
            sprint_plan=sprint_plan,
            dependency_graph=graph_edges,
            risk_alerts=alerts,
            executive_insights=insights,
            summary=summary,
            storage=str(HISTORY_PATH),
        )
        self._append_jsonl(response.model_dump(mode="json"))
        return response

    async def stream(self, payload: ResourceAllocationRequest | None = None):
        base = payload or self.default_request()
        scenarios = [
            base,
            self._scenario_variant(base, urgency_delta=0.1, workload_delta=2.5, burnout_delta=0.04),
            self._scenario_variant(base, urgency_delta=0.22, workload_delta=5.0, burnout_delta=0.09),
        ]
        for sequence, scenario in enumerate(scenarios, start=1):
            response = self.optimize(scenario)
            data = response.model_dump(mode="json")
            data["summary"]["stream_sequence"] = sequence
            yield f"event: resource_allocation\ndata: {json.dumps(data)}\n\n"
            await asyncio.sleep(0.8)

    def _assignments(
        self,
        request: ResourceAllocationRequest,
        employees: list[ResourceEmployeeProfile],
        tasks: list[ResourceTaskProfile],
        task_pressure: dict[str, float],
    ) -> tuple[list[AssignmentRecommendation], dict[str, float]]:
        optimized_hours = {employee.employee_id: employee.current_hours for employee in employees}
        ordered_tasks = sorted(
            tasks,
            key=lambda task: (task.priority, 1 / max(task.deadline_days, 1), task_pressure.get(task.task_id, 0), task.complexity),
            reverse=True,
        )
        assignments: list[AssignmentRecommendation] = []
        for task in ordered_tasks:
            rows: list[list[float]] = []
            skill_scores: list[float] = []
            for employee in employees:
                skill = self._skill_similarity(employee, task)
                skill_scores.append(skill)
                rows.append(self._feature_row(employee, task, optimized_hours[employee.employee_id], task_pressure.get(task.task_id, 0), skill))
            match_predictions, delay_predictions = self._ml.predict(rows)
            candidates: list[tuple[float, ResourceEmployeeProfile, float, float, float, float, float]] = []
            for employee, skill, match_score, delay_risk in zip(employees, skill_scores, match_predictions, delay_predictions):
                effective_capacity = max(employee.capacity_hours * employee.availability, 1)
                projected_hours = optimized_hours[employee.employee_id] + task.effort_hours
                utilization_after = projected_hours / effective_capacity
                burnout_after = self._clip(employee.burnout_risk * 100 + max(0, utilization_after - 0.88) * 42 + task.cognitive_load * 9 + employee.stress_score * 8)
                graph_fit = self._clip(100 - task_pressure.get(task.task_id, 0) * 45 + employee.collaboration_score * 12)
                objective_bonus = self._objective_bonus(request.objective, employee, task, skill, utilization_after)
                safety_penalty = max(0, utilization_after - 1.0) * 24 + employee.burnout_risk * 9
                score = self._clip(match_score * 0.58 + skill * 100 * 0.22 + graph_fit * 0.08 + objective_bonus - delay_risk * 0.16 - safety_penalty)
                candidates.append((score, employee, skill, float(delay_risk), utilization_after, burnout_after, graph_fit))
            candidates.sort(key=lambda item: item[0], reverse=True)
            best = candidates[0]
            score, employee, skill, delay_risk, utilization_after, burnout_after, graph_fit = best
            optimized_hours[employee.employee_id] += task.effort_hours
            alternatives = [candidate[1].name for candidate in candidates[1:3]]
            delivery_success = self._clip(100 - delay_risk + skill * 9 - max(0, utilization_after - 1) * 18)
            confidence = self._clip01(0.56 + skill * 0.22 + employee.historical_delivery_speed * 0.12 + employee.collaboration_score * 0.08 - task.complexity * 0.06)
            rationale = (
                f"Assign {task.title} to {employee.name}: {round(skill * 100)}% semantic skill fit, "
                f"{round((1 - min(utilization_after, 1.4) / 1.4) * 100)}% remaining load safety, "
                f"and {round(delivery_success)}% delivery success under current deadline pressure."
            )
            assignments.append(
                AssignmentRecommendation(
                    task_id=task.task_id,
                    task_title=task.title,
                    employee_id=employee.employee_id,
                    employee_name=employee.name,
                    team=employee.team,
                    assignment_score=round(score, 2),
                    confidence=round(confidence, 3),
                    skill_match_score=round(skill * 100, 2),
                    capacity_after_assignment=round(utilization_after * 100, 2),
                    delivery_success_probability=round(delivery_success, 2),
                    delay_risk=round(float(delay_risk), 2),
                    burnout_risk_after_assignment=round(burnout_after, 2),
                    graph_bottleneck_score=round(task_pressure.get(task.task_id, 0) * 100, 2),
                    rationale=rationale,
                    alternatives=alternatives,
                    optimization_model=self.optimization_model,
                )
            )
        assignments.sort(key=lambda item: (item.assignment_score, item.delivery_success_probability), reverse=True)
        return assignments, optimized_hours

    def _workload_balance(self, employees: list[ResourceEmployeeProfile], optimized_hours: dict[str, float]) -> list[WorkloadBalanceItem]:
        items: list[WorkloadBalanceItem] = []
        for employee in employees:
            effective_capacity = max(employee.capacity_hours * employee.availability, 1)
            current_utilization = employee.current_hours / effective_capacity * 100
            optimized_utilization = optimized_hours.get(employee.employee_id, employee.current_hours) / effective_capacity * 100
            delta = optimized_hours.get(employee.employee_id, employee.current_hours) - employee.current_hours
            overload_risk = self._clip(max(0, optimized_utilization - 92) * 1.4 + employee.burnout_risk * 45 + employee.stress_score * 20)
            if optimized_utilization > 104:
                action = "Reduce allocation"
                rationale = f"{employee.name} remains above safe capacity after optimization; move low-priority work to a lower-risk teammate."
            elif delta > 0:
                action = "Increase allocation"
                rationale = f"{employee.name} receives {round(delta, 1)}h because skill fit and capacity safety outscore alternatives."
            elif current_utilization > 100 and optimized_utilization <= current_utilization:
                action = "Protect capacity"
                rationale = f"{employee.name} is already overloaded; optimizer avoids adding new sprint work."
            else:
                action = "Maintain"
                rationale = f"{employee.name} remains within sustainable capacity for the planning horizon."
            items.append(
                WorkloadBalanceItem(
                    employee_id=employee.employee_id,
                    name=employee.name,
                    team=employee.team,
                    current_utilization=round(current_utilization, 2),
                    optimized_utilization=round(optimized_utilization, 2),
                    hours_delta=round(delta, 2),
                    overload_risk=round(overload_risk, 2),
                    action=action,
                    rationale=rationale,
                )
            )
        return sorted(items, key=lambda item: item.overload_risk, reverse=True)

    def _capacity_forecast(
        self,
        request: ResourceAllocationRequest,
        employees: list[ResourceEmployeeProfile],
        tasks: list[ResourceTaskProfile],
        balance: list[WorkloadBalanceItem],
        summary: ResourceOptimizationSummary,
        task_pressure: dict[str, float],
    ) -> list[CapacityForecastPoint]:
        total_capacity = sum(employee.capacity_hours * employee.availability for employee in employees)
        base_committed = sum(employee.current_hours for employee in employees) + sum(task.effort_hours for task in tasks)
        avg_burnout = mean([employee.burnout_risk for employee in employees]) * 100 if employees else 0
        avg_bottleneck = mean(task_pressure.values()) * 100 if task_pressure else 0
        forecast: list[CapacityForecastPoint] = []
        for index in range(4):
            growth = 1 + index * 0.055
            committed = base_committed * growth
            capacity = max(total_capacity * (1 - index * 0.015), 1)
            utilization = committed / capacity * 100
            shortage = max(0, committed - capacity)
            burnout = self._clip(avg_burnout + max(0, utilization - 88) * 0.55 + index * 2.4)
            bottleneck = self._clip(avg_bottleneck + max(0, utilization - 92) * 0.44 + index * 3.1)
            delivery = self._clip(summary.delivery_success_probability - shortage / max(total_capacity, 1) * 48 - index * 2.2)
            forecast.append(
                CapacityForecastPoint(
                    sprint=f"{request.sprint_name} +{index}",
                    capacity_utilization=round(utilization, 2),
                    available_hours=round(max(0, capacity - committed), 2),
                    committed_hours=round(committed, 2),
                    delivery_probability=round(delivery, 2),
                    shortage_hours=round(shortage, 2),
                    burnout_pressure=round(burnout, 2),
                    bottleneck_risk=round(bottleneck, 2),
                )
            )
        return forecast

    def _summary(
        self,
        request: ResourceAllocationRequest,
        employees: list[ResourceEmployeeProfile],
        tasks: list[ResourceTaskProfile],
        assignments: list[AssignmentRecommendation],
        balance: list[WorkloadBalanceItem],
        optimized_hours: dict[str, float],
    ) -> ResourceOptimizationSummary:
        total_capacity = sum(max(employee.capacity_hours * employee.availability, 1) for employee in employees)
        current_hours = sum(employee.current_hours for employee in employees)
        optimized_total = sum(optimized_hours.values())
        utilization = optimized_total / max(total_capacity, 1) * 100
        current_overload = sum(max(0, employee.current_hours - employee.capacity_hours * employee.availability) for employee in employees)
        optimized_overload = sum(max(0, optimized_hours[employee.employee_id] - employee.capacity_hours * employee.availability) for employee in employees)
        overload_reduction = self._clip((current_overload - optimized_overload) / max(current_overload, 1) * 100)
        delivery_success = mean([assignment.delivery_success_probability for assignment in assignments]) if assignments else 0
        sprint_completion = self._clip(delivery_success - max(0, utilization - 92) * 0.72 - pstdev([item.optimized_utilization for item in balance]) * 0.18 if len(balance) > 1 else delivery_success)
        projected_delay = self._clip(max(0, 100 - sprint_completion) / 18 + max(0, utilization - 100) / 12, upper=90)
        cost_avoidance = sum(task.revenue_impact for task in tasks) * (overload_reduction / 100) * 0.018 + max(0, current_hours - optimized_total) * mean([employee.hourly_cost for employee in employees]) if employees else 0
        return ResourceOptimizationSummary(
            employees_analyzed=len(employees),
            tasks_analyzed=len(tasks),
            assignments_generated=len(assignments),
            capacity_utilization=round(utilization, 2),
            overload_reduction=round(overload_reduction, 2),
            delivery_success_probability=round(delivery_success, 2),
            sprint_completion_probability=round(sprint_completion, 2),
            projected_delay_days=round(projected_delay, 2),
            estimated_cost_avoidance=round(max(0, cost_avoidance), 2),
        )

    def _sprint_plan(
        self,
        summary: ResourceOptimizationSummary,
        assignments: list[AssignmentRecommendation],
        balance: list[WorkloadBalanceItem],
        forecast: list[CapacityForecastPoint],
    ) -> list[SprintPlanningRecommendation]:
        overloaded = [item for item in balance if item.optimized_utilization > 100]
        high_risk_tasks = [item for item in assignments if item.delay_risk > 48]
        recommendations = [
            SprintPlanningRecommendation(
                title="Commit optimized sprint allocation",
                action=f"Lock {summary.assignments_generated} task-owner assignments and track daily capacity drift.",
                expected_impact=f"Expected sprint completion probability improves to {round(summary.sprint_completion_probability)}%.",
                priority="medium" if summary.sprint_completion_probability >= 72 else "high",
                confidence=0.86,
            )
        ]
        if overloaded:
            recommendations.append(
                SprintPlanningRecommendation(
                    title="Burnout-safe workload guardrail",
                    action=f"Remove or defer low-priority work from {overloaded[0].name} before sprint kickoff.",
                    expected_impact=f"Reduces overload risk from {round(overloaded[0].overload_risk)}% and protects delivery quality.",
                    priority="critical" if overloaded[0].overload_risk >= 75 else "high",
                    confidence=0.88,
                )
            )
        if high_risk_tasks:
            recommendations.append(
                SprintPlanningRecommendation(
                    title="Dependency recovery lane",
                    action=f"Create a blocker-clearing lane for {high_risk_tasks[0].task_title}.",
                    expected_impact="Reduces projected delay by isolating graph bottlenecks from execution work.",
                    priority="high",
                    confidence=0.82,
                )
            )
        if forecast and forecast[-1].capacity_utilization > 105:
            recommendations.append(
                SprintPlanningRecommendation(
                    title="Next sprint intake reduction",
                    action="Reduce next-sprint intake by 10-15% or add specialist capacity.",
                    expected_impact=f"Prevents utilization from reaching {round(forecast[-1].capacity_utilization)}%.",
                    priority="high",
                    confidence=0.84,
                )
            )
        return recommendations

    @staticmethod
    def default_request() -> ResourceAllocationRequest:
        employees = [
            ResourceEmployeeProfile(employee_id="res-backend", name="Aarav Mehta", role="Senior Backend Engineer", team="Platform", department="Engineering", skills=["python", "api architecture", "postgresql", "incident response"], capacity_hours=40, current_hours=37, availability=0.95, productivity=0.84, historical_delivery_speed=0.86, collaboration_score=0.78, learning_agility=0.76, burnout_risk=0.44, stress_score=0.48, focus_score=0.67, hourly_cost=92),
            ResourceEmployeeProfile(employee_id="res-devops", name="Bianca Shah", role="DevOps Reliability Engineer", team="Platform", department="Engineering", skills=["kubernetes", "terraform", "redis", "incident response", "automation"], capacity_hours=40, current_hours=24, availability=0.92, productivity=0.9, historical_delivery_speed=0.91, collaboration_score=0.88, learning_agility=0.74, burnout_risk=0.24, stress_score=0.3, focus_score=0.71, hourly_cost=96),
            ResourceEmployeeProfile(employee_id="res-ml", name="Devika Nair", role="ML Engineer", team="AI", department="AI", skills=["mlops", "forecasting", "python", "model evaluation", "rag"], capacity_hours=40, current_hours=29, availability=0.9, productivity=0.91, historical_delivery_speed=0.88, collaboration_score=0.84, learning_agility=0.9, burnout_risk=0.27, stress_score=0.32, focus_score=0.76, hourly_cost=105),
            ResourceEmployeeProfile(employee_id="res-ui", name="Nina Kapoor", role="Product Designer", team="Experience", department="Design", skills=["dashboard", "ux research", "accessibility", "visual systems"], capacity_hours=36, current_hours=28, availability=0.88, productivity=0.82, historical_delivery_speed=0.8, collaboration_score=0.9, learning_agility=0.78, burnout_risk=0.3, stress_score=0.34, focus_score=0.58, hourly_cost=82),
            ResourceEmployeeProfile(employee_id="res-qa", name="Maya Iyer", role="QA Automation Engineer", team="Quality", department="Engineering", skills=["testing", "automation", "api testing", "python", "release quality"], capacity_hours=38, current_hours=25, availability=0.95, productivity=0.87, historical_delivery_speed=0.89, collaboration_score=0.82, learning_agility=0.72, burnout_risk=0.22, stress_score=0.28, focus_score=0.8, hourly_cost=78),
            ResourceEmployeeProfile(employee_id="res-risk", name="John Rivera", role="Incident Lead", team="Platform", department="Engineering", skills=["api architecture", "incident response", "security", "backend"], capacity_hours=40, current_hours=51, availability=0.82, productivity=0.66, historical_delivery_speed=0.62, collaboration_score=0.6, learning_agility=0.58, burnout_risk=0.82, stress_score=0.88, focus_score=0.33, hourly_cost=110),
        ]
        tasks = [
            ResourceTaskProfile(task_id="task-api", title="Backend API resilience hardening", project="Reliability Recovery", description="Stabilize latency and retry semantics across core FastAPI services.", required_skills=["python", "api architecture", "incident response"], effort_hours=14, complexity=0.74, priority=5, deadline_days=4, revenue_impact=1800000, dependency_task_ids=["task-observability"], preferred_team="Platform", cognitive_load=0.72),
            ResourceTaskProfile(task_id="task-k8s", title="Kubernetes rollout guardrails", project="Reliability Recovery", description="Build deployment safety checks and rollback automation.", required_skills=["kubernetes", "automation", "terraform"], effort_hours=12, complexity=0.69, priority=5, deadline_days=5, revenue_impact=1600000, preferred_team="Platform", cognitive_load=0.64),
            ResourceTaskProfile(task_id="task-mlops", title="Forecast model drift monitor", project="AI Stability", description="Add model drift detection and retraining signal tracking.", required_skills=["mlops", "forecasting", "python"], effort_hours=11, complexity=0.68, priority=4, deadline_days=7, revenue_impact=950000, dependency_task_ids=["task-api"], preferred_team="AI", cognitive_load=0.61),
            ResourceTaskProfile(task_id="task-quality", title="Release quality automation", project="Reliability Recovery", description="Expand regression suites around API and realtime stream behavior.", required_skills=["testing", "automation", "api testing"], effort_hours=9, complexity=0.45, priority=4, deadline_days=6, revenue_impact=700000, dependency_task_ids=["task-api"], preferred_team="Quality", cognitive_load=0.42),
            ResourceTaskProfile(task_id="task-dashboard", title="Executive allocation dashboard", project="Workforce OS", description="Visualize allocation, capacity, bottlenecks, and burnout-safe sprint planning.", required_skills=["dashboard", "ux research", "accessibility"], effort_hours=10, complexity=0.52, priority=3, deadline_days=9, revenue_impact=600000, preferred_team="Experience", cognitive_load=0.48),
            ResourceTaskProfile(task_id="task-observability", title="Incident observability runbook", project="Reliability Recovery", description="Document and automate operational playbooks for incident triage.", required_skills=["incident response", "automation", "redis"], effort_hours=8, complexity=0.5, priority=4, deadline_days=3, revenue_impact=850000, preferred_team="Platform", cognitive_load=0.46),
        ]
        dependencies = [
            ResourceDependencySignal(source_task_id="task-api", target_task_id="task-observability", blocker_type="runbook_dependency", risk_weight=0.74),
            ResourceDependencySignal(source_task_id="task-mlops", target_task_id="task-api", blocker_type="platform_dependency", risk_weight=0.56),
            ResourceDependencySignal(source_task_id="task-quality", target_task_id="task-api", blocker_type="test_fixture_dependency", risk_weight=0.48),
        ]
        return ResourceAllocationRequest(employees=employees, tasks=tasks, dependencies=dependencies)

    @staticmethod
    def _scenario_variant(base: ResourceAllocationRequest, urgency_delta: float, workload_delta: float, burnout_delta: float) -> ResourceAllocationRequest:
        employees = [
            employee.model_copy(
                update={
                    "current_hours": min(120, employee.current_hours + workload_delta * (1.35 if employee.burnout_risk > 0.5 else 0.75)),
                    "burnout_risk": min(1, employee.burnout_risk + burnout_delta * (1.25 if employee.current_hours / employee.capacity_hours > 0.9 else 0.65)),
                    "stress_score": min(1, employee.stress_score + burnout_delta * 0.8),
                    "availability": max(0.45, employee.availability - burnout_delta * 0.18),
                }
            )
            for employee in (base.employees or ResourceAllocationService.default_request().employees)
        ]
        tasks = [
            task.model_copy(
                update={
                    "deadline_days": max(1, task.deadline_days * (1 - urgency_delta)),
                    "complexity": min(1, task.complexity + urgency_delta * 0.16),
                    "cognitive_load": min(1, task.cognitive_load + urgency_delta * 0.12),
                }
            )
            for task in (base.tasks or ResourceAllocationService.default_request().tasks)
        ]
        return base.model_copy(update={"employees": employees, "tasks": tasks, "realtime": True})

    def _dependency_graph(
        self,
        tasks: list[ResourceTaskProfile],
        dependencies: list[ResourceDependencySignal],
    ) -> tuple[list[WorkforceDependencyEdge], dict[str, float]]:
        pressure: dict[str, float] = {task.task_id: min(1, len(task.dependency_task_ids) * 0.18 + task.complexity * 0.2) for task in tasks}
        edges: list[WorkforceDependencyEdge] = []
        known_tasks = {task.task_id: task for task in tasks}
        for dependency in dependencies:
            source = known_tasks.get(dependency.source_task_id)
            target = known_tasks.get(dependency.target_task_id)
            if not source or not target:
                continue
            urgency = min(1, 1 / max(source.deadline_days, 1) * 5)
            bottleneck = self._clip((dependency.risk_weight * 0.54 + source.complexity * 0.22 + urgency * 0.24) * 100)
            pressure[source.task_id] = min(1, pressure.get(source.task_id, 0) + dependency.risk_weight * 0.36)
            pressure[target.task_id] = min(1, pressure.get(target.task_id, 0) + dependency.risk_weight * 0.18)
            edges.append(
                WorkforceDependencyEdge(
                    source=source.title,
                    target=target.title,
                    edge_type=dependency.blocker_type,
                    weight=round(dependency.risk_weight, 3),
                    bottleneck_score=round(bottleneck, 2),
                )
            )
        if not edges:
            for task in sorted(tasks, key=lambda item: item.complexity, reverse=True)[:3]:
                edges.append(
                    WorkforceDependencyEdge(
                        source=task.project,
                        target=task.title,
                        edge_type="complexity_pressure",
                        weight=round(task.complexity, 3),
                        bottleneck_score=round(self._clip(task.complexity * 72 + task.priority * 4), 2),
                    )
                )
        return edges, pressure

    def _skill_similarity(self, employee: ResourceEmployeeProfile, task: ResourceTaskProfile) -> float:
        employee_doc = " ".join([employee.role, employee.team, *employee.skills]).lower()
        task_doc = " ".join([task.title, task.description, task.project, *task.required_skills]).lower()
        employee_terms = {term.strip().lower() for skill in employee.skills for term in [skill, *skill.replace("-", " ").split()]}
        task_terms = {term.strip().lower() for skill in task.required_skills for term in [skill, *skill.replace("-", " ").split()]}
        lexical = len(employee_terms.intersection(task_terms)) / max(len(task_terms), 1)
        try:
            matrix = TfidfVectorizer(ngram_range=(1, 2)).fit_transform([employee_doc, task_doc])
            semantic = float(cosine_similarity(matrix[0], matrix[1])[0][0])
        except ValueError:
            semantic = 0.0
        return self._clip01(semantic * 0.58 + lexical * 0.42)

    def _feature_row(
        self,
        employee: ResourceEmployeeProfile,
        task: ResourceTaskProfile,
        current_hours: float,
        dependency_pressure: float,
        skill_similarity: float,
    ) -> list[float]:
        effective_capacity = max(employee.capacity_hours * employee.availability, 1)
        available_ratio = max(0, effective_capacity - current_hours) / effective_capacity
        utilization = current_hours / effective_capacity
        deadline_pressure = min(1, 5 / max(task.deadline_days, 1))
        revenue = min(task.revenue_impact / 5000000, 1)
        return [
            skill_similarity,
            self._clip01(available_ratio),
            min(utilization, 1.5),
            employee.burnout_risk,
            employee.stress_score,
            employee.productivity,
            employee.historical_delivery_speed,
            employee.collaboration_score,
            employee.learning_agility,
            employee.focus_score,
            task.priority / 5,
            deadline_pressure,
            task.complexity,
            self._clip01(dependency_pressure),
            revenue,
        ]

    @staticmethod
    def _objective_bonus(objective: str, employee: ResourceEmployeeProfile, task: ResourceTaskProfile, skill: float, utilization_after: float) -> float:
        if objective == "delivery_speed":
            return employee.historical_delivery_speed * 7 + employee.productivity * 5 + task.priority
        if objective == "burnout_safe":
            return (1 - employee.burnout_risk) * 9 + max(0, 1 - utilization_after) * 8
        if objective == "skill_depth":
            return skill * 13
        if objective == "cost_efficiency":
            return max(0, 1 - employee.hourly_cost / 180) * 9
        return employee.collaboration_score * 4 + (1 - employee.burnout_risk) * 5 + skill * 4

    @staticmethod
    def _risk_alerts(
        assignments: list[AssignmentRecommendation],
        balance: list[WorkloadBalanceItem],
        forecast: list[CapacityForecastPoint],
        graph_edges: list[WorkforceDependencyEdge],
    ) -> list[ResourceRiskAlert]:
        alerts: list[ResourceRiskAlert] = []
        overloaded = [item for item in balance if item.overload_risk >= 62]
        if overloaded:
            top = overloaded[0]
            alerts.append(
                ResourceRiskAlert(
                    severity="critical" if top.overload_risk >= 80 else "high",
                    title="Burnout-safe allocation breach",
                    probability=round(top.overload_risk, 2),
                    affected_entities=[top.name],
                    intervention="Redistribute non-critical work and preserve recovery capacity before sprint kickoff.",
                )
            )
        delayed = [assignment for assignment in assignments if assignment.delay_risk >= 50]
        if delayed:
            top_assignment = max(delayed, key=lambda item: item.delay_risk)
            alerts.append(
                ResourceRiskAlert(
                    severity="high",
                    title="Deadline delivery risk",
                    probability=round(top_assignment.delay_risk, 2),
                    affected_entities=[top_assignment.task_title, top_assignment.employee_name],
                    intervention="Pair with alternate owner or split task into a blocker-clearing lane.",
                )
            )
        if forecast and forecast[-1].shortage_hours > 0:
            alerts.append(
                ResourceRiskAlert(
                    severity="high" if forecast[-1].shortage_hours > 16 else "medium",
                    title="Capacity shortage forecast",
                    probability=round(forecast[-1].bottleneck_risk, 2),
                    affected_entities=[forecast[-1].sprint],
                    intervention="Reduce intake or add temporary specialist capacity for the next planning window.",
                )
            )
        if graph_edges:
            edge = max(graph_edges, key=lambda item: item.bottleneck_score)
            if edge.bottleneck_score >= 52:
                alerts.append(
                    ResourceRiskAlert(
                        severity="high" if edge.bottleneck_score >= 70 else "medium",
                        title="Dependency bottleneck propagation",
                        probability=round(edge.bottleneck_score, 2),
                        affected_entities=[edge.source, edge.target],
                        intervention="Clear dependency before assigning dependent execution work.",
                    )
                )
        return alerts[:5]

    @staticmethod
    def _executive_insights(
        request: ResourceAllocationRequest,
        assignments: list[AssignmentRecommendation],
        balance: list[WorkloadBalanceItem],
        forecast: list[CapacityForecastPoint],
        summary: ResourceOptimizationSummary,
    ) -> list[str]:
        best = assignments[0] if assignments else None
        highest_risk = balance[0] if balance else None
        future = forecast[-1] if forecast else None
        insights = [
            f"{request.sprint_name} is operating at {round(summary.capacity_utilization)}% optimized utilization with {round(summary.sprint_completion_probability)}% sprint completion probability.",
        ]
        if best:
            insights.append(f"Best task-owner match: {best.task_title} to {best.employee_name} at {round(best.assignment_score)}% allocation score.")
        if highest_risk:
            insights.append(f"Highest workload risk remains {highest_risk.name} at {round(highest_risk.overload_risk)}% overload risk after optimization.")
        if future:
            insights.append(f"Capacity forecast shows {round(future.shortage_hours, 1)}h shortage risk by {future.sprint} if intake continues unchanged.")
        return insights

    @staticmethod
    def _clip(value: float, lower: float = 0, upper: float = 100) -> float:
        return float(max(lower, min(upper, value)))

    @staticmethod
    def _clip01(value: float) -> float:
        return float(max(0, min(1, value)))

    def _append_jsonl(self, payload: dict[str, object]) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with self._lock:
            with HISTORY_PATH.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload) + "\n")


resource_allocation_service = ResourceAllocationService()
