export type CompanySimulationScenarioType =
  | "work_from_home_policy"
  | "hiring_freeze"
  | "employee_resignation"
  | "department_restructure"
  | "budget_reduction"
  | "meeting_reduction"
  | "hiring_growth"
  | "revenue_change"
  | "client_loss"
  | "market_expansion";

export type CompanySimulationRiskLevel = "low" | "medium" | "high" | "critical";
export type CompanySimulationFutureBranch = "best_case" | "expected_case" | "worst_case" | "optimistic_case" | "pessimistic_case" | "ai_recommended_case";

export interface CompanySimulationImpactVector {
  productivityChange: number;
  employeeHappinessChange: number;
  attritionRiskChange: number;
  burnoutChange: number;
  recruitmentDifficultyChange: number;
  collaborationChange: number;
  financialImpact: number;
  revenueImpact: number;
  deliveryDelayDays: number;
  operationalRiskChange: number;
  growthImpact: number;
}

export interface CompanySimulationMetricForecast {
  metric: string;
  baseline: number;
  projected: number;
  delta: number;
  unit: string;
  confidence: number;
  model: string;
}

export interface CompanySimulationRiskHeatmapItem {
  domain: string;
  riskScore: number;
  riskLevel: CompanySimulationRiskLevel;
  driver: string;
  mitigation: string;
}

export interface CompanySimulationRecommendation {
  title: string;
  priority: CompanySimulationRiskLevel;
  action: string;
  rationale: string;
  expectedBenefit: string;
  confidence: number;
}

export interface EmployeeMovementFrame {
  month: number;
  label: string;
  hires: number;
  exits: number;
  transfers: number;
  netHeadcountChange: number;
  explanation: string;
}

export interface TeamStressFrame {
  team: string;
  baselineStress: number;
  projectedStress: number;
  riskLevel: CompanySimulationRiskLevel;
  color: string;
  explanation: string;
}

export interface ProjectHealthFrame {
  project: string;
  baselineState: string;
  projectedState: string;
  delayDays: number;
  riskScore: number;
  color: string;
  explanation: string;
}

export interface RevenueEvolutionPoint {
  month: number;
  current: number;
  bestCase: number;
  expectedCase: number;
  worstCase: number;
}

export interface RiskPropagationStep {
  step: number;
  title: string;
  source: string;
  target: string;
  riskScore: number;
  explanation: string;
}

export interface MultiFutureBranch {
  caseName: CompanySimulationFutureBranch;
  probability: number;
  successProbability: number;
  riskScore: number;
  revenueImpact: number;
  workforceHealthDelta: number;
  summary: string;
}

export interface SimulationAgentContribution {
  agent: string;
  role: string;
  finding: string;
  recommendation: string;
  confidence: number;
  sourceSystems: string[];
}

export interface ShadowCompanyStage {
  stage: string;
  label: string;
  healthScore: number;
  riskScore: number;
  revenue: number;
  workforce: number;
  explanation: string;
}

export interface CompanySimulationScenarioResult {
  scenarioId: string;
  scenarioType: CompanySimulationScenarioType;
  question: string;
  executiveSummary: string;
  confidence: number;
  successProbability: number;
  impact: CompanySimulationImpactVector;
  forecasts: CompanySimulationMetricForecast[];
  riskHeatmap: CompanySimulationRiskHeatmapItem[];
  recommendations: CompanySimulationRecommendation[];
  requiredActions: string[];
  resourceAdjustments: string[];
  staffingChanges: string[];
  employeeMovement: EmployeeMovementFrame[];
  teamStressEvolution: TeamStressFrame[];
  projectHealthVisualization: ProjectHealthFrame[];
  revenueEvolution: RevenueEvolutionPoint[];
  riskPropagationPath: RiskPropagationStep[];
  multiFutureBranches: MultiFutureBranch[];
  agentCouncil: SimulationAgentContribution[];
  shadowCompanyStages: ShadowCompanyStage[];
  aiExplanation: string;
  visualizationEngineStatus: "ready" | "degraded";
  digitalTwinEvidence: string[];
  sourceSystems: string[];
  forecastModels: string[];
  comparisonScore: number;
}

export interface CompanySimulationComparisonItem {
  rank: number;
  scenarioId: string;
  scenarioType: CompanySimulationScenarioType;
  label: string;
  score: number;
  successProbability: number;
  riskLevel: CompanySimulationRiskLevel;
  tradeoffSummary: string;
}

export interface CompanySimulationDashboardSummary {
  scenarioCount: number;
  recommendedScenario: string;
  safestScenario: string;
  highestRiskScenario: string;
  averageConfidence: number;
  decisionReadinessScore: number;
  topRisk: string;
  streamSequence: number;
}

export interface CompanySimulationLabResponse {
  model: string;
  generatedAt: string;
  labName: string;
  horizonMonths: number;
  summary: CompanySimulationDashboardSummary;
  scenarios: CompanySimulationScenarioResult[];
  comparison: CompanySimulationComparisonItem[];
  executiveRecommendations: CompanySimulationRecommendation[];
  supportedQuestions: string[];
  sourceSystems: string[];
  forecastModels: string[];
  storage: string;
}

export interface CompanySimulationAssistantResponse {
  model: string;
  generatedAt: string;
  question: string;
  intent: string;
  answer: string;
  confidence: number;
  scenario: CompanySimulationScenarioResult | null;
  comparison: CompanySimulationComparisonItem[];
  recommendedActions: string[];
  citedEvidence: string[];
  sourceSystems: string[];
  storage: string;
}
