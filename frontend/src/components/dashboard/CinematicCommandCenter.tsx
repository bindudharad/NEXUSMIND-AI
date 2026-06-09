import {
  Activity,
  BrainCircuit,
  CircleDollarSign,
  Gauge,
  GitBranch,
  Mic,
  Network,
  Radio,
  Shield,
  Sparkles,
  TriangleAlert,
  Users,
  Workflow,
  Zap,
} from "lucide-react";
import type React from "react";

import type { DashboardOverview, DepartmentSignal, EnterpriseMetric, RiskSignal } from "@/types/dashboard";
import type { EnterpriseImpactResponse } from "@/types/impact";

type CinematicCommandCenterProps = {
  dashboard: DashboardOverview;
  impact: EnterpriseImpactResponse | null;
};

const featureSignals = [
  { icon: Mic, label: "AI CEO", value: "voice ready", href: "#judge-demo-mode-panel" },
  { icon: BrainCircuit, label: "Digital Twin", value: "live mirror", href: "#self-learning-company-ai-panel" },
  { icon: Workflow, label: "Boardroom", value: "8 agents", href: "#boardroom-dashboard-panel" },
  { icon: GitBranch, label: "Simulation", value: "future path", href: "#judge-demo-mode-panel" },
];

const demoSteps = [
  "Company appears healthy",
  "Hidden risk emerges",
  "Future collapse is simulated",
  "AI predicts the failure window",
  "Recovery plan appears",
  "Company stabilizes",
];

