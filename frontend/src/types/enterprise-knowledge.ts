export type EnterpriseKnowledgePriority = "critical" | "high" | "medium" | "low";

export interface EnterpriseKnowledgeEntitySet {
  people: string[];
  skills: string[];
  technologies: string[];
  projects: string[];
  incidents: string[];
  solutions: string[];
  systems: string[];
}

export interface EnterpriseKnowledgeDocumentRecord {
  documentId: string;
  title: string;
  sourceType: string;
  fileName: string;
  parser: string;
  chunks: number;
  extractedEntities: EnterpriseKnowledgeEntitySet;
  experts: string[];
  systems: string[];
  metadata: Record<string, unknown>;
  createdAt: string;
}

export interface EnterpriseKnowledgeCitation {
  citationId: string;
  documentId: string;
  title: string;
  chunkId: string;
  snippet: string;
  score: number;
  metadata: Record<string, unknown>;
}

export interface EnterpriseKnowledgeMatchedChunk {
  chunkId: string;
  text: string;
  score: number;
  entities: EnterpriseKnowledgeEntitySet;
  experts: string[];
  systems: string[];
  citationId: string;
}

export interface EnterpriseKnowledgeSearchResult {
  documentId: string;
  title: string;
  sourceType: string;
  score: number;
  matchedChunks: EnterpriseKnowledgeMatchedChunk[];
  extractedEntities: EnterpriseKnowledgeEntitySet;
  experts: string[];
  systems: string[];
  citations: EnterpriseKnowledgeCitation[];
  metadata: Record<string, unknown>;
}

export interface EnterpriseKnowledgeExpertRanking {
  employeeId: string;
  employeeName: string;
  department: string;
  team: string;
  skill: string;
  score: number;
  evidence: string[];
  documents: string[];
  systems: string[];
}

export interface EnterpriseKnowledgeGraphNode {
  id: string;
  label: string;
  type: string;
  score: number;
  metadata: Record<string, unknown>;
}

export interface EnterpriseKnowledgeGraphEdge {
  source: string;
  target: string;
  type: string;
  weight: number;
  evidence: string;
}

export interface EnterpriseKnowledgeRecommendation {
  title: string;
  priority: EnterpriseKnowledgePriority;
  action: string;
  rationale: string;
  expectedImpact: number;
}

export interface EnterpriseKnowledgeInsight {
  title: string;
  category: string;
  detail: string;
  score: number;
  evidence: string[];
}

export interface EnterpriseKnowledgeTimelineEvent {
  eventId: string;
  occurredAt: string;
  eventType: string;
  title: string;
  summary: string;
  people: string[];
  systems: string[];
  projects: string[];
  evidence: string[];
}

export interface EnterpriseKnowledgeSecurityControl {
  control: string;
  status: "ready" | "enforced" | "simulated" | "watch";
  detail: string;
  evidence: string[];
}

export interface EnterpriseKnowledgeIntegrationSignal {
  system: string;
  status: "synced" | "ready" | "projected" | "watch";
  update: string;
  evidence: string[];
}

export interface EnterpriseKnowledgeAgentContribution {
  agent: string;
  role: string;
  finding: string;
  recommendation: string;
  confidence: number;
  sourceSystems: string[];
}

export interface EnterpriseKnowledgeStatusReport {
  knowledgeIngestionStatus: string;
  documentIntelligenceStatus: string;
  vectorDatabaseStatus: string;
  knowledgeGraphStatus: string;
  ragStatus: string;
  expertiseDiscoveryStatus: string;
  lessonsLearnedStatus: string;
  knowledgeAssistantStatus: string;
  dashboardStatus: string;
  securityStatus: string;
  digitalTwinIntegrationStatus: string;
  multiAgentIntegrationStatus: string;
  missingComponents: string[];
  fixedComponents: string[];
  errorsFound: string[];
  errorsFixed: string[];
  performanceMetrics: Record<string, string | number | boolean>;
  productionReadinessScore: number;
  innovationScore: number;
  businessValueScore: number;
  finalVerdict: string;
}

export interface EnterpriseKnowledgeSummary {
  knowledgeHealthScore: number;
  documentsIndexed: number;
  chunksIndexed: number;
  expertsDetected: number;
  graphNodes: number;
  graphEdges: number;
  incidentsDetected: number;
  solutionsDetected: number;
  sopGaps: number;
  qdrantStatus: string;
  neo4jStatus: string;
}

export interface EnterpriseKnowledgeDefaultResponse {
  model: string;
  generatedAt: string;
  summary: EnterpriseKnowledgeSummary;
  documents: EnterpriseKnowledgeDocumentRecord[];
  topExperts: EnterpriseKnowledgeExpertRanking[];
  graphNodes: EnterpriseKnowledgeGraphNode[];
  graphEdges: EnterpriseKnowledgeGraphEdge[];
  technologyMap: EnterpriseKnowledgeInsight[];
  valuableDocuments: EnterpriseKnowledgeInsight[];
  incidentMemory: EnterpriseKnowledgeInsight[];
  lessonsLearned: EnterpriseKnowledgeInsight[];
  organizationalMemoryTimeline: EnterpriseKnowledgeTimelineEvent[];
  sopGaps: EnterpriseKnowledgeInsight[];
  recommendations: EnterpriseKnowledgeRecommendation[];
  securityControls: EnterpriseKnowledgeSecurityControl[];
  digitalTwinSync: EnterpriseKnowledgeIntegrationSignal[];
  agentCouncil: EnterpriseKnowledgeAgentContribution[];
  statusReport: EnterpriseKnowledgeStatusReport;
  sourceSystems: string[];
  storage: Record<string, string>;
  finalVerdict: string;
}

export interface EnterpriseKnowledgeSearchResponse {
  model: string;
  generatedAt: string;
  query: string;
  results: EnterpriseKnowledgeSearchResult[];
  citations: EnterpriseKnowledgeCitation[];
  graphEvidence: EnterpriseKnowledgeGraphEdge[];
  sourceSystems: string[];
  vectorDatabase: string;
  storage: Record<string, string>;
}

export interface EnterpriseKnowledgeAskResponse {
  model: string;
  generatedAt: string;
  question: string;
  answer: string;
  confidence: number;
  citations: EnterpriseKnowledgeCitation[];
  retrievedChunks: EnterpriseKnowledgeMatchedChunk[];
  graphEvidence: EnterpriseKnowledgeGraphEdge[];
  sourceSystems: string[];
  recommendedFollowUpActions: string[];
  storage: Record<string, string>;
  finalVerdict: string;
}

export interface EnterpriseKnowledgeIngestResponse {
  model: string;
  generatedAt: string;
  ingestedDocuments: EnterpriseKnowledgeDocumentRecord[];
  summary: EnterpriseKnowledgeSummary;
  graphNodes: EnterpriseKnowledgeGraphNode[];
  graphEdges: EnterpriseKnowledgeGraphEdge[];
  recommendations: EnterpriseKnowledgeRecommendation[];
  sourceSystems: string[];
  storage: Record<string, string>;
}
