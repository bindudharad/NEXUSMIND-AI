"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Activity, BrainCircuit, Clock3, RefreshCw, Zap } from "lucide-react";

import type { EmployeeDashboardResponse, EmployeeScore, ScoreStatus } from "@/types/employee-dashboard";

const statusTone: Record<ScoreStatus, string> = {
  optimal: "border-mint/35 bg-mint/10 text-mint",
  stable: "border-cyan/35 bg-cyan/10 text-cyan",
  watch: "border-amber/40 bg-amber/10 text-amber",
  high_risk: "border-signal/40 bg-signal/10 text-signal",
};

export function EmployeeDashboardPanel() {
  const [dashboard, setDashboard] = useState<EmployeeDashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshCount, setRefreshCount] = useState(0);
  const [error, setError] = useState("");
  const activeMode = useRef<"default" | "overload">("default");

  async function loadDashboard(mode: "default" | "overload" = "default") {
    activeMode.current = mode;
    setLoading(true);
    setError("");
    try {
      const response =
        mode === "default"
          ? await fetch("/api/employees/dashboard", { cache: "no-store" })
          : await fetch("/api/employees/dashboard", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                employee_id: "emp-overloaded",
                employee_name: "Overloaded Employee",
                department: "Engineering",
                role: "Incident Lead",
                current: {
                  timestamp: "2026-05-28T10:05:00Z",
                  overtime_hours: 21,
                  workload_intensity: 93,
                  meeting_hours: 15,
                  sentiment_score: -0.72,
                  task_completion_ratio: 0.48,
                  attendance_rate: 0.82,
                  focus_hours: 1.8,
                  collaboration_score: 0.52,
                  activity_variance: 0.86,
                  negative_message_ratio: 0.67,
                  toxic_message_count: 4,
                  absence_days: 6,
                },
              }),
            });
      if (!response.ok) throw new Error("Workforce intelligence request failed");
      setDashboard((await response.json()) as EmployeeDashboardResponse);
      setRefreshCount((current) => current + 1);
    } catch {
      setError("Workforce intelligence telemetry could not refresh.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const firstRefresh = window.setTimeout(() => {
      void loadDashboard();
    }, 5000);
    const interval = window.setInterval(() => {
      void loadDashboard(activeMode.current);
    }, 15000);
    return () => {
      window.clearTimeout(firstRefresh);
      window.clearInterval(interval);
    };
  }, []);

  const chartData = useMemo(() => {
    if (!dashboard) return [];
    return dashboard.history.map((point) => ({
      timestamp: new Date(point.timestamp).toLocaleDateString(undefined, { month: "short", day: "numeric" }),
      stress: point.stressScore,
      productivity: point.productivityScore,
      burnout: point.burnoutProbability,
      workload: point.workloadIntensity,
    }));
  }, [dashboard]);

  return (
    <section className="border border-line/80 bg-panel/85 p-5 shadow-control backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <BrainCircuit className="size-5 text-cyan" />
          <div>
            <p className="text-xs uppercase text-cyan">Workforce Intelligence Network</p>
            <h2 className="text-xl font-semibold text-white">Individual digital twin stress, productivity, and burnout intelligence</h2>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => void loadDashboard("default")}
            className="inline-flex items-center gap-2 border border-line bg-panel2 px-3 py-2 text-sm text-slate-300"
          >
            <RefreshCw className="size-4" />
            Refresh live
          </button>
          <button
            onClick={() => void loadDashboard("overload")}
            className="inline-flex items-center gap-2 border border-amber/40 bg-amber/10 px-3 py-2 text-sm text-amber"
          >
            <Zap className="size-4" />
            Simulate overload
          </button>
        </div>
      </div>

      {error ? <p className="mt-4 text-sm text-signal">{error}</p> : null}
      {loading ? <p className="mt-6 text-sm text-slate-400">Refreshing workforce AI telemetry...</p> : null}

      {dashboard ? (
        <>
          <div className="mt-5 flex flex-wrap items-center justify-between gap-3 border border-line/70 bg-panel2/65 p-4">
            <div>
              <p className="text-sm text-slate-400">{dashboard.department} / {dashboard.role}</p>
              <h3 className="mt-1 text-2xl font-semibold text-white">{dashboard.employeeName}</h3>
            </div>
            <div className="flex items-center gap-2 text-sm text-slate-400">
              <Clock3 className="size-4 text-cyan" />
              Live refresh #{refreshCount} / {new Date(dashboard.generatedAt).toLocaleTimeString()}
            </div>
          </div>

          <div className="mt-4 grid gap-3 md:grid-cols-3">
            <ScoreCard score={dashboard.stress} accent="text-amber" />
            <ScoreCard score={dashboard.productivity} accent="text-mint" />
            <ScoreCard score={dashboard.burnoutProbability} accent="text-signal" suffix="%" />
          </div>

          <div className="mt-5 grid gap-4 xl:grid-cols-[1.15fr_0.85fr]">
            <div className="h-80 border border-line/70 bg-panel2/65 p-4">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ left: -18, right: 8, top: 10, bottom: 0 }}>
                  <defs>
                    <linearGradient id="employeeStressGradient" x1="0" x2="0" y1="0" y2="1">
                      <stop offset="5%" stopColor="#F6B44B" stopOpacity={0.28} />
                      <stop offset="95%" stopColor="#F6B44B" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                  <XAxis dataKey="timestamp" stroke="#64748b" tickLine={false} axisLine={false} />
                  <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                  <Legend />
                  <Area type="monotone" dataKey="stress" stroke="#F6B44B" fill="url(#employeeStressGradient)" strokeWidth={2} />
                  <Line type="monotone" dataKey="productivity" stroke="#7CF0A6" strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="burnout" stroke="#F05D5E" strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="workload" stroke="#2EE9D3" strokeDasharray="4 4" dot={false} />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            <div className="grid gap-3">
              <div className="border border-cyan/25 bg-cyan/10 p-4">
                <div className="flex items-center gap-2 text-xs uppercase text-cyan">
                  <Activity className="size-4" />
                  AI Recommendations
                </div>
                <div className="mt-3 space-y-2">
                  {dashboard.recommendations.map((recommendation) => (
                    <p key={recommendation} className="border border-line/60 bg-panel/65 p-3 text-sm leading-6 text-slate-300">
                      {recommendation}
                    </p>
                  ))}
                </div>
              </div>
              <div className="border border-line/70 bg-panel2/65 p-4">
                <p className="text-xs uppercase text-slate-500">Burnout ensemble</p>
                <div className="mt-3 grid grid-cols-2 gap-2 text-sm">
                  {Object.entries(dashboard.modelProbabilities).map(([model, value]) => (
                    <div key={model} className="border border-line/60 bg-panel/60 p-2">
                      <span className="block text-xs uppercase text-slate-500">{model.replaceAll("_", " ")}</span>
                      <strong className="text-white">{Math.round(value * 100)}%</strong>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </>
      ) : null}
    </section>
  );
}

function ScoreCard({ score, accent, suffix = "" }: { score: EmployeeScore; accent: string; suffix?: string }) {
  return (
    <article className="border border-line/70 bg-panel2/65 p-4">
      <div className="flex items-start justify-between gap-3">
        <p className="text-xs uppercase text-slate-500">{score.label}</p>
        <span className={`border px-2 py-1 text-[10px] uppercase ${statusTone[score.status]}`}>
          {score.status.replace("_", " ")}
        </span>
      </div>
      <strong className={`mt-4 block text-4xl font-semibold ${accent}`}>{Math.round(score.value)}{suffix}</strong>
      <p className="mt-2 text-sm text-slate-400">
        {score.trendDelta >= 0 ? "+" : ""}
        {score.trendDelta.toFixed(1)} vs recent trend
      </p>
      <div className="mt-3 flex flex-wrap gap-2">
        {score.drivers.slice(0, 3).map((driver) => (
          <span key={driver} className="border border-line/60 bg-panel/60 px-2 py-1 text-xs text-slate-300">
            {driver}
          </span>
        ))}
      </div>
    </article>
  );
}
