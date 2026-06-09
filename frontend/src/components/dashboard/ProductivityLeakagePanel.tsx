"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Activity, BrainCircuit, Clock3, Loader2, Radio, RefreshCw, Send, Zap } from "lucide-react";

import type { ProductivityAnalysisResponse, ProductivitySeverity } from "@/types/productivity";

const severityColor: Record<ProductivitySeverity, string> = {
  low: "#7CF0A6",
  medium: "#F6B44B",
  high: "#F05D5E",
  critical: "#FF3B6B",
};

export function ProductivityLeakagePanel() {
  const [analysis, setAnalysis] = useState<ProductivityAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [streamStatus, setStreamStatus] = useState("connecting");

  const loadSample = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await fetchJson("/api/productivity/analyze", { cache: "no-store" });
      if (!isProductivityAnalysis(payload)) throw new Error("Malformed productivity payload");
      setAnalysis(payload);
      setStreamStatus((status) => (status === "connecting" ? "polling" : status));
    } catch {
      setError("Productivity Leakage Detector AI could not refresh the live signal.");
    } finally {
      setLoading(false);
    }
  }, []);

  const simulateLeakage = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await fetchJson("/api/productivity/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(buildLeakagePayload()),
        cache: "no-store",
      }, 60000);
      if (!isProductivityAnalysis(payload)) throw new Error("Malformed productivity payload");
      setAnalysis(payload);
      setStreamStatus((status) => (status === "connecting" ? "polling" : status));
    } catch {
      setError("Productivity Leakage Detector AI could not process the fragmented workflow scenario.");
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
        const response = await fetch("/api/productivity/stream", { cache: "no-store", signal: controller.signal });
        if (!response.ok) throw new Error("Productivity stream failed");
        const reader = response.body?.getReader();
        if (!reader) throw new Error("Missing productivity stream");
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
            if (isProductivityAnalysis(payload)) {
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
      void loadSample();
    }, 0);
    const streamRefresh = window.setTimeout(() => {
      void connectStream();
    }, 3200);
    return () => {
      controller.abort();
      window.clearTimeout(firstRefresh);
      window.clearTimeout(streamRefresh);
    };
  }, [loadSample]);

  const hourlyData = useMemo(
    () =>
      analysis?.hourlyTrend.map((point) => ({
        hour: point.hourLabel,
        productivity: Math.round(point.productivityScore),
        focus: Math.round(point.focusScore),
        leakage: Math.round(point.leakageMinutes),
        energy: Math.round(point.energyScore),
        deepWork: Math.round(point.deepWorkMinutes),
      })) ?? [],
    [analysis],
  );

  const heatmapData = useMemo(
    () =>
      analysis?.leakageHeatmap.map((cell) => ({
        window: cell.window,
        leakage: Math.round(cell.leakageScore),
        focus: Math.round(cell.focusScore),
        lost: Math.round(cell.lostMinutes),
        cause: cell.dominantCause,
      })) ?? [],
    [analysis],
  );

  const energyData = useMemo(
    () =>
      analysis?.energyForecast.map((point) => ({
        window: point.window,
        energy: Math.round(point.energyScore),
        productivity: Math.round(point.productivityScore),
        fatigue: Math.round(point.fatigueRisk),
      })) ?? [],
    [analysis],
  );

  return (
    <section className="border border-line/80 bg-panel/85 p-5 shadow-control backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <BrainCircuit className="size-5 text-cyan" />
          <div>
            <p className="text-xs uppercase text-cyan">Productivity Leakage Detector AI</p>
            <h2 className="text-xl font-semibold text-white">Tool switching, distractions, low-focus hours, deep-work disruption, energy forecasting, and workflow recovery</h2>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button onClick={() => void loadSample()} className="inline-flex items-center gap-2 border border-line bg-panel2 px-3 py-2 text-sm text-slate-300">
            <RefreshCw className="size-4" />
            Refresh live
          </button>
          <button onClick={() => void simulateLeakage()} className="inline-flex items-center gap-2 border border-cyan/40 bg-cyan/10 px-3 py-2 text-sm text-cyan">
            {loading ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
            Simulate leakage
          </button>
        </div>
      </div>

      {error && !analysis ? <p className="mt-4 text-sm text-signal">{error}</p> : null}
      {loading && !analysis ? <p className="mt-5 text-sm text-slate-400">Scoring active work hours, app switching, idle time, notifications, deep-work blocks, and energy trend...</p> : null}

      {analysis ? (
        <>
          <div className="mt-5 grid gap-3 md:grid-cols-4 xl:grid-cols-9">
            <Stat label="Productivity" value={`${Math.round(analysis.summary.productivityScore)}%`} />
            <Stat label="Focus" value={`${Math.round(analysis.summary.focusScore)}%`} />
            <Stat label="Efficiency" value={`${Math.round(analysis.summary.efficiencyScore)}%`} />
            <Stat label="Leakage" value={`${Math.round(analysis.summary.leakagePercent)}%`} />
            <Stat label="Lost hours" value={`${analysis.summary.lostProductiveHours.toFixed(1)}h`} />
            <Stat label="Loss cost" value={formatMoney(analysis.summary.estimatedLossCost)} />
            <Stat label="Switch load" value={`${Math.round(analysis.summary.toolSwitchingOverload)}%`} />
            <Stat label="Low focus" value={String(analysis.summary.lowFocusWindowCount)} />
            <Stat label="Stream" value={streamStatus} />
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
                <Activity className="size-4" />
                Productive-hours and energy trend
              </div>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={hourlyData} margin={{ left: -24, right: 8, top: 8, bottom: 0 }}>
                    <defs>
                      <linearGradient id="productivityLeakageFocus" x1="0" x2="0" y1="0" y2="1">
                        <stop offset="5%" stopColor="#2EE9D3" stopOpacity={0.28} />
                        <stop offset="95%" stopColor="#2EE9D3" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="hour" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Area type="monotone" dataKey="focus" stroke="#2EE9D3" fill="url(#productivityLeakageFocus)" strokeWidth={2} />
                    <Line type="monotone" dataKey="productivity" stroke="#7CF0A6" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="energy" stroke="#F6B44B" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="leakage" stroke="#F05D5E" strokeWidth={2} dot={false} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-amber">
                <Zap className="size-4" />
                Tool-switching overload
              </div>
              <p className="text-sm leading-6 text-slate-300">{analysis.toolSwitching.insight}</p>
              <div className="mt-4 grid gap-2 md:grid-cols-2">
                <Progress label="Context penalty" value={analysis.toolSwitching.contextSwitchPenalty} color="bg-signal" />
                <Progress label="Switch fatigue" value={analysis.toolSwitching.fatigueScore} color="bg-amber" />
                <Progress label="Switch loss" value={analysis.toolSwitching.productivityLossPercent} color="bg-cyan" />
                <Progress label="Distraction" value={analysis.distractionAnalytics.distractionScore} color="bg-slate-400" />
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                {analysis.toolSwitching.overloadedTools.map((tool) => (
                  <span key={tool} className="border border-line/60 bg-panel/70 px-2 py-1 text-xs text-slate-300">{tool}</span>
                ))}
              </div>
            </article>
          </div>

          <div className="mt-5 grid gap-4 xl:grid-cols-[1fr_1fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-signal">
                <Radio className="size-4" />
                Leakage heatmap
              </div>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={heatmapData} margin={{ left: -24, right: 8, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="window" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Bar dataKey="leakage" radius={[3, 3, 0, 0]}>
                      {heatmapData.map((item) => (
                        <Cell key={item.window} fill={item.leakage >= 60 ? "#FF3B6B" : item.leakage >= 42 ? "#F6B44B" : "#2EE9D3"} />
                      ))}
                    </Bar>
                    <Bar dataKey="focus" fill="#7CF0A6" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="mt-3 grid gap-2 md:grid-cols-2">
                {analysis.leakageHeatmap.slice().sort((a, b) => b.leakageScore - a.leakageScore).slice(0, 4).map((cell) => (
                  <div key={cell.window} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-sm font-medium text-white">{cell.window}</span>
                      <span className="text-xs text-signal">{Math.round(cell.leakageScore)}% leakage</span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{cell.dominantCause} / {Math.round(cell.lostMinutes)} lost minutes</p>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-mint">
                <Clock3 className="size-4" />
                Deep-work and energy forecast
              </div>
              <p className="text-sm leading-6 text-slate-300">{analysis.deepWorkAnalytics.insight}</p>
              <div className="mt-4 h-48">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={energyData} margin={{ left: -24, right: 8, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="window" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 10 }} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Bar dataKey="energy" fill="#7CF0A6" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="fatigue" fill="#F05D5E" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="mt-3 grid gap-2 md:grid-cols-2">
                <Stat label="Deep work" value={`${analysis.deepWorkAnalytics.totalDeepWorkHours.toFixed(1)}h`} />
                <Stat label="Avg block" value={`${Math.round(analysis.deepWorkAnalytics.averageDeepWorkBlockMinutes)}m`} />
                <Stat label="Interruptions" value={String(Math.round(analysis.deepWorkAnalytics.interruptionFrequency))} />
                <Stat label="Stability" value={`${Math.round(analysis.deepWorkAnalytics.stabilityScore)}%`} />
              </div>
            </article>
          </div>

          <div className="mt-5 grid gap-4 xl:grid-cols-[1fr_0.95fr]">
            <article className="border border-cyan/25 bg-cyan/10 p-4">
              <div className="text-xs uppercase text-cyan">AI productivity recommendations</div>
              <div className="mt-3 grid gap-2">
                {analysis.recommendations.slice(0, 5).map((recommendation) => (
                  <div key={`${recommendation.category}-${recommendation.action}`} className="border border-cyan/20 bg-panel/70 p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="text-sm font-medium text-white">{recommendation.action}</span>
                      <span className="text-xs uppercase" style={{ color: severityColor[recommendation.priority] }}>
                        {recommendation.priority} / {Math.round(recommendation.confidence * 100)}%
                      </span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{recommendation.expectedImpact}</p>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="text-xs uppercase text-slate-500">Executive productivity insights</div>
              <div className="mt-3 space-y-2">
                {analysis.executiveInsights.map((insight) => (
                  <p key={insight} className="border border-line/60 bg-panel/60 p-3 text-sm leading-6 text-slate-300">
                    {insight}
                  </p>
                ))}
              </div>
              <div className="mt-3 border border-line/60 bg-panel/60 p-3 text-xs leading-5 text-slate-500">
                Model fusion: {analysis.mlModel} / {analysis.nlpModel} / {analysis.behavioralModel}
              </div>
            </article>
          </div>
        </>
      ) : null}
    </section>
  );
}

function Progress({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="border border-line/60 bg-panel/60 p-3">
      <div className="flex items-center justify-between gap-2 text-xs uppercase text-slate-500">
        <span>{label}</span>
        <span>{Math.round(value)}%</span>
      </div>
      <div className="mt-2 h-2 bg-void/80">
        <div className={`h-full ${color}`} style={{ width: `${Math.max(4, Math.min(100, value))}%` }} />
      </div>
    </div>
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
    if (!response.ok) throw new Error("Productivity request failed");
    return await response.json();
  } finally {
    window.clearTimeout(timeout);
  }
}

function isProductivityAnalysis(value: unknown): value is ProductivityAnalysisResponse {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Partial<ProductivityAnalysisResponse>;
  return Boolean(candidate.model && candidate.summary?.productivityScore !== undefined && Array.isArray(candidate.hourlyTrend));
}

function buildLeakagePayload() {
  return {
    employee_id: "emp-productivity-fragmented",
    employee_name: "Fragmented Workflow Owner",
    department: "Engineering",
    role: "Incident Lead",
    hourly_cost: 96,
    work_pattern: {
      timestamp: new Date().toISOString(),
      overtime_hours: 18,
      workload_intensity: 91,
      meeting_hours: 14,
      sentiment_score: -0.6,
      task_completion_ratio: 0.52,
      attendance_rate: 0.86,
      focus_hours: 1.7,
      collaboration_score: 0.55,
      activity_variance: 0.88,
      negative_message_ratio: 0.64,
      toxic_message_count: 2,
      absence_days: 4,
    },
    messages: [
      { channel: "slack", text: "Slack, Email, Jira, and browser tabs keep interrupting the release work." },
      { channel: "chat", text: "The deepest work window is gone after lunch because every notification triggers another context switch." },
    ],
    windows: Array.from({ length: 8 }, (_, index) => {
      const hour = [9, 10, 11, 12, 14, 15, 16, 17][index];
      const peakLeak = hour >= 14 && hour <= 15;
      return {
        hour,
        active_minutes: peakLeak ? 46 : 51,
        productive_minutes: peakLeak ? 18 : 31,
        idle_minutes: peakLeak ? 12 : 7,
        app_switches: peakLeak ? 68 : 38,
        tab_switches: peakLeak ? 96 : 54,
        notifications: peakLeak ? 58 : 28,
        meeting_minutes: peakLeak ? 20 : 12,
        deep_work_minutes: peakLeak ? 4 : 18,
        keyboard_events: peakLeak ? 980 : 1450,
        mouse_events: peakLeak ? 1380 : 900,
        distraction_minutes: peakLeak ? 18 : 8,
        task_completion_ratio: peakLeak ? 0.44 : 0.66,
        focus_quality: peakLeak ? 0.24 : 0.56,
      };
    }),
    app_usage: [
      { app_name: "Slack", category: "communication", minutes: 98, switches: 86, notification_count: 83, productive: false },
      { app_name: "Email", category: "communication", minutes: 61, switches: 54, notification_count: 59, productive: false },
      { app_name: "Jira", category: "planning", minutes: 74, switches: 67, notification_count: 24, productive: true },
      { app_name: "Browser tabs", category: "research", minutes: 88, switches: 92, notification_count: 12, productive: true },
      { app_name: "Social tabs", category: "distraction", minutes: 34, switches: 27, notification_count: 14, productive: false },
      { app_name: "VS Code", category: "development", minutes: 142, switches: 41, notification_count: 0, productive: true },
    ],
    realtime: true,
  };
}
