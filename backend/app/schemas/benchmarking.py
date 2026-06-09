from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


BenchmarkPriority = Literal["low", "medium", "high", "critical"]
IndustrySegment = Literal["ai_saas", "fintech", "healthcare", "retail", "logistics", "enterprise_software", "general"]
CompanyStage = Literal["startup", "scaleup", "mid_market", "enterprise"]


class CompanyBenchmarkSignal(BaseModel):
    company_id: str
    industry: IndustrySegment = "ai_saas"
    company_stage: CompanyStage = "scaleup"
    region: str = "global"
    employee_count: int = Field(default=420, ge=10, le=250000)
    department: str = "Engineering"
    productivity_score: float = Field(default=0.78, ge=0, le=1)
    burnout_index: float = Field(default=0.34, ge=0, le=1)
    attrition_rate: float = Field(default=0.16, ge=0, le=1)
    retention_rate: float = Field(default=0.84, ge=0, le=1)
    team_efficiency: float = Field(default=0.76, ge=0, le=1)
    delivery_stability: float = Field(default=0.74, ge=0, le=1)
    workforce_happiness: float = Field(default=0.72, ge=0, le=1)
    innovation_output: float = Field(default=0.68, ge=0, le=1)
    collaboration_quality: float = Field(default=0.74, ge=0, le=1)
    project_success_rate: float = Field(default=0.77, ge=0, le=1)
    communication_health: float = Field(default=0.73, ge=0, le=1)
    learning_growth: float = Field(default=0.66, ge=0, le=1)
    operational_stability: float = Field(default=0.76, ge=0, le=1)
    sprint_velocity: float = Field(default=0.72, ge=0, le=1)
    overtime_intensity: float = Field(default=0.28, ge=0, le=1)
    incident_rate: float = Field(default=0.18, ge=0, le=1)
    ai_adoption: float = Field(default=0.62, ge=0, le=1)
    data_confidence: float = Field(default=0.82, ge=0, le=1)


class BenchmarkingRequest(BaseModel):
    cycle_name: str = "Realtime Multi-Company Benchmark Review"
    target_company_id: str = "target-nexusmind"
    industry: IndustrySegment = "ai_saas"
    company_stage: CompanyStage = "scaleup"
    horizon_days: int = Field(default=90, ge=30, le=365)
    privacy_epsilon: float = Field(default=2.4, ge=0.5, le=10)
    companies: list[CompanyBenchmarkSignal] = Field(default_factory=list, max_length=150)
    realtime: bool = False


class BenchmarkForecastPoint(BaseModel):
    day: int = Field(ge=1)
    benchmark_score: float = Field(ge=0, le=100)
    productivity_percentile: float = Field(ge=0, le=100)
    burnout_percentile: float = Field(ge=0, le=100)
    retention_percentile: float = Field(ge=0, le=100)
    maturity_score: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)


class CompanyBenchmarkScore(BaseModel):
    anonymized_company_id: str
    cohort_label: str
    industry: IndustrySegment
    company_stage: CompanyStage
    company_size_band: str
    is_target: bool
    benchmark_score: float = Field(ge=0, le=100)
    percentile_rank: float = Field(ge=0, le=100)
    productivity_delta_percent: float
    burnout_delta_percent: float
    retention_delta_percent: float
    maturity_delta_percent: float
    retention_stability_score: float = Field(ge=0, le=100)
    operational_maturity_score: float = Field(ge=0, le=100)
    workforce_maturity_score: float = Field(ge=0, le=100)
    innovation_maturity_score: float = Field(ge=0, le=100)
    privacy_noise_applied: float = Field(ge=0, le=10)
    confidence: float = Field(ge=0, le=1)
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    forecast: list[BenchmarkForecastPoint] = Field(default_factory=list)


class IndustryKpiComparison(BaseModel):
    metric: str
    company_value: float = Field(ge=0, le=100)
    industry_median: float = Field(ge=0, le=100)
    top_quartile: float = Field(ge=0, le=100)
    delta_percent: float
    percentile: float = Field(ge=0, le=100)
    priority: BenchmarkPriority
    insight: str


class BenchmarkHeatmapPoint(BaseModel):
    cohort: str
    metric: str
    score: float = Field(ge=0, le=100)
    industry_delta: float
    priority: BenchmarkPriority


class WorkforceMaturityScorecard(BaseModel):
    category: str
    score: float = Field(ge=0, le=100)
    industry_median: float = Field(ge=0, le=100)
    top_decile: float = Field(ge=0, le=100)
    maturity_level: str


class BenchmarkRecommendation(BaseModel):
    title: str
    category: Literal["productivity", "burnout", "retention", "collaboration", "maturity", "privacy", "executive"]
    priority: BenchmarkPriority
    action: str
    expected_impact: str
    confidence: float = Field(ge=0, le=1)
    target_metrics: list[str] = Field(default_factory=list)


class BenchmarkAlert(BaseModel):
    title: str
    severity: BenchmarkPriority
    probability: float = Field(ge=0, le=100)
    impact: str
    recommendation: str


class BenchmarkingSummary(BaseModel):
    companies_analyzed: int
    anonymous_peer_count: int
    target_percentile: float = Field(ge=0, le=100)
    target_benchmark_score: float = Field(ge=0, le=100)
    industry_ranking_label: str
    productivity_vs_industry: float
    burnout_vs_industry: float
    retention_vs_industry: float
    maturity_score: float = Field(ge=0, le=100)
    high_priority_gaps: int
    stream_sequence: int = 1


class BenchmarkingResponse(BaseModel):
    model: str
    generated_at: datetime
    cycle_name: str
    horizon_days: int
    industry: IndustrySegment
    company_stage: CompanyStage
    privacy_epsilon: float
    benchmark_scores: list[CompanyBenchmarkScore]
    kpi_comparisons: list[IndustryKpiComparison]
    heatmap: list[BenchmarkHeatmapPoint]
    maturity_scorecards: list[WorkforceMaturityScorecard]
    recommendations: list[BenchmarkRecommendation]
    alerts: list[BenchmarkAlert]
    executive_insights: list[str]
    summary: BenchmarkingSummary
    source_systems: list[str]
    storage: str
