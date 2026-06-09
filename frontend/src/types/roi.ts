export type RoiSeverity = "low" | "medium" | "high" | "critical";

export interface ReplacementCostAnalysis {
  employeeId: string;
  employeeName: string;
  teamName: string;
  replacementCost: number;
  expectedAttritionExposure: number;
  hiringCost: number;
  trainingCost: number;
  productivityRecoveryCost: number;
  knowledgeTransferLoss: number;
  teamDisruptionCost: number;
  revenueAtRisk: number;
  preventionSavings: number;
  severity: RoiSeverity;
}

export interface ProductivityLossAnalysis {
  teamName: string;
  employeesAnalyzed: number;
  monthlyProductivityLoss: number;
  annualizedProductivityLoss: number;
  recoverableValue: number;
  burnoutDragPercent: number;
  meetingInefficiencyCost: number;
  overtimeInefficiencyCost: number;
  recommendation: string;
}

export interface DelayCostAnalysis {
  projectId: string;
  projectName: string;
  teamName: string;
  expectedDelayCost: number;
  revenueAtRisk: number;
  operationalCostIncrease: number;
  overtimeCost: number;
  deliveryPenaltyRisk: number;
  clientChurnCost: number;
  mitigatedCost: number;
  severity: RoiSeverity;
}

export interface RoiForecastPoint {
  month: number;
  baselineCost: number;
  optimizedCost: number;
  cumulativeSavings: number;
  roiPercent: number;
  confidence: number;
}

export interface RoiRecommendation {
  recommendationId: string;
  category: string;
  title: string;
  action: string;
  rationale: string;
  expectedSavings: number;
  roiMultiplier: number;
  confidence: number;
  sourceSystems: string[];
  evidence: string[];
}

export interface ExecutiveInsight {
  title: string;
  message: string;
  financialImpact: number;
  severity: RoiSeverity;
  confidence: number;
}

export interface RoiSummary {
  baselineAnnualLoss: number;
  optimizedAnnualLoss: number;
  netSavings: number;
  roiPercent: number;
  paybackMonths: number;
  replacementCostExposure: number;
  productivityLossExposure: number;
  projectDelayExposure: number;
  hrOperationalSavings: number;
  streamSequence: number;
}

export interface RoiResponse {
  model: string;
  generatedAt: string;
  horizonMonths: number;
  replacementCosts: ReplacementCostAnalysis[];
  productivityLosses: ProductivityLossAnalysis[];
  delayCosts: DelayCostAnalysis[];
  recommendations: RoiRecommendation[];
  executiveInsights: ExecutiveInsight[];
  forecast: RoiForecastPoint[];
  summary: RoiSummary;
  storage: string;
}