export function CinematicCommandCenter({ dashboard, impact }: CinematicCommandCenterProps) {
  const metrics = dashboard.metrics.slice(0, 5);
  const topRisks = dashboard.riskSignals.slice(0, 3);
  const departments = dashboard.departments.slice(0, 6);
  const proof = impact?.summary;
  const wowScore = proof?.judgeWowScore ?? dashboard.predictionConfidence;
  const healthScore = dashboard.companyHealth;
  const criticalRisk = topRisks[0];

  return (
    <section data-testid="cinematic-command-center" className="hud-panel mb-4 p-4 sm:p-5 lg:p-6">
      <div className="hud-content">
        <div className="mb-5 flex flex-wrap items-center justify-between gap-3 border-b border-cyan/10 pb-4">
          <div className="flex flex-wrap items-center gap-3 text-xs uppercase text-cyan">
            <span className="live-dot" />
            <span>NEXUSMIND AI</span>
            <span className="h-px w-10 bg-cyan/40" />
            <span>Enterprise Command Center</span>
          </div>
          <div className="flex flex-wrap gap-2 text-[11px] uppercase text-slate-400">
            <span className="border border-cyan/25 bg-cyan/10 px-2 py-1 text-cyan">Digital twins online</span>
            <span className="border border-electric/30 bg-electric/10 px-2 py-1 text-ion">Forecast engine live</span>
            <span className="border border-mint/25 bg-mint/10 px-2 py-1 text-mint">Agents synchronized</span>
          </div>
        </div>

        <div className="grid gap-4 xl:grid-cols-[1.02fr_0.98fr]">
          <div className="grid gap-4">
            <div className="grid gap-4 lg:grid-cols-[1fr_0.8fr]">
              <article className="cinematic-card p-5">
                <div className="hud-content">
                  <div className="flex items-center gap-2 text-xs uppercase text-cyan">
                    <Sparkles className="size-4" />
                    <span>Executive future-risk demo</span>
                  </div>
                  <h1 className="mt-3 max-w-3xl text-4xl font-semibold leading-tight text-white sm:text-5xl lg:text-6xl">
                    What if your company could warn you before it starts to fail?
                  </h1>
                  <p className="mt-4 max-w-2xl text-sm leading-6 text-slate-400">
                    NEXUSMIND starts with the business danger: a healthy-looking company, a hidden workforce shock, delayed projects, revenue exposure, and an AI that predicts the chain reaction early enough to act.
                  </p>
                  <div className="mt-5 flex flex-wrap gap-3">
                    <a href="#judge-demo-mode-panel" className="cinematic-button inline-flex h-11 items-center gap-2 px-4 text-sm font-medium text-white">
                      <Zap className="size-4 text-cyan" />
                      Show The Future
                    </a>
                    <a href="#boardroom-dashboard-panel" className="cinematic-button-secondary inline-flex h-11 items-center gap-2 px-4 text-sm text-slate-200">
                      <Users className="size-4 text-ion" />
                      Open AI Boardroom
                    </a>
                    <a href="#self-learning-company-ai-panel" className="cinematic-button-secondary inline-flex h-11 items-center gap-2 px-4 text-sm text-slate-200">
                      <BrainCircuit className="size-4 text-mint" />
                      Show Learning Loop
                    </a>
                  </div>
                </div>
              </article>

              <article className="cinematic-card p-5">
                <div className="hud-content">
                  <div className="flex items-center justify-between gap-3">
                    <div className="text-xs uppercase text-slate-500">Company health</div>
                    <span className="border border-mint/30 bg-mint/10 px-2 py-1 text-[11px] uppercase text-mint">live</span>
                  </div>
                  <div className="mt-5 flex items-end justify-between gap-3">
                    <strong className="count-up text-6xl font-semibold text-white">{healthScore}</strong>
                    <span className="pb-2 text-sm text-slate-400">/100</span>
                  </div>
                  <div className="hud-progress mt-5 h-2">
                    <span style={{ width: `${Math.min(100, Math.max(0, healthScore))}%` }} />
                  </div>
                  <div className="mt-5 grid grid-cols-2 gap-2">
                    <MiniProof icon={Gauge} label="AI confidence" value={`${dashboard.predictionConfidence}%`} />
                    <MiniProof icon={Sparkles} label="Wow score" value={`${Math.round(wowScore)}`} />
                  </div>
                </div>
              </article>
            </div>

            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
              {metrics.map((metric, index) => (
                <CinematicMetric key={metric.label} metric={metric} delay={index} />
              ))}
            </div>

            <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
              <article className="cinematic-card p-4">
                <div className="hud-content">
                  <div className="flex items-center gap-2 text-xs uppercase text-cyan">
                    <Activity className="size-4" />
                    <span>Real-time emotion map</span>
                  </div>
                  <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-3">
                    {departments.map((department) => (
                      <HeatCell key={department.department} department={department} />
                    ))}
                  </div>
                </div>
              </article>

              <article className="cinematic-card p-4">
                <div className="hud-content">
                  <div className="flex items-center gap-2 text-xs uppercase text-signal">
                    <TriangleAlert className="size-4" />
                    <span>Glowing alert stack</span>
                  </div>
                  <div className="mt-4 grid gap-2">
                    {topRisks.map((risk) => (
                      <RiskAlert key={risk.id} risk={risk} />
                    ))}
                  </div>
                </div>
              </article>
            </div>
          </div>

          <div className="grid gap-4">
            <article className="radar-shell">
              <div className="radar-sweep" />
              <HudNode className="left-[8%] top-[12%]" icon={Radio} label="AI CEO" value="reasoning" />
              <HudNode className="right-[8%] top-[15%]" icon={Network} label="Org brain" value="graph live" />
              <HudNode className="bottom-[14%] left-[10%]" icon={Shield} label="Risk shield" value={criticalRisk?.impact ?? "guarded"} />
              <HudNode className="bottom-[12%] right-[10%]" icon={CircleDollarSign} label="Value" value={formatMoney(proof?.netSavings)} />
              <div className="absolute left-1/2 top-1/2 z-10 grid size-32 -translate-x-1/2 -translate-y-1/2 place-items-center border border-cyan/40 bg-panel/80 shadow-control">
                <BrainCircuit className="size-10 text-cyan" />
                <span className="mt-2 text-center text-[10px] uppercase text-slate-400">AI company brain</span>
              </div>
            </article>

            <div className="grid gap-3 sm:grid-cols-2">
              {featureSignals.map((signal, index) => (
                <a key={signal.label} href={signal.href} className="cinematic-card floating-metric p-3" style={{ animationDelay: `${index * 140}ms` }}>
                  <div className="hud-content flex items-center justify-between gap-3">
                    <span className="inline-flex items-center gap-2 text-xs uppercase text-cyan">
                      <signal.icon className="size-4" />
                      {signal.label}
                    </span>
                    <strong className="text-sm text-white">{signal.value}</strong>
                  </div>
                </a>
              ))}
            </div>

            <article className="cinematic-card p-4">
              <div className="hud-content">
                <div className="flex items-center gap-2 text-xs uppercase text-mint">
                  <Workflow className="size-4" />
                  <span>Problem to prediction to recovery sequence</span>
                </div>
                <div className="mt-4 grid gap-2">
                  {demoSteps.map((step, index) => (
                    <div key={step} className="flex items-center gap-3 border border-line/60 bg-void/45 px-3 py-2">
                      <span className="grid size-7 place-items-center border border-cyan/30 bg-cyan/10 text-xs text-cyan">{index + 1}</span>
                      <span className="text-sm text-slate-300">{step}</span>
                    </div>
                  ))}
                </div>
              </div>
            </article>
          </div>
        </div>
      </div>
    </section>
  );
}

