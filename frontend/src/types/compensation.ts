export type CompensationSeverity = "low" | "medium" | "high" | "critical";

export interface MarketBenchmark {
  employeeId: string;
  employeeName: string;
  role: string;
  marketMin: number;
  marketMid: number;
  marketMax: number;
  marketGapPercent: number;
  marketCompetitiveness: number;
  skillScarcityIndex: number;
}

export interface CompensationRecommendation {
  employeeId: string;
  employeeName: string;
  role: string;
  currentSalary: number;
  recommendedSalaryMin: number;
  recommendedSalaryMid: number;
  recommendedSalaryMax: number;
  recommendedAdjustmentPercent: number;
  recommendedAdjustmentAmount: number;
  bonusRecommendation: number;
  bonusPercent: number;
  promotionEligibility: number;
  promotionTrack: string;
  retentionImpact: number;
  fairnessScore: number;
  compensationRiskScore: number;
  confidence: number;
  rationale: string;
  actions: string[];
  sourceSystems: string[];
}

export interface CompensationFairnessPoint {
  department: string;
  averageFairnessScore: number;
  averageMarketGap: number;
  highRiskCount: number;
  recommendedBudget: number;
}

export interface CompensationAlert {
  title: string;
  severity: CompensationSeverity;
  probability: number;
  impact: string;
  intervention: string;
}

export interface CompensationSummary {
  employeesAnalyzed: number;
  totalRecommendedAdjustment: number;
  budgetUtilization: number;
  averageMarketGap: number;
  promotionCandidates: number;
  retentionRiskReduced: number;
  fairnessScore: number;
  streamSequence: number;
}

export interface CompensationResponse {
  model: string;
  generatedAt: string;
  cycleName: string;
  recommendations: CompensationRecommendation[];
  marketBenchmarks: MarketBenchmark[];
  fairnessHeatmap: CompensationFairnessPoint[];
  alerts: CompensationAlert[];
  executiveInsights: string[];
  summary: CompensationSummary;
  storage: string;
}
