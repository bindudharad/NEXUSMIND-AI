"use client";

import {
  AlertTriangle,
  BarChart3,
  BrainCircuit,
  Loader2,
  Mic,
  ShieldAlert,
  Sparkles,
  TrendingUp,
  Volume2,
  Zap,
} from "lucide-react";
import type React from "react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Area,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type { DashboardOverview, RiskSignal } from "@/types/dashboard";
import type { EnterpriseImpactResponse } from "@/types/impact";

type CinematicExecutiveDemoPanelProps = {
  dashboard: DashboardOverview;
  impact: EnterpriseImpactResponse | null;
};

type DemoPhase = "idle" | "listening" | "analyzing" | "forecasting" | "alerting" | "recommending" | "complete";
type DemoSpeechRecognitionEvent = Event & {
  results: {
    length: number;
    [index: number]: {
      [index: number]: {
        transcript: string;
        confidence: number;
      };
    };
  };
};
type DemoSpeechRecognitionController = {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onerror: ((event: Event) => void) | null;
  onresult: ((event: DemoSpeechRecognitionEvent) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
};
type DemoSpeechRecognitionConstructor = new () => DemoSpeechRecognitionController;

const demoPhases: DemoPhase[] = ["listening", "analyzing", "forecasting", "alerting", "recommending", "complete"];
const commandSuggestions = [
  "Show biggest company risk",
  "Predict next quarter",
  "Run simulation",
  "What should management focus on?",
];

export function CinematicExecutiveDemoPanel({ dashboard, impact }: CinematicExecutiveDemoPanelProps) {
  const [phase, setPhase] = useState<DemoPhase>("idle");
  const [phaseIndex, setPhaseIndex] = useState(0);
  const [voiceStatus, setVoiceStatus] = useState("Voice system ready");
  const [lastCommand, setLastCommand] = useState(commandSuggestions[0]);
  const [transcript, setTranscript] = useState("");
  const [speaking, setSpeaking] = useState(false);
  const recognitionRef = useRef<DemoSpeechRecognitionController | null>(null);
  const timersRef = useRef<number[]>([]);

  const topRisk = dashboard.riskSignals[0];
  const executiveResponse = useMemo(
    () => buildExecutiveResponse(lastCommand, dashboard, impact),
    [dashboard, impact, lastCommand],
  );

  const demoIntensity = phase === "idle" ? 0 : phaseIndex + 1;
  const chartData = useMemo(
    () =>
      dashboard.forecastSeries.map((point, index) => {
        const pressure = demoIntensity * (index + 1);
        return {
          label: point.label,
          revenue: Math.round(point.revenue * (1 + demoIntensity * 0.006)),
          forecast: Math.round(point.revenue * (1 + 0.035 + demoIntensity * 0.008)),
          risk: Math.min(100, Math.round(point.risk + pressure * 1.2)),
          burnout: Math.min(100, Math.round(point.risk * 0.62 + pressure * 0.95)),
          productivity: Math.max(0, Math.round(point.productivity - demoIntensity * 1.1 + index * 0.4)),
        };
      }),
    [dashboard.forecastSeries, demoIntensity],
  );

  const workforceRows = useMemo(
    () =>
      dashboard.departments.slice(0, 6).map((department) => ({
        name: department.department,
        health: Math.round((department.productivity + department.wellness + department.security + (100 - department.risk)) / 4),
        risk: Math.min(100, Math.round(department.risk + demoIntensity * 3)),
      })),
    [dashboard.departments, demoIntensity],
  );

  const floatingMetrics = useMemo(() => {
    const productivity = metricNumber(dashboard.metrics.find((metric) => metric.label.toLowerCase().includes("productivity"))?.value);
    const revenueTrend = dashboard.metrics.find((metric) => metric.label.toLowerCase().includes("revenue"))?.trend ?? 0;
    const topRiskProbability = Math.round((topRisk?.probability ?? 0.22) * 100);
    return [
      { label: "Company Health", value: `${Math.min(100, dashboard.companyHealth + demoIntensity)}%`, tone: "mint" },
      { label: "Revenue Growth", value: `${formatSigned(revenueTrend + demoIntensity * 0.4)}%`, tone: revenueTrend >= 0 ? "mint" : "amber" },
      { label: "Burnout Risk", value: `${Math.min(100, topRiskProbability + demoIntensity * 2)}%`, tone: topRiskProbability > 65 ? "signal" : "amber" },
      { label: "Forecast Accuracy", value: `${Math.min(99, dashboard.predictionConfidence + demoIntensity)}%`, tone: "cyan" },
      { label: "Productivity Score", value: `${Math.min(100, productivity + demoIntensity)}%`, tone: "mint" },
      { label: "Active Risks", value: `${dashboard.riskSignals.length + (phase === "alerting" ? 1 : 0)}`, tone: "signal" },
      { label: "AI Confidence", value: `${Math.min(99, dashboard.predictionConfidence + 2 + demoIntensity)}%`, tone: "cyan" },
    ];
  }, [dashboard.companyHealth, dashboard.metrics, dashboard.predictionConfidence, dashboard.riskSignals.length, demoIntensity, phase, topRisk?.probability]);

  const alerts = useMemo(() => buildAlerts(dashboard.riskSignals, demoIntensity), [dashboard.riskSignals, demoIntensity]);

  const clearTimers = useCallback(() => {
    timersRef.current.forEach((timer) => window.clearTimeout(timer));
    timersRef.current = [];
  }, []);

  const speak = useCallback((message: string) => {
    if (!("speechSynthesis" in window)) {
      setVoiceStatus("Text-to-speech unavailable in this browser");
      return;
    }
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(message);
    utterance.rate = 0.96;
    utterance.pitch = 0.92;
    utterance.onstart = () => {
      setSpeaking(true);
      setVoiceStatus("AI voice speaking");
    };
    utterance.onend = () => {
      setSpeaking(false);
      setVoiceStatus("Voice response complete");
    };
    utterance.onerror = () => {
      setSpeaking(false);
      setVoiceStatus("Voice response interrupted");
    };
    window.speechSynthesis.speak(utterance);
  }, []);

  const runExecutiveDemo = useCallback(
    (command = lastCommand) => {
      clearTimers();
      setLastCommand(command);
      setTranscript(command);
      setVoiceStatus("AI voice activated");
      setPhase("listening");
      setPhaseIndex(0);
      demoPhases.forEach((nextPhase, index) => {
        const timer = window.setTimeout(() => {
          setPhase(nextPhase);
          setPhaseIndex(index);
          if (nextPhase === "complete") speak(buildExecutiveResponse(command, dashboard, impact));
        }, 720 + index * 900);
        timersRef.current.push(timer);
      });
    },
    [clearTimers, dashboard, impact, lastCommand, speak],
  );

  const startVoiceInput = useCallback(() => {
    const voiceWindow = window as Window &
      typeof globalThis & {
        SpeechRecognition?: DemoSpeechRecognitionConstructor;
        webkitSpeechRecognition?: DemoSpeechRecognitionConstructor;
      };
    const Recognition = voiceWindow.SpeechRecognition ?? voiceWindow.webkitSpeechRecognition;
    if (!Recognition) {
      setVoiceStatus("Speech-to-text unavailable in this browser");
      runExecutiveDemo(lastCommand);
      return;
    }
    recognitionRef.current?.stop();
    const recognition = new Recognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = "en-US";
    recognition.onresult = (event) => {
      const spokenCommand = event.results[0]?.[0]?.transcript?.trim() || lastCommand;
      setTranscript(spokenCommand);
      runExecutiveDemo(spokenCommand);
    };
    recognition.onerror = () => {
      setVoiceStatus("Speech-to-text could not capture audio");
      runExecutiveDemo(lastCommand);
    };
    recognition.onend = () => {
      if (phase === "listening") setVoiceStatus("Voice capture complete");
    };
    recognitionRef.current = recognition;
    setVoiceStatus("Listening for executive command");
    setPhase("listening");
    recognition.start();
  }, [lastCommand, phase, runExecutiveDemo]);

  useEffect(
    () => () => {
      clearTimers();
      recognitionRef.current?.stop();
      if ("speechSynthesis" in window) window.speechSynthesis.cancel();
    },
    [clearTimers],
  );

  return (
    <section id="cinematic-executive-demo" data-testid="cinematic-executive-demo" className="hud-panel mb-4 p-4 sm:p-5 lg:p-6">
      <div className="hud-content">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
          <div className="max-w-4xl">
            <div className="flex flex-wrap items-center gap-2 text-xs uppercase text-cyan">
              <Sparkles className="size-4" />
              <span>Cinematic Executive Demo</span>
              <span className="border border-cyan/25 bg-cyan/10 px-2 py-1 text-cyan">{phase}</span>
              <span className="border border-mint/25 bg-mint/10 px-2 py-1 text-mint">{voiceStatus}</span>
            </div>
            <h2 className="mt-3 text-3xl font-semibold text-white sm:text-4xl">One command triggers voice, forecasts, alerts, and live metrics</h2>
            <p className="mt-3 text-sm leading-6 text-slate-400">
              The demo uses current command-center data to animate forecasts, surface risk alerts, update floating metrics, and speak an executive recommendation.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <button type="button" onClick={() => runExecutiveDemo(commandSuggestions[0])} className="cinematic-button inline-flex h-11 items-center gap-2 px-4 text-sm font-semibold text-white">
              {phase !== "idle" && phase !== "complete" ? <Loader2 className="size-4 animate-spin text-cyan" /> : <Zap className="size-4 text-cyan" />}
              Start Executive Demo
            </button>
            <button type="button" onClick={startVoiceInput} className="cinematic-button-secondary inline-flex h-11 items-center gap-2 px-4 text-sm text-white">
              <Mic className="size-4 text-cyan" />
              Ask By Voice
            </button>
          </div>
        </div>

        <div className="mt-5 grid gap-4 xl:grid-cols-[0.72fr_1.28fr]">
          <article className="cinematic-card p-5">
            <div className="hud-content">
              <div className="grid place-items-center py-4">
                <div className={`voice-orb grid size-32 place-items-center border border-cyan/40 bg-cyan/10 ${speaking || phase === "listening" ? "alert-glow" : ""}`}>
                  {speaking ? <Volume2 className="size-12 text-cyan" /> : <Mic className="size-12 text-cyan" />}
                </div>
              </div>
              <div className="mt-3 border border-cyan/20 bg-void/55 p-3">
                <div className="text-[10px] uppercase text-slate-500">Command</div>
                <p className="mt-2 text-sm text-white">{transcript || lastCommand}</p>
              </div>
              <div className="mt-3 border border-mint/20 bg-mint/5 p-3">
                <div className="text-[10px] uppercase text-mint">AI voice response</div>
                <p className="mt-2 text-sm leading-6 text-slate-300">{executiveResponse}</p>
              </div>
              <div className="mt-4 grid gap-2">
                {commandSuggestions.map((command) => (
                  <button
                    key={command}
                    type="button"
                    onClick={() => runExecutiveDemo(command)}
                    className="border border-line/70 bg-panel2/60 px-3 py-2 text-left text-xs text-slate-300 transition hover:border-cyan/50 hover:text-white"
                  >
                    {command}
                  </button>
                ))}
              </div>
            </div>
          </article>

          <div className="grid gap-4">
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              {floatingMetrics.map((metric, index) => (
                <FloatingMetric key={metric.label} label={metric.label} value={metric.value} tone={metric.tone} delay={index} />
              ))}
            </div>

            <div className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
              <article className="cinematic-card chart-pulse p-4">
                <div className="hud-content">
                  <PanelTitle icon={TrendingUp} label="Animated revenue and forecast overlay" />
                  <div className="mt-4 h-72 min-w-0">
                    <ResponsiveContainer width="100%" height="100%">
                      <ComposedChart data={chartData} margin={{ left: -10, right: 8, top: 10, bottom: 0 }}>
                        <CartesianGrid stroke="#1C2B3A" strokeDasharray="3 3" />
                        <XAxis dataKey="label" tick={{ fill: "#94a3b8", fontSize: 11 }} />
                        <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} />
                        <Tooltip contentStyle={{ background: "#0B1020", border: "1px solid #23405d", color: "#fff" }} />
                        <Area dataKey="forecast" fill="#2EE9D3" fillOpacity={0.12} stroke="#2EE9D3" isAnimationActive animationDuration={900} />
                        <Line dataKey="revenue" stroke="#3B82F6" strokeWidth={3} dot={false} isAnimationActive animationDuration={900} />
                        <Line dataKey="productivity" stroke="#7CF0A6" strokeWidth={2} dot={false} isAnimationActive animationDuration={900} />
                      </ComposedChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </article>

              <article className="cinematic-card chart-pulse p-4">
                <div className="hud-content">
                  <PanelTitle icon={BarChart3} label="Burnout, risk, and workforce movement" />
                  <div className="mt-4 h-72 min-w-0">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={workforceRows} margin={{ left: -18, right: 8, top: 10, bottom: 32 }}>
                        <CartesianGrid stroke="#1C2B3A" strokeDasharray="3 3" />
                        <XAxis dataKey="name" angle={-25} textAnchor="end" height={52} tick={{ fill: "#94a3b8", fontSize: 10 }} />
                        <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} />
                        <Tooltip contentStyle={{ background: "#0B1020", border: "1px solid #23405d", color: "#fff" }} />
                        <Bar dataKey="health" radius={[4, 4, 0, 0]} isAnimationActive animationDuration={900}>
                          {workforceRows.map((row) => (
                            <Cell key={`health-${row.name}`} fill={row.health >= 80 ? "#7CF0A6" : row.health >= 60 ? "#F6B44B" : "#FF3B6B"} />
                          ))}
                        </Bar>
                        <Bar dataKey="risk" fill="#FF3B6B" radius={[4, 4, 0, 0]} fillOpacity={0.62} isAnimationActive animationDuration={900} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </article>
            </div>

            <div className="grid gap-4 lg:grid-cols-[0.95fr_1.05fr]">
              <article className="cinematic-card p-4">
                <div className="hud-content">
                  <PanelTitle icon={ShieldAlert} label="Glowing alert system" />
                  <div className="mt-4 grid gap-2">
                    {alerts.map((alert) => (
                      <DemoAlert key={alert.id} alert={alert} />
                    ))}
                  </div>
                </div>
              </article>

              <article className="cinematic-card p-4">
                <div className="hud-content">
                  <PanelTitle icon={BrainCircuit} label="Integrated demo chain" />
                  <div className="mt-4 grid gap-2">
                    {demoPhases.map((item, index) => (
                      <div key={item} className={`flex items-center gap-3 border px-3 py-2 ${index <= phaseIndex && phase !== "idle" ? "border-cyan/35 bg-cyan/10 text-cyan" : "border-line/60 bg-void/45 text-slate-500"}`}>
                        <span className="grid size-7 place-items-center border border-current text-xs">{index + 1}</span>
                        <span className="text-sm capitalize">{item}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </article>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function FloatingMetric({ label, value, tone, delay }: { label: string; value: string; tone: string; delay: number }) {
  const toneClass =
    tone === "signal"
      ? "border-signal/35 text-signal"
      : tone === "amber"
        ? "border-amber/35 text-amber"
        : tone === "mint"
          ? "border-mint/35 text-mint"
          : "border-cyan/35 text-cyan";
  return (
    <div className="cinematic-card floating-metric p-4" style={{ animationDelay: `${delay * 120}ms` }}>
      <div className="hud-content">
        <div className={`inline-flex border px-2 py-1 text-[10px] uppercase ${toneClass}`}>{label}</div>
        <strong className="count-up mt-3 block text-2xl text-white">{value}</strong>
      </div>
    </div>
  );
}

function DemoAlert({ alert }: { alert: ReturnType<typeof buildAlerts>[number] }) {
  const tone =
    alert.severity === "critical"
      ? "alert-glow border-signal/45 bg-signal/10 text-signal"
      : alert.severity === "warning"
        ? "border-amber/40 bg-amber/10 text-amber"
        : "border-mint/35 bg-mint/10 text-mint";
  return (
    <div className={`border p-3 ${tone}`}>
      <div className="flex items-center justify-between gap-3">
        <span className="inline-flex items-center gap-2 text-sm font-semibold text-white">
          <AlertTriangle className="size-4" />
          {alert.title}
        </span>
        <span className="text-xs uppercase">{alert.severity}</span>
      </div>
      <p className="mt-2 text-xs leading-5 text-slate-300">{alert.detail}</p>
    </div>
  );
}

function PanelTitle({ icon: Icon, label }: { icon: React.ComponentType<{ className?: string }>; label: string }) {
  return (
    <div className="flex items-center gap-2 text-xs uppercase text-cyan">
      <Icon className="size-4" />
      <span>{label}</span>
    </div>
  );
}

function buildAlerts(risks: RiskSignal[], demoIntensity: number) {
  const riskAlerts = risks.slice(0, 4).map((risk) => ({
    id: risk.id,
    title: risk.name,
    detail: risk.recommendation,
    severity: risk.impact === "critical" || risk.impact === "high" ? "critical" : risk.impact === "medium" ? "warning" : "success",
  }));
  const eventAlert = {
    id: "voice-triggered-forecast",
    title: "AI voice forecast update",
    detail: demoIntensity > 0 ? "Voice command triggered forecast, risk, alert, and metric refresh." : "Waiting for executive demo activation.",
    severity: demoIntensity > 2 ? "warning" : "success",
  };
  return [eventAlert, ...riskAlerts] as Array<{ id: string; title: string; detail: string; severity: "critical" | "warning" | "success" }>;
}

function buildExecutiveResponse(command: string, dashboard: DashboardOverview, impact: EnterpriseImpactResponse | null) {
  const risk = dashboard.riskSignals[0];
  const forecast = dashboard.forecastSeries[dashboard.forecastSeries.length - 1];
  const focus = dashboard.agentMessages[0]?.message ?? "management should focus on risk reduction, delivery protection, and burnout prevention";
  const savings = impact?.summary.netSavings ? formatMoney(impact.summary.netSavings) : "verified financial upside";
  const normalized = command.toLowerCase();

  if (normalized.includes("quarter") || normalized.includes("predict")) {
    return `Next quarter forecast shows ${forecast?.productivity ?? dashboard.companyHealth}% productivity confidence with risk at ${forecast?.risk ?? Math.round((risk?.probability ?? 0.2) * 100)}%. Management should protect delivery capacity and keep AI monitoring active.`;
  }
  if (normalized.includes("simulation") || normalized.includes("run")) {
    return `Simulation mode is active. The company twin is updating forecasts, alerts, and live metrics. Expected value protected is ${savings}.`;
  }
  if (normalized.includes("focus") || normalized.includes("management")) {
    return `Management should focus on ${focus}. The AI council recommends acting on the highest-risk signal before it spreads into delivery and revenue.`;
  }
  return `${risk?.name ?? "Enterprise operating risk"} is the biggest company risk. Probability is ${Math.round((risk?.probability ?? 0.2) * 100)}%, impact is ${risk?.impact ?? "medium"}, and the recommended action is: ${risk?.recommendation ?? "increase executive monitoring and run the future simulation"}.`;
}

function metricNumber(value?: string) {
  if (!value) return 0;
  const parsed = Number(value.replace(/[^0-9.-]/g, ""));
  return Number.isFinite(parsed) ? parsed : 0;
}

function formatSigned(value: number) {
  return `${value >= 0 ? "+" : ""}${value.toFixed(1)}`;
}

function formatMoney(value: number) {
  if (Math.abs(value) >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (Math.abs(value) >= 1_000) return `$${Math.round(value / 1_000)}K`;
  return `$${Math.round(value)}`;
}
