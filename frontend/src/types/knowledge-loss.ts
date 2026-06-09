export type KnowledgePriority = "low" | "medium" | "high" | "critical";
export type KnowledgeNodeType = "employee" | "skill" | "system" | "workflow" | "document" | "team";
export type KnowledgeDocumentType = "sop" | "deployment_guide" | "troubleshooting_manual" | "architecture_summary" | "onboarding_guide";
export type KnowledgeRecommendationCategory = "documentation" | "session" | "cross_training" | "mentorship" | "backup_owner" | "onboarding" | "executive";

export interface ExpertiseProfile {
  employeeId: string;
  employeeName: string;
  department: string;
  team: string;
  role: string;
  topExpertise: string[];
  ownedSystems: string[];
  expertiseScore: number;
  knowledgeCriticality: number;
  ownershipConcentration: number;
  documentationCoverage: number;
  attritionRisk: number;
  knowledgeLossProbability: number;
  operationalDisruptionRisk: number;
  confidence: number;
  evidence: string[];
  transferActions: string[];
}

export interface KnowledgeGraphNode {
  nodeId: string;
  label: string;
  nodeType: KnowledgeNodeType;
  riskScore: number;
  size: number;
  metadata: Record<string, string | number>;
}

export interface KnowledgeGraphEdge {
  source: string;
  target: string;
  relation: string;
  strength: number;
  risk: number;
  evidence: string;
}

export interface GeneratedKnowledgeDocument {
  documentId: string;
  title: string;
  documentType: KnowledgeDocumentType;
  owner: string;
  systems: string[];
  content: string;
  coverageScore: number;
  confidence: number;
  sourceCount: number;
}

export interface KnowledgeRiskForecastPoint {
  employeeName: string;
  day: number;
  knowledgeLossProbability: number;
  operationalDisruptionRisk: number;
  transferCompletionProbability: number;
  confidence: number;
}

export interface OrganizationalMemoryHeatmapPoint {
  department: string;
  system: string;
  expertiseConcentration: number;
  documentationCoverage: number;
  redundancyScore: number;
  knowledgeLossRisk: number;
  priority: KnowledgePriority;
}

export interface OnboardingRoadmap {
  role: string;
  focusArea: string;
  steps: string[];
  estimatedDaysSaved: number;
  confidence: number;
}

export interface KnowledgeTransferRecommendation {
  title: string;
  category: KnowledgeRecommendationCategory;
  priority: KnowledgePriority;
  action: string;
  expectedImpact: string;
  affectedEmployees: string[];
  targetSystems: string[];
  confidence: number;
}

export interface KnowledgeRiskAlert {
  title: string;
  severity: KnowledgePriority;
  probability: number;
  impact: string;
  recommendation: string;
}

export interface KnowledgeLossSummary {
  sourcesAnalyzed: number;
  expertsIdentified: number;
  graphNodes: number;
  graphEdges: number;
  highRiskDependencies: number;
  generatedDocuments: number;
  averageDocumentationCoverage: number;
  knowledgeLossRisk: number;
  topRiskOwner: string;
  streamSequence: number;
}

export interface KnowledgeLossResponse {
  model: string;
  generatedAt: string;
  cycleName: string;
  horizonDays: number;
  targetRole: string;
  expertiseProfiles: ExpertiseProfile[];
  graphNodes: KnowledgeGraphNode[];
  graphEdges: KnowledgeGraphEdge[];
  generatedDocuments: GeneratedKnowledgeDocument[];
  forecasts: KnowledgeRiskForecastPoint[];
  memoryHeatmap: OrganizationalMemoryHeatmapPoint[];
  onboardingRoadmaps: OnboardingRoadmap[];
  recommendations: KnowledgeTransferRecommendation[];
  alerts: KnowledgeRiskAlert[];
  executiveInsights: string[];
  summary: KnowledgeLossSummary;
  sourceSystems: string[];
  storage: string;
  graphStore: string;
}
