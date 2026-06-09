export type BrainNodeType = "employee" | "team" | "department" | "project" | "skill" | "client" | "knowledge_asset" | "location";
export type BrainEdgeType =
  | "reports_to"
  | "works_with"
  | "communicates_with"
  | "collaborates_with"
  | "depends_on"
  | "mentors"
  | "shares_knowledge_with";
export type BrainRiskLevel = "low" | "medium" | "high" | "critical";
export type BrainComponentStatus = "ready" | "degraded" | "missing";
export type BrainAssistantIntent = "influence" | "silo" | "bottleneck" | "knowledge" | "dependency" | "simulation" | "risk" | "summary";

export interface OrganizationalBrainNode {
  id: string;
  label: string;
  nodeType: BrainNodeType;
  department?: string | null;
  team?: string | null;
  riskScore: number;
  influenceScore: number;
  knowledgeScore: number;
  x: number;
  y: number;
  metadata: Record<string, string | number | boolean>;
}

export interface OrganizationalBrainEdge {
  source: string;
  target: string;
  edgeType: BrainEdgeType;
  weight: number;
  riskScore: number;
  evidence: string;
  sourceSystem: string;
}

export interface GraphDatabaseStatus {
  engine: string;
  status: BrainComponentStatus;
  configuredExternalDatabase: string;
  nodeCount: number;
  relationshipCount: number;
  indexedFields: string[];
  queryLatencyMs: number;
  storage: string;
  exportFormat: string;
}

export interface GNNNodeEmbedding {
  nodeId: string;
  label: string;
  nodeType: BrainNodeType;
  embedding: number[];
  influencePrediction: number;
  knowledgeFlowPrediction: number;
  riskPrediction: number;
  nearestNeighbors: string[];
}

export interface GNNRelationshipPrediction {
  source: string;
  target: string;
  predictedRelationship: BrainEdgeType;
  probability: number;
  rationale: string;
}

export interface GNNEngineStatus {
  status: BrainComponentStatus;
  supportedModels: Array<"GraphSAGE" | "GAT" | "GCN" | "GIN">;
  trainingStatus: string;
  nodeEmbeddingDimensions: number;
  trainingNodes: number;
  trainingEdges: number;
  validationMae: number;
  inferenceLatencyMs: number;
  embeddings: GNNNodeEmbedding[];
  relationshipPredictions: GNNRelationshipPrediction[];
  sourceSystems: string[];
}

export interface CommunicationFlowFinding {
  sourceUnit: string;
  targetUnit: string;
  communicationScore: number;
  bottleneckNode: string;
  delayRisk: number;
  evidence: string[];
  recommendation: string;
}

export interface KnowledgeFlowFinding {
  knowledgeAsset: string;
  primaryExperts: string[];
  dependentTeams: string[];
  knowledgeLossRisk: number;
  flowScore: number;
  recommendation: string;
  evidence: string[];
}

export interface TeamDependencyFinding {
  sourceTeam: string;
  dependentOn: string;
  dependencyStrength: number;
  deliveryRisk: number;
  criticalPath: boolean;
  evidence: string[];
  recommendation: string;
}

export interface BottleneckFinding {
  nodeId: string;
  label: string;
  nodeType: BrainNodeType;
  bottleneckScore: number;
  affectedUnits: string[];
  evidence: string[];
  recommendation: string;
}

export interface InfluenceFinding {
  employeeId: string;
  employeeName: string;
  formalRole: string;
  influenceScore: number;
  influencedTeams: string[];
  hiddenLeader: boolean;
  evidence: string[];
}

export interface SiloFinding {
  unit: string;
  siloRisk: number;
  externalCollaborationRatio: number;
  missingBridges: string[];
  evidence: string[];
  recommendation: string;
}

export interface OrganizationalRiskPrediction {
  riskType: "knowledge_loss" | "communication_failure" | "leadership_dependency" | "team_collapse" | "collaboration_decline";
  affectedEntity: string;
  riskScore: number;
  confidence: number;
  evidence: string[];
  recommendation: string;
}

export interface OrganizationalBrainRecommendation {
  recommendationId: string;
  priority: BrainRiskLevel;
  action: string;
  reason: string;
  expectedImpact: string;
  confidence: number;
  sourceSystems: string[];
}

export interface OrganizationalBrainIntegrationStatus {
  employeeTwin: BrainComponentStatus;
  teamTwin: BrainComponentStatus;
  departmentTwin: BrainComponentStatus;
  companyTwin: BrainComponentStatus;
  timeMachine: BrainComponentStatus;
  workforceSimulator: BrainComponentStatus;
  executiveDashboard: BrainComponentStatus;
  evidence: string[];
}

export interface OrganizationalBrainComponent {
  name: string;
  status: BrainComponentStatus;
  evidence: string[];
}

export interface OrganizationalBrainSummary {
  organizationalBrainScore: number;
  graphNodes: number;
  graphEdges: number;
  gnnPredictionCount: number;
  communicationBottlenecks: number;
  knowledgeLossHotspots: number;
  highSiloUnits: number;
  criticalDependencyPaths: number;
  hiddenInfluencers: number;
  streamSequence: number;
}

export interface GraphVisualizationLayer {
  layoutAlgorithm: string;
  supportsZoom: boolean;
  supportsSearch: boolean;
  supportsFilters: boolean;
  realtimeUpdates: boolean;
  nodes: OrganizationalBrainNode[];
  edges: OrganizationalBrainEdge[];
}

export interface OrganizationalBrainResponse {
  model: string;
  generatedAt: string;
  cycleName: string;
  summary: OrganizationalBrainSummary;
  graphDatabase: GraphDatabaseStatus;
  graphNodes: OrganizationalBrainNode[];
  graphEdges: OrganizationalBrainEdge[];
  gnnEngine: GNNEngineStatus;
  communicationFlow: CommunicationFlowFinding[];
  knowledgeFlow: KnowledgeFlowFinding[];
  teamDependencies: TeamDependencyFinding[];
  bottlenecks: BottleneckFinding[];
  influenceNetwork: InfluenceFinding[];
  siloDetection: SiloFinding[];
  riskPredictions: OrganizationalRiskPrediction[];
  recommendations: OrganizationalBrainRecommendation[];
  graphVisualization: GraphVisualizationLayer;
  integrationStatus: OrganizationalBrainIntegrationStatus;
  components: OrganizationalBrainComponent[];
  executiveBrief: string;
  supportedQuestions: string[];
  sourceSystems: string[];
  productionReadinessScore: number;
  researchInnovationScore: number;
  finalVerdict: string;
  storage: string;
}

export interface OrganizationalBrainAssistantResponse {
  model: string;
  generatedAt: string;
  question: string;
  intent: BrainAssistantIntent;
  answer: string;
  confidence: number;
  citedNodes: string[];
  citedEdges: string[];
  recommendedActions: string[];
  graphEvidence: string[];
  gnnEvidence: string[];
  sourceSystems: string[];
  storage: string;
}
