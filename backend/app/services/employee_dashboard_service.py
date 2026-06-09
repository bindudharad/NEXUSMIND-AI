from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

from app.ai.burnout_model import BurnoutFeatures
from app.ai.employee_analytics_engine import employee_analytics_engine
from app.ai.enterprise_models import enterprise_model_registry
from app.core.cache import TTLResponseCache
from app.schemas.employee_dashboard import (
    EmployeeActivityPoint,
    EmployeeDashboardRequest,
    EmployeeDashboardResponse,
    EmployeeScore,
    EmployeeTrendPoint,
    ScoreStatus,
)


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
HISTORY_PATH = DATA_DIR / "employee_dashboard_history.jsonl"


class EmployeeDashboardService:
    def __init__(self) -> None:
        self._default_cache: TTLResponseCache[EmployeeDashboardResponse] = TTLResponseCache(ttl_seconds=8)

    def analyze(self, payload: EmployeeDashboardRequest | None = None) -> EmployeeDashboardResponse:
        if payload is None:
            return self._default_cache.get_or_set(self._analyze_uncached)
        return self._analyze_uncached(payload)

    def _analyze_uncached(self, payload: EmployeeDashboardRequest | None = None) -> EmployeeDashboardResponse:
        request = payload or EmployeeDashboardRequest()
        current = request.current or self.default_current()
        history = request.history or self.default_history(current)
        current_prediction = employee_analytics_engine.predict(current)
        model_probabilities = self._burnout_probabilities(current, current_prediction.stress_score, current_prediction.productivity_score)
        burnout_score = round(model_probabilities["employee_burnout"] * 100, 2)

        trend_history = history[-30:]
        trend_predictions = employee_analytics_engine.predict_many(trend_history)
        trend = [self._trend_point(point, prediction) for point, prediction in zip(trend_history, trend_predictions)]
        previous = trend[-6:] if len(trend) >= 6 else trend
        stress_delta = round(current_prediction.stress_score - self._avg([point.stress_score for point in previous]), 2)
        productivity_delta = round(current_prediction.productivity_score - self._avg([point.productivity_score for point in previous]), 2)
        burnout_delta = round(burnout_score - self._avg([point.burnout_probability for point in previous]), 2)

        response = EmployeeDashboardResponse(
            employee_id=request.employee_id,
            employee_name=request.employee_name,
            department=request.department,
            role=request.role,
            generated_at=datetime.now(timezone.utc),
            model=employee_analytics_engine.model_name,
            stress=EmployeeScore(
                label="Stress Score",
                value=current_prediction.stress_score,
                status=self._stress_status(current_prediction.stress_score),
                trend_delta=stress_delta,
                drivers=self._stress_drivers(current),
            ),
            productivity=EmployeeScore(
                label="Productivity Score",
                value=current_prediction.productivity_score,
                status=self._productivity_status(current_prediction.productivity_score),
                trend_delta=productivity_delta,
                drivers=self._productivity_drivers(current),
            ),
            burnout_probability=EmployeeScore(
                label="Burnout Probability",
                value=burnout_score,
                status=self._burnout_status(burnout_score),
                trend_delta=burnout_delta,
                drivers=self._burnout_drivers(current, current_prediction.stress_score),
            ),
            history=[*trend, self._trend_point(current, current_prediction, burnout_score)],
            recommendations=self._recommendations(current, current_prediction.stress_score, current_prediction.productivity_score, burnout_score),
            model_probabilities=model_probabilities,
            storage=str(HISTORY_PATH),
        )
        self._append_jsonl(HISTORY_PATH, response.model_dump(mode="json"))
        return response

    @staticmethod
    def default_current() -> EmployeeActivityPoint:
        now = datetime.now(timezone.utc)
        minute_wave = (now.minute % 12) / 12
        return EmployeeActivityPoint(
            timestamp=now,
            overtime_hours=12 + minute_wave * 2.4,
            workload_intensity=78 + minute_wave * 5,
            meeting_hours=10 + minute_wave * 2,
            sentiment_score=-0.38 - minute_wave * 0.08,
            task_completion_ratio=0.67 - minute_wave * 0.03,
            attendance_rate=0.9,
            focus_hours=3.4 - minute_wave * 0.3,
            collaboration_score=0.71,
            activity_variance=0.62 + minute_wave * 0.08,
            negative_message_ratio=0.38 + minute_wave * 0.05,
            toxic_message_count=1,
            absence_days=3,
        )

    @staticmethod
    def default_history(current: EmployeeActivityPoint) -> list[EmployeeActivityPoint]:
        rng = np.random.default_rng(122)
        points: list[EmployeeActivityPoint] = []
        start = current.timestamp - timedelta(days=21)
        for index in range(21):
            drift = index / 20
            points.append(
                EmployeeActivityPoint(
                    timestamp=start + timedelta(days=index),
                    overtime_hours=float(np.clip(5.5 + drift * 6.5 + rng.normal(0, 0.8), 0, 22)),
                    workload_intensity=float(np.clip(58 + drift * 18 + rng.normal(0, 2.4), 20, 100)),
                    meeting_hours=float(np.clip(6 + drift * 4.6 + rng.normal(0, 0.7), 0, 18)),
                    sentiment_score=float(np.clip(0.08 - drift * 0.42 + rng.normal(0, 0.07), -1, 1)),
                    task_completion_ratio=float(np.clip(0.87 - drift * 0.18 + rng.normal(0, 0.025), 0.2, 1)),
                    attendance_rate=float(np.clip(0.97 - drift * 0.07 + rng.normal(0, 0.015), 0.55, 1)),
                    focus_hours=float(np.clip(6.2 - drift * 2.3 + rng.normal(0, 0.25), 0, 12)),
                    collaboration_score=float(np.clip(0.84 - drift * 0.1 + rng.normal(0, 0.025), 0.2, 1)),
                    activity_variance=float(np.clip(0.25 + drift * 0.34 + rng.normal(0, 0.04), 0, 1)),
                    negative_message_ratio=float(np.clip(0.13 + drift * 0.26 + rng.normal(0, 0.03), 0, 1)),
                    toxic_message_count=int(np.clip(round(drift * 2 + rng.poisson(0.2)), 0, 12)),
                    absence_days=float(np.clip(round(drift * 4 + rng.poisson(0.4)), 0, 14)),
                )
            )
        return points

    def _trend_point(self, point: EmployeeActivityPoint, prediction=None, burnout_probability: float | None = None) -> EmployeeTrendPoint:
        prediction = prediction or employee_analytics_engine.predict(point)
        burnout = burnout_probability if burnout_probability is not None else self._historical_burnout_pressure(point, prediction.stress_score, prediction.productivity_score)
        return EmployeeTrendPoint(
            timestamp=point.timestamp,
            stress_score=prediction.stress_score,
            productivity_score=prediction.productivity_score,
            burnout_probability=round(burnout, 2),
            workload_intensity=point.workload_intensity,
            sentiment_score=point.sentiment_score,
        )

    @staticmethod
    def _historical_burnout_pressure(point: EmployeeActivityPoint, stress_score: float, productivity_score: float) -> float:
        return float(
            np.clip(
                stress_score * 0.54
                + max(0, 78 - productivity_score) * 0.42
                + point.overtime_hours * 0.78
                + point.meeting_hours * 0.32
                + max(0, -point.sentiment_score) * 12,
                0,
                98,
            )
        )

    @staticmethod
    def _burnout_probabilities(point: EmployeeActivityPoint, stress_score: float, productivity_score: float) -> dict[str, float]:
        probabilities = enterprise_model_registry.predict(
            BurnoutFeatures(
                overtime_hours=point.overtime_hours,
                meeting_hours=point.meeting_hours,
                sentiment_score=point.sentiment_score,
                task_completion_ratio=point.task_completion_ratio,
                absence_days=point.absence_days,
            )
        )
        stress_pressure = stress_score / 100
        productivity_pressure = max(0, 78 - productivity_score) / 78
        probabilities["employee_burnout"] = round(
            min(0.98, probabilities["ensemble"] * 0.72 + stress_pressure * 0.18 + productivity_pressure * 0.1),
            3,
        )
        return probabilities

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
    def _recommendations(point: EmployeeActivityPoint, stress: float, productivity: float, burnout: float) -> list[str]:
        recommendations: list[str] = []
        if stress >= 72:
            recommendations.append("Move two high-focus tasks away from this employee for the next sprint cycle.")
        if point.meeting_hours >= 10:
            recommendations.append("Reduce recurring meetings by at least 3 hours this week.")
        if productivity <= 68:
            recommendations.append("Create two protected focus blocks and review blockers with the manager.")
        if burnout >= 62:
            recommendations.append("Schedule recovery time and trigger a wellness check-in within 24 hours.")
        if point.sentiment_score <= -0.35:
            recommendations.append("Review recent communication sentiment and route conflict signals to HR.")
        return recommendations or ["Maintain current workload balance and continue passive monitoring."]

    @staticmethod
    def _stress_status(value: float) -> ScoreStatus:
        if value >= 78:
            return "high_risk"
        if value >= 62:
            return "watch"
        if value >= 38:
            return "stable"
        return "optimal"

    @staticmethod
    def _productivity_status(value: float) -> ScoreStatus:
        if value >= 82:
            return "optimal"
        if value >= 68:
            return "stable"
        if value >= 52:
            return "watch"
        return "high_risk"

    @staticmethod
    def _burnout_status(value: float) -> ScoreStatus:
        if value >= 72:
            return "high_risk"
        if value >= 52:
            return "watch"
        if value >= 28:
            return "stable"
        return "optimal"

    @staticmethod
    def _avg(values: list[float]) -> float:
        return round(sum(values) / len(values), 2) if values else 0

    @staticmethod
    def _append_jsonl(path: Path, payload: dict[str, object]) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload) + "\n")


employee_dashboard_service = EmployeeDashboardService()
