export type RecommendationCategory = "work_redistribution" | "break" | "team_balancing";
export type RecommendationPriority = "critical" | "high" | "medium" | "low";

export interface EmployeeProfile {
  employeeId: string;
  name: string;
  role: string;
  team: string;
  skills: string[];
  currentTasks: number;
  capacityHours: number;
  allocatedHours: number;
  productivity: number;
  overtimeHours: number;
  stressScore: number;
  burnoutRisk: number;
  collaborationScore: number;
}

export interface TaskProfile {
  taskId: string;
  title: string;
  requiredSkill: string;
  effortHours: number;
  priority: number;
  project: string;
  dependencyTeam?: string | null;
}

export interface RecommendationItem {
  recommendationId: string;
  category: RecommendationCategory;
  title: string;
  action: string;
  rationale: string;
  confidence: number;
  impactScore: number;
  priority: RecommendationPriority;
  affectedEmployees: string[];
  sourceModel: string;
}

export interface RecommendationResponse {
  model: string;
  generatedAt: string;
  employeesAnalyzed: number;
  tasksAnalyzed: number;
  teamBalanceScore: number;
  recommendations: RecommendationItem[];
  storage: string;
}
