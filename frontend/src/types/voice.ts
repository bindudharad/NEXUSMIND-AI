export interface VoiceAcousticFeatures {
  rmsEnergy: number;
  peakAmplitude: number;
  zeroCrossingRate: number;
  pauseRatio: number;
  pitchMeanHz: number;
  pitchVariation: number;
  intensityVariability: number;
  jitterProxy: number;
  tremorProxy: number;
  speechRateWpm: number;
  vocalTension: number;
}

export interface VoiceEmotionScores {
  stress: number;
  frustration: number;
  anger: number;
  anxiety: number;
  fatigue: number;
  calmness: number;
  motivation: number;
}

export interface VoiceAlert {
  category: string;
  severity: "low" | "medium" | "high" | "critical";
  score: number;
  message: string;
  evidence: string[];
  recommendation: string;
}

export interface VoiceTimelinePoint {
  second: number;
  stress: number;
  intensity: number;
  pitchHz: number;
}

export interface VoiceStressSummary {
  averageStress: number;
  peakStress: number;
  alertCount: number;
  streamSequence: number;
}

export interface VoiceStressResponse {
  model: string;
  generatedAt: string;
  employeeId: string;
  speaker: string;
  department: string;
  sourceFormat: "pcm" | "wav" | "webm" | "mp3" | "ogg" | "browser_pcm";
  durationSeconds: number;
  transcript: string | null;
  primaryEmotion: string;
  confidence: number;
  stressScore: number;
  burnoutRisk: number;
  conflictIntensity: number;
  communicationPressure: number;
  acousticFeatures: VoiceAcousticFeatures;
  emotionScores: VoiceEmotionScores;
  fusionEvidence: string[];
  alerts: VoiceAlert[];
  recommendations: string[];
  timeline: VoiceTimelinePoint[];
  summary: VoiceStressSummary;
  storage: string;
}

export interface VoiceCommandAction {
  label: string;
  actionType: string;
  target: string;
  priority: "low" | "medium" | "high" | "critical";
}

export interface VoiceCapabilityStatus {
  capability: string;
  status: "ready" | "degraded" | "missing";
  evidence: string[];
}

export interface VoiceVisualKPI {
  label: string;
  value: string;
  trend: string;
  severity: "low" | "medium" | "high" | "critical";
}

export interface VoiceVisualChart {
  chartType: "risk_bar" | "forecast_line" | "heatmap" | "kpi_strip" | "timeline";
  title: string;
  data: Array<Record<string, string | number>>;
}

export interface VoiceVisualResponse {
  displayMode: "executive_command_card" | "forecast_console" | "risk_map" | "simulation_brief";
  dashboardPanels: string[];
  kpis: VoiceVisualKPI[];
  charts: VoiceVisualChart[];
  recommendedActions: string[];
}

export interface VoiceAICouncilTurn {
  agent: string;
  role: string;
  finding: string;
  confidence: number;
  sourceSystems: string[];
}

export interface VoiceExecutiveReadiness {
  voiceInputStatus: "ready" | "degraded" | "missing";
  speechToTextStatus: "ready" | "degraded" | "missing";
  executiveReasoningStatus: "ready" | "degraded" | "missing";
  multiAgentCouncilStatus: "ready" | "degraded" | "missing";
  analyticsIntegrationStatus: "ready" | "degraded" | "missing";
  voiceOutputStatus: "ready" | "degraded" | "missing";
  memorySystemStatus: "ready" | "degraded" | "missing";
  dashboardControlStatus: "ready" | "degraded" | "missing";
  visualResponseStatus: "ready" | "degraded" | "missing";
  simulationStatus: "ready" | "degraded" | "missing";
  digitalTwinStatus: "ready" | "degraded" | "missing";
}

export interface VoiceCommandResponse {
  model: string;
  generatedAt: string;
  transcript: string;
  recognizedIntent:
    | "highest_risk_department"
    | "productivity_forecast"
    | "crisis_dashboard"
    | "security_posture"
    | "digital_twin_simulation"
    | "department_failure_forecast"
    | "company_threat"
    | "client_risk"
    | "company_health"
    | "revenue_forecast"
    | "project_risk"
    | "boardroom_priority"
    | "competitive_threat"
    | "innovation_opportunity"
    | "memory_query"
    | "recommendation"
    | "follow_up_explanation";
  targetDashboard: string;
  answer: string;
  spokenResponse: string;
  riskScore: number;
  confidence: number;
  workflowTriggered: string;
  actions: VoiceCommandAction[];
  sourceSystems: string[];
  commandTrace: string[];
  sessionId: string;
  liveTranscript: string;
  dashboardControl: VoiceDashboardControl;
  tts: VoiceTTSMetadata;
  voiceCapabilities: VoiceCapabilityStatus[];
  visualResponse: VoiceVisualResponse | null;
  aiCouncil: VoiceAICouncilTurn[];
  dashboardControlReady: boolean;
  analyticsCoverage: string[];
  simulationStatus: "ready" | "not_requested" | "degraded";
  memoryStatus: "ready" | "degraded" | "missing";
  executiveReadiness: VoiceExecutiveReadiness | null;
  productionReadinessScore: number;
  finalVerdict: "AI CEO ASSISTANT COMPLETE" | "AI CEO ASSISTANT GAPS REMAIN";
  conversationMemory: VoiceConversationMemoryItem[];
  recommendations: string[];
  supportedFollowups: string[];
  latencyMs: number;
  storage: string;
}

export interface VoiceDashboardControl {
  route: string;
  panelId: string;
  action: string;
  targetLabel: string;
}

export interface VoiceTTSMetadata {
  engine: string;
  voice: string;
  rate: number;
  pitch: number;
  latencyBudgetMs: number;
  playbackSupported: boolean;
}

export interface VoiceConversationMemoryItem {
  turnId: string;
  sessionId: string;
  speaker: string;
  transcript: string;
  intent: VoiceCommandResponse["recognizedIntent"];
  answer: string;
  targetDashboard: string;
  riskScore: number;
  createdAt: string;
}
