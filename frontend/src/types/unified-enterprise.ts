export type UnifiedStatus = "connected" | "partial" | "disconnected";
export type UnifiedVerdict = "TRUE AUTONOMOUS AI-DRIVEN ENTERPRISE INTELLIGENCE SYSTEM" | "UNIFICATION GAPS REMAIN";

export interface UnifiedScorecard {
  unifiedPlatformScore: number;
  enterpriseArchitectureScore: number;
  integrationScore: number;
  automationScore: number;
  aiIntelligenceScore: number;
  productionReadinessScore: number;
  minimumScore: number;
}

export interface UnifiedModuleStatus {
  module: string;
  status: UnifiedStatus;
  score: number;
  evidence: string[];
  sharedData: string[];
  apiRoutes: string[];
  boardroomVisible: boolean;
  agentAccessible: boolean;
  workflowConnected: boolean;
}

export interface UnifiedDataLayerItem {
  entity: string;
  status: UnifiedStatus;
  sourceOfTruth: string;
  producers: string[];
  consumers: string[];
  evidence: string[];
}

export interface CrossModuleWorkflow {
  name: string;
  status: UnifiedStatus;
  trigger: string;
  chain: string[];
  autonomousAction: string;
  evidence: string[];
}

export interface AgentCollaborationAudit {
  status: UnifiedStatus;
  agents: string[];
  messages: number;
  sharedMemoryRecords: number;
  workflows: number;
  decisions: number;
  simulations: number;
  evidence: string[];
}

export interface ExecutiveExperienceAudit {
  status: UnifiedStatus;
  dashboard: string;
  panels: string[];
  visibleDomains: string[];
  voiceCommands: string[];
  evidence: string[];
}

export interface UnifiedEnterpriseResponse {
  model: string;
  generatedAt: string;
  scorecard: UnifiedScorecard;
  modulesConnected: string[];
  modulesDisconnected: string[];
  moduleStatus: UnifiedModuleStatus[];
  singleSourceOfTruth: UnifiedDataLayerItem[];
  crossModuleWorkflows: CrossModuleWorkflow[];
  autonomousActions: CrossModuleWorkflow[];
  digitalTwinSyncSources: string[];
  knowledgeBrainSources: string[];
  agentCollaboration: AgentCollaborationAudit;
  executiveExperience: ExecutiveExperienceAudit;
  missingComponents: string[];
  fixedComponents: string[];
  regeneratedComponents: string[];
  executiveExperienceRating: string;
  finalVerdict: UnifiedVerdict;
  proofStatement: string;
  sourceSystems: string[];
  storage: string;
  streamSequence: number;
}
