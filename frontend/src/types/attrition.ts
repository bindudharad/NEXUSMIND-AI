export type AttritionRiskLevel = "low" | "medium" | "high" | "critical";
export type AttritionDirection = "increases_attrition" | "reduces_attrition" | "neutral";

export interface AttritionFeatureAttribution {
  feature: string;
  value: number;
  contribution: number;
  direction: AttritionDirection;
  evidence: string;
}

export interface AttritionForecastPoint {
  day: number;
  resignationProbability: number;
  workforceStability: number;
}

export interface AttritionPrediction {
  employeeId: string;
  employeeName: string;
  department: string;
  teamName: string;
  role: string;
  resignationProbability: number;
  confidence: number;
  riskLevel: AttritionRiskLevel;
  estimatedDepartureWindow: string;
  primaryReasons: string[];
  featureAttributions: AttritionFeatureAttribution[];
  burnoutCorrelationMultiplier: number;
  replacementCostExposure: number;
  recommendedInterventions: string[];
  modelProbabilities: Record<string, number>;
  forecast: AttritionForecastPoint[];
}

export interface TeamAttritionTrend {
  teamName: string;
  department: string;
  employeesAnalyzed: number;
  averageAttritionProbability: number;
  highRiskCount: number;
  turnoverPressure: number;
  chainReactionRisk: number;
  moraleSignal: "stable" | "watch" | "unstable" | "critical";
  recommendation: string;
}

export interface AttritionRecommendation {
  recommendationId: string;
  category: string;
  title: string;
  action: string;
  rationale: string;
  impactScore: number;
  confidence: number;
  affectedEmployees: string[];
  evidence: string[];
}

export interface AttritionSummary {
  employeesAnalyzed: number;
  averageResignationProbability: number;
  highRiskEmployees: number;
  criticalRiskEmployees: number;
  workforceStabilityScore: number;
  topRiskEmployee: string;
  estimatedReplacementExposure: number;
  streamSequence: number;
}

export interface AttritionHeatmapPoint {
  employee: string;
  team: string;
  department: string;
  attrition: number;
  stability: number;
  costExposure: number;
  burnoutMultiplier: number;
}

export interface AttritionResponse {
  model: string;
  generatedAt: string;
  horizonDays: number;
  predictions: AttritionPrediction[];
  teamTrends: TeamAttritionTrend[];
  heatmap: AttritionHeatmapPoint[];
  recommendations: AttritionRecommendation[];
  summary: AttritionSummary;
  storage: string;
}
