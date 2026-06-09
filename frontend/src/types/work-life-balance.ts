export type WorkLifeSeverity = "low" | "medium" | "high" | "critical";
export type WorkLifeCategory =
  | "flexible_timing"
  | "meeting_reduction"
  | "task_redistribution"
  | "burnout_prevention"
  | "focus_time"
  | "productivity_balance"
  | "executive";

export interface WorkLifeBalanceSummary {
  employeesAnalyzed: number;
  teamCount: number;
  wellnessScore: number;
  burnoutRisk: number;
  projectedBurnoutReduction: number;
  meetingReductionPercent: number;
  focusTimeGainHours: number;
  taskRedistributionHours: number;
  productivityWellnessBalance: number;
  sustainableProductivityScore: number;
  streamSequence: number;
}

export interface WorkLifeEmployeePlan {
  employeeId: string;
  name: string;
  team: string;
  role: string;
  currentWellnessScore: number;
  optimizedWellnessScore: number;
  burnoutRiskBefore: number;
  burnoutRiskAfter: number;
  meetingReductionPercent: number;
  recurringHoursToAsync: number;
  focusBlock: string;
  flexibleSchedule: string;
  taskRedistributionHours: number;
  productivityWellnessBalance: number;
  sustainabilityScore: number;
  confidence: number;
  rationale: string;
  evidence: string[];
}

export interface WorkLifeTeamBalance {
  team: string;
  employees: number;
  wellnessScore: number;
  burnoutRisk: number;
  meetingOverload: number;
  workloadImbalance: number;
  focusProtectionScore: number;
  recommendedPolicy: string;
}

export interface WorkLifeScheduleRecommendation {
  category: WorkLifeCategory;
  priority: WorkLifeSeverity;
  title: string;
  action: string;
  expectedImpact: string;
  confidence: number;
  affectedEmployees: string[];
  affectedTeams: string[];
}

export interface WorkLifeFocusBlock {
  team: string;
  block: string;
  protectedHours: number;
  expectedFocusGain: number;
  meetingConflictReduction: number;
  rationale: string;
}

export interface MeetingReductionPlan {
  team: string;
  currentMeetingHours: number;
  recommendedMeetingHours: number;
  reductionPercent: number;
  asyncConversionHours: number;
  productivityRecoveryHours: number;
  recommendation: string;
}

export interface WorkloadRedistributionPlan {
  sourceEmployee: string;
  targetEmployee: string;
  team: string;
  hoursToShift: number;
  burnoutReduction: number;
  deliveryRiskChange: number;
  rationale: string;
}

export interface WorkLifeForecastPoint {
  day: number;
  wellnessScore: number;
  burnoutRisk: number;
  productivityScore: number;
  meetingLoad: number;
  focusTimeScore: number;
  confidence: number;
}

export interface WorkLifeHeatmapCell {
  team: string;
  metric: string;
  score: number;
  severity: WorkLifeSeverity;
  recommendation: string;
}

export interface WorkLifeRiskAlert {
  category: WorkLifeCategory;
  severity: WorkLifeSeverity;
  score: number;
  message: string;
  evidence: string[];
  intervention: string;
}

export interface WorkLifeBalanceResponse {
  model: string;
  generatedAt: string;
  cycleName: string;
  targetDepartment: string;
  horizonDays: number;
  mlModel: string;
  forecastingModel: string;
  optimizationModel: string;
  sourceSystems: string[];
  summary: WorkLifeBalanceSummary;
  employeePlans: WorkLifeEmployeePlan[];
  teamBalance: WorkLifeTeamBalance[];
  focusBlocks: WorkLifeFocusBlock[];
  meetingPlan: MeetingReductionPlan[];
  workloadRedistribution: WorkloadRedistributionPlan[];
  recommendations: WorkLifeScheduleRecommendation[];
  forecast: WorkLifeForecastPoint[];
  heatmap: WorkLifeHeatmapCell[];
  riskAlerts: WorkLifeRiskAlert[];
  executiveInsights: string[];
  storage: string;
}
