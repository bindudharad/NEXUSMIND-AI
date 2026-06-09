"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { AlertTriangle, BrainCircuit, Gauge, Loader2, Radio, RefreshCw, Route, Send, ShieldAlert, Users } from "lucide-react";

import type { DecisionAssistantResponse, DecisionPriority } from "@/types/decision-assistant";

const severityColor: Record<DecisionPriority, string> = {
  low: "#7CF0A6",
  medium: "#F6B44B",
  high: "#F05D5E",
  critical: "#FF3B6B",
};

export function DecisionAssistantPanel() {
  const [analysis, setAnalysis] = useState<DecisionAssistantResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [streamStatus, setStreamStatus] = useState("connecting");
  const manualScenarioUntil = useRef(0);

  const loadDefault = useCallback(async () => {
    setLoading(true);
    setError("");
    manualScenarioUntil.current = 0;
    try {
      const payload = await fetchJson("/api/decision-assistant/recommend", { cache: "no-store" });
      if (!isDecisionAssistant(payload)) throw new Error("Malformed decision assistant payload");
      setAnalysis(payload);
      setStreamStatus((status) => (status === "connecting" ? "polling" : status));
    } catch {
      setError("AI Decision Assistant for Managers could not refresh live routing intelligence.");
    } finally {
      setLoading(false);
    }
  }, []);

  const simulateRoutingDecision = useCallback(async () => {
    setLoading(true);
    setError("");
    manualScenarioUntil.current = Date.now() + 30000;
    try {
      const payload = await fetchJson(
        "/api/decision-assistant/recommend",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(buildDecisionScenario()),
          cache: "no-store",
        },
        60000,
      );
      if (!isDecisionAssistant(payload)) throw new Error("Malformed decision assistant payload");
      setAnalysis(payload);
      setStreamStatus((status) => (status === "connecting" ? "polling" : status));
    } catch {
      setError("AI Decision Assistant for Managers could not process the project-routing scenario.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    async function connectStream() {
      let streamStarted = false;
      const fallback = window.setTimeout(() => {
        if (!streamStarted && !controller.signal.aborted) setStreamStatus("polling");
      }, 12000);
      try {
        const response = await fetch("/api/decision-assistant/stream", { cache: "no-store", signal: controller.signal });
        if (!response.ok) throw new Error("Decision assistant stream failed");
        const reader = response.body?.getReader();
        if (!reader) throw new Error("Missing decision assistant stream");
        const decoder = new TextDecoder();
        let buffer = "";
        streamStarted = true;
        window.clearTimeout(fallback);
        setStreamStatus("streaming");
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const events = buffer.split("\n\n");
          buffer = events.pop() ?? "";
          for (const event of events) {
            const dataLine = event.split("\n").find((line) => line.startsWith("data: "));
            if (!dataLine) continue;
            const payload = JSON.parse(dataLine.slice(6));
            if (isDecisionAssistant(payload) && Date.now() > manualScenarioUntil.current) {
              setAnalysis(payload);
              setLoading(false);
            }
          }
        }
        setStreamStatus("polling");
      } catch {
        if (!controller.signal.aborted) setStreamStatus("polling");
      } finally {
        window.clearTimeout(fallback);
      }
    }

    const firstRefresh = window.setTimeout(() => {
      void loadDefault();
    }, 0);
    const streamRefresh = window.setTimeout(() => {
      void connectStream();
    }, 3200);
    return () => {
      controller.abort();
      window.clearTimeout(firstRefresh);
      window.clearTimeout(streamRefresh);
    };
  }, [loadDefault]);

  const rankingData = useMemo(
    () =>
      analysis?.rankings.slice(0, 6).map((team) => ({
        name: team.teamName.split(" ")[0],
        suitability: Math.round(team.suitabilityScore),
        success: Math.round(team.deliverySuccessProbability),
        risk: Math.round(team.riskScore),
      })) ?? [],
    [analysis],
  );

  const timelineData = useMemo(
    () =>
      analysis?.timelineForecast.map((point) => ({
        day: `D${point.day}`,
        completion: Math.round(point.completionProbability),
        delay: Math.round(point.delayRisk),
        workload: Math.round(point.workloadPressure),
      })) ?? [],
    [analysis],
  );

  const capabilityData = useMemo(
    () =>
      analysis?.capabilityForecast.slice(0, 6).map((team) => ({
        name: team.teamName.split(" ")[0],
        skill: Math.round(team.skillFit),
        capacity: Math.round(team.capacityFit),
        delivery: Math.round(team.deliveryFit),
        stability: Math.round(team.stabilityFit),
        overall: Math.round(team.overallCapability),
      })) ?? [],
    [analysis],
  );

  return (
    <section data-testid="decision-assistant-panel" className="border border-line/80 bg-panel/85 p-5 shadow-control backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <BrainCircuit className="size-5 text-cyan" />
          <div>
            <p className="text-xs uppercase text-cyan">AI Decision Assistant for Managers</p>
            <h2 className="text-xl font-semibold text-white">Managerial project-routing intelligence and delivery-risk forecasting</h2>
            <p className="mt-2 max-w-5xl text-sm text-slate-500">
              AI decision dashboard, Team recommendation panels, Risk-analysis heatmaps, Timeline forecasting charts, Team capability analytics, Burnout-risk indicators, Resource-utilization graphs, and Executive recommendation widgets
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button data-testid="refresh-decision-assistant" onClick={() => void loadDefault()} className="inline-flex items-center gap-2 border border-line bg-panel2 px-3 py-2 text-sm text-slate-300">
            <RefreshCw className="size-4" />
            Refresh decision
          </button>
          <button data-testid="simulate-decision-assistant" onClick={() => void simulateRoutingDecision()} className="inline-flex items-center gap-2 border border-cyan/40 bg-cyan/10 px-3 py-2 text-sm text-cyan">
            {loading ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
            Simulate route
          </button>
        </div>
      </div>

      {error && !analysis ? <p className="mt-4 text-sm text-signal">{error}</p> : null}
      {loading && !analysis ? <p className="mt-5 text-sm text-slate-400">Scoring team skills, workload, burnout, timeline risk, historical delivery, cost, and executive priority...</p> : null}

      {analysis ? (
        <>
          <div className="mt-5 grid gap-3 md:grid-cols-4 xl:grid-cols-8">
            <Stat label="Best Team" value={analysis.summary.recommendedTeam} />
            <Stat label="Score" value={`${Math.round(analysis.summary.bestTeamScore)}%`} />
            <Stat label="Success" value={`${Math.round(analysis.summary.successProbability)}%`} />
            <Stat label="Completion" value={`${analysis.summary.estimatedCompletionDays.toFixed(1)}d`} />
            <Stat label="Risk" value={`${Math.round(analysis.summary.deliveryRisk)}%`} tone={analysis.summary.deliveryRisk >= 55 ? "risk" : "normal"} />
            <Stat label="Workload" value={`${Math.round(analysis.summary.workloadImpact)}%`} tone={analysis.summary.workloadImpact >= 90 ? "risk" : "normal"} />
            <Stat label="Skill Gaps" value={String(analysis.summary.skillGapCount)} />
            <Stat label="Stream" value={streamStatus} />
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <PanelTitle icon={Route} label="Team recommendation panels" />
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={rankingData} margin={{ left: -24, right: 8, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="name" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Bar dataKey="suitability" fill="#2EE9D3" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="success" fill="#7CF0A6" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="risk" radius={[3, 3, 0, 0]}>
                      {rankingData.map((item) => (
                        <Cell key={item.name} fill={item.risk >= 70 ? "#FF3B6B" : item.risk >= 45 ? "#F6B44B" : "#64748b"} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </article>

            <article className="border border-cyan/25 bg-cyan/10 p-4">
              <PanelTitle icon={Users} label="Executive recommendation widgets" />
              <div className="grid gap-3">
                {analysis.rankings.slice(0, 3).map((team) => (
                  <div key={team.teamId} className="border border-cyan/20 bg-panel/70 p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="text-sm font-semibold text-white">#{team.rank} {team.teamName}</span>
                      <span className="text-xs text-cyan">{Math.round(team.suitabilityScore)}% fit</span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{team.rationale}</p>
                    <div className="mt-2 flex flex-wrap gap-2 text-xs text-slate-500">
                      <span>{Math.round(team.skillCompatibility)}% skill</span>
                      <span>{Math.round(team.capacityScore)}% capacity</span>
                      <span>{formatMoney(team.estimatedCost)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[1fr_1fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <PanelTitle icon={Radio} label="Timeline forecasting charts" />
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={timelineData} margin={{ left: -24, right: 8, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="day" stroke="#64748b" tickLine={false} axisLine={false} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Line type="monotone" dataKey="completion" stroke="#7CF0A6" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="delay" stroke="#F05D5E" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="workload" stroke="#F6B44B" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <PanelTitle icon={Gauge} label="Team capability analytics" />
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={capabilityData} margin={{ left: -24, right: 8, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="name" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Bar dataKey="overall" fill="#2EE9D3" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="skill" fill="#7CF0A6" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="stability" fill="#64748b" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </article>
          </div>

          <div className="mt-5 grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <PanelTitle icon={AlertTriangle} label="Risk-analysis heatmaps" />
              <div className="grid gap-2 sm:grid-cols-2">
                {analysis.riskHeatmap.slice(0, 12).map((point) => (
                  <div key={`${point.teamName}-${point.metric}`} className="border-l-2 bg-panel/60 p-3" style={{ borderColor: severityColor[point.severity] }}>
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold text-white">{point.teamName}</p>
                        <p className="mt-1 text-xs text-slate-500">{point.metric}</p>
                      </div>
                      <span className="text-sm font-semibold" style={{ color: severityColor[point.severity] }}>{Math.round(point.score)}%</span>
                    </div>
                    <div className="mt-3 h-1.5 bg-black/30">
                      <div className="h-full" style={{ width: `${Math.round(point.score)}%`, backgroundColor: severityColor[point.severity] }} />
                    </div>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <PanelTitle icon={ShieldAlert} label="Burnout-risk indicators" />
              <div className="grid gap-2">
                {analysis.alerts.map((alert) => (
                  <div key={`${alert.title}-${alert.probability}`} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="text-sm font-medium text-white">{alert.title}</span>
                      <span className="text-xs uppercase" style={{ color: severityColor[alert.severity] }}>{alert.severity} / {Math.round(alert.probability)}%</span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{alert.impact}</p>
                    <p className="mt-1 text-xs leading-5 text-slate-500">{alert.mitigation}</p>
                  </div>
                ))}
              </div>
            </article>
          </div>

          <div className="mt-5 grid gap-4 xl:grid-cols-[1fr_1fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="text-xs uppercase text-cyan">AI decision dashboard</div>
              <div className="mt-3 grid gap-2">
                {analysis.executiveInsights.map((insight) => (
                  <p key={insight} className="border border-line/60 bg-panel/60 p-3 text-xs leading-5 text-slate-400">{insight}</p>
                ))}
              </div>
              <p className="mt-3 border border-line/60 bg-panel/60 p-3 text-xs leading-5 text-slate-500">
                Models: {analysis.model}. Sources: {analysis.sourceSystems.join(", ")}.
              </p>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="text-xs uppercase text-mint">Managerial routing recommendations</div>
              <div className="mt-3 grid gap-2">
                {analysis.recommendations.map((item) => (
                  <div key={item.title} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="text-sm font-medium text-white">{item.title}</span>
                      <span className="text-xs uppercase" style={{ color: severityColor[item.priority] }}>{item.category} / {Math.round(item.confidence * 100)}%</span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{item.action}</p>
                    <p className="mt-1 text-xs leading-5 text-slate-500">{item.expectedImpact}</p>
                  </div>
                ))}
              </div>
            </article>
          </div>
        </>
      ) : null}
    </section>
  );
}

function PanelTitle({ icon: Icon, label }: { icon: typeof Route; label: string }) {
  return (
    <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
      <Icon className="size-4" />
      {label}
    </div>
  );
}

function Stat({ label, value, tone = "normal" }: { label: string; value: string; tone?: "normal" | "risk" }) {
  return (
    <div className="border border-line/70 bg-panel2/65 p-3">
      <p className="text-xs uppercase text-slate-500">{label}</p>
      <strong className={`mt-2 block truncate text-lg font-semibold ${tone === "risk" ? "text-signal" : "text-white"}`}>{value}</strong>
    </div>
  );
}

function formatMoney(value: number) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(value);
}

async function fetchJson(input: string, init: RequestInit, timeoutMs = 30000): Promise<unknown> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(input, { ...init, signal: controller.signal });
    if (!response.ok) throw new Error("Decision assistant request failed");
    return await response.json();
  } finally {
    window.clearTimeout(timeout);
  }
}

function isDecisionAssistant(value: unknown): value is DecisionAssistantResponse {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Partial<DecisionAssistantResponse>;
  return Boolean(candidate.model && candidate.summary?.recommendedTeam && Array.isArray(candidate.rankings));
}

function buildDecisionScenario() {
  return {
    question: "Which team should handle the Project Atlas Kubernetes security migration?",
    horizon_days: 42,
    realtime: true,
    project: {
      project_id: "project-atlas-ui",
      project_name: "Project Atlas Kubernetes Security Migration",
      description: "Secure migration of FastAPI, MLOps, observability, and realtime AI services onto Kubernetes.",
      required_skills: ["kubernetes", "security", "observability", "fastapi", "mlops"],
      complexity: 0.82,
      deadline_days: 22,
      budget: 720000,
      revenue_impact: 2800000,
      dependency_count: 8,
      security_sensitivity: 0.86,
      innovation_requirement: 0.66,
      scope_volatility: 0.38,
      executive_visibility: 0.91,
    },
    teams: [
      team("fit-team", "Platform AI Delivery", "Engineering", ["kubernetes", "security", "observability", "fastapi", "mlops", "python", "realtime streaming"], 9, 0.92, 0.91, 0.66, 0.46, 0.9, 0.9, 0.88, 0.2, 0.12, 0.92, 0.82, 118, 1),
      team("overloaded-team", "Security Incident Response", "Security", ["kubernetes", "security", "observability", "fastapi", "mlops"], 7, 0.78, 0.72, 1.22, 0.08, 0.64, 0.69, 0.68, 0.88, 0.46, 0.62, 0.58, 136, 7),
      team("weak-team", "Design Systems", "Product", ["dashboard", "ux research", "accessibility"], 6, 0.72, 0.78, 0.62, 0.42, 0.68, 0.88, 0.86, 0.18, 0.1, 0.74, 0.76, 86, 0),
    ],
  };
}

function team(
  team_id: string,
  team_name: string,
  department: string,
  skills: string[],
  member_count: number,
  historical_success_rate: number,
  productivity_score: number,
  current_workload: number,
  capacity_available: number,
  sprint_velocity: number,
  communication_quality: number,
  collaboration_score: number,
  burnout_risk: number,
  attrition_risk: number,
  delivery_consistency: number,
  innovation_score: number,
  hourly_cost: number,
  active_incidents: number,
) {
  return {
    team_id,
    team_name,
    department,
    skills,
    member_count,
    historical_success_rate,
    productivity_score,
    current_workload,
    capacity_available,
    sprint_velocity,
    communication_quality,
    collaboration_score,
    burnout_risk,
    attrition_risk,
    delivery_consistency,
    innovation_score,
    hourly_cost,
    active_incidents,
  };
}
