export type ShadowScenarioType =
  | "hiring"
  | "revenue_drop"
  | "client_loss"
  | "executive_resignation"
  | "engineering_resignation"
  | "budget_reduction"
  | "market_expansion"
  | "security_incident"
  | "custom";

export type ShadowRiskLevel = "low" | "medium" | "high" | "critical";
export type ShadowSyncStatus = "synced" | "projected" | "watch";
export type ShadowRealityCase =
  | "best_case"
  | "expected_case"
  | "worst_case"
  | "optimistic_case"
  | "pessimistic_case"
  | "ai_recommended_case";

export interface ShadowDecisionSimulationRequest {
  scenarioId: string;
  scenarioName: string;
  question: string;
  scenarioType: ShadowScenarioType;
  horizonMonths: number;
  employeeDelta: number;
  workloadDeltaPercent: number;
  budgetDeltaPercent: number;
  revenueDeltaPercent: number;
  clientLossPercent: number;
  targetDepartment: string;
  targetMarket: string;
  securityIncident: boolean;
  notes: string;
}

export interface ShadowMirrorSummary {
  realTimeMirroringStatus: "active" | "degraded" | "missing";
  syncCompleteness: number;
  employeesMirrored: number;
  teamsMirrored: number;
  departmentsMirrored: number;
  projectsMirrored: number;
  clientsMirrored: number;
  workflowsMirrored: number;
  revenueModeled: number;
  costsModeled: number;
  productivityModeled: number;
  risksModeled: number;
  knowledgeNetworkNodes: number;
  communicationNetworkEdges: number;
  lastSyncAt: string;
  productionReadinessScore: number;
  innovationScore: number;
  judgeWowFactorScore: number;
  streamSequence: number;
}

export interface ShadowCompanyState {
  stateId: string;
  label: string;
  employees: number;
  teams: number;
  departments: number;
  projects: number;
  clients: number;
  revenue: number;
  costs: number;
  productivity: number;
  workforceHealth: number;
  riskScore: number;
  growthScore: number;
  explanation: string;
}

export interface ShadowEmployee {
  employeeId: string;
  name: string;
  role: string;
  department: string;
  skills: string[];
  productivityScore: number;
  burnoutRisk: number;
  growthPotential: number;
  attritionRisk: number;
  leadershipInfluence: number;
  futureReadiness: number;
  twinStatus: ShadowSyncStatus;
}

export interface ShadowProject {
  projectId: string;
  name: string;
  owningTeam: string;
  timelineRisk: number;
  budgetRisk: number;
  dependencyRisk: number;
  resourceShortageRisk: number;
  deliveryConfidence: number;
  predictedDelayWeeks: number;
  twinStatus: ShadowSyncStatus;
}

export interface ShadowDepartment {
  departmentId: string;
  name: string;
  performanceScore: number;
  moraleScore: number;
  productivityScore: number;
  capacityScore: number;
  communicationHealth: number;
  riskScore: number;
  twinStatus: ShadowSyncStatus;
}

export interface ShadowFutureState {
  horizonLabel: "30_days" | "90_days" | "6_months" | "12_months";
  scenarioName: string;
  probability: number;
  confidence: number;
  revenueForecast: number;
  costForecast: number;
  productivityForecast: number;
  workforceHealth: number;
  riskScore: number;
  growthScore: number;
  recommendation: string;
  drivers: string[];
}

export interface ShadowRealitySimulation {
  caseName: ShadowRealityCase;
  probability: number;
  confidence: number;
  riskScore: number;
  growthScore: number;
  revenueDeltaPercent: number;
  workforceDeltaPercent: number;
  summary: string;
  actions: string[];
}

export interface ShadowImpactDelta {
  label: string;
  baseline: number;
  projected: number;
  delta: number;
  unit: string;
  explanation: string;
}

export interface ShadowAgentContribution {
  agent: string;
  role: string;
  finding: string;
  action: string;
  confidence: number;
  sourceSystems: string[];
}

