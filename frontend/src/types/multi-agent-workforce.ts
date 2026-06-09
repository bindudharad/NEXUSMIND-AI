export type AgentName =
  | "HR Agent"
  | "Security Agent"
  | "Finance Agent"
  | "Project Agent"
  | "Productivity Agent"
  | "Client Agent"
  | "Knowledge Agent"
  | "Executive Agent";

export type AgentStatus = "active" | "monitoring" | "coordinating" | "degraded";
export type AgentMemoryType = "short_term" | "long_term" | "context" | "decision_history";
export type AgentRiskLevel = "low" | "medium" | "high" | "critical";
export type AgentWorkflowStatus = "queued" | "running" | "completed" | "escalated";
export type AgentCouncilIntent =
  | "company_health"
  | "burnout"
  | "security"
  | "project"
  | "client"
  | "simulation"
  | "summary"
  | "recommendation";
export type AgentBoardroomPhase = "thinking" | "analysis" | "challenge" | "consensus";
export type AgentBoardroomStatus = "thinking" | "speaking" | "agreed" | "escalated";
export type AgentDebateResolution = "resolved" | "conditional" | "escalated";
export type AgentConsensusVoteType = "support" | "conditional_support" | "oppose";

export interface AgentProfile {
  agentId: string;
  name: AgentName;
  role: string;
  mission: string;
  systemPrompt: string;
  status: AgentStatus;
  deployableEndpoint: string;
  memoryKeys: string[];
  toolPermissions: string[];
  ownedWorkflows: string[];
  contextManagement: string[];
  decisionLogic: string[];
  outputValidation: string[];
  sourceSystems: string[];
}

export interface AgentMemoryRecord {
  memoryId: string;
  agent: AgentName;
  memoryType: AgentMemoryType;
  key: string;
  value: string;
  importance: number;
  createdAt: string;
  sourceSystems: string[];
}

export interface AgentToolExecution {
  executionId: string;
  agent: AgentName;
  toolName: string;
  inputSummary: string;
  outputSummary: string;
  latencyMs: number;
  success: boolean;
  permissionScope: string;
}

export interface AgentMessage {
  messageId: string;
  fromAgent: AgentName;
  toAgent: AgentName;
  topic: string;
  content: string;
  evidence: string[];
  createdAt: string;
}

export interface AgentCouncilTurn {
  agent: AgentName;
  observation: string;
  recommendation: string;
  confidence: number;
  memoryKeys: string[];
  toolCalls: string[];
  workflowTrigger: string;
  dependsOn: AgentName[];
}

export interface AgentTask {
  taskId: string;
  owner: AgentName;
  task: string;
  trigger: string;
  status: AgentWorkflowStatus;
  priority: AgentRiskLevel;
  expectedBusinessImpact: string;
  automationReady: boolean;
}

export interface AgentWorkflowStep {
  step: number;
  agent: AgentName;
  action: string;
  inputContext: string[];
  output: string;
}

export interface AgentWorkflow {
  workflowId: string;
  name: string;
  trigger: string;
  participants: AgentName[];
  status: AgentWorkflowStatus;
  steps: AgentWorkflowStep[];
  finalRecommendation: string;
  expectedRiskReduction: number;
}

export interface AgentDecision {
  decisionId: string;
  title: string;
  riskLevel: AgentRiskLevel;
  recommendation: string;
  rationale: string;
  participatingAgents: AgentName[];
  confidence: number;
  actionPlan: string[];
}

export interface AgentSimulationResult {
  scenarioType: string;
  question: string;
  participatingAgents: AgentName[];
  productivityImpact: number;
  revenueImpactPercent: number;
  delayProbability: number;
  burnoutDelta: number;
  securityRiskDelta: number;
  clientRiskDelta: number;
  recommendedResponse: string[];
  digitalTwinEvidence: string[];
  confidence: number;
}

export interface AgentBoardroomStage {
  stage: number;
  agent: AgentName;
  phase: AgentBoardroomPhase;
  status: AgentBoardroomStatus;
  message: string;
  recommendation: string;
  confidence: number;
  evidence: string[];
  dependsOn: AgentName[];
}

export interface AgentCouncilConsensus {
  finalDecision: string;
  confidence: number;
  ownerAgent: AgentName;
  recommendedActions: string[];
  dissentingRisks: string[];
  digitalTwinEvidence: string[];
  simulationEvidence: string[];
  majorityVote: string;
  riskWeightedScore: number;
  agreementLevel: "low" | "medium" | "high" | "unanimous";
  conflictResolutionSummary: string;
}

