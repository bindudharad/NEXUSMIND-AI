from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from threading import Lock

from app.ai.company_health_engine import company_health_engine
from app.core.cache import TTLResponseCache
from app.schemas.company_health import (
    CompanyHealthAlert,
    CompanyHealthHeatmapPoint,
    CompanyHealthPriority,
    CompanyHealthRequest,
    CompanyHealthResponse,
    CompanyHealthStatus,
    CompanyHealthSummary,
    CompanyHealthTeamSignal,
    ExecutiveCompanyRecommendation,
    ExecutiveKPI,
    ProductivityTrendPoint,
    ProjectHealthScorecard,
    RiskForecastPoint,
    TeamHealthScore,
)


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
HISTORY_PATH = DATA_DIR / "company_health_history.jsonl"


class CompanyHealthService:
    model_name = company_health_engine.model_name

    def __init__(self) -> None:
        self._default_cache: TTLResponseCache[CompanyHealthResponse] = TTLResponseCache(ttl_seconds=7)
        self._lock = Lock()
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def analyze(self, payload: CompanyHealthRequest | None = None) -> CompanyHealthResponse:
        if payload is None:
            return self._default_cache.get_or_set(self._analyze_default_uncached)
        return self._analyze_uncached(payload)

    def _analyze_default_uncached(self) -> CompanyHealthResponse:
        return self._analyze_uncached(self.default_request())

    def _analyze_uncached(self, payload: CompanyHealthRequest) -> CompanyHealthResponse:
        request = payload if payload.teams else self.default_request()
        team_scores = [self._score_team(team) for team in request.teams]
        team_scores = sorted(team_scores, key=lambda item: item.risk_score, reverse=True)
        summary = self._summary(team_scores)
        response = CompanyHealthResponse(
            model=self.model_name,
            generated_at=datetime.now(timezone.utc),
            cycle_name=request.cycle_name,
            horizon_days=request.horizon_days,
            executive_kpis=self._executive_kpis(summary, team_scores),
            team_scores=team_scores,
            heatmap=self._heatmap(team_scores),
            productivity_trends=self._productivity_trends(request.teams, request.horizon_days),
            risk_forecasts=self._risk_forecasts(team_scores, request.horizon_days),
            project_scorecards=self._project_scorecards(team_scores),
            recommendations=self._recommendations(team_scores, summary),
            alerts=self._alerts(team_scores, summary),
            executive_insights=self._executive_insights(team_scores, summary),
            summary=summary,
            source_systems=[
                "employee_dashboard",
                "productivity_leakage_detector",
                "wellness_burnout_forecaster",
                "attrition_prediction",
                "project_failure_prediction",
                "communication_quality_analyzer",
                "innovation_scoring",
                "security_anomaly_detection",
                "random_forest_company_health_model",
                "gradient_boosting_enterprise_risk_forecaster",
                "company_health_history_jsonl",
            ],
            storage=str(HISTORY_PATH),
        )
        self._append_jsonl(response.model_dump(mode="json"))
        return response

    async def stream(self, payload: CompanyHealthRequest | None = None):
        base = payload or self.default_request()
        scenarios = [
            base,
            self._scenario_variant(base, pressure_delta=5, positive_delta=-2),
            self._scenario_variant(base, pressure_delta=11, positive_delta=-5),
        ]
        for sequence, scenario in enumerate(scenarios, start=1):
            response = self.analyze(scenario)
            data = response.model_dump(mode="json")
            data["summary"]["stream_sequence"] = sequence
            yield f"event: company_health\ndata: {json.dumps(data)}\n\n"
            await asyncio.sleep(0.8)

    @staticmethod
    def default_request() -> CompanyHealthRequest:
        return CompanyHealthRequest(
            cycle_name="Realtime Company Health Review",
            horizon_days=30,
            teams=[
                CompanyHealthTeamSignal(
                    team_id="team-platform",
                    department="Engineering",
                    team_name="Backend Platform",
                    headcount=28,
                    employee_happiness_score=67,
                    productivity_score=73,
                    burnout_risk=58,
                    attrition_risk=45,
                    project_health=69,
                    collaboration_quality=72,
                    delivery_stability=68,
                    resource_utilization=95,
                    innovation_score=82,
                    security_risk=24,
                    communication_health=70,
                    meeting_efficiency=61,
                    workforce_engagement=66,
                    open_project_risks=8,
                    active_incidents=2,
                ),
                CompanyHealthTeamSignal(
                    team_id="team-ai-product",
                    department="Product",
                    team_name="AI Products",
                    headcount=19,
                    employee_happiness_score=78,
                    productivity_score=83,
                    burnout_risk=34,
                    attrition_risk=27,
                    project_health=81,
                    collaboration_quality=86,
                    delivery_stability=80,
                    resource_utilization=82,
                    innovation_score=88,
                    security_risk=12,
                    communication_health=84,
                    meeting_efficiency=76,
                    workforce_engagement=81,
                    open_project_risks=3,
                    active_incidents=0,
                ),
                CompanyHealthTeamSignal(
                    team_id="team-quality",
                    department="Quality",
                    team_name="Release Intelligence",
                    headcount=15,
                    employee_happiness_score=74,
                    productivity_score=79,
                    burnout_risk=31,
                    attrition_risk=23,
                    project_health=84,
                    collaboration_quality=78,
                    delivery_stability=86,
                    resource_utilization=78,
                    innovation_score=72,
                    security_risk=10,
                    communication_health=79,
                    meeting_efficiency=82,
                    workforce_engagement=76,
                    open_project_risks=2,
                    active_incidents=0,
                ),
                CompanyHealthTeamSignal(
                    team_id="team-incident",
                    department="Operations",
                    team_name="Incident Response",
                    headcount=12,
                    employee_happiness_score=55,
                    productivity_score=63,
                    burnout_risk=74,
                    attrition_risk=61,
                    project_health=58,
                    collaboration_quality=65,
                    delivery_stability=54,
                    resource_utilization=108,
                    innovation_score=70,
                    security_risk=42,
                    communication_health=62,
                    meeting_efficiency=52,
                    workforce_engagement=58,
                    open_project_risks=13,
                    active_incidents=5,
                ),
                CompanyHealthTeamSignal(
                    team_id="team-design",
                    department="Design",
                    team_name="Design Systems",
                    headcount=9,
                    employee_happiness_score=81,
                    productivity_score=76,
                    burnout_risk=28,
                    attrition_risk=19,
                    project_health=78,
                    collaboration_quality=83,
                    delivery_stability=77,
                    resource_utilization=74,
                    innovation_score=76,
                    security_risk=8,
                    communication_health=86,
                    meeting_efficiency=79,
                    workforce_engagement=84,
                    open_project_risks=2,
                    active_incidents=0,
                ),
            ],
        )

    def _score_team(self, team: CompanyHealthTeamSignal) -> TeamHealthScore:
        features = {
            "employee_happiness_score": team.employee_happiness_score,
            "productivity_score": team.productivity_score,
            "burnout_risk": team.burnout_risk,
            "attrition_risk": team.attrition_risk,
            "project_health": team.project_health,
            "collaboration_quality": team.collaboration_quality,
            "delivery_stability": team.delivery_stability,
            "resource_utilization": team.resource_utilization,
            "innovation_score": team.innovation_score,
            "security_risk": team.security_risk,
            "communication_health": team.communication_health,
            "meeting_efficiency": team.meeting_efficiency,
            "workforce_engagement": team.workforce_engagement,
            "open_project_risks": float(team.open_project_risks),
            "active_incidents": float(team.active_incidents),
        }
        prediction = company_health_engine.predict(features)
        team_efficiency = self._clip100(
            team.productivity_score * 0.32
            + team.collaboration_quality * 0.18
            + team.delivery_stability * 0.22
            + team.meeting_efficiency * 0.16
            + self._clip100(100 - abs(team.resource_utilization - 82) * 1.35) * 0.12
        )
        operational_risk = self._clip100(
            prediction["risk_score"] * 0.58
            + max(0, team.resource_utilization - 88) * 1.2
            + team.open_project_risks * 1.5
            + team.active_incidents * 3
        )
        dominant_risks = self._dominant_risks(team, operational_risk)
        health_score = self._clip100(prediction["health_score"] * 0.82 + team_efficiency * 0.18)
        return TeamHealthScore(
            team_id=team.team_id,
            department=team.department,
            team_name=team.team_name,
            headcount=team.headcount,
            health_score=round(health_score, 2),
            risk_score=round(operational_risk, 2),
            happiness_score=round(team.employee_happiness_score, 2),
            productivity_score=round(team.productivity_score, 2),
            burnout_risk=round(team.burnout_risk, 2),
            attrition_risk=round(team.attrition_risk, 2),
            project_health=round(team.project_health, 2),
            team_efficiency=round(team_efficiency, 2),
            collaboration_quality=round(team.collaboration_quality, 2),
            delivery_stability=round(team.delivery_stability, 2),
            operational_risk=round(operational_risk, 2),
            priority=self._priority(operational_risk),
            confidence=float(prediction["confidence"]),
            dominant_risks=dominant_risks,
            recommendation=self._team_recommendation(team, dominant_risks, operational_risk),
        )

    def _summary(self, teams: list[TeamHealthScore]) -> CompanyHealthSummary:
        weighted_health = self._weighted_average(teams, "health_score")
        return CompanyHealthSummary(
            company_health_score=round(weighted_health, 2),
            employee_happiness_score=round(self._weighted_average(teams, "happiness_score"), 2),
            productivity_score=round(self._weighted_average(teams, "productivity_score"), 2),
            burnout_risk=round(self._weighted_average(teams, "burnout_risk"), 2),
            attrition_risk=round(self._weighted_average(teams, "attrition_risk"), 2),
            project_health_score=round(self._weighted_average(teams, "project_health"), 2),
            collaboration_quality=round(self._weighted_average(teams, "collaboration_quality"), 2),
            delivery_stability=round(self._weighted_average(teams, "delivery_stability"), 2),
            workforce_engagement=round(mean([team.happiness_score * 0.38 + team.collaboration_quality * 0.24 + team.team_efficiency * 0.18 + (100 - team.attrition_risk) * 0.2 for team in teams] or [0]), 2),
            operational_risk=round(self._weighted_average(teams, "operational_risk"), 2),
            high_risk_teams=sum(1 for team in teams if team.risk_score >= 60),
            critical_alerts=sum(1 for team in teams if team.risk_score >= 78),
        )

    def _executive_kpis(self, summary: CompanyHealthSummary, teams: list[TeamHealthScore]) -> list[ExecutiveKPI]:
        kpis = [
            ("Company Health Score", summary.company_health_score, f"{round(summary.company_health_score)}%", "random_forest_company_health"),
            ("Employee Happiness", summary.employee_happiness_score, f"{round(summary.employee_happiness_score)}%", "wellness_and_engagement"),
            ("Productivity", summary.productivity_score, f"{round(summary.productivity_score)}%", "productivity_leakage_detector"),
            ("Burnout Risk", 100 - summary.burnout_risk, f"{round(summary.burnout_risk)}% risk", "wellness_burnout_forecaster"),
            ("Attrition Risk", 100 - summary.attrition_risk, f"{round(summary.attrition_risk)}% risk", "attrition_prediction"),
            ("Project Health", summary.project_health_score, f"{round(summary.project_health_score)}%", "project_failure_prediction"),
            ("Team Efficiency", mean([team.team_efficiency for team in teams] or [0]), f"{round(mean([team.team_efficiency for team in teams] or [0]))}%", "resource_and_collaboration_models"),
            ("Operational Risk", 100 - summary.operational_risk, f"{round(summary.operational_risk)}% risk", "enterprise_risk_forecaster"),
        ]
        return [
            ExecutiveKPI(
                label=label,
                value=value,
                score=round(self._clip100(score), 2),
                trend_delta=round((score - 70) / 6, 2),
                status=self._status(score),
                source=source,
            )
            for label, score, value, source in kpis
        ]

    def _heatmap(self, teams: list[TeamHealthScore]) -> list[CompanyHealthHeatmapPoint]:
        cells: list[CompanyHealthHeatmapPoint] = []
        for team in teams:
            metrics = {
                "Employee happiness heatmaps": 100 - team.happiness_score,
                "Burnout": team.burnout_risk,
                "Attrition": team.attrition_risk,
                "Project health": 100 - team.project_health,
                "Communication": 100 - team.collaboration_quality,
                "Delivery stability": 100 - team.delivery_stability,
            }
            for metric, risk in metrics.items():
                cells.append(
                    CompanyHealthHeatmapPoint(
                        department=team.department,
                        team_name=team.team_name,
                        metric=metric,
                        health_score=round(self._clip100(100 - risk), 2),
                        risk_score=round(self._clip100(risk), 2),
                        intensity=round(self._clip100(max(risk, team.risk_score)), 2),
                        priority=self._priority(max(risk, team.risk_score)),
                    )
                )
        return sorted(cells, key=lambda item: item.intensity, reverse=True)[:24]

    def _productivity_trends(self, signals: list[CompanyHealthTeamSignal], horizon_days: int) -> list[ProductivityTrendPoint]:
        productivity = mean([team.productivity_score for team in signals] or [0])
        delivery = mean([team.delivery_stability for team in signals] or [0])
        meeting = mean([team.meeting_efficiency for team in signals] or [0])
        burnout = mean([team.burnout_risk for team in signals] or [0])
        resource_pressure = mean([max(0, team.resource_utilization - 82) for team in signals] or [0])
        points: list[ProductivityTrendPoint] = []
        for index in range(6):
            step = index + 1
            drift = (horizon_days / 30) * step
            fatigue_drag = burnout * 0.012 * drift + resource_pressure * 0.02 * step
            recovery = meeting * 0.004 * step
            points.append(
                ProductivityTrendPoint(
                    label=f"T+{step}",
                    productivity_score=round(self._clip100(productivity - fatigue_drag + recovery), 2),
                    focus_stability=round(self._clip100(productivity * 0.55 + meeting * 0.24 + (100 - burnout) * 0.21 - fatigue_drag), 2),
                    meeting_efficiency=round(self._clip100(meeting - resource_pressure * 0.05 * step), 2),
                    delivery_stability=round(self._clip100(delivery - fatigue_drag * 0.7), 2),
                )
            )
        return points

    def _risk_forecasts(self, teams: list[TeamHealthScore], horizon_days: int) -> list[RiskForecastPoint]:
        health = self._weighted_average(teams, "health_score")
        burnout = self._weighted_average(teams, "burnout_risk")
        attrition = self._weighted_average(teams, "attrition_risk")
        project_failure = 100 - self._weighted_average(teams, "project_health")
        operational = self._weighted_average(teams, "operational_risk")
        points: list[RiskForecastPoint] = []
        for index in range(6):
            step = index + 1
            acceleration = (horizon_days / 30) * step
            pressure = operational * 0.018 * acceleration + burnout * 0.01 * step
            points.append(
                RiskForecastPoint(
                    label=f"D+{round(horizon_days * step / 6)}",
                    company_health_score=round(self._clip100(health - pressure), 2),
                    burnout_risk=round(self._clip100(burnout + pressure * 0.65), 2),
                    attrition_risk=round(self._clip100(attrition + pressure * 0.48), 2),
                    project_failure_risk=round(self._clip100(project_failure + pressure * 0.58), 2),
                    operational_risk=round(self._clip100(operational + pressure * 0.72), 2),
                )
            )
        return points

    def _project_scorecards(self, teams: list[TeamHealthScore]) -> list[ProjectHealthScorecard]:
        cards: list[ProjectHealthScorecard] = []
        for team in teams:
            delay = self._clip100((100 - team.delivery_stability) * 0.58 + (100 - team.team_efficiency) * 0.24 + team.burnout_risk * 0.18)
            productivity_risk = self._clip100(100 - team.productivity_score + team.operational_risk * 0.28)
            drivers = []
            if delay >= 45:
                drivers.append("delivery instability")
            if team.burnout_risk >= 55:
                drivers.append("burnout pressure")
            if team.attrition_risk >= 50:
                drivers.append("attrition exposure")
            if team.collaboration_quality < 68:
                drivers.append("collaboration quality")
            cards.append(
                ProjectHealthScorecard(
                    project_id=f"project-{team.team_id}",
                    department=team.department,
                    team_name=team.team_name,
                    health_score=round(team.project_health, 2),
                    delay_probability=round(delay, 2),
                    delivery_stability=round(team.delivery_stability, 2),
                    productivity_risk=round(productivity_risk, 2),
                    priority=self._priority(max(delay, productivity_risk, team.operational_risk)),
                    risk_drivers=drivers or ["delivery inside modeled threshold"],
                    recommended_action=self._project_action(team, delay, productivity_risk),
                )
            )
        return sorted(cards, key=lambda item: item.delay_probability, reverse=True)

    def _recommendations(self, teams: list[TeamHealthScore], summary: CompanyHealthSummary) -> list[ExecutiveCompanyRecommendation]:
        recommendations: list[ExecutiveCompanyRecommendation] = []
        riskiest = teams[0] if teams else None
        weakest_delivery = min(teams, key=lambda team: team.delivery_stability, default=None)
        highest_burnout = max(teams, key=lambda team: team.burnout_risk, default=None)
        if riskiest:
            recommendations.append(
                ExecutiveCompanyRecommendation(
                    title="Stabilize highest-risk team",
                    category="operational",
                    priority=riskiest.priority,
                    expected_impact=round(self._clip100(riskiest.risk_score * 0.72), 2),
                    action=f"Move executive intervention capacity to {riskiest.department} / {riskiest.team_name} and clear the top two risk drivers.",
                    rationale=f"{riskiest.team_name} has {round(riskiest.risk_score)} operational risk driven by {', '.join(riskiest.dominant_risks[:3])}.",
                    confidence=riskiest.confidence,
                )
            )
        if highest_burnout and highest_burnout.burnout_risk >= 45:
            recommendations.append(
                ExecutiveCompanyRecommendation(
                    title="Reduce burnout pressure",
                    category="burnout",
                    priority=self._priority(highest_burnout.burnout_risk),
                    expected_impact=round(self._clip100(highest_burnout.burnout_risk * 0.64), 2),
                    action=f"Reduce {highest_burnout.team_name} meeting and incident load for one sprint and redistribute high-cognitive work.",
                    rationale=f"Burnout risk is {round(highest_burnout.burnout_risk)} with attrition risk {round(highest_burnout.attrition_risk)}.",
                    confidence=0.86,
                )
            )
        if weakest_delivery and weakest_delivery.delivery_stability < 72:
            recommendations.append(
                ExecutiveCompanyRecommendation(
                    title="Protect delivery stability",
                    category="project",
                    priority=self._priority(100 - weakest_delivery.delivery_stability),
                    expected_impact=round(self._clip100((100 - weakest_delivery.delivery_stability) * 0.7), 2),
                    action=f"Add delivery checkpoints and dependency owners for {weakest_delivery.team_name}.",
                    rationale=f"Delivery stability is {round(weakest_delivery.delivery_stability)} and project health is {round(weakest_delivery.project_health)}.",
                    confidence=0.83,
                )
            )
        if summary.employee_happiness_score < 72:
            recommendations.append(
                ExecutiveCompanyRecommendation(
                    title="Improve workforce engagement",
                    category="workforce",
                    priority="medium",
                    expected_impact=42,
                    action="Run targeted engagement recovery for teams below the happiness threshold and review manager escalation load.",
                    rationale=f"Company happiness is {round(summary.employee_happiness_score)} across the monitored workforce.",
                    confidence=0.81,
                )
            )
        recommendations.append(
            ExecutiveCompanyRecommendation(
                title="Maintain realtime executive monitoring",
                category="operational",
                priority=self._priority(summary.operational_risk),
                expected_impact=round(self._clip100(summary.operational_risk * 0.52), 2),
                action="Keep live KPI alerts enabled for company health, project risk, attrition pressure, and communication degradation.",
                rationale="Realtime company health is computed from workforce, productivity, project, risk, and communication signals.",
                confidence=0.88,
            )
        )
        return recommendations[:6]

    def _alerts(self, teams: list[TeamHealthScore], summary: CompanyHealthSummary) -> list[CompanyHealthAlert]:
        alerts: list[CompanyHealthAlert] = []
        for team in teams:
            if team.risk_score >= 55:
                alerts.append(
                    CompanyHealthAlert(
                        title=f"{team.department} / {team.team_name} health degradation",
                        category="team_health",
                        severity=team.priority,
                        probability=team.risk_score,
                        impact=f"{team.team_name} health score is {round(team.health_score)} with {round(team.operational_risk)} operational risk.",
                        recommendation=team.recommendation,
                    )
                )
            if team.burnout_risk >= 65:
                alerts.append(
                    CompanyHealthAlert(
                        title=f"{team.team_name} burnout escalation",
                        category="burnout",
                        severity=self._priority(team.burnout_risk),
                        probability=team.burnout_risk,
                        impact=f"Burnout risk reached {round(team.burnout_risk)} and may affect delivery stability.",
                        recommendation="Reduce live meeting load, redistribute urgent incidents, and protect recovery time.",
                    )
                )
        if summary.company_health_score < 62:
            alerts.append(
                CompanyHealthAlert(
                    title="Company Health Score below executive threshold",
                    category="company_health",
                    severity=self._priority(100 - summary.company_health_score),
                    probability=round(100 - summary.company_health_score, 2),
                    impact=f"Enterprise health is {round(summary.company_health_score)}, below the safe operating band.",
                    recommendation="Trigger cross-functional stabilization review and require owner-level mitigation plans.",
                )
            )
        return sorted(alerts, key=lambda alert: alert.probability, reverse=True)[:8]

    def _executive_insights(self, teams: list[TeamHealthScore], summary: CompanyHealthSummary) -> list[str]:
        insights = [
            f"Company Health Score is {round(summary.company_health_score)} with {summary.high_risk_teams} high-risk team(s) under realtime watch.",
            f"Employee happiness is {round(summary.employee_happiness_score)} and productivity is {round(summary.productivity_score)} across monitored teams.",
            f"Burnout risk is {round(summary.burnout_risk)} and attrition risk is {round(summary.attrition_risk)}, creating a {round(summary.operational_risk)} operational risk score.",
        ]
        if teams:
            risk = teams[0]
            stable = max(teams, key=lambda team: team.health_score)
            insights.append(f"Highest-risk area is {risk.department} / {risk.team_name}; strongest operating zone is {stable.department} / {stable.team_name}.")
        insights.append("Company health combines RandomForest health scoring, GradientBoosting risk forecasting, workforce engagement, productivity, project, communication, security, and realtime KPI signals.")
        return insights

    @staticmethod
    def _dominant_risks(team: CompanyHealthTeamSignal, operational_risk: float) -> list[str]:
        risks = [
            ("burnout pressure", team.burnout_risk),
            ("attrition risk", team.attrition_risk),
            ("project health degradation", 100 - team.project_health),
            ("delivery instability", 100 - team.delivery_stability),
            ("communication health decline", 100 - team.communication_health),
            ("meeting inefficiency", 100 - team.meeting_efficiency),
            ("security risk", team.security_risk),
            ("resource overutilization", max(0, team.resource_utilization - 82) * 1.5),
            ("open project risks", team.open_project_risks * 4),
            ("active incidents", team.active_incidents * 8),
            ("operational risk", operational_risk),
        ]
        return [name for name, _ in sorted(risks, key=lambda item: item[1], reverse=True)[:4]]

    @staticmethod
    def _team_recommendation(team: CompanyHealthTeamSignal, risks: list[str], operational_risk: float) -> str:
        if operational_risk >= 78:
            return f"Open executive stabilization lane for {team.team_name}; reduce incident load, rebalance capacity, and assign risk owners."
        if "burnout pressure" in risks or "attrition risk" in risks:
            return f"Reduce workload pressure for {team.team_name} and run retention check-ins for critical contributors."
        if "delivery instability" in risks or "project health degradation" in risks:
            return f"Add delivery checkpoints and dependency owners for {team.team_name}."
        return f"Maintain current operating rhythm for {team.team_name} while monitoring leading risk indicators."

    @staticmethod
    def _project_action(team: TeamHealthScore, delay: float, productivity_risk: float) -> str:
        if delay >= 60:
            return f"Escalate delivery recovery for {team.team_name} and reduce scope risk this week."
        if productivity_risk >= 55:
            return f"Protect focus blocks and rebalance work for {team.team_name}."
        return f"Keep {team.team_name} on current delivery cadence with realtime monitoring."

    @staticmethod
    def _weighted_average(teams: list[TeamHealthScore], attr: str) -> float:
        total = sum(team.headcount for team in teams)
        if total <= 0:
            return 0.0
        return sum(getattr(team, attr) * team.headcount for team in teams) / total

    @staticmethod
    def _priority(score: float) -> CompanyHealthPriority:
        if score >= 82:
            return "critical"
        if score >= 64:
            return "high"
        if score >= 38:
            return "medium"
        return "low"

    @staticmethod
    def _status(score: float) -> CompanyHealthStatus:
        if score >= 82:
            return "optimal"
        if score >= 70:
            return "stable"
        if score >= 56:
            return "watch"
        if score >= 42:
            return "risk"
        return "critical"

    @staticmethod
    def _clip100(value: float) -> float:
        return max(0.0, min(100.0, float(value)))

    def _scenario_variant(self, base: CompanyHealthRequest, pressure_delta: float, positive_delta: float) -> CompanyHealthRequest:
        source = base if base.teams else self.default_request()
        teams = [
            team.model_copy(
                update={
                    "employee_happiness_score": self._clip100(team.employee_happiness_score + positive_delta),
                    "productivity_score": self._clip100(team.productivity_score + positive_delta),
                    "burnout_risk": self._clip100(team.burnout_risk + pressure_delta),
                    "attrition_risk": self._clip100(team.attrition_risk + pressure_delta * 0.72),
                    "project_health": self._clip100(team.project_health + positive_delta),
                    "delivery_stability": self._clip100(team.delivery_stability + positive_delta),
                    "resource_utilization": min(130, team.resource_utilization + pressure_delta * 0.65),
                    "communication_health": self._clip100(team.communication_health + positive_delta),
                    "meeting_efficiency": self._clip100(team.meeting_efficiency + positive_delta),
                    "workforce_engagement": self._clip100(team.workforce_engagement + positive_delta),
                    "open_project_risks": min(120, team.open_project_risks + round(pressure_delta / 4)),
                    "active_incidents": min(80, team.active_incidents + (1 if pressure_delta >= 8 else 0)),
                }
            )
            for team in source.teams
        ]
        return source.model_copy(update={"teams": teams, "realtime": True})

    def _append_jsonl(self, payload: dict[str, object]) -> None:
        with self._lock:
            with HISTORY_PATH.open("a", encoding="utf-8") as file:
                file.write(json.dumps(payload) + "\n")


company_health_service = CompanyHealthService()
