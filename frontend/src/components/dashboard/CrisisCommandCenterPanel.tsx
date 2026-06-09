"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type React from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  AlertTriangle,
  Brain,
  Flame,
  Loader2,
  Radio,
  RefreshCw,
  Send,
  Shield,
  Siren,
  UsersRound,
  Zap,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import type {
  CrisisAssistantResponse,
  CrisisCommandCenterResponse,
  CrisisHeatmapCell,
  CrisisRecommendation,
  CrisisRiskLevel,
  CrisisSimulationResult,
  CrisisScenarioBuilderResponse,
  CrisisSeverityBand,
  CrisisType,
} from "@/types/crisis-management";

const severityColor: Record<CrisisSeverityBand, string> = {
  level_1_minor: "#7CF0A6",
  level_2_moderate: "#F6B44B",
  level_3_high: "#F97316",
  level_4_critical: "#F05D5E",
  level_5_company_threatening: "#FF3B6B",
};

const riskColor: Record<CrisisRiskLevel, string> = {
  low: "#7CF0A6",
  medium: "#F6B44B",
  high: "#F97316",
  critical: "#F05D5E",
  company_threatening: "#FF3B6B",
};

const scenarioOptions: CrisisType[] = [
  "cyber_attack",
  "ransomware",
  "data_breach",
  "server_failure",
  "cloud_outage",
  "database_corruption",
  "project_collapse",
  "product_launch_failure",
  "client_escalation",
  "major_client_loss",
  "revenue_crash",
  "financial_crash",
  "mass_resignation",
  "critical_employee_loss",
  "supply_chain_disruption",
  "regulatory_incident",
  "public_relations_crisis",
];

const retryDelay = (attempt: number) => new Promise((resolve) => window.setTimeout(resolve, 1400 * (attempt + 1)));

