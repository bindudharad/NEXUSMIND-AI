export type TimeMachineScenarioType =
  | "workload_increase"
  | "hiring_freeze"
  | "revenue_drop"
  | "engineer_resignation"
  | "market_expansion"
  | "budget_reduction"
  | "major_client_loss"
  | "custom";

export type TimeMachineRiskLevel = "low" | "medium" | "high" | "critical";

export interface TimeMachineScenarioRequest {
  scenarioId: string;
  scenarioName: string;
  question: string;
  scenarioType: TimeMachineScenarioType;
  horizonMonths: number;
  workloadDeltaPercent: number;
  hiringFreezeMonths: number;
  revenueDeltaPercent: number;
  resignationCount: number;
  budgetDeltaPercent: number;
  marketExpansionInvestment: number;
  clientLossPercent: number;
  affectedDepartment: string;
  notes: string;
}

export interface TimeMachineImpactBlock {
  domain: "workforce" | "financial" | "project" | "client";
  baseline: number;
  projected: number;
  delta: number;
  unit: string;
  riskScore: number;
  explanation: string;
}

export interface TimeMachineTimelinePoint {
  month: number;
  burnoutRisk: number;
  productivity: number;
  attritionRisk: number;
  revenue: number;
  profit: number;
  projectDelayProbability: number;
  clientChurnRisk: number;
  teamHealth: number;
}

export interface TimeMachineRiskPrediction {
  risk: string;
  domain: string;
  probability: number;
  level: TimeMachineRiskLevel;
  driver: string;
  mitigation: string;
}

export interface TimeMachineRecommendation {
  action: string;
  priority: TimeMachineRiskLevel;
  expectedImpact: string;
  ownerAgent: string;
  confidence: number;
}

export interface TimeMachineExplanation {
  summary: string;
  causalDrivers: string[];
  modelEvidence: string[];
  assumptions: string[];
}

export interface TimeMachineAgentContribution {
  agent: string;
  focus: string;
  finding: string;
  confidence: number;
}

export interface TimeMachineSimulationResponse {
  model: string;
  generatedAt: string;
  scenario: TimeMachineScenarioRequest;
  confidence: number;
  riskLevel: TimeMachineRiskLevel;
  successProbability: number;
  workforceImpact: TimeMachineImpactBlock;
  financialImpact: TimeMachineImpactBlock;
  projectImpact: TimeMachineImpactBlock;
  clientImpact: TimeMachineImpactBlock;
  timeline: TimeMachineTimelinePoint[];
  risks: TimeMachineRiskPrediction[];
  recommendations: TimeMachineRecommendation[];
  explanation: TimeMachineExplanation;
  agentContributions: TimeMachineAgentContribution[];
  digitalTwinEvidence: string[];
  forecastModels: string[];
  sourceSystems: string[];
  storage: string;
}

export interface TimeMachineDashboardSummary {
  scenarioCount: number;
  highestRiskScenario: string;
  strongestRecommendation: string;
  averageConfidence: number;
  productionReadinessScore: number;
  streamSequence: number;
}

export interface TimeMachineDashboardResponse {
  model: string;
  generatedAt: string;
  dashboardName: string;
  summary: TimeMachineDashboardSummary;
  scenarios: TimeMachineSimulationResponse[];
  scenarioBuilderTemplates: TimeMachineScenarioRequest[];
  supportedQuestions: string[];
  digitalTwinStatus: Record<string, unknown>;
  forecastModels: string[];
  sourceSystems: string[];
  storage: string;
}

export interface TimeMachineAssistantResponse {
  model: string;
  generatedAt: string;
  question: string;
  intent: TimeMachineScenarioType;
  answer: string;
  simulation: TimeMachineSimulationResponse;
  citedEvidence: string[];
  recommendedActions: string[];
  sourceSystems: string[];
  storage: string;
}
