"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  AlertTriangle,
  ArrowRight,
  BrainCircuit,
  CheckCircle2,
  CircleDollarSign,
  Clapperboard,
  GitBranch,
  HeartPulse,
  Mic,
  Orbit,
  Play,
  Radio,
  ShieldCheck,
  Sparkles,
  TimerReset,
  TrendingDown,
  Users,
  Workflow,
  Zap,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import type { DashboardOverview } from "@/types/dashboard";
import type { EnterpriseImpactResponse } from "@/types/impact";

type JudgeStorytellingEnginePanelProps = {
  dashboard: DashboardOverview;
  impact: EnterpriseImpactResponse | null;
};

type StoryPhase = "healthy" | "hidden-risk" | "collapse" | "prediction" | "recovery";

const storyPhases: StoryPhase[] = ["healthy", "hidden-risk", "collapse", "prediction", "recovery"];

const phaseLabels: Record<StoryPhase, string> = {
  healthy: "Company looks healthy",
  "hidden-risk": "Hidden risk appears",
  collapse: "Future collapse simulated",
  prediction: "AI predicts it early",
  recovery: "Recovery path stabilizes",
};

const wowMoments = [
  {
    icon: Mic,
    label: "AI CEO Voice",
    proof: "answers the risk question",
    threshold: 0,
  },
  {
    icon: Zap,
    label: "Future Simulation",
    proof: "shows the failure chain",
    threshold: 2,
  },
  {
    icon: GitBranch,
    label: "Shadow Company",
    proof: "mirrors current to future",
    threshold: 2,
  },
  {
    icon: Workflow,
    label: "AI Boardroom",
    proof: "agents debate the response",
    threshold: 3,
  },
  {
    icon: HeartPulse,
    label: "Emotion Map",
    proof: "teams turn from green to red",
    threshold: 2,
  },
  {
    icon: ShieldCheck,
    label: "Recovery Strategy",
    proof: "stabilizes the company",
    threshold: 4,
  },
];

