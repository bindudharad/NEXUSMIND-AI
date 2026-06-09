export type BenchmarkPriority = "low" | "medium" | "high" | "critical";
export type IndustrySegment = "ai_saas" | "fintech" | "healthcare" | "retail" | "logistics" | "enterprise_software" | "general";
export type CompanyStage = "startup" | "scaleup" | "mid_market" | "enterprise";

export interface BenchmarkForecastPoint {
  day: number;
  benchmarkScore: number;
  productivityPercentile: number;
  burnoutPercentile: number;
  retentionPercentile: number;
  maturityScore: number;
  confidence: number;
}

export interface CompanyBenchmarkScore {
  anonymizedCompanyId: string;
  cohortLabel: string;
  industry: IndustrySegment;
  companyStage: CompanyStage;
  companySizeBand: string;
  isTarget: boolean;
  benchmarkScore: number;
  percentileRank: number;
  productivityDeltaPercent: number;
  burnoutDeltaPercent: number;
  retentionDeltaPercent: number;
  maturityDeltaPercent: number;
  retentionStabilityScore: number;
  operationalMaturityScore: number;
  workforceMaturityScore: number;
  innovationMaturityScore: number;
  privacyNoiseApplied: number;
  confidence: number;
  strengths: string[];
  gaps: string[];
  forecast: BenchmarkForecastPoint[];
}

export interface IndustryKpiComparison {
  metric: string;
  companyValue: number;
  industryMedian: number;
  topQuartile: number;
  deltaPercent: number;
  percentile: number;
  priority: BenchmarkPriority;
  insight: string;
}

export interface BenchmarkHeatmapPoint {
  cohort: string;
  metric: string;
  score: number;
  industryDelta: number;
  priority: BenchmarkPriority;
}

export interface WorkforceMaturityScorecard {
  category: string;
  score: number;
  industryMedian: number;
  topDecile: number;
  maturityLevel: string;
}

export interface BenchmarkRecommendation {
  title: string;
  category: "productivity" | "burnout" | "retention" | "collaboration" | "maturity" | "privacy" | "executive";
  priority: BenchmarkPriority;
  action: string;
  expectedImpact: string;
  confidence: number;
  targetMetrics: string[];
}

export interface BenchmarkAlert {
  title: string;
  severity: BenchmarkPriority;
  probability: number;
  impact: string;
  recommendation: string;
}

export interface BenchmarkingSummary {
  companiesAnalyzed: number;
  anonymousPeerCount: number;
  targetPercentile: number;
  targetBenchmarkScore: number;
  industryRankingLabel: string;
  productivityVsIndustry: number;
  burnoutVsIndustry: number;
  retentionVsIndustry: number;
  maturityScore: number;
  highPriorityGaps: number;
  streamSequence: number;
}

export interface BenchmarkingResponse {
  model: string;
  generatedAt: string;
  cycleName: string;
  horizonDays: number;
  industry: IndustrySegment;
  companyStage: CompanyStage;
  privacyEpsilon: number;
  benchmarkScores: CompanyBenchmarkScore[];
  kpiComparisons: IndustryKpiComparison[];
  heatmap: BenchmarkHeatmapPoint[];
  maturityScorecards: WorkforceMaturityScorecard[];
  recommendations: BenchmarkRecommendation[];
  alerts: BenchmarkAlert[];
  executiveInsights: string[];
  summary: BenchmarkingSummary;
  sourceSystems: string[];
  storage: string;
}
