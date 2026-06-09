from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.ai.decision_assistant_engine import DecisionAssistantEngine, decision_assistant_engine
from app.core.cache import TTLResponseCache
from app.schemas.decision_assistant import (
    DecisionAlert,
    DecisionAssistantRequest,
    DecisionAssistantResponse,
    DecisionCapabilityForecast,
    DecisionPriority,
    DecisionProjectSignal,
    DecisionRecommendation,
    DecisionRiskHeatmapPoint,
    DecisionSummary,
    DecisionTeamOption,
    DecisionTimelineForecastPoint,
    TeamDecisionRanking,
)


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
HISTORY_PATH = DATA_DIR / "decision_assistant_history.jsonl"


class DecisionAssistantService:
    model_name = "AI Decision Assistant for Managers"
    source_systems = [
        "manager_dashboard",
        "resource_allocation",
        "project_failure_prediction",
        "team_builder_graph",
        "team_compatibility",
        "random_forest_decision_router",
        "gradient_boosting_timeline_forecaster",
        "decision_history_jsonl",
    ]

    def __init__(self, engine: DecisionAssistantEngine = decision_assistant_engine) -> None:
        self._cache: TTLResponseCache[DecisionAssistantResponse] = TTLResponseCache(ttl_seconds=8)
        self._lock = Lock()
        self._engine = engine
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def recommend(self, payload: DecisionAssistantRequest | None = None) -> DecisionAssistantResponse:
        if payload is None:
            return self._cache.get_or_set(self._default_uncached)
        return self._recommend_uncached(payload)

    def _default_uncached(self) -> DecisionAssistantResponse:
        return self._recommend_uncached(self.default_request())

    def _recommend_uncached(self, payload: DecisionAssistantRequest) -> DecisionAssistantResponse:
        request = payload or self.default_request()
        teams = request.teams or self.default_request().teams
        feature_rows = [self._feature_row(request.project, team) for team in teams]
        predictions = self._engine.predict(feature_rows)
        rankings = self._rankings(request, teams, feature_rows, predictions)
        heatmap = self._risk_heatmap(rankings)
        capability = self._capability_forecast(rankings)
        timeline = self._timeline_forecast(request, rankings[0])
        recommendations = self._recommendations(request, rankings)
        alerts = self._alerts(request, rankings, timeline)
        insights = self._executive_insights(request, rankings, timeline)
        response = DecisionAssistantResponse(
            model=self._engine.model_name,
            generated_at=datetime.now(timezone.utc),
            question=request.question,
            project_name=request.project.project_name,
            horizon_days=request.horizon_days,
            rankings=rankings,
            risk_heatmap=heatmap,
            timeline_forecast=timeline,
            capability_forecast=capability,
            recommendations=recommendations,
            alerts=alerts,
            executive_insights=insights,
            summary=DecisionSummary(
                recommended_team=rankings[0].team_name,
                recommended_team_id=rankings[0].team_id,
                best_team_score=rankings[0].suitability_score,
                success_probability=rankings[0].delivery_success_probability,
                estimated_completion_days=rankings[0].estimated_completion_days,
                delivery_risk=rankings[0].risk_score,
                workload_impact=rankings[0].workload_impact,
                skill_gap_count=len(rankings[0].missing_skills),
            ),
            source_systems=self.source_systems,
            storage=str(HISTORY_PATH),
        )
        self._append_jsonl(response.model_dump(mode="json"))
        return response

    async def stream(self, payload: DecisionAssistantRequest | None = None):
        base = payload or self.default_request()
        scenarios = [
            base,
            self._scenario_variant(base, complexity_delta=0.06, deadline_factor=0.84, workload_delta=0.05, burnout_delta=0.03),
            self._scenario_variant(base, complexity_delta=0.13, deadline_factor=0.68, workload_delta=0.1, burnout_delta=0.07),
        ]
        for sequence, scenario in enumerate(scenarios, start=1):
            response = self.recommend(scenario)
            data = response.model_dump(mode="json")
            data["summary"]["stream_sequence"] = sequence
            yield f"event: decision_assistant\ndata: {json.dumps(data)}\n\n"
            await asyncio.sleep(0.8)

    def _rankings(
        self,
        request: DecisionAssistantRequest,
        teams: list[DecisionTeamOption],
        feature_rows: list[dict[str, float]],
        predictions: list[dict[str, float]],
    ) -> list[TeamDecisionRanking]:
        ranked: list[TeamDecisionRanking] = []
        for team, row, prediction in zip(teams, feature_rows, predictions):
            skill_score = row["skill_similarity"] * 100
            capacity_score = self._clip(row["capacity_available"] * 82 + (1 - min(team.current_workload, 1.2) / 1.2) * 18)
            workload_impact = self._clip(team.current_workload * 100 + request.project.complexity * 14 - team.capacity_available * 10, upper=160)
            burnout = self._clip(team.burnout_risk * 100 + max(0, workload_impact - 88) * 0.38 + request.project.deadline_days ** -0.35 * 6)
            risk_score = self._clip(prediction["risk_score"] + max(0, workload_impact - 95) * 0.2 + len(self._missing_skills(request.project, team)) * 3.2)
            completion_days = self._clip(
                prediction["estimated_completion_days"] * (1 + max(0, request.project.deadline_days - request.horizon_days) * 0.002),
                lower=1,
                upper=365,
            )
            delivery_success = self._clip(prediction["suitability_score"] * 0.64 + (100 - risk_score) * 0.28 + min(100, request.project.deadline_days / max(completion_days, 1) * 55) * 0.08)
            final_score = self._clip(prediction["suitability_score"] * 0.78 + delivery_success * 0.12 + skill_score * 0.1 - max(0, completion_days - request.project.deadline_days) * 0.75)
            estimated_cost = completion_days * team.member_count * team.hourly_cost * 8 * (0.82 + request.project.complexity * 0.34)
            drivers = self._capability_drivers(team, skill_score, capacity_score)
            risks = self._risk_drivers(request, team, risk_score, workload_impact)
            rationale = (
                f"{team.team_name} scores {round(final_score)}% for {request.project.project_name}: "
                f"{round(skill_score)}% skill compatibility, {round(capacity_score)}% capacity fit, "
                f"{round(delivery_success)}% delivery confidence, and {round(risk_score)}% modeled risk."
            )
            ranked.append(
                TeamDecisionRanking(
                    rank=1,
                    team_id=team.team_id,
                    team_name=team.team_name,
                    department=team.department,
                    suitability_score=round(final_score, 2),
                    skill_compatibility=round(skill_score, 2),
                    capacity_score=round(capacity_score, 2),
                    workload_impact=round(workload_impact, 2),
                    burnout_risk=round(burnout, 2),
                    delivery_success_probability=round(delivery_success, 2),
                    estimated_completion_days=round(completion_days, 2),
                    estimated_cost=round(estimated_cost, 2),
                    risk_score=round(risk_score, 2),
                    confidence=round(float(prediction["confidence"]), 3),
                    rationale=rationale,
                    capability_drivers=drivers,
                    risk_drivers=risks,
                    missing_skills=self._missing_skills(request.project, team),
                )
            )
        ranked.sort(key=lambda item: (item.suitability_score, item.delivery_success_probability, -item.risk_score), reverse=True)
        return [item.model_copy(update={"rank": index}) for index, item in enumerate(ranked, start=1)]

    def _feature_row(self, project: DecisionProjectSignal, team: DecisionTeamOption) -> dict[str, float]:
        deadline_pressure = min(1, 14 / max(project.deadline_days, 1))
        dependency_pressure = min(1, project.dependency_count / 12)
        return {
            "skill_similarity": self._skill_similarity(project, team),
            "historical_success_rate": team.historical_success_rate,
            "productivity_score": team.productivity_score,
            "current_workload": min(team.current_workload, 1.6),
            "capacity_available": team.capacity_available,
            "sprint_velocity": team.sprint_velocity,
            "communication_quality": team.communication_quality,
            "collaboration_score": team.collaboration_score,
            "burnout_risk": team.burnout_risk,
            "attrition_risk": team.attrition_risk,
            "delivery_consistency": team.delivery_consistency,
            "innovation_score": team.innovation_score,
            "deadline_pressure": deadline_pressure,
            "complexity": project.complexity,
            "dependency_pressure": dependency_pressure,
            "security_sensitivity": project.security_sensitivity,
            "scope_volatility": project.scope_volatility,
            "executive_visibility": project.executive_visibility,
        }

    def _skill_similarity(self, project: DecisionProjectSignal, team: DecisionTeamOption) -> float:
        project_doc = " ".join([project.project_name, project.description, *project.required_skills]).lower()
        team_doc = " ".join([team.team_name, team.department, *team.skills]).lower()
        project_terms = self._terms(project.required_skills)
        team_terms = self._terms(team.skills)
        lexical = len(project_terms.intersection(team_terms)) / max(len(project_terms), 1)
        try:
            matrix = TfidfVectorizer(ngram_range=(1, 2)).fit_transform([project_doc, team_doc])
            semantic = float(cosine_similarity(matrix[0], matrix[1])[0][0])
        except ValueError:
            semantic = 0.0
        return self._clip01(lexical * 0.54 + semantic * 0.46)

    @staticmethod
    def _terms(skills: list[str]) -> set[str]:
        terms: set[str] = set()
        for skill in skills:
            normalized = skill.lower().replace("-", " ").replace("/", " ")
            terms.add(normalized.strip())
            terms.update(part.strip() for part in normalized.split() if part.strip())
        return terms

    def _missing_skills(self, project: DecisionProjectSignal, team: DecisionTeamOption) -> list[str]:
        team_terms = self._terms(team.skills)
        missing = []
        for skill in project.required_skills:
            skill_terms = self._terms([skill])
            if not skill_terms.intersection(team_terms) and skill.lower() not in " ".join(team.skills).lower():
                missing.append(skill)
        return missing[:8]

    @staticmethod
    def _capability_drivers(team: DecisionTeamOption, skill_score: float, capacity_score: float) -> list[str]:
        drivers = [
            f"{round(skill_score)}% semantic skill fit",
            f"{round(team.historical_success_rate * 100)}% historical project success",
            f"{round(team.sprint_velocity * 100)}% sprint velocity",
        ]
        if capacity_score >= 65:
            drivers.append(f"{round(capacity_score)}% available capacity")
        if team.innovation_score >= 0.72:
            drivers.append("High innovation capability for ambiguous scope")
        if team.communication_quality >= 0.82:
            drivers.append("Strong communication quality for executive delivery")
        return drivers[:5]

    @staticmethod
    def _risk_drivers(request: DecisionAssistantRequest, team: DecisionTeamOption, risk_score: float, workload_impact: float) -> list[str]:
        drivers = []
        if workload_impact >= 86:
            drivers.append("Workload pressure may degrade execution speed")
        if team.burnout_risk >= 0.55:
            drivers.append("Burnout indicators require capacity guardrails")
        if request.project.dependency_count >= 6:
            drivers.append("Dependency graph creates delivery bottleneck risk")
        if request.project.scope_volatility >= 0.45:
            drivers.append("Scope volatility increases estimation uncertainty")
        if request.project.deadline_days <= 21:
            drivers.append("Deadline urgency compresses validation time")
        if risk_score < 35:
            drivers.append("No critical routing risk detected")
        return drivers[:5]

    def _risk_heatmap(self, rankings: list[TeamDecisionRanking]) -> list[DecisionRiskHeatmapPoint]:
        points: list[DecisionRiskHeatmapPoint] = []
        for ranking in rankings[:6]:
            metrics = {
                "Risk-analysis heatmaps": ranking.risk_score,
                "Burnout-risk indicators": ranking.burnout_risk,
                "Resource-utilization graphs": ranking.workload_impact,
                "Skill gap risk": max(0, 100 - ranking.skill_compatibility),
            }
            for metric, score in metrics.items():
                heatmap_score = self._clip(score)
                points.append(
                    DecisionRiskHeatmapPoint(
                        team_name=ranking.team_name,
                        metric=metric,
                        score=round(heatmap_score, 2),
                        severity=self._severity(score),
                    )
                )
        return points

    @staticmethod
    def _timeline_forecast(request: DecisionAssistantRequest, top: TeamDecisionRanking) -> list[DecisionTimelineForecastPoint]:
        points: list[DecisionTimelineForecastPoint] = []
        total_steps = 6
        for index in range(total_steps):
            day = max(1, round((index + 1) * request.horizon_days / total_steps))
            progress_ratio = min(1.15, day / max(top.estimated_completion_days, 1))
            completion = DecisionAssistantService._clip(top.delivery_success_probability * progress_ratio - max(0, top.risk_score - 55) * 0.06 + index * 1.4)
            delay = DecisionAssistantService._clip(top.risk_score + max(0, top.estimated_completion_days - day) * 0.42 - index * 1.7)
            pressure = DecisionAssistantService._clip(top.workload_impact + index * 1.8 + request.project.complexity * 4, upper=160)
            confidence = DecisionAssistantService._clip01(top.confidence - index * 0.018 + min(0.04, progress_ratio * 0.025))
            points.append(
                DecisionTimelineForecastPoint(
                    day=day,
                    completion_probability=round(completion, 2),
                    delay_risk=round(delay, 2),
                    workload_pressure=round(pressure, 2),
                    confidence=round(confidence, 3),
                )
            )
        return points

    @staticmethod
    def _capability_forecast(rankings: list[TeamDecisionRanking]) -> list[DecisionCapabilityForecast]:
        forecasts: list[DecisionCapabilityForecast] = []
        for ranking in rankings:
            delivery = ranking.delivery_success_probability
            stability = DecisionAssistantService._clip(100 - ranking.risk_score * 0.65 - ranking.burnout_risk * 0.18)
            overall = DecisionAssistantService._clip(
                ranking.skill_compatibility * 0.28 + ranking.capacity_score * 0.22 + delivery * 0.27 + stability * 0.23
            )
            forecasts.append(
                DecisionCapabilityForecast(
                    team_name=ranking.team_name,
                    skill_fit=round(ranking.skill_compatibility, 2),
                    capacity_fit=round(ranking.capacity_score, 2),
                    delivery_fit=round(delivery, 2),
                    stability_fit=round(stability, 2),
                    overall_capability=round(overall, 2),
                )
            )
        return forecasts[:8]

    def _recommendations(self, request: DecisionAssistantRequest, rankings: list[TeamDecisionRanking]) -> list[DecisionRecommendation]:
        top = rankings[0]
        second = rankings[1] if len(rankings) > 1 else top
        recommendations = [
            DecisionRecommendation(
                title="Route project to best-fit delivery team",
                category="routing",
                priority="medium" if top.suitability_score >= 70 else "high",
                action=f"Assign {request.project.project_name} to {top.team_name} and use {second.team_name} as escalation backup.",
                expected_impact=f"Modeled delivery confidence reaches {round(top.delivery_success_probability)}% with {round(top.estimated_completion_days, 1)} day completion estimate.",
                confidence=top.confidence,
                affected_teams=[top.team_name, second.team_name],
            )
        ]
        if top.missing_skills:
            recommendations.append(
                DecisionRecommendation(
                    title="Close project skill gaps before kickoff",
                    category="skills",
                    priority="high",
                    action=f"Add specialist coverage for {', '.join(top.missing_skills[:3])}.",
                    expected_impact="Improves delivery confidence and reduces rework from capability mismatch.",
                    confidence=0.84,
                    affected_teams=[top.team_name],
                )
            )
        if top.workload_impact >= 88 or top.burnout_risk >= 58:
            recommendations.append(
                DecisionRecommendation(
                    title="Protect delivery capacity",
                    category="burnout",
                    priority="critical" if top.burnout_risk >= 76 else "high",
                    action=f"Move 10-15% lower-priority work away from {top.team_name} before assigning this project.",
                    expected_impact="Reduces burnout-driven delivery variance and protects sprint velocity.",
                    confidence=0.86,
                    affected_teams=[top.team_name],
                )
            )
        if top.estimated_completion_days > request.project.deadline_days:
            recommendations.append(
                DecisionRecommendation(
                    title="Deadline recovery plan",
                    category="timeline",
                    priority="high",
                    action="Split the project into a dependency-clearing lane and an execution lane with daily decision checkpoints.",
                    expected_impact=f"Addresses a {round(top.estimated_completion_days - request.project.deadline_days, 1)} day forecast gap.",
                    confidence=0.81,
                    affected_teams=[top.team_name],
                )
            )
        if len(rankings) > 2:
            lower_cost = min(rankings, key=lambda item: item.estimated_cost)
            if lower_cost.team_id != top.team_id and lower_cost.suitability_score >= top.suitability_score - 12:
                recommendations.append(
                    DecisionRecommendation(
                        title="Cost optimization backup",
                        category="cost",
                        priority="medium",
                        action=f"Use {lower_cost.team_name} for non-critical workstreams if budget pressure increases.",
                        expected_impact=f"Potentially lowers delivery cost by {round(max(0, top.estimated_cost - lower_cost.estimated_cost)):,}.",
                        confidence=0.78,
                        affected_teams=[top.team_name, lower_cost.team_name],
                    )
                )
        return recommendations[:5]

    def _alerts(
        self,
        request: DecisionAssistantRequest,
        rankings: list[TeamDecisionRanking],
        timeline: list[DecisionTimelineForecastPoint],
    ) -> list[DecisionAlert]:
        top = rankings[0]
        alerts: list[DecisionAlert] = []
        if top.risk_score >= 55:
            alerts.append(
                DecisionAlert(
                    title="Delivery-risk analysis breach",
                    severity=self._severity(top.risk_score),
                    probability=top.risk_score,
                    impact=f"{top.team_name} may need executive intervention before final routing.",
                    mitigation="Require mitigation owner, dependency map, and daily risk review for the first week.",
                )
            )
        if top.burnout_risk >= 58:
            alerts.append(
                DecisionAlert(
                    title="Burnout-aware routing warning",
                    severity=self._severity(top.burnout_risk),
                    probability=top.burnout_risk,
                    impact="Team stability may degrade if the project is added without load reduction.",
                    mitigation="Shift operational work away before project kickoff.",
                )
            )
        if timeline[-1].delay_risk >= 50:
            alerts.append(
                DecisionAlert(
                    title="Timeline forecast pressure",
                    severity=self._severity(timeline[-1].delay_risk),
                    probability=timeline[-1].delay_risk,
                    impact=f"{request.project.project_name} is forecast near deadline pressure by day {timeline[-1].day}.",
                    mitigation="Start dependency-clearing work before assigning build execution.",
                )
            )
        if top.missing_skills:
            alerts.append(
                DecisionAlert(
                    title="Skill compatibility gap",
                    severity="medium" if len(top.missing_skills) <= 2 else "high",
                    probability=min(100, 42 + len(top.missing_skills) * 9),
                    impact=f"Missing {', '.join(top.missing_skills[:3])} may create delivery rework.",
                    mitigation="Add temporary specialist support or select the next-highest team with deeper skill coverage.",
                )
            )
        if not alerts:
            alerts.append(
                DecisionAlert(
                    title="No critical decision risk detected",
                    severity="low",
                    probability=max(5, top.risk_score),
                    impact="Recommended routing is inside operating tolerance.",
                    mitigation="Proceed with normal executive monitoring cadence.",
                )
            )
        return alerts[:5]

    @staticmethod
    def _executive_insights(
        request: DecisionAssistantRequest,
        rankings: list[TeamDecisionRanking],
        timeline: list[DecisionTimelineForecastPoint],
    ) -> list[str]:
        top = rankings[0]
        second = rankings[1] if len(rankings) > 1 else top
        return [
            f"{top.team_name} is the best team for {request.project.project_name} with {round(top.suitability_score)}% suitability and {round(top.delivery_success_probability)}% success probability.",
            f"{second.team_name} is the strongest backup route at {round(second.suitability_score)}%, useful if capacity changes during the planning window.",
            f"Timeline forecasting estimates {round(top.estimated_completion_days, 1)} days with {round(timeline[-1].delay_risk)}% terminal delay pressure.",
            f"Workload impact is {round(top.workload_impact)}%, so routing should include capacity protection if active commitments increase.",
        ]

    @staticmethod
    def default_request() -> DecisionAssistantRequest:
        project = DecisionProjectSignal(
            project_id="proj-atlas",
            project_name="Project Atlas AI Infrastructure Migration",
            description="Migrate core AI orchestration, vector retrieval, observability, and realtime analytics into a hardened enterprise deployment lane.",
            required_skills=["python", "fastapi", "kubernetes", "mlops", "security", "observability", "vector search", "realtime streaming"],
            complexity=0.7,
            deadline_days=36,
            budget=650000,
            revenue_impact=2200000,
            dependency_count=5,
            security_sensitivity=0.72,
            innovation_requirement=0.74,
            scope_volatility=0.32,
            executive_visibility=0.82,
        )
        teams = [
            DecisionTeamOption(team_id="team-platform", team_name="Platform Reliability", department="Engineering", skills=["python", "fastapi", "kubernetes", "terraform", "security", "observability", "mlops", "vector search", "realtime streaming", "incident response", "redis"], member_count=9, historical_success_rate=0.9, productivity_score=0.88, current_workload=0.68, capacity_available=0.44, sprint_velocity=0.87, communication_quality=0.88, collaboration_score=0.86, burnout_risk=0.24, attrition_risk=0.16, delivery_consistency=0.91, innovation_score=0.72, hourly_cost=118, active_incidents=1),
            DecisionTeamOption(team_id="team-ai", team_name="AI Products", department="AI", skills=["python", "fastapi", "mlops", "forecasting", "vector search", "rag", "model evaluation", "realtime streaming", "kubernetes"], member_count=10, historical_success_rate=0.84, productivity_score=0.88, current_workload=0.81, capacity_available=0.28, sprint_velocity=0.82, communication_quality=0.83, collaboration_score=0.84, burnout_risk=0.34, attrition_risk=0.22, delivery_consistency=0.84, innovation_score=0.91, hourly_cost=125, active_incidents=0),
            DecisionTeamOption(team_id="team-backend", team_name="Backend Infrastructure", department="Engineering", skills=["python", "fastapi", "postgresql", "api architecture", "observability", "security", "realtime streaming", "vector search"], member_count=8, historical_success_rate=0.82, productivity_score=0.83, current_workload=0.89, capacity_available=0.2, sprint_velocity=0.78, communication_quality=0.8, collaboration_score=0.78, burnout_risk=0.46, attrition_risk=0.28, delivery_consistency=0.8, innovation_score=0.62, hourly_cost=106, active_incidents=2),
            DecisionTeamOption(team_id="team-incident", team_name="Incident Response", department="Operations", skills=["incident response", "security", "observability", "backend", "runbooks"], member_count=7, historical_success_rate=0.72, productivity_score=0.62, current_workload=1.17, capacity_available=0.09, sprint_velocity=0.58, communication_quality=0.7, collaboration_score=0.66, burnout_risk=0.78, attrition_risk=0.44, delivery_consistency=0.64, innovation_score=0.44, hourly_cost=132, active_incidents=8),
            DecisionTeamOption(team_id="team-design", team_name="Design Systems", department="Product", skills=["dashboard", "ux research", "accessibility", "design systems"], member_count=6, historical_success_rate=0.76, productivity_score=0.79, current_workload=0.68, capacity_available=0.42, sprint_velocity=0.7, communication_quality=0.89, collaboration_score=0.88, burnout_risk=0.24, attrition_risk=0.16, delivery_consistency=0.76, innovation_score=0.78, hourly_cost=88, active_incidents=0),
        ]
        return DecisionAssistantRequest(project=project, teams=teams, horizon_days=45)

    @staticmethod
    def _scenario_variant(
        base: DecisionAssistantRequest,
        complexity_delta: float,
        deadline_factor: float,
        workload_delta: float,
        burnout_delta: float,
    ) -> DecisionAssistantRequest:
        project = base.project.model_copy(
            update={
                "complexity": min(1, base.project.complexity + complexity_delta),
                "deadline_days": max(1, round(base.project.deadline_days * deadline_factor)),
                "dependency_count": min(50, base.project.dependency_count + round(complexity_delta * 24)),
                "scope_volatility": min(1, base.project.scope_volatility + complexity_delta * 0.8),
            }
        )
        teams = [
            team.model_copy(
                update={
                    "current_workload": min(1.6, team.current_workload + workload_delta * (1.25 if team.current_workload > 0.85 else 0.85)),
                    "capacity_available": max(0, team.capacity_available - workload_delta * 0.42),
                    "burnout_risk": min(1, team.burnout_risk + burnout_delta * (1.3 if team.current_workload > 0.9 else 0.75)),
                    "attrition_risk": min(1, team.attrition_risk + burnout_delta * 0.45),
                }
            )
            for team in base.teams
        ]
        return base.model_copy(update={"project": project, "teams": teams, "realtime": True})

    @staticmethod
    def _severity(score: float) -> DecisionPriority:
        if score >= 82:
            return "critical"
        if score >= 62:
            return "high"
        if score >= 38:
            return "medium"
        return "low"

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


decision_assistant_service = DecisionAssistantService()
