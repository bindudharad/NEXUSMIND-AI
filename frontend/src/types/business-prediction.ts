export type BusinessRiskLevel = "low" | "medium" | "high" | "critical";

export interface BusinessForecastPoint {
  month: string;
  revenue: number;
  lowerBound: number;
  upperBound: number;
  growthRate: number;
  revenueRisk: number;
  confidence: number;
}

export interface ClientChurnForecast {
  clientId: string;
  clientName: string;
  churnProbability: number;
  renewalProbability: number;
  revenueAtRisk: number;
  contractValue: number;
  reasons: string[];
  recommendedActions: string[];
  confidence: number;
}

export interface MarketRiskPrediction {
  riskId: string;
  category: string;
  riskScore: number;
  trend: "declining" | "stable" | "rising";
  forecast: string;
  drivers: string[];
  strategicWarning: string;
}

export interface EmployeeGrowthForecast {
  department: string;
  currentHeadcount: number;
  forecastHeadcount: number;
  growthPercent: number;
  productivityCapacity: number;
  skillDemand: string[];
  confidence: number;
}

export interface HiringDemandForecast {
  role: string;
  department: string;
  requiredCount: number;
  urgency: BusinessRiskLevel;
  skills: string[];
  justification: string;
  revenueLinked: number;
}

export interface ProjectProfitabilityForecast {
  projectId: string;
  projectName: string;
  estimatedCost: number;
  expectedRevenue: number;
  roiPercent: number;
  budgetEfficiency: number;
  overrunProbability: number;
  riskLevel: BusinessRiskLevel;
  confidence: number;
}

export interface CompanyHealthFuture {
  score: number;
  riskLevel: BusinessRiskLevel;
  forecast: string;
  revenueHealth: number;
  workforceHealth: number;
  clientHealth: number;
  deliveryHealth: number;
  productivityHealth: number;
  securityHealth: number;
}

export interface BusinessScenarioResult {
  scenarioId: string;
  scenario: string;
  financialImpact: number;
  revenueAfterImpact: number;
  churnDelta: number;
  workforceImpact: string;
  profitabilityImpact: number;
  growthImpact: number;
  riskImpact: number;
  successProbability: number;
  recommendations: string[];
}

export interface BusinessRecommendation {
  title: string;
  priority: BusinessRiskLevel;
  action: string;
  rationale: string;
  expectedFinancialImpact: number;
  confidence: number;
}

export interface BusinessEvidence {
  source: string;
  signal: string;
  value: string;
  weight: number;
}

export interface BusinessModelStatus {
  model: string;
  status: string;
  detail: string;
}

export interface BusinessPredictionSummary {
  currentRevenue: number;
  predictedNextQuarterRevenue: number;
  annualRevenueForecast: number;
  revenueGrowthRate: number;
  averageChurnProbability: number;
  revenueAtRisk: number;
  hiringNeeded: number;
  companyHealthScore: number;
  marketRiskScore: number;
  profitabilityIndex: number;
  topBusinessRisk: string;
  forecastConfidence: number;
  streamSequence: number;
}

export interface BusinessPredictionResponse {
  model: string;
  generatedAt: string;
  cycleName: string;
  horizonMonths: number;
  summary: BusinessPredictionSummary;
  revenueForecast: BusinessForecastPoint[];
  churnPredictions: ClientChurnForecast[];
  marketRisks: MarketRiskPrediction[];
  employeeGrowthForecast: EmployeeGrowthForecast[];
  hiringDemand: HiringDemandForecast[];
  projectProfitability: ProjectProfitabilityForecast[];
  companyHealthForecast: CompanyHealthFuture;
  scenarioSimulations: BusinessScenarioResult[];
  recommendations: BusinessRecommendation[];
  evidence: BusinessEvidence[];
  modelStatus: BusinessModelStatus[];
  supportedQuestions: string[];
  sourceSystems: string[];
  storage: string;
}

export interface BusinessAssistantResponse {
  model: string;
  generatedAt: string;
  question: string;
  intent: string;
  answer: string;
  confidence: number;
  citedEvidence: BusinessEvidence[];
  scenario: BusinessScenarioResult | null;
  recommendedActions: string[];
  sourceSystems: string[];
  storage: string;
}
