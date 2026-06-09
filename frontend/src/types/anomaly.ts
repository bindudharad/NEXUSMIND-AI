export type AnomalySeverity = "critical" | "high" | "medium" | "low";

export interface BehaviorEvent {
  employeeId: string;
  employeeName: string;
  department: string;
  role: string;
  timestamp: string;
  loginCount: number;
  failedLogins: number;
  offHoursLogins: number;
  inactiveHours: number;
  productivityScore: number;
  overtimeHours: number;
  messagesSent: number;
  negativeSentimentRatio: number;
  toxicMessageCount: number;
  dataDownloadMb: number;
  privilegedActions: number;
  projectCommits: number;
  meetingHours: number;
  stressScore: number;
  accessScopeChanges: number;
  deviceChangeCount: number;
  unusualLocationCount: number;
  impossibleTravelEvents: number;
  browserFingerprintChanges: number;
  sensitiveFileAccesses: number;
  externalTransferMb: number;
  cloudUploadMb: number;
  usbWriteMb: number;
  policyViolationCount: number;
  adminRoleChanges: number;
  privilegedSessionMinutes: number;
  baselineDeviation: number;
}

export interface AnomalyAlert {
  alertId: string;
  employeeId: string;
  employeeName: string;
  department: string;
  anomalyType: string;
  severity: AnomalySeverity;
  anomalyScore: number;
  insiderThreatScore: number;
  accessAnomalyScore: number;
  dataLeakageProbability: number;
  privilegeMisuseScore: number;
  fraudLikelihood: number;
  burnoutAnomalyScore: number;
  productivityAnomalyScore: number;
  behavioralDriftScore: number;
  confidence: number;
  evidence: string[];
  affectedAssets: string[];
  recommendation: string;
  mitigationActions: string[];
  sourceModel: string;
}

export interface AnomalySummary {
  criticalAlerts: number;
  highAlerts: number;
  insiderThreats: number;
  burnoutAnomalies: number;
  productivityAnomalies: number;
  dataLeakageAlerts: number;
  accessAnomalyAlerts: number;
  privilegeMisuseAlerts: number;
  averageInsiderScore: number;
  averageDataLeakageProbability: number;
}

export interface UserRiskHeatmapPoint {
  department: string;
  employeeCount: number;
  highestRiskEmployee: string;
  averageThreatScore: number;
  averageDataLeakageProbability: number;
  averageAccessAnomalyScore: number;
  criticalAlerts: number;
}

export interface SecurityRecommendation {
  title: string;
  priority: AnomalySeverity;
  action: string;
  rationale: string;
  expectedImpact: string;
  confidence: number;
}

export interface AnomalyDetectionResponse {
  model: string;
  generatedAt: string;
  eventsAnalyzed: number;
  anomalyRate: number;
  adaptiveThreshold: number;
  alerts: AnomalyAlert[];
  userRiskHeatmap: UserRiskHeatmapPoint[];
  securityRecommendations: SecurityRecommendation[];
  executiveInsights: string[];
  summary: AnomalySummary;
  sourceSystems: string[];
  streamSequence: number;
  storage: string;
}
