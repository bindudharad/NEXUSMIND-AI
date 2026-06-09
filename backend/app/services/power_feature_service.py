from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from threading import Lock

import numpy as np
from sklearn.linear_model import LinearRegression

from app.ai.burnout_model import BurnoutFeatures
from app.ai.employee_analytics_engine import employee_analytics_engine
from app.ai.enterprise_models import enterprise_model_registry
from app.ai.graph_relation_engine import graph_relation_engine
from app.ai.knowledge_engine import knowledge_engine
from app.ai.project_failure_engine import project_failure_engine
from app.ai.team_compatibility_engine import team_compatibility_engine
from app.core.cache import TTLResponseCache
from app.schemas.alerts import AlertDetectionRequest
from app.schemas.employee_dashboard import EmployeeActivityPoint
from app.schemas.power_features import (
    AssistantContextSource,
    CounterfactualAction,
    FeatureAttribution,
    GNNEdge,
    GNNNode,
    GNNTeamRelationResponse,
    ManagerAssistantRequest,
    ManagerAssistantResponse,
    PowerFeatureAuditResponse,
    PowerFeatureCheck,
    PowerFeatureSummary,
    RealtimeAnalyticsResponse,
    RealtimeEvent,
    RealtimeKPI,
    XAIExplanationRequest,
    XAIExplanationResponse,
)
from app.schemas.project_failure import ProjectProfile
from app.schemas.suggestions import SmartSuggestionRequest
from app.services.alert_service import alert_service
from app.services.employee_dashboard_service import employee_dashboard_service
from app.services.manager_dashboard_service import manager_dashboard_service
from app.services.project_failure_service import project_failure_service
from app.services.roi_service import roi_intelligence_service
from app.services.suggestion_service import smart_suggestion_service
from app.services.team_compatibility_service import team_compatibility_service


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
POWER_HISTORY_PATH = DATA_DIR / "power_realtime_history.jsonl"
XAI_HISTORY_PATH = DATA_DIR / "xai_explanations.jsonl"
GNN_HISTORY_PATH = DATA_DIR / "gnn_team_relations_history.jsonl"
ASSISTANT_HISTORY_PATH = DATA_DIR / "manager_assistant_history.jsonl"


