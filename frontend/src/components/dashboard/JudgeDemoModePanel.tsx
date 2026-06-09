"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type React from "react";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  BrainCircuit,
  CheckCircle2,
  Clapperboard,
  GitBranch,
  Loader2,
  Mic,
  Orbit,
  Play,
  Radio,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  Volume2,
  Workflow,
  Zap,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import type {
  DemoStatus,
  JudgeDemoAgentLine,
  JudgeDemoModeResponse,
  JudgeDemoRecommendation,
  JudgeDemoShadowStage,
  JudgeDemoStep,
  JudgeDemoTransformation,
} from "@/types/judge-demo-mode";

const defaultQuestion = "What happens if 30 engineers resign tomorrow?";

const statusTone: Record<DemoStatus, string> = {
  complete: "border-mint/40 bg-mint/10 text-mint",
  running: "border-cyan/40 bg-cyan/10 text-cyan",
  partial: "border-amber/40 bg-amber/10 text-amber",
  missing: "border-signal/40 bg-signal/10 text-signal",
};

const severityTone: Record<JudgeDemoTransformation["severity"], string> = {
  healthy: "border-mint/35 bg-mint/10 text-mint",
  warning: "border-amber/40 bg-amber/10 text-amber",
  critical: "border-signal/45 bg-signal/10 text-signal shadow-signal",
};

const priorityTone: Record<JudgeDemoRecommendation["priority"], string> = {
  low: "border-mint/35 bg-mint/10 text-mint",
  medium: "border-cyan/35 bg-cyan/10 text-cyan",
  high: "border-amber/40 bg-amber/10 text-amber",
  critical: "border-signal/45 bg-signal/10 text-signal",
};

const fallbackTransformations: JudgeDemoTransformation[] = [
  {
    entity: "Engineering Team Twins",
    baseline: "Teams operating normally",
    projected: "30 engineer capacity shock",
    severity: "critical",
    evidence: "Team twins recalculate capacity, morale, and delivery pressure.",
  },
  {
    entity: "Project Portfolio",
    baseline: "Project twins on active timeline",
    projected: "Delivery delay probability rises",
    severity: "warning",
    evidence: "Project twins propagate missing critical engineering capacity.",
  },
  {
    entity: "Revenue Forecast",
    baseline: "Current company revenue model",
    projected: "Revenue exposure forecast updates",
    severity: "warning",
    evidence: "Financial model links productivity and delivery risk to revenue.",
  },
  {
    entity: "Emotion Radar",
    baseline: "Burnout and morale baseline",
    projected: "Burnout and stress increase",
    severity: "critical",
    evidence: "Emotion Radar detects stress propagation.",
  },
];

const fallbackAgents: JudgeDemoAgentLine[] = [
  {
    agent: "HR Agent",
    line: "30 resignations create immediate retention, replacement, and knowledge-continuity pressure.",
    confidence: 0.91,
    sourceSystem: "workforce_impact_engine",
  },
  {
    agent: "Finance Agent",
    line: "Revenue and profit exposure increase because delivery capacity falls.",
    confidence: 0.88,
    sourceSystem: "financial_impact_engine",
  },
  {
    agent: "Project Agent",
    line: "Critical project timelines need immediate replan and owner protection.",
    confidence: 0.87,
    sourceSystem: "project_digital_twin",
  },
  {
    agent: "Executive Agent",
    line: "Recommendation: stabilize delivery capacity before approving any new commitments.",
    confidence: 0.92,
    sourceSystem: "executive_recommendation_engine",
  },
];

const fallbackShadowStages: JudgeDemoShadowStage[] = [
  { stage: "real", title: "Real Company", signal: "Current digital twin baseline", status: "complete" },
  { stage: "shadow", title: "Shadow Company", signal: "Parallel copy receives the resignation shock", status: "running" },
  { stage: "future", title: "Future Company", signal: "Risk branch becomes executive forecast", status: "partial" },
];

const fallbackRecommendations: JudgeDemoRecommendation[] = [
  {
    action: "Activate critical-role recovery plan.",
    impact: "Reduces delivery, burnout, and revenue exposure before the shock compounds.",
    ownerAgent: "Executive Agent",
    priority: "critical",
  },
];

