export type ClientRiskPriority = "low" | "medium" | "high" | "critical";
export type ClientAccountTier = "standard" | "strategic" | "enterprise" | "global";
export type ClientRecommendationCategory =
  | "communication"
  | "delivery"
  | "quality"
  | "churn"
  | "escalation"
  | "renewal"
  | "executive"
  | "payment"
  | "project"
  | "engagement"
  | "opportunity";
export type ClientEngagementTrend = "declining" | "stable" | "improving";

export interface ClientForecastPoint {
  day: number;
  clientHealthScore: number;
  churnRisk: number;
  escalationProbability: number;
  deliveryConfidence: number;
  confidence: number;
}

export interface ClientSatisfactionPrediction {
  clientId: string;
  clientName: string;
  industry: string;
  accountTier: ClientAccountTier;
  projectName: string;
  clientHealthScore: number;
  satisfactionScore: number;
  dissatisfactionProbability: number;
  churnRisk: number;
  escalationProbability: number;
  relationshipStability: number;
  communicationHealth: number;
  deliveryHealth: number;
  qualityRisk: number;
  trustDecline: number;
  renewalRisk: number;
  renewalProbability: number;
  paymentDelayRisk: number;
  predictedPaymentDelayDays: number;
  invoiceCollectionRisk: number;
  projectFailureRisk: number;
  budgetOverrunRisk: number;
  clientDissatisfactionRisk: number;
  engagementScore: number;
  engagementTrend: ClientEngagementTrend;
  upsellOpportunityScore: number;
  upsellRevenuePotential: number;
  interventionPriorityScore: number;
  revenueAtRisk: number;
  sentimentLabel: string;
  confidence: number;
  riskDrivers: string[];
  recoveryActions: string[];
  forecast: ClientForecastPoint[];
}

export interface ClientHealthHeatmapPoint {
  clientName: string;
  metric: string;
  score: number;
  priority: ClientRiskPriority;
}

export interface CommunicationSentimentPoint {
  clientName: string;
  label: string;
  sentimentScore: number;
  negativityRisk: number;
  trustRisk: number;
}

export interface DeliveryRiskPoint {
  clientName: string;
  delayRisk: number;
  slaRisk: number;
  qualityRisk: number;
  issueResolutionRisk: number;
}

export interface ClientPaymentRiskPoint {
  clientName: string;
  paymentDelayRisk: number;
  predictedDelayDays: number;
  collectionRisk: number;
  overdueInvoiceAmount: number;
  priority: ClientRiskPriority;
}

export interface ClientProjectRiskPoint {
  clientName: string;
  projectName: string;
  projectFailureRisk: number;
  delayRisk: number;
  budgetOverrunRisk: number;
  dissatisfactionRisk: number;
  primaryCause: string;
  priority: ClientRiskPriority;
}

export interface ClientEngagementAnalyticsPoint {
  clientName: string;
  engagementScore: number;
  trend: ClientEngagementTrend;
  meetingParticipation: number;
  emailResponsiveness: number;
  platformUsage: number;
  featureAdoption: number;
  supportPressure: number;
}

export interface ClientOpportunityInsight {
  clientName: string;
  opportunity: string;
  probability: number;
  potentialRevenue: number;
  rationale: string;
  recommendedAction: string;
  priority: ClientRiskPriority;
}

export interface ClientRecoveryRecommendation {
  title: string;
  category: ClientRecommendationCategory;
  priority: ClientRiskPriority;
  action: string;
  expectedImpact: string;
  confidence: number;
  affectedClients: string[];
}

export interface ClientSatisfactionAlert {
  title: string;
  severity: ClientRiskPriority;
  probability: number;
  impact: string;
  recommendation: string;
}

export interface ClientSatisfactionSummary {
  clientsAnalyzed: number;
  averageClientHealthScore: number;
  averageChurnRisk: number;
  averageEscalationProbability: number;
  highRiskClients: number;
  revenueAtRisk: number;
  paymentRiskAccounts: number;
  projectRiskAccounts: number;
  opportunityRevenue: number;
  highestRiskClient: string;
  bestUpsellClient: string;
  streamSequence: number;
}

export interface ClientSatisfactionResponse {
  model: string;
  generatedAt: string;
  cycleName: string;
  horizonDays: number;
  predictions: ClientSatisfactionPrediction[];
  heatmap: ClientHealthHeatmapPoint[];
  communicationSentiment: CommunicationSentimentPoint[];
  deliveryRisks: DeliveryRiskPoint[];
  paymentRisks: ClientPaymentRiskPoint[];
  projectRisks: ClientProjectRiskPoint[];
  engagementAnalytics: ClientEngagementAnalyticsPoint[];
  opportunityPipeline: ClientOpportunityInsight[];
  recommendations: ClientRecoveryRecommendation[];
  alerts: ClientSatisfactionAlert[];
  executiveInsights: string[];
  supportedQuestions: string[];
  summary: ClientSatisfactionSummary;
  sourceSystems: string[];
  storage: string;
}

export interface ClientAssistantResponse {
  model: string;
  generatedAt: string;
  question: string;
  intent: string;
  answer: string;
  confidence: number;
  citedClients: string[];
  citedEvidence: string[];
  recommendedActions: string[];
  sourceSystems: string[];
  storage: string;
}
