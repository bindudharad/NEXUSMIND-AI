"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { AlertTriangle, BellRing, CheckCircle2, Radio, RefreshCw, Siren, Workflow } from "lucide-react";

import type { AIAlert, AlertFeedResponse, AlertSeverity } from "@/types/alerts";

type SnakeRecord = Record<string, unknown>;

const severityColor: Record<AlertSeverity, string> = {
  critical: "#F05D5E",
  high: "#F6B44B",
  medium: "#2EE9D3",
  low: "#7CF0A6",
};

export function AIAlertCenterPanel() {
  const [feed, setFeed] = useState<AlertFeedResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [streamStatus, setStreamStatus] = useState("connecting");
  const [acknowledging, setAcknowledging] = useState("");
  const activeMode = useRef<"default" | "crisis">("default");

  async function loadAlerts(mode: "default" | "crisis" = activeMode.current) {
    activeMode.current = mode;
    setLoading(true);
    setError("");
    try {
      const response =
        mode === "default"
          ? await fetch("/api/alerts/feed", { cache: "no-store" })
          : await fetch("/api/alerts/feed", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ scenario: "crisis", sensitivity: 0.78, include_recommendations: true }),
              cache: "no-store",
            });
      if (!response.ok) throw new Error("AI alert feed failed");
      const nextFeed = normalizeFeed(await response.json());
      if (!nextFeed) throw new Error("Invalid AI alert feed");
      setFeed(nextFeed);
    } catch {
      setError("The AI alert engine could not refresh.");
    } finally {
      setLoading(false);
    }
  }

  async function acknowledge(alert: AIAlert) {
    setAcknowledging(alert.alertId);
    try {
      const response = await fetch("/api/alerts/acknowledge", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ alertId: alert.alertId, acknowledged: !alert.acknowledged }),
      });
      if (!response.ok) throw new Error("Alert acknowledgement failed");
      setFeed((current) => {
        if (!current) return current;
        const alerts = current.alerts.map((item) =>
          item.alertId === alert.alertId ? { ...item, acknowledged: !alert.acknowledged } : item,
        );
        return {
          ...current,
          alerts,
          summary: {
            ...current.summary,
            unacknowledged: alerts.filter((item) => !item.acknowledged).length,
          },
        };
      });
    } catch {
      setError("Alert acknowledgement could not be stored.");
    } finally {
      setAcknowledging("");
    }
  }

  useEffect(() => {
    const controller = new AbortController();

    async function connectStream() {
      try {
        const response = await fetch("/api/alerts/stream", { cache: "no-store", signal: controller.signal });
        const reader = response.body?.getReader();
        if (!reader) throw new Error("Missing alert stream");
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
              const nextFeed = normalizeFeed(toCamel<AlertFeedResponse>(JSON.parse(dataLine.slice(6))));
              if (nextFeed) {
                setFeed(nextFeed);
                setLoading(false);
              }
            }
          }
        }
        setStreamStatus("polling");
      } catch {
        if (!controller.signal.aborted) setStreamStatus("polling");
      }
    }

    const firstRefresh = window.setTimeout(() => {
      void loadAlerts();
    }, 6600);
    const streamRefresh = window.setTimeout(() => {
      void connectStream();
    }, 9000);
    const interval = window.setInterval(() => {
      void loadAlerts(activeMode.current);
    }, 12000);

    return () => {
      controller.abort();
      window.clearTimeout(firstRefresh);
      window.clearTimeout(streamRefresh);
      window.clearInterval(interval);
    };
  }, []);

  const chartData = useMemo(() => {
    if (!feed) return [];
    return (feed.alerts ?? []).slice(0, 8).map((alert) => ({
      name: alert.category,
      risk: alert.riskScore,
      severity: alert.severity,
    }));
  }, [feed]);

  return (
    <section className="border border-line/80 bg-panel/85 p-5 shadow-control backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <Siren className="size-5 text-signal" />
          <div>
            <p className="text-xs uppercase text-signal">AI Alert System</p>
            <h2 className="text-xl font-semibold text-white">Realtime cross-system risk notification center</h2>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => void loadAlerts("default")}
            className="inline-flex items-center gap-2 border border-line bg-panel2 px-3 py-2 text-sm text-slate-300"
          >
            <RefreshCw className="size-4" />
            Refresh alerts
          </button>
          <button
            onClick={() => void loadAlerts("crisis")}
            className="inline-flex items-center gap-2 border border-signal/40 bg-signal/10 px-3 py-2 text-sm text-signal"
          >
            <AlertTriangle className="size-4" />
            Simulate alert crisis
          </button>
        </div>
      </div>

      {error ? <p className="mt-4 text-sm text-signal">{error}</p> : null}
      {loading ? <p className="mt-6 text-sm text-slate-400">Correlating ML events across burnout, NLP, anomaly, and forecasting systems...</p> : null}

      {feed ? (
        <>
          <div className="mt-5 grid gap-3 md:grid-cols-6">
            <Stat label="Model" value={feed.model} />
            <Stat label="Alerts" value={String(feed.summary.total)} />
            <Stat label="Critical" value={String(feed.summary.critical)} />
            <Stat label="High" value={String(feed.summary.high)} />
            <Stat label="Threshold" value={`${Math.round(feed.adaptiveThreshold)}%`} />
            <Stat label="Stream" value={streamStatus} />
          </div>

          <div className="mt-5 grid gap-4 xl:grid-cols-[0.78fr_1.22fr]">
            <div className="h-80 border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
                <Radio className="size-4" />
                Live alert risk spectrum
              </div>
              <ResponsiveContainer width="100%" height="88%">
                <BarChart data={chartData} margin={{ left: -22, right: 8, top: 8, bottom: 0 }}>
                  <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                  <XAxis dataKey="name" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                  <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                  <Bar dataKey="risk" radius={[3, 3, 0, 0]}>
                    {chartData.map((entry) => (
                      <Cell key={`${entry.name}-${entry.risk}`} fill={severityColor[entry.severity]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="grid gap-3">
              {(feed.alerts ?? []).slice(0, 6).map((alert) => (
                <AlertCard
                  key={alert.alertId}
                  alert={alert}
                  acknowledging={acknowledging === alert.alertId}
                  onAcknowledge={() => void acknowledge(alert)}
                />
              ))}
            </div>
          </div>

          <div className="mt-4 border border-cyan/25 bg-cyan/10 p-4">
            <div className="flex items-center gap-2 text-xs uppercase text-cyan">
              <Workflow className="size-4" />
              Cross-system correlation
            </div>
            <p className="mt-2 text-sm leading-6 text-slate-300">
              Alerts are ranked from live manager risk, employee burnout ensemble, NLP emotion analysis, anomaly detection,
              and workload forecasting. Acknowledgements feed the adaptive threshold so the system becomes less noisy over time.
            </p>
          </div>
        </>
      ) : null}
    </section>
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

function normalizeFeed(value: unknown): AlertFeedResponse | null {
  if (!value || typeof value !== "object") return null;
  const candidate = value as Partial<AlertFeedResponse>;
  if (!Array.isArray(candidate.alerts) || !candidate.summary) return null;
  const summary = {
    total: candidate.summary.total ?? candidate.alerts.length,
    critical: candidate.summary.critical ?? 0,
    high: candidate.summary.high ?? 0,
    unacknowledged: candidate.summary.unacknowledged ?? 0,
    averageRisk: candidate.summary.averageRisk ?? 0,
    streamSequence: candidate.summary.streamSequence ?? 1,
  };
  return {
    model: candidate.model ?? "Cross-System AI Alert Correlator",
    generatedAt: candidate.generatedAt ?? new Date().toISOString(),
    scenario: candidate.scenario ?? "default",
    adaptiveThreshold: candidate.adaptiveThreshold ?? 0,
    alerts: candidate.alerts,
    summary,
    storage: candidate.storage ?? "",
  };
}

function AlertCard({
  alert,
  acknowledging,
  onAcknowledge,
}: {
  alert: AIAlert;
  acknowledging: boolean;
  onAcknowledge: () => void;
}) {
  return (
    <article className="border border-line/70 bg-panel2/65 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <BellRing className="mt-1 size-4 text-amber" />
          <div>
            <p className="text-xs uppercase text-slate-500">
              {alert.category} / {alert.severity} / confidence {Math.round(alert.confidence * 100)}%
            </p>
            <h3 className="mt-1 text-base font-semibold text-white">{alert.title}</h3>
            <p className="mt-1 text-sm leading-6 text-slate-400">{alert.message}</p>
          </div>
        </div>
        <span
          className="border px-2 py-1 text-xs"
          style={{ borderColor: `${severityColor[alert.severity]}66`, color: severityColor[alert.severity] }}
        >
          {Math.round(alert.riskScore)} risk
        </span>
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        {(alert.evidence ?? []).slice(0, 5).map((item) => (
          <span key={item} className="border border-line/60 bg-panel/60 px-2 py-1 text-xs text-slate-300">
            {item}
          </span>
        ))}
      </div>

      <p className="mt-3 text-sm leading-6 text-slate-300">{alert.recommendation}</p>
      <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
        <span className="text-xs uppercase text-slate-500">{(alert.sourceSystems ?? []).slice(0, 4).join(" / ")}</span>
        <button
          onClick={onAcknowledge}
          disabled={acknowledging}
          className="inline-flex items-center gap-2 border border-mint/35 bg-mint/10 px-3 py-2 text-xs text-mint disabled:opacity-60"
        >
          <CheckCircle2 className="size-3.5" />
          {alert.acknowledged ? "Acknowledged" : acknowledging ? "Saving" : "Acknowledge"}
        </button>
      </div>
    </article>
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
