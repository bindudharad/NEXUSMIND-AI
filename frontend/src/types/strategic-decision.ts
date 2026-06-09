import type { ExecutiveImpactAnalysisPanel, WhatIfRiskLevel, WhatIfSimulationResponse } from "@/types/what-if-decision";
import type { ShadowDecisionSimulationResponse } from "@/types/shadow-company";

export interface StrategicDecisionRequest {
  question: string;
  sessionId?: string;
  horizonMonths?: number;
}

export interface StrategicChainReactionStep {
  step: number;
  title: string;
  baseline: number;
  projected: number;
  delta: number;
  severity: WhatIfRiskLevel;
  explanation: string;
  sourceSystems: string[];
}

export interface StrategicDecisionOption {
  optionId: string;
  title: string;
  description: string;
  riskScore: number;
  revenueImpactPercent: number;
  costImpactPercent: number;
  burnoutImpactPoints: number;
  productivityImpactPercent: number;
  clientImpactScore: number;
  decisionReadinessScore: number;
  recommendation: string;
  recommended: boolean;
}

export interface StrategicBoardroomFinding {
  agent: string;
  perspective: string;
  finding: string;
  recommendation: string;
  confidence: number;
  evidence: string[];
}

export interface StrategicDecisionScores {
  strategicIntelligenceScore: number;
  innovationScore: number;
  enterpriseValueScore: number;
  technicalComplexityScore: number;
  judgeWowFactorScore: number;
  productionReadinessScore: number;
}

export interface StrategicDecisionResponse {
  model: string;
  generatedAt: string;
  question: string;
  decisionIntent: string;
  executiveAnswer: string;
  recommendedAction: string;
  confidenceScore: number;
  strategicRiskScore: number;
  futureSimulationStatus: "working" | "partial" | "missing";
  digitalTwinStatus: "working" | "partial" | "missing";
  chainReactionStatus: "working" | "partial" | "missing";
  boardroomStatus: "working" | "partial" | "missing";
  shadowCompanyStatus: "working" | "partial" | "missing";
  demoModeStatus: "working" | "partial" | "missing";
  decisionOptions: StrategicDecisionOption[];
  chainReaction: StrategicChainReactionStep[];
  boardroomFindings: StrategicBoardroomFinding[];
  impactPanel: ExecutiveImpactAnalysisPanel;
  whatIfSimulation: WhatIfSimulationResponse;
  shadowCompanySimulation: ShadowDecisionSimulationResponse;
  sourceSystems: string[];
  scores: StrategicDecisionScores;
  storage: string;
  finalVerdict: string;
}
