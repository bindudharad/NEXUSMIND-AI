from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from uuid import NAMESPACE_DNS, uuid5

from app.core.cache import TTLResponseCache
from app.schemas.alerts import AIAlert, AlertAckRequest, AlertAckResponse, AlertDetectionRequest, AlertFeedResponse, AlertSummary
from app.schemas.anomaly import AnomalyDetectionRequest, BehaviorEvent
from app.schemas.employee_dashboard import EmployeeActivityPoint, EmployeeDashboardRequest
from app.schemas.forecasting import ForecastRequest, WorkloadHistoryPoint
from app.schemas.manager_dashboard import EmployeeWorkloadInput, ManagerDashboardRequest, ProjectDeliveryInput, TeamAnalyticsInput
from app.schemas.nlp import NLPAnalyzeRequest, NLPBatchRequest
from app.services.anomaly_service import anomaly_service
from app.services.employee_dashboard_service import employee_dashboard_service
from app.services.forecasting_service import forecasting_service
from app.services.manager_dashboard_service import manager_dashboard_service
from app.services.nlp_service import nlp_service


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
HISTORY_PATH = DATA_DIR / "ai_alert_history.jsonl"
ACK_PATH = DATA_DIR / "ai_alert_acknowledgements.jsonl"


class AIAlertService:
    model_name = "Cross-System AI Alert Correlator"

    def __init__(self) -> None:
        self._default_cache: TTLResponseCache[AlertFeedResponse] = TTLResponseCache(ttl_seconds=5)

    def feed(self, payload: AlertDetectionRequest | None = None) -> AlertFeedResponse:
        if payload is None:
            return self._default_cache.get_or_set(self._feed_uncached)
        return self._feed_uncached(payload)

    def _feed_uncached(self, payload: AlertDetectionRequest | None = None) -> AlertFeedResponse:
        request = payload or AlertDetectionRequest()
        now = datetime.now(timezone.utc)
        threshold = self._adaptive_threshold(request.sensitivity)
        manager = manager_dashboard_service.analyze(self._manager_payload(request) if request.scenario == "crisis" else None)
        employee = employee_dashboard_service.analyze(self._employee_payload(request) if request.scenario == "crisis" else None)
        anomaly = anomaly_service.detect(self._anomaly_payload(request) if request.scenario == "crisis" else None)
        nlp = nlp_service.batch(self._nlp_payload(request))
        forecast = forecasting_service.forecast(self._forecast_payload(request))

        alerts: list[AIAlert] = []
        alerts.extend(self._manager_alerts(manager, threshold, now))
        alerts.extend(self._employee_alerts(employee, threshold, now))
        alerts.extend(self._anomaly_alerts(anomaly, threshold, now))
        alerts.extend(self._nlp_alerts(nlp, threshold, now))
        alerts.extend(self._forecast_alerts(forecast, threshold, now))
        alerts = self._dedupe(alerts)

        acknowledgements = self._acknowledgements()
        for alert in alerts:
            if acknowledgements.get(alert.alert_id, False):
                alert.acknowledged = True

        alerts.sort(key=lambda item: (item.priority_rank, item.risk_score, item.confidence), reverse=True)
        for index, alert in enumerate(alerts, start=1):
            alert.priority_rank = index

        response = AlertFeedResponse(
            model=self.model_name,
            generated_at=now,
            scenario=request.scenario,
            adaptive_threshold=threshold,
            alerts=alerts[:12],
            summary=self._summary(alerts[:12]),
            storage=str(HISTORY_PATH),
        )
        self._append_jsonl(HISTORY_PATH, response.model_dump(mode="json"))
        return response

    def acknowledge(self, payload: AlertAckRequest) -> AlertAckResponse:
        self._default_cache.clear()
        record = {
            "alert_id": payload.alert_id,
            "acknowledged": payload.acknowledged,
            "notes": payload.notes,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._append_jsonl(ACK_PATH, record)
        state = "acknowledged" if payload.acknowledged else "reopened"
        return AlertAckResponse(
            alert_id=payload.alert_id,
            acknowledged=payload.acknowledged,
            message=f"Alert {state}; adaptive alert thresholds will incorporate this operator signal.",
            storage=str(ACK_PATH),
        )

    async def stream(self, payload: AlertDetectionRequest | None = None):
        request = payload or AlertDetectionRequest()
        for sequence in range(3):
            current = request.model_copy(update={"sensitivity": min(1, request.sensitivity + sequence * 0.02)})
            response = self.feed(current)
            data = response.model_dump(mode="json")
            data["summary"]["stream_sequence"] = sequence + 1
            yield f"event: alerts\ndata: {json.dumps(data)}\n\n"
            await asyncio.sleep(0.8)

    def _manager_alerts(self, manager, threshold: float, now: datetime) -> list[AIAlert]:
        alerts: list[AIAlert] = []
        for team in manager.risky_teams:
            if team.risk_score >= threshold:
                alerts.append(
                    self._alert(
                        "burnout",
                        f"{team.team_name} burnout escalation",
                        f"{team.team_name} has {round(team.risk_score)}% enterprise risk with burnout and overload drivers.",
                        team.risk_score,
                        ["manager_dashboard", manager.model, "random_forest", "xgboost"],
                        team.drivers,
                        team.recommendation,
                        now,
                        f"team:{team.team_id}:burnout",
                    )
                )
            if team.risk_score >= threshold and any("productivity" in driver for driver in team.drivers):
                alerts.append(
                    self._alert(
                        "productivity",
                        f"{team.team_name} productivity collapse risk",
                        f"{team.team_name} productivity decline is contributing to a {round(team.risk_score)}% team risk score.",
                        min(100, team.risk_score + 3),
                        ["manager_dashboard", manager.model],
                        team.drivers,
                        "Start a blocker review, protect focus time, and inspect delivery throughput for the next sprint.",
                        now,
                        f"team:{team.team_id}:productivity",
                    )
                )
        for employee in manager.overloaded_employees:
            if employee.overload_score >= threshold:
                alerts.append(
                    self._alert(
                        "overload",
                        f"{employee.employee_name} workload exceeds safe threshold",
                        f"{employee.employee_name} is operating at {round(employee.overload_score)}% overload pressure.",
                        employee.overload_score,
                        ["manager_dashboard", manager.model],
                        employee.drivers,
                        employee.recommendation,
                        now,
                        f"employee:{employee.employee_id}:overload",
                    )
                )
        for project in manager.delay_predictions:
            if project.delay_probability >= threshold:
                alerts.append(
                    self._alert(
                        "delay",
                        f"{project.project_name} delivery delay probability increased",
                        f"{project.project_name} has {round(project.delay_probability)}% probability of delivery delay.",
                        project.delay_probability,
                        ["manager_dashboard", manager.model, "time_series_forecasting"],
                        project.bottlenecks,
                        project.recommendation,
                        now,
                        f"project:{project.project_id}:delay",
                    )
                )
        if manager.summary.average_team_risk >= threshold * 0.9:
            alerts.append(
                self._alert(
                    "revenue",
                    "Revenue delivery risk is rising",
                    f"Average team risk is {round(manager.summary.average_team_risk)}% and delay risk is {round(manager.summary.average_delay_probability)}%, creating revenue exposure.",
                    min(100, (manager.summary.average_team_risk * 0.55) + (manager.summary.average_delay_probability * 0.45)),
                    ["manager_dashboard", "forecasting"],
                    ["project delivery risk", "capacity pressure", "missed deadline exposure"],
                    "Escalate revenue-critical projects and move dependency blockers into executive review.",
                    now,
                    "company:revenue:risk",
                )
            )
        return alerts

    def _employee_alerts(self, employee, threshold: float, now: datetime) -> list[AIAlert]:
        alerts: list[AIAlert] = []
        if employee.stress.value >= threshold:
            alerts.append(
                self._alert(
                    "burnout",
                    f"{employee.employee_name} stress spike detected",
                    f"{employee.employee_name} stress score reached {round(employee.stress.value)}/100 with burnout probability {round(employee.burnout_probability.value)}%.",
                    max(employee.stress.value, employee.burnout_probability.value),
                    ["employee_dashboard", employee.model, "random_forest", "xgboost", "neural_network"],
                    employee.stress.drivers + employee.burnout_probability.drivers,
                    employee.recommendations[0] if employee.recommendations else "Schedule a manager review and lower workload intensity.",
                    now,
                    f"employee:{employee.employee_id}:stress",
                )
            )
        if employee.productivity.value <= max(45, 100 - threshold):
            alerts.append(
                self._alert(
                    "productivity",
                    f"{employee.employee_name} productivity collapse detected",
                    f"{employee.employee_name} productivity score dropped to {round(employee.productivity.value)}/100.",
                    min(100, 100 - employee.productivity.value + abs(employee.productivity.trend_delta)),
                    ["employee_dashboard", employee.model],
                    employee.productivity.drivers,
                    "Run blocker triage and allocate protected focus sessions before the next checkpoint.",
                    now,
                    f"employee:{employee.employee_id}:productivity",
                )
            )
        if employee.history and employee.history[-1].burnout_probability >= threshold:
            alerts.append(
                self._alert(
                    "attendance",
                    f"{employee.employee_name} wellness availability anomaly",
                    "Burnout and absence drivers indicate availability reliability may degrade.",
                    employee.history[-1].burnout_probability,
                    ["employee_dashboard", "burnout_ensemble"],
                    ["absence pattern rising", *employee.burnout_probability.drivers],
                    "Protect recovery time and route the employee to a manager wellness intervention.",
                    now,
                    f"employee:{employee.employee_id}:attendance",
                )
            )
        return alerts

    def _anomaly_alerts(self, anomaly, threshold: float, now: datetime) -> list[AIAlert]:
        alerts: list[AIAlert] = []
        for item in anomaly.alerts:
            score = max(item.anomaly_score, item.insider_threat_score)
            if score >= threshold:
                alerts.append(
                    self._alert(
                        "security",
                        item.anomaly_type,
                        f"{item.employee_name} triggered behavioral anomaly score {round(item.anomaly_score)} and insider threat score {round(item.insider_threat_score)}.",
                        score,
                        ["anomaly_detection", anomaly.model, "isolation_forest", "local_outlier_factor"],
                        item.evidence,
                        item.recommendation,
                        now,
                        f"security:{item.employee_id}:{item.anomaly_type.lower().replace(' ', '-')}",
                    )
                )
        return alerts

    def _nlp_alerts(self, nlp, threshold: float, now: datetime) -> list[AIAlert]:
        alerts: list[AIAlert] = []
        toxicity = max((result.emotion_scores.toxicity for result in nlp.results), default=0) * 100
        stress = max((result.emotion_scores.stress for result in nlp.results), default=0) * 100
        if max(toxicity, stress) >= threshold:
            high_risk = max(nlp.results, key=lambda result: max(result.emotion_scores.toxicity, result.emotion_scores.stress))
            alerts.append(
                self._alert(
                    "toxicity",
                    "Negative communication trend increasing",
                    f"{high_risk.department} communication stream shows {round(toxicity)}% toxicity and {round(stress)}% stress signal.",
                    max(toxicity, stress),
                    ["nlp_sentiment", high_risk.model, "pytorch_text_emotion_net"],
                    [high_risk.primary_emotion, *high_risk.burnout_indicators],
                    high_risk.recommendation,
                    now,
                    f"nlp:{high_risk.department}:toxicity",
                )
            )
        return alerts

    def _forecast_alerts(self, forecast, threshold: float, now: datetime) -> list[AIAlert]:
        alerts: list[AIAlert] = []
        max_instability = max((point.operational_instability for point in forecast.forecast), default=0) * 100
        max_burnout = max((point.burnout_risk for point in forecast.forecast), default=0) * 100
        max_delay = max((point.delay_probability for point in forecast.forecast), default=0) * 100
        operational_score = max(max_instability, max_burnout, max_delay, forecast.team_collapse_probability * 100)
        if operational_score >= threshold * 0.85:
            alerts.append(
                self._alert(
                    "operations",
                    f"{forecast.department} operational instability forecast",
                    f"{forecast.department} forecast predicts {round(operational_score)}% operational risk over the next {forecast.horizon_days} days.",
                    operational_score,
                    ["time_series_forecasting", forecast.model, "lstm"],
                    [f"{signal.metric} trend {signal.direction} by {signal.change}" for signal in forecast.trend_signals],
                    forecast.recommendation,
                    now,
                    f"forecast:{forecast.department}:operations",
                )
            )
        return alerts

    def _alert(
        self,
        category,
        title: str,
        message: str,
        risk_score: float,
        source_systems: list[str],
        evidence: list[str],
        recommendation: str,
        created_at: datetime,
        group_key: str,
    ) -> AIAlert:
        score = round(float(min(100, max(0, risk_score))), 2)
        return AIAlert(
            alert_id=f"alert-{uuid5(NAMESPACE_DNS, group_key).hex[:12]}",
            category=category,
            title=title,
            message=message,
            severity=self._severity(score),
            risk_score=score,
            confidence=round(min(0.99, 0.58 + score / 250 + min(len(source_systems), 5) * 0.035), 3),
            source_systems=source_systems,
            evidence=list(dict.fromkeys(evidence))[:6],
            recommendation=recommendation,
            created_at=created_at,
            acknowledged=False,
            group_key=group_key,
            priority_rank=self._priority(score),
        )

    @staticmethod
    def _severity(score: float):
        if score >= 86:
            return "critical"
        if score >= 72:
            return "high"
        if score >= 55:
            return "medium"
        return "low"

    @staticmethod
    def _priority(score: float) -> int:
        if score >= 86:
            return 4
        if score >= 72:
            return 3
        if score >= 55:
            return 2
        return 1

    @staticmethod
    def _summary(alerts: list[AIAlert]) -> AlertSummary:
        return AlertSummary(
            total=len(alerts),
            critical=sum(1 for alert in alerts if alert.severity == "critical"),
            high=sum(1 for alert in alerts if alert.severity == "high"),
            unacknowledged=sum(1 for alert in alerts if not alert.acknowledged),
            average_risk=round(mean([alert.risk_score for alert in alerts]), 2) if alerts else 0,
            stream_sequence=1,
        )

    @staticmethod
    def _dedupe(alerts: list[AIAlert]) -> list[AIAlert]:
        grouped: dict[str, AIAlert] = {}
        for alert in alerts:
            current = grouped.get(alert.group_key)
            if current is None or alert.risk_score > current.risk_score:
                grouped[alert.group_key] = alert
        return list(grouped.values())

    @staticmethod
    def _append_jsonl(path: Path, payload: dict[str, object]) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, default=str) + "\n")

    @staticmethod
    def _acknowledgements() -> dict[str, bool]:
        if not ACK_PATH.exists():
            return {}
        states: dict[str, bool] = {}
        for line in ACK_PATH.read_text(encoding="utf-8").splitlines()[-300:]:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            states[str(record.get("alert_id"))] = bool(record.get("acknowledged", False))
        return states

    def _adaptive_threshold(self, sensitivity: float) -> float:
        base = 70 - sensitivity * 22
        if not ACK_PATH.exists():
            return round(float(min(76, max(42, base))), 2)
        acknowledgements: list[bool] = []
        for line in ACK_PATH.read_text(encoding="utf-8").splitlines()[-80:]:
            try:
                acknowledgements.append(bool(json.loads(line).get("acknowledged", False)))
            except json.JSONDecodeError:
                continue
        if not acknowledgements:
            return round(float(min(76, max(42, base))), 2)
        confirmed_pressure = sum(acknowledgements) / len(acknowledgements)
        return round(float(min(76, max(42, base - confirmed_pressure * 5))), 2)

    @staticmethod
    def _manager_payload(request: AlertDetectionRequest) -> ManagerDashboardRequest:
        return ManagerDashboardRequest(
            manager_id="mgr-alert-crisis",
            manager_name="Priya Raman",
            sensitivity=request.sensitivity,
            teams=[
                TeamAnalyticsInput(
                    team_id="team-alert-dev",
                    team_name="Development Team",
                    department="Engineering",
                    member_count=22,
                    burnout_probability=0.93,
                    productivity_decline=0.76,
                    average_stress=0.91,
                    toxicity_ratio=0.34,
                    overload_ratio=0.9,
                    missed_deadlines=12,
                    attendance_rate=0.76,
                    collaboration_score=0.46,
                    overtime_escalation=0.89,
                    dependency_bottlenecks=13,
                )
            ],
            employees=[
                EmployeeWorkloadInput(
                    employee_id="emp-alert-john",
                    employee_name="Employee John",
                    team_name="Development Team",
                    role="Backend Lead",
                    active_tasks=25,
                    overtime_hours=23,
                    meeting_hours=17,
                    productivity_score=0.42,
                    work_intensity=0.97,
                    deadline_pressure=0.95,
                    multi_project_allocation=7,
                    stress_score=0.94,
                    task_completion_ratio=0.42,
                )
            ],
            projects=[
                ProjectDeliveryInput(
                    project_id="project-alert-alpha",
                    project_name="Project Alpha",
                    team_name="Development Team",
                    task_completion_speed=0.3,
                    team_productivity_trend=-0.74,
                    historical_delivery_rate=0.47,
                    burnout_growth=0.88,
                    team_overload=0.93,
                    dependency_bottlenecks=14,
                    resource_shortage=0.74,
                    communication_efficiency=0.36,
                    scope_change_rate=0.68,
                    days_to_deadline=8,
                )
            ],
        )

    @staticmethod
    def _employee_payload(request: AlertDetectionRequest) -> EmployeeDashboardRequest:
        return EmployeeDashboardRequest(
            employee_id="emp-alert-john",
            employee_name="Employee John",
            department="Engineering",
            role="Backend Lead",
            current=EmployeeActivityPoint(
                timestamp=datetime.now(timezone.utc),
                overtime_hours=23,
                workload_intensity=95,
                meeting_hours=17,
                sentiment_score=-0.78,
                task_completion_ratio=0.43,
                attendance_rate=0.78,
                focus_hours=1.5,
                collaboration_score=0.48,
                activity_variance=0.9,
                negative_message_ratio=0.7,
                toxic_message_count=5,
                absence_days=7,
            ),
        )

    @staticmethod
    def _anomaly_payload(request: AlertDetectionRequest) -> AnomalyDetectionRequest:
        return AnomalyDetectionRequest(
            sensitivity=request.sensitivity,
            events=[
                BehaviorEvent(
                    employee_id="emp-alert-threat",
                    employee_name="Riya Malhotra",
                    department="Finance",
                    role="Finance Systems Admin",
                    timestamp=datetime.now(timezone.utc),
                    login_count=25,
                    failed_logins=16,
                    off_hours_logins=12,
                    inactive_hours=0.4,
                    productivity_score=0.81,
                    overtime_hours=4,
                    messages_sent=20,
                    negative_sentiment_ratio=0.24,
                    toxic_message_count=0,
                    data_download_mb=8900,
                    privileged_actions=40,
                    project_commits=2,
                    meeting_hours=3,
                    stress_score=0.43,
                    access_scope_changes=12,
                )
            ],
        )

    @staticmethod
    def _nlp_payload(request: AlertDetectionRequest) -> NLPBatchRequest:
        if request.scenario == "crisis":
            texts = [
                "I am exhausted, overloaded, and working late every night while the deadline keeps moving.",
                "This thread is hostile, people are blaming each other, and the team is burned out.",
            ]
        else:
            texts = [
                "I am overloaded and frustrated by weekend incident pressure.",
                "The handoff is tense and several messages are becoming hostile.",
                "The team is still motivated by the product launch progress.",
            ]
        return NLPBatchRequest(
            messages=[
                NLPAnalyzeRequest(employee_id=f"emp-alert-nlp-{index}", department="Engineering", channel="chat", text=text)
                for index, text in enumerate(texts, start=1)
            ]
        )

    @staticmethod
    def _forecast_payload(request: AlertDetectionRequest) -> ForecastRequest:
        if request.scenario == "default":
            return ForecastRequest(department="Engineering", horizon_days=14)
        history: list[WorkloadHistoryPoint] = []
        start = datetime.now(timezone.utc).date() - timedelta(days=20)
        for index in range(21):
            history.append(
                WorkloadHistoryPoint(
                    date=start + timedelta(days=index),
                    workload=min(100, 76 + index * 0.85),
                    productivity=max(40, 78 - index * 0.9),
                    overtime_hours=min(22, 10 + index * 0.35),
                    attendance_rate=max(0.72, 0.93 - index * 0.006),
                    task_completion_rate=max(0.46, 0.82 - index * 0.012),
                    burnout_risk=min(0.96, 0.5 + index * 0.021),
                    delay_probability=min(0.92, 0.44 + index * 0.02),
                )
            )
        return ForecastRequest(department="Engineering", horizon_days=14, history=history)


alert_service = AIAlertService()
