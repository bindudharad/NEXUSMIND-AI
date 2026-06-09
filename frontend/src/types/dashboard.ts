export type MetricStatus = "optimal" | "watch" | "risk";

export interface EnterpriseMetric {
  label: string;
  value: string;
  trend: number;
  status: MetricStatus;
}

export interface RiskSignal {
  id: string;
  name: string;
  probability: number;
  impact: "low" | "medium" | "high" | "critical";
  recommendation: string;
}

export interface DepartmentSignal {
  department: string;
  productivity: number;
  wellness: number;
  security: number;
  risk: number;
}

export interface AgentMessage {
  agent: string;
  message: string;
  severity: MetricStatus | "critical";
}

export interface DashboardForecastPoint {
  label: string;
  revenue: number;
  risk: number;
  productivity: number;
}

export interface DashboardOverview {
  companyHealth: number;
  predictionConfidence: number;
  metrics: EnterpriseMetric[];
  riskSignals: RiskSignal[];
  departments: DepartmentSignal[];
  agentMessages: AgentMessage[];
  forecastSeries: DashboardForecastPoint[];
}
