"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type React from "react";
import { Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Bot, BriefcaseBusiness, Loader2, Radio, RefreshCw, Send, ShieldAlert, TrendingUp, Users } from "lucide-react";

import type { BusinessAssistantResponse, BusinessPredictionResponse, BusinessRiskLevel } from "@/types/business-prediction";

const riskColor: Record<BusinessRiskLevel, string> = {
  low: "#7CF0A6",
  medium: "#F6B44B",
  high: "#F05D5E",
  critical: "#FF3B6B",
};

export function BusinessPredictionPanel() {
  const [analysis, setAnalysis] = useState<BusinessPredictionResponse | null>(null);
  const [assistant, setAssistant] = useState<BusinessAssistantResponse | null>(null);
  const [question, setQuestion] = useState("Forecast next quarter revenue.");
  const [loading, setLoading] = useState(true);
  const [assistantLoading, setAssistantLoading] = useState(false);
  const [error, setError] = useState("");
  const [streamStatus, setStreamStatus] = useState("connecting");
  const manualScenarioUntil = useRef(0);

  const loadDefault = useCallback(async () => {
    setLoading(true);
    setError("");
    manualScenarioUntil.current = 0;
    try {
      const payload = await fetchJson("/api/business/prediction/default", { cache: "no-store" });
      if (!isBusinessPrediction(payload)) throw new Error("Malformed business prediction payload");
      setAnalysis(payload);
      setStreamStatus((status) => (status === "connecting" ? "polling" : status));
    } catch {
      setError("Business Prediction Engine could not refresh live executive forecast intelligence.");
    } finally {
      setLoading(false);
    }
  }, []);

  const runScenario = useCallback(async (scenario: "revenue" | "churn" | "freeze") => {
    setLoading(true);
    setError("");
    manualScenarioUntil.current = Date.now() + 30000;
    const scenarioPayload =
      scenario === "revenue"
        ? { scenario_id: "revenue-drop-20", scenario: "What happens if revenue drops by 20%?", revenue_delta_percent: -20 }
        : scenario === "churn"
          ? { scenario_id: "churn-plus-15", scenario: "What happens if churn increases by 15%?", churn_delta_percent: 15 }
          : { scenario_id: "hiring-freeze", scenario: "What happens if hiring freezes?", hiring_freeze_months: 6 };
    try {
      const payload = await fetchJson(
        "/api/business/prediction/forecast",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ horizon_months: 12, scenario: scenarioPayload }),
          cache: "no-store",
        },
        60000,
      );
      if (!isBusinessPrediction(payload)) throw new Error("Malformed business prediction payload");
      setAnalysis(payload);
    } catch {
      setError("Business Prediction Engine could not process the executive scenario.");
    } finally {
      setLoading(false);
    }
  }, []);

  const askAssistant = useCallback(async () => {
    if (!question.trim()) return;
    setAssistantLoading(true);
    try {
      const payload = await fetchJson(
        "/api/business/prediction/ask",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question, horizon_months: 12 }),
          cache: "no-store",
        },
        60000,
      );
      if (!isBusinessAssistant(payload)) throw new Error("Malformed business assistant payload");
      setAssistant(payload);
    } catch {
      setAssistant({
        model: "Executive Business Intelligence Assistant",
        generatedAt: new Date().toISOString(),
        question,
        intent: "error",
        answer: "Business assistant could not produce a forecast answer from the live API.",
        confidence: 0,
        citedEvidence: [],
        scenario: null,
        recommendedActions: [],
        sourceSystems: [],
        storage: "",
      });
    } finally {
      setAssistantLoading(false);
    }
  }, [question]);

  useEffect(() => {
    const controller = new AbortController();
    async function connectStream() {
      let streamStarted = false;
      const fallback = window.setTimeout(() => {
        if (!streamStarted && !controller.signal.aborted) setStreamStatus("polling");
      }, 12000);
      try {
        const response = await fetch("/api/business/prediction/stream", { cache: "no-store", signal: controller.signal });
        if (!response.ok) throw new Error("Business Prediction stream failed");
        const reader = response.body?.getReader();
        if (!reader) throw new Error("Missing Business Prediction stream");
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
            if (isBusinessPrediction(payload) && Date.now() > manualScenarioUntil.current) {
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
    }, 3000);
    return () => {
      controller.abort();
      window.clearTimeout(firstRefresh);
      window.clearTimeout(streamRefresh);
    };
  }, [loadDefault]);

  const revenueData = useMemo(
    () =>
      analysis?.revenueForecast.map((point) => ({
        month: point.month,
        revenue: dollarsToMillions(point.revenue),
        lower: dollarsToMillions(point.lowerBound),
        upper: dollarsToMillions(point.upperBound),
        risk: Math.round(point.revenueRisk),
      })) ?? [],
    [analysis],
  );
  const churnData = useMemo(
    () =>
      analysis?.churnPredictions.slice(0, 5).map((client) => ({
        name: shortName(client.clientName),
        churn: Math.round(client.churnProbability),
        renewal: Math.round(client.renewalProbability),
        risk: dollarsToMillions(client.revenueAtRisk),
      })) ?? [],
    [analysis],
  );
  const hiringData = useMemo(
    () =>
      analysis?.hiringDemand.slice(0, 6).map((item) => ({
        department: item.department,
        required: item.requiredCount,
        revenue: dollarsToMillions(item.revenueLinked),
        urgency: item.urgency,
      })) ?? [],
    [analysis],
  );

  const topScenario = analysis?.scenarioSimulations[0];

  return (
    <article className="border border-cyan/20 bg-panel/85 p-5 shadow-control backdrop-blur" data-testid="business-prediction-panel">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div className="max-w-3xl">
          <div className="flex items-center gap-2 text-xs uppercase text-cyan">
            <BriefcaseBusiness className="size-4" />
            <span>AI Business Prediction Engine</span>
            <span className="inline-flex items-center gap-1 text-mint">
              <Radio className="size-3" />
              {streamStatus}
            </span>
          </div>
          <h2 className="mt-2 text-2xl font-semibold text-white">Company future prediction AI</h2>
          <p className="mt-2 text-sm leading-6 text-slate-400">
            Revenue, churn, hiring, market pressure, profitability, company health, and executive scenarios are forecast from live operating signals.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button className="inline-flex items-center gap-2 border border-line bg-panel2 px-3 py-2 text-sm text-white hover:border-cyan/60" onClick={loadDefault} type="button">
            {loading ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />}
            Refresh
          </button>
          <button className="border border-line bg-panel2 px-3 py-2 text-sm text-white hover:border-cyan/60" onClick={() => void runScenario("revenue")} type="button">
            Revenue -20%
          </button>
          <button className="border border-line bg-panel2 px-3 py-2 text-sm text-white hover:border-cyan/60" onClick={() => void runScenario("churn")} type="button">
            Churn +15%
          </button>
          <button className="border border-line bg-panel2 px-3 py-2 text-sm text-white hover:border-cyan/60" onClick={() => void runScenario("freeze")} type="button">
            Hiring freeze
          </button>
        </div>
      </div>

      {error ? <p className="mt-4 border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-200">{error}</p> : null}
      {loading && !analysis ? <p className="mt-5 text-sm text-slate-400">Building executive forecast ensemble...</p> : null}

      {analysis ? (
        <>
          <section className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-6">
            <Metric label="Next quarter" value={formatMoney(analysis.summary.predictedNextQuarterRevenue)} />
            <Metric label="Annual forecast" value={formatMoney(analysis.summary.annualRevenueForecast)} />
            <Metric label="Growth" value={`${analysis.summary.revenueGrowthRate}%`} />
            <Metric label="Churn risk" value={`${analysis.summary.averageChurnProbability}%`} />
            <Metric label="Hiring need" value={String(analysis.summary.hiringNeeded)} />
            <Metric label="Health" value={`${analysis.companyHealthForecast.score}/100`} />
          </section>

          <section className="mt-5 grid gap-4 xl:grid-cols-[1.35fr_0.95fr]">
            <div className="min-h-80 border border-line/70 bg-void/35 p-4">
              <div className="mb-3 flex items-center justify-between gap-3">
                <span className="text-xs uppercase text-slate-500">Revenue forecast</span>
                <span className="text-xs text-mint">{Math.round(analysis.summary.forecastConfidence * 100)}% confidence</span>
              </div>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={revenueData}>
                    <CartesianGrid stroke="#233047" strokeDasharray="3 3" />
                    <XAxis dataKey="month" stroke="#64748b" fontSize={11} />
                    <YAxis stroke="#64748b" fontSize={11} tickFormatter={(value) => `$${value}M`} />
                    <Tooltip contentStyle={{ background: "#0b1220", border: "1px solid #1f2a44", color: "#e2e8f0" }} />
                    <Area type="monotone" dataKey="upper" stroke="transparent" fill="#1D9BF0" fillOpacity={0.08} />
                    <Area type="monotone" dataKey="lower" stroke="transparent" fill="#0B1220" fillOpacity={0.9} />
                    <Line type="monotone" dataKey="revenue" stroke="#7CF0A6" strokeWidth={2} dot={false} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="border border-line/70 bg-void/35 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-slate-500">
                <ShieldAlert className="size-4 text-cyan" />
                <span>Market and scenario risk</span>
              </div>
              <div className="space-y-3">
                {analysis.marketRisks.map((risk) => (
                  <div key={risk.riskId} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex items-center justify-between gap-3">
                      <span className="text-sm font-medium text-white">{risk.category}</span>
                      <strong className="text-sm" style={{ color: risk.riskScore >= 58 ? "#F05D5E" : "#F6B44B" }}>
                        {risk.riskScore}%
                      </strong>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-500">{risk.strategicWarning}</p>
                  </div>
                ))}
              </div>
              {topScenario ? (
                <div className="mt-3 border border-cyan/25 bg-cyan/5 p-3">
                  <span className="text-xs uppercase text-cyan">Scenario</span>
                  <p className="mt-2 text-sm text-white">{topScenario.scenario}</p>
                  <p className="mt-1 text-xs text-slate-500">
                    {topScenario.successProbability}% success, {formatMoney(topScenario.financialImpact)} impact
                  </p>
                </div>
              ) : null}
            </div>
          </section>

          <section className="mt-4 grid gap-4 xl:grid-cols-3">
            <ChartBlock title="Client churn">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={churnData}>
                  <CartesianGrid stroke="#233047" strokeDasharray="3 3" />
                  <XAxis dataKey="name" stroke="#64748b" fontSize={10} />
                  <YAxis stroke="#64748b" fontSize={11} />
                  <Tooltip contentStyle={{ background: "#0b1220", border: "1px solid #1f2a44", color: "#e2e8f0" }} />
                  <Bar dataKey="churn">
                    {churnData.map((item) => (
                      <Cell key={item.name} fill={item.churn >= 60 ? "#F05D5E" : "#F6B44B"} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </ChartBlock>

            <ChartBlock title="Hiring demand">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={hiringData}>
                  <CartesianGrid stroke="#233047" strokeDasharray="3 3" />
                  <XAxis dataKey="department" stroke="#64748b" fontSize={10} />
                  <YAxis stroke="#64748b" fontSize={11} />
                  <Tooltip contentStyle={{ background: "#0b1220", border: "1px solid #1f2a44", color: "#e2e8f0" }} />
                  <Bar dataKey="required">
                    {hiringData.map((item) => (
                      <Cell key={item.department} fill={riskColor[item.urgency]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </ChartBlock>

            <div className="border border-line/70 bg-void/35 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-slate-500">
                <Users className="size-4 text-cyan" />
                <span>Executive recommendations</span>
              </div>
              <div className="space-y-3">
                {analysis.recommendations.slice(0, 4).map((item) => (
                  <div key={item.title} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex items-center justify-between gap-3">
                      <span className="text-sm font-medium text-white">{item.title}</span>
                      <span className="text-xs uppercase" style={{ color: riskColor[item.priority] }}>
                        {item.priority}
                      </span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-500">{item.action}</p>
                  </div>
                ))}
              </div>
            </div>
          </section>

          <section className="mt-4 grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
            <div className="border border-line/70 bg-void/35 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-slate-500">
                <TrendingUp className="size-4 text-cyan" />
                <span>Profitability pressure</span>
              </div>
              <div className="space-y-2">
                {analysis.projectProfitability.slice(0, 4).map((project) => (
                  <div key={project.projectId} className="grid gap-1 border border-line/60 bg-panel/60 p-3">
                    <div className="flex items-center justify-between gap-3">
                      <span className="text-sm text-white">{project.projectName}</span>
                      <span className="text-sm" style={{ color: riskColor[project.riskLevel] }}>
                        {project.roiPercent}%
                      </span>
                    </div>
                    <p className="text-xs text-slate-500">
                      {formatMoney(project.expectedRevenue)} revenue, {project.overrunProbability}% overrun risk
                    </p>
                  </div>
                ))}
              </div>
            </div>

            <div className="border border-cyan/20 bg-panel2/60 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
                <Bot className="size-4" />
                <span>AI Business Assistant</span>
              </div>
              <div className="flex flex-col gap-2 sm:flex-row">
                <input
                  className="min-h-10 flex-1 border border-line bg-void/80 px-3 text-sm text-white outline-none focus:border-cyan/60"
                  onChange={(event) => setQuestion(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") void askAssistant();
                  }}
                  value={question}
                />
                <button className="inline-flex items-center justify-center gap-2 border border-cyan/40 bg-cyan/10 px-4 py-2 text-sm text-white hover:bg-cyan/15" onClick={askAssistant} type="button">
                  {assistantLoading ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
                  Ask
                </button>
              </div>
              <div className="mt-4 border border-line/60 bg-void/50 p-3">
                <p className="text-sm leading-6 text-slate-200">
                  {assistant?.answer ??
                    `Top business risk: ${analysis.summary.topBusinessRisk}. Forecast confidence is ${Math.round(analysis.summary.forecastConfidence * 100)}%.`}
                </p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {(assistant?.citedEvidence ?? analysis.evidence.slice(0, 4)).map((item) => (
                    <span key={`${item.source}-${item.signal}`} className="border border-line/60 bg-panel px-2 py-1 text-xs text-slate-400">
                      {item.signal}: {item.value}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </section>
        </>
      ) : null}
    </article>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-line/70 bg-void/40 p-3">
      <span className="text-xs uppercase text-slate-500">{label}</span>
      <strong className="mt-2 block text-xl font-semibold text-white">{value}</strong>
    </div>
  );
}

function ChartBlock({ children, title }: { children: React.ReactNode; title: string }) {
  return (
    <div className="h-72 border border-line/70 bg-void/35 p-4">
      <span className="mb-3 block text-xs uppercase text-slate-500">{title}</span>
      <div className="h-56">{children}</div>
    </div>
  );
}

async function fetchJson(path: string, init?: RequestInit, timeoutMs = 45000): Promise<unknown> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(path, { ...init, signal: controller.signal });
    if (!response.ok) throw new Error(`Request failed: ${response.status}`);
    return await response.json();
  } finally {
    window.clearTimeout(timeout);
  }
}

function isBusinessPrediction(value: unknown): value is BusinessPredictionResponse {
  return Boolean(
    value &&
      typeof value === "object" &&
      "summary" in value &&
      "revenueForecast" in value &&
      Array.isArray((value as BusinessPredictionResponse).revenueForecast),
  );
}

function isBusinessAssistant(value: unknown): value is BusinessAssistantResponse {
  return Boolean(value && typeof value === "object" && "answer" in value && "confidence" in value);
}

function dollarsToMillions(value: number) {
  return Number((value / 1_000_000).toFixed(2));
}

function formatMoney(value: number) {
  const sign = value < 0 ? "-" : "";
  const absolute = Math.abs(value);
  if (absolute >= 1_000_000) return `${sign}$${(absolute / 1_000_000).toFixed(1)}M`;
  if (absolute >= 1_000) return `${sign}$${Math.round(absolute / 1_000)}K`;
  return `${sign}$${Math.round(absolute)}`;
}

function shortName(value: string) {
  return value.replace(/\b(Global|Group|Corporation|Company|Enterprises|Systems|Bank|Retail)\b/g, "").trim().slice(0, 14);
}
