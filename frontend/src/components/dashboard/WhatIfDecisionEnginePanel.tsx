"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type React from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  AlertTriangle,
  Bot,
  BriefcaseBusiness,
  Building2,
  CircleDollarSign,
  Database,
  GitCompare,
  Loader2,
  Network,
  RefreshCw,
  Save,
  Send,
  ShieldCheck,
  Sparkles,
  TrendingUp,
  Users,
  Workflow,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import type {
  WhatIfAssistantResponse,
  WhatIfDecisionDashboardResponse,
  WhatIfImpactMetric,
  WhatIfRecommendation,
  WhatIfRiskItem,
  WhatIfRiskLevel,
  WhatIfScenarioRequest,
  WhatIfScenarioType,
  WhatIfSimulationResponse,
} from "@/types/what-if-decision";

const scenarioTypes: { value: WhatIfScenarioType; label: string }[] = [
  { value: "hiring", label: "Hiring" },
  { value: "layoff", label: "Layoff" },
  { value: "budget_reduction", label: "Budget reduction" },
  { value: "major_client_loss", label: "Major client loss" },
  { value: "international_expansion", label: "International expansion" },
  { value: "engineer_resignation", label: "Engineer resignation" },
  { value: "new_product_launch", label: "New product launch" },
  { value: "department_restructure", label: "Department restructure" },
  { value: "revenue_drop", label: "Revenue drop" },
];

const presets = [
  "What if 30 employees resign tomorrow?",
  "What happens if we hire 50 employees?",
  "What happens if we reduce budget by 20%?",
  "What happens if we lose our largest client?",
  "What happens if we expand internationally?",
  "What happens if 25 engineers resign?",
  "What happens if we launch a new product?",
];

const WHAT_IF_DEMO_PROMPT = "What if 30 employees resign tomorrow?";

const demoSteps = [
  "Scenario received",
  "Digital twins updating",
  "Team health recalculating",
  "Revenue forecast shifting",
  "Project risks surfacing",
  "AI agent council analyzing",
  "Recovery strategy generated",
  "Executive recommendation displayed",
];

const riskTone: Record<WhatIfRiskLevel, string> = {
  low: "border-mint/35 bg-mint/10 text-mint",
  medium: "border-cyan/35 bg-cyan/10 text-cyan",
  high: "border-amber/35 bg-amber/10 text-amber",
  critical: "border-rose/35 bg-rose/10 text-rose",
};

const riskFill: Record<WhatIfRiskLevel, string> = {
  low: "bg-mint",
  medium: "bg-cyan",
  high: "bg-amber",
  critical: "bg-rose",
};

const defaultScenario: WhatIfScenarioRequest = {
  scenarioId: "frontend-hire-50",
  scenarioName: "Hire 50 employees",
  question: "What happens if we hire 50 employees?",
  scenarioType: "hiring",
  horizonMonths: 12,
  employeeDelta: 50,
  targetDepartment: "Engineering",
  targetRegion: "Global",
  budgetDeltaPercent: 0,
  revenueDeltaPercent: 0,
  clientLossPercent: 0,
  expansionInvestment: 0,
  newProductInvestment: 0,
  affectedClient: "Largest client",
  notes: "",
};

const inputClass = "w-full border border-line bg-void px-3 py-2 text-sm text-white outline-none focus:border-cyan/60";

