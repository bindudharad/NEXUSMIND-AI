from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from threading import Lock

import numpy as np

from app.core.cache import TTLResponseCache
from app.ai.project_failure_engine import project_failure_engine
from app.schemas.project_failure import (
    ProjectFailurePrediction,
    ProjectFailureRequest,
    ProjectFailureResponse,
    ProjectFailureSummary,
    ProjectMetricPoint,
    ProjectProfile,
    ProjectRecommendation,
    ProjectRiskForecastPoint,
    ProjectRiskSeverity,
    ProjectRiskSignal,
)


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
HISTORY_PATH = DATA_DIR / "project_failure_history.jsonl"


class ProjectFailureService:
    model_name = "RandomForest/XGBoost Project Failure Forecaster"

    def __init__(self) -> None:
        self._lock = Lock()
        self._default_cache: TTLResponseCache[ProjectFailureResponse] = TTLResponseCache(ttl_seconds=8)
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def analyze(self, payload: ProjectFailureRequest | None = None) -> ProjectFailureResponse:
        if payload is None:
            return self._default_cache.get_or_set(self._analyze_default_uncached)
        return self._analyze_uncached(payload)

    def _analyze_default_uncached(self) -> ProjectFailureResponse:
        return self._analyze_uncached(self.default_request())

    def _analyze_uncached(self, payload: ProjectFailureRequest) -> ProjectFailureResponse:
        request = payload or self.default_request()
        if not request.projects:
            request = request.model_copy(update={"projects": self.default_request().projects})
        predictions = [self._prediction(project, request.horizon_days) for project in request.projects]
        portfolio_recommendations = self._portfolio_recommendations(predictions)
        response = ProjectFailureResponse(
            model=self.model_name,
            generated_at=datetime.now(timezone.utc),
            horizon_days=request.horizon_days,
            predictions=sorted(predictions, key=lambda item: item.failure_probability, reverse=True),
            portfolio_recommendations=portfolio_recommendations,
            heatmap=self._heatmap(predictions),
            summary=self._summary(predictions),
            storage=str(HISTORY_PATH),
        )
        self._append_jsonl(response.model_dump(mode="json"))
        return response

    async def stream(self, payload: ProjectFailureRequest | None = None):
        base = payload or self.default_request()
        scenarios = [
            base,
            self._scenario_variant(base, stress_delta=0.07, dependency_delta=1, budget_delta=0.05),
            self._scenario_variant(base, stress_delta=0.14, dependency_delta=3, budget_delta=0.1),
        ]
        for sequence, scenario in enumerate(scenarios, start=1):
            response = self.analyze(scenario)
            data = response.model_dump(mode="json")
            data["summary"]["stream_sequence"] = sequence
            yield f"event: project_failure\ndata: {json.dumps(data)}\n\n"
            await asyncio.sleep(0.8)

    @staticmethod
    def default_request() -> ProjectFailureRequest:
        return ProjectFailureRequest(
            horizon_days=21,
            projects=[
                ProjectProfile(
                    project_id="project-alpha",
                    project_name="Project Alpha Revenue Platform",
                    department="Engineering",
                    team_name="Development Team",
                    days_to_deadline=13,
                    budget_utilization=0.86,
                    required_skills=["python", "api", "security", "mlops"],
                    available_skills=["python", "api", "security"],
                    team_size=18,
                    critical_dependency_count=8,
                    historical_delivery_rate=0.58,
                    current_scope_completion=0.47,
                    executive_visibility=0.9,
                    history=ProjectFailureService._history(
                        velocity=[0.68, 0.63, 0.59, 0.52, 0.47, 0.42, 0.36],
                        completion=[0.66, 0.63, 0.6, 0.55, 0.5, 0.45, 0.39],
                        burnout=[0.52, 0.58, 0.64, 0.69, 0.74, 0.8, 0.86],
                        communication=[0.69, 0.64, 0.59, 0.55, 0.49, 0.44, 0.38],
                        resource=[0.68, 0.64, 0.59, 0.54, 0.5, 0.46, 0.41],
                        dependency_start=5,
                        risk_start=10,
                        scope_change=0.46,
                        defect=0.32,
                        rework=0.28,
                        meeting=0.78,
                        budget=0.94,
                        compatibility=0.48,
                    ),
                ),
                ProjectProfile(
                    project_id="project-beta",
                    project_name="Project Beta Workflow Modernization",
                    department="Operations",
                    team_name="Automation Team",
                    days_to_deadline=43,
                    budget_utilization=0.54,
                    required_skills=["automation", "workflow", "analytics"],
                    available_skills=["automation", "workflow", "analytics", "python"],
                    team_size=10,
                    critical_dependency_count=2,
                    historical_delivery_rate=0.88,
                    current_scope_completion=0.71,
                    executive_visibility=0.48,
                    history=ProjectFailureService._history(
                        velocity=[0.72, 0.74, 0.75, 0.77, 0.79, 0.8, 0.82],
                        completion=[0.7, 0.72, 0.75, 0.76, 0.79, 0.8, 0.83],
                        burnout=[0.32, 0.29, 0.31, 0.3, 0.28, 0.27, 0.26],
                        communication=[0.78, 0.8, 0.82, 0.81, 0.84, 0.86, 0.87],
                        resource=[0.75, 0.77, 0.79, 0.8, 0.82, 0.83, 0.84],
                        dependency_start=1,
                        risk_start=3,
                        scope_change=0.12,
                        defect=0.09,
                        rework=0.08,
                        meeting=0.32,
                        budget=0.52,
                        compatibility=0.82,
                    ),
                ),
                ProjectProfile(
                    project_id="project-delta",
                    project_name="Project Delta Security Migration",
                    department="Security",
                    team_name="Platform Reliability",
                    days_to_deadline=24,
                    budget_utilization=1.08,
                    required_skills=["kubernetes", "security", "networking", "automation"],
                    available_skills=["kubernetes", "security", "automation"],
                    team_size=12,
                    critical_dependency_count=6,
                    historical_delivery_rate=0.72,
                    current_scope_completion=0.55,
                    executive_visibility=0.78,
                    history=ProjectFailureService._history(
                        velocity=[0.64, 0.62, 0.61, 0.59, 0.56, 0.54, 0.52],
                        completion=[0.61, 0.6, 0.58, 0.56, 0.54, 0.52, 0.5],
                        burnout=[0.46, 0.5, 0.54, 0.57, 0.61, 0.64, 0.67],
                        communication=[0.72, 0.69, 0.68, 0.65, 0.62, 0.59, 0.56],
                        resource=[0.66, 0.63, 0.61, 0.58, 0.55, 0.53, 0.51],
                        dependency_start=4,
                        risk_start=8,
                        scope_change=0.31,
                        defect=0.24,
                        rework=0.22,
                        meeting=0.56,
                        budget=1.08,
                        compatibility=0.61,
                    ),
                ),
            ],
        )

    def _prediction(self, project: ProjectProfile, horizon_days: int) -> ProjectFailurePrediction:
        prediction = project_failure_engine.predict(project)
        latest = self._latest(project)
        features = prediction.features
        failure_score, delay_score, budget_score = self._calibrated_scores(project, latest, prediction)
        team_collapse = self._clip100(100 * (latest.team_burnout * 0.34 + (1 - latest.resource_allocation) * 0.23 + (1 - latest.team_compatibility) * 0.2 + features["dependency_pressure"] * 0.13 + features["open_risk_pressure"] * 0.1))
        productivity_slowdown = self._clip100(100 * ((1 - latest.sprint_velocity) * 0.34 + (1 - latest.task_completion_rate) * 0.27 + latest.meeting_load * 0.14 + latest.team_burnout * 0.16 + max(0, 1 - latest.communication_score) * 0.09))
        resource_shortage = self._clip100(100 * ((1 - latest.resource_allocation) * 0.48 + (1 - features["skill_coverage"]) * 0.24 + features["dependency_pressure"] * 0.16 + latest.open_risks / 60 * 0.12))
        burnout_impact = self._clip100(100 * (latest.team_burnout * 0.72 + latest.meeting_load * 0.16 + max(0, 1 - latest.task_completion_rate) * 0.12))
        communication = self._clip100(100 * ((1 - latest.communication_score) * 0.62 + latest.meeting_load * 0.18 + latest.team_burnout * 0.2))
        dependency = self._clip100(100 * (features["dependency_pressure"] * 0.68 + project.critical_dependency_count / 30 * 0.22 + latest.open_risks / 60 * 0.1))
        instability = self._clip100(mean([failure_score, delay_score, team_collapse, dependency, burnout_impact]))
        health_score = self._clip100(100 - mean([failure_score, delay_score, budget_score, instability]))
        risk_signals = self._risk_signals(
            project,
            failure_score,
            delay_score,
            budget_score,
            team_collapse,
            productivity_slowdown,
            resource_shortage,
            burnout_impact,
            communication,
            dependency,
        )
        recommendations = self._recommendations(project, risk_signals, failure_score, delay_score)
        return ProjectFailurePrediction(
            project_id=project.project_id,
            project_name=project.project_name,
            department=project.department,
            team_name=project.team_name,
            failure_probability=round(failure_score, 2),
            deadline_miss_probability=round(delay_score, 2),
            budget_overrun_probability=round(budget_score, 2),
            team_collapse_risk=round(team_collapse, 2),
            productivity_slowdown=round(productivity_slowdown, 2),
            resource_shortage_impact=round(resource_shortage, 2),
            burnout_impact=round(burnout_impact, 2),
            communication_bottleneck_risk=round(communication, 2),
            dependency_failure_impact=round(dependency, 2),
            operational_instability=round(instability, 2),
            confidence=prediction.confidence,
            health_score=round(health_score, 2),
            forecast=self._forecast(project, horizon_days),
            risk_signals=risk_signals,
            recommendations=recommendations,
        )

    def _forecast(self, project: ProjectProfile, horizon_days: int) -> list[ProjectRiskForecastPoint]:
        latest = self._latest(project)
        points: list[ProjectRiskForecastPoint] = []
        simulated = project.model_copy(deep=True)
        for day in range(1, horizon_days + 1):
            pressure = day / max(horizon_days, 1)
            simulated_latest = latest.model_copy(
                update={
                    "timestamp": datetime.now(timezone.utc) + timedelta(days=day),
                    "sprint_velocity": self._clip01(latest.sprint_velocity - latest.team_burnout * 0.085 * pressure - latest.scope_change_rate * 0.045 * pressure),
                    "task_completion_rate": self._clip01(latest.task_completion_rate - latest.team_burnout * 0.07 * pressure - latest.dependency_bottlenecks / 120 * pressure),
                    "scope_change_rate": self._clip01(latest.scope_change_rate + 0.035 * pressure * (1 - latest.communication_score)),
                    "defect_rate": self._clip01(latest.defect_rate + latest.rework_ratio * 0.04 * pressure),
                    "rework_ratio": self._clip01(latest.rework_ratio + latest.defect_rate * 0.035 * pressure),
                    "dependency_bottlenecks": min(30, latest.dependency_bottlenecks + round(project.critical_dependency_count * 0.08 * pressure)),
                    "resource_allocation": self._clip01(latest.resource_allocation - latest.team_burnout * 0.05 * pressure),
                    "budget_burn_rate": min(1.5, latest.budget_burn_rate + latest.scope_change_rate * 0.08 * pressure),
                    "meeting_load": self._clip01(latest.meeting_load + latest.team_burnout * 0.04 * pressure),
                    "communication_score": self._clip01(latest.communication_score - latest.team_burnout * 0.05 * pressure - latest.meeting_load * 0.025 * pressure),
                    "team_burnout": self._clip01(latest.team_burnout + latest.meeting_load * 0.055 * pressure + (1 - latest.resource_allocation) * 0.04 * pressure),
                    "team_compatibility": self._clip01(latest.team_compatibility - latest.team_burnout * 0.03 * pressure),
                    "open_risks": min(60, latest.open_risks + round((latest.scope_change_rate + latest.defect_rate) * 2.4 * pressure)),
                }
            )
            simulated = simulated.model_copy(
                update={
                    "days_to_deadline": max(1, project.days_to_deadline - day),
                    "budget_utilization": min(1.6, project.budget_utilization + simulated_latest.budget_burn_rate * 0.006 * day),
                    "current_scope_completion": self._clip01(project.current_scope_completion + latest.task_completion_rate * day / max(horizon_days, 1) * 0.34),
                    "history": [*project.history[-10:], simulated_latest],
                }
            )
            predicted = project_failure_engine.predict(simulated)
            failure_score, delay_score, budget_score = self._calibrated_scores(simulated, simulated_latest, predicted)
            sprint_probability = self._clip100(100 - delay_score * 0.64 - failure_score * 0.22 + simulated_latest.task_completion_rate * 18)
            points.append(
                ProjectRiskForecastPoint(
                    day=day,
                    failure_probability=round(failure_score, 2),
                    delay_probability=round(delay_score, 2),
                    budget_overrun_probability=round(budget_score, 2),
                    sprint_completion_probability=round(sprint_probability, 2),
                    confidence=predicted.confidence,
                )
            )
        return points

    def _risk_signals(
        self,
        project: ProjectProfile,
        failure: float,
        delay: float,
        budget: float,
        collapse: float,
        slowdown: float,
        resource: float,
        burnout: float,
        communication: float,
        dependency: float,
    ) -> list[ProjectRiskSignal]:
        latest = self._latest(project)
        signals = [
            ("delivery_failure", failure, f"{project.project_name} has {round(failure)}% delivery failure probability.", "Split the critical path into 48-hour recovery checkpoints."),
            ("deadline_miss", delay, f"Deadline miss probability is {round(delay)}% with {project.days_to_deadline} days remaining.", "Move deadline risk to executive review and freeze non-critical scope."),
            ("budget_overrun", budget, f"Budget utilization is {round(project.budget_utilization * 100)}% and burn rate is {round(latest.budget_burn_rate * 100)}%.", "Hold scope additions until burn rate returns below forecasted delivery value."),
            ("team_collapse", collapse, f"Team collapse pressure is {round(collapse)}% from burnout and resource strain.", "Rotate incident ownership and add protected recovery windows."),
            ("productivity_slowdown", slowdown, f"Sprint velocity is {round(latest.sprint_velocity * 100)}% with completion rate {round(latest.task_completion_rate * 100)}%.", "Remove multitasking and dedicate two focus blocks per day to milestone work."),
            ("resource_shortage", resource, f"Skill coverage and resource allocation create {round(resource)}% shortage impact.", "Reassign underutilized specialists to blocked dependencies."),
            ("burnout_project_impact", burnout, f"Team burnout is {round(latest.team_burnout * 100)}% and rising.", "Reduce meeting load and rebalance critical tasks away from overloaded owners."),
            ("communication_bottleneck", communication, f"Communication quality is {round(latest.communication_score * 100)}%.", "Create a single decision log and reduce status meetings."),
            ("dependency_failure", dependency, f"{latest.dependency_bottlenecks + project.critical_dependency_count} dependency bottlenecks are active.", "Escalate external blockers and assign dependency owners."),
        ]
        return [
            ProjectRiskSignal(
                category=category,
                severity=self._severity(score),
                score=round(self._clip100(score), 2),
                evidence=evidence,
                recommendation=recommendation,
            )
            for category, score, evidence, recommendation in sorted(signals, key=lambda item: item[1], reverse=True)
            if score >= 28
        ][:8]

    @staticmethod
    def _calibrated_scores(project: ProjectProfile, latest: ProjectMetricPoint, prediction) -> tuple[float, float, float]:
        features = prediction.features
        deadline_pressure = (1 - min(project.days_to_deadline / 90, 1)) * 100
        dependency_pressure = features["dependency_pressure"] * 100
        burnout_pressure = latest.team_burnout * 100
        resource_pressure = (1 - latest.resource_allocation) * 100
        skill_pressure = (1 - features["skill_coverage"]) * 100
        communication_pressure = (1 - latest.communication_score) * 100
        velocity_pressure = (1 - latest.sprint_velocity) * 100
        completion_pressure = (1 - latest.task_completion_rate) * 100
        collapse_proxy = ProjectFailureService._clip100(
            burnout_pressure * 0.34
            + resource_pressure * 0.24
            + (1 - latest.team_compatibility) * 100 * 0.18
            + dependency_pressure * 0.14
            + latest.open_risks / 60 * 10
        )
        slowdown_proxy = ProjectFailureService._clip100(
            velocity_pressure * 0.38
            + completion_pressure * 0.3
            + latest.meeting_load * 100 * 0.13
            + burnout_pressure * 0.12
            + communication_pressure * 0.07
        )
        budget_pressure = ProjectFailureService._clip100(
            min(project.budget_utilization / 1.25, 1) * 42
            + min(latest.budget_burn_rate / 1.2, 1) * 36
            + latest.scope_change_rate * 100 * 0.12
            + latest.rework_ratio * 100 * 0.1
        )
        deadline_bonus = 15 if project.days_to_deadline <= 14 else 6 if project.days_to_deadline <= 28 else 0
        failure_score = ProjectFailureService._clip100(
            prediction.failure_probability * 0.45
            + collapse_proxy * 0.2
            + burnout_pressure * 0.16
            + dependency_pressure * 0.12
            + slowdown_proxy * 0.07
            + deadline_bonus
        )
        delay_score = ProjectFailureService._clip100(
            prediction.delay_probability * 0.55
            + dependency_pressure * 0.22
            + slowdown_proxy * 0.12
            + deadline_pressure * 0.07
            + deadline_bonus
        )
        budget_score = ProjectFailureService._clip100(
            prediction.budget_overrun_probability * 0.54
            + budget_pressure * 0.28
            + latest.scope_change_rate * 100 * 0.08
            + skill_pressure * 0.05
            + resource_pressure * 0.05
        )
        return round(failure_score, 2), round(delay_score, 2), round(budget_score, 2)

    def _recommendations(self, project: ProjectProfile, signals: list[ProjectRiskSignal], failure: float, delay: float) -> list[ProjectRecommendation]:
        categories = {signal.category: signal for signal in signals}
        recommendations: list[ProjectRecommendation] = []
        if "resource_shortage" in categories or "dependency_failure" in categories:
            recommendations.append(
                self._recommendation(
                    project,
                    "resource_optimization",
                    "Rebalance scarce delivery capacity",
                    f"Move two specialists into {project.team_name}'s highest-risk dependency lane for the next sprint.",
                    "Resource shortage and dependency pressure are now stronger predictors than normal sprint variance.",
                    [categories.get("resource_shortage"), categories.get("dependency_failure")],
                )
            )
        if "burnout_project_impact" in categories or "team_collapse" in categories:
            recommendations.append(
                self._recommendation(
                    project,
                    "burnout_recovery",
                    "Protect delivery by reducing burnout load",
                    f"Cut recurring meetings for {project.team_name} by 18% and rotate escalation duty within 24 hours.",
                    "Burnout-driven project risk is degrading sprint completion probability.",
                    [categories.get("burnout_project_impact"), categories.get("team_collapse")],
                )
            )
        if "deadline_miss" in categories or delay >= 58:
            recommendations.append(
                self._recommendation(
                    project,
                    "deadline_adjustment",
                    "Restructure the sprint around the critical path",
                    f"Freeze non-critical scope for {project.project_name} and convert unresolved blockers into executive-owned decisions.",
                    "The delay model shows deadline pressure compounding with velocity decline.",
                    [categories.get("deadline_miss")],
                )
            )
        if "budget_overrun" in categories:
            recommendations.append(
                self._recommendation(
                    project,
                    "budget_control",
                    "Stop budget drift before it becomes irreversible",
                    f"Cap change requests on {project.project_name} until budget burn drops below 80% of the risk threshold.",
                    "Budget utilization and burn rate are forecasted to outrun delivery confidence.",
                    [categories.get("budget_overrun")],
                )
            )
        if "communication_bottleneck" in categories:
            recommendations.append(
                self._recommendation(
                    project,
                    "communication_reset",
                    "Create one source of truth for project decisions",
                    f"Replace status loops with a daily blocker ledger for {project.team_name}.",
                    "Communication bottlenecks are amplifying dependency and rework risk.",
                    [categories.get("communication_bottleneck")],
                )
            )
        if not recommendations:
            recommendations.append(
                self._recommendation(
                    project,
                    "stability_guardrail",
                    "Keep project health within the green band",
                    f"Maintain current staffing and review {project.project_name} risk weekly.",
                    "Forecast risk is stable, but continued monitoring prevents slow drift.",
                    [],
                    base_score=max(failure, delay, 34),
                )
            )
        return sorted(recommendations, key=lambda item: item.impact_score, reverse=True)[:5]

    def _portfolio_recommendations(self, predictions: list[ProjectFailurePrediction]) -> list[ProjectRecommendation]:
        if not predictions:
            return []
        highest = max(predictions, key=lambda item: item.failure_probability)
        overloaded = [item for item in predictions if item.resource_shortage_impact >= 50 or item.burnout_impact >= 55]
        recommendations = [
            ProjectRecommendation(
                recommendation_id="portfolio-war-room",
                category="portfolio_risk_control",
                title="Open an executive delivery war room",
                action=f"Review {highest.project_name} every 48 hours until failure probability drops below 45%.",
                rationale=f"{highest.project_name} is the portfolio peak risk at {round(highest.failure_probability)}%.",
                impact_score=round(self._clip100(highest.failure_probability + 12), 2),
                confidence=highest.confidence,
                affected_projects=[highest.project_id],
                source_systems=["project_failure_forecaster", "manager_dashboard", "burnout_ai"],
                evidence=[f"failure={highest.failure_probability}", f"delay={highest.deadline_miss_probability}"],
            )
        ]
        if overloaded:
            recommendations.append(
                ProjectRecommendation(
                    recommendation_id="portfolio-resource-balance",
                    category="portfolio_resource_balance",
                    title="Balance overloaded teams across the portfolio",
                    action="Move available platform and QA capacity into the highest dependency lanes before the next sprint review.",
                    rationale=f"{len(overloaded)} project(s) show resource or burnout pressure above the safety band.",
                    impact_score=round(mean(item.resource_shortage_impact + item.burnout_impact for item in overloaded) / 2, 2),
                    confidence=round(mean(item.confidence for item in overloaded), 3),
                    affected_projects=[item.project_id for item in overloaded],
                    source_systems=["project_failure_forecaster", "team_compatibility_ai", "smart_suggestion_engine"],
                    evidence=[f"{item.project_name}: resource={item.resource_shortage_impact}, burnout={item.burnout_impact}" for item in overloaded],
                )
            )
        return recommendations

    @staticmethod
    def _recommendation(
        project: ProjectProfile,
        category: str,
        title: str,
        action: str,
        rationale: str,
        signals: list[ProjectRiskSignal | None],
        base_score: float | None = None,
    ) -> ProjectRecommendation:
        valid = [signal for signal in signals if signal is not None]
        impact = base_score if base_score is not None else mean(signal.score for signal in valid) if valid else 42
        confidence = 0.62 + min(0.28, impact / 380) + (0.04 if valid else 0)
        return ProjectRecommendation(
            recommendation_id=f"{project.project_id}-{category}",
            category=category,
            title=title,
            action=action,
            rationale=rationale,
            impact_score=round(float(np.clip(impact, 0, 100)), 2),
            confidence=round(float(np.clip(confidence, 0.55, 0.96)), 3),
            affected_projects=[project.project_id],
            source_systems=["project_failure_forecaster", "time_series_forecasting", "burnout_ai", "resource_optimizer"],
            evidence=[signal.evidence for signal in valid],
        )

    @staticmethod
    def _summary(predictions: list[ProjectFailurePrediction]) -> ProjectFailureSummary:
        highest = max(predictions, key=lambda item: item.failure_probability) if predictions else None
        return ProjectFailureSummary(
            projects_analyzed=len(predictions),
            average_failure_probability=round(mean(item.failure_probability for item in predictions) if predictions else 0, 2),
            average_delay_probability=round(mean(item.deadline_miss_probability for item in predictions) if predictions else 0, 2),
            critical_projects=sum(1 for item in predictions if item.failure_probability >= 70 or item.deadline_miss_probability >= 70),
            highest_risk_project=highest.project_name if highest else "n/a",
            average_health_score=round(mean(item.health_score for item in predictions) if predictions else 0, 2),
        )

    @staticmethod
    def _heatmap(predictions: list[ProjectFailurePrediction]) -> list[dict[str, float | str]]:
        return [
            {
                "project": item.project_name,
                "team": item.team_name,
                "failure": item.failure_probability,
                "delay": item.deadline_miss_probability,
                "budget": item.budget_overrun_probability,
                "burnout": item.burnout_impact,
                "resources": item.resource_shortage_impact,
                "health": item.health_score,
            }
            for item in sorted(predictions, key=lambda prediction: prediction.failure_probability, reverse=True)
        ]

    @staticmethod
    def _history(
        velocity: list[float],
        completion: list[float],
        burnout: list[float],
        communication: list[float],
        resource: list[float],
        dependency_start: int,
        risk_start: int,
        scope_change: float,
        defect: float,
        rework: float,
        meeting: float,
        budget: float,
        compatibility: float,
    ) -> list[ProjectMetricPoint]:
        now = datetime.now(timezone.utc)
        points = []
        for index, current_velocity in enumerate(velocity):
            points.append(
                ProjectMetricPoint(
                    timestamp=now - timedelta(days=(len(velocity) - index) * 3),
                    sprint_velocity=current_velocity,
                    task_completion_rate=completion[index],
                    scope_change_rate=min(1, scope_change + index * 0.01),
                    defect_rate=min(1, defect + index * 0.006),
                    rework_ratio=min(1, rework + index * 0.005),
                    dependency_bottlenecks=min(30, dependency_start + index // 2),
                    resource_allocation=resource[index],
                    budget_burn_rate=min(1.5, budget + index * 0.01),
                    meeting_load=meeting,
                    communication_score=communication[index],
                    team_burnout=burnout[index],
                    team_compatibility=compatibility,
                    open_risks=min(60, risk_start + index),
                )
            )
        return points

    @staticmethod
    def _scenario_variant(base: ProjectFailureRequest, stress_delta: float, dependency_delta: int, budget_delta: float) -> ProjectFailureRequest:
        projects = []
        for project in base.projects or ProjectFailureService.default_request().projects:
            history = []
            for point in project.history:
                history.append(
                    point.model_copy(
                        update={
                            "team_burnout": ProjectFailureService._clip01(point.team_burnout + stress_delta),
                            "communication_score": ProjectFailureService._clip01(point.communication_score - stress_delta * 0.55),
                            "team_compatibility": ProjectFailureService._clip01(point.team_compatibility - stress_delta * 0.35),
                            "resource_allocation": ProjectFailureService._clip01(point.resource_allocation - stress_delta * 0.48),
                            "dependency_bottlenecks": min(30, point.dependency_bottlenecks + dependency_delta),
                            "open_risks": min(60, point.open_risks + dependency_delta * 2),
                            "budget_burn_rate": min(1.5, point.budget_burn_rate + budget_delta),
                        }
                    )
                )
            projects.append(
                project.model_copy(
                    update={
                        "days_to_deadline": max(1, project.days_to_deadline - dependency_delta),
                        "budget_utilization": min(1.6, project.budget_utilization + budget_delta),
                        "critical_dependency_count": min(30, project.critical_dependency_count + dependency_delta),
                        "history": history,
                    }
                )
            )
        return base.model_copy(update={"projects": projects, "realtime": True})

    @staticmethod
    def _latest(project: ProjectProfile) -> ProjectMetricPoint:
        return project.history[-1] if project.history else ProjectMetricPoint(timestamp=datetime.now(timezone.utc))

    @staticmethod
    def _severity(score: float) -> ProjectRiskSeverity:
        if score >= 82:
            return "critical"
        if score >= 64:
            return "high"
        if score >= 42:
            return "medium"
        return "low"

    @staticmethod
    def _clip01(value: float) -> float:
        return float(np.clip(value, 0, 1))

    @staticmethod
    def _clip100(value: float) -> float:
        return float(np.clip(value, 0, 100))

    def _append_jsonl(self, payload: dict[str, object]) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with self._lock:
            with HISTORY_PATH.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, default=str) + "\n")


project_failure_service = ProjectFailureService()
