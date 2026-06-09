export type LearningStatus = "ready" | "learning" | "degraded" | "missing";
export type AdaptiveVerdict =
  | "SELF-EVOLVING AI SYSTEM COMPLETE"
  | "ADAPTIVE ENTERPRISE INTELLIGENCE SYSTEM COMPLETE"
  | "SELF-LEARNING GAPS REMAIN";

export interface SelfLearningScorecard {
  learningEngineScore: number;
  adaptiveRecommendationScore: number;
  feedbackLoopScore: number;
  knowledgeEvolutionScore: number;
  agentLearningScore: number;
  digitalTwinLearningScore: number;
  predictionImprovementScore: number;
  productionReadinessScore: number;
  minimumScore: number;
}

export interface LearningComponentStatus {
  component: string;
  status: LearningStatus;
  score: number;
  learningSignalCount: number;
  evidence: string[];
  sourceSystems: string[];
}

export interface LearnedPattern {
  domain: "culture" | "employee_behavior" | "business_pattern";
  pattern: string;
  confidence: number;
  evidence: string[];
  adaptation: string;
}

export interface DecisionOutcomeLearning {
  decision: string;
  outcome: string;
  outcomeScore: number;
  confidenceDelta: number;
  learnedRule: string;
  sourceSystems: string[];
}

export interface FeedbackLoopStatus {
  loop: string;
  status: LearningStatus;
  records: number;
  averageLearningSignal: number;
  confidenceDelta: number;
  adaptation: string;
  storage: string;
}

export interface AdaptiveRecommendationLearning {
  recommendation: string;
  previousConfidence: number;
  adaptedConfidence: number;
  confidenceDelta: number;
  learnedFrom: string[];
  action: string;
}

export interface PredictionAccuracyMetric {
  metric: string;
  baselineAccuracy: number;
  currentAccuracy: number;
  improvementPercent: number;
  evidence: string[];
}

export interface PredictionErrorRecord {
  predictionId: string;
  modelName: string;
  domain: "revenue" | "burnout" | "attrition" | "project_delay" | "risk" | "simulation";
  predictedValue: number;
  actualValue: number;
  absoluteError: number;
  errorPercent: number;
  observedAt: string;
  sourceSystems: string[];
}

export interface ModelEvaluationMetric {
  modelName: string;
  modelType: "forecasting" | "recommendation" | "risk" | "burnout" | "attrition" | "simulation";
  version: string;
  accuracy: number;
  precision: number;
  recall: number;
  f1Score: number;
  mae: number;
  rmse: number;
  status: LearningStatus;
  retrainingRequired: boolean;
  evaluatedAt: string;
  evidence: string[];
}

export interface DriftDetectionSignal {
  driftType: "data_drift" | "concept_drift" | "feature_drift" | "behavioral_drift";
  domain: string;
  driftScore: number;
  threshold: number;
  status: "stable" | "watch" | "retrain";
  retrainingTriggered: boolean;
  evidence: string[];
}

export interface RetrainingEvent {
  eventId: string;
  modelName: string;
  trigger: "accuracy_drop" | "new_data" | "model_drift" | "performance_degradation" | "scheduled_refresh";
  previousVersion: string;
  newVersion: string;
  previousAccuracy: number;
  newAccuracy: number;
  accuracyDelta: number;
  status: "completed" | "scheduled" | "skipped";
  startedAt: string;
  completedAt?: string | null;
  trainingRecords: number;
  evidence: string[];
}

export interface CompanyConditionChange {
  metric: string;
  beforeValue: number;
  afterValue: number;
  changePercent: number;
  sourceSystem: string;
}

export interface StrategyEvolutionRecord {
  oldStrategy: string;
  newStrategy: string;
  reason: string;
  expectedImprovement: number;
  evidence: string[];
}

export interface SelfLearningDemoStage {
  stage: number;
  title: string;
  status: "completed" | "active" | "queued";
  explanation: string;
  evidence: string[];
}