function CinematicMetric({ metric, delay }: { metric: EnterpriseMetric; delay: number }) {
  const positive = metric.trend >= 0;
  const tone =
    metric.status === "risk"
      ? "border-signal/35 text-signal"
      : metric.status === "watch"
        ? "border-amber/35 text-amber"
        : "border-mint/35 text-mint";
  const width = Math.min(100, Math.max(12, Math.abs(metric.trend) * 4 + 38));

  return (
    <article className="cinematic-card p-4" style={{ animationDelay: `${delay * 90}ms` }}>
      <div className="hud-content">
        <div className="flex items-center justify-between gap-2">
          <p className="text-xs uppercase text-slate-500">{metric.label}</p>
          <span className={`border px-2 py-1 text-[10px] uppercase ${tone}`}>{metric.status}</span>
        </div>
        <strong className="count-up mt-4 block text-3xl font-semibold text-white">{metric.value}</strong>
        <div className="mt-4 flex items-center justify-between gap-3 text-xs">
          <span className={positive ? "text-mint" : "text-amber"}>{positive ? "rising" : "falling"} {Math.abs(metric.trend).toFixed(1)}%</span>
          <span className="text-slate-500">live signal</span>
        </div>
        <div className="hud-progress mt-2 h-1">
          <span style={{ width: `${width}%` }} />
        </div>
      </div>
    </article>
  );
}

function HeatCell({ department }: { department: DepartmentSignal }) {
  const health = Math.round((department.productivity + department.wellness + department.security + (100 - department.risk)) / 4);
  const tone = health >= 80 ? "border-mint/35 bg-mint/10 text-mint" : health >= 60 ? "border-amber/35 bg-amber/10 text-amber" : "alert-glow border-signal/40 bg-signal/10 text-signal";

  return (
    <div className={`border p-3 ${tone}`}>
      <div className="flex items-center justify-between gap-2">
        <span className="truncate text-xs uppercase">{department.department}</span>
        <strong className="text-sm">{health}</strong>
      </div>
      <div className="hud-progress mt-3 h-1">
        <span style={{ width: `${health}%` }} />
      </div>
    </div>
  );
}

function RiskAlert({ risk }: { risk: RiskSignal }) {
  const critical = risk.impact === "critical" || risk.impact === "high";
  return (
    <div className={`border p-3 ${critical ? "alert-glow border-signal/40 bg-signal/10" : "border-amber/30 bg-amber/10"}`}>
      <div className="flex items-center justify-between gap-3">
        <span className="text-sm font-medium text-white">{risk.name}</span>
        <span className={critical ? "text-xs uppercase text-signal" : "text-xs uppercase text-amber"}>{risk.impact}</span>
      </div>
      <p className="mt-2 text-xs leading-5 text-slate-400">{risk.recommendation}</p>
    </div>
  );
}

function HudNode({
  className,
  icon: Icon,
  label,
  value,
}: {
  className: string;
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
}) {
  return (
    <div className={`hud-node ${className}`}>
      <Icon className="mb-1 size-4 text-cyan" />
      <span className="text-[10px] uppercase text-slate-500">{label}</span>
      <strong className="text-xs uppercase text-white">{value}</strong>
    </div>
  );
}

function MiniProof({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
}) {
  return (
    <div className="border border-line/60 bg-void/45 p-3">
      <span className="inline-flex items-center gap-2 text-[10px] uppercase text-slate-500">
        <Icon className="size-3.5 text-cyan" />
        {label}
      </span>
      <strong className="mt-1 block text-lg text-white">{value}</strong>
    </div>
  );
}

function formatMoney(value?: number) {
  if (typeof value !== "number") return "verifying";
  if (Math.abs(value) >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (Math.abs(value) >= 1_000) return `$${Math.round(value / 1_000)}K`;
  return `$${Math.round(value)}`;
}
