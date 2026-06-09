"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Banknote, BriefcaseBusiness, CircleDollarSign, Loader2, ReceiptText, RefreshCw, Send, TrendingUp } from "lucide-react";

import type { RoiResponse, RoiSeverity } from "@/types/roi";

type SnakeRecord = Record<string, unknown>;

const severityColor: Record<RoiSeverity, string> = {
  low: "#7CF0A6",
  medium: "#2EE9D3",
  high: "#F6B44B",
  critical: "#FF3B6B",
};

export function RoiIntelligencePanel() {
  const [analysis, setAnalysis] = useState<RoiResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [streamStatus, setStreamStatus] = useState("connecting");

  const loadRoi = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/roi/analyze", { cache: "no-store" });
      if (!response.ok) throw new Error("ROI intelligence failed");
      setAnalysis((await response.json()) as RoiResponse);
    } catch {
      setError("ROI Intelligence could not load executive economics.");
    } finally {
      setLoading(false);
    }
  }, []);

  const runExecutiveCase = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/roi/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(executiveScenarioPayload()),
        cache: "no-store",
      });
      if (!response.ok) throw new Error("ROI intelligence failed");
      setAnalysis((await response.json()) as RoiResponse);
    } catch {
      setError("ROI Intelligence could not process the executive scenario.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    async function connectStream() {
      try {
        const response = await fetch("/api/roi/stream", { cache: "no-store", signal: controller.signal });
        const reader = response.body?.getReader();
        if (!reader) throw new Error("Missing ROI stream");
        const decoder = new TextDecoder();
        let buffer = "";
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
              setAnalysis(toCamel<RoiResponse>(JSON.parse(dataLine.slice(6))));
              setLoading(false);
            }
          }
        }
        setStreamStatus("polling");
      } catch {
        if (!controller.signal.aborted) setStreamStatus("polling");
      }
    }

    const firstRefresh = window.setTimeout(() => {
      void loadRoi();
    }, 11800);
    const streamRefresh = window.setTimeout(() => {
      void connectStream();
    }, 13000);
    return () => {
      controller.abort();
      window.clearTimeout(firstRefresh);
      window.clearTimeout(streamRefresh);
    };
  }, [loadRoi]);

  const exposureChart = useMemo(
    () =>
      analysis
        ? [
            { name: "Replacement", value: Math.round(analysis.summary.replacementCostExposure), severity: "high" as RoiSeverity },
            { name: "Productivity", value: Math.round(analysis.summary.productivityLossExposure), severity: "medium" as RoiSeverity },
            { name: "Delay", value: Math.round(analysis.summary.projectDelayExposure), severity: "critical" as RoiSeverity },
            { name: "Net savings", value: Math.round(analysis.summary.netSavings), severity: "low" as RoiSeverity },
          ]
        : [],
    [analysis],
  );

  const forecastChart = useMemo(
    () =>
      analysis?.forecast.map((point) => ({
        month: `M${point.month}`,
        baseline: Math.round(point.baselineCost / 1000),
        optimized: Math.round(point.optimizedCost / 1000),
        savings: Math.round(point.cumulativeSavings / 1000),
        roi: Math.round(point.roiPercent),
      })) ?? [],
    [analysis],
  );

  return (
    <section className="border border-line/80 bg-panel/85 p-5 shadow-control backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <CircleDollarSign className="size-5 text-mint" />
          <div>
            <p className="text-xs uppercase text-mint">Enterprise ROI Intelligence</p>
            <h2 className="text-xl font-semibold text-white">Business impact, savings, payback, and workforce economics</h2>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button onClick={() => void loadRoi()} className="inline-flex items-center gap-2 border border-line bg-panel2 px-3 py-2 text-sm text-slate-300">
            <RefreshCw className="size-4" />
            Load ROI
          </button>
          <button onClick={() => void runExecutiveCase()} className="inline-flex items-center gap-2 border border-mint/40 bg-mint/10 px-3 py-2 text-sm text-mint">
            {loading ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
            Executive case
          </button>
        </div>
      </div>

      {error ? <p className="mt-4 text-sm text-signal">{error}</p> : null}
      {loading ? <p className="mt-5 text-sm text-slate-400">Calculating replacement cost, productivity drag, delay economics, and ROI capture...</p> : null}

      {analysis ? (
        <>
          <div className="mt-5 grid gap-3 md:grid-cols-6">
            <Stat label="Net savings" value={money(analysis.summary.netSavings)} tone="text-mint" />
            <Stat label="ROI" value={`${Math.round(analysis.summary.roiPercent)}%`} tone="text-cyan" />
            <Stat label="Payback" value={`${analysis.summary.paybackMonths} mo`} tone="text-amber" />
            <Stat label="Baseline loss" value={money(analysis.summary.baselineAnnualLoss)} tone="text-signal" />
            <Stat label="HR savings" value={money(analysis.summary.hrOperationalSavings)} tone="text-mint" />
            <Stat label="Stream" value={streamStatus} tone="text-slate-300" />
          </div>

          <div className="mt-5 grid gap-4 xl:grid-cols-[1fr_0.9fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-mint">
                <Banknote className="size-4" />
                Board-level exposure model
              </div>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={exposureChart} margin={{ left: -10, right: 8, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="name" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} tickFormatter={(value) => `$${Math.round(Number(value) / 1000)}K`} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} formatter={(value) => money(Number(value))} />
                    <Bar dataKey="value" radius={[3, 3, 0, 0]}>
                      {exposureChart.map((entry) => (
                        <Cell key={entry.name} fill={severityColor[entry.severity]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
                <TrendingUp className="size-4" />
                ROI forecast
              </div>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={forecastChart} margin={{ left: -18, right: 8, top: 10, bottom: 0 }}>
                    <defs>
                      <linearGradient id="roiSavingsGradient" x1="0" x2="0" y1="0" y2="1">
                        <stop offset="5%" stopColor="#7CF0A6" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#7CF0A6" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="month" stroke="#64748b" tickLine={false} axisLine={false} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Area type="monotone" dataKey="baseline" stroke="#FF3B6B" fill="transparent" strokeWidth={2} />
                    <Area type="monotone" dataKey="optimized" stroke="#F6B44B" fill="transparent" strokeWidth={2} />
                    <Area type="monotone" dataKey="savings" stroke="#7CF0A6" fill="url(#roiSavingsGradient)" strokeWidth={2} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-amber">
                <BriefcaseBusiness className="size-4" />
                Replacement and retention economics
              </div>
              <div className="grid gap-3">
                {analysis.replacementCosts.slice(0, 4).map((employee) => (
                  <div key={employee.employeeId} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <h3 className="text-sm font-medium text-white">{employee.employeeName}</h3>
                        <p className="mt-1 text-xs text-slate-500">{employee.teamName}</p>
                      </div>
                      <span style={{ color: severityColor[employee.severity] }} className="text-xs uppercase">
                        {employee.severity}
                      </span>
                    </div>
                    <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
                      <MoneyPill label="Exposure" value={employee.expectedAttritionExposure} />
                      <MoneyPill label="Preventable" value={employee.preventionSavings} />
                    </div>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-signal">
                <ReceiptText className="size-4" />
                Delay-cost and productivity impact
              </div>
              <div className="grid gap-3 md:grid-cols-2">
                {analysis.delayCosts.slice(0, 3).map((project) => (
                  <div key={project.projectId} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex items-start justify-between gap-2">
                      <h3 className="text-sm font-medium text-white">{project.projectName}</h3>
                      <span className="text-xs text-signal">{money(project.expectedDelayCost)}</span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">Revenue at risk: {money(project.revenueAtRisk)}</p>
                    <p className="mt-1 text-xs leading-5 text-slate-400">Mitigated value: {money(project.mitigatedCost)}</p>
                  </div>
                ))}
                {analysis.productivityLosses.slice(0, 3).map((team) => (
                  <div key={team.teamName} className="border border-line/60 bg-panel/60 p-3">
                    <h3 className="text-sm font-medium text-white">{team.teamName}</h3>
                    <p className="mt-2 text-xs leading-5 text-slate-400">Annual drag: {money(team.annualizedProductivityLoss)}</p>
                    <p className="mt-1 text-xs leading-5 text-slate-400">Recoverable: {money(team.recoverableValue)}</p>
                  </div>
                ))}
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[1fr_1fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-mint">
                <CircleDollarSign className="size-4" />
                Executive recommendations
              </div>
              <div className="grid gap-3">
                {analysis.recommendations.slice(0, 4).map((recommendation) => (
                  <div key={recommendation.recommendationId} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <h3 className="text-sm font-medium text-white">{recommendation.title}</h3>
                      <span className="text-xs text-mint">{money(recommendation.expectedSavings)}</span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{recommendation.action}</p>
                    <p className="mt-2 text-xs leading-5 text-slate-300">{recommendation.rationale}</p>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
                <Banknote className="size-4" />
                CEO impact brief
              </div>
              <div className="grid gap-3">
                {analysis.executiveInsights.map((insight) => (
                  <div key={insight.title} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <h3 className="text-sm font-medium text-white">{insight.title}</h3>
                      <span style={{ color: severityColor[insight.severity] }} className="text-xs uppercase">
                        {insight.severity}
                      </span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{insight.message}</p>
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

function executiveScenarioPayload() {
  return {
    horizon_months: 12,
    intervention_budget: 240000,
    retention_improvement: 0.32,
    productivity_recovery: 0.22,
    meeting_reduction: 0.24,
    overtime_reduction: 0.28,
    delay_risk_reduction: 0.26,
    realtime: true,
    employees: [
      {
        employee_id: "emp-critical-a",
        name: "Critical Architect",
        role: "Principal Engineer",
        team_name: "Development Team",
        annual_salary: 178000,
        attrition_probability: 0.72,
        burnout_probability: 0.88,
        productivity_score: 0.49,
        stress_score: 0.91,
        overtime_hours_monthly: 86,
        meeting_hours_weekly: 17,
        knowledge_criticality: 0.96,
        billable_revenue_per_day: 3600,
        open_critical_tasks: 24,
      },
      {
        employee_id: "emp-critical-b",
        name: "Release Lead",
        role: "QA Lead",
        team_name: "Development Team",
        annual_salary: 132000,
        attrition_probability: 0.54,
        burnout_probability: 0.72,
        productivity_score: 0.58,
        stress_score: 0.78,
        overtime_hours_monthly: 58,
        meeting_hours_weekly: 12,
        knowledge_criticality: 0.74,
        billable_revenue_per_day: 2100,
        open_critical_tasks: 16,
      },
    ],
    projects: [
      {
        project_id: "project-alpha-roi",
        project_name: "Project Alpha Revenue Platform",
        team_name: "Development Team",
        forecasted_revenue: 2400000,
        gross_margin: 0.66,
        failure_probability: 0.74,
        delay_probability: 0.73,
        projected_delay_days: 18,
        daily_burn_rate: 22000,
        delivery_penalty_per_day: 6500,
        client_churn_risk: 0.31,
        budget_utilization: 1.08,
        team_size: 19,
      },
    ],
  };
}

function MoneyPill({ label, value }: { label: string; value: number }) {
  return (
    <div className="border border-line/50 bg-void/50 px-2 py-2">
      <span className="block text-slate-500">{label}</span>
      <strong className="mt-1 block text-sm text-mint">{money(value)}</strong>
    </div>
  );
}

function Stat({ label, value, tone }: { label: string; value: string; tone: string }) {
  return (
    <div className="border border-line/70 bg-panel2/65 p-3">
      <span className="block text-xs uppercase text-slate-500">{label}</span>
      <strong className={`mt-1 block break-words text-base ${tone}`}>{value}</strong>
    </div>
  );
}

function money(value: number) {
  const abs = Math.abs(value);
  if (abs >= 1_000_000) return `$${(value / 1_000_000).toFixed(2)}M`;
  if (abs >= 1_000) return `$${Math.round(value / 1_000)}K`;
  return `$${Math.round(value)}`;
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
