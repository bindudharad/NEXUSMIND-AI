export type EmotionPriority = "low" | "medium" | "high" | "critical";
export type EmotionHealthStatus = "healthy" | "attention_needed" | "overloaded" | "critical";
export type EmotionScope = "employee" | "team" | "department" | "project" | "location";
export type EmotionMetric = "stress" | "happiness" | "burnout" | "engagement" | "motivation" | "conflict" | "morale";
export type EmotionAssistantIntent =
  | "stress"
  | "burnout"
  | "conflict"
  | "morale"
  | "happiness"
  | "forecast"
  | "motivation"
  | "recommendation"
  | "toxic"
  | "silent"
  | "summary";

export interface EmployeeEmotionScore {
  employeeId: string;
  name: string;
  team: string;
  department: string;
  project: string;
  location: string;
  role: string;
  happinessScore: number;
  stressScore: number;
  motivationScore: number;
  burnoutScore: number;
  engagementScore: number;
  satisfactionScore: number;
  moraleScore: number;
  psychologicalRisk: number;
  sentimentScore: number;
  conflictExposure: number;
  priority: EmotionPriority;
  evidence: string[];
}

export interface TeamEmotionScore {
  team: string;
  department: string;
  headcount: number;
  teamHealthIndex: number;
  healthStatus: EmotionHealthStatus;
  healthColor: string;
  happinessScore: number;
  stressScore: number;
  workloadScore: number;
  collaborationScore: number;
  productivityHealthScore: number;
  motivationScore: number;
  conflictRisk: number;
  burnoutRisk: number;
  engagementScore: number;
  moraleScore: number;
  retentionRisk: number;
  priority: EmotionPriority;
  trend: string;
  recommendation: string;
}

export interface DepartmentEmotionScore {
  department: string;
  headcount: number;
  departmentHealthIndex: number;
  healthStatus: EmotionHealthStatus;
  healthColor: string;
  moraleScore: number;
  burnoutScore: number;
  stressIndex: number;
  motivationIndex: number;
  retentionRisk: number;
  happinessScore: number;
  engagementScore: number;
  conflictRisk: number;
  priority: EmotionPriority;
  recommendation: string;
}

export interface EmotionHeatmapPoint {
  scope: EmotionScope;
  entityId: string;
  label: string;
  department: string;
  metric: EmotionMetric;
  value: number;
  riskScore: number;
  intensity: number;
  priority: EmotionPriority;
  color: string;
}

export interface EmotionHeatmapZone {
  scope: "company" | "department" | "team";
  entityId: string;
  label: string;
  department: string;
  healthIndex: number;
  healthStatus: EmotionHealthStatus;
  color: string;
  stressScore: number;
  burnoutScore: number;
  workloadScore: number;
  moraleScore: number;
  collaborationScore: number;
  productivityHealthScore: number;
  conflictRisk: number;
  forecast30dBurnout: number;
  forecast90dBurnout: number;
  attritionRisk: number;
  trend: "improving" | "stable" | "declining" | "critical";
  explanation: string;
  recommendations: string[];
  twinEvidence: string[];
  agentEvidence: string[];
}

export interface ConflictRiskInsight {
  sourceEntity: string;
  targetEntity: string;
  scope: "employee" | "team" | "department";
  conflictProbability: number;
  communicationBreakdownRisk: number;
  toxicInteractionIndex: number;
  reason: string;
  evidence: string[];
  recommendedAction: string;
}

export interface BurnoutPrediction {
  entityId: string;
  label: string;
  scope: "employee" | "team" | "department";
  burnoutProbability: number;
  overworkRisk: number;
  fatigueTrend: number;
  mentalWorkloadPressure: number;
  forecast30d: number;
  forecast90d: number;
  recommendation: string;
}

export interface MotivationTrend {
  entityId: string;
  label: string;
  scope: "employee" | "team" | "department";
  motivationScore: number;
  trendDelta: number;
  drivers: string[];
  recommendation: string;
}

