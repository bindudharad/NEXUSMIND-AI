"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type React from "react";
import { Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import {
  AlertTriangle,
  Bot,
  BrainCircuit,
  CircleDollarSign,
  GitCompare,
  Loader2,
  Network,
  RefreshCw,
  Send,
  ShieldCheck,
  Sparkles,
  Users,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import type { StrategicDecisionResponse, StrategicDecisionOption } from "@/types/strategic-decision";
import type { WhatIfRiskLevel } from "@/types/what-if-decision";

const DEMO_QUESTION = "Should we reduce workforce by 20%?";

const presets = [
  DEMO_QUESTION,
  "Should we hire 50 engineers?",
  "Should we expand to a new market?",
  "Should we cut costs by 15%?",
  "Should we delay Project Alpha?",
  "Should we close a department?",
  "Should we increase hiring?",
];

const demoSteps = [
  "Executive question received",
  "What-If future simulation running",
  "Shadow Company branch generated",
  "Digital twins projecting changes",
  "Chain reaction visualized",
  "AI Boardroom debating",
  "Impact panel calculated",
  "Recommendation generated",
];

const riskTone: Record<WhatIfRiskLevel, string> = {
  low: "border-mint/35 bg-mint/10 text-mint",
  medium: "border-cyan/35 bg-cyan/10 text-cyan",
  high: "border-amber/35 bg-amber/10 text-amber",
  critical: "border-rose/35 bg-rose/10 text-rose",
};

const inputClass = "w-full border border-line bg-void px-3 py-2 text-sm text-white outline-none focus:border-cyan/60";

export function StrategicDecisionIntelligencePanel() {
  const [decision, setDecision] = useState<StrategicDecisionResponse | null>(null);
  const [question, setQuestion] = useState(DEMO_QUESTION);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [demoRunning, setDemoRunning] = useState(false);
  const [demoStep, setDemoStep] = useState("");
  const [streamStatus, setStreamStatus] = useState("connecting");
  const [error, setError] = useState("");
  const manualUntil = useRef(0);

  const loadDefault = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/strategic/decision-engine/default", { cache: "no-store" });
      if (!response.ok) throw new Error("Strategic Decision Intelligence default failed");
      setDecision((await response.json()) as StrategicDecisionResponse);
      setStreamStatus((current) => (current === "connecting" ? "polling" : current));
    } catch {
      setError("Strategic Decision Intelligence Engine could not load.");
    } finally {
      setLoading(false);
    }
  }, []);

  const ask = useCallback(async (override?: string) => {
    const prompt = override ?? question;
    if (!prompt.trim()) return;
    setRunning(true);
    setError("");
    manualUntil.current = Date.now() + 30000;
    try {
      const response = await fetch("/api/strategic/decision-engine/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: prompt, horizon_months: 12 }),
        cache: "no-store",
      });
      if (!response.ok) throw new Error("Strategic Decision Intelligence ask failed");
      setDecision((await response.json()) as StrategicDecisionResponse);
    } catch {
      setError("Strategic decision simulation failed.");
    } finally {
      setRunning(false);
    }
  }, [question]);

  const runDemo = useCallback(async () => {
    setQuestion(DEMO_QUESTION);
    setDemoRunning(true);
    demoSteps.forEach((step, index) => {
      window.setTimeout(() => setDemoStep(step), index * 520);
    });
    await ask(DEMO_QUESTION);
    window.setTimeout(() => {
      setDemoStep(demoSteps[demoSteps.length - 1]);
      setDemoRunning(false);
    }, demoSteps.length * 520);
  }, [ask]);

  useEffect(() => {
    const timer = window.setTimeout(() => void loadDefault(), 0);
    return () => window.clearTimeout(timer);
  }, [loadDefault]);

  useEffect(() => {
    const source = new EventSource("/api/strategic/decision-engine/stream");
    source.addEventListener("strategic_decision", (event) => {
      try {
        const payload = JSON.parse((event as MessageEvent).data) as StrategicDecisionResponse;
        if (Date.now() > manualUntil.current) setDecision(payload);
        setStreamStatus("live");
        setLoading(false);
      } catch {
        setStreamStatus((current) => (current === "live" ? "live" : "degraded"));
      }
    });
    source.onerror = () => setStreamStatus((current) => (current === "live" ? "live" : "degraded"));
    return () => source.close();
  }, []);

  const chainData = useMemo(
    () =>
      decision?.chainReaction.map((step) => ({
        name: `${step.step}`,
        baseline: Math.round(step.baseline),
        projected: Math.round(step.projected),
        delta: Math.round(Math.abs(step.delta)),
      })) ?? [],
    [decision],
  );

  const futureData = useMemo(
    () =>
      decision?.whatIfSimulation.timeline.slice(0, 13).map((point) => ({
        month: `M${point.month}`,
        revenue: Math.round(point.revenue / 1_000_000),
        burnout: Math.round(point.burnout),
        risk: Math.round(point.riskScore),
      })) ?? [],
    [decision],
  );

  const demoProgress = Math.max(0, demoSteps.indexOf(demoStep));

  return (
    <section data-testid="strategic-decision-intelligence-panel" id="strategic-decision-intelligence-panel" className="w-full max-w-[calc(100vw-2rem)] overflow-hidden border border-cyan/30 bg-panel/90 p-5 shadow-control backdrop-blur lg:max-w-full">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div className="min-w-0 max-w-[calc(100vw-4rem)] xl:max-w-5xl">
          <div className="flex flex-wrap items-center gap-2 text-xs uppercase text-cyan">
            <BrainCircuit className="size-4" />
            <span>Strategic Decision Intelligence Engine</span>
            <span className="border border-cyan/25 bg-cyan/10 px-2 py-1 text-cyan">{streamStatus}</span>
            <span className="border border-mint/25 bg-mint/10 px-2 py-1 text-mint">{decision?.finalVerdict ?? "loading"}</span>
          </div>
          <h2 className="mt-2 break-words text-2xl font-semibold text-white">Simulate executive decisions before the company pays for them</h2>
          <p className="mt-3 break-words text-sm leading-6 text-slate-400">
            {decision?.executiveAnswer ??
              "Ask a strategic decision in natural language. The engine runs What-If forecasting, Shadow Company simulation, digital twin projection, chain reaction modeling, boardroom reasoning, and executive impact analysis."}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button type="button" onClick={() => void runDemo()} className="inline-flex h-10 items-center justify-center gap-2 border border-cyan/50 bg-cyan/15 px-3 text-sm text-cyan transition hover:border-cyan">
            {demoRunning ? <Loader2 className="size-4 animate-spin" /> : <Sparkles className="size-4" />}
            Billion Dollar Decision Demo
          </button>
          <button type="button" onClick={() => void loadDefault()} className="inline-flex h-10 items-center justify-center gap-2 border border-line bg-panel2 px-3 text-sm text-white transition hover:border-cyan/60">
            {loading ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />}
            Refresh
          </button>
        </div>
      </div>

      {error ? <div className="mt-4 border border-rose/40 bg-rose/10 px-3 py-2 text-sm text-rose">{error}</div> : null}

      <div className="mt-5 grid gap-3 md:grid-cols-3 xl:grid-cols-6">
        <Metric icon={AlertTriangle} label="Strategic risk" value={decision ? `${Math.round(decision.strategicRiskScore)}/100` : "loading"} />
        <Metric icon={ShieldCheck} label="Confidence" value={decision ? `${Math.round(decision.confidenceScore)}%` : "loading"} />
        <Metric icon={CircleDollarSign} label="Financial loss" value={decision ? formatMoney(decision.impactPanel.financialLoss) : "loading"} />
        <Metric icon={Network} label="Delay probability" value={decision ? `${Math.round(decision.impactPanel.delayProbability)}%` : "loading"} />
        <Metric icon={Users} label="Hiring need" value={decision ? `${decision.impactPanel.hiringRequirements.requiredHires} hires` : "loading"} />
        <Metric icon={GitCompare} label="Options" value={decision ? String(decision.decisionOptions.length) : "loading"} />
      </div>

      {(demoRunning || demoStep) ? (
        <div data-testid="billion-dollar-decision-demo" className="mt-5 border border-cyan/30 bg-cyan/5 p-4">
          <div className="flex flex-col gap-2 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <div className="text-xs uppercase text-cyan">Billion Dollar Decision Demo</div>
              <div className="mt-1 text-lg font-semibold text-white">{demoStep || "Ready"}</div>
            </div>
            <div className="text-sm text-slate-300">{DEMO_QUESTION}</div>
          </div>
          <div className="mt-4 grid gap-2 md:grid-cols-4">
            {demoSteps.map((step, index) => (
              <div key={step} className={`border px-3 py-2 text-xs ${index <= demoProgress ? "border-cyan/50 bg-cyan/15 text-cyan" : "border-line/60 bg-void/35 text-slate-500"}`}>
                {step}
              </div>
            ))}
          </div>
        </div>
      ) : null}

      <Panel title="Natural-language strategic decision" icon={Bot}>
        <div className="grid gap-2 md:grid-cols-4">
          {presets.map((item) => (
            <button
              type="button"
              key={item}
              onClick={() => {
                setQuestion(item);
                void ask(item);
              }}
              className="border border-line bg-void px-3 py-2 text-left text-xs text-slate-300 transition hover:border-cyan/60 hover:text-white"
            >
              {item}
            </button>
          ))}
        </div>
        <div className="mt-4 flex flex-col gap-2 sm:flex-row">
          <input value={question} onChange={(event) => setQuestion(event.target.value)} className={inputClass} />
          <button type="button" onClick={() => void ask()} className="inline-flex h-10 items-center justify-center gap-2 border border-cyan/45 bg-cyan/10 px-4 text-sm text-cyan transition hover:border-cyan">
            {running ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
            Ask
          </button>
        </div>
      </Panel>

      {decision ? (
        <>
          <div className="mt-4 grid gap-4 xl:grid-cols-[1.05fr_0.95fr]">
            <Panel title="Decision comparison" icon={GitCompare}>
              <div className="grid gap-3 lg:grid-cols-3">
                {decision.decisionOptions.map((option) => (
                  <DecisionOption key={option.optionId} option={option} />
                ))}
              </div>
            </Panel>
            <Panel title="Executive impact analysis" icon={CircleDollarSign}>
              <div className="grid gap-3 sm:grid-cols-2">
                <Impact label="Financial loss" value={formatMoney(decision.impactPanel.financialLoss)} />
                <Impact label="Delay probability" value={`${Math.round(decision.impactPanel.delayProbability)}%`} />
                <Impact label="Strategic risk" value={`${Math.round(decision.strategicRiskScore)}/100`} />
                <Impact label="Confidence" value={`${Math.round(decision.confidenceScore)}%`} />
              </div>
              <div className="mt-4 border border-line bg-void p-3 text-sm leading-6 text-slate-300">{decision.recommendedAction}</div>
            </Panel>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
            <Panel title="Chain reaction engine" icon={Network}>
              <div className="grid gap-2">
                {decision.chainReaction.map((step) => (
                  <div key={step.step} className={`border p-3 ${riskTone[step.severity]}`}>
                    <div className="flex items-center justify-between gap-3">
                      <span className="text-sm font-semibold text-white">{step.step}. {step.title}</span>
                      <span className="text-xs uppercase">{step.severity}</span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-300">{step.explanation}</p>
                    <p className="mt-2 text-xs text-slate-400">Delta {formatNumber(step.delta)}</p>
                  </div>
                ))}
              </div>
            </Panel>
            <Panel title="Live future visualization" icon={Sparkles}>
              <div className="h-72 min-w-0">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={futureData}>
                    <CartesianGrid stroke="#213144" strokeDasharray="3 3" />
                    <XAxis dataKey="month" tick={{ fill: "#94a3b8", fontSize: 12 }} />
                    <YAxis tick={{ fill: "#94a3b8", fontSize: 12 }} />
                    <Tooltip contentStyle={{ background: "#101827", border: "1px solid #22324a", color: "#fff" }} />
                    <Line type="monotone" dataKey="revenue" stroke="#22d3ee" strokeWidth={2} name="Revenue $M" />
                    <Line type="monotone" dataKey="burnout" stroke="#fb7185" strokeWidth={2} name="Burnout" />
                    <Line type="monotone" dataKey="risk" stroke="#f59e0b" strokeWidth={2} name="Risk" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
              <div className="mt-4 h-56 min-w-0">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chainData}>
                    <CartesianGrid stroke="#213144" strokeDasharray="3 3" />
                    <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 12 }} />
                    <YAxis tick={{ fill: "#94a3b8", fontSize: 12 }} />
                    <Tooltip contentStyle={{ background: "#101827", border: "1px solid #22324a", color: "#fff" }} />
                    <Bar dataKey="delta" fill="#a78bfa" name="Chain delta" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Panel>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[1fr_1fr]">
            <Panel title="AI Boardroom" icon={BrainCircuit}>
              <div className="grid gap-2">
                {decision.boardroomFindings.map((finding) => (
                  <div key={`${finding.agent}-${finding.perspective}`} className="border border-line bg-void p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="text-sm font-semibold text-white">{finding.agent}</span>
                      <span className="text-xs text-cyan">{Math.round(finding.confidence * 100)}% confidence</span>
                    </div>
                    <p className="mt-2 text-xs uppercase text-slate-500">{finding.perspective}</p>
                    <p className="mt-2 text-sm leading-6 text-slate-300">{finding.finding}</p>
                    <p className="mt-2 text-xs leading-5 text-mint">{finding.recommendation}</p>
                  </div>
                ))}
              </div>
            </Panel>
            <Panel title="Shadow Company future state" icon={ShieldCheck}>
              <div className="grid gap-3 sm:grid-cols-2">
                <Impact label="Current employees" value={String(decision.shadowCompanySimulation.baselineOutcome.employees)} />
                <Impact label="Future employees" value={String(decision.shadowCompanySimulation.simulatedOutcome.employees)} />
                <Impact label="Current risk" value={`${Math.round(decision.shadowCompanySimulation.baselineOutcome.riskScore)}/100`} />
                <Impact label="Future risk" value={`${Math.round(decision.shadowCompanySimulation.simulatedOutcome.riskScore)}/100`} />
                <Impact label="Current health" value={`${Math.round(decision.shadowCompanySimulation.baselineOutcome.workforceHealth)}/100`} />
                <Impact label="Future health" value={`${Math.round(decision.shadowCompanySimulation.simulatedOutcome.workforceHealth)}/100`} />
              </div>
              <div className="mt-4 border border-line bg-void p-3 text-sm leading-6 text-slate-300">
                {decision.shadowCompanySimulation.executiveSummary}
              </div>
            </Panel>
          </div>
        </>
      ) : null}
    </section>
  );
}

