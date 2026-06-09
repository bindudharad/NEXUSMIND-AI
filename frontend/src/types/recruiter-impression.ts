export type ImpressionStatus = "elite" | "strong" | "needs_work" | "weak";

export interface ImpressionMetric {
  label: string;
  value: string;
  explanation: string;
}

export interface ImpressionDimension {
  name: string;
  category: string;
  score: number;
  status: ImpressionStatus;
  verdict: string;
  evidence: string[];
  proofPoints: string[];
  upgradeActions: string[];
}

export interface DemoMoment {
  title: string;
  narrative: string;
  proof: string;
  route: string;
  component: string;
}

export interface RecruiterImpressionSummary {
  overallScore: number;
  startupScore: number;
  industryScore: number;
  researchScore: number;
  recruiterScore: number;
  judgeWowScore: number;
  verdict: string;
  strongestSignal: string;
  residualRiskLevel: "low" | "medium" | "high";
  streamSequence: number;
}

export interface RecruiterImpressionResponse {
  model: string;
  generatedAt: string;
  summary: RecruiterImpressionSummary;
  dimensions: ImpressionDimension[];
  metrics: ImpressionMetric[];
  demoMoments: DemoMoment[];
  technicalProof: string[];
  residualRisks: string[];
  storage: string;
}
