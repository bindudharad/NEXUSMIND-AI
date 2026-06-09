from __future__ import annotations

import asyncio
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median
from threading import Lock

import numpy as np

from app.ai.benchmarking_engine import benchmarking_engine
from app.core.cache import TTLResponseCache
from app.schemas.benchmarking import (
    BenchmarkAlert,
    BenchmarkForecastPoint,
    BenchmarkHeatmapPoint,
    BenchmarkingRequest,
    BenchmarkingResponse,
    BenchmarkingSummary,
    BenchmarkPriority,
    BenchmarkRecommendation,
    CompanyBenchmarkScore,
    CompanyBenchmarkSignal,
    IndustryKpiComparison,
    WorkforceMaturityScorecard,
)


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
HISTORY_PATH = DATA_DIR / "benchmarking_history.jsonl"

METRICS: tuple[tuple[str, str, bool], ...] = (
    ("productivity_score", "Productivity benchmark", False),
    ("burnout_index", "Burnout comparison", True),
    ("retention_rate", "Retention stability", False),
    ("team_efficiency", "Team efficiency", False),
    ("delivery_stability", "Delivery stability", False),
    ("workforce_happiness", "Workforce happiness", False),
    ("innovation_output", "Innovation output", False),
    ("collaboration_quality", "Collaboration quality", False),
    ("project_success_rate", "Project success rate", False),
    ("communication_health", "Communication health", False),
    ("learning_growth", "Learning growth", False),
    ("operational_stability", "Operational stability", False),
)


