from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from threading import Lock

import numpy as np

from app.ai.time_series_engine import FEATURES, synthetic_history, time_series_forecaster
from app.schemas.forecasting import ForecastPoint, ForecastRequest, ForecastResponse, TrendSignal, WorkloadHistoryPoint


FORECAST_HISTORY_PATH = Path(__file__).resolve().parents[1] / "data" / "forecast_predictions.jsonl"


class ForecastHistoryRepository:
    def __init__(self) -> None:
        self._lock = Lock()
        FORECAST_HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)

    def append(self, record: dict[str, object]) -> None:
        with self._lock:
            with FORECAST_HISTORY_PATH.open("a", encoding="utf-8") as file:
                file.write(json.dumps(record, default=str) + "\n")


def default_history(days: int = 60) -> list[WorkloadHistoryPoint]:
    start = date.today() - timedelta(days=days - 1)
    history: list[WorkloadHistoryPoint] = []
    for index in range(days):
        weekly = np.sin(index / 7 * np.pi)
        workload = 57 + weekly * 4 + index * 0.04
        productivity = 88 - max(workload - 65, 0) * 0.18
        overtime = max(0.5, (workload - 49) / 7)
        burnout = min(0.42, 0.19 + max(workload - 58, 0) * 0.008)
        delay = min(0.34, 0.15 + max(workload - 60, 0) * 0.006)
        history.append(
            WorkloadHistoryPoint(
                date=start + timedelta(days=index),
                workload=round(float(workload), 2),
                productivity=round(float(productivity), 2),
                overtime_hours=round(float(overtime), 2),
                attendance_rate=round(float(0.965 - burnout * 0.025), 3),
                task_completion_rate=round(float(0.9 - burnout * 0.06), 3),
                burnout_risk=round(float(burnout), 3),
                delay_probability=round(float(delay), 3),
            )
        )
    return history


def _to_array(history: list[WorkloadHistoryPoint]) -> np.ndarray:
    return np.array(
        [
            [
                point.workload,
                point.productivity,
                point.overtime_hours,
                point.attendance_rate,
                point.task_completion_rate,
                point.burnout_risk,
                point.delay_probability,
            ]
            for point in history
        ],
        dtype=np.float32,
    )


class ForecastingService:
    def __init__(self) -> None:
        self._history = ForecastHistoryRepository()

    def forecast(self, payload: ForecastRequest) -> ForecastResponse:
        history = payload.history or default_history()
        history = sorted(history, key=lambda point: point.date)
        raw = _to_array(history)
        predictions = time_series_forecaster.forecast(raw, payload.horizon_days)
        last_date = history[-1].date
        forecast_points: list[ForecastPoint] = []
        for index, row in enumerate(predictions):
            workload, productivity, overtime, _attendance, completion, burnout, delay = row
            instability = float(np.clip((burnout * 0.42) + (delay * 0.36) + max(workload - 70, 0) / 100 + (1 - completion) * 0.18, 0, 1))
            band = 3.5 + index * 0.18
            forecast_points.append(
                ForecastPoint(
                    date=last_date + timedelta(days=index + 1),
                    workload=round(float(np.clip(workload, 0, 100)), 2),
                    productivity=round(float(np.clip(productivity, 0, 100)), 2),
                    burnout_risk=round(float(np.clip(burnout, 0, 1)), 3),
                    overtime_hours=round(float(np.clip(overtime, 0, 24)), 2),
                    delay_probability=round(float(np.clip(delay, 0, 1)), 3),
                    operational_instability=round(instability, 3),
                    lower_bound=round(float(max(workload - band, 0)), 2),
                    upper_bound=round(float(min(workload + band, 100)), 2),
                )
            )
        trend_signals = self._trend_signals(history, forecast_points)
        collapse_probability = round(
            min(
                1.0,
                max(point.burnout_risk for point in forecast_points) * 0.38
                + max(point.delay_probability for point in forecast_points) * 0.34
                + max(point.operational_instability for point in forecast_points) * 0.28,
            ),
            3,
        )
        recommendation = "Forecast is stable; continue monitoring workload trend."
        if collapse_probability >= 0.62:
            recommendation = "Trigger workload intervention, reduce overtime, and move project risk to executive review."
        elif collapse_probability >= 0.42:
            recommendation = "Rebalance tasks and reduce meeting load before burnout accelerates."
        response = ForecastResponse(
            department=payload.department,
            model=str(time_series_forecaster.metrics()["model"]),
            horizon_days=payload.horizon_days,
            confidence=round(max(0.55, 1 - float(time_series_forecaster.metrics()["validation_mae"]) * 2.2), 3),
            history=history,
            forecast=forecast_points,
            trend_signals=trend_signals,
            team_collapse_probability=collapse_probability,
            recommendation=recommendation,
            storage=str(FORECAST_HISTORY_PATH),
        )
        self._history.append(response.model_dump())
        return response

    @staticmethod
    def _trend_signals(history: list[WorkloadHistoryPoint], forecast: list[ForecastPoint]) -> list[TrendSignal]:
        recent_workload = sum(point.workload for point in history[-7:]) / 7
        future_workload = sum(point.workload for point in forecast[:7]) / min(7, len(forecast))
        recent_productivity = sum(point.productivity for point in history[-7:]) / 7
        future_productivity = sum(point.productivity for point in forecast[:7]) / min(7, len(forecast))
        recent_burnout = sum(point.burnout_risk for point in history[-7:]) / 7
        future_burnout = sum(point.burnout_risk for point in forecast[:7]) / min(7, len(forecast))
        return [
            _signal("workload", future_workload - recent_workload, high_when_positive=True),
            _signal("productivity", future_productivity - recent_productivity, high_when_positive=False),
            _signal("burnout", future_burnout - recent_burnout, high_when_positive=True),
        ]


def _signal(metric: str, change: float, high_when_positive: bool) -> TrendSignal:
    direction = "up" if change > 0 else "down" if change < 0 else "flat"
    magnitude = abs(change)
    risky = (change > 0 and high_when_positive) or (change < 0 and not high_when_positive)
    severity = "critical" if risky and magnitude > 8 else "watch" if risky and magnitude > 2 else "stable"
    return TrendSignal(metric=metric, direction=direction, change=round(float(change), 3), severity=severity)


forecasting_service = ForecastingService()
