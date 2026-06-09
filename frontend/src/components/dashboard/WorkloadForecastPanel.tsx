"use client";

import { useEffect, useMemo, useState } from "react";
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
import { Activity, ChartSpline, RefreshCw } from "lucide-react";

import type { ForecastResponse } from "@/types/forecasting";

export function WorkloadForecastPanel() {
  const [forecast, setForecast] = useState<ForecastResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadForecast(mode: "default" | "overload" = "default") {
    setLoading(true);
    setError("");
    try {
      const response =
        mode === "default"
          ? await fetch("/api/forecasting/workload", { cache: "no-store" })
          : await fetch("/api/forecasting/workload", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                department: "Engineering",
                horizon_days: 14,
                history: Array.from({ length: 24 }, (_, index) => ({
                  date: `2026-05-${String(index + 1).padStart(2, "0")}`,
                  workload: Math.min(100, 72 + index * 0.85),
                  productivity: Math.max(45, 84 - index * 0.75),
                  overtime_hours: Math.min(18, 7 + index * 0.28),
                  attendance_rate: Math.max(0.8, 0.96 - index * 0.004),
                  task_completion_rate: Math.max(0.5, 0.9 - index * 0.011),
                  burnout_risk: Math.min(0.95, 0.32 + index * 0.021),
                  delay_probability: Math.min(0.9, 0.2 + index * 0.019),
                })),
              }),
            });
      if (!response.ok) throw new Error("Forecast request failed");
      setForecast((await response.json()) as ForecastResponse);
    } catch {
      setError("Forecasting model could not generate a prediction.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadForecast();
    }, 7400);
    return () => window.clearTimeout(timer);
  }, []);

  const chartData = useMemo(() => {
    if (!forecast) return [];
    const history = forecast.history.slice(-18).map((point) => ({
      date: point.date.slice(5),
      workload: point.workload,
      productivity: point.productivity,
      burnout: Math.round(point.burnoutRisk * 100),
      lowerBound: null,
      upperBound: null,
      phase: "history",
    }));
    const future = forecast.forecast.map((point) => ({
      date: point.date.slice(5),
      workload: point.workload,
      productivity: point.productivity,
      burnout: Math.round(point.burnoutRisk * 100),
      lowerBound: point.lowerBound,
      upperBound: point.upperBound,
      phase: "forecast",
    }));
    return [...history, ...future];
  }, [forecast]);

  return (
    <section className="border border-line/80 bg-panel/85 p-5 shadow-control backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <ChartSpline className="size-5 text-cyan" />
          <div>
            <p className="text-xs uppercase text-cyan">Time Series Forecasting AI</p>
            <h2 className="text-xl font-semibold text-white">Workload, burnout, and productivity trajectory</h2>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => void loadForecast("default")}
            className="inline-flex items-center gap-2 border border-line bg-panel2 px-3 py-2 text-sm text-slate-300"
          >
            <RefreshCw className="size-4" />
            Baseline
          </button>
          <button
            onClick={() => void loadForecast("overload")}
            className="inline-flex items-center gap-2 border border-amber/40 bg-amber/10 px-3 py-2 text-sm text-amber"
          >
            <Activity className="size-4" />
            Simulate overload
          </button>
        </div>
      </div>

      {error ? <p className="mt-4 text-sm text-signal">{error}</p> : null}
      {loading ? <p className="mt-6 text-sm text-slate-400">Generating LSTM forecast...</p> : null}

      {forecast ? (
        <>
          <div className="mt-5 grid gap-3 md:grid-cols-4">
            <Stat label="Model" value={forecast.model} />
            <Stat label="Confidence" value={`${Math.round(forecast.confidence * 100)}%`} />
            <Stat label="Collapse Risk" value={`${Math.round(forecast.teamCollapseProbability * 100)}%`} />
            <Stat label="Horizon" value={`${forecast.horizonDays} days`} />
          </div>

          <div className="mt-5 h-80">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ left: -18, right: 8, top: 10, bottom: 0 }}>
                <defs>
                  <linearGradient id="workloadForecast" x1="0" x2="0" y1="0" y2="1">
                    <stop offset="5%" stopColor="#2EE9D3" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#2EE9D3" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                <XAxis dataKey="date" stroke="#64748b" tickLine={false} axisLine={false} />
                <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                <Legend />
                <Area type="monotone" dataKey="workload" stroke="#2EE9D3" fill="url(#workloadForecast)" strokeWidth={2} />
                <Line type="monotone" dataKey="productivity" stroke="#7CF0A6" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="burnout" stroke="#F05D5E" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="upperBound" stroke="#F6B44B" strokeDasharray="4 4" dot={false} />
                <Line type="monotone" dataKey="lowerBound" stroke="#F6B44B" strokeDasharray="4 4" dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="mt-5 grid gap-3 lg:grid-cols-[0.9fr_1.1fr]">
            <div className="border border-line/70 bg-panel2/65 p-4">
              <p className="text-xs uppercase text-slate-500">Trend signals</p>
              <div className="mt-3 space-y-2">
                {forecast.trendSignals.map((signal) => (
                  <div key={signal.metric} className="flex items-center justify-between gap-3 text-sm">
                    <span className="capitalize text-slate-300">{signal.metric}</span>
                    <span className={signal.severity === "stable" ? "text-mint" : "text-amber"}>
                      {signal.direction} {signal.change.toFixed(2)} / {signal.severity}
                    </span>
                  </div>
                ))}
              </div>
            </div>
            <div className="border border-cyan/25 bg-cyan/10 p-4 text-sm leading-6 text-slate-200">
              {forecast.recommendation}
            </div>
          </div>
        </>
      ) : null}
    </section>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-line/70 bg-panel2/65 p-3">
      <span className="block text-xs uppercase text-slate-500">{label}</span>
      <strong className="mt-1 block text-lg text-white">{value}</strong>
    </div>
  );
}