export interface AgentReasoningTrace {
  agent: AgentName;
  perspective: string;
  reasoningSummary: string;
  evidenceUsed: string[];
  assumptions: string[];
  uncertainty: string;
  conclusion: string;
  confidence: number;
}

export interface AgentDebateExchange {
  exchangeId: string;
  fromAgent: AgentName;
  toAgent: AgentName;
  disagreement: string;
  challenge: string;
  response: string;
  resolution: AgentDebateResolution;
  disagreementScore: number;
  evidence: string[];
}

export interface AgentConsensusVote {
  agent: AgentName;
  vote: AgentConsensusVoteType;
  riskWeight: number;
  confidence: number;
  rationale: string;
  evidence: string[];
}

export interface AgentResearchMetrics {
  perspectiveDiversityScore: number;
  evidenceCoverageScore: number;
  disagreementCount: number;
  consensusScore: number;
  explainabilityScore: number;
  negotiationRounds: number;
  conflictResolutionStatus: "resolved" | "partially_resolved" | "unresolved";
  reasoningAbstractionLayer: string;
}

export interface AgentAnalytics {
  agent: AgentName;
  averageResponseMs: number;
  usageCount: number;
  recommendationCount: number;
  successRate: number;
  workloadScore: number;
  healthScore: number;
}

export interface AgentCommunicationBusStatus {
  busName: string;
  protocol: string;
  activeChannels: string[];
  messageCount: number;
  averageLatencyMs: number;
  persistence: string;
  failureRecovery: string[];
  status: "ready" | "degraded" | "missing";
}

export interface AgentSharedMemoryStatus {
  memoryStore: string;
  persistent: boolean;
  records: number;
  memoryTypes: AgentMemoryType[];
  retrievalStrategy: string;
  latestDecisionKeys: string[];
  status: "ready" | "degraded" | "missing";
}

export interface AgentMonitoringStatus {
  activeAgents: number;
  averageResponseMs: number;
  averageSuccessRate: number;
  monitoredMetrics: string[];
  realtimeStream: boolean;
  status: "ready" | "degraded" | "missing";
}

export interface AgentSecurityControl {
  control: string;
  status: "enforced" | "warning" | "missing";
  evidence: string;
}

export interface AgentWorkforceSummary {
  activeAgents: number;
  messages: number;
  workflows: number;
  autonomousTasks: number;
  recommendations: number;
  sharedMemoryRecords: number;
  averageAgentHealth: number;
  coordinationScore: number;
  productionReadinessScore: number;
  innovationScore: number;
  streamSequence: number;
}

export interface MultiAgentWorkforceResponse {
  model: string;
  generatedAt: string;
  topic: string;
  summary: AgentWorkforceSummary;
  agents: AgentProfile[];
  councilTurns: AgentCouncilTurn[];
  messages: AgentMessage[];
  memory: AgentMemoryRecord[];
  toolExecutions: AgentToolExecution[];
  autonomousTasks: AgentTask[];
  workflows: AgentWorkflow[];
  decisions: AgentDecision[];
  simulations: AgentSimulationResult[];
  boardroomStages: AgentBoardroomStage[];
  consensus: AgentCouncilConsensus;
  reasoningTraces: AgentReasoningTrace[];
  debateExchanges: AgentDebateExchange[];
  consensusVotes: AgentConsensusVote[];
  researchMetrics: AgentResearchMetrics;
  analytics: AgentAnalytics[];
  communicationBus: AgentCommunicationBusStatus;
  sharedMemoryStatus: AgentSharedMemoryStatus;
  monitoring: AgentMonitoringStatus;
  securityControls: AgentSecurityControl[];
  executiveBrief: string;
  supportedQuestions: string[];
  sourceSystems: string[];
  finalVerdict: string;
  storage: string;
}

export interface AgentCouncilResponse {
  model: string;
  generatedAt: string;
  question: string;
  intent: AgentCouncilIntent;
  answer: string;
  participatingAgents: AgentName[];
  councilTurns: AgentCouncilTurn[];
  messages: AgentMessage[];
  decisions: AgentDecision[];
  simulation: AgentSimulationResult | null;
  boardroomStages: AgentBoardroomStage[];
  consensus: AgentCouncilConsensus;
  reasoningTraces: AgentReasoningTrace[];
  debateExchanges: AgentDebateExchange[];
  consensusVotes: AgentConsensusVote[];
  researchMetrics: AgentResearchMetrics;
  confidence: number;
  finalVerdict: string;
  sourceSystems: string[];
  storage: string;
}
