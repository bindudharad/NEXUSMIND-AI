import type { AttritionResponse } from "@/types/attrition";
import type { DashboardOverview } from "@/types/dashboard";
import type { EnterpriseImpactResponse } from "@/types/impact";
import type { IntelligenceOverview, ModelValidationResponse } from "@/types/intelligence";

const API_BASE_URL = process.env.API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";
const DEMO_EMAIL = process.env.DEMO_EMAIL ?? "ceo@nexusmind.ai";
const DEMO_PASSWORD = process.env.DEMO_PASSWORD ?? "nexusmind-demo";
const API_TIMEOUT_MS = Number(process.env.API_TIMEOUT_MS ?? 90000);
const HOMEPAGE_API_TIMEOUT_MS = Number(process.env.HOMEPAGE_API_TIMEOUT_MS ?? Math.min(API_TIMEOUT_MS, 90000));
const API_RETRY_ATTEMPTS = Number(process.env.API_RETRY_ATTEMPTS ?? 1);

type SnakeRecord = Record<string, unknown>;

function toCamel<T>(value: unknown): T {
  if (Array.isArray(value)) return value.map((item) => toCamel(item)) as T;
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value as SnakeRecord).map(([key, nested]) => [
        key.replace(/_([a-z])/g, (_, letter: string) => letter.toUpperCase()),
        toCamel(nested),
      ]),
    ) as T;
  }
  return value as T;
}

async function getDemoToken(timeoutMs = API_TIMEOUT_MS): Promise<string> {
  const response = await fetchWithRetry(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: DEMO_EMAIL, password: DEMO_PASSWORD }),
    cache: "no-store",
  }, timeoutMs);
  if (!response.ok) throw new Error("Demo login failed");
  const data = (await response.json()) as { access_token: string };
  return data.access_token;
}

async function authedGet<T>(path: string, token: string, timeoutMs = API_TIMEOUT_MS): Promise<T> {
  const response = await fetchWithRetry(`${API_BASE_URL}${path}`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  }, timeoutMs);
  if (!response.ok) throw new Error(`API request failed: ${path}`);
  return toCamel<T>(await response.json());
}

async function fetchWithRetry(input: string, init: RequestInit, timeoutMs = API_TIMEOUT_MS): Promise<Response> {
  let lastError: unknown;
  for (let attempt = 0; attempt < API_RETRY_ATTEMPTS; attempt += 1) {
    try {
      const response = await fetch(input, { ...init, signal: AbortSignal.timeout(timeoutMs) });
      if (response.ok || response.status < 500 || attempt === API_RETRY_ATTEMPTS - 1) return response;
      lastError = new Error(`Backend returned ${response.status}`);
    } catch (error) {
      lastError = error;
      if (attempt === API_RETRY_ATTEMPTS - 1) break;
    }
    await new Promise((resolve) => setTimeout(resolve, 350 * (attempt + 1)));
  }
  throw lastError instanceof Error ? lastError : new Error("Backend request failed");
}

export async function getCommandCenterData(): Promise<{
  dashboard: DashboardOverview;
  intelligence: IntelligenceOverview;
  modelValidation: ModelValidationResponse;
  source: "api" | "degraded";
}> {
  try {
    const token = await getDemoToken(HOMEPAGE_API_TIMEOUT_MS);
    const [dashboard, intelligence, modelValidation] = await Promise.allSettled([
      authedGet<DashboardOverview>("/dashboard/overview", token, HOMEPAGE_API_TIMEOUT_MS),
      authedGet<IntelligenceOverview>("/intelligence/overview", token, HOMEPAGE_API_TIMEOUT_MS),
      authedGet<ModelValidationResponse>("/intelligence/models/validation", token, HOMEPAGE_API_TIMEOUT_MS),
    ]);
    const degraded =
      dashboard.status === "rejected" || intelligence.status === "rejected" || modelValidation.status === "rejected";

    return {
      dashboard: dashboard.status === "fulfilled" ? dashboard.value : FALLBACK_DASHBOARD,
      intelligence: intelligence.status === "fulfilled" ? intelligence.value : FALLBACK_INTELLIGENCE,
      modelValidation: modelValidation.status === "fulfilled" ? modelValidation.value : FALLBACK_MODEL_VALIDATION,
      source: degraded ? "degraded" : "api",
    };
  } catch {
    return {
      dashboard: FALLBACK_DASHBOARD,
      intelligence: FALLBACK_INTELLIGENCE,
      modelValidation: FALLBACK_MODEL_VALIDATION,
      source: "degraded",
    };
  }
}

export async function getAttritionPredictionData(): Promise<AttritionResponse | null> {
  try {
    const token = await getDemoToken();
    return await authedGet<AttritionResponse>("/attrition/default", token);
  } catch {
    return null;
  }
}

export async function getEnterpriseImpactData(): Promise<EnterpriseImpactResponse | null> {
  try {
    const token = await getDemoToken(HOMEPAGE_API_TIMEOUT_MS);
    return await authedGet<EnterpriseImpactResponse>("/impact/summary", token, HOMEPAGE_API_TIMEOUT_MS);
  } catch {
    return null;
  }
}

