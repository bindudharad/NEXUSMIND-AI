export type CompetitiveRiskLevel = "low" | "medium" | "high" | "critical";

export interface CompetitorProfile {
  competitorId: string;
  companyName: string;
  industry: string;
  products: string[];
  marketPosition: string;
  revenueEstimateMillions: number;
  employeeCount: number;
  technologyStack: string[];
  recentActivities: string[];
  strategicRisks: string[];
  rank: number;
  threatScore: number;
  threatLevel: CompetitiveRiskLevel;
  sourceSignals: string[];
}

export interface ProductLaunchSignal {
  competitor: string;
  launchName: string;
  category: string;
  releaseWindow: string;
  launchFrequencyScore: number;
  productStrategyShift: string;
  impact: string;
  riskLevel: CompetitiveRiskLevel;
  evidence: string[];
}

export interface HiringTrendSignal {
  competitor: string;
  hiringGrowthPercent: number;
  focus: string;
  roles: string[];
  departmentsExpanding: string[];
  geographicHiring: string[];
  skillDemand: string[];
  forecast: string;
  strategicInterpretation: string;
  riskLevel: CompetitiveRiskLevel;
}

export interface TechnologyAdoptionSignal {
  competitor: string;
  technologies: string[];
  adoptionScore: number;
  investmentSignal: number;
  strategicInsight: string;
  riskLevel: CompetitiveRiskLevel;
}

export interface MarketExpansionSignal {
  competitor: string;
  regions: string[];
  expansionScore: number;
  customerAcquisitionSignal: number;
  potentialMarketThreat: CompetitiveRiskLevel;
  strategicInterpretation: string;
}

export interface IndustryTrendSignal {
  trend: string;
  tractionScore: number;
  forecastImpact: string;
  likelyTimeHorizon: string;
  opportunity: string;
  risk: string;
}

export interface CompetitiveRiskScore {
  competitor: string;
  threatScore: number;
  threatLevel: CompetitiveRiskLevel;
  marketDisruptionRisk: number;
  innovationRisk: number;
  talentAcquisitionRisk: number;
  technologyRisk: number;
  primaryThreat: string;
  evidence: string[];
}

export interface CompetitorComparisonMetric {
  metric: string;
  companyScore: number;
  competitorScore: number;
  delta: number;
  interpretation: string;
}

export interface CompetitorComparisonCard {
  competitor: string;
  rank: number;
  overallScore: number;
  metrics: CompetitorComparisonMetric[];
}

export interface CompetitiveStrategicRecommendation {
  title: string;
  priority: CompetitiveRiskLevel;
  action: string;
  reason: string;
  expectedCompetitiveBenefit: string;
  confidence: number;
  relatedCompetitors: string[];
}

export interface CompetitiveDashboardSummary {
  competitorCount: number;
  highThreatCompetitors: number;
  topCompetitorThreat: string;
  averageThreatScore: number;
  productLaunchesTracked: number;
  aggressiveHiringCompetitors: number;
  technologiesTracked: number;
  marketsExpanding: number;
  strategicReadinessScore: number;
  streamSequence: number;
}

export interface CompetitiveIntelligenceResponse {
  model: string;
  generatedAt: string;
  horizonMonths: number;
  summary: CompetitiveDashboardSummary;
  profiles: CompetitorProfile[];
  productLaunches: ProductLaunchSignal[];
  hiringTrends: HiringTrendSignal[];
  technologyAdoption: TechnologyAdoptionSignal[];
  marketExpansions: MarketExpansionSignal[];
  riskScores: CompetitiveRiskScore[];
  industryTrends: IndustryTrendSignal[];
  comparison: CompetitorComparisonCard[];
  recommendations: CompetitiveStrategicRecommendation[];
  supportedQuestions: string[];
  sourceSystems: string[];
  storage: string;
}

export interface CompetitiveAssistantResponse {
  model: string;
  generatedAt: string;
  question: string;
  intent: string;
  answer: string;
  confidence: number;
  citedEvidence: string[];
  competitors: string[];
  recommendations: CompetitiveStrategicRecommendation[];
  sourceSystems: string[];
  storage: string;
}
