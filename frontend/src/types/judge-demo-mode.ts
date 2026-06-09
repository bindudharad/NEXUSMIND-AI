export type DemoStatus = "complete" | "running" | "partial" | "missing";

export interface JudgeDemoMetric {
  label: string;
  value: string;
  status: DemoStatus;
  evidence: string;
}

export interface JudgeDemoStep {
  order: number;
  title: string;
  cue: string;
  action: string;
  systems: string[];
  apiRoutes: string[];
  visualSurface: string;
  output: string;
  judgeSignal: string;
  durationSeconds: number;
  status: DemoStatus;
}

export interface JudgeDemoFeatureStatus {
  feature: string;
  status: DemoStatus;
  evidence: string[];
  apiRoutes: string[];
}

export interface JudgeDemoTransformation {
  entity: string;
  baseline: string;
  projected: string;
  severity: "healthy" | "warning" | "critical";
  evidence: string;
}

export interface JudgeDemoAgentLine {
  agent: string;
  line: string;
  confidence: number;
  sourceSystem: string;
}

export interface JudgeDemoShadowStage {
  stage: string;
  title: string;
  signal: string;
  status: DemoStatus;
}

export interface JudgeDemoRecommendation {
  action: string;
  impact: string;
  ownerAgent: string;
  priority: "low" | "medium" | "high" | "critical";
}

export interface JudgeDemoImpossibleMoment {
  scenarioQuestion: string;
  oneButtonLabel: string;
  userAction: string;
  visualTransformations: JudgeDemoTransformation[];
  agentCouncil: JudgeDemoAgentLine[];
  shadowCompany: JudgeDemoShadowStage[];
  executiveRecommendations: JudgeDemoRecommendation[];
  judgeUnderstandsInSeconds: number;
}

export interface JudgeDemoModeResponse {
  model: string;
  generatedAt: string;
  headline: string;
  executiveNarrative: string;
  impossibleMoment: JudgeDemoImpossibleMoment;
  demoSequence: JudgeDemoStep[];
  featureStatus: JudgeDemoFeatureStatus[];
  liveMetrics: JudgeDemoMetric[];
  missingFeaturesFixed: string[];
  runtimeErrorsFixed: string[];
  apiIssuesFixed: string[];
  dashboardIssuesFixed: string[];
  simulationIssuesFixed: string[];
  agentIssuesFixed: string[];
  performanceImprovements: string[];
  securityImprovements: string[];
  errorsFound: string[];
  productionReadinessScore: number;
  innovationScore: number;
  judgeWowFactorScore: number;
  demoReadinessScore: number;
  finalVerdict: "NEXUSMIND AI COMPLETE" | "NEXUSMIND AI DEMO GAPS REMAIN";
  sourceSystems: string[];
  storage: string;
}
