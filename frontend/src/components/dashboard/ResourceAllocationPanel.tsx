"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
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
import { Boxes, GitBranch, Loader2, Radio, RefreshCw, Route, Send, ShieldAlert } from "lucide-react";

import type { ResourceAllocationResponse, ResourceSeverity } from "@/types/resource-allocation";

const severityColor: Record<ResourceSeverity, string> = {
  low: "#7CF0A6",
  medium: "#F6B44B",
  high: "#F05D5E",
  critical: "#FF3B6B",
};

export function ResourceAllocationPanel() {
  const [analysis, setAnalysis] = useState<ResourceAllocationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [streamStatus, setStreamStatus] = useState("connecting");

  const loadDefault = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await fetchJson("/api/resource-allocation/optimize", { cache: "no-store" });
      if (!isResourceAllocation(payload)) throw new Error("Malformed resource allocation payload");
      setAnalysis(payload);
      setStreamStatus((status) => (status === "connecting" ? "polling" : status));
    } catch {
      setError("AI Resource Allocation System could not refresh the live plan.");
    } finally {
      setLoading(false);
    }
  }, []);

  const simulateOverload = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await fetchJson(
        "/api/resource-allocation/optimize",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(buildOverloadPayload()),
          cache: "no-store",
        },
        60000,
      );
      if (!isResourceAllocation(payload)) throw new Error("Malformed resource allocation payload");
      setAnalysis(payload);
      setStreamStatus((status) => (status === "connecting" ? "polling" : status));
    } catch {
      setError("AI Resource Allocation System could not process the overload scenario.");
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
        const response = await fetch("/api/resource-allocation/stream", { cache: "no-store", signal: controller.signal });
        if (!response.ok) throw new Error("Resource allocation stream failed");
        const reader = response.body?.getReader();
        if (!reader) throw new Error("Missing allocation stream");
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
            if (isResourceAllocation(payload)) {
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

  const workloadData = useMemo(
    () =>
      analysis?.workloadBalance.map((item) => ({
        name: item.name.split(" ")[0],
        current: Math.round(item.currentUtilization),
        optimized: Math.round(item.optimizedUtilization),
        risk: Math.round(item.overloadRisk),
      })) ?? [],
    [analysis],
  );

  const forecastData = useMemo(
    () =>
      analysis?.capacityForecast.map((point, index) => ({
        sprint: `S+${index}`,
        utilization: Math.round(point.capacityUtilization),
        delivery: Math.round(point.deliveryProbability),
        shortage: Math.round(point.shortageHours),
        burnout: Math.round(point.burnoutPressure),
      })) ?? [],
    [analysis],
  );

  return (
    <section data-testid="resource-allocation-panel" className="border border-line/80 bg-panel/85 p-5 shadow-control backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <Route className="size-5 text-cyan" />
          <div>
            <p className="text-xs uppercase text-cyan">AI Resource Allocation System</p>
            <h2 className="text-xl font-semibold text-white">Task assignment, workload balancing, sprint capacity forecasting, and burnout-safe delivery optimization</h2>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button data-testid="refresh-resource-allocation" onClick={() => void loadDefault()} className="inline-flex items-center gap-2 border border-line bg-panel2 px-3 py-2 text-sm text-slate-300">
            <RefreshCw className="size-4" />
            Refresh plan
          </button>
          <button data-testid="simulate-resource-allocation" onClick={() => void simulateOverload()} className="inline-flex items-center gap-2 border border-cyan/40 bg-cyan/10 px-3 py-2 text-sm text-cyan">
            {loading ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
            Simulate overload
          </button>
        </div>
      </div>

      {error && !analysis ? <p className="mt-4 text-sm text-signal">{error}</p> : null}
      {loading && !analysis ? <p className="mt-5 text-sm text-slate-400">Optimizing skills, capacity, dependency graph pressure, deadlines, and burnout risk...</p> : null}

      {analysis ? (
        <>
          <div className="mt-5 grid gap-3 md:grid-cols-4 xl:grid-cols-8">
            <Stat label="Assignments" value={String(analysis.summary.assignmentsGenerated)} />
            <Stat label="Utilization" value={`${Math.round(analysis.summary.capacityUtilization)}%`} />
            <Stat label="Completion" value={`${Math.round(analysis.summary.sprintCompletionProbability)}%`} />
            <Stat label="Delivery" value={`${Math.round(analysis.summary.deliverySuccessProbability)}%`} />
            <Stat label="Delay" value={`${analysis.summary.projectedDelayDays.toFixed(1)}d`} />
            <Stat label="Overload cut" value={`${Math.round(analysis.summary.overloadReduction)}%`} />
            <Stat label="Avoidance" value={formatMoney(analysis.summary.estimatedCostAvoidance)} />
            <Stat label="Stream" value={streamStatus} />
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
                <Boxes className="size-4" />
                Workload heatmap
              </div>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={workloadData} margin={{ left: -24, right: 8, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="name" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Bar dataKey="current" fill="#64748b" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="optimized" fill="#2EE9D3" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="risk" radius={[3, 3, 0, 0]}>
                      {workloadData.map((item) => (
                        <Cell key={item.name} fill={item.risk >= 75 ? "#FF3B6B" : item.risk >= 55 ? "#F6B44B" : "#7CF0A6"} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-mint">
                <Radio className="size-4" />
                Capacity forecast
              </div>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={forecastData} margin={{ left: -24, right: 8, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="sprint" stroke="#64748b" tickLine={false} axisLine={false} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Line type="monotone" dataKey="utilization" stroke="#2EE9D3" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="delivery" stroke="#7CF0A6" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="burnout" stroke="#F05D5E" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="shortage" stroke="#F6B44B" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </article>
          </div>

          <div className="mt-5 grid gap-4 xl:grid-cols-[1fr_0.95fr]">
            <article className="border border-cyan/25 bg-cyan/10 p-4">
              <div className="text-xs uppercase text-cyan">Smart task assignment AI</div>
              <div className="mt-3 grid gap-2">
                {analysis.assignments.slice(0, 5).map((assignment) => (
                  <div key={assignment.taskId} className="border border-cyan/20 bg-panel/70 p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="text-sm font-medium text-white">{assignment.taskTitle}</span>
                      <span className="text-xs text-cyan">{Math.round(assignment.assignmentScore)}% / {assignment.employeeName}</span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{assignment.rationale}</p>
                    <div className="mt-2 flex flex-wrap gap-2 text-xs text-slate-500">
                      <span>Skill {Math.round(assignment.skillMatchScore)}%</span>
                      <span>Delivery {Math.round(assignment.deliverySuccessProbability)}%</span>
                      <span>Delay {Math.round(assignment.delayRisk)}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-amber">
                <GitBranch className="size-4" />
                Dependency graph optimizer
              </div>
              <div className="grid gap-2">
                {analysis.dependencyGraph.slice(0, 5).map((edge) => (
                  <div key={`${edge.source}-${edge.target}`} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="text-sm text-white">{edge.source}</span>
                      <span className="text-xs text-amber">{Math.round(edge.bottleneckScore)}% bottleneck</span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{edge.edgeType} to {edge.target}</p>
                  </div>
                ))}
              </div>
              <div className="mt-3 border border-line/60 bg-panel/60 p-3 text-xs leading-5 text-slate-500">
                Models: {analysis.mlModel} / {analysis.optimizationModel} / {analysis.graphModel}
              </div>
            </article>
          </div>

          <div className="mt-5 grid gap-4 xl:grid-cols-[1fr_1fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-signal">
                <ShieldAlert className="size-4" />
                Realtime resource alerts
              </div>
              <div className="grid gap-2">
                {analysis.riskAlerts.map((alert) => (
                  <div key={`${alert.title}-${alert.probability}`} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="text-sm font-medium text-white">{alert.title}</span>
                      <span className="text-xs uppercase" style={{ color: severityColor[alert.severity] }}>{alert.severity} / {Math.round(alert.probability)}%</span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{alert.intervention}</p>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="text-xs uppercase text-cyan">Sprint planning recommendations</div>
              <div className="mt-3 grid gap-2">
                {analysis.sprintPlan.map((item) => (
                  <div key={item.title} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="text-sm font-medium text-white">{item.title}</span>
                      <span className="text-xs uppercase" style={{ color: severityColor[item.priority] }}>{item.priority} / {Math.round(item.confidence * 100)}%</span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{item.action} {item.expectedImpact}</p>
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

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-line/70 bg-panel2/65 p-3">
      <p className="text-xs uppercase text-slate-500">{label}</p>
      <strong className="mt-2 block truncate text-lg font-semibold text-white">{value}</strong>
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
    if (!response.ok) throw new Error("Resource allocation request failed");
    return await response.json();
  } finally {
    window.clearTimeout(timeout);
  }
}

function isResourceAllocation(value: unknown): value is ResourceAllocationResponse {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Partial<ResourceAllocationResponse>;
  return Boolean(candidate.model && candidate.summary?.assignmentsGenerated !== undefined && Array.isArray(candidate.assignments));
}

function buildOverloadPayload() {
  return {
    department: "Engineering",
    sprint_name: "Sprint 5 Emergency Rebalance",
    planning_horizon_days: 14,
    objective: "burnout_safe",
    realtime: true,
    employees: [
      employee("res-overloaded", "Employee A", "Backend Lead", "Core", ["python", "api architecture", "incident response"], 40, 62, 0.78, 0.68, 0.62, 0.72, 0.58, 0.9, 0.88, 0.34, 112),
      employee("res-ready", "Employee B", "DevOps Engineer", "Enablement", ["kubernetes", "automation", "incident response", "terraform"], 40, 23, 0.96, 0.91, 0.89, 0.9, 0.74, 0.18, 0.22, 0.76, 94),
      employee("res-ml-ready", "Employee C", "ML Engineer", "AI", ["mlops", "python", "forecasting"], 40, 26, 0.92, 0.9, 0.88, 0.84, 0.9, 0.24, 0.28, 0.78, 105),
      employee("res-qa-ready", "Employee D", "QA Engineer", "Quality", ["testing", "automation", "api testing"], 38, 22, 0.95, 0.87, 0.9, 0.83, 0.72, 0.2, 0.25, 0.82, 78),
    ],
    tasks: [
      task("task-api", "API recovery lane", "Reliability", ["python", "api architecture", "incident response"], 15, 0.78, 5, 3, 1800000, ["task-runbook"], "Core", 0.75),
      task("task-k8s", "Kubernetes rollback automation", "Reliability", ["kubernetes", "automation", "terraform"], 12, 0.66, 5, 4, 1600000, [], "Enablement", 0.62),
      task("task-mlops", "Forecast drift monitor", "AI Stability", ["mlops", "python", "forecasting"], 10, 0.62, 4, 6, 900000, ["task-api"], "AI", 0.58),
      task("task-qa", "Regression stream suite", "Reliability", ["testing", "automation", "api testing"], 9, 0.5, 4, 5, 750000, ["task-api"], "Quality", 0.43),
    ],
    dependencies: [
      { source_task_id: "task-api", target_task_id: "task-runbook", blocker_type: "incident_dependency", risk_weight: 0.82 },
      { source_task_id: "task-mlops", target_task_id: "task-api", blocker_type: "platform_dependency", risk_weight: 0.55 },
      { source_task_id: "task-qa", target_task_id: "task-api", blocker_type: "test_dependency", risk_weight: 0.46 },
    ],
  };
}

function employee(
  employee_id: string,
  name: string,
  role: string,
  team: string,
  skills: string[],
  capacity_hours: number,
  current_hours: number,
  availability: number,
  productivity: number,
  historical_delivery_speed: number,
  collaboration_score: number,
  learning_agility: number,
  burnout_risk: number,
  stress_score: number,
  focus_score: number,
  hourly_cost: number,
) {
  return {
    employee_id,
    name,
    role,
    team,
    department: team === "AI" ? "AI" : "Engineering",
    skills,
    capacity_hours,
    current_hours,
    availability,
    productivity,
    historical_delivery_speed,
    collaboration_score,
    learning_agility,
    burnout_risk,
    stress_score,
    focus_score,
    hourly_cost,
  };
}

function task(
  task_id: string,
  title: string,
  project: string,
  required_skills: string[],
  effort_hours: number,
  complexity: number,
  priority: number,
  deadline_days: number,
  revenue_impact: number,
  dependency_task_ids: string[],
  preferred_team: string,
  cognitive_load: number,
) {
  return {
    task_id,
    title,
    project,
    description: `${title} for ${project}`,
    required_skills,
    effort_hours,
    complexity,
    priority,
    deadline_days,
    revenue_impact,
    dependency_task_ids,
    preferred_team,
    cognitive_load,
  };
}
