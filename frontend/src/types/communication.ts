export type CommunicationPriority = "low" | "medium" | "high" | "critical";

export interface MessageRiskInsight {
  messageId: string;
  employeeId: string;
  employeeName: string;
  department: string;
  team: string;
  channel: string;
  sentiment: string;
  primaryEmotion: string;
  sentimentScore: number;
  toxicityScore: number;
  aggressionScore: number;
  conflictEscalationScore: number;
  communicationQualityScore: number;
  confidence: number;
  evidence: string[];
  recommendation: string;
}

export interface TeamCommunicationHeatmapPoint {
  department: string;
  team: string;
  toxicityRisk: number;
  moraleScore: number;
  collaborationQuality: number;
  conflictProbability: number;
  isolationRisk: number;
  messagesAnalyzed: number;
  priority: CommunicationPriority;
}

export interface InteractionGraphEdge {
  sourceId: string;
  sourceName: string;
  targetId: string;
  targetName: string;
  department: string;
  team: string;
  collaborationScore: number;
  responseHealth: number;
  sentimentAlignment: number;
  conflictProbability: number;
  isolationSignal: number;
  recommendation: string;
}

export interface ConflictForecast {
  department: string;
  team: string;
  conflictProbability: number;
  projectedProductivityLossHours: number;
  confidence: number;
  drivers: string[];
  forecast: number[];
}

export interface IsolationRiskInsight {
  employeeId: string;
  employeeName: string;
  department: string;
  team: string;
  isolationRisk: number;
  interactionDrop: number;
  responseDelayPressure: number;
  unansweredThreads: number;
  recommendation: string;
}

export interface CommunicationRecommendation {
  title: string;
  category: "toxicity" | "aggression" | "collaboration" | "isolation" | "conflict" | "morale";
  priority: CommunicationPriority;
  impactScore: number;
  action: string;
  rationale: string;
  confidence: number;
}

export interface CommunicationAlert {
  title: string;
  priority: CommunicationPriority;
  probability: number;
  impact: string;
  recommendation: string;
}

export interface CommunicationSummary {
  messagesAnalyzed: number;
  interactionsAnalyzed: number;
  highToxicityAlerts: number;
  isolationRisks: number;
  averageQualityScore: number;
  averageCollaborationQuality: number;
  conflictProbability: number;
  moraleScore: number;
  streamSequence: number;
}

export interface CommunicationResponse {
  model: string;
  generatedAt: string;
  cycleName: string;
  horizonDays: number;
  messageRisks: MessageRiskInsight[];
  teamHeatmap: TeamCommunicationHeatmapPoint[];
  interactionGraph: InteractionGraphEdge[];
  conflictForecasts: ConflictForecast[];
  isolationRisks: IsolationRiskInsight[];
  recommendations: CommunicationRecommendation[];
  alerts: CommunicationAlert[];
  executiveInsights: string[];
  summary: CommunicationSummary;
  sourceSystems: string[];
  storage: string;
}
