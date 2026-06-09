export interface TeamCompatibilityPair {
  sourceId: string;
  sourceName: string;
  targetId: string;
  targetName: string;
  compatibilityScore: number;
  collaborationSuccessProbability: number;
  conflictProbability: number;
  productivitySynergy: number;
  communicationCompatibility: number;
  leadershipCompatibility: number;
  burnoutPropagationRisk: number;
  confidence: number;
  chemistryLabel: string;
  evidence: string[];
  recommendation: string;
}

export interface TeamGraphNode {
  employeeId: string;
  name: string;
  role: string;
  department: string;
  cluster: string;
  influenceScore: number;
  stressIndex: number;
  skillCount: number;
}

export interface TeamGraphEdge {
  sourceId: string;
  targetId: string;
  compatibilityScore: number;
  conflictProbability: number;
}

export interface TeamRecommendation {
  teamId: string;
  title: string;
  members: string[];
  leader: string;
  compatibilityScore: number;
  chemistryScore: number;
  skillCoverage: number;
  conflictRisk: number;
  burnoutBalance: number;
  projectedVelocity: number;
  rationale: string;
  warnings: string[];
}

export interface TeamConflictWarning {
  severity: "low" | "medium" | "high" | "critical";
  probability: number;
  employees: string[];
  message: string;
  intervention: string;
}

export interface LeadershipMatch {
  leaderId: string;
  leaderName: string;
  teamScope: string;
  compatibilityScore: number;
  rationale: string;
  watchouts: string[];
}

export interface TeamCompatibilitySummary {
  employeesAnalyzed: number;
  pairsAnalyzed: number;
  averageCompatibility: number;
  averageConflictProbability: number;
  highestCompatibilityPair: string;
  highestRiskPair: string;
  recommendedTeamScore: number;
  streamSequence: number;
}

export interface TeamCompatibilityResponse {
  model: string;
  generatedAt: string;
  projectName: string;
  requiredSkills: string[];
  pairScores: TeamCompatibilityPair[];
  graphNodes: TeamGraphNode[];
  graphEdges: TeamGraphEdge[];
  teamRecommendations: TeamRecommendation[];
  conflictWarnings: TeamConflictWarning[];
  leadershipMatches: LeadershipMatch[];
  chemistryInsights: string[];
  optimizationSuggestions: string[];
  summary: TeamCompatibilitySummary;
  storage: string;
}
