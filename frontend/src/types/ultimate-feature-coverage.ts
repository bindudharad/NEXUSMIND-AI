export type FeatureGroupStatus = "present" | "missing" | "partial" | "broken" | "fixed";
export type IntegrationWorkflowStatus = "connected" | "partial" | "disconnected";

export interface UltimateFeatureGroupAudit {
  groupKey: string;
  featureGroup: string;
  status: FeatureGroupStatus;
  present: boolean;
  coveragePercent: number;
  requiredCapabilities: string[];
  verifiedComponents: string[];
  backendSystems: string[];
  frontendSurfaces: string[];
  apiRoutes: string[];
  integrationLinks: string[];
  evidence: string[];
  fixedComponents: string[];
  productionReady: boolean;
}

export interface UltimateIntegrationWorkflow {
  name: string;
  status: IntegrationWorkflowStatus;
  trigger: string;
  chain: string[];
  evidence: string[];
  executiveOutcome: string;
}

export interface UltimateFeatureCoverageResponse {
  model: string;
  generatedAt: string;
  platformPositioning: string;
  executiveSummary: string;
  featureStatusTable: UltimateFeatureGroupAudit[];
  integrationWorkflows: UltimateIntegrationWorkflow[];
  missingComponents: string[];
  fixedComponents: string[];
  newComponentsAdded: string[];
  integrationIssuesFound: string[];
  integrationIssuesFixed: string[];
  runtimeErrorsFixed: string[];
  buildErrorsFixed: string[];
  apiErrorsFixed: string[];
  dashboardErrorsFixed: string[];
  agentErrorsFixed: string[];
  simulationErrorsFixed: string[];
  overallCoveragePercent: number;
  aiInnovationScore: number;
  technicalComplexityScore: number;
  researchScore: number;
  startupPotentialScore: number;
  enterpriseReadinessScore: number;
  judgeWowFactorScore: number;
  demoWowFactorAssessment: string;
  finalVerdict: "NEXUSMIND AI COMPLETE" | "NEXUSMIND AI FEATURE COVERAGE GAPS REMAIN";
  sourceSystems: string[];
  storage: string;
  activeGroup?: UltimateFeatureGroupAudit;
  streamSequence?: number;
}
