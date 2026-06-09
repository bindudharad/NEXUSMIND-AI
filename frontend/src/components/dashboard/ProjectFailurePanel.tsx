"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { AlertTriangle, Flame, FolderKanban, Gauge, Loader2, RefreshCw, Send, TrendingDown, Workflow } from "lucide-react";

import type { ProjectFailureResponse, ProjectRiskSeverity } from "@/types/project-failure";

type SnakeRecord = Record<string, unknown>;

const severityColor: Record<ProjectRiskSeverity, string> = {
  low: "#7CF0A6",
  medium: "#2EE9D3",
  high: "#F6B44B",
  critical: "#FF3B6B",
};

export function ProjectFailurePanel() {
  const [analysis, setAnalysis] = useState<ProjectFailureResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [streamStatus, setStreamStatus] = useState("connecting");

  const loadPortfolio = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await fetchJson("/api/project-failure/predict", { cache: "no-store" });
      if (!isProjectFailureResponse(payload)) throw new Error("Malformed project failure payload");
      setAnalysis(payload);
      setStreamStatus((status) => (status === "connecting" ? "polling" : status));
    } catch {
      setError("Project Failure AI could not load portfolio risk.");
    } finally {
      setLoading(false);
    }
  }, []);

  const runCrisisForecast = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await fetchJson(
        "/api/project-failure/predict",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(crisisProjectPayload()),
          cache: "no-store",
        },
        60000,
      );
      if (!isProjectFailureResponse(payload)) throw new Error("Malformed project failure payload");
      setAnalysis(payload);
      setStreamStatus((status) => (status === "connecting" ? "polling" : status));
    } catch {
      setError("Project Failure AI could not process the crisis forecast.");
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
        const response = await fetch("/api/project-failure/stream", { cache: "no-store", signal: controller.signal });
        if (!response.ok) throw new Error("Project failure stream failed");
        const reader = response.body?.getReader();
        if (!reader) throw new Error("Missing project failure stream");
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
            if (dataLine) {
              setAnalysis(toCamel<ProjectFailureResponse>(JSON.parse(dataLine.slice(6))));
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
      void loadPortfolio();
    }, 0);
    const streamRefresh = window.setTimeout(() => {
      void connectStream();
    }, 3200);
    return () => {
      controller.abort();
      window.clearTimeout(firstRefresh);
      window.clearTimeout(streamRefresh);
    };
  }, [loadPortfolio]);

  const portfolioChart = useMemo(
    () =>
      analysis?.predictions.map((project) => ({
        name: compactProjectName(project.projectName),
        failure: Math.round(project.failureProbability),
        delay: Math.round(project.deadlineMissProbability),
        budget: Math.round(project.budgetOverrunProbability),
        health: Math.round(project.healthScore),
      })) ?? [],
    [analysis],
  );

  const topProject = analysis?.predictions[0] ?? null;
  const forecastChart = useMemo(
    () =>
      topProject?.forecast.map((point) => ({
        day: `D${point.day}`,
        failure: Math.round(point.failureProbability),
        delay: Math.round(point.delayProbability),
        budget: Math.round(point.budgetOverrunProbability),
        sprint: Math.round(point.sprintCompletionProbability),
      })) ?? [],
    [topProject],
  );

  return (
    <section data-testid="project-failure-panel" className="border border-line/80 bg-panel/85 p-5 shadow-control backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <FolderKanban className="size-5 text-cyan" />
          <div>
            <p className="text-xs uppercase text-cyan">AI Project Failure Prediction</p>
            <h2 className="text-xl font-semibold text-white">Delivery failure, delay, budget, burnout impact, and resource-risk forecasting</h2>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button data-testid="load-project-failure" onClick={() => void loadPortfolio()} className="inline-flex items-center gap-2 border border-line bg-panel2 px-3 py-2 text-sm text-slate-300">
            <RefreshCw className="size-4" />
            Load portfolio
          </button>
          <button data-testid="simulate-project-failure" onClick={() => void runCrisisForecast()} className="inline-flex items-center gap-2 border border-signal/40 bg-signal/10 px-3 py-2 text-sm text-signal">
            {loading ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
            Simulate failure
          </button>
        </div>
      </div>

      {error ? <p className="mt-4 text-sm text-signal">{error}</p> : null}
      {loading && !analysis ? <p className="mt-5 text-sm text-slate-400">Running RandomForest/XGBoost project-risk inference and horizon forecasting...</p> : null}

      {analysis ? (
        <>
          <div className="mt-5 grid gap-3 md:grid-cols-6">
            <Stat label="Projects" value={String(analysis.summary.projectsAnalyzed)} />
            <Stat label="Avg failure" value={`${Math.round(analysis.summary.averageFailureProbability)}%`} />
            <Stat label="Avg delay" value={`${Math.round(analysis.summary.averageDelayProbability)}%`} />
            <Stat label="Critical" value={String(analysis.summary.criticalProjects)} />
            <Stat label="Health" value={`${Math.round(analysis.summary.averageHealthScore)}%`} />
            <Stat label="Stream" value={streamStatus} />
          </div>

          <div className="mt-5 grid gap-4 xl:grid-cols-[1fr_0.9fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
                <Gauge className="size-4" />
                Portfolio risk heatmap
              </div>
              <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                {analysis.heatmap.map((item) => (
                  <div key={item.project} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <h3 className="text-sm font-medium text-white">{compactProjectName(item.project)}</h3>
                        <p className="mt-1 text-xs text-slate-500">{item.team}</p>
                      </div>
                      <span className="text-xs text-cyan">{Math.round(item.health)} health</span>
                    </div>
                    <div className="mt-3 grid grid-cols-3 gap-2 text-xs">
                      <RiskPill label="Fail" value={item.failure} />
                      <RiskPill label="Delay" value={item.delay} />
                      <RiskPill label="Burn" value={item.burnout} />
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-4 h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={portfolioChart} margin={{ left: -22, right: 8, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="name" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Bar dataKey="failure" fill="#FF3B6B" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="delay" fill="#F6B44B" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="budget" fill="#2EE9D3" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-signal">
                <TrendingDown className="size-4" />
                {topProject ? compactProjectName(topProject.projectName) : "Top project"} forecast
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                {topProject ? (
                  <>
                    <SignalStat label="Failure" value={topProject.failureProbability} color="#FF3B6B" />
                    <SignalStat label="Deadline miss" value={topProject.deadlineMissProbability} color="#F6B44B" />
                    <SignalStat label="Budget overrun" value={topProject.budgetOverrunProbability} color="#2EE9D3" />
                    <SignalStat label="Ops instability" value={topProject.operationalInstability} color="#F05D5E" />
                  </>
                ) : null}
              </div>
              <div className="mt-4 h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={forecastChart} margin={{ left: -18, right: 8, top: 10, bottom: 0 }}>
                    <defs>
                      <linearGradient id="projectFailureGradient" x1="0" x2="0" y1="0" y2="1">
                        <stop offset="5%" stopColor="#FF3B6B" stopOpacity={0.32} />
                        <stop offset="95%" stopColor="#FF3B6B" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="day" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 10 }} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Area type="monotone" dataKey="failure" stroke="#FF3B6B" fill="url(#projectFailureGradient)" strokeWidth={2} />
                    <Area type="monotone" dataKey="delay" stroke="#F6B44B" fill="transparent" strokeWidth={2} />
                    <Area type="monotone" dataKey="sprint" stroke="#7CF0A6" fill="transparent" strokeWidth={2} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-amber">
                <AlertTriangle className="size-4" />
                Risk signals
              </div>
              <div className="grid gap-3">
                {(topProject?.riskSignals ?? []).slice(0, 6).map((signal) => (
                  <div key={`${signal.category}-${signal.score}`} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex items-center justify-between gap-2">
                      <h3 className="text-sm font-medium text-white">{labelize(signal.category)}</h3>
                      <span style={{ color: severityColor[signal.severity] }} className="text-xs uppercase">
                        {signal.severity} / {Math.round(signal.score)}
                      </span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{signal.evidence}</p>
                    <p className="mt-2 text-xs leading-5 text-slate-300">{signal.recommendation}</p>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-mint">
                <Workflow className="size-4" />
                AI recovery recommendations
              </div>
              <div className="grid gap-3 md:grid-cols-2">
                {[...(topProject?.recommendations ?? []), ...analysis.portfolioRecommendations].slice(0, 6).map((recommendation) => (
                  <div key={recommendation.recommendationId} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex items-start justify-between gap-2">
                      <h3 className="text-sm font-medium text-white">{recommendation.title}</h3>
                      <span className="text-xs text-cyan">{Math.round(recommendation.impactScore)} impact</span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{recommendation.action}</p>
                    <p className="mt-2 text-xs leading-5 text-slate-300">{recommendation.rationale}</p>
                  </div>
                ))}
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-3 md:grid-cols-3">
            {(analysis.predictions ?? []).slice(0, 3).map((project) => (
              <article key={project.projectId} className="border border-cyan/20 bg-cyan/10 p-4">
                <div className="flex items-center gap-2 text-xs uppercase text-cyan">
                  <Flame className="size-4" />
                  Burnout to delivery impact
                </div>
                <h3 className="mt-2 text-base font-semibold text-white">{compactProjectName(project.projectName)}</h3>
                <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
                  <RiskPill label="Collapse" value={project.teamCollapseRisk} />
                  <RiskPill label="Resources" value={project.resourceShortageImpact} />
                  <RiskPill label="Comms" value={project.communicationBottleneckRisk} />
                  <RiskPill label="Deps" value={project.dependencyFailureImpact} />
                </div>
              </article>
            ))}
          </div>
        </>
      ) : null}
    </section>
  );
}

function crisisProjectPayload() {
  return {
    horizon_days: 21,
    realtime: true,
    projects: [
      {
        project_id: "project-crisis-alpha",
        project_name: "Project Alpha Critical Launch",
        department: "Engineering",
        team_name: "Development Team",
        days_to_deadline: 9,
        budget_utilization: 1.12,
        required_skills: ["python", "api", "security", "mlops"],
        available_skills: ["python", "api"],
        team_size: 18,
        critical_dependency_count: 12,
        historical_delivery_rate: 0.46,
        current_scope_completion: 0.39,
        executive_visibility: 0.94,
        history: projectHistory("crisis"),
      },
      {
        project_id: "project-stable-omega",
        project_name: "Project Omega Knowledge Base",
        department: "Operations",
        team_name: "Enablement Team",
        days_to_deadline: 52,
        budget_utilization: 0.48,
        required_skills: ["docs", "automation", "analytics"],
        available_skills: ["docs", "automation", "analytics", "python"],
        team_size: 8,
        critical_dependency_count: 1,
        historical_delivery_rate: 0.93,
        current_scope_completion: 0.76,
        executive_visibility: 0.35,
        history: projectHistory("stable"),
      },
    ],
  };
}

function projectHistory(mode: "crisis" | "stable") {
  const now = Date.now();
  const base = mode === "crisis"
    ? { velocity: 0.48, completion: 0.44, burnout: 0.84, comms: 0.39, resource: 0.42, deps: 9, risks: 18, scope: 0.58, defect: 0.36, rework: 0.33, meeting: 0.83, budget: 1.15, compatibility: 0.42 }
    : { velocity: 0.82, completion: 0.84, burnout: 0.23, comms: 0.87, resource: 0.86, deps: 1, risks: 2, scope: 0.08, defect: 0.06, rework: 0.05, meeting: 0.28, budget: 0.5, compatibility: 0.84 };
  return Array.from({ length: 7 }, (_, index) => ({
    timestamp: new Date(now - (7 - index) * 86400000).toISOString(),
    sprint_velocity: clamp(base.velocity + (mode === "crisis" ? -index * 0.018 : index * 0.008)),
    task_completion_rate: clamp(base.completion + (mode === "crisis" ? -index * 0.016 : index * 0.006)),
    scope_change_rate: clamp(base.scope + index * 0.008),
    defect_rate: clamp(base.defect + index * 0.004),
    rework_ratio: clamp(base.rework + index * 0.004),
    dependency_bottlenecks: base.deps + Math.floor(index / 2),
    resource_allocation: clamp(base.resource + (mode === "crisis" ? -index * 0.01 : index * 0.006)),
    budget_burn_rate: Math.min(1.5, base.budget + index * 0.012),
    meeting_load: base.meeting,
    communication_score: clamp(base.comms + (mode === "crisis" ? -index * 0.014 : index * 0.004)),
    team_burnout: clamp(base.burnout + (mode === "crisis" ? index * 0.012 : -index * 0.004)),
    team_compatibility: clamp(base.compatibility + (mode === "crisis" ? -index * 0.01 : index * 0.005)),
    open_risks: base.risks + index,
  }));
}

function RiskPill({ label, value }: { label: string; value: number }) {
  const color = value >= 75 ? "#FF3B6B" : value >= 55 ? "#F6B44B" : value >= 35 ? "#2EE9D3" : "#7CF0A6";
  return (
    <div className="border border-line/50 bg-void/50 px-2 py-2">
      <span className="block text-slate-500">{label}</span>
      <strong style={{ color }} className="mt-1 block text-sm">
        {Math.round(value)}%
      </strong>
    </div>
  );
}

function SignalStat({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="border border-line/60 bg-panel/60 p-3">
      <span className="block text-xs uppercase text-slate-500">{label}</span>
      <strong style={{ color }} className="mt-1 block text-xl text-white">
        {Math.round(value)}%
      </strong>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-line/70 bg-panel2/65 p-3">
      <span className="block text-xs uppercase text-slate-500">{label}</span>
      <strong className="mt-1 block break-words text-base text-white">{value}</strong>
    </div>
  );
}

function compactProjectName(name: string) {
  return name.replace(/^Project\s+/i, "").replace(/\s+(Platform|Modernization|Migration|Launch)$/i, "");
}

function labelize(value: string) {
  return value.replace(/_/g, " ");
}

function clamp(value: number) {
  return Math.max(0, Math.min(1, value));
}

async function fetchJson(input: string, init: RequestInit, timeoutMs = 30000): Promise<unknown> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(input, { ...init, signal: controller.signal });
    if (!response.ok) throw new Error("Project failure request failed");
    return await response.json();
  } finally {
    window.clearTimeout(timeout);
  }
}

function isProjectFailureResponse(value: unknown): value is ProjectFailureResponse {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Partial<ProjectFailureResponse>;
  return Boolean(candidate.model && Array.isArray(candidate.predictions) && candidate.summary?.projectsAnalyzed !== undefined);
}

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
