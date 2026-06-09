from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from threading import Lock

import numpy as np

from app.ai.compensation_engine import compensation_engine
from app.core.cache import TTLResponseCache
from app.schemas.compensation import (
    CompensationAlert,
    CompensationEmployeeProfile,
    CompensationFairnessPoint,
    CompensationRecommendation,
    CompensationRequest,
    CompensationResponse,
    CompensationSeverity,
    CompensationSummary,
    MarketBenchmark,
)


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
HISTORY_PATH = DATA_DIR / "compensation_history.jsonl"


class CompensationIntelligenceService:
    model_name = "RandomForest/GradientBoosting Compensation Intelligence Engine"

    def __init__(self) -> None:
        self._lock = Lock()
        self._default_cache: TTLResponseCache[CompensationResponse] = TTLResponseCache(ttl_seconds=8)
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def analyze(self, payload: CompensationRequest | None = None) -> CompensationResponse:
        if payload is None:
            return self._default_cache.get_or_set(self._analyze_default_uncached)
        return self._analyze_uncached(payload)

    def _analyze_default_uncached(self) -> CompensationResponse:
        return self._analyze_uncached(self.default_request())

    def _analyze_uncached(self, payload: CompensationRequest) -> CompensationResponse:
        request = payload if payload.employees else payload.model_copy(update={"employees": self.default_request().employees})
        recommendations = [self._recommendation(employee) for employee in request.employees]
        benchmarks = [self._benchmark(employee) for employee in request.employees]
        response = CompensationResponse(
            model=self.model_name,
            generated_at=datetime.now(timezone.utc),
            cycle_name=request.cycle_name,
            recommendations=sorted(recommendations, key=lambda item: item.compensation_risk_score, reverse=True),
            market_benchmarks=sorted(benchmarks, key=lambda item: item.market_gap_percent, reverse=True),
            fairness_heatmap=self._fairness_heatmap(request.employees, recommendations, benchmarks),
            alerts=self._alerts(recommendations, benchmarks),
            executive_insights=self._executive_insights(recommendations, benchmarks, request.budget_pool),
            summary=self._summary(recommendations, benchmarks, request.budget_pool),
            storage=str(HISTORY_PATH),
        )
        self._append_jsonl(response.model_dump(mode="json"))
        return response

    async def stream(self, payload: CompensationRequest | None = None):
        base = payload or self.default_request()
        scenarios = [
            base,
            self._scenario_variant(base, attrition_delta=0.06, market_delta=0.05, satisfaction_delta=-0.04),
            self._scenario_variant(base, attrition_delta=0.12, market_delta=0.11, satisfaction_delta=-0.09),
        ]
        for sequence, scenario in enumerate(scenarios, start=1):
            response = self.analyze(scenario)
            data = response.model_dump(mode="json")
            data["summary"]["stream_sequence"] = sequence
            yield f"event: compensation\ndata: {json.dumps(data)}\n\n"
            await asyncio.sleep(0.8)

    @staticmethod
    def default_request() -> CompensationRequest:
        return CompensationRequest(
            cycle_name="FY2026 Executive Compensation Review",
            budget_pool=1_400_000,
            employees=[
                CompensationEmployeeProfile(
                    employee_id="comp-001",
                    employee_name="Aarav Mehta",
                    role="Senior ML Engineer",
                    level=5,
                    department="AI Platform",
                    location="United States",
                    annual_salary=168_000,
                    experience_years=8.5,
                    performance_score=93,
                    productivity_score=91,
                    skill_growth=0.78,
                    skill_scarcity=0.86,
                    leadership_score=0.72,
                    delivery_consistency=0.9,
                    collaboration_score=0.84,
                    innovation_score=0.82,
                    learning_velocity=0.88,
                    attrition_probability=0.62,
                    burnout_risk=0.58,
                    salary_satisfaction=0.38,
                    peer_compa_ratio=0.82,
                    last_raise_months=22,
                    promotion_delay_months=20,
                    criticality_score=0.9,
                    market_multiplier=1.18,
                    skills=["mlops", "forecasting", "python", "vector search", "llm systems"],
                ),
                CompensationEmployeeProfile(
                    employee_id="comp-002",
                    employee_name="Nisha Rao",
                    role="Backend Engineer",
                    level=4,
                    department="Engineering",
                    annual_salary=132_000,
                    experience_years=6.0,
                    performance_score=86,
                    productivity_score=88,
                    skill_growth=0.62,
                    skill_scarcity=0.58,
                    leadership_score=0.54,
                    delivery_consistency=0.86,
                    collaboration_score=0.8,
                    innovation_score=0.52,
                    learning_velocity=0.76,
                    attrition_probability=0.46,
                    burnout_risk=0.42,
                    salary_satisfaction=0.55,
                    peer_compa_ratio=0.9,
                    last_raise_months=16,
                    promotion_delay_months=12,
                    criticality_score=0.74,
                    market_multiplier=1.05,
                    skills=["python", "fastapi", "postgresql", "distributed systems"],
                ),
                CompensationEmployeeProfile(
                    employee_id="comp-003",
                    employee_name="Maya Iyer",
                    role="Product Designer",
                    level=3,
                    department="Experience",
                    annual_salary=116_000,
                    experience_years=5.2,
                    performance_score=82,
                    productivity_score=79,
                    skill_growth=0.56,
                    skill_scarcity=0.44,
                    leadership_score=0.48,
                    delivery_consistency=0.78,
                    collaboration_score=0.86,
                    innovation_score=0.7,
                    learning_velocity=0.72,
                    attrition_probability=0.28,
                    burnout_risk=0.3,
                    salary_satisfaction=0.72,
                    peer_compa_ratio=1.0,
                    last_raise_months=9,
                    promotion_delay_months=7,
                    criticality_score=0.56,
                    market_multiplier=0.98,
                    skills=["ux research", "design systems", "accessibility", "enterprise dashboards"],
                ),
                CompensationEmployeeProfile(
                    employee_id="comp-004",
                    employee_name="Omar Singh",
                    role="Engineering Manager",
                    level=6,
                    department="Engineering",
                    annual_salary=214_000,
                    experience_years=12,
                    performance_score=90,
                    productivity_score=84,
                    skill_growth=0.5,
                    skill_scarcity=0.62,
                    leadership_score=0.9,
                    delivery_consistency=0.88,
                    collaboration_score=0.86,
                    innovation_score=0.58,
                    learning_velocity=0.7,
                    attrition_probability=0.34,
                    burnout_risk=0.64,
                    salary_satisfaction=0.68,
                    peer_compa_ratio=0.96,
                    last_raise_months=13,
                    promotion_delay_months=8,
                    criticality_score=0.82,
                    market_multiplier=1.1,
                    skills=["leadership", "platform strategy", "delivery management", "incident response"],
                ),
            ],
        )

    def _recommendation(self, employee: CompensationEmployeeProfile) -> CompensationRecommendation:
        prediction = compensation_engine.predict(employee)
        benchmark = self._benchmark(employee)
        market_gap = benchmark.market_gap_percent
        salary_mid = max(prediction.fair_salary_mid, benchmark.market_mid * 0.92)
        retention_pressure = self._clip100((employee.attrition_probability * 0.36 + (1 - employee.salary_satisfaction) * 0.26 + max(market_gap, 0) / 100 * 0.22 + employee.criticality_score * 0.16) * 100)
        fairness_score = self._clip100(100 - max(market_gap, 0) * 0.52 - max(0, 1 - employee.peer_compa_ratio) * 100 * 0.32 - employee.promotion_delay_months / 96 * 12)
        compensation_risk = self._clip100(retention_pressure * 0.45 + max(market_gap, 0) * 0.28 + (100 - fairness_score) * 0.18 + employee.burnout_risk * 100 * 0.09)
        adjusted_raise = self._clip(prediction.raise_percent + max(market_gap, 0) * 0.13 + employee.attrition_probability * 4.5 + employee.skill_scarcity * 2.5, 0, 45)
        recommended_mid = max(employee.annual_salary * (1 + adjusted_raise / 100), salary_mid)
        recommended_min = recommended_mid * 0.94
        recommended_max = recommended_mid * 1.12
        adjustment_amount = max(0, recommended_mid - employee.annual_salary)
        bonus_percent = self._clip(prediction.bonus_percent + employee.criticality_score * 1.8 + employee.delivery_consistency * 1.2, 0, 35)
        bonus = employee.annual_salary * bonus_percent / 100
        promotion = self._clip100(prediction.promotion_probability + employee.promotion_delay_months / 36 * 8 + employee.leadership_score * 4)
        track = self._promotion_track(employee, promotion)
        actions = self._actions(employee, market_gap, adjusted_raise, promotion, compensation_risk)
        rationale = (
            f"{employee.employee_name} is {round(max(market_gap, 0), 1)}% below modeled market midpoint with "
            f"{round(employee.performance_score)} performance, {round(employee.skill_scarcity * 100)} skill scarcity, "
            f"and {round(employee.attrition_probability * 100)}% retention pressure."
        )
        return CompensationRecommendation(
            employee_id=employee.employee_id,
            employee_name=employee.employee_name,
            role=employee.role,
            current_salary=round(employee.annual_salary, 2),
            recommended_salary_min=round(recommended_min, 2),
            recommended_salary_mid=round(recommended_mid, 2),
            recommended_salary_max=round(recommended_max, 2),
            recommended_adjustment_percent=round(adjusted_raise, 2),
            recommended_adjustment_amount=round(adjustment_amount, 2),
            bonus_recommendation=round(bonus, 2),
            bonus_percent=round(bonus_percent, 2),
            promotion_eligibility=round(promotion, 2),
            promotion_track=track,
            retention_impact=round(self._clip100(adjusted_raise * 1.45 + bonus_percent * 0.8 + employee.salary_satisfaction * 8), 2),
            fairness_score=round(fairness_score, 2),
            compensation_risk_score=round(compensation_risk, 2),
            confidence=prediction.confidence,
            rationale=rationale,
            actions=actions,
            source_systems=["compensation_forecaster", "attrition_prediction", "roi_engine", "market_benchmarking"],
        )

    @staticmethod
    def _benchmark(employee: CompensationEmployeeProfile) -> MarketBenchmark:
        role_lower = employee.role.lower()
        role_factor = 1.0
        if "ml" in role_lower or "ai" in role_lower:
            role_factor = 1.22
        elif "manager" in role_lower or "lead" in role_lower:
            role_factor = 1.18
        elif "backend" in role_lower or "platform" in role_lower:
            role_factor = 1.08
        elif "designer" in role_lower:
            role_factor = 0.92
        location_factor = 1.0 if "united states" in employee.location.lower() else 0.72 if "india" in employee.location.lower() else 0.88
        skill_factor = 1 + employee.skill_scarcity * 0.22 + min(len(employee.skills), 10) * 0.012
        market_mid = (
            58_000
            + employee.level * 20_500
            + employee.experience_years * 5_200
            + employee.performance_score * 115
            + employee.leadership_score * 12_000
            + employee.criticality_score * 18_000
        ) * role_factor * location_factor * employee.market_multiplier * skill_factor
        market_min = market_mid * 0.86
        market_max = market_mid * 1.24
        gap = (market_mid - employee.annual_salary) / max(employee.annual_salary, 1) * 100
        competitiveness = CompensationIntelligenceService._clip100(100 - max(gap, 0) * 1.15 + min(-gap, 0) * 0.22)
        return MarketBenchmark(
            employee_id=employee.employee_id,
            employee_name=employee.employee_name,
            role=employee.role,
            market_min=round(market_min, 2),
            market_mid=round(market_mid, 2),
            market_max=round(market_max, 2),
            market_gap_percent=round(gap, 2),
            market_competitiveness=round(competitiveness, 2),
            skill_scarcity_index=round(employee.skill_scarcity * 100, 2),
        )

    @staticmethod
    def _fairness_heatmap(
        employees: list[CompensationEmployeeProfile],
        recommendations: list[CompensationRecommendation],
        benchmarks: list[MarketBenchmark],
    ) -> list[CompensationFairnessPoint]:
        grouped: dict[str, list[tuple[CompensationRecommendation, MarketBenchmark]]] = defaultdict(list)
        employee_department = {employee.employee_id: employee.department for employee in employees}
        benchmark_by_id = {benchmark.employee_id: benchmark for benchmark in benchmarks}
        for recommendation in recommendations:
            benchmark = benchmark_by_id[recommendation.employee_id]
            grouped[employee_department[recommendation.employee_id]].append((recommendation, benchmark))
        return [
            CompensationFairnessPoint(
                department=department,
                average_fairness_score=round(mean(item[0].fairness_score for item in items), 2),
                average_market_gap=round(mean(item[1].market_gap_percent for item in items), 2),
                high_risk_count=sum(1 for recommendation, _ in items if recommendation.compensation_risk_score >= 65),
                recommended_budget=round(sum(recommendation.recommended_adjustment_amount + recommendation.bonus_recommendation for recommendation, _ in items), 2),
            )
            for department, items in sorted(grouped.items())
        ]

    @staticmethod
    def _alerts(recommendations: list[CompensationRecommendation], benchmarks: list[MarketBenchmark]) -> list[CompensationAlert]:
        alerts: list[CompensationAlert] = []
        benchmark_by_id = {benchmark.employee_id: benchmark for benchmark in benchmarks}
        for recommendation in sorted(recommendations, key=lambda item: item.compensation_risk_score, reverse=True)[:5]:
            benchmark = benchmark_by_id[recommendation.employee_id]
            if recommendation.compensation_risk_score >= 50:
                alerts.append(
                    CompensationAlert(
                        title=f"{recommendation.employee_name} compensation risk",
                        severity=CompensationIntelligenceService._severity(recommendation.compensation_risk_score),
                        probability=recommendation.compensation_risk_score,
                        impact=f"Market gap {round(benchmark.market_gap_percent)}%, retention impact {round(recommendation.retention_impact)}%.",
                        intervention=recommendation.actions[0] if recommendation.actions else "Review compensation package.",
                    )
                )
        return alerts

    @staticmethod
    def _summary(recommendations: list[CompensationRecommendation], benchmarks: list[MarketBenchmark], budget_pool: float) -> CompensationSummary:
        total_adjustment = sum(item.recommended_adjustment_amount + item.bonus_recommendation for item in recommendations)
        return CompensationSummary(
            employees_analyzed=len(recommendations),
            total_recommended_adjustment=round(total_adjustment, 2),
            budget_utilization=round(min(200, total_adjustment / max(budget_pool, 1) * 100), 2),
            average_market_gap=round(mean(item.market_gap_percent for item in benchmarks) if benchmarks else 0, 2),
            promotion_candidates=sum(1 for item in recommendations if item.promotion_eligibility >= 70),
            retention_risk_reduced=round(mean(item.retention_impact for item in recommendations) if recommendations else 0, 2),
            fairness_score=round(mean(item.fairness_score for item in recommendations) if recommendations else 0, 2),
        )

    @staticmethod
    def _executive_insights(recommendations: list[CompensationRecommendation], benchmarks: list[MarketBenchmark], budget_pool: float) -> list[str]:
        if not recommendations:
            return []
        top = max(recommendations, key=lambda item: item.compensation_risk_score)
        total = sum(item.recommended_adjustment_amount + item.bonus_recommendation for item in recommendations)
        avg_gap = mean(item.market_gap_percent for item in benchmarks) if benchmarks else 0
        return [
            f"{top.employee_name} is the highest compensation-risk employee at {round(top.compensation_risk_score)} risk with {round(top.recommended_adjustment_percent)}% recommended adjustment.",
            f"Portfolio recommendation uses {round(total / max(budget_pool, 1) * 100)}% of the compensation pool and targets {sum(1 for item in recommendations if item.promotion_eligibility >= 70)} promotion-ready employees.",
            f"Average market gap is {round(avg_gap, 1)}%; prioritize salary corrections where retention pressure, skill scarcity, and peer fairness all exceed thresholds.",
        ]

    @staticmethod
    def _actions(employee: CompensationEmployeeProfile, market_gap: float, raise_percent: float, promotion: float, risk: float) -> list[str]:
        actions: list[str] = []
        if market_gap >= 8 or risk >= 65:
            actions.append(f"Approve a {round(raise_percent)}% salary correction for {employee.employee_name} tied to retention and market parity.")
        if promotion >= 70:
            actions.append(f"Open promotion packet for {employee.employee_name} with a 60-day evidence review.")
        if employee.burnout_risk >= 0.55 and employee.attrition_probability >= 0.5:
            actions.append("Pair compensation correction with workload recovery to protect retention impact.")
        if employee.performance_score >= 88:
            actions.append("Issue performance bonus for sustained delivery and high-impact contribution.")
        if not actions:
            actions.append("Maintain current salary band and monitor market movement next cycle.")
        return actions

    @staticmethod
    def _promotion_track(employee: CompensationEmployeeProfile, promotion: float) -> str:
        if promotion >= 82 and employee.leadership_score >= 0.72:
            return "Ready for lead or manager promotion review"
        if promotion >= 70:
            return "Ready for senior-level promotion path"
        if promotion >= 55:
            return "Growth track with next-cycle promotion checkpoint"
        return "Maintain current level with development plan"

    @staticmethod
    def _scenario_variant(base: CompensationRequest, attrition_delta: float, market_delta: float, satisfaction_delta: float) -> CompensationRequest:
        employees = [
            employee.model_copy(
                update={
                    "attrition_probability": CompensationIntelligenceService._clip01(employee.attrition_probability + attrition_delta),
                    "market_multiplier": min(2.2, employee.market_multiplier + market_delta),
                    "salary_satisfaction": CompensationIntelligenceService._clip01(employee.salary_satisfaction + satisfaction_delta),
                    "peer_compa_ratio": max(0.45, employee.peer_compa_ratio - market_delta * 0.35),
                }
            )
            for employee in base.employees
        ]
        return base.model_copy(update={"employees": employees, "realtime": True})

    @staticmethod
    def _severity(score: float) -> CompensationSeverity:
        if score >= 82:
            return "critical"
        if score >= 64:
            return "high"
        if score >= 42:
            return "medium"
        return "low"

    @staticmethod
    def _clip(value: float, low: float, high: float) -> float:
        return float(np.clip(value, low, high))

    @staticmethod
    def _clip01(value: float) -> float:
        return float(np.clip(value, 0, 1))

    @staticmethod
    def _clip100(value: float) -> float:
        return float(np.clip(value, 0, 100))

    def _append_jsonl(self, payload: dict[str, object]) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with self._lock:
            with HISTORY_PATH.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, default=str) + "\n")


compensation_service = CompensationIntelligenceService()
