"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type React from "react";
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
import {
  AlertTriangle,
  Bot,
  Brain,
  CircleDollarSign,
  Cpu,
  Globe2,
  Loader2,
  Radio,
  RefreshCw,
  Scale,
  Send,
  ShieldAlert,
  Sparkles,
  TrendingUp,
  Users,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import type {
  GlobalRiskAlert,
  GlobalRiskAssistantResponse,
  GlobalRiskLevel,
  GlobalRiskRecommendation,
  GlobalRiskScannerRequest,
  GlobalRiskScannerResponse,
} from "@/types/global-risk";

const riskTone: Record<GlobalRiskLevel, string> = {
  low: "border-mint/35 bg-mint/10 text-mint",
  medium: "border-cyan/35 bg-cyan/10 text-cyan",
  high: "border-amber/35 bg-amber/10 text-amber",
  critical: "border-rose/35 bg-rose/10 text-rose",
};

const defaultScan: GlobalRiskScannerRequest = {
  cycleName: "Realtime Global Risk Scanner Review",
  horizonDays: 365,
  companyIndustries: ["Enterprise AI Software", "Workforce Analytics", "Cybersecurity"],
  targetRegions: ["United States", "India", "Singapore", "UAE", "European Union"],
  events: [],
  useLiveSources: false,
};

const prompts = [
  "What global risks affect us?",
  "What competitor is our biggest threat?",
  "How will inflation affect revenue?",
  "What market trends should we monitor?",
  "What regulations may affect us next year?",
  "What cyber threats are relevant right now?",
];

export function GlobalRiskScannerPanel() {
  const [analysis, setAnalysis] = useState<GlobalRiskScannerResponse | null>(null);
  const [assistant, setAssistant] = useState<GlobalRiskAssistantResponse | null>(null);
  const [question, setQuestion] = useState(prompts[0]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [streamStatus, setStreamStatus] = useState("connecting");
  const [error, setError] = useState("");
  const manualUntil = useRef(0);

  const loadDefault = useCallback(async () => {
    setLoading(true);
    setError("");
    manualUntil.current = 0;
    try {
      const response = await fetch("/api/global-risk/scanner/default", { cache: "no-store" });
      if (!response.ok) throw new Error("Global risk scanner default failed");
      setAnalysis((await response.json()) as GlobalRiskScannerResponse);
      setStreamStatus((current) => (current === "connecting" ? "polling" : current));
    } catch {
      setError("Global Risk Scanner could not load external intelligence.");
    } finally {
      setLoading(false);
    }
  }, []);

  const scan = useCallback(async (useLiveSources = false) => {
    setRunning(true);
    setError("");
    manualUntil.current = Date.now() + 30000;
    try {
      const response = await fetch("/api/global-risk/scanner/scan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(toSnake({ ...defaultScan, useLiveSources })),
        cache: "no-store",
      });
      if (!response.ok) throw new Error("Global risk scan failed");
      setAnalysis((await response.json()) as GlobalRiskScannerResponse);
    } catch {
      setError("Global Risk Scanner could not complete the external risk scan.");
    } finally {
      setRunning(false);
    }
  }, []);

  const ask = useCallback(async (override?: string) => {
    const prompt = override ?? question;
    if (!prompt.trim()) return;
    setRunning(true);
    setError("");
    try {
      const response = await fetch("/api/global-risk/scanner/assistant", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: prompt, horizon_days: 365 }),
        cache: "no-store",
      });
      if (!response.ok) throw new Error("Global risk assistant failed");
      setAssistant((await response.json()) as GlobalRiskAssistantResponse);
    } catch {
      setError("Global Risk Assistant could not answer the external intelligence question.");
    } finally {
      setRunning(false);
    }
  }, [question]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadDefault();
      void ask(prompts[0]);
    }, 0);
    return () => window.clearTimeout(timer);
  }, [ask, loadDefault]);

  useEffect(() => {
    const source = new EventSource("/api/global-risk/scanner/stream");
    source.addEventListener("global_risk_scanner", (event) => {
      try {
        const payload = JSON.parse((event as MessageEvent).data) as GlobalRiskScannerResponse;
        if (Date.now() > manualUntil.current) setAnalysis(payload);
        setStreamStatus("live");
        setLoading(false);
      } catch {
        setStreamStatus((current) => (current === "live" ? "live" : "degraded"));
      }
    });
    source.onerror = () => setStreamStatus((current) => (current === "live" ? "live" : "degraded"));
    return () => source.close();
  }, []);

  const heatmap = useMemo(
    () =>
      analysis?.newsIntelligence.slice(0, 8).map((item) => ({
        name: item.title.split(" ").slice(0, 2).join(" "),
        risk: Math.round(item.riskScore),
        opportunity: Math.round(item.opportunityScore),
        relevance: Math.round(item.companyRelevance),
      })) ?? [],
    [analysis],
  );

  const forecast = useMemo(
    () =>
      analysis?.riskForecasts.map((item) => ({
        label: item.horizonLabel.replace("_", " "),
        risk: Math.round(item.riskScore),
        opportunity: Math.round(item.opportunityScore),
      })) ?? [],
    [analysis],
  );

  const impact = useMemo(
    () =>
      analysis?.impactPredictions.slice(0, 8).map((item) => ({
        name: item.title.split(" ").slice(0, 2).join(" "),
        revenue: Math.round(item.revenueImpactPercent),
        client: Math.round(item.clientImpactScore),
        operations: Math.round(item.operationalImpactScore),
      })) ?? [],
    [analysis],
  );

  return (
    <section data-testid="global-risk-scanner-panel" className="border border-line/80 bg-panel/85 p-5 shadow-control backdrop-blur">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2 text-xs uppercase text-cyan">
            <Globe2 className="size-4" />
            Real-Time Global Risk Scanner
          </div>
          <h2 className="mt-2 text-2xl font-semibold text-white">Enterprise external intelligence platform</h2>
          <p className="mt-2 max-w-4xl text-sm leading-6 text-slate-400">
            Converts global news, economic pressure, competitor activity, regulations, technology trends, cyber threats, supply chain risk, and geopolitical events into company-specific forecasts and actions.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button onClick={() => void loadDefault()} className="inline-flex items-center gap-2 border border-line bg-panel2 px-3 py-2 text-sm text-slate-300">
            <RefreshCw className="size-4" />
            Refresh
          </button>
          <button onClick={() => void scan(false)} className="inline-flex items-center gap-2 border border-cyan/40 bg-cyan/10 px-3 py-2 text-sm text-cyan">
            {running ? <Loader2 className="size-4 animate-spin" /> : <Radio className="size-4" />}
            Run scan
          </button>
        </div>
      </div>

      {error && !analysis ? <p className="mt-4 text-sm text-signal">{error}</p> : null}
      {loading && !analysis ? <p className="mt-5 text-sm text-slate-400">Scanning external intelligence, forecasting company impact, and routing alerts to executive agents...</p> : null}

      {analysis ? (
        <>
          <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-10">
            <Metric icon={Globe2} label="Events" value={String(analysis.summary.eventsAnalyzed)} />
            <Metric icon={AlertTriangle} label="High risk" value={String(analysis.summary.highRiskEvents)} />
            <Metric icon={ShieldAlert} label="Critical" value={String(analysis.summary.criticalAlerts)} />
            <Metric icon={CircleDollarSign} label="Economy" value={`${Math.round(analysis.summary.economicRiskScore)}%`} />
            <Metric icon={TrendingUp} label="Competitor" value={`${Math.round(analysis.summary.competitiveThreatScore)}%`} />
            <Metric icon={Scale} label="Regulatory" value={`${Math.round(analysis.summary.regulatoryRiskScore)}%`} />
            <Metric icon={Cpu} label="Tech upside" value={`${Math.round(analysis.summary.technologyOpportunityScore)}%`} />
            <Metric icon={ShieldAlert} label="Cyber" value={`${Math.round(analysis.summary.cyberThreatScore)}%`} />
            <Metric icon={Brain} label="Ready" value={`${Math.round(analysis.summary.productionReadinessScore)}%`} />
            <Metric icon={Radio} label="Stream" value={streamStatus} />
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[1.05fr_0.95fr]">
            <Panel title="Global risk heatmap" icon={Globe2}>
              <ResponsiveContainer width="100%" height={290}>
                <BarChart data={heatmap}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#263143" />
                  <XAxis dataKey="name" stroke="#94a3b8" tick={{ fontSize: 11 }} />
                  <YAxis stroke="#94a3b8" tick={{ fontSize: 11 }} />
                  <Tooltip contentStyle={{ background: "#101827", border: "1px solid #253047", color: "#e5edf7" }} />
                  <Bar dataKey="risk" fill="#FF3B6B" />
                  <Bar dataKey="opportunity" fill="#7CF0A6" />
                  <Bar dataKey="relevance" fill="#4DD5FF" />
                </BarChart>
              </ResponsiveContainer>
            </Panel>

            <Panel title="Executive intelligence assistant" icon={Bot}>
              <div className="flex flex-wrap gap-2">
                {prompts.slice(0, 4).map((prompt) => (
                  <button key={prompt} onClick={() => { setQuestion(prompt); void ask(prompt); }} className="border border-line/70 bg-panel/65 px-2 py-1 text-xs text-slate-300">
                    {prompt}
                  </button>
                ))}
              </div>
              <div className="mt-3 flex gap-2">
                <input value={question} onChange={(event) => setQuestion(event.target.value)} className="min-w-0 flex-1 border border-line bg-void px-3 py-2 text-sm text-white outline-none focus:border-cyan/60" />
                <button onClick={() => void ask()} className="inline-flex items-center gap-2 border border-cyan/40 bg-cyan/10 px-3 py-2 text-sm text-cyan">
                  {running ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
                  Ask
                </button>
              </div>
              {assistant ? (
                <div className="mt-4 border border-line/60 bg-void/35 p-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="text-xs uppercase text-cyan">{assistant.intent.replaceAll("_", " ")}</span>
                    <span className="text-xs text-slate-500">{Math.round(assistant.confidence * 100)}% confidence</span>
                  </div>
                  <p className="mt-2 text-sm leading-6 text-slate-200">{assistant.answer}</p>
                  <ul className="mt-3 space-y-2">
                    {assistant.recommendedActions.slice(0, 3).map((action) => (
                      <li key={action} className="text-xs leading-5 text-slate-400">{action}</li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </Panel>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-3">
            <Panel title="Risk forecast horizons" icon={TrendingUp}>
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={forecast}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#263143" />
                  <XAxis dataKey="label" stroke="#94a3b8" tick={{ fontSize: 11 }} />
                  <YAxis stroke="#94a3b8" tick={{ fontSize: 11 }} />
                  <Tooltip contentStyle={{ background: "#101827", border: "1px solid #253047", color: "#e5edf7" }} />
                  <Line type="monotone" dataKey="risk" stroke="#FF3B6B" strokeWidth={2} />
                  <Line type="monotone" dataKey="opportunity" stroke="#7CF0A6" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </Panel>
            <Panel title="Company impact predictions" icon={CircleDollarSign}>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={impact}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#263143" />
                  <XAxis dataKey="name" stroke="#94a3b8" tick={{ fontSize: 11 }} />
                  <YAxis stroke="#94a3b8" tick={{ fontSize: 11 }} />
                  <Tooltip contentStyle={{ background: "#101827", border: "1px solid #253047", color: "#e5edf7" }} />
                  <Bar dataKey="revenue" fill="#F6B44B" />
                  <Bar dataKey="client" fill="#4DD5FF" />
                  <Bar dataKey="operations" fill="#C084FC" />
                </BarChart>
              </ResponsiveContainer>
            </Panel>
            <Panel title="Live source adapters" icon={Radio}>
              <div className="space-y-2">
                {analysis.liveSourceAdapters.map((adapter) => (
                  <div key={adapter} className="border border-line/60 bg-void/35 p-2 text-xs leading-5 text-slate-300">{adapter}</div>
                ))}
              </div>
            </Panel>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
            <Panel title="Executive alerts" icon={AlertTriangle}>
              <div className="space-y-3">
                {analysis.alerts.slice(0, 6).map((alert) => <AlertRow key={alert.alertId} alert={alert} />)}
              </div>
            </Panel>
            <Panel title="Economic, regulatory, technology, and cyber intelligence" icon={Sparkles}>
              <div className="grid gap-3 lg:grid-cols-2">
                <MiniList title="Economic risk trends" rows={analysis.economicIntelligence.map((item) => `${item.indicator}: ${Math.round(item.riskScore)}% - ${item.predictedCompanyImpact}`)} />
                <MiniList title="Competitor threats" rows={analysis.competitorIntelligence.slice(0, 4).map((item) => `${item.competitor}: ${Math.round(item.threatScore)}% threat, churn +${Math.round(item.predictedClientChurnDelta)}%`)} />
                <MiniList title="Regulatory alerts" rows={analysis.regulatoryIntelligence.map((item) => `${item.region}: compliance ${Math.round(item.complianceRisk)}%, cost +${Math.round(item.costImpactPercent)}%`)} />
                <MiniList title="Cyber threat alerts" rows={analysis.cyberThreatIntelligence.slice(0, 4).map((item) => `${item.threat}: ${Math.round(item.threatScore)}%`)} />
              </div>
            </Panel>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-3">
            <Panel title="Executive recommendations" icon={Sparkles}>
              <div className="space-y-3">
                {analysis.recommendations.slice(0, 5).map((item) => <RecommendationRow key={item.recommendationId} item={item} />)}
              </div>
            </Panel>
            <Panel title="Digital twin integration" icon={Brain}>
              <div className="space-y-2">
                {analysis.digitalTwinSync.map((sync) => (
                  <div key={sync.twin} className="border border-line/60 bg-void/35 p-2">
                    <div className="flex items-center justify-between gap-3">
                      <span className="text-sm font-medium text-white">{sync.twin.replaceAll("_", " ")}</span>
                      <span className="text-xs text-cyan">{sync.status}</span>
                    </div>
                    <p className="mt-1 text-xs leading-5 text-slate-400">{sync.update}</p>
                  </div>
                ))}
              </div>
            </Panel>
            <Panel title="Global intelligence council" icon={Users}>
              <div className="space-y-2">
                {analysis.agentCouncil.map((agent) => (
                  <div key={agent.agent} className="border border-line/60 bg-void/35 p-2">
                    <div className="flex items-center justify-between gap-3">
                      <span className="text-sm font-medium text-white">{agent.agent}</span>
                      <span className="text-xs text-cyan">{Math.round(agent.confidence * 100)}%</span>
                    </div>
                    <p className="mt-1 text-xs leading-5 text-slate-400">{agent.recommendation}</p>
                  </div>
                ))}
              </div>
            </Panel>
          </div>

          <div className="mt-4 border border-cyan/30 bg-cyan/10 p-3 text-sm text-cyan">{analysis.finalVerdict}</div>
        </>
      ) : null}
    </section>
  );
}

function Panel({ title, icon: Icon, children }: { title: string; icon: LucideIcon; children: React.ReactNode }) {
  return (
    <div className="min-w-0 overflow-hidden border border-line/80 bg-panel2/70 p-4">
      <div className="mb-3 flex items-center gap-2 text-sm font-medium text-white">
        <Icon className="size-4 text-cyan" />
        {title}
      </div>
      {children}
    </div>
  );
}

function Metric({ icon: Icon, label, value }: { icon: LucideIcon; label: string; value: string }) {
  return (
    <div className="min-w-0 border border-line bg-void/45 p-3">
      <div className="flex items-center justify-between gap-2">
        <span className="truncate text-xs uppercase text-slate-500">{label}</span>
        <Icon className="size-4 shrink-0 text-cyan" />
      </div>
      <div className="mt-2 truncate text-lg font-semibold text-white">{value}</div>
    </div>
  );
}

function AlertRow({ alert }: { alert: GlobalRiskAlert }) {
  return (
    <div className="border border-line/60 bg-void/35 p-3">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="text-sm font-medium text-white">{alert.title}</div>
          <div className="mt-1 text-xs uppercase text-slate-500">{alert.category.replaceAll("_", " ")} - {alert.urgencyHours}h</div>
        </div>
        <span className={`shrink-0 border px-2 py-1 text-xs ${riskTone[alert.riskLevel]}`}>{alert.riskLevel}</span>
      </div>
      <p className="mt-2 text-xs leading-5 text-slate-400">{alert.recommendedAction}</p>
      <div className={alert.potentialRevenueImpact < 0 ? "mt-2 text-xs text-rose" : "mt-2 text-xs text-mint"}>
        Revenue impact {alert.potentialRevenueImpact > 0 ? "+" : ""}{Math.round(alert.potentialRevenueImpact)}%
      </div>
    </div>
  );
}

function RecommendationRow({ item }: { item: GlobalRiskRecommendation }) {
  return (
    <div className="border border-line/60 bg-void/35 p-3">
      <div className="flex items-center justify-between gap-3">
        <div className="text-sm font-medium text-white">{item.ownerAgent}</div>
        <span className={`border px-2 py-1 text-xs ${riskTone[item.priority]}`}>{item.priority}</span>
      </div>
      <p className="mt-2 text-sm leading-6 text-slate-200">{item.action}</p>
      <p className="mt-2 text-xs leading-5 text-slate-500">{item.expectedImpact}</p>
    </div>
  );
}

function MiniList({ title, rows }: { title: string; rows: string[] }) {
  return (
    <div className="border border-line/60 bg-void/35 p-3">
      <div className="text-sm font-medium text-white">{title}</div>
      <ul className="mt-2 space-y-2">
        {rows.slice(0, 4).map((row) => (
          <li key={row} className="text-xs leading-5 text-slate-400">{row}</li>
        ))}
      </ul>
    </div>
  );
}

function toSnake(value: unknown): unknown {
  if (Array.isArray(value)) return value.map((item) => toSnake(item));
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>).map(([key, nested]) => [
        key.replace(/[A-Z]/g, (letter) => `_${letter.toLowerCase()}`),
        toSnake(nested),
      ]),
    );
  }
  return value;
}
