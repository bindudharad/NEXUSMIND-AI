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
  Brain,
  Building2,
  CheckCircle2,
  GitBranch,
  GitCompare,
  Loader2,
  Network,
  Orbit,
  RefreshCw,
  Send,
  ShieldCheck,
  Sparkles,
  Users,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import type {
  ShadowCompanyAssistantResponse,
  ShadowCompanyDashboardResponse,
  ShadowDecisionSimulationRequest,
  ShadowDecisionSimulationResponse,
  ShadowFutureState,
  ShadowRealitySimulation,
  ShadowScenarioType,
} from "@/types/shadow-company";

const scenarioTypes: { value: ShadowScenarioType; label: string }[] = [
  { value: "hiring", label: "Hiring" },
  { value: "revenue_drop", label: "Revenue drop" },
  { value: "client_loss", label: "Client loss" },
  { value: "executive_resignation", label: "Executive resignation" },
  { value: "engineering_resignation", label: "Engineering resignation" },
  { value: "budget_reduction", label: "Budget reduction" },
  { value: "market_expansion", label: "Market expansion" },
  { value: "security_incident", label: "Security incident" },
  { value: "custom", label: "Custom" },
];

const presets = [
  "Should we reduce workforce by 20%?",
  "Show the most likely company future.",
  "What happens if we lose our top client?",
  "What future has the highest growth potential?",
  "Which decision produces the best outcome?",
  "What if we hire 100 engineers?",
  "What if our CTO resigns?",
];

const flagshipScenario: ShadowDecisionSimulationRequest = {
  scenarioId: "frontend-shadow-workforce-reduction-20",
  scenarioName: "Reduce workforce by 20%",
  question: "Should we reduce workforce by 20%?",
  scenarioType: "budget_reduction",
  horizonMonths: 12,
  employeeDelta: -25,
  workloadDeltaPercent: 34,
  budgetDeltaPercent: -18,
  revenueDeltaPercent: -7,
  clientLossPercent: 0,
  targetDepartment: "Company-wide",
  targetMarket: "Global",
  securityIncident: false,
  notes: "Flagship Shadow Company demo: test a 20% workforce reduction before executing it in reality.",
};

const defaultScenario: ShadowDecisionSimulationRequest = flagshipScenario;

const inputClass = "w-full border border-line bg-void px-3 py-2 text-sm text-white outline-none focus:border-cyan/60";

