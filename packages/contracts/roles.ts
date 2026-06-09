export const enterpriseRoles = ["CEO", "HR", "Manager", "Employee", "Admin"] as const;

export type EnterpriseRole = (typeof enterpriseRoles)[number];

export interface EnterpriseUser {
  id: string;
  email: string;
  fullName: string;
  role: EnterpriseRole;
  department: string;
}

export interface EnterpriseMetric {
  label: string;
  value: string;
  trend: number;
  status: "optimal" | "watch" | "risk";
}

export interface RiskSignal {
  id: string;
  name: string;
  probability: number;
  impact: "low" | "medium" | "high" | "critical";
  recommendation: string;
}
