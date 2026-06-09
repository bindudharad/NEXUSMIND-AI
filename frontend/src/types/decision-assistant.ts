export type DecisionPriority = "low" | "medium" | "high" | "critical";
export type DecisionCategory = "routing" | "risk" | "timeline" | "capacity" | "burnout" | "cost" | "skills";

export interface TeamDecisionRanking {
  rank: number;
  teamId: string;
  teamName: string;
  department: string;
  suitabilityScore: number;
  skillCompatibility: number;
  capacityScore: number;
  workloadImpact: number;
  burnoutRisk: number;
  deliverySuccessProbability: number;
  estimatedCompletionDays: number;
  estimatedCost: number;
  riskScore: number;
  confidence: number;
  rationale: string;
  capabilityDrivers: string[];
  riskDrivers: string[];
  missingSkills: string[];
}

export interface DecisionRiskHeatmapPoint {
  teamName: string;
  metric: string;
  score: number;
  severity: DecisionPriority;
}

export interface DecisionTimelineForecastPoint {
  day: number;
  completionProbability: number;
  delayRisk: number;
  workloadPressure: number;
  confidence: number;
}

export interface DecisionCapabilityForecast {
  teamName: string;
  skillFit: number;
  capacityFit: number;
  deliveryFit: number;
  stabilityFit: number;
  overallCapability: number;
}

export interface DecisionRecommendation {
  title: string;
  category: DecisionCategory;
  priority: DecisionPriority;
  action: string;
  expectedImpact: string;
  confidence: number;
  affectedTeams: string[];
}

export interface DecisionAlert {
  title: string;
  severity: DecisionPriority;
  probability: number;
  impact: string;
  mitigation: string;
}

export interface DecisionSummary {
  recommendedTeam: string;
  recommendedTeamId: string;
  bestTeamScore: number;
  successProbability: number;
  estimatedCompletionDays: number;
  deliveryRisk: number;
  workloadImpact: number;
  skillGapCount: number;
  streamSequence: number;
}

export interface DecisionAssistantResponse {
  model: string;
  generatedAt: string;
  question: string;
  projectName: string;
  horizonDays: number;
  rankings: TeamDecisionRanking[];
  riskHeatmap: DecisionRiskHeatmapPoint[];
  timelineForecast: DecisionTimelineForecastPoint[];
  capabilityForecast: DecisionCapabilityForecast[];
  recommendations: DecisionRecommendation[];
  alerts: DecisionAlert[];
  executiveInsights: string[];
  summary: DecisionSummary;
  sourceSystems: string[];
  storage: string;
}