class BenchmarkingService:
    model_name = "Multi-Company Benchmarking & Industry Intelligence System"
    source_systems = [
        "anonymous_company_aggregation",
        "random_forest_benchmark_score_model",
        "gradient_boosting_maturity_forecaster",
        "kmeans_peer_cohort_clustering",
        "privacy_noise_secure_aggregation",
        "industry_kpi_percentile_engine",
        "benchmarking_history_jsonl",
    ]

    def __init__(self) -> None:
        self._cache: TTLResponseCache[BenchmarkingResponse] = TTLResponseCache(ttl_seconds=10)
        self._lock = Lock()
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def analyze(self, payload: BenchmarkingRequest | None = None) -> BenchmarkingResponse:
        if payload is None:
            return self._cache.get_or_set(self._default_uncached)
        return self._analyze_uncached(payload)

    def _default_uncached(self) -> BenchmarkingResponse:
        return self._analyze_uncached(self.default_request())

    def _analyze_uncached(self, payload: BenchmarkingRequest) -> BenchmarkingResponse:
        request = payload if payload.companies else self.default_request()
        companies = self._cohort(request)
        rows = [self._feature_row(company) for company in companies]
        model_predictions = benchmarking_engine.predict(rows)
        benchmark_distribution = [self._clip(prediction["benchmark_score"]) for prediction in model_predictions]
        peer_values = self._peer_values(request.target_company_id, companies)
        industry_stats = self._industry_stats(peer_values)
        scores = [
            self._company_score(request, company, row, prediction, industry_stats, peer_values, benchmark_distribution)
            for company, row, prediction in zip(companies, rows, model_predictions)
        ]
        scores.sort(key=lambda item: (not item.is_target, -item.benchmark_score))
        target = next((score for score in scores if score.is_target), scores[0])
        comparisons = self._kpi_comparisons(request, companies, target, industry_stats)
        heatmap = self._heatmap(scores, comparisons)
        maturity = self._maturity_scorecards(target, comparisons)
        recommendations = self._recommendations(target, comparisons)
        alerts = self._alerts(target, comparisons)
        response = BenchmarkingResponse(
            model=benchmarking_engine.model_name,
            generated_at=datetime.now(timezone.utc),
            cycle_name=request.cycle_name,
            horizon_days=request.horizon_days,
            industry=request.industry,
            company_stage=request.company_stage,
            privacy_epsilon=request.privacy_epsilon,
            benchmark_scores=scores,
            kpi_comparisons=comparisons,
            heatmap=heatmap,
            maturity_scorecards=maturity,
            recommendations=recommendations,
            alerts=alerts,
            executive_insights=self._executive_insights(target, comparisons, len(companies) - 1),
            summary=self._summary(target, comparisons, len(companies), len(peer_values)),
            source_systems=self.source_systems,
            storage=str(HISTORY_PATH),
        )
        self._append_jsonl(response.model_dump(mode="json"))
        return response

    async def stream(self, payload: BenchmarkingRequest | None = None):
        base = payload or self.default_request()
        scenarios = [
            base,
            self._scenario_variant(base, productivity_delta=0.025, burnout_delta=-0.02, retention_delta=0.014),
            self._scenario_variant(base, productivity_delta=0.045, burnout_delta=-0.035, retention_delta=0.024),
        ]
        for sequence, scenario in enumerate(scenarios, start=1):
            response = self.analyze(scenario)
            data = response.model_dump(mode="json")
            data["summary"]["stream_sequence"] = sequence
            yield f"event: benchmarking\ndata: {json.dumps(data)}\n\n"
            await asyncio.sleep(0.8)

    def _cohort(self, request: BenchmarkingRequest) -> list[CompanyBenchmarkSignal]:
        companies = [*request.companies] if request.companies else [*self.default_request().companies]
        if not any(company.company_id == request.target_company_id for company in companies):
            companies.insert(
                0,
                CompanyBenchmarkSignal(
                    company_id=request.target_company_id,
                    industry=request.industry,
                    company_stage=request.company_stage,
                    productivity_score=0.78,
                    burnout_index=0.32,
                    attrition_rate=0.13,
                    retention_rate=0.87,
                    delivery_stability=0.79,
                    innovation_output=0.72,
                    ai_adoption=0.68,
                ),
            )
        return companies

    def _company_score(
        self,
        request: BenchmarkingRequest,
        company: CompanyBenchmarkSignal,
        row: dict[str, float],
        prediction: dict[str, float],
        industry_stats: dict[str, dict[str, float]],
        peer_values: list[CompanyBenchmarkSignal],
        benchmark_distribution: list[float],
    ) -> CompanyBenchmarkScore:
        noise = self._privacy_noise(company.company_id, request.privacy_epsilon)
        score = self._clip(prediction["benchmark_score"] + noise)
        maturity = self._clip(prediction["maturity_score"] + noise * 0.55)
        retention_stability = self._clip(company.retention_rate * 74 + company.delivery_stability * 12 + (1 - company.attrition_rate) * 14 + noise * 0.35)
        workforce_maturity = self._clip(company.workforce_happiness * 27 + company.collaboration_quality * 23 + company.communication_health * 18 + company.learning_growth * 14 + company.retention_rate * 18 + noise * 0.3)
        innovation_maturity = self._clip(company.innovation_output * 57 + company.ai_adoption * 31 + company.learning_growth * 12 + noise * 0.4)
        company_values = [self._raw_metric(peer, "productivity_score") for peer in peer_values] or [company.productivity_score * 100]
        productivity_median = median(company_values)
        burnout_median = median([self._raw_metric(peer, "burnout_index") for peer in peer_values] or [company.burnout_index * 100])
        retention_median = median([self._raw_metric(peer, "retention_rate") for peer in peer_values] or [company.retention_rate * 100])
        maturity_median = median(
            [
                self._clip(peer.operational_stability * 34 + peer.delivery_stability * 24 + peer.project_success_rate * 18 + peer.ai_adoption * 12 + peer.innovation_output * 12)
                for peer in peer_values
            ]
            or [maturity]
        )
        return CompanyBenchmarkScore(
            anonymized_company_id=self._anonymous_id(company.company_id),
            cohort_label=f"{company.industry.replace('_', ' ').title()} {company.company_stage.replace('_', ' ').title()} cluster {int(prediction['cluster']) + 1}",
            industry=company.industry,
            company_stage=company.company_stage,
            company_size_band=self._size_band(company.employee_count),
            is_target=company.company_id == request.target_company_id,
            benchmark_score=round(score, 2),
            percentile_rank=round(self._percentile(score, benchmark_distribution), 2),
            productivity_delta_percent=round(company.productivity_score * 100 - productivity_median, 2),
            burnout_delta_percent=round(burnout_median - company.burnout_index * 100, 2),
            retention_delta_percent=round(company.retention_rate * 100 - retention_median, 2),
            maturity_delta_percent=round(maturity - maturity_median, 2),
            retention_stability_score=round(retention_stability, 2),
            operational_maturity_score=round(maturity, 2),
            workforce_maturity_score=round(workforce_maturity, 2),
            innovation_maturity_score=round(innovation_maturity, 2),
            privacy_noise_applied=round(abs(noise), 3),
            confidence=round(float(prediction["confidence"]) * company.data_confidence, 3),
            strengths=self._strengths(company, industry_stats),
            gaps=self._gaps(company, industry_stats),
            forecast=self._forecast(request.horizon_days, score, company, maturity, prediction["confidence"]),
        )

    def _kpi_comparisons(
        self,
        request: BenchmarkingRequest,
        companies: list[CompanyBenchmarkSignal],
        target: CompanyBenchmarkScore,
        industry_stats: dict[str, dict[str, float]],
    ) -> list[IndustryKpiComparison]:
        target_company = next(company for company in companies if company.company_id == request.target_company_id)
        comparisons: list[IndustryKpiComparison] = []
        for key, label, inverse in METRICS:
            company_value = self._raw_metric(target_company, key)
            stats = industry_stats[key]
            percentile = self._metric_percentile(company_value, stats["values"], inverse)
            delta = stats["median"] - company_value if inverse else company_value - stats["median"]
            priority = self._priority_gap(delta)
            direction = "below" if delta < 0 else "above"
            if inverse:
                direction = "lower risk than" if delta >= 0 else "higher risk than"
            comparisons.append(
                IndustryKpiComparison(
                    metric=label,
                    company_value=round(company_value, 2),
                    industry_median=round(stats["median"], 2),
                    top_quartile=round(stats["top_quartile"], 2),
                    delta_percent=round(delta, 2),
                    percentile=round(percentile, 2),
                    priority=priority,
                    insight=f"Target organization is {abs(round(delta, 1))}% {direction} comparable {target.industry.replace('_', ' ')} peers for {label.lower()}.",
                )
            )
        return comparisons

    def _industry_stats(self, peer_values: list[CompanyBenchmarkSignal]) -> dict[str, dict[str, float]]:
        stats: dict[str, dict[str, float]] = {}
        for key, _, inverse in METRICS:
            values = [self._raw_metric(peer, key) for peer in peer_values]
            if not values:
                values = [50.0]
            percentile = 25 if inverse else 75
            stats[key] = {
                "values": values,
                "median": float(median(values)),
                "top_quartile": float(np.percentile(values, percentile)),
            }
        return stats

    def _heatmap(self, scores: list[CompanyBenchmarkScore], comparisons: list[IndustryKpiComparison]) -> list[BenchmarkHeatmapPoint]:
        target = next((score for score in scores if score.is_target), scores[0])
        points = [
            BenchmarkHeatmapPoint(
                cohort=target.cohort_label,
                metric=comparison.metric,
                score=comparison.company_value,
                industry_delta=comparison.delta_percent,
                priority=comparison.priority,
            )
            for comparison in comparisons
        ]
        return sorted(points, key=lambda item: ({"critical": 4, "high": 3, "medium": 2, "low": 1}[item.priority], abs(item.industry_delta)), reverse=True)

    def _maturity_scorecards(self, target: CompanyBenchmarkScore, comparisons: list[IndustryKpiComparison]) -> list[WorkforceMaturityScorecard]:
        lookup = {comparison.metric: comparison for comparison in comparisons}
        return [
            self._scorecard("Workforce maturity", target.workforce_maturity_score, lookup["Workforce happiness"].industry_median, 88),
            self._scorecard("Operational maturity", target.operational_maturity_score, lookup["Operational stability"].industry_median, 90),
            self._scorecard("Innovation maturity", target.innovation_maturity_score, lookup["Innovation output"].industry_median, 86),
            self._scorecard("Retention stability", target.retention_stability_score, lookup["Retention stability"].industry_median, 91),
        ]

    def _recommendations(self, target: CompanyBenchmarkScore, comparisons: list[IndustryKpiComparison]) -> list[BenchmarkRecommendation]:
        weak = sorted(comparisons, key=lambda item: item.delta_percent)[:4]
        recommendations: list[BenchmarkRecommendation] = []
        for item in weak:
            if item.metric == "Burnout comparison" and item.delta_percent < 0:
                recommendations.append(
                    BenchmarkRecommendation(
                        title="Reduce burnout to benchmark-safe range",
                        category="burnout",
                        priority="critical" if item.delta_percent < -15 else "high",
                        action="Reduce sprint overload, cap recurring meetings, and move high-interruption work into protected operating windows.",
                        expected_impact="Moves burnout risk toward top-quartile industry operating levels.",
                        confidence=0.88,
                        target_metrics=[item.metric],
                    )
                )
            elif item.metric == "Retention stability" and item.delta_percent < 0:
                recommendations.append(
                    BenchmarkRecommendation(
                        title="Improve retention stability against peer cohort",
                        category="retention",
                        priority="high",
                        action="Create retention interventions for critical roles and rebalance compensation, workload, and manager compatibility.",
                        expected_impact="Improves continuity and reduces workforce replacement exposure.",
                        confidence=0.86,
                        target_metrics=[item.metric],
                    )
                )
            elif item.metric in {"Collaboration quality", "Communication health"} and item.delta_percent < 0:
                recommendations.append(
                    BenchmarkRecommendation(
                        title="Raise cross-team collaboration maturity",
                        category="collaboration",
                        priority="medium",
                        action="Standardize decision logs, reduce handoff ambiguity, and assign shared outcome owners across departments.",
                        expected_impact="Closes collaboration and communication gaps against high-performing enterprise peers.",
                        confidence=0.84,
                        target_metrics=[item.metric],
                    )
                )
            elif item.delta_percent < 0:
                recommendations.append(
                    BenchmarkRecommendation(
                        title=f"Improve {item.metric.lower()}",
                        category="productivity" if "Productivity" in item.metric else "maturity",
                        priority=self._priority_gap(item.delta_percent),
                        action=f"Prioritize operating changes that move {item.metric.lower()} from peer median toward top-quartile benchmark performance.",
                        expected_impact="Raises enterprise benchmark percentile and operating maturity.",
                        confidence=0.82,
                        target_metrics=[item.metric],
                    )
                )
        recommendations.append(
            BenchmarkRecommendation(
                title="Maintain privacy-safe benchmark aggregation",
                category="privacy",
                priority="low",
                action="Keep peer comparisons anonymized and report only aggregated cohort deltas to executive users.",
                expected_impact="Prevents company identity leakage while preserving competitive workforce intelligence.",
                confidence=0.91,
                target_metrics=["Anonymous peer comparison"],
            )
        )
        return recommendations[:5]

    def _alerts(self, target: CompanyBenchmarkScore, comparisons: list[IndustryKpiComparison]) -> list[BenchmarkAlert]:
        alerts: list[BenchmarkAlert] = []
        for item in comparisons:
            if item.delta_percent < -12:
                alerts.append(
                    BenchmarkAlert(
                        title=f"{item.metric} benchmark gap",
                        severity="critical" if item.delta_percent < -20 else "high",
                        probability=self._clip(abs(item.delta_percent) * 3.2),
                        impact=f"{item.metric} is {abs(round(item.delta_percent, 1))}% behind comparable peer organizations.",
                        recommendation=f"Prioritize executive action for {item.metric.lower()} before the next benchmark cycle.",
                    )
                )
        if target.percentile_rank < 45:
            alerts.append(
                BenchmarkAlert(
                    title="Benchmark ranking below target operating band",
                    severity="high",
                    probability=round(100 - target.percentile_rank, 2),
                    impact=f"Target organization ranks at percentile {round(target.percentile_rank)} in the anonymous peer cohort.",
                    recommendation="Launch a 30-day benchmark recovery plan focused on top negative KPI deltas.",
                )
            )
        return alerts[:4]

    def _summary(
        self,
        target: CompanyBenchmarkScore,
        comparisons: list[IndustryKpiComparison],
        companies_analyzed: int,
        anonymous_peer_count: int,
    ) -> BenchmarkingSummary:
        return BenchmarkingSummary(
            companies_analyzed=companies_analyzed,
            anonymous_peer_count=anonymous_peer_count,
            target_percentile=target.percentile_rank,
            target_benchmark_score=target.benchmark_score,
            industry_ranking_label=self._ranking_label(target.percentile_rank),
            productivity_vs_industry=self._comparison_delta(comparisons, "Productivity benchmark"),
            burnout_vs_industry=self._comparison_delta(comparisons, "Burnout comparison"),
            retention_vs_industry=self._comparison_delta(comparisons, "Retention stability"),
            maturity_score=target.operational_maturity_score,
            high_priority_gaps=sum(1 for item in comparisons if item.priority in {"high", "critical"}),
        )

    def _executive_insights(self, target: CompanyBenchmarkScore, comparisons: list[IndustryKpiComparison], peers: int) -> list[str]:
        best = max(comparisons, key=lambda item: item.delta_percent)
        worst = min(comparisons, key=lambda item: item.delta_percent)
        return [
            f"Target organization ranks in the {round(target.percentile_rank)}th percentile across {peers} anonymous comparable organizations.",
            f"{best.metric} is the strongest benchmark signal at {round(best.delta_percent, 1)}% above peer median.",
            f"{worst.metric} is the largest operating gap at {round(worst.delta_percent, 1)}% versus peer median.",
            "Benchmarking uses anonymized cohort aggregation, KPI percentile scoring, forecasting, and privacy-noise controls.",
        ]

    @staticmethod
    def _feature_row(company: CompanyBenchmarkSignal) -> dict[str, float]:
        return {
            "productivity_score": company.productivity_score,
            "burnout_inverse": 1 - company.burnout_index,
            "retention_rate": company.retention_rate,
            "team_efficiency": company.team_efficiency,
            "delivery_stability": company.delivery_stability,
            "workforce_happiness": company.workforce_happiness,
            "innovation_output": company.innovation_output,
            "collaboration_quality": company.collaboration_quality,
            "project_success_rate": company.project_success_rate,
            "communication_health": company.communication_health,
            "learning_growth": company.learning_growth,
            "operational_stability": company.operational_stability,
            "sprint_velocity": company.sprint_velocity,
            "overtime_inverse": 1 - company.overtime_intensity,
            "incident_inverse": 1 - company.incident_rate,
            "ai_adoption": company.ai_adoption,
            "size_index": BenchmarkingService._clip01(np.log10(company.employee_count) / 5),
        }

    @staticmethod
    def _peer_values(target_id: str, companies: list[CompanyBenchmarkSignal]) -> list[CompanyBenchmarkSignal]:
        peers = [company for company in companies if company.company_id != target_id]
        return peers or companies

    @staticmethod
    def _raw_metric(company: CompanyBenchmarkSignal, key: str) -> float:
        return round(float(getattr(company, key)) * 100, 4)

    @staticmethod
    def _metric_percentile(value: float, values: list[float], inverse: bool) -> float:
        if not values:
            return 50.0
        if inverse:
            better = sum(1 for item in values if item >= value)
        else:
            better = sum(1 for item in values if item <= value)
        return BenchmarkingService._clip((better / len(values)) * 100)

    @staticmethod
    def _percentile(value: float, values: list[float]) -> float:
        if not values:
            return 50.0
        return BenchmarkingService._clip((sum(1 for item in values if item <= value) / len(values)) * 100)

    def _strengths(self, company: CompanyBenchmarkSignal, industry_stats: dict[str, dict[str, float]]) -> list[str]:
        strengths: list[str] = []
        for key, label, inverse in METRICS:
            value = self._raw_metric(company, key)
            median_value = industry_stats[key]["median"]
            delta = median_value - value if inverse else value - median_value
            if delta >= 8:
                strengths.append(f"{label} outperforms peer median by {round(delta)}%")
        return strengths[:4]

    def _gaps(self, company: CompanyBenchmarkSignal, industry_stats: dict[str, dict[str, float]]) -> list[str]:
        gaps: list[str] = []
        for key, label, inverse in METRICS:
            value = self._raw_metric(company, key)
            median_value = industry_stats[key]["median"]
            delta = median_value - value if inverse else value - median_value
            if delta <= -8:
                gaps.append(f"{label} trails peer median by {abs(round(delta))}%")
        return gaps[:4]

    @staticmethod
    def _forecast(
        horizon_days: int,
        benchmark_score: float,
        company: CompanyBenchmarkSignal,
        maturity: float,
        confidence: float,
    ) -> list[BenchmarkForecastPoint]:
        points: list[BenchmarkForecastPoint] = []
        momentum = (
            (company.productivity_score - 0.62) * 3.2
            + (company.retention_rate - 0.78) * 2.4
            + (0.42 - company.burnout_index) * 2.8
            + (company.ai_adoption - 0.55) * 1.6
        )
        for index in range(6):
            day = max(1, round((index + 1) * horizon_days / 6))
            drift = index * momentum
            score = BenchmarkingService._clip(benchmark_score + drift)
            burnout_percentile = BenchmarkingService._clip((1 - company.burnout_index) * 100 + drift * 0.36)
            productivity_percentile = BenchmarkingService._clip(company.productivity_score * 100 + drift * 0.44)
            retention_percentile = BenchmarkingService._clip(company.retention_rate * 100 + drift * 0.34)
            points.append(
                BenchmarkForecastPoint(
                    day=day,
                    benchmark_score=round(score, 2),
                    productivity_percentile=round(productivity_percentile, 2),
                    burnout_percentile=round(burnout_percentile, 2),
                    retention_percentile=round(retention_percentile, 2),
                    maturity_score=round(BenchmarkingService._clip(maturity + drift * 0.52), 2),
                    confidence=round(max(0.68, confidence - index * 0.024), 3),
                )
            )
        return points

    @staticmethod
    def _scorecard(category: str, score: float, industry_median: float, top_decile: float) -> WorkforceMaturityScorecard:
        if score >= top_decile:
            level = "top-decile"
        elif score >= industry_median + 8:
            level = "advanced"
        elif score >= industry_median - 6:
            level = "competitive"
        else:
            level = "needs executive focus"
        return WorkforceMaturityScorecard(
            category=category,
            score=round(score, 2),
            industry_median=round(industry_median, 2),
            top_decile=round(top_decile, 2),
            maturity_level=level,
        )

    @staticmethod
    def _comparison_delta(comparisons: list[IndustryKpiComparison], metric: str) -> float:
        return next((item.delta_percent for item in comparisons if item.metric == metric), 0.0)

    @staticmethod
    def _priority_gap(delta: float) -> BenchmarkPriority:
        if delta <= -20:
            return "critical"
        if delta <= -10:
            return "high"
        if delta <= -3:
            return "medium"
        return "low"

    @staticmethod
    def _ranking_label(percentile: float) -> str:
        if percentile >= 90:
            return "top 10% enterprise benchmark"
        if percentile >= 75:
            return "top quartile"
        if percentile >= 50:
            return "above industry median"
        return "below target benchmark band"

    @staticmethod
    def _size_band(employee_count: int) -> str:
        if employee_count < 100:
            return "10-99"
        if employee_count < 500:
            return "100-499"
        if employee_count < 2500:
            return "500-2499"
        if employee_count < 10000:
            return "2500-9999"
        return "10000+"

    @staticmethod
    def _anonymous_id(company_id: str) -> str:
        digest = hashlib.sha256(f"nexusmind-benchmark::{company_id}".encode("utf-8")).hexdigest()[:12]
        return f"anon-{digest}"

    @staticmethod
    def _privacy_noise(company_id: str, epsilon: float) -> float:
        seed = int(hashlib.sha256(f"benchmark-noise::{company_id}".encode("utf-8")).hexdigest()[:8], 16)
        rng = np.random.default_rng(seed)
        return float(np.clip(rng.laplace(0, 1 / max(epsilon, 0.5)), -2.25, 2.25))

    @staticmethod
    def _clip(value: float, lower: float = 0, upper: float = 100) -> float:
        return max(lower, min(upper, float(value)))

    @staticmethod
    def _clip01(value: float) -> float:
        return max(0.0, min(1.0, float(value)))

    def _append_jsonl(self, payload: dict[str, object]) -> None:
        with self._lock:
            with HISTORY_PATH.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, default=str) + "\n")

    def _scenario_variant(
        self,
        base: BenchmarkingRequest,
        productivity_delta: float,
        burnout_delta: float,
        retention_delta: float,
    ) -> BenchmarkingRequest:
        companies = []
        for company in base.companies:
            if company.company_id == base.target_company_id:
                companies.append(
                    company.model_copy(
                        update={
                            "productivity_score": self._clip01(company.productivity_score + productivity_delta),
                            "burnout_index": self._clip01(company.burnout_index + burnout_delta),
                            "retention_rate": self._clip01(company.retention_rate + retention_delta),
                            "delivery_stability": self._clip01(company.delivery_stability + productivity_delta * 0.5),
                            "operational_stability": self._clip01(company.operational_stability + productivity_delta * 0.45),
                        }
                    )
                )
            else:
                companies.append(company)
        return base.model_copy(update={"companies": companies, "realtime": True})

    @staticmethod
    def default_request() -> BenchmarkingRequest:
        return BenchmarkingRequest(
            cycle_name="Realtime Multi-Company Benchmark Review",
            target_company_id="target-nexusmind",
            industry="ai_saas",
            company_stage="scaleup",
            horizon_days=90,
            privacy_epsilon=2.4,
            companies=[
                CompanyBenchmarkSignal(
                    company_id="target-nexusmind",
                    industry="ai_saas",
                    company_stage="scaleup",
                    region="global",
                    employee_count=620,
                    department="Enterprise",
                    productivity_score=0.82,
                    burnout_index=0.29,
                    attrition_rate=0.11,
                    retention_rate=0.89,
                    team_efficiency=0.8,
                    delivery_stability=0.81,
                    workforce_happiness=0.78,
                    innovation_output=0.84,
                    collaboration_quality=0.76,
                    project_success_rate=0.83,
                    communication_health=0.74,
                    learning_growth=0.79,
                    operational_stability=0.8,
                    sprint_velocity=0.81,
                    overtime_intensity=0.24,
                    incident_rate=0.13,
                    ai_adoption=0.88,
                    data_confidence=0.91,
                ),
                CompanyBenchmarkSignal(company_id="peer-ai-01", employee_count=540, productivity_score=0.74, burnout_index=0.38, attrition_rate=0.17, retention_rate=0.83, team_efficiency=0.72, delivery_stability=0.7, workforce_happiness=0.68, innovation_output=0.73, collaboration_quality=0.69, project_success_rate=0.72, communication_health=0.7, learning_growth=0.67, operational_stability=0.72, sprint_velocity=0.7, overtime_intensity=0.34, incident_rate=0.22, ai_adoption=0.66),
                CompanyBenchmarkSignal(company_id="peer-ai-02", employee_count=980, productivity_score=0.79, burnout_index=0.31, attrition_rate=0.13, retention_rate=0.87, team_efficiency=0.78, delivery_stability=0.8, workforce_happiness=0.75, innovation_output=0.8, collaboration_quality=0.77, project_success_rate=0.8, communication_health=0.76, learning_growth=0.74, operational_stability=0.79, sprint_velocity=0.78, overtime_intensity=0.27, incident_rate=0.15, ai_adoption=0.82),
                CompanyBenchmarkSignal(company_id="peer-ai-03", employee_count=430, productivity_score=0.68, burnout_index=0.47, attrition_rate=0.23, retention_rate=0.77, team_efficiency=0.66, delivery_stability=0.64, workforce_happiness=0.6, innovation_output=0.62, collaboration_quality=0.61, project_success_rate=0.65, communication_health=0.58, learning_growth=0.6, operational_stability=0.63, sprint_velocity=0.64, overtime_intensity=0.48, incident_rate=0.31, ai_adoption=0.55),
                CompanyBenchmarkSignal(company_id="peer-ai-04", employee_count=1550, productivity_score=0.86, burnout_index=0.24, attrition_rate=0.09, retention_rate=0.91, team_efficiency=0.84, delivery_stability=0.87, workforce_happiness=0.82, innovation_output=0.86, collaboration_quality=0.83, project_success_rate=0.88, communication_health=0.82, learning_growth=0.81, operational_stability=0.86, sprint_velocity=0.85, overtime_intensity=0.22, incident_rate=0.1, ai_adoption=0.9),
                CompanyBenchmarkSignal(company_id="peer-ai-05", employee_count=780, productivity_score=0.72, burnout_index=0.41, attrition_rate=0.2, retention_rate=0.8, team_efficiency=0.69, delivery_stability=0.68, workforce_happiness=0.66, innovation_output=0.7, collaboration_quality=0.67, project_success_rate=0.69, communication_health=0.65, learning_growth=0.63, operational_stability=0.67, sprint_velocity=0.69, overtime_intensity=0.39, incident_rate=0.24, ai_adoption=0.61),
            ],
        )


benchmarking_service = BenchmarkingService()
