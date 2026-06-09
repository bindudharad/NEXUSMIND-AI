"use client";

import type React from "react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
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
import { BarChart3, Building2, Gauge, Globe2, Loader2, LockKeyhole, Radio, RefreshCw, Send, ShieldCheck, TrendingUp } from "lucide-react";

import type { BenchmarkingResponse, BenchmarkPriority } from "@/types/benchmarking";

const priorityColor: Record<BenchmarkPriority, string> = {
  low: "#7CF0A6",
  medium: "#F6B44B",
  high: "#F05D5E",
  critical: "#FF3B6B",
};

export function BenchmarkingPanel() {
  const [analysis, setAnalysis] = useState<BenchmarkingResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [streamStatus, setStreamStatus] = useState("connecting");
  const manualScenarioUntil = useRef(0);

  const loadDefault = useCallback(async () => {
    setLoading(true);
    setError("");
    manualScenarioUntil.current = 0;
    try {
      const payload = await fetchJson("/api/benchmarking/analyze", { cache: "no-store" });
      if (!isBenchmarking(payload)) throw new Error("Malformed benchmarking payload");
      setAnalysis(payload);
      setStreamStatus((status) => (status === "connecting" ? "polling" : status));
    } catch {
      setError("Multi-company benchmark intelligence could not refresh.");
    } finally {
      setLoading(false);
    }
  }, []);

  const simulateBenchmarkGap = useCallback(async () => {
    setLoading(true);
    setError("");
    manualScenarioUntil.current = Date.now() + 30000;
    try {
      const payload = await fetchJson(
        "/api/benchmarking/analyze",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(buildBenchmarkScenario()),
          cache: "no-store",
        },
        60000,
      );
      if (!isBenchmarking(payload)) throw new Error("Malformed benchmarking payload");
      setAnalysis(payload);
      setStreamStatus((status) => (status === "connecting" ? "polling" : status));
    } catch {
      setError("Benchmark simulation could not process the anonymous peer comparison.");
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
        const response = await fetch("/api/benchmarking/stream", { cache: "no-store", signal: controller.signal });
        if (!response.ok) throw new Error("Benchmarking stream failed");
        const reader = response.body?.getReader();
        if (!reader) throw new Error("Missing benchmarking stream");
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
            if (isBenchmarking(payload) && Date.now() > manualScenarioUntil.current) {
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

  const target = analysis?.benchmarkScores.find((score) => score.isTarget) ?? analysis?.benchmarkScores[0];
  const kpiData = useMemo(
    () =>
      analysis?.kpiComparisons.slice(0, 8).map((item) => ({
        metric: shortMetric(item.metric),
        company: Math.round(item.companyValue),
        median: Math.round(item.industryMedian),
        top: Math.round(item.topQuartile),
        delta: Math.round(item.deltaPercent),
        priority: item.priority,
      })) ?? [],
    [analysis],
  );
  const forecastData = useMemo(
    () =>
      target?.forecast.map((point) => ({
        day: `D${point.day}`,
        score: Math.round(point.benchmarkScore),
        productivity: Math.round(point.productivityPercentile),
        retention: Math.round(point.retentionPercentile),
        maturity: Math.round(point.maturityScore),
      })) ?? [],
    [target],
  );

  return (
    <section data-testid="benchmarking-panel" className="border border-cyan/25 bg-panel/85 p-5 shadow-control backdrop-blur">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex gap-3">
          <div className="mt-1 grid size-10 place-items-center border border-cyan/40 bg-cyan/10 text-cyan">
            <Globe2 className="size-5" />
          </div>
          <div>
            <p className="text-xs uppercase text-cyan">Multi-Company Benchmarking & Industry Intelligence</p>
            <h2 className="text-xl font-semibold text-white">
              Anonymous peer benchmarking, industry KPI forecasting, and workforce maturity intelligence
            </h2>
            <p className="mt-2 max-w-5xl text-sm leading-6 text-slate-500">
              Benchmark analytics dashboard, Industry comparison graphs, Productivity benchmark heatmaps, Burnout comparison visualizations,
              Retention analytics charts, Workforce maturity scorecards, AI recommendation widgets, and Executive competitive insights
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            data-testid="refresh-benchmarking"
            type="button"
            onClick={() => void loadDefault()}
            className="inline-flex items-center gap-2 border border-line bg-panel2 px-3 py-2 text-sm text-slate-300"
          >
            <RefreshCw className="size-4" />
            Refresh benchmark
          </button>
          <button
            data-testid="simulate-benchmarking"
            type="button"
            onClick={() => void simulateBenchmarkGap()}
            className="inline-flex items-center gap-2 border border-cyan/50 bg-cyan/10 px-3 py-2 text-sm text-cyan"
          >
            <Send className="size-4" />
            Simulate gap
          </button>
        </div>
      </div>

      {error ? <div className="mt-4 border border-signal/30 bg-signal/10 p-3 text-sm text-signal">{error}</div> : null}

      <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-8">
        <Stat label="Companies" value={analysis ? String(analysis.summary.companiesAnalyzed) : "..."} />
        <Stat label="Peers" value={analysis ? String(analysis.summary.anonymousPeerCount) : "..."} />
        <Stat label="Percentile" value={analysis ? `${Math.round(analysis.summary.targetPercentile)}%` : "..."} />
        <Stat label="Benchmark" value={analysis ? `${Math.round(analysis.summary.targetBenchmarkScore)}` : "..."} />
        <Stat label="Productivity" value={analysis ? signed(analysis.summary.productivityVsIndustry) : "..."} />
        <Stat label="Burnout" value={analysis ? signed(analysis.summary.burnoutVsIndustry) : "..."} tone="text-signal" />
        <Stat label="Maturity" value={analysis ? `${Math.round(analysis.summary.maturityScore)}` : "..."} />
        <Stat label="Stream" value={streamStatus} />
      </div>

      {loading && !analysis ? (
        <div className="mt-5 flex items-center gap-3 border border-line bg-panel2/70 p-5 text-sm text-slate-400">
          <Loader2 className="size-4 animate-spin text-cyan" />
          Loading anonymous benchmark intelligence...
        </div>
      ) : null}

      {analysis && target ? (
        <>
          <div className="mt-5 grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
            <article className="border border-line/80 bg-panel2/55 p-4">
              <PanelTitle icon={BarChart3} label="Industry comparison graphs" />
              <div className="mt-4 h-[330px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={kpiData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1D2A3A" />
                    <XAxis dataKey="metric" tick={{ fill: "#71839B", fontSize: 11 }} />
                    <YAxis tick={{ fill: "#71839B", fontSize: 11 }} />
                    <Tooltip contentStyle={{ background: "#0B111A", border: "1px solid #213044", color: "#E6EDF7" }} />
                    <Bar dataKey="company" name="Target" radius={[2, 2, 0, 0]}>
                      {kpiData.map((item) => (
                        <Cell key={item.metric} fill={priorityColor[item.priority]} />
                      ))}
                    </Bar>
                    <Bar dataKey="median" name="Industry median" fill="#2EE9D3" radius={[2, 2, 0, 0]} />
                    <Bar dataKey="top" name="Top quartile" fill="#7CF0A6" radius={[2, 2, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </article>

            <article className="border border-cyan/35 bg-cyan/10 p-4">
              <PanelTitle icon={Gauge} label="Benchmark analytics dashboard" />
              <div className="mt-4 border border-cyan/25 bg-panel/70 p-4">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-xs uppercase text-slate-500">Target cohort</p>
                    <h3 className="mt-1 text-lg font-semibold text-white">{target.cohortLabel}</h3>
                  </div>
                  <span className="text-2xl font-semibold text-cyan">{Math.round(target.percentileRank)}%</span>
                </div>
                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  <Score label="Retention stability" value={target.retentionStabilityScore} />
                  <Score label="Operational maturity" value={target.operationalMaturityScore} />
                  <Score label="Workforce maturity" value={target.workforceMaturityScore} />
                  <Score label="Innovation maturity" value={target.innovationMaturityScore} />
                </div>
                <div className="mt-4 flex items-start gap-2 border border-line/70 bg-void/60 p-3 text-xs leading-5 text-slate-400">
                  <LockKeyhole className="mt-0.5 size-4 shrink-0 text-mint" />
                  Privacy-safe ID {target.anonymizedCompanyId}; epsilon {analysis.privacyEpsilon}; noise {target.privacyNoiseApplied.toFixed(2)}.
                </div>
              </div>
              <div className="mt-3 grid gap-2">
                {target.gaps.slice(0, 3).map((gap) => (
                  <div key={gap} className="border border-signal/25 bg-signal/10 p-3 text-sm text-slate-300">
                    {gap}
                  </div>
                ))}
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
            <article className="border border-line/80 bg-panel2/55 p-4">
              <PanelTitle icon={TrendingUp} label="Retention analytics charts" />
              <div className="mt-4 h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={forecastData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1D2A3A" />
                    <XAxis dataKey="day" tick={{ fill: "#71839B", fontSize: 11 }} />
                    <YAxis domain={[0, 100]} tick={{ fill: "#71839B", fontSize: 11 }} />
                    <Tooltip contentStyle={{ background: "#0B111A", border: "1px solid #213044", color: "#E6EDF7" }} />
                    <Line type="monotone" dataKey="score" stroke="#2EE9D3" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="retention" stroke="#7CF0A6" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="maturity" stroke="#F6B44B" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </article>

            <article className="border border-line/80 bg-panel2/55 p-4">
              <PanelTitle icon={ShieldCheck} label="Workforce maturity scorecards" />
              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                {analysis.maturityScorecards.map((card) => (
                  <div key={card.category} className="border border-line/70 bg-panel/65 p-4">
                    <div className="flex items-center justify-between gap-3">
                      <h3 className="font-medium text-white">{card.category}</h3>
                      <span className="text-sm text-cyan">{Math.round(card.score)}</span>
                    </div>
                    <div className="mt-3 h-2 bg-line">
                      <div className="h-full bg-cyan" style={{ width: `${card.score}%` }} />
                    </div>
                    <p className="mt-3 text-xs text-slate-500">
                      Median {Math.round(card.industryMedian)} / top decile {Math.round(card.topDecile)} / {card.maturityLevel}
                    </p>
                  </div>
                ))}
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[1fr_1fr]">
            <article className="border border-line/80 bg-panel2/55 p-4">
              <PanelTitle icon={Building2} label="Productivity benchmark heatmaps" />
              <div className="mt-4 grid gap-2">
                {analysis.heatmap.slice(0, 8).map((point) => (
                  <div key={`${point.metric}-${point.score}`} className="border border-line/70 bg-panel/65 p-3">
                    <div className="flex items-center justify-between gap-3 text-sm">
                      <span className="font-medium text-white">{point.metric}</span>
                      <span style={{ color: priorityColor[point.priority] }}>{signed(point.industryDelta)}</span>
                    </div>
                    <div className="mt-2 h-2 bg-line">
                      <div className="h-full" style={{ width: `${point.score}%`, backgroundColor: priorityColor[point.priority] }} />
                    </div>
                  </div>
                ))}
              </div>
              <p className="mt-4 text-xs uppercase text-slate-500">Burnout comparison visualizations included in risk-colored benchmark deltas</p>
            </article>

            <article className="border border-line/80 bg-panel2/55 p-4">
              <PanelTitle icon={Radio} label="AI recommendation widgets" />
              <div className="mt-4 grid gap-3">
                {analysis.recommendations.slice(0, 4).map((recommendation) => (
                  <div key={recommendation.title} className="border border-line/70 bg-panel/65 p-3">
                    <div className="flex items-center justify-between gap-3">
                      <h3 className="font-medium text-white">{recommendation.title}</h3>
                      <span style={{ color: priorityColor[recommendation.priority] }}>{recommendation.priority}</span>
                    </div>
                    <p className="mt-2 text-sm leading-6 text-slate-400">{recommendation.action}</p>
                    <p className="mt-2 text-xs text-cyan">{recommendation.expectedImpact}</p>
                  </div>
                ))}
              </div>
            </article>
          </div>

          <article className="mt-4 border border-cyan/25 bg-panel2/55 p-4">
            <PanelTitle icon={Globe2} label="Executive competitive insights" />
            <div className="mt-4 grid gap-3 md:grid-cols-2">
              {analysis.executiveInsights.map((insight) => (
                <div key={insight} className="border border-cyan/20 bg-cyan/10 p-3 text-sm leading-6 text-slate-300">
                  {insight}
                </div>
              ))}
            </div>
          </article>
        </>
      ) : null}
    </section>
  );
}

function PanelTitle({ icon: Icon, label }: { icon: React.ComponentType<{ className?: string }>; label: string }) {
  return (
    <div className="flex items-center gap-2 text-xs uppercase text-cyan">
      <Icon className="size-4" />
      {label}
    </div>
  );
}

function Stat({ label, value, tone = "text-white" }: { label: string; value: string; tone?: string }) {
  return (
    <div className="border border-line/70 bg-panel2/70 p-3">
      <span className="block text-xs uppercase text-slate-500">{label}</span>
      <strong className={`mt-2 block text-lg ${tone}`}>{value}</strong>
    </div>
  );
}

function Score({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <span className="block text-[11px] uppercase text-slate-500">{label}</span>
      <strong className="mt-1 block text-lg text-white">{Math.round(value)}</strong>
    </div>
  );
}

function signed(value: number) {
  return `${value >= 0 ? "+" : ""}${Math.round(value)}%`;
}

function shortMetric(value: string) {
  return value.replace(" benchmark", "").replace(" comparison", "").replace(" stability", " retention").split(" ").slice(0, 2).join(" ");
}

async function fetchJson(input: string, init: RequestInit = {}, timeoutMs = 30000): Promise<unknown> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(input, { ...init, signal: controller.signal });
    if (!response.ok) throw new Error("Benchmarking request failed");
    return await response.json();
  } finally {
    window.clearTimeout(timeout);
  }
}

function isBenchmarking(value: unknown): value is BenchmarkingResponse {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Partial<BenchmarkingResponse>;
  return Boolean(
    candidate.model &&
      candidate.summary?.industryRankingLabel &&
      Array.isArray(candidate.benchmarkScores) &&
      Array.isArray(candidate.kpiComparisons) &&
      Array.isArray(candidate.recommendations),
  );
}

function buildBenchmarkScenario() {
  const peers = [
    peer("peer-top-1", 0.86, 0.24, 0.92, 0.87, 0.86, 0.84, 0.9),
    peer("peer-top-2", 0.81, 0.29, 0.89, 0.82, 0.83, 0.79, 0.84),
    peer("peer-top-3", 0.79, 0.31, 0.87, 0.8, 0.8, 0.77, 0.82),
  ];
  return {
    cycle_name: "Executive Benchmark Gap Simulation",
    target_company_id: "target-company",
    industry: "ai_saas",
    company_stage: "scaleup",
    horizon_days: 120,
    privacy_epsilon: 2.2,
    realtime: true,
    companies: [
      {
        company_id: "target-company",
        industry: "ai_saas",
        company_stage: "scaleup",
        employee_count: 620,
        productivity_score: 0.58,
        burnout_index: 0.66,
        attrition_rate: 0.28,
        retention_rate: 0.72,
        team_efficiency: 0.55,
        delivery_stability: 0.57,
        workforce_happiness: 0.5,
        innovation_output: 0.58,
        collaboration_quality: 0.52,
        project_success_rate: 0.56,
        communication_health: 0.49,
        learning_growth: 0.54,
        operational_stability: 0.55,
        sprint_velocity: 0.56,
        overtime_intensity: 0.61,
        incident_rate: 0.34,
        ai_adoption: 0.62,
        data_confidence: 0.88,
      },
      ...peers,
    ],
  };
}

function peer(id: string, productivity: number, burnout: number, retention: number, delivery: number, innovation: number, collaboration: number, aiAdoption: number) {
  return {
    company_id: id,
    industry: "ai_saas",
    company_stage: "scaleup",
    employee_count: 900,
    productivity_score: productivity,
    burnout_index: burnout,
    attrition_rate: Math.max(0.04, 1 - retention),
    retention_rate: retention,
    team_efficiency: productivity - 0.02,
    delivery_stability: delivery,
    workforce_happiness: Math.max(0.55, 1 - burnout * 0.72),
    innovation_output: innovation,
    collaboration_quality: collaboration,
    project_success_rate: delivery + 0.01,
    communication_health: collaboration - 0.01,
    learning_growth: innovation - 0.03,
    operational_stability: delivery,
    sprint_velocity: productivity - 0.01,
    overtime_intensity: burnout * 0.78,
    incident_rate: Math.max(0.05, 1 - delivery),
    ai_adoption: aiAdoption,
    data_confidence: 0.9,
  };
}
