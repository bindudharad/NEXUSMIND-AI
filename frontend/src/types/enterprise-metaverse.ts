export type MetaverseRoomType =
  | "headquarters"
  | "department"
  | "team"
  | "project"
  | "meeting_room"
  | "data_room"
  | "executive_command_center"
  | "crisis_command_room"
  | "innovation_lab";

export type MetaverseOverlayType = "risk" | "productivity" | "burnout" | "revenue" | "security" | "client" | "simulation" | "agent";
export type MetaverseRiskLevel = "low" | "medium" | "high" | "critical";
export type MetaverseNavigationAction = "navigate" | "inspect" | "simulate" | "show_overlay" | "summon_agent";
export type MetaverseSimulationType =
  | "revenue_drop"
  | "mass_resignation"
  | "cloud_outage"
  | "team_restructure"
  | "new_market_expansion"
  | "workload_increase"
  | "cyberattack";

export interface MetaverseVector3 {
  x: number;
  y: number;
  z: number;
}

export interface MetaverseRoom {
  roomId: string;
  name: string;
  roomType: MetaverseRoomType;
  level: number;
  position: MetaverseVector3;
  size: MetaverseVector3;
  color: string;
  glowColor: string;
  healthScore: number;
  riskScore: number;
  riskLevel: MetaverseRiskLevel;
  occupancy: number;
  kpis: Record<string, number | string | boolean>;
  analytics: string[];
  overlays: MetaverseOverlayType[];
  enterActions: string[];
  sourceSystems: string[];
}

export interface MetaverseConnection {
  sourceRoomId: string;
  targetRoomId: string;
  connectionType: "corridor" | "elevator" | "data_link" | "risk_propagation" | "agent_route";
  strength: number;
  latencyMs: number;
  riskFlow: number;
  sourceSystems: string[];
}

export interface MetaverseOverlay {
  overlayId: string;
  roomId: string;
  overlayType: MetaverseOverlayType;
  label: string;
  value: number;
  severity: MetaverseRiskLevel;
  color: string;
  explanation: string;
  sourceSystems: string[];
}

export interface MetaverseAgentAvatar {
  avatarId: string;
  agentName: string;
  roomId: string;
  position: MetaverseVector3;
  color: string;
  currentMessage: string;
  recommendation: string;
  confidence: number;
  sourceSystems: string[];
}

export interface MetaverseSimulationImpact {
  scenarioId: string;
  scenarioType: MetaverseSimulationType;
  question: string;
  affectedRooms: string[];
  propagationEdges: string[];
  riskDelta: number;
  revenueImpactPercent: number;
  burnoutDelta: number;
  productivityDelta: number;
  recoveryTimeline: string[];
  recommendedActions: string[];
  digitalTwinEvidence: string[];
  confidence: number;
  sourceSystems: string[];
}

export interface MetaverseNavigationState {
  selectedRoomId: string;
  action: MetaverseNavigationAction;
  cameraTarget: MetaverseVector3;
  cameraPosition: MetaverseVector3;
  route: string[];
  transcript: string;
  confidence: number;
}

export interface MetaverseDigitalTwinSync {
  twin: "employee" | "team" | "department" | "project" | "company" | "client";
  status: "synced" | "degraded" | "missing";
  updateRule: string;
  latestSignal: string;
  roomIds: string[];
}

export interface MetaversePerformanceStatus {
  renderer: string;
  estimatedFps: number;
  drawCalls: number;
  instancedMeshes: number;
  roomCount: number;
  overlayCount: number;
  assetStrategy: string;
  scalabilityTarget: string;
  status: "ready" | "degraded" | "missing";
}

export interface MetaverseSummary {
  roomCount: number;
  departmentRooms: number;
  teamRooms: number;
  dataRooms: number;
  activeOverlays: number;
  agentAvatars: number;
  companyHealthScore: number;
  highestRiskScore: number;
  productionReadinessScore: number;
  innovationScore: number;
  judgeWowFactorScore: number;
  streamSequence: number;
}

export interface EnterpriseMetaverseControlRoomResponse {
  model: string;
  generatedAt: string;
  experienceName: string;
  executiveBrief: string;
  summary: MetaverseSummary;
  rooms: MetaverseRoom[];
  connections: MetaverseConnection[];
  overlays: MetaverseOverlay[];
  agentAvatars: MetaverseAgentAvatar[];
  navigation: MetaverseNavigationState;
  simulation: MetaverseSimulationImpact | null;
  digitalTwinSync: MetaverseDigitalTwinSync[];
  performance: MetaversePerformanceStatus;
  voiceCommands: string[];
  recommendations: string[];
  sourceSystems: string[];
  finalVerdict: string;
  storage: string;
}

export interface MetaverseVoiceNavigationResponse {
  model: string;
  generatedAt: string;
  command: string;
  interpretedAction: MetaverseNavigationAction;
  targetRoomId: string;
  spokenResponse: string;
  navigation: MetaverseNavigationState;
  visualOverlays: MetaverseOverlay[];
  recommendedActions: string[];
  sourceSystems: string[];
  storage: string;
}
