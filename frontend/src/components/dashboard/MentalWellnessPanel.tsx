"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { BrainCircuit, HeartPulse, Loader2, Radio, RefreshCw, Send, ShieldAlert, TimerReset } from "lucide-react";

import type { WellnessAnalysisResponse, WellnessRiskAlert, WellnessSeverity } from "@/types/wellness";

const severityColor: Record<WellnessSeverity, string> = {
  low: "#7CF0A6",
  medium: "#F6B44B",
  high: "#F05D5E",
  critical: "#FF3B6B",
};

export function MentalWellnessPanel() {
  const [analysis, setAnalysis] = useState<WellnessAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [streamStatus, setStreamStatus] = useState("connecting");

  const loadSample = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/wellness/analyze", { cache: "no-store" });
      if (!response.ok) throw new Error("Mental wellness analysis failed");
      const payload = await response.json();
      if (!isWellnessAnalysis(payload)) throw new Error("Malformed wellness analysis");
      setAnalysis(payload);
    } catch {
      setError("Employee Mental Wellness AI could not refresh the live signal.");
    } finally {
      setLoading(false);
    }
  }, []);

  const simulateOverload = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/wellness/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(buildOverloadPayload()),
        cache: "no-store",
      });
      if (!response.ok) throw new Error("Mental wellness overload analysis failed");
      const payload = await response.json();
      if (!isWellnessAnalysis(payload)) throw new Error("Malformed wellness analysis");
      setAnalysis(payload);
    } catch {
      setError("Employee Mental Wellness AI could not process the overload scenario.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    async function connectStream() {
      try {
        const response = await fetch("/api/wellness/stream", { cache: "no-store", signal: controller.signal });
        if (!response.ok) throw new Error("Wellness stream failed");
        const reader = response.body?.getReader();
        if (!reader) throw new Error("Missing wellness stream");
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
              const payload = JSON.parse(dataLine.slice(6));
              if (isWellnessAnalysis(payload)) {
                setAnalysis(payload);
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
      void loadSample();
    }, 0);
    const streamRefresh = window.setTimeout(() => {
      void connectStream();
    }, 3200);
    return () => {
      controller.abort();
      window.clearTimeout(firstRefresh);
      window.clearTimeout(streamRefresh);
    };
  }, [loadSample]);

  const heatmapData = useMemo(
    () =>
      analysis?.emotionalHeatmap.map((cell) => ({
        department: cell.department,
        stress: Math.round(cell.stressScore),
        burnout: Math.round(cell.burnoutProbability),
        exhaustion: Math.round(cell.emotionalExhaustion),
        morale: Math.round(cell.moraleScore),
      })) ?? [],
    [analysis],
  );

  const signalData = useMemo(() => {
    if (!analysis) return [];
    return [
      { label: "Stress", value: Math.round(analysis.summary.stressScore), color: "#F6B44B" },
      { label: "Burnout", value: Math.round(analysis.summary.burnoutProbability), color: "#F05D5E" },
      { label: "Exhaustion", value: Math.round(analysis.summary.emotionalExhaustionProbability), color: "#FF3B6B" },
      { label: "Anxiety", value: Math.round(analysis.summary.anxietyScore), color: "#B388FF" },
      { label: "Fatigue", value: Math.round(analysis.summary.communicationFatigue), color: "#2EE9D3" },
    ];
  }, [analysis]);

  return (
    <section className="border border-line/80 bg-panel/85 p-5 shadow-control backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <HeartPulse className="size-5 text-cyan" />
          <div>
            <p className="text-xs uppercase text-cyan">Employee Mental Wellness AI</p>
            <h2 className="text-xl font-semibold text-white">Stress, emotional exhaustion, burnout probability, typing behavior, voice fusion, and recovery recommendations</h2>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button onClick={() => void loadSample()} className="inline-flex items-center gap-2 border border-line bg-panel2 px-3 py-2 text-sm text-slate-300">
            <RefreshCw className="size-4" />
            Refresh live
          </button>
          <button onClick={() => void simulateOverload()} className="inline-flex items-center gap-2 border border-cyan/40 bg-cyan/10 px-3 py-2 text-sm text-cyan">
            {loading ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
            Simulate overload
          </button>
        </div>
      </div>

      {error ? <p className="mt-4 text-sm text-signal">{error}</p> : null}
      {loading ? <p className="mt-5 text-sm text-slate-400">Analyzing NLP sentiment, acoustic stress, typing rhythm, workload, meetings, and burnout ensemble signals...</p> : null}

      {analysis ? (
        <>
          <div className="mt-5 grid gap-3 md:grid-cols-3 xl:grid-cols-8">
            <Stat label="Wellness" value={`${Math.round(analysis.summary.wellnessScore)}%`} />
            <Stat label="Stress" value={`${Math.round(analysis.summary.stressScore)}%`} />
            <Stat label="Burnout" value={`${Math.round(analysis.summary.burnoutProbability)}%`} />
            <Stat label="Exhaustion" value={`${Math.round(analysis.summary.emotionalExhaustionProbability)}%`} />
            <Stat label="Overload" value={`${Math.round(analysis.summary.mentalOverload)}%`} />
            <Stat label="High-risk teams" value={String(analysis.summary.highRiskTeamCount)} />
            <Stat label="Dominant emotion" value={String(analysis.sentimentSummary.dominantEmotion ?? "neutral")} />
            <Stat label="Stream" value={streamStatus} />
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[1fr_0.95fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="flex items-center gap-2 text-xs uppercase text-cyan">
                <BrainCircuit className="size-4" />
                Emotional risk fusion
              </div>
              <div className="mt-4 h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={signalData} margin={{ left: -24, right: 8, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="label" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Bar dataKey="value" radius={[3, 3, 0, 0]}>
                      {signalData.map((item) => (
                        <Cell key={item.label} fill={item.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="mt-3 grid gap-2 md:grid-cols-3">
                <Progress label="Typing stress" value={analysis.typingAnalytics.stressScore} color="bg-amber" />
                <Progress label="Cognitive load" value={analysis.typingAnalytics.cognitiveLoadScore} color="bg-cyan" />
                <Progress label="Typing fatigue" value={analysis.typingAnalytics.fatigueScore} color="bg-signal" />
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="flex items-center gap-2 text-xs uppercase text-amber">
                <ShieldAlert className="size-4" />
                Realtime emotional alerts
              </div>
              <div className="mt-3 grid gap-2">
                {analysis.riskAlerts.slice(0, 5).map((alert) => (
                  <AlertRow key={`${alert.category}-${alert.score}`} alert={alert} />
                ))}
              </div>
            </article>
          </div>

          <div className="mt-5 grid gap-4 xl:grid-cols-[1.05fr_0.95fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-mint">
                <Radio className="size-4" />
                Emotional heatmap
              </div>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={heatmapData} margin={{ left: -24, right: 8, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="department" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Bar dataKey="stress" fill="#F6B44B" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="burnout" fill="#F05D5E" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="exhaustion" fill="#FF3B6B" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="morale" fill="#7CF0A6" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="mt-3 grid gap-2 md:grid-cols-2">
                {analysis.emotionalHeatmap.slice(0, 4).map((cell) => (
                  <div key={cell.department} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex items-center justify-between gap-2">
                      <h3 className="text-sm font-medium text-white">{cell.department}</h3>
                      <span className="text-xs text-signal">{Math.round(cell.emotionalExhaustion)}% exhaustion</span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{cell.recommendation}</p>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="flex items-center gap-2 text-xs uppercase text-cyan">
                <TimerReset className="size-4" />
                Work-pattern forecast
              </div>
              <p className="mt-3 text-sm leading-6 text-slate-300">{analysis.workPatternAnalytics.forecast}</p>
              <div className="mt-4 grid gap-2">
                <Progress label="Overtime pressure" value={analysis.workPatternAnalytics.overtimePressure} color="bg-amber" />
                <Progress label="Meeting overload" value={analysis.workPatternAnalytics.meetingOverload} color="bg-cyan" />
                <Progress label="Productivity decline" value={analysis.workPatternAnalytics.productivityDecline} color="bg-signal" />
                <Progress label="Focus deficit" value={analysis.workPatternAnalytics.focusDeficit} color="bg-mint" />
                <Progress label="Collaboration risk" value={analysis.workPatternAnalytics.collaborationRisk} color="bg-slate-400" />
              </div>
            </article>
          </div>

          <div className="mt-5 grid gap-4 xl:grid-cols-[1fr_0.95fr]">
            <article className="border border-cyan/25 bg-cyan/10 p-4">
              <div className="text-xs uppercase text-cyan">AI wellness recommendations</div>
              <div className="mt-3 grid gap-2">
                {analysis.recommendations.slice(0, 5).map((recommendation) => (
                  <div key={`${recommendation.category}-${recommendation.action}`} className="border border-cyan/20 bg-panel/70 p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="text-sm font-medium text-white">{recommendation.action}</span>
                      <span className="text-xs uppercase" style={{ color: severityColor[recommendation.priority] }}>
                        {recommendation.priority} / {Math.round(recommendation.confidence * 100)}%
                      </span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{recommendation.expectedImpact}</p>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="text-xs uppercase text-slate-500">Executive wellness insights</div>
              <div className="mt-3 space-y-2">
                {analysis.executiveInsights.map((insight) => (
                  <p key={insight} className="border border-line/60 bg-panel/60 p-3 text-sm leading-6 text-slate-300">
                    {insight}
                  </p>
                ))}
              </div>
              <div className="mt-3 border border-line/60 bg-panel/60 p-3 text-xs leading-5 text-slate-500">
                Model fusion: {analysis.nlpModel} / {analysis.voiceModel} / {analysis.behavioralModel}
              </div>
            </article>
          </div>
        </>
      ) : null}
    </section>
  );
}

function AlertRow({ alert }: { alert: WellnessRiskAlert }) {
  return (
    <div className="border border-line/60 bg-panel/60 p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="text-sm font-medium text-white">{alert.message}</span>
        <span className="text-xs uppercase" style={{ color: severityColor[alert.severity] }}>
          {alert.severity} / {Math.round(alert.score)}%
        </span>
      </div>
      <p className="mt-2 text-xs leading-5 text-slate-400">{alert.recommendation}</p>
    </div>
  );
}

function Progress({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="border border-line/60 bg-panel/60 p-3">
      <div className="flex items-center justify-between gap-2 text-xs uppercase text-slate-500">
        <span>{label}</span>
        <span>{Math.round(value)}%</span>
      </div>
      <div className="mt-2 h-2 bg-void/80">
        <div className={`h-full ${color}`} style={{ width: `${Math.max(4, Math.min(100, value))}%` }} />
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-line/70 bg-panel2/65 p-3">
      <p className="text-xs uppercase text-slate-500">{label}</p>
      <strong className="mt-2 block truncate text-lg font-semibold text-white">{value}</strong>
    </div>
  );
}

function isWellnessAnalysis(value: unknown): value is WellnessAnalysisResponse {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Partial<WellnessAnalysisResponse>;
  return Boolean(candidate.model && candidate.summary?.wellnessScore !== undefined && Array.isArray(candidate.recommendations));
}

function buildOverloadPayload() {
  return {
    employee_id: "emp-wellness-overload",
    employee_name: "Live Incident Owner",
    department: "Engineering",
    role: "Incident Lead",
    messages: [
      {
        channel: "slack",
        text: "I am exhausted, anxious, and frustrated because the escalation keeps restarting every night.",
      },
      {
        channel: "chat",
        text: "The meetings are constant, I cannot focus, and the deadline pressure is becoming unmanageable.",
      },
      {
        channel: "email",
        text: "I need help now because the team is overwhelmed and the same blockers are repeating.",
      },
    ],
    work_pattern: {
      timestamp: new Date().toISOString(),
      overtime_hours: 24,
      workload_intensity: 96,
      meeting_hours: 16,
      sentiment_score: -0.78,
      task_completion_ratio: 0.44,
      attendance_rate: 0.8,
      focus_hours: 1.4,
      collaboration_score: 0.48,
      activity_variance: 0.9,
      negative_message_ratio: 0.72,
      toxic_message_count: 3,
      absence_days: 6,
    },
    typing_samples: [
      { typing_speed_cpm: 368, backspace_rate: 0.27, error_rate: 0.18, pause_ratio: 0.49, burstiness: 0.84, after_hours: true },
      { typing_speed_cpm: 304, backspace_rate: 0.22, error_rate: 0.2, pause_ratio: 0.56, burstiness: 0.78, after_hours: true },
      { typing_speed_cpm: 391, backspace_rate: 0.25, error_rate: 0.16, pause_ratio: 0.43, burstiness: 0.9, after_hours: true },
    ],
    team_members: [
      { employee_id: "eng-live", name: "Live Incident Owner", department: "Engineering", stress_score: 91, burnout_probability: 86, sentiment_score: -0.72, meeting_hours: 16, overtime_hours: 24 },
      { employee_id: "eng-peer", name: "Platform Peer", department: "Engineering", stress_score: 76, burnout_probability: 68, sentiment_score: -0.38, meeting_hours: 12, overtime_hours: 15 },
      { employee_id: "ops-lead", name: "Operations Lead", department: "Operations", stress_score: 62, burnout_probability: 52, sentiment_score: -0.18, meeting_hours: 10, overtime_hours: 8 },
      { employee_id: "design-partner", name: "Design Partner", department: "Design", stress_score: 41, burnout_probability: 29, sentiment_score: 0.18, meeting_hours: 5, overtime_hours: 2 },
    ],
    realtime: true,
  };
}
