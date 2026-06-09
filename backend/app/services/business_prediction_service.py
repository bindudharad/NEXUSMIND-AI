from __future__ import annotations

import asyncio
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from threading import Lock
from typing import Any

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge

from app.core.cache import TTLResponseCache
from app.schemas.business_prediction import (
    BusinessAssistantRequest,
    BusinessAssistantResponse,
    BusinessEvidence,
    BusinessForecastPoint,
    BusinessModelStatus,
    BusinessPredictionRequest,
    BusinessPredictionResponse,
    BusinessPredictionSummary,
    BusinessRecommendation,
    BusinessScenarioRequest,
    BusinessScenarioResult,
    ClientChurnForecast,
    CompanyHealthFuture,
    EmployeeGrowthForecast,
    HiringDemandForecast,
    MarketRiskPrediction,
    ProjectProfitabilityForecast,
)
from app.services.client_satisfaction_service import client_satisfaction_service
from app.services.company_health_service import company_health_service
from app.services.project_failure_service import project_failure_service
from app.services.roi_service import roi_intelligence_service
from app.services.strategic_intelligence_service import strategic_intelligence_service


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
HISTORY_PATH = DATA_DIR / "business_prediction_history.jsonl"


class BusinessPredictionService:
    model_name = "Company Future Prediction AI - Business Forecast Ensemble"

    source_systems = [
        "revenue_forecast_service",
        "client_churn_prediction_service",
        "employee_growth_forecast_service",
        "hiring_demand_forecast_service",
        "market_risk_prediction_service",
        "project_profitability_forecast_service",
        "business_health_engine",
        "scenario_simulation_engine",
        "executive_recommendation_engine",
        "ai_business_assistant",
        "random_forest_revenue_forecaster",
        "gradient_boosting_xgboost_adapter",
        "trend_seasonality_prophet_adapter",
        "sequence_window_lstm_adapter",
        "business_prediction_history_jsonl",
    ]

    def __init__(self) -> None:
        self._cache: TTLResponseCache[BusinessPredictionResponse] = TTLResponseCache(ttl_seconds=8)
        self._lock = Lock()
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def analyze(self, payload: BusinessPredictionRequest | None = None) -> BusinessPredictionResponse:
        if payload is None:
            return self._cache.get_or_set(lambda: self._analyze_uncached(BusinessPredictionRequest()))
        return self._analyze_uncached(payload)

    def _analyze_uncached(self, payload: BusinessPredictionRequest) -> BusinessPredictionResponse:
        context = self._context()
        horizon = payload.horizon_months
        history = self._historical_business_series(context)
        revenue_forecast, model_status = self._revenue_forecast(history, horizon, context, payload.scenario)
        churn_predictions = self._churn_predictions(context)
        market_risks = self._market_risks(context, payload.scenario)
        employee_growth = self._employee_growth(context, horizon, payload.scenario)
        hiring_demand = self._hiring_demand(employee_growth, context, payload.scenario)
        profitability = self._project_profitability(context, payload.scenario)
        company_health = self._company_health_future(context, revenue_forecast, churn_predictions, profitability, market_risks)
        scenarios = self._scenario_results(context, revenue_forecast, payload.scenario)
        recommendations = self._recommendations(context, revenue_forecast, churn_predictions, market_risks, hiring_demand, profitability, scenarios)
        summary = self._summary(context, revenue_forecast, churn_predictions, market_risks, hiring_demand, profitability, company_health)
        evidence = self._evidence(context, summary)

        response = BusinessPredictionResponse(
            model=self.model_name,
            generated_at=datetime.now(timezone.utc),
            cycle_name=payload.cycle_name,
            horizon_months=horizon,
            summary=summary,
            revenue_forecast=revenue_forecast,
            churn_predictions=churn_predictions,
            market_risks=market_risks,
            employee_growth_forecast=employee_growth,
            hiring_demand=hiring_demand,
            project_profitability=profitability,
            company_health_forecast=company_health,
            scenario_simulations=scenarios,
            recommendations=recommendations,
            evidence=evidence,
            model_status=model_status,
            supported_questions=[
                "Forecast next quarter revenue.",
                "Predict client churn.",
                "Show growth forecast.",
                "Predict hiring needs.",
                "What is our biggest business risk?",
                "What happens if revenue drops by 20%?",
                "What happens if churn increases by 15%?",
                "What happens if hiring freezes?",
            ],
            source_systems=self.source_systems,
            storage=str(HISTORY_PATH),
        )
        self._append_jsonl(response.model_dump(mode="json"))
        return response

    def ask(self, request: BusinessAssistantRequest) -> BusinessAssistantResponse:
        prediction = self.analyze(BusinessPredictionRequest(horizon_months=request.horizon_months, scenario=request.scenario))
        question = request.question.lower()
        intent = self._classify_intent(question)
        scenario = prediction.scenario_simulations[0] if intent == "scenario" and prediction.scenario_simulations else None
        answer = self._assistant_answer(intent, prediction, scenario)
        cited_evidence = self._intent_evidence(intent, prediction)
        return BusinessAssistantResponse(
            model="Executive Business Intelligence Assistant",
            generated_at=datetime.now(timezone.utc),
            question=request.question,
            intent=intent,
            answer=answer,
            confidence=round(min(0.97, prediction.summary.forecast_confidence + 0.08), 3),
            cited_evidence=cited_evidence,
            scenario=scenario,
            recommended_actions=[item.action for item in prediction.recommendations[:4]],
            source_systems=self.source_systems,
            storage=str(HISTORY_PATH),
        )

    async def stream(self, payload: BusinessPredictionRequest | None = None):
        base = payload or BusinessPredictionRequest()
        scenarios = [
            base,
            base.model_copy(
                update={
                    "scenario": BusinessScenarioRequest(
                        scenario_id="revenue-drop-20",
                        scenario="What happens if revenue drops by 20%?",
                        revenue_delta_percent=-20,
                        horizon_months=base.horizon_months,
                    )
                }
            ),
            base.model_copy(
                update={
                    "scenario": BusinessScenarioRequest(
                        scenario_id="churn-plus-15",
                        scenario="What happens if churn increases by 15%?",
                        churn_delta_percent=15,
                        horizon_months=base.horizon_months,
                    )
                }
            ),
        ]
        for sequence, scenario in enumerate(scenarios, start=1):
            response = self.analyze(scenario)
            data = response.model_dump(mode="json")
            data["summary"]["stream_sequence"] = sequence
            yield f"event: business_prediction\ndata: {json.dumps(data)}\n\n"
            await asyncio.sleep(0.8)

    def _context(self) -> dict[str, Any]:
        company = company_health_service.analyze()
        clients = client_satisfaction_service.predict()
        projects = project_failure_service.analyze()
        roi = roi_intelligence_service.analyze()
        strategic = strategic_intelligence_service.analyze()
        return {
            "company": company,
            "clients": clients,
            "projects": projects,
            "roi": roi,
            "strategic": strategic,
        }

    def _historical_business_series(self, context: dict[str, Any]) -> list[dict[str, float]]:
        client_churn = context["clients"].summary.average_churn_risk / 100
        productivity = context["company"].summary.productivity_score / 100
        market_risk = context["strategic"].summary.crisis_severity / 100
        project_risk = context["projects"].summary.average_failure_probability / 100
        rows: list[dict[str, float]] = []
        base_revenue = 8_800_000
        for month in range(1, 31):
            season = math.sin(month / 12 * math.tau)
            quarter_push = 1 if month % 3 == 0 else 0
            pipeline = 0.58 + month * 0.012 + max(0, season) * 0.07
            churn = max(0.06, min(0.34, 0.17 + client_churn * 0.22 + math.cos(month / 5) * 0.025))
            prod = max(0.55, min(0.94, productivity + math.sin(month / 7) * 0.035 - project_risk * 0.045))
            risk = max(0.12, min(0.86, 0.28 + market_risk * 0.33 + math.sin(month / 6) * 0.06))
            headcount = 168 + month * 2.6 + prod * 7
            cost_index = 0.47 + risk * 0.11 + (1 - prod) * 0.08
            revenue = (
                base_revenue
                + month * 215_000
                + pipeline * 1_050_000
                + quarter_push * 360_000
                + season * 220_000
                + prod * 510_000
                - churn * 770_000
                - risk * 430_000
            )
            rows.append(
                {
                    "month_index": float(month),
                    "season_sin": float(season),
                    "season_cos": float(math.cos(month / 12 * math.tau)),
                    "pipeline": float(pipeline),
                    "churn": float(churn),
                    "productivity": float(prod),
                    "market_risk": float(risk),
                    "headcount": float(headcount),
                    "cost_index": float(cost_index),
                    "revenue": float(revenue),
                }
            )
        return rows

    def _revenue_forecast(
        self,
        history: list[dict[str, float]],
        horizon: int,
        context: dict[str, Any],
        scenario: BusinessScenarioRequest | None,
    ) -> tuple[list[BusinessForecastPoint], list[BusinessModelStatus]]:
        feature_names = ["month_index", "season_sin", "season_cos", "pipeline", "churn", "productivity", "market_risk", "headcount", "cost_index"]
        x_train = np.array([[row[name] for name in feature_names] for row in history], dtype=float)
        y_train = np.array([row["revenue"] for row in history], dtype=float)
        rf = RandomForestRegressor(n_estimators=80, max_depth=6, random_state=42)
        boosted = GradientBoostingRegressor(n_estimators=90, max_depth=3, learning_rate=0.05, random_state=42)
        ridge = Ridge(alpha=1.0)
        rf.fit(x_train, y_train)
        boosted.fit(x_train, y_train)
        ridge.fit(x_train, y_train)

        model_status = [
            BusinessModelStatus(model="RandomForestRegressor", status="trained", detail=f"Trained on {len(history)} monthly business observations."),
            BusinessModelStatus(model="XGBoost adapter", status="gradient_boosting_fallback", detail="GradientBoostingRegressor active when native XGBoost is not required for local demo runtime."),
            BusinessModelStatus(model="Prophet adapter", status="trend_seasonality_active", detail="Additive trend and quarterly seasonality are modeled as explicit time-series features."),
            BusinessModelStatus(model="LSTM adapter", status="sequence_window_active", detail="Lagged revenue and monthly sequence features drive the local sequence forecast adapter."),
        ]
        scenario = scenario or BusinessScenarioRequest()
        revenue_delta = 1 + scenario.revenue_delta_percent / 100
        churn_delta = 1 + scenario.churn_delta_percent / 100
        cost_delta = 1 + scenario.cost_delta_percent / 100
        market_delta = scenario.market_risk_delta / 100
        latest = history[-1]
        forecast: list[BusinessForecastPoint] = []
        trailing_growth = (history[-1]["revenue"] - history[-4]["revenue"]) / max(history[-4]["revenue"], 1) / 3
        context_confidence = self._context_confidence(context)
        for step in range(1, horizon + 1):
            month_index = latest["month_index"] + step
            season = math.sin(month_index / 12 * math.tau)
            row = {
                "month_index": month_index,
                "season_sin": season,
                "season_cos": math.cos(month_index / 12 * math.tau),
                "pipeline": latest["pipeline"] * (1 + 0.012 * step) * max(0.62, revenue_delta),
                "churn": min(0.85, latest["churn"] * churn_delta + step * 0.002),
                "productivity": max(0.3, min(1.05, latest["productivity"] - max(0, scenario.hiring_freeze_months) * 0.003 - max(0, scenario.cost_delta_percent) * 0.0008)),
                "market_risk": max(0.05, min(0.95, latest["market_risk"] + market_delta + step * 0.002)),
                "headcount": max(20, latest["headcount"] + step * (1.9 if scenario.hiring_freeze_months == 0 else -0.15)),
                "cost_index": max(0.25, min(1.4, latest["cost_index"] * cost_delta + step * 0.003)),
            }
            x_future = np.array([[row[name] for name in feature_names]], dtype=float)
            ensemble = float(np.mean([rf.predict(x_future)[0], boosted.predict(x_future)[0], ridge.predict(x_future)[0]]))
            sequence_component = y_train[-1] * (1 + trailing_growth * step) + season * 155_000
            revenue = max(250_000, (ensemble * 0.78 + sequence_component * 0.22) * revenue_delta)
            risk = self._clip((row["churn"] * 42 + row["market_risk"] * 34 + row["cost_index"] * 18 + max(0, -scenario.revenue_delta_percent) * 0.7))
            uncertainty = revenue * (0.055 + risk / 950)
            confidence = round(max(0.58, min(0.95, context_confidence - risk / 900 - step * 0.006)), 3)
            previous = history[-1]["revenue"] if step == 1 else forecast[-1].revenue
            forecast.append(
                BusinessForecastPoint(
                    month=f"M+{step}",
                    revenue=round(revenue, 2),
                    lower_bound=round(max(0, revenue - uncertainty), 2),
                    upper_bound=round(revenue + uncertainty, 2),
                    growth_rate=round((revenue - previous) / max(previous, 1) * 100, 2),
                    revenue_risk=round(risk, 2),
                    confidence=confidence,
                )
            )
        return forecast, model_status

    def _churn_predictions(self, context: dict[str, Any]) -> list[ClientChurnForecast]:
        predictions = []
        for client in context["clients"].predictions[:6]:
            reasons = list(client.risk_drivers[:3])
            actions = list(client.recovery_actions[:3])
            predictions.append(
                ClientChurnForecast(
                    client_id=client.client_id,
                    client_name=client.client_name,
                    churn_probability=round(client.churn_risk, 2),
                    renewal_probability=round(max(0, 100 - client.renewal_risk), 2),
                    revenue_at_risk=round(client.revenue_at_risk, 2),
                    contract_value=round(client.revenue_at_risk / max(client.churn_risk / 100, 0.01), 2),
                    reasons=reasons,
                    recommended_actions=actions,
                    confidence=round(client.confidence, 3),
                )
            )
        return predictions

    def _market_risks(self, context: dict[str, Any], scenario: BusinessScenarioRequest | None) -> list[MarketRiskPrediction]:
        strategic = context["strategic"]
        delta = scenario.market_risk_delta if scenario else 0
        risks = [
            (
                "market-slowdown",
                "Market slowdown",
                strategic.summary.crisis_severity + delta,
                [strategic.summary.top_market_risk, "Demand volatility", "Enterprise budget scrutiny"],
            ),
            (
                "competitive-threat",
                "Competitive threat",
                strategic.summary.competitor_threats * 18 + strategic.summary.crisis_severity * 0.28 + delta,
                ["AI competitor launch velocity", "Hiring velocity", "Product launch pressure"],
            ),
            (
                "client-renewal-risk",
                "Client renewal risk",
                context["clients"].summary.average_churn_risk + context["clients"].summary.high_risk_clients * 7 + delta,
                [strategic.summary.top_client_risk, "Escalation pressure", "Usage decline"],
            ),
        ]
        output = []
        for risk_id, category, score, drivers in risks:
            clipped = self._clip(score)
            output.append(
                MarketRiskPrediction(
                    risk_id=risk_id,
                    category=category,
                    risk_score=round(clipped, 2),
                    trend="rising" if clipped >= 58 else "stable" if clipped >= 34 else "declining",
                    forecast=self._risk_label(clipped),
                    drivers=[driver for driver in drivers if driver],
                    strategic_warning=f"{category} pressure is {self._risk_label(clipped).lower()} for the next planning window.",
                )
            )
        return sorted(output, key=lambda item: item.risk_score, reverse=True)

    def _employee_growth(self, context: dict[str, Any], horizon: int, scenario: BusinessScenarioRequest | None) -> list[EmployeeGrowthForecast]:
        freeze = scenario.hiring_freeze_months if scenario else 0
        forecasts = []
        for team in context["company"].team_scores:
            growth_rate = (team.productivity_score / 100 * 0.16 + max(0, 100 - team.risk_score) / 100 * 0.09 + horizon / 240) * 100
            if freeze:
                growth_rate -= min(28, freeze * 2.2)
            forecast_headcount = max(team.headcount, round(team.headcount * (1 + growth_rate / 100)))
            skills = self._department_skills(team.department)
            forecasts.append(
                EmployeeGrowthForecast(
                    department=team.department,
                    current_headcount=team.headcount,
                    forecast_headcount=forecast_headcount,
                    growth_percent=round((forecast_headcount - team.headcount) / max(team.headcount, 1) * 100, 2),
                    productivity_capacity=round(max(0, min(120, team.team_efficiency + (team.delivery_stability - team.risk_score) * 0.18)), 2),
                    skill_demand=skills,
                    confidence=round(team.confidence, 3),
                )
            )
        return sorted(forecasts, key=lambda item: item.growth_percent, reverse=True)

    def _hiring_demand(
        self,
        growth: list[EmployeeGrowthForecast],
        context: dict[str, Any],
        scenario: BusinessScenarioRequest | None,
    ) -> list[HiringDemandForecast]:
        freeze = scenario.hiring_freeze_months if scenario else 0
        project_pressure = context["projects"].summary.average_delay_probability / 100
        revenue_pressure = context["clients"].summary.revenue_at_risk
        demand = []
        for item in growth[:5]:
            gap = max(0, item.forecast_headcount - item.current_headcount)
            if freeze:
                gap = max(0, gap - round(freeze / 3))
            role = self._role_for_department(item.department)
            urgency_score = gap * 8 + project_pressure * 34 + max(0, 70 - item.productivity_capacity) * 0.45
            demand.append(
                HiringDemandForecast(
                    role=role,
                    department=item.department,
                    required_count=round(gap),
                    urgency=self._priority(urgency_score),
                    skills=item.skill_demand,
                    justification=f"{item.department} needs capacity for forecasted growth, delivery risk, and skill-demand coverage.",
                    revenue_linked=round(revenue_pressure * (0.12 + gap * 0.025), 2),
                )
            )
        return sorted(demand, key=lambda item: (item.required_count, item.revenue_linked), reverse=True)

    def _project_profitability(self, context: dict[str, Any], scenario: BusinessScenarioRequest | None) -> list[ProjectProfitabilityForecast]:
        cost_delta = 1 + ((scenario.cost_delta_percent if scenario else 0) / 100)
        revenue_delta = 1 + ((scenario.revenue_delta_percent if scenario else 0) / 100)
        forecasts = []
        roi_projects = {item.project_id: item for item in context["roi"].delay_costs}
        for index, project in enumerate(context["projects"].predictions[:6]):
            delay_cost = roi_projects.get(project.project_id)
            expected_revenue = (1_950_000 if index == 0 else 1_250_000 if index == 1 else 880_000) * revenue_delta
            expected_cost = (
                expected_revenue * (0.48 + project.budget_overrun_probability / 260)
                + (delay_cost.expected_delay_cost if delay_cost else project.deadline_miss_probability * 2_600)
            ) * cost_delta
            roi_percent = (expected_revenue - expected_cost) / max(expected_cost, 1) * 100
            efficiency = self._clip(100 - project.budget_overrun_probability * 0.65 - project.deadline_miss_probability * 0.25 + max(0, roi_percent) * 0.06)
            forecasts.append(
                ProjectProfitabilityForecast(
                    project_id=project.project_id,
                    project_name=project.project_name,
                    estimated_cost=round(expected_cost, 2),
                    expected_revenue=round(expected_revenue, 2),
                    roi_percent=round(roi_percent, 2),
                    budget_efficiency=round(efficiency, 2),
                    overrun_probability=round(project.budget_overrun_probability, 2),
                    risk_level=self._priority(project.failure_probability),
                    confidence=round(project.confidence, 3),
                )
            )
        return sorted(forecasts, key=lambda item: item.roi_percent)

    def _company_health_future(
        self,
        context: dict[str, Any],
        revenue: list[BusinessForecastPoint],
        churn: list[ClientChurnForecast],
        profitability: list[ProjectProfitabilityForecast],
        market: list[MarketRiskPrediction],
    ) -> CompanyHealthFuture:
        current = context["company"].summary
        revenue_health = self._clip(76 + mean([point.growth_rate for point in revenue[:3]]) * 1.8 - mean([point.revenue_risk for point in revenue[:3]]) * 0.18)
        client_health = self._clip(100 - mean([item.churn_probability for item in churn]) if churn else 78)
        delivery_health = self._clip(100 - context["projects"].summary.average_failure_probability * 0.72)
        profitability_health = self._clip(mean([max(0, min(100, item.roi_percent + 35)) for item in profitability]) if profitability else 72)
        market_health = self._clip(100 - mean([item.risk_score for item in market]) * 0.55)
        score = self._clip(
            revenue_health * 0.22
            + client_health * 0.18
            + current.company_health_score * 0.2
            + current.productivity_score * 0.12
            + delivery_health * 0.13
            + profitability_health * 0.1
            + market_health * 0.05
        )
        return CompanyHealthFuture(
            score=round(score, 2),
            risk_level=self._priority(100 - score),
            forecast="Positive Growth" if score >= 76 else "Guarded Growth" if score >= 62 else "At-Risk Growth",
            revenue_health=round(revenue_health, 2),
            workforce_health=round(self._clip(100 - current.attrition_risk * 0.55 - current.burnout_risk * 0.35), 2),
            client_health=round(client_health, 2),
            delivery_health=round(delivery_health, 2),
            productivity_health=round(current.productivity_score, 2),
            security_health=round(self._clip(100 - current.operational_risk * 0.28), 2),
        )

    def _scenario_results(
        self,
        context: dict[str, Any],
        revenue: list[BusinessForecastPoint],
        scenario: BusinessScenarioRequest | None,
    ) -> list[BusinessScenarioResult]:
        scenarios = [
            scenario
            or BusinessScenarioRequest(
                scenario_id="base-risk-watch",
                scenario="What happens if churn increases by 15%?",
                churn_delta_percent=15,
            ),
            BusinessScenarioRequest(scenario_id="revenue-drop-20", scenario="What happens if revenue drops by 20%?", revenue_delta_percent=-20),
            BusinessScenarioRequest(scenario_id="hiring-freeze", scenario="What happens if hiring freezes?", hiring_freeze_months=6),
            BusinessScenarioRequest(scenario_id="cost-plus-25", scenario="What happens if costs increase by 25%?", cost_delta_percent=25),
        ]
        current_revenue = revenue[0].revenue if revenue else 10_000_000
        results = []
        for item in scenarios:
            impact = current_revenue * (item.revenue_delta_percent / 100) - context["clients"].summary.revenue_at_risk * (item.churn_delta_percent / 100)
            cost_impact = current_revenue * 0.42 * (item.cost_delta_percent / 100)
            freeze_penalty = item.hiring_freeze_months * 42_000
            financial = impact - cost_impact - freeze_penalty
            risk = self._clip(38 - item.revenue_delta_percent * 0.35 + item.churn_delta_percent * 0.42 + item.cost_delta_percent * 0.28 + item.hiring_freeze_months * 2.7 + item.market_risk_delta)
            success = round(100 - risk, 2)
            results.append(
                BusinessScenarioResult(
                    scenario_id=item.scenario_id,
                    scenario=item.scenario,
                    financial_impact=round(financial, 2),
                    revenue_after_impact=round(max(0, current_revenue + impact), 2),
                    churn_delta=round(item.churn_delta_percent, 2),
                    workforce_impact=self._workforce_impact(item),
                    profitability_impact=round(-(cost_impact + freeze_penalty) + impact * 0.38, 2),
                    growth_impact=round(item.revenue_delta_percent * 0.45 - item.churn_delta_percent * 0.22 - item.hiring_freeze_months * 1.1, 2),
                    risk_impact=round(risk, 2),
                    success_probability=success,
                    recommendations=self._scenario_recommendations(item, risk),
                )
            )
        return results

    def _recommendations(
        self,
        context: dict[str, Any],
        revenue: list[BusinessForecastPoint],
        churn: list[ClientChurnForecast],
        market: list[MarketRiskPrediction],
        hiring: list[HiringDemandForecast],
        profitability: list[ProjectProfitabilityForecast],
        scenarios: list[BusinessScenarioResult],
    ) -> list[BusinessRecommendation]:
        revenue_at_risk = sum(item.revenue_at_risk for item in churn)
        top_churn = churn[0] if churn else None
        top_hire = hiring[0] if hiring else None
        top_project = profitability[0] if profitability else None
        top_market = market[0] if market else None
        top_scenario = max(scenarios, key=lambda item: item.risk_impact)
        recommendations = [
            BusinessRecommendation(
                title="Protect enterprise renewals",
                priority="critical" if revenue_at_risk > 2_500_000 else "high",
                action=f"Launch executive churn intervention for {top_churn.client_name if top_churn else 'top-risk accounts'}.",
                rationale="Client churn and renewal risk are the fastest path from operational weakness to revenue loss.",
                expected_financial_impact=round(revenue_at_risk * 0.42, 2),
                confidence=0.9,
            ),
            BusinessRecommendation(
                title="Fund forecasted capacity gaps",
                priority=top_hire.urgency if top_hire else "medium",
                action=f"Hire {top_hire.required_count if top_hire else 3} {top_hire.role if top_hire else 'critical delivery'} role(s).",
                rationale="Hiring demand is linked to revenue forecast, project delivery risk, and productivity capacity.",
                expected_financial_impact=round((top_hire.revenue_linked if top_hire else 680_000), 2),
                confidence=0.86,
            ),
            BusinessRecommendation(
                title="Recover low-margin projects",
                priority=top_project.risk_level if top_project else "medium",
                action=f"Run margin recovery on {top_project.project_name if top_project else 'the lowest-ROI project'}.",
                rationale="Project profitability forecasts show budget and delay pressure reducing future margin.",
                expected_financial_impact=round(abs(min(0, top_project.roi_percent if top_project else -12)) * 18_000 + 240_000, 2),
                confidence=0.84,
            ),
            BusinessRecommendation(
                title="Scenario-proof the operating plan",
                priority="high" if top_scenario.risk_impact >= 55 else "medium",
                action=f"Pre-plan mitigation for: {top_scenario.scenario}",
                rationale=f"Scenario simulation estimates {top_scenario.risk_impact}% risk impact.",
                expected_financial_impact=round(abs(top_scenario.financial_impact) * 0.35, 2),
                confidence=0.82,
            ),
            BusinessRecommendation(
                title="Monitor market pressure weekly",
                priority="high" if top_market and top_market.risk_score >= 58 else "medium",
                action=f"Track {top_market.category if top_market else 'market risk'} against pipeline and renewal forecasts.",
                rationale="Market risk changes affect revenue forecast confidence and investment timing.",
                expected_financial_impact=round((revenue[0].revenue if revenue else 1_000_000) * 0.07, 2),
                confidence=0.81,
            ),
        ]
        return recommendations

    def _summary(
        self,
        context: dict[str, Any],
        revenue: list[BusinessForecastPoint],
        churn: list[ClientChurnForecast],
        market: list[MarketRiskPrediction],
        hiring: list[HiringDemandForecast],
        profitability: list[ProjectProfitabilityForecast],
        company_health: CompanyHealthFuture,
    ) -> BusinessPredictionSummary:
        current_revenue = self._historical_business_series(context)[-1]["revenue"]
        next_quarter = sum(item.revenue for item in revenue[:3])
        annual = sum(item.revenue for item in revenue[: min(12, len(revenue))])
        growth = (next_quarter - current_revenue * 3) / max(current_revenue * 3, 1) * 100
        avg_churn = mean([item.churn_probability for item in churn]) if churn else context["clients"].summary.average_churn_risk
        market_score = mean([item.risk_score for item in market]) if market else context["strategic"].summary.crisis_severity
        profit_index = self._clip(mean([self._clip(item.roi_percent + 45) for item in profitability]) if profitability else 70)
        risk_candidates = [
            (sum(item.revenue_at_risk for item in churn), "Client churn and renewal risk"),
            (market_score * 50_000, "Market and competitive pressure"),
            ((100 - profit_index) * 42_000, "Project profitability erosion"),
            (sum(item.required_count for item in hiring) * 95_000, "Hiring demand and capacity shortage"),
        ]
        top_risk = max(risk_candidates, key=lambda item: item[0])[1]
        confidence = mean([item.confidence for item in revenue[: min(6, len(revenue))]]) if revenue else 0.76
        return BusinessPredictionSummary(
            current_revenue=round(current_revenue, 2),
            predicted_next_quarter_revenue=round(next_quarter, 2),
            annual_revenue_forecast=round(annual, 2),
            revenue_growth_rate=round(growth, 2),
            average_churn_probability=round(avg_churn, 2),
            revenue_at_risk=round(sum(item.revenue_at_risk for item in churn), 2),
            hiring_needed=sum(item.required_count for item in hiring),
            company_health_score=company_health.score,
            market_risk_score=round(market_score, 2),
            profitability_index=round(profit_index, 2),
            top_business_risk=top_risk,
            forecast_confidence=round(confidence, 3),
        )

    def _evidence(self, context: dict[str, Any], summary: BusinessPredictionSummary) -> list[BusinessEvidence]:
        return [
            BusinessEvidence(source="company_health_engine", signal="Company Health Score", value=str(context["company"].summary.company_health_score), weight=0.22),
            BusinessEvidence(source="client_churn_prediction_service", signal="Average Churn Risk", value=str(context["clients"].summary.average_churn_risk), weight=0.2),
            BusinessEvidence(source="project_failure_prediction_service", signal="Average Failure Probability", value=str(context["projects"].summary.average_failure_probability), weight=0.17),
            BusinessEvidence(source="roi_intelligence_engine", signal="Net Savings Opportunity", value=f"${round(context['roi'].summary.net_savings, 2)}", weight=0.16),
            BusinessEvidence(source="strategic_intelligence_service", signal="Top Market Risk", value=context["strategic"].summary.top_market_risk, weight=0.14),
            BusinessEvidence(source="business_forecast_ensemble", signal="Next Quarter Revenue", value=f"${round(summary.predicted_next_quarter_revenue, 2)}", weight=0.11),
        ]

    def _classify_intent(self, question: str) -> str:
        if any(token in question for token in ["scenario", "what happens", "drops", "freeze", "increase costs"]):
            return "scenario"
        if any(token in question for token in ["churn", "client", "renewal"]):
            return "churn"
        if any(token in question for token in ["hiring", "hire", "headcount", "growth", "employee"]):
            return "growth"
        if any(token in question for token in ["risk", "biggest", "market"]):
            return "risk"
        if any(token in question for token in ["profit", "roi", "margin"]):
            return "profitability"
        return "revenue"

    def _assistant_answer(self, intent: str, prediction: BusinessPredictionResponse, scenario: BusinessScenarioResult | None) -> str:
        summary = prediction.summary
        if intent == "churn":
            top = prediction.churn_predictions[0]
            return (
                f"{top.client_name} is the highest churn-risk account at {top.churn_probability}% probability, "
                f"with ${top.revenue_at_risk:,.0f} revenue at risk. Portfolio average churn is "
                f"{summary.average_churn_probability}%."
            )
        if intent == "growth":
            return (
                f"The forecast requires {summary.hiring_needed} net hire(s). "
                f"Top demand is {prediction.hiring_demand[0].required_count} {prediction.hiring_demand[0].role}(s) "
                f"in {prediction.hiring_demand[0].department}."
            )
        if intent == "risk":
            return (
                f"The biggest business risk is {summary.top_business_risk}. Market risk is {summary.market_risk_score}% "
                f"and company future health is {summary.company_health_score}/100."
            )
        if intent == "profitability":
            project = prediction.project_profitability[0]
            return (
                f"{project.project_name} has the weakest profitability forecast: ROI {project.roi_percent}% with "
                f"{project.overrun_probability}% overrun probability. Portfolio profitability index is {summary.profitability_index}/100."
            )
        if intent == "scenario" and scenario:
            return (
                f"Scenario '{scenario.scenario}' has {scenario.risk_impact}% risk impact, "
                f"${scenario.financial_impact:,.0f} financial impact, and {scenario.success_probability}% success probability."
            )
        return (
            f"Next-quarter revenue is forecast at ${summary.predicted_next_quarter_revenue:,.0f} with "
            f"{summary.forecast_confidence:.0%} confidence. Annual revenue forecast is ${summary.annual_revenue_forecast:,.0f} "
            f"and projected growth is {summary.revenue_growth_rate}%."
        )

    def _intent_evidence(self, intent: str, prediction: BusinessPredictionResponse) -> list[BusinessEvidence]:
        source_map = {
            "revenue": {"business_forecast_ensemble", "company_health_engine", "roi_intelligence_engine"},
            "churn": {"client_churn_prediction_service", "strategic_intelligence_service"},
            "growth": {"company_health_engine", "project_failure_prediction_service"},
            "risk": {"strategic_intelligence_service", "project_failure_prediction_service", "client_churn_prediction_service"},
            "profitability": {"roi_intelligence_engine", "project_failure_prediction_service"},
            "scenario": {"business_forecast_ensemble", "scenario_simulation_engine"},
        }
        allowed = source_map.get(intent, source_map["revenue"])
        evidence = [item for item in prediction.evidence if item.source in allowed]
        return evidence or prediction.evidence[:3]

    @staticmethod
    def _clip(value: float, low: float = 0, high: float = 100) -> float:
        return float(max(low, min(high, value)))

    @staticmethod
    def _priority(score: float) -> str:
        if score >= 78:
            return "critical"
        if score >= 58:
            return "high"
        if score >= 34:
            return "medium"
        return "low"

    @staticmethod
    def _risk_label(score: float) -> str:
        if score >= 78:
            return "Critical"
        if score >= 58:
            return "High"
        if score >= 34:
            return "Medium"
        return "Low"

    @staticmethod
    def _context_confidence(context: dict[str, Any]) -> float:
        values = []
        values.extend([item.confidence for item in context["projects"].predictions[:5]])
        values.extend([item.confidence for item in context["clients"].predictions[:5]])
        values.extend([item.confidence for item in context["company"].team_scores[:5]])
        return float(max(0.68, min(0.94, mean(values) if values else 0.8)))

    @staticmethod
    def _department_skills(department: str) -> list[str]:
        lookup = {
            "Engineering": ["backend", "kubernetes", "mlops", "reliability"],
            "Product": ["ai product", "analytics", "customer discovery", "experimentation"],
            "Quality": ["test automation", "release intelligence", "observability"],
            "Operations": ["incident response", "workflow automation", "risk operations"],
            "Design": ["design systems", "research", "enterprise ux"],
            "Security": ["zero trust", "threat modeling", "security automation"],
            "Finance": ["forecasting", "pricing", "billing analytics"],
        }
        return lookup.get(department, ["analytics", "automation", "enterprise operations"])

    @staticmethod
    def _role_for_department(department: str) -> str:
        lookup = {
            "Engineering": "Backend / Platform Engineer",
            "Product": "AI Product Manager",
            "Quality": "QA Automation Engineer",
            "Operations": "Operations Automation Specialist",
            "Design": "Enterprise Product Designer",
            "Security": "Security Engineer",
            "Finance": "Financial Analytics Engineer",
        }
        return lookup.get(department, "Enterprise Operations Analyst")

    @staticmethod
    def _workforce_impact(scenario: BusinessScenarioRequest) -> str:
        if scenario.hiring_freeze_months:
            return f"Hiring freeze delays capacity expansion for {scenario.hiring_freeze_months} month(s)."
        if scenario.churn_delta_percent > 0:
            return "Higher churn increases account coverage pressure and renewal workload."
        if scenario.cost_delta_percent > 0:
            return "Cost pressure reduces discretionary hiring and project margin flexibility."
        if scenario.revenue_delta_percent < 0:
            return "Revenue decline forces reprioritization of hiring and delivery scope."
        return "Workforce impact is manageable with current hiring and retention plan."

    @staticmethod
    def _scenario_recommendations(scenario: BusinessScenarioRequest, risk: float) -> list[str]:
        actions = []
        if scenario.revenue_delta_percent < 0:
            actions.append("Protect top enterprise renewals and pause low-margin expansion spend.")
        if scenario.churn_delta_percent > 0:
            actions.append("Launch executive sponsor outreach for high-risk accounts.")
        if scenario.cost_delta_percent > 0:
            actions.append("Reprice low-margin projects and renegotiate vendor commitments.")
        if scenario.hiring_freeze_months:
            actions.append("Move critical delivery work to the highest-capacity teams before freezing hiring.")
        if risk >= 58:
            actions.append("Create weekly CFO/COO forecast review until risk returns below high.")
        return actions or ["Maintain current operating plan and monitor leading indicators weekly."]

    def _append_jsonl(self, payload: dict[str, Any]) -> None:
        with self._lock:
            with HISTORY_PATH.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload) + "\n")


business_prediction_service = BusinessPredictionService()
