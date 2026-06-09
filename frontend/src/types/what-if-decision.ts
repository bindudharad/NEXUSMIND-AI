export type WhatIfScenarioType =
  | "hiring"
  | "layoff"
  | "budget_reduction"
  | "major_client_loss"
  | "international_expansion"
  | "engineer_resignation"
  | "new_product_launch"
  | "department_restructure"
  | "revenue_drop"
  | "custom";

export type WhatIfRiskLevel = "low" | "medium" | "high" | "critical";

export interface WhatIfScenarioRequest {
  scenarioId: string;
  scenarioName: string;
  question: string;
  scenarioType: WhatIfScenarioType;
  horizonMonths: number;
  employeeDelta: number;
  targetDepartment: string;
  targetRegion: string;
  budgetDeltaPercent: number;
  revenueDeltaPercent: number;
  clientLossPercent: number;
  expansionInvestment: number;
  newProductInvestment: number;
  affectedClient: string;
  notes: string;
}

export interface WhatIfScenarioRecord {
  createdAt: string;
  scenario: WhatIfScenarioRequest;
  simulation: WhatIfSimulationResponse;
}

export interface WhatIfImpactMetric {
  label: string;
  baseline: number;
  projected: number;
  delta: number;
  unit: string;
  confidence: number;
  explanation: string;
}

export interface WhatIfRiskItem {
  riskId: string;
  category: "financial" | "workforce" | "delivery" | "client" | "operational" | "strategic";
  title: string;
  probability: number;
  impact: number;
  level: WhatIfRiskLevel;
  mitigation: string;
}

export interface WhatIfRecommendation {
  recommendationId: string;
  action: string;
  category: string;
  priority: WhatIfRiskLevel;
  reason: string;
  expectedBenefit: string;
  ownerAgent: string;
  confidence: number;
}

export interface WhatIfScenarioComparison {
  scenarioId: string;
  scenarioName: string;
  riskScore: number;
  upsideScore: number;
  costScore: number;
  readinessScore: number;
  recommendation: string;
}

export type WhatIfFutureBranchName =
  | "best_case"
  | "expected_case"
  | "worst_case"
  | "optimistic_case"
  | "pessimistic_case"
  | "ai_recommended_case";

export interface WhatIfFutureBranch {
  caseName: WhatIfFutureBranchName;
  probability: number;
  successProbability: number;
  riskScore: number;
  revenueDelta: number;
  productivityDelta: number;
  burnoutDelta: number;
  deliveryConfidence: number;
  readinessScore: number;
  recommendation: string;
  explanation: string;
}

export interface WhatIfTimelinePoint {
  month: number;
  revenue: number;
  cost: number;
  profit: number;
  productivity: number;
  burnout: number;
  deliveryConfidence: number;
  riskScore: number;
}

export interface WhatIfCapacityPlan {
  workstations: number;
  meetingRooms: number;
  softwareLicenses: number;
  cloudCostDelta: number;
  equipmentCost: number;
  officeCapacityRisk: number;
  plan: string[];
}

export interface WhatIfAgentContribution {
  agent: string;
  role: string;
  finding: string;
  recommendation: string;
  confidence: number;
  sourceSystems: string[];
}

export interface WhatIfDigitalTwinSync {
  twin: "employee" | "team" | "department" | "project" | "company";
  entityCount: number;
  update: string;
  status: "synced" | "projected" | "watch";
}

export interface ExecutiveImpactTeam {
  teamName: string;
  department: string;
  impactScore: number;
  shortageScore: number;
  delayRisk: number;
  burnoutRisk: number;
  knowledgeLossRisk: number;
  reason: string;
}

export interface ExecutiveImpactRecoveryStrategy {
  immediateActions: string[];
  shortTermRecovery: string[];
  longTermRecovery: string[];
  riskReductionActions: string[];
  executiveRecommendations: string[];
}

export interface ExecutiveImpactHiringRequirement {
  requiredHires: number;
  priority: WhatIfRiskLevel;
  skillsNeeded: string[];
  targetTeams: string[];
  urgencyDays: number;
  rationale: string;
}

export interface ExecutiveImpactAgentContribution {
  agent: string;
  responsibility: string;
  finding: string;
  recommendation: string;
  confidence: number;
}

export interface ExecutiveImpactForecastPoint {
  label: string;
  financialLoss: number;
  delayProbability: number;
  workforceCapacity: number;
  recoveryProgress: number;
}

export interface ExecutiveImpactAnalysisPanel {
  panelTitle: string;
  triggerType: "what_if_simulation" | "crisis_simulation" | "workforce_event" | "revenue_event" | "risk_event" | "strategic_decision";
  scenarioName: string;
  generatedAt: string;
  financialLoss: number;
  revenueImpactPercent: number;
  profitImpactPercent: number;
  costIncrease: number;
  productivityCost: number;
  delayProbability: number;
  mostAffectedTeams: ExecutiveImpactTeam[];
  recoveryStrategy: ExecutiveImpactRecoveryStrategy;
  hiringRequirements: ExecutiveImpactHiringRequirement;
  riskLevel: WhatIfRiskLevel;
  confidenceScore: number;
  twinUpdates: string[];
  agentCouncil: ExecutiveImpactAgentContribution[];
  forecastPoints: ExecutiveImpactForecastPoint[];
  sourceSystems: string[];
  finalVerdict: string;
}

export interface WhatIfSimulationResponse {
  model: string;
  generatedAt: string;
  scenario: WhatIfScenarioRequest;
  executiveSummary: string;
  riskLevel: WhatIfRiskLevel;
  successProbability: number;
  decisionReadinessScore: number;
  financialImpact: WhatIfImpactMetric[];
  workforceImpact: WhatIfImpactMetric[];
  productivityImpact: WhatIfImpactMetric[];
  burnoutImpact: WhatIfImpactMetric[];
  infrastructureImpact: WhatIfCapacityPlan;
  riskAnalysis: WhatIfRiskItem[];
  recommendations: WhatIfRecommendation[];
  timeline: WhatIfTimelinePoint[];
  scenarioComparison: WhatIfScenarioComparison[];
  futureBranches: WhatIfFutureBranch[];
  executiveImpactAnalysis: ExecutiveImpactAnalysisPanel;
  digitalTwinSync: WhatIfDigitalTwinSync[];
  agentCouncil: WhatIfAgentContribution[];
  explanation: string[];
  forecastModels: string[];
  sourceSystems: string[];
  storage: string;
  finalVerdict: string;
}

export interface WhatIfDashboardSummary {
  scenarioCount: number;
  highestRiskScenario: string;
  recommendedStrategy: string;
  averageReadiness: number;
  productionReadinessScore: number;
  innovationScore: number;
  judgeWowFactorScore: number;
  streamSequence: number;
}

export interface WhatIfDecisionDashboardResponse {
  model: string;
  generatedAt: string;
  dashboardName: string;
  summary: WhatIfDashboardSummary;
  scenarios: WhatIfSimulationResponse[];
  scenarioBuilderTemplates: WhatIfScenarioRequest[];
  supportedQuestions: string[];
  componentStatus: Record<string, string>;
  digitalTwinStatus: WhatIfDigitalTwinSync[];
  multiAgentStatus: string;
  forecastModels: string[];
  sourceSystems: string[];
  storage: string;
  finalVerdict: string;
}

export interface WhatIfAssistantResponse {
  model: string;
  generatedAt: string;
  question: string;
  answer: string;
  intent: WhatIfScenarioType;
  simulation: WhatIfSimulationResponse;
  recommendedActions: string[];
  citedEvidence: string[];
  sourceSystems: string[];
  storage: string;
}
