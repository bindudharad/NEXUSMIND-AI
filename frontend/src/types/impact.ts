export interface EnterpriseImpactSummary {
  netSavings: number;
  baselineAnnualLoss: number;
  roiPercent: number;
  paybackMonths: number;
  platformScore: number;
  capabilitiesReady: number;
  capabilitiesTotal: number;
  realtimeStreams: number;
  recruiterScore: number;
  judgeWowScore: number;
  residualRiskLevel: "low" | "medium" | "high";
}

export interface EnterpriseImpactResponse {
  model: string;
  generatedAt: string;
  summary: EnterpriseImpactSummary;
  topBusinessInsight: string;
  strongestSignal: string;
  proofPoints: string[];
  sourceHistories: string[];
}
