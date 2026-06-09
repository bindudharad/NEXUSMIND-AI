export type FeatureCoverageStatus = "ready" | "warning" | "missing" | "error";

export interface FeatureCoverageCheck {
  name: string;
  category: string;
  status: FeatureCoverageStatus;
  details: string;
  evidence: string[];
  remediation: string | null;
}

export interface FeatureCoverageSummary {
  total: number;
  ready: number;
  warnings: number;
  missing: number;
  errors: number;
  coverageScore: number;
}

export interface FeatureCoverageResponse {
  generatedAt: string;
  summary: FeatureCoverageSummary;
  checks: FeatureCoverageCheck[];
  criticalGaps: string[];
  verdict: string;
}
