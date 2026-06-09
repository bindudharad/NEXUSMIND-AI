"use client";

import {
  AlertTriangle,
  Bot,
  BriefcaseBusiness,
  Building2,
  Cpu,
  Globe2,
  Loader2,
  RefreshCw,
  Rocket,
  Search,
  Send,
  ShieldAlert,
  Sparkles,
  TrendingUp,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import type React from "react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type {
  CompetitiveAssistantResponse,
  CompetitiveIntelligenceResponse,
  CompetitiveRiskLevel,
} from "@/types/competitive-intelligence";

const riskColor: Record<CompetitiveRiskLevel, string> = {
  low: "#7CF0A6",
  medium: "#F6B44B",
  high: "#F05D5E",
  critical: "#FF3B6B",
};

export function CompetitiveIntelligencePanel() {
  const [analysis, setAnalysis] = useState<CompetitiveIntelligenceResponse | null>(null);
  const [assistant, setAssistant] = useState<CompetitiveAssistantResponse | null>(null);
  const [question, setQuestion] = useState("Show biggest competitor threat.");
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [assistantLoading, setAssistantLoading] = useState(false);
  const [streamStatus, setStreamStatus] = useState("connecting");
  const [error, setError] = useState("");
  const manualUntil = useRef(0);

  const loadDefault = useCallback(async () => {
    setLoading(true);
    setError("");
    manualUntil.current = 0;
    try {
      const payload = await fetchJson<CompetitiveIntelligenceResponse>("/api/competitive/intelligence/default");
      setAnalysis(payload);
      setStreamStatus((status) => (status === "connecting" ? "polling" : status));
    } catch {
      setError("Competitive intelligence war room could not refresh.");
    } finally {
      setLoading(false);
    }
  }, []);

  const runSurge = useCallback(async () => {
    setRunning(true);
    setError("");
    manualUntil.current = Date.now() + 30000;
    try {
      const payload = await fetchJson<CompetitiveIntelligenceResponse>("/api/competitive/intelligence/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(competitiveSurgePayload()),
      });
      setAnalysis(payload);
    } catch {
      setError("Competitive surge simulation could not complete.");
    } finally {
      setRunning(false);
    }
  }, []);

  const askAssistant = useCallback(async () => {
    if (!question.trim()) return;
    setAssistantLoading(true);
    try {
      const payload = await fetchJson<CompetitiveAssistantResponse>("/api/competitive/intelligence/assistant", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, horizon_months: 12 }),
      });
      setAssistant(payload);
    } catch {
      setAssistant({
        model: "Competitive AI Assistant",
        generatedAt: new Date().toISOString(),
        question,
        intent: "error",
        answer: "Competitive AI Assistant could not query the strategic war room.",
        confidence: 0,
        citedEvidence: [],
        competitors: [],
        recommendations: [],
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
      try {
        const response = await fetch("/api/competitive/intelligence/stream", { cache: "no-store", signal: controller.signal });
        const reader = response.body?.getReader();
        if (!reader) throw new Error("Missing competitive intelligence stream");
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
            if (dataLine && Date.now() > manualUntil.current) {
              setAnalysis(JSON.parse(dataLine.slice(6)) as CompetitiveIntelligenceResponse);
              setLoading(false);
            }
          }
        }
        setStreamStatus("ready");
      } catch {
        if (!controller.signal.aborted) setStreamStatus("fallback");
      }
    }

    const refreshTimer = window.setTimeout(() => {
      void loadDefault();
    }, 200);
    const streamTimer = window.setTimeout(() => {
      void connectStream();
    }, 9000);
    return () => {
      controller.abort();
      window.clearTimeout(refreshTimer);
      window.clearTimeout(streamTimer);
    };
  }, [loadDefault]);

  const threatChart = useMemo(
    () =>
      analysis?.riskScores.map((item) => ({
        name: shortName(item.competitor),
        threat: Math.round(item.threatScore),
        talent: Math.round(item.talentAcquisitionRisk),
        tech: Math.round(item.technologyRisk),
      })) ?? [],
    [analysis],
  );

  const comparisonChart = useMemo(
    () =>
      analysis?.comparison.map((item) => ({
        name: shortName(item.competitor),
        score: Math.round(item.overallScore),
      })) ?? [],
    [analysis],
  );

  const topRisk = analysis?.riskScores[0];

  return (
    <section className="border border-line/80 bg-panel/85 p-5 shadow-control backdrop-blur">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <ShieldAlert className="mt-1 size-5 text-cyan" />
          <div>
            <p className="text-xs uppercase text-cyan">AI Strategic War Room</p>
            <h2 className="text-xl font-semibold text-white">Competitive Intelligence System</h2>
            <p className="mt-1 max-w-3xl text-sm leading-6 text-slate-400">
              Monitors product launches, hiring velocity, technology adoption, market expansion, trend pressure, competitor comparisons, and executive response actions.
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button onClick={() => void loadDefault()} className="inline-flex items-center gap-2 border border-line bg-panel2 px-3 py-2 text-sm text-slate-300">
            <RefreshCw className="size-4" />
            Refresh
          </button>
          <button onClick={() => void runSurge()} className="inline-flex items-center gap-2 border border-cyan/40 bg-cyan/10 px-3 py-2 text-sm text-cyan">
            {running ? <Loader2 className="size-4 animate-spin" /> : <TrendingUp className="size-4" />}
            Run surge
          </button>
        </div>
      </div>

      {error ? <p className="mt-4 text-sm text-signal">{error}</p> : null}
      {loading ? <p className="mt-5 text-sm text-slate-400">Synchronizing competitor, product, hiring, technology, and market signals...</p> : null}

      {analysis ? (
        <>
          <div className="mt-5 grid gap-3 md:grid-cols-4 xl:grid-cols-8">
            <Stat label="Top threat" value={analysis.summary.topCompetitorThreat} />
            <Stat label="Avg threat" value={`${Math.round(analysis.summary.averageThreatScore)}%`} />
            <Stat label="Launches" value={String(analysis.summary.productLaunchesTracked)} />
            <Stat label="Hiring surge" value={String(analysis.summary.aggressiveHiringCompetitors)} />
            <Stat label="Tech tracked" value={String(analysis.summary.technologiesTracked)} />
            <Stat label="Markets" value={String(analysis.summary.marketsExpanding)} />
            <Stat label="Readiness" value={`${Math.round(analysis.summary.strategicReadinessScore)}%`} />
            <Stat label="Stream" value={streamStatus} />
          </div>

          {topRisk ? (
            <article className="mt-5 border border-cyan/25 bg-panel2/70 p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2 text-xs uppercase text-cyan">
                    <AlertTriangle className="size-4" />
                    <span>Highest competitor threat</span>
                  </div>
                  <h3 className="mt-2 text-lg font-semibold text-white">{topRisk.competitor}</h3>
                  <p className="mt-2 max-w-4xl text-sm leading-6 text-slate-300">
                    Primary threat: {topRisk.primaryThreat}. Market disruption {Math.round(topRisk.marketDisruptionRisk)}%, innovation risk {Math.round(topRisk.innovationRisk)}%, talent risk {Math.round(topRisk.talentAcquisitionRisk)}%.
                  </p>
                </div>
                <span className="border border-line bg-panel px-3 py-2 text-sm uppercase" style={{ color: riskColor[topRisk.threatLevel] }}>
                  {topRisk.threatLevel}
                </span>
              </div>
            </article>
          ) : null}

          <div className="mt-4 grid gap-4 xl:grid-cols-2">
            <ChartPanel title="Competitor threat heatmap" icon={ShieldAlert}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={threatChart} margin={{ left: -22, right: 8, top: 8, bottom: 0 }}>
                  <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                  <XAxis dataKey="name" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                  <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                  <Bar dataKey="threat" fill="#FF3B6B" radius={[3, 3, 0, 0]} />
                  <Bar dataKey="talent" fill="#F6B44B" radius={[3, 3, 0, 0]} />
                  <Bar dataKey="tech" fill="#2EE9D3" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </ChartPanel>

            <ChartPanel title="Company vs competitor scorecards" icon={Search}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={comparisonChart} margin={{ left: -22, right: 8, top: 8, bottom: 0 }}>
                  <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                  <XAxis dataKey="name" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                  <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                  <Bar dataKey="score" fill="#7CF0A6" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </ChartPanel>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[1fr_0.9fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={Rocket} label="Product launch tracker" />
              <div className="grid gap-3 md:grid-cols-2">
                {analysis.productLaunches.slice(0, 4).map((launch) => (
                  <SignalCard key={`${launch.competitor}-${launch.launchName}`} title={launch.launchName} label={launch.competitor} risk={launch.riskLevel}>
                    <p>{launch.impact}</p>
                    <p className="mt-2 text-slate-500">{launch.productStrategyShift}</p>
                  </SignalCard>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={BriefcaseBusiness} label="Hiring trend intelligence" />
              <div className="grid gap-3">
                {analysis.hiringTrends.slice(0, 3).map((trend) => (
                  <SignalCard key={trend.competitor} title={`${Math.round(trend.hiringGrowthPercent)}% hiring growth`} label={trend.competitor} risk={trend.riskLevel}>
                    <p>{trend.strategicInterpretation}</p>
                    <p className="mt-2 text-slate-500">Focus: {trend.focus}</p>
                  </SignalCard>
                ))}
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-3">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={Cpu} label="Technology adoption tracker" />
              <div className="grid gap-3">
                {analysis.technologyAdoption.slice(0, 3).map((item) => (
                  <div key={item.competitor} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex items-start justify-between gap-2">
                      <h3 className="text-sm font-medium text-white">{item.competitor}</h3>
                      <span className="text-xs text-cyan">{Math.round(item.adoptionScore)}</span>
                    </div>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {item.technologies.slice(0, 5).map((tech) => (
                        <span key={`${item.competitor}-${tech}`} className="border border-line/70 bg-void/50 px-2 py-1 text-xs text-slate-400">
                          {tech}
                        </span>
                      ))}
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-500">{item.strategicInsight}</p>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={Globe2} label="Market expansion map" />
              <div className="grid gap-3">
                {analysis.marketExpansions.slice(0, 3).map((item) => (
                  <div key={item.competitor} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex items-start justify-between gap-2">
                      <h3 className="text-sm font-medium text-white">{item.competitor}</h3>
                      <span className="text-xs uppercase" style={{ color: riskColor[item.potentialMarketThreat] }}>
                        {item.potentialMarketThreat}
                      </span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{item.strategicInterpretation}</p>
                    <p className="mt-2 text-xs text-slate-500">{item.regions.join(" / ")}</p>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={Sparkles} label="Industry trends" />
              <div className="grid gap-3">
                {analysis.industryTrends.slice(0, 3).map((trend) => (
                  <div key={trend.trend} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex items-start justify-between gap-2">
                      <h3 className="text-sm font-medium text-white">{trend.trend}</h3>
                      <span className="text-xs text-mint">{Math.round(trend.tractionScore)}</span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{trend.forecastImpact}</p>
                    <p className="mt-2 text-xs text-slate-500">{trend.likelyTimeHorizon}</p>
                  </div>
                ))}
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={Building2} label="Executive strategy recommendations" />
              <div className="grid gap-3">
                {analysis.recommendations.slice(0, 4).map((item) => (
                  <div key={item.title} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex items-start justify-between gap-3">
                      <h3 className="text-sm font-medium text-white">{item.title}</h3>
                      <span className="text-xs uppercase" style={{ color: riskColor[item.priority] }}>
                        {item.priority}
                      </span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-300">{item.action}</p>
                    <p className="mt-2 text-xs leading-5 text-slate-500">{item.expectedCompetitiveBenefit}</p>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-cyan/25 bg-panel2/65 p-4">
              <SectionTitle icon={Bot} label="Competitive AI Assistant" />
              <div className="flex gap-2">
                <input
                  value={question}
                  onChange={(event) => setQuestion(event.target.value)}
                  className="min-w-0 flex-1 border border-line bg-panel px-3 py-2 text-sm text-white outline-none focus:border-cyan"
                  placeholder="Ask about threats, launches, hiring, technology, expansion..."
                />
                <button onClick={() => void askAssistant()} className="inline-flex items-center gap-2 border border-cyan/40 bg-cyan/10 px-3 py-2 text-sm text-cyan">
                  {assistantLoading ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
                  Ask
                </button>
              </div>
              <div className="mt-3 border border-line/60 bg-panel/60 p-3">
                {assistant ? (
                  <>
                    <div className="flex items-center justify-between gap-3">
                      <span className="text-xs uppercase text-cyan">{assistant.intent}</span>
                      <span className="text-xs text-mint">{Math.round(assistant.confidence * 100)} confidence</span>
                    </div>
                    <p className="mt-2 text-sm leading-6 text-slate-300">{assistant.answer}</p>
                    <div className="mt-3 grid gap-2">
                      {assistant.citedEvidence.slice(0, 3).map((item) => (
                        <p key={item} className="text-xs leading-5 text-slate-500">{item}</p>
                      ))}
                    </div>
                  </>
                ) : (
                  <p className="text-sm leading-6 text-slate-400">Ask a strategic question to query the same competitor risk, launch, hiring, technology, and market-expansion engines used by the dashboard.</p>
                )}
              </div>
            </article>
          </div>
        </>
      ) : null}
    </section>
  );
}

function ChartPanel({ title, icon: Icon, children }: { title: string; icon: LucideIcon; children: React.ReactNode }) {
  return (
    <article className="border border-line/70 bg-panel2/65 p-4">
      <SectionTitle icon={Icon} label={title} />
      <div className="h-72">{children}</div>
    </article>
  );
}

function SectionTitle({ icon: Icon, label }: { icon: LucideIcon; label: string }) {
  return (
    <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
      <Icon className="size-4" />
      {label}
    </div>
  );
}

function SignalCard({
  title,
  label,
  risk,
  children,
}: {
  title: string;
  label: string;
  risk: CompetitiveRiskLevel;
  children: React.ReactNode;
}) {
  return (
    <div className="border border-line/60 bg-panel/60 p-3">
      <div className="flex items-start justify-between gap-2">
        <div>
          <h3 className="text-sm font-medium text-white">{title}</h3>
          <p className="mt-1 text-xs uppercase text-mint">{label}</p>
        </div>
        <span className="text-xs uppercase" style={{ color: riskColor[risk] }}>
          {risk}
        </span>
      </div>
      <div className="mt-2 text-xs leading-5 text-slate-400">{children}</div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-line/70 bg-panel2/70 p-3">
      <p className="text-xs uppercase text-slate-500">{label}</p>
      <p className="mt-1 truncate text-lg font-semibold text-white" title={value}>{value}</p>
    </div>
  );
}

async function fetchJson<T>(input: string, init: RequestInit = {}, timeoutMs = 45000): Promise<T> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(input, { ...init, cache: "no-store", signal: controller.signal });
    const payload = (await response.json()) as T;
    if (!response.ok) throw new Error("Competitive intelligence request failed");
    return payload;
  } finally {
    window.clearTimeout(timeout);
  }
}

function shortName(value: string) {
  return value
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .join(" ");
}

function competitiveSurgePayload() {
  return {
    horizon_months: 12,
    focus_markets: ["India", "Singapore", "UAE"],
    competitors: [
      {
        company_name: "HelixOps AI",
        industry: "Enterprise AI Operations",
        products: ["AI Workflow Automator", "Security Copilot", "Workforce Command Graph"],
        market_position: "AI-native challenger",
        revenue_estimate_millions: 210,
        employee_count: 860,
        technology_stack: ["Kubernetes", "Generative AI", "Multi-Agent Systems", "Qdrant", "Neo4j", "Kafka"],
        regions: ["India", "Singapore", "UAE"],
        job_roles: ["AI Engineer", "MLOps Engineer", "Security Analyst", "Enterprise Sales"],
        hiring_growth_percent: 64,
        product_launches_90d: 5,
        ai_mentions_30d: 180,
        funding_signal: 0.9,
        partnership_signal: 0.72,
        pricing_pressure: 0.61,
        customer_sentiment: 0.68,
        market_share_growth: 16,
        technology_adoption_score: 96,
        product_velocity_score: 94,
        recent_activities: [
          "Released agentic enterprise operations suite",
          "Opened APAC go-to-market pods",
          "Announced AI security partnership",
        ],
      },
      {
        company_name: "Apex Strategy Labs",
        industry: "Market Intelligence Software",
        products: ["Strategy Radar", "Market Expansion Model", "Pricing Intelligence"],
        market_position: "strategy analytics specialist",
        revenue_estimate_millions: 112,
        employee_count: 470,
        technology_stack: ["Generative AI", "Spark", "Kafka", "Market Graphs", "Python"],
        regions: ["Singapore", "Japan", "Australia", "India"],
        job_roles: ["Market Analyst", "AI Research Engineer", "Pricing Strategist"],
        hiring_growth_percent: 43,
        product_launches_90d: 4,
        ai_mentions_30d: 118,
        funding_signal: 0.62,
        partnership_signal: 0.58,
        pricing_pressure: 0.45,
        customer_sentiment: 0.53,
        market_share_growth: 11,
        technology_adoption_score: 88,
        product_velocity_score: 86,
        recent_activities: ["Expanded APAC channel partnership", "Hired pricing AI research pod"],
      },
    ],
  };
}
