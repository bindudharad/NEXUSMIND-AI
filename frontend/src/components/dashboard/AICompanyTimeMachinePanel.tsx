"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type React from "react";
import { Area, AreaChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { AlertTriangle, Bot, BrainCircuit, Clock, Database, Loader2, Network, RefreshCw, Send, Sparkles, TrendingDown, Users } from "lucide-react";
import type { LucideIcon } from "lucide-react";

import type {
  TimeMachineAssistantResponse,
  TimeMachineDashboardResponse,
  TimeMachineRiskLevel,
  TimeMachineScenarioRequest,
  TimeMachineSimulationResponse,
} from "@/types/time-machine";

const riskTone: Record<TimeMachineRiskLevel, string> = {
  low: "border-mint/35 bg-mint/10 text-mint",
  medium: "border-cyan/35 bg-cyan/10 text-cyan",
  high: "border-amber/35 bg-amber/10 text-amber",
  critical: "border-rose/35 bg-rose/10 text-rose",
};

const presets = [
  "What will happen in 6 months if employee workload increases by 30%?",
  "What will happen if hiring freezes for 1 year?",
  "What will happen if revenue drops by 20%?",
  "What will happen if 25 engineers resign?",
  "What will happen if we expand into a new market?",
];

export function AICompanyTimeMachinePanel() {
  const [dashboard, setDashboard] = useState<TimeMachineDashboardResponse | null>(null);
  const [selected, setSelected] = useState<TimeMachineSimulationResponse | null>(null);
  const [assistant, setAssistant] = useState<TimeMachineAssistantResponse | null>(null);
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
      const response = await fetch("/api/time-machine/default", { cache: "no-store" });
      if (!response.ok) throw new Error("Time Machine default failed");
      const payload = (await response.json()) as TimeMachineDashboardResponse;
      setDashboard(payload);
      setSelected((current) => current ?? payload.scenarios[0] ?? null);
      setStreamStatus((status) => (status === "connecting" ? "polling" : status));
    } catch {
      setError("AI Company Time Machine could not load.");
    } finally {
      setLoading(false);
    }
  }, []);

  const ask = useCallback(async (override?: string) => {
    const prompt = override ?? question;
    if (!prompt.trim()) return;
    setRunning(true);
    setError("");
    manualScenarioUntil.current = Date.now() + 30000;
    try {
      const response = await fetch("/api/time-machine/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: prompt, horizon_months: 6 }),
        cache: "no-store",
      });
      if (!response.ok) throw new Error("Time Machine assistant failed");
      const payload = (await response.json()) as TimeMachineAssistantResponse;
      setAssistant(payload);
      setSelected(payload.simulation);
    } catch {
      setError("Time Machine assistant could not execute the scenario.");
    } finally {
      setRunning(false);
    }
  }, [question]);

  const runTemplate = useCallback(async (scenario: TimeMachineScenarioRequest) => {
    setRunning(true);
    setError("");
    manualScenarioUntil.current = Date.now() + 30000;
    try {
      const response = await fetch("/api/time-machine/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(toSnake(scenario)),
        cache: "no-store",
      });
      if (!response.ok) throw new Error("Time Machine simulation failed");
      setSelected((await response.json()) as TimeMachineSimulationResponse);
    } catch {
      setError("Time Machine scenario could not run.");
    } finally {
      setRunning(false);
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => void loadDefault(), 0);
    return () => window.clearTimeout(timer);
  }, [loadDefault]);

  useEffect(() => {
    const source = new EventSource("/api/time-machine/stream");
    source.addEventListener("company_time_machine", (event) => {
      try {
        const payload = toCamel<TimeMachineSimulationResponse>(JSON.parse((event as MessageEvent).data));
        if (Date.now() > manualScenarioUntil.current) setSelected(payload);
        setStreamStatus("live");
        setLoading(false);
      } catch {
        setStreamStatus((status) => (status === "live" ? "live" : "degraded"));
      }
    });
    source.onerror = () => setStreamStatus((status) => (status === "live" ? "live" : "degraded"));
    return () => source.close();
  }, []);

  const chartData = useMemo(() => selected?.timeline ?? [], [selected]);

  return (
    <section id="ai-company-time-machine-panel" data-testid="ai-company-time-machine-panel" className="border border-cyan/30 bg-panel/90 p-5 shadow-control backdrop-blur">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div className="max-w-5xl">
          <div className="flex flex-wrap items-center gap-2 text-xs uppercase text-cyan">
            <Clock className="size-4" />
            <span>AI Company Time Machine</span>
            <span className="border border-cyan/25 bg-cyan/10 px-2 py-1 text-cyan">{streamStatus}</span>
          </div>
          <h2 className="mt-2 text-2xl font-semibold text-white">GPT + digital twin + business simulator + future predictor</h2>
          <p className="mt-3 text-sm leading-6 text-slate-400">
            {selected
              ? `${selected.scenario.scenarioName}: success probability ${Math.round(selected.successProbability)}%, risk ${selected.riskLevel}, confidence ${Math.round(selected.confidence * 100)}%.`
              : "Building the future state from employee, team, department, project, client, and company twins."}
          </p>
        </div>
        <button type="button" onClick={() => void loadDefault()} className="inline-flex h-10 items-center gap-2 border border-line bg-panel2 px-3 text-sm text-white transition hover:border-cyan/60">
          {loading ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />}
          Refresh
        </button>
      </div>

      {error ? <div className="mt-4 border border-rose/40 bg-rose/10 px-3 py-2 text-sm text-rose">{error}</div> : null}

      <div className="mt-5 grid gap-3 md:grid-cols-5">
        <Metric icon={BrainCircuit} label="Twin Scope" value={dashboard ? `${String(dashboard.digitalTwinStatus.employees)} employees` : "loading"} />
        <Metric icon={Sparkles} label="Readiness" value={dashboard ? `${Math.round(dashboard.summary.productionReadinessScore)}/100` : "loading"} />
        <Metric icon={AlertTriangle} label="Risk" value={selected?.riskLevel ?? "loading"} />
        <Metric icon={TrendingDown} label="Revenue Impact" value={selected ? `${Math.round(selected.financialImpact.delta)}%` : "loading"} />
        <Metric icon={Users} label="Burnout" value={selected ? `${Math.round(selected.workforceImpact.projected)}%` : "loading"} />
      </div>

      <div className="mt-5 grid gap-4 xl:grid-cols-[0.75fr_1.25fr]">
        <Panel title="Scenario Builder" icon={Bot}>
          <div className="flex flex-col gap-2">
            {presets.map((item) => (
              <button
                type="button"
                key={item}
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
          <div className="mt-4 flex gap-2">
            <input
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              className="min-h-10 flex-1 border border-line bg-void px-3 text-sm text-white outline-none focus:border-cyan/60"
              aria-label="Time Machine question"
            />
            <button type="button" onClick={() => void ask()} className="inline-flex min-h-10 items-center gap-2 border border-cyan/40 bg-cyan/10 px-3 text-sm text-cyan">
              {running ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
              Run
            </button>
          </div>
          <div className="mt-4 grid gap-2">
            {dashboard?.scenarioBuilderTemplates.slice(0, 5).map((scenario) => (
              <button key={scenario.scenarioId} type="button" onClick={() => void runTemplate(scenario)} className="border border-line/60 bg-panel2/45 p-2 text-left text-xs text-slate-400 transition hover:border-mint/50 hover:text-white">
                {scenario.scenarioName} | {scenario.horizonMonths} mo
              </button>
            ))}
          </div>
        </Panel>

        <Panel title="Future Timeline" icon={Clock}>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ left: 4, right: 12, top: 8, bottom: 8 }}>
                <CartesianGrid stroke="#1C2B3A" strokeDasharray="3 3" />
                <XAxis dataKey="month" stroke="#64748b" tickLine={false} axisLine={false} />
                <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                <Tooltip contentStyle={{ background: "#08111f", border: "1px solid #223044", color: "#e2e8f0" }} />
                <Line type="monotone" dataKey="burnoutRisk" stroke="#FF3B6B" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="productivity" stroke="#2EE9D3" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="projectDelayProbability" stroke="#F6B44B" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="teamHealth" stroke="#7CF0A6" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Panel>
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-4">
        <ImpactCard title="Workforce" impact={selected?.workforceImpact} />
        <ImpactCard title="Financial" impact={selected?.financialImpact} />
        <ImpactCard title="Project" impact={selected?.projectImpact} />
        <ImpactCard title="Client" impact={selected?.clientImpact} />
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
        <Panel title="AI Reasoning and Agents" icon={Network}>
          <p className="text-sm leading-6 text-slate-300">{selected?.explanation.summary ?? assistant?.answer ?? "Run a scenario to inspect causal reasoning."}</p>
          <div className="mt-3 grid gap-2">
            {selected?.agentContributions.map((item) => (
              <div key={item.agent} className="border border-line/60 bg-void/35 p-2">
                <div className="flex items-center justify-between gap-3">
                  <strong className="text-xs text-white">{item.agent}</strong>
                  <span className="text-[10px] uppercase text-cyan">{Math.round(item.confidence * 100)}%</span>
                </div>
                <p className="mt-1 text-xs leading-5 text-slate-400">{item.finding}</p>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Risks and Recommendations" icon={AlertTriangle}>
          <div className="grid max-h-72 gap-2 overflow-y-auto pr-1 md:grid-cols-2">
            {selected?.risks.map((risk) => (
              <div key={`${risk.domain}-${risk.risk}`} className="border border-line/60 bg-panel2/45 p-3">
                <div className="flex items-start justify-between gap-2">
                  <h3 className="text-sm font-semibold text-white">{risk.risk}</h3>
                  <span className={`border px-2 py-1 text-[10px] uppercase ${riskTone[risk.level]}`}>{risk.level}</span>
                </div>
                <p className="mt-2 text-xs text-slate-500">Probability {Math.round(risk.probability)}%</p>
                <p className="mt-2 text-xs leading-5 text-slate-400">{risk.mitigation}</p>
              </div>
            ))}
          </div>
        </Panel>
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-[1fr_0.8fr]">
        <Panel title="Financial Future" icon={TrendingDown}>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ left: 4, right: 12, top: 8, bottom: 8 }}>
                <CartesianGrid stroke="#1C2B3A" strokeDasharray="3 3" />
                <XAxis dataKey="month" stroke="#64748b" tickLine={false} axisLine={false} />
                <YAxis stroke="#64748b" tickLine={false} axisLine={false} tickFormatter={(value) => `$${Math.round(Number(value) / 1_000_000)}M`} />
                <Tooltip contentStyle={{ background: "#08111f", border: "1px solid #223044", color: "#e2e8f0" }} />
                <Area type="monotone" dataKey="revenue" stroke="#38BDF8" fill="#38BDF833" />
                <Area type="monotone" dataKey="profit" stroke="#7CF0A6" fill="#7CF0A622" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel title="Digital Twin Evidence" icon={Database}>
          <div className="grid max-h-64 gap-2 overflow-y-auto pr-1">
            {selected?.digitalTwinEvidence.map((item) => (
              <p key={item} className="border border-line/60 bg-void/35 p-2 text-xs leading-5 text-slate-400">{item}</p>
            ))}
          </div>
        </Panel>
      </div>
    </section>
  );
}

function ImpactCard({ title, impact }: { title: string; impact?: TimeMachineSimulationResponse["workforceImpact"] }) {
  return (
    <article className="border border-line/70 bg-panel2/55 p-3">
      <h3 className="text-xs uppercase text-slate-500">{title}</h3>
      <strong className="mt-2 block text-xl text-white">{impact ? `${Math.round(impact.projected)}${impact.unit}` : "loading"}</strong>
      <p className="mt-1 text-xs text-slate-500">Delta {impact ? `${Math.round(impact.delta)}${impact.unit}` : "loading"} | Risk {impact ? Math.round(impact.riskScore) : "--"}</p>
      <p className="mt-2 text-xs leading-5 text-slate-400">{impact?.explanation ?? "Awaiting simulation."}</p>
    </article>
  );
}

function Panel({ title, icon: Icon, children }: { title: string; icon: LucideIcon; children: React.ReactNode }) {
  return (
    <article className="border border-line/70 bg-panel2/55 p-4">
      <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
        <Icon className="size-4" />
        <span>{title}</span>
      </div>
      {children}
    </article>
  );
}

function Metric({ icon: Icon, label, value }: { icon: LucideIcon; label: string; value: string }) {
  return (
    <div className="border border-line/70 bg-panel2/60 p-3">
      <div className="flex items-center gap-2 text-xs uppercase text-slate-500">
        <Icon className="size-4 text-cyan" />
        <span>{label}</span>
      </div>
      <strong className="mt-2 block break-words text-lg font-semibold text-white">{value}</strong>
    </div>
  );
}

function toCamel<T>(value: unknown): T {
  if (Array.isArray(value)) return value.map((item) => toCamel(item)) as T;
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>).map(([key, nested]) => [
        key.replace(/_([a-z])/g, (_, letter: string) => letter.toUpperCase()),
        toCamel(nested),
      ]),
    ) as T;
  }
  return value as T;
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
