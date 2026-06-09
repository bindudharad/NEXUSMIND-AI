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
import { AlertTriangle, Brain, GitBranch, Loader2, MessageSquareWarning, Network, Radio, RefreshCw, Send, ShieldAlert, Users } from "lucide-react";

import type { CommunicationPriority, CommunicationResponse } from "@/types/communication";

const priorityColor: Record<CommunicationPriority, string> = {
  low: "#7CF0A6",
  medium: "#F6B44B",
  high: "#F05D5E",
  critical: "#FF3B6B",
};

export function CommunicationQualityPanel() {
  const [analysis, setAnalysis] = useState<CommunicationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [streamStatus, setStreamStatus] = useState("connecting");
  const manualScenarioUntil = useRef(0);

  const loadDefault = useCallback(async () => {
    setLoading(true);
    setError("");
    manualScenarioUntil.current = 0;
    try {
      const payload = await fetchJson("/api/communication/analyze", { cache: "no-store" });
      if (!isCommunicationResponse(payload)) throw new Error("Malformed communication payload");
      setAnalysis(payload);
      setStreamStatus((status) => (status === "connecting" ? "polling" : status));
    } catch {
      setError("AI Communication Quality Analyzer could not refresh live communication intelligence.");
    } finally {
      setLoading(false);
    }
  }, []);

  const simulateEscalation = useCallback(async () => {
    setLoading(true);
    setError("");
    manualScenarioUntil.current = Date.now() + 30000;
    try {
      const payload = await fetchJson(
        "/api/communication/analyze",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(buildCommunicationPayload()),
          cache: "no-store",
        },
        60000,
      );
      if (!isCommunicationResponse(payload)) throw new Error("Malformed communication payload");
      setAnalysis(payload);
      setStreamStatus((status) => (status === "connecting" ? "polling" : status));
    } catch {
      setError("AI Communication Quality Analyzer could not process the conflict escalation scenario.");
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
        const response = await fetch("/api/communication/stream", { cache: "no-store", signal: controller.signal });
        if (!response.ok) throw new Error("Communication stream failed");
        const reader = response.body?.getReader();
        if (!reader) throw new Error("Missing communication stream");
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
            if (isCommunicationResponse(payload) && Date.now() > manualScenarioUntil.current) {
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

  const messageRiskData = useMemo(
    () =>
      analysis?.messageRisks.slice(0, 6).map((item) => ({
        name: item.employeeName.split(" ")[0],
        toxicity: Math.round(item.toxicityScore),
        aggression: Math.round(item.aggressionScore),
        conflict: Math.round(item.conflictEscalationScore),
        quality: Math.round(item.communicationQualityScore),
      })) ?? [],
    [analysis],
  );

  const heatmapData = useMemo(
    () =>
      analysis?.teamHeatmap.slice(0, 8).map((item) => ({
        name: `${item.department.slice(0, 3)}-${item.team.split(" ")[0]}`,
        toxicity: Math.round(item.toxicityRisk),
        conflict: Math.round(item.conflictProbability),
        isolation: Math.round(item.isolationRisk),
        morale: Math.round(item.moraleScore),
        priority: item.priority,
      })) ?? [],
    [analysis],
  );

  const graphData = useMemo(
    () =>
      analysis?.interactionGraph.slice(0, 8).map((item) => ({
        edge: `${item.sourceName.split(" ")[0]}-${item.targetName.split(" ")[0]}`,
        collaboration: Math.round(item.collaborationScore),
        conflict: Math.round(item.conflictProbability),
        response: Math.round(item.responseHealth),
        isolation: Math.round(item.isolationSignal),
      })) ?? [],
    [analysis],
  );

  const conflictTrend = useMemo(() => {
    const forecast = analysis?.conflictForecasts[0];
    return (
      forecast?.forecast.map((value, index) => ({
        window: `T+${index + 1}`,
        probability: Math.round(value),
      })) ?? []
    );
  }, [analysis]);

  return (
    <section data-testid="communication-quality-panel" className="border border-line/80 bg-panel/85 p-5 shadow-control backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <MessageSquareWarning className="size-5 text-cyan" />
          <div>
            <p className="text-xs uppercase text-cyan">AI Communication Quality Analyzer</p>
            <h2 className="text-xl font-semibold text-white">
              Toxicity heatmaps, team interaction graphs, conflict-risk analytics, collaboration-quality charts, isolation detection panels, AI recommendation widgets, and realtime communication alerts
            </h2>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button data-testid="refresh-communication-quality" onClick={() => void loadDefault()} className="inline-flex items-center gap-2 border border-line bg-panel2 px-3 py-2 text-sm text-slate-300">
            <RefreshCw className="size-4" />
            Refresh quality
          </button>
          <button data-testid="simulate-communication-quality" onClick={() => void simulateEscalation()} className="inline-flex items-center gap-2 border border-cyan/40 bg-cyan/10 px-3 py-2 text-sm text-cyan">
            {loading ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
            Simulate escalation
          </button>
        </div>
      </div>

      {error && !analysis ? <p className="mt-4 text-sm text-signal">{error}</p> : null}
      {loading && !analysis ? <p className="mt-5 text-sm text-slate-400">Analyzing toxicity, interaction graph pressure, isolation risk, and conflict propagation...</p> : null}

      {analysis ? (
        <>
          <div className="mt-5 grid gap-3 md:grid-cols-4 xl:grid-cols-8">
            <Stat label="Messages" value={String(analysis.summary.messagesAnalyzed)} />
            <Stat label="Edges" value={String(analysis.summary.interactionsAnalyzed)} />
            <Stat label="Toxicity" value={String(analysis.summary.highToxicityAlerts)} />
            <Stat label="Isolation" value={String(analysis.summary.isolationRisks)} />
            <Stat label="Quality" value={`${Math.round(analysis.summary.averageQualityScore)}%`} />
            <Stat label="Collab" value={`${Math.round(analysis.summary.averageCollaborationQuality)}%`} />
            <Stat label="Conflict" value={`${Math.round(analysis.summary.conflictProbability)}%`} />
            <Stat label="Stream" value={streamStatus} />
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[1.08fr_0.92fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
                <ShieldAlert className="size-4" />
                Toxicity heatmaps
              </div>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={messageRiskData} margin={{ left: -24, right: 8, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="name" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Bar dataKey="toxicity" fill="#FF3B6B" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="aggression" fill="#F6B44B" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="conflict" fill="#8B5CF6" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="quality" fill="#2EE9D3" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
                <Network className="size-4" />
                Team interaction graphs
              </div>
              <div className="space-y-3">
                {analysis.interactionGraph.slice(0, 5).map((edge) => (
                  <div key={`${edge.sourceId}-${edge.targetId}`} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold text-white">
                          {edge.sourceName} to {edge.targetName}
                        </p>
                        <p className="mt-1 text-xs text-slate-500">{edge.department} - {edge.team}</p>
                      </div>
                      <span className="text-sm font-semibold text-cyan">{Math.round(edge.conflictProbability)}%</span>
                    </div>
                    <p className="mt-2 text-xs text-slate-400">{edge.recommendation}</p>
                    <div className="mt-3 h-1.5 bg-line/60">
                      <div className="h-1.5 bg-cyan" style={{ width: `${Math.min(100, edge.collaborationScore)}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
                <GitBranch className="size-4" />
                Conflict-risk analytics
              </div>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={conflictTrend} margin={{ left: -22, right: 10, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="window" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Line type="monotone" dataKey="probability" stroke="#FF3B6B" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
              <div className="mt-3 grid gap-2">
                {analysis.conflictForecasts.slice(0, 3).map((forecast) => (
                  <p key={`${forecast.department}-${forecast.team}`} className="border border-line/60 bg-panel/60 p-3 text-xs text-slate-400">
                    {forecast.department} / {forecast.team}: {Math.round(forecast.conflictProbability)}% conflict probability, {forecast.projectedProductivityLossHours.toFixed(1)} projected loss hours.
                  </p>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
                <Users className="size-4" />
                Collaboration-quality charts
              </div>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={graphData} margin={{ left: -24, right: 8, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="edge" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 10 }} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Bar dataKey="collaboration" fill="#2EE9D3" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="response" fill="#7CF0A6" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="conflict" fill="#F6B44B" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="isolation" fill="#FF3B6B" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[1.02fr_0.98fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
                <AlertTriangle className="size-4" />
                Isolation detection panels
              </div>
              <div className="grid gap-3">
                {analysis.isolationRisks.slice(0, 5).map((risk) => (
                  <div key={`${risk.employeeId}-${risk.team}`} className="border-l-2 bg-panel/60 p-3" style={{ borderColor: risk.isolationRisk >= 55 ? "#FF3B6B" : "#F6B44B" }}>
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold text-white">{risk.employeeName}</p>
                        <p className="mt-1 text-xs text-slate-500">{risk.department} - {risk.team}</p>
                      </div>
                      <span className="text-sm font-semibold text-cyan">{Math.round(risk.isolationRisk)}%</span>
                    </div>
                    <p className="mt-2 text-xs text-slate-400">{risk.recommendation}</p>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
                <Brain className="size-4" />
                AI recommendation widgets
              </div>
              <div className="space-y-3">
                {analysis.recommendations.slice(0, 5).map((item) => (
                  <div key={`${item.category}-${item.title}`} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-sm font-semibold text-white">{item.title}</p>
                      <span className="text-sm font-semibold" style={{ color: priorityColor[item.priority] }}>
                        {Math.round(item.impactScore)}
                      </span>
                    </div>
                    <p className="mt-2 text-xs text-slate-400">{item.action}</p>
                    <p className="mt-2 text-[11px] uppercase text-slate-500">{item.category} - {Math.round(item.confidence * 100)}% confidence</p>
                  </div>
                ))}
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
                <ShieldAlert className="size-4" />
                Realtime communication alerts
              </div>
              <div className="space-y-3">
                {analysis.alerts.slice(0, 5).map((alert, index) => (
                  <div key={`${alert.title}-${index}`} className="border-l-2 bg-panel/60 p-3" style={{ borderColor: priorityColor[alert.priority] }}>
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold text-white">{alert.title}</p>
                        <p className="mt-1 text-xs text-slate-400">{alert.impact}</p>
                      </div>
                      <span className="text-sm font-semibold" style={{ color: priorityColor[alert.priority] }}>
                        {Math.round(alert.probability)}%
                      </span>
                    </div>
                    <p className="mt-2 text-xs text-slate-500">{alert.recommendation}</p>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
                <Radio className="size-4" />
                Team sentiment heatmap
              </div>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={heatmapData} margin={{ left: -24, right: 8, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="name" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 10 }} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Bar dataKey="morale" radius={[3, 3, 0, 0]}>
                      {heatmapData.map((item) => (
                        <Cell key={item.name} fill={priorityColor[item.priority]} />
                      ))}
                    </Bar>
                    <Bar dataKey="toxicity" fill="#FF3B6B" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="conflict" fill="#F6B44B" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="isolation" fill="#8B5CF6" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="mt-3 flex flex-wrap items-center gap-2 text-[11px] uppercase text-slate-500">
                <Radio className="size-3 text-cyan" />
                {analysis.model}
              </div>
            </article>
          </div>
        </>
      ) : null}
    </section>
  );
}

async function fetchJson(input: string, init?: RequestInit, timeoutMs = 45000): Promise<unknown> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(input, { ...init, signal: controller.signal });
    const text = await response.text();
    const payload = text ? (JSON.parse(text) as unknown) : {};
    if (!response.ok) throw new Error("Communication request failed");
    return payload;
  } finally {
    window.clearTimeout(timeout);
  }
}

function isCommunicationResponse(payload: unknown): payload is CommunicationResponse {
  const value = payload as Partial<CommunicationResponse> | null;
  return Boolean(
    value &&
      typeof value.model === "string" &&
      Array.isArray(value.messageRisks) &&
      Array.isArray(value.teamHeatmap) &&
      Array.isArray(value.interactionGraph) &&
      Array.isArray(value.conflictForecasts) &&
      Array.isArray(value.isolationRisks) &&
      Array.isArray(value.recommendations) &&
      value.summary,
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-line/70 bg-panel2/70 p-3">
      <p className="text-xs uppercase text-slate-500">{label}</p>
      <strong className="mt-1 block text-lg font-semibold text-white">{value}</strong>
    </div>
  );
}

function buildCommunicationPayload() {
  return {
    cycle_name: "Realtime Conflict Escalation Scenario",
    horizon_days: 45,
    realtime: true,
    messages: [
      {
        message_id: "comm-ui-toxic",
        employee_id: "comm-ui-a",
        employee_name: "Employee A",
        department: "Engineering",
        team: "Platform",
        channel: "review",
        thread_id: "release-quality",
        text: "Stop making excuses. This reckless deployment keeps breaking everything and the handoff is unacceptable.",
        response_delay_minutes: 260,
        expected_response_minutes: 45,
        unresolved: true,
        recipient_ids: ["comm-ui-b"],
      },
      {
        message_id: "comm-ui-calm",
        employee_id: "comm-ui-b",
        employee_name: "Employee B",
        department: "Engineering",
        team: "Platform",
        channel: "chat",
        thread_id: "release-quality",
        text: "The rollback plan is clear, QA has ownership, and I can help document the deployment notes.",
        response_delay_minutes: 12,
        expected_response_minutes: 60,
        unresolved: false,
        recipient_ids: ["comm-ui-a"],
      },
      {
        message_id: "comm-ui-isolated",
        employee_id: "comm-ui-isolated",
        employee_name: "Isolated Engineer",
        department: "Engineering",
        team: "Platform",
        channel: "email",
        thread_id: "design-review",
        text: "I have not received a response after several follow ups and the review thread is silent.",
        response_delay_minutes: 520,
        expected_response_minutes: 70,
        unresolved: true,
        recipient_ids: ["comm-ui-manager"],
      },
    ],
    interactions: [
      {
        source_id: "comm-ui-a",
        source_name: "Employee A",
        target_id: "comm-ui-b",
        target_name: "Employee B",
        department: "Engineering",
        team: "Platform",
        messages_sent: 41,
        messages_received: 12,
        average_response_minutes: 260,
        baseline_response_minutes: 45,
        collaboration_frequency: 0.24,
        sentiment_alignment: -0.68,
        conflict_incidents: 8,
        unanswered_threads: 9,
        participation_delta: -0.62,
      },
      {
        source_id: "comm-ui-isolated",
        source_name: "Isolated Engineer",
        target_id: "comm-ui-manager",
        target_name: "Engineering Manager",
        department: "Engineering",
        team: "Platform",
        messages_sent: 2,
        messages_received: 17,
        average_response_minutes: 540,
        baseline_response_minutes: 70,
        collaboration_frequency: 0.08,
        sentiment_alignment: -0.4,
        conflict_incidents: 1,
        unanswered_threads: 12,
        participation_delta: -0.74,
      },
    ],
  };
}
