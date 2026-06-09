export type JudgeImpactStatus = "elite" | "strong" | "needs_work" | "weak";
export type JudgeVerdict = "WORLD-CLASS ENTERPRISE AI PLATFORM" | "NEEDS PRODUCT HARDENING";
export type EvaluatorName =
  | "College Project Judge"
  | "Hackathon Judge"
  | "Startup Investor"
  | "Enterprise CTO"
  | "Enterprise CIO"
  | "Product Manager"
  | "AI Researcher"
  | "Recruiter";

export interface EvaluatorAudit {
  evaluator: EvaluatorName;
  innovationScore: number;
  enterpriseReadinessScore: number;
  technicalComplexityScore: number;
  productMaturityScore: number;
  marketPotentialScore: number;
  impressive: string[];
  weak: string[];
  unfinished: string[];
  fakeSignals: string[];
  enterpriseGrade: string[];
  productionBelief: string;
  status: JudgeImpactStatus;
}

export interface JudgeImpactScorecard {
  innovationScore: number;
  enterpriseReadinessScore: number;
  productMaturityScore: number;
  startupPotentialScore: number;
  technicalComplexityScore: number;
  judgeWowFactorScore: number;
  recruiterImpactScore: number;
  productionReadinessScore: number;
  minimumScore: number;
}

export interface ProductAuditDimension {
  name: string;
  score: number;
  status: JudgeImpactStatus;
  evidence: string[];
  improvements: string[];
}

export interface ProductDifferentiation {
  question: string;
  answer: string;
  proofPoints: string[];
}

export interface IntegrationAuditItem {
  integration: string;
  status: "connected" | "partial" | "disconnected";
  evidence: string[];
}

export interface JudgeImpactValidationResponse {
  model: string;
  generatedAt: string;
  scorecard: JudgeImpactScorecard;
  evaluatorAudits: EvaluatorAudit[];
  productAudit: ProductAuditDimension[];
  differentiationReport: ProductDifferentiation[];
  integrationStatus: IntegrationAuditItem[];
  missingComponents: string[];
  fixedComponents: string[];
  regeneratedComponents: string[];
  residualRisks: string[];
  productionReadinessEvidence: string[];
  finalVerdict: JudgeVerdict;
  executiveSummary: string;
  sourceSystems: string[];
  storage: string;
  streamSequence: number;
}