export function AIShadowCompanyPanel() {
  const [dashboard, setDashboard] = useState<ShadowCompanyDashboardResponse | null>(null);
  const [selected, setSelected] = useState<ShadowDecisionSimulationResponse | null>(null);
  const [assistant, setAssistant] = useState<ShadowCompanyAssistantResponse | null>(null);
  const [scenario, setScenario] = useState<ShadowDecisionSimulationRequest>(defaultScenario);
  const [question, setQuestion] = useState(presets[0]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [streamStatus, setStreamStatus] = useState("connecting");
  const [error, setError] = useState("");
  const manualScenarioUntil = useRef(0);

  const loadDefault = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/shadow-company/default", { cache: "no-store" });
      if (!response.ok) throw new Error("Shadow Company default failed");
      const payload = (await response.json()) as ShadowCompanyDashboardResponse;
      setDashboard(payload);
      setSelected((current) => current ?? payload.latestDecisionTest);
      setStreamStatus((current) => (current === "connecting" ? "polling" : current));
    } catch {
      setError("AI Shadow Company could not load.");
    } finally {
      setLoading(false);
    }
  }, []);

  const runScenario = useCallback(async (payload: ShadowDecisionSimulationRequest) => {
    setRunning(true);
    setError("");
    manualScenarioUntil.current = Date.now() + 30000;
    try {
      const response = await fetch("/api/shadow-company/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(toSnake(payload)),
        cache: "no-store",
      });
      if (!response.ok) throw new Error("Shadow Company simulation failed");
      setSelected((await response.json()) as ShadowDecisionSimulationResponse);
    } catch {
      setError("Shadow Company decision test failed.");
    } finally {
      setRunning(false);
    }
  }, []);

  const ask = useCallback(async (override?: string) => {
    const prompt = override ?? question;
    if (!prompt.trim()) return;
    setRunning(true);
    setError("");
    manualScenarioUntil.current = Date.now() + 30000;
    try {
      const response = await fetch("/api/shadow-company/assistant", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: prompt, horizon_months: scenario.horizonMonths }),
        cache: "no-store",
      });
      if (!response.ok) throw new Error("Shadow Company assistant failed");
      const payload = (await response.json()) as ShadowCompanyAssistantResponse;
      setAssistant(payload);
      setSelected(payload.simulation);
    } catch {
      setError("Shadow Company assistant could not answer.");
    } finally {
      setRunning(false);
    }
  }, [question, scenario.horizonMonths]);

  useEffect(() => {
    const timer = window.setTimeout(() => void loadDefault(), 0);
    return () => window.clearTimeout(timer);
  }, [loadDefault]);

  useEffect(() => {
    const source = new EventSource("/api/shadow-company/stream");
    source.addEventListener("ai_shadow_company", (event) => {
      try {
        const payload = JSON.parse((event as MessageEvent).data) as ShadowCompanyDashboardResponse;
        setDashboard(payload);
        if (Date.now() > manualScenarioUntil.current) setSelected(payload.latestDecisionTest);
        setStreamStatus("live");
        setLoading(false);
      } catch {
        setStreamStatus((current) => (current === "live" ? "live" : "degraded"));
      }
    });
    source.onerror = () => setStreamStatus((current) => (current === "live" ? "live" : "degraded"));
    return () => source.close();
  }, []);

  const futureChart = useMemo(() => chartFuture(selected?.futureStates ?? dashboard?.futureStates ?? []), [dashboard, selected]);
  const realityChart = useMemo(() => chartRealities(selected?.multiRealitySimulations ?? dashboard?.multiRealitySimulations ?? []), [dashboard, selected]);
  const stateChart = useMemo(() => {
    if (!dashboard) return [];
    return [
      { name: "Real", risk: dashboard.realCompanyState.riskScore, growth: dashboard.realCompanyState.growthScore, health: dashboard.realCompanyState.workforceHealth },
      { name: "Shadow", risk: dashboard.shadowCompanyState.riskScore, growth: dashboard.shadowCompanyState.growthScore, health: dashboard.shadowCompanyState.workforceHealth },
      ...(selected
        ? [{ name: "Simulated", risk: selected.simulatedOutcome.riskScore, growth: selected.simulatedOutcome.growthScore, health: selected.simulatedOutcome.workforceHealth }]
        : []),
    ];
  }, [dashboard, selected]);

  return (
    <section data-testid="ai-shadow-company-panel" id="ai-shadow-company-panel" className="w-full max-w-[calc(100vw-2rem)] overflow-hidden border border-cyan/30 bg-panel/90 p-5 shadow-control backdrop-blur lg:max-w-full">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div className="min-w-0 max-w-[calc(100vw-4rem)] xl:max-w-5xl">
          <div className="flex flex-wrap items-center gap-2 text-xs uppercase text-cyan">
            <Orbit className="size-4" />
            <span>AI Shadow Company</span>
            <span className="border border-cyan/25 bg-cyan/10 px-2 py-1 text-cyan">{streamStatus}</span>
            <span className="border border-mint/25 bg-mint/10 px-2 py-1 text-mint">{dashboard?.finalVerdict ?? "loading"}</span>
          </div>
          <h2 className="mt-2 break-words text-2xl font-semibold text-white">Parallel virtual enterprise and future reality simulation engine</h2>
          <p className="mt-3 break-words text-sm leading-6 text-slate-400">
            {dashboard?.executiveBrief ??
              "Mirroring employees, teams, departments, projects, clients, revenue, costs, productivity, risks, workflows, knowledge networks, and communication networks into a synchronized Shadow Company."}
          </p>
        </div>
        <div className="flex flex-col gap-2 sm:flex-row">
          <button
            type="button"
            onClick={() => {
              setScenario(flagshipScenario);
              setQuestion(flagshipScenario.question);
              void runScenario(flagshipScenario);
            }}
            className="inline-flex h-10 items-center justify-center gap-2 border border-cyan/45 bg-cyan/10 px-3 text-sm text-cyan transition hover:border-cyan"
          >
            {running ? <Loader2 className="size-4 animate-spin" /> : <GitBranch className="size-4" />}
            Run Shadow Company Demo
          </button>
          <button type="button" onClick={() => void loadDefault()} className="inline-flex h-10 items-center justify-center gap-2 border border-line bg-panel2 px-3 text-sm text-white transition hover:border-cyan/60">
            {loading ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />}
            Refresh
          </button>
        </div>
      </div>

      {error ? <div className="mt-4 border border-rose/40 bg-rose/10 px-3 py-2 text-sm text-rose">{error}</div> : null}

      <div className="mt-5 grid gap-3 md:grid-cols-3 xl:grid-cols-6">
        <Metric icon={GitCompare} label="Real-time mirroring" value={dashboard ? `${Math.round(dashboard.summary.syncCompleteness)}%` : "loading"} />
        <Metric icon={Users} label="Shadow workforce twins" value={dashboard ? String(dashboard.summary.employeesMirrored) : "loading"} />
        <Metric icon={Building2} label="Departments" value={dashboard ? String(dashboard.summary.departmentsMirrored) : "loading"} />
        <Metric icon={Network} label="Knowledge nodes" value={dashboard ? String(dashboard.summary.knowledgeNetworkNodes) : "loading"} />
        <Metric icon={GitBranch} label="Future timelines" value={dashboard ? String(dashboard.futureStates.length) : "loading"} />
        <Metric icon={Sparkles} label="Wow score" value={dashboard ? `${Math.round(dashboard.summary.judgeWowFactorScore)}/100` : "loading"} />
      </div>

      <div className="mt-5 grid gap-4 xl:grid-cols-[0.85fr_1.15fr]">
        <Panel title="Decision Testing Engine" icon={Bot}>
          <div className="grid gap-2 sm:grid-cols-2">
            {dashboard?.decisionTestingTemplates.map((item) => (
              <button
                type="button"
                key={item.scenarioId}
                onClick={() => {
                  setScenario(item);
                  setQuestion(item.question);
                  void runScenario(item);
                }}
                className="border border-line bg-void px-3 py-2 text-left text-xs text-slate-300 transition hover:border-cyan/60 hover:text-white"
              >
                {item.scenarioName}
              </button>
            ))}
          </div>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <label className="text-xs text-slate-400">
              Scenario type
              <select
                value={scenario.scenarioType}
                onChange={(event) => setScenario((current) => ({ ...current, scenarioType: event.target.value as ShadowScenarioType }))}
                className={`${inputClass} mt-1`}
              >
                {scenarioTypes.map((item) => (
                  <option key={item.value} value={item.value}>
                    {item.label}
                  </option>
                ))}
              </select>
            </label>
            <NumberInput label="Workforce capacity delta" value={scenario.employeeDelta} onChange={(employeeDelta) => setScenario((current) => ({ ...current, employeeDelta }))} />
            <NumberInput label="Revenue delta %" value={scenario.revenueDeltaPercent} onChange={(revenueDeltaPercent) => setScenario((current) => ({ ...current, revenueDeltaPercent }))} />
            <NumberInput label="Budget delta %" value={scenario.budgetDeltaPercent} onChange={(budgetDeltaPercent) => setScenario((current) => ({ ...current, budgetDeltaPercent }))} />
            <NumberInput label="Workload delta %" value={scenario.workloadDeltaPercent} onChange={(workloadDeltaPercent) => setScenario((current) => ({ ...current, workloadDeltaPercent }))} />
            <NumberInput label="Client loss %" value={scenario.clientLossPercent} onChange={(clientLossPercent) => setScenario((current) => ({ ...current, clientLossPercent }))} />
          </div>
          <button type="button" onClick={() => void runScenario(scenario)} className="mt-4 inline-flex h-10 w-full items-center justify-center gap-2 border border-cyan/45 bg-cyan/10 px-3 text-sm text-cyan transition hover:border-cyan">
            {running ? <Loader2 className="size-4 animate-spin" /> : <GitBranch className="size-4" />}
            Clone current state and simulate branch
          </button>
        </Panel>

        <Panel title="Current Company State vs Shadow Company State" icon={GitCompare}>
          <div className="h-64 min-w-0">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stateChart}>
                <CartesianGrid stroke="#213144" strokeDasharray="3 3" />
                <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 12 }} />
                <YAxis tick={{ fill: "#94a3b8", fontSize: 12 }} />
                <Tooltip contentStyle={{ background: "#101827", border: "1px solid #22324a", color: "#fff" }} />
                <Bar dataKey="risk" fill="#fb7185" name="Risk" />
                <Bar dataKey="growth" fill="#22d3ee" name="Growth" />
                <Bar dataKey="health" fill="#34d399" name="Workforce Health" />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <p className="mt-3 text-sm leading-6 text-slate-400">{selected?.executiveSummary ?? dashboard?.shadowCompanyState.explanation}</p>
        </Panel>
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-2">
        <Panel title="Executive decision comparison" icon={GitCompare}>
          <div className="grid gap-3 lg:grid-cols-3">
            {decisionOptions(selected, dashboard).map((option) => (
              <article key={option.label} className={`border bg-void p-4 ${option.recommended ? "border-mint/50 shadow-[0_0_24px_rgba(52,211,153,0.14)]" : "border-line"}`}>
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs uppercase text-slate-500">{option.label}</span>
                  <span className={`border px-2 py-1 text-[10px] uppercase ${option.recommended ? "border-mint/40 text-mint" : "border-line text-slate-400"}`}>
                    {option.badge}
                  </span>
                </div>
                <h3 className="mt-2 text-base font-semibold text-white">{option.title}</h3>
                <div className="mt-4 grid gap-2 text-xs">
                  <ComparisonMetric label="Risk score" value={option.riskScore} tone={Number.parseFloat(option.riskScore) >= 70 ? "text-rose" : "text-cyan"} />
                  <ComparisonMetric label="Cost impact" value={option.costImpact} tone={option.costImpact.startsWith("-") ? "text-mint" : "text-amber"} />
                  <ComparisonMetric label="Revenue impact" value={option.revenueImpact} tone={option.revenueImpact.startsWith("-") ? "text-rose" : "text-mint"} />
                  <ComparisonMetric label="Workforce impact" value={option.workforceImpact} tone={option.workforceImpact.startsWith("-") ? "text-rose" : "text-mint"} />
                </div>
                <p className="mt-4 text-xs leading-5 text-slate-400">{option.recommendation}</p>
              </article>
            ))}
          </div>
        </Panel>
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-2">
        <Panel title="Future Timelines" icon={GitBranch}>
          <div className="h-72 min-w-0">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={futureChart}>
                <CartesianGrid stroke="#213144" strokeDasharray="3 3" />
                <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 12 }} />
                <YAxis tick={{ fill: "#94a3b8", fontSize: 12 }} />
                <Tooltip contentStyle={{ background: "#101827", border: "1px solid #22324a", color: "#fff" }} />
                <Line type="monotone" dataKey="risk" stroke="#fb7185" strokeWidth={2} name="Risk" />
                <Line type="monotone" dataKey="growth" stroke="#22d3ee" strokeWidth={2} name="Growth" />
                <Line type="monotone" dataKey="workforce" stroke="#34d399" strokeWidth={2} name="Workforce" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel title="Multi-reality simulations" icon={Sparkles}>
          <div className="h-72 min-w-0">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={realityChart}>
                <CartesianGrid stroke="#213144" strokeDasharray="3 3" />
                <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 11 }} interval={0} angle={-18} height={58} />
                <YAxis tick={{ fill: "#94a3b8", fontSize: 12 }} />
                <Tooltip contentStyle={{ background: "#101827", border: "1px solid #22324a", color: "#fff" }} />
                <Bar dataKey="probability" fill="#a78bfa" name="Probability" />
                <Bar dataKey="risk" fill="#fb7185" name="Risk" />
                <Bar dataKey="growth" fill="#34d399" name="Growth" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-[1fr_0.9fr]">
        <Panel title="Shadow Company Assistant" icon={Brain}>
          <div className="grid gap-2 sm:grid-cols-3">
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
          <div className="mt-4 border border-line bg-void p-4 text-sm leading-6 text-slate-300">
            {assistant?.answer ?? "Ask the Shadow Company to compare futures, identify the strongest branch, and recommend the safest executive decision."}
          </div>
        </Panel>

        <Panel title="Impact Delta" icon={AlertTriangle}>
          <div className="grid gap-2">
            {selected?.impactDelta.map((item) => (
              <div key={item.label} className="flex items-center justify-between gap-3 border border-line bg-void px-3 py-2 text-sm">
                <span className="text-slate-300">{item.label}</span>
                <span className={item.delta >= 0 ? "text-mint" : "text-rose"}>
                  {item.delta >= 0 ? "+" : ""}
                  {formatDelta(item.delta, item.unit)}
                </span>
              </div>
            )) ?? <Empty label="Run a branch to see impact deltas." />}
          </div>
        </Panel>
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-3">
        <Panel title="Autonomous shadow workforce" icon={Bot}>
          <List items={(selected?.agentContributions ?? dashboard?.agentEcosystem ?? []).map((item) => `${item.agent}: ${item.action}`)} />
        </Panel>
        <Panel title="Knowledge Brain integration" icon={Brain}>
          <List items={(dashboard?.integrationSignals ?? []).filter((item) => item.system.includes("Knowledge")).map((item) => item.update)} />
        </Panel>
        <Panel title="Organizational Brain integration" icon={Network}>
          <List items={(dashboard?.integrationSignals ?? []).filter((item) => item.system.includes("Organizational")).map((item) => item.update)} />
        </Panel>
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-[1fr_1fr]">
        <Panel title="Digital twin integration" icon={ShieldCheck}>
          <List items={(dashboard?.integrationSignals ?? []).filter((item) => item.system.includes("Digital") || item.system.includes("Multi-Agent")).map((item) => item.update)} />
        </Panel>
        <Panel title="Shadow Reality Viewer" icon={Orbit}>
          {dashboard ? (
            <div className="grid gap-3 sm:grid-cols-3">
              <Metric icon={GitCompare} label="Real nodes" value={String(dashboard.shadowRealityVisualization.realCompanyNodes)} compact />
              <Metric icon={Orbit} label="Shadow nodes" value={String(dashboard.shadowRealityVisualization.shadowCompanyNodes)} compact />
              <Metric icon={GitBranch} label="Branches" value={String(dashboard.shadowRealityVisualization.futureBranches)} compact />
              <div className="sm:col-span-3 border border-line bg-void p-3 text-sm leading-6 text-slate-300">{dashboard.shadowRealityVisualization.renderingStrategy}</div>
            </div>
          ) : (
            <Empty label="Loading Shadow Reality Viewer." />
          )}
        </Panel>
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-3">
        <Panel title="Shadow workforce twins" icon={Users}>
          <List items={(dashboard?.shadowEmployees ?? []).slice(0, 5).map((item) => `${item.name} | ${item.department} | readiness ${Math.round(item.futureReadiness)}`)} />
        </Panel>
        <Panel title="Shadow projects" icon={GitBranch}>
          <List items={(dashboard?.shadowProjects ?? []).slice(0, 5).map((item) => `${item.name} | delay ${item.predictedDelayWeeks} weeks | confidence ${Math.round(item.deliveryConfidence)}%`)} />
        </Panel>
        <Panel title="Shadow departments" icon={Building2}>
          <List items={(dashboard?.shadowDepartments ?? []).slice(0, 5).map((item) => `${item.name} | risk ${Math.round(item.riskScore)} | capacity ${Math.round(item.capacityScore)}`)} />
        </Panel>
      </div>

      <div className="mt-4 border border-mint/30 bg-mint/10 p-4 text-sm text-mint">
        {dashboard?.statusReport.finalVerdict ?? "AI SHADOW COMPANY COMPLETE"} | Production readiness {dashboard ? Math.round(dashboard.statusReport.productionReadinessScore) : "--"}/100 | Missing components{" "}
        {dashboard?.statusReport.missingComponents.length ?? 0}
      </div>
    </section>
  );
}

