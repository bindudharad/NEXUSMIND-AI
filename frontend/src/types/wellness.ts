export type WellnessSeverity = "low" | "medium" | "high" | "critical";

export interface TypingBehaviorAnalytics {
  stressScore: number;
  instabilityScore: number;
  cognitiveLoadScore: number;
  fatigueScore: number;
  aggressiveTypingScore: number;
  evidence: string[];
}

export interface WorkPatternWellnessAnalytics {
  overtimePressure: number;
  meetingOverload: number;
  productivityDecline: number;
  focusDeficit: number;
  collaborationRisk: number;
  forecast: string;
}

export interface WellnessHeatmapCell {
  department: string;
  stressScore: number;
  burnoutProbability: number;
  emotionalExhaustion: number;
  moraleScore: number;
  headcount: number;
  recommendation: string;
}

export interface WellnessRecommendation {
  category: string;
  priority: WellnessSeverity;
  action: string;
  expectedImpact: string;
  confidence: number;
}

export interface WellnessRiskAlert {
  category: string;
  severity: WellnessSeverity;
  score: number;
  message: string;
  evidence: string[];
  recommendation: string;
}

export interface WellnessSummary {
  wellnessScore: number;
  stressScore: number;
  burnoutProbability: number;
  emotionalExhaustionProbability: number;
  frustrationScore: number;
  anxietyScore: number;
  motivationDecline: number;
  communicationFatigue: number;
  mentalOverload: number;
  highRiskTeamCount: number;
  streamSequence: number;
}

export interface WellnessAnalysisResponse {
  model: string;
  generatedAt: string;
  employeeId: string;
  employeeName: string;
  department: string;
  role: string;
  nlpModel: string;
  voiceModel: string;
  behavioralModel: string;
  summary: WellnessSummary;
  sentimentSummary: Record<string, string | number>;
  typingAnalytics: TypingBehaviorAnalytics;
  workPatternAnalytics: WorkPatternWellnessAnalytics;
  emotionalHeatmap: WellnessHeatmapCell[];
  recommendations: WellnessRecommendation[];
  riskAlerts: WellnessRiskAlert[];
  executiveInsights: string[];
  storage: string;
}
