export type VirtualEmployeeScenarioType =
  | "baseline"
  | "hiring_impact"
  | "leadership_change"
  | "organizational_change"
  | "project_outcome"
  | "stress_propagation";

export type VirtualEmployeeRiskLevel = "low" | "medium" | "high" | "critical";
export type VirtualEmployeeExperienceLevel = "junior" | "mid" | "senior" | "lead" | "principal";

export interface WorkforceSimulationRequest {
  question: string;
  scenarioType: VirtualEmployeeScenarioType;
  employeeCount: number;
  hiringCount: number;
  managerCount: number;
  resignationCount: number;
  workloadDeltaPercent: number;
  leadershipStyle: "supportive" | "directive" | "hands_off" | "transformational";
  restructureIntensity: number;
  projectComplexity: number;
  horizonWeeks: number;
  seed: number;
}

export interface VirtualEmployeeIdentity {
  employeeId: string;
  name: string;
  department: string;
  role: string;
  experienceLevel: VirtualEmployeeExperienceLevel;
  experienceYears: number;
}

export interface VirtualEmployeeSkills {
  technicalSkills: Record<string, number>;
  softSkills: Record<string, number>;
  leadershipSkills: Record<string, number>;
}

export interface BigFivePersonality {
  openness: number;
  conscientiousness: number;
  extraversion: number;
  agreeableness: number;
  neuroticism: number;
}

export interface VirtualEmployeePersonality {
  bigFive: BigFivePersonality;
  introversionExtroversion: string;
  collaborativeLevel: number;
  riskTolerance: number;
  learningSpeed: number;
  communicationStyle: string;
  teamCollaborationPreference: string;
  leadershipTendency: number;
}

export interface VirtualEmployeeWorkCharacteristics {
  productivityPattern: string;
  focusPattern: string;
  burnoutSensitivity: number;
  adaptability: number;
  preferredWorkload: number;
  contextSwitchingTolerance: number;
}

export interface VirtualEmployeeBehaviorState {
  workCompletion: number;
  collaboration: number;
  learningProgress: number;
  escalationLikelihood: number;
  conflictLikelihood: number;
  innovationLikelihood: number;
  stressLevel: number;
  burnoutRisk: number;
  productivityScore: number;
  outputQuality: number;
}

export interface VirtualEmployeeAgent {
  identity: VirtualEmployeeIdentity;
  skills: VirtualEmployeeSkills;
  personality: VirtualEmployeePersonality;
  workCharacteristics: VirtualEmployeeWorkCharacteristics;
  behavior: VirtualEmployeeBehaviorState;
  sourceDigitalTwin: string;
}

export interface StressPropagationEdge {
  sourceEmployeeId: string;
  targetEmployeeId: string;
  relationship: "manager_to_team" | "peer_pressure" | "dependency_owner" | "mentor_support";
  stressTransfer: number;
  reason: string;
}

export interface TeamInteractionResult {
  teamName: string;
  collaborationScore: number;
  knowledgeSharingScore: number;
  communicationScore: number;
  cohesionScore: number;
  conflictRisk: number;
  leadershipStability: number;
  explanation: string;
}

export interface WorkforceImpactMetric {
  metric: string;
  baseline: number;
  projected: number;
  delta: number;
  unit: string;
  riskLevel: VirtualEmployeeRiskLevel;
}

export interface WorkforceForecastPoint {
  week: number;
  productivity: number;
  stress: number;
  burnoutRisk: number;
  collaboration: number;
  attritionRisk: number;
  deliveryConfidence: number;
}

export interface ProjectOutcomeSimulation {
  projectName: string;
  deliveryDelayWeeks: number;
  deliveryConfidence: number;
  qualityScore: number;
  resourceRisk: number;
  expectedCompletionWeeks: number;
  explanation: string;
}

export interface WorkforceRecommendation {
  action: string;
  priority: VirtualEmployeeRiskLevel;
  expectedImpact: string;
  ownerAgent: string;
  confidence: number;
}

export interface VirtualWorkforceSummary {
  generatedEmployees: number;
  simulatedWeeks: number;
  averageProductivity: number;
  averageStress: number;
  burnoutRisk: number;
  teamConflictRisk: number;
  deliveryConfidence: number;
  readinessScore: number;
  streamSequence: number;
}

export interface VirtualWorkforceResponse {
  model: string;
  generatedAt: string;
  scenario: WorkforceSimulationRequest;
  summary: VirtualWorkforceSummary;
  virtualEmployees: VirtualEmployeeAgent[];
  teamInteractions: TeamInteractionResult[];
  stressPropagation: StressPropagationEdge[];
  impactMetrics: WorkforceImpactMetric[];
  forecast: WorkforceForecastPoint[];
  projectOutcome: ProjectOutcomeSimulation;
  recommendations: WorkforceRecommendation[];
  assistantSummary: string;
  integrationEvidence: string[];
  supportedQuestions: string[];
  sourceSystems: string[];
  forecastModels: string[];
  storage: string;
}

export interface VirtualWorkforceAssistantResponse {
  model: string;
  generatedAt: string;
  question: string;
  intent: VirtualEmployeeScenarioType;
  answer: string;
  simulation: VirtualWorkforceResponse;
  citedEvidence: string[];
  recommendedActions: string[];
  sourceSystems: string[];
  storage: string;
}
