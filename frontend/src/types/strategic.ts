export type RiskLevel = "low" | "medium" | "high" | "critical";

export interface CompetitorInsight {
  competitor: string;
  marketPressureScore: number;
  threatLevel: RiskLevel;
  likelyMoves: string[];
  recommendedResponse: string;
  evidence: string[];
}

export interface ClientRiskInsight {
  clientId: string;
  clientName: string;
  revenueAtRisk: number;
  churnRisk: number;
  paymentDelayRisk: number;
  escalationRisk: number;
  relationshipHealth: number;
  intervention: string;
  evidence: string[];
}

export interface MarketplaceMatch {
  employeeId: string;
  employeeName: string;
  projectId: string;
  projectTitle: string;
  matchScore: number;
  capacityFit: number;
  rationale: string;
}

export interface MentorMatch {
  mentorId: string;
  mentorName: string;
  menteeId: string;
  menteeName: string;
  topic: string;
  matchScore: number;
}

export interface OrgOptimizationInsight {
  unit: string;
  optimizationPressure: number;
  reportingChange: string;
  communicationFlow: string;
  expectedLatencyReductionDays: number;
  evidence: string[];
}

export interface CrisisResponsePlan {
  scenario: string;
  severityScore: number;
  riskLevel: RiskLevel;
  recoveryPriorities: string[];
  commandCenterActions: string[];
  expectedRecoveryDays: number;
}

export interface InnovationSignal {
  employeeId: string;
  employeeName: string;
  innovationScore: number;
  leadershipPotential: number;
  sponsorshipAction: string;
  evidence: string[];
}

export interface StrategicIntelligenceSummary {
  competitorThreats: number;
  highRiskClients: number;
  marketplaceMatches: number;
  mentorMatches: number;
  orgUnitsToRestructure: number;
  innovationLeaders: number;
  crisisSeverity: number;
  strategicReadinessScore: number;
  topMarketRisk: string;
  topClientRisk: string;
}

export interface StrategicIntelligenceResponse {
  model: string;
  generatedAt: string;
  summary: StrategicIntelligenceSummary;
  competitiveIntelligence: CompetitorInsight[];
  clientRelationshipIntelligence: ClientRiskInsight[];
  internalMarketplaceMatches: MarketplaceMatch[];
  mentorMatches: MentorMatch[];
  organizationOptimizations: OrgOptimizationInsight[];
  crisisResponse: CrisisResponsePlan;
  innovationSignals: InnovationSignal[];
  executiveBrief: string;
  storage: string;
}