export function JudgeDemoModePanel() {
  const [demo, setDemo] = useState<JudgeDemoModeResponse | null>(null);
  const [activeStep, setActiveStep] = useState<JudgeDemoStep | null>(null);
  const [loading, setLoading] = useState(true);
  const [playing, setPlaying] = useState(false);
  const [streamStatus, setStreamStatus] = useState("ready");
  const [error, setError] = useState("");
  const sourceRef = useRef<EventSource | null>(null);
  const playbackRef = useRef<number | null>(null);
  const finishRef = useRef<number | null>(null);

  const closeStream = useCallback(() => {
    sourceRef.current?.close();
    sourceRef.current = null;
  }, []);

  const clearPlayback = useCallback(() => {
    if (playbackRef.current !== null) {
      window.clearInterval(playbackRef.current);
      playbackRef.current = null;
    }
  }, []);

  const clearFinish = useCallback(() => {
    if (finishRef.current !== null) {
      window.clearTimeout(finishRef.current);
      finishRef.current = null;
    }
  }, []);

  const startLocalPlayback = useCallback(
    (sequence: JudgeDemoStep[]) => {
      clearPlayback();
      if (!sequence.length) return;
      let index = 0;
      setActiveStep(sequence[0]);
      playbackRef.current = window.setInterval(() => {
        index += 1;
        const next = sequence[index];
        if (next) {
          setActiveStep(next);
          return;
        }
        clearPlayback();
        setActiveStep(sequence[sequence.length - 1]);
        setPlaying(false);
        setStreamStatus("complete");
      }, 900);
    },
    [clearPlayback],
  );

  const loadDemo = useCallback(async () => {
    setLoading(true);
    setError("");
    clearPlayback();
    clearFinish();
    closeStream();
    try {
      const response = await fetch("/api/judge-demo-mode/default", { cache: "no-store" });
      if (!response.ok) throw new Error("Judge demo mode failed");
      const payload = (await response.json()) as JudgeDemoModeResponse;
      setDemo(payload);
      setActiveStep(payload.demoSequence[0] ?? null);
      setStreamStatus("loaded");
    } catch {
      setError("Judge Demo Mode could not load.");
    } finally {
      setLoading(false);
    }
  }, [clearFinish, clearPlayback, closeStream]);

  useEffect(() => {
    const timer = window.setTimeout(() => void loadDemo(), 0);
    return () => {
      window.clearTimeout(timer);
      closeStream();
      clearPlayback();
      clearFinish();
    };
  }, [clearFinish, clearPlayback, closeStream, loadDemo]);

  const runDemo = useCallback(() => {
    closeStream();
    clearFinish();
    const sequence = demo?.demoSequence ?? [];
    startLocalPlayback(sequence);
    finishRef.current = window.setTimeout(() => {
      clearPlayback();
      closeStream();
      setActiveStep(sequence[sequence.length - 1] ?? null);
      setPlaying(false);
      setStreamStatus("complete");
    }, 11000);
    setPlaying(true);
    setStreamStatus("running");
    setError("");
    const source = new EventSource("/api/judge-demo-mode/stream");
    sourceRef.current = source;
    source.addEventListener("judge_demo_mode", (event) => {
      try {
        const payload = JSON.parse((event as MessageEvent).data) as JudgeDemoModeResponse & { activeStep?: JudgeDemoStep };
        setDemo(payload);
        setActiveStep(payload.activeStep ?? payload.demoSequence[0] ?? null);
        if (playbackRef.current === null) startLocalPlayback(payload.demoSequence);
      } catch {
        setStreamStatus("degraded");
      }
    });
    source.onerror = () => {
      closeStream();
      if (playbackRef.current === null) {
        setPlaying(false);
        setStreamStatus((status) => (status === "degraded" ? "degraded" : "complete"));
      }
    };
  }, [clearFinish, clearPlayback, closeStream, demo?.demoSequence, startLocalPlayback]);

  const impossibleMoment = demo?.impossibleMoment;
  const transformations = impossibleMoment?.visualTransformations.length ? impossibleMoment.visualTransformations : fallbackTransformations;
  const agentLines = impossibleMoment?.agentCouncil.length ? impossibleMoment.agentCouncil : fallbackAgents;
  const shadowStages = impossibleMoment?.shadowCompany.length ? impossibleMoment.shadowCompany : fallbackShadowStages;
  const recommendations = impossibleMoment?.executiveRecommendations.length ? impossibleMoment.executiveRecommendations : fallbackRecommendations;
  const question = impossibleMoment?.scenarioQuestion ?? defaultQuestion;
  const activeOrder = activeStep?.order ?? 0;
  const totalSteps = demo?.demoSequence.length ?? 9;
  const progress = Math.max(0, Math.min(100, (activeOrder / totalSteps) * 100));
  const transformationReveal = streamStatus === "complete" ? transformations.length : Math.max(0, activeOrder - 1);
  const agentReveal = streamStatus === "complete" || activeOrder >= 8 ? agentLines.length : Math.max(0, activeOrder - 4);
  const recommendationReveal = streamStatus === "complete" || activeOrder >= 8 ? recommendations.length : Math.max(0, activeOrder - 7);
  const shadowReveal = streamStatus === "complete" ? shadowStages.length : activeOrder >= 7 ? shadowStages.length : activeOrder >= 2 ? 1 : 0;

  const timelineRows = useMemo(
    () => [
      { label: "Ask", threshold: 1, icon: Mic },
      { label: "Twin", threshold: 2, icon: Orbit },
      { label: "Simulate", threshold: 3, icon: Zap },
      { label: "Agents", threshold: 5, icon: Workflow },
      { label: "Recommend", threshold: 9, icon: Sparkles },
    ],
    [],
  );

  return (
    <section
      id="judge-demo-mode-panel"
      data-testid="judge-demo-mode-panel"
      className="relative w-full max-w-[calc(100vw-2rem)] overflow-hidden border border-cyan/30 bg-[#07111f]/95 p-5 shadow-control backdrop-blur lg:max-w-full"
    >
      <div className="pointer-events-none absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-cyan via-mint to-signal" />
      <div className="pointer-events-none absolute inset-0 control-grid opacity-40" />
      <div className="pointer-events-none absolute inset-x-0 top-0 h-28 scanline opacity-50" />

      <div className="relative">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
          <div className="min-w-0 max-w-[calc(100vw-4rem)] xl:max-w-5xl">
            <div className="flex flex-wrap items-center gap-2 text-xs uppercase text-cyan">
              <Clapperboard className="size-4" />
              <span>Impossible Moment Demo</span>
              <span className="border border-cyan/25 bg-cyan/10 px-2 py-1 text-cyan">{streamStatus}</span>
              <span className="border border-mint/25 bg-mint/10 px-2 py-1 text-mint">{demo?.finalVerdict ?? "verifying"}</span>
            </div>
            <h2 className="mt-2 break-words text-2xl font-semibold text-white sm:text-4xl">{demo?.headline ?? "Ask The Future Of The Company"}</h2>
            <p className="mt-3 max-w-4xl break-words text-sm leading-6 text-slate-400">
              {demo?.executiveNarrative ??
                "One button turns a future scenario into digital twin changes, animated impact, agent debate, Shadow Company branching, and executive action."}
            </p>
          </div>
          <div className="grid gap-2 sm:min-w-72">
            <button
              type="button"
              onClick={runDemo}
              aria-label="Show The Future demo mode"
              className="inline-flex h-12 items-center justify-center gap-2 border border-mint/60 bg-mint/15 px-4 text-sm font-semibold text-mint transition hover:bg-mint/20"
            >
              {playing ? <Loader2 className="size-4 animate-spin" /> : <Play className="size-4" />}
              {playing ? "Running Future Simulation" : impossibleMoment?.oneButtonLabel ?? "Show The Future"}
            </button>
            <button
              type="button"
              onClick={() => void loadDemo()}
              className="inline-flex h-10 items-center justify-center gap-2 border border-line bg-panel2/90 px-3 text-sm text-white transition hover:border-cyan/60"
            >
              {loading ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />}
              Verify Demo Systems
            </button>
          </div>
        </div>

        {error ? <div className="mt-4 border border-signal/40 bg-signal/10 px-3 py-2 text-sm text-signal">{error}</div> : null}

        <div className="mt-5 grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
          <section className="min-w-0 border border-cyan/25 bg-void/75 p-4">
            <div className="flex items-center gap-2 text-xs uppercase text-cyan">
              <Radio className="size-4" />
              <span>Ask The Future</span>
            </div>
            <div className="mt-3 border border-line bg-panel2/80 p-4">
              <p className="text-xs uppercase text-slate-500">Executive command</p>
              <p className="mt-2 break-words text-xl font-semibold leading-8 text-white">{question}</p>
              <p className="mt-3 text-sm leading-6 text-slate-400">{impossibleMoment?.userAction ?? "Press one button to run the full judge demo with no setup."}</p>
            </div>
            <div className="mt-4 h-2 overflow-hidden bg-line">
              <div className="h-full bg-gradient-to-r from-cyan via-mint to-signal transition-all duration-700" style={{ width: `${progress}%` }} />
            </div>
            <div className="mt-4 grid gap-2 sm:grid-cols-5">
              {timelineRows.map((item) => (
                <TimelineStep key={item.label} label={item.label} icon={item.icon} active={activeOrder >= item.threshold || streamStatus === "complete"} />
              ))}
            </div>
          </section>

          <section className="min-w-0 border border-line bg-panel2/80 p-4">
            <div className="flex items-center gap-2 text-xs uppercase text-mint">
              <Activity className="size-4" />
              <span>Active Shot</span>
            </div>
            <h3 className="mt-3 break-words text-xl font-semibold text-white">{activeStep?.title ?? "Ready to simulate the future"}</h3>
            <p className="mt-2 text-sm leading-6 text-slate-300">{activeStep?.cue ?? question}</p>
            <p className="mt-3 text-sm leading-6 text-mint">{activeStep?.output ?? "Waiting for the live demo stream."}</p>
            <div className="mt-4 flex flex-wrap gap-2">
              {(activeStep?.systems ?? ["AI CEO Assistant", "Digital Twin", "Shadow Company"]).map((system) => (
                <span key={system} className="border border-line bg-void/80 px-2 py-1 text-xs text-slate-300">
                  {system}
                </span>
              ))}
            </div>
          </section>
        </div>

        <div className="mt-4 grid gap-4 xl:grid-cols-[1fr_0.85fr]">
          <Panel title="Company Transforming Live" icon={Zap}>
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              {transformations.map((item, index) => (
                <TransformationCard key={item.entity} item={item} active={transformationReveal > index} />
              ))}
            </div>
          </Panel>

          <Panel title="Real Company -> Shadow Company -> Future Company" icon={GitBranch}>
            <div className="grid gap-3">
              {shadowStages.map((stage, index) => (
                <ShadowStageRow key={stage.stage} stage={stage} active={shadowReveal > index} showArrow={index < shadowStages.length - 1} />
              ))}
            </div>
          </Panel>
        </div>

        <div className="mt-4 grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
          <Panel title="AI Agent Council Live" icon={BrainCircuit}>
            <div className="grid gap-2">
              {agentLines.slice(0, 5).map((line, index) => (
                <AgentLine key={`${line.agent}-${index}`} line={line} active={agentReveal > index} />
              ))}
            </div>
          </Panel>

          <Panel title="Executive Recommendation" icon={ShieldCheck}>
            <div className="grid gap-3 md:grid-cols-2">
              {recommendations.slice(0, 4).map((item, index) => (
                <RecommendationCard key={`${item.ownerAgent}-${index}`} item={item} active={recommendationReveal > index} />
              ))}
            </div>
          </Panel>
        </div>

        <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-5">
          <Metric icon={ShieldCheck} label="Production" value={demo ? `${Math.round(demo.productionReadinessScore)}/100` : "verifying"} />
          <Metric icon={Sparkles} label="Innovation" value={demo ? `${Math.round(demo.innovationScore)}/100` : "verifying"} />
          <Metric icon={Orbit} label="Judge Wow" value={demo ? `${Math.round(demo.judgeWowFactorScore)}/100` : "verifying"} />
          <Metric icon={Workflow} label="Demo Ready" value={demo ? `${Math.round(demo.demoReadinessScore)}/100` : "verifying"} />
          <Metric icon={Volume2} label="Understood In" value={`${impossibleMoment?.judgeUnderstandsInSeconds ?? 30}s`} />
        </div>

        <div className="mt-4 grid gap-4 xl:grid-cols-3">
          <Panel title="Demo Systems" icon={CheckCircle2}>
            <List items={(demo?.featureStatus ?? []).slice(0, 8).map((item) => `${item.feature}: ${item.status}`)} />
          </Panel>
          <Panel title="Evidence Metrics" icon={Sparkles}>
            <List items={(demo?.liveMetrics ?? []).map((item) => `${item.label}: ${item.value} - ${item.evidence}`)} />
          </Panel>
          <Panel title="Errors" icon={AlertTriangle}>
            <List items={demo?.errorsFound.length ? demo.errorsFound : ["No runtime, API, dashboard, simulation, agent, or demo-sequence errors detected."]} />
          </Panel>
        </div>
      </div>
    </section>
  );
}

