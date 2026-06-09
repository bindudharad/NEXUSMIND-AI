from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from threading import Lock

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

from app.schemas.employee_dashboard import EmployeeActivityPoint, EmployeeDashboardRequest
from app.schemas.nlp import NLPAnalyzeRequest, NLPBatchRequest
from app.schemas.productivity import (
    AppUsageSegment,
    DeepWorkAnalytics,
    DistractionAnalytics,
    EnergyForecastPoint,
    HourlyProductivityPoint,
    ProductivityActivityWindow,
    ProductivityAnalysisResponse,
    ProductivityAnalyzeRequest,
    ProductivityHeatmapCell,
    ProductivityMessage,
    ProductivityRecommendation,
    ProductivityRiskAlert,
    ProductivitySummary,
    ToolSwitchingAnalytics,
)
from app.services.employee_dashboard_service import employee_dashboard_service
from app.services.nlp_service import nlp_service


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
HISTORY_PATH = DATA_DIR / "productivity_leakage_history.jsonl"
ARTIFACT_DIR = Path(__file__).resolve().parents[1] / "ai" / "artifacts"
MODEL_PATH = ARTIFACT_DIR / "productivity_leakage_models.joblib"
METRICS_PATH = ARTIFACT_DIR / "productivity_leakage_metrics.json"


