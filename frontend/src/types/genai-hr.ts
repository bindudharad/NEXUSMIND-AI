export type GenAIHRIntent =
  | "attrition"
  | "burnout"
  | "productivity"
  | "project_risk"
  | "hiring"
  | "company_health"
  | "knowledge"
  | "report"
  | "general";

export interface GenAIContextSource {
  citationId: string;
  system: string;
  title: string;
  snippet: string;
  confidence: number;
  metadata: Record<string, string | number>;
}

export interface GenAIToolCall {
  name: string;
  status: "success" | "degraded" | "error";
  latencyMs: number;
  summary: string;
  evidence: string[];
}

export interface GenAIReportSection {
  title: string;
  summary: string;
  metrics: Record<string, string | number>;
  evidence: string[];
  recommendations: string[];
}

export interface GenAIConversationMemory {
  sessionId: string;
  turns: number;
  lastIntent: GenAIHRIntent;
  rememberedEntities: string[];
  memorySummary: string;
}

export interface GenAIHRAssistantResponse {
  model: string;
  generatedAt: string;
  sessionId: string;
  question: string;
  intent: GenAIHRIntent;
  responseMode: "answer" | "report" | "forecast" | "comparison";
  answer: string;
  executiveSummary: string;
  recommendedActions: string[];
  retrievedContext: GenAIContextSource[];
  toolCalls: GenAIToolCall[];
  reportSections: GenAIReportSection[];
  conversationMemory: GenAIConversationMemory;
  reasoningTrace: string[];
  confidence: number;
  sourceSystems: string[];
  llmProvider: string;
  ragPipeline: string;
  vectorDatabase: string;
  storage: string;
  vectorIndex: string;
  streamSequence: number;
}