export interface EmotionForecastPoint {
  period: "30_days" | "90_days" | "6_months" | "1_year";
  metric: EmotionMetric;
  scope: EmotionScope;
  entityId: string;
  label: string;
  projectedScore: number;
  riskProbability: number;
  confidence: number;
  driver: string;
}

export interface EmotionRecommendation {
  title: string;
  category: "workload" | "conflict" | "wellness" | "motivation" | "engagement" | "manager_intervention" | "team_structure" | "retention";
  priority: EmotionPriority;
  action: string;
  rationale: string;
  expectedImprovement: number;
  confidence: number;
  triggeredWorkflow: string;
}

export interface EmotionDataPipelineStatus {
  source:
    | "survey"
    | "feedback"
    | "meeting"
    | "chat"
    | "email_metadata"
    | "performance_review"
    | "engagement"
    | "workload"
    | "project_activity"
    | "attendance";
  signalsProcessed: number;
  privacyControl: string;
  permissionScope: string;
  status: "active" | "limited" | "blocked";
}

export interface TeamEmotionClassification {
  team: string;
  department: string;
  classification: "happy" | "healthy" | "watch" | "toxic";
  score: number;
  reason: string;
  drivers: string[];
  recommendedAction: string;
}

export interface SilentEmployeeRisk {
  employeeId: string;
  name: string;
  team: string;
  department: string;
  isolationRisk: number;
  participationDelta: number;
  communicationWithdrawalScore: number;
  reason: string;
  recommendedAction: string;
}

export interface Emotion3DNode {
  nodeId: string;
  label: string;
  scope: EmotionScope;
  department: string;
  x: number;
  y: number;
  z: number;
  stress: number;
  burnout: number;
  morale: number;
  conflict: number;
  intensity: number;
  color: string;
}

export interface EmotionAgentContribution {
  agent: string;
  domain: string;
  finding: string;
  recommendedAction: string;
  confidence: number;
}

export interface CompanyEmotionMapSummary {
  employeesAnalyzed: number;
  teamsAnalyzed: number;
  departmentsAnalyzed: number;
  highStressHotspots: number;
  highBurnoutHotspots: number;
  highConflictZones: number;
  averageHappiness: number;
  averageStress: number;
  averageBurnout: number;
  averageMotivation: number;
  averageEngagement: number;
  moraleForecast90d: number;
  organizationalHealthScore: number;
  companyHealthStatus: EmotionHealthStatus;
  companyHealthColor: string;
  toxicTeams: number;
  happyTeams: number;
  silentEmployeeRisks: number;
  productionReadinessScore: number;
  innovationScore: number;
  streamSequence: number;
}

export interface CompanyEmotionMapResponse {
  model: string;
  generatedAt: string;
  cycleName: string;
  horizonDays: number;
  employeeScores: EmployeeEmotionScore[];
  teamScores: TeamEmotionScore[];
  departmentScores: DepartmentEmotionScore[];
  heatmap: EmotionHeatmapPoint[];
  heatmapZones: EmotionHeatmapZone[];
  conflictRisks: ConflictRiskInsight[];
  burnoutPredictions: BurnoutPrediction[];
  motivationTrends: MotivationTrend[];
  forecasts: EmotionForecastPoint[];
  recommendations: EmotionRecommendation[];
  dataPipeline: EmotionDataPipelineStatus[];
  privacyControls: string[];
  toxicTeamRisks: TeamEmotionClassification[];
  happyTeamSignals: TeamEmotionClassification[];
  silentEmployeeRisks: SilentEmployeeRisk[];
  emotion3dNodes: Emotion3DNode[];
  agentCouncil: EmotionAgentContribution[];
  assistantPrompts: string[];
  executiveInsights: string[];
  summary: CompanyEmotionMapSummary;
  sourceSystems: string[];
  digitalTwinUpdates: string[];
  workflowTriggers: string[];
  finalVerdict: string;
  storage: string;
}

export interface EmotionAssistantResponse {
  model: string;
  generatedAt: string;
  question: string;
  intent: EmotionAssistantIntent;
  answer: string;
  confidence: number;
  citedEntities: string[];
  recommendedActions: string[];
  evidence: string[];
  sourceSystems: string[];
  storage: string;
}
