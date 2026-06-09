"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Bar,
  BarChart as RechartsBarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart as RechartsLineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type React from "react";
import { Activity, AlertTriangle, BarChart3, Brain, Flame, Gauge, Loader2, Radio, RefreshCw, Send, ShieldAlert, Users } from "lucide-react";

import type { CompanyHealthPriority, CompanyHealthResponse } from "@/types/company-health";

const priorityColor: Record<CompanyHealthPriority, string> = {
  low: "#7CF0A6",
  medium: "#F6B44B",
  high: "#F05D5E",
  critical: "#FF3B6B",
};

export function CompanyHealthPanel() {
  const [analysis, setAnalysis] = useState<CompanyHealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [streamStatus, setStreamStatus] = useState("connecting");
  const manualScenarioUntil = useRef(0);

  const loadDefault = useCallback(async () => {
    setLoading(true);
    setError("");
    manualScenarioUntil.current = 0;
    try {
      const payload = await fetchJson("/api/company-health/analyze", { cache: "no-store" });
      if (!isCompanyHealthResponse(payload)) throw new Error("Malformed company health payload");
      setAnalysis(payload);
      setStreamStatus((status) => (status === "connecting" ? "polling" : status));
    } catch {
      setError("Real-Time Company Health Dashboard could not refresh live enterprise analytics.");
    } finally {
      setLoading(false);
    }
  }, []);

  const simulateRisk = useCallback(async () => {
    setLoading(true);
    setError("");
    manualScenarioUntil.current = Date.now() + 30000;
    try {
      const payload = await fetchJson(
        "/api/company-health/analyze",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(buildCompanyHealthStressPayload()),
          cache: "no-store",
        },
        60000,
      );
      if (!isCompanyHealthResponse(payload)) throw new Error("Malformed company health payload");
      setAnalysis(payload);
      setStreamStatus((status) => (status === "connecting" ? "polling" : status));
    } catch {
      setError("Real-Time Company Health Dashboard could not process the stress scenario.");
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
        const response = await fetch("/api/company-health/stream", { cache: "no-store", signal: controller.signal });
        if (!response.ok) throw new Error("Company health stream failed");
        const reader = response.body?.getReader();
        if (!reader) throw new Error("Missing company health stream");
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
            if (isCompanyHealthResponse(payload) && Date.now() > manualScenarioUntil.current) {
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

  const teamChartData = useMemo(
    () =>
      analysis?.teamScores.slice(0, 8).map((team) => ({
        name: team.teamName.split(" ")[0],
        health: Math.round(team.healthScore),
        risk: Math.round(team.riskScore),
        efficiency: Math.round(team.teamEfficiency),
        priority: team.priority,
      })) ?? [],
    [analysis],
  );

  const riskForecastData = useMemo(
    () =>
      analysis?.riskForecasts.map((point) => ({
        label: point.label,
        health: Math.round(point.companyHealthScore),
        burnout: Math.round(point.burnoutRisk),
        attrition: Math.round(point.attritionRisk),
        project: Math.round(point.projectFailureRisk),
        operational: Math.round(point.operationalRisk),
      })) ?? [],
    [analysis],
  );

  const productivityData = useMemo(
    () =>
      analysis?.productivityTrends.map((point) => ({
        label: point.label,
        productivity: Math.round(point.productivityScore),
        focus: Math.round(point.focusStability),
        meetings: Math.round(point.meetingEfficiency),
        delivery: Math.round(point.deliveryStability),
      })) ?? [],
    [analysis],
  );

  const heatmapData = useMemo(() => analysis?.heatmap.slice(0, 12) ?? [], [analysis]);

  return (
    <section data-testid="company-health-panel" className="border border-line/80 bg-panel/85 p-5 shadow-control backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <Gauge className="size-5 text-cyan" />
          <div>
            <p className="text-xs text-cyan">Company Health dashboard</p>
            <h2 className="text-xl font-semibold text-white">Real-Time Company Health Dashboard</h2>
            <p className="mt-2 max-w-5xl text-sm text-slate-500">
              Employee happiness heatmaps, Productivity analytics graphs, Risk-level visualizations, Project-health scorecards, Team efficiency charts, AI executive recommendation widgets, Live KPI monitoring panels, and Realtime company alerts
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button data-testid="refresh-company-health" onClick={() => void loadDefault()} className="inline-flex items-center gap-2 border border-line bg-panel2 px-3 py-2 text-sm text-slate-300">
            <RefreshCw className="size-4" />
            Refresh health
          </button>
          <button data-testid="simulate-company-health" onClick={() => void simulateRisk()} className="inline-flex items-center gap-2 border border-cyan/40 bg-cyan/10 px-3 py-2 text-sm text-cyan">
            {loading ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
            Simulate risk
          </button>
        </div>
      </div>

      {error && !analysis ? <p className="mt-4 text-sm text-signal">{error}</p> : null}
      {loading && !analysis ? <p className="mt-5 text-sm text-slate-400">Scoring employee happiness, productivity, burnout, attrition, project health, communication, and operational risk...</p> : null}

      {analysis ? (
        <>
          <div className="mt-5 grid gap-3 md:grid-cols-4 xl:grid-cols-8">
            {analysis.executiveKpis.slice(0, 7).map((kpi) => (
              <Stat key={kpi.label} label={kpi.label} value={kpi.value} tone={kpi.status === "risk" || kpi.status === "critical" ? "risk" : "normal"} />
            ))}
            <Stat label="Stream" value={streamStatus} tone="normal" />
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[1.08fr_0.92fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={BarChart3} label="Team efficiency charts" />
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <RechartsBarChart data={teamChartData} margin={{ left: -24, right: 8, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="name" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Bar dataKey="health" fill="#2EE9D3" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="efficiency" fill="#7CF0A6" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="risk" radius={[3, 3, 0, 0]}>
                      {teamChartData.map((item) => (
                        <Cell key={item.name} fill={priorityColor[item.priority]} />
                      ))}
                    </Bar>
                  </RechartsBarChart>
                </ResponsiveContainer>
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={Activity} label="Live KPI monitoring panels" />
              <div className="grid gap-3">
                <HealthMeter label="Company Health Score" value={analysis.summary.companyHealthScore} />
                <HealthMeter label="Employee happiness" value={analysis.summary.employeeHappinessScore} />
                <HealthMeter label="Productivity" value={analysis.summary.productivityScore} />
                <HealthMeter label="Workforce engagement" value={analysis.summary.workforceEngagement} />
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={Flame} label="Employee happiness heatmaps" />
              <div className="grid gap-2 sm:grid-cols-2">
                {heatmapData.map((point) => (
                  <div key={`${point.department}-${point.teamName}-${point.metric}`} className="border-l-2 bg-panel/60 p-3" style={{ borderColor: priorityColor[point.priority] }}>
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold text-white">{point.teamName}</p>
                        <p className="mt-1 text-xs text-slate-500">{point.metric}</p>
                      </div>
                      <span className="text-sm font-semibold" style={{ color: priorityColor[point.priority] }}>{Math.round(point.intensity)}</span>
                    </div>
                    <div className="mt-3 h-1.5 bg-black/30">
                      <div className="h-full" style={{ width: `${Math.round(point.intensity)}%`, backgroundColor: priorityColor[point.priority] }} />
                    </div>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={AlertTriangle} label="Risk-level visualizations" />
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <RechartsLineChart data={riskForecastData} margin={{ left: -22, right: 10, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="label" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Line type="monotone" dataKey="health" stroke="#2EE9D3" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="burnout" stroke="#FF3B6B" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="attrition" stroke="#F05D5E" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="project" stroke="#F6B44B" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="operational" stroke="#8B5CF6" strokeWidth={2} dot={false} />
                  </RechartsLineChart>
                </ResponsiveContainer>
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[1fr_0.95fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={Activity} label="Productivity analytics graphs" />
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <RechartsLineChart data={productivityData} margin={{ left: -22, right: 10, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="label" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Line type="monotone" dataKey="productivity" stroke="#2EE9D3" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="focus" stroke="#7CF0A6" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="meetings" stroke="#F6B44B" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="delivery" stroke="#8B5CF6" strokeWidth={2} dot={false} />
                  </RechartsLineChart>
                </ResponsiveContainer>
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={Users} label="Project-health scorecards" />
              <div className="space-y-3">
                {analysis.projectScorecards.slice(0, 5).map((project) => (
                  <div key={project.projectId} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold text-white">{project.department} / {project.teamName}</p>
                        <p className="mt-1 text-xs text-slate-500">{project.riskDrivers.join(", ")}</p>
                      </div>
                      <span className="text-sm font-semibold" style={{ color: priorityColor[project.priority] }}>{Math.round(project.healthScore)}%</span>
                    </div>
                    <p className="mt-2 text-xs text-slate-400">{project.recommendedAction}</p>
                  </div>
                ))}
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[1fr_1fr]">
            <article className="border border-cyan/25 bg-cyan/10 p-4">
              <SectionTitle icon={Brain} label="AI executive recommendation widgets" />
              <div className="space-y-3">
                {analysis.recommendations.slice(0, 5).map((recommendation) => (
                  <div key={`${recommendation.category}-${recommendation.title}`} className="border border-cyan/20 bg-panel/70 p-3">
                    <div className="flex items-start justify-between gap-3">
                      <p className="text-sm font-semibold text-white">{recommendation.title}</p>
                      <span className="text-sm font-semibold" style={{ color: priorityColor[recommendation.priority] }}>{Math.round(recommendation.expectedImpact)}</span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{recommendation.action}</p>
                    <p className="mt-2 text-[11px] uppercase text-slate-500">{recommendation.category} - {Math.round(recommendation.confidence * 100)}% confidence</p>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={ShieldAlert} label="Realtime company alerts" />
              <div className="space-y-3">
                {analysis.alerts.slice(0, 6).map((alert) => (
                  <div key={`${alert.category}-${alert.title}`} className="border-l-2 bg-panel/60 p-3" style={{ borderColor: priorityColor[alert.severity] }}>
                    <div className="flex items-start justify-between gap-3">
                      <p className="text-sm font-semibold text-white">{alert.title}</p>
                      <span className="text-sm font-semibold" style={{ color: priorityColor[alert.severity] }}>{Math.round(alert.probability)}%</span>
                    </div>
                    <p className="mt-2 text-xs text-slate-400">{alert.impact}</p>
                    <p className="mt-2 text-xs text-slate-500">{alert.recommendation}</p>
                  </div>
                ))}
              </div>
              <div className="mt-4 flex flex-wrap items-center gap-2 text-[11px] uppercase text-slate-500">
                <Radio className="size-3 text-cyan" />
                {analysis.model}
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-3 md:grid-cols-2">
            {analysis.executiveInsights.slice(0, 4).map((insight, index) => (
              <p key={`${insight}-${index}`} className="border border-line/60 bg-panel2/60 p-3 text-sm text-slate-300">
                {insight}
              </p>
            ))}
          </div>
        </>
      ) : null}
    </section>
  );
}

async function fetchJson(input: string, init?: RequestInit, timeoutMs = 45000): Promise<unknown> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(input, { ...init, signal: controller.signal });
    const text = await response.text();
    const payload = text ? (JSON.parse(text) as unknown) : {};
    if (!response.ok) throw new Error("Company health request failed");
    return payload;
  } finally {
    window.clearTimeout(timeout);
  }
}

function isCompanyHealthResponse(payload: unknown): payload is CompanyHealthResponse {
  const value = payload as Partial<CompanyHealthResponse> | null;
  return Boolean(
    value &&
      typeof value.model === "string" &&
      Array.isArray(value.executiveKpis) &&
      Array.isArray(value.teamScores) &&
      Array.isArray(value.heatmap) &&
      Array.isArray(value.productivityTrends) &&
      Array.isArray(value.riskForecasts) &&
      Array.isArray(value.projectScorecards) &&
      Array.isArray(value.recommendations) &&
      Array.isArray(value.alerts) &&
      value.summary,
  );
}

function SectionTitle({ icon: Icon, label }: { icon: React.ComponentType<{ className?: string }>; label: string }) {
  return (
    <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
      <Icon className="size-4" />
      {label}
    </div>
  );
}

function Stat({ label, value, tone }: { label: string; value: string; tone: "normal" | "risk" }) {
  return (
    <div className="border border-line/70 bg-panel2/70 p-3">
      <p className="text-xs uppercase text-slate-500">{label}</p>
      <strong className={`mt-1 block text-lg font-semibold ${tone === "risk" ? "text-signal" : "text-white"}`}>{value}</strong>
    </div>
  );
}

function HealthMeter({ label, value }: { label: string; value: number }) {
  const priority = value >= 75 ? "low" : value >= 62 ? "medium" : value >= 48 ? "high" : "critical";
  return (
    <div className="border border-line/60 bg-panel/60 p-3">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm text-slate-300">{label}</p>
        <span className="text-sm font-semibold" style={{ color: priorityColor[priority] }}>{Math.round(value)}%</span>
      </div>
      <div className="mt-3 h-1.5 bg-black/30">
        <div className="h-full" style={{ width: `${Math.round(value)}%`, backgroundColor: priorityColor[priority] }} />
      </div>
    </div>
  );
}

function buildCompanyHealthStressPayload() {
  return {
    cycle_name: "Realtime Company Health Stress Scenario",
    horizon_days: 45,
    realtime: true,
    teams: [
      {
        team_id: "company-ui-stable",
        department: "Product",
        team_name: "AI Product Studio",
        headcount: 18,
        employee_happiness_score: 88,
        productivity_score: 90,
        burnout_risk: 16,
        attrition_risk: 14,
        project_health: 91,
        collaboration_quality: 92,
        delivery_stability: 90,
        resource_utilization: 80,
        innovation_score: 86,
        security_risk: 8,
        communication_health: 91,
        meeting_efficiency: 86,
        workforce_engagement: 89,
        open_project_risks: 1,
        active_incidents: 0,
      },
      {
        team_id: "company-ui-crisis",
        department: "Operations",
        team_name: "Incident Response",
        headcount: 12,
        employee_happiness_score: 37,
        productivity_score: 42,
        burnout_risk: 91,
        attrition_risk: 84,
        project_health: 36,
        collaboration_quality: 44,
        delivery_stability: 32,
        resource_utilization: 122,
        innovation_score: 48,
        security_risk: 68,
        communication_health: 39,
        meeting_efficiency: 31,
        workforce_engagement: 35,
        open_project_risks: 23,
        active_incidents: 9,
      },
    ],
  };
}