export interface ShadowIntegrationSignal {
  system: string;
  status: "connected" | "projected" | "watch";
  update: string;
  evidence: string[];
}

export interface ShadowRealityVisualization {
  engine: string;
  status: "ready" | "degraded" | "missing";
  realCompanyNodes: number;
  shadowCompanyNodes: number;
  futureBranches: number;
  riskPaths: number;
  growthPaths: number;
  decisionTreeDepth: number;
  renderingStrategy: string;
}

export interface ShadowCompanyStatusReport {
  shadowCompanyStatus: "working" | "partial" | "missing";
  synchronizationEngineStatus: "working" | "partial" | "missing";
  employeeShadowStatus: "working" | "partial" | "missing";
  projectShadowStatus: "working" | "partial" | "missing";
  departmentShadowStatus: "working" | "partial" | "missing";
  futureStateGeneratorStatus: "working" | "partial" | "missing";
  decisionTestingStatus: "working" | "partial" | "missing";
  multiRealitySimulationStatus: "working" | "partial" | "missing";
  aiAgentEcosystemStatus: "working" | "partial" | "missing";
  knowledgeBrainIntegrationStatus: "working" | "partial" | "missing";
  organizationalBrainIntegrationStatus: "working" | "partial" | "missing";
  dashboardStatus: "working" | "partial" | "missing";
  visualizationStatus: "working" | "partial" | "missing";
  digitalTwinIntegrationStatus: "working" | "partial" | "missing";
  missingComponents: string[];
  fixedComponents: string[];
  errorsFound: string[];
  errorsFixed: string[];
  performanceMetrics: Record<string, number>;
  productionReadinessScore: number;
  innovationScore: number;
  judgeWowFactorScore: number;
  finalVerdict: string;
}

export interface ShadowDecisionSimulationResponse {
  model: string;
  generatedAt: string;
  scenario: ShadowDecisionSimulationRequest;
  executiveSummary: string;
  baselineOutcome: ShadowCompanyState;
  simulatedOutcome: ShadowCompanyState;
  impactDelta: ShadowImpactDelta[];
  riskLevel: ShadowRiskLevel;
  successProbability: number;
  confidence: number;
  recommendations: string[];
  agentContributions: ShadowAgentContribution[];
  futureStates: ShadowFutureState[];
  multiRealitySimulations: ShadowRealitySimulation[];
  integrationSignals: ShadowIntegrationSignal[];
  sourceSystems: string[];
  storage: string;
  finalVerdict: string;
}

export interface ShadowCompanyDashboardResponse {
  model: string;
  generatedAt: string;
  dashboardName: string;
  executiveBrief: string;
  summary: ShadowMirrorSummary;
  realCompanyState: ShadowCompanyState;
  shadowCompanyState: ShadowCompanyState;
  shadowEmployees: ShadowEmployee[];
  shadowProjects: ShadowProject[];
  shadowDepartments: ShadowDepartment[];
  futureStates: ShadowFutureState[];
  multiRealitySimulations: ShadowRealitySimulation[];
  decisionTestingTemplates: ShadowDecisionSimulationRequest[];
  latestDecisionTest: ShadowDecisionSimulationResponse;
  integrationSignals: ShadowIntegrationSignal[];
  agentEcosystem: ShadowAgentContribution[];
  shadowRealityVisualization: ShadowRealityVisualization;
  statusReport: ShadowCompanyStatusReport;
  supportedQuestions: string[];
  sourceSystems: string[];
  storage: string;
  finalVerdict: string;
}

export interface ShadowCompanyAssistantResponse {
  model: string;
  generatedAt: string;
  question: string;
  answer: string;
  intent: ShadowScenarioType;
  simulation: ShadowDecisionSimulationResponse;
  recommendedActions: string[];
  citedEvidence: string[];
  sourceSystems: string[];
  storage: string;
  finalVerdict: string;
}