function Metric({ icon: Icon, label, value, compact = false }: { icon: LucideIcon; label: string; value: string; compact?: boolean }) {
  return (
    <div className={`border border-line bg-void ${compact ? "p-3" : "p-4"}`}>
      <div className="flex items-center gap-2 text-xs uppercase text-slate-500">
        <Icon className="size-4 text-cyan" />
        <span>{label}</span>
      </div>
      <div className="mt-2 break-words text-lg font-semibold text-white">{value}</div>
    </div>
  );
}

function ComparisonMetric({ label, value, tone }: { label: string; value: string; tone: string }) {
  return (
    <div className="flex items-center justify-between gap-2 border border-line/70 bg-panel/50 px-2 py-1">
      <span className="text-slate-500">{label}</span>
      <strong className={`text-right ${tone}`}>{value}</strong>
    </div>
  );
}

function Panel({ title, icon: Icon, children }: { title: string; icon: LucideIcon; children: React.ReactNode }) {
  return (
    <div className="min-w-0 border border-line bg-panel2/80 p-4">
      <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-white">
        <Icon className="size-4 text-cyan" />
        <span>{title}</span>
      </div>
      {children}
    </div>
  );
}

function NumberInput({ label, value, onChange }: { label: string; value: number; onChange: (value: number) => void }) {
  return (
    <label className="text-xs text-slate-400">
      {label}
      <input value={value} onChange={(event) => onChange(Number(event.target.value))} type="number" className={`${inputClass} mt-1`} />
    </label>
  );
}

