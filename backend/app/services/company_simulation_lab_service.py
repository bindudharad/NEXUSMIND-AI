from __future__ import annotations

import asyncio
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from threading import Lock

from app.ai.digital_twin import TwinScenarioInput, digital_twin_simulator
from app.core.cache import TTLResponseCache
from app.schemas.company_simulation_lab import (
    CompanySimulationAssistantRequest,
    CompanySimulationAssistantResponse,
    CompanySimulationLabRequest,
    CompanySimulationLabResponse,
    CompanySimulationScenarioRequest,
    EmployeeMovementFrame,
    MultiFutureBranch,
    ProjectHealthFrame,
    RevenueEvolutionPoint,
    RiskPropagationStep,
    ScenarioComparisonItem,
    ScenarioSimulationResult,
    ShadowCompanyStage,
    SimulationAgentContribution,
    SimulationDashboardSummary,
    SimulationImpactVector,
    SimulationMetricForecast,
    SimulationRecommendation,
    SimulationRiskHeatmapItem,
    TeamStressFrame,
)
from app.services.business_prediction_service import business_prediction_service
from app.services.company_health_service import company_health_service
from app.services.project_failure_service import project_failure_service
from app.services.roi_service import roi_intelligence_service


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
HISTORY_PATH = DATA_DIR / "company_simulation_lab_history.jsonl"


