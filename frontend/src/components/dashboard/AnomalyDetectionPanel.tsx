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
import { Activity, AlertTriangle, Check, DatabaseZap, Loader2, Radio, RefreshCw, Shield, ShieldAlert } from "lucide-react";

import type { AnomalyAlert, AnomalyDetectionResponse, AnomalySeverity } from "@/types/anomaly";

const severityColor: Record<AnomalySeverity, string> = {
  critical: "#FF3B6B",
  high: "#F05D5E",
  medium: "#F6B44B",
  low: "#7CF0A6",
};

export function AnomalyDetectionPanel() {
  const [result, setResult] = useState<AnomalyDetectionResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [feedbackId, setFeedbackId] = useState("");
  const [error, setError] = useState("");
  const [streamStatus, setStreamStatus] = useState("connecting");

  const loadAnomalies = useCallback(async (mode: "default" | "insider" = "default") => {
    setLoading(true);
    setError("");
    try {
      const payload = await fetchJson(
        "/api/anomalies/detect",
        mode === "default"
          ? { cache: "no-store" }
          : {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(buildInsiderThreatPayload()),
              cache: "no-store",
            },
      );
      if (!isAnomalyResponse(payload)) throw new Error("Malformed threat payload");
      setResult(payload);
      setStreamStatus((status) => (status === "connecting" ? "polling" : status));
    } catch {
      setError("Fraud and insider-threat detector could not generate SOC intelligence.");
    } finally {
      setLoading(false);
    }
  }, []);

  async function sendFeedback(alertId: string) {
    setFeedbackId(alertId);
    await fetch("/api/anomalies/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ alert_id: alertId, confirmed: true, severity_adjustment: 1 }),
    });
  }

  useEffect(() => {
    const controller = new AbortController();

    async function connectStream() {
      let streamStarted = false;
      const fallback = window.setTimeout(() => {
        if (!streamStarted && !controller.signal.aborted) setStreamStatus("polling");
      }, 12000);
      try {
        const response = await fetch("/api/anomalies/stream", { cache: "no-store", signal: controller.signal });
        if (!response.ok) throw new Error("Anomaly stream failed");
        const reader = response.body?.getReader();
        if (!reader) throw new Error("Missing anomaly stream");
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
            if (isAnomalyResponse(payload)) {
              setResult(payload);
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
      void loadAnomalies();
    }, 0);
    const streamRefresh = window.setTimeout(() => {
      void connectStream();
    }, 3200);
    return () => {
      controller.abort();
      window.clearTimeout(firstRefresh);
      window.clearTimeout(streamRefresh);
    };
  }, [loadAnomalies]);

  const threatChartData = useMemo(
    () =>
      result?.alerts.map((alert) => ({
        name: alert.employeeName.split(" ")[0],
        anomaly: Math.round(alert.anomalyScore),
        insider: Math.round(alert.insiderThreatScore),
        leakage: Math.round(alert.dataLeakageProbability),
        access: Math.round(alert.accessAnomalyScore),
        privilege: Math.round(alert.privilegeMisuseScore),
        severity: alert.severity,
      })) ?? [],
    [result],
  );

  const heatmapData = useMemo(
    () =>
      result?.userRiskHeatmap.map((point) => ({
        department: point.department,
        threat: Math.round(point.averageThreatScore),
        leakage: Math.round(point.averageDataLeakageProbability),
        access: Math.round(point.averageAccessAnomalyScore),
        critical: point.criticalAlerts,
      })) ?? [],
    [result],
  );

  return (
    <section data-testid="fraud-insider-threat-panel" className="border border-line/80 bg-panel/85 p-5 shadow-control backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <ShieldAlert className="size-5 text-amber" />
          <div>
            <p className="text-xs uppercase text-amber">Fraud & Insider Threat Detection AI</p>
            <h2 className="text-xl font-semibold text-white">Realtime SOC intelligence for suspicious behavior, access drift, data leakage, privilege misuse, and fraud risk</h2>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            data-testid="refresh-fraud-threat"
            onClick={() => void loadAnomalies("default")}
            className="inline-flex items-center gap-2 border border-line bg-panel2 px-3 py-2 text-sm text-slate-300"
          >
            <RefreshCw className="size-4" />
            Baseline
          </button>
          <button
            data-testid="simulate-fraud-threat"
            onClick={() => void loadAnomalies("insider")}
            className="inline-flex items-center gap-2 border border-amber/40 bg-amber/10 px-3 py-2 text-sm text-amber"
          >
            {loading ? <Loader2 className="size-4 animate-spin" /> : <AlertTriangle className="size-4" />}
            Simulate insider threat
          </button>
        </div>
      </div>

      {error && !result ? <p className="mt-4 text-sm text-signal">{error}</p> : null}
      {loading && !result ? <p className="mt-6 text-sm text-slate-400">Scoring access patterns, exfiltration pressure, privileged sessions, behavioral drift, and fraud likelihood...</p> : null}

      {result ? (
        <>
          <div className="mt-5 grid gap-3 md:grid-cols-4 xl:grid-cols-8">
            <Stat label="Events" value={String(result.eventsAnalyzed)} />
            <Stat label="Threshold" value={`${Math.round(result.adaptiveThreshold)}%`} />
            <Stat label="Anomaly rate" value={`${Math.round(result.anomalyRate * 100)}%`} />
            <Stat label="Insider" value={String(result.summary.insiderThreats)} />
            <Stat label="Leakage" value={String(result.summary.dataLeakageAlerts)} />
            <Stat label="Access" value={String(result.summary.accessAnomalyAlerts)} />
            <Stat label="Privilege" value={String(result.summary.privilegeMisuseAlerts)} />
            <Stat label="Stream" value={streamStatus} />
          </div>

          <div className="mt-5 grid gap-4 xl:grid-cols-[1.05fr_0.95fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-amber">
                <Shield className="size-4" />
                Insider-threat command console
              </div>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={threatChartData} margin={{ left: -24, right: 8, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="name" stroke="#64748b" tickLine={false} axisLine={false} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Bar dataKey="anomaly" radius={[3, 3, 0, 0]}>
                      {threatChartData.map((entry) => (
                        <Cell key={`${entry.name}-${entry.anomaly}`} fill={severityColor[entry.severity]} />
                      ))}
                    </Bar>
                    <Bar dataKey="insider" fill="#F6B44B" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="leakage" fill="#2EE9D3" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
                <DatabaseZap className="size-4" />
                Threat heatmaps
              </div>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={heatmapData} margin={{ left: -24, right: 8, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="department" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Bar dataKey="threat" fill="#FF3B6B" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="leakage" fill="#F6B44B" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="access" fill="#2EE9D3" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </article>
          </div>

          <div className="mt-5 grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-mint">
                <Activity className="size-4" />
                Access anomaly graphs
              </div>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={threatChartData} margin={{ left: -24, right: 8, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="name" stroke="#64748b" tickLine={false} axisLine={false} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Line type="monotone" dataKey="access" stroke="#2EE9D3" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="privilege" stroke="#F6B44B" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="leakage" stroke="#FF3B6B" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </article>

            <article className="border border-amber/25 bg-amber/10 p-4">
              <div className="text-xs uppercase text-amber">Data leakage analytics</div>
              <div className="mt-3 grid gap-2">
                {result.alerts.slice(0, 4).map((alert) => (
                  <div key={`${alert.alertId}-leakage`} className="border border-amber/20 bg-panel/70 p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="text-sm font-medium text-white">{alert.employeeName}</span>
                      <span className="text-xs text-amber">{Math.round(alert.dataLeakageProbability)}% leakage / {Math.round(alert.fraudLikelihood)}% fraud</span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{alert.evidence.join(" · ")}</p>
                    <p className="mt-2 text-xs leading-5 text-slate-500">Assets: {alert.affectedAssets.join(", ")}</p>
                  </div>
                ))}
              </div>
            </article>
          </div>

          <div className="mt-5 grid gap-4 xl:grid-cols-[1fr_1fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-signal">
                <Radio className="size-4" />
                Live SOC alert panels
              </div>
              <div className="grid gap-3">
                {result.alerts.slice(0, 4).map((alert) => (
                  <AlertCard
                    key={alert.alertId}
                    alert={alert}
                    feedbackId={feedbackId}
                    onFeedback={() => void sendFeedback(alert.alertId)}
                  />
                ))}
                {result.alerts.length === 0 ? (
                  <div className="border border-mint/30 bg-mint/10 p-4 text-sm text-mint">No alerts crossed the adaptive threshold in this sample.</div>
                ) : null}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="text-xs uppercase text-cyan">AI mitigation recommendations</div>
              <div className="mt-3 grid gap-2">
                {result.securityRecommendations.map((recommendation) => (
                  <div key={recommendation.title} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="text-sm font-medium text-white">{recommendation.title}</span>
                      <span className="text-xs uppercase" style={{ color: severityColor[recommendation.priority] }}>
                        {recommendation.priority} / {Math.round(recommendation.confidence * 100)}%
                      </span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{recommendation.action}</p>
                    <p className="mt-2 text-xs leading-5 text-slate-500">{recommendation.expectedImpact}</p>
                  </div>
                ))}
              </div>

              <div className="mt-5 text-xs uppercase text-cyan">Executive cybersecurity insights</div>
              <div className="mt-3 grid gap-2">
                {result.executiveInsights.map((insight) => (
                  <div key={insight} className="border border-line/60 bg-panel/60 p-3 text-sm leading-6 text-slate-300">
                    {insight}
                  </div>
                ))}
              </div>
            </article>
          </div>
        </>
      ) : null}
    </section>
  );
}

function AlertCard({
  alert,
  feedbackId,
  onFeedback,
}: {
  alert: AnomalyAlert;
  feedbackId: string;
  onFeedback: () => void;
}) {
  return (
    <article className="border border-line/70 bg-panel/70 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <Shield className="mt-1 size-4 text-amber" />
          <div>
            <p className="text-xs uppercase text-slate-500">
              {alert.department} / {alert.severity}
            </p>
            <h3 className="mt-1 text-base font-semibold text-white">{alert.anomalyType}</h3>
            <p className="mt-1 text-sm text-slate-400">{alert.employeeName}</p>
          </div>
        </div>
        <span className="border border-amber/35 bg-amber/10 px-2 py-1 text-xs text-amber">
          {Math.round(alert.anomalyScore)} threat
        </span>
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        {alert.evidence.map((item) => (
          <span key={item} className="border border-line/70 bg-panel2 px-2 py-1 text-xs text-slate-300">
            {item}
          </span>
        ))}
      </div>
      <p className="mt-3 text-sm leading-6 text-slate-300">{alert.recommendation}</p>
      <div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-500">
        <span>Insider {Math.round(alert.insiderThreatScore)}</span>
        <span>Access {Math.round(alert.accessAnomalyScore)}</span>
        <span>DLP {Math.round(alert.dataLeakageProbability)}</span>
        <span>Privilege {Math.round(alert.privilegeMisuseScore)}</span>
      </div>
      <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
        <span className="text-xs uppercase text-slate-500">Confidence {Math.round(alert.confidence * 100)}%</span>
        <button onClick={onFeedback} className="inline-flex items-center gap-2 border border-mint/35 bg-mint/10 px-3 py-2 text-xs text-mint">
          <Check className="size-3.5" />
          {feedbackId === alert.alertId ? "Learning captured" : "Confirm alert"}
        </button>
      </div>
    </article>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-line/70 bg-panel2/65 p-3">
      <span className="block text-xs uppercase text-slate-500">{label}</span>
      <strong className="mt-1 block truncate text-lg text-white">{value}</strong>
    </div>
  );
}

async function fetchJson(input: string, init: RequestInit, timeoutMs = 30000): Promise<unknown> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(input, { ...init, signal: controller.signal });
    if (!response.ok) throw new Error("Threat request failed");
    return await response.json();
  } finally {
    window.clearTimeout(timeout);
  }
}

function isAnomalyResponse(value: unknown): value is AnomalyDetectionResponse {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Partial<AnomalyDetectionResponse>;
  return Boolean(candidate.model && candidate.summary?.insiderThreats !== undefined && Array.isArray(candidate.alerts));
}

function buildInsiderThreatPayload() {
  return {
    sensitivity: 0.72,
    events: [
      event("emp-threat", "Employee X", "Finance", "Privileged Admin", 24, 16, 12, 0.4, 0.81, 4, 18, 0.21, 0, 8600, 38, 2, 3, 0.43, 11, 4, 3, 1, 5, 1040, 3200, 2800, 1400, 8, 3, 260, 0.94),
      event("emp-fatigue", "Employee Y", "Engineering", "Incident Lead", 10, 1, 3, 8, 0.46, 20, 76, 0.61, 2, 210, 4, 1, 12, 0.93, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0.58),
      event("emp-normal", "Employee Z", "Operations", "Program Manager", 7, 0, 0, 1.1, 0.89, 2, 38, 0.12, 0, 140, 2, 5, 5, 0.28, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.08),
    ],
  };
}

function event(
  employee_id: string,
  employee_name: string,
  department: string,
  role: string,
  login_count: number,
  failed_logins: number,
  off_hours_logins: number,
  inactive_hours: number,
  productivity_score: number,
  overtime_hours: number,
  messages_sent: number,
  negative_sentiment_ratio: number,
  toxic_message_count: number,
  data_download_mb: number,
  privileged_actions: number,
  project_commits: number,
  meeting_hours: number,
  stress_score: number,
  access_scope_changes: number,
  device_change_count: number,
  unusual_location_count: number,
  impossible_travel_events: number,
  browser_fingerprint_changes: number,
  sensitive_file_accesses: number,
  external_transfer_mb: number,
  cloud_upload_mb: number,
  usb_write_mb: number,
  policy_violation_count: number,
  admin_role_changes: number,
  privileged_session_minutes: number,
  baseline_deviation: number,
) {
  return {
    employee_id,
    employee_name,
    department,
    role,
    timestamp: "2026-05-28T09:05:00Z",
    login_count,
    failed_logins,
    off_hours_logins,
    inactive_hours,
    productivity_score,
    overtime_hours,
    messages_sent,
    negative_sentiment_ratio,
    toxic_message_count,
    data_download_mb,
    privileged_actions,
    project_commits,
    meeting_hours,
    stress_score,
    access_scope_changes,
    device_change_count,
    unusual_location_count,
    impossible_travel_events,
    browser_fingerprint_changes,
    sensitive_file_accesses,
    external_transfer_mb,
    cloud_upload_mb,
    usb_write_mb,
    policy_violation_count,
    admin_role_changes,
    privileged_session_minutes,
    baseline_deviation,
  };
}
