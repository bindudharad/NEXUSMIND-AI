export type GlobalRiskLevel = "low" | "medium" | "high" | "critical";
export type GlobalSignalType = "news" | "economic" | "competitor" | "regulatory" | "technology" | "cyber" | "supply_chain" | "geopolitical";
export type GlobalAssistantIntent = "global_risks" | "competitor" | "inflation" | "market_trends" | "regulations" | "cyber" | "summary";

export interface ExternalEventInput {
  eventId: string;
  sourceType: GlobalSignalType;
  title: string;
  sourceName: string;
  region: string;
  industry: string;
  publishedAt?: string | null;
  summary: string;
  sentimentScore: number;
  severity: number;
  relevance: number;
  opportunityScore: number;
  keywords: string[];
  sourceUrl: string;
}

export interface GlobalRiskScannerRequest {
  cycleName: string;
  horizonDays: number;
  companyIndustries: string[];
  targetRegions: string[];
  events: ExternalEventInput[];
  useLiveSources: boolean;
}

export interface ExternalIntelligenceSignal {
  eventId: string;
  signalType: GlobalSignalType;
  title: string;
  sourceName: string;
  region: string;
  industry: string;
  sentimentScore: number;
  riskScore: number;
  opportunityScore: number;
  riskLevel: GlobalRiskLevel;
  industryRelevance: number;
  companyRelevance: number;
  interpretation: string;
  evidence: string[];
  sourceUrl: string;
}

export interface EconomicIndicatorSignal {
  indicator: string;
  region: string;
  currentSignal: string;
  riskScore: number;
  opportunityScore: number;
  predictedCompanyImpact: string;
  evidence: string[];
}

export interface CompetitorGlobalThreat {
  competitor: string;
  threatScore: number;
  opportunityScore: number;
  threatLevel: GlobalRiskLevel;
  primaryThreat: string;
  predictedClientChurnDelta: number;
  evidence: string[];
}

export interface RegulatoryRiskSignal {
  regulation: string;
  region: string;
  complianceRisk: number;
  costImpactPercent: number;
  operationalImpact: number;
  recommendedAction: string;
  evidence: string[];
}

export interface TechnologyTrendSignal {
  trend: string;
  category: string;
  opportunityScore: number;
  technologyRisk: number;
  strategicWindow: string;
  recommendedAction: string;
  evidence: string[];
}

export interface CyberThreatSignal {
  threat: string;
  threatScore: number;
  businessImpact: string;
  affectedCapabilities: string[];
  recommendedAction: string;
  evidence: string[];
}

export interface CompanyImpactPrediction {
  eventId: string;
  title: string;
  category: GlobalSignalType;
  revenueImpactPercent: number;
  workforceImpactScore: number;
  clientImpactScore: number;
  operationalImpactScore: number;
  projectImpactScore: number;
  strategicImpactScore: number;
  confidence: number;
  explanation: string;
}

export interface GlobalRiskForecastPoint {
  horizonLabel: "30_days" | "90_days" | "6_months" | "12_months";
  horizonDays: number;
  riskScore: number;
  opportunityScore: number;
  confidence: number;
  trend: "declining" | "stable" | "rising";
  topDrivers: string[];
}

export interface GlobalRiskAlert {
  alertId: string;
  title: string;
  category: GlobalSignalType;
  riskLevel: GlobalRiskLevel;
  potentialRevenueImpact: number;
  recommendedAction: string;
  urgencyHours: number;
  evidence: string[];
}

export interface GlobalRiskRecommendation {
  recommendationId: string;
  title: string;
  priority: GlobalRiskLevel;
  action: string;
  rationale: string;
  expectedImpact: string;
  confidence: number;
  ownerAgent: string;
}

export interface GlobalRiskDigitalTwinSync {
  twin: "company" | "department" | "workforce" | "revenue_forecast" | "crisis_simulator" | "executive_dashboard";
  status: "synced" | "projected" | "watch";
  update: string;
  entityCount: number;
}

export interface GlobalRiskAgentContribution {
  agent: string;
  role: string;
  finding: string;
  recommendation: string;
  confidence: number;
  sourceSystems: string[];
}

export interface GlobalRiskDashboardSummary {
  eventsAnalyzed: number;
  highRiskEvents: number;
  criticalAlerts: number;
  economicRiskScore: number;
  competitiveThreatScore: number;
  regulatoryRiskScore: number;
  technologyOpportunityScore: number;
  cyberThreatScore: number;
  averageCompanyImpact: number;
  productionReadinessScore: number;
  innovationScore: number;
  judgeWowFactorScore: number;
  streamSequence: number;
}

export interface GlobalRiskScannerResponse {
  model: string;
  generatedAt: string;
  cycleName: string;
  horizonDays: number;
  summary: GlobalRiskDashboardSummary;
  newsIntelligence: ExternalIntelligenceSignal[];
  economicIntelligence: EconomicIndicatorSignal[];
  competitorIntelligence: CompetitorGlobalThreat[];
  regulatoryIntelligence: RegulatoryRiskSignal[];
  technologyIntelligence: TechnologyTrendSignal[];
  cyberThreatIntelligence: CyberThreatSignal[];
  impactPredictions: CompanyImpactPrediction[];
  riskForecasts: GlobalRiskForecastPoint[];
  alerts: GlobalRiskAlert[];
  recommendations: GlobalRiskRecommendation[];
  digitalTwinSync: GlobalRiskDigitalTwinSync[];
  agentCouncil: GlobalRiskAgentContribution[];
  supportedQuestions: string[];
  executiveInsights: string[];
  liveSourceAdapters: string[];
  sourceSystems: string[];
  storage: string;
  finalVerdict: string;
}

export interface GlobalRiskAssistantResponse {
  model: string;
  generatedAt: string;
  question: string;
  intent: GlobalAssistantIntent;
  answer: string;
  confidence: number;
  citedEvents: string[];
  recommendedActions: string[];
  evidence: string[];
  sourceSystems: string[];
  storage: string;
}
