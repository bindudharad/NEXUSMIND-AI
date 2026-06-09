from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from threading import Lock
from typing import Any

from app.core.cache import TTLResponseCache
from app.schemas.boardroom import (
    BoardroomAlert,
    BoardroomAssistantRequest,
    BoardroomAssistantResponse,
    BoardroomDashboardResponse,
    BoardroomKPI,
    BoardroomSeverity,
    BoardroomStatus,
    BoardroomSummary,
    ClientIntelligencePanel,
    CompanyHealthPanel,
    CompetitiveIntelligencePanel,
    CybersecurityPanel,
    DigitalTwinCommandCenter,
    ExecutiveRecommendation,
    ExecutiveRiskItem,
    FinancialPredictionPanel,
    InnovationIntelligencePanel,
    ProjectIntelligencePanel,
    WorkforceIntelligencePanel,
)
from app.services.anomaly_service import anomaly_service
from app.services.autonomous_workflow_service import autonomous_workflow_service
from app.services.business_prediction_service import business_prediction_service
from app.services.client_satisfaction_service import client_satisfaction_service
from app.services.company_emotion_map_service import company_emotion_map_service
from app.services.company_health_service import company_health_service
from app.services.company_simulation_lab_service import company_simulation_lab_service
from app.services.competitive_intelligence_service import competitive_intelligence_service
from app.services.dashboard_service import dashboard_service
from app.services.innovation_service import innovation_scoring_service
from app.services.project_failure_service import project_failure_service


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
HISTORY_PATH = DATA_DIR / "boardroom_dashboard_history.jsonl"


