import type { ExecutiveImpactAnalysisPanel } from "./what-if-decision";

export type CrisisType =
  | "cyber_attack"
  | "data_breach"
  | "ransomware"
  | "server_failure"
  | "cloud_outage"
  | "database_corruption"
  | "project_collapse"
  | "product_launch_failure"
  | "client_escalation"
  | "major_client_loss"
  | "revenue_crash"
  | "financial_crash"
  | "mass_resignation"
  | "critical_employee_loss"
  | "supply_chain_disruption"
  | "regulatory_incident"
  | "public_relations_crisis";

export type CrisisSeverityBand =
  | "level_1_minor"
  | "level_2_moderate"
  | "level_3_high"
  | "level_4_critical"
  | "level_5_company_threatening";

export type CrisisRiskLevel = "low" | "medium" | "high" | "critical" | "company_threatening";
export type CrisisStatus = "detected" | "triaging" | "contained" | "recovering" | "resolved";
export type CrisisAssistantIntent =
  | "biggest_crisis"
  | "recovery"
  | "affected_systems"
  | "responders"
  | "simulation"
  | "summary"
  | "recommendation";

export interface CrisisImpactAnalysis {
  financialImpact: number;
  workforceImpact: number;
  clientImpact: number;
  securityImpact: number;
  reputationImpact: number;
  operationalImpact: number;
  longTermImpact: number;
  impactRadius: string[];
  businessFunctionsAtRisk: string[];
}

export interface CrisisContainmentAction {
  actionId: string;
  incidentId: string;
  priority: number;
  action: string;
  owner: string;
  targetMinutes: number;
  status: CrisisStatus;
  expectedRiskReduction: number;
  sourceSystems: string[];
}

export interface CrisisRecoveryStep {
  step: number;
  action: string;
  owner: string;
  targetMinutes: number;
  dependencies: string[];
  successCriteria: string;
}

export interface CrisisRecoveryPlan {
  incidentId: string;
  planName: string;
  recoverySequence: CrisisRecoveryStep[];
  resourceRequirements: string[];
  escalationProcedure: string[];
  estimatedRecoveryHours: number;
  recoveryConfidence: number;
}

export interface BusinessContinuityAction {
  actionId: string;
  domain: string;
  action: string;
  continuityOwner: string;
  expectedContinuityPercent: number;
  dependency: string;
  sourceSystems: string[];
}

export interface CrisisIncidentAssessment {
  incidentId: string;
  incidentType: CrisisType;
  title: string;
  classification: string;
  severityScore: number;
  severityBand: CrisisSeverityBand;
  riskLevel: CrisisRiskLevel;
  status: CrisisStatus;
  affectedSystems: string[];
  affectedDepartments: string[];
  affectedClients: string[];
  affectedProjects: string[];
  rootCauseHypothesis: string;
  impact: CrisisImpactAnalysis;
  containmentActions: CrisisContainmentAction[];
  recoveryPlan: CrisisRecoveryPlan;
  executiveSummary: string;
  evidence: string[];
  sourceSystems: string[];
}

export interface CrisisSimulationResult {
  scenarioType: CrisisType;
  question: string;
  financialImpact: number;
  workforceImpact: number;
  operationalImpact: number;
  clientImpact: number;
  securityImpact: number;
  reputationImpact: number;
  longTermImpact: number;
  recoveryHours: number;
  systemsAffected: string[];
  forecastTimeline: Array<Record<string, number | string>>;
  requiredResources: string[];
  recommendedResponse: string[];
  recoveryStrategy: string[];
  executiveRecommendations: string[];
  confidence: number;
  forecastingModels: string[];
  digitalTwinEvidence: string[];
  agentContributions: string[];
  executiveImpactAnalysis: ExecutiveImpactAnalysisPanel;
}

export interface CrisisScenarioRecord {
  scenarioId: string;
  scenarioName: string;
  scenarioType: CrisisType;
  question: string;
  affectedScope: string;
  severityMultiplier: number;
  horizonHours: number;
  createdAt: string;
  executionStatus: "stored" | "executed";
  storage: string;
  sourceSystems: string[];
}

export interface CrisisAgentContribution {
  agent: string;
  domain: string;
  assessment: string;
  recommendedAction: string;
  confidence: number;
}

export interface CrisisScenarioBuilderResponse {
  model: string;
  generatedAt: string;
  scenario: CrisisScenarioRecord;
  simulation: CrisisSimulationResult | null;
  commandCenter: CrisisCommandCenterResponse | null;
  storage: string;
}

export interface ExecutiveCrisisAlert {
  alertId: string;
  incidentId: string;
  severityBand: CrisisSeverityBand;
  title: string;
  message: string;
  channels: string[];
  recipients: string[];
  slaMinutes: number;
  escalationOwner: string;
  acknowledged: boolean;
}

export interface CrisisHeatmapCell {
  domain: string;
  entity: string;
  riskScore: number;
  severityBand: CrisisSeverityBand;
  impactType: string;
  recommendedOwner: string;
}

export interface CrisisRecommendation {
  recommendationId: string;
  priority: CrisisRiskLevel;
  action: string;
  reason: string;
  expectedRiskReduction: number;
  confidence: number;
  sourceSystems: string[];
}

export interface CrisisCommandSummary {
  activeCrises: number;
  criticalCrises: number;
  companyThreateningCrises: number;
  highestSeverityScore: number;
  averageRecoveryHours: number;
  totalFinancialExposure: number;
  affectedSystems: number;
  executiveAlerts: number;
  commandCenterReadiness: number;
  streamSequence: number;
}

export interface CrisisCommandCenterResponse {
  model: string;
  generatedAt: string;
  cycleName: string;
  summary: CrisisCommandSummary;
  activeCrises: CrisisIncidentAssessment[];
  containmentActions: CrisisContainmentAction[];
  recoveryPlans: CrisisRecoveryPlan[];
  businessContinuity: BusinessContinuityAction[];
  simulations: CrisisSimulationResult[];
  executiveAlerts: ExecutiveCrisisAlert[];
  heatmap: CrisisHeatmapCell[];
  recommendations: CrisisRecommendation[];
  agentCouncil: CrisisAgentContribution[];
  productionReadinessScore: number;
  innovationScore: number;
  finalVerdict: string;
  executiveBrief: string;
  supportedQuestions: string[];
  supportedScenarios: CrisisType[];
  sourceSystems: string[];
  storage: string;
}

export interface CrisisAssistantResponse {
  model: string;
  generatedAt: string;
  question: string;
  intent: CrisisAssistantIntent;
  answer: string;
  confidence: number;
  citedIncidents: string[];
  citedEvidence: string[];
  recommendedActions: string[];
  simulation: CrisisSimulationResult | null;
  sourceSystems: string[];
  storage: string;
}