function TimelineStep({ label, icon: Icon, active }: { label: string; icon: LucideIcon; active: boolean }) {
  return (
    <div className={`border p-2 text-center transition ${active ? "border-cyan/45 bg-cyan/10 text-cyan" : "border-line bg-void/70 text-slate-500"}`}>
      <Icon className="mx-auto size-4" />
      <div className="mt-1 text-[11px] uppercase">{label}</div>
    </div>
  );
}

function TransformationCard({ item, active }: { item: JudgeDemoTransformation; active: boolean }) {
  return (
    <div className={`min-w-0 border p-4 transition duration-500 ${active ? severityTone[item.severity] : "border-line bg-void/75 text-slate-500"}`}>
      <div className="flex items-center justify-between gap-3">
        <span className="text-xs uppercase">{item.entity}</span>
        <span className={`size-2 shrink-0 ${active ? "animate-pulse bg-current" : "bg-line"}`} />
      </div>
      <p className="mt-3 text-xs leading-5 text-slate-500">{item.baseline}</p>
      <div className="mt-2 flex items-center gap-2 text-sm">
        <ArrowRight className="size-4 shrink-0" />
        <strong className="break-words text-white">{active ? item.projected : "Awaiting future shock"}</strong>
      </div>
      <p className="mt-3 text-xs leading-5 text-slate-400">{item.evidence}</p>
    </div>
  );
}

