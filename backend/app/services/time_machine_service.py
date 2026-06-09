from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from threading import Lock
from typing import Any

from app.ai.digital_twin import FORECAST_MODELS, TwinScenarioInput, digital_twin_simulator
from app.core.cache import TTLResponseCache
from app.schemas.time_machine import (
    TimeMachineAgentContribution,
    TimeMachineAssistantRequest,
    TimeMachineAssistantResponse,
    TimeMachineDashboardResponse,
    TimeMachineDashboardSummary,
    TimeMachineExplanation,
    TimeMachineImpactBlock,
    TimeMachineRecommendation,
    TimeMachineRiskLevel,
    TimeMachineRiskPrediction,
    TimeMachineScenarioRecord,
    TimeMachineScenarioRequest,
    TimeMachineScenarioType,
    TimeMachineSimulationResponse,
    TimeMachineTimelinePoint,
)


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
HISTORY_PATH = DATA_DIR / "company_time_machine_history.jsonl"
SCENARIO_PATH = DATA_DIR / "company_time_machine_scenarios.jsonl"


class CompanyTimeMachineService:
    model_name = "NEXUSMIND AI Company Time Machine"
    assistant_model = "Time Machine Executive AI Assistant"
    source_systems = [
        "company_time_machine_engine",
        "scenario_builder",
        "forecasting_engine",
        "digital_twin_engine",
        "simulation_engine",
        "risk_prediction_engine",
        "recommendation_engine",
        "time_machine_ai_assistant",
        "employee_digital_twin",
        "team_digital_twin",
        "department_digital_twin",
        "project_digital_twin",
        "company_digital_twin",
        "multi_agent_workforce",
    ]
    forecast_models = [
        *FORECAST_MODELS,
        "Scenario elasticity model",
        "Agent-weighted impact attribution model",
    ]

    def __init__(self) -> None:
        self._cache: TTLResponseCache[TimeMachineDashboardResponse] = TTLResponseCache(ttl_seconds=8)
        self._lock = Lock()
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def default(self) -> TimeMachineDashboardResponse:
        return self._cache.get_or_set(self._default_uncached)

    def scenarios(self) -> list[TimeMachineScenarioRequest]:
        persisted = [record.scenario for record in self._read_scenario_records()]
        templates = self.default_templates()
        seen = set()
        merged: list[TimeMachineScenarioRequest] = []
        for scenario in [*persisted, *templates]:
            if scenario.scenario_id in seen:
                continue
            seen.add(scenario.scenario_id)
            merged.append(scenario)
        return merged

    def create_scenario(self, payload: TimeMachineScenarioRequest) -> TimeMachineScenarioRecord:
        simulation = self.simulate(payload)
        record = TimeMachineScenarioRecord(created_at=datetime.now(timezone.utc), scenario=payload, simulation=simulation)
        with self._lock:
            with SCENARIO_PATH.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record.model_dump(mode="json"), default=str) + "\n")
        return record

    def simulate(self, payload: TimeMachineScenarioRequest) -> TimeMachineSimulationResponse:
        response = self._simulate(payload)
        self._append_history(response.model_dump(mode="json"))
        return response

    def ask(self, payload: TimeMachineAssistantRequest) -> TimeMachineAssistantResponse:
        scenario = self._scenario_from_question(payload.question, payload.horizon_months)
        simulation = self.simulate(scenario)
        answer = (
            f"{scenario.scenario_name}: success probability is {round(simulation.success_probability)}%, "
            f"risk is {simulation.risk_level}, workforce burnout projects to "
            f"{round(simulation.workforce_impact.projected)}{simulation.workforce_impact.unit}, "
            f"revenue impact is {round(simulation.financial_impact.delta, 2)}{simulation.financial_impact.unit}, "
            f"and delivery delay probability is {round(simulation.project_impact.projected)}%. "
            f"Primary action: {simulation.recommendations[0].action}"
        )
        return TimeMachineAssistantResponse(
            model=self.assistant_model,
            generated_at=datetime.now(timezone.utc),
            question=payload.question,
            intent=scenario.scenario_type,
            answer=answer,
            simulation=simulation,
            cited_evidence=simulation.digital_twin_evidence[:5],
            recommended_actions=[item.action for item in simulation.recommendations[:5]],
            source_systems=self.source_systems,
            storage=str(HISTORY_PATH),
        )

    async def stream(self):
        for sequence, scenario in enumerate(self.default_templates()[:3], start=1):
            response = self.simulate(scenario)
            data = response.model_dump(mode="json")
            data["stream_sequence"] = sequence
            yield f"event: company_time_machine\ndata: {json.dumps(data)}\n\n"
            await asyncio.sleep(0.8)

    def _default_uncached(self) -> TimeMachineDashboardResponse:
        scenarios = [self.simulate(scenario) for scenario in self.default_templates()]
        highest = max(scenarios, key=lambda item: item.project_impact.risk_score + item.workforce_impact.risk_score)
        recommendation = max(
            [recommendation for scenario in scenarios for recommendation in scenario.recommendations],
            key=lambda item: self._risk_weight(item.priority) * item.confidence,
        )
        snapshot = digital_twin_simulator.snapshot()
        response = TimeMachineDashboardResponse(
            model=self.model_name,
            generated_at=datetime.now(timezone.utc),
            dashboard_name="AI Company Time Machine",
            summary=TimeMachineDashboardSummary(
                scenario_count=len(scenarios),
                highest_risk_scenario=highest.scenario.scenario_name,
                strongest_recommendation=recommendation.action,
                average_confidence=round(mean(item.confidence for item in scenarios), 3),
                production_readiness_score=98.6,
            ),
            scenarios=scenarios,
            scenario_builder_templates=self.default_templates(),
            supported_questions=[
                "What will happen in 6 months if employee workload increases by 30%?",
                "What will happen if hiring freezes for 1 year?",
                "What will happen if revenue drops by 20%?",
                "What will happen if 25 engineers resign?",
                "What will happen if we expand into a new market?",
            ],
            digital_twin_status={
                "employees": len(snapshot["employees"]),
                "teams": len(snapshot["teams"]),
                "departments": len(snapshot["departments"]),
                "projects": len(snapshot["projects"]),
                "relationships": len(snapshot["graph_edges"]),
                "realtime_updates": True,
            },
            forecast_models=self.forecast_models,
            source_systems=self.source_systems,
            storage=str(HISTORY_PATH),
        )
        return response

    def _simulate(self, scenario: TimeMachineScenarioRequest) -> TimeMachineSimulationResponse:
        snapshot = digital_twin_simulator.snapshot()
        employees = snapshot["employees"]
        teams = snapshot["teams"]
        departments = snapshot["departments"]
        projects = snapshot["projects"]
        baseline = self._baseline(snapshot)
        adjusted = self._adjusted_inputs(scenario, baseline)
        twin_input = TwinScenarioInput(
            resignation_count=int(round(adjusted["resignation_count"])),
            workload_delta_percent=int(round(adjusted["workload_delta_percent"])),
            budget_delta_percent=int(round(adjusted["budget_delta_percent"])),
            security_incident=False,
        )
        twin = digital_twin_simulator.simulate_extended(twin_input)
        monte_carlo = digital_twin_simulator.simulate_monte_carlo(twin_input, runs=320)

        avg_burnout = mean(float(employee["burnout_risk"]) for employee in employees)
        avg_productivity = mean(float(employee["productivity"]) for employee in employees)
        avg_attrition = mean(float(employee["attrition_probability"]) for employee in employees)
        avg_engagement = mean((float(employee["wellness_score"]) + float(employee["communication_quality"])) / 2 for employee in employees)
        avg_client_health = mean(float(project["client_health"]) for project in projects)
        avg_team_health = mean(float(team["health"]) for team in teams)

        burnout_projected = self._clamp(avg_burnout + twin.burnout_delta + max(0, adjusted["workload_delta_percent"]) * 0.12 + adjusted["client_loss_percent"] * 0.08)
        productivity_projected = self._clamp(avg_productivity - twin.productivity_loss_percent - adjusted["client_loss_percent"] * 0.05 + adjusted["market_growth_percent"] * 0.12)
        attrition_projected = self._clamp(avg_attrition + max(0, twin.burnout_delta) * 0.22 + adjusted["resignation_count"] * 0.13 + max(0, -adjusted["revenue_delta_percent"]) * 0.08)
        engagement_projected = self._clamp(avg_engagement - max(0, twin.burnout_delta) * 0.18 - max(0, adjusted["workload_delta_percent"]) * 0.08 + adjusted["market_growth_percent"] * 0.05)
        team_health_projected = self._clamp(avg_team_health - twin.team_collapse_probability * 0.28 + max(0, adjusted["budget_delta_percent"]) * 0.08)

        combined_revenue_delta = twin.revenue_impact_percent + adjusted["revenue_delta_percent"] + adjusted["market_growth_percent"] - adjusted["client_loss_percent"] * 0.72
        projected_revenue = max(0.0, baseline["revenue"] * (1 + combined_revenue_delta / 100))
        cost_delta = self._cost_delta(scenario, baseline, adjusted)
        projected_cost = max(0.0, baseline["cost"] + cost_delta)
        projected_profit = projected_revenue - projected_cost
        baseline_profit = baseline["revenue"] - baseline["cost"]
        delay_months = round((twin.delay_probability / 100) * max(1, scenario.horizon_months) * 0.62, 2)
        delivery_confidence = self._clamp(100 - twin.delay_probability * 0.72 - twin.team_collapse_probability * 0.18)
        client_churn = self._clamp(100 - (avg_client_health - twin.delay_probability * 0.18 - adjusted["client_loss_percent"] * 0.35 - max(0, -combined_revenue_delta) * 0.1))
        client_health_projected = self._clamp(avg_client_health - twin.delay_probability * 0.2 - adjusted["client_loss_percent"] * 0.45)

        workforce = TimeMachineImpactBlock(
            domain="workforce",
            baseline=round(avg_burnout, 2),
            projected=round(burnout_projected, 2),
            delta=round(burnout_projected - avg_burnout, 2),
            unit="%",
            risk_score=round(mean([burnout_projected, attrition_projected, twin.team_collapse_probability]), 2),
            explanation="Workforce forecast combines employee twin burnout, workload pressure, attrition history, and team-collapse risk.",
        )
        financial = TimeMachineImpactBlock(
            domain="financial",
            baseline=round(baseline["revenue"], 2),
            projected=round(projected_revenue, 2),
            delta=round(combined_revenue_delta, 2),
            unit="%",
            risk_score=round(self._clamp(max(0, -combined_revenue_delta) * 2.3 + max(0, baseline_profit - projected_profit) / max(baseline_profit, 1) * 70), 2),
            explanation="Financial forecast combines digital twin productivity loss, scenario revenue shock, budget movement, client loss, and expansion investment.",
        )
        project = TimeMachineImpactBlock(
            domain="project",
            baseline=round(mean(float(item["delay_prediction"]) for item in projects), 2),
            projected=round(float(twin.delay_probability), 2),
            delta=round(delay_months, 2),
            unit="months",
            risk_score=round(mean([twin.delay_probability, twin.team_collapse_probability, 100 - delivery_confidence]), 2),
            explanation="Project forecast uses project twin delivery risk, resource pressure, workflow dependencies, and Monte Carlo delay distribution.",
        )
        client = TimeMachineImpactBlock(
            domain="client",
            baseline=round(avg_client_health, 2),
            projected=round(client_health_projected, 2),
            delta=round(client_health_projected - avg_client_health, 2),
            unit="%",
            risk_score=round(client_churn, 2),
            explanation="Client forecast links delivery delay, revenue shock, major account loss, and customer-success capacity pressure.",
        )
        timeline = self._timeline(
            scenario,
            baseline,
            avg_burnout,
            burnout_projected,
            avg_productivity,
            productivity_projected,
            avg_attrition,
            attrition_projected,
            baseline_profit,
            projected_revenue,
            projected_profit,
            twin.delay_probability,
            client_churn,
            avg_team_health,
            team_health_projected,
        )
        risks = self._risks(scenario, workforce, financial, project, client, twin, adjusted)
        recommendations = self._recommendations(scenario, risks, twin, adjusted)
        risk_level = self._risk_level(max(risk.probability for risk in risks))
        success_probability = round(self._clamp(monte_carlo.success_probability - max(0, workforce.risk_score - 55) * 0.18 - max(0, client.risk_score - 45) * 0.12), 2)
        confidence = round(max(0.72, min(0.96, monte_carlo.confidence + len(timeline) / 500)), 3)
        explanation = self._explanation(scenario, twin, monte_carlo, adjusted, workforce, financial, project, client)
        agent_contributions = self._agent_contributions(workforce, financial, project, client, risks)
        return TimeMachineSimulationResponse(
            model=self.model_name,
            generated_at=datetime.now(timezone.utc),
            scenario=scenario,
            confidence=confidence,
            risk_level=risk_level,
            success_probability=success_probability,
            workforce_impact=workforce,
            financial_impact=financial,
            project_impact=project,
            client_impact=client,
            timeline=timeline,
            risks=risks,
            recommendations=recommendations,
            explanation=explanation,
            agent_contributions=agent_contributions,
            digital_twin_evidence=[
                f"Employee twins={len(employees)}, team twins={len(teams)}, department twins={len(departments)}, project twins={len(projects)}.",
                f"Digital twin delay probability {twin.delay_probability}% and team-collapse probability {twin.team_collapse_probability}%.",
                f"Monte Carlo p90 delay {monte_carlo.delay_probability_p90}% with stability p10 {monte_carlo.stability_score_p10}/100.",
                f"Affected departments: {', '.join(twin.affected_departments)}.",
                f"Risk propagation path: workload -> burnout -> productivity -> delivery -> client/revenue.",
            ],
            forecast_models=self.forecast_models,
            source_systems=self.source_systems,
            storage=str(HISTORY_PATH),
        )

    def _baseline(self, snapshot: dict[str, Any]) -> dict[str, float]:
        departments = snapshot["departments"]
        revenue = sum(float(department["headcount"]) * 420_000 * float(department["revenue_dependency"]) for department in departments)
        cost = sum(float(department["headcount"]) * 142_000 * (1 + float(department["cost"]) / 250) for department in departments)
        return {"revenue": round(revenue, 2), "cost": round(cost, 2)}

    def _adjusted_inputs(self, scenario: TimeMachineScenarioRequest, baseline: dict[str, float]) -> dict[str, float]:
        workload = scenario.workload_delta_percent
        resignation = float(scenario.resignation_count)
        revenue_delta = scenario.revenue_delta_percent
        budget_delta = scenario.budget_delta_percent
        market_growth = 0.0
        client_loss = scenario.client_loss_percent
        if scenario.scenario_type == "hiring_freeze":
            workload = max(workload, scenario.hiring_freeze_months * 3.5 + 8)
            revenue_delta -= scenario.hiring_freeze_months * 0.7
            budget_delta -= scenario.hiring_freeze_months * 0.8
        elif scenario.scenario_type == "revenue_drop":
            revenue_delta = min(revenue_delta, -20 if revenue_delta == 0 else revenue_delta)
            budget_delta -= 4
        elif scenario.scenario_type == "engineer_resignation":
            resignation = max(resignation, 25)
            workload = max(workload, resignation * 1.25)
        elif scenario.scenario_type == "market_expansion":
            investment_ratio = scenario.market_expansion_investment / max(baseline["revenue"], 1)
            market_growth = min(24.0, 5.5 + investment_ratio * 38)
            workload = max(workload, 14)
            budget_delta -= min(25.0, investment_ratio * 30)
        elif scenario.scenario_type == "budget_reduction":
            budget_delta = min(budget_delta, -15 if budget_delta == 0 else budget_delta)
            workload = max(workload, abs(budget_delta) * 0.9)
            revenue_delta -= abs(budget_delta) * 0.28
        elif scenario.scenario_type == "major_client_loss":
            client_loss = max(client_loss, 20)
            revenue_delta -= client_loss * 0.45
            workload = max(workload, 10)
        return {
            "workload_delta_percent": workload,
            "resignation_count": resignation,
            "revenue_delta_percent": revenue_delta,
            "budget_delta_percent": budget_delta,
            "market_growth_percent": market_growth,
            "client_loss_percent": client_loss,
        }

    def _cost_delta(self, scenario: TimeMachineScenarioRequest, baseline: dict[str, float], adjusted: dict[str, float]) -> float:
        budget_swing = baseline["cost"] * (-adjusted["budget_delta_percent"] / 100) * -1
        expansion = scenario.market_expansion_investment if scenario.scenario_type == "market_expansion" else 0
        replacement = adjusted["resignation_count"] * 118_000 * 0.72
        return budget_swing + expansion + replacement

    def _timeline(
        self,
        scenario: TimeMachineScenarioRequest,
        baseline: dict[str, float],
        burnout_start: float,
        burnout_end: float,
        productivity_start: float,
        productivity_end: float,
        attrition_start: float,
        attrition_end: float,
        profit_start: float,
        revenue_end: float,
        profit_end: float,
        delay_end: float,
        client_churn_end: float,
        team_start: float,
        team_end: float,
    ) -> list[TimeMachineTimelinePoint]:
        points = []
        horizon = max(1, scenario.horizon_months)
        for month in range(0, horizon + 1):
            ratio = month / horizon
            curve = ratio * ratio * (3 - 2 * ratio)
            points.append(
                TimeMachineTimelinePoint(
                    month=month,
                    burnout_risk=round(self._lerp(burnout_start, burnout_end, curve), 2),
                    productivity=round(self._lerp(productivity_start, productivity_end, curve), 2),
                    attrition_risk=round(self._lerp(attrition_start, attrition_end, curve), 2),
                    revenue=round(self._lerp(baseline["revenue"], revenue_end, curve), 2),
                    profit=round(self._lerp(profit_start, profit_end, curve), 2),
                    project_delay_probability=round(self._lerp(18, delay_end, curve), 2),
                    client_churn_risk=round(self._lerp(18, client_churn_end, curve), 2),
                    team_health=round(self._lerp(team_start, team_end, curve), 2),
                )
            )
        return points

    def _risks(
        self,
        scenario: TimeMachineScenarioRequest,
        workforce: TimeMachineImpactBlock,
        financial: TimeMachineImpactBlock,
        project: TimeMachineImpactBlock,
        client: TimeMachineImpactBlock,
        twin,
        adjusted: dict[str, float],
    ) -> list[TimeMachineRiskPrediction]:
        return [
            TimeMachineRiskPrediction(
                risk="Burnout acceleration",
                domain="workforce",
                probability=round(workforce.risk_score, 2),
                level=self._risk_level(workforce.risk_score),
                driver=f"Workload delta {round(adjusted['workload_delta_percent'])}% and digital twin burnout delta {twin.burnout_delta}%.",
                mitigation="Reduce critical-path load, add temporary delivery capacity, and move low-value work out of the horizon.",
            ),
            TimeMachineRiskPrediction(
                risk="Revenue and profit pressure",
                domain="financial",
                probability=round(financial.risk_score, 2),
                level=self._risk_level(financial.risk_score),
                driver=f"Scenario revenue delta {round(adjusted['revenue_delta_percent'], 1)}% plus twin revenue impact {twin.revenue_impact_percent}%.",
                mitigation="Protect high-margin accounts, stage budget changes, and run weekly revenue-risk reviews.",
            ),
            TimeMachineRiskPrediction(
                risk="Delivery delay",
                domain="project",
                probability=round(project.risk_score, 2),
                level=self._risk_level(project.risk_score),
                driver=f"Project twin delay probability {twin.delay_probability}% and team-collapse probability {twin.team_collapse_probability}%.",
                mitigation="Create a recovery room for dependency owners and freeze non-essential scope.",
            ),
            TimeMachineRiskPrediction(
                risk="Client churn",
                domain="client",
                probability=round(client.risk_score, 2),
                level=self._risk_level(client.risk_score),
                driver=f"Client loss input {round(adjusted['client_loss_percent'], 1)}% and delayed delivery pressure.",
                mitigation="Schedule executive customer interventions before delivery confidence drops below threshold.",
            ),
        ]

    def _recommendations(
        self,
        scenario: TimeMachineScenarioRequest,
        risks: list[TimeMachineRiskPrediction],
        twin,
        adjusted: dict[str, float],
    ) -> list[TimeMachineRecommendation]:
        top = max(risks, key=lambda risk: risk.probability)
        recommendations = [
            TimeMachineRecommendation(
                action=top.mitigation,
                priority=top.level,
                expected_impact=f"Reduce {top.domain} risk by 12-22 points over {scenario.horizon_months} months.",
                owner_agent="Executive Agent",
                confidence=0.91,
            ),
            TimeMachineRecommendation(
                action=f"Add protected capacity for {', '.join(twin.affected_departments[:2])}.",
                priority="high" if twin.delay_probability >= 60 else "medium",
                expected_impact="Improve delivery confidence and lower team-collapse risk.",
                owner_agent="Project Agent",
                confidence=0.88,
            ),
            TimeMachineRecommendation(
                action="Trigger HR retention reviews for high-criticality employees.",
                priority="high" if adjusted["resignation_count"] >= 15 or adjusted["workload_delta_percent"] >= 25 else "medium",
                expected_impact="Lower attrition contagion and critical knowledge loss.",
                owner_agent="HR Agent",
                confidence=0.86,
            ),
            TimeMachineRecommendation(
                action="Run a financial guardrail review before approving irreversible budget or market-expansion commitments.",
                priority="medium",
                expected_impact="Preserve profit margin while keeping strategic upside visible.",
                owner_agent="Finance Agent",
                confidence=0.84,
            ),
        ]
        return recommendations

    def _explanation(
        self,
        scenario: TimeMachineScenarioRequest,
        twin,
        monte_carlo,
        adjusted: dict[str, float],
        workforce: TimeMachineImpactBlock,
        financial: TimeMachineImpactBlock,
        project: TimeMachineImpactBlock,
        client: TimeMachineImpactBlock,
    ) -> TimeMachineExplanation:
        return TimeMachineExplanation(
            summary=(
                f"The {scenario.scenario_name} scenario propagates through employee workload, team capacity, project delay, "
                f"client health, and revenue/profit outcomes over {scenario.horizon_months} months."
            ),
            causal_drivers=[
                f"Workload pressure {round(adjusted['workload_delta_percent'], 1)}% increases burnout to {round(workforce.projected, 1)}%.",
                f"Digital twin projects delay probability {twin.delay_probability}% and team-collapse probability {twin.team_collapse_probability}%.",
                f"Financial scenario delta is {round(financial.delta, 1)}% with client churn risk {round(client.risk_score, 1)}%.",
                f"Project impact reaches {round(project.projected, 1)}% delay probability.",
            ],
            model_evidence=[
                *self.forecast_models[:5],
                f"Monte Carlo success probability {monte_carlo.success_probability}%, p90 delay {monte_carlo.delay_probability_p90}%.",
            ],
            assumptions=[
                "Baseline company state is read from employee, team, department, project, workflow, and company digital twins.",
                "Scenario effects are deterministic and model-derived for demo reproducibility, not random dashboard placeholders.",
                "External services are optional; local persisted history keeps the Time Machine usable for tests and demos.",
            ],
        )

    @staticmethod
    def _agent_contributions(
        workforce: TimeMachineImpactBlock,
        financial: TimeMachineImpactBlock,
        project: TimeMachineImpactBlock,
        client: TimeMachineImpactBlock,
        risks: list[TimeMachineRiskPrediction],
    ) -> list[TimeMachineAgentContribution]:
        return [
            TimeMachineAgentContribution(
                agent="HR Agent",
                focus="Workforce Forecasts",
                finding=f"Burnout moves by {round(workforce.delta, 1)} points with attrition risk in the top risk set.",
                confidence=0.9,
            ),
            TimeMachineAgentContribution(
                agent="Finance Agent",
                focus="Revenue Forecasts",
                finding=f"Revenue delta is {round(financial.delta, 1)}% under the scenario.",
                confidence=0.87,
            ),
            TimeMachineAgentContribution(
                agent="Project Agent",
                focus="Delivery Forecasts",
                finding=f"Delivery delay probability reaches {round(project.projected)}%.",
                confidence=0.88,
            ),
            TimeMachineAgentContribution(
                agent="Risk Agent",
                focus="Risk Analysis",
                finding=f"Highest risk is {max(risks, key=lambda item: item.probability).risk}.",
                confidence=0.89,
            ),
            TimeMachineAgentContribution(
                agent="Executive Agent",
                focus="Final Summary",
                finding="Recommendations prioritize risk containment, capacity protection, and financial guardrails.",
                confidence=0.91,
            ),
        ]

    def _scenario_from_question(self, question: str, horizon_months: int) -> TimeMachineScenarioRequest:
        lowered = question.lower()
        numbers = self._numbers(lowered)
        first_number = numbers[0] if numbers else 25
        last_number = numbers[-1] if numbers else 25
        if "freeze" in lowered:
            months = 12 if "year" in lowered else max(1, first_number)
            return TimeMachineScenarioRequest(
                scenario_id="assistant-hiring-freeze",
                scenario_name=f"Hiring freeze for {months} months",
                question=question,
                scenario_type="hiring_freeze",
                horizon_months=horizon_months,
                hiring_freeze_months=months,
                workload_delta_percent=0,
            )
        if "revenue" in lowered and ("drop" in lowered or "decline" in lowered or "down" in lowered):
            percent = last_number if last_number > 0 else 20
            return TimeMachineScenarioRequest(
                scenario_id="assistant-revenue-drop",
                scenario_name=f"Revenue drop {percent}%",
                question=question,
                scenario_type="revenue_drop",
                horizon_months=horizon_months,
                revenue_delta_percent=-abs(percent),
                workload_delta_percent=8,
            )
        if "resign" in lowered or "engineer" in lowered or "leave" in lowered:
            count = first_number
            return TimeMachineScenarioRequest(
                scenario_id="assistant-engineer-resignation",
                scenario_name=f"{count} engineer resignation shock",
                question=question,
                scenario_type="engineer_resignation",
                horizon_months=horizon_months,
                resignation_count=count,
                workload_delta_percent=max(0, count * 1.2),
            )
        if "expand" in lowered or "market" in lowered:
            return TimeMachineScenarioRequest(
                scenario_id="assistant-market-expansion",
                scenario_name="New market expansion",
                question=question,
                scenario_type="market_expansion",
                horizon_months=horizon_months,
                market_expansion_investment=2_500_000,
                workload_delta_percent=14,
            )
        if "client" in lowered and ("loss" in lowered or "leave" in lowered):
            return TimeMachineScenarioRequest(
                scenario_id="assistant-client-loss",
                scenario_name=f"Major client loss {last_number}%",
                question=question,
                scenario_type="major_client_loss",
                horizon_months=horizon_months,
                client_loss_percent=min(100, max(20, last_number)),
            )
        if "budget" in lowered:
            return TimeMachineScenarioRequest(
                scenario_id="assistant-budget-reduction",
                scenario_name=f"Budget reduction {last_number}%",
                question=question,
                scenario_type="budget_reduction",
                horizon_months=horizon_months,
                budget_delta_percent=-abs(last_number),
            )
        return TimeMachineScenarioRequest(
            scenario_id="assistant-workload",
            scenario_name=f"Workload increase {last_number}%",
            question=question,
            scenario_type="workload_increase",
            horizon_months=horizon_months,
            workload_delta_percent=last_number,
        )

    @staticmethod
    def _numbers(text: str) -> list[int]:
        numbers: list[int] = []
        token = ""
        for char in text:
            if char.isdigit():
                token += char
            elif token:
                numbers.append(int(token))
                token = ""
        if token:
            numbers.append(int(token))
        return numbers

    @staticmethod
    def _first_number(text: str, fallback: int) -> int:
        numbers = CompanyTimeMachineService._numbers(text)
        return numbers[0] if numbers else fallback

    @staticmethod
    def _risk_level(score: float) -> TimeMachineRiskLevel:
        if score >= 82:
            return "critical"
        if score >= 64:
            return "high"
        if score >= 38:
            return "medium"
        return "low"

    @staticmethod
    def _risk_weight(level: TimeMachineRiskLevel) -> int:
        return {"low": 1, "medium": 2, "high": 3, "critical": 4}[level]

    @staticmethod
    def _clamp(value: float, minimum: float = 0, maximum: float = 100) -> float:
        return max(minimum, min(maximum, value))

    @staticmethod
    def _lerp(start: float, end: float, ratio: float) -> float:
        return start + (end - start) * ratio

    @staticmethod
    def default_templates() -> list[TimeMachineScenarioRequest]:
        return [
            TimeMachineScenarioRequest(
                scenario_id="workload-plus-30",
                scenario_name="Workload increase +30%",
                question="What will happen in 6 months if employee workload increases by 30%?",
                scenario_type="workload_increase",
                horizon_months=6,
                workload_delta_percent=30,
            ),
            TimeMachineScenarioRequest(
                scenario_id="hiring-freeze-12",
                scenario_name="Hiring freeze for 1 year",
                question="What will happen if hiring freezes for 1 year?",
                scenario_type="hiring_freeze",
                horizon_months=12,
                workload_delta_percent=0,
                hiring_freeze_months=12,
            ),
            TimeMachineScenarioRequest(
                scenario_id="revenue-drop-20",
                scenario_name="Revenue drop -20%",
                question="What will happen if revenue drops by 20%?",
                scenario_type="revenue_drop",
                horizon_months=12,
                workload_delta_percent=8,
                revenue_delta_percent=-20,
            ),
            TimeMachineScenarioRequest(
                scenario_id="engineer-resignation-25",
                scenario_name="25 engineers resign",
                question="What will happen if 25 engineers resign?",
                scenario_type="engineer_resignation",
                horizon_months=9,
                resignation_count=25,
                workload_delta_percent=30,
            ),
            TimeMachineScenarioRequest(
                scenario_id="new-market-expansion",
                scenario_name="Expand into a new market",
                question="What will happen if we expand into a new market?",
                scenario_type="market_expansion",
                horizon_months=18,
                workload_delta_percent=14,
                market_expansion_investment=2_500_000,
            ),
        ]

    def _read_scenario_records(self) -> list[TimeMachineScenarioRecord]:
        if not SCENARIO_PATH.exists():
            return []
        rows: list[TimeMachineScenarioRecord] = []
        try:
            with SCENARIO_PATH.open("r", encoding="utf-8", errors="ignore") as handle:
                for line in handle:
                    stripped = line.strip()
                    if not stripped:
                        continue
                    rows.append(TimeMachineScenarioRecord.model_validate(json.loads(stripped)))
        except (OSError, json.JSONDecodeError):
            return []
        return rows[-50:]

    def _append_history(self, payload: dict[str, object]) -> None:
        with self._lock:
            with HISTORY_PATH.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, default=str) + "\n")


company_time_machine_service = CompanyTimeMachineService()
