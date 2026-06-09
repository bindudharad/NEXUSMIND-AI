export type UniverseStatus = "complete" | "working" | "partial" | "missing";
export type UniverseWorkflowStatus = "connected" | "partial" | "disconnected";

export interface UniverseScorecard {
  architectureScore: number;
  aiInnovationScore: number;
  digitalTwinScore: number;
  multiAgentScore: number;
  simulationScore: number;
  knowledgeBrainScore: number;
  executiveIntelligenceScore: number;
  metaverseScore: number;
  dashboardScore: number;
  securityScore: number;
  performanceScore: number;
  productionReadinessScore: number;
  competitionReadinessScore: number;
  judgeWowFactorScore: number;
  minimumScore: number;
}

export interface UniverseModuleAudit {
  module: string;
  status: UniverseStatus;
  score: number;
  apiRoutes: string[];
  dashboardSurface: string;
  sourceSystems: string[];
  integrationEvidence: string[];
  productionReady: boolean;
}

export interface UniverseConnectivityWorkflow {
  name: string;
  status: UniverseWorkflowStatus;
  trigger: string;
  chain: string[];
  propagatedUpdates: string[];
  executiveOutput: string;
  evidence: string[];
}

export interface UniverseDigitalTwinAudit {
  twin: "employee" | "team" | "department" | "project" | "client" | "company";
  status: UniverseWorkflowStatus;
  sourceOfTruth: string;
  producers: string[];
  consumers: string[];
  propagationExample: string;
  evidence: string[];
}

export interface UniverseAgentAudit {
  agent: string;
  status: UniverseStatus;
  responsibilities: string[];
  memoryKeys: string[];
  tools: string[];
  collaborationEvidence: string[];
}

export interface UniverseDashboardAudit {
  dashboard: string;
  status: UniverseStatus;
  realtime: boolean;
  responsive: boolean;
  connectedModules: string[];
  evidence: string[];
}

export interface UniverseSecurityAudit {
  control: string;
  status: UniverseStatus;
  evidence: string;
  fixed: boolean;
}

export interface UniversePerformanceAudit {
  area: string;
  metric: string;
  value: number;
  target: number;
  status: UniverseStatus;
}

export interface VirtualEnterpriseUniverseResponse {
  model: string;
  generatedAt: string;
  executiveSummary: string;
  scorecard: UniverseScorecard;
  moduleAudit: UniverseModuleAudit[];
  connectivityWorkflows: UniverseConnectivityWorkflow[];
  digitalTwinAudit: UniverseDigitalTwinAudit[];
  agentEcosystem: UniverseAgentAudit[];
  knowledgeBrainAudit: UniverseModuleAudit[];
  organizationalBrainAudit: UniverseModuleAudit[];
  simulationAudit: UniverseModuleAudit[];
  globalIntelligenceAudit: UniverseModuleAudit[];
  metaverseAudit: UniverseModuleAudit[];
  dashboardAudit: UniverseDashboardAudit[];
  securityAudit: UniverseSecurityAudit[];
  performanceAudit: UniversePerformanceAudit[];
  missingFeatures: string[];
  fixedFeatures: string[];
  errorsFound: string[];
  errorsFixed: string[];
  productionReadinessScore: number;
  competitionReadinessScore: number;
  judgeWowFactorScore: number;
  finalVerdict: "AI-POWERED VIRTUAL ENTERPRISE UNIVERSE COMPLETE" | "VIRTUAL ENTERPRISE UNIVERSE GAPS REMAIN";
  finalEvaluation: string;
  sourceSystems: string[];
  storage: string;
  streamSequence: number;
}