class ProductivityLeakageModel:
    model_name = "RandomForest Productivity Leakage + IsolationForest Behavior Model"
    feature_names = [
        "active_minutes",
        "productive_ratio",
        "idle_ratio",
        "distraction_ratio",
        "app_switches_per_hour",
        "tab_switches_per_hour",
        "notifications_per_hour",
        "meeting_ratio",
        "deep_work_ratio",
        "keyboard_intensity",
        "mouse_intensity",
        "task_completion_ratio",
        "focus_quality",
        "negative_sentiment",
        "workload_pressure",
    ]

    def __init__(self) -> None:
        ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
        self.leakage_model: RandomForestRegressor | None = None
        self.focus_model: RandomForestRegressor | None = None
        self.efficiency_model: RandomForestRegressor | None = None
        self.anomaly_model: IsolationForest | None = None
        self.metrics: dict[str, float | int | str] = {}
        self._load_or_train()

    def _load_or_train(self) -> None:
        if MODEL_PATH.exists() and METRICS_PATH.exists():
            bundle = joblib.load(MODEL_PATH)
            self.leakage_model = bundle["leakage"]
            self.focus_model = bundle["focus"]
            self.efficiency_model = bundle["efficiency"]
            self.anomaly_model = bundle["anomaly"]
            self.metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
            return
        self.train()

    @property
    def available(self) -> bool:
        return self.leakage_model is not None and self.focus_model is not None and self.efficiency_model is not None

    def train(self) -> dict[str, float | int | str]:
        rng = np.random.default_rng(319)
        features, leakage, focus, efficiency = self._dataset(rng, 5200)
        x_train, x_test, leakage_train, leakage_test, focus_train, focus_test, efficiency_train, efficiency_test = train_test_split(
            features,
            leakage,
            focus,
            efficiency,
            test_size=0.22,
            random_state=31,
        )
        self.leakage_model = RandomForestRegressor(n_estimators=240, max_depth=12, min_samples_leaf=4, random_state=31, n_jobs=-1)
        self.focus_model = RandomForestRegressor(n_estimators=220, max_depth=12, min_samples_leaf=4, random_state=37, n_jobs=-1)
        self.efficiency_model = RandomForestRegressor(n_estimators=220, max_depth=11, min_samples_leaf=4, random_state=41, n_jobs=-1)
        self.anomaly_model = IsolationForest(n_estimators=160, contamination=0.08, random_state=43)
        self.leakage_model.fit(x_train, leakage_train)
        self.focus_model.fit(x_train, focus_train)
        self.efficiency_model.fit(x_train, efficiency_train)
        self.anomaly_model.fit(x_train)
        leakage_pred = self.leakage_model.predict(x_test)
        focus_pred = self.focus_model.predict(x_test)
        efficiency_pred = self.efficiency_model.predict(x_test)
        self.metrics = {
            "model": self.model_name,
            "training_examples": len(features),
            "leakage_mae": round(float(mean_absolute_error(leakage_test, leakage_pred)), 3),
            "leakage_r2": round(float(r2_score(leakage_test, leakage_pred)), 3),
            "focus_mae": round(float(mean_absolute_error(focus_test, focus_pred)), 3),
            "focus_r2": round(float(r2_score(focus_test, focus_pred)), 3),
            "efficiency_mae": round(float(mean_absolute_error(efficiency_test, efficiency_pred)), 3),
            "efficiency_r2": round(float(r2_score(efficiency_test, efficiency_pred)), 3),
        }
        joblib.dump(
            {
                "leakage": self.leakage_model,
                "focus": self.focus_model,
                "efficiency": self.efficiency_model,
                "anomaly": self.anomaly_model,
            },
            MODEL_PATH,
        )
        METRICS_PATH.write_text(json.dumps(self.metrics, indent=2), encoding="utf-8")
        return self.metrics

    def predict(self, features: list[list[float]]) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        if not self.available:
            self.train()
        matrix = np.array(features, dtype=np.float32)
        leakage = self.leakage_model.predict(matrix) if self.leakage_model else np.zeros(len(matrix))
        focus = self.focus_model.predict(matrix) if self.focus_model else np.zeros(len(matrix))
        efficiency = self.efficiency_model.predict(matrix) if self.efficiency_model else np.zeros(len(matrix))
        anomaly = self.anomaly_model.decision_function(matrix) if self.anomaly_model else np.zeros(len(matrix))
        return (
            np.clip(leakage, 0, 100),
            np.clip(focus, 0, 100),
            np.clip(efficiency, 0, 100),
            anomaly,
        )

    @staticmethod
    def _dataset(rng: np.random.Generator, rows: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        active = rng.normal(49, 8, rows).clip(8, 60)
        productive_ratio = rng.beta(6.2, 2.4, rows).clip(0.05, 1)
        idle_ratio = rng.beta(1.6, 8.0, rows).clip(0, 0.85)
        distraction_ratio = rng.beta(1.8, 9.0, rows).clip(0, 0.9)
        app_switches = rng.normal(23, 13, rows).clip(0, 120)
        tab_switches = rng.normal(34, 22, rows).clip(0, 180)
        notifications = rng.normal(16, 11, rows).clip(0, 120)
        meeting_ratio = rng.beta(2.2, 5.0, rows).clip(0, 0.95)
        deep_work_ratio = rng.beta(4.0, 3.2, rows).clip(0, 1)
        keyboard = rng.normal(28, 12, rows).clip(0, 90)
        mouse = rng.normal(12, 8, rows).clip(0, 70)
        completion = rng.beta(6.5, 2.0, rows).clip(0.05, 1)
        focus_quality = rng.beta(5.4, 2.3, rows).clip(0.05, 1)
        negative_sentiment = rng.beta(1.7, 6.5, rows).clip(0, 1)
        workload_pressure = rng.beta(3.2, 3.5, rows).clip(0, 1)

        switch_pressure = np.clip(app_switches / 60, 0, 1) * 17 + np.clip(tab_switches / 90, 0, 1) * 14
        notification_pressure = np.clip(notifications / 60, 0, 1) * 13
        leakage = (
            idle_ratio * 30
            + distraction_ratio * 34
            + switch_pressure
            + notification_pressure
            + meeting_ratio * 16
            + negative_sentiment * 8
            + workload_pressure * 9
            - deep_work_ratio * 18
            - completion * 9
            - focus_quality * 11
            + rng.normal(0, 2.8, rows)
        ).clip(0, 100)
        focus = (
            focus_quality * 42
            + deep_work_ratio * 31
            + completion * 18
            + productive_ratio * 14
            - idle_ratio * 18
            - distraction_ratio * 23
            - np.clip(app_switches / 80, 0, 1) * 13
            - np.clip(tab_switches / 110, 0, 1) * 10
            - meeting_ratio * 11
            + rng.normal(0, 2.5, rows)
        ).clip(0, 100)
        efficiency = (
            productive_ratio * 34
            + completion * 31
            + focus_quality * 19
            + deep_work_ratio * 18
            - leakage * 0.38
            - meeting_ratio * 8
            - workload_pressure * 5
            + rng.normal(0, 2.3, rows)
        ).clip(0, 100)
        features = np.column_stack(
            [
                active,
                productive_ratio,
                idle_ratio,
                distraction_ratio,
                app_switches,
                tab_switches,
                notifications,
                meeting_ratio,
                deep_work_ratio,
                keyboard,
                mouse,
                completion,
                focus_quality,
                negative_sentiment,
                workload_pressure,
            ]
        ).astype(np.float32)
        return features, leakage.astype(np.float32), focus.astype(np.float32), efficiency.astype(np.float32)


class ProductivityLeakageService:
    model_name = "Productivity Leakage Detector AI"
    behavioral_model = "App-Switch, Idle-Time, Deep-Work, Notification, and Energy Trend Behavioral Pipeline"

    def __init__(self) -> None:
        self._lock = Lock()
        self._ml = ProductivityLeakageModel()
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def analyze(self, payload: ProductivityAnalyzeRequest | None = None) -> ProductivityAnalysisResponse:
        request = payload or self.default_request()
        windows = request.windows or self.default_request().windows
        app_usage = request.app_usage or self.default_request().app_usage
        work_pattern = request.work_pattern or employee_dashboard_service.default_current()
        messages = request.messages or self.default_request().messages
        nlp = nlp_service.batch(
            NLPBatchRequest(
                messages=[
                    NLPAnalyzeRequest(
                        employee_id=request.employee_id,
                        department=request.department,
                        channel=message.channel,
                        text=message.text,
                    )
                    for message in messages
                ]
            )
        )
        employee_prediction = employee_dashboard_service.analyze(
            EmployeeDashboardRequest(
                employee_id=request.employee_id,
                employee_name=request.employee_name,
                department=request.department,
                role=request.role,
                current=work_pattern,
            )
        )
        employee_productivity = employee_prediction.productivity.value
        negative_sentiment = max(0, -nlp.team_sentiment_score)
        workload_pressure = min(1, work_pattern.workload_intensity / 100 * 0.72 + work_pattern.overtime_hours / 40 * 0.28)
        feature_rows = [self._features(window, negative_sentiment, workload_pressure) for window in windows]
        leakage_values, focus_values, efficiency_values, anomaly_scores = self._ml.predict(feature_rows)
        hourly = self._hourly_trend(windows, leakage_values, focus_values, efficiency_values, anomaly_scores)
        tool_switching = self._tool_switching(windows, app_usage)
        distractions = self._distractions(windows, app_usage, request.hourly_cost)
        deep_work = self._deep_work(windows, tool_switching, distractions)
        energy = self._energy_forecast(hourly, work_pattern, nlp.team_sentiment_score)
        summary = self._summary(hourly, tool_switching, distractions, deep_work, request.hourly_cost, employee_productivity)
        heatmap = self._heatmap(hourly)
        recommendations = self._recommendations(summary, tool_switching, distractions, deep_work, energy)
        alerts = self._alerts(summary, tool_switching, distractions, deep_work)
        insights = self._executive_insights(request, summary, tool_switching, distractions, deep_work, hourly)
        response = ProductivityAnalysisResponse(
            model=self.model_name,
            generated_at=datetime.now(timezone.utc),
            employee_id=request.employee_id,
            employee_name=request.employee_name,
            department=request.department,
            role=request.role,
            ml_model=str(self._ml.metrics.get("model", ProductivityLeakageModel.model_name)),
            nlp_model=nlp.results[0].model if nlp.results else "PyTorch TextEmotionNet",
            behavioral_model=self.behavioral_model,
            summary=summary,
            hourly_trend=hourly,
            tool_switching=tool_switching,
            distraction_analytics=distractions,
            deep_work_analytics=deep_work,
            energy_forecast=energy,
            leakage_heatmap=heatmap,
            recommendations=recommendations,
            risk_alerts=alerts,
            executive_insights=insights,
            storage=str(HISTORY_PATH),
        )
        self._append_jsonl(response.model_dump(mode="json"))
        return response

    async def stream(self, payload: ProductivityAnalyzeRequest | None = None):
        base = payload or self.default_request()
        scenarios = [
            base,
            self._scenario_variant(base, switch_delta=6, distraction_delta=2, notification_delta=5),
            self._scenario_variant(base, switch_delta=14, distraction_delta=5, notification_delta=12),
        ]
        for sequence, scenario in enumerate(scenarios, start=1):
            response = self.analyze(scenario)
            data = response.model_dump(mode="json")
            data["summary"]["stream_sequence"] = sequence
            yield f"event: productivity\ndata: {json.dumps(data)}\n\n"
            await asyncio.sleep(0.8)

    @staticmethod
    def default_request() -> ProductivityAnalyzeRequest:
        windows = [
            ProductivityActivityWindow(hour=9, active_minutes=55, productive_minutes=46, idle_minutes=2, app_switches=14, tab_switches=18, notifications=6, meeting_minutes=0, deep_work_minutes=42, keyboard_events=2100, mouse_events=520, distraction_minutes=2, task_completion_ratio=0.9, focus_quality=0.88),
            ProductivityActivityWindow(hour=10, active_minutes=54, productive_minutes=44, idle_minutes=3, app_switches=17, tab_switches=20, notifications=7, meeting_minutes=5, deep_work_minutes=38, keyboard_events=2050, mouse_events=600, distraction_minutes=3, task_completion_ratio=0.88, focus_quality=0.84),
            ProductivityActivityWindow(hour=11, active_minutes=52, productive_minutes=39, idle_minutes=5, app_switches=24, tab_switches=31, notifications=14, meeting_minutes=14, deep_work_minutes=26, keyboard_events=1650, mouse_events=810, distraction_minutes=5, task_completion_ratio=0.8, focus_quality=0.72),
            ProductivityActivityWindow(hour=12, active_minutes=38, productive_minutes=21, idle_minutes=10, app_switches=31, tab_switches=45, notifications=22, meeting_minutes=22, deep_work_minutes=8, keyboard_events=900, mouse_events=760, distraction_minutes=7, task_completion_ratio=0.62, focus_quality=0.5),
            ProductivityActivityWindow(hour=14, active_minutes=49, productive_minutes=23, idle_minutes=9, app_switches=46, tab_switches=69, notifications=35, meeting_minutes=18, deep_work_minutes=7, keyboard_events=1180, mouse_events=1120, distraction_minutes=12, task_completion_ratio=0.58, focus_quality=0.42),
            ProductivityActivityWindow(hour=15, active_minutes=47, productive_minutes=20, idle_minutes=11, app_switches=52, tab_switches=74, notifications=42, meeting_minutes=16, deep_work_minutes=5, keyboard_events=1040, mouse_events=1200, distraction_minutes=14, task_completion_ratio=0.53, focus_quality=0.36),
            ProductivityActivityWindow(hour=16, active_minutes=50, productive_minutes=31, idle_minutes=6, app_switches=29, tab_switches=38, notifications=19, meeting_minutes=10, deep_work_minutes=20, keyboard_events=1500, mouse_events=830, distraction_minutes=6, task_completion_ratio=0.73, focus_quality=0.66),
            ProductivityActivityWindow(hour=17, active_minutes=42, productive_minutes=27, idle_minutes=7, app_switches=26, tab_switches=35, notifications=17, meeting_minutes=4, deep_work_minutes=17, keyboard_events=1200, mouse_events=610, distraction_minutes=5, task_completion_ratio=0.7, focus_quality=0.62),
        ]
        return ProductivityAnalyzeRequest(
            employee_id="emp-productivity-001",
            employee_name="Aarav Mehta",
            department="Engineering",
            role="Senior Backend Engineer",
            windows=windows,
            app_usage=[
                AppUsageSegment(app_name="VS Code", category="development", minutes=180, switches=38, notification_count=0, productive=True),
                AppUsageSegment(app_name="Jira", category="planning", minutes=52, switches=31, notification_count=12, productive=True),
                AppUsageSegment(app_name="Slack", category="communication", minutes=76, switches=58, notification_count=54, productive=False),
                AppUsageSegment(app_name="Email", category="communication", minutes=42, switches=29, notification_count=33, productive=False),
                AppUsageSegment(app_name="Browser research", category="research", minutes=64, switches=46, notification_count=4, productive=True),
                AppUsageSegment(app_name="Social tabs", category="distraction", minutes=21, switches=18, notification_count=6, productive=False),
            ],
            work_pattern=employee_dashboard_service.default_current(),
            messages=[
                ProductivityMessage(text="The constant Slack and Jira switching is breaking focus during the release work.", channel="chat"),
                ProductivityMessage(text="I lose the deepest work window after lunch because meetings and notifications pile up.", channel="slack"),
            ],
            hourly_cost=85,
        )

    @staticmethod
    def _features(window: ProductivityActivityWindow, negative_sentiment: float, workload_pressure: float) -> list[float]:
        active_hours = max(window.active_minutes / 60, 0.1)
        return [
            window.active_minutes,
            window.productive_minutes / max(window.active_minutes, 1),
            window.idle_minutes / 60,
            window.distraction_minutes / 60,
            window.app_switches / active_hours,
            window.tab_switches / active_hours,
            window.notifications / active_hours,
            window.meeting_minutes / 60,
            window.deep_work_minutes / 60,
            window.keyboard_events / max(window.active_minutes, 1) / 60,
            window.mouse_events / max(window.active_minutes, 1) / 60,
            window.task_completion_ratio,
            window.focus_quality,
            negative_sentiment,
            workload_pressure,
        ]

    @staticmethod
    def _hourly_trend(
        windows: list[ProductivityActivityWindow],
        leakage_values,
        focus_values,
        efficiency_values,
        anomaly_scores,
    ) -> list[HourlyProductivityPoint]:
        trend: list[HourlyProductivityPoint] = []
        for window, leakage, focus, efficiency, anomaly in zip(windows, leakage_values, focus_values, efficiency_values, anomaly_scores):
            anomaly_penalty = max(0, -float(anomaly)) * 18
            leakage_score = float(np.clip(leakage + anomaly_penalty, 0, 100))
            focus_score = float(np.clip(focus - anomaly_penalty * 0.4, 0, 100))
            efficiency_score = float(np.clip(efficiency - anomaly_penalty * 0.35, 0, 100))
            leakage_minutes = float(np.clip(window.idle_minutes + window.distraction_minutes + max(0, window.app_switches - 22) * 0.18 + max(0, window.notifications - 12) * 0.12 + window.meeting_minutes * 0.14, 0, 60))
            dominant = "tool switching"
            if window.distraction_minutes >= max(window.meeting_minutes, window.idle_minutes):
                dominant = "distractions"
            elif window.meeting_minutes >= max(window.distraction_minutes, window.idle_minutes):
                dominant = "meeting interruptions"
            elif window.idle_minutes > 8:
                dominant = "idle time"
            energy = float(np.clip(focus_score * 0.48 + efficiency_score * 0.28 + window.deep_work_minutes * 0.55 - leakage_score * 0.12, 0, 100))
            trend.append(
                HourlyProductivityPoint(
                    hour_label=f"{window.hour:02d}:00",
                    productivity_score=round(efficiency_score, 2),
                    focus_score=round(focus_score, 2),
                    efficiency_score=round(efficiency_score, 2),
                    leakage_minutes=round(leakage_minutes, 2),
                    energy_score=round(energy, 2),
                    deep_work_minutes=round(window.deep_work_minutes, 2),
                    dominant_cause=dominant,
                )
            )
        return trend

    @staticmethod
    def _tool_switching(windows: list[ProductivityActivityWindow], app_usage: list[AppUsageSegment]) -> ToolSwitchingAnalytics:
        active_hours = sum(window.active_minutes for window in windows) / 60
        app_switches_per_hour = sum(window.app_switches for window in windows) / max(active_hours, 0.1)
        tab_switches_per_hour = sum(window.tab_switches for window in windows) / max(active_hours, 0.1)
        overloaded = sorted(
            [
                app
                for app in app_usage
                if app.switches >= 24 or app.notification_count >= 24 or app.category in {"communication", "distraction"}
            ],
            key=lambda app: app.switches + app.notification_count,
            reverse=True,
        )
        penalty = float(np.clip(max(0, app_switches_per_hour - 20) * 1.1 + max(0, tab_switches_per_hour - 28) * 0.75, 0, 100))
        fatigue = float(np.clip(penalty * 0.62 + sum(app.notification_count for app in app_usage) / max(active_hours, 1) * 0.42, 0, 100))
        loss = float(np.clip(penalty * 0.42 + fatigue * 0.24, 0, 100))
        tools = [app.app_name for app in overloaded[:5]]
        return ToolSwitchingAnalytics(
            app_switches_per_hour=round(app_switches_per_hour, 2),
            tab_switches_per_hour=round(tab_switches_per_hour, 2),
            context_switch_penalty=round(penalty, 2),
            overloaded_tools=tools,
            fatigue_score=round(fatigue, 2),
            productivity_loss_percent=round(loss, 2),
            insight=(
                f"Tool-switching overload reduced productivity by {round(loss)}%; "
                f"highest pressure came from {', '.join(tools[:3]) or 'workflow switching'}."
            ),
        )

    @staticmethod
    def _distractions(windows: list[ProductivityActivityWindow], app_usage: list[AppUsageSegment], hourly_cost: float) -> DistractionAnalytics:
        idle = sum(window.idle_minutes for window in windows)
        distraction = sum(window.distraction_minutes for window in windows)
        notifications = sum(window.notifications for window in windows)
        active_hours = sum(window.active_minutes for window in windows) / 60
        distraction_apps = sorted(
            [app for app in app_usage if app.category in {"communication", "distraction"} or not app.productive],
            key=lambda app: app.minutes + app.notification_count * 0.8,
            reverse=True,
        )
        notification_pressure = float(np.clip(notifications / max(active_hours, 1) * 2.2, 0, 100))
        lost_hours = round((idle + distraction + notifications * 0.45) / 60, 2)
        score = float(np.clip(distraction / max(sum(window.active_minutes for window in windows), 1) * 185 + notification_pressure * 0.36 + idle / max(active_hours, 1) * 2.2, 0, 100))
        sources = [app.app_name for app in distraction_apps[:4]]
        return DistractionAnalytics(
            distraction_score=round(score, 2),
            idle_time_minutes=round(idle, 2),
            distraction_minutes=round(distraction, 2),
            notification_pressure=round(notification_pressure, 2),
            top_distraction_sources=sources,
            estimated_lost_hours=lost_hours,
            insight=(
                f"Employee lost approximately {lost_hours} productive hours; "
                f"notification pressure is {round(notification_pressure)}% with {', '.join(sources[:3]) or 'low-source'} interruptions."
            ),
        )

    @staticmethod
    def _deep_work(windows: list[ProductivityActivityWindow], tool_switching: ToolSwitchingAnalytics, distractions: DistractionAnalytics) -> DeepWorkAnalytics:
        deep_minutes = [window.deep_work_minutes for window in windows]
        total = sum(deep_minutes) / 60
        interruptions = sum(window.app_switches + window.tab_switches + window.notifications for window in windows) / max(len(windows), 1)
        average_block = mean(deep_minutes) if deep_minutes else 0
        stability = float(np.clip(average_block * 2.35 - tool_switching.context_switch_penalty * 0.28 - distractions.distraction_score * 0.18, 0, 100))
        causes = []
        if tool_switching.context_switch_penalty >= 45:
            causes.append("excessive app and tab switching")
        if distractions.notification_pressure >= 45:
            causes.append("notification overload")
        if any(window.meeting_minutes >= 15 for window in windows):
            causes.append("meeting interruptions")
        if distractions.distraction_minutes >= 40:
            causes.append("distraction-heavy browser/app usage")
        return DeepWorkAnalytics(
            total_deep_work_hours=round(total, 2),
            average_deep_work_block_minutes=round(average_block, 2),
            interruption_frequency=round(interruptions, 2),
            stability_score=round(stability, 2),
            disruption_causes=causes or ["normal workflow variance"],
            insight=f"Deep-work stability is {round(stability)}%; interruption frequency averaged {round(interruptions)} signals per work window.",
        )

    @staticmethod
    def _energy_forecast(hourly: list[HourlyProductivityPoint], work_pattern: EmployeeActivityPoint, sentiment: float) -> list[EnergyForecastPoint]:
        recent_energy = [point.energy_score for point in hourly[-4:]] or [68]
        start = mean(recent_energy)
        fatigue_drift = work_pattern.overtime_hours * 0.38 + work_pattern.meeting_hours * 0.24 + max(0, -sentiment) * 7
        points: list[EnergyForecastPoint] = []
        for index, label in enumerate(["Next hour", "Late afternoon", "Tomorrow AM", "Tomorrow PM", "This week", "Friday close"]):
            energy = float(np.clip(start - fatigue_drift * (0.22 + index * 0.08) + (6 if index == 2 else 0), 0, 100))
            productivity = float(np.clip(energy * 0.78 + (hourly[-1].productivity_score if hourly else 65) * 0.22, 0, 100))
            fatigue = float(np.clip(100 - energy + fatigue_drift * 0.35, 0, 100))
            points.append(
                EnergyForecastPoint(
                    window=label,
                    energy_score=round(energy, 2),
                    productivity_score=round(productivity, 2),
                    fatigue_risk=round(fatigue, 2),
                )
            )
        return points

    @staticmethod
    def _summary(
        hourly: list[HourlyProductivityPoint],
        tool_switching: ToolSwitchingAnalytics,
        distractions: DistractionAnalytics,
        deep_work: DeepWorkAnalytics,
        hourly_cost: float,
        employee_productivity: float,
    ) -> ProductivitySummary:
        productivity = mean([point.productivity_score for point in hourly]) if hourly else 0
        focus = mean([point.focus_score for point in hourly]) if hourly else 0
        efficiency = mean([point.efficiency_score for point in hourly]) if hourly else 0
        lost_hours = max(distractions.estimated_lost_hours, sum(point.leakage_minutes for point in hourly) / 60)
        leakage_percent = float(np.clip((100 - productivity) * 0.42 + tool_switching.productivity_loss_percent * 0.24 + distractions.distraction_score * 0.2 + (100 - deep_work.stability_score) * 0.14, 0, 100))
        blended_productivity = float(np.clip(productivity * 0.72 + employee_productivity * 0.28, 0, 100))
        return ProductivitySummary(
            productivity_score=round(blended_productivity, 2),
            focus_score=round(focus, 2),
            efficiency_score=round(efficiency, 2),
            leakage_percent=round(leakage_percent, 2),
            lost_productive_hours=round(lost_hours, 2),
            estimated_loss_cost=round(lost_hours * hourly_cost, 2),
            tool_switching_overload=round(tool_switching.context_switch_penalty, 2),
            distraction_score=round(distractions.distraction_score, 2),
            deep_work_stability=round(deep_work.stability_score, 2),
            low_focus_window_count=sum(1 for point in hourly if point.focus_score < 50),
        )

    @staticmethod
    def _heatmap(hourly: list[HourlyProductivityPoint]) -> list[ProductivityHeatmapCell]:
        return [
            ProductivityHeatmapCell(
                window=point.hour_label,
                leakage_score=round(float(np.clip(100 - point.productivity_score + point.leakage_minutes * 0.7, 0, 100)), 2),
                focus_score=point.focus_score,
                productive_minutes=round(max(0, 60 - point.leakage_minutes), 2),
                lost_minutes=point.leakage_minutes,
                dominant_cause=point.dominant_cause,
            )
            for point in hourly
        ]

    @staticmethod
    def _recommendations(
        summary: ProductivitySummary,
        tool_switching: ToolSwitchingAnalytics,
        distractions: DistractionAnalytics,
        deep_work: DeepWorkAnalytics,
        energy: list[EnergyForecastPoint],
    ) -> list[ProductivityRecommendation]:
        recommendations: list[ProductivityRecommendation] = []
        if tool_switching.context_switch_penalty >= 38:
            recommendations.append(
                ProductivityRecommendation(
                    category="tool_switching",
                    priority="high" if tool_switching.context_switch_penalty >= 62 else "medium",
                    action="Batch Slack, Email, and Jira into two review windows and keep engineering tools pinned during focus blocks.",
                    expected_impact=f"Expected to recover {round(tool_switching.productivity_loss_percent * 0.38, 1)}% focus efficiency.",
                    confidence=0.89,
                )
            )
        if deep_work.stability_score <= 58:
            recommendations.append(
                ProductivityRecommendation(
                    category="deep_work",
                    priority="high" if deep_work.stability_score <= 36 else "medium",
                    action="Block 9AM-11AM as uninterrupted deep-work time and suppress notifications during that window.",
                    expected_impact="Increases deep-work continuity and reduces restart cost after interruptions.",
                    confidence=0.87,
                )
            )
        if distractions.distraction_score >= 42:
            recommendations.append(
                ProductivityRecommendation(
                    category="distraction_reduction",
                    priority="medium",
                    action="Disable non-critical notifications and close distraction-heavy browser groups before sprint execution work.",
                    expected_impact=f"Expected to recover about {round(distractions.estimated_lost_hours * 0.42, 1)} productive hours daily.",
                    confidence=0.84,
                )
            )
        low_energy = min(energy, key=lambda point: point.energy_score) if energy else None
        if low_energy and low_energy.energy_score <= 54:
            recommendations.append(
                ProductivityRecommendation(
                    category="energy_scheduling",
                    priority="medium",
                    action=f"Move complex work away from {low_energy.window} and schedule review/admin tasks there instead.",
                    expected_impact="Aligns cognitive demand with predicted energy level.",
                    confidence=0.81,
                )
            )
        if summary.low_focus_window_count:
            recommendations.append(
                ProductivityRecommendation(
                    category="low_focus_windows",
                    priority="medium",
                    action="Protect low-focus hours with shorter task batches and defer cross-functional interruptions.",
                    expected_impact=f"Targets {summary.low_focus_window_count} low-focus windows detected in today’s telemetry.",
                    confidence=0.8,
                )
            )
        if not recommendations:
            recommendations.append(
                ProductivityRecommendation(
                    category="maintain",
                    priority="low",
                    action="Maintain current focus cadence and continue passive productivity telemetry monitoring.",
                    expected_impact="Keeps productivity baseline stable.",
                    confidence=0.76,
                )
            )
        return recommendations[:6]

    @staticmethod
    def _alerts(summary: ProductivitySummary, tool_switching: ToolSwitchingAnalytics, distractions: DistractionAnalytics, deep_work: DeepWorkAnalytics) -> list[ProductivityRiskAlert]:
        alerts = [
            ProductivityLeakageService._alert("productivity_leakage", summary.leakage_percent, [f"lost_hours={summary.lost_productive_hours}", f"loss_cost={summary.estimated_loss_cost}"], "Create protected focus blocks and remove low-signal interruptions."),
            ProductivityLeakageService._alert("tool_switching_overload", tool_switching.context_switch_penalty, [tool_switching.insight, f"switches_per_hour={tool_switching.app_switches_per_hour}"], "Batch communication tools and reduce tab churn."),
            ProductivityLeakageService._alert("distraction_pressure", distractions.distraction_score, [distractions.insight], "Suppress non-critical notifications and close distraction sources."),
            ProductivityLeakageService._alert("deep_work_disruption", 100 - deep_work.stability_score, deep_work.disruption_causes, "Protect long uninterrupted execution windows."),
        ]
        return [alert for alert in alerts if alert.score >= 32]

    @staticmethod
    def _alert(category: str, score: float, evidence: list[str], recommendation: str) -> ProductivityRiskAlert:
        if score >= 78:
            severity = "critical"
        elif score >= 60:
            severity = "high"
        elif score >= 42:
            severity = "medium"
        else:
            severity = "low"
        return ProductivityRiskAlert(
            category=category,
            severity=severity,
            score=round(float(np.clip(score, 0, 100)), 2),
            message=f"{category.replace('_', ' ').title()} signal is {round(score)}%.",
            evidence=evidence[:5],
            recommendation=recommendation,
        )

    @staticmethod
    def _executive_insights(
        request: ProductivityAnalyzeRequest,
        summary: ProductivitySummary,
        tool_switching: ToolSwitchingAnalytics,
        distractions: DistractionAnalytics,
        deep_work: DeepWorkAnalytics,
        hourly: list[HourlyProductivityPoint],
    ) -> list[str]:
        low_focus = [point.hour_label for point in hourly if point.focus_score < 50]
        peak = max(hourly, key=lambda point: point.focus_score) if hourly else None
        trough = min(hourly, key=lambda point: point.focus_score) if hourly else None
        insights = [
            f"{request.employee_name} lost approximately {summary.lost_productive_hours} productive hours from leakage signals today.",
            tool_switching.insight,
            distractions.insight,
            deep_work.insight,
        ]
        if peak:
            insights.append(f"Highest productivity window detected around {peak.hour_label}; schedule complex work there.")
        if trough:
            insights.append(f"Low-focus hours detected around {trough.hour_label}; dominant cause is {trough.dominant_cause}.")
        if low_focus:
            insights.append(f"Low-focus windows: {', '.join(low_focus[:4])}.")
        return insights[:7]

    @staticmethod
    def _scenario_variant(base: ProductivityAnalyzeRequest, switch_delta: int, distraction_delta: float, notification_delta: int) -> ProductivityAnalyzeRequest:
        source = base.windows or ProductivityLeakageService.default_request().windows
        windows = [
            window.model_copy(
                update={
                    "app_switches": min(600, window.app_switches + switch_delta),
                    "tab_switches": min(900, window.tab_switches + switch_delta * 2),
                    "notifications": min(500, window.notifications + notification_delta),
                    "distraction_minutes": min(60, window.distraction_minutes + distraction_delta),
                    "deep_work_minutes": max(0, window.deep_work_minutes - distraction_delta * 1.8),
                    "focus_quality": max(0, window.focus_quality - switch_delta * 0.006),
                    "task_completion_ratio": max(0, window.task_completion_ratio - switch_delta * 0.004),
                }
            )
            for window in source
        ]
        apps = [
            app.model_copy(update={"switches": min(600, app.switches + switch_delta), "notification_count": min(500, app.notification_count + notification_delta)})
            for app in (base.app_usage or ProductivityLeakageService.default_request().app_usage)
        ]
        return base.model_copy(update={"windows": windows, "app_usage": apps, "realtime": True})

    def _append_jsonl(self, payload: dict[str, object]) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with self._lock:
            with HISTORY_PATH.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, default=str) + "\n")


productivity_leakage_service = ProductivityLeakageService()
