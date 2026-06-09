"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type React from "react";
import {
  Area,
  AreaChart,
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
  Activity,
  AlertTriangle,
  Brain,
  Building2,
  CircleDollarSign,
  Gauge,
  GitBranch,
  Loader2,
  Radio,
  RefreshCw,
  Rocket,
  Send,
  Shield,
  Sparkles,
  Target,
  TrendingUp,
  Users,
} from "lucide-react";

import type {
  BoardroomAssistantResponse,
  BoardroomDashboardResponse,
  BoardroomSeverity,
  ExecutiveRecommendation,
  ExecutiveRiskItem,
} from "@/types/boardroom";

const severityColor: Record<BoardroomSeverity, string> = {
  low: "#7CF0A6",
  medium: "#F6B44B",
  high: "#F05D5E",
  critical: "#FF3B6B",
};

export function BoardroomDashboardPanel() {
  const [dashboard, setDashboard] = useState<BoardroomDashboardResponse | null>(null);
  const [assistant, setAssistant] = useState<BoardroomAssistantResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [assistantLoading, setAssistantLoading] = useState(false);
  const [error, setError] = useState("");
  const [streamStatus, setStreamStatus] = useState("connecting");
  const [question, setQuestion] = useState("Which risk should I solve first?");

  const loadDefault = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await fetchJson("/api/boardroom/default");
      if (!isBoardroom(payload)) throw new Error("Malformed boardroom payload");
      setDashboard(payload);
      setStreamStatus((status) => (status === "connecting" ? "polling" : status));
    } catch {
      setError("AI Boardroom Dashboard could not refresh executive intelligence.");
    } finally {
      setLoading(false);
    }
  }, []);

  const askAssistant = useCallback(async () => {
    setAssistantLoading(true);
    try {
      const payload = await fetchJson("/api/boardroom/assistant", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      if (isBoardroomAssistant(payload)) setAssistant(payload);
    } catch {
      setAssistant(null);
    } finally {
      setAssistantLoading(false);
    }
  }, [question]);

  useEffect(() => {
    const controller = new AbortController();

    async function connectStream() {
      try {
        const response = await fetch("/api/boardroom/stream", { cache: "no-store", signal: controller.signal });
        if (!response.ok) throw new Error("Boardroom stream failed");
        const reader = response.body?.getReader();
        if (!reader) throw new Error("Missing Boardroom stream");
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
            if (!dataLine) continue;
            const payload = JSON.parse(dataLine.slice(6));
            if (isBoardroom(payload)) {
              setDashboard(payload);
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
      void loadDefault();
      void askAssistant();
    }, 0);
    const streamRefresh = window.setTimeout(() => {
      void connectStream();
    }, 2600);
    return () => {
      controller.abort();
      window.clearTimeout(firstRefresh);
      window.clearTimeout(streamRefresh);
    };
  }, [askAssistant, loadDefault]);

  const financeSeries = useMemo(
    () =>
      dashboard?.financialPredictions.monthlyForecast.map((value, index) => ({
        month: `M${index + 1}`,
        revenue: Math.round(value / 1000),
      })) ?? [],
    [dashboard],
  );

  const healthSeries = useMemo(
    () =>
      dashboard?.companyHealth.historicalTrend.map((value, index) => ({
        cycle: `T${index + 1}`,
        health: Math.round(value),
      })) ?? [],
    [dashboard],
  );

  const deliverySeries = useMemo(
    () =>
      dashboard?.projects.deliveryForecast.map((value, index) => ({
        sprint: `S${index + 1}`,
        confidence: Math.round(value),
      })) ?? [],
    [dashboard],
  );

  return (
    <section data-testid="boardroom-dashboard-panel" className="border border-cyan/30 bg-panel/90 p-5 shadow-control backdrop-blur">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="max-w-5xl">
          <div className="flex flex-wrap items-center gap-3 text-xs uppercase text-cyan">
            <Brain className="size-4" />
            <span>AI Boardroom Dashboard</span>
            <span className="h-px w-8 bg-cyan/40" />
            <span>JARVIS for Companies</span>
          </div>
          <h2 className="mt-3 text-2xl font-semibold text-white">Real-time AI CEO copilot</h2>
          <p className="mt-2 text-sm leading-6 text-slate-400">
            Company health, risk aggregation, revenue forecasts, workforce status, cybersecurity, projects, clients, competitive threats, innovation signals, digital twin state, alerts, and executive actions.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button onClick={() => void loadDefault()} className="inline-flex items-center gap-2 border border-line bg-panel2 px-3 py-2 text-sm text-slate-300">
            <RefreshCw className="size-4" />
            Refresh
          </button>
          <span className="inline-flex items-center gap-2 border border-cyan/25 bg-cyan/10 px-3 py-2 text-sm text-cyan">
            <Radio className="size-4" />
            {streamStatus}
          </span>
        </div>
      </div>

      {error && !dashboard ? <p className="mt-4 text-sm text-signal">{error}</p> : null}
      {loading && !dashboard ? <p className="mt-5 text-sm text-slate-400">Aggregating executive telemetry across company health, risk, forecasts, digital twins, and live AI systems...</p> : null}

      {dashboard ? (
        <>
          <div className="mt-5 grid gap-3 md:grid-cols-4 xl:grid-cols-8">
            {dashboard.kpis.map((kpi) => (
              <KpiTile key={kpi.label} icon={iconForKpi(kpi.label)} label={kpi.label} value={kpi.value} score={kpi.score} status={kpi.status} />
            ))}
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[1.05fr_0.95fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={Gauge} label="Company Health Panel" />
              <div className="grid gap-4 lg:grid-cols-[0.8fr_1.2fr]">
                <div>
                  <p className="text-xs uppercase text-slate-500">Company Health</p>
                  <strong className="mt-2 block text-5xl font-semibold text-white">{Math.round(dashboard.companyHealth.score)}</strong>
                  <p className="mt-2 text-sm text-cyan">{dashboard.companyHealth.status} / {dashboard.companyHealth.trend}</p>
                  <div className="mt-4 grid gap-2">
                    {dashboard.companyHealth.drivers.map((driver) => (
                      <p key={driver} className="border border-line/60 bg-panel/60 p-2 text-xs text-slate-400">{driver}</p>
                    ))}
                  </div>
                </div>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={healthSeries} margin={{ left: -22, right: 8, top: 8, bottom: 0 }}>
                      <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                      <XAxis dataKey="cycle" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                      <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                      <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                      <Area type="monotone" dataKey="health" stroke="#2EE9D3" fill="#2EE9D3" fillOpacity={0.18} strokeWidth={2} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={AlertTriangle} label="Executive Risk Panel" />
              <div className="grid gap-3">
                {dashboard.executiveRisks.slice(0, 5).map((risk) => (
                  <RiskRow key={risk.riskId} risk={risk} />
                ))}
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[1fr_1fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={CircleDollarSign} label="Financial Prediction Panel" />
              <div className="grid gap-3 md:grid-cols-4">
                <Metric label="Next quarter" value={formatMoney(dashboard.financialPredictions.nextQuarterRevenue)} />
                <Metric label="Annual forecast" value={formatMoney(dashboard.financialPredictions.annualRevenueForecast)} />
                <Metric label="Profit forecast" value={formatMoney(dashboard.financialPredictions.profitForecast)} />
                <Metric label="Confidence" value={`${Math.round(dashboard.financialPredictions.forecastConfidence * 100)}%`} />
              </div>
              <div className="mt-4 h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={financeSeries} margin={{ left: -22, right: 8, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="month" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} formatter={(value) => [`$${value}K`, "Revenue"]} />
                    <Bar dataKey="revenue" fill="#2EE9D3" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                {dashboard.financialPredictions.forecastModels.map((model) => (
                  <span key={model} className="border border-line/60 bg-panel px-2 py-1 text-xs text-slate-400">{model}</span>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={Users} label="Employee Status Panel" />
              <div className="grid gap-3 md:grid-cols-3">
                <Metric label="Employee health" value={`${Math.round(dashboard.workforce.employeeHealthScore)}%`} />
                <Metric label="Attrition risk" value={`${Math.round(dashboard.workforce.attritionRisk)}%`} tone="risk" />
                <Metric label="Top innovator" value={dashboard.workforce.topInnovator} />
              </div>
              <div className="mt-4 grid gap-3 md:grid-cols-2">
                <SignalList title="Burnout hotspots" items={dashboard.workforce.burnoutHotspots} />
                <SignalList
                  title="Talent growth"
                  items={[
                    `${dashboard.workforce.hiddenTalentCount} hidden talent signals`,
                    `${dashboard.workforce.futureLeadersCount} future leader signals`,
                    `Productivity trend ${dashboard.workforce.productivityTrend.toFixed(1)}`,
                  ]}
                />
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-3">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={Shield} label="Cybersecurity Panel" />
              <Metric label="Security Score" value={`${Math.round(dashboard.cybersecurity.securityScore)}%`} />
              <div className="mt-3 grid gap-2">
                <RiskMeter label="Insider threat" value={dashboard.cybersecurity.insiderThreatRisk} />
                <RiskMeter label="Data leakage" value={dashboard.cybersecurity.dataLeakageRisk} />
              </div>
              <SignalList title={`${dashboard.cybersecurity.activeThreats} active threat signals`} items={dashboard.cybersecurity.suspiciousActivity.slice(0, 4)} />
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={Target} label="Project Intelligence Panel" />
              <div className="grid gap-3 md:grid-cols-2">
                <Metric label="Completion confidence" value={`${Math.round(dashboard.projects.completionConfidence)}%`} />
                <Metric label="Delivery risk" value={`${Math.round(dashboard.projects.deliveryRisk)}%`} tone="risk" />
              </div>
              <p className="mt-3 text-sm text-white">{dashboard.projects.highestRiskProject}</p>
              <div className="mt-3 h-36">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={deliverySeries} margin={{ left: -22, right: 8, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="sprint" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Line type="monotone" dataKey="confidence" stroke="#7CF0A6" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
              <SignalList title="Resource gaps" items={dashboard.projects.resourceGaps} />
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={Building2} label="Client Intelligence Panel" />
              <div className="grid gap-3 md:grid-cols-2">
                <Metric label="Client health" value={`${Math.round(dashboard.clients.averageClientHealth)}%`} />
                <Metric label="Churn risk" value={`${Math.round(dashboard.clients.churnRisk)}%`} tone="risk" />
              </div>
              <p className="mt-3 text-sm text-white">Highest risk: {dashboard.clients.highestChurnRiskClient}</p>
              <p className="mt-1 text-xs text-slate-500">Upsell opportunity: {formatMoney(dashboard.clients.upsellOpportunityRevenue)}</p>
              <SignalList title="Client actions" items={dashboard.clients.recommendedActions.slice(0, 4)} />
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[1fr_1fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={TrendingUp} label="Competitive Intelligence Panel" />
              <div className="grid gap-3 md:grid-cols-2">
                <Metric label="Threat score" value={`${Math.round(dashboard.competitive.threatScore)}%`} tone="risk" />
                <Metric label="Top threat" value={dashboard.competitive.topThreat} />
              </div>
              <div className="mt-4 grid gap-3 md:grid-cols-3">
                <SignalList title="Market trends" items={dashboard.competitive.marketTrends} />
                <SignalList title="Industry risks" items={dashboard.competitive.industryRisks} />
                <SignalList title="Opportunities" items={dashboard.competitive.strategicOpportunities} />
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={Sparkles} label="Innovation Panel" />
              <div className="grid gap-3 md:grid-cols-3">
                <Metric label="Hidden talent" value={String(dashboard.innovation.hiddenTalentCount)} />
                <Metric label="Future leaders" value={String(dashboard.innovation.futureLeadersCount)} />
                <Metric label="Skill growth" value={`${Math.round(dashboard.innovation.skillGrowthTrend)}%`} />
              </div>
              <div className="mt-4 grid gap-3 md:grid-cols-2">
                <SignalList title="Innovation champions" items={dashboard.innovation.innovationChampions} />
                <SignalList title="Promotion recommendations" items={dashboard.innovation.promotionRecommendations} />
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={GitBranch} label="Digital Twin Command Center" />
              <div className="grid gap-3 md:grid-cols-3">
                <Metric label="Twin status" value={dashboard.digitalTwin.companyTwinStatus} />
                <Metric label="Simulations" value={String(dashboard.digitalTwin.activeSimulations)} />
                <Metric label="Highest risk" value={dashboard.digitalTwin.highestRiskScenario} tone="risk" />
              </div>
              <div className="mt-4 grid gap-3 md:grid-cols-2">
                <SignalList title="Future forecasts" items={dashboard.digitalTwin.futureForecasts} />
                <SignalList title="Organizational status" items={dashboard.digitalTwin.organizationalStatus} />
              </div>
            </article>

            <article className="border border-cyan/25 bg-cyan/10 p-4">
              <SectionTitle icon={Brain} label="Executive AI Assistant" />
              <div className="flex flex-wrap gap-2">
                <input
                  value={question}
                  onChange={(event) => setQuestion(event.target.value)}
                  className="min-w-0 flex-1 border border-line bg-panel px-3 py-2 text-sm text-slate-200 outline-none"
                />
                <button onClick={() => void askAssistant()} className="inline-flex items-center gap-2 border border-cyan/40 bg-cyan/10 px-3 py-2 text-sm text-cyan">
                  {assistantLoading ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
                  Ask
                </button>
              </div>
              {assistant ? (
                <div className="mt-3 border border-line/60 bg-panel/70 p-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="text-xs uppercase text-cyan">{assistant.intent}</span>
                    <span className="text-xs text-slate-500">{Math.round(assistant.confidence * 100)}% confidence</span>
                  </div>
                  <p className="mt-2 text-sm leading-6 text-slate-300">{assistant.answer}</p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {assistant.citedPanels.map((panel) => (
                      <span key={panel} className="border border-line/60 bg-panel2 px-2 py-1 text-xs text-slate-400">{panel}</span>
                    ))}
                  </div>
                </div>
              ) : null}
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[1fr_1fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={AlertTriangle} label="Real-Time Alert System" />
              <div className="grid gap-3">
                {dashboard.alerts.slice(0, 6).map((alert) => (
                  <div key={alert.alertId} className="border-l-2 bg-panel/60 p-3" style={{ borderColor: severityColor[alert.severity] }}>
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <p className="text-sm font-semibold text-white">{alert.title}</p>
                      <span className="text-sm font-semibold" style={{ color: severityColor[alert.severity] }}>{Math.round(alert.probability)}%</span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{alert.recommendation}</p>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-cyan/25 bg-cyan/10 p-4">
              <SectionTitle icon={Rocket} label="Executive Recommendation Engine" />
              <div className="grid gap-3">
                {dashboard.recommendations.slice(0, 6).map((recommendation) => (
                  <RecommendationRow key={recommendation.recommendationId} recommendation={recommendation} />
                ))}
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-3 md:grid-cols-2">
            {dashboard.executiveSummary.map((line, index) => (
              <p key={`${line}-${index}`} className="border border-line/60 bg-panel2/60 p-3 text-sm leading-6 text-slate-300">{line}</p>
            ))}
          </div>
        </>
      ) : null}
    </section>
  );
}

function SectionTitle({ icon: Icon, label }: { icon: React.ComponentType<{ className?: string }>; label: string }) {
  return (
    <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
      <Icon className="size-4" />
      {label}
    </div>
  );
}

function KpiTile({
  icon: Icon,
  label,
  value,
  score,
  status,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
  score: number;
  status: string;
}) {
  return (
    <div className="border border-line/70 bg-panel2/70 p-3">
      <div className="flex items-center gap-2 text-xs uppercase text-slate-500">
        <Icon className="size-4 text-cyan" />
        <span>{label}</span>
      </div>
      <strong className="mt-2 block truncate text-xl font-semibold text-white">{value}</strong>
      <div className="mt-3 h-1 bg-black/30">
        <div className="h-full bg-cyan" style={{ width: `${Math.max(4, Math.min(100, score))}%` }} />
      </div>
      <p className="mt-2 text-[11px] uppercase text-slate-500">{status}</p>
    </div>
  );
}

function RiskRow({ risk }: { risk: ExecutiveRiskItem }) {
  return (
    <div className="border-l-2 bg-panel/65 p-3" style={{ borderColor: severityColor[risk.severity] }}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-white">{risk.title}</p>
          <p className="mt-1 text-xs text-slate-500">{risk.category} / {risk.affectedArea}</p>
        </div>
        <span className="text-sm font-semibold" style={{ color: severityColor[risk.severity] }}>{Math.round(risk.probability)}%</span>
      </div>
      <p className="mt-2 text-xs leading-5 text-slate-400">{risk.recommendation}</p>
    </div>
  );
}

function Metric({ label, value, tone = "normal" }: { label: string; value: string; tone?: "normal" | "risk" }) {
  return (
    <div className="border border-line/60 bg-panel/60 p-3">
      <p className="text-xs uppercase text-slate-500">{label}</p>
      <strong className={`mt-1 block truncate text-lg font-semibold ${tone === "risk" ? "text-signal" : "text-white"}`}>{value}</strong>
    </div>
  );
}

function RiskMeter({ label, value }: { label: string; value: number }) {
  const severity = value >= 82 ? "critical" : value >= 64 ? "high" : value >= 38 ? "medium" : "low";
  return (
    <div>
      <div className="flex items-center justify-between gap-2 text-xs text-slate-500">
        <span>{label}</span>
        <span style={{ color: severityColor[severity] }}>{Math.round(value)}%</span>
      </div>
      <div className="mt-1 h-1 bg-black/30">
        <div className="h-full" style={{ width: `${Math.max(4, Math.min(100, value))}%`, backgroundColor: severityColor[severity] }} />
      </div>
    </div>
  );
}

function SignalList({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="mt-3">
      <p className="mb-2 text-xs uppercase text-slate-500">{title}</p>
      <div className="grid gap-2">
        {items.slice(0, 5).map((item) => (
          <p key={item} className="border border-line/60 bg-panel/60 p-2 text-xs leading-5 text-slate-400">{item}</p>
        ))}
      </div>
    </div>
  );
}

function RecommendationRow({ recommendation }: { recommendation: ExecutiveRecommendation }) {
  return (
    <div className="border border-cyan/20 bg-panel/70 p-3">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <p className="text-sm font-semibold text-white">{recommendation.action}</p>
        <span className="text-sm font-semibold" style={{ color: severityColor[recommendation.priority] }}>{Math.round(recommendation.confidence * 100)}%</span>
      </div>
      <p className="mt-2 text-xs leading-5 text-slate-400">{recommendation.reason}</p>
      <p className="mt-2 text-[11px] uppercase text-slate-500">{recommendation.category} / {recommendation.expectedBenefit}</p>
    </div>
  );
}

function iconForKpi(label: string) {
  if (label.includes("Revenue")) return CircleDollarSign;
  if (label.includes("Employee")) return Users;
  if (label.includes("Security")) return Shield;
  if (label.includes("Project")) return Target;
  if (label.includes("Client")) return Building2;
  if (label.includes("Competitive")) return TrendingUp;
  if (label.includes("Innovation")) return Sparkles;
  return Activity;
}

async function fetchJson(input: string, init?: RequestInit): Promise<unknown> {
  const response = await fetch(input, { cache: "no-store", ...init });
  const text = await response.text();
  const payload = text ? (JSON.parse(text) as unknown) : {};
  if (!response.ok) throw new Error("Boardroom request failed");
  return payload;
}

function isBoardroom(value: unknown): value is BoardroomDashboardResponse {
  const candidate = value as Partial<BoardroomDashboardResponse> | null;
  return Boolean(
    candidate &&
      typeof candidate.model === "string" &&
      Array.isArray(candidate.kpis) &&
      Array.isArray(candidate.executiveRisks) &&
      candidate.companyHealth &&
      candidate.financialPredictions &&
      candidate.workforce &&
      candidate.cybersecurity &&
      candidate.projects &&
      candidate.clients &&
      candidate.competitive &&
      candidate.innovation &&
      candidate.digitalTwin &&
      candidate.summary,
  );
}

function isBoardroomAssistant(value: unknown): value is BoardroomAssistantResponse {
  const candidate = value as Partial<BoardroomAssistantResponse> | null;
  return Boolean(candidate && typeof candidate.answer === "string" && typeof candidate.intent === "string");
}

function formatMoney(value?: number) {
  if (typeof value !== "number") return "verifying";
  if (Math.abs(value) >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (Math.abs(value) >= 1_000) return `$${Math.round(value / 1_000)}K`;
  return `$${Math.round(value)}`;
}
