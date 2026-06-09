export type AlertSeverity = "critical" | "high" | "medium" | "low";
export type AlertCategory =
  | "burnout"
  | "productivity"
  | "overload"
  | "delay"
  | "security"
  | "toxicity"
  | "attendance"
  | "revenue"
  | "operations";

export interface AIAlert {
  alertId: string;
  category: AlertCategory;
  title: string;
  message: string;
  severity: AlertSeverity;
  riskScore: number;
  confidence: number;
  sourceSystems: string[];
  evidence: string[];
  recommendation: string;
  createdAt: string;
  acknowledged: boolean;
  groupKey: string;
  priorityRank: number;
}

export interface AlertSummary {
  total: number;
  critical: number;
  high: number;
  unacknowledged: number;
  averageRisk: number;
  streamSequence: number;
}

export interface AlertFeedResponse {
  model: string;
  generatedAt: string;
  scenario: "default" | "crisis";
  adaptiveThreshold: number;
  alerts: AIAlert[];
  summary: AlertSummary;
  storage: string;
}

export interface AlertAckResponse {
  alertId: string;
  acknowledged: boolean;
  message: string;
  storage: string;
}
