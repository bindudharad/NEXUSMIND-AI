export type BoardroomSeverity = "low" | "medium" | "high" | "critical";
export type BoardroomStatus = "excellent" | "healthy" | "watch" | "risk" | "critical";
export type BoardroomAssistantIntent =
  | "health"
  | "risk"
  | "forecast"
  | "burnout"
  | "client"
  | "simulation"
  | "security"
  | "innovation"
  | "recommendation"
  | "summary";

export interface BoardroomKPI {
  label: string;
  value: string;
  score: number;
  trend: number;
  status: BoardroomStatus;
  source: string;
}

export interface CompanyHealthPanel {
  score: number;
  status: BoardroomStatus;
  trend: string;
  drivers: string[];
  historicalTrend: number[];
  sourceSystems: string[];
}

export interface ExecutiveRiskItem {
  riskId: string;
  category: string;
  title: string;
  affectedArea: string;
  probability: number;
  impactScore: number;
  severity: BoardroomSeverity;
  recommendation: string;
  evidence: string[];
  sourceSystems: string[];
}

export interface FinancialPredictionPanel {
  currentRevenue: number;
  nextQuarterRevenue: number;
  annualRevenueForecast: number;
  revenueGrowthRate: number;
  profitForecast: number;
  costForecast: number;
  forecastConfidence: number;
  monthlyForecast: number[];
  quarterlyForecast: number[];
  annualForecast: number[];
  forecastModels: string[];
}

export interface WorkforceIntelligencePanel {
  employeeHealthScore: number;
  burnoutHotspots: string[];
  attritionRisk: number;
  productivityTrend: number;
  topInnovator: string;
  hiddenTalentCount: number;
  futureLeadersCount: number;
  sourceSystems: string[];
}

export interface CybersecurityPanel {
  securityScore: number;
  threatLevel: BoardroomSeverity;
  activeThreats: number;
  insiderThreatRisk: number;
  dataLeakageRisk: number;
  suspiciousActivity: string[];
  recommendations: string[];
  sourceSystems: string[];
}

export interface ProjectIntelligencePanel {
  projectHealthScore: number;
  completionConfidence: number;
  highestRiskProject: string;
  deliveryRisk: number;
  resourceGaps: string[];
  deliveryForecast: number[];
  sourceSystems: string[];
}

export interface ClientIntelligencePanel {
  averageClientHealth: number;
  highestChurnRiskClient: string;
  churnRisk: number;
  paymentRiskAccounts: number;
  upsellOpportunityRevenue: number;
  relationshipStatus: string;
  recommendedActions: string[];
  sourceSystems: string[];
}

export interface CompetitiveIntelligencePanel {
  threatScore: number;
  topThreat: string;
  marketTrends: string[];
  industryRisks: string[];
  strategicOpportunities: string[];
  recommendations: string[];
  sourceSystems: string[];
}

export interface InnovationIntelligencePanel {
  hiddenTalentCount: number;
  futureLeadersCount: number;
  innovationChampions: string[];
  skillGrowthTrend: number;
  promotionRecommendations: string[];
  sourceSystems: string[];
}

export interface DigitalTwinCommandCenter {
  companyTwinStatus: string;
  activeSimulations: number;
  recommendedScenario: string;
  highestRiskScenario: string;
  futureForecasts: string[];
  organizationalStatus: string[];
  sourceSystems: string[];
}

export interface BoardroomAlert {
  alertId: string;
  category: string;
  severity: BoardroomSeverity;
  title: string;
  probability: number;
  recommendation: string;
  sourceSystems: string[];
}

export interface ExecutiveRecommendation {
  recommendationId: string;
  category: string;
  priority: BoardroomSeverity;
  action: string;
  reason: string;
  expectedBenefit: string;
  confidence: number;
  sourceSystems: string[];
}

export interface BoardroomSummary {
  companyHealthScore: number;
  overallRiskScore: number;
  executiveConfidence: number;
  criticalRisks: number;
  activeAlerts: number;
  recommendedActions: number;
  realtimeStreams: number;
  connectedEngines: number;
  streamSequence: number;
}

export interface BoardroomDashboardResponse {
  model: string;
  generatedAt: string;
  dashboardName: string;
  kpis: BoardroomKPI[];
  companyHealth: CompanyHealthPanel;
  executiveRisks: ExecutiveRiskItem[];
  financialPredictions: FinancialPredictionPanel;
  workforce: WorkforceIntelligencePanel;
  cybersecurity: CybersecurityPanel;
  projects: ProjectIntelligencePanel;
  clients: ClientIntelligencePanel;
  competitive: CompetitiveIntelligencePanel;
  innovation: InnovationIntelligencePanel;
  digitalTwin: DigitalTwinCommandCenter;
  alerts: BoardroomAlert[];
  recommendations: ExecutiveRecommendation[];
  executiveSummary: string[];
  supportedQuestions: string[];
  sourceSystems: string[];
  summary: BoardroomSummary;
  storage: string;
}

export interface BoardroomAssistantResponse {
  model: string;
  generatedAt: string;
  question: string;
  intent: BoardroomAssistantIntent;
  answer: string;
  confidence: number;
  citedPanels: string[];
  citedEvidence: string[];
  recommendedActions: string[];
  sourceSystems: string[];
  storage: string;
}
