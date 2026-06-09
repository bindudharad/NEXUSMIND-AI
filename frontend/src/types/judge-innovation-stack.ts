export type InnovationStackStatus = "complete" | "working" | "partial" | "missing";
export type InnovationWorkflowStatus = "connected" | "partial" | "missing";

export interface InnovationStackCapabilityAudit {
  capability: string;
  status: InnovationStackStatus;
  score: number;
  requiredSystems: string[];
  verifiedSystems: string[];
  apiRoutes: string[];
  integrationEvidence: string[];
  dynamicOutputs: boolean;
  productionReady: boolean;
}

export interface InnovationStackWorkflow {
  name: string;
  status: InnovationWorkflowStatus;
  trigger: string;
  chain: string[];
  propagation: string[];
  executiveOutcome: string;
  evidence: string[];
}

export interface EnterpriseProblemSolvingAudit {
  problem: string;
  status: InnovationStackStatus;
  decisionSupport: string;
  systems: string[];
  evidence: string[];
}

export interface InnovationStackPerformanceMetric {
  metric: string;
  value: number;
  target: number;
  unit: string;
  status: InnovationStackStatus;
}

export interface CompetitionComparison {
  comparator: string;
  verdict: string;
  evidence: string[];
}

export interface InnovationStackScorecard {
  aiInnovation: number;
  technicalComplexity: number;
  researchValue: number;
  businessValue: number;
  visualImpact: number;
  industryRelevance: number;
  scalability: number;
  judgeAppeal: number;
  productionReadiness: number;
  startupPotential: number;
  minimumScore: number;
}

export interface JudgeWinningInnovationStackResponse {
  model: string;
  generatedAt: string;
  executiveSummary: string;
  aiStatus: InnovationStackStatus;
  predictionStatus: InnovationStackStatus;
  simulationStatus: InnovationStackStatus;
  multiAgentStatus: InnovationStackStatus;
  digitalTwinStatus: InnovationStackStatus;
  selfLearningStatus: InnovationStackStatus;
  analyticsStatus: InnovationStackStatus;
  uiStatus: InnovationStackStatus;
  integrationStatus: InnovationStackStatus;
  scorecard: InnovationStackScorecard;
  capabilityAudit: InnovationStackCapabilityAudit[];
  integrationWorkflows: InnovationStackWorkflow[];
  enterpriseProblemSolving: EnterpriseProblemSolvingAudit[];
  competitionComparison: CompetitionComparison[];
  missingComponents: string[];
  fixedComponents: string[];
  errorsFound: string[];
  errorsFixed: string[];
  performanceMetrics: InnovationStackPerformanceMetric[];
  productionReadinessScore: number;
  innovationScore: number;
  researchScore: number;
  startupPotentialScore: number;
  judgeWowFactorScore: number;
  finalVerdict: "JUDGE-WINNING INNOVATION STACK COMPLETE" | "JUDGE-WINNING INNOVATION STACK GAPS REMAIN";
  finalAnswer: string;
  sourceSystems: string[];
  storage: string;
}
