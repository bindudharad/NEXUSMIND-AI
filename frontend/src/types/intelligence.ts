export interface BurnoutSignal {
  department: string;
  burnout: number;
  stress: number;
  attrition: number;
  meetingLoad: number;
  recommendation: string;
}

export interface SecurityEvent {
  id: string;
  title: string;
  actor: string;
  threatScore: number;
  status: string;
  response: string;
}

export interface SimulationScenario {
  id: string;
  scenario: string;
  revenueImpact: string;
  delayProbability: number;
  burnoutDelta: number;
  recoveryPlan: string;
}

export interface SimulationResponse {
  delayProbability: number;
  burnoutDelta: number;
  revenueImpactPercent: number;
  stabilityScore: number;
  recoveryPlan: string;
  productivityLossPercent: number;
  teamCollapseProbability: number;
  affectedDepartments: string[];
  workflowImpacts: Record<string, number>;
  recoveryActions: string[];
  riskPropagationPath: string[];
  forecastModels: string[];
  sourceSystems: string[];
  monteCarlo: SimulationMonteCarloResponse;
}

export interface SimulationMonteCarloResponse {
  runs: number;
  successProbability: number;
  delayProbabilityP50: number;
  delayProbabilityP90: number;
  burnoutDeltaP90: number;
  expectedRevenueImpactPercent: number;
  worstCaseRevenueImpactPercent: number;
  stabilityScoreP10: number;
  stabilityScoreP50: number;
  teamCollapseP90: number;
  riskDistribution: Record<string, number>;
  confidence: number;
}

export interface ExecutiveDirective {
  command: string;
  answer: string;
  confidence: number;
  action: string;
}

export interface AgentTurn {
  agent: string;
  observation: string;
  recommendation: string;
  confidence: number;
  memoryKeys: string[];
  toolCalls: string[];
  workflowTrigger: string | null;
}

export interface AgentCouncilResponse {
  topic: string;
  sharedMemory: string[];
  turns: AgentTurn[];
  decision: string;
  workflowTriggers: string[];
  coordinationScore: number;
}

export interface OrgGraphNode {
  id: string;
  label: string;
  risk: number;
}

export interface OrgGraphEdge {
  source: string;
  target: string;
  strength: number;
}

export interface OrgBrainResponse {
  nodes: OrgGraphNode[];
  edges: OrgGraphEdge[];
  bottlenecks: string[];
  recommendation: string;
}

export interface ModelMetric {
  model: string;
  accuracy: number;
  rocAuc: number;
  f1: number;
  trainedSamples: number;
}

export interface ModelValidationResponse {
  available: boolean;
  metrics: ModelMetric[];
  predictionSample: Record<string, number>;
}

export interface IntelligenceOverview {
  burnoutSignals: BurnoutSignal[];
  securityEvents: SecurityEvent[];
  simulations: SimulationScenario[];
  executiveDirectives: ExecutiveDirective[];
  agentCouncil: AgentCouncilResponse;
  orgBrain: OrgBrainResponse;
}

export interface DigitalTwinEmployee {
  employeeId: string;
  name: string;
  department: string;
  role: string;
  workload: number;
  productivity: number;
  burnoutRisk: number;
  criticality: number;
  skills: string[];
  experienceYears: number;
  performance: number;
  wellnessScore: number;
  attendance: number;
  communicationQuality: number;
  learningProgress: number;
  promotionProbability: number;
  attritionProbability: number;
}

export interface DigitalTwinTeam {
  teamId: string;
  name: string;
  department: string;
  health: number;
  productivity: number;
  collaboration: number;
  risk: number;
  burnout: number;
  deliveryPerformance: number;
  communicationQuality: number;
}

export interface DigitalTwinDepartment {
  departmentId: string;
  name: string;
  headcount: number;
  revenueDependency: number;
  deliveryDependency: number;
  resilience: number;
  performance: number;
  risk: number;
  productivity: number;
  cost: number;
  workload: number;
  hiringNeed: number;
}