class CompanySimulationLabService:
    model_name = "NEXUSMIND AI Company Simulation Lab"
    assistant_model = "AI Simulation Assistant"
    source_systems = [
        "simulation_engine",
        "decision_engine",
        "forecasting_engine",
        "impact_analysis_engine",
        "risk_analysis_engine",
        "scenario_management_engine",
        "recommendation_engine",
        "ai_simulation_assistant",
        "digital_twin",
        "employee_digital_twin",
        "team_digital_twin",
        "department_digital_twin",
        "project_digital_twin",
        "company_digital_twin",
        "live_company_visualization_engine",
        "employee_movement_visualizer",
        "team_stress_evolution_engine",
        "project_health_visualization_engine",
        "risk_propagation_engine",
        "shadow_company_visualization",
        "multi_future_engine",
        "ai_agent_council",
        "business_prediction_engine",
        "project_failure_prediction",
        "roi_forecasting",
        "company_simulation_lab_history_jsonl",
    ]
    forecast_models = [
        "RandomForest scenario impact model",
        "XGBoost risk model",
        "Prophet trend adapter",
        "LSTM sequence forecaster",
        "Monte Carlo digital twin simulator",
    ]

    def __init__(self) -> None:
        self._cache: TTLResponseCache[CompanySimulationLabResponse] = TTLResponseCache(ttl_seconds=8)
        self._lock = Lock()
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def run(self, payload: CompanySimulationLabRequest | None = None) -> CompanySimulationLabResponse:
        if payload is None:
            return self._cache.get_or_set(lambda: self._run_uncached(self.default_request()))
        return self._run_uncached(payload)

    def simulate(self, payload: CompanySimulationScenarioRequest) -> CompanySimulationLabResponse:
        return self._run_uncached(
            CompanySimulationLabRequest(
                lab_name="Single Scenario Simulation",
                horizon_months=payload.horizon_months,
                scenarios=[payload],
                compare=False,
            )
        )

    def ask(self, payload: CompanySimulationAssistantRequest) -> CompanySimulationAssistantResponse:
        intent = self._intent(payload.question.lower())
        if intent == "comparison":
            lab = self._run_uncached(
                CompanySimulationLabRequest(
                    lab_name="Assistant Scenario Comparison",
                    horizon_months=payload.horizon_months,
                    scenarios=[
                        CompanySimulationScenarioRequest(
                            scenario_id="fully-remote",
                            scenario_type="work_from_home_policy",
                            question="Compare fully remote policy.",
                            remote_days_before=5,
                            remote_days_after=5,
                            horizon_months=payload.horizon_months,
                        ),
                        CompanySimulationScenarioRequest(
                            scenario_id="hybrid-2-days",
                            scenario_type="work_from_home_policy",
                            question="Compare hybrid policy with 2 remote days.",
                            remote_days_before=5,
                            remote_days_after=2,
                            horizon_months=payload.horizon_months,
                        ),
                        CompanySimulationScenarioRequest(
                            scenario_id="office-first",
                            scenario_type="work_from_home_policy",
                            question="Compare office-first policy.",
                            remote_days_before=5,
                            remote_days_after=0,
                            horizon_months=payload.horizon_months,
                        ),
                    ],
                )
            )
        else:
            lab = self._run_uncached(
                CompanySimulationLabRequest(
                    lab_name="Assistant Scenario Simulation",
                    horizon_months=payload.horizon_months,
                    scenarios=[self._scenario_from_question(payload.question, intent, payload.horizon_months)],
                    compare=False,
                )
            )

        scenario = lab.scenarios[0] if lab.scenarios else None
        answer = self._assistant_answer(payload.question, intent, lab, scenario)
        cited = []
        if scenario:
            cited.extend(scenario.digital_twin_evidence[:4])
            cited.extend([item.driver for item in scenario.risk_heatmap[:3]])
        return CompanySimulationAssistantResponse(
            model=self.assistant_model,
            generated_at=datetime.now(timezone.utc),
            question=payload.question,
            intent=intent,
            answer=answer,
            confidence=lab.summary.average_confidence,
            scenario=scenario,
            comparison=lab.comparison,
            recommended_actions=[item.action for item in lab.executive_recommendations[:5]],
            cited_evidence=cited,
            source_systems=self.source_systems,
            storage=str(HISTORY_PATH),
        )

    async def stream(self):
        scenarios = [
            self.default_request(),
            CompanySimulationLabRequest(
                lab_name="Remote Work Pressure Simulation",
                scenarios=[
                    CompanySimulationScenarioRequest(
                        scenario_id="office-first-pressure",
                        scenario_type="work_from_home_policy",
                        question="What happens if remote work is completely removed?",
                        remote_days_before=5,
                        remote_days_after=0,
                        mode="stress",
                    )
                ],
            ),
            CompanySimulationLabRequest(
                lab_name="Cost and Capacity Stress Simulation",
                scenarios=[
                    CompanySimulationScenarioRequest(
                        scenario_id="budget-minus-20",
                        scenario_type="budget_reduction",
                        question="What happens if budget is reduced by 20%?",
                        budget_reduction_percent=20,
                    ),
                    CompanySimulationScenarioRequest(
                        scenario_id="engineer-loss-20",
                        scenario_type="employee_resignation",
                        question="What happens if 20 engineers resign?",
                        resignation_count=20,
                        resignation_seniority="senior",
                    ),
                ],
            ),
        ]
        for sequence, scenario in enumerate(scenarios, start=1):
            response = self.run(scenario)
            data = response.model_dump(mode="json")
            data["summary"]["stream_sequence"] = sequence
            yield f"event: company_simulation_lab\ndata: {json.dumps(data)}\n\n"
            await asyncio.sleep(0.8)

    def _run_uncached(self, payload: CompanySimulationLabRequest) -> CompanySimulationLabResponse:
        request = payload if payload.scenarios else payload.model_copy(update={"scenarios": self.default_request().scenarios})
        context = self._context()
        scenarios = [self._simulate_scenario(scenario, context, request.horizon_months) for scenario in request.scenarios]
        comparison = self._comparison(scenarios) if request.compare or len(scenarios) > 1 else []
        summary = self._summary(scenarios, comparison)
        executive_recommendations = self._executive_recommendations(scenarios, comparison)
        response = CompanySimulationLabResponse(
            model=self.model_name,
            generated_at=datetime.now(timezone.utc),
            lab_name=request.lab_name,
            horizon_months=request.horizon_months,
            summary=summary,
            scenarios=scenarios,
            comparison=comparison,
            executive_recommendations=executive_recommendations,
            supported_questions=[
                "What happens if work-from-home is reduced from 5 days to 2 days?",
                "What happens if remote work is completely removed?",
                "What happens if hiring freezes for 6 months?",
                "What happens if 20 engineers resign?",
                "What happens if 30 engineers resign?",
                "What happens if revenue drops 20%?",
                "What happens if we hire 50 engineers?",
                "What happens if our biggest client leaves?",
                "What happens if we open a new office?",
                "What happens if Engineering merges with Security?",
                "What happens if budget is reduced by 20%?",
                "What happens if meetings are reduced by 50%?",
                "Compare hybrid vs office-first.",
                "Which scenario is safest?",
            ],
            source_systems=self.source_systems,
            forecast_models=self.forecast_models,
            storage=str(HISTORY_PATH),
        )
        self._append_jsonl(response.model_dump(mode="json"))
        return response

    def _simulate_scenario(
        self,
        scenario: CompanySimulationScenarioRequest,
        context: dict[str, float | str],
        horizon_months: int,
    ) -> ScenarioSimulationResult:
        impact = self._impact_for_scenario(scenario, context)
        twin_input = self._twin_input(scenario, impact)
        twin = digital_twin_simulator.simulate_extended(twin_input)
        success_probability = self._success_probability(impact, twin)
        confidence = self._confidence(impact, twin, context)
        forecasts = self._forecasts(impact, twin, context, horizon_months)
        heatmap = self._risk_heatmap(scenario, impact, twin, context)
        recommendations = self._scenario_recommendations(scenario, impact, heatmap, success_probability)
        comparison_score = self._comparison_score(impact, success_probability, heatmap)
        employee_movement = self._employee_movement(scenario, impact, context)
        team_stress = self._team_stress_evolution(scenario, impact)
        project_health = self._project_health_visualization(scenario, impact, twin)
        revenue_evolution = self._revenue_evolution(impact, context, horizon_months)
        risk_path = self._risk_propagation_path(scenario, impact, heatmap, twin)
        multi_future = self._multi_future_branches(impact, success_probability, heatmap, context)
        agent_council = self._agent_council(scenario, impact, heatmap, recommendations, twin)
        shadow_stages = self._shadow_company_stages(scenario, impact, context, heatmap)
        ai_explanation = self._ai_explanation(scenario, impact, heatmap, twin)
        return ScenarioSimulationResult(
            scenario_id=scenario.scenario_id,
            scenario_type=scenario.scenario_type,
            question=scenario.question,
            executive_summary=self._executive_summary(scenario, impact, success_probability, heatmap),
            confidence=confidence,
            success_probability=success_probability,
            impact=impact,
            forecasts=forecasts,
            risk_heatmap=heatmap,
            recommendations=recommendations,
            required_actions=[item.action for item in recommendations[:3]],
            resource_adjustments=self._resource_adjustments(scenario, impact),
            staffing_changes=self._staffing_changes(scenario, impact),
            employee_movement=employee_movement,
            team_stress_evolution=team_stress,
            project_health_visualization=project_health,
            revenue_evolution=revenue_evolution,
            risk_propagation_path=risk_path,
            multi_future_branches=multi_future,
            agent_council=agent_council,
            shadow_company_stages=shadow_stages,
            ai_explanation=ai_explanation,
            visualization_engine_status="ready",
            digital_twin_evidence=[
                f"Digital twin stability score {twin.stability_score}/100.",
                f"Modeled delay probability {twin.delay_probability}% and team-collapse probability {twin.team_collapse_probability}%.",
                f"Affected departments: {', '.join(twin.affected_departments[:3])}.",
                f"Workflow impacts: {', '.join(f'{name} {risk}%' for name, risk in list(twin.workflow_impacts.items())[:3])}.",
            ],
            source_systems=self.source_systems,
            forecast_models=self.forecast_models,
            comparison_score=comparison_score,
        )

    def _context(self) -> dict[str, float | str]:
        model = digital_twin_simulator.company_model
        company = company_health_service.analyze()
        project = project_failure_service.analyze()
        roi = roi_intelligence_service.analyze()
        business = business_prediction_service.analyze()
        return {
            "productivity": mean(employee.productivity for employee in model.employees),
            "burnout": mean(employee.burnout_risk for employee in model.employees),
            "attrition": mean(employee.attrition_probability for employee in model.employees),
            "workload": mean(employee.workload for employee in model.employees),
            "collaboration": mean(team.collaboration for team in model.teams),
            "team_risk": mean(team.risk for team in model.teams),
            "headcount": sum(department.headcount for department in model.departments),
            "hiring_need": mean(department.hiring_need for department in model.departments),
            "revenue": business.summary.current_revenue,
            "roi_percent": roi.summary.roi_percent,
            "company_health": company.summary.company_health_score,
            "project_delay": project.summary.average_delay_probability,
            "project_failure": project.summary.average_failure_probability,
        }

    def _impact_for_scenario(
        self,
        scenario: CompanySimulationScenarioRequest,
        context: dict[str, float | str],
    ) -> SimulationImpactVector:
        revenue = float(context["revenue"])
        workload_pressure = max(0, float(context["workload"]) - 75) / 25
        burnout_pressure = max(0, float(context["burnout"]) - 55) / 45
        if scenario.mode == "stress":
            workload_pressure += 0.18
            burnout_pressure += 0.14
        elif scenario.mode == "optimistic":
            workload_pressure = max(0, workload_pressure - 0.12)
            burnout_pressure = max(0, burnout_pressure - 0.1)

        if scenario.scenario_type == "work_from_home_policy":
            reduction = max(0, scenario.remote_days_before - scenario.remote_days_after)
            expansion = max(0, scenario.remote_days_after - scenario.remote_days_before)
            productivity = reduction * 1.45 - max(0, reduction - 3) * 1.2 + expansion * 0.8
            happiness = -reduction * 6.0 + expansion * 3.5 - burnout_pressure * 3.0
            attrition = reduction * 3.4 + burnout_pressure * 4.0 - expansion * 1.2
            burnout = reduction * 2.2 + workload_pressure * 2.4 - expansion * 0.8
            recruitment = reduction * 5.0 - expansion * 1.4
            collaboration = reduction * 2.1 - max(0, reduction - 3) * 2.8 - expansion * 0.4
            delivery_delay = max(0, attrition * 0.24 + max(0, -collaboration) * 0.35)
            operational_risk = attrition * 0.55 + burnout * 0.4 - productivity * 0.2
            growth = productivity * 0.5 - recruitment * 0.45
            financial = revenue * (productivity * 0.004 - max(0, attrition) * 0.0025 - max(0, recruitment) * 0.0015)
            revenue_impact = revenue * (productivity * 0.0028 - max(0, attrition) * 0.0018)
        elif scenario.scenario_type == "hiring_freeze":
            months = scenario.hiring_freeze_months or 6
            productivity = -months * 0.72 - float(context["hiring_need"]) * 0.05
            happiness = -months * 0.58 - burnout_pressure * 3.0
            attrition = months * 1.7 + burnout_pressure * 5.2
            burnout = months * 2.2 + workload_pressure * 6.0
            recruitment = months * 1.25
            collaboration = -months * 0.42
            delivery_delay = months * 1.9 + float(context["project_delay"]) * 0.06
            operational_risk = months * 2.1 + float(context["project_failure"]) * 0.16
            growth = -months * 1.8
            financial = revenue * (-0.006 * months - delivery_delay * 0.0016)
            revenue_impact = revenue * (-0.0045 * months - attrition * 0.0012)
        elif scenario.scenario_type == "employee_resignation":
            total = max(1, float(context["headcount"]))
            ratio = scenario.resignation_count / total
            seniority_multiplier = 1.28 if scenario.resignation_seniority.lower() in {"senior", "lead", "critical"} else 1.0
            productivity = -ratio * 142 * seniority_multiplier
            happiness = -ratio * 58 * seniority_multiplier - burnout_pressure * 2.0
            attrition = ratio * 88 * seniority_multiplier
            burnout = ratio * 76 * seniority_multiplier + workload_pressure * 8.0
            recruitment = ratio * 95 * seniority_multiplier
            collaboration = -ratio * 64 * seniority_multiplier
            delivery_delay = ratio * 76 * seniority_multiplier + float(context["project_delay"]) * 0.12
            operational_risk = ratio * 118 * seniority_multiplier
            growth = -ratio * 86 * seniority_multiplier
            financial = revenue * (-ratio * 0.32 * seniority_multiplier)
            revenue_impact = revenue * (-ratio * 0.22 * seniority_multiplier)
        elif scenario.scenario_type == "department_restructure":
            turbulence = 9 + float(context["team_risk"]) * 0.08 + burnout_pressure * 4
            synergy = max(-4, 8 - turbulence * 0.42)
            productivity = synergy
            happiness = -turbulence * 0.65
            attrition = turbulence * 0.42
            burnout = turbulence * 0.38
            recruitment = 4.0
            collaboration = synergy * 0.9 - turbulence * 0.2
            delivery_delay = max(0, turbulence * 0.55 - synergy * 0.2)
            operational_risk = turbulence * 0.82
            growth = synergy * 0.7 - 3.2
            financial = revenue * (-0.018 - delivery_delay * 0.0012 + max(0, productivity) * 0.0018)
            revenue_impact = revenue * (productivity * 0.002 - delivery_delay * 0.002)
        elif scenario.scenario_type == "budget_reduction":
            cut = scenario.budget_reduction_percent
            productivity = -cut * 0.5 - workload_pressure * 2.0
            happiness = -cut * 0.4
            attrition = cut * 0.6 + burnout_pressure * 4.0
            burnout = cut * 0.5 + workload_pressure * 6.0
            recruitment = cut * 0.8
            collaboration = -cut * 0.2
            delivery_delay = cut * 0.46 + float(context["project_delay"]) * 0.08
            operational_risk = cut * 0.72
            growth = -cut * 0.62
            financial = revenue * (-cut / 100 * 0.09)
            revenue_impact = revenue * (-cut / 100 * 0.13)
        elif scenario.scenario_type == "hiring_growth":
            hires = scenario.hiring_count
            scale = hires / max(float(context["headcount"]), 1)
            productivity = min(24, scale * 32 - min(8, scale * 8))
            happiness = min(18, scale * 22 - burnout_pressure * 2.0)
            attrition = -min(18, scale * 20)
            burnout = -min(16, scale * 18) + max(0, hires - 80) * 0.03
            recruitment = min(42, scale * 36 + max(0, hires - 50) * 0.08)
            collaboration = -min(10, scale * 12)
            delivery_delay = max(0, float(context["project_delay"]) * 0.05 - scale * 8 + max(0, hires - 80) * 0.04)
            operational_risk = max(0, recruitment * 0.35 + max(0, -collaboration) * 0.7 - productivity * 0.25)
            growth = min(28, scale * 42)
            hiring_cost = hires * 185_000
            financial = revenue * (growth * 0.006 + productivity * 0.003) - hiring_cost
            revenue_impact = revenue * (growth * 0.0045 + productivity * 0.0025)
        elif scenario.scenario_type == "revenue_change":
            change = scenario.revenue_change_percent
            pressure = max(0, -change)
            upside = max(0, change)
            productivity = -pressure * 0.16 + upside * 0.08
            happiness = -pressure * 0.2 + upside * 0.06
            attrition = pressure * 0.35 - upside * 0.08 + burnout_pressure * 2.0
            burnout = pressure * 0.28 + workload_pressure * 2.0
            recruitment = pressure * 0.22 - upside * 0.08
            collaboration = -pressure * 0.08 + upside * 0.03
            delivery_delay = pressure * 0.18 + float(context["project_delay"]) * 0.04
            operational_risk = pressure * 0.48
            growth = change * 0.62
            financial = revenue * (change / 100)
            revenue_impact = revenue * (change / 100)
        elif scenario.scenario_type == "client_loss":
            loss = scenario.client_loss_percent
            productivity = -loss * 0.18 - workload_pressure * 1.5
            happiness = -loss * 0.22
            attrition = loss * 0.32 + burnout_pressure * 2.5
            burnout = loss * 0.25 + workload_pressure * 3.5
            recruitment = loss * 0.18
            collaboration = -loss * 0.12
            delivery_delay = loss * 0.2 + float(context["project_delay"]) * 0.05
            operational_risk = loss * 0.55
            growth = -loss * 0.68
            financial = revenue * (-loss / 100)
            revenue_impact = revenue * (-loss / 100)
        elif scenario.scenario_type == "market_expansion":
            offices = max(1, scenario.office_count)
            cost = scenario.expansion_cost_percent
            productivity = -offices * 1.2 + min(8, scenario.hiring_count * 0.04)
            happiness = min(9, offices * 1.4) - burnout_pressure * 1.8
            attrition = offices * 0.9 + burnout_pressure * 1.5
            burnout = offices * 1.4 + workload_pressure * 3.2
            recruitment = offices * 8.0 + max(0, scenario.hiring_count - 30) * 0.05
            collaboration = -offices * 1.8
            delivery_delay = offices * 1.6 + float(context["project_delay"]) * 0.04
            operational_risk = offices * 5.5 + cost * 0.24
            growth = offices * 10.0 + scenario.revenue_change_percent * 0.3
            financial = revenue * (growth * 0.005 - cost / 100 * 0.16)
            revenue_impact = revenue * (growth * 0.004)
        else:
            reduction = scenario.meeting_reduction_percent
            overcut = max(0, reduction - 60)
            productivity = reduction * 0.22 - overcut * 0.18
            happiness = reduction * 0.1 - overcut * 0.08
            attrition = -reduction * 0.08 + overcut * 0.12
            burnout = -reduction * 0.12 + overcut * 0.1
            recruitment = -reduction * 0.04
            collaboration = -reduction * 0.02 - overcut * 0.18
            delivery_delay = max(0, overcut * 0.12 - reduction * 0.03)
            operational_risk = -reduction * 0.09 + overcut * 0.22
            growth = productivity * 0.58
            financial = revenue * (productivity * 0.004 - max(0, overcut) * 0.0008)
            revenue_impact = revenue * (productivity * 0.0028)

        return SimulationImpactVector(
            productivity_change=round(productivity, 2),
            employee_happiness_change=round(happiness, 2),
            attrition_risk_change=round(attrition, 2),
            burnout_change=round(burnout, 2),
            recruitment_difficulty_change=round(recruitment, 2),
            collaboration_change=round(collaboration, 2),
            financial_impact=round(financial, 2),
            revenue_impact=round(revenue_impact, 2),
            delivery_delay_days=round(max(0, delivery_delay), 2),
            operational_risk_change=round(operational_risk, 2),
            growth_impact=round(growth, 2),
        )

    def _forecasts(
        self,
        impact: SimulationImpactVector,
        twin,
        context: dict[str, float | str],
        horizon_months: int,
    ) -> list[SimulationMetricForecast]:
        confidence = self._confidence(impact, twin, context)
        months_factor = min(1.4, max(0.6, horizon_months / 12))
        baselines = {
            "Productivity Forecast": (float(context["productivity"]), impact.productivity_change, "%", "RandomForest scenario impact model"),
            "Attrition Forecast": (float(context["attrition"]), impact.attrition_risk_change, "%", "XGBoost risk model"),
            "Burnout Forecast": (float(context["burnout"]), impact.burnout_change, "%", "LSTM sequence forecaster"),
            "Revenue Forecast": (float(context["revenue"]), impact.revenue_impact, "$", "Prophet trend adapter"),
            "Hiring Forecast": (float(context["hiring_need"]), impact.recruitment_difficulty_change, "%", "RandomForest scenario impact model"),
            "Delivery Forecast": (float(context["project_delay"]) / 5, impact.delivery_delay_days, "days", "Monte Carlo digital twin simulator"),
        }
        forecasts = []
        for metric, (baseline, delta, unit, model) in baselines.items():
            scaled_delta = delta * months_factor if unit != "$" else delta
            projected = max(0, baseline + scaled_delta)
            forecasts.append(
                SimulationMetricForecast(
                    metric=metric,
                    baseline=round(baseline, 2),
                    projected=round(projected, 2),
                    delta=round(projected - baseline, 2),
                    unit=unit,
                    confidence=confidence,
                    model=model,
                )
            )
        return forecasts

    def _risk_heatmap(
        self,
        scenario: CompanySimulationScenarioRequest,
        impact: SimulationImpactVector,
        twin,
        context: dict[str, float | str],
    ) -> list[SimulationRiskHeatmapItem]:
        rows = [
            (
                "Productivity",
                max(0, -impact.productivity_change) + max(0, impact.delivery_delay_days) * 1.2,
                "Productivity and delivery throughput shift under the scenario.",
                "Protect deep-work capacity and rebalance milestone ownership.",
            ),
            (
                "Employee Happiness",
                max(0, -impact.employee_happiness_change) * 1.6 + max(0, impact.attrition_risk_change) * 0.4,
                "Policy and workload changes affect morale and retention.",
                "Run manager check-ins and keep policy exceptions transparent.",
            ),
            (
                "Attrition",
                max(0, impact.attrition_risk_change) * 1.8 + max(0, impact.burnout_change) * 0.8,
                "Resignation probability changes based on burnout, policy friction, and capacity pressure.",
                "Prioritize retention actions for critical roles before scenario execution.",
            ),
            (
                "Financial",
                max(0, -impact.financial_impact / max(float(context["revenue"]), 1) * 1000),
                "Financial impact combines revenue pressure, delivery risk, and workforce cost exposure.",
                "Stage the decision behind CFO review gates and leading indicators.",
            ),
            (
                "Collaboration",
                max(0, -impact.collaboration_change) * 1.8 + max(0, twin.team_collapse_probability - 45) * 0.4,
                "Communication and cross-functional execution risk change under the scenario.",
                "Keep decision rituals intact and clarify team ownership boundaries.",
            ),
            (
                "Operational Risk",
                max(0, impact.operational_risk_change) * 1.5 + max(0, twin.delay_probability - 40) * 0.3,
                "Operating stability changes across workflows, departments, and project delivery.",
                "Trigger executive review when risk exceeds the high threshold.",
            ),
        ]
        heatmap = []
        for domain, raw, driver, mitigation in rows:
            score = self._clip(raw + (6 if scenario.mode == "stress" else -3 if scenario.mode == "optimistic" else 0))
            heatmap.append(
                SimulationRiskHeatmapItem(
                    domain=domain,
                    risk_score=round(score, 2),
                    risk_level=self._risk_level(score),
                    driver=driver,
                    mitigation=mitigation,
                )
            )
        return sorted(heatmap, key=lambda item: item.risk_score, reverse=True)

    def _employee_movement(
        self,
        scenario: CompanySimulationScenarioRequest,
        impact: SimulationImpactVector,
        context: dict[str, float | str],
    ) -> list[EmployeeMovementFrame]:
        baseline_headcount = int(float(context["headcount"]))
        if scenario.scenario_type == "employee_resignation":
            final_hires = max(0, round(scenario.resignation_count * 0.35))
            final_exits = scenario.resignation_count
            final_transfers = max(1, round(scenario.resignation_count * 0.18))
        elif scenario.scenario_type == "hiring_growth":
            final_hires = scenario.hiring_count
            final_exits = max(0, round(max(0, impact.attrition_risk_change) / 5))
            final_transfers = max(1, round(scenario.hiring_count * 0.12))
        elif scenario.scenario_type == "market_expansion":
            final_hires = max(8, scenario.hiring_count or scenario.office_count * 18)
            final_exits = max(0, round(max(0, impact.attrition_risk_change) / 4))
            final_transfers = max(4, scenario.office_count * 6)
        else:
            final_hires = max(0, round(max(0, -impact.attrition_risk_change) / 2))
            final_exits = max(0, round(max(0, impact.attrition_risk_change) / 2))
            final_transfers = max(0, round(abs(impact.collaboration_change) / 3))

        frames = []
        for month, label, factor in [(0, "Current Company", 0.0), (1, "Shock Applied", 0.35), (3, "Twin Rebalanced", 0.65), (6, "Future Company", 1.0)]:
            hires = round(final_hires * factor)
            exits = round(final_exits * factor)
            transfers = round(final_transfers * factor)
            net = hires - exits
            frames.append(
                EmployeeMovementFrame(
                    month=month,
                    label=label,
                    hires=hires,
                    exits=exits,
                    transfers=transfers,
                    net_headcount_change=net,
                    explanation=(
                        f"{label}: workforce changes from {baseline_headcount} by {net:+d} after applying "
                        f"{scenario.scenario_type.replace('_', ' ')} signals."
                    ),
                )
            )
        return frames

    def _team_stress_evolution(self, scenario: CompanySimulationScenarioRequest, impact: SimulationImpactVector) -> list[TeamStressFrame]:
        frames = []
        for team in digital_twin_simulator.company_model.teams:
            baseline = float(team.burnout)
            department_multiplier = 1.12 if team.department.lower() in {scenario.source_department.lower(), scenario.target_department.lower()} else 0.9
            projected = self._clip(baseline + impact.burnout_change * department_multiplier + max(0, impact.operational_risk_change) * 0.18)
            level = self._risk_level(projected)
            frames.append(
                TeamStressFrame(
                    team=team.name,
                    baseline_stress=round(baseline, 2),
                    projected_stress=round(projected, 2),
                    risk_level=level,
                    color=self._risk_color(level),
                    explanation=f"{team.name} moves from {round(baseline)} to {round(projected)} stress as the digital twin applies workload, attrition, and operating-risk pressure.",
                )
            )
        return sorted(frames, key=lambda item: item.projected_stress, reverse=True)

    def _project_health_visualization(self, scenario: CompanySimulationScenarioRequest, impact: SimulationImpactVector, twin) -> list[ProjectHealthFrame]:
        frames = []
        for project in digital_twin_simulator.company_model.projects:
            baseline = float(project.risk)
            allocation_pressure = sum(project.team_allocation.values()) / max(len(project.team_allocation), 1) / 100
            projected = self._clip(baseline + impact.delivery_delay_days * 1.4 + twin.delay_probability * 0.18 + max(0, impact.operational_risk_change) * 0.2 + allocation_pressure * 6)
            level = self._risk_level(projected)
            frames.append(
                ProjectHealthFrame(
                    project=project.name,
                    baseline_state=self._project_state(baseline),
                    projected_state=self._project_state(projected),
                    delay_days=round(max(0, project.timeline_forecast_days * 0.08 + impact.delivery_delay_days), 2),
                    risk_score=round(projected, 2),
                    color=self._risk_color(level),
                    explanation=f"{project.name} changes from {self._project_state(baseline)} to {self._project_state(projected)} as resource and delivery-risk forecasts propagate.",
                )
            )
        return sorted(frames, key=lambda item: item.risk_score, reverse=True)

    def _revenue_evolution(
        self,
        impact: SimulationImpactVector,
        context: dict[str, float | str],
        horizon_months: int,
    ) -> list[RevenueEvolutionPoint]:
        current = float(context["revenue"])
        points = []
        for month in [0, max(1, round(horizon_months * 0.25)), max(2, round(horizon_months * 0.5)), max(3, round(horizon_months * 0.75)), horizon_months]:
            factor = 0 if horizon_months == 0 else month / horizon_months
            expected = current + impact.revenue_impact * factor
            volatility = abs(impact.revenue_impact) * factor
            points.append(
                RevenueEvolutionPoint(
                    month=month,
                    current=round(current, 2),
                    best_case=round(expected + volatility * 0.45 + current * 0.018 * factor, 2),
                    expected_case=round(expected, 2),
                    worst_case=round(max(0, expected - volatility * 0.65 - current * 0.014 * factor), 2),
                )
            )
        return points

    def _risk_propagation_path(
        self,
        scenario: CompanySimulationScenarioRequest,
        impact: SimulationImpactVector,
        heatmap: list[SimulationRiskHeatmapItem],
        twin,
    ) -> list[RiskPropagationStep]:
        top_score = heatmap[0].risk_score if heatmap else 50
        event_title = {
            "employee_resignation": f"{scenario.resignation_count} engineers resign",
            "hiring_growth": f"{scenario.hiring_count} hires enter onboarding",
            "revenue_change": f"Revenue changes {scenario.revenue_change_percent:+.0f}%",
            "client_loss": f"{scenario.client_loss_percent:.0f}% client loss shock",
            "market_expansion": f"{scenario.office_count} new office expansion",
            "budget_reduction": f"Budget reduced {scenario.budget_reduction_percent:.0f}%",
            "hiring_freeze": f"Hiring freezes for {scenario.hiring_freeze_months} months",
            "meeting_reduction": f"Meetings reduced {scenario.meeting_reduction_percent:.0f}%",
            "department_restructure": "Department structure changes",
            "work_from_home_policy": "Work policy changes",
        }.get(scenario.scenario_type, scenario.scenario_type.replace("_", " ").title())
        rows = [
            ("Decision Shock", event_title, "Company Twin", top_score, "The selected scenario is applied to the current company state."),
            ("Workforce Propagation", "Company Twin", "Team Twins", self._clip(max(0, impact.burnout_change) * 2.2 + max(0, impact.attrition_risk_change) * 1.6), "Workload, attrition, and morale pressure update team stress."),
            ("Project Propagation", "Team Twins", "Project Twins", self._clip(twin.delay_probability + impact.delivery_delay_days * 2.4), "Capacity loss and dependency pressure change delivery confidence."),
            ("Financial Propagation", "Project Twins", "Revenue Forecast", self._clip(max(0, -impact.revenue_impact / 120_000) + max(0, -impact.financial_impact / 180_000)), "Delivery and client pressure alter revenue and financial exposure."),
            ("Executive Alert", "Revenue Forecast", "Executive Recommendation", self._clip(top_score + max(0, impact.operational_risk_change) * 0.4), "The AI council generates recovery actions and rollout gates."),
        ]
        return [
            RiskPropagationStep(step=index, title=title, source=source, target=target, risk_score=round(score, 2), explanation=explanation)
            for index, (title, source, target, score, explanation) in enumerate(rows, start=1)
        ]

    def _multi_future_branches(
        self,
        impact: SimulationImpactVector,
        success_probability: float,
        heatmap: list[SimulationRiskHeatmapItem],
        context: dict[str, float | str],
    ) -> list[MultiFutureBranch]:
        top_risk = heatmap[0].risk_score if heatmap else 45
        cases = [
            ("best_case", 16, 1.35, -16, 8),
            ("expected_case", 34, 1.0, 0, 0),
            ("worst_case", 12, 0.55, 24, -10),
            ("optimistic_case", 18, 1.18, -9, 5),
            ("pessimistic_case", 14, 0.72, 13, -6),
            ("ai_recommended_case", 6, 1.08, -18, 7),
        ]
        branches = []
        for name, probability, revenue_factor, risk_delta, health_delta in cases:
            risk = self._clip(top_risk + risk_delta)
            success = self._clip(success_probability - risk_delta * 0.5 + health_delta * 0.25)
            revenue_impact = impact.revenue_impact * revenue_factor
            branches.append(
                MultiFutureBranch(
                    case_name=name,
                    probability=probability,
                    success_probability=round(success, 2),
                    risk_score=round(risk, 2),
                    revenue_impact=round(revenue_impact, 2),
                    workforce_health_delta=round(health_delta - max(0, impact.burnout_change) * 0.12, 2),
                    summary=(
                        f"{name.replace('_', ' ').title()} projects {round(success)}% success, "
                        f"{round(risk)} risk, and {self._format_money(revenue_impact)} revenue movement from a "
                        f"{self._format_money(float(context['revenue']))} baseline."
                    ),
                )
            )
        return branches

    def _agent_council(
        self,
        scenario: CompanySimulationScenarioRequest,
        impact: SimulationImpactVector,
        heatmap: list[SimulationRiskHeatmapItem],
        recommendations: list[SimulationRecommendation],
        twin,
    ) -> list[SimulationAgentContribution]:
        top = heatmap[0] if heatmap else None
        first_action = recommendations[0].action if recommendations else "Gate rollout with weekly model refresh."
        return [
            SimulationAgentContribution(
                agent="HR Agent",
                role="Workforce and burnout simulation",
                finding=f"Attrition changes {impact.attrition_risk_change:+.1f}% and burnout changes {impact.burnout_change:+.1f}%.",
                recommendation="Rebalance critical work and activate retention or onboarding guardrails.",
                confidence=0.91,
                source_systems=["employee_digital_twin", "team_digital_twin", "burnout_forecast"],
            ),
            SimulationAgentContribution(
                agent="Finance Agent",
                role="Revenue and cost forecast",
                finding=f"Revenue impact is {self._format_money(impact.revenue_impact)} and financial impact is {self._format_money(impact.financial_impact)}.",
                recommendation="Place the decision behind CFO guardrails and margin thresholds.",
                confidence=0.89,
                source_systems=["revenue_forecast", "roi_forecasting", "business_prediction_engine"],
            ),
            SimulationAgentContribution(
                agent="Project Agent",
                role="Delivery and dependency forecast",
                finding=f"Delivery delay changes by {impact.delivery_delay_days:.1f} days with {twin.delay_probability}% digital-twin delay probability.",
                recommendation="Freeze unstable scope and assign project recovery owners.",
                confidence=0.9,
                source_systems=["project_digital_twin", "project_failure_prediction", "dependency_graph"],
            ),
            SimulationAgentContribution(
                agent="Security Agent",
                role="Operational control risk",
                finding=f"Operational risk changes {impact.operational_risk_change:+.1f}% and top risk is {top.domain if top else 'none'}.",
                recommendation="Preserve control, incident, and access-review capacity during the scenario.",
                confidence=0.87,
                source_systems=["security_risk_model", "operational_risk_engine", "crisis_monitor"],
            ),
            SimulationAgentContribution(
                agent="Executive Agent",
                role="Decision synthesis",
                finding=f"The simulation compares six futures and recommends the controlled branch with {round(100 - (top.risk_score if top else 40))}% residual headroom.",
                recommendation=first_action,
                confidence=0.94,
                source_systems=["executive_recommendation_engine", "multi_future_engine", "shadow_company"],
            ),
        ]

    def _shadow_company_stages(
        self,
        scenario: CompanySimulationScenarioRequest,
        impact: SimulationImpactVector,
        context: dict[str, float | str],
        heatmap: list[SimulationRiskHeatmapItem],
    ) -> list[ShadowCompanyStage]:
        workforce = int(float(context["headcount"]))
        top_risk = heatmap[0].risk_score if heatmap else 45
        baseline_health = float(context["company_health"])
        net_headcount = 0
        if scenario.scenario_type == "employee_resignation":
            net_headcount -= scenario.resignation_count
        elif scenario.scenario_type in {"hiring_growth", "market_expansion"}:
            net_headcount += scenario.hiring_count
        return [
            ShadowCompanyStage(
                stage="current_company",
                label="Current Company",
                health_score=round(baseline_health, 2),
                risk_score=round(float(context["team_risk"]), 2),
                revenue=round(float(context["revenue"]), 2),
                workforce=workforce,
                explanation="Baseline state read from the current company digital twin.",
            ),
            ShadowCompanyStage(
                stage="shadow_company",
                label="Shadow Company",
                health_score=round(self._clip(baseline_health + impact.employee_happiness_change * 0.35 - max(0, impact.burnout_change) * 0.2), 2),
                risk_score=round(self._clip(top_risk), 2),
                revenue=round(float(context["revenue"]) + impact.revenue_impact * 0.55, 2),
                workforce=max(0, workforce + round(net_headcount * 0.55)),
                explanation="Parallel virtual company after synchronization and partial scenario propagation.",
            ),
            ShadowCompanyStage(
                stage="future_company",
                label="Future Company",
                health_score=round(self._clip(baseline_health + impact.employee_happiness_change * 0.55 - max(0, impact.burnout_change) * 0.34), 2),
                risk_score=round(self._clip(top_risk + impact.operational_risk_change * 0.35), 2),
                revenue=round(float(context["revenue"]) + impact.revenue_impact, 2),
                workforce=max(0, workforce + net_headcount),
                explanation="Projected future company after the full decision branch is applied.",
            ),
        ]

    def _ai_explanation(self, scenario: CompanySimulationScenarioRequest, impact: SimulationImpactVector, heatmap: list[SimulationRiskHeatmapItem], twin) -> str:
        top = heatmap[0] if heatmap else None
        scenario_label = scenario.scenario_type.replace("_", " ")
        if scenario.scenario_type == "employee_resignation":
            driver = f"{scenario.resignation_count} resignations remove critical capacity"
        elif scenario.scenario_type == "hiring_growth":
            driver = f"{scenario.hiring_count} hires add capacity but create onboarding load"
        elif scenario.scenario_type == "revenue_change":
            driver = f"{scenario.revenue_change_percent:+.0f}% revenue movement changes investment and workload pressure"
        elif scenario.scenario_type == "client_loss":
            driver = f"{scenario.client_loss_percent:.0f}% client loss reduces revenue coverage and increases retention pressure"
        elif scenario.scenario_type == "market_expansion":
            driver = f"{scenario.office_count} new office expansion increases growth upside and operational complexity"
        else:
            driver = f"{scenario_label} changes the operating baseline"
        return (
            f"{driver}, causing productivity to move {impact.productivity_change:+.1f}%, burnout to move {impact.burnout_change:+.1f}%, "
            f"and delivery delay to change by {impact.delivery_delay_days:.1f} days. The digital twin reports {twin.delay_probability}% delay probability; "
            f"the strongest propagated risk is {top.domain if top else 'none'} at {round(top.risk_score) if top else 0}%."
        )

    def _scenario_recommendations(
        self,
        scenario: CompanySimulationScenarioRequest,
        impact: SimulationImpactVector,
        heatmap: list[SimulationRiskHeatmapItem],
        success_probability: float,
    ) -> list[SimulationRecommendation]:
        top = heatmap[0] if heatmap else None
        recommendations: list[SimulationRecommendation] = []
        if scenario.scenario_type == "work_from_home_policy":
            recommendations.append(
                SimulationRecommendation(
                    title="Prefer the hybrid policy",
                    priority="high" if impact.attrition_risk_change >= 8 else "medium",
                    action="Maintain a hybrid model and avoid abrupt office-first rollout unless retention guardrails are funded.",
                    rationale="The simulator shows productivity can improve slightly, but happiness, attrition, and recruiting risk worsen when remote flexibility is reduced sharply.",
                    expected_benefit="Balances productivity gains with lower retention and hiring risk.",
                    confidence=0.88,
                )
            )
        if scenario.scenario_type == "hiring_freeze":
            recommendations.append(
                SimulationRecommendation(
                    title="Freeze only non-critical hiring",
                    priority="high",
                    action="Create exemptions for platform, customer escalation, and security response roles during the freeze.",
                    rationale="Hiring freezes compound burnout, delay risk, and capacity pressure in delivery-critical teams.",
                    expected_benefit="Preserves delivery capacity while controlling non-critical spend.",
                    confidence=0.86,
                )
            )
        if scenario.scenario_type == "employee_resignation":
            recommendations.append(
                SimulationRecommendation(
                    title="Protect critical knowledge owners",
                    priority="critical" if impact.recruitment_difficulty_change >= 12 else "high",
                    action="Launch retention interviews, knowledge-transfer sprints, and urgent backfill planning for senior engineers.",
                    rationale="Employee loss simulation increases productivity loss, knowledge loss, delivery delay, and replacement difficulty.",
                    expected_benefit="Reduces delivery shock and protects critical organizational memory.",
                    confidence=0.9,
                )
            )
        if scenario.scenario_type == "department_restructure":
            recommendations.append(
                SimulationRecommendation(
                    title="Stage restructure with ownership map",
                    priority="medium",
                    action="Run a 30-day transition scorecard before permanently merging or splitting departments.",
                    rationale="Restructuring creates short-term turbulence and role ambiguity even when long-term synergy is possible.",
                    expected_benefit="Limits collaboration breakdown and manager handoff risk.",
                    confidence=0.83,
                )
            )
        if scenario.scenario_type == "budget_reduction":
            recommendations.append(
                SimulationRecommendation(
                    title="Protect delivery-critical budget",
                    priority="critical" if scenario.budget_reduction_percent >= 20 else "high",
                    action="Cut discretionary programs before reducing platform, security, customer escalation, or incident-response capacity.",
                    rationale="Budget reductions increase attrition, burnout, delivery, growth, and revenue exposure.",
                    expected_benefit="Contains financial pressure without creating larger operating losses.",
                    confidence=0.87,
                )
            )
        if scenario.scenario_type == "meeting_reduction":
            recommendations.append(
                SimulationRecommendation(
                    title="Reduce status meetings, not decision rituals",
                    priority="medium",
                    action="Cut recurring status meetings and protect executive decision, incident, and architecture review forums.",
                    rationale="Meeting reduction improves focus, but over-cutting damages collaboration and decision velocity.",
                    expected_benefit="Recovers focus time without creating coordination gaps.",
                    confidence=0.85,
                )
            )
        if scenario.scenario_type == "hiring_growth":
            recommendations.append(
                SimulationRecommendation(
                    title="Stage hiring into capacity waves",
                    priority="high" if scenario.hiring_count >= 50 else "medium",
                    action="Hire in two waves, attach onboarding mentors, and track productivity recovery before opening the next batch.",
                    rationale="Hiring improves delivery capacity but creates onboarding, management, equipment, and budget pressure before productivity materializes.",
                    expected_benefit="Adds capacity without overwhelming managers or cloud, license, and collaboration systems.",
                    confidence=0.87,
                )
            )
        if scenario.scenario_type == "revenue_change":
            recommendations.append(
                SimulationRecommendation(
                    title="Protect operating runway",
                    priority="critical" if scenario.revenue_change_percent <= -20 else "high",
                    action="Reforecast hiring, vendor spend, and delivery commitments before the revenue branch is approved.",
                    rationale="Revenue movement changes financial runway, project confidence, client commitments, and workforce pressure.",
                    expected_benefit="Prevents delayed cost corrections and keeps execution tied to revenue reality.",
                    confidence=0.88,
                )
            )
        if scenario.scenario_type == "client_loss":
            recommendations.append(
                SimulationRecommendation(
                    title="Activate client-loss recovery lane",
                    priority="critical" if scenario.client_loss_percent >= 20 else "high",
                    action="Launch an executive retention and replacement-revenue plan while reducing exposure in dependent projects.",
                    rationale="Client loss propagates from revenue to delivery, morale, and budget pressure.",
                    expected_benefit="Reduces churn contagion and protects revenue recovery speed.",
                    confidence=0.86,
                )
            )
        if scenario.scenario_type == "market_expansion":
            recommendations.append(
                SimulationRecommendation(
                    title="Expand through staged market gates",
                    priority="high",
                    action="Open the new office as a staged pilot with hiring, compliance, client, and operational guardrails.",
                    rationale="Market expansion creates growth upside but increases coordination, compliance, hiring, and budget complexity.",
                    expected_benefit="Captures growth while limiting operational instability.",
                    confidence=0.85,
                )
            )
        if top:
            recommendations.append(
                SimulationRecommendation(
                    title=f"Mitigate {top.domain.lower()} exposure",
                    priority=top.risk_level,
                    action=top.mitigation,
                    rationale=top.driver,
                    expected_benefit=f"Reduces the top modeled risk domain from {round(top.risk_score)}%.",
                    confidence=0.82,
                )
            )
        recommendations.append(
            SimulationRecommendation(
                title="Gate decision with measurable thresholds",
                priority="high" if success_probability < 70 else "medium",
                action="Run the scenario as a controlled pilot and monitor productivity, attrition, burnout, revenue, hiring, and delivery forecasts weekly.",
                rationale="The simulation is decision support; production rollout should be tied to live operating indicators.",
                expected_benefit="Prevents irreversible policy drift when leading indicators move against the plan.",
                confidence=0.84,
            )
        )
        return recommendations[:5]

    def _comparison(self, scenarios: list[ScenarioSimulationResult]) -> list[ScenarioComparisonItem]:
        ranked = sorted(scenarios, key=lambda item: item.comparison_score, reverse=True)
        output = []
        for index, scenario in enumerate(ranked, start=1):
            highest = scenario.risk_heatmap[0] if scenario.risk_heatmap else None
            output.append(
                ScenarioComparisonItem(
                    rank=index,
                    scenario_id=scenario.scenario_id,
                    scenario_type=scenario.scenario_type,
                    label=scenario.question,
                    score=round(scenario.comparison_score, 2),
                    success_probability=scenario.success_probability,
                    risk_level=highest.risk_level if highest else "low",
                    tradeoff_summary=(
                        f"{scenario.scenario_type.replace('_', ' ').title()} scores {round(scenario.comparison_score)} with "
                        f"{round(scenario.success_probability)}% success probability and top risk {highest.domain if highest else 'none'}."
                    ),
                )
            )
        return output

    def _summary(self, scenarios: list[ScenarioSimulationResult], comparison: list[ScenarioComparisonItem]) -> SimulationDashboardSummary:
        if not scenarios:
            return SimulationDashboardSummary(
                scenario_count=0,
                recommended_scenario="none",
                safest_scenario="none",
                highest_risk_scenario="none",
                average_confidence=0,
                decision_readiness_score=0,
                top_risk="none",
            )
        best = comparison[0] if comparison else max(scenarios, key=lambda item: item.comparison_score)
        safest = min(scenarios, key=lambda item: item.risk_heatmap[0].risk_score if item.risk_heatmap else 0)
        riskiest = max(scenarios, key=lambda item: item.risk_heatmap[0].risk_score if item.risk_heatmap else 0)
        avg_confidence = mean(item.confidence for item in scenarios)
        average_success = mean(item.success_probability for item in scenarios)
        top_risk = riskiest.risk_heatmap[0].risk_score if riskiest.risk_heatmap else 0
        readiness = self._clip(50 + avg_confidence * 30 + len(scenarios) * 1.2 + average_success * 0.2 - top_risk * 0.1)
        return SimulationDashboardSummary(
            scenario_count=len(scenarios),
            recommended_scenario=best.label if isinstance(best, ScenarioComparisonItem) else best.question,
            safest_scenario=safest.question,
            highest_risk_scenario=riskiest.question,
            average_confidence=round(avg_confidence, 3),
            decision_readiness_score=round(readiness, 2),
            top_risk=riskiest.risk_heatmap[0].domain if riskiest.risk_heatmap else "none",
        )

    def _executive_recommendations(
        self,
        scenarios: list[ScenarioSimulationResult],
        comparison: list[ScenarioComparisonItem],
    ) -> list[SimulationRecommendation]:
        if not scenarios:
            return []
        best = comparison[0] if comparison else max(scenarios, key=lambda item: item.comparison_score)
        worst = max(scenarios, key=lambda item: item.risk_heatmap[0].risk_score if item.risk_heatmap else 0)
        top_risk = worst.risk_heatmap[0] if worst.risk_heatmap else None
        return [
            SimulationRecommendation(
                title="Adopt the highest-scoring scenario",
                priority="high",
                action=f"Prioritize '{best.label if isinstance(best, ScenarioComparisonItem) else best.question}' as the safest operating decision.",
                rationale="Scenario ranking combines success probability, workforce impact, financial impact, delivery delay, and risk heatmap pressure.",
                expected_benefit=f"Decision score {round(best.score if isinstance(best, ScenarioComparisonItem) else best.comparison_score)} with monitored rollout.",
                confidence=0.88,
            ),
            SimulationRecommendation(
                title=f"Control {top_risk.domain.lower() if top_risk else 'top'} risk",
                priority=top_risk.risk_level if top_risk else "medium",
                action=top_risk.mitigation if top_risk else "Monitor top risk weekly.",
                rationale=top_risk.driver if top_risk else "The top scenario risk should determine rollout gates.",
                expected_benefit="Keeps simulation output tied to measurable executive action.",
                confidence=0.84,
            ),
            SimulationRecommendation(
                title="Use pilots before enterprise rollout",
                priority="medium",
                action="Run a controlled pilot with weekly simulation refresh before committing the operating change company-wide.",
                rationale="Digital twin forecasts should be recalibrated against live employee, delivery, and revenue signals.",
                expected_benefit="Reduces irreversible policy and operating risk.",
                confidence=0.82,
            ),
        ]

    def _twin_input(self, scenario: CompanySimulationScenarioRequest, impact: SimulationImpactVector) -> TwinScenarioInput:
        resignation_count = scenario.resignation_count if scenario.scenario_type == "employee_resignation" else round(max(0, impact.attrition_risk_change) / 6)
        workload_delta = round(impact.burnout_change + max(0, -impact.productivity_change) + max(0, impact.operational_risk_change * 0.35))
        budget_delta = -round(scenario.budget_reduction_percent) if scenario.scenario_type == "budget_reduction" else round(impact.financial_impact / 250_000)
        if scenario.scenario_type == "hiring_growth":
            resignation_count = 0
            workload_delta = round(min(35, scenario.hiring_count * 0.08) + max(0, -impact.collaboration_change))
            budget_delta = round(min(200, scenario.hiring_count * 1.4))
        elif scenario.scenario_type == "revenue_change":
            budget_delta = round(scenario.revenue_change_percent)
        elif scenario.scenario_type == "client_loss":
            budget_delta = -round(scenario.client_loss_percent)
            workload_delta = round(workload_delta + scenario.client_loss_percent * 0.3)
        elif scenario.scenario_type == "market_expansion":
            budget_delta = round(scenario.expansion_cost_percent)
            workload_delta = round(workload_delta + scenario.office_count * 5)
        return TwinScenarioInput(
            resignation_count=max(0, min(500, resignation_count)),
            workload_delta_percent=max(-50, min(150, workload_delta)),
            budget_delta_percent=max(-80, min(200, budget_delta)),
            security_incident=False,
        )

    def _success_probability(self, impact: SimulationImpactVector, twin) -> float:
        pressure = (
            max(0, impact.attrition_risk_change) * 0.72
            + max(0, impact.burnout_change) * 0.62
            + max(0, impact.operational_risk_change) * 0.58
            + max(0, impact.delivery_delay_days) * 1.4
            + twin.delay_probability * 0.28
            + twin.team_collapse_probability * 0.22
            + max(0, -impact.financial_impact / 125_000) * 0.18
        )
        upside = max(0, impact.productivity_change) * 0.42 + max(0, impact.employee_happiness_change) * 0.32 + max(0, impact.growth_impact) * 0.28
        return round(self._clip(91 - pressure + upside), 2)

    def _comparison_score(
        self,
        impact: SimulationImpactVector,
        success_probability: float,
        heatmap: list[SimulationRiskHeatmapItem],
    ) -> float:
        top_risk = heatmap[0].risk_score if heatmap else 40
        score = (
            success_probability * 0.55
            + (50 + impact.productivity_change) * 0.16
            + (50 + impact.employee_happiness_change) * 0.12
            + (50 + impact.growth_impact) * 0.08
            - top_risk * 0.18
            + max(-18, min(18, impact.financial_impact / 600_000)) * 0.09
        )
        return round(self._clip(score), 2)

    def _confidence(self, impact: SimulationImpactVector, twin, context: dict[str, float | str]) -> float:
        volatility = (
            abs(impact.productivity_change)
            + abs(impact.attrition_risk_change)
            + abs(impact.burnout_change)
            + abs(impact.operational_risk_change)
            + twin.delay_probability * 0.08
        )
        health_factor = float(context["company_health"]) / 100
        return round(max(0.62, min(0.94, 0.9 + health_factor * 0.05 - volatility / 520)), 3)

    def _executive_summary(
        self,
        scenario: CompanySimulationScenarioRequest,
        impact: SimulationImpactVector,
        success_probability: float,
        heatmap: list[SimulationRiskHeatmapItem],
    ) -> str:
        top = heatmap[0] if heatmap else None
        if scenario.scenario_type == "work_from_home_policy":
            policy = "hybrid" if scenario.remote_days_after in {2, 3} else "office-first" if scenario.remote_days_after <= 1 else "remote-heavy"
            return (
                f"{policy.title()} policy simulation projects {impact.productivity_change:+.1f}% productivity, "
                f"{impact.employee_happiness_change:+.1f}% employee happiness, and {impact.attrition_risk_change:+.1f}% attrition-risk change. "
                f"Success probability is {round(success_probability)}%; top risk is {top.domain if top else 'none'}."
            )
        return (
            f"{scenario.scenario_type.replace('_', ' ').title()} simulation projects {impact.productivity_change:+.1f}% productivity, "
            f"{impact.attrition_risk_change:+.1f}% attrition risk, ${impact.financial_impact:,.0f} financial impact, "
            f"and {impact.delivery_delay_days:.1f} delivery-delay days. Success probability is {round(success_probability)}%."
        )

    def _resource_adjustments(self, scenario: CompanySimulationScenarioRequest, impact: SimulationImpactVector) -> list[str]:
        if scenario.scenario_type == "hiring_freeze":
            return ["Exempt delivery-critical backfills.", "Move lower-priority roadmap work into deferred queue."]
        if scenario.scenario_type == "employee_resignation":
            return ["Create emergency backfill plan.", "Shift critical project ownership to low-burnout senior engineers."]
        if scenario.scenario_type == "budget_reduction":
            return ["Protect platform and security budgets.", "Delay discretionary tooling cuts until after active release milestones."]
        if scenario.scenario_type == "meeting_reduction":
            return ["Move status updates to async dashboards.", "Keep decision and incident-response meetings intact."]
        if scenario.scenario_type == "work_from_home_policy":
            return ["Pilot policy with opt-outs for retention-risk teams.", "Increase manager check-in capacity during transition."]
        if scenario.scenario_type == "hiring_growth":
            return ["Open onboarding lanes before headcount arrives.", "Reserve manager capacity and cloud, device, and license budgets."]
        if scenario.scenario_type == "revenue_change":
            return ["Rebalance roadmap commitments to the updated revenue branch.", "Tie hiring and vendor spend to monthly revenue guardrails."]
        if scenario.scenario_type == "client_loss":
            return ["Protect delivery teams tied to replacement revenue.", "Open client recovery and expansion pipeline rooms."]
        if scenario.scenario_type == "market_expansion":
            return ["Create launch pods for sales, delivery, support, security, and compliance.", "Set a 90-day kill or scale checkpoint for the new office."]
        return ["Assign transition owners.", "Keep delivery dependencies mapped weekly."]

    def _staffing_changes(self, scenario: CompanySimulationScenarioRequest, impact: SimulationImpactVector) -> list[str]:
        needed = max(0, round((max(0, impact.recruitment_difficulty_change) + max(0, impact.delivery_delay_days)) / 6))
        if scenario.scenario_type == "meeting_reduction":
            return ["No new headcount required if recovered focus time materializes."]
        if scenario.scenario_type == "hiring_growth":
            return [f"Add {scenario.hiring_count} planned hires in staged cohorts.", "Assign mentors before each cohort starts."]
        if scenario.scenario_type == "market_expansion":
            return [f"Staff {scenario.office_count} new office launch pod(s).", "Backfill central teams before local execution load increases."]
        if scenario.scenario_type == "client_loss":
            return ["Reassign account and delivery owners to replacement-revenue work.", "Protect critical client-success roles from budget cuts."]
        if needed <= 0:
            return ["No immediate staffing increase required; monitor capacity drift."]
        return [f"Plan {needed} additional critical role(s) or contractor equivalents.", "Prioritize platform, QA, DevOps, and customer escalation capacity."]

    def _assistant_answer(
        self,
        question: str,
        intent: str,
        lab: CompanySimulationLabResponse,
        scenario: ScenarioSimulationResult | None,
    ) -> str:
        if intent == "comparison" and lab.comparison:
            best = lab.comparison[0]
            return (
                f"The safest option is {best.label}. It scores {round(best.score)} with "
                f"{round(best.success_probability)}% success probability. The ranking accounts for productivity, attrition, "
                f"burnout, revenue, hiring, and delivery impact."
            )
        if not scenario:
            return "The simulation lab did not produce a scenario result."
        if scenario.scenario_type == "work_from_home_policy":
            return (
                f"Remote-work simulation: productivity changes {scenario.impact.productivity_change:+.1f}%, happiness "
                f"{scenario.impact.employee_happiness_change:+.1f}%, attrition risk {scenario.impact.attrition_risk_change:+.1f}%, "
                f"and recruiting difficulty {scenario.impact.recruitment_difficulty_change:+.1f}%. Recommendation: "
                f"{scenario.recommendations[0].action}"
            )
        return (
            f"{question} Result: {scenario.executive_summary} Recommended action: "
            f"{scenario.recommendations[0].action}"
        )

    def _scenario_from_question(self, question: str, intent: str, horizon: int) -> CompanySimulationScenarioRequest:
        lower = question.lower()
        if intent == "remote_policy":
            after = 0 if any(token in lower for token in ["removed", "remove", "completely", "office-first", "office first"]) else 2
            return CompanySimulationScenarioRequest(
                scenario_id="assistant-remote-policy",
                scenario_type="work_from_home_policy",
                question=question,
                remote_days_before=5,
                remote_days_after=after,
                horizon_months=horizon,
            )
        if intent == "hiring_freeze":
            return CompanySimulationScenarioRequest(scenario_id="assistant-hiring-freeze", scenario_type="hiring_freeze", question=question, horizon_months=horizon)
        if intent == "hiring_growth":
            count = self._extract_number(lower, default=50)
            return CompanySimulationScenarioRequest(
                scenario_id="assistant-hiring-growth",
                scenario_type="hiring_growth",
                question=question,
                hiring_count=count,
                horizon_months=horizon,
            )
        if intent == "resignation":
            count = self._extract_number(lower, default=20)
            return CompanySimulationScenarioRequest(scenario_id="assistant-resignation", scenario_type="employee_resignation", question=question, resignation_count=count, horizon_months=horizon)
        if intent == "revenue":
            percent = -abs(self._extract_number(lower, default=20)) if any(token in lower for token in ["drop", "fall", "decline", "crash", "down"]) else self._extract_number(lower, default=10)
            return CompanySimulationScenarioRequest(
                scenario_id="assistant-revenue-change",
                scenario_type="revenue_change",
                question=question,
                revenue_change_percent=percent,
                horizon_months=horizon,
            )
        if intent == "client_loss":
            percent = self._extract_number(lower, default=20)
            return CompanySimulationScenarioRequest(
                scenario_id="assistant-client-loss",
                scenario_type="client_loss",
                question=question,
                client_loss_percent=percent,
                horizon_months=horizon,
            )
        if intent == "market_expansion":
            return CompanySimulationScenarioRequest(
                scenario_id="assistant-market-expansion",
                scenario_type="market_expansion",
                question=question,
                office_count=1,
                hiring_count=max(30, self._extract_number(lower, default=50)),
                revenue_change_percent=8,
                horizon_months=horizon,
            )
        if intent == "budget":
            return CompanySimulationScenarioRequest(scenario_id="assistant-budget", scenario_type="budget_reduction", question=question, budget_reduction_percent=20, horizon_months=horizon)
        if intent == "meeting":
            return CompanySimulationScenarioRequest(scenario_id="assistant-meetings", scenario_type="meeting_reduction", question=question, meeting_reduction_percent=50, horizon_months=horizon)
        if intent == "restructure":
            return CompanySimulationScenarioRequest(scenario_id="assistant-restructure", scenario_type="department_restructure", question=question, horizon_months=horizon)
        return CompanySimulationScenarioRequest(question=question, horizon_months=horizon)

    @staticmethod
    def _intent(question: str) -> str:
        if any(token in question for token in ["compare", "safest", "best option", "hybrid vs", "office-first", "office first"]):
            return "comparison"
        if any(token in question for token in ["remote", "work from home", "wfh", "hybrid", "office"]):
            if any(token in question for token in ["new office", "open office", "new market", "market expansion", "expand"]):
                return "market_expansion"
            return "remote_policy"
        if "hiring freeze" in question or ("hiring" in question and "freeze" in question):
            return "hiring_freeze"
        if any(token in question for token in ["hire", "hiring", "add employees", "add engineers"]):
            return "hiring_growth"
        if any(token in question for token in ["resign", "leave", "key experts", "senior engineers"]):
            return "resignation"
        if any(token in question for token in ["biggest client", "largest client", "client leaves", "client loss", "lose our top client"]):
            return "client_loss"
        if any(token in question for token in ["revenue", "sales"]) and any(token in question for token in ["drop", "fall", "decline", "increase", "rise", "growth", "crash"]):
            return "revenue"
        if any(token in question for token in ["new office", "new market", "market expansion", "expand internationally", "open a new office"]):
            return "market_expansion"
        if any(token in question for token in ["budget", "cost cut", "reduced by 20"]):
            return "budget"
        if any(token in question for token in ["meeting", "meetings"]):
            return "meeting"
        if any(token in question for token in ["merge", "split", "restructure"]):
            return "restructure"
        return "remote_policy"

    @staticmethod
    def _extract_number(text: str, default: int) -> int:
        match = re.search(r"(\d+)", text)
        return int(match.group(1)) if match else default

    @staticmethod
    def default_request() -> CompanySimulationLabRequest:
        return CompanySimulationLabRequest(
            scenarios=[
                CompanySimulationScenarioRequest(
                    scenario_id="wfh-5-to-2",
                    scenario_type="work_from_home_policy",
                    question="What happens if work-from-home is reduced from 5 days to 2 days?",
                    remote_days_before=5,
                    remote_days_after=2,
                ),
                CompanySimulationScenarioRequest(
                    scenario_id="hiring-freeze-6",
                    scenario_type="hiring_freeze",
                    question="What happens if hiring freezes for 6 months?",
                    hiring_freeze_months=6,
                ),
                CompanySimulationScenarioRequest(
                    scenario_id="engineer-resignation-20",
                    scenario_type="employee_resignation",
                    question="What happens if 20 engineers resign?",
                    resignation_count=20,
                    resignation_seniority="senior",
                ),
                CompanySimulationScenarioRequest(
                    scenario_id="future-demo-engineer-resignation-30",
                    scenario_type="employee_resignation",
                    question="What happens if 30 engineers resign?",
                    resignation_count=30,
                    resignation_seniority="senior",
                    mode="stress",
                ),
                CompanySimulationScenarioRequest(
                    scenario_id="hire-50-engineers",
                    scenario_type="hiring_growth",
                    question="What happens if we hire 50 engineers?",
                    hiring_count=50,
                ),
                CompanySimulationScenarioRequest(
                    scenario_id="revenue-drop-20",
                    scenario_type="revenue_change",
                    question="What happens if revenue drops 20%?",
                    revenue_change_percent=-20,
                ),
                CompanySimulationScenarioRequest(
                    scenario_id="largest-client-leaves",
                    scenario_type="client_loss",
                    question="What happens if our biggest client leaves?",
                    client_loss_percent=20,
                ),
                CompanySimulationScenarioRequest(
                    scenario_id="new-office-expansion",
                    scenario_type="market_expansion",
                    question="What happens if we open a new office?",
                    office_count=1,
                    hiring_count=40,
                    revenue_change_percent=8,
                ),
                CompanySimulationScenarioRequest(
                    scenario_id="engineering-security-restructure",
                    scenario_type="department_restructure",
                    question="What happens if Engineering merges with Security Response?",
                    source_department="Engineering",
                    target_department="Security",
                ),
                CompanySimulationScenarioRequest(
                    scenario_id="budget-reduction-20",
                    scenario_type="budget_reduction",
                    question="What happens if budget is reduced by 20%?",
                    budget_reduction_percent=20,
                ),
                CompanySimulationScenarioRequest(
                    scenario_id="meeting-reduction-50",
                    scenario_type="meeting_reduction",
                    question="What happens if meetings are reduced by 50%?",
                    meeting_reduction_percent=50,
                ),
            ]
        )

    @staticmethod
    def _risk_level(score: float) -> str:
        if score >= 78:
            return "critical"
        if score >= 58:
            return "high"
        if score >= 34:
            return "medium"
        return "low"

    @staticmethod
    def _risk_color(level: str) -> str:
        return {
            "low": "green",
            "medium": "yellow",
            "high": "red",
            "critical": "red",
        }.get(level, "yellow")

    @staticmethod
    def _project_state(score: float) -> str:
        if score >= 78:
            return "Delayed"
        if score >= 58:
            return "At Risk"
        return "On Track"

    @staticmethod
    def _format_money(value: float) -> str:
        sign = "-" if value < 0 else ""
        absolute = abs(value)
        if absolute >= 1_000_000:
            return f"{sign}${absolute / 1_000_000:.1f}M"
        if absolute >= 1_000:
            return f"{sign}${absolute / 1_000:.0f}K"
        return f"{sign}${absolute:.0f}"

    @staticmethod
    def _clip(value: float, low: float = 0, high: float = 100) -> float:
        return max(low, min(high, float(value)))

    def _append_jsonl(self, payload: dict[str, object]) -> None:
        with self._lock:
            with HISTORY_PATH.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, default=str) + "\n")


company_simulation_lab_service = CompanySimulationLabService()
