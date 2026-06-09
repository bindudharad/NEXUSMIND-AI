export type TechnologyStatus = "ready" | "configured" | "missing" | "error";

export interface TechnologyCheck {
  name: string;
  category: string;
  status: TechnologyStatus;
  details: string;
  evidence: string[];
  remediation: string | null;
}

export interface TechnologyStackSummary {
  total: number;
  ready: number;
  configured: number;
  missing: number;
  errors: number;
  productionReadyScore: number;
}

export interface TechnologyStackResponse {
  summary: TechnologyStackSummary;
  checks: TechnologyCheck[];
  recommendations: string[];
  verifiedAt: string;
}