export interface SelfLearningDemoState {
  demoId: string;
  scenario: string;
  initialPrediction: number;
  adaptedPrediction: number;
  predictionDelta: number;
  detectedChanges: CompanyConditionChange[];
  activeDriftTypes: string[];
  retrainedModels: string[];
  previousStrategy: string;
  evolvedStrategy: string;
  strategyEvolution: StrategyEvolutionRecord[];
  digitalTwinSignals: string[];
  agentLearningUpdates: string[];
  executiveExplanation: string;
  stages: SelfLearningDemoStage[];
  completed: boolean;
}

export interface ForecastLearningStatus {
  status: LearningStatus;
  trackedMetrics: string[];
  meanAbsoluteError: number;
  rmse: number;
  forecastAccuracy: number;
  calibrationFactor: number;
  learnedAdjustments: string[];
  evidence: string[];
}

export interface SimulationLearningStatus {
  status: LearningStatus;
  simulationAccuracy: number;
  calibrationDelta: number;
  scenariosCalibrated: number;
  learnedAdjustments: string[];
  evidence: string[];
}

export interface SelfLearningAssistantResponse {
  answer: string;
  confidence: number;
  actions: string[];
  citedEngines: string[];
  learningEvidence: string[];
}

export interface KnowledgeEvolutionStatus {
  status: LearningStatus;
  documentsIndexed: number;
  chunksIndexed: number;
  graphNodes: number;
  graphEdges: number;
  expertsDetected: number;
  incidentsDetected: number;
  solutionsDetected: number;
  staleAssumptionsRetired: number;
  newBestPractices: string[];
  evidence: string[];
}

export interface AgentLearningStatus {
  status: LearningStatus;
  agents: string[];
  sharedMemoryRecords: number;
  messages: number;
  workflows: number;
  learnedPatterns: string[];
  propagatedInsights: string[];
  evidence: string[];
}

export interface DigitalTwinLearningStatus {
  status: LearningStatus;
  twinEntities: string[];
  adaptationSignals: string[];
  scenarioAccuracy: number;
  simulationAccuracy: number;
  evidence: string[];
}

export interface SelfLearningAIResponse {
  model: string;
  generatedAt: string;
  learningEngineStatus: LearningStatus;
  adaptiveAiStatus: LearningStatus;
  recommendationAccuracy: number;
  forecastAccuracy: number;
  knowledgeEvolutionStatus: LearningStatus;
  agentLearningStatus: LearningStatus;
  digitalTwinLearningStatus: LearningStatus;
  scorecard: SelfLearningScorecard;
  components: LearningComponentStatus[];
  cultureInsights: LearnedPattern[];
  employeeBehaviorInsights: LearnedPattern[];
  businessPatternInsights: LearnedPattern[];
  decisionOutcomes: DecisionOutcomeLearning[];
  feedbackLoops: FeedbackLoopStatus[];
  adaptiveRecommendations: AdaptiveRecommendationLearning[];
  predictionErrors: PredictionErrorRecord[];
  modelEvaluations: ModelEvaluationMetric[];
  driftSignals: DriftDetectionSignal[];
  retrainingEvents: RetrainingEvent[];
  demoState?: SelfLearningDemoState | null;
  forecastLearning?: ForecastLearningStatus | null;
  simulationLearning?: SimulationLearningStatus | null;
  knowledgeEvolution: KnowledgeEvolutionStatus;
  agentLearning: AgentLearningStatus;
  digitalTwinLearning: DigitalTwinLearningStatus;
  predictionImprovements: PredictionAccuracyMetric[];
  learningTimeline: string[];
  missingComponents: string[];
  fixedComponents: string[];
  regeneratedComponents: string[];
  productionReadinessScore: number;
  learningMaturityScore: number;
  finalVerdict: AdaptiveVerdict;
  sourceSystems: string[];
  storage: Record<string, string>;
  streamSequence: number;
}
