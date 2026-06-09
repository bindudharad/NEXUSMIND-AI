export type UltimateStatus = "ready" | "partial" | "missing" | "failed";
export type UltimateVerdict =
  | "COMPLETE AUTONOMOUS ENTERPRISE INTELLIGENCE & SIMULATION PLATFORM"
  | "ULTIMATE PLATFORM GAPS REMAIN";

export interface PlatformAuditMap {
  backendFiles: number;
  frontendFiles: number;
  apiRouteModules: number;
  serviceModules: number;
  schemaModules: number;
  aiModules: number;
  dashboardComponents: number;
  persistedDataStores: number;
  dependencyFiles: string[];
  apiMap: string[];
  databaseMap: string[];
  frontendComponentMap: string[];
  aiModuleMap: string[];
}

export interface UltimateFeatureAudit {
  featureId: number;
  name: string;
  status: UltimateStatus;
  present: boolean;
  working: boolean;
  connected: boolean;
  tested: boolean;
  productionReady: boolean;
  score: number;
  evidence: string[];
  integrations: string[];
  endpoints: string[];
  dashboards: string[];
}

export interface IntegrationAuditLink {
  source: string;
  target: string;
  status: UltimateStatus;
  evidence: string[];
}

export interface VirtualEmployeeProfile {
  employeeId: string;
  name: string;
  role: string;
  department: string;
  behaviorModel: string;
  workPattern: string;
  productivityProfile: number;
  collaborationProfile: number;
  stressPropagationRisk: number;
  leadershipEffect: number;
}

export interface TimeMachineScenario {
  question: string;
  horizonMonths: number;
  burnoutForecast: number;
  revenueImpactPercent: number;
  productivityImpactPercent: number;
  attritionRisk: number;
  projectDelayProbability: number;
  teamHealthScore: number;
  recommendation: string;
}

export interface GlobalRiskSignal {
  risk: string;
  category: string;
  severity: "low" | "medium" | "high" | "critical";
  score: number;
  strategicInsight: string;
  recommendedAction: string;
  sourceSystems: string[];
}

export interface ProductionReadinessReport {
  score: number;
  authentication: UltimateStatus;
  authorization: UltimateStatus;
  logging: UltimateStatus;
  monitoring: UltimateStatus;
  errorHandling: UltimateStatus;
  ciCd: UltimateStatus;
  evidence: string[];
}

export interface UltimatePlatformScorecard {
  judgeWowFactorScore: number;
  innovationScore: number;
  enterpriseScore: number;
  integrationScore: number;
  securityScore: number;
  performanceScore: number;
  productionReadinessScore: number;
  minimumScore: number;
}

export interface UltimatePlatformResponse {
  model: string;
  generatedAt: string;
  auditMap: PlatformAuditMap;
  featureCoverageReport: UltimateFeatureAudit[];
  integrationReport: IntegrationAuditLink[];
  errorReport: string[];
  securityReport: string[];
  performanceReport: string[];
  productionReadinessReport: ProductionReadinessReport;
  virtualEmployees: VirtualEmployeeProfile[];
  timeMachineScenarios: TimeMachineScenario[];
  globalRiskSignals: GlobalRiskSignal[];
  scorecard: UltimatePlatformScorecard;
  missingComponents: string[];
  fixedComponents: string[];
  regeneratedComponents: string[];
  finalVerdict: UltimateVerdict;
  sourceSystems: string[];
  storage: string;
  streamSequence: number;
}