export interface DigitalTwinProject {
  projectId: string;
  name: string;
  owningTeam: string;
  progress: number;
  risk: number;
  resources: string[];
  teamAllocation: Record<string, number>;
  timelineForecastDays: number;
  budgetForecastPercent: number;
  delayPrediction: number;
  clientHealth: number;
}

export interface DigitalTwinResource {
  resourceId: string;
  name: string;
  resourceType: string;
  capacity: number;
  utilization: number;
  risk: number;
}

export interface DigitalTwinWorkflow {
  workflowId: string;
  name: string;
  ownerDepartment: string;
  dependencyCount: number;
  baselineDelayRisk: number;
}

export interface DigitalTwinOperation {
  operationId: string;
  name: string;
  owner: string;
  securityHealth: number;
  productivityHealth: number;
  financialHealth: number;
  clientHealth: number;
  knowledgeHealth: number;
}

export interface DigitalTwinGraphEdge {
  source: string;
  target: string;
  relationship: string;
  strength: number;
  riskTransfer: number;
}

export interface DigitalTwinScenarioPreview {
  delayProbability: number;
  burnoutDelta: number;
  revenueImpactPercent: number;
  stabilityScore: number;
  productivityLossPercent: number;
  teamCollapseProbability: number;
  affectedDepartments: string[];
  workflowImpacts: Record<string, number>;
  recoveryActions: string[];
}

export interface DigitalTwinSnapshotResponse {
  model: string;
  generatedAt: string;
  employees: DigitalTwinEmployee[];
  teams: DigitalTwinTeam[];
  departments: DigitalTwinDepartment[];
  projects: DigitalTwinProject[];
  resources: DigitalTwinResource[];
  workflows: DigitalTwinWorkflow[];
  operations: DigitalTwinOperation[];
  graphEdges: DigitalTwinGraphEdge[];
  forecastModels: string[];
  supportedScenarios: string[];
  baseline: DigitalTwinScenarioPreview;
  stressCase: DigitalTwinScenarioPreview;
  sourceSystems: string[];
}

export type EnterpriseScenarioType =
  | "employee_resignation"
  | "project_completion"
  | "hiring_freeze"
  | "team_restructure"
  | "budget_cut"
  | "productivity_change";

export interface ScenarioRiskHeatmapRow {
  department: string;
  risk: number;
  productivity: number;
  workload: number;
  hiringNeed: number;
}

export interface ScenarioImpactVector {
  domain: string;
  impactPercent: number;
  severity: "low" | "medium" | "high" | "critical";
  explanation: string;
}

export interface ScenarioSimulationResponse {
  model: string;
  generatedAt: string;
  scenarioType: EnterpriseScenarioType;
  scenarioSummary: string;
  successProbability: number;
  failureProbability: number;
  productivityImpactPercent: number;
  revenueImpactPercent: number;
  burnoutImpact: number;
  deliveryDelayProbability: number;
  clientImpact: number;
  riskLevel: "low" | "medium" | "high" | "critical";
  requiredEngineers: number;
  requiredBudget: number;
  hiringRequirements: string[];
  knowledgeLossRisk: number;
  riskFactors: string[];
  bottlenecks: string[];
  recommendations: string[];
  forecastModels: string[];
  sourceSystems: string[];
  digitalTwinEntities: string[];
  riskHeatmap: ScenarioRiskHeatmapRow[];
  impactVectors: ScenarioImpactVector[];
  decisionTrace: string[];
  forecastHorizonDays: number;
}

export interface ScenarioDecisionSuiteResponse {
  model: string;
  generatedAt: string;
  scenarios: ScenarioSimulationResponse[];
  executiveRecommendations: string[];
  decisionReadinessScore: number;
  forecastModels: string[];
  sourceSystems: string[];
}