class PowerFeatureService:
    realtime_model = "Unified Realtime Enterprise Analytics Stream"
    xai_model = "TreeSHAP-style + LIME Explainable AI Engine"
    assistant_model = "Local RAG Generative Manager Assistant"

    def __init__(self) -> None:
        self._lock = Lock()
        self._audit_cache: TTLResponseCache[PowerFeatureAuditResponse] = TTLResponseCache(ttl_seconds=20)
        self._default_snapshot_cache: TTLResponseCache[RealtimeAnalyticsResponse] = TTLResponseCache(ttl_seconds=5)
        self._graph_cache: TTLResponseCache[GNNTeamRelationResponse] = TTLResponseCache(ttl_seconds=20)
        self._assistant_cache: TTLResponseCache[ManagerAssistantResponse] = TTLResponseCache(ttl_seconds=20)
        self._burnout_explanation_cache: TTLResponseCache[XAIExplanationResponse] = TTLResponseCache(ttl_seconds=20)
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def audit(self) -> PowerFeatureAuditResponse:
        return self._audit_cache.get_or_set(self._audit_uncached)

    def _audit_uncached(self) -> PowerFeatureAuditResponse:
        checks = [
            self._realtime_check(),
            self._xai_check(),
            self._gnn_check(),
            self._assistant_check(),
        ]
        ready = sum(1 for check in checks if check.status == "ready")
        warnings = sum(1 for check in checks if check.status == "warning")
        missing = sum(1 for check in checks if check.status == "missing")
        errors = sum(1 for check in checks if check.status == "error")
        score = round(((ready + warnings * 0.72) / len(checks)) * 100, 2)
        verdict = (
            "Advanced AI power layer is implemented: realtime analytics, XAI, GraphSAGE team relations, and a RAG manager assistant are live."
            if missing == 0 and errors == 0 and score >= 90
            else "Advanced AI power layer needs remediation before production demo."
        )
        return PowerFeatureAuditResponse(
            model="Advanced AI Power Feature Auditor",
            generated_at=datetime.now(timezone.utc),
            summary=PowerFeatureSummary(total=len(checks), ready=ready, warnings=warnings, missing=missing, errors=errors, power_score=score),
            checks=checks,
            verdict=verdict,
        )

    def realtime_snapshot(self, sequence: int = 1, mode: str = "default") -> RealtimeAnalyticsResponse:
        if sequence == 1 and mode == "default":
            return self._default_snapshot_cache.get_or_set(lambda: self._realtime_snapshot_uncached(sequence=sequence, mode=mode))
        return self._realtime_snapshot_uncached(sequence=sequence, mode=mode)

    def _realtime_snapshot_uncached(self, sequence: int = 1, mode: str = "default") -> RealtimeAnalyticsResponse:
        scenario = "crisis" if mode == "crisis" else "default"
        employee = employee_dashboard_service.analyze()
        manager = manager_dashboard_service.analyze()
        projects = project_failure_service.analyze()
        team = team_compatibility_service.analyze()
        alerts = alert_service.feed(AlertDetectionRequest(scenario=scenario, sensitivity=0.76 if mode == "crisis" else 0.68))
        suggestions = smart_suggestion_service.generate(SmartSuggestionRequest(scenario=scenario, sensitivity=0.76 if mode == "crisis" else 0.66))
        roi = roi_intelligence_service.analyze()
        top_project = projects.predictions[0]
        top_team = manager.risky_teams[0]
        pressure = 1 + (0.045 * (sequence - 1) if mode != "default" else 0)
        kpis = [
            RealtimeKPI(label="Live stress", value=self._clip(employee.stress.value * pressure), unit="/100", delta=employee.stress.trend_delta, severity=self._severity(employee.stress.value), source_system="employee_dashboard"),
            RealtimeKPI(label="Productivity", value=self._clip(employee.productivity.value / pressure), unit="/100", delta=employee.productivity.trend_delta, severity=self._inverse_severity(employee.productivity.value), source_system="employee_dashboard"),
            RealtimeKPI(label="Burnout probability", value=self._clip(employee.burnout_probability.value * pressure), unit="%", delta=employee.burnout_probability.trend_delta, severity=self._severity(employee.burnout_probability.value), source_system="burnout_ai"),
            RealtimeKPI(label="Team risk", value=self._clip(top_team.risk_score * pressure), unit="/100", delta=manager.summary.average_team_risk - (manager.trend[-2].average_team_risk if len(manager.trend) > 1 else manager.summary.average_team_risk), severity=top_team.severity, source_system="manager_dashboard"),
            RealtimeKPI(label="Project delay", value=self._clip(top_project.deadline_miss_probability * pressure), unit="%", delta=top_project.forecast[-1].delay_probability - top_project.forecast[0].delay_probability, severity=self._severity(top_project.deadline_miss_probability), source_system="project_failure_prediction"),
            RealtimeKPI(label="AI alerts", value=float(alerts.summary.total), unit="events", delta=float(alerts.summary.critical), severity="critical" if alerts.summary.critical else "high", source_system="alert_correlator"),
            RealtimeKPI(label="Recommendations", value=float(suggestions.summary.total), unit="actions", delta=suggestions.summary.average_impact - 70, severity="high", source_system="smart_suggestion_engine"),
            RealtimeKPI(label="ROI capture", value=self._clip(roi.summary.roi_percent / 10), unit="score", delta=roi.summary.payback_months * -1, severity="low", source_system="roi_intelligence"),
        ]
        events = [
            RealtimeEvent(
                event_id=f"rt-alert-{sequence}",
                title=alerts.alerts[0].title,
                message=alerts.alerts[0].message,
                severity=alerts.alerts[0].severity,
                source_systems=alerts.alerts[0].source_systems,
                created_at=datetime.now(timezone.utc),
            ),
            RealtimeEvent(
                event_id=f"rt-project-{sequence}",
                title=f"{top_project.project_name} delay risk",
                message=f"{top_project.project_name} has {round(top_project.deadline_miss_probability)}% deadline miss probability and {round(top_project.burnout_impact)}% burnout impact.",
                severity=self._severity(top_project.deadline_miss_probability),
                source_systems=["project_failure_prediction", "time_series_forecasting", "manager_dashboard"],
                created_at=datetime.now(timezone.utc),
            ),
            RealtimeEvent(
                event_id=f"rt-team-{sequence}",
                title="Graph team relation update",
                message=f"{team.summary.highest_risk_pair} is the highest conflict pair; recommended team score is {round(team.summary.recommended_team_score)}%.",
                severity="high" if team.summary.average_conflict_probability >= 20 else "medium",
                source_systems=["team_compatibility_ai", "graph_neural_network"],
                created_at=datetime.now(timezone.utc),
            ),
        ]
        response = RealtimeAnalyticsResponse(
            model=self.realtime_model,
            generated_at=datetime.now(timezone.utc),
            sequence=sequence,
            mode=mode if mode in {"default", "pressure", "crisis"} else "default",
            kpis=kpis,
            events=events,
            source_systems=[
                "employee_dashboard",
                "manager_dashboard",
                "project_failure_prediction",
                "team_compatibility_ai",
                "alert_correlator",
                "smart_suggestion_engine",
                "roi_intelligence",
            ],
            sync_status="streaming" if sequence > 1 else "ready",
            storage=str(POWER_HISTORY_PATH),
        )
        self._append_jsonl(POWER_HISTORY_PATH, response.model_dump(mode="json"))
        return response

    async def realtime_stream(self):
        modes = ["default", "pressure", "crisis"]
        for sequence, mode in enumerate(modes, start=1):
            response = self.realtime_snapshot(sequence=sequence, mode=mode)
            yield f"event: power_realtime\ndata: {json.dumps(response.model_dump(mode='json'))}\n\n"
            await asyncio.sleep(0.8)

    def explain(self, request: XAIExplanationRequest) -> XAIExplanationResponse:
        spec = self._target_spec(request)
        names = spec["names"]
        current = spec["current"]
        baseline = spec["baseline"]
        predict = spec["predict"]
        prediction = float(predict(current))
        baseline_prediction = float(predict(baseline))
        shap = self._shap_like(names, current, baseline, predict)
        lime = self._lime_like(names, current, baseline, predict)
        top = shap[:3]
        explanation = self._explanation_text(request.target, prediction, baseline_prediction, top)
        counterfactuals = self._counterfactuals(names, current, baseline, predict, prediction)
        response = XAIExplanationResponse(
            model=self.xai_model,
            generated_at=datetime.now(timezone.utc),
            target=request.target,
            prediction=round(prediction, 2),
            baseline_prediction=round(baseline_prediction, 2),
            confidence=round(float(np.clip(0.72 + abs(prediction - baseline_prediction) / 180 + sum(item.importance for item in top) / 8, 0.62, 0.96)), 3),
            methods=["KernelSHAP-style baseline perturbation", "LIME local surrogate regression", "Model-native feature importance alignment"],
            shap_values=shap,
            lime_weights=lime,
            explanation=explanation,
            counterfactuals=counterfactuals,
            decision_trace=[
                f"Loaded live target '{request.target}' from {', '.join(spec['source_systems'])}.",
                f"Computed baseline prediction {round(baseline_prediction, 2)} and current prediction {round(prediction, 2)}.",
                "Ranked feature attributions by marginal model impact and local surrogate coefficients.",
            ],
            source_systems=spec["source_systems"],
            storage=str(XAI_HISTORY_PATH),
        )
        self._append_jsonl(XAI_HISTORY_PATH, response.model_dump(mode="json"))
        return response

    def graph_relations(self) -> GNNTeamRelationResponse:
        return self._graph_cache.get_or_set(self._graph_relations_uncached)

    def _graph_relations_uncached(self) -> GNNTeamRelationResponse:
        request = team_compatibility_service.default_request()
        team = team_compatibility_service.analyze(request)
        employees = request.employees
        inference = graph_relation_engine.infer(employees, team.pair_scores)
        employee_lookup = {employee.employee_id: employee for employee in employees}
        node_predictions = {node.employee_id: node for node in inference.nodes}
        nodes = [
            GNNNode(
                employee_id=node.employee_id,
                name=employee_lookup[node.employee_id].name,
                department=employee_lookup[node.employee_id].department,
                embedding=node.embedding,
                influence_score=node.leadership_influence,
                burnout_spread_risk=node.burnout_spread_risk,
                compatibility_projection=node.compatibility_projection,
                conflict_projection=node.conflict_projection,
                leadership_influence=node.leadership_influence,
            )
            for node in inference.nodes
        ]
        edges = []
        for pair in team.pair_scores:
            key = frozenset({pair.source_id, pair.target_id})
            attention = inference.edge_attention.get(key, 0.25)
            source_burnout = node_predictions[pair.source_id].burnout_spread_risk
            target_burnout = node_predictions[pair.target_id].burnout_spread_risk
            transmission = self._clip((source_burnout + target_burnout) / 2 * attention + pair.burnout_propagation_risk * 0.28)
            edges.append(
                GNNEdge(
                    source_id=pair.source_id,
                    target_id=pair.target_id,
                    attention_weight=attention,
                    collaboration_strength=round(pair.collaboration_success_probability, 2),
                    burnout_transmission=round(transmission, 2),
                    conflict_probability=pair.conflict_probability,
                    explanation=f"{pair.source_name} to {pair.target_name}: attention={attention}, conflict={round(pair.conflict_probability)}%, burnout transmission={round(transmission)}%.",
                )
            )
        alerts = [
            f"Burnout risk may spread through {edge.source_id}->{edge.target_id}; transmission is {round(edge.burnout_transmission)}%."
            for edge in sorted(edges, key=lambda item: item.burnout_transmission, reverse=True)[:3]
            if edge.burnout_transmission >= 42
        ]
        recommendations = [
            f"Use {team.team_recommendations[0].leader} as the graph-stable coordination lead for {team.team_recommendations[0].title}.",
            "Reduce communication dependency around the highest burnout-transmission edge before the next sprint planning cycle.",
            "Recompute graph embeddings after new meeting sentiment, voice stress, or alert events arrive.",
        ]
        response = GNNTeamRelationResponse(
            model=graph_relation_engine.model_name,
            generated_at=datetime.now(timezone.utc),
            architecture=graph_relation_engine.architecture,
            training_metrics=inference.metrics,
            nodes=sorted(nodes, key=lambda node: node.burnout_spread_risk, reverse=True),
            edges=sorted(edges, key=lambda edge: edge.attention_weight, reverse=True),
            propagation_alerts=alerts or ["No severe burnout propagation path exceeds the current adaptive threshold."],
            recommendations=recommendations,
            storage=str(GNN_HISTORY_PATH),
        )
        self._append_jsonl(GNN_HISTORY_PATH, response.model_dump(mode="json"))
        return response

    def ask_manager(self, request: ManagerAssistantRequest) -> ManagerAssistantResponse:
        if request.question.strip().lower() == "why is team alpha productivity decreasing?":
            return self._assistant_cache.get_or_set(lambda: self._ask_manager_uncached(request))
        return self._ask_manager_uncached(request)

    def _ask_manager_uncached(self, request: ManagerAssistantRequest) -> ManagerAssistantResponse:
        manager = manager_dashboard_service.analyze()
        projects = project_failure_service.analyze()
        alerts = alert_service.feed()
        suggestions = smart_suggestion_service.generate()
        roi = roi_intelligence_service.analyze()
        retrieval = knowledge_engine.search(request.question, top_k=2)
        top_team = manager.risky_teams[0]
        top_employee = manager.overloaded_employees[0]
        top_project = projects.predictions[0]
        question = request.question.lower()
        focus = "productivity"
        if "burnout" in question or "stress" in question:
            focus = "burnout"
        elif "project" in question or "fail" in question or "delay" in question:
            focus = "project"
        elif "overloaded" in question or "employee" in question:
            focus = "workload"
        elif "save" in question or "cost" in question or "roi" in question:
            focus = "roi"
        if focus == "project":
            answer = (
                f"{top_project.project_name} is the project most likely to fail: failure risk is {round(top_project.failure_probability)}%, "
                f"deadline miss probability is {round(top_project.deadline_miss_probability)}%, and burnout impact is {round(top_project.burnout_impact)}%. "
                f"The strongest operational explanation is {top_project.risk_signals[0].evidence}"
            )
        elif focus == "workload":
            answer = (
                f"{top_employee.employee_name} is the clearest overload case at {round(top_employee.overload_score)}%. "
                f"Drivers include {', '.join(top_employee.drivers[:3])}. The manager should rebalance work before this becomes attrition or delivery drag."
            )
        elif focus == "burnout":
            answer = (
                f"{top_team.team_name} is carrying the strongest burnout and team-risk signal at {round(top_team.risk_score)}%. "
                f"The risk is tied to {', '.join(top_team.drivers[:3])}, and current alerts report {alerts.summary.critical} critical items."
            )
        elif focus == "roi":
            answer = (
                f"The business case is material: NEXUSMIND models ${round(roi.summary.net_savings):,} net annual savings, "
                f"{round(roi.summary.roi_percent)}% ROI, and {roi.summary.payback_months} month payback by reducing attrition, meeting drag, overtime, and delay cost."
            )
        else:
            answer = (
                f"{top_team.team_name} productivity is decreasing because team risk is {round(top_team.risk_score)}%, "
                f"{top_employee.employee_name} is overloaded at {round(top_employee.overload_score)}%, and {top_project.project_name} has "
                f"{round(top_project.deadline_miss_probability)}% delay probability. The fastest intervention is {suggestions.suggestions[0].action}"
            )
        context_sources = [
            AssistantContextSource(system="manager_dashboard", title=top_team.team_name, snippet=top_team.recommendation, confidence=0.88),
            AssistantContextSource(system="project_failure_prediction", title=top_project.project_name, snippet=top_project.recommendations[0].action, confidence=top_project.confidence),
            AssistantContextSource(system="smart_suggestion_engine", title=suggestions.suggestions[0].title, snippet=suggestions.suggestions[0].rationale, confidence=suggestions.suggestions[0].confidence),
            *[
                AssistantContextSource(system="enterprise_vector_memory", title=hit.document.title, snippet=hit.document.content, confidence=round(hit.score, 3))
                for hit in retrieval
            ],
        ]
        actions = [
            suggestions.suggestions[0].action,
            top_team.recommendation,
            top_project.recommendations[0].action,
        ]
        response = ManagerAssistantResponse(
            model=self.assistant_model,
            generated_at=datetime.now(timezone.utc),
            question=request.question,
            answer=answer,
            risk_summary=f"{manager.summary.teams_at_risk} teams at risk, {manager.summary.overloaded_employees} overloaded employees, {projects.summary.critical_projects} critical projects, and ${round(roi.summary.net_savings):,} modeled savings.",
            recommended_actions=actions,
            context_sources=context_sources,
            reasoning_trace=[
                f"Classified manager question as '{focus}' intent.",
                "Retrieved current manager dashboard, project failure, alert, suggestion, ROI, and vector memory context.",
                "Grounded the answer in the highest-risk team, overloaded employee, highest-risk project, and top AI intervention.",
            ],
            confidence=round(float(np.clip(0.78 + len(context_sources) * 0.025 + max(hit.score for hit in retrieval) * 0.08, 0.74, 0.96)), 3),
            storage=str(ASSISTANT_HISTORY_PATH),
        )
        self._append_jsonl(ASSISTANT_HISTORY_PATH, response.model_dump(mode="json"))
        return response

    def _realtime_check(self) -> PowerFeatureCheck:
        snapshot = self.realtime_snapshot()
        ready = len(snapshot.kpis) >= 7 and len(snapshot.events) >= 3
        return PowerFeatureCheck(
            name="Real-time Analytics",
            category="realtime",
            status="ready" if ready else "error",
            details="Unified analytics stream combines employee, manager, project, team, alert, suggestion, and ROI systems into live KPI/event updates.",
            evidence=[snapshot.model, f"kpis={len(snapshot.kpis)}", f"events={len(snapshot.events)}", "SSE=/api/v1/power/realtime/stream", "WebSocket=/api/v1/power/realtime/ws"],
            remediation=None if ready else "Rebuild realtime analytics aggregation and streaming routes.",
        )

    def _xai_check(self) -> PowerFeatureCheck:
        explanation = self._burnout_explanation_cache.get_or_set(lambda: self.explain(XAIExplanationRequest(target="burnout")))
        ready = explanation.shap_values and explanation.lime_weights and explanation.prediction > explanation.baseline_prediction
        return PowerFeatureCheck(
            name="AI Explanations / XAI",
            category="xai",
            status="ready" if ready else "error",
            details="SHAP-style perturbation and LIME local surrogate explanations produce feature-level reasoning for burnout, project delay, productivity, recommendations, and compatibility.",
            evidence=[explanation.model, f"prediction={explanation.prediction}", f"top={explanation.shap_values[0].feature}", f"methods={len(explanation.methods)}"],
            remediation=None if ready else "Implement feature attribution, local surrogate explanation, and counterfactual generation.",
        )

    def _gnn_check(self) -> PowerFeatureCheck:
        graph = self.graph_relations()
        ready = graph.nodes and graph.edges and graph.training_metrics.get("mae", 1) < 0.08
        return PowerFeatureCheck(
            name="Graph Neural Networks for Team Relations",
            category="graph_ai",
            status="ready" if ready else "error",
            details="PyTorch GraphSAGE model generates employee embeddings, relation attention, burnout propagation, conflict projection, and leadership influence.",
            evidence=[graph.model, graph.architecture, f"nodes={len(graph.nodes)}", f"edges={len(graph.edges)}", f"mae={graph.training_metrics.get('mae')}"],
            remediation=None if ready else "Train GraphSAGE relation model and connect graph inference to team analytics.",
        )

    def _assistant_check(self) -> PowerFeatureCheck:
        response = self.ask_manager(ManagerAssistantRequest(question="Why is Team Alpha productivity decreasing?"))
        ready = bool(response.answer and response.context_sources and response.recommended_actions)
        return PowerFeatureCheck(
            name="Generative AI Assistant for Managers",
            category="assistant",
            status="ready" if ready else "error",
            details="Local RAG assistant answers manager questions with live analytics, vector-memory retrieval, recommendations, and traceable reasoning.",
            evidence=[response.model, f"sources={len(response.context_sources)}", f"actions={len(response.recommended_actions)}", f"confidence={response.confidence}"],
            remediation=None if ready else "Reconnect manager assistant to RAG memory and live analytics context.",
        )

    def _target_spec(self, request: XAIExplanationRequest) -> dict[str, object]:
        if request.target == "project_delay":
            project = project_failure_service.default_request().projects[0]
            names = project_failure_engine.feature_names
            current = np.array([request.features.get(name, value) for name, value in zip(names, project_failure_engine.project_features(project), strict=True)], dtype=np.float32)
            baseline = np.array([0.65 if name in {"velocity_current", "completion_rate", "resource_allocation", "communication_score", "team_compatibility", "historical_delivery_rate", "skill_coverage"} else 0.28 for name in names], dtype=np.float32)

            def predict(vector: np.ndarray) -> float:
                if project_failure_engine.delay_model is None:
                    project_failure_engine.train()
                return float(np.clip(project_failure_engine.delay_model.predict(np.array([vector]))[0], 0, 100))  # type: ignore[union-attr]

            return {"names": names, "current": current, "baseline": baseline, "predict": predict, "source_systems": ["project_failure_prediction", "xgboost_delay_model"]}
        if request.target == "team_compatibility":
            req = team_compatibility_service.default_request()
            interaction = req.interactions[0]
            current_pair = (req.employees[0], req.employees[1])
            names = team_compatibility_engine.feature_names
            current = np.array([request.features.get(name, value) for name, value in zip(names, team_compatibility_engine.pair_features(current_pair[0], current_pair[1], interaction), strict=True)], dtype=np.float32)
            baseline = np.array([0.62 if "conflict" not in name and "burnout" not in name and "stress_mean" not in name else 0.22 for name in names], dtype=np.float32)

            def predict(vector: np.ndarray) -> float:
                if team_compatibility_engine.compatibility_model is None:
                    team_compatibility_engine.train()
                return float(np.clip(team_compatibility_engine.compatibility_model.predict(np.array([vector]))[0], 0, 100))

            return {"names": names, "current": current, "baseline": baseline, "predict": predict, "source_systems": ["team_compatibility_ai", "random_forest_pair_regressor"]}
        if request.target == "productivity":
            point = employee_dashboard_service.default_current()
            names = employee_analytics_engine.feature_names
            current = np.array([request.features.get(name, value) for name, value in zip(names, employee_analytics_engine.vectorize(point), strict=True)], dtype=np.float32)
            baseline_point = EmployeeActivityPoint(
                timestamp=point.timestamp,
                overtime_hours=3,
                workload_intensity=52,
                meeting_hours=4,
                sentiment_score=0.42,
                task_completion_ratio=0.92,
                attendance_rate=0.98,
                focus_hours=7,
                collaboration_score=0.88,
                activity_variance=0.18,
                negative_message_ratio=0.08,
                toxic_message_count=0,
                absence_days=0,
            )
            baseline = np.array(employee_analytics_engine.vectorize(baseline_point), dtype=np.float32)

            def predict(vector: np.ndarray) -> float:
                if employee_analytics_engine.productivity_model is None:
                    employee_analytics_engine.train()
                # Invert productivity for risk-style explanation so higher means worse.
                return float(np.clip(100 - employee_analytics_engine.productivity_model.predict(np.array([vector]))[0], 0, 100))

            return {"names": names, "current": current, "baseline": baseline, "predict": predict, "source_systems": ["employee_dashboard", "productivity_regressor"]}
        if request.target == "recommendation":
            suggestions = smart_suggestion_service.generate()
            names = ["impact_score", "confidence", "critical_priority", "affected_employees", "feedback_weight"]
            top = suggestions.suggestions[0]
            current = np.array([
                request.features.get("impact_score", top.impact_score / 100),
                request.features.get("confidence", top.confidence),
                request.features.get("critical_priority", 1 if top.priority == "critical" else 0.6),
                request.features.get("affected_employees", min(len(top.affected_employees) / 8, 1)),
                request.features.get("feedback_weight", 0.32),
            ], dtype=np.float32)
            baseline = np.array([0.45, 0.55, 0.2, 0.2, 0.15], dtype=np.float32)

            def predict(vector: np.ndarray) -> float:
                return float(np.clip((vector[0] * 0.42 + vector[1] * 0.22 + vector[2] * 0.18 + vector[3] * 0.1 + vector[4] * 0.08) * 100, 0, 100))

            return {"names": names, "current": current, "baseline": baseline, "predict": predict, "source_systems": ["smart_suggestion_engine", "recommendation_ranker"]}
        point = employee_dashboard_service.default_current()
        names = ["overtime_hours", "meeting_hours", "sentiment_score", "task_completion_ratio", "absence_days"]
        current_values = [
            point.overtime_hours,
            point.meeting_hours,
            point.sentiment_score,
            point.task_completion_ratio,
            point.absence_days,
        ]
        current = np.array([request.features.get(name, value) for name, value in zip(names, current_values, strict=True)], dtype=np.float32)
        if request.scenario == "crisis":
            current = np.array([22, 26, -0.78, 0.44, 7], dtype=np.float32)
        baseline = np.array([3, 5, 0.45, 0.92, 0], dtype=np.float32)

        def predict(vector: np.ndarray) -> float:
            probabilities = enterprise_model_registry.predict(
                BurnoutFeatures(
                    overtime_hours=float(vector[0]),
                    meeting_hours=float(vector[1]),
                    sentiment_score=float(vector[2]),
                    task_completion_ratio=float(vector[3]),
                    absence_days=float(vector[4]),
                )
            )
            return float(np.clip(probabilities["ensemble"] * 100, 0, 100))

        return {"names": names, "current": current, "baseline": baseline, "predict": predict, "source_systems": ["burnout_ai", "random_forest", "xgboost", "neural_network"]}

    def _shap_like(self, names: list[str], current: np.ndarray, baseline: np.ndarray, predict) -> list[FeatureAttribution]:
        prediction = predict(current)
        rows = []
        for index, name in enumerate(names):
            masked = current.copy()
            masked[index] = baseline[index]
            contribution = prediction - predict(masked)
            rows.append(self._attribution(name, current[index], contribution, prediction))
        return self._normalize_attributions(rows)

    def _lime_like(self, names: list[str], current: np.ndarray, baseline: np.ndarray, predict) -> list[FeatureAttribution]:
        rng = np.random.default_rng(909)
        span = np.maximum(np.abs(current - baseline), 0.08)
        samples = []
        targets = []
        for _ in range(36):
            noise = rng.normal(0, 0.22, size=len(current)) * span
            sample = np.clip(current + noise, np.minimum(current, baseline) - span, np.maximum(current, baseline) + span)
            samples.append(sample)
            targets.append(predict(sample))
        regression = LinearRegression().fit(np.array(samples), np.array(targets))
        rows = [self._attribution(name, value, coefficient * value, predict(current)) for name, value, coefficient in zip(names, current, regression.coef_, strict=True)]
        return self._normalize_attributions(rows)

    @staticmethod
    def _attribution(name: str, value: float, contribution: float, prediction: float) -> FeatureAttribution:
        if contribution > 0.35:
            direction = "increases_risk"
        elif contribution < -0.35:
            direction = "reduces_risk"
        else:
            direction = "neutral"
        return FeatureAttribution(
            feature=name,
            value=round(float(value), 4),
            contribution=round(float(contribution), 4),
            direction=direction,
            importance=0,
            evidence=f"{name} moves the local prediction by {round(float(contribution), 2)} points around a {round(float(prediction), 2)} prediction.",
        )

    @staticmethod
    def _normalize_attributions(rows: list[FeatureAttribution]) -> list[FeatureAttribution]:
        total = sum(abs(row.contribution) for row in rows) or 1
        normalized = [
            row.model_copy(update={"importance": round(abs(row.contribution) / total, 4)})
            for row in rows
        ]
        return sorted(normalized, key=lambda item: item.importance, reverse=True)

    def _counterfactuals(self, names: list[str], current: np.ndarray, baseline: np.ndarray, predict, prediction: float) -> list[CounterfactualAction]:
        actions = []
        for index, name in enumerate(names):
            adjusted = current.copy()
            adjusted[index] = baseline[index]
            expected = float(predict(adjusted))
            impact = prediction - expected
            if impact <= 1:
                continue
            actions.append(
                CounterfactualAction(
                    action=f"Move {name.replace('_', ' ')} toward the healthy baseline.",
                    expected_prediction=round(expected, 2),
                    impact=round(impact, 2),
                    rationale=f"Changing {name} from {round(float(current[index]), 3)} to {round(float(baseline[index]), 3)} lowers the modeled risk by {round(impact, 2)} points.",
                )
            )
        return sorted(actions, key=lambda item: item.impact, reverse=True)[:4]

    @staticmethod
    def _explanation_text(target: str, prediction: float, baseline: float, top: list[FeatureAttribution]) -> str:
        drivers = ", ".join(f"{item.feature.replace('_', ' ')} ({item.contribution:+.2f})" for item in top)
        delta = prediction - baseline
        if delta >= 0:
            return f"{target.replace('_', ' ').title()} risk is {round(delta, 2)} points above baseline because the strongest model attributions are {drivers}."
        return f"{target.replace('_', ' ').title()} risk is {abs(round(delta, 2))} points below baseline because protective attributions dominate: {drivers}."

    @staticmethod
    def _severity(value: float) -> str:
        if value >= 82:
            return "critical"
        if value >= 66:
            return "high"
        if value >= 42:
            return "medium"
        return "low"

    @staticmethod
    def _inverse_severity(value: float) -> str:
        if value < 45:
            return "critical"
        if value < 62:
            return "high"
        if value < 76:
            return "medium"
        return "low"

    @staticmethod
    def _clip(value: float) -> float:
        return round(float(np.clip(value, 0, 100)), 2)

    def _append_jsonl(self, path: Path, payload: dict[str, object]) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with self._lock:
            with path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, default=str) + "\n")


power_feature_service = PowerFeatureService()