function Metric({ icon: Icon, label, value }: { icon: LucideIcon; label: string; value: string }) {
  return (
    <div className="border border-line bg-void p-4">
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
    <article className="mt-4 min-w-0 border border-line bg-panel2/80 p-4">
      <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-white">
        <Icon className="size-4 text-cyan" />
        <span>{title}</span>
      </div>
      {children}
    </article>
  );
}

function DecisionOption({ option }: { option: StrategicDecisionOption }) {
  return (
    <div className={`border bg-void p-4 ${option.recommended ? "border-mint/50 shadow-[0_0_24px_rgba(52,211,153,0.14)]" : "border-line"}`}>
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs uppercase text-slate-500">{option.title}</span>
        <span className={`border px-2 py-1 text-[10px] uppercase ${option.recommended ? "border-mint/40 text-mint" : "border-line text-slate-400"}`}>
          {option.recommended ? "recommended" : "option"}
        </span>
      </div>
      <p className="mt-3 text-xs leading-5 text-slate-400">{option.description}</p>
      <div className="mt-4 grid gap-2 text-xs">
        <Impact label="Risk" value={`${Math.round(option.riskScore)}/100`} />
        <Impact label="Revenue" value={formatPercent(option.revenueImpactPercent)} />
        <Impact label="Cost" value={formatPercent(option.costImpactPercent)} />
        <Impact label="Burnout" value={`${formatNumber(option.burnoutImpactPoints)} pts`} />
        <Impact label="Productivity" value={formatPercent(option.productivityImpactPercent)} />
        <Impact label="Readiness" value={`${Math.round(option.decisionReadinessScore)}/100`} />
      </div>
      <p className="mt-4 text-xs leading-5 text-slate-300">{option.recommendation}</p>
    </div>
  );
}

function Impact({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3 border border-line/70 bg-panel/50 px-3 py-2 text-xs">
      <span className="text-slate-500">{label}</span>
      <strong className="text-right text-white">{value}</strong>
    </div>
  );
}

function formatMoney(value: number) {
  const sign = value < 0 ? "-" : "";
  return `${sign}$${Math.round(Math.abs(value)).toLocaleString()}`;
}

function formatPercent(value: number) {
  const prefix = value > 0 ? "+" : "";
  return `${prefix}${value.toFixed(1)}%`;
}

function formatNumber(value: number) {
  const prefix = value > 0 ? "+" : "";
  return `${prefix}${Math.round(value).toLocaleString()}`;
}
