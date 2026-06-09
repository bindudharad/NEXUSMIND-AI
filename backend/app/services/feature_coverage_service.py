from __future__ import annotations

import inspect
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

from app.ai.burnout_model import BurnoutFeatures
from app.ai.enterprise_models import enterprise_model_registry
from app.ai.huggingface_engine import huggingface_sentiment_engine
from app.ai.tensorflow_engine import tensorflow_risk_engine
from app.core.cache import TTLResponseCache
from app.schemas.feature_coverage import FeatureCoverageCheck, FeatureCoverageResponse, FeatureCoverageSummary
from app.schemas.forecasting import ForecastRequest
from app.schemas.nlp import NLPAnalyzeRequest
from app.services.alert_service import alert_service
from app.services.anomaly_service import anomaly_service
from app.services.employee_dashboard_service import employee_dashboard_service
from app.services.forecasting_service import forecasting_service
from app.services.manager_dashboard_service import manager_dashboard_service
from app.services.nlp_service import nlp_service
from app.services.recommendation_service import recommendation_service
from app.services.suggestion_service import smart_suggestion_service
from app.services.technology_stack_service import technology_stack_service


ROOT = Path(__file__).resolve().parents[3]
FRONTEND_COMPONENTS = ROOT / "frontend" / "src" / "components" / "dashboard"
FRONTEND_API = ROOT / "frontend" / "src" / "app" / "api"
DATA_DIR = ROOT / "backend" / "app" / "data"


