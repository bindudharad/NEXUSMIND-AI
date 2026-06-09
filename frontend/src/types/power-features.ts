export type PowerFeatureStatus = "ready" | "warning" | "missing" | "error";
export type PowerSeverity = "low" | "medium" | "high" | "critical";
export type ExplanationTarget = "burnout" | "project_delay" | "team_compatibility" | "productivity" | "recommendation";

export interface PowerFeatureCheck {
  name: string;
  category: string;
  status: PowerFeatureStatus;
  details: string;
  evidence: string[];
  remediation: string | null;
}

export interface PowerFeatureAuditResponse {
  model: string;
  generatedAt: string;
  summary: {
    total: number;
    ready: number;
    warnings: number;
    missing: number;
    errors: number;
    powerScore: number;
  };
  checks: PowerFeatureCheck[];
  verdict: string;
}

export interface RealtimeKPI {
  label: string;
  value: number;
  unit: string;
  delta: number;
  severity: PowerSeverity;
  sourceSystem: string;
}

export interface RealtimeEvent {
  eventId: string;
  title: string;
  message: string;
  severity: PowerSeverity;
  sourceSystems: string[];
  createdAt: string;
}

export interface RealtimeAnalyticsResponse {
  model: string;
  generatedAt: string;
  sequence: number;
  mode: "default" | "pressure" | "crisis";
  kpis: RealtimeKPI[];
  events: RealtimeEvent[];
  sourceSystems: string[];
  syncStatus: "streaming" | "ready" | "degraded";
  storage: string;
}

export interface FeatureAttribution {
  feature: string;
  value: number;
  contribution: number;
  direction: "increases_risk" | "reduces_risk" | "neutral";
  importance: number;
  evidence: string;
}

export interface XAIExplanationResponse {
  model: string;
  generatedAt: string;
  target: ExplanationTarget;
  prediction: number;
  baselinePrediction: number;
  confidence: number;
  methods: string[];
  shapValues: FeatureAttribution[];
  limeWeights: FeatureAttribution[];
  explanation: string;
  counterfactuals: Array<{
    action: string;
    expectedPrediction: number;
    impact: number;
    rationale: string;
  }>;
  decisionTrace: string[];
  sourceSystems: string[];
  storage: string;
}

export interface GNNTeamRelationResponse {
  model: string;
  generatedAt: string;
  architecture: string;
  trainingMetrics: Record<string, string | number>;
  nodes: Array<{
    employeeId: string;
    name: string;
    department: string;
    embedding: number[];
    influenceScore: number;
    burnoutSpreadRisk: number;
    compatibilityProjection: number;
    conflictProjection: number;
    leadershipInfluence: number;
  }>;
  edges: Array<{
    sourceId: string;
    targetId: string;
    attentionWeight: number;
    collaborationStrength: number;
    burnoutTransmission: number;
    conflictProbability: number;
    explanation: string;
  }>;
  propagationAlerts: string[];
  recommendations: string[];
  storage: string;
  streamSequence: number;
}

export interface ManagerAssistantResponse {
  model: string;
  generatedAt: string;
  question: string;
  answer: string;
  riskSummary: string;
  recommendedActions: string[];
  contextSources: Array<{
    system: string;
    title: string;
    snippet: string;
    confidence: number;
  }>;
  reasoningTrace: string[];
  confidence: number;
  storage: string;
  streamSequence: number;
}
