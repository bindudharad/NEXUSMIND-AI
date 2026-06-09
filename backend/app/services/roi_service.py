from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from threading import Lock

import numpy as np

from app.core.cache import TTLResponseCache
from app.ai.roi_engine import roi_intelligence_engine
from app.schemas.roi import (
    DelayCostAnalysis,
    ExecutiveInsight,
    ProductivityLossAnalysis,
    ProjectFinancialInput,
    ReplacementCostAnalysis,
    RoiForecastPoint,
    RoiRecommendation,
    RoiResponse,
    RoiScenarioRequest,
    RoiSeverity,
    RoiSummary,
    WorkforceCostInput,
)
from app.services.project_failure_service import project_failure_service


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
HISTORY_PATH = DATA_DIR / "roi_intelligence_history.jsonl"


class RoiIntelligenceService:
    model_name = "RandomForest Workforce Economics ROI Engine"

    def __init__(self) -> None:
        self._lock = Lock()
        self._default_cache: TTLResponseCache[RoiResponse] = TTLResponseCache(ttl_seconds=8)
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def analyze(self, payload: RoiScenarioRequest | None = None) -> RoiResponse:
        if payload is None:
            return self._default_cache.get_or_set(self._analyze_default_uncached)
        return self._analyze_uncached(payload)

    def _analyze_default_uncached(self) -> RoiResponse:
        return self._analyze_uncached(self.default_request())

    def _analyze_uncached(self, payload: RoiScenarioRequest) -> RoiResponse:
        request = payload or self.default_request()
        if not request.employees or not request.projects:
            default = self.default_request()
            request = request.model_copy(
                update={
                    "employees": request.employees or default.employees,
                    "projects": request.projects or default.projects,
                }
            )
        replacement_costs = [self._replacement_cost(employee, request.retention_improvement) for employee in request.employees]
        productivity_losses = self._productivity_losses(request.employees, request)
        delay_costs = [self._delay_cost(project, request.delay_risk_reduction) for project in request.projects]
        summary, capture_confidence = self._summary(request, replacement_costs, productivity_losses, delay_costs)
        recommendations = self._recommendations(request, replacement_costs, productivity_losses, delay_costs, summary, capture_confidence)
        insights = self._executive_insights(summary, replacement_costs, productivity_losses, delay_costs)
        forecast = self._forecast(request, summary, capture_confidence)
        response = RoiResponse(
            model=self.model_name,
            generated_at=datetime.now(timezone.utc),
            horizon_months=request.horizon_months,
            replacement_costs=sorted(replacement_costs, key=lambda item: item.expected_attrition_exposure, reverse=True),
            productivity_losses=sorted(productivity_losses, key=lambda item: item.annualized_productivity_loss, reverse=True),
            delay_costs=sorted(delay_costs, key=lambda item: item.expected_delay_cost, reverse=True),
            recommendations=recommendations,
            executive_insights=insights,
            forecast=forecast,
            summary=summary,
            storage=str(HISTORY_PATH),
        )
        self._append_jsonl(response.model_dump(mode="json"))
        return response

    async def stream(self, payload: RoiScenarioRequest | None = None):
        base = payload or self.default_request()
        scenarios = [
            base,
            self._scenario_variant(base, risk_delta=0.08, intervention_delta=0.02),
            self._scenario_variant(base, risk_delta=0.15, intervention_delta=0.05),
        ]
        for sequence, scenario in enumerate(scenarios, start=1):
            response = self.analyze(scenario)
            data = response.model_dump(mode="json")
            data["summary"]["stream_sequence"] = sequence
            yield f"event: roi\ndata: {json.dumps(data)}\n\n"
            await asyncio.sleep(0.8)

    def default_request(self) -> RoiScenarioRequest:
        project_risk = project_failure_service.analyze()
        projects = [
            ProjectFinancialInput(
                project_id=prediction.project_id,
                project_name=prediction.project_name,
                team_name=prediction.team_name,
                forecasted_revenue=1_850_000 if index == 0 else 1_100_000 if index == 1 else 720_000,
                gross_margin=0.64 if index == 0 else 0.58,
                failure_probability=prediction.failure_probability / 100,
                delay_probability=prediction.deadline_miss_probability / 100,
                projected_delay_days=max(4, round(prediction.deadline_miss_probability / 5)),
                daily_burn_rate=18_500 if index == 0 else 12_400,
                delivery_penalty_per_day=5_500 if index == 0 else 3_200,
                client_churn_risk=min(0.42, prediction.operational_instability / 240),
                budget_utilization=prediction.budget_overrun_probability / 72,
                team_size=18 if index == 0 else 12,
            )
            for index, prediction in enumerate(project_risk.predictions)
        ]
        employees = [
            WorkforceCostInput(
                employee_id="emp-john",
                name="Employee John",
                role="Backend Lead",
                team_name="Development Team",
                annual_salary=156_000,
                attrition_probability=0.62,
                burnout_probability=0.82,
                productivity_score=0.54,
                stress_score=0.88,
                overtime_hours_monthly=74,
                meeting_hours_weekly=15,
                knowledge_criticality=0.9,
                billable_revenue_per_day=2_800,
                open_critical_tasks=19,
            ),
            WorkforceCostInput(
                employee_id="emp-nina",
                name="Employee Nina",
                role="QA Automation Lead",
                team_name="Development Team",
                annual_salary=128_000,
                attrition_probability=0.44,
                burnout_probability=0.68,
                productivity_score=0.63,
                stress_score=0.74,
                overtime_hours_monthly=52,
                meeting_hours_weekly=11,
                knowledge_criticality=0.72,
                billable_revenue_per_day=1_950,
                open_critical_tasks=13,
            ),
            WorkforceCostInput(
                employee_id="emp-bianca",
                name="Bianca Shah",
                role="Reliability Engineer",
                team_name="Platform Reliability",
                annual_salary=148_000,
                attrition_probability=0.24,
                burnout_probability=0.36,
                productivity_score=0.86,
                stress_score=0.42,
                overtime_hours_monthly=22,
                meeting_hours_weekly=7,
                knowledge_criticality=0.78,
                billable_revenue_per_day=2_300,
                open_critical_tasks=8,
            ),
            WorkforceCostInput(
                employee_id="emp-maya",
                name="Maya Iyer",
                role="Operations Analyst",
                team_name="Automation Team",
                annual_salary=112_000,
                attrition_probability=0.12,
                burnout_probability=0.24,
                productivity_score=0.9,
                stress_score=0.28,
                overtime_hours_monthly=10,
                meeting_hours_weekly=5,
                knowledge_criticality=0.48,
                billable_revenue_per_day=1_450,
                open_critical_tasks=4,
            ),
        ]
        return RoiScenarioRequest(employees=employees, projects=projects)

    @staticmethod
    def _replacement_cost(employee: WorkforceCostInput, retention_improvement: float) -> ReplacementCostAnalysis:
        loaded_salary = employee.annual_salary * employee.fully_loaded_multiplier
        hiring_cost = loaded_salary * 0.18 + 4_500
        training_cost = loaded_salary * (0.14 + employee.knowledge_criticality * 0.08)
        productivity_recovery_cost = loaded_salary * (0.18 + (1 - employee.productivity_score) * 0.24)
        knowledge_transfer_loss = employee.billable_revenue_per_day * (18 + 42 * employee.knowledge_criticality)
        team_disruption_cost = loaded_salary / 260 * employee.open_critical_tasks * (0.9 + employee.stress_score)
        replacement_cost = hiring_cost + training_cost + productivity_recovery_cost + knowledge_transfer_loss + team_disruption_cost
        revenue_at_risk = employee.billable_revenue_per_day * (35 + employee.open_critical_tasks * 1.6) * employee.attrition_probability
        exposure = replacement_cost * employee.attrition_probability + revenue_at_risk
        prevention_savings = exposure * retention_improvement * (0.74 + employee.burnout_probability * 0.18)
        return ReplacementCostAnalysis(
            employee_id=employee.employee_id,
            employee_name=employee.name,
            team_name=employee.team_name,
            replacement_cost=round(replacement_cost, 2),
            expected_attrition_exposure=round(exposure, 2),
            hiring_cost=round(hiring_cost, 2),
            training_cost=round(training_cost, 2),
            productivity_recovery_cost=round(productivity_recovery_cost, 2),
            knowledge_transfer_loss=round(knowledge_transfer_loss, 2),
            team_disruption_cost=round(team_disruption_cost, 2),
            revenue_at_risk=round(revenue_at_risk, 2),
            prevention_savings=round(prevention_savings, 2),
            severity=RoiIntelligenceService._severity(exposure / 5_500),
        )

    @staticmethod
    def _productivity_losses(employees: list[WorkforceCostInput], request: RoiScenarioRequest) -> list[ProductivityLossAnalysis]:
        teams: dict[str, list[WorkforceCostInput]] = defaultdict(list)
        for employee in employees:
            teams[employee.team_name].append(employee)
        losses = []
        for team_name, members in teams.items():
            monthly_loss = 0.0
            meeting_loss = 0.0
            overtime_loss = 0.0
            burnout_drag = mean(member.burnout_probability * 0.55 + member.stress_score * 0.25 + (1 - member.productivity_score) * 0.2 for member in members)
            for member in members:
                loaded_hourly = member.annual_salary * member.fully_loaded_multiplier / 2080
                productivity_gap = 1 - member.productivity_score
                monthly_loss += member.billable_revenue_per_day * 21.67 * productivity_gap * (0.65 + member.burnout_probability * 0.35)
                meeting_loss += max(0, member.meeting_hours_weekly - 6) * 4.33 * loaded_hourly * (1.2 + member.stress_score)
                overtime_loss += member.overtime_hours_monthly * loaded_hourly * 0.38 * (0.8 + member.burnout_probability)
            annualized = (monthly_loss + meeting_loss + overtime_loss) * 12
            recoverable = annualized * (request.productivity_recovery * 0.65 + request.meeting_reduction * 0.18 + request.overtime_reduction * 0.17)
            losses.append(
                ProductivityLossAnalysis(
                    team_name=team_name,
                    employees_analyzed=len(members),
                    monthly_productivity_loss=round(monthly_loss + meeting_loss + overtime_loss, 2),
                    annualized_productivity_loss=round(annualized, 2),
                    recoverable_value=round(recoverable, 2),
                    burnout_drag_percent=round(float(np.clip(burnout_drag * 100, 0, 100)), 2),
                    meeting_inefficiency_cost=round(meeting_loss * 12, 2),
                    overtime_inefficiency_cost=round(overtime_loss * 12, 2),
                    recommendation=f"Reduce meetings and overtime in {team_name} before burnout drag converts into delivery risk.",
                )
            )
        return losses

    @staticmethod
    def _delay_cost(project: ProjectFinancialInput, delay_risk_reduction: float) -> DelayCostAnalysis:
        expected_delay_days = project.projected_delay_days * project.delay_probability
        operational_cost = expected_delay_days * project.daily_burn_rate
        penalty = expected_delay_days * project.delivery_penalty_per_day
        overtime = expected_delay_days * project.team_size * 8 * 92
        revenue_at_risk = project.forecasted_revenue * project.gross_margin * (project.failure_probability * 0.42 + project.delay_probability * 0.28)
        churn = project.forecasted_revenue * project.client_churn_risk * project.delay_probability * 0.24
        expected = operational_cost + penalty + overtime + revenue_at_risk + churn
        mitigated = expected * delay_risk_reduction * (0.72 + min(project.budget_utilization, 1.4) * 0.12)
        return DelayCostAnalysis(
            project_id=project.project_id,
            project_name=project.project_name,
            team_name=project.team_name,
            expected_delay_cost=round(expected, 2),
            revenue_at_risk=round(revenue_at_risk, 2),
            operational_cost_increase=round(operational_cost, 2),
            overtime_cost=round(overtime, 2),
            delivery_penalty_risk=round(penalty, 2),
            client_churn_cost=round(churn, 2),
            mitigated_cost=round(mitigated, 2),
            severity=RoiIntelligenceService._severity(expected / 7_500),
        )

    def _summary(
        self,
        request: RoiScenarioRequest,
        replacement: list[ReplacementCostAnalysis],
        productivity: list[ProductivityLossAnalysis],
        delays: list[DelayCostAnalysis],
    ) -> tuple[RoiSummary, float]:
        replacement_exposure = sum(item.expected_attrition_exposure for item in replacement)
        productivity_exposure = sum(item.annualized_productivity_loss for item in productivity)
        delay_exposure = sum(item.expected_delay_cost for item in delays)
        features = self._portfolio_features(request, replacement_exposure, productivity_exposure, delay_exposure)
        capture = roi_intelligence_engine.predict_capture_rate(features)
        gross_loss = replacement_exposure + productivity_exposure + delay_exposure
        hr_savings = replacement_exposure * request.retention_improvement * 0.18
        optimized_loss = max(0, gross_loss * (1 - capture.savings_capture_rate) - hr_savings)
        gross_savings = gross_loss - optimized_loss
        net_savings = gross_savings - request.intervention_budget
        roi_percent = (net_savings / request.intervention_budget) * 100
        monthly_savings = max(gross_savings / 12, 1)
        payback = request.intervention_budget / monthly_savings
        return (
            RoiSummary(
                baseline_annual_loss=round(gross_loss, 2),
                optimized_annual_loss=round(optimized_loss, 2),
                net_savings=round(net_savings, 2),
                roi_percent=round(roi_percent, 2),
                payback_months=round(payback, 2),
                replacement_cost_exposure=round(replacement_exposure, 2),
                productivity_loss_exposure=round(productivity_exposure, 2),
                project_delay_exposure=round(delay_exposure, 2),
                hr_operational_savings=round(hr_savings, 2),
            ),
            capture.confidence,
        )

    def _forecast(self, request: RoiScenarioRequest, summary: RoiSummary, confidence: float) -> list[RoiForecastPoint]:
        points = []
        monthly_baseline = summary.baseline_annual_loss / 12
        monthly_optimized = summary.optimized_annual_loss / 12
        ramp = min(6, request.horizon_months)
        cumulative_savings = -request.intervention_budget
        for month in range(1, request.horizon_months + 1):
            ramp_factor = min(1, month / ramp)
            baseline_cost = monthly_baseline * month
            optimized_cost = monthly_optimized * month + request.intervention_budget
            cumulative_savings += max(0, monthly_baseline - monthly_optimized) * ramp_factor
            roi_percent = (cumulative_savings / request.intervention_budget) * 100
            points.append(
                RoiForecastPoint(
                    month=month,
                    baseline_cost=round(baseline_cost, 2),
                    optimized_cost=round(optimized_cost, 2),
                    cumulative_savings=round(cumulative_savings, 2),
                    roi_percent=round(roi_percent, 2),
                    confidence=confidence,
                )
            )
        return points

    def _recommendations(
        self,
        request: RoiScenarioRequest,
        replacement: list[ReplacementCostAnalysis],
        productivity: list[ProductivityLossAnalysis],
        delays: list[DelayCostAnalysis],
        summary: RoiSummary,
        confidence: float,
    ) -> list[RoiRecommendation]:
        recommendations = []
        if replacement:
            top = replacement[0]
            recommendations.append(
                RoiRecommendation(
                    recommendation_id="roi-retention",
                    category="retention_optimization",
                    title="Prevent high-cost resignations",
                    action=f"Run targeted retention and recovery plan for {top.employee_name} and adjacent critical owners.",
                    rationale=f"Replacement exposure is ${round(top.expected_attrition_exposure):,}, driven by knowledge loss and revenue-at-risk.",
                    expected_savings=round(sum(item.prevention_savings for item in replacement), 2),
                    roi_multiplier=round(sum(item.prevention_savings for item in replacement) / max(request.intervention_budget, 1), 2),
                    confidence=confidence,
                    source_systems=["employee_dashboard", "burnout_ai", "roi_engine"],
                    evidence=[f"{item.employee_name}: exposure=${round(item.expected_attrition_exposure):,}" for item in replacement[:3]],
                )
            )
        if productivity:
            top_team = productivity[0]
            recommendations.append(
                RoiRecommendation(
                    recommendation_id="roi-productivity",
                    category="productivity_recovery",
                    title="Recover productivity lost to burnout and meetings",
                    action=f"Reduce meeting load and overtime pressure in {top_team.team_name}.",
                    rationale=f"{top_team.team_name} has ${round(top_team.annualized_productivity_loss):,} annualized productivity drag.",
                    expected_savings=round(sum(item.recoverable_value for item in productivity), 2),
                    roi_multiplier=round(sum(item.recoverable_value for item in productivity) / max(request.intervention_budget, 1), 2),
                    confidence=confidence,
                    source_systems=["meeting_analyzer", "voice_stress_ai", "smart_suggestion_engine"],
                    evidence=[f"{item.team_name}: burnout drag={item.burnout_drag_percent}%" for item in productivity[:3]],
                )
            )
        if delays:
            top_project = delays[0]
            recommendations.append(
                RoiRecommendation(
                    recommendation_id="roi-delay",
                    category="delay_cost_reduction",
                    title="Protect revenue from project delay cost",
                    action=f"Open a delivery-cost review for {top_project.project_name} and fund dependency removal first.",
                    rationale=f"Delay economics show ${round(top_project.expected_delay_cost):,} expected business impact.",
                    expected_savings=round(sum(item.mitigated_cost for item in delays), 2),
                    roi_multiplier=round(sum(item.mitigated_cost for item in delays) / max(request.intervention_budget, 1), 2),
                    confidence=confidence,
                    source_systems=["project_failure_prediction", "manager_dashboard", "time_series_forecasting"],
                    evidence=[f"{item.project_name}: delay impact=${round(item.expected_delay_cost):,}" for item in delays[:3]],
                )
            )
        recommendations.append(
            RoiRecommendation(
                recommendation_id="roi-executive-program",
                category="executive_roi_program",
                title="Fund the highest-ROI workforce stability program",
                action="Prioritize retention, meeting reduction, and dependency removal as one executive operating plan.",
                rationale=f"Modeled net savings are ${round(summary.net_savings):,} with payback in {summary.payback_months} months.",
                expected_savings=summary.net_savings,
                roi_multiplier=round(summary.net_savings / max(request.intervention_budget, 1), 2),
                confidence=confidence,
                source_systems=["roi_engine", "project_failure_prediction", "team_compatibility_ai"],
                evidence=[f"roi={summary.roi_percent}%", f"baseline_loss=${round(summary.baseline_annual_loss):,}"],
            )
        )
        return sorted(recommendations, key=lambda item: item.expected_savings, reverse=True)

    @staticmethod
    def _executive_insights(
        summary: RoiSummary,
        replacement: list[ReplacementCostAnalysis],
        productivity: list[ProductivityLossAnalysis],
        delays: list[DelayCostAnalysis],
    ) -> list[ExecutiveInsight]:
        insights = [
            ExecutiveInsight(
                title="Annual business loss avoided",
                message=f"NEXUSMIND models ${round(summary.net_savings):,} net savings after intervention cost.",
                financial_impact=summary.net_savings,
                severity=RoiIntelligenceService._severity(summary.net_savings / 9_000),
                confidence=0.86,
            ),
            ExecutiveInsight(
                title="Replacement cost exposure",
                message=f"Expected attrition and knowledge-loss exposure is ${round(summary.replacement_cost_exposure):,}.",
                financial_impact=summary.replacement_cost_exposure,
                severity=RoiIntelligenceService._severity(summary.replacement_cost_exposure / 7_500),
                confidence=0.82,
            ),
            ExecutiveInsight(
                title="Delay cost exposure",
                message=f"Project delay risk is carrying ${round(summary.project_delay_exposure):,} in expected cost.",
                financial_impact=summary.project_delay_exposure,
                severity=RoiIntelligenceService._severity(summary.project_delay_exposure / 7_500),
                confidence=0.84,
            ),
        ]
        if productivity:
            insights.append(
                ExecutiveInsight(
                    title="Productivity recovery value",
                    message=f"{productivity[0].team_name} is the largest productivity recovery target.",
                    financial_impact=productivity[0].recoverable_value,
                    severity=RoiIntelligenceService._severity(productivity[0].recoverable_value / 6_000),
                    confidence=0.81,
                )
            )
        if replacement and delays:
            insights.append(
                ExecutiveInsight(
                    title="Why executives care",
                    message="The ROI layer converts burnout, attrition, meetings, and delay risk into board-readable dollars.",
                    financial_impact=summary.baseline_annual_loss,
                    severity=RoiIntelligenceService._severity(summary.baseline_annual_loss / 14_000),
                    confidence=0.88,
                )
            )
        return insights

    @staticmethod
    def _portfolio_features(request: RoiScenarioRequest, replacement: float, productivity: float, delay: float) -> list[float]:
        employees = request.employees
        projects = request.projects
        total_loss = max(replacement + productivity + delay, 1)
        return [
            mean([employee.attrition_probability for employee in employees]) if employees else 0,
            mean([employee.burnout_probability for employee in employees]) if employees else 0,
            mean([1 - employee.productivity_score for employee in employees]) if employees else 0,
            mean([employee.stress_score for employee in employees]) if employees else 0,
            min(mean([employee.meeting_hours_weekly for employee in employees]) / 24, 1) if employees else 0,
            min(mean([employee.overtime_hours_monthly for employee in employees]) / 100, 1) if employees else 0,
            mean([employee.knowledge_criticality for employee in employees]) if employees else 0,
            mean([project.delay_probability for project in projects]) if projects else 0,
            mean([project.failure_probability for project in projects]) if projects else 0,
            min(mean([project.budget_utilization for project in projects]) / 1.4, 1) if projects else 0,
            request.retention_improvement,
            request.productivity_recovery,
            request.meeting_reduction,
            request.overtime_reduction,
            request.delay_risk_reduction,
            min(request.intervention_budget / total_loss, 1),
        ]

    @staticmethod
    def _scenario_variant(base: RoiScenarioRequest, risk_delta: float, intervention_delta: float) -> RoiScenarioRequest:
        default = RoiIntelligenceService().default_request() if not base.employees or not base.projects else base
        employees = [
            employee.model_copy(
                update={
                    "attrition_probability": float(np.clip(employee.attrition_probability + risk_delta, 0, 1)),
                    "burnout_probability": float(np.clip(employee.burnout_probability + risk_delta, 0, 1)),
                    "stress_score": float(np.clip(employee.stress_score + risk_delta * 0.8, 0, 1)),
                    "productivity_score": float(np.clip(employee.productivity_score - risk_delta * 0.45, 0, 1)),
                    "overtime_hours_monthly": min(220, employee.overtime_hours_monthly + risk_delta * 80),
                    "meeting_hours_weekly": min(60, employee.meeting_hours_weekly + risk_delta * 18),
                }
            )
            for employee in default.employees
        ]
        projects = [
            project.model_copy(
                update={
                    "failure_probability": float(np.clip(project.failure_probability + risk_delta, 0, 1)),
                    "delay_probability": float(np.clip(project.delay_probability + risk_delta * 0.9, 0, 1)),
                    "projected_delay_days": min(365, project.projected_delay_days + round(risk_delta * 20)),
                    "budget_utilization": min(1.8, project.budget_utilization + risk_delta * 0.25),
                    "client_churn_risk": float(np.clip(project.client_churn_risk + risk_delta * 0.25, 0, 1)),
                }
            )
            for project in default.projects
        ]
        return default.model_copy(
            update={
                "employees": employees,
                "projects": projects,
                "retention_improvement": min(0.8, default.retention_improvement + intervention_delta),
                "productivity_recovery": min(0.6, default.productivity_recovery + intervention_delta),
                "meeting_reduction": min(0.7, default.meeting_reduction + intervention_delta),
                "overtime_reduction": min(0.7, default.overtime_reduction + intervention_delta),
                "delay_risk_reduction": min(0.7, default.delay_risk_reduction + intervention_delta),
                "realtime": True,
            }
        )

    @staticmethod
    def _severity(value: float) -> RoiSeverity:
        if value >= 82:
            return "critical"
        if value >= 48:
            return "high"
        if value >= 22:
            return "medium"
        return "low"

    def _append_jsonl(self, payload: dict[str, object]) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with self._lock:
            with HISTORY_PATH.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, default=str) + "\n")


roi_intelligence_service = RoiIntelligenceService()