function ShadowStageRow({ stage, active, showArrow }: { stage: JudgeDemoShadowStage; active: boolean; showArrow: boolean }) {
  return (
    <div className="min-w-0">
      <div className={`border p-4 transition ${active ? statusTone[stage.status] : "border-line bg-void/75 text-slate-500"}`}>
        <div className="flex items-center justify-between gap-3">
          <span className="text-xs uppercase">{stage.title}</span>
          <span className="text-[10px] uppercase">{active ? stage.status : "standby"}</span>
        </div>
        <p className="mt-2 break-words text-sm text-white">{active ? stage.signal : "Waiting for synchronization"}</p>
      </div>
      {showArrow ? (
        <div className="grid h-7 place-items-center text-cyan">
          <ArrowRight className="size-4 rotate-90" />
        </div>
      ) : null}
    </div>
  );
}

function AgentLine({ line, active }: { line: JudgeDemoAgentLine; active: boolean }) {
  return (
    <div className={`border p-3 transition ${active ? "border-cyan/35 bg-cyan/10" : "border-line bg-void/75 opacity-60"}`}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="text-xs uppercase text-cyan">{line.agent}</span>
        <span className="text-[10px] uppercase text-slate-500">{Math.round(line.confidence * 100)}% confidence</span>
      </div>
      <p className="mt-2 text-sm leading-6 text-slate-300">{active ? line.line : "Waiting for council turn."}</p>
      <p className="mt-1 text-xs text-slate-500">{line.sourceSystem}</p>
    </div>
  );
}

