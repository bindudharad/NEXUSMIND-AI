"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { CalendarClock, HeartPulse, Loader2, Radio, RefreshCw, Send, ShieldCheck, TimerReset } from "lucide-react";

import type { WorkLifeBalanceResponse, WorkLifeSeverity } from "@/types/work-life-balance";

const severityColor: Record<WorkLifeSeverity, string> = {
  low: "#7CF0A6",
  medium: "#F6B44B",
  high: "#F05D5E",
  critical: "#FF3B6B",
};

export function WorkLifeBalancePanel() {
  const [analysis, setAnalysis] = useState<WorkLifeBalanceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [streamStatus, setStreamStatus] = useState("connecting");

  const loadDefault = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await fetchJson("/api/work-life-balance/optimize", { cache: "no-store" });
      if (!isWorkLifeBalance(payload)) throw new Error("Malformed work-life balance payload");
      setAnalysis(payload);
      setStreamStatus((status) => (status === "connecting" ? "polling" : status));
    } catch {
      setError("AI Work-Life Balance Optimizer could not refresh the live plan.");
    } finally {
      setLoading(false);
    }
  }, []);

  const simulateReleasePressure = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await fetchJson(
        "/api/work-life-balance/optimize",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(buildReleasePressurePayload()),
          cache: "no-store",
        },
        60000,
      );
      if (!isWorkLifeBalance(payload)) throw new Error("Malformed work-life balance payload");
      setAnalysis(payload);
      setStreamStatus((status) => (status === "connecting" ? "polling" : status));
    } catch {
      setError("AI Work-Life Balance Optimizer could not process the release-pressure scenario.");
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
        const response = await fetch("/api/work-life-balance/stream", { cache: "no-store", signal: controller.signal });
        if (!response.ok) throw new Error("Work-life balance stream failed");
        const reader = response.body?.getReader();
        if (!reader) throw new Error("Missing work-life balance stream");
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
            if (isWorkLifeBalance(payload)) {
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

  const teamChart = useMemo(
    () =>
      analysis?.teamBalance.map((team) => ({
        team: team.team.replace("Platform ", "Platform").replace("Enterprise ", "Ent."),
        wellness: Math.round(team.wellnessScore),
        burnout: Math.round(team.burnoutRisk),
        meetings: Math.round(team.meetingOverload),
        focus: Math.round(team.focusProtectionScore),
      })) ?? [],
    [analysis],
  );

  const forecastChart = useMemo(
    () =>
      analysis?.forecast.map((point) => ({
        day: `D${point.day}`,
        wellness: Math.round(point.wellnessScore),
        burnout: Math.round(point.burnoutRisk),
        productivity: Math.round(point.productivityScore),
        focus: Math.round(point.focusTimeScore),
      })) ?? [],
    [analysis],
  );

  return (
    <section id="work-life-balance" data-testid="work-life-balance-panel" className="border border-cyan/25 bg-panel/85 p-5 shadow-control backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="border border-cyan/30 bg-cyan/10 p-2 text-cyan">
            <HeartPulse className="size-5" />
          </div>
          <div>
            <p className="text-xs text-cyan">Sustainable Productivity Intelligence Engine</p>
            <h2 className="text-xl font-semibold text-white">Sustainable productivity scheduling, burnout prevention, meeting reduction, and focus-time protection</h2>
            <p className="mt-2 text-sm text-slate-500">
              Workforce resilience command surface, Burnout-risk heatmaps, Meeting-overload intelligence, Productivity-balance graphs, Focus-time visualizations, Workload distribution panels,
              AI recommendation widgets, and Executive wellness insights
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button data-testid="refresh-work-life-balance" onClick={() => void loadDefault()} className="inline-flex items-center gap-2 border border-line bg-panel2 px-3 py-2 text-sm text-slate-300">
            <RefreshCw className="size-4" />
            Refresh optimizer
          </button>
          <button data-testid="simulate-work-life-balance" onClick={() => void simulateReleasePressure()} className="inline-flex items-center gap-2 border border-cyan/40 bg-cyan/10 px-3 py-2 text-sm text-cyan">
            {loading ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
            Simulate release week
          </button>
        </div>
      </div>

      {error && !analysis ? <p className="mt-4 text-sm text-signal">{error}</p> : null}
      {loading && !analysis ? <p className="mt-5 text-sm text-slate-400">Optimizing calendar load, focus windows, workload balance, burnout forecasts, and energy-aware schedules...</p> : null}

      {analysis ? (
        <>
          <div className="mt-5 grid gap-3 md:grid-cols-4 xl:grid-cols-8">
            <Stat label="Workforce signals" value={String(analysis.summary.employeesAnalyzed)} />
            <Stat label="Teams" value={String(analysis.summary.teamCount)} />
            <Stat label="Wellness" value={`${Math.round(analysis.summary.wellnessScore)}%`} />
            <Stat label="Burnout" value={`${Math.round(analysis.summary.burnoutRisk)}%`} danger={analysis.summary.burnoutRisk >= 60} />
            <Stat label="Burnout cut" value={`${Math.round(analysis.summary.projectedBurnoutReduction)}%`} />
            <Stat label="Meetings cut" value={`${Math.round(analysis.summary.meetingReductionPercent)}%`} />
            <Stat label="Focus gain" value={`${analysis.summary.focusTimeGainHours.toFixed(1)}h`} />
            <Stat label="Stream" value={streamStatus} />
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[1.05fr_0.95fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
                <CalendarClock className="size-4" />
                Productivity-balance graphs
              </div>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={teamChart} margin={{ left: -24, right: 8, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="team" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Bar dataKey="wellness" fill="#7CF0A6" radius={[3, 3, 0, 0]} isAnimationActive={false} />
                    <Bar dataKey="burnout" fill="#F05D5E" radius={[3, 3, 0, 0]} isAnimationActive={false} />
                    <Bar dataKey="meetings" fill="#F6B44B" radius={[3, 3, 0, 0]} isAnimationActive={false} />
                    <Bar dataKey="focus" fill="#2EE9D3" radius={[3, 3, 0, 0]} isAnimationActive={false} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </article>

            <article className="border border-cyan/25 bg-cyan/10 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
                <ShieldCheck className="size-4" />
                Workforce resilience command surface
              </div>
              <div className="grid gap-3 md:grid-cols-2">
                {analysis.teamBalance.slice(0, 4).map((team) => (
                  <div key={team.team} className="border border-cyan/20 bg-panel/70 p-3">
                    <div className="flex items-center justify-between gap-2">
                      <h3 className="text-sm font-semibold text-white">{team.team}</h3>
                      <span className="text-sm text-cyan">{Math.round(team.wellnessScore)}%</span>
                    </div>
                    <Progress label="Burnout risk" value={team.burnoutRisk} color="bg-signal" />
                    <Progress label="Focus protection" value={team.focusProtectionScore} color="bg-cyan" />
                    <p className="mt-2 text-xs leading-5 text-slate-400">{team.recommendedPolicy}</p>
                  </div>
                ))}
              </div>
            </article>
          </div>

          <div className="mt-5 grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-mint">
                <TimerReset className="size-4" />
                Focus-time visualizations
              </div>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={forecastChart} margin={{ left: -24, right: 8, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="day" stroke="#64748b" tickLine={false} axisLine={false} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Line type="monotone" dataKey="wellness" stroke="#7CF0A6" strokeWidth={2} dot={false} isAnimationActive={false} />
                    <Line type="monotone" dataKey="burnout" stroke="#F05D5E" strokeWidth={2} dot={false} isAnimationActive={false} />
                    <Line type="monotone" dataKey="productivity" stroke="#2EE9D3" strokeWidth={2} dot={false} isAnimationActive={false} />
                    <Line type="monotone" dataKey="focus" stroke="#F6B44B" strokeWidth={2} dot={false} isAnimationActive={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
              <div className="mt-3 grid gap-2 md:grid-cols-3">
                {analysis.focusBlocks.slice(0, 3).map((block) => (
                  <div key={block.team} className="border border-line/60 bg-panel/60 p-3">
                    <div className="text-xs uppercase text-cyan">{block.team}</div>
                    <div className="mt-1 text-lg font-semibold text-white">{block.block}</div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{block.rationale}</p>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-amber">
                <Radio className="size-4" />
                Burnout-risk heatmaps
              </div>
              <div className="grid gap-2">
                {analysis.heatmap.slice(0, 8).map((cell) => (
                  <div key={`${cell.team}-${cell.metric}`} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <p className="text-sm font-medium text-white">{cell.team}</p>
                        <p className="text-xs uppercase text-slate-500">{cell.metric}</p>
                      </div>
                      <span className="text-sm font-semibold" style={{ color: severityColor[cell.severity] }}>
                        {Math.round(cell.score)}%
                      </span>
                    </div>
                    <div className="mt-2 h-1.5 bg-slate-800">
                      <div className="h-full" style={{ width: `${Math.min(100, cell.score)}%`, background: severityColor[cell.severity] }} />
                    </div>
                  </div>
                ))}
              </div>
            </article>
          </div>

          <div className="mt-5 grid gap-4 xl:grid-cols-[1fr_1fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="text-xs uppercase text-cyan">Meeting-overload analytics</div>
              <div className="mt-3 grid gap-2">
                {analysis.meetingPlan.slice(0, 4).map((plan) => (
                  <div key={plan.team} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-sm font-medium text-white">{plan.team}</span>
                      <span className="text-sm text-cyan">{Math.round(plan.reductionPercent)}% cut</span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">
                      {plan.currentMeetingHours.toFixed(1)}h to {plan.recommendedMeetingHours.toFixed(1)}h, recovering {plan.productivityRecoveryHours.toFixed(1)}h.
                    </p>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="text-xs uppercase text-mint">Workload distribution panels</div>
              <div className="mt-3 grid gap-2">
                {analysis.workloadRedistribution.length ? (
                  analysis.workloadRedistribution.slice(0, 4).map((plan) => (
                    <div key={`${plan.sourceEmployee}-${plan.targetEmployee}`} className="border border-line/60 bg-panel/60 p-3">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-sm font-medium text-white">{plan.sourceEmployee} to {plan.targetEmployee}</span>
                        <span className="text-sm text-mint">{plan.hoursToShift.toFixed(1)}h</span>
                      </div>
                      <p className="mt-2 text-xs leading-5 text-slate-400">{plan.rationale}</p>
                    </div>
                  ))
                ) : (
                  <div className="border border-line/60 bg-panel/60 p-3 text-sm text-slate-400">No unsafe workload transfers required in the current plan.</div>
                )}
              </div>
            </article>
          </div>

          <div className="mt-5 grid gap-4 xl:grid-cols-[1fr_0.95fr]">
            <article className="border border-cyan/25 bg-cyan/10 p-4">
              <div className="text-xs uppercase text-cyan">AI recommendation widgets</div>
              <div className="mt-3 grid gap-2">
                {analysis.recommendations.slice(0, 5).map((recommendation) => (
                  <div key={`${recommendation.category}-${recommendation.title}`} className="border border-cyan/20 bg-panel/70 p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <h3 className="text-sm font-semibold text-white">{recommendation.title}</h3>
                      <span className="text-xs uppercase" style={{ color: severityColor[recommendation.priority] }}>{recommendation.priority}</span>
                    </div>
                    <p className="mt-2 text-sm leading-6 text-slate-300">{recommendation.action}</p>
                    <p className="mt-1 text-xs text-cyan">{recommendation.expectedImpact}</p>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="text-xs uppercase text-amber">Executive wellness insights</div>
              <div className="mt-3 grid gap-2">
                {analysis.executiveInsights.map((insight) => (
                  <p key={insight} className="border border-line/60 bg-panel/60 p-3 text-sm leading-6 text-slate-300">{insight}</p>
                ))}
              </div>
            </article>
          </div>
        </>
      ) : null}
    </section>
  );
}

async function fetchJson(input: string, init: RequestInit = {}, timeoutMs = 45000): Promise<unknown> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(input, { ...init, signal: controller.signal });
    const payload = await response.json();
    if (!response.ok) throw new Error("Work-life balance request failed");
    return payload;
  } finally {
    window.clearTimeout(timeout);
  }
}

function isWorkLifeBalance(value: unknown): value is WorkLifeBalanceResponse {
  const payload = value as WorkLifeBalanceResponse;
  return Boolean(payload?.summary && Array.isArray(payload.employeePlans) && Array.isArray(payload.recommendations) && Array.isArray(payload.forecast));
}

function buildReleasePressurePayload() {
  return {
    cycle_name: "Frontend Release Week Sustainable Productivity Simulation",
    target_department: "Engineering",
    horizon_days: 60,
    employees: [
      {
        employee_id: "release-owner",
        name: "Release Owner",
        department: "Engineering",
        team: "Platform Reliability",
        role: "Backend Lead",
        meeting_hours_per_week: 25,
        recurring_meeting_hours: 16,
        async_candidate_hours: 9,
        overtime_hours_30d: 82,
        after_hours_messages_30d: 210,
        focus_hours_per_day: 1.3,
        context_switches_per_hour: 44,
        task_load_hours: 68,
        capacity_hours: 40,
        deadline_pressure: 0.92,
        collaboration_dependency: 0.86,
        burnout_risk: 0.88,
        stress_score: 0.86,
        wellness_score: 0.3,
        productivity_score: 0.76,
        energy_morning: 0.84,
        energy_afternoon: 0.48,
        flexibility_fit: 0.74,
        manager_support: 0.62,
      },
      {
        employee_id: "stable-peer",
        name: "Stable Peer",
        department: "Engineering",
        team: "Platform Reliability",
        role: "Automation Engineer",
        meeting_hours_per_week: 7,
        recurring_meeting_hours: 3,
        async_candidate_hours: 1,
        overtime_hours_30d: 8,
        after_hours_messages_30d: 12,
        focus_hours_per_day: 5.6,
        context_switches_per_hour: 9,
        task_load_hours: 27,
        capacity_hours: 40,
        deadline_pressure: 0.28,
        collaboration_dependency: 0.38,
        burnout_risk: 0.16,
        stress_score: 0.22,
        wellness_score: 0.86,
        productivity_score: 0.9,
        energy_morning: 0.72,
        energy_afternoon: 0.78,
        flexibility_fit: 0.84,
        manager_support: 0.86,
      },
    ],
  };
}

function Stat({ label, value, danger = false }: { label: string; value: string; danger?: boolean }) {
  return (
    <div className="border border-line/70 bg-panel2/75 p-3">
      <p className="text-xs uppercase text-slate-500">{label}</p>
      <strong className={`mt-2 block text-lg font-semibold ${danger ? "text-signal" : "text-white"}`}>{value}</strong>
    </div>
  );
}

function Progress({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="mt-3">
      <div className="mb-1 flex items-center justify-between text-xs">
        <span className="text-slate-400">{label}</span>
        <span className="text-slate-300">{Math.round(value)}</span>
      </div>
      <div className="h-1.5 bg-slate-800">
        <div className={`h-full ${color}`} style={{ width: `${Math.max(4, Math.min(100, value))}%` }} />
      </div>
    </div>
  );
}
