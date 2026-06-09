export type LearningPriority = "low" | "medium" | "high" | "critical";

export interface SkillGapInsight {
  employeeId: string;
  employeeName: string;
  role: string;
  department: string;
  missingSkills: string[];
  gapScore: number;
  futureCriticality: number;
  promotionBlockerScore: number;
  rationale: string;
}

export interface CourseRecommendation {
  employeeId: string;
  employeeName: string;
  courseId: string;
  title: string;
  provider: "Coursera" | "Udemy" | "LinkedIn Learning";
  targetSkill: string;
  category: string;
  difficulty: "foundation" | "intermediate" | "advanced" | "expert";
  durationHours: number;
  certification: string;
  recommendationScore: number;
  completionProbability: number;
  careerImpact: number;
  confidence: number;
  rationale: string;
  sourceModel: string;
}

export interface CareerRoadmapStep {
  employeeId: string;
  employeeName: string;
  month: number;
  title: string;
  focusSkills: string[];
  learningActions: string[];
  expectedOutcome: string;
  confidence: number;
}

export interface ProgressForecast {
  employeeId: string;
  employeeName: string;
  targetSkill: string;
  masteryProbability: number;
  certificationCompletionProbability: number;
  estimatedMonthsToProficiency: number;
  productivityLiftEstimate: number;
  confidence: number;
}

export interface TeamUpskillingHeatmapPoint {
  department: string;
  skill: string;
  gapScore: number;
  demandScore: number;
  readinessScore: number;
  employeesImpacted: number;
  priority: LearningPriority;
}

export interface FutureSkillForecast {
  skill: string;
  demandScore: number;
  currentReadiness: number;
  shortageRisk: number;
  forecast: number[];
  rationale: string;
}

export interface LearningAlert {
  title: string;
  priority: LearningPriority;
  probability: number;
  impact: string;
  recommendation: string;
}

export interface LearningSummary {
  employeesAnalyzed: number;
  recommendationsGenerated: number;
  criticalSkillGaps: number;
  averageGapScore: number;
  averageCompletionProbability: number;
  promotionRoadmaps: number;
  workforceReadinessScore: number;
  streamSequence: number;
}

export interface LearningResponse {
  model: string;
  generatedAt: string;
  cycleName: string;
  horizonMonths: number;
  skillGaps: SkillGapInsight[];
  courseRecommendations: CourseRecommendation[];
  careerRoadmaps: CareerRoadmapStep[];
  progressForecasts: ProgressForecast[];
  teamUpskillingHeatmap: TeamUpskillingHeatmapPoint[];
  futureSkillForecasts: FutureSkillForecast[];
  learningAlerts: LearningAlert[];
  executiveInsights: string[];
  summary: LearningSummary;
  sourceSystems: string[];
  storage: string;
}
