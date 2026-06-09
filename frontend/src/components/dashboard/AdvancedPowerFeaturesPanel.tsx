"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Bar, BarChart, CartesianGrid, Cell, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { BrainCircuit, Bot, GitBranch, Loader2, Radio, RefreshCw, SearchCheck, Send, ShieldCheck, Zap } from "lucide-react";

import type {
  GNNTeamRelationResponse,
  ManagerAssistantResponse,
  PowerFeatureAuditResponse,
  PowerSeverity,
  RealtimeAnalyticsResponse,
  XAIExplanationResponse,
} from "@/types/power-features";

type SnakeRecord = Record<string, unknown>;

const severityColor: Record<PowerSeverity, string> = {
  low: "#7CF0A6",
  medium: "#2EE9D3",
  high: "#F6B44B",
  critical: "#FF3B6B",
};

export function AdvancedPowerFeaturesPanel() {
  const [audit, setAudit] = useState<PowerFeatureAuditResponse | null>(null);
  const [realtime, setRealtime] = useState<RealtimeAnalyticsResponse | null>(null);
  const [xai, setXai] = useState<XAIExplanationResponse | null>(null);
  const [gnn, setGnn] = useState<GNNTeamRelationResponse | null>(null);
  const [assistant, setAssistant] = useState<ManagerAssistantResponse | null>(null);
  const [question, setQuestion] = useState("Why is Team Alpha productivity decreasing?");
  const [streamStatus, setStreamStatus] = useState("connecting");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadPowerLayer = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [auditRes, realtimeRes, xaiRes, gnnRes, assistantRes] = await Promise.all([
        fetch("/api/power/audit", { cache: "no-store" }),
        fetch("/api/power/realtime/snapshot", { cache: "no-store" }),
        fetch("/api/power/xai/explain", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ target: "burnout", scenario: "crisis" }),
          cache: "no-store",
        }),
        fetch("/api/power/gnn/team-relations", { cache: "no-store" }),
        fetch("/api/power/assistant/ask", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question }),
          cache: "no-store",
        }),
      ]);
      if (![auditRes, realtimeRes, xaiRes, gnnRes, assistantRes].every((response) => response.ok)) {
        throw new Error("Power layer failed");
      }
      setAudit((await auditRes.json()) as PowerFeatureAuditResponse);
      setRealtime((await realtimeRes.json()) as RealtimeAnalyticsResponse);
      setXai((await xaiRes.json()) as XAIExplanationResponse);
      setGnn((await gnnRes.json()) as GNNTeamRelationResponse);
      setAssistant((await assistantRes.json()) as ManagerAssistantResponse);
    } catch {
      setError("Advanced AI power layer could not complete verification.");
    } finally {
      setLoading(false);
    }
  }, [question]);

  const askAssistant = useCallback(async () => {
    setError("");
    try {
      const response = await fetch("/api/power/assistant/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
        cache: "no-store",
      });
      if (!response.ok) throw new Error("Manager assistant failed");
      setAssistant((await response.json()) as ManagerAssistantResponse);
    } catch {
      setError("Manager assistant could not answer with live context.");
    }
  }, [question]);

  useEffect(() => {
    const controller = new AbortController();

    async function connectStream() {
      try {
        const response = await fetch("/api/power/realtime/stream", { cache: "no-store", signal: controller.signal });
        const reader = response.body?.getReader();
        if (!reader) throw new Error("Missing power stream");
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
              setRealtime(toCamel<RealtimeAnalyticsResponse>(JSON.parse(dataLine.slice(6))));
            }
          }
        }
        setStreamStatus("polling");
      } catch {
        if (!controller.signal.aborted) setStreamStatus("polling");
      }
    }

    const firstRefresh = window.setTimeout(() => {
      void loadPowerLayer();
    }, 3200);
    const streamRefresh = window.setTimeout(() => {
      void connectStream();
    }, 8000);
    return () => {
      controller.abort();
      window.clearTimeout(firstRefresh);
      window.clearTimeout(streamRefresh);
    };
  }, [loadPowerLayer]);

  const kpiChart = useMemo(
    () =>
      realtime?.kpis.map((kpi) => ({
        name: kpi.label.replace(" probability", "").replace("Live ", ""),
        value: Math.round(kpi.value),
        severity: kpi.severity,
      })) ?? [],
    [realtime],
  );

  const attributionChart = useMemo(
    () =>
      xai?.shapValues.slice(0, 6).map((item) => ({
        feature: item.feature.replace(/_/g, " "),
        contribution: Number(item.contribution.toFixed(2)),
        direction: item.direction,
      })) ?? [],
    [xai],
  );

  const gnnChart = useMemo(
    () =>
      gnn?.nodes.slice(0, 6).map((node) => ({
        name: node.name.split(" ")[0],
        burnout: Math.round(node.burnoutSpreadRisk),
        influence: Math.round(node.leadershipInfluence),
        conflict: Math.round(node.conflictProjection),
      })) ?? [],
    [gnn],
  );

  return (
    <section className="border border-purple-400/25 bg-panel/85 p-5 shadow-control backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <BrainCircuit className="size-5 text-purple-300" />
          <div>
            <p className="text-xs uppercase text-purple-300">Advanced AI Power Features</p>
            <h2 className="text-xl font-semibold text-white">Realtime analytics, XAI, GraphSAGE relations, and manager assistant</h2>
          </div>
        </div>
        <button onClick={() => void loadPowerLayer()} className="inline-flex items-center gap-2 border border-line bg-panel2 px-3 py-2 text-sm text-slate-300">
          {loading ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />}
          Verify power layer
        </button>
      </div>

      {error ? <p className="mt-4 text-sm text-signal">{error}</p> : null}
      {loading ? <p className="mt-5 text-sm text-slate-400">Validating live analytics, explainability, graph neural inference, and manager reasoning...</p> : null}

      {audit && realtime && xai && gnn && assistant ? (
        <>
          <div className="mt-5 grid gap-3 md:grid-cols-5">
            <Stat label="Power score" value={`${Math.round(audit.summary.powerScore)}%`} tone="text-purple-300" />
            <Stat label="Ready checks" value={`${audit.summary.ready}/${audit.summary.total}`} tone="text-mint" />
            <Stat label="Stream" value={streamStatus} tone="text-cyan" />
            <Stat label="GNN MAE" value={String(gnn.trainingMetrics.mae ?? "n/a")} tone="text-amber" />
            <Stat label="XAI confidence" value={`${Math.round(xai.confidence * 100)}%`} tone="text-cyan" />
          </div>

          <div className="mt-5 border border-purple-400/25 bg-purple-400/10 p-4">
            <div className="flex items-start gap-3">
              <ShieldCheck className="mt-0.5 size-5 text-purple-300" />
              <div>
                <p className="text-xs uppercase text-purple-300">Power verdict</p>
                <p className="mt-2 text-sm leading-6 text-slate-300">{audit.verdict}</p>
              </div>
            </div>
          </div>

          <div className="mt-5 grid gap-4 xl:grid-cols-[1fr_1fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
                <Radio className="size-4" />
                Realtime analytics stream
              </div>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={kpiChart} margin={{ left: -18, right: 8, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="name" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Bar dataKey="value" radius={[3, 3, 0, 0]}>
                      {kpiChart.map((entry) => (
                        <Cell key={entry.name} fill={severityColor[entry.severity]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="mt-3 grid gap-2">
                {realtime.events.slice(0, 3).map((event) => (
                  <p key={event.eventId} className="border border-line/50 bg-panel/60 px-3 py-2 text-xs leading-5 text-slate-400">
                    <span style={{ color: severityColor[event.severity] }}>{event.title}</span> — {event.message}
                  </p>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-mint">
                <SearchCheck className="size-4" />
                Explainable AI reasoning
              </div>
              <p className="text-sm leading-6 text-slate-300">{xai.explanation}</p>
              <div className="mt-4 h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={attributionChart} layout="vertical" margin={{ left: 44, right: 8, top: 0, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis type="number" stroke="#64748b" tickLine={false} axisLine={false} />
                    <YAxis type="category" dataKey="feature" width={118} stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Bar dataKey="contribution" radius={[0, 3, 3, 0]}>
                      {attributionChart.map((entry) => (
                        <Cell key={entry.feature} fill={entry.direction === "reduces_risk" ? "#7CF0A6" : "#FF3B6B"} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="mt-3 grid gap-2">
                {xai.counterfactuals.slice(0, 2).map((item) => (
                  <p key={item.action} className="border border-line/50 bg-panel/60 px-3 py-2 text-xs leading-5 text-slate-400">
                    {item.action} Impact: {item.impact.toFixed(1)} pts.
                  </p>
                ))}
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-amber">
                <GitBranch className="size-4" />
                GraphSAGE team relations
              </div>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={gnnChart} margin={{ left: -18, right: 10, top: 10, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="name" stroke="#64748b" tickLine={false} axisLine={false} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Line type="monotone" dataKey="burnout" stroke="#FF3B6B" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="influence" stroke="#7CF0A6" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="conflict" stroke="#F6B44B" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
              <div className="mt-3 grid gap-2">
                {gnn.propagationAlerts.slice(0, 3).map((alert) => (
                  <p key={alert} className="border border-line/50 bg-panel/60 px-3 py-2 text-xs leading-5 text-slate-400">
                    {alert}
                  </p>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
                <Bot className="size-4" />
                Generative manager assistant
              </div>
              <div className="flex flex-col gap-2 sm:flex-row">
                <input
                  value={question}
                  onChange={(event) => setQuestion(event.target.value)}
                  className="min-w-0 flex-1 border border-line bg-void px-3 py-2 text-sm text-slate-200 outline-none focus:border-cyan/60"
                />
                <button onClick={() => void askAssistant()} className="inline-flex items-center justify-center gap-2 border border-cyan/40 bg-cyan/10 px-3 py-2 text-sm text-cyan">
                  <Send className="size-4" />
                  Ask
                </button>
              </div>
              <div className="mt-4 border border-cyan/25 bg-cyan/10 p-4">
                <p className="text-sm leading-6 text-slate-200">{assistant.answer}</p>
                <p className="mt-3 text-xs leading-5 text-slate-400">{assistant.riskSummary}</p>
              </div>
              <div className="mt-3 grid gap-2">
                {assistant.recommendedActions.slice(0, 3).map((action) => (
                  <p key={action} className="border border-line/50 bg-panel/60 px-3 py-2 text-xs leading-5 text-slate-400">
                    <Zap className="mr-2 inline size-3 text-mint" />
                    {action}
                  </p>
                ))}
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-3 md:grid-cols-4">
            {audit.checks.map((check) => (
              <div key={check.name} className="border border-line/60 bg-panel2/65 p-3">
                <div className="flex items-start justify-between gap-2">
                  <h3 className="text-sm font-medium text-white">{check.name}</h3>
                  <span className="text-[11px] uppercase text-mint">{check.status}</span>
                </div>
                <p className="mt-2 text-xs leading-5 text-slate-500">{check.details}</p>
              </div>
            ))}
          </div>
        </>
      ) : null}
    </section>
  );
}

function Stat({ label, value, tone }: { label: string; value: string; tone: string }) {
  return (
    <div className="border border-line/70 bg-panel2/65 p-3">
      <span className="block text-[11px] uppercase text-slate-500">{label}</span>
      <strong className={`mt-1 block break-words text-base ${tone}`}>{value}</strong>
    </div>
  );
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
