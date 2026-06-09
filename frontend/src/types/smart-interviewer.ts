export type InterviewRiskLevel = "low" | "medium" | "high" | "critical";
export type HiringDecision = "strong_hire" | "hire" | "consider" | "reject";

export interface GeneratedInterviewQuestion {
  questionId: string;
  interviewType: string;
  difficulty: string;
  question: string;
  targetSkills: string[];
  followUpQuestions: string[];
  evaluationRubric: string[];
}

export interface ResumeAnalysis {
  candidateId: string;
  candidateName: string;
  extractedSkills: string[];
  education: string[];
  certifications: string[];
  experienceYears: number;
  projects: string[];
  summary: string;
  skillGapAnalysis: string[];
  resumeQualityScore: number;
}

export interface TechnicalEvaluation {
  candidateId: string;
  score: number;
  strengths: string[];
  weaknesses: string[];
  followUpQuestions: string[];
  answerEvidence: string[];
}

export interface BehavioralEvaluation {
  candidateId: string;
  leadershipScore: number;
  communicationScore: number;
  teamworkScore: number;
  problemSolvingScore: number;
  adaptabilityScore: number;
  ownershipScore: number;
  overallScore: number;
  evidence: string[];
}

export interface VoiceConfidenceAnalysis {
  candidateId: string;
  confidenceScore: number;
  communicationScore: number;
  clarityScore: number;
  hesitationFrequency: number;
  speakingSpeedWpm: number;
  voiceStability: number;
  evidence: string[];
}

export interface CheatingDetectionReport {
  candidateId: string;
  cheatingRiskScore: number;
  riskLevel: InterviewRiskLevel;
  suspiciousEvents: string[];
  copyPasteEvents: number;
  tabSwitchEvents: number;
  externalAssistanceSignals: number;
  repeatedSimilarityScore: number;
  recommendation: string;
}

export interface SkillProficiencyScore {
  skill: string;
  score: number;
  evidence: string;
}

export interface HiringRecommendation {
  decision: HiringDecision;
  strengths: string[];
  weaknesses: string[];
  risks: string[];
  developmentAreas: string[];
  rationale: string;
  confidence: number;
}

export interface InterviewReportArtifact {
  candidateId: string;
  title: string;
  pdfPath: string;
  docxPath: string;
  sections: string[];
  generatedAt: string;
}

export interface CandidateInterviewRanking {
  rank: number;
  candidateId: string;
  candidateName: string;
  overallScore: number;
  technicalScore: number;
  behavioralScore: number;
  communicationScore: number;
  voiceConfidenceScore: number;
  skillMatchScore: number;
  experienceRelevanceScore: number;
  cheatingRiskScore: number;
  recommendation: HiringRecommendation;
  skillScores: SkillProficiencyScore[];
  resumeAnalysis: ResumeAnalysis;
  technicalEvaluation: TechnicalEvaluation;
  behavioralEvaluation: BehavioralEvaluation;
  voiceAnalysis: VoiceConfidenceAnalysis;
  cheatingReport: CheatingDetectionReport;
  report: InterviewReportArtifact;
  modelScores: Record<string, number>;
}

export interface SmartInterviewerSummary {
  activeInterviews: number;
  topCandidate: string;
  averageOverallScore: number;
  strongHireCount: number;
  highRiskCandidates: number;
  reportCount: number;
  streamSequence: number;
}

export interface SmartInterviewerResponse {
  model: string;
  generatedAt: string;
  roleTitle: string;
  summary: SmartInterviewerSummary;
  generatedQuestions: GeneratedInterviewQuestion[];
  candidateRankings: CandidateInterviewRanking[];
  recommendations: HiringRecommendation[];
  supportedQuestions: string[];
  sourceSystems: string[];
  storage: string;
}

export interface SmartInterviewAssistantResponse {
  model: string;
  generatedAt: string;
  question: string;
  intent: string;
  answer: string;
  confidence: number;
  candidateIds: string[];
  citedEvidence: string[];
  reportArtifacts: InterviewReportArtifact[];
  sourceSystems: string[];
  storage: string;
}