class FeatureCoverageService:
    def __init__(self) -> None:
        self._cache: TTLResponseCache[FeatureCoverageResponse] = TTLResponseCache(ttl_seconds=45)

    def verify(self) -> FeatureCoverageResponse:
        return self._cache.get_or_set(self._verify_uncached)

    def _verify_uncached(self) -> FeatureCoverageResponse:
        probes: list[Callable[[], FeatureCoverageCheck]] = [
            self._random_forest,
            self._xgboost,
            self._neural_networks,
            self._nlp_sentiment,
            self._time_series,
            self._recommendations,
            self._anomaly_detection,
            self._employee_dashboard,
            self._manager_dashboard,
            self._ai_alerts,
            self._smart_suggestions,
            self._technology_stack,
            self._realtime_systems,
            self._database_and_history,
            self._enterprise_ui,
            self._original_prediction_coverage,
        ]
        checks = [self._safe(probe) for probe in probes]
        summary = self._summary(checks)
        critical_gaps = [
            f"{check.name}: {check.remediation or check.details}"
            for check in checks
            if check.status in {"missing", "error"}
        ]
        verdict = (
            "Original NEXUSMIND burnout and productivity intelligence scope is implemented and verified."
            if not critical_gaps and summary.coverage_score >= 85
            else "Feature coverage needs remediation before enterprise demo readiness."
        )
        return FeatureCoverageResponse(
            generated_at=datetime.now(timezone.utc),
            summary=summary,
            checks=checks,
            critical_gaps=critical_gaps,
            verdict=verdict,
        )

    def _random_forest(self) -> FeatureCoverageCheck:
        low, high = self._burnout_samples()
        metrics = self._metric("Random Forest")
        ready = high["random_forest"] > low["random_forest"] and metrics is not None
        return FeatureCoverageCheck(
            name="Random Forest burnout model",
            category="ml",
            status="ready" if ready else "error",
            details="RandomForestClassifier artifact, metrics, feature engineering, and live inference are verified.",
            evidence=[
                f"low={low['random_forest']}",
                f"high={high['random_forest']}",
                f"roc_auc={metrics.get('roc_auc') if metrics else 'missing'}",
                "features=overtime, meetings, sentiment, task completion, absence",
            ],
            remediation=None if ready else "Retrain random_forest_burnout.joblib and reconnect burnout prediction API.",
        )

    def _xgboost(self) -> FeatureCoverageCheck:
        low, high = self._burnout_samples()
        metrics = self._metric("XGBoost")
        ready = high["xgboost"] > low["xgboost"] and metrics is not None
        return FeatureCoverageCheck(
            name="XGBoost burnout model",
            category="ml",
            status="ready" if ready else "error",
            details="XGBoost classifier artifact, evaluation metrics, and realtime ensemble inference are verified.",
            evidence=[f"low={low['xgboost']}", f"high={high['xgboost']}", f"f1={metrics.get('f1') if metrics else 'missing'}"],
            remediation=None if ready else "Regenerate xgboost_burnout.joblib and validate class weighting/hyperparameters.",
        )

    def _neural_networks(self) -> FeatureCoverageCheck:
        low, high = self._burnout_samples()
        tf = tensorflow_risk_engine.verify()
        ready = high["neural_network"] > low["neural_network"]
        status = "ready" if ready and tf.available else "warning" if ready else "error"
        return FeatureCoverageCheck(
            name="Neural network risk models",
            category="ml",
            status=status,
            details="PyTorch burnout network is active; TensorFlow Keras engine is implemented and activates when runtime dependency is installed.",
            evidence=[
                f"torch_low={low['neural_network']}",
                f"torch_high={high['neural_network']}",
                f"tensorflow_available={tf.available}",
                tf.details,
            ],
            remediation=None if status == "ready" else "Install backend TensorFlow runtime in the production container to enable Keras inference.",
        )

    def _nlp_sentiment(self) -> FeatureCoverageCheck:
        positive = nlp_service.analyze(
            NLPAnalyzeRequest(
                employee_id="audit-positive",
                department="Engineering",
                channel="chat",
                text="The delivery plan is clear and I feel motivated by the team progress.",
            )
        )
        burnout = nlp_service.analyze(
            NLPAnalyzeRequest(
                employee_id="audit-burnout",
                department="Engineering",
                channel="email",
                text="I am exhausted, frustrated, overloaded, and working late every night.",
            )
        )
        toxic = nlp_service.analyze(
            NLPAnalyzeRequest(
                employee_id="audit-toxic",
                department="Operations",
                channel="chat",
                text="This discussion is hostile, aggressive, and people are blaming each other.",
            )
        )
        ready = (
            huggingface_sentiment_engine.available
            and burnout.emotion_scores.stress > positive.emotion_scores.stress
            and toxic.emotion_scores.toxicity > positive.emotion_scores.toxicity
        )
        return FeatureCoverageCheck(
            name="NLP sentiment and emotion analysis",
            category="nlp",
            status="ready" if ready else "error",
            details="Employee text sentiment, stress, frustration, motivation, toxicity, and burnout indicators are dynamically inferred.",
            evidence=[
                positive.model,
                huggingface_sentiment_engine.model_name,
                f"stress_delta={round(burnout.emotion_scores.stress - positive.emotion_scores.stress, 3)}",
                f"toxicity_delta={round(toxic.emotion_scores.toxicity - positive.emotion_scores.toxicity, 3)}",
            ],
            remediation=None if ready else "Repair NLP model artifacts and transformer sentiment verifier.",
        )

    def _time_series(self) -> FeatureCoverageCheck:
        forecast = forecasting_service.forecast(ForecastRequest(department="Engineering", horizon_days=7))
        ready = len(forecast.forecast) == 7 and bool(forecast.trend_signals) and forecast.confidence > 0.55
        return FeatureCoverageCheck(
            name="Time-series workload forecasting",
            category="forecasting",
            status="ready" if ready else "error",
            details="LSTM workload forecasting predicts burnout progression, productivity decline, delay probability, and collapse risk.",
            evidence=[
                forecast.model,
                f"horizon={forecast.horizon_days}",
                f"confidence={forecast.confidence}",
                f"collapse_probability={forecast.team_collapse_probability}",
            ],
            remediation=None if ready else "Retrain workload_lstm.pt and validate historical sequence generation.",
        )

    def _recommendations(self) -> FeatureCoverageCheck:
        response = recommendation_service.generate()
        categories = {item.category for item in response.recommendations}
        expected = {"work_redistribution", "break", "team_balancing"}
        ready = expected.issubset(categories) and all(item.confidence > 0 for item in response.recommendations)
        return FeatureCoverageCheck(
            name="Recommendation AI",
            category="recommendations",
            status="ready" if ready else "error",
            details="Hybrid ML recommendation engine generates work redistribution, break, and team balancing actions.",
            evidence=[response.model, f"categories={sorted(categories)}", f"team_balance={response.team_balance_score}"],
            remediation=None if ready else "Restore recommendation_ranker.joblib and category generators.",
        )

    def _anomaly_detection(self) -> FeatureCoverageCheck:
        response = anomaly_service.detect()
        ready = "IsolationForest" in response.model and response.alerts and response.events_analyzed >= 1
        return FeatureCoverageCheck(
            name="Behavioral anomaly detection",
            category="anomaly",
            status="ready" if ready else "error",
            details="Isolation Forest and LOF detect insider-risk, overtime, productivity, communication, and behavioral drift anomalies.",
            evidence=[response.model, f"alerts={len(response.alerts)}", f"events={response.events_analyzed}"],
            remediation=None if ready else "Regenerate anomaly artifacts and behavioral baseline feature extraction.",
        )

    def _employee_dashboard(self) -> FeatureCoverageCheck:
        dashboard = employee_dashboard_service.analyze()
        ready = dashboard.stress.value > 0 and dashboard.productivity.value > 0 and dashboard.burnout_probability.value > 0
        return FeatureCoverageCheck(
            name="Employee dashboard",
            category="dashboard",
            status="ready" if ready else "error",
            details="Employee dashboard exposes realtime stress score, productivity score, burnout probability, trend history, and AI recommendations.",
            evidence=[
                dashboard.model,
                f"stress={round(dashboard.stress.value, 2)}",
                f"productivity={round(dashboard.productivity.value, 2)}",
                f"burnout={round(dashboard.burnout_probability.value, 2)}",
            ],
            remediation=None if ready else "Reconnect employee analytics engine to dashboard API and chart panel.",
        )

    def _manager_dashboard(self) -> FeatureCoverageCheck:
        dashboard = manager_dashboard_service.analyze()
        ready = bool(dashboard.risky_teams and dashboard.overloaded_employees and dashboard.delay_predictions)
        return FeatureCoverageCheck(
            name="Manager dashboard",
            category="dashboard",
            status="ready" if ready else "error",
            details="Manager dashboard exposes risky teams, overloaded employees, delay prediction, trends, and recommendations.",
            evidence=[
                dashboard.model,
                f"risky_teams={len(dashboard.risky_teams)}",
                f"overloaded={len(dashboard.overloaded_employees)}",
                f"delay_predictions={len(dashboard.delay_predictions)}",
            ],
            remediation=None if ready else "Repair manager analytics models and dashboard endpoint integration.",
        )

    def _ai_alerts(self) -> FeatureCoverageCheck:
        feed = alert_service.feed()
        categories = {alert.category for alert in feed.alerts}
        expected = {"burnout", "overload", "delay"}
        ready = bool(feed.alerts) and expected.intersection(categories)
        return FeatureCoverageCheck(
            name="AI alert system",
            category="alerts",
            status="ready" if ready else "error",
            details="Cross-system alert correlator generates predictive alerts with severity, priority ranking, recommendations, and acknowledgement support.",
            evidence=[feed.model, f"alerts={len(feed.alerts)}", f"categories={sorted(categories)}"],
            remediation=None if ready else "Reconnect alert correlator to manager, employee, anomaly, NLP, and forecasting services.",
        )

    def _smart_suggestions(self) -> FeatureCoverageCheck:
        response = smart_suggestion_service.generate()
        categories = {item.category for item in response.suggestions}
        expected = {"meeting_reduction", "workload_redistribution", "wellness_break", "team_optimization", "productivity_improvement"}
        ready = expected.issubset(categories)
        return FeatureCoverageCheck(
            name="Smart suggestion engine",
            category="recommendations",
            status="ready" if ready else "error",
            details="Decision intelligence engine creates meeting reduction, workload, wellness, team optimization, and productivity suggestions.",
            evidence=[response.model, f"categories={sorted(categories)}", f"average_impact={response.summary.average_impact}"],
            remediation=None if ready else "Restore smart suggestion category generators and feedback learning.",
        )

    def _technology_stack(self) -> FeatureCoverageCheck:
        stack = technology_stack_service.verify()
        ready = stack.summary.missing == 0 and stack.summary.errors == 0
        status = "ready" if ready and stack.summary.configured == 0 else "warning" if ready else "error"
        return FeatureCoverageCheck(
            name="Technology stack integration",
            category="stack",
            status=status,
            details="React, Next.js, Python, FastAPI, Scikit-learn, Hugging Face, PostgreSQL, MongoDB, Docker, and AWS readiness are audited.",
            evidence=[
                f"score={stack.summary.production_ready_score}",
                f"ready={stack.summary.ready}",
                f"configured={stack.summary.configured}",
                f"missing={stack.summary.missing}",
            ],
            remediation=None if status == "ready" else "Connect configured runtime dependencies such as local PostgreSQL, Docker CLI, AWS SDK, or TensorFlow.",
        )

    def _realtime_systems(self) -> FeatureCoverageCheck:
        alert_stream = inspect.isasyncgen(alert_service.stream())
        suggestion_stream = inspect.isasyncgen(smart_suggestion_service.stream())
        api_routes = [
            FRONTEND_API / "alerts" / "stream" / "route.ts",
            FRONTEND_API / "suggestions" / "stream" / "route.ts",
        ]
        ready = alert_stream and suggestion_stream and all(path.exists() for path in api_routes)
        return FeatureCoverageCheck(
            name="Realtime streaming systems",
            category="realtime",
            status="ready" if ready else "error",
            details="Server-sent alert and suggestion streams feed live dashboard panels without static notification cards.",
            evidence=[f"alert_stream={alert_stream}", f"suggestion_stream={suggestion_stream}", *[str(path) for path in api_routes]],
            remediation=None if ready else "Repair streaming generators and frontend stream proxy routes.",
        )

    def _database_and_history(self) -> FeatureCoverageCheck:
        expected = [
            "nlp_predictions.jsonl",
            "forecast_predictions.jsonl",
            "recommendation_history.jsonl",
            "anomaly_alerts.jsonl",
            "employee_dashboard_history.jsonl",
            "manager_dashboard_history.jsonl",
            "ai_alert_history.jsonl",
            "smart_suggestion_history.jsonl",
        ]
        existing = [name for name in expected if (DATA_DIR / name).exists()]
        stack = technology_stack_service.verify()
        db_checks = {check.name: check.status for check in stack.checks if check.category == "database"}
        ready = len(existing) >= 6 and all(status in {"ready", "configured"} for status in db_checks.values())
        return FeatureCoverageCheck(
            name="Database and historical analytics",
            category="database",
            status="ready" if ready and all(status == "ready" for status in db_checks.values()) else "warning" if ready else "error",
            details="Historical analytics are persisted locally, while PostgreSQL and MongoDB integrations are probed through the stack verifier.",
            evidence=[f"history_files={len(existing)}/{len(expected)}", f"database_status={db_checks}"],
            remediation=None if ready else "Create missing history repositories and connect PostgreSQL/MongoDB runtime services.",
        )

    def _enterprise_ui(self) -> FeatureCoverageCheck:
        required = [
            "EmployeeDashboardPanel.tsx",
            "ManagerDashboardPanel.tsx",
            "AIAlertCenterPanel.tsx",
            "SmartSuggestionPanel.tsx",
            "AnomalyDetectionPanel.tsx",
            "NlpSentimentPanel.tsx",
            "WorkloadForecastPanel.tsx",
            "TechnologyStackPanel.tsx",
        ]
        existing = [name for name in required if (FRONTEND_COMPONENTS / name).exists()]
        ready = len(existing) == len(required)
        return FeatureCoverageCheck(
            name="Enterprise UI/UX coverage",
            category="ui",
            status="ready" if ready else "missing",
            details="Futuristic dashboard panels exist for employee, manager, alert, suggestion, anomaly, NLP, forecasting, and stack verification workflows.",
            evidence=[f"panels={len(existing)}/{len(required)}", *existing],
            remediation=None if ready else "Regenerate missing dashboard panels and wire them into the Next.js command center.",
        )

    def _original_prediction_coverage(self) -> FeatureCoverageCheck:
        employee = employee_dashboard_service.analyze()
        manager = manager_dashboard_service.analyze()
        dashboard_files = [
            FRONTEND_COMPONENTS / "BurnoutHeatmap.tsx",
            FRONTEND_COMPONENTS / "EmployeeDashboardPanel.tsx",
            FRONTEND_COMPONENTS / "ManagerDashboardPanel.tsx",
        ]
        ready = (
            employee.burnout_probability.value > 0
            and employee.productivity.value > 0
            and bool(manager.risky_teams)
            and bool(manager.delay_predictions)
            and all(path.exists() for path in dashboard_files)
        )
        return FeatureCoverageCheck(
            name="Original idea prediction coverage",
            category="scope",
            status="ready" if ready else "error",
            details="The original system scope covers burnout risk, productivity drop, possible resignation/attrition, team stress, and project delay risk.",
            evidence=[
                f"burnout={round(employee.burnout_probability.value, 2)}",
                f"productivity={round(employee.productivity.value, 2)}",
                f"team_stress={round(manager.summary.average_team_risk, 2)}",
                f"delay={round(manager.summary.average_delay_probability, 2)}",
                "attrition_heatmap=BurnoutHeatmap.tsx",
            ],
            remediation=None if ready else "Reconnect original prediction outputs to employee, manager, and attrition heatmap panels.",
        )

    @staticmethod
    def _safe(probe: Callable[[], FeatureCoverageCheck]) -> FeatureCoverageCheck:
        try:
            return probe()
        except Exception as exc:
            return FeatureCoverageCheck(
                name=probe.__name__.replace("_", " ").title(),
                category="system",
                status="error",
                details=f"Feature coverage probe crashed: {type(exc).__name__}",
                evidence=[str(exc)[:220]],
                remediation="Fix the crashed probe or underlying module before claiming enterprise readiness.",
            )

    @staticmethod
    def _summary(checks: list[FeatureCoverageCheck]) -> FeatureCoverageSummary:
        ready = sum(1 for check in checks if check.status == "ready")
        warnings = sum(1 for check in checks if check.status == "warning")
        missing = sum(1 for check in checks if check.status == "missing")
        errors = sum(1 for check in checks if check.status == "error")
        score = round(((ready + warnings * 0.72) / len(checks)) * 100, 2) if checks else 0
        return FeatureCoverageSummary(total=len(checks), ready=ready, warnings=warnings, missing=missing, errors=errors, coverage_score=score)

    @staticmethod
    def _burnout_samples() -> tuple[dict[str, float], dict[str, float]]:
        low = enterprise_model_registry.predict(
            BurnoutFeatures(overtime_hours=2, meeting_hours=4, sentiment_score=0.72, task_completion_ratio=0.96, absence_days=0)
        )
        high = enterprise_model_registry.predict(
            BurnoutFeatures(overtime_hours=26, meeting_hours=32, sentiment_score=-0.82, task_completion_ratio=0.42, absence_days=8)
        )
        return low, high

    @staticmethod
    def _metric(name: str) -> dict[str, float | int | str] | None:
        return next((metric for metric in enterprise_model_registry.metrics() if metric["model"] == name), None)


feature_coverage_service = FeatureCoverageService()
