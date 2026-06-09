export type CompanyHealthPriority = "low" | "medium" | "high" | "critical";
export type CompanyHealthStatus = "optimal" | "stable" | "watch" | "risk" | "critical";

export interface ExecutiveKPI {
  label: string;
  value: string;
  score: number;
  trendDelta: number;
  status: CompanyHealthStatus;
  source: string;
}

export interface TeamHealthScore {
  teamId: string;
  department: string;
  teamName: string;
  headcount: number;
  healthScore: number;
  riskScore: number;
  happinessScore: number;
  productivityScore: number;
  burnoutRisk: number;
  attritionRisk: number;
  projectHealth: number;
  teamEfficiency: number;
  collaborationQuality: number;
  deliveryStability: number;
  operationalRisk: number;
  priority: CompanyHealthPriority;
  confidence: number;
  dominantRisks: string[];
  recommendation: string;
}

export interface CompanyHealthHeatmapPoint {
  department: string;
  teamName: string;
  metric: string;
  healthScore: number;
  riskScore: number;
  intensity: number;
  priority: CompanyHealthPriority;
}

export interface ProductivityTrendPoint {
  label: string;
  productivityScore: number;
  focusStability: number;
  meetingEfficiency: number;
  deliveryStability: number;
}

export interface RiskForecastPoint {
  label: string;
  companyHealthScore: number;
  burnoutRisk: number;
  attritionRisk: number;
  projectFailureRisk: number;
  operationalRisk: number;
}

export interface ProjectHealthScorecard {
  projectId: string;
  department: string;
  teamName: string;
  healthScore: number;
  delayProbability: number;
  deliveryStability: number;
  productivityRisk: number;
  priority: CompanyHealthPriority;
  riskDrivers: string[];
  recommendedAction: string;
}

export interface ExecutiveCompanyRecommendation {
  title: string;
  category: "workforce" | "productivity" | "burnout" | "attrition" | "project" | "communication" | "security" | "operational";
  priority: CompanyHealthPriority;
  expectedImpact: number;
  action: string;
  rationale: string;
  confidence: number;
}

export interface CompanyHealthAlert {
  title: string;
  category: string;
  severity: CompanyHealthPriority;
  probability: number;
  impact: string;
  recommendation: string;
}

export interface CompanyHealthSummary {
  companyHealthScore: number;
  employeeHappinessScore: number;
  productivityScore: number;
  burnoutRisk: number;
  attritionRisk: number;
  projectHealthScore: number;
  collaborationQuality: number;
  deliveryStability: number;
  workforceEngagement: number;
  operationalRisk: number;
  highRiskTeams: number;
  criticalAlerts: number;
  streamSequence: number;
}

export interface CompanyHealthResponse {
  model: string;
  generatedAt: string;
  cycleName: string;
  horizonDays: number;
  executiveKpis: ExecutiveKPI[];
  teamScores: TeamHealthScore[];
  heatmap: CompanyHealthHeatmapPoint[];
  productivityTrends: ProductivityTrendPoint[];
  riskForecasts: RiskForecastPoint[];
  projectScorecards: ProjectHealthScorecard[];
  recommendations: ExecutiveCompanyRecommendation[];
  alerts: CompanyHealthAlert[];
  executiveInsights: string[];
  summary: CompanyHealthSummary;
  sourceSystems: string[];
  storage: string;
}
