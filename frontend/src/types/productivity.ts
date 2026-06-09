export type ProductivitySeverity = "low" | "medium" | "high" | "critical";

export interface HourlyProductivityPoint {
  hourLabel: string;
  productivityScore: number;
  focusScore: number;
  efficiencyScore: number;
  leakageMinutes: number;
  energyScore: number;
  deepWorkMinutes: number;
  dominantCause: string;
}

export interface ToolSwitchingAnalytics {
  appSwitchesPerHour: number;
  tabSwitchesPerHour: number;
  contextSwitchPenalty: number;
  overloadedTools: string[];
  fatigueScore: number;
  productivityLossPercent: number;
  insight: string;
}

export interface DistractionAnalytics {
  distractionScore: number;
  idleTimeMinutes: number;
  distractionMinutes: number;
  notificationPressure: number;
  topDistractionSources: string[];
  estimatedLostHours: number;
  insight: string;
}

export interface DeepWorkAnalytics {
  totalDeepWorkHours: number;
  averageDeepWorkBlockMinutes: number;
  interruptionFrequency: number;
  stabilityScore: number;
  disruptionCauses: string[];
  insight: string;
}

export interface EnergyForecastPoint {
  window: string;
  energyScore: number;
  productivityScore: number;
  fatigueRisk: number;
}

export interface ProductivityHeatmapCell {
  window: string;
  leakageScore: number;
  focusScore: number;
  productiveMinutes: number;
  lostMinutes: number;
  dominantCause: string;
}

export interface ProductivityRecommendation {
  category: string;
  priority: ProductivitySeverity;
  action: string;
  expectedImpact: string;
  confidence: number;
}

export interface ProductivityRiskAlert {
  category: string;
  severity: ProductivitySeverity;
  score: number;
  message: string;
  evidence: string[];
  recommendation: string;
}

export interface ProductivitySummary {
  productivityScore: number;
  focusScore: number;
  efficiencyScore: number;
  leakagePercent: number;
  lostProductiveHours: number;
  estimatedLossCost: number;
  toolSwitchingOverload: number;
  distractionScore: number;
  deepWorkStability: number;
  lowFocusWindowCount: number;
  streamSequence: number;
}

export interface ProductivityAnalysisResponse {
  model: string;
  generatedAt: string;
  employeeId: string;
  employeeName: string;
  department: string;
  role: string;
  mlModel: string;
  nlpModel: string;
  behavioralModel: string;
  summary: ProductivitySummary;
  hourlyTrend: HourlyProductivityPoint[];
  toolSwitching: ToolSwitchingAnalytics;
  distractionAnalytics: DistractionAnalytics;
  deepWorkAnalytics: DeepWorkAnalytics;
  energyForecast: EnergyForecastPoint[];
  leakageHeatmap: ProductivityHeatmapCell[];
  recommendations: ProductivityRecommendation[];
  riskAlerts: ProductivityRiskAlert[];
  executiveInsights: string[];
  storage: string;
}