function RecommendationCard({ item, active }: { item: JudgeDemoRecommendation; active: boolean }) {
  return (
    <div className={`min-w-0 border p-4 transition ${active ? priorityTone[item.priority] : "border-line bg-void/75 text-slate-500"}`}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="text-xs uppercase">{item.ownerAgent}</span>
        <span className="border border-current px-2 py-1 text-[10px] uppercase">{item.priority}</span>
      </div>
      <p className="mt-3 text-sm font-semibold leading-6 text-white">{active ? item.action : "Awaiting executive synthesis."}</p>
      <p className="mt-2 text-xs leading-5 text-slate-400">{item.impact}</p>
    </div>
  );
}

function Metric({ icon: Icon, label, value }: { icon: LucideIcon; label: string; value: string }) {
  return (
    <div className="border border-line bg-void/80 p-4">
      <div className="flex items-center gap-2 text-xs uppercase text-slate-500">
        <Icon className="size-4 text-cyan" />
        <span>{label}</span>
      </div>
      <div className="mt-2 break-words text-lg font-semibold text-white">{value}</div>
    </div>
  );
}

function Panel({ title, icon: Icon, children }: { title: string; icon: LucideIcon; children: React.ReactNode }) {
  return (
    <section className="min-w-0 border border-line bg-panel2/80 p-4">
      <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-white">
        <Icon className="size-4 text-cyan" />
        <span>{title}</span>
      </div>
      {children}
    </section>
  );
}

function List({ items }: { items: string[] }) {
  if (!items.length) return <div className="border border-line bg-void p-3 text-sm text-slate-500">No records loaded yet.</div>;
  return (
    <div className="space-y-2">
      {items.slice(0, 7).map((item) => (
        <div key={item} className="flex gap-2 border border-line bg-void/75 p-3 text-sm leading-6 text-slate-300">
          <CheckCircle2 className="mt-1 size-4 shrink-0 text-mint" />
          <span className="break-words">{item}</span>
        </div>
      ))}
    </div>
  );
}
