export type OrgRiskLevel = "low" | "medium" | "high" | "critical";
export type OrgNodeType = "employee" | "manager" | "team" | "department" | "project" | "location" | "skill";
export type OrgEdgeType = "reports_to" | "collaborates_with" | "works_on" | "mentors" | "communicates_with" | "belongs_to" | "has_skill";
export type OrgScenarioType = "split_team" | "merge_teams" | "reduce_layers" | "create_department" | "rebalance_leadership";
export type OrgAssistantIntent =
  | "bottlenecks"
  | "manager_overload"
  | "reporting_structure"
  | "communication_gaps"
  | "simulation"
  | "skills"
  | "recommendation"
  | "summary";

export interface OrgGraphNode {
  id: string;
  label: string;
  nodeType: OrgNodeType;
  department?: string | null;
  team?: string | null;
  riskScore: number;
  centrality: number;
  metadata: Record<string, string | number>;
}

export interface OrgGraphEdge {
  source: string;
  target: string;
  edgeType: OrgEdgeType;
  weight: number;
  risk: number;
  evidence: string;
}

export interface ManagerLoadInsight {
  managerId: string;
  managerName: string;
  department: string;
  directReports: number;
  spanOfControl: number;
  overloadRisk: number;
  leadershipBottleneckScore: number;
  recommendation: string;
  evidence: string[];
}

export interface ReportingStructureInsight {
  unit: string;
  hierarchyDepth: number;
  excessiveLayers: boolean;
  leadershipBottleneck: string;
  reportingRisk: number;
  recommendation: string;
  evidence: string[];
}

export interface CommunicationFlowInsight {
  sourceUnit: string;
  targetUnit: string;
  pathLength: number;
  bottleneckEmployee: string;
  delayRisk: number;
  recommendation: string;
  evidence: string[];
}

export interface TeamOptimizationRecommendation {
  teamId: string;
  teamName: string;
  currentSize: number;
  recommendedStructure: string;
  expectedProductivityGain: number;
  expectedLatencyReduction: number;
  confidence: number;
  rationale: string;
}

export interface SiloRiskInsight {
  unit: string;
  siloRisk: number;
  externalCollaborationRatio: number;
  knowledgeIsolationScore: number;
  recommendation: string;
  evidence: string[];
}

export interface SkillDistributionInsight {
  skill: string;
  expertCount: number;
  dominantTeam: string;
  concentrationRisk: number;
  singlePointOfFailure: boolean;
  recommendation: string;
  evidence: string[];
}

export interface OrganizationalSimulationResult {
  scenarioType: OrgScenarioType;
  question: string;
  targetTeam: string;
  productivityImpact: number;
  communicationImpact: number;
  costImpact: number;
  collaborationImpact: number;
  riskImpact: number;
  expectedBenefit: string;
  confidence: number;
  requiredActions: string[];
  digitalTwinEvidence: string[];
}

export interface OrganizationalForecast {
  period: "6_months" | "1_year" | "3_years";
  projectedHeadcount: number;
  leadershipRolesNeeded: number;
  departmentsToScale: string[];
  restructureProbability: number;
  forecastConfidence: number;
  forecastModel: string;
}

export interface OrganizationalRecommendation {
  recommendationId: string;
  priority: OrgRiskLevel;
  action: string;
  reason: string;
  expectedImprovement: string;
  confidence: number;
  sourceSystems: string[];
}

export interface OrganizationalOptimizerSummary {
  organizationalHealthScore: number;
  graphNodes: number;
  graphEdges: number;
  overloadedManagers: number;
  communicationBottlenecks: number;
  highSiloUnits: number;
  criticalSkillConcentrations: number;
  restructureRecommendations: number;
  averageDecisionLatencyRisk: number;
  streamSequence: number;
}

export interface OrganizationalOptimizerResponse {
  model: string;
  generatedAt: string;
  cycleName: string;
  summary: OrganizationalOptimizerSummary;
  graphNodes: OrgGraphNode[];
  graphEdges: OrgGraphEdge[];
  managerLoad: ManagerLoadInsight[];
  reportingStructure: ReportingStructureInsight[];
  communicationFlows: CommunicationFlowInsight[];
  teamRecommendations: TeamOptimizationRecommendation[];
  siloRisks: SiloRiskInsight[];
  skillDistribution: SkillDistributionInsight[];
  simulations: OrganizationalSimulationResult[];
  forecasts: OrganizationalForecast[];
  recommendations: OrganizationalRecommendation[];
  executiveBrief: string;
  supportedQuestions: string[];
  sourceSystems: string[];
  storage: string;
}

export interface OrganizationalAssistantResponse {
  model: string;
  generatedAt: string;
  question: string;
  intent: OrgAssistantIntent;
  answer: string;
  confidence: number;
  citedEvidence: string[];
  recommendedActions: string[];
  simulation: OrganizationalSimulationResult | null;
  sourceSystems: string[];
  storage: string;
}