export function WhatIfDecisionEnginePanel() {
  const [dashboard, setDashboard] = useState<WhatIfDecisionDashboardResponse | null>(null);
  const [selected, setSelected] = useState<WhatIfSimulationResponse | null>(null);
  const [assistant, setAssistant] = useState<WhatIfAssistantResponse | null>(null);
  const [scenario, setScenario] = useState<WhatIfScenarioRequest>(defaultScenario);
  const [question, setQuestion] = useState(presets[0]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [demoRunning, setDemoRunning] = useState(false);
  const [demoStep, setDemoStep] = useState("");
  const [streamStatus, setStreamStatus] = useState("connecting");
  const [error, setError] = useState("");
  const manualScenarioUntil = useRef(0);

  const loadDefault = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/what-if/decision-engine/default", { cache: "no-store" });
      if (!response.ok) throw new Error("What-If Decision Engine default failed");
      const payload = (await response.json()) as WhatIfDecisionDashboardResponse;
      setDashboard(payload);
      setSelected((current) => current ?? payload.scenarios[0] ?? null);
      setStreamStatus((current) => (current === "connecting" ? "polling" : current));
    } catch {
      setError("What-If Decision Engine could not load.");
    } finally {
      setLoading(false);
    }
  }, []);

  const runScenario = useCallback(async (payload: WhatIfScenarioRequest, persist = false) => {
    setRunning(true);
    setError("");
    manualScenarioUntil.current = Date.now() + 30000;
    try {
      const response = await fetch(`/api/what-if/decision-engine/${persist ? "scenarios" : "simulate"}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(toSnake(payload)),
        cache: "no-store",
      });
      if (!response.ok) throw new Error("What-If scenario failed");
      if (persist) {
        const record = (await response.json()) as { simulation: WhatIfSimulationResponse };
        setSelected(record.simulation);
        void loadDefault();
      } else {
        setSelected((await response.json()) as WhatIfSimulationResponse);
      }
    } catch {
      setError("Scenario simulation failed.");
    } finally {
      setRunning(false);
    }
  }, [loadDefault]);

  const ask = useCallback(async (override?: string) => {
    const prompt = override ?? question;
    if (!prompt.trim()) return;
    setRunning(true);
    setError("");
    manualScenarioUntil.current = Date.now() + 30000;
    try {
      const response = await fetch("/api/what-if/decision-engine/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: prompt, horizon_months: scenario.horizonMonths }),
        cache: "no-store",
      });
      if (!response.ok) throw new Error("What-If assistant failed");
      const payload = (await response.json()) as WhatIfAssistantResponse;
      setAssistant(payload);
      setSelected(payload.simulation);
    } catch {
      setError("Strategy assistant could not answer the scenario.");
    } finally {
      setRunning(false);
    }
  }, [question, scenario.horizonMonths]);

  const runDemo = useCallback(async () => {
    setDemoRunning(true);
    setQuestion(WHAT_IF_DEMO_PROMPT);
    demoSteps.forEach((step, index) => {
      window.setTimeout(() => setDemoStep(step), index * 520);
    });
    try {
      await ask(WHAT_IF_DEMO_PROMPT);
      window.setTimeout(() => {
        setDemoStep(demoSteps[demoSteps.length - 1]);
        setDemoRunning(false);
      }, demoSteps.length * 520);
    } catch {
      setDemoRunning(false);
    }
  }, [ask]);

  useEffect(() => {
    const timer = window.setTimeout(() => void loadDefault(), 0);
    return () => window.clearTimeout(timer);
  }, [loadDefault]);

  useEffect(() => {
    const source = new EventSource("/api/what-if/decision-engine/stream");
    source.addEventListener("what_if_decision", (event) => {
      try {
        const payload = JSON.parse((event as MessageEvent).data) as WhatIfSimulationResponse;
        if (Date.now() > manualScenarioUntil.current) setSelected(payload);
        setStreamStatus("live");
        setLoading(false);
      } catch {
        setStreamStatus((current) => (current === "live" ? "live" : "degraded"));
      }
    });
    source.onerror = () => setStreamStatus((current) => (current === "live" ? "live" : "degraded"));
    return () => source.close();
  }, []);

  const topRisk = useMemo(() => {
    if (!selected?.riskAnalysis.length) return null;
    return selected.riskAnalysis.reduce((highest, risk) => (risk.probability * risk.impact > highest.probability * highest.impact ? risk : highest));
  }, [selected]);

  const metricBars = useMemo(() => {
    if (!selected) return [];
    return [
      metricBar(selected.financialImpact, "Revenue Forecast"),
      metricBar(selected.financialImpact, "Profit Forecast"),
      metricBar(selected.productivityImpact, "Productivity"),
      metricBar(selected.burnoutImpact, "Burnout Risk"),
      metricBar(selected.productivityImpact, "Delivery Speed"),
    ].filter(Boolean) as { name: string; delta: number }[];
  }, [selected]);

  const demoProgress = Math.max(0, demoSteps.indexOf(demoStep));

  return (
    <section id="what-if-decision-engine-panel" data-testid="what-if-decision-engine-panel" className="w-full max-w-[calc(100vw-2rem)] overflow-hidden border border-cyan/30 bg-panel/90 p-5 shadow-control backdrop-blur lg:max-w-full">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div className="min-w-0 max-w-[calc(100vw-4rem)] xl:max-w-5xl">
          <div className="flex flex-wrap items-center gap-2 text-xs uppercase text-cyan">
            <GitCompare className="size-4" />
            <span>What-If Decision Engine</span>
            <span className="border border-cyan/25 bg-cyan/10 px-2 py-1 text-cyan">{streamStatus}</span>
            <span className="border border-mint/25 bg-mint/10 px-2 py-1 text-mint">{selected?.finalVerdict ?? "loading"}</span>
          </div>
          <h2 className="mt-2 break-words text-2xl font-semibold text-white">Enterprise strategy simulator for decisions before execution</h2>
          <p className="mt-3 break-words text-sm leading-6 text-slate-400">
            {selected
              ? selected.executiveSummary
              : "Building financial, workforce, productivity, burnout, infrastructure, risk, recommendation, digital twin, and agent council projections."}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button type="button" onClick={() => void runDemo()} className="inline-flex h-10 items-center justify-center gap-2 border border-cyan/50 bg-cyan/15 px-3 text-sm text-cyan transition hover:border-cyan">
            {demoRunning ? <Loader2 className="size-4 animate-spin" /> : <Sparkles className="size-4" />}
            Show The Future
          </button>
          <button type="button" onClick={() => void loadDefault()} className="inline-flex h-10 items-center justify-center gap-2 border border-line bg-panel2 px-3 text-sm text-white transition hover:border-cyan/60">
            {loading ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />}
            Refresh
          </button>
        </div>
      </div>

      {error ? <div className="mt-4 border border-rose/40 bg-rose/10 px-3 py-2 text-sm text-rose">{error}</div> : null}

      <div className="mt-5 grid gap-3 md:grid-cols-3 xl:grid-cols-6">
        <Metric icon={ShieldCheck} label="Readiness" value={selected ? `${Math.round(selected.decisionReadinessScore)}/100` : "loading"} />
        <Metric icon={TrendingUp} label="Success" value={selected ? `${Math.round(selected.successProbability)}%` : "loading"} />
        <Metric icon={AlertTriangle} label="Risk" value={selected?.riskLevel ?? "loading"} />
        <Metric icon={CircleDollarSign} label="Revenue" value={selected ? formatMetric(metric(selected.financialImpact, "Revenue Forecast")) : "loading"} />
        <Metric icon={Users} label="Headcount" value={selected ? formatMetric(metric(selected.workforceImpact, "Headcount")) : "loading"} />
        <Metric icon={Network} label="Twin Sync" value={selected ? `${selected.digitalTwinSync.length} twins` : "loading"} />
      </div>

      {(demoRunning || demoStep) ? (
        <div data-testid="what-if-demo-mode" className="mt-5 border border-cyan/30 bg-cyan/5 p-4">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <div className="text-xs uppercase text-cyan">What-If Demo Mode</div>
              <div className="mt-1 text-lg font-semibold text-white">{demoStep || "Ready to simulate the future"}</div>
            </div>
            <div className="text-sm text-slate-300">{WHAT_IF_DEMO_PROMPT}</div>
          </div>
          <div className="mt-4 grid gap-2 md:grid-cols-4">
            {demoSteps.map((step, index) => (
              <div
                key={step}
                className={`border px-3 py-2 text-xs ${
                  index <= demoProgress ? "border-cyan/50 bg-cyan/15 text-cyan" : "border-line/60 bg-void/35 text-slate-500"
                }`}
              >
                {step}
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {selected?.executiveImpactAnalysis ? (
        <ExecutiveImpactAnalysisPanel simulation={selected} />
      ) : null}

      <div className="mt-5 grid gap-4 xl:grid-cols-[0.8fr_1.2fr]">
        <Panel title="Scenario Builder" icon={Bot}>
          <div className="grid gap-2 sm:grid-cols-2">
            {dashboard?.scenarioBuilderTemplates.map((item) => (
              <button
                type="button"
                key={item.scenarioId}
                onClick={() => {
                  setScenario(item);
                  setQuestion(item.question);
                  void runScenario(item);
                }}
                className="border border-line/60 bg-void/35 p-2 text-left text-xs leading-5 text-slate-300 transition hover:border-cyan/50 hover:text-white"
              >
                <span className="block text-sm text-white">{item.scenarioName}</span>
                <span>{item.question}</span>
              </button>
            ))}
          </div>

          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <Field label="Scenario name">
              <input value={scenario.scenarioName} onChange={(event) => updateScenario(setScenario, { scenarioName: event.target.value })} className={inputClass} />
            </Field>
            <Field label="Scenario type">
              <select
                value={scenario.scenarioType}
                onChange={(event) => updateScenario(setScenario, { scenarioType: event.target.value as WhatIfScenarioType })}
                className={inputClass}
              >
                {scenarioTypes.map((item) => (
                  <option key={item.value} value={item.value}>
                    {item.label}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Horizon months">
              <input type="number" min={1} max={36} value={scenario.horizonMonths} onChange={(event) => updateScenario(setScenario, { horizonMonths: numberValue(event.target.value, 12) })} className={inputClass} />
            </Field>
            <Field label="Workforce capacity delta">
              <input type="number" value={scenario.employeeDelta} onChange={(event) => updateScenario(setScenario, { employeeDelta: numberValue(event.target.value, 0) })} className={inputClass} />
            </Field>
            <Field label="Budget delta %">
              <input type="number" value={scenario.budgetDeltaPercent} onChange={(event) => updateScenario(setScenario, { budgetDeltaPercent: numberValue(event.target.value, 0) })} className={inputClass} />
            </Field>
            <Field label="Revenue delta %">
              <input type="number" value={scenario.revenueDeltaPercent} onChange={(event) => updateScenario(setScenario, { revenueDeltaPercent: numberValue(event.target.value, 0) })} className={inputClass} />
            </Field>
            <Field label="Client loss %">
              <input type="number" min={0} max={100} value={scenario.clientLossPercent} onChange={(event) => updateScenario(setScenario, { clientLossPercent: numberValue(event.target.value, 0) })} className={inputClass} />
            </Field>
            <Field label="Expansion investment">
              <input type="number" min={0} value={scenario.expansionInvestment} onChange={(event) => updateScenario(setScenario, { expansionInvestment: numberValue(event.target.value, 0) })} className={inputClass} />
            </Field>
          </div>

          <textarea
            value={question}
            onChange={(event) => {
              setQuestion(event.target.value);
              updateScenario(setScenario, { question: event.target.value });
            }}
            rows={2}
            className="mt-3 w-full border border-line bg-void px-3 py-2 text-sm text-white outline-none focus:border-cyan/60"
            aria-label="Strategy question"
          />
          <div className="mt-3 flex flex-wrap gap-2">
            <button type="button" onClick={() => void runScenario({ ...scenario, scenarioId: normalizeScenarioId(scenario.scenarioName) })} className="inline-flex min-h-10 items-center gap-2 border border-cyan/40 bg-cyan/10 px-3 text-sm text-cyan">
              {running ? <Loader2 className="size-4 animate-spin" /> : <Workflow className="size-4" />}
              Run scenario
            </button>
            <button type="button" onClick={() => void runScenario({ ...scenario, scenarioId: normalizeScenarioId(scenario.scenarioName) }, true)} className="inline-flex min-h-10 items-center gap-2 border border-mint/40 bg-mint/10 px-3 text-sm text-mint">
              <Save className="size-4" />
              Save + run
            </button>
            <button type="button" onClick={() => void ask()} className="inline-flex min-h-10 items-center gap-2 border border-line bg-panel2 px-3 text-sm text-white">
              <Send className="size-4" />
              Ask assistant
            </button>
          </div>
        </Panel>

        <Panel title="Future Impact Timeline" icon={TrendingUp}>
          <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
            <div className="h-80 min-w-0">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={selected?.timeline ?? []} margin={{ left: 4, right: 12, top: 8, bottom: 8 }}>
                  <CartesianGrid stroke="#1C2B3A" strokeDasharray="3 3" />
                  <XAxis dataKey="month" stroke="#64748b" tickLine={false} axisLine={false} />
                  <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={{ background: "#08111f", border: "1px solid #223044", color: "#e2e8f0" }} />
                  <Line type="monotone" dataKey="productivity" name="Productivity" stroke="#2EE9D3" strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="burnout" name="Burnout" stroke="#FF3B6B" strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="deliveryConfidence" name="Delivery" stroke="#7CF0A6" strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="riskScore" name="Risk" stroke="#F6B44B" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <div className="h-80 min-w-0">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={metricBars} margin={{ left: 4, right: 12, top: 8, bottom: 8 }}>
                  <CartesianGrid stroke="#1C2B3A" strokeDasharray="3 3" />
                  <XAxis dataKey="name" stroke="#64748b" tickLine={false} axisLine={false} interval={0} tick={{ fontSize: 10 }} />
                  <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={{ background: "#08111f", border: "1px solid #223044", color: "#e2e8f0" }} />
                  <Bar dataKey="delta" fill="#2EE9D3" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </Panel>
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-4">
        <ImpactList title="Financial Impact" metrics={selected?.financialImpact ?? []} />
        <ImpactList title="Workforce Impact" metrics={selected?.workforceImpact ?? []} />
        <ImpactList title="Productivity Impact" metrics={selected?.productivityImpact ?? []} />
        <ImpactList title="Burnout Impact" metrics={selected?.burnoutImpact ?? []} />
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
        <Panel title="Risk Analysis" icon={AlertTriangle}>
          <div className="space-y-3">
            {selected?.riskAnalysis.map((risk) => <RiskRow key={risk.riskId} risk={risk} />)}
          </div>
        </Panel>
        <Panel title="Recommendations + Agent Council" icon={Sparkles}>
          <div className="grid gap-3 lg:grid-cols-2">
            <div className="space-y-3">
              {(selected?.recommendations ?? []).slice(0, 5).map((item) => <RecommendationRow key={item.recommendationId} item={item} />)}
            </div>
            <div className="space-y-3">
              {(selected?.agentCouncil ?? []).map((agent) => (
                <div key={agent.agent} className="border border-line/60 bg-void/35 p-3">
                  <div className="flex items-center justify-between gap-3">
                    <div className="text-sm font-medium text-white">{agent.agent}</div>
                    <div className="text-xs text-cyan">{Math.round(agent.confidence * 100)}%</div>
                  </div>
                  <p className="mt-2 text-xs leading-5 text-slate-400">{agent.finding}</p>
                  <p className="mt-2 text-xs leading-5 text-mint">{agent.recommendation}</p>
                </div>
              ))}
            </div>
          </div>
        </Panel>
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-3">
        <Panel title="Infrastructure Capacity" icon={Building2}>
          <div className="grid gap-2 sm:grid-cols-2">
            <MiniStat label="Workstations" value={String(selected?.infrastructureImpact.workstations ?? 0)} />
            <MiniStat label="Meeting rooms" value={String(selected?.infrastructureImpact.meetingRooms ?? 0)} />
            <MiniStat label="Licenses" value={String(selected?.infrastructureImpact.softwareLicenses ?? 0)} />
            <MiniStat label="Capacity risk" value={`${Math.round(selected?.infrastructureImpact.officeCapacityRisk ?? 0)}%`} />
          </div>
          <ul className="mt-3 space-y-2">
            {(selected?.infrastructureImpact.plan ?? []).map((item) => (
              <li key={item} className="text-xs leading-5 text-slate-400">{item}</li>
            ))}
          </ul>
        </Panel>

        <Panel title="Scenario Comparison" icon={GitCompare}>
          <div className="space-y-3">
            {selected?.scenarioComparison.map((item) => (
              <div key={item.scenarioId} className="border border-line/60 bg-void/35 p-3">
                <div className="flex items-center justify-between gap-3">
                  <div className="text-sm font-medium text-white">{item.scenarioName}</div>
                  <div className="text-xs text-mint">{Math.round(item.readinessScore)} readiness</div>
                </div>
                <div className="mt-3 grid grid-cols-3 gap-2 text-xs">
                  <MiniStat label="Risk" value={`${Math.round(item.riskScore)}`} />
                  <MiniStat label="Upside" value={`${Math.round(item.upsideScore)}`} />
                  <MiniStat label="Cost" value={`${Math.round(item.costScore)}`} />
                </div>
                <p className="mt-2 text-xs leading-5 text-slate-400">{item.recommendation}</p>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Digital Twin Sync" icon={Database}>
          <div className="space-y-3">
            {selected?.digitalTwinSync.map((item) => (
              <div key={item.twin} className="border border-line/60 bg-void/35 p-3">
                <div className="flex items-center justify-between gap-3">
                  <div className="text-sm capitalize text-white">{item.twin} twin</div>
                  <div className="text-xs text-cyan">{item.entityCount} entities</div>
                </div>
                <p className="mt-2 text-xs leading-5 text-slate-400">{item.update}</p>
              </div>
            ))}
          </div>
        </Panel>
      </div>

      <div className="mt-4">
        <Panel title="Multi-Future Scenario Branches" icon={GitCompare}>
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {(selected?.futureBranches ?? []).map((branch) => (
              <div key={branch.caseName} className="border border-line/60 bg-void/35 p-3">
                <div className="flex items-center justify-between gap-3">
                  <div className="text-sm font-medium text-white">{formatBranchName(branch.caseName)}</div>
                  <div className="text-xs text-cyan">{Math.round(branch.probability)}% path</div>
                </div>
                <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
                  <MiniStat label="Success" value={`${Math.round(branch.successProbability)}%`} />
                  <MiniStat label="Risk" value={`${Math.round(branch.riskScore)}%`} />
                  <MiniStat label="Revenue" value={`${branch.revenueDelta > 0 ? "+" : ""}${Math.round(branch.revenueDelta)}%`} />
                  <MiniStat label="Burnout" value={`${branch.burnoutDelta > 0 ? "+" : ""}${Math.round(branch.burnoutDelta)} pts`} />
                </div>
                <p className="mt-2 text-xs leading-5 text-slate-400">{branch.explanation}</p>
                <p className="mt-2 text-xs leading-5 text-mint">{branch.recommendation}</p>
              </div>
            ))}
          </div>
        </Panel>
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
        <Panel title="Strategy AI Assistant" icon={Bot}>
          <div className="grid gap-2">
            {presets.map((item) => (
              <button
                key={item}
                type="button"
                onClick={() => {
                  setQuestion(item);
                  void ask(item);
                }}
                className="border border-line/60 bg-void/35 p-2 text-left text-xs leading-5 text-slate-300 transition hover:border-cyan/50 hover:text-white"
              >
                {item}
              </button>
            ))}
          </div>
          {assistant ? (
            <div className="mt-3 border border-cyan/25 bg-cyan/10 p-3">
              <div className="text-xs uppercase text-cyan">Assistant answer</div>
              <p className="mt-2 text-sm leading-6 text-white">{assistant.answer}</p>
            </div>
          ) : null}
        </Panel>

        <Panel title="Executive Explanation" icon={BriefcaseBusiness}>
          <div className="grid gap-3 lg:grid-cols-2">
            <div>
              <div className="text-xs uppercase text-cyan">Top risk driver</div>
              <p className="mt-2 text-sm leading-6 text-white">{topRisk ? `${topRisk.title}: ${Math.round(topRisk.probability)}% probability` : "loading"}</p>
              <p className="mt-2 text-xs leading-5 text-slate-400">{topRisk?.mitigation}</p>
            </div>
            <div>
              <div className="text-xs uppercase text-cyan">Model evidence</div>
              <ul className="mt-2 space-y-2">
                {(selected?.explanation ?? []).map((item) => (
                  <li key={item} className="text-xs leading-5 text-slate-400">{item}</li>
                ))}
              </ul>
            </div>
          </div>
        </Panel>
      </div>
    </section>
  );
}

function Panel({ title, icon: Icon, children }: { title: string; icon: LucideIcon; children: React.ReactNode }) {
  return (
    <div className="min-w-0 overflow-hidden border border-line/80 bg-panel2/70 p-4">
      <div className="mb-3 flex items-center gap-2 text-sm font-medium text-white">
        <Icon className="size-4 text-cyan" />
        {title}
      </div>
      {children}
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="grid gap-1 text-xs text-slate-400">
      <span>{label}</span>
      {children}
    </label>
  );
}

function Metric({ icon: Icon, label, value }: { icon: LucideIcon; label: string; value: string }) {
  return (
    <div className="min-w-0 border border-line bg-void/45 p-3">
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs uppercase text-slate-500">{label}</span>
        <Icon className="size-4 shrink-0 text-cyan" />
      </div>
      <div className="mt-2 truncate text-lg font-semibold text-white">{value}</div>
    </div>
  );
}

function ExecutiveImpactAnalysisPanel({ simulation }: { simulation: WhatIfSimulationResponse }) {
  const panel = simulation.executiveImpactAnalysis;
  const highestTeamImpact = Math.max(...panel.mostAffectedTeams.map((team) => team.impactScore), 1);
  return (
    <div data-testid="executive-impact-analysis-panel" className="mt-5 border border-mint/30 bg-gradient-to-br from-mint/10 via-panel2/80 to-cyan/10 p-4 shadow-control">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2 text-xs uppercase text-mint">
            <BriefcaseBusiness className="size-4" />
            <span>{panel.panelTitle}</span>
            <span className="border border-mint/30 bg-mint/10 px-2 py-1 text-mint">{panel.finalVerdict}</span>
            <span className={`border px-2 py-1 ${riskTone[panel.riskLevel]}`}>{panel.riskLevel}</span>
            <span className="border border-cyan/30 bg-cyan/10 px-2 py-1 text-cyan">{panel.triggerType.replaceAll("_", " ")}</span>
          </div>
          <h3 className="mt-2 text-xl font-semibold text-white">{panel.scenarioName}</h3>
          <p className="mt-2 max-w-4xl text-sm leading-6 text-slate-300">
            Financial, delivery, workforce, recovery, hiring, digital twin, and agent council impact analysis generated from the active simulation.
          </p>
        </div>
        <div className="border border-mint/25 bg-mint/10 px-3 py-2 text-sm text-mint">
          {Math.round(panel.confidenceScore)}% confidence
        </div>
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-5">
        <ImpactHeroMetric label="Financial Loss" value={formatMoney(panel.financialLoss)} detail={`Revenue ${formatSigned(panel.revenueImpactPercent)}%`} tone="rose" />
        <ImpactHeroMetric label="Delay Probability" value={`${Math.round(panel.delayProbability)}%`} detail={`Profit ${formatSigned(panel.profitImpactPercent)}%`} tone="amber" />
        <ImpactHeroMetric label="Most Affected" value={panel.mostAffectedTeams[0]?.teamName ?? "None"} detail={`${Math.round(panel.mostAffectedTeams[0]?.impactScore ?? 0)} impact`} tone="cyan" />
        <ImpactHeroMetric label="Required Hires" value={`${panel.hiringRequirements.requiredHires}`} detail={`${panel.hiringRequirements.priority} priority`} tone="mint" />
        <ImpactHeroMetric label="Productivity Cost" value={formatMoney(panel.productivityCost)} detail={`Cost +${formatMoney(panel.costIncrease)}`} tone="slate" />
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-[1fr_0.9fr]">
        <div className="grid gap-4 lg:grid-cols-2">
          <div className="border border-line/70 bg-black/20 p-4">
            <div className="text-sm font-semibold text-white">Most Affected Teams</div>
            <div className="mt-3 space-y-3">
              {panel.mostAffectedTeams.map((team) => (
                <div key={`${team.department}-${team.teamName}`} className="border border-line/60 bg-white/[0.03] p-3">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <div className="text-sm font-semibold text-white">{team.teamName}</div>
                      <div className="text-xs uppercase text-slate-500">{team.department}</div>
                    </div>
                    <div className="text-sm text-cyan">{Math.round(team.impactScore)}</div>
                  </div>
                  <div className="mt-3 h-2 bg-white/10">
                    <div className="h-2 bg-cyan transition-all duration-700" style={{ width: `${Math.max(8, (team.impactScore / highestTeamImpact) * 100)}%` }} />
                  </div>
                  <div className="mt-3 grid grid-cols-3 gap-2 text-xs">
                    <MiniStat label="Delay" value={`${Math.round(team.delayRisk)}%`} />
                    <MiniStat label="Burnout" value={`${Math.round(team.burnoutRisk)}%`} />
                    <MiniStat label="Shortage" value={`${Math.round(team.shortageScore)}%`} />
                  </div>
                  <p className="mt-2 text-xs leading-5 text-slate-400">{team.reason}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="border border-line/70 bg-black/20 p-4">
            <div className="text-sm font-semibold text-white">Recovery Strategy</div>
            <ImpactActionList title="Immediate" items={panel.recoveryStrategy.immediateActions} />
            <ImpactActionList title="Short-Term" items={panel.recoveryStrategy.shortTermRecovery} />
            <ImpactActionList title="Long-Term" items={panel.recoveryStrategy.longTermRecovery} />
          </div>
        </div>

        <div className="grid gap-4">
          <div className="border border-line/70 bg-black/20 p-4">
            <div className="flex items-center justify-between gap-3">
              <div>
                <div className="text-sm font-semibold text-white">Hiring Requirements</div>
                <p className="mt-1 text-xs leading-5 text-slate-400">{panel.hiringRequirements.rationale}</p>
              </div>
              <span className={`border px-2 py-1 text-xs ${riskTone[panel.hiringRequirements.priority]}`}>{panel.hiringRequirements.priority}</span>
            </div>
            <div className="mt-3 grid grid-cols-2 gap-2">
              <MiniStat label="Required hires" value={String(panel.hiringRequirements.requiredHires)} />
              <MiniStat label="Urgency" value={panel.hiringRequirements.urgencyDays ? `${panel.hiringRequirements.urgencyDays} days` : "monitor"} />
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              {panel.hiringRequirements.skillsNeeded.map((skill) => (
                <span key={skill} className="border border-mint/20 bg-mint/5 px-2 py-1 text-[11px] text-mint">{skill}</span>
              ))}
            </div>
          </div>

          <div className="border border-line/70 bg-black/20 p-4">
            <div className="text-sm font-semibold text-white">Recovery Timeline</div>
            <div className="mt-3 space-y-2">
              {panel.forecastPoints.map((point) => (
                <div key={point.label} className="grid grid-cols-[72px_1fr_42px] items-center gap-2 text-xs">
                  <span className="text-slate-400">{point.label}</span>
                  <span className="h-2 bg-white/10">
                    <span className="block h-2 bg-mint transition-all duration-700" style={{ width: `${Math.max(4, point.recoveryProgress)}%` }} />
                  </span>
                  <span className="text-right text-white">{Math.round(point.delayProbability)}%</span>
                </div>
              ))}
            </div>
          </div>

          <div className="border border-line/70 bg-black/20 p-4">
            <div className="text-sm font-semibold text-white">Agent Council Summary</div>
            <div className="mt-3 space-y-2">
              {panel.agentCouncil.slice(0, 4).map((agent) => (
                <div key={`${agent.agent}-${agent.responsibility}`} className="border-l border-cyan/40 pl-3">
                  <div className="text-xs font-semibold text-white">{agent.agent}</div>
                  <p className="mt-1 text-xs leading-5 text-slate-400">{agent.finding}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function ImpactHeroMetric({ label, value, detail, tone }: { label: string; value: string; detail: string; tone: "rose" | "amber" | "cyan" | "mint" | "slate" }) {
  const tones = {
    rose: "border-rose/30 bg-rose/10 text-rose",
    amber: "border-amber/30 bg-amber/10 text-amber",
    cyan: "border-cyan/30 bg-cyan/10 text-cyan",
    mint: "border-mint/30 bg-mint/10 text-mint",
    slate: "border-line bg-white/[0.03] text-slate-300",
  };
  return (
    <div className={`min-w-0 border p-3 ${tones[tone]}`}>
      <div className="text-[11px] uppercase opacity-80">{label}</div>
      <div className="mt-2 truncate text-xl font-semibold text-white">{value}</div>
      <div className="mt-1 truncate text-xs">{detail}</div>
    </div>
  );
}

function ImpactActionList({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="mt-3">
      <div className="text-[11px] uppercase text-cyan">{title}</div>
      <ul className="mt-2 space-y-2">
        {items.slice(0, 3).map((item) => (
          <li key={item} className="border border-line/60 bg-white/[0.03] p-2 text-xs leading-5 text-slate-300">{item}</li>
        ))}
      </ul>
    </div>
  );
}

function MiniStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0 border border-line/60 bg-panel/60 p-2">
      <div className="truncate text-[11px] uppercase text-slate-500">{label}</div>
      <div className="mt-1 truncate text-sm font-medium text-white">{value}</div>
    </div>
  );
}

function ImpactList({ title, metrics }: { title: string; metrics: WhatIfImpactMetric[] }) {
  return (
    <Panel title={title} icon={TrendingUp}>
      <div className="space-y-3">
        {metrics.map((item) => (
          <div key={item.label} className="border border-line/60 bg-void/35 p-3">
            <div className="flex items-center justify-between gap-3">
              <div className="text-sm font-medium text-white">{item.label}</div>
              <div className={item.delta >= 0 ? "text-xs text-mint" : "text-xs text-rose"}>{formatMetric(item)}</div>
            </div>
            <div className="mt-2 h-1.5 overflow-hidden bg-panel">
              <div className={item.delta >= 0 ? "h-full bg-mint" : "h-full bg-rose"} style={{ width: `${Math.min(100, Math.max(8, Math.abs(item.delta)))}%` }} />
            </div>
            <p className="mt-2 text-xs leading-5 text-slate-400">{item.explanation}</p>
          </div>
        ))}
      </div>
    </Panel>
  );
}

function RiskRow({ risk }: { risk: WhatIfRiskItem }) {
  return (
    <div className="border border-line/60 bg-void/35 p-3">
      <div className="flex items-center justify-between gap-3">
        <div className="min-w-0">
          <div className="truncate text-sm font-medium text-white">{risk.title}</div>
          <div className="mt-1 text-xs uppercase text-slate-500">{risk.category}</div>
        </div>
        <span className={`border px-2 py-1 text-xs ${riskTone[risk.level]}`}>{risk.level}</span>
      </div>
      <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
        <MiniStat label="Probability" value={`${Math.round(risk.probability)}%`} />
        <MiniStat label="Impact" value={`${Math.round(risk.impact)}%`} />
      </div>
      <div className="mt-2 h-1.5 overflow-hidden bg-panel">
        <div className={`h-full ${riskFill[risk.level]}`} style={{ width: `${risk.probability}%` }} />
      </div>
      <p className="mt-2 text-xs leading-5 text-slate-400">{risk.mitigation}</p>
    </div>
  );
}

function RecommendationRow({ item }: { item: WhatIfRecommendation }) {
  return (
    <div className="border border-line/60 bg-void/35 p-3">
      <div className="flex items-center justify-between gap-3">
        <div className="text-sm font-medium text-white">{item.ownerAgent}</div>
        <span className={`border px-2 py-1 text-xs ${riskTone[item.priority]}`}>{item.priority}</span>
      </div>
      <p className="mt-2 text-sm leading-6 text-slate-200">{item.action}</p>
      <p className="mt-2 text-xs leading-5 text-slate-500">{item.expectedBenefit}</p>
    </div>
  );
}

function metric(metrics: WhatIfImpactMetric[], label: string) {
  return metrics.find((item) => item.label === label);
}

function metricBar(metrics: WhatIfImpactMetric[], label: string) {
  const item = metric(metrics, label);
  if (!item) return null;
  const shortLabels: Record<string, string> = {
    "Revenue Forecast": "Revenue",
    "Profit Forecast": "Profit",
    Productivity: "Prod",
    "Burnout Risk": "Burnout",
    "Delivery Speed": "Delivery",
  };
  return { name: shortLabels[label] ?? label.replace(" Forecast", "").replace(" Risk", ""), delta: item.delta };
}

function formatMetric(item?: WhatIfImpactMetric) {
  if (!item) return "loading";
  const sign = item.delta > 0 ? "+" : "";
  if (item.unit === "USD") return `${sign}${Math.round(item.delta)}%`;
  return `${sign}${Math.round(item.delta)} ${item.unit}`;
}

function formatMoney(value: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
    notation: Math.abs(value) >= 1_000_000 ? "compact" : "standard",
  }).format(value);
}

function formatSigned(value: number) {
  return `${value > 0 ? "+" : ""}${Math.round(value * 10) / 10}`;
}

function formatBranchName(value: string) {
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function numberValue(value: string, fallback: number) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function normalizeScenarioId(name: string) {
  const id = name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
  return id ? `frontend-${id}` : "frontend-custom-scenario";
}

function updateScenario(setScenario: React.Dispatch<React.SetStateAction<WhatIfScenarioRequest>>, patch: Partial<WhatIfScenarioRequest>) {
  setScenario((current) => ({ ...current, ...patch }));
}

function toSnake(value: unknown): unknown {
  if (Array.isArray(value)) return value.map((item) => toSnake(item));
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>).map(([key, nested]) => [
        key.replace(/[A-Z]/g, (letter) => `_${letter.toLowerCase()}`),
        toSnake(nested),
      ]),
    );
  }
  return value;
}
