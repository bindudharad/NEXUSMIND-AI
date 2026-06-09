export type ManagerRiskSeverity = "critical" | "high" | "medium" | "low";

export interface RiskyTeam {
  teamId: string;
  teamName: string;
  department: string;
  riskScore: number;
  severity: ManagerRiskSeverity;
  memberCount: number;
  drivers: string[];
  recommendation: string;
}

export interface OverloadedEmployee {
  employeeId: string;
  employeeName: string;
  teamName: string;
  role: string;
  overloadScore: number;
  severity: ManagerRiskSeverity;
  drivers: string[];
  recommendation: string;
}

export interface DelayPrediction {
  projectId: string;
  projectName: string;
  teamName: string;
  delayProbability: number;
  severity: ManagerRiskSeverity;
  projectedDelayDays: number;
  bottlenecks: string[];
  recommendation: string;
}

export interface ManagerTrendPoint {
  timestamp: string;
  averageTeamRisk: number;
  overloadPressure: number;
  delayRisk: number;
}

export interface ManagerDashboardSummary {
  teamsAtRisk: number;
  overloadedEmployees: number;
  projectsAtDelayRisk: number;
  averageTeamRisk: number;
  averageDelayProbability: number;
}

export interface ManagerDashboardResponse {
  managerId: string;
  managerName: string;
  generatedAt: string;
  model: string;
  summary: ManagerDashboardSummary;
  riskyTeams: RiskyTeam[];
  overloadedEmployees: OverloadedEmployee[];
  delayPredictions: DelayPrediction[];
  trend: ManagerTrendPoint[];
  recommendations: string[];
  storage: string;
}
