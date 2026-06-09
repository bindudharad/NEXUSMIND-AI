export type TalentReadinessLevel = "emerging" | "ready_soon" | "ready_now" | "executive_bench";
export type TalentRiskLevel = "low" | "medium" | "high" | "critical";
export type TalentAssistantIntent =
  | "future_leaders"
  | "top_leader"
  | "influence"
  | "promotion"
  | "innovation"
  | "knowledge"
  | "problem_solving"
  | "summary";

export interface HiddenLeaderRequest {
  cycleName: string;
  horizonMonths: number;
  minCandidateScore: number;
  includeOrganizationalGraph: boolean;
  includeTalentMarketplace: boolean;
  includeInnovationEngine: boolean;
}

export interface HiddenLeaderAssistantRequest {
  question: string;
  sessionId: string;
  horizonMonths: number;
}

export interface TalentDataQualityReport {
  communicationActivity: string;
  collaborationPatterns: string;
  projectContributions: string;
  knowledgeSharing: string;
  mentoringActivity: string;
  problemSolvingHistory: string;
  learningActivity: string;
  innovationContributions: string;
  peerRecognition: string;
  performanceTrends: string;
  qualityScore: number;
  validationNotes: string[];
}

export interface LeadershipScorecard {
  employeeId: string;
  employeeName: string;
  currentRole: string;
  department: string;
  team: string;
  leadershipPotentialScore: number;
  readinessLevel: TalentReadinessLevel;
  growthTrend: "declining" | "stable" | "increasing" | "accelerating";
  confidence: number;
  initiativeTaking: number;
  decisionMaking: number;
  teamCoordination: number;
  conflictResolution: number;
  communicationQuality: number;
  accountability: number;
  reliability: number;
  influence: number;
  evidence: string[];
}

export interface HiddenLeaderCandidate {
  employeeId: string;
  employeeName: string;
  currentRole: string;
  recommendedFutureRole: string;
  leadershipReadiness: TalentReadinessLevel;
  hiddenLeaderScore: number;
  hiddenTalentScore: number;
  influenceScore: number;
  innovationScore: number;
  knowledgeLeadershipScore: number;
  promotionRecommendation: string;
  whyHidden: string;
  evidence: string[];
}

export interface InfluenceAnalysisInsight {
  employeeId: string;
  employeeName: string;
  influenceScore: number;
  consultedByTeams: string[];
  informalAdvisor: boolean;
  connectorScore: number;
  communicationHubScore: number;
  graphEvidence: string[];
}

export interface ProblemSolvingTalentInsight {
  employeeId: string;
  employeeName: string;
  problemSolvingScore: number;
  impactScore: number;
  innovationScore: number;
  strength: string;
  evidence: string[];
}

export interface InnovationLeaderInsight {
  employeeId: string;
  employeeName: string;
  innovationScore: number;
  creativityScore: number;
  strategicThinkingScore: number;
  adoptedIdeaSignal: number;
  evidence: string[];
}

export interface KnowledgeLeaderInsight {
  employeeId: string;
  employeeName: string;
  knowledgeLeadershipScore: number;
  expertiseAreas: string[];
  documentationContributions: number;
  mentorshipSignal: number;
  internalSupportSignal: number;
  evidence: string[];
}

export interface LeadershipForecastPoint {
  employeeId: string;
  employeeName: string;
  forecastMonth: number;
  teamLeadPotential: number;
  managerPotential: number;
  directorPotential: number;
  executivePotential: number;
  readinessScore: number;
}

export interface TalentPromotionRecommendation {
  recommendationId: string;
  employeeId: string;
  employeeName: string;
  priority: TalentRiskLevel;
  targetTrack: string;
  action: string;
  reason: string;
  expectedBusinessImpact: string;
  confidence: number;
}

export interface TalentGraphIntegration {
  communicationGraphStatus: string;
  collaborationGraphStatus: string;
  knowledgeGraphStatus: string;
  organizationalBrainStatus: string;
  influenceRelationshipsAnalyzed: number;
  knowledgeRelationshipsAnalyzed: number;
  graphEvidence: string[];
}

export interface TalentDigitalTwinSync {
  twin: "employee" | "team" | "department" | "company" | "executive_dashboard";
  status: "synced" | "projected" | "watch";
  update: string;
  entityCount: number;
}

export interface TalentAgentContribution {
  agent: string;
  role: string;
  finding: string;
  recommendation: string;
  confidence: number;
  sourceSystems: string[];
}

export interface HiddenLeaderDashboardSummary {
  employeesAnalyzed: number;
  hiddenLeadersFound: number;
  futureManagerCandidates: number;
  futureExecutiveCandidates: number;
  innovationLeaders: number;
  knowledgeLeaders: number;
  averageLeadershipPotential: number;
  productionReadinessScore: number;
  innovationScore: number;
  judgeWowFactorScore: number;
  streamSequence: number;
}

export interface HiddenLeaderDetectionResponse {
  model: string;
  generatedAt: string;
  cycleName: string;
  summary: HiddenLeaderDashboardSummary;
  dataQuality: TalentDataQualityReport;
  leadershipScorecards: LeadershipScorecard[];
  hiddenLeaderCandidates: HiddenLeaderCandidate[];
  influenceAnalysis: InfluenceAnalysisInsight[];
  problemSolvingIntelligence: ProblemSolvingTalentInsight[];
  innovationLeaders: InnovationLeaderInsight[];
  knowledgeLeaders: KnowledgeLeaderInsight[];
  leadershipForecast: LeadershipForecastPoint[];
  promotionRecommendations: TalentPromotionRecommendation[];
  graphIntegration: TalentGraphIntegration;
  digitalTwinSync: TalentDigitalTwinSync[];
  agentCouncil: TalentAgentContribution[];
  supportedQuestions: string[];
  executiveInsights: string[];
  sourceSystems: string[];
  storage: string;
  finalVerdict: string;
}

export interface HiddenLeaderAssistantResponse {
  model: string;
  generatedAt: string;
  question: string;
  intent: TalentAssistantIntent;
  answer: string;
  confidence: number;
  citedEmployees: string[];
  recommendedActions: string[];
  evidence: string[];
  sourceSystems: string[];
  storage: string;
}