export function JudgeStorytellingEnginePanel({ dashboard, impact }: JudgeStorytellingEnginePanelProps) {
  const [phase, setPhase] = useState<StoryPhase>("healthy");
  const [running, setRunning] = useState(false);
  const timersRef = useRef<number[]>([]);
  const autoStartedRef = useRef(false);

  const highestRisk = dashboard.riskSignals[0];
  const engineering = dashboard.departments.find((item) => /engineering|development/i.test(item.department)) ?? dashboard.departments[0];
  const health = Math.round(
    engineering ? (engineering.productivity + engineering.wellness + engineering.security + (100 - engineering.risk)) / 4 : dashboard.companyHealth,
  );
  const riskProbability = Math.max(72, Math.round((highestRisk?.probability ?? 0.72) * 100));
  const protectedValue = impact?.summary.netSavings ?? 420_000;
  const phaseIndex = storyPhases.indexOf(phase);

  const collapseChain = useMemo(
    () => [
      {
        icon: Users,
        title: "30 engineers resign",
        before: "Capacity appears stable",
        after: "Critical ownership disappears",
        severity: "critical",
        threshold: 1,
      },
      {
        icon: HeartPulse,
        title: "Burnout spreads",
        before: `${health}% team health`,
        after: `${Math.min(96, riskProbability + 8)}% burnout pressure`,
        severity: "critical",
        threshold: 2,
      },
      {
        icon: TimerReset,
        title: "Project Delta slips",
        before: "Delivery still looks on track",
        after: "11 day delay forecast",
        severity: "warning",
        threshold: 2,
      },
      {
        icon: TrendingDown,
        title: "Revenue drops",
        before: "Forecast appears safe",
        after: "$420K exposure detected",
        severity: "warning",
        threshold: 2,
      },
      {
        icon: AlertTriangle,
        title: "Clients lose confidence",
        before: "No executive alarm yet",
        after: "Renewal risk rises",
        severity: "critical",
        threshold: 2,
      },
    ],
    [health, riskProbability],
  );

  const recoveryPath = useMemo(
    () => [
      {
        title: "Hire 5 critical engineers",
        outcome: "Restores delivery ownership before the failure window.",
      },
      {
        title: "Redistribute Project Delta work",
        outcome: "Reduces the delay forecast and isolates critical dependencies.",
      },
      {
        title: "Reduce burnout load",
        outcome: "Moves Engineering from red back toward warning within 30 days.",
      },
      {
        title: "Protect client commitments",
        outcome: `Preserves ${formatMoney(protectedValue)} in modeled enterprise value.`,
      },
    ],
    [protectedValue],
  );

  const runStoryMode = useCallback(() => {
    timersRef.current.forEach((timer) => window.clearTimeout(timer));
    timersRef.current = [];
    setRunning(true);
    storyPhases.forEach((nextPhase, index) => {
      const timer = window.setTimeout(() => {
        setPhase(nextPhase);
        if (index === storyPhases.length - 1) setRunning(false);
      }, index * 1150);
      timersRef.current.push(timer);
    });
  }, []);

  useEffect(() => {
    if (autoStartedRef.current) return;
    autoStartedRef.current = true;
    const timer = window.setTimeout(() => runStoryMode(), 900);
    return () => window.clearTimeout(timer);
  }, [runStoryMode]);

  useEffect(
    () => () => {
      timersRef.current.forEach((timer) => window.clearTimeout(timer));
      timersRef.current = [];
    },
    [],
  );

  return (
    <section id="judge-story-mode" data-testid="judge-storytelling-engine" className="hud-panel mb-4 p-4 sm:p-5 lg:p-6">
      <div className="hud-content">
        <div className="grid gap-5 xl:grid-cols-[1.05fr_0.95fr]">
          <article className="cinematic-card luxury-hero p-5 sm:p-6">
            <div className="neural-mesh" />
            <div className="decision-lattice" />
            <div className="hud-content">
              <div className="flex flex-wrap items-center gap-2 text-xs uppercase text-cyan">
                <Clapperboard className="size-4" />
                <span>NEXUSMIND AI</span>
                <span className="h-px w-8 bg-cyan/40" />
                <span>Autonomous Enterprise Intelligence & Digital Twin Platform</span>
                <span className="border border-cyan/30 bg-cyan/10 px-2 py-1 text-cyan">{phaseLabels[phase]}</span>
              </div>

              <h1 className="mt-5 max-w-4xl text-4xl font-semibold leading-tight text-white sm:text-6xl lg:text-7xl">
                Predict the Future of Your Enterprise.
              </h1>
              <p className="mt-4 max-w-3xl text-lg leading-8 text-slate-200">
                An Autonomous Enterprise Intelligence & Digital Twin Platform.
              </p>
              <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-400">
                See the hidden collapse before it happens: workforce pressure, project failure, revenue exposure, AI Boardroom debate, Shadow Company simulation, and a recovery plan in one cinematic command system.
              </p>

              <div className="mt-5 flex flex-wrap gap-3">
                <a href="#cinematic-command-center" className="cinematic-button inline-flex h-11 items-center gap-2 px-4 text-sm font-semibold text-white">
                  <ArrowRight className="size-4 text-cyan" />
                  Enter Command Center
                </a>
                <button type="button" onClick={runStoryMode} className="cinematic-button inline-flex h-11 items-center gap-2 px-4 text-sm font-semibold text-white">
                  {running ? <Zap className="size-4 animate-pulse text-cyan" /> : <Play className="size-4 text-cyan" />}
                  WOW Mode: Show The Future
                </button>
                <a href="#judge-demo-mode-panel" className="cinematic-button-secondary inline-flex h-11 items-center gap-2 px-4 text-sm text-slate-200">
                  <Sparkles className="size-4 text-mint" />
                  Open Full Demo Sequence
                </a>
              </div>

              <div className="mt-6 grid gap-3 md:grid-cols-3">
                <StoryMetric icon={ShieldCheck} label="Today" value={`${dashboard.companyHealth}/100 health`} tone="mint" />
                <StoryMetric icon={AlertTriangle} label="Hidden risk" value={`${riskProbability}% failure signal`} tone="signal" />
                <StoryMetric icon={CircleDollarSign} label="Value protected" value={formatMoney(protectedValue)} tone="cyan" />
              </div>

              <div className="mt-5 grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
                {wowMoments.map((moment) => (
                  <WowMomentChip key={moment.label} moment={moment} active={phaseIndex >= moment.threshold} />
                ))}
              </div>
            </div>
          </article>

          <article className="cinematic-card story-stage p-5">
            <div className="hud-content">
              <div className="flex items-center gap-2 text-xs uppercase text-mint">
                <BrainCircuit className="size-4" />
                <span>The Hero Moment</span>
              </div>
              <div className="mt-4 border border-signal/35 bg-signal/10 p-4">
                <p className="text-sm leading-6 text-slate-300">AI CEO prediction</p>
                <p className="mt-2 text-2xl font-semibold leading-9 text-white">
                  Based on current workforce trends, Project Delta has a {riskProbability}% probability of failure within 45 days.
                </p>
              </div>
              <div className="mt-4 grid gap-3 border border-cyan/25 bg-cyan/10 p-3 sm:grid-cols-3">
                <MiniWowProof icon={Orbit} label="Current Company" value={`${dashboard.companyHealth}/100`} />
                <MiniWowProof icon={GitBranch} label="Shadow Company" value="branching" />
                <MiniWowProof icon={Workflow} label="Future Company" value={phase === "recovery" ? "recovering" : "forecasting"} />
              </div>
              <div className="mt-4 grid gap-2">
                {storyPhases.map((item, index) => (
                  <div key={item} className={`flex items-center gap-3 border px-3 py-2 transition ${phaseIndex >= index ? "border-cyan/40 bg-cyan/10 text-cyan" : "border-line/70 bg-void/60 text-slate-500"}`}>
                    <span className="grid size-7 place-items-center border border-current text-xs">{index + 1}</span>
                    <span className="text-sm">{phaseLabels[item]}</span>
                  </div>
                ))}
              </div>
            </div>
          </article>
        </div>

        <div className="mt-5 grid gap-4 xl:grid-cols-[1.25fr_0.75fr]">
          <article className="cinematic-card p-4">
            <div className="hud-content">
              <div className="flex items-center gap-2 text-xs uppercase text-signal">
                <AlertTriangle className="size-4" />
                <span>Company collapse scenario</span>
              </div>
              <div className="mt-4 grid gap-3 md:grid-cols-5">
                {collapseChain.map((item, index) => (
                  <CollapseNode key={item.title} item={item} active={phaseIndex >= item.threshold} showArrow={index < collapseChain.length - 1} />
                ))}
              </div>
            </div>
          </article>

          <article className="cinematic-card p-4">
            <div className="hud-content">
              <div className="flex items-center gap-2 text-xs uppercase text-mint">
                <CheckCircle2 className="size-4" />
                <span>Recovery story</span>
              </div>
              <div className="mt-4 grid gap-2">
                {recoveryPath.map((item, index) => (
                  <div key={item.title} className={`border p-3 transition ${phase === "recovery" ? "border-mint/35 bg-mint/10" : "border-line/70 bg-void/60"}`}>
                    <div className="flex items-center gap-2">
                      <span className={`grid size-6 place-items-center border text-xs ${phase === "recovery" ? "border-mint/50 text-mint" : "border-line text-slate-500"}`}>{index + 1}</span>
                      <strong className="text-sm text-white">{item.title}</strong>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{item.outcome}</p>
                  </div>
                ))}
              </div>
            </div>
          </article>
        </div>

        <div className="mt-5 grid gap-4 lg:grid-cols-3">
          <StoryBeat title="Problem" body="Executives usually see collapse after the damage is visible." active={phaseIndex >= 0} />
          <StoryBeat title="Prediction" body="The AI CEO, Shadow Company, and forecast engine detect the hidden chain reaction before it becomes a crisis." active={phaseIndex >= 3} />
          <StoryBeat title="Recovery" body="The AI Boardroom turns the simulation into an executive recovery strategy." active={phase === "recovery"} />
        </div>
      </div>
    </section>
  );
}

