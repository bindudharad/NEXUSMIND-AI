export type InnovationPriority = "low" | "medium" | "high" | "critical";

export interface IdeaMiningInsight {
  ideaId: string;
  employeeId: string;
  employeeName: string;
  department: string;
  team: string;
  channel: string;
  ideaCategory: string;
  extractedTheme: string;
  originalityScore: number;
  feasibilityScore: number;
  impactScore: number;
  adoptionProbability: number;
  confidence: number;
  evidence: string[];
  extractedKeywords: string[];
  recommendation: string;
}

export interface EmployeeInnovationScore {
  employeeId: string;
  employeeName: string;
  department: string;
  team: string;
  innovationScore: number;
  originalityScore: number;
  ideaImpactScore: number;
  contributionFrequency: number;
  adoptionRate: number;
  collaborationInfluence: number;
  creativityRank: number;
  topIdea: string;
  evidence: string[];
}

export type TalentPotential = "moderate" | "high" | "very_high" | "exceptional";
export type TalentRiskLevel = "low" | "medium" | "high" | "critical";

export interface HiddenTalentInsight {
  employeeId: string;
  employeeName: string;
  department: string;
  team: string;
  hiddenTalentScore: number;
  potential: TalentPotential;
  underRecognizedGap: number;
  growthTrajectoryScore: number;
  emergingExpertiseScore: number;
  reason: string;
  evidence: string[];
}

export interface LeadershipPotentialInsight {
  employeeId: string;
  employeeName: string;
  department: string;
  team: string;
  leadershipPotential: number;
  teamInfluence: number;
  decisionMakingAbility: number;
  communicationEffectiveness: number;
  ownershipMindset: number;
  futureManagerProbability: number;
  futureArchitectProbability: number;
  futureExecutiveProbability: number;
  confidence: number;
  recommendedTrack: string;
  reason: string;
}

export interface ProblemSolvingInsight {
  employeeId: string;
  employeeName: string;
  department: string;
  team: string;
  problemSolvingScore: number;
  complexIssueResolution: number;
  incidentHandling: number;
  rootCauseAnalysis: number;
  strategicThinking: number;
  strength: string;
  evidence: string[];
}

export interface GrowthTrajectoryForecast {
  employeeId: string;
  employeeName: string;
  currentRole: string;
  expectedFutureRole: string;
  growthForecast: TalentPotential;
  skillGrowth3Months: number;
  careerGrowth6Months: number;
  leadershipGrowth1Year: number;
  innovationGrowth3Years: number;
  confidence: number;
  drivers: string[];
}

export interface TalentRiskInsight {
  employeeId: string;
  employeeName: string;
  department: string;
  team: string;
  criticalTalentRisk: TalentRiskLevel;
  flightRisk: number;
  retentionRisk: number;
  burnoutRisk: number;
  riskReason: string;
  retentionAction: string;
}

export interface PromotionRecommendation {
  employeeId: string;
  employeeName: string;
  targetProgram: string;
  priority: InnovationPriority;
  readinessScore: number;
  action: string;
  reason: string;
  expectedImpact: number;
  confidence: number;
}

export interface TeamInnovationHeatmapPoint {
  department: string;
  team: string;
  innovationScore: number;
  creativityDensity: number;
  adoptionVelocity: number;
  crossFunctionalInfluence: number;
  ideaCount: number;
  priority: InnovationPriority;
}

export interface IdeaImpactForecast {
  ideaId: string;
  title: string;
  department: string;
  team: string;
  predictedBusinessImpact: number;
  productivityLiftPercent: number;
  costSavingEstimate: number;
  adoptionProbability: number;
  confidence: number;
  drivers: string[];
  forecast: number[];
}

export interface InnovationTrendPoint {
  label: string;
  ideaVolume: number;
  averageImpact: number;
  averageOriginality: number;
  adoptionProbability: number;
}

export interface InnovationRecommendation {
  title: string;
  category: "idea_sponsorship" | "prototype" | "collaboration" | "research" | "process" | "recognition";
  priority: InnovationPriority;
  impactScore: number;
  action: string;
  rationale: string;
  confidence: number;
}

export interface InnovationAlert {
  title: string;
  priority: InnovationPriority;
  probability: number;
  impact: string;
  recommendation: string;
}

export interface InnovationSummary {
  ideasAnalyzed: number;
  employeesRanked: number;
  highImpactIdeas: number;
  adoptedOrPilotingIdeas: number;
  averageInnovationScore: number;
  averageOriginalityScore: number;
  forecastedBusinessImpact: number;
  hiddenTalentCount: number;
  futureLeadersCount: number;
  promotionCandidates: number;
  criticalTalentRisks: number;
  averageLeadershipPotential: number;
  averageGrowthVelocity: number;
  streamSequence: number;
}

export interface InnovationResponse {
  model: string;
  generatedAt: string;
  cycleName: string;
  horizonDays: number;
  ideaInsights: IdeaMiningInsight[];
  employeeScores: EmployeeInnovationScore[];
  hiddenTalent: HiddenTalentInsight[];
  leadershipPredictions: LeadershipPotentialInsight[];
  problemSolvingInsights: ProblemSolvingInsight[];
  growthForecasts: GrowthTrajectoryForecast[];
  talentRisks: TalentRiskInsight[];
  promotionRecommendations: PromotionRecommendation[];
  teamHeatmap: TeamInnovationHeatmapPoint[];
  impactForecasts: IdeaImpactForecast[];
  trendPoints: InnovationTrendPoint[];
  recommendations: InnovationRecommendation[];
  alerts: InnovationAlert[];
  executiveInsights: string[];
  summary: InnovationSummary;
  sourceSystems: string[];
  digitalTwinUpdates: string[];
  marketplaceUpdates: string[];
  storage: string;
}

export interface InnovationAssistantResponse {
  model: string;
  generatedAt: string;
  question: string;
  intent: "leaders" | "hidden_talent" | "innovation" | "promotion" | "problem_solving" | "risk" | "growth" | "summary";
  answer: string;
  confidence: number;
  citedEmployees: string[];
  recommendedActions: string[];
  evidence: string[];
  sourceSystems: string[];
  storage: string;
}