const FALLBACK_DASHBOARD: DashboardOverview = {
  companyHealth: 84,
  predictionConfidence: 88,
  metrics: [
    { label: "Productivity", value: "86%", trend: 4.2, status: "optimal" },
    { label: "Employee Wellness", value: "78%", trend: -1.8, status: "watch" },
    { label: "Security Posture", value: "91%", trend: 2.1, status: "optimal" },
    { label: "Revenue Forecast", value: "$2.4M", trend: 6.5, status: "optimal" },
    { label: "Project Health", value: "81%", trend: 3.4, status: "watch" },
    { label: "Team Throughput", value: "1.18x", trend: 8.2, status: "optimal" },
  ],
  riskSignals: [
    {
      id: "risk-degraded-workforce",
      name: "Command-center data degraded",
      probability: 0.31,
      impact: "medium",
      recommendation: "Continue live subsystem monitoring while the aggregate overview retries.",
    },
  ],
  departments: [
    { department: "Engineering", productivity: 84, wellness: 76, security: 92, risk: 38 },
    { department: "Product", productivity: 81, wellness: 82, security: 89, risk: 29 },
    { department: "Security", productivity: 88, wellness: 79, security: 95, risk: 26 },
    { department: "Operations", productivity: 78, wellness: 74, security: 87, risk: 41 },
  ],
  agentMessages: [
    {
      agent: "Platform Agent",
      message: "Aggregate command-center data is isolated; live AI panels continue independent backend verification.",
      severity: "watch",
    },
  ],
  forecastSeries: [
    { label: "Jun 02", revenue: 1.1, risk: 34, productivity: 82 },
    { label: "Jun 03", revenue: 1.4, risk: 31, productivity: 84 },
    { label: "Jun 04", revenue: 1.8, risk: 29, productivity: 85 },
    { label: "Jun 05", revenue: 2.1, risk: 27, productivity: 86 },
    { label: "Jun 06", revenue: 2.3, risk: 26, productivity: 87 },
    { label: "Jun 07", revenue: 2.4, risk: 25, productivity: 88 },
  ],
};

const FALLBACK_INTELLIGENCE: IntelligenceOverview = {
  burnoutSignals: [
    {
      department: "Engineering",
      burnout: 42,
      stress: 58,
      attrition: 36,
      meetingLoad: 49,
      recommendation: "Keep workload rebalancing active while the aggregate overview refreshes.",
    },
    {
      department: "Operations",
      burnout: 47,
      stress: 61,
      attrition: 34,
      meetingLoad: 44,
      recommendation: "Protect incident owners with explicit recovery windows.",
    },
  ],
  securityEvents: [
    {
      id: "security-degraded-guard",
      title: "Security posture fallback monitor",
      actor: "Platform Agent",
      threatScore: 18,
      status: "guarded",
      response: "No browser-blocking security fault detected; subsystem panels remain active.",
    },
  ],
  simulations: [
    {
      id: "sim-degraded-shell",
      scenario: "Command center aggregate retry window",
      revenueImpact: "Low direct impact",
      delayProbability: 22,
      burnoutDelta: 3,
      recoveryPlan: "Retry aggregate APIs while live AI dashboards continue independent data pulls.",
    },
  ],
  executiveDirectives: [
    {
      command: "Show enterprise operating health",
      answer: "The command shell is in degraded mode, but live subsystem panels continue to fetch backend AI intelligence.",
      confidence: 82,
      action: "Monitor aggregate API recovery and continue reviewing subsystem output.",
    },
  ],
  agentCouncil: {
    topic: "Degraded command-center resilience",
    sharedMemory: ["Aggregate API timeout isolated", "Subsystem dashboards stay live"],
    turns: [
      {
        agent: "Reliability Agent",
        observation: "A slow aggregate overview should not blank the enterprise dashboard.",
        recommendation: "Use per-endpoint fallback and keep subsystem panels independent.",
        confidence: 91,
        memoryKeys: ["aggregate_api_timeout", "subsystem_route_health"],
        toolCalls: ["platform.operating_system", "system.feature_coverage"],
        workflowTrigger: "keep_resilient_shell_online",
      },
      {
        agent: "Knowledge Agent",
        observation: "Knowledge Loss Prevention data is delivered by its own backend route and proxy.",
        recommendation: "Continue visual verification on the live Knowledge Loss panel.",
        confidence: 89,
        memoryKeys: ["knowledge_loss_route", "vector_memory_health"],
        toolCalls: ["knowledge.query", "knowledge_loss.analyze"],
        workflowTrigger: "verify_knowledge_panel",
      },
    ],
    decision: "Render a resilient shell and preserve live AI module verification paths.",
    workflowTriggers: ["keep_resilient_shell_online", "verify_knowledge_panel"],
    coordinationScore: 88,
  },
  orgBrain: {
    nodes: [
      { id: "engineering", label: "Engineering", risk: 38 },
      { id: "knowledge", label: "Knowledge Systems", risk: 34 },
      { id: "operations", label: "Operations", risk: 41 },
      { id: "security", label: "Security", risk: 26 },
    ],
    edges: [
      { source: "engineering", target: "knowledge", strength: 0.82 },
      { source: "operations", target: "engineering", strength: 0.64 },
    ],
    bottlenecks: ["Aggregate overview retry in progress", "Subsystem panels remain independently hydrated"],
    recommendation: "Keep live AI route verification active and isolate command-center latency.",
  },
};

const FALLBACK_MODEL_VALIDATION: ModelValidationResponse = {
  available: false,
  metrics: [
    { model: "Command center aggregate fallback", accuracy: 0.82, rocAuc: 0.84, f1: 0.8, trainedSamples: 0 },
  ],
  predictionSample: {
    shell_resilience: 0.91,
    subsystem_independence: 0.89,
  },
};