function WowMomentChip({
  moment,
  active,
}: {
  moment: { icon: LucideIcon; label: string; proof: string; threshold: number };
  active: boolean;
}) {
  const Icon = moment.icon;
  return (
    <div className={`border p-3 transition duration-500 ${active ? "border-cyan/40 bg-cyan/10 text-cyan" : "border-line/70 bg-void/60 text-slate-500"}`}>
      <div className="flex items-center gap-2 text-xs uppercase">
        <Icon className={active ? "size-4 animate-pulse" : "size-4"} />
        <span>{moment.label}</span>
      </div>
      <p className="mt-2 text-xs leading-5 text-slate-300">{moment.proof}</p>
    </div>
  );
}

function MiniWowProof({
  icon: Icon,
  label,
  value,
}: {
  icon: LucideIcon;
  label: string;
  value: string;
}) {
  return (
    <div className="border border-cyan/25 bg-void/50 p-3">
      <span className="inline-flex items-center gap-2 text-[10px] uppercase text-cyan">
        <Icon className="size-3.5" />
        {label}
      </span>
      <strong className="mt-1 block text-sm text-white">{value}</strong>
    </div>
  );
}

function StoryMetric({ icon: Icon, label, value, tone }: { icon: LucideIcon; label: string; value: string; tone: "cyan" | "mint" | "signal" }) {
  const toneClass = tone === "mint" ? "text-mint border-mint/35 bg-mint/10" : tone === "signal" ? "text-signal border-signal/40 bg-signal/10" : "text-cyan border-cyan/35 bg-cyan/10";
  return (
    <div className={`border p-3 ${toneClass}`}>
      <div className="flex items-center gap-2 text-xs uppercase">
        <Icon className="size-4" />
        <span>{label}</span>
      </div>
      <strong className="mt-2 block text-xl text-white">{value}</strong>
    </div>
  );
}