function List({ items }: { items: string[] }) {
  if (!items.length) return <Empty label="No records loaded yet." />;
  return (
    <div className="space-y-2">
      {items.slice(0, 6).map((item) => (
        <div key={item} className="flex gap-2 border border-line bg-void p-3 text-sm leading-6 text-slate-300">
          <CheckCircle2 className="mt-1 size-4 shrink-0 text-mint" />
          <span className="break-words">{item}</span>
        </div>
      ))}
    </div>
  );
}

function Empty({ label }: { label: string }) {
  return <div className="border border-line bg-void p-3 text-sm text-slate-500">{label}</div>;
}

function chartFuture(states: ShadowFutureState[]) {
  return states.map((item) => ({
    name: item.horizonLabel.replace("_", " "),
    risk: Math.round(item.riskScore),
    growth: Math.round(item.growthScore),
    workforce: Math.round(item.workforceHealth),
  }));
}

function chartRealities(realities: ShadowRealitySimulation[]) {
  return realities.map((item) => ({
    name: item.caseName.replace("_", " "),
    probability: Math.round(item.probability),
    risk: Math.round(item.riskScore),
    growth: Math.round(item.growthScore),
  }));
}

function formatDelta(value: number, unit: string) {
  if (unit === "$") return `$${Math.round(value).toLocaleString()}`;
  return `${Math.round(value)} ${unit}`;
}

