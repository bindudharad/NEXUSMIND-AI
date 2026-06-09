export type PlatformCapabilityStatus = "ready" | "configured" | "warning" | "missing" | "error";

export interface PlatformCapability {
  id: string;
  name: string;
  category: string;
  status: PlatformCapabilityStatus;
  score: number;
  details: string;
  evidence: string[];
  recommendation: string;
  sourceSystems: string[];
}

export interface PlatformMetric {
  label: string;
  value: number;
  unit: string;
  delta: number;
  severity: string;
}

export interface PlatformSummary {
  totalCapabilities: number;
  ready: number;
  configured: number;
  warnings: number;
  missing: number;
  errors: number;
  platformScore: number;
  executiveScore: number;
  realtimeStreams: number;
  cloudNativeScore: number;
}

export interface CompletePlatformResponse {
  model: string;
  generatedAt: string;
  summary: PlatformSummary;
  metrics: PlatformMetric[];
  capabilities: PlatformCapability[];
  dashboards: string[];
  aiStack: string[];
  dataStack: string[];
  devopsStack: string[];
  executiveBrief: string;
  storage: string;
}
