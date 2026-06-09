export type SmartSuggestionCategory =
  | "meeting_reduction"
  | "workload_redistribution"
  | "wellness_break"
  | "team_optimization"
  | "productivity_improvement";
export type SmartSuggestionPriority = "critical" | "high" | "medium" | "low";

export interface SmartSuggestion {
  suggestionId: string;
  category: SmartSuggestionCategory;
  title: string;
  action: string;
  rationale: string;
  priority: SmartSuggestionPriority;
  confidence: number;
  impactScore: number;
  estimatedGain: string;
  timeToImpactHours: number;
  affectedEmployees: string[];
  sourceSystems: string[];
  evidence: string[];
  createdAt: string;
  feedbackState: "new" | "accepted" | "dismissed";
}

export interface SmartSuggestionSummary {
  total: number;
  critical: number;
  high: number;
  averageImpact: number;
  averageConfidence: number;
  streamSequence: number;
}

export interface SmartSuggestionResponse {
  model: string;
  generatedAt: string;
  scenario: "default" | "crisis";
  adaptiveThreshold: number;
  suggestions: SmartSuggestion[];
  summary: SmartSuggestionSummary;
  storage: string;
}