function CollapseNode({
  item,
  active,
  showArrow,
}: {
  item: { icon: LucideIcon; title: string; before: string; after: string; severity: string };
  active: boolean;
  showArrow: boolean;
}) {
  const Icon = item.icon;
  const tone = item.severity === "critical" ? "border-signal/45 bg-signal/10 text-signal" : "border-amber/40 bg-amber/10 text-amber";
  return (
    <div className="relative min-w-0">
      <div className={`h-full border p-3 transition duration-500 ${active ? `${tone} ${item.severity === "critical" ? "alert-glow" : ""}` : "border-line/70 bg-void/60 text-slate-500"}`}>
        <Icon className="size-5" />
        <h3 className="mt-3 text-sm font-semibold text-white">{item.title}</h3>
        <p className="mt-2 text-xs leading-5 text-slate-500">{item.before}</p>
        <p className="mt-2 text-xs leading-5 text-slate-300">{active ? item.after : "Risk still hidden"}</p>
      </div>
      {showArrow ? <ArrowRight className="absolute -right-4 top-1/2 hidden size-5 -translate-y-1/2 text-cyan md:block" /> : null}
    </div>
  );
}

function StoryBeat({ title, body, active }: { title: string; body: string; active: boolean }) {
  return (
    <article className={`cinematic-card p-4 transition ${active ? "border-cyan/40" : "opacity-70"}`}>
      <div className="hud-content">
        <div className="flex items-center gap-2 text-xs uppercase text-cyan">
          <Radio className="size-4" />
          <span>{title}</span>
        </div>
        <p className="mt-3 text-sm leading-6 text-slate-300">{body}</p>
      </div>
    </article>
  );
}

function formatMoney(value: number) {
  if (Math.abs(value) >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (Math.abs(value) >= 1_000) return `$${Math.round(value / 1_000)}K`;
  return `$${Math.round(value)}`;
}
