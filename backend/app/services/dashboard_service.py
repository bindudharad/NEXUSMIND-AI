from __future__ import annotations

from statistics import mean

from app.core.cache import TTLResponseCache
from app.schemas.dashboard import (
    AgentMessage,
    DashboardForecastPoint,
    DashboardOverview,
    DepartmentSignal,
    EnterpriseMetric,
    RiskSignal,
)
from app.schemas.forecasting import ForecastRequest
from app.services.anomaly_service import anomaly_service
from app.services.employee_dashboard_service import employee_dashboard_service
from app.services.forecasting_service import forecasting_service
from app.services.manager_dashboard_service import manager_dashboard_service
from app.services.project_failure_service import project_failure_service
from app.services.roi_service import roi_intelligence_service


class DashboardService:
    def __init__(self) -> None:
        self._cache: TTLResponseCache[DashboardOverview] = TTLResponseCache(ttl_seconds=6)

    def get_overview(self) -> DashboardOverview:
        return self._cache.get_or_set(self._get_overview_uncached)

    def _get_overview_uncached(self) -> DashboardOverview:
        employee = employee_dashboard_service.analyze()
        manager = manager_dashboard_service.analyze()
        projects = project_failure_service.analyze()
        anomalies = anomaly_service.detect()
        forecast = forecasting_service.forecast(ForecastRequest(department="Enterprise", horizon_days=14))
        roi = roi_intelligence_service.analyze()

        top_project = projects.predictions[0] if projects.predictions else None
        top_alert = max(anomalies.alerts, key=lambda alert: alert.insider_threat_score, default=None)
        future_productivity = mean(point.productivity for point in forecast.forecast[:7])
        security_score = self._security_score(anomalies.alerts)
        wellness_score = self._clamp(100 - employee.burnout_probability.value)
        instability_score = forecast.team_collapse_probability * 100
        project_health = projects.summary.average_health_score

        company_health = round(
            mean(
                [
                    employee.productivity.value,
                    wellness_score,
                    security_score,
                    project_health,
                    future_productivity,
                    100 - instability_score,
                ]
            )
        )
        prediction_confidence = round(
            mean(
                [
                    forecast.confidence * 100,
                    mean(prediction.confidence * 100 for prediction in projects.predictions) if projects.predictions else 82,
                    mean(insight.confidence * 100 for insight in roi.executive_insights) if roi.executive_insights else 82,
                ]
            )
        )

        return DashboardOverview(
            company_health=int(self._clamp(company_health)),
            prediction_confidence=int(self._clamp(prediction_confidence)),
            metrics=self._metrics(employee, projects, anomalies, forecast, roi, security_score, wellness_score),
            risk_signals=self._risk_signals(employee, projects, anomalies, forecast, top_project, top_alert),
            departments=self._department_signals(employee, manager, projects, anomalies),
            agent_messages=self._agent_messages(employee, projects, anomalies, roi, top_project, top_alert),
            forecast_series=self._forecast_series(forecast, roi),
        )

    def _metrics(self, employee, projects, anomalies, forecast, roi, security_score: float, wellness_score: float) -> list[EnterpriseMetric]:
        project_health = projects.summary.average_health_score
        throughput = self._clamp(1 + (employee.productivity.value - 72) / 100 + (1 - forecast.team_collapse_probability) * 0.12, 0.55, 1.65)
        return [
            EnterpriseMetric(
                label="Productivity",
                value=f"{round(employee.productivity.value)}%",
                trend=round(employee.productivity.trend_delta, 2),
                status=self._metric_status(employee.productivity.value),
            ),
            EnterpriseMetric(
                label="Employee Wellness",
                value=f"{round(wellness_score)}%",
                trend=round(-employee.burnout_probability.trend_delta, 2),
                status=self._metric_status(wellness_score),
            ),
            EnterpriseMetric(
                label="Security Posture",
                value=f"{round(security_score)}%",
                trend=round(-anomalies.anomaly_rate * 100, 2),
                status=self._metric_status(security_score),
            ),
            EnterpriseMetric(
                label="Revenue Forecast",
                value=f"${round(max(roi.summary.net_savings, 0) / 1_000_000, 2)}M",
                trend=round(min(32, roi.summary.roi_percent / 45), 2),
                status=self._metric_status(min(100, 62 + roi.summary.roi_percent / 18)),
            ),
            EnterpriseMetric(
                label="Project Health",
                value=f"{round(project_health)}%",
                trend=round(project_health - projects.summary.average_failure_probability, 2),
                status=self._metric_status(project_health),
            ),
            EnterpriseMetric(
                label="Team Throughput",
                value=f"{throughput:.2f}x",
                trend=round((throughput - 1) * 100, 2),
                status=self._metric_status(throughput * 70),
            ),
        ]

    def _risk_signals(self, employee, projects, anomalies, forecast, top_project, top_alert) -> list[RiskSignal]:
        signals = [
            RiskSignal(
                id=f"risk-burnout-{employee.employee_id}",
                name=f"{employee.department} burnout pressure",
                probability=round(employee.burnout_probability.value / 100, 3),
                impact=self._impact(employee.burnout_probability.value),
                recommendation=employee.recommendations[0] if employee.recommendations else "Rebalance workload before burnout accelerates.",
            ),
            RiskSignal(
                id=f"risk-forecast-{forecast.department.lower()}",
                name=f"{forecast.department} operational instability forecast",
                probability=round(forecast.team_collapse_probability, 3),
                impact=self._impact(forecast.team_collapse_probability * 100),
                recommendation=forecast.recommendation,
            ),
        ]
        if top_project is not None:
            signals.append(
                RiskSignal(
                    id=f"risk-project-{top_project.project_id}",
                    name=f"{top_project.project_name} delivery risk",
                    probability=round(top_project.deadline_miss_probability / 100, 3),
                    impact=self._impact(top_project.deadline_miss_probability),
                    recommendation=top_project.recommendations[0].action if top_project.recommendations else "Escalate delivery risk to executive review.",
                )
            )
        if top_alert is not None:
            signals.append(
                RiskSignal(
                    id=f"risk-security-{top_alert.alert_id}",
                    name=f"{top_alert.department} insider-threat pattern",
                    probability=round(top_alert.insider_threat_score / 100, 3),
                    impact=self._impact(top_alert.insider_threat_score),
                    recommendation=top_alert.recommendation,
                )
            )
        return sorted(signals, key=lambda item: item.probability, reverse=True)[:5]

    def _department_signals(self, employee, manager, projects, anomalies) -> list[DepartmentSignal]:
        departments: dict[str, dict[str, list[float]]] = {}

        def bucket(name: str) -> dict[str, list[float]]:
            return departments.setdefault(name, {"team": [], "project": [], "security": [], "burnout": [], "productivity": []})

        employee_bucket = bucket(employee.department)
        employee_bucket["burnout"].append(employee.burnout_probability.value)
        employee_bucket["productivity"].append(employee.productivity.value)

        for team in manager.risky_teams:
            bucket(team.department)["team"].append(team.risk_score)
        for project in projects.predictions:
            item = bucket(project.department)
            item["project"].append(project.failure_probability)
            item["productivity"].append(100 - project.productivity_slowdown)
        for alert in anomalies.alerts:
            bucket(alert.department)["security"].append(alert.insider_threat_score)

        signals: list[DepartmentSignal] = []
        for department, values in departments.items():
            team_risk = self._average(values["team"])
            project_risk = self._average(values["project"])
            security_risk = self._average(values["security"])
            burnout = self._average(values["burnout"])
            productivity = self._average(values["productivity"], default=88 - team_risk * 0.24 - project_risk * 0.16)
            risk = self._clamp(mean([team_risk, project_risk, security_risk, burnout]))
            signals.append(
                DepartmentSignal(
                    department=department,
                    productivity=round(self._clamp(productivity)),
                    wellness=round(self._clamp(100 - burnout * 0.62 - team_risk * 0.2)),
                    security=round(self._clamp(100 - security_risk)),
                    risk=round(risk),
                )
            )
        return sorted(signals, key=lambda item: item.risk, reverse=True)[:8]

    def _agent_messages(self, employee, projects, anomalies, roi, top_project, top_alert) -> list[AgentMessage]:
        messages = [
            AgentMessage(
                agent="HR Agent",
                message=employee.recommendations[0] if employee.recommendations else "Workforce wellness remains inside the adaptive threshold.",
                severity=self._agent_severity(employee.burnout_probability.value),
            ),
            AgentMessage(
                agent="Finance Agent",
                message=roi.executive_insights[0].message if roi.executive_insights else "ROI exposure is inside modeled recovery limits.",
                severity=self._agent_severity(min(100, roi.summary.baseline_annual_loss / 250_000)),
            ),
        ]
        if top_project is not None:
            messages.append(
                AgentMessage(
                    agent="Project Agent",
                    message=top_project.recommendations[0].action if top_project.recommendations else f"{top_project.project_name} remains under active forecasting.",
                    severity=self._agent_severity(top_project.failure_probability),
                )
            )
        if top_alert is not None:
            messages.append(
                AgentMessage(
                    agent="Security Agent",
                    message=top_alert.recommendation,
                    severity=self._agent_severity(top_alert.insider_threat_score),
                )
            )
        messages.append(
            AgentMessage(
                agent="Executive Agent",
                message=projects.portfolio_recommendations[0].action if projects.portfolio_recommendations else "Executive operating model is synchronized.",
                severity=self._agent_severity(projects.summary.average_failure_probability),
            )
        )
        return messages[:6]

    @staticmethod
    def _forecast_series(forecast, roi) -> list[DashboardForecastPoint]:
        series: list[DashboardForecastPoint] = []
        roi_points = roi.forecast or []
        for index, point in enumerate(forecast.forecast[:6]):
            roi_point = roi_points[min(index, len(roi_points) - 1)] if roi_points else None
            revenue = roi_point.cumulative_savings / 1_000_000 if roi_point else 0
            risk = max(point.delay_probability, point.burnout_risk, point.operational_instability) * 100
            series.append(
                DashboardForecastPoint(
                    label=point.date.strftime("%b %d"),
                    revenue=round(float(revenue), 2),
                    risk=round(float(risk), 2),
                    productivity=round(float(point.productivity), 2),
                )
            )
        return series

    @staticmethod
    def _security_score(alerts) -> float:
        if not alerts:
            return 98.0
        return DashboardService._clamp(100 - mean(alert.insider_threat_score for alert in alerts) * 0.54 - len(alerts) * 2.5)

    @staticmethod
    def _average(values: list[float], default: float = 0) -> float:
        return float(mean(values)) if values else default

    @staticmethod
    def _metric_status(score: float) -> str:
        if score >= 82:
            return "optimal"
        if score >= 64:
            return "watch"
        return "risk"

    @staticmethod
    def _impact(score: float) -> str:
        if score >= 82:
            return "critical"
        if score >= 64:
            return "high"
        if score >= 38:
            return "medium"
        return "low"

    @staticmethod
    def _agent_severity(score: float) -> str:
        if score >= 82:
            return "critical"
        if score >= 64:
            return "risk"
        if score >= 38:
            return "watch"
        return "optimal"

    @staticmethod
    def _clamp(value: float, lower: float = 0, upper: float = 100) -> float:
        return max(lower, min(upper, float(value)))


dashboard_service = DashboardService()