class BoardroomDashboardService:
    model_name = "AI Boardroom Dashboard - JARVIS for Companies"
    assistant_model = "Executive AI Boardroom Assistant"
    source_systems = [
        "executive_dashboard",
        "real_time_data_layer",
        "ai_insights_engine",
        "risk_aggregation_engine",
        "executive_recommendation_engine",
        "company_digital_twin",
        "executive_ai_assistant",
        "forecasting_integration",
        "company_health_engine",
        "financial_prediction_engine",
        "workforce_intelligence_engine",
        "cybersecurity_intelligence_engine",
        "project_intelligence_engine",
        "client_intelligence_engine",
        "competitive_intelligence_engine",
        "innovation_intelligence_engine",
        "digital_twin_command_center",
        "realtime_alert_engine",
        "boardroom_dashboard_history_jsonl",
    ]
    forecast_models = [
        "Prophet trend adapter",
        "XGBoost risk model",
        "Random Forest revenue model",
        "LSTM sequence forecaster",
        "Monte Carlo digital twin simulator",
    ]

    def __init__(self) -> None:
        self._cache: TTLResponseCache[BoardroomDashboardResponse] = TTLResponseCache(ttl_seconds=6)
        self._lock = Lock()
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def default(self) -> BoardroomDashboardResponse:
        return self._cache.get_or_set(self._latest_or_build)

    def ask(self, payload: BoardroomAssistantRequest) -> BoardroomAssistantResponse:
        dashboard = self.default()
        intent = self._intent(payload.question)
        answer, panels, evidence = self._answer(intent, dashboard)
        return BoardroomAssistantResponse(
            model=self.assistant_model,
            generated_at=datetime.now(timezone.utc),
            question=payload.question,
            intent=intent,
            answer=answer,
            confidence=dashboard.summary.executive_confidence,
            cited_panels=panels,
            cited_evidence=evidence[:10],
            recommended_actions=[item.action for item in dashboard.recommendations[:5]],
            source_systems=["executive_ai_assistant", "ai_insights_engine", "risk_aggregation_engine", *dashboard.source_systems[:10]],
            storage=str(HISTORY_PATH),
        )

    async def stream(self):
        for sequence in range(1, 4):
            response = self.default()
            data = response.model_dump(mode="json")
            data["summary"]["stream_sequence"] = sequence
            yield f"event: boardroom\ndata: {json.dumps(data)}\n\n"
            await asyncio.sleep(0.8)

    def _latest_or_build(self) -> BoardroomDashboardResponse:
        snapshot = self._latest_snapshot()
        if snapshot is not None:
            return snapshot
        return self._build_uncached()

    def _latest_snapshot(self) -> BoardroomDashboardResponse | None:
        if not HISTORY_PATH.exists():
            return None
        latest = ""
        try:
            with HISTORY_PATH.open("r", encoding="utf-8", errors="ignore") as handle:
                for line in handle:
                    stripped = line.strip()
                    if stripped:
                        latest = stripped
            if not latest:
                return None
            payload = json.loads(latest)
            payload["generated_at"] = datetime.now(timezone.utc).isoformat()
            if isinstance(payload.get("summary"), dict):
                payload["summary"]["stream_sequence"] = 1
            return BoardroomDashboardResponse.model_validate(payload)
        except (OSError, json.JSONDecodeError, ValueError):
            return None

    def _build_uncached(self) -> BoardroomDashboardResponse:
        context = self._context()
        company_health = self._company_health(context)
        financial = self._financial(context)
        workforce = self._workforce(context)
        cybersecurity = self._cybersecurity(context)
        projects = self._projects(context)
        clients = self._clients(context)
        competitive = self._competitive(context)
        innovation = self._innovation(context)
        digital_twin = self._digital_twin(context)
        risks = self._risks(context)
        alerts = self._alerts(context, risks)
        recommendations = self._recommendations(context, risks)
        kpis = self._kpis(company_health, financial, workforce, cybersecurity, projects, clients, competitive, innovation)
        summary = self._summary(company_health, risks, alerts, recommendations, context)

        response = BoardroomDashboardResponse(
            model=self.model_name,
            generated_at=datetime.now(timezone.utc),
            dashboard_name="AI Boardroom Dashboard - JARVIS for Companies",
            kpis=kpis,
            company_health=company_health,
            executive_risks=risks,
            financial_predictions=financial,
            workforce=workforce,
            cybersecurity=cybersecurity,
            projects=projects,
            clients=clients,
            competitive=competitive,
            innovation=innovation,
            digital_twin=digital_twin,
            alerts=alerts,
            recommendations=recommendations,
            executive_summary=self._executive_summary(company_health, risks, financial, workforce, clients, competitive, innovation),
            supported_questions=[
                "Why is company health declining?",
                "Which risk should I solve first?",
                "Predict next quarter.",
                "Show highest burnout team.",
                "Which client may leave?",
                "Simulate losing 10 engineers.",
                "What should the executive team do next?",
                "Show cybersecurity threats.",
                "Show innovation opportunities.",
            ],
            source_systems=self._source_systems(context),
            summary=summary,
            storage=str(HISTORY_PATH),
        )
        self._append_jsonl(response.model_dump(mode="json"))
        return response

    def _context(self) -> dict[str, Any]:
        return {
            "overview": dashboard_service.get_overview(),
            "company": company_health_service.analyze(),
            "business": business_prediction_service.analyze(),
            "security": anomaly_service.detect(),
            "projects": project_failure_service.analyze(),
            "clients": client_satisfaction_service.predict(),
            "competitive": competitive_intelligence_service.analyze(),
            "innovation": innovation_scoring_service.score(),
            "emotion": company_emotion_map_service.default(),
            "simulation": company_simulation_lab_service.run(),
            "workflow": autonomous_workflow_service.run(),
        }

    def _company_health(self, context: dict[str, Any]) -> CompanyHealthPanel:
        company = context["company"]
        business = context["business"]
        overview = context["overview"]
        score = round(mean([company.summary.company_health_score, business.summary.company_health_score, overview.company_health]), 2)
        return CompanyHealthPanel(
            score=score,
            status=self._status(score),
            trend="improving" if business.summary.revenue_growth_rate >= 0 and company.summary.operational_risk < 60 else "watching risk pressure",
            drivers=[
                f"Productivity {round(company.summary.productivity_score)}%",
                f"Wellbeing {round(company.summary.employee_happiness_score)}%",
                f"Client health {round(context['clients'].summary.average_client_health_score)}%",
                f"Security {round(100 - context['security'].summary.average_insider_score)}%",
                f"Innovation {round(context['innovation'].summary.average_innovation_score)}%",
            ],
            historical_trend=[round(point.company_health_score, 2) for point in company.risk_forecasts[:6]],
            source_systems=["company_health_engine", "business_health_engine", "dashboard_service", "company_digital_twin"],
        )

    def _financial(self, context: dict[str, Any]) -> FinancialPredictionPanel:
        business = context["business"]
        revenue = [point.revenue for point in business.revenue_forecast]
        current = business.summary.current_revenue
        annual = business.summary.annual_revenue_forecast
        cost = max(0.0, annual * (0.42 + business.summary.market_risk_score / 500))
        profit = max(0.0, annual - cost)
        quarterly = []
        for index in range(0, min(12, len(revenue)), 3):
            chunk = revenue[index : index + 3]
            if chunk:
                quarterly.append(round(sum(chunk), 2))
        annual_series = [round(sum(revenue[: min(len(revenue), months)]), 2) for months in (3, 6, 9, 12) if revenue]
        return FinancialPredictionPanel(
            current_revenue=round(current, 2),
            next_quarter_revenue=round(business.summary.predicted_next_quarter_revenue, 2),
            annual_revenue_forecast=round(annual, 2),
            revenue_growth_rate=round(business.summary.revenue_growth_rate, 2),
            profit_forecast=round(profit, 2),
            cost_forecast=round(cost, 2),
            forecast_confidence=business.summary.forecast_confidence,
            monthly_forecast=[round(value, 2) for value in revenue[:12]],
            quarterly_forecast=quarterly,
            annual_forecast=annual_series,
            forecast_models=self.forecast_models,
        )

    def _workforce(self, context: dict[str, Any]) -> WorkforceIntelligencePanel:
        company = context["company"]
        emotion = context["emotion"]
        innovation = context["innovation"]
        hotspots = [
            f"{team.department} / {team.team_name}"
            for team in company.team_scores
            if team.burnout_risk >= 55 or team.risk_score >= 55
        ][:5]
        top_innovator = innovation.employee_scores[0].employee_name if innovation.employee_scores else "No innovation signal"
        productivity_trend = (
            company.productivity_trends[-1].productivity_score - company.productivity_trends[0].productivity_score
            if len(company.productivity_trends) >= 2
            else 0
        )
        return WorkforceIntelligencePanel(
            employee_health_score=round(100 - mean([company.summary.burnout_risk, emotion.summary.average_burnout]), 2),
            burnout_hotspots=hotspots or ["No critical burnout hotspot"],
            attrition_risk=round(company.summary.attrition_risk, 2),
            productivity_trend=round(productivity_trend, 2),
            top_innovator=top_innovator,
            hidden_talent_count=innovation.summary.hidden_talent_count,
            future_leaders_count=innovation.summary.future_leaders_count,
            source_systems=["workforce_intelligence_engine", "company_emotion_map", "innovation_intelligence_engine", "employee_digital_twin"],
        )

    def _cybersecurity(self, context: dict[str, Any]) -> CybersecurityPanel:
        security = context["security"]
        insider = security.summary.average_insider_score
        leakage = security.summary.average_data_leakage_probability
        score = self._clamp(100 - mean([insider, leakage, security.anomaly_rate * 100]) * 0.72)
        suspicious = [f"{alert.employee_name}: {alert.anomaly_type}" for alert in security.alerts[:5]]
        return CybersecurityPanel(
            security_score=round(score, 2),
            threat_level=self._severity(mean([insider, leakage, security.anomaly_rate * 100])),
            active_threats=len(security.alerts),
            insider_threat_risk=round(insider, 2),
            data_leakage_risk=round(leakage, 2),
            suspicious_activity=suspicious or ["No high-severity suspicious activity"],
            recommendations=[item.action for item in security.security_recommendations[:4]],
            source_systems=["cybersecurity_intelligence_engine", "insider_threat_detection", "data_leakage_prediction", *security.source_systems],
        )

    def _projects(self, context: dict[str, Any]) -> ProjectIntelligencePanel:
        projects = context["projects"]
        top = projects.predictions[0] if projects.predictions else None
        confidence = 100 - projects.summary.average_delay_probability
        gaps = []
        if top:
            gaps = [signal.recommendation for signal in top.risk_signals[:3]]
        forecast = [round(point.sprint_completion_probability, 2) for point in top.forecast[:6]] if top else []
        return ProjectIntelligencePanel(
            project_health_score=round(projects.summary.average_health_score, 2),
            completion_confidence=round(self._clamp(confidence), 2),
            highest_risk_project=projects.summary.highest_risk_project,
            delivery_risk=round(projects.summary.average_delay_probability, 2),
            resource_gaps=gaps or ["No urgent resource gap detected"],
            delivery_forecast=forecast,
            source_systems=["project_intelligence_engine", "completion_forecasting", "resource_gap_analyzer"],
        )

    def _clients(self, context: dict[str, Any]) -> ClientIntelligencePanel:
        clients = context["clients"]
        status = "healthy"
        if clients.summary.average_churn_risk >= 65:
            status = "at risk"
        elif clients.summary.average_churn_risk >= 42:
            status = "watch"
        return ClientIntelligencePanel(
            average_client_health=round(clients.summary.average_client_health_score, 2),
            highest_churn_risk_client=clients.summary.highest_risk_client,
            churn_risk=round(clients.summary.average_churn_risk, 2),
            payment_risk_accounts=clients.summary.payment_risk_accounts,
            upsell_opportunity_revenue=round(clients.summary.opportunity_revenue, 2),
            relationship_status=status,
            recommended_actions=[item.action for item in clients.recommendations[:4]],
            source_systems=["client_intelligence_engine", *clients.source_systems[:8]],
        )

    def _competitive(self, context: dict[str, Any]) -> CompetitiveIntelligencePanel:
        competitive = context["competitive"]
        top = competitive.risk_scores[0] if competitive.risk_scores else None
        return CompetitiveIntelligencePanel(
            threat_score=round(competitive.summary.average_threat_score, 2),
            top_threat=competitive.summary.top_competitor_threat,
            market_trends=[trend.trend for trend in competitive.industry_trends[:4]],
            industry_risks=[trend.risk for trend in competitive.industry_trends[:4]],
            strategic_opportunities=[trend.opportunity for trend in competitive.industry_trends[:4]],
            recommendations=[item.action for item in competitive.recommendations[:4]],
            source_systems=["competitive_intelligence_engine", "market_intelligence_engine", *(top.evidence if top else [])[:2]],
        )

    def _innovation(self, context: dict[str, Any]) -> InnovationIntelligencePanel:
        innovation = context["innovation"]
        return InnovationIntelligencePanel(
            hidden_talent_count=innovation.summary.hidden_talent_count,
            future_leaders_count=innovation.summary.future_leaders_count,
            innovation_champions=[item.employee_name for item in innovation.employee_scores[:4]],
            skill_growth_trend=round(innovation.summary.average_growth_velocity, 2),
            promotion_recommendations=[item.action for item in innovation.promotion_recommendations[:4]],
            source_systems=["innovation_intelligence_engine", *innovation.source_systems[:8]],
        )

    def _digital_twin(self, context: dict[str, Any]) -> DigitalTwinCommandCenter:
        simulation = context["simulation"]
        workflow = context["workflow"]
        emotion = context["emotion"]
        return DigitalTwinCommandCenter(
            company_twin_status="synchronized",
            active_simulations=simulation.summary.scenario_count,
            recommended_scenario=simulation.summary.recommended_scenario,
            highest_risk_scenario=simulation.summary.highest_risk_scenario,
            future_forecasts=[
                f"Decision readiness {round(simulation.summary.decision_readiness_score)}%",
                f"Workflow readiness {round(workflow.summary.operations_readiness_score)}%",
                f"Morale forecast {round(emotion.summary.morale_forecast_90d)}%",
            ],
            organizational_status=[
                f"Open escalations {workflow.summary.escalations_open}",
                f"Automation events {workflow.summary.automation_events}",
                f"Emotion heatmap points {len(emotion.heatmap)}",
            ],
            source_systems=["company_digital_twin", "simulation_engine", "workflow_automation", *simulation.source_systems[:8]],
        )

    def _risks(self, context: dict[str, Any]) -> list[ExecutiveRiskItem]:
        company = context["company"]
        business = context["business"]
        security = context["security"]
        projects = context["projects"]
        clients = context["clients"]
        competitive = context["competitive"]
        innovation = context["innovation"]
        emotion = context["emotion"]
        risks = [
            ExecutiveRiskItem(
                risk_id="risk-boardroom-burnout",
                category="Burnout Risk",
                title="Workforce burnout pressure",
                affected_area=company.team_scores[0].department if company.team_scores else "Workforce",
                probability=round(company.summary.burnout_risk, 2),
                impact_score=round(100 - emotion.summary.organizational_health_score, 2),
                severity=self._severity(company.summary.burnout_risk),
                recommendation=company.recommendations[0].action if company.recommendations else "Reduce workload pressure in high-risk teams.",
                evidence=[f"burnout={round(company.summary.burnout_risk)}", f"emotion_health={round(emotion.summary.organizational_health_score)}"],
                source_systems=["company_health_engine", "company_emotion_map"],
            ),
            ExecutiveRiskItem(
                risk_id="risk-boardroom-project",
                category="Project Risk",
                title=f"{projects.summary.highest_risk_project} delivery risk",
                affected_area=projects.summary.highest_risk_project,
                probability=round(projects.summary.average_delay_probability, 2),
                impact_score=round(projects.summary.average_failure_probability, 2),
                severity=self._severity(projects.summary.average_failure_probability),
                recommendation=projects.portfolio_recommendations[0].action if projects.portfolio_recommendations else "Escalate project delivery risk.",
                evidence=[f"critical_projects={projects.summary.critical_projects}", f"health={round(projects.summary.average_health_score)}"],
                source_systems=["project_intelligence_engine", "completion_forecasting"],
            ),
            ExecutiveRiskItem(
                risk_id="risk-boardroom-client",
                category="Client Risk",
                title=f"{clients.summary.highest_risk_client} churn risk",
                affected_area=clients.summary.highest_risk_client,
                probability=round(clients.summary.average_churn_risk, 2),
                impact_score=round(min(100, clients.summary.revenue_at_risk / 50_000), 2),
                severity=self._severity(clients.summary.average_churn_risk),
                recommendation=clients.recommendations[0].action if clients.recommendations else "Schedule executive client intervention.",
                evidence=[f"revenue_at_risk={round(clients.summary.revenue_at_risk)}", f"payment_risk_accounts={clients.summary.payment_risk_accounts}"],
                source_systems=["client_intelligence_engine", "churn_prediction_engine"],
            ),
            ExecutiveRiskItem(
                risk_id="risk-boardroom-security",
                category="Cybersecurity Risk",
                title="Insider and data leakage threat",
                affected_area=security.alerts[0].department if security.alerts else "Security",
                probability=round(max(security.summary.average_insider_score, security.summary.average_data_leakage_probability), 2),
                impact_score=round(max(security.summary.average_insider_score, security.summary.average_data_leakage_probability), 2),
                severity=self._severity(max(security.summary.average_insider_score, security.summary.average_data_leakage_probability)),
                recommendation=security.security_recommendations[0].action if security.security_recommendations else "Maintain adaptive security controls.",
                evidence=[f"alerts={len(security.alerts)}", f"data_leakage={round(security.summary.average_data_leakage_probability)}"],
                source_systems=["cybersecurity_intelligence_engine", "soc_alert_correlator"],
            ),
            ExecutiveRiskItem(
                risk_id="risk-boardroom-revenue",
                category="Revenue Risk",
                title=business.summary.top_business_risk,
                affected_area="Finance",
                probability=round(business.summary.market_risk_score, 2),
                impact_score=round(min(100, business.summary.revenue_at_risk / 80_000), 2),
                severity=self._severity(business.summary.market_risk_score),
                recommendation=business.recommendations[0].action if business.recommendations else "Review revenue risk mitigation.",
                evidence=[f"revenue_at_risk={round(business.summary.revenue_at_risk)}", f"growth={round(business.summary.revenue_growth_rate, 2)}"],
                source_systems=["financial_prediction_engine", "business_prediction_engine"],
            ),
            ExecutiveRiskItem(
                risk_id="risk-boardroom-competitive",
                category="Competitive Risk",
                title=f"{competitive.summary.top_competitor_threat} market pressure",
                affected_area="Strategy",
                probability=round(competitive.summary.average_threat_score, 2),
                impact_score=round(competitive.summary.average_threat_score, 2),
                severity=self._severity(competitive.summary.average_threat_score),
                recommendation=competitive.recommendations[0].action if competitive.recommendations else "Review competitive response plan.",
                evidence=[f"high_threat_competitors={competitive.summary.high_threat_competitors}", f"launches={competitive.summary.product_launches_tracked}"],
                source_systems=["competitive_intelligence_engine", "market_intelligence_engine"],
            ),
            ExecutiveRiskItem(
                risk_id="risk-boardroom-talent",
                category="Talent Flight Risk",
                title="Hidden talent retention exposure",
                affected_area="Leadership Bench",
                probability=round(max([item.flight_risk for item in innovation.talent_risks] or [0]), 2),
                impact_score=round(max([item.hidden_talent_score for item in innovation.hidden_talent] or [0]), 2),
                severity=self._severity(max([item.flight_risk for item in innovation.talent_risks] or [0])),
                recommendation=innovation.promotion_recommendations[0].action if innovation.promotion_recommendations else "Sponsor high-potential employees.",
                evidence=[f"hidden_talent={innovation.summary.hidden_talent_count}", f"future_leaders={innovation.summary.future_leaders_count}"],
                source_systems=["innovation_intelligence_engine", "talent_discovery_engine"],
            ),
        ]
        return sorted(risks, key=lambda item: (item.severity == "critical", item.probability + item.impact_score), reverse=True)

    def _alerts(self, context: dict[str, Any], risks: list[ExecutiveRiskItem]) -> list[BoardroomAlert]:
        alerts = [
            BoardroomAlert(
                alert_id=f"alert-{risk.risk_id}",
                category=risk.category,
                severity=risk.severity,
                title=risk.title,
                probability=risk.probability,
                recommendation=risk.recommendation,
                source_systems=risk.source_systems,
            )
            for risk in risks
            if risk.severity in {"high", "critical"}
        ]
        for escalation in context["workflow"].escalations[:3]:
            alerts.append(
                BoardroomAlert(
                    alert_id=f"alert-workflow-{escalation.escalation_id}",
                    category="Escalation",
                    severity=escalation.severity,
                    title=escalation.title,
                    probability=82 if escalation.severity == "critical" else 68,
                    recommendation=escalation.rationale,
                    source_systems=["realtime_alert_engine", "workflow_automation", "escalation_engine"],
                )
            )
        return sorted(alerts, key=lambda item: item.probability, reverse=True)[:10]

    def _recommendations(self, context: dict[str, Any], risks: list[ExecutiveRiskItem]) -> list[ExecutiveRecommendation]:
        recommendations: list[ExecutiveRecommendation] = []
        sources = [
            ("workforce", context["company"].recommendations[:2]),
            ("finance", context["business"].recommendations[:2]),
            ("client", context["clients"].recommendations[:2]),
            ("security", context["security"].security_recommendations[:2]),
            ("strategy", context["competitive"].recommendations[:2]),
            ("innovation", context["innovation"].promotion_recommendations[:2]),
            ("operations", context["workflow"].recommendations[:2]),
        ]
        for category, items in sources:
            for index, item in enumerate(items, start=1):
                action = getattr(item, "action", getattr(item, "recommendation", str(item)))
                reason = getattr(item, "rationale", getattr(item, "reason", getattr(item, "expected_impact", "Derived from live enterprise signal.")))
                priority = getattr(item, "priority", "high")
                confidence = getattr(item, "confidence", 0.84)
                recommendations.append(
                    ExecutiveRecommendation(
                        recommendation_id=f"rec-{category}-{index}",
                        category=category,
                        priority=priority if priority in {"low", "medium", "high", "critical"} else "high",
                        action=action,
                        reason=str(reason),
                        expected_benefit=str(getattr(item, "expected_benefit", getattr(item, "expected_impact", "Improve executive operating confidence."))),
                        confidence=float(confidence),
                        source_systems=[f"{category}_engine", "executive_recommendation_engine"],
                    )
                )
        for risk in risks[:3]:
            recommendations.append(
                ExecutiveRecommendation(
                    recommendation_id=f"rec-{risk.risk_id}",
                    category=risk.category.lower().replace(" ", "_"),
                    priority=risk.severity,
                    action=risk.recommendation,
                    reason=f"{risk.title} has {round(risk.probability)}% probability and {round(risk.impact_score)} impact.",
                    expected_benefit="Reduce board-level risk exposure before it becomes operational loss.",
                    confidence=0.9,
                    source_systems=risk.source_systems,
                )
            )
        return sorted(recommendations, key=lambda item: (item.priority == "critical", item.confidence), reverse=True)[:12]

    def _kpis(
        self,
        company_health: CompanyHealthPanel,
        financial: FinancialPredictionPanel,
        workforce: WorkforceIntelligencePanel,
        cybersecurity: CybersecurityPanel,
        projects: ProjectIntelligencePanel,
        clients: ClientIntelligencePanel,
        competitive: CompetitiveIntelligencePanel,
        innovation: InnovationIntelligencePanel,
    ) -> list[BoardroomKPI]:
        return [
            BoardroomKPI(label="Company Health", value=f"{round(company_health.score)}%", score=company_health.score, trend=1.8, status=company_health.status, source="company_health_engine"),
            BoardroomKPI(label="Revenue Forecast", value=f"${financial.next_quarter_revenue / 1_000_000:.1f}M", score=self._clamp(55 + financial.revenue_growth_rate), trend=financial.revenue_growth_rate, status=self._status(55 + financial.revenue_growth_rate), source="financial_prediction_engine"),
            BoardroomKPI(label="Employee Status", value=f"{round(workforce.employee_health_score)}%", score=workforce.employee_health_score, trend=workforce.productivity_trend, status=self._status(workforce.employee_health_score), source="workforce_intelligence_engine"),
            BoardroomKPI(label="Security Score", value=f"{round(cybersecurity.security_score)}%", score=cybersecurity.security_score, trend=-cybersecurity.active_threats, status=self._status(cybersecurity.security_score), source="cybersecurity_intelligence_engine"),
            BoardroomKPI(label="Project Delivery", value=f"{round(projects.completion_confidence)}%", score=projects.completion_confidence, trend=-projects.delivery_risk / 10, status=self._status(projects.completion_confidence), source="project_intelligence_engine"),
            BoardroomKPI(label="Client Health", value=f"{round(clients.average_client_health)}%", score=clients.average_client_health, trend=-clients.churn_risk / 10, status=self._status(clients.average_client_health), source="client_intelligence_engine"),
            BoardroomKPI(label="Competitive Threat", value=f"{round(competitive.threat_score)}%", score=100 - competitive.threat_score, trend=-competitive.threat_score / 10, status=self._status(100 - competitive.threat_score), source="competitive_intelligence_engine"),
            BoardroomKPI(label="Innovation Bench", value=f"{innovation.future_leaders_count}", score=innovation.skill_growth_trend, trend=innovation.future_leaders_count, status=self._status(innovation.skill_growth_trend), source="innovation_intelligence_engine"),
        ]

    def _summary(
        self,
        company_health: CompanyHealthPanel,
        risks: list[ExecutiveRiskItem],
        alerts: list[BoardroomAlert],
        recommendations: list[ExecutiveRecommendation],
        context: dict[str, Any],
    ) -> BoardroomSummary:
        risk_score = mean([risk.probability * 0.55 + risk.impact_score * 0.45 for risk in risks]) if risks else 0
        confidence = mean(
            [
                context["business"].summary.forecast_confidence,
                context["simulation"].summary.average_confidence,
                context["workflow"].summary.average_assignment_confidence,
                0.9,
            ]
        )
        return BoardroomSummary(
            company_health_score=company_health.score,
            overall_risk_score=round(self._clamp(risk_score), 2),
            executive_confidence=round(self._clamp(confidence, 0, 1), 3),
            critical_risks=sum(1 for risk in risks if risk.severity == "critical"),
            active_alerts=len(alerts),
            recommended_actions=len(recommendations),
            realtime_streams=9,
            connected_engines=len(self.source_systems),
            stream_sequence=1,
        )

    def _executive_summary(
        self,
        company_health: CompanyHealthPanel,
        risks: list[ExecutiveRiskItem],
        financial: FinancialPredictionPanel,
        workforce: WorkforceIntelligencePanel,
        clients: ClientIntelligencePanel,
        competitive: CompetitiveIntelligencePanel,
        innovation: InnovationIntelligencePanel,
    ) -> list[str]:
        top_risk = risks[0]
        return [
            f"Company health is {round(company_health.score)}% and currently {company_health.status}.",
            f"Top board-level risk is {top_risk.title} with {round(top_risk.probability)}% probability.",
            f"Next-quarter revenue forecast is ${financial.next_quarter_revenue / 1_000_000:.1f}M with {round(financial.forecast_confidence * 100)}% confidence.",
            f"Workforce signal shows {len(workforce.burnout_hotspots)} burnout hotspot(s), {workforce.future_leaders_count} future leaders, and top innovator {workforce.top_innovator}.",
            f"Client risk centers on {clients.highest_churn_risk_client}; competitive pressure centers on {competitive.top_threat}.",
            f"Innovation pipeline has {innovation.hidden_talent_count} hidden talent signals and {len(innovation.promotion_recommendations)} promotion actions.",
        ]

    def _source_systems(self, context: dict[str, Any]) -> list[str]:
        systems = list(self.source_systems)
        for key in ["business", "clients", "competitive", "innovation", "emotion", "simulation", "workflow", "security"]:
            systems.extend(getattr(context[key], "source_systems", []))
        return list(dict.fromkeys(systems))[:80]

    def _intent(self, question: str):
        text = question.lower()
        if any(token in text for token in ["declining", "health", "company"]):
            return "health"
        if any(token in text for token in ["risk", "solve first", "priority"]):
            return "risk"
        if any(token in text for token in ["quarter", "revenue", "forecast", "future", "predict"]):
            return "forecast"
        if any(token in text for token in ["burnout", "stress", "employee"]):
            return "burnout"
        if any(token in text for token in ["client", "leave", "churn", "pay"]):
            return "client"
        if any(token in text for token in ["simulate", "engineer", "resign", "scenario"]):
            return "simulation"
        if any(token in text for token in ["security", "cyber", "threat"]):
            return "security"
        if any(token in text for token in ["innovation", "leader", "talent", "promote"]):
            return "innovation"
        if any(token in text for token in ["recommend", "action", "do next"]):
            return "recommendation"
        return "summary"

    def _answer(self, intent: str, dashboard: BoardroomDashboardResponse) -> tuple[str, list[str], list[str]]:
        top_risk = dashboard.executive_risks[0]
        if intent == "health":
            answer = (
                f"Company health is {round(dashboard.company_health.score)}% ({dashboard.company_health.status}). "
                f"The main drivers are {', '.join(dashboard.company_health.drivers[:3])}. "
                f"Risk pressure is {round(dashboard.summary.overall_risk_score)}%."
            )
            panels = ["Company Health", "Executive Risk"]
            evidence = dashboard.company_health.drivers + [top_risk.title]
        elif intent == "risk":
            answer = (
                f"Solve {top_risk.title} first. It has {round(top_risk.probability)}% probability, "
                f"{round(top_risk.impact_score)} impact, and affects {top_risk.affected_area}."
            )
            panels = ["Executive Risk", "Realtime Alerts"]
            evidence = top_risk.evidence + [top_risk.recommendation]
        elif intent == "forecast":
            answer = (
                f"Next-quarter revenue is forecast at ${dashboard.financial_predictions.next_quarter_revenue / 1_000_000:.1f}M. "
                f"Annual forecast is ${dashboard.financial_predictions.annual_revenue_forecast / 1_000_000:.1f}M "
                f"with {round(dashboard.financial_predictions.forecast_confidence * 100)}% confidence."
            )
            panels = ["Financial Prediction", "Digital Twin"]
            evidence = dashboard.financial_predictions.forecast_models
        elif intent == "burnout":
            answer = (
                f"Highest burnout pressure is in {dashboard.workforce.burnout_hotspots[0]}. "
                f"Employee health is {round(dashboard.workforce.employee_health_score)}% and attrition risk is "
                f"{round(dashboard.workforce.attrition_risk)}%."
            )
            panels = ["Employee Status", "Company Emotion Map"]
            evidence = dashboard.workforce.burnout_hotspots
        elif intent == "client":
            answer = (
                f"{dashboard.clients.highest_churn_risk_client} is the highest client risk. "
                f"Average churn risk is {round(dashboard.clients.churn_risk)}% and payment-risk accounts total "
                f"{dashboard.clients.payment_risk_accounts}."
            )
            panels = ["Client Intelligence"]
            evidence = dashboard.clients.recommended_actions
        elif intent == "simulation":
            answer = (
                f"Digital twin is {dashboard.digital_twin.company_twin_status}. "
                f"Recommended scenario is {dashboard.digital_twin.recommended_scenario}; highest-risk scenario is "
                f"{dashboard.digital_twin.highest_risk_scenario}."
            )
            panels = ["Digital Twin Command Center", "Simulation Lab"]
            evidence = dashboard.digital_twin.future_forecasts + dashboard.digital_twin.organizational_status
        elif intent == "security":
            answer = (
                f"Security score is {round(dashboard.cybersecurity.security_score)}% with "
                f"{dashboard.cybersecurity.active_threats} active threat(s). "
                f"Threat level is {dashboard.cybersecurity.threat_level}."
            )
            panels = ["Cybersecurity"]
            evidence = dashboard.cybersecurity.suspicious_activity + dashboard.cybersecurity.recommendations
        elif intent == "innovation":
            answer = (
                f"Innovation panel shows {dashboard.innovation.hidden_talent_count} hidden talent signals and "
                f"{dashboard.innovation.future_leaders_count} future leaders. Champions: "
                f"{', '.join(dashboard.innovation.innovation_champions[:3])}."
            )
            panels = ["Innovation"]
            evidence = dashboard.innovation.promotion_recommendations
        elif intent == "recommendation":
            first = dashboard.recommendations[0]
            answer = f"Recommended next action: {first.action} Reason: {first.reason}"
            panels = ["Executive Recommendation Engine"]
            evidence = [first.reason, first.expected_benefit]
        else:
            answer = " ".join(dashboard.executive_summary[:3])
            panels = ["Executive Summary"]
            evidence = dashboard.executive_summary
        return answer, panels, evidence

    @staticmethod
    def _status(score: float) -> BoardroomStatus:
        if score >= 88:
            return "excellent"
        if score >= 74:
            return "healthy"
        if score >= 58:
            return "watch"
        if score >= 38:
            return "risk"
        return "critical"

    @staticmethod
    def _severity(score: float) -> BoardroomSeverity:
        if score >= 82:
            return "critical"
        if score >= 64:
            return "high"
        if score >= 38:
            return "medium"
        return "low"

    @staticmethod
    def _clamp(value: float, lower: float = 0, upper: float = 100) -> float:
        return max(lower, min(upper, float(value)))

    def _append_jsonl(self, payload: dict[str, Any]) -> None:
        with self._lock:
            with HISTORY_PATH.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload) + "\n")


boardroom_dashboard_service = BoardroomDashboardService()
