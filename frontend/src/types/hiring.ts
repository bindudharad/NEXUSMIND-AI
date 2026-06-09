export type HiringRiskLevel = "low" | "medium" | "high" | "critical";
export type HiringRecommendationLabel = "strong_hire" | "hire" | "hold" | "reject";

export interface SkillGap {
  skill: string;
  severity: "low" | "medium" | "high";
  recommendation: string;
}

export interface HiringFraudSignal {
  signal: string;
  severity: HiringRiskLevel;
  evidence: string;
}

export interface InterviewInsight {
  label: string;
  score: number;
  evidence: string;
}

export interface CandidateRanking {
  rank: number;
  candidateId: string;
  candidateName: string;
  compatibilityScore: number;
  hiringRecommendation: HiringRecommendationLabel;
  confidence: number;
  resumeQualityScore: number;
  semanticMatchScore: number;
  skillMatchScore: number;
  cultureFitScore: number;
  learningPotentialScore: number;
  communicationQualityScore: number;
  experienceQualityScore: number;
  projectRelevanceScore: number;
  leadershipSignalScore: number;
  hiringRiskScore: number;
  matchedSkills: string[];
  missingSkills: string[];
  skillGaps: SkillGap[];
  fraudSignals: HiringFraudSignal[];
  interviewInsights: InterviewInsight[];
  rankingExplanation: string[];
  modelScores: Record<string, number>;
}

export interface RecruiterRecommendation {
  recommendationId: string;
  title: string;
  action: string;
  rationale: string;
  impactScore: number;
  confidence: number;
  candidateIds: string[];
}

export interface HiringTrend {
  label: string;
  value: number;
  severity: HiringRiskLevel;
  explanation: string;
}

export interface HiringSummary {
  candidatesAnalyzed: number;
  averageCompatibility: number;
  topCandidate: string;
  strongHireCount: number;
  skillGapCount: number;
  fraudRiskCount: number;
  streamSequence: number;
}

export interface HiringResponse {
  model: string;
  generatedAt: string;
  roleTitle: string;
  rankings: CandidateRanking[];
  recommendations: RecruiterRecommendation[];
  recruiterTrends: HiringTrend[];
  skillGapHeatmap: Array<Record<string, number | string>>;
  summary: HiringSummary;
  storage: string;
}
