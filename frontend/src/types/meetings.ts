export interface MeetingActionItem {
  owner: string;
  task: string;
  deadline: string | null;
  confidence: number;
  evidence: string;
}

export interface MeetingSpeakerAnalytics {
  speaker: string;
  utterances: number;
  wordCount: number;
  participationPercent: number;
  sentimentScore: number;
  stressScore: number;
  toxicityScore: number;
  burnoutScore: number;
  participationFlag: "dominant" | "silent" | "balanced";
}

export interface MeetingProductivityInsight {
  label: string;
  score: number;
  details: string;
  recommendation: string;
}

export interface MeetingRiskSignal {
  category: string;
  severity: "low" | "medium" | "high" | "critical";
  score: number;
  evidence: string[];
  recommendation: string;
}

export interface MeetingTopicCluster {
  topicId: string;
  label: string;
  turnIndices: number[];
  speakers: string[];
  mentions: number;
  semanticRepetitionScore: number;
  unresolved: boolean;
  representativePhrases: string[];
}

export interface MeetingNecessityAssessment {
  verdict: "synchronous_required" | "async_preferred" | "could_have_been_email";
  confidence: number;
  rationale: string;
  signals: string[];
  asyncRecommendation: string;
}

export interface MeetingWasteEconomics {
  currency: string;
  participantCount: number;
  averageHourlyCost: number;
  employeeHoursSpent: number;
  wastedHours: number;
  meetingCost: number;
  wastedCost: number;
  opportunityCost: number;
  weeklyWasteHoursEstimate: number;
  weeklyWasteCostEstimate: number;
}

export interface MeetingOverloadAnalytics {
  department: string;
  meetingLoadScore: number;
  overloadPercent: number;
  burnoutCorrelation: number;
  productivityDragPercent: number;
  recommendedReductionMinutes: number;
  forecast: string;
}

export interface MeetingAnalysisSummary {
  sentimentScore: number;
  stressIndex: number;
  toxicityIndex: number;
  burnoutIndex: number;
  participationImbalance: number;
  productivityScore: number;
  efficiencyScore: number;
  wastePercentage: number;
  actionabilityScore: number;
  repeatedTopicRate: number;
  estimatedWasteHours: number;
  estimatedWasteCost: number;
  actionItemCount: number;
  blockerCount: number;
  streamSequence: number;
}

export interface MeetingAnalysisResponse {
  model: string;
  generatedAt: string;
  meetingId: string;
  title: string;
  durationMinutes: number;
  transcriptTurns: number;
  summaryText: string;
  keyPoints: string[];
  decisions: string[];
  actionItems: MeetingActionItem[];
  blockers: string[];
  speakerAnalytics: MeetingSpeakerAnalytics[];
  productivityInsights: MeetingProductivityInsight[];
  topicClusters: MeetingTopicCluster[];
  necessityAssessment: MeetingNecessityAssessment;
  wasteEconomics: MeetingWasteEconomics;
  overloadAnalytics: MeetingOverloadAnalytics;
  riskSignals: MeetingRiskSignal[];
  recommendations: string[];
  summary: MeetingAnalysisSummary;
  storage: string;
}
