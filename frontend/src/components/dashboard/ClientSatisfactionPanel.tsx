"use client";

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
import {
  AlertTriangle,
  BarChart3,
  Bot,
  BriefcaseBusiness,
  CircleDollarSign,
  Gauge,
  Loader2,
  MessageSquareText,
  Radio,
  RefreshCw,
  Send,
  ShieldAlert,
  Target,
  TrendingDown,
  Users,
} from "lucide-react";

import type { ClientAssistantResponse, ClientRiskPriority, ClientSatisfactionResponse } from "@/types/client-satisfaction";

const priorityColor: Record<ClientRiskPriority, string> = {
  low: "#7CF0A6",
  medium: "#F6B44B",
  high: "#F05D5E",
  critical: "#FF3B6B",
};

export function ClientSatisfactionPanel() {
  const [analysis, setAnalysis] = useState<ClientSatisfactionResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [streamStatus, setStreamStatus] = useState("connecting");
  const [assistantQuestion, setAssistantQuestion] = useState("Which clients may pay late?");
  const [assistant, setAssistant] = useState<ClientAssistantResponse | null>(null);
  const [assistantLoading, setAssistantLoading] = useState(false);
  const manualScenarioUntil = useRef(0);

  const loadDefault = useCallback(async () => {
    setLoading(true);
    setError("");
    manualScenarioUntil.current = 0;
    try {
      const payload = await fetchJson("/api/client-satisfaction/predict", { cache: "no-store" });
      if (!isClientSatisfaction(payload)) throw new Error("Malformed client satisfaction payload");
      setAnalysis(payload);
      setStreamStatus((status) => (status === "connecting" ? "polling" : status));
    } catch {
      setError("Predictive Client Satisfaction AI could not refresh live client-health intelligence.");
    } finally {
      setLoading(false);
    }
  }, []);

  const simulateClientCrisis = useCallback(async () => {
    setLoading(true);
    setError("");
    manualScenarioUntil.current = Date.now() + 30000;
    try {
      const payload = await fetchJson(
        "/api/client-satisfaction/predict",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(buildClientSatisfactionScenario()),
          cache: "no-store",
        },
        60000,
      );
      if (!isClientSatisfaction(payload)) throw new Error("Malformed client satisfaction payload");
      setAnalysis(payload);
      setStreamStatus((status) => (status === "connecting" ? "polling" : status));
    } catch {
      setError("Predictive Client Satisfaction AI could not process the client-risk simulation.");
    } finally {
      setLoading(false);
    }
  }, []);

  const askAssistant = useCallback(async () => {
    if (!assistantQuestion.trim()) return;
    setAssistantLoading(true);
    try {
      const payload = await fetchJson(
        "/api/client-satisfaction/assistant",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question: assistantQuestion }),
          cache: "no-store",
        },
        45000,
      );
      if (!isClientAssistant(payload)) throw new Error("Malformed client assistant payload");
      setAssistant(payload);
    } catch {
      setAssistant({
        model: "AI Client Relationship Intelligence Assistant",
        generatedAt: new Date().toISOString(),
        question: assistantQuestion,
        intent: "error",
        answer: "AI Client Relationship Intelligence Assistant could not query the client-risk engine.",
        confidence: 0,
        citedClients: [],
        citedEvidence: [],
        recommendedActions: [],
        sourceSystems: [],
        storage: "",
      });
    } finally {
      setAssistantLoading(false);
    }
  }, [assistantQuestion]);

  useEffect(() => {
    const controller = new AbortController();

    async function connectStream() {
      let streamStarted = false;
      const fallback = window.setTimeout(() => {
        if (!streamStarted && !controller.signal.aborted) setStreamStatus("polling");
      }, 12000);
      try {
        const response = await fetch("/api/client-satisfaction/stream", { cache: "no-store", signal: controller.signal });
        if (!response.ok) throw new Error("Client satisfaction stream failed");
        const reader = response.body?.getReader();
        if (!reader) throw new Error("Missing client satisfaction stream");
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
            if (isClientSatisfaction(payload) && Date.now() > manualScenarioUntil.current) {
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

  const clientRiskData = useMemo(
    () =>
      analysis?.predictions.slice(0, 6).map((client) => ({
        name: shortName(client.clientName),
        health: Math.round(client.clientHealthScore),
        churn: Math.round(client.churnRisk),
        escalation: Math.round(client.escalationProbability),
      })) ?? [],
    [analysis],
  );

  const forecastData = useMemo(() => {
    const client = analysis?.predictions[0];
    if (!client) return [];
    return client.forecast.map((point) => ({
      day: `D${point.day}`,
      health: Math.round(point.clientHealthScore),
      churn: Math.round(point.churnRisk),
      escalation: Math.round(point.escalationProbability),
      delivery: Math.round(point.deliveryConfidence),
    }));
  }, [analysis]);

  const deliveryData = useMemo(
    () =>
      analysis?.deliveryRisks.slice(0, 6).map((client) => ({
        name: shortName(client.clientName),
        delay: Math.round(client.delayRisk),
        sla: Math.round(client.slaRisk),
        quality: Math.round(client.qualityRisk),
        resolution: Math.round(client.issueResolutionRisk),
      })) ?? [],
    [analysis],
  );

  return (
    <section data-testid="client-satisfaction-panel" className="border border-line/80 bg-panel/85 p-5 shadow-control backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <BriefcaseBusiness className="size-5 text-cyan" />
          <div>
            <p className="text-xs uppercase text-cyan">AI Client Relationship Intelligence</p>
            <h2 className="text-xl font-semibold text-white">Client health, churn, payment, project, sentiment, engagement, and revenue-opportunity forecasting</h2>
            <p className="mt-2 max-w-5xl text-sm text-slate-500">
              Client-health dashboard, churn predictions, payment-risk scores, project-risk analytics, communication-sentiment graphs, engagement analytics, opportunity pipeline, AI recommendations, and executive client assistant.
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button data-testid="refresh-client-satisfaction" onClick={() => void loadDefault()} className="inline-flex items-center gap-2 border border-line bg-panel2 px-3 py-2 text-sm text-slate-300">
            <RefreshCw className="size-4" />
            Refresh clients
          </button>
          <button data-testid="simulate-client-satisfaction" onClick={() => void simulateClientCrisis()} className="inline-flex items-center gap-2 border border-cyan/40 bg-cyan/10 px-3 py-2 text-sm text-cyan">
            {loading ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
            Simulate churn
          </button>
        </div>
      </div>

      {error && !analysis ? <p className="mt-4 text-sm text-signal">{error}</p> : null}
      {loading && !analysis ? <p className="mt-5 text-sm text-slate-400">Scoring client sentiment, delivery delay, SLA breaches, QA quality, issue resolution, escalation history, renewal risk, and executive sponsor engagement...</p> : null}

      {analysis ? (
        <>
          <div className="mt-5 grid gap-3 md:grid-cols-4 xl:grid-cols-8">
            <Stat label="Clients" value={String(analysis.summary.clientsAnalyzed)} />
            <Stat label="Health" value={`${Math.round(analysis.summary.averageClientHealthScore)}%`} />
            <Stat label="Churn" value={`${Math.round(analysis.summary.averageChurnRisk)}%`} tone={analysis.summary.averageChurnRisk >= 55 ? "risk" : "normal"} />
            <Stat label="Escalation" value={`${Math.round(analysis.summary.averageEscalationProbability)}%`} tone={analysis.summary.averageEscalationProbability >= 55 ? "risk" : "normal"} />
            <Stat label="High Risk" value={String(analysis.summary.highRiskClients)} tone={analysis.summary.highRiskClients > 0 ? "risk" : "normal"} />
            <Stat label="Revenue Risk" value={formatMoney(analysis.summary.revenueAtRisk)} tone={analysis.summary.revenueAtRisk > 1000000 ? "risk" : "normal"} />
            <Stat label="Top Risk" value={analysis.summary.highestRiskClient} tone={analysis.summary.highRiskClients > 0 ? "risk" : "normal"} />
            <Stat label="Payment Risk" value={String(analysis.summary.paymentRiskAccounts)} tone={analysis.summary.paymentRiskAccounts > 0 ? "risk" : "normal"} />
            <Stat label="Opportunity" value={formatMoney(analysis.summary.opportunityRevenue)} />
            <Stat label="Stream" value={streamStatus} />
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <PanelTitle icon={BarChart3} label="Churn-risk visualizations" />
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={clientRiskData} margin={{ left: -24, right: 8, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="name" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Bar dataKey="health" fill="#2EE9D3" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="churn" radius={[3, 3, 0, 0]}>
                      {clientRiskData.map((item) => (
                        <Cell key={item.name} fill={item.churn >= 70 ? "#FF3B6B" : item.churn >= 45 ? "#F6B44B" : "#7CF0A6"} />
                      ))}
                    </Bar>
                    <Bar dataKey="escalation" fill="#F05D5E" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </article>

            <article className="border border-cyan/25 bg-cyan/10 p-4">
              <PanelTitle icon={Gauge} label="Client-health dashboard" />
              <div className="grid gap-3">
                {analysis.predictions.slice(0, 3).map((client) => (
                  <div key={client.clientId} className="border border-cyan/20 bg-panel/70 p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="text-sm font-semibold text-white">{client.clientName}</span>
                      <span className="text-xs text-cyan">{Math.round(client.clientHealthScore)}% health</span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{client.projectName} / {client.sentimentLabel}</p>
                    <div className="mt-2 flex flex-wrap gap-2 text-xs text-slate-500">
                      <span>{Math.round(client.churnRisk)}% churn</span>
                      <span>{Math.round(client.escalationProbability)}% escalation</span>
                      <span>{formatMoney(client.revenueAtRisk)} at risk</span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-500">{client.riskDrivers.slice(0, 2).join(" / ")}</p>
                  </div>
                ))}
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[1fr_1fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <PanelTitle icon={TrendingDown} label={`Executive client insights: ${analysis.predictions[0]?.clientName ?? "Portfolio"}`} />
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={forecastData} margin={{ left: -24, right: 8, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="day" stroke="#64748b" tickLine={false} axisLine={false} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Line type="monotone" dataKey="health" stroke="#2EE9D3" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="churn" stroke="#FF3B6B" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="escalation" stroke="#F6B44B" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="delivery" stroke="#7CF0A6" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <PanelTitle icon={Radio} label="Delivery-risk analytics" />
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={deliveryData} margin={{ left: -24, right: 8, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="name" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Bar dataKey="delay" fill="#F6B44B" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="sla" fill="#FF3B6B" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="quality" fill="#F05D5E" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="resolution" fill="#64748b" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-3">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <PanelTitle icon={CircleDollarSign} label="Payment delay prediction" />
              <div className="grid gap-2">
                {analysis.paymentRisks.slice(0, 4).map((item) => (
                  <RiskCard
                    key={item.clientName}
                    title={item.clientName}
                    score={item.paymentDelayRisk}
                    priority={item.priority}
                    lines={[
                      `${Math.round(item.predictedDelayDays)} predicted delay days`,
                      `${Math.round(item.collectionRisk)}% collection risk`,
                      `${formatMoney(item.overdueInvoiceAmount)} overdue exposure`,
                    ]}
                  />
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <PanelTitle icon={Target} label="Project failure prediction" />
              <div className="grid gap-2">
                {analysis.projectRisks.slice(0, 4).map((item) => (
                  <RiskCard
                    key={`${item.clientName}-${item.projectName}`}
                    title={item.clientName}
                    score={item.projectFailureRisk}
                    priority={item.priority}
                    lines={[
                      item.projectName,
                      item.primaryCause,
                      `${Math.round(item.budgetOverrunRisk)}% budget risk`,
                    ]}
                  />
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <PanelTitle icon={Users} label="Client engagement analytics" />
              <div className="grid gap-2">
                {analysis.engagementAnalytics.slice(0, 4).map((item) => (
                  <div key={item.clientName} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-sm font-medium text-white">{item.clientName}</span>
                      <span className={`text-xs uppercase ${item.trend === "declining" ? "text-signal" : item.trend === "improving" ? "text-mint" : "text-cyan"}`}>{item.trend}</span>
                    </div>
                    <div className="mt-3 grid gap-2 sm:grid-cols-2">
                      <Meter label="Engagement" value={item.engagementScore} />
                      <Meter label="Meetings" value={item.meetingParticipation} />
                      <Meter label="Email speed" value={item.emailResponsiveness} />
                      <Meter label="Support pressure" value={item.supportPressure} risk />
                    </div>
                  </div>
                ))}
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[1fr_1fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <PanelTitle icon={BriefcaseBusiness} label="Opportunity pipeline" />
              <div className="grid gap-2">
                {analysis.opportunityPipeline.slice(0, 4).map((item) => (
                  <div key={`${item.clientName}-${item.opportunity}`} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="text-sm font-medium text-white">{item.clientName}</span>
                      <span className="text-xs text-mint">{Math.round(item.probability)}% / {formatMoney(item.potentialRevenue)}</span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{item.opportunity}</p>
                    <p className="mt-1 text-xs leading-5 text-slate-500">{item.rationale}</p>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <PanelTitle icon={Bot} label="AI client assistant" />
              <div className="flex gap-2">
                <input
                  value={assistantQuestion}
                  onChange={(event) => setAssistantQuestion(event.target.value)}
                  className="min-w-0 flex-1 border border-line bg-panel px-3 py-2 text-sm text-white outline-none focus:border-cyan"
                  aria-label="Client relationship question"
                />
                <button onClick={() => void askAssistant()} className="inline-flex items-center gap-2 border border-cyan/40 bg-cyan/10 px-3 py-2 text-sm text-cyan">
                  {assistantLoading ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
                  Ask
                </button>
              </div>
              <p className="mt-3 text-sm leading-6 text-slate-300">
                {assistant?.answer ?? "Ask which clients may leave, pay late, fail delivery, show negative sentiment, or have upsell potential."}
              </p>
              {assistant?.citedEvidence.length ? (
                <div className="mt-3 grid gap-2 md:grid-cols-2">
                  {assistant.citedEvidence.slice(0, 4).map((item) => (
                    <p key={item} className="border border-line/60 bg-panel/60 p-2 text-xs leading-5 text-slate-400">{item}</p>
                  ))}
                </div>
              ) : null}
            </article>
          </div>

          <div className="mt-5 grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <PanelTitle icon={AlertTriangle} label="Satisfaction heatmaps" />
              <div className="grid gap-2 sm:grid-cols-2">
                {analysis.heatmap.slice(0, 12).map((point) => (
                  <div key={`${point.clientName}-${point.metric}`} className="border-l-2 bg-panel/60 p-3" style={{ borderColor: priorityColor[point.priority] }}>
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold text-white">{point.clientName}</p>
                        <p className="mt-1 text-xs text-slate-500">{point.metric}</p>
                      </div>
                      <span className="text-sm font-semibold" style={{ color: priorityColor[point.priority] }}>{Math.round(point.score)}%</span>
                    </div>
                    <div className="mt-3 h-1.5 bg-black/30">
                      <div className="h-full" style={{ width: `${Math.round(point.score)}%`, backgroundColor: priorityColor[point.priority] }} />
                    </div>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <PanelTitle icon={MessageSquareText} label="Communication-sentiment graphs" />
              <div className="grid gap-2">
                {analysis.communicationSentiment.map((item) => (
                  <div key={item.clientName} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="text-sm font-medium text-white">{item.clientName}</span>
                      <span className="text-xs uppercase text-cyan">{item.label}</span>
                    </div>
                    <div className="mt-3 grid gap-2 sm:grid-cols-3">
                      <Meter label="Sentiment" value={(item.sentimentScore + 1) * 50} />
                      <Meter label="Negativity" value={item.negativityRisk} risk />
                      <Meter label="Trust risk" value={item.trustRisk} risk />
                    </div>
                  </div>
                ))}
              </div>
            </article>
          </div>

          <div className="mt-5 grid gap-4 xl:grid-cols-[1fr_1fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <PanelTitle icon={ShieldAlert} label="Escalation-warning panels" />
              <div className="grid gap-2">
                {analysis.alerts.map((alert) => (
                  <div key={`${alert.title}-${alert.probability}`} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="text-sm font-medium text-white">{alert.title}</span>
                      <span className="text-xs uppercase" style={{ color: priorityColor[alert.severity] }}>{alert.severity} / {Math.round(alert.probability)}%</span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{alert.impact}</p>
                    <p className="mt-1 text-xs leading-5 text-slate-500">{alert.recommendation}</p>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <PanelTitle icon={BriefcaseBusiness} label="AI recovery recommendation widgets" />
              <div className="grid gap-2">
                {analysis.recommendations.map((item) => (
                  <div key={item.title} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="text-sm font-medium text-white">{item.title}</span>
                      <span className="text-xs uppercase" style={{ color: priorityColor[item.priority] }}>{item.category} / {Math.round(item.confidence * 100)}%</span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{item.action}</p>
                    <p className="mt-1 text-xs leading-5 text-slate-500">{item.expectedImpact}</p>
                  </div>
                ))}
              </div>
            </article>
          </div>

          <article className="mt-5 border border-line/70 bg-panel2/65 p-4">
            <div className="text-xs uppercase text-cyan">Executive client insights</div>
            <div className="mt-3 grid gap-2 md:grid-cols-2">
              {analysis.executiveInsights.map((insight) => (
                <p key={insight} className="border border-line/60 bg-panel/60 p-3 text-xs leading-5 text-slate-400">{insight}</p>
              ))}
            </div>
            <p className="mt-3 border border-line/60 bg-panel/60 p-3 text-xs leading-5 text-slate-500">
              Models: {analysis.model}. Sources: {analysis.sourceSystems.join(", ")}.
            </p>
          </article>
        </>
      ) : null}
    </section>
  );
}

function PanelTitle({ icon: Icon, label }: { icon: typeof BriefcaseBusiness; label: string }) {
  return (
    <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
      <Icon className="size-4" />
      {label}
    </div>
  );
}

function Stat({ label, value, tone = "normal" }: { label: string; value: string; tone?: "normal" | "risk" }) {
  return (
    <div className="border border-line/70 bg-panel2/65 p-3">
      <p className="text-xs uppercase text-slate-500">{label}</p>
      <strong className={`mt-2 block truncate text-lg font-semibold ${tone === "risk" ? "text-signal" : "text-white"}`}>{value}</strong>
    </div>
  );
}

function Meter({ label, value, risk = false }: { label: string; value: number; risk?: boolean }) {
  const normalized = Math.max(0, Math.min(100, value));
  const color = risk ? (normalized >= 70 ? "#FF3B6B" : normalized >= 45 ? "#F6B44B" : "#7CF0A6") : "#2EE9D3";
  return (
    <div>
      <div className="mb-1 flex items-center justify-between gap-2 text-[11px] uppercase text-slate-500">
        <span>{label}</span>
        <span>{Math.round(normalized)}%</span>
      </div>
      <div className="h-1.5 bg-black/30">
        <div className="h-full" style={{ width: `${Math.round(normalized)}%`, backgroundColor: color }} />
      </div>
    </div>
  );
}

function RiskCard({ title, score, priority, lines }: { title: string; score: number; priority: ClientRiskPriority; lines: string[] }) {
  return (
    <div className="border-l-2 bg-panel/60 p-3" style={{ borderColor: priorityColor[priority] }}>
      <div className="flex items-start justify-between gap-3">
        <span className="text-sm font-medium text-white">{title}</span>
        <span className="text-sm font-semibold" style={{ color: priorityColor[priority] }}>{Math.round(score)}%</span>
      </div>
      <div className="mt-2 grid gap-1">
        {lines.map((line) => (
          <p key={line} className="text-xs leading-5 text-slate-500">{line}</p>
        ))}
      </div>
    </div>
  );
}

function formatMoney(value: number) {
  if (value >= 1000000) return `$${(value / 1000000).toFixed(1)}M`;
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(value);
}

function shortName(value: string) {
  return value.split(" ")[0] ?? value;
}

async function fetchJson(input: string, init: RequestInit, timeoutMs = 30000): Promise<unknown> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(input, { ...init, signal: controller.signal });
    if (!response.ok) throw new Error("Client satisfaction request failed");
    return await response.json();
  } finally {
    window.clearTimeout(timeout);
  }
}

function isClientSatisfaction(value: unknown): value is ClientSatisfactionResponse {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Partial<ClientSatisfactionResponse>;
  return Boolean(
    candidate.model
      && candidate.summary?.highestRiskClient
      && Array.isArray(candidate.predictions)
      && Array.isArray(candidate.heatmap)
      && Array.isArray(candidate.paymentRisks)
      && Array.isArray(candidate.projectRisks)
      && Array.isArray(candidate.opportunityPipeline),
  );
}

function isClientAssistant(value: unknown): value is ClientAssistantResponse {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Partial<ClientAssistantResponse>;
  return Boolean(candidate.model && candidate.intent && candidate.answer && Array.isArray(candidate.citedEvidence));
}

function buildClientSatisfactionScenario() {
  return {
    cycle_name: "Strategic Client Satisfaction Simulation",
    horizon_days: 60,
    realtime: true,
    clients: [
      {
        client_id: "client-stable-bank",
        client_name: "Stable Bank",
        industry: "Financial Services",
        account_tier: "global",
        project_name: "Risk Data Platform",
        contract_value: 6200000,
        renewal_days: 160,
        delivery_delay_days: 1,
        missed_milestones: 0,
        sla_breach_count: 0,
        bug_frequency: 0.08,
        production_incidents: 0,
        qa_pass_rate: 0.94,
        rework_ratio: 0.06,
        issue_resolution_hours: 12,
        escalation_count: 0,
        communication_sentiment: 0.52,
        interaction_frequency: 0.86,
        feedback_score: 0.9,
        nps_delta: 10,
        delivery_consistency: 0.91,
        relationship_tenure_months: 48,
        executive_sponsor_engagement: 0.88,
        open_critical_issues: 0,
        meeting_transcripts: ["The release is stable, communication is clear, and our team is confident in the migration plan."],
        email_threads: ["Thanks for resolving questions quickly and keeping the roadmap predictable."],
      },
      {
        client_id: "client-crisis-retail",
        client_name: "Crisis Retail",
        industry: "Retail",
        account_tier: "enterprise",
        project_name: "Commerce Replatform",
        contract_value: 3600000,
        renewal_days: 45,
        delivery_delay_days: 21,
        missed_milestones: 6,
        sla_breach_count: 5,
        bug_frequency: 0.58,
        production_incidents: 5,
        qa_pass_rate: 0.55,
        rework_ratio: 0.48,
        issue_resolution_hours: 144,
        escalation_count: 6,
        communication_sentiment: -0.44,
        interaction_frequency: 0.32,
        feedback_score: 0.34,
        nps_delta: -35,
        delivery_consistency: 0.42,
        relationship_tenure_months: 16,
        executive_sponsor_engagement: 0.28,
        open_critical_issues: 5,
        meeting_transcripts: [
          "The client is frustrated because the deployment was delayed again and the checkout defect remains unresolved.",
          "This requires executive escalation. Trust is dropping and the same SLA breach keeps repeating.",
        ],
        email_threads: ["We are disappointed with the missed milestone and need an immediate recovery plan."],
      },
    ],
  };
}
