export type ProjectRiskSeverity = "low" | "medium" | "high" | "critical";

export interface ProjectRiskForecastPoint {
  day: number;
  failureProbability: number;
  delayProbability: number;
  budgetOverrunProbability: number;
  sprintCompletionProbability: number;
  confidence: number;
}

export interface ProjectRiskSignal {
  category: string;
  severity: ProjectRiskSeverity;
  score: number;
  evidence: string;
  recommendation: string;
}

export interface ProjectRecommendation {
  recommendationId: string;
  category: string;
  title: string;
  action: string;
  rationale: string;
  impactScore: number;
  confidence: number;
  affectedProjects: string[];
  sourceSystems: string[];
  evidence: string[];
}

export interface ProjectFailurePrediction {
  projectId: string;
  projectName: string;
  department: string;
  teamName: string;
  failureProbability: number;
  deadlineMissProbability: number;
  budgetOverrunProbability: number;
  teamCollapseRisk: number;
  productivitySlowdown: number;
  resourceShortageImpact: number;
  burnoutImpact: number;
  communicationBottleneckRisk: number;
  dependencyFailureImpact: number;
  operationalInstability: number;
  confidence: number;
  healthScore: number;
  forecast: ProjectRiskForecastPoint[];
  riskSignals: ProjectRiskSignal[];
  recommendations: ProjectRecommendation[];
}

export interface ProjectFailureSummary {
  projectsAnalyzed: number;
  averageFailureProbability: number;
  averageDelayProbability: number;
  criticalProjects: number;
  highestRiskProject: string;
  averageHealthScore: number;
  streamSequence: number;
}

export interface ProjectFailureHeatmapPoint {
  project: string;
  team: string;
  failure: number;
  delay: number;
  budget: number;
  burnout: number;
  resources: number;
  health: number;
}

export interface ProjectFailureResponse {
  model: string;
  generatedAt: string;
  horizonDays: number;
  predictions: ProjectFailurePrediction[];
  portfolioRecommendations: ProjectRecommendation[];
  heatmap: ProjectFailureHeatmapPoint[];
  summary: ProjectFailureSummary;
  storage: string;
}
