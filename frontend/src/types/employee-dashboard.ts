export type ScoreStatus = "optimal" | "stable" | "watch" | "high_risk";

export interface EmployeeScore {
  label: string;
  value: number;
  status: ScoreStatus;
  trendDelta: number;
  drivers: string[];
}

export interface EmployeeTrendPoint {
  timestamp: string;
  stressScore: number;
  productivityScore: number;
  burnoutProbability: number;
  workloadIntensity: number;
  sentimentScore: number;
}

export interface EmployeeDashboardResponse {
  employeeId: string;
  employeeName: string;
  department: string;
  role: string;
  generatedAt: string;
  model: string;
  stress: EmployeeScore;
  productivity: EmployeeScore;
  burnoutProbability: EmployeeScore;
  history: EmployeeTrendPoint[];
  recommendations: string[];
  modelProbabilities: Record<string, number>;
  storage: string;
}
