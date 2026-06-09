export interface TeamBuilderMember {
  employeeId: string;
  name: string;
  role: string;
  department: string;
  workStyle: string;
  skills: string[];
  graphCluster: string;
  graphCompatibilityProjection: number;
  graphBurnoutSpreadRisk: number;
  leadershipInfluence: number;
}

export interface OptimizedTeam {
  teamId: string;
  title: string;
  members: TeamBuilderMember[];
  leader: string;
  compatibilityScore: number;
  skillCoverage: number;
  chemistryScore: number;
  conflictProbability: number;
  burnoutBalance: number;
  leadershipBalance: number;
  projectedDeliverySuccess: number;
  graphConfidence: number;
  missingSkills: string[];
  roleMix: string[];
  rationale: string;
  recommendations: string[];
  warnings: string[];
  evidence: string[];
}

export interface SkillBalanceItem {
  skill: string;
  coverageScore: number;
  owners: string[];
  gapRisk: "low" | "medium" | "high" | "critical";
  recommendation: string;
}

export interface ChemistryHeatmapCell {
  source: string;
  target: string;
  compatibilityScore: number;
  communicationScore: number;
  conflictProbability: number;
  burnoutSpreadRisk: number;
  graphAttention: number;
}

export interface LeadershipRecommendation {
  leaderName: string;
  leadershipScore: number;
  scope: string;
  rationale: string;
  watchouts: string[];
}

export interface TeamBuilderRiskAlert {
  severity: "low" | "medium" | "high" | "critical";
  probability: number;
  title: string;
  members: string[];
  intervention: string;
}

export interface TeamBuilderSummary {
  employeesAnalyzed: number;
  combinationsEvaluated: number;
  bestTeamScore: number;
  bestTeamName: string;
  averageConflictProbability: number;
  graphNodes: number;
  graphEdges: number;
  streamSequence: number;
}

export interface TeamBuilderResponse {
  model: string;
  generatedAt: string;
  projectName: string;
  projectType: string;
  requiredSkills: string[];
  optimizedTeams: OptimizedTeam[];
  skillBalance: SkillBalanceItem[];
  chemistryHeatmap: ChemistryHeatmapCell[];
  leadershipRecommendations: LeadershipRecommendation[];
  riskAlerts: TeamBuilderRiskAlert[];
  collaborationAnalytics: string[];
  graphModelMetrics: Record<string, string | number | boolean | null>;
  summary: TeamBuilderSummary;
  storage: string;
}