export function CrisisCommandCenterPanel() {
  const [analysis, setAnalysis] = useState<CrisisCommandCenterResponse | null>(null);
  const [assistant, setAssistant] = useState<CrisisAssistantResponse | null>(null);
  const [question, setQuestion] = useState("What is our biggest crisis?");
  const [loading, setLoading] = useState(true);
  const [assistantLoading, setAssistantLoading] = useState(false);
  const [scenarioLoading, setScenarioLoading] = useState(false);
  const [streamStatus, setStreamStatus] = useState("connecting");
  const [error, setError] = useState("");
  const [selectedScenario, setSelectedScenario] = useState<CrisisType>("ransomware");
  const [scenarioScope, setScenarioScope] = useState("production");
  const [scenarioHorizon, setScenarioHorizon] = useState(72);
  const [severityMultiplier, setSeverityMultiplier] = useState(1.15);
  const [scenarioBuilder, setScenarioBuilder] = useState<CrisisScenarioBuilderResponse | null>(null);
  const manualUpdateUntil = useRef(0);

  const loadDefault = useCallback(async () => {
    setLoading(true);
    setError("");
    manualUpdateUntil.current = 0;
    try {
      for (let attempt = 0; attempt < 3; attempt += 1) {
        try {
          const payload = await fetchJson<CrisisCommandCenterResponse>("/api/crisis/management/default");
          if (!isCrisisResponse(payload)) throw new Error("Malformed crisis payload");
          setAnalysis(payload);
          setStreamStatus((status) => (status === "connecting" ? "polling" : status));
          return;
        } catch {
          if (attempt === 2) throw new Error("Crisis default payload unavailable");
          await retryDelay(attempt);
        }
      }
    } catch {
      setError("Crisis Command Center could not load live incident analytics.");
    } finally {
      setLoading(false);
    }
  }, []);

  const runRansomwareSimulation = useCallback(async () => {
    setLoading(true);
    setError("");
    manualUpdateUntil.current = Date.now() + 30000;
    try {
      const payload = await fetchJson<CrisisCommandCenterResponse>("/api/crisis/management/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          scenario_type: "ransomware",
          question: "What if ransomware affects production?",
          affected_scope: "production",
          severity_multiplier: 1.18,
          horizon_hours: 72,
        }),
      });
      if (!isCrisisResponse(payload)) throw new Error("Malformed crisis simulation payload");
      setAnalysis(payload);
    } catch {
      setError("Crisis simulation failed.");
    } finally {
      setLoading(false);
    }
  }, []);

  const runScenarioBuilder = useCallback(async () => {
    setScenarioLoading(true);
    setError("");
    manualUpdateUntil.current = Date.now() + 30000;
    try {
      const payload = await fetchJson<CrisisScenarioBuilderResponse>("/api/crisis/management/scenarios", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          scenario_name: `${labelize(selectedScenario)} executive simulation`,
          scenario_type: selectedScenario,
          question: `What happens if ${labelize(selectedScenario).toLowerCase()} hits ${scenarioScope}?`,
          affected_scope: scenarioScope,
          severity_multiplier: severityMultiplier,
          horizon_hours: scenarioHorizon,
          execute: true,
        }),
      });
      if (!isScenarioBuilder(payload)) throw new Error("Malformed crisis scenario payload");
      setScenarioBuilder(payload);
      if (payload.commandCenter) setAnalysis(payload.commandCenter);
    } catch {
      setError("Crisis scenario builder failed.");
    } finally {
      setScenarioLoading(false);
    }
  }, [scenarioHorizon, scenarioScope, selectedScenario, severityMultiplier]);

  const askAssistant = useCallback(async () => {
    if (!question.trim()) return;
    setAssistantLoading(true);
    try {
      const payload = await fetchJson<CrisisAssistantResponse>("/api/crisis/management/assistant", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, horizon_hours: 72 }),
      });
      if (isAssistant(payload)) setAssistant(payload);
    } catch {
      setAssistant({
        model: "Crisis AI Assistant",
        generatedAt: new Date().toISOString(),
        question,
        intent: "summary",
        answer: "The crisis assistant could not query live emergency-command analytics.",
        confidence: 0,
        citedIncidents: [],
        citedEvidence: [],
        recommendedActions: [],
        simulation: null,
        sourceSystems: [],
        storage: "",
      });
    } finally {
      setAssistantLoading(false);
    }
  }, [question]);

  useEffect(() => {
    const controller = new AbortController();

    async function connectStream() {
      try {
        const response = await fetch("/api/crisis/management/stream", { cache: "no-store", signal: controller.signal });
        const reader = response.body?.getReader();
        if (!reader) throw new Error("Missing crisis stream");
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
            if (!dataLine || Date.now() <= manualUpdateUntil.current) continue;
            const payload = JSON.parse(dataLine.slice(6)) as unknown;
            if (isCrisisResponse(payload)) {
              setAnalysis(payload);
              setLoading(false);
            }
          }
        }
        setStreamStatus("ready");
      } catch {
        if (!controller.signal.aborted) setStreamStatus("fallback");
      }
    }

    const refreshTimer = window.setTimeout(() => {
      void loadDefault();
      void askAssistant();
    }, 200);
    const streamTimer = window.setTimeout(() => {
      void connectStream();
    }, 7000);
    return () => {
      controller.abort();
      window.clearTimeout(refreshTimer);
      window.clearTimeout(streamTimer);
    };
  }, [askAssistant, loadDefault]);

  const topCrisis = analysis?.activeCrises[0] ?? null;
  const severityChart = useMemo(
    () =>
      analysis?.activeCrises.slice(0, 6).map((crisis) => ({
        name: crisis.title.length > 24 ? `${crisis.title.slice(0, 21)}...` : crisis.title,
        severity: Math.round(crisis.severityScore),
        recovery: Math.round(crisis.recoveryPlan.estimatedRecoveryHours),
        band: crisis.severityBand,
      })) ?? [],
    [analysis],
  );
  const impactChart = useMemo(
    () =>
      topCrisis
        ? [
            { name: "Security", value: Math.round(topCrisis.impact.securityImpact), band: topCrisis.severityBand },
            { name: "Operations", value: Math.round(topCrisis.impact.operationalImpact), band: topCrisis.severityBand },
            { name: "Clients", value: Math.round(topCrisis.impact.clientImpact), band: topCrisis.severityBand },
            { name: "Workforce", value: Math.round(topCrisis.impact.workforceImpact), band: topCrisis.severityBand },
            { name: "Reputation", value: Math.round(topCrisis.impact.reputationImpact), band: topCrisis.severityBand },
          ]
        : [],
    [topCrisis],
  );
  const simulationChart = useMemo(
    () =>
      analysis?.simulations.slice(0, 5).map((simulation) => ({
        scenario: labelize(simulation.scenarioType),
        operations: Math.round(simulation.operationalImpact),
        clients: Math.round(simulation.clientImpact),
        recovery: Math.round(simulation.recoveryHours),
      })) ?? [],
    [analysis],
  );
  const activeSimulation = scenarioBuilder?.simulation ?? analysis?.simulations[0] ?? null;

  return (
    <section id="crisis-command-center-panel" data-testid="crisis-command-center-panel" className="space-y-5">
      <div className="flex flex-col gap-3 rounded-lg border border-rose-400/20 bg-slate-950/80 p-5 shadow-[0_24px_90px_rgba(15,23,42,0.45)] lg:flex-row lg:items-center lg:justify-between">
        <div>
          <div className="flex items-center gap-2 text-xs uppercase tracking-[0.28em] text-rose-200/70">
            <Siren className="h-4 w-4" />
            Real-Time Crisis Management AI
          </div>
          <h2 className="mt-2 text-2xl font-semibold text-white">AI Emergency Command Center</h2>
          <p className="mt-2 max-w-3xl text-sm text-slate-300">
            {analysis?.executiveBrief ?? "Detecting active crises, modeling blast radius, and preparing recovery plans."}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <StatusBadge label={streamStatus} icon={Radio} />
          <button
            type="button"
            onClick={() => void loadDefault()}
            className="inline-flex items-center gap-2 rounded-md border border-slate-700 px-3 py-2 text-sm font-medium text-slate-100 hover:border-cyan-300"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </button>
          <button
            type="button"
            onClick={() => void runRansomwareSimulation()}
            className="inline-flex items-center gap-2 rounded-md bg-rose-500 px-3 py-2 text-sm font-semibold text-white hover:bg-rose-400"
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Zap className="h-4 w-4" />}
            Simulate Ransomware
          </button>
        </div>
      </div>

      {error ? <div className="rounded-md border border-red-400/40 bg-red-950/40 p-3 text-sm text-red-100">{error}</div> : null}

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
        <MetricCard label="Active crises" value={analysis?.summary.activeCrises ?? 0} icon={AlertTriangle} tone="rose" />
        <MetricCard label="Critical" value={analysis?.summary.criticalCrises ?? 0} icon={Flame} tone="orange" />
        <MetricCard label="Top severity" value={analysis ? Math.round(analysis.summary.highestSeverityScore) : 0} icon={Shield} tone="cyan" suffix="/100" />
        <MetricCard label="Recovery avg" value={analysis ? Math.round(analysis.summary.averageRecoveryHours) : 0} icon={RefreshCw} tone="violet" suffix="h" />
        <MetricCard label="Exposure" value={formatMoney(analysis?.summary.totalFinancialExposure ?? 0)} icon={Brain} tone="emerald" />
      </div>

      <Panel title="Crisis Scenario Builder" icon={Zap}>
        <div className="grid gap-3 lg:grid-cols-[1.2fr_0.8fr_0.7fr_0.7fr_auto]">
          <label className="grid gap-2 text-xs uppercase tracking-[0.16em] text-slate-400">
            Crisis type
            <select
              value={selectedScenario}
              onChange={(event) => setSelectedScenario(event.target.value as CrisisType)}
              className="h-10 rounded-md border border-slate-700 bg-slate-950 px-3 text-sm normal-case tracking-normal text-white outline-none focus:border-cyan-300"
            >
              {scenarioOptions.map((scenario) => (
                <option key={scenario} value={scenario}>
                  {labelize(scenario)}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-2 text-xs uppercase tracking-[0.16em] text-slate-400">
            Scope
            <input
              value={scenarioScope}
              onChange={(event) => setScenarioScope(event.target.value)}
              className="h-10 rounded-md border border-slate-700 bg-slate-950 px-3 text-sm normal-case tracking-normal text-white outline-none focus:border-cyan-300"
            />
          </label>
          <label className="grid gap-2 text-xs uppercase tracking-[0.16em] text-slate-400">
            Severity
            <input
              type="number"
              min="0.4"
              max="2"
              step="0.05"
              value={severityMultiplier}
              onChange={(event) => setSeverityMultiplier(Number(event.target.value))}
              className="h-10 rounded-md border border-slate-700 bg-slate-950 px-3 text-sm normal-case tracking-normal text-white outline-none focus:border-cyan-300"
            />
          </label>
          <label className="grid gap-2 text-xs uppercase tracking-[0.16em] text-slate-400">
            Horizon
            <input
              type="number"
              min="1"
              max="720"
              value={scenarioHorizon}
              onChange={(event) => setScenarioHorizon(Number(event.target.value))}
              className="h-10 rounded-md border border-slate-700 bg-slate-950 px-3 text-sm normal-case tracking-normal text-white outline-none focus:border-cyan-300"
            />
          </label>
          <button
            type="button"
            onClick={() => void runScenarioBuilder()}
            className="mt-auto inline-flex h-10 items-center justify-center gap-2 rounded-md bg-cyan-400 px-3 text-sm font-semibold text-slate-950 hover:bg-cyan-300"
          >
            {scenarioLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Zap className="h-4 w-4" />}
            Run Scenario
          </button>
        </div>
        <div className="mt-4 grid gap-3 lg:grid-cols-4">
          <MiniStat label="Supported scenarios" value={analysis?.supportedScenarios?.length ?? scenarioOptions.length} />
          <MiniStat label="Readiness" value={`${Math.round(analysis?.productionReadinessScore ?? 0)}/100`} />
          <MiniStat label="Innovation" value={`${Math.round(analysis?.innovationScore ?? 0)}/100`} />
          <MiniStat label="Verdict" value={analysis?.finalVerdict ?? "loading"} />
        </div>
        {scenarioBuilder?.simulation ? (
          <div className="mt-4 rounded-md border border-cyan-300/20 bg-cyan-950/20 p-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="text-sm font-semibold text-white">{scenarioBuilder.scenario.scenarioName}</p>
              <span className="text-xs text-cyan-200">{scenarioBuilder.scenario.executionStatus}</span>
            </div>
            <p className="mt-2 text-sm text-slate-300">
              {labelize(scenarioBuilder.simulation.scenarioType)} projects {Math.round(scenarioBuilder.simulation.operationalImpact)} operational impact,
              {" "}{Math.round(scenarioBuilder.simulation.longTermImpact)} long-term impact, and {Math.round(scenarioBuilder.simulation.recoveryHours)}h recovery.
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              {scenarioBuilder.simulation.executiveRecommendations.slice(0, 3).map((action, index) => (
                <span key={`${action}-${index}`} className="rounded-md border border-slate-700 px-2 py-1 text-xs text-slate-300">
                  {action}
                </span>
              ))}
            </div>
          </div>
        ) : null}
      </Panel>

      {activeSimulation?.executiveImpactAnalysis ? (
        <CrisisExecutiveImpactPanel simulation={activeSimulation} />
      ) : null}

      <div className="grid gap-5 xl:grid-cols-[1.2fr_0.8fr]">
        <Panel title="Active Crisis Severity" icon={Siren}>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={severityChart} margin={{ top: 12, right: 18, bottom: 42, left: 0 }}>
                <CartesianGrid stroke="#1E293B" strokeDasharray="3 3" />
                <XAxis dataKey="name" angle={-18} interval={0} textAnchor="end" height={58} tick={{ fill: "#CBD5E1", fontSize: 11 }} />
                <YAxis tick={{ fill: "#CBD5E1", fontSize: 11 }} />
                <Tooltip contentStyle={{ background: "#020617", border: "1px solid #334155", borderRadius: 8, color: "#E2E8F0" }} />
                <Bar dataKey="severity" radius={[4, 4, 0, 0]}>
                  {severityChart.map((item) => (
                    <Cell key={item.name} fill={severityColor[item.band as CrisisSeverityBand] ?? "#F05D5E"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel title="Top Crisis Impact Radius" icon={Shield}>
          {topCrisis ? (
            <div className="space-y-4">
              <div>
                <p className="text-sm font-semibold text-white">{topCrisis.title}</p>
                <p className="mt-1 text-xs text-slate-400">{topCrisis.rootCauseHypothesis}</p>
              </div>
              <div className="h-52">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={impactChart} dataKey="value" nameKey="name" innerRadius={52} outerRadius={84} paddingAngle={3}>
                      {impactChart.map((item, index) => (
                        <Cell key={`${item.name}-${index}`} fill={index % 2 === 0 ? severityColor[item.band] : "#38BDF8"} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ background: "#020617", border: "1px solid #334155", borderRadius: 8, color: "#E2E8F0" }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="flex flex-wrap gap-2">
                {topCrisis.impact.impactRadius.slice(0, 7).map((item) => (
                  <span key={item} className="rounded-md border border-slate-700 px-2 py-1 text-xs text-slate-300">
                    {item}
                  </span>
                ))}
              </div>
            </div>
          ) : (
            <EmptyState label="No active crisis above command-center threshold." />
          )}
        </Panel>
      </div>

      <div className="grid gap-5 xl:grid-cols-3">
        <Panel title="Recovery Plan" icon={RefreshCw}>
          <div className="space-y-3">
            {topCrisis?.recoveryPlan.recoverySequence.slice(0, 5).map((step) => (
              <div key={`${topCrisis.incidentId}-${step.step}`} className="rounded-md border border-slate-800 bg-slate-900/60 p-3">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm font-medium text-white">Step {step.step}</p>
                  <span className="text-xs text-cyan-200">{step.targetMinutes}m</span>
                </div>
                <p className="mt-1 text-xs text-slate-300">{step.action}</p>
                <p className="mt-2 text-xs text-slate-500">{step.owner}</p>
              </div>
            )) ?? <EmptyState label="Recovery plan pending." />}
          </div>
        </Panel>

        <Panel title="Risk Heatmap" icon={Flame}>
          <div className="grid grid-cols-2 gap-2">
            {(analysis?.heatmap.slice(0, 10) ?? []).map((cell, index) => (
              <HeatmapCell key={`${cell.domain}-${cell.entity}-${index}`} cell={cell} />
            ))}
          </div>
        </Panel>

        <Panel title="Executive Alerts" icon={AlertTriangle}>
          <div className="space-y-3">
            {(analysis?.executiveAlerts.slice(0, 5) ?? []).map((alert) => (
              <div key={alert.alertId} className="rounded-md border border-slate-800 bg-slate-900/60 p-3">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm font-medium text-white">{alert.title}</p>
                  <span className="rounded-sm px-2 py-1 text-[11px] font-semibold text-white" style={{ backgroundColor: severityColor[alert.severityBand] }}>
                    {alert.slaMinutes}m SLA
                  </span>
                </div>
                <p className="mt-1 line-clamp-2 text-xs text-slate-400">{alert.message}</p>
                <p className="mt-2 text-xs text-cyan-200">{alert.channels.join(", ")}</p>
              </div>
            ))}
          </div>
        </Panel>
      </div>

      <div className="grid gap-5 xl:grid-cols-[0.95fr_1.05fr]">
        <Panel title="Worst-Case Simulations" icon={Zap}>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={simulationChart} margin={{ top: 12, right: 18, bottom: 34, left: 0 }}>
                <CartesianGrid stroke="#1E293B" strokeDasharray="3 3" />
                <XAxis dataKey="scenario" tick={{ fill: "#CBD5E1", fontSize: 11 }} />
                <YAxis tick={{ fill: "#CBD5E1", fontSize: 11 }} />
                <Tooltip contentStyle={{ background: "#020617", border: "1px solid #334155", borderRadius: 8, color: "#E2E8F0" }} />
                <Area dataKey="operations" stroke="#FF3B6B" fill="#FF3B6B33" strokeWidth={2} />
                <Area dataKey="clients" stroke="#38BDF8" fill="#38BDF833" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel title="Crisis AI Assistant" icon={Brain}>
          <div className="space-y-4">
            <div className="flex flex-col gap-2 sm:flex-row">
              <input
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                className="min-h-10 flex-1 rounded-md border border-slate-700 bg-slate-950 px-3 text-sm text-white outline-none focus:border-cyan-300"
                placeholder="Ask: How do we recover?"
              />
              <button
                type="button"
                onClick={() => void askAssistant()}
                className="inline-flex min-h-10 items-center justify-center gap-2 rounded-md bg-cyan-400 px-3 text-sm font-semibold text-slate-950 hover:bg-cyan-300"
              >
                {assistantLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                Ask
              </button>
            </div>
            <div className="rounded-md border border-cyan-300/20 bg-cyan-950/20 p-4">
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm font-semibold text-white">{assistant?.intent ? labelize(assistant.intent) : "Executive answer"}</p>
                <span className="text-xs text-cyan-200">{assistant ? Math.round(assistant.confidence * 100) : 0}% confidence</span>
              </div>
              <p className="mt-2 text-sm text-slate-300">{assistant?.answer ?? "The assistant will explain the highest-severity crisis, affected systems, recovery owners, and next actions."}</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {(assistant?.recommendedActions ?? analysis?.recommendations.map((item) => item.action) ?? []).slice(0, 4).map((action) => (
                  <span key={action} className="rounded-md border border-slate-700 px-2 py-1 text-xs text-slate-300">
                    {action}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </Panel>
      </div>

      <Panel title="Executive Recommendations" icon={UsersRound}>
        <div className="grid gap-3 lg:grid-cols-3">
          {(analysis?.recommendations.slice(0, 6) ?? []).map((recommendation) => (
            <RecommendationCard key={recommendation.recommendationId} recommendation={recommendation} />
          ))}
        </div>
      </Panel>
    </section>
  );
}

function CrisisExecutiveImpactPanel({ simulation }: { simulation: CrisisSimulationResult }) {
  const panel = simulation.executiveImpactAnalysis;
  const topTeam = panel.mostAffectedTeams[0];
  const hires = panel.hiringRequirements;
  const forecast = panel.forecastPoints.slice(0, 5);

  return (
    <section
      data-testid="crisis-executive-impact-analysis-panel"
      className="overflow-hidden rounded-lg border border-cyan-300/25 bg-[radial-gradient(circle_at_top_left,rgba(34,211,238,0.18),rgba(15,23,42,0.92)_40%,rgba(2,6,23,0.98))] shadow-[0_24px_110px_rgba(8,47,73,0.35)]"
    >
      <div className="flex flex-col gap-4 border-b border-cyan-300/15 p-5 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2 text-xs uppercase tracking-[0.24em] text-cyan-100/80">
            <Brain className="h-4 w-4" />
            Executive Impact Analysis
            <span className="rounded-sm border border-cyan-300/30 bg-cyan-400/10 px-2 py-1 text-[10px] text-cyan-100">
              {panel.finalVerdict}
            </span>
          </div>
          <h3 className="mt-3 text-xl font-semibold text-white">{panel.scenarioName}</h3>
          <p className="mt-2 max-w-4xl text-sm text-slate-300">
            Crisis simulation generated a {labelize(panel.riskLevel)} executive risk posture with {Math.round(panel.confidenceScore)}% confidence,
            live twin updates, recovery sequencing, and AI council evidence.
          </p>
        </div>
        <div className="rounded-md border border-slate-700 bg-slate-950/60 px-3 py-2 text-right">
          <p className="text-[11px] uppercase tracking-[0.16em] text-slate-500">Trigger</p>
          <p className="mt-1 text-sm font-semibold text-cyan-100">{labelize(panel.triggerType)}</p>
        </div>
      </div>

      <div className="grid gap-3 p-5 sm:grid-cols-2 xl:grid-cols-5">
        <ImpactTile label="Financial Loss" value={formatMoney(panel.financialLoss)} detail={`${panel.revenueImpactPercent}% revenue impact`} />
        <ImpactTile label="Delay Probability" value={`${Math.round(panel.delayProbability)}%`} detail={`${Math.round(simulation.recoveryHours)}h recovery path`} />
        <ImpactTile label="Most Affected" value={topTeam?.teamName ?? "No critical team"} detail={topTeam ? `${Math.round(topTeam.impactScore)} impact score` : "Monitoring only"} />
        <ImpactTile label="Required Hires" value={hires.requiredHires} detail={`${labelize(hires.priority)} priority`} />
        <ImpactTile label="Productivity Cost" value={formatMoney(panel.productivityCost)} detail={`${formatMoney(panel.costIncrease)} added cost`} />
      </div>

      <div className="grid gap-4 px-5 pb-5 xl:grid-cols-[1.05fr_0.95fr]">
        <div className="rounded-md border border-slate-800 bg-slate-950/55 p-4">
          <div className="mb-3 flex items-center justify-between gap-3">
            <h4 className="text-sm font-semibold uppercase tracking-[0.16em] text-slate-200">Most Affected Teams</h4>
            <span className="text-xs text-cyan-200">{panel.mostAffectedTeams.length} teams</span>
          </div>
          <div className="space-y-2">
            {panel.mostAffectedTeams.slice(0, 4).map((team, index) => (
              <div key={`${team.department}-${team.teamName}-${index}`} className="rounded-md border border-slate-800 bg-slate-900/60 p-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="text-sm font-medium text-white">{team.teamName}</p>
                  <span className="text-xs text-rose-200">{Math.round(team.delayRisk)}% delay</span>
                </div>
                <div className="mt-2 grid grid-cols-3 gap-2 text-xs text-slate-400">
                  <span>Shortage {Math.round(team.shortageScore)}%</span>
                  <span>Burnout {Math.round(team.burnoutRisk)}%</span>
                  <span>Knowledge {Math.round(team.knowledgeLossRisk)}%</span>
                </div>
                <p className="mt-2 text-xs text-slate-500">{team.reason}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="grid gap-4">
          <div className="rounded-md border border-slate-800 bg-slate-950/55 p-4">
            <h4 className="text-sm font-semibold uppercase tracking-[0.16em] text-slate-200">Recovery Strategy</h4>
            <div className="mt-3 grid gap-3 sm:grid-cols-2">
              <ActionColumn title="Immediate" actions={panel.recoveryStrategy.immediateActions} />
              <ActionColumn title="Short Term" actions={panel.recoveryStrategy.shortTermRecovery} />
            </div>
          </div>

          <div className="rounded-md border border-slate-800 bg-slate-950/55 p-4">
            <h4 className="text-sm font-semibold uppercase tracking-[0.16em] text-slate-200">Hiring Requirements</h4>
            <p className="mt-2 text-sm text-slate-300">{hires.rationale}</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {hires.skillsNeeded.slice(0, 6).map((skill) => (
                <span key={skill} className="rounded-md border border-cyan-300/20 bg-cyan-950/30 px-2 py-1 text-xs text-cyan-100">
                  {skill}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="grid gap-4 border-t border-cyan-300/15 p-5 xl:grid-cols-[0.85fr_1.15fr]">
        <div className="rounded-md border border-slate-800 bg-slate-950/55 p-4">
          <h4 className="text-sm font-semibold uppercase tracking-[0.16em] text-slate-200">Recovery Timeline</h4>
          <div className="mt-4 space-y-3">
            {forecast.map((point) => (
              <div key={point.label} className="grid grid-cols-[80px_1fr_auto] items-center gap-3">
                <span className="text-xs text-slate-400">{point.label}</span>
                <div className="h-2 rounded-full bg-slate-800">
                  <div className="h-2 rounded-full bg-cyan-300" style={{ width: `${Math.max(8, Math.min(100, point.recoveryProgress))}%` }} />
                </div>
                <span className="text-xs text-cyan-100">{Math.round(point.recoveryProgress)}%</span>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-md border border-slate-800 bg-slate-950/55 p-4">
          <h4 className="text-sm font-semibold uppercase tracking-[0.16em] text-slate-200">AI Agent Council</h4>
          <div className="mt-3 grid gap-3 lg:grid-cols-2">
            {panel.agentCouncil.slice(0, 4).map((agent) => (
              <div key={agent.agent} className="rounded-md border border-slate-800 bg-slate-900/60 p-3">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-medium text-white">{agent.agent}</p>
                  <span className="text-xs text-cyan-200">{Math.round(agent.confidence * 100)}%</span>
                </div>
                <p className="mt-2 line-clamp-2 text-xs text-slate-400">{agent.finding}</p>
                <p className="mt-2 line-clamp-2 text-xs text-slate-300">{agent.recommendation}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

function ImpactTile({ label, value, detail }: { label: string; value: number | string; detail: string }) {
  return (
    <div className="rounded-md border border-slate-800 bg-slate-950/60 p-4">
      <p className="text-[11px] uppercase tracking-[0.16em] text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-white">{value}</p>
      <p className="mt-1 text-xs text-slate-400">{detail}</p>
    </div>
  );
}

function ActionColumn({ title, actions }: { title: string; actions: string[] }) {
  return (
    <div>
      <p className="text-xs uppercase tracking-[0.16em] text-cyan-200">{title}</p>
      <div className="mt-2 space-y-2">
        {actions.slice(0, 4).map((action, index) => (
          <div key={`${title}-${action}-${index}`} className="rounded-md border border-slate-800 bg-slate-900/60 p-2 text-xs text-slate-300">
            {action}
          </div>
        ))}
      </div>
    </div>
  );
}

function MetricCard({
  label,
  value,
  icon: Icon,
  tone,
  suffix = "",
}: {
  label: string;
  value: number | string;
  icon: LucideIcon;
  tone: "rose" | "orange" | "cyan" | "violet" | "emerald";
  suffix?: string;
}) {
  const tones = {
    rose: "border-rose-400/25 text-rose-200",
    orange: "border-orange-400/25 text-orange-200",
    cyan: "border-cyan-400/25 text-cyan-200",
    violet: "border-violet-400/25 text-violet-200",
    emerald: "border-emerald-400/25 text-emerald-200",
  };
  return (
    <div className={`rounded-lg border bg-slate-950/70 p-4 ${tones[tone]}`}>
      <div className="flex items-center justify-between gap-3">
        <span className="text-xs uppercase tracking-[0.18em] text-slate-400">{label}</span>
        <Icon className="h-4 w-4" />
      </div>
      <p className="mt-3 text-2xl font-semibold text-white">
        {value}
        {suffix}
      </p>
    </div>
  );
}

function MiniStat({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-md border border-slate-800 bg-slate-900/60 p-3">
      <p className="text-[11px] uppercase tracking-[0.16em] text-slate-500">{label}</p>
      <p className="mt-2 text-sm font-semibold text-white">{value}</p>
    </div>
  );
}

function Panel({ title, icon: Icon, children }: { title: string; icon: LucideIcon; children: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-950/70 p-4">
      <div className="mb-4 flex items-center justify-between gap-3">
        <h3 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.18em] text-slate-200">
          <Icon className="h-4 w-4 text-cyan-200" />
          {title}
        </h3>
      </div>
      {children}
    </div>
  );
}

function StatusBadge({ label, icon: Icon }: { label: string; icon: LucideIcon }) {
  return (
    <span className="inline-flex items-center gap-2 rounded-md border border-cyan-300/30 bg-cyan-950/30 px-3 py-2 text-sm font-medium text-cyan-100">
      <Icon className="h-4 w-4" />
      {label}
    </span>
  );
}

function HeatmapCell({ cell }: { cell: CrisisHeatmapCell }) {
  return (
    <div className="min-h-24 rounded-md border border-slate-800 p-3" style={{ background: `${severityColor[cell.severityBand]}18` }}>
      <div className="flex items-center justify-between gap-2">
        <span className="text-[11px] uppercase tracking-[0.16em] text-slate-400">{cell.domain}</span>
        <span className="text-xs font-semibold text-white">{Math.round(cell.riskScore)}</span>
      </div>
      <p className="mt-2 text-sm font-medium text-white">{cell.entity}</p>
      <p className="mt-1 text-xs text-slate-400">{cell.recommendedOwner}</p>
    </div>
  );
}

function RecommendationCard({ recommendation }: { recommendation: CrisisRecommendation }) {
  return (
    <div className="rounded-md border border-slate-800 bg-slate-900/60 p-3">
      <div className="flex items-center justify-between gap-3">
        <span className="rounded-sm px-2 py-1 text-[11px] font-semibold text-slate-950" style={{ backgroundColor: riskColor[recommendation.priority] }}>
          {labelize(recommendation.priority)}
        </span>
        <span className="text-xs text-cyan-200">{Math.round(recommendation.expectedRiskReduction)}% reduction</span>
      </div>
      <p className="mt-3 text-sm font-medium text-white">{recommendation.action}</p>
      <p className="mt-2 line-clamp-3 text-xs text-slate-400">{recommendation.reason}</p>
    </div>
  );
}

function EmptyState({ label }: { label: string }) {
  return <div className="rounded-md border border-slate-800 bg-slate-900/50 p-4 text-sm text-slate-400">{label}</div>;
}

async function fetchJson<T>(input: RequestInfo | URL, init?: RequestInit): Promise<T> {
  const response = await fetch(input, { cache: "no-store", ...init });
  if (!response.ok) throw new Error(`Request failed: ${response.status}`);
  return (await response.json()) as T;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value && typeof value === "object" && !Array.isArray(value));
}

function isCrisisResponse(value: unknown): value is CrisisCommandCenterResponse {
  return (
    isRecord(value) &&
    typeof value.model === "string" &&
    isRecord(value.summary) &&
    Array.isArray(value.activeCrises) &&
    Array.isArray(value.recoveryPlans) &&
    Array.isArray(value.simulations)
  );
}

function isAssistant(value: unknown): value is CrisisAssistantResponse {
  return isRecord(value) && typeof value.answer === "string" && typeof value.intent === "string";
}

function isScenarioBuilder(value: unknown): value is CrisisScenarioBuilderResponse {
  return isRecord(value) && isRecord(value.scenario) && typeof value.scenario.scenarioId === "string";
}

function labelize(value: string): string {
  return value.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatMoney(value: number): string {
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `$${Math.round(value / 1_000)}K`;
  return `$${Math.round(value)}`;
}
