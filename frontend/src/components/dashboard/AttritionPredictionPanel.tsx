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
import { BriefcaseBusiness, BrainCircuit, DollarSign, Loader2, RefreshCw, ShieldAlert, TrendingUp, Users } from "lucide-react";

import type { AttritionResponse, AttritionRiskLevel } from "@/types/attrition";

type SnakeRecord = Record<string, unknown>;

const riskColor: Record<AttritionRiskLevel, string> = {
  low: "#7CF0A6",
  medium: "#2EE9D3",
  high: "#F6B44B",
  critical: "#FF3B6B",
};

export function AttritionPredictionPanel({ initialAnalysis = null }: { initialAnalysis?: AttritionResponse | null }) {
  const [analysis, setAnalysis] = useState<AttritionResponse | null>(initialAnalysis);
  const [loading, setLoading] = useState(!initialAnalysis);
  const [error, setError] = useState("");
  const [streamStatus, setStreamStatus] = useState("connecting");

  const loadDefault = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/attrition/analyze", { cache: "no-store" });
      if (!response.ok) throw new Error("Attrition prediction failed");
      setAnalysis((await response.json()) as AttritionResponse);
    } catch {
      setError("Attrition AI could not load workforce risk.");
    } finally {
      setLoading(false);
    }
  }, []);

  const runRetentionStress = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/attrition/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(retentionStressPayload()),
        cache: "no-store",
      });
      if (!response.ok) throw new Error("Attrition prediction failed");
      setAnalysis((await response.json()) as AttritionResponse);
    } catch {
      setError("Attrition AI could not process the retention stress test.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    async function connectStream() {
      try {
        const response = await fetch("/api/attrition/stream", { cache: "no-store", signal: controller.signal });
        const reader = response.body?.getReader();
        if (!reader) throw new Error("Missing attrition stream");
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
              setAnalysis(toCamel<AttritionResponse>(JSON.parse(dataLine.slice(6))));
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
      if (!initialAnalysis) void loadDefault();
    }, 0);
    const streamRefresh = window.setTimeout(() => {
      void connectStream();
    }, 10000);
    return () => {
      controller.abort();
      window.clearTimeout(firstRefresh);
      window.clearTimeout(streamRefresh);
    };
  }, [initialAnalysis, loadDefault]);

  const riskChart = useMemo(
    () =>
      analysis?.predictions.map((prediction) => ({
        name: compactName(prediction.employeeName),
        attrition: Math.round(prediction.resignationProbability),
        stability: Math.round(100 - prediction.resignationProbability),
        exposure: Math.round(prediction.replacementCostExposure / 1000),
      })) ?? [],
    [analysis],
  );

  const topEmployee = analysis?.predictions[0] ?? null;
  const forecastChart = useMemo(
    () =>
      topEmployee?.forecast.map((point) => ({
        day: `D${point.day}`,
        resignation: Math.round(point.resignationProbability),
        stability: Math.round(point.workforceStability),
      })) ?? [],
    [topEmployee],
  );

  return (
    <section className="border border-line/80 bg-panel/85 p-5 shadow-control backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <Users className="size-5 text-cyan" />
          <div>
            <p className="text-xs uppercase text-cyan">Talent Continuity Forecast Engine</p>
            <h2 className="text-xl font-semibold text-white">Resignation forecasting, retention drivers, workforce stability, and strategic intervention intelligence</h2>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button onClick={() => void loadDefault()} className="inline-flex items-center gap-2 border border-line bg-panel2 px-3 py-2 text-sm text-slate-300">
            <RefreshCw className="size-4" />
            Refresh risk
          </button>
          <button onClick={() => void runRetentionStress()} className="inline-flex items-center gap-2 border border-signal/40 bg-signal/10 px-3 py-2 text-sm text-signal">
            {loading ? <Loader2 className="size-4 animate-spin" /> : <ShieldAlert className="size-4" />}
            Stress test
          </button>
        </div>
      </div>

      {error ? <p className="mt-4 text-sm text-signal">{error}</p> : null}
      {loading ? <p className="mt-5 text-sm text-slate-400">Running RandomForest/XGBoost attrition inference and retention attribution...</p> : null}

      {analysis ? (
        <>
          <div className="mt-5 grid gap-3 md:grid-cols-6">
            <Stat label="Workforce signals" value={String(analysis.summary.employeesAnalyzed)} />
            <Stat label="Avg risk" value={`${Math.round(analysis.summary.averageResignationProbability)}%`} />
            <Stat label="Elevated risk" value={String(analysis.summary.highRiskEmployees)} />
            <Stat label="Critical risk" value={String(analysis.summary.criticalRiskEmployees)} />
            <Stat label="Exposure" value={formatMoney(analysis.summary.estimatedReplacementExposure)} />
            <Stat label="Stream" value={streamStatus} />
          </div>

          <div className="mt-5 grid gap-4 xl:grid-cols-[1fr_0.9fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
                <BrainCircuit className="size-4" />
                Talent continuity heatmap
              </div>
              <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
                {analysis.heatmap.map((item) => (
                  <div key={`${item.employee}-${item.team}`} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <h3 className="text-sm font-medium text-white">{compactName(item.employee)}</h3>
                        <p className="mt-1 text-xs text-slate-500">{item.team}</p>
                      </div>
                      <span className="text-xs text-cyan">{Math.round(item.stability)} stable</span>
                    </div>
                    <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
                      <RiskPill label="Risk" value={item.attrition} />
                      <RiskPill label="Burnout x" value={item.burnoutMultiplier * 25} suffix="" />
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-4 h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={riskChart} margin={{ left: -22, right: 8, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="name" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Bar dataKey="attrition" fill="#FF3B6B" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="stability" fill="#2EE9D3" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-signal">
                <TrendingUp className="size-4" />
                {topEmployee ? compactName(topEmployee.employeeName) : "Critical talent"} resignation forecast
              </div>
              {topEmployee ? (
                <>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <SignalStat label="Probability" value={topEmployee.resignationProbability} color={riskColor[topEmployee.riskLevel]} />
                    <SignalStat label="Confidence" value={topEmployee.confidence * 100} color="#2EE9D3" />
                    <SignalStat label="Burnout x" value={topEmployee.burnoutCorrelationMultiplier * 25} color="#F6B44B" />
                    <SignalStat label="Cost exposure" value={topEmployee.replacementCostExposure / 1000} color="#FF3B6B" suffix="k" />
                  </div>
                  <div className="mt-3 border border-line/60 bg-panel/60 p-3">
                    <div className="flex items-center justify-between gap-2 text-xs uppercase">
                      <span className="text-slate-500">Departure window</span>
                      <span style={{ color: riskColor[topEmployee.riskLevel] }}>{topEmployee.estimatedDepartureWindow}</span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-300">{topEmployee.primaryReasons[0]}</p>
                  </div>
                </>
              ) : null}
              <div className="mt-4 h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={forecastChart} margin={{ left: -18, right: 8, top: 10, bottom: 0 }}>
                    <defs>
                      <linearGradient id="attritionGradient" x1="0" x2="0" y1="0" y2="1">
                        <stop offset="5%" stopColor="#FF3B6B" stopOpacity={0.32} />
                        <stop offset="95%" stopColor="#FF3B6B" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="day" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 10 }} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Area type="monotone" dataKey="resignation" stroke="#FF3B6B" fill="url(#attritionGradient)" strokeWidth={2} />
                    <Area type="monotone" dataKey="stability" stroke="#7CF0A6" fill="transparent" strokeWidth={2} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[0.85fr_1.15fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-amber">
                <BriefcaseBusiness className="size-4" />
                Team turnover pressure
              </div>
              <div className="grid gap-3">
                {analysis.teamTrends.map((trend) => (
                  <div key={`${trend.department}-${trend.teamName}`} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex items-center justify-between gap-2">
                      <div>
                        <h3 className="text-sm font-medium text-white">{trend.teamName}</h3>
                        <p className="mt-1 text-xs text-slate-500">{trend.department}</p>
                      </div>
                      <span className="text-xs uppercase text-cyan">{trend.moraleSignal}</span>
                    </div>
                    <div className="mt-3 grid grid-cols-3 gap-2 text-xs">
                      <RiskPill label="Avg" value={trend.averageAttritionProbability} />
                      <RiskPill label="Chain" value={trend.chainReactionRisk} />
                      <RiskPill label="Pressure" value={trend.turnoverPressure} />
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{trend.recommendation}</p>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-mint">
                <DollarSign className="size-4" />
                Retention recommendations
              </div>
              <div className="grid gap-3 md:grid-cols-2">
                {analysis.recommendations.map((recommendation) => (
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
            {(analysis.predictions ?? []).slice(0, 3).map((prediction) => (
              <article key={prediction.employeeId} className="border border-cyan/20 bg-cyan/10 p-4">
                <div className="flex items-center gap-2 text-xs uppercase text-cyan">
                  <BrainCircuit className="size-4" />
                  Explainable retention drivers
                </div>
                <h3 className="mt-2 text-base font-semibold text-white">{prediction.employeeName}</h3>
                <div className="mt-3 grid gap-2">
                  {prediction.featureAttributions.slice(0, 3).map((driver) => (
                    <div key={`${prediction.employeeId}-${driver.feature}`} className="flex items-center justify-between gap-3 border border-line/50 bg-panel/60 px-2 py-2 text-xs">
                      <span className="text-slate-400">{labelize(driver.feature)}</span>
                      <strong style={{ color: driver.direction === "increases_attrition" ? "#FF3B6B" : "#7CF0A6" }}>{Math.round(driver.contribution)}</strong>
                    </div>
                  ))}
                </div>
              </article>
            ))}
          </div>
        </>
      ) : null}
    </section>
  );
}

function retentionStressPayload() {
  return {
    horizon_days: 90,
    sensitivity: 0.78,
    realtime: true,
    employees: [
      {
        employee_id: "emp-critical-attrition",
        employee_name: "Sarah Malik",
        department: "Engineering",
        team_name: "Core Platform",
        role: "Principal API Architect",
        burnout_score: 93,
        productivity_score: 39,
        productivity_trend: -0.62,
        overtime_hours_30d: 104,
        meeting_hours_weekly: 23,
        salary_satisfaction: 0.31,
        sentiment_score: -0.74,
        manager_compatibility: 0.37,
        team_stress: 0.91,
        promotion_delay_months: 34,
        work_life_balance: 0.22,
        attendance_rate: 0.76,
        absences_90d: 11,
        tenure_months: 28,
        knowledge_criticality: 0.98,
        annual_salary: 196000,
        billable_revenue_per_day: 4200,
      },
      {
        employee_id: "emp-stable-attrition",
        employee_name: "Arjun Rao",
        department: "Operations",
        team_name: "Automation Team",
        role: "Automation Engineer",
        burnout_score: 18,
        productivity_score: 94,
        productivity_trend: 0.24,
        overtime_hours_30d: 4,
        meeting_hours_weekly: 4,
        salary_satisfaction: 0.9,
        sentiment_score: 0.68,
        manager_compatibility: 0.91,
        team_stress: 0.16,
        promotion_delay_months: 3,
        work_life_balance: 0.88,
        attendance_rate: 1,
        absences_90d: 0,
        tenure_months: 38,
        knowledge_criticality: 0.44,
        annual_salary: 128000,
        billable_revenue_per_day: 1700,
      },
    ],
  };
}

function RiskPill({ label, value, suffix = "%" }: { label: string; value: number; suffix?: string }) {
  const color = value >= 75 ? "#FF3B6B" : value >= 55 ? "#F6B44B" : value >= 35 ? "#2EE9D3" : "#7CF0A6";
  return (
    <div className="border border-line/50 bg-void/50 px-2 py-2">
      <span className="block text-slate-500">{label}</span>
      <strong style={{ color }} className="mt-1 block text-sm">
        {Math.round(value)}
        {suffix}
      </strong>
    </div>
  );
}

function SignalStat({ label, value, color, suffix = "%" }: { label: string; value: number; color: string; suffix?: string }) {
  return (
    <div className="border border-line/60 bg-panel/60 p-3">
      <span className="block text-xs uppercase text-slate-500">{label}</span>
      <strong style={{ color }} className="mt-1 block text-xl text-white">
        {Math.round(value)}
        {suffix}
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

function formatMoney(value: number) {
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  return `$${Math.round(value / 1000)}K`;
}

function compactName(name: string) {
  return name.replace(/^Employee\s+/i, "");
}

function labelize(value: string) {
  return value.replace(/_/g, " ");
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
