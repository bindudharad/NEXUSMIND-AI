export type ResearchGradeStatus = "fully_implemented" | "partial" | "missing" | "broken";
export type ResearchGradeVerdict =
  | "RESEARCH-GRADE AUTONOMOUS ENTERPRISE INTELLIGENCE PLATFORM"
  | "RESEARCH-GRADE GAPS REMAIN";

export interface ResearchGradeFeatureAudit {
  featureId: number;
  name: string;
  status: ResearchGradeStatus;
  coveragePercent: number;
  present: boolean;
  working: boolean;
  connected: boolean;
  tested: boolean;
  productionReady: boolean;
  requiredCapabilities: string[];
  evidence: string[];
  integrations: string[];
  endpoints: string[];
  dashboards: string[];
}

export interface ResearchGradeIntegrationLink {
  source: string;
  target: string;
  status: ResearchGradeStatus;
  evidence: string[];
}

export interface ResearchGradeScorecard {
  integrationScore: number;
  innovationScore: number;
  enterpriseScore: number;
  researchLevelScore: number;
  judgeWowFactorScore: number;
  productionReadinessScore: number;
  minimumScore: number;
}

export interface ResearchGradePlatformResponse {
  model: string;
  generatedAt: string;
  featureCoverageMatrix: ResearchGradeFeatureAudit[];
  integrationAudit: ResearchGradeIntegrationLink[];
  scorecard: ResearchGradeScorecard;
  errorsFound: string[];
  errorsFixed: string[];
  missingComponents: string[];
  implementedComponents: string[];
  finalVerdict: ResearchGradeVerdict;
  sourceSystems: string[];
  storage: string;
  streamSequence: number;
}
