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
import { Award, DollarSign, Gauge, Loader2, Radio, RefreshCw, Send, ShieldAlert, TrendingUp } from "lucide-react";

import type { CompensationResponse, CompensationSeverity } from "@/types/compensation";

const severityColor: Record<CompensationSeverity, string> = {
  low: "#7CF0A6",
  medium: "#F6B44B",
  high: "#F05D5E",
  critical: "#FF3B6B",
};

export function SalaryRecommendationPanel() {
  const [analysis, setAnalysis] = useState<CompensationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [streamStatus, setStreamStatus] = useState("connecting");

  const loadDefault = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await fetchJson("/api/compensation/recommend", { cache: "no-store" });
      if (!isCompensation(payload)) throw new Error("Malformed compensation payload");
      setAnalysis(payload);
      setStreamStatus((status) => (status === "connecting" ? "polling" : status));
    } catch {
      setError("AI Salary Recommendation Engine could not refresh live compensation intelligence.");
    } finally {
      setLoading(false);
    }
  }, []);

  const simulateRetentionPressure = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await fetchJson(
        "/api/compensation/recommend",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(buildCompensationPayload()),
          cache: "no-store",
        },
        60000,
      );
      if (!isCompensation(payload)) throw new Error("Malformed compensation payload");
      setAnalysis(payload);
      setStreamStatus((status) => (status === "connecting" ? "polling" : status));
    } catch {
      setError("AI Salary Recommendation Engine could not process the retention pressure scenario.");
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
        const response = await fetch("/api/compensation/stream", { cache: "no-store", signal: controller.signal });
        if (!response.ok) throw new Error("Compensation stream failed");
        const reader = response.body?.getReader();
        if (!reader) throw new Error("Missing compensation stream");
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
            if (isCompensation(payload)) {
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

  const salaryData = useMemo(
    () =>
      analysis?.recommendations.map((item) => ({
        name: item.employeeName.split(" ")[0],
        current: Math.round(item.currentSalary / 1000),
        recommended: Math.round(item.recommendedSalaryMid / 1000),
        risk: Math.round(item.compensationRiskScore),
      })) ?? [],
    [analysis],
  );

  const fairnessData = useMemo(
    () =>
      analysis?.fairnessHeatmap.map((item) => ({
        department: item.department.replace(" Platform", ""),
        fairness: Math.round(item.averageFairnessScore),
        gap: Math.round(item.averageMarketGap),
        budget: Math.round(item.recommendedBudget / 1000),
        risk: item.highRiskCount,
      })) ?? [],
    [analysis],
  );

  const promotionData = useMemo(
    () =>
      analysis?.recommendations.map((item) => ({
        name: item.employeeName.split(" ")[0],
        promotion: Math.round(item.promotionEligibility),
        bonus: Math.round(item.bonusPercent),
        retention: Math.round(item.retentionImpact),
      })) ?? [],
    [analysis],
  );

  return (
    <section data-testid="salary-recommendation-panel" className="border border-line/80 bg-panel/85 p-5 shadow-control backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <DollarSign className="size-5 text-cyan" />
          <div>
            <p className="text-xs uppercase text-cyan">AI Salary Recommendation Engine</p>
            <h2 className="text-xl font-semibold text-white">Fair salary bands, promotion intelligence, bonus planning, market benchmarking, and retention-safe compensation review</h2>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button data-testid="refresh-salary-recommendation" onClick={() => void loadDefault()} className="inline-flex items-center gap-2 border border-line bg-panel2 px-3 py-2 text-sm text-slate-300">
            <RefreshCw className="size-4" />
            Refresh review
          </button>
          <button data-testid="simulate-salary-recommendation" onClick={() => void simulateRetentionPressure()} className="inline-flex items-center gap-2 border border-cyan/40 bg-cyan/10 px-3 py-2 text-sm text-cyan">
            {loading ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
            Simulate retention gap
          </button>
        </div>
      </div>

      {error && !analysis ? <p className="mt-4 text-sm text-signal">{error}</p> : null}
      {loading && !analysis ? <p className="mt-5 text-sm text-slate-400">Modeling salary bands, market gaps, peer fairness, promotion readiness, and retention-compensation impact...</p> : null}

      {analysis ? (
        <>
          <div className="mt-5 grid gap-3 md:grid-cols-4 xl:grid-cols-8">
            <Stat label="Compensation signals" value={String(analysis.summary.employeesAnalyzed)} />
            <Stat label="Budget use" value={`${Math.round(analysis.summary.budgetUtilization)}%`} />
            <Stat label="Market gap" value={`${analysis.summary.averageMarketGap.toFixed(1)}%`} />
            <Stat label="Fairness" value={`${Math.round(analysis.summary.fairnessScore)}%`} />
            <Stat label="Promotions" value={String(analysis.summary.promotionCandidates)} />
            <Stat label="Risk reduced" value={`${Math.round(analysis.summary.retentionRiskReduced)}%`} />
            <Stat label="Plan value" value={formatMoney(analysis.summary.totalRecommendedAdjustment)} />
            <Stat label="Stream" value={streamStatus} />
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
                <Gauge className="size-4" />
                Compensation fairness heatmap
              </div>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={fairnessData} margin={{ left: -24, right: 8, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="department" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Bar dataKey="fairness" fill="#2EE9D3" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="gap" radius={[3, 3, 0, 0]}>
                      {fairnessData.map((item) => (
                        <Cell key={item.department} fill={item.gap >= 20 ? "#FF3B6B" : item.gap >= 10 ? "#F6B44B" : "#7CF0A6"} />
                      ))}
                    </Bar>
                    <Bar dataKey="budget" fill="#8B5CF6" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-mint">
                <TrendingUp className="size-4" />
                Market benchmarking
              </div>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={salaryData} margin={{ left: -24, right: 8, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="name" stroke="#64748b" tickLine={false} axisLine={false} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} formatter={(value) => [`$${value}k`, ""]} />
                    <Bar dataKey="current" fill="#64748b" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="recommended" fill="#7CF0A6" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="risk" radius={[3, 3, 0, 0]}>
                      {salaryData.map((item) => (
                        <Cell key={item.name} fill={item.risk >= 75 ? "#FF3B6B" : item.risk >= 55 ? "#F6B44B" : "#2EE9D3"} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </article>
          </div>

          <div className="mt-5 grid gap-4 xl:grid-cols-[1fr_0.95fr]">
            <article className="border border-cyan/25 bg-cyan/10 p-4">
              <div className="text-xs uppercase text-cyan">Fair salary recommendations</div>
              <div className="mt-3 grid gap-2">
                {analysis.recommendations.slice(0, 5).map((recommendation) => (
                  <div key={recommendation.employeeId} className="border border-cyan/20 bg-panel/70 p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="text-sm font-medium text-white">{recommendation.employeeName}</span>
                      <span className="text-xs text-cyan">
                        {recommendation.recommendedAdjustmentPercent.toFixed(1)}% / {formatMoney(recommendation.recommendedAdjustmentAmount)}
                      </span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{recommendation.rationale}</p>
                    <div className="mt-2 flex flex-wrap gap-2 text-xs text-slate-500">
                      <span>Risk {Math.round(recommendation.compensationRiskScore)}%</span>
                      <span>Fairness {Math.round(recommendation.fairnessScore)}%</span>
                      <span>Confidence {Math.round(recommendation.confidence * 100)}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-amber">
                <Award className="size-4" />
                Promotion and bonus recommendations
              </div>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={promotionData} margin={{ left: -24, right: 8, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="name" stroke="#64748b" tickLine={false} axisLine={false} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Line type="monotone" dataKey="promotion" stroke="#2EE9D3" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="bonus" stroke="#F6B44B" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="retention" stroke="#7CF0A6" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
              <div className="mt-3 grid gap-2">
                {analysis.recommendations.slice(0, 3).map((recommendation) => (
                  <div key={`${recommendation.employeeId}-promotion`} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="text-sm text-white">{recommendation.employeeName}</span>
                      <span className="text-xs text-amber">{Math.round(recommendation.promotionEligibility)}% promotion ready</span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{recommendation.promotionTrack}</p>
                  </div>
                ))}
              </div>
            </article>
          </div>

          <div className="mt-5 grid gap-4 xl:grid-cols-[1fr_1fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-signal">
                <ShieldAlert className="size-4" />
                Retention compensation alerts
              </div>
              <div className="grid gap-2">
                {analysis.alerts.map((alert) => (
                  <div key={`${alert.title}-${alert.probability}`} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="text-sm font-medium text-white">{alert.title}</span>
                      <span className="text-xs uppercase" style={{ color: severityColor[alert.severity] }}>
                        {alert.severity} / {Math.round(alert.probability)}%
                      </span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{alert.impact}</p>
                    <p className="mt-2 text-xs leading-5 text-slate-500">{alert.intervention}</p>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
                <Radio className="size-4" />
                Executive compensation insights
              </div>
              <div className="grid gap-2">
                {analysis.executiveInsights.map((insight) => (
                  <div key={insight} className="border border-line/60 bg-panel/60 p-3 text-sm leading-6 text-slate-300">
                    {insight}
                  </div>
                ))}
              </div>
              <div className="mt-3 border border-line/60 bg-panel/60 p-3 text-xs leading-5 text-slate-500">
                Model: {analysis.model}. Sources: attrition prediction, ROI engine, market benchmarking, compensation history.
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
    if (!response.ok) throw new Error("Compensation request failed");
    return await response.json();
  } finally {
    window.clearTimeout(timeout);
  }
}

function isCompensation(value: unknown): value is CompensationResponse {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Partial<CompensationResponse>;
  return Boolean(candidate.model && candidate.summary?.employeesAnalyzed !== undefined && Array.isArray(candidate.recommendations));
}

function buildCompensationPayload() {
  return {
    cycle_name: "Critical Retention Compensation Review",
    budget_pool: 720000,
    realtime: true,
    employees: [
      employee("salary-critical", "Employee A", "Principal Backend Engineer", 6, "Engineering", 176000, 11, 96, 94, 0.82, 0.9, 0.84, 0.93, 0.88, 0.78, 0.86, 0.78, 0.66, 0.24, 0.72, 26, 28, 0.96, 1.32, [
        "distributed systems",
        "fastapi",
        "kubernetes",
        "incident response",
        "postgresql",
      ]),
      employee("salary-market-gap", "Employee B", "Senior ML Engineer", 5, "AI Platform", 164000, 8, 92, 91, 0.76, 0.88, 0.7, 0.9, 0.84, 0.82, 0.88, 0.66, 0.58, 0.34, 0.78, 22, 20, 0.9, 1.24, [
        "mlops",
        "forecasting",
        "llm systems",
        "vector search",
      ]),
      employee("salary-stable", "Employee C", "Product Analyst", 3, "Product", 132000, 5, 78, 81, 0.42, 0.28, 0.34, 0.8, 0.82, 0.46, 0.58, 0.1, 0.18, 0.9, 1.12, 6, 3, 0.38, 0.9, [
        "analytics",
        "roadmapping",
        "sql",
      ]),
    ],
  };
}

function employee(
  employee_id: string,
  employee_name: string,
  role: string,
  level: number,
  department: string,
  annual_salary: number,
  experience_years: number,
  performance_score: number,
  productivity_score: number,
  skill_growth: number,
  skill_scarcity: number,
  leadership_score: number,
  delivery_consistency: number,
  collaboration_score: number,
  innovation_score: number,
  learning_velocity: number,
  attrition_probability: number,
  burnout_risk: number,
  salary_satisfaction: number,
  peer_compa_ratio: number,
  last_raise_months: number,
  promotion_delay_months: number,
  criticality_score: number,
  market_multiplier: number,
  skills: string[],
) {
  return {
    employee_id,
    employee_name,
    role,
    level,
    department,
    location: "United States",
    annual_salary,
    experience_years,
    performance_score,
    productivity_score,
    skill_growth,
    skill_scarcity,
    leadership_score,
    delivery_consistency,
    collaboration_score,
    innovation_score,
    learning_velocity,
    attrition_probability,
    burnout_risk,
    salary_satisfaction,
    peer_compa_ratio,
    last_raise_months,
    promotion_delay_months,
    criticality_score,
    market_multiplier,
    skills,
  };
}
