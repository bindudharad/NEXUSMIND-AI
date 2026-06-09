export type ResourceSeverity = "low" | "medium" | "high" | "critical";

export interface AssignmentRecommendation {
  taskId: string;
  taskTitle: string;
  employeeId: string;
  employeeName: string;
  team: string;
  assignmentScore: number;
  confidence: number;
  skillMatchScore: number;
  capacityAfterAssignment: number;
  deliverySuccessProbability: number;
  delayRisk: number;
  burnoutRiskAfterAssignment: number;
  graphBottleneckScore: number;
  rationale: string;
  alternatives: string[];
  optimizationModel: string;
}

export interface WorkloadBalanceItem {
  employeeId: string;
  name: string;
  team: string;
  currentUtilization: number;
  optimizedUtilization: number;
  hoursDelta: number;
  overloadRisk: number;
  action: string;
  rationale: string;
}

export interface CapacityForecastPoint {
  sprint: string;
  capacityUtilization: number;
  availableHours: number;
  committedHours: number;
  deliveryProbability: number;
  shortageHours: number;
  burnoutPressure: number;
  bottleneckRisk: number;
}

export interface SprintPlanningRecommendation {
  title: string;
  action: string;
  expectedImpact: string;
  priority: ResourceSeverity;
  confidence: number;
}

export interface ResourceRiskAlert {
  severity: ResourceSeverity;
  title: string;
  probability: number;
  affectedEntities: string[];
  intervention: string;
}

export interface WorkforceDependencyEdge {
  source: string;
  target: string;
  edgeType: string;
  weight: number;
  bottleneckScore: number;
}

export interface ResourceOptimizationSummary {
  employeesAnalyzed: number;
  tasksAnalyzed: number;
  assignmentsGenerated: number;
  capacityUtilization: number;
  overloadReduction: number;
  deliverySuccessProbability: number;
  sprintCompletionProbability: number;
  projectedDelayDays: number;
  estimatedCostAvoidance: number;
  streamSequence: number;
}

export interface ResourceAllocationResponse {
  model: string;
  generatedAt: string;
  department: string;
  sprintName: string;
  planningHorizonDays: number;
  mlModel: string;
  optimizationModel: string;
  graphModel: string;
  assignments: AssignmentRecommendation[];
  workloadBalance: WorkloadBalanceItem[];
  capacityForecast: CapacityForecastPoint[];
  sprintPlan: SprintPlanningRecommendation[];
  dependencyGraph: WorkforceDependencyEdge[];
  riskAlerts: ResourceRiskAlert[];
  executiveInsights: string[];
  summary: ResourceOptimizationSummary;
  storage: string;
}
