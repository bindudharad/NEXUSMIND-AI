export type BrainComponentStatus = "active" | "watch" | "degraded" | "missing";
export type BrainVerdict = "LIVING AI COMPANY BRAIN COMPLETE" | "LIVING AI COMPANY BRAIN GAPS REMAIN";

export interface BrainComponentSignal {
  component: string;
  status: BrainComponentStatus;
  score: number;
  summary: string;
  evidence: string[];
  sourceSystems: string[];
}

export interface CompanyAwarenessSnapshot {
  employeesMirrored: number;
  teamsMirrored: number;
  departmentsMirrored: number;
  projectsMirrored: number;
  clientsMirrored: number;
  currentRevenue: number;
  companyHealthScore: number;
  productivityScore: number;
  burnoutRisk: number;
  attritionRisk: number;
  topRiskTeam: string;
  topRiskScore: number;
  activeAlerts: number;
  sourceSystems: string[];
}

export interface MemorySnapshot {
  documentsIndexed: number;
  chunksIndexed: number;
  graphNodes: number;
  graphEdges: number;
  expertsDetected: number;
  incidentsDetected: number;
  solutionsDetected: number;
  sampleQuestion: string;
  sampleAnswer: string;
  citations: string[];
  finalVerdict: string;
  sourceSystems: string[];
}

export interface CausalReasoningStep {
  step: number;
  cause: string;
  effect: string;
  metric: string;
  confidence: number;
  evidence: string[];
}

export interface BrainPredictionSignal {
  domain: "burnout" | "attrition" | "project_delay" | "revenue" | "client_risk" | "operational_risk";
  currentValue: number;
  projectedValue: number;
  delta: number;
  unit: string;
  confidence: number;
  explanation: string;
  sourceSystems: string[];
}

export interface SimulationSnapshot {
  scenario: string;
  successProbability: number;
  riskScore: number;
  revenueImpact: number;
  burnoutChange: number;
  deliveryDelayDays: number;
  aiExplanation: string;
  riskPropagationPath: string[];
  digitalTwinEvidence: string[];
  recommendations: string[];
  sourceSystems: string[];
}

export interface AgentCouncilSnapshot {
  activeAgents: number;
  messages: number;
  workflows: number;
  sharedMemoryRecords: number;
  coordinationScore: number;
  averageResponseMs: number;
  executiveBrief: string;
  councilDiscussion: string[];
  decisions: string[];
  sourceSystems: string[];
}

export interface LearningSnapshot {
  learningEngineStatus: string;
  recommendationAccuracy: number;
  forecastAccuracy: number;
  learningMaturityScore: number;
  driftSignals: number;
  retrainingEvents: number;
  feedbackLoops: number;
  evidence: string[];
  sourceSystems: string[];
}

export interface DigitalTwinBrainSnapshot {
  companyTwinStatus: string;
  activeSimulations: number;
  recommendedScenario: string;
  highestRiskScenario: string;
  mirrorSyncCompleteness: number;
  employeesMirrored: number;
  teamsMirrored: number;
  departmentsMirrored: number;
  projectsMirrored: number;
  twinUpdates: string[];
  sourceSystems: string[];
}

export interface ExecutiveIntelligenceSnapshot {
  answer: string;
  confidence: number;
  recommendedActions: string[];
  citedEvidence: string[];
  currentCompanyFocus: string[];
  sourceSystems: string[];
}

export interface BrainIntegrationEdge {
  source: string;
  target: string;
  event: string;
  evidence: string[];
}

export interface LivingCompanyBrainResponse {
  model: string;
  generatedAt: string;
  companyBrainStatus: BrainComponentStatus;
  organismScore: number;
  awareness: CompanyAwarenessSnapshot;
  memory: MemorySnapshot;
  reasoningChain: CausalReasoningStep[];
  predictions: BrainPredictionSignal[];
  simulation: SimulationSnapshot;
  multiAgent: AgentCouncilSnapshot;
  learning: LearningSnapshot;
  digitalTwin: DigitalTwinBrainSnapshot;
  executiveIntelligence: ExecutiveIntelligenceSnapshot;
  componentSignals: BrainComponentSignal[];
  integrationGraph: BrainIntegrationEdge[];
  missingComponents: string[];
  fixedComponents: string[];
  errorsFound: string[];
  errorsFixed: string[];
  performanceNotes: Record<string, number>;
  productionReadinessScore: number;
  innovationScore: number;
  judgeWowFactorScore: number;
  finalVerdict: BrainVerdict;
  sourceSystems: string[];
  storage: string;
}

export interface LivingCompanyBrainAnswerResponse {
  model: string;
  generatedAt: string;
  question: string;
  answer: string;
  mode: "executive_intelligence" | "enterprise_memory" | "future_simulation";
  confidence: number;
  recommendedActions: string[];
  citedEvidence: string[];
  consultedEngines: string[];
  brainStatus: BrainComponentStatus;
  organismScore: number;
  finalVerdict: BrainVerdict;
  storage: string;
}