function decisionOptions(selected: ShadowDecisionSimulationResponse | null, dashboard: ShadowCompanyDashboardResponse | null) {
  const active = selected ?? dashboard?.latestDecisionTest ?? null;
  const baseline = active?.baselineOutcome ?? dashboard?.realCompanyState ?? null;
  const simulated = active?.simulatedOutcome ?? dashboard?.shadowCompanyState ?? null;
  const recommended = active?.multiRealitySimulations.find((item) => item.caseName === "ai_recommended_case");
  const costDelta = active ? deltaValue(active, "Costs") : null;
  const revenueDelta = active ? deltaValue(active, "Revenue") : null;
  const workforceDelta = active ? deltaValue(active, "Workforce Health") : null;

  return [
    {
      label: "Option A",
      title: "Keep current company",
      badge: "baseline",
      riskScore: baseline ? `${Math.round(baseline.riskScore)}/100` : "loading",
      costImpact: "$0",
      revenueImpact: "$0",
      workforceImpact: "0 points",
      recommendation: "Hold current state and continue monitoring the live company twin before making a workforce decision.",
      recommended: false,
    },
    {
      label: "Option B",
      title: active?.scenario.scenarioName ?? "Reduce workforce by 20%",
      badge: active?.riskLevel ?? "scenario",
      riskScore: simulated ? `${Math.round(simulated.riskScore)}/100` : "loading",
      costImpact: costDelta ? signedDelta(costDelta.delta, costDelta.unit) : "loading",
      revenueImpact: revenueDelta ? signedDelta(revenueDelta.delta, revenueDelta.unit) : "loading",
      workforceImpact: workforceDelta ? signedDelta(workforceDelta.delta, workforceDelta.unit) : "loading",
      recommendation: active?.recommendations[0] ?? "Clone the current company, apply the workforce reduction, and inspect risk before approval.",
      recommended: false,
    },
    {
      label: "Option C",
      title: "AI-recommended branch",
      badge: "recommended",
      riskScore: recommended ? `${Math.round(recommended.riskScore)}/100` : "loading",
      costImpact: "staged guardrails",
      revenueImpact: recommended ? signedPercent(recommended.revenueDeltaPercent) : "loading",
      workforceImpact: recommended ? signedPercent(recommended.workforceDeltaPercent) : "loading",
      recommendation: recommended?.actions[0] ?? "Use the Shadow Company's recommended branch with checkpoints, rollback thresholds, and agent monitoring.",
      recommended: true,
    },
  ];
}

function deltaValue(response: ShadowDecisionSimulationResponse, label: string) {
  return response.impactDelta.find((item) => item.label === label) ?? null;
}

function signedDelta(value: number, unit: string) {
  const prefix = value > 0 ? "+" : value < 0 ? "-" : "";
  const absolute = Math.abs(value);
  if (unit === "$") return `${prefix}$${Math.round(absolute).toLocaleString()}`;
  return `${prefix}${Math.round(absolute)} ${unit}`;
}

function signedPercent(value: number) {
  const prefix = value > 0 ? "+" : "";
  return `${prefix}${value.toFixed(1)}%`;
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
