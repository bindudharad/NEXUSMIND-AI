export interface WorkloadHistoryPoint {
  date: string;
  workload: number;
  productivity: number;
  overtimeHours: number;
  attendanceRate: number;
  taskCompletionRate: number;
  burnoutRisk: number;
  delayProbability: number;
}

export interface ForecastPoint {
  date: string;
  workload: number;
  productivity: number;
  burnoutRisk: number;
  overtimeHours: number;
  delayProbability: number;
  operationalInstability: number;
  lowerBound: number;
  upperBound: number;
}

export interface TrendSignal {
  metric: string;
  direction: string;
  change: number;
  severity: string;
}

export interface ForecastResponse {
  department: string;
  model: string;
  horizonDays: number;
  confidence: number;
  history: WorkloadHistoryPoint[];
  forecast: ForecastPoint[];
  trendSignals: TrendSignal[];
  teamCollapseProbability: number;
  recommendation: string;
  storage: string;
}
