"use client";

import {
  AlertTriangle,
  Bot,
  BrainCircuit,
  Building2,
  CircleDollarSign,
  GitCompare,
  Loader2,
  Radio,
  RefreshCw,
  Send,
  Sparkles,
  TimerReset,
  TrendingUp,
  Users,
} from "lucide-react";
import type React from "react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Bar, BarChart, CartesianGrid, Cell, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type {
  CompanySimulationAssistantResponse,
  CompanySimulationLabResponse,
  CompanySimulationRiskLevel,
  CompanySimulationScenarioResult,
  CompanySimulationScenarioType,
} from "@/types/company-simulation-lab";

const riskColor: Record<CompanySimulationRiskLevel, string> = {
  low: "#7CF0A6",
  medium: "#F6B44B",
  high: "#F05D5E",
  critical: "#FF3B6B",
};

const scenarioButtons: Array<{
  type: CompanySimulationScenarioType;
  label: string;
  payload: Record<string, unknown>;
}> = [
  {
    type: "work_from_home_policy",
    label: "WFH 5 -> 2",
    payload: {
      scenario_id: "ui-wfh-5-to-2",
      scenario_type: "work_from_home_policy",
      question: "What happens if work-from-home is reduced from 5 days to 2 days?",
      remote_days_before: 5,
      remote_days_after: 2,
    },
  },
  {
    type: "employee_resignation",
    label: "30 resign",
    payload: { scenario_id: "ui-future-resignation-30", scenario_type: "employee_resignation", question: "What happens if 30 engineers resign?", resignation_count: 30, resignation_seniority: "senior", mode: "stress" },
  },
  {
    type: "hiring_growth",
    label: "Hire 50",
    payload: { scenario_id: "ui-hire-50", scenario_type: "hiring_growth", question: "What happens if we hire 50 engineers?", hiring_count: 50 },
  },
  {
    type: "revenue_change",
    label: "Revenue -20%",
    payload: { scenario_id: "ui-revenue-drop-20", scenario_type: "revenue_change", question: "What happens if revenue drops 20%?", revenue_change_percent: -20 },
  },
  {
    type: "client_loss",
    label: "Client leaves",
    payload: { scenario_id: "ui-client-loss", scenario_type: "client_loss", question: "What happens if our biggest client leaves?", client_loss_percent: 20 },
  },
  {
    type: "market_expansion",
    label: "New office",
    payload: { scenario_id: "ui-new-office", scenario_type: "market_expansion", question: "What happens if we open a new office?", office_count: 1, hiring_count: 40, revenue_change_percent: 8 },
  },
  {
    type: "hiring_freeze",
    label: "Hiring freeze",
    payload: { scenario_id: "ui-hiring-freeze", scenario_type: "hiring_freeze", question: "What happens if hiring freezes for 6 months?", hiring_freeze_months: 6 },
  },
  {
    type: "employee_resignation",
    label: "20 resign",
    payload: { scenario_id: "ui-resignation-20", scenario_type: "employee_resignation", question: "What happens if 20 engineers resign?", resignation_count: 20, resignation_seniority: "senior" },
  },
  {
    type: "department_restructure",
    label: "Restructure",
    payload: { scenario_id: "ui-restructure", scenario_type: "department_restructure", question: "What happens if Engineering merges with Security?", source_department: "Engineering", target_department: "Security" },
  },
  {
    type: "budget_reduction",
    label: "Budget -20%",
    payload: { scenario_id: "ui-budget-20", scenario_type: "budget_reduction", question: "What happens if budget is reduced by 20%?", budget_reduction_percent: 20 },
  },
  {
    type: "meeting_reduction",
    label: "Meetings -50%",
    payload: { scenario_id: "ui-meeting-50", scenario_type: "meeting_reduction", question: "What happens if meetings are reduced by 50%?", meeting_reduction_percent: 50 },
  },
];

const FUTURE_DEMO_SCENARIO_ID = "future-demo-engineer-resignation-30";

const FUTURE_DEMO_SCENARIO = {
  type: "employee_resignation" as CompanySimulationScenarioType,
  label: "Show Future",
  payload: {
    scenario_id: FUTURE_DEMO_SCENARIO_ID,
    scenario_type: "employee_resignation",
    question: "What happens if 30 engineers resign?",
    resignation_count: 30,
    resignation_seniority: "senior",
    mode: "stress",
  },
};

const LIVE_FUTURE_STEPS = [
  "Read current company state",
  "Load employee, team, department, project, and company twins",
  "Generate future states",
  "Run workforce, project, revenue, and risk simulations",
  "Animate team stress, project health, revenue, and risk propagation",
  "Run AI Agent Council",
  "Generate executive recommendations",
];

export function CompanySimulationLabPanel() {
  const [lab, setLab] = useState<CompanySimulationLabResponse | null>(null);
  const [selected, setSelected] = useState<CompanySimulationScenarioResult | null>(null);
  const [assistant, setAssistant] = useState<CompanySimulationAssistantResponse | null>(null);
  const [question, setQuestion] = useState("Compare hybrid vs office-first.");
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState<CompanySimulationScenarioType | null>(null);
  const [assistantLoading, setAssistantLoading] = useState(false);
  const [streamStatus, setStreamStatus] = useState("connecting");
  const [error, setError] = useState("");
  const [futureDemoRunning, setFutureDemoRunning] = useState(false);
  const [futureDemoStep, setFutureDemoStep] = useState(0);
  const manualScenarioUntil = useRef(0);
  const futureDemoTimerRef = useRef<number | null>(null);

  const loadDefault = useCallback(async () => {
    setLoading(true);
    setError("");
    manualScenarioUntil.current = 0;
    try {
      const payload = await fetchJson("/api/simulation/company-lab/default", { cache: "no-store" }, 90000);
      if (!isLabResponse(payload)) throw new Error("Malformed simulation lab payload");
      setLab(payload);
      setSelected((current) => current ?? payload.scenarios[0] ?? null);
      setStreamStatus((status) => (status === "connecting" ? "polling" : status));
    } catch {
      setError("Company Simulation Lab could not refresh executive scenario intelligence.");
    } finally {
      setLoading(false);
    }
  }, []);

  const runScenario = useCallback(async (config: (typeof scenarioButtons)[number]) => {
    setRunning(config.type);
    setError("");
    manualScenarioUntil.current = Date.now() + 30000;
    try {
      const payload = await fetchJson(
        "/api/simulation/company-lab/simulate",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(config.payload),
          cache: "no-store",
        },
        60000,
      );
      if (!isLabResponse(payload)) throw new Error("Malformed scenario payload");
      setSelected(payload.scenarios[0] ?? null);
      setLab((current) => (current ? { ...current, scenarios: payload.scenarios, comparison: payload.comparison, executiveRecommendations: payload.executiveRecommendations } : payload));
    } catch {
      setError("Company Simulation Lab could not run the selected scenario.");
    } finally {
      setRunning(null);
    }
  }, []);

  const runFutureDemo = useCallback(async () => {
    if (futureDemoTimerRef.current) window.clearInterval(futureDemoTimerRef.current);
    const cachedFuture = lab?.scenarios.find((scenario) => scenario.scenarioId === FUTURE_DEMO_SCENARIO_ID) ?? lab?.scenarios.find((scenario) => scenario.scenarioType === "employee_resignation" && scenario.question.includes("30"));
    setFutureDemoRunning(true);
    setFutureDemoStep(0);
    setError("");
    manualScenarioUntil.current = Date.now() + 30000;
    futureDemoTimerRef.current = window.setInterval(() => {
      setFutureDemoStep((step) => Math.min(LIVE_FUTURE_STEPS.length - 1, step + 1));
    }, 700);
    if (cachedFuture) {
      setSelected(cachedFuture);
      await new Promise((resolve) => window.setTimeout(resolve, LIVE_FUTURE_STEPS.length * 700));
    } else {
      await runScenario(FUTURE_DEMO_SCENARIO);
    }
    if (futureDemoTimerRef.current) window.clearInterval(futureDemoTimerRef.current);
    setFutureDemoStep(LIVE_FUTURE_STEPS.length - 1);
    setFutureDemoRunning(false);
  }, [lab, runScenario]);

  const askAssistant = useCallback(async () => {
    if (!question.trim()) return;
    setAssistantLoading(true);
    try {
      const payload = await fetchJson(
        "/api/simulation/company-lab/assistant",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question, horizon_months: 12 }),
          cache: "no-store",
        },
        60000,
      );
      if (!isAssistantResponse(payload)) throw new Error("Malformed assistant payload");
      setAssistant(payload);
      if (payload.scenario) setSelected(payload.scenario);
    } catch {
      setAssistant({
        model: "AI Simulation Assistant",
        generatedAt: new Date().toISOString(),
        question,
        intent: "error",
        answer: "AI Simulation Assistant could not execute the scenario through the live API.",
        confidence: 0,
        scenario: null,
        comparison: [],
        recommendedActions: [],
        citedEvidence: [],
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
      let streamStarted = false;
      const fallback = window.setTimeout(() => {
        if (!streamStarted && !controller.signal.aborted) setStreamStatus("polling");
      }, 12000);
      try {
        const response = await fetch("/api/simulation/company-lab/stream", { cache: "no-store", signal: controller.signal });
        if (!response.ok) throw new Error("Company Simulation Lab stream failed");
        const reader = response.body?.getReader();
        if (!reader) throw new Error("Missing Company Simulation Lab stream");
        const decoder = new TextDecoder();
        let buffer = "";
        streamStarted = true;
        window.clearTimeout(fallback);
        setStreamStatus("streaming");
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const events = buffer.split("\n\n");
          buffer = events.pop() ?? "";
          for (const event of events) {
            const dataLine = event.split("\n").find((line) => line.startsWith("data: "));
            if (!dataLine) continue;
            const payload = JSON.parse(dataLine.slice(6));
            if (isLabResponse(payload) && Date.now() > manualScenarioUntil.current) {
              setLab(payload);
              setSelected((current) => current ?? payload.scenarios[0] ?? null);
              setLoading(false);
            }
          }
        }
        setStreamStatus("polling");
      } catch {
        if (!controller.signal.aborted) setStreamStatus("polling");
      } finally {
        window.clearTimeout(fallback);
      }
    }

    const firstRefresh = window.setTimeout(() => {
      void loadDefault();
    }, 0);
    const streamRefresh = window.setTimeout(() => {
      void connectStream();
    }, 3000);
    return () => {
      controller.abort();
      window.clearTimeout(firstRefresh);
      window.clearTimeout(streamRefresh);
      if (futureDemoTimerRef.current) window.clearInterval(futureDemoTimerRef.current);
    };
  }, [loadDefault]);

  const active = selected ?? lab?.scenarios[0] ?? null;
  const forecastData = useMemo(
    () =>
      active?.forecasts.map((item) => ({
        metric: shortMetric(item.metric),
        baseline: item.unit === "$" ? dollarsToMillions(item.baseline) : item.baseline,
        projected: item.unit === "$" ? dollarsToMillions(item.projected) : item.projected,
        delta: item.unit === "$" ? dollarsToMillions(item.delta) : item.delta,
      })) ?? [],
    [active],
  );
  const riskData = useMemo(
    () =>
      active?.riskHeatmap.slice(0, 6).map((item) => ({
        domain: item.domain,
        risk: Math.round(item.riskScore),
        level: item.riskLevel,
      })) ?? [],
    [active],
  );
  const comparisonData = useMemo(
    () =>
      lab?.comparison.slice(0, 6).map((item) => ({
        label: scenarioShort(item.scenarioType),
        score: Math.round(item.score),
        success: Math.round(item.successProbability),
        level: item.riskLevel,
      })) ?? [],
    [lab],
  );
  const revenueEvolutionData = useMemo(
    () =>
      active?.revenueEvolution.map((item) => ({
        month: `M${item.month}`,
        current: dollarsToMillions(item.current),
        bestCase: dollarsToMillions(item.bestCase),
        expectedCase: dollarsToMillions(item.expectedCase),
        worstCase: dollarsToMillions(item.worstCase),
      })) ?? [],
    [active],
  );

  return (
    <article className="border border-cyan/20 bg-panel/85 p-5 shadow-control backdrop-blur" data-testid="company-simulation-lab-panel">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div className="max-w-3xl">
          <div className="flex items-center gap-2 text-xs uppercase text-cyan">
            <BrainCircuit className="size-4" />
            <span>AI Company Simulation Lab</span>
            <span className="inline-flex items-center gap-1 text-mint">
              <Radio className="size-3" />
              {streamStatus}
            </span>
          </div>
          <h2 className="mt-2 text-2xl font-semibold text-white">Business decision flight simulator</h2>
          <p className="mt-2 text-sm leading-6 text-slate-400">
            Test major operating decisions against the company digital twin before rollout: WFH policy, hiring freeze, resignations, restructuring, budget cuts, meeting policy, and scenario comparisons.
          </p>
        </div>
        <button className="inline-flex items-center gap-2 border border-line bg-panel2 px-3 py-2 text-sm text-white hover:border-cyan/60" onClick={loadDefault} type="button">
          {loading ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />}
          Refresh
        </button>
      </div>

      {error ? <p className="mt-4 border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-200">{error}</p> : null}
      {loading && !lab ? <p className="mt-5 text-sm text-slate-400">Running business flight simulator...</p> : null}

      {lab && active ? (
        <>
          <section className="mt-5 border border-mint/25 bg-void/45 p-4" data-testid="live-company-simulation-engine">
            <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
              <div className="max-w-3xl">
                <div className="flex flex-wrap items-center gap-2 text-xs uppercase text-mint">
                  <Sparkles className="size-4" />
                  <span>Future Demo Mode</span>
                  <span className="border border-mint/30 px-2 py-1 text-[10px]">{active.visualizationEngineStatus}</span>
                </div>
                <h3 className="mt-2 text-2xl font-semibold text-white">Live Company Simulation Engine</h3>
                <p className="mt-2 text-sm leading-6 text-slate-400">
                  Press <span className="text-white">SIMULATE FUTURE</span> to read the current company state, update digital twins, run the future engine, animate risk propagation, and generate executive action from real simulation output.
                </p>
              </div>
              <div className="grid gap-2 sm:grid-cols-2 xl:w-[360px]">
                <button
                  className="inline-flex h-12 items-center justify-center gap-2 border border-mint/50 bg-mint/15 px-4 text-sm font-semibold uppercase tracking-wide text-mint transition hover:bg-mint/20 disabled:cursor-wait disabled:opacity-70"
                  disabled={futureDemoRunning || running !== null}
                  onClick={() => void runFutureDemo()}
                  type="button"
                >
                  {futureDemoRunning ? <Loader2 className="size-4 animate-spin" /> : <Sparkles className="size-4" />}
                  SIMULATE FUTURE
                </button>
                <button
                  className="inline-flex h-12 items-center justify-center gap-2 border border-cyan/50 bg-cyan/10 px-4 text-sm font-semibold text-white transition hover:bg-cyan/15 disabled:cursor-wait disabled:opacity-70"
                  disabled={futureDemoRunning || running !== null}
                  onClick={() => void runFutureDemo()}
                  type="button"
                >
                  {futureDemoRunning ? <Loader2 className="size-4 animate-spin" /> : <TimerReset className="size-4" />}
                  Show Future
                </button>
              </div>
            </div>

            <div className="mt-4 grid gap-2 md:grid-cols-4 xl:grid-cols-7">
              {LIVE_FUTURE_STEPS.map((step, index) => (
                <div
                  className={`min-h-20 border p-3 transition ${
                    index <= futureDemoStep ? "border-mint/50 bg-mint/10 text-white" : "border-line/60 bg-panel/45 text-slate-500"
                  }`}
                  key={step}
                >
                  <span className="text-[10px] uppercase">Step {index + 1}</span>
                  <p className="mt-2 text-xs leading-5">{step}</p>
                </div>
              ))}
            </div>

            <section className="mt-4 grid gap-4 xl:grid-cols-[1.15fr_0.85fr]">
              <div className="border border-line/70 bg-panel/45 p-4">
                <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
                  <Users className="size-4" />
                  <span>Employee Movement Visualization</span>
                </div>
                <div className="grid gap-3 md:grid-cols-4">
                  {active.employeeMovement.map((frame) => (
                    <div className="border border-line/60 bg-void/50 p-3" key={`${frame.label}-${frame.month}`}>
                      <div className="flex items-center justify-between gap-3 text-xs uppercase text-slate-500">
                        <span>{frame.label}</span>
                        <span>M{frame.month}</span>
                      </div>
                      <strong className={`mt-2 block text-2xl ${frame.netHeadcountChange < 0 ? "text-signal" : "text-mint"}`}>{signedInt(frame.netHeadcountChange)}</strong>
                      <p className="mt-2 text-xs leading-5 text-slate-400">
                        Hires {frame.hires} | Exits {frame.exits} | Transfers {frame.transfers}
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="border border-line/70 bg-panel/45 p-4">
                <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
                  <Building2 className="size-4" />
                  <span>Current Company &rarr; Shadow Company &rarr; Future Company</span>
                </div>
                <div className="grid gap-3">
                  {active.shadowCompanyStages.map((stage) => (
                    <div className="border border-line/60 bg-void/50 p-3" key={stage.stage}>
                      <div className="flex items-center justify-between gap-3">
                        <strong className="text-sm text-white">{stage.label}</strong>
                        <span className={stage.riskScore >= 58 ? "text-signal" : "text-mint"}>{Math.round(stage.riskScore)} risk</span>
                      </div>
                      <div className="mt-2 grid grid-cols-3 gap-2 text-xs text-slate-400">
                        <span>Health {Math.round(stage.healthScore)}</span>
                        <span>{formatMoney(stage.revenue)}</span>
                        <span>{stage.workforce} people</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </section>

            <section className="mt-4 grid gap-4 xl:grid-cols-3">
              <div className="border border-line/70 bg-panel/45 p-4">
                <span className="text-xs uppercase text-slate-500">Team Stress Evolution</span>
                <div className="mt-3 grid gap-3">
                  {active.teamStressEvolution.slice(0, 5).map((team) => (
                    <div key={team.team}>
                      <div className="flex items-center justify-between gap-3 text-xs">
                        <span className="text-white">{team.team}</span>
                        <span className={riskTextColor(team.riskLevel)}>{Math.round(team.projectedStress)} {team.riskLevel}</span>
                      </div>
                      <div className="mt-2 h-2 bg-void">
                        <div className={riskBarColor(team.riskLevel)} style={{ width: `${Math.max(6, team.projectedStress)}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="border border-line/70 bg-panel/45 p-4">
                <span className="text-xs uppercase text-slate-500">Project Health Visualization</span>
                <div className="mt-3 grid gap-2">
                  {active.projectHealthVisualization.slice(0, 5).map((project) => (
                    <div className="border border-line/60 bg-void/50 p-3" key={project.project}>
                      <div className="flex items-center justify-between gap-3 text-xs">
                        <span className="text-white">{project.project}</span>
                        <span className={project.projectedState === "Delayed" ? "text-signal" : project.projectedState === "At Risk" ? "text-amber-300" : "text-mint"}>
                          {project.projectedState}
                        </span>
                      </div>
                      <p className="mt-2 text-xs text-slate-400">{project.delayDays.toFixed(1)}d delay | {Math.round(project.riskScore)} risk</p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="border border-line/70 bg-panel/45 p-4">
                <span className="text-xs uppercase text-slate-500">Risk Propagation Engine</span>
                <div className="mt-3 grid gap-2">
                  {active.riskPropagationPath.map((step) => (
                    <div className="border border-line/60 bg-void/50 p-3" key={step.step}>
                      <div className="flex items-center justify-between gap-3 text-xs">
                        <span className="text-white">{step.step}. {step.title}</span>
                        <span className={step.riskScore >= 58 ? "text-signal" : "text-mint"}>{Math.round(step.riskScore)}</span>
                      </div>
                      <p className="mt-1 text-xs text-slate-500">
                        {step.source} &rarr; {step.target}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </section>

            <section className="mt-4 grid gap-4 xl:grid-cols-[1fr_1fr]">
              <ChartBlock title="Revenue Evolution: Current, Best, Expected, Worst">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={revenueEvolutionData}>
                    <CartesianGrid stroke="#233047" strokeDasharray="3 3" />
                    <XAxis dataKey="month" stroke="#64748b" fontSize={10} />
                    <YAxis stroke="#64748b" fontSize={11} />
                    <Tooltip contentStyle={{ background: "#0b1220", border: "1px solid #1f2a44", color: "#e2e8f0" }} />
                    <Line dataKey="current" stroke="#64748b" strokeWidth={2} dot={false} />
                    <Line dataKey="bestCase" stroke="#7CF0A6" strokeWidth={2} dot={false} />
                    <Line dataKey="expectedCase" stroke="#4CC9F0" strokeWidth={2} dot={false} />
                    <Line dataKey="worstCase" stroke="#F05D5E" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </ChartBlock>

              <div className="border border-line/70 bg-panel/45 p-4">
                <span className="text-xs uppercase text-slate-500">Multi-Future Engine</span>
                <div className="mt-3 grid gap-2 md:grid-cols-2">
                  {active.multiFutureBranches.map((branch) => (
                    <div className="border border-line/60 bg-void/50 p-3" key={branch.caseName}>
                      <div className="flex items-center justify-between gap-3 text-xs uppercase">
                        <span className="text-white">{branch.caseName.replaceAll("_", " ")}</span>
                        <span className={branch.riskScore >= 58 ? "text-signal" : "text-mint"}>{Math.round(branch.riskScore)} risk</span>
                      </div>
                      <p className="mt-2 text-xs leading-5 text-slate-400">
                        {Math.round(branch.successProbability)}% success | {formatMoney(branch.revenueImpact)} revenue
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </section>

            <section className="mt-4 grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
              <div className="border border-line/70 bg-panel/45 p-4">
                <span className="text-xs uppercase text-cyan">AI Explanation Engine</span>
                <p className="mt-3 text-sm leading-6 text-slate-300">{active.aiExplanation}</p>
              </div>
              <div className="border border-line/70 bg-panel/45 p-4">
                <span className="text-xs uppercase text-cyan">AI Agent Council</span>
                <div className="mt-3 grid gap-2 md:grid-cols-2">
                  {active.agentCouncil.map((agent) => (
                    <div className="border border-line/60 bg-void/50 p-3" key={agent.agent}>
                      <div className="flex items-center justify-between gap-3">
                        <strong className="text-sm text-white">{agent.agent}</strong>
                        <span className="text-xs text-mint">{Math.round(agent.confidence * 100)}%</span>
                      </div>
                      <p className="mt-2 text-xs leading-5 text-slate-400">{agent.finding}</p>
                    </div>
                  ))}
                </div>
              </div>
            </section>
          </section>

          <section className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-6">
            <Metric icon={Sparkles} label="Decision readiness" value={`${Math.round(lab.summary.decisionReadinessScore)}%`} detail={`${lab.summary.scenarioCount} scenarios`} />
            <Metric icon={TrendingUp} label="Success" value={`${Math.round(active.successProbability)}%`} detail={`${Math.round(active.confidence * 100)}% confidence`} />
            <Metric icon={AlertTriangle} label="Top risk" value={lab.summary.topRisk} detail={active.riskHeatmap[0]?.riskLevel ?? "low"} />
            <Metric icon={CircleDollarSign} label="Financial impact" value={formatMoney(active.impact.financialImpact)} detail={formatMoney(active.impact.revenueImpact)} />
            <Metric icon={Users} label="Attrition" value={`${signed(active.impact.attritionRiskChange)}%`} detail={`${signed(active.impact.burnoutChange)}% burnout`} />
            <Metric icon={TimerReset} label="Delay" value={`${active.impact.deliveryDelayDays.toFixed(1)}d`} detail={`${signed(active.impact.productivityChange)}% productivity`} />
          </section>

          <section className="mt-5">
            <div className="mb-3 flex items-center gap-2 text-xs uppercase text-slate-500">
              <Building2 className="size-4 text-cyan" />
              <span>Scenario Builder</span>
            </div>
            <div className="grid gap-2 md:grid-cols-3 xl:grid-cols-6">
              {scenarioButtons.map((config) => {
                const scenarioId = String(config.payload.scenario_id ?? `${config.type}-${config.label}`);
                return (
                  <button
                    className={`min-h-16 border px-3 py-2 text-left text-xs uppercase transition ${
                      active.scenarioId === scenarioId ? "border-cyan bg-cyan/10 text-white" : "border-line/70 bg-void/45 text-slate-400 hover:border-cyan/60 hover:text-white"
                    } disabled:cursor-wait disabled:opacity-70`}
                    disabled={running !== null}
                    key={scenarioId}
                    onClick={() => void runScenario(config)}
                    type="button"
                  >
                    <span>{config.label}</span>
                    {running === config.type ? <Loader2 className="mt-2 size-4 animate-spin text-cyan" /> : null}
                  </button>
                );
              })}
            </div>
          </section>

          <section className="mt-5 grid gap-4 xl:grid-cols-[1fr_0.9fr]">
            <div className="border border-line/70 bg-void/35 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
                <GitCompare className="size-4" />
                <span>Simulation Results</span>
              </div>
              <p className="text-sm leading-6 text-slate-300">{active.executiveSummary}</p>
              <div className="mt-4 grid gap-3 md:grid-cols-2">
                <ImpactLine label="Employee happiness" value={active.impact.employeeHappinessChange} />
                <ImpactLine label="Collaboration" value={active.impact.collaborationChange} />
                <ImpactLine label="Recruitment difficulty" value={active.impact.recruitmentDifficultyChange} invert />
                <ImpactLine label="Growth impact" value={active.impact.growthImpact} />
              </div>
            </div>

            <div className="border border-line/70 bg-void/35 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-mint">
                <Bot className="size-4" />
                <span>AI Simulation Assistant</span>
              </div>
              <div className="flex flex-col gap-2 sm:flex-row">
                <input
                  className="min-h-10 flex-1 border border-line bg-panel/80 px-3 text-sm text-white outline-none focus:border-cyan/60"
                  onChange={(event) => setQuestion(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") void askAssistant();
                  }}
                  value={question}
                />
                <button className="inline-flex items-center justify-center gap-2 border border-cyan/40 bg-cyan/10 px-4 py-2 text-sm text-white hover:bg-cyan/15" onClick={askAssistant} type="button">
                  {assistantLoading ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
                  Ask
                </button>
              </div>
              <div className="mt-4 border border-line/60 bg-panel/55 p-3">
                <p className="text-sm leading-6 text-slate-200">{assistant?.answer ?? lab.summary.recommendedScenario}</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {(assistant?.citedEvidence ?? active.digitalTwinEvidence).slice(0, 4).map((item) => (
                    <span className="border border-line/60 bg-void/50 px-2 py-1 text-xs text-slate-400" key={item}>
                      {item}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </section>

          <section className="mt-4 grid gap-4 xl:grid-cols-3">
            <ChartBlock title="Forecast Charts">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={forecastData}>
                  <CartesianGrid stroke="#233047" strokeDasharray="3 3" />
                  <XAxis dataKey="metric" stroke="#64748b" fontSize={10} />
                  <YAxis stroke="#64748b" fontSize={11} />
                  <Tooltip contentStyle={{ background: "#0b1220", border: "1px solid #1f2a44", color: "#e2e8f0" }} />
                  <Line dataKey="baseline" stroke="#64748b" strokeWidth={2} dot={false} />
                  <Line dataKey="projected" stroke="#7CF0A6" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </ChartBlock>

            <ChartBlock title="Risk Heatmaps">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={riskData}>
                  <CartesianGrid stroke="#233047" strokeDasharray="3 3" />
                  <XAxis dataKey="domain" stroke="#64748b" fontSize={10} />
                  <YAxis stroke="#64748b" fontSize={11} />
                  <Tooltip contentStyle={{ background: "#0b1220", border: "1px solid #1f2a44", color: "#e2e8f0" }} />
                  <Bar dataKey="risk">
                    {riskData.map((item) => (
                      <Cell fill={riskColor[item.level]} key={item.domain} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </ChartBlock>

            <ChartBlock title="Scenario Comparison">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={comparisonData}>
                  <CartesianGrid stroke="#233047" strokeDasharray="3 3" />
                  <XAxis dataKey="label" stroke="#64748b" fontSize={10} />
                  <YAxis stroke="#64748b" fontSize={11} />
                  <Tooltip contentStyle={{ background: "#0b1220", border: "1px solid #1f2a44", color: "#e2e8f0" }} />
                  <Bar dataKey="score">
                    {comparisonData.map((item) => (
                      <Cell fill={riskColor[item.level]} key={item.label} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </ChartBlock>
          </section>

          <section className="mt-4 grid gap-4 xl:grid-cols-3">
            <ListBlock title="Recommendation Panel" items={active.recommendations.map((item) => `${item.title}: ${item.action}`)} />
            <ListBlock title="Workforce Impact" items={[...active.resourceAdjustments, ...active.staffingChanges]} />
            <ListBlock title="Financial Impact" items={[`Financial impact ${formatMoney(active.impact.financialImpact)}`, `Revenue impact ${formatMoney(active.impact.revenueImpact)}`, ...lab.executiveRecommendations.map((item) => item.expectedBenefit)]} />
          </section>
        </>
      ) : null}
    </article>
  );
}

function Metric({
  icon: Icon,
  label,
  value,
  detail,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <div className="border border-line/70 bg-void/40 p-3">
      <div className="flex items-center gap-2 text-xs uppercase text-slate-500">
        <Icon className="size-4 text-cyan" />
        <span>{label}</span>
      </div>
      <strong className="mt-2 block break-words text-xl font-semibold text-white">{value}</strong>
      <span className="mt-1 block text-xs text-slate-500">{detail}</span>
    </div>
  );
}

function ImpactLine({ label, value, invert = false }: { label: string; value: number; invert?: boolean }) {
  const positive = invert ? value <= 0 : value >= 0;
  return (
    <div>
      <div className="flex items-center justify-between gap-3 text-sm">
        <span className="text-white">{label}</span>
        <span className={positive ? "text-mint" : "text-signal"}>{signed(value)}%</span>
      </div>
      <div className="mt-2 h-2 bg-void">
        <div className={positive ? "h-2 bg-mint" : "h-2 bg-signal"} style={{ width: `${Math.min(100, Math.max(6, Math.abs(value) * 3))}%` }} />
      </div>
    </div>
  );
}

function ChartBlock({ children, title }: { children: React.ReactNode; title: string }) {
  return (
    <div className="h-72 border border-line/70 bg-void/35 p-4">
      <span className="mb-3 block text-xs uppercase text-slate-500">{title}</span>
      <div className="h-56">{children}</div>
    </div>
  );
}

function ListBlock({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="border border-line/70 bg-void/35 p-4">
      <span className="text-xs uppercase text-cyan">{title}</span>
      <div className="mt-3 grid gap-2">
        {items.slice(0, 5).map((item) => (
          <p className="border border-line/60 bg-panel/55 px-3 py-2 text-sm leading-6 text-slate-300" key={item}>
            {item}
          </p>
        ))}
      </div>
    </div>
  );
}

async function fetchJson(path: string, init?: RequestInit, timeoutMs = 45000): Promise<unknown> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(path, { ...init, signal: controller.signal });
    if (!response.ok) throw new Error(`Request failed: ${response.status}`);
    return await response.json();
  } finally {
    window.clearTimeout(timeout);
  }
}

function isLabResponse(value: unknown): value is CompanySimulationLabResponse {
  return Boolean(value && typeof value === "object" && "summary" in value && "scenarios" in value && Array.isArray((value as CompanySimulationLabResponse).scenarios));
}

function isAssistantResponse(value: unknown): value is CompanySimulationAssistantResponse {
  return Boolean(value && typeof value === "object" && "answer" in value && "confidence" in value);
}

function dollarsToMillions(value: number) {
  return Number((value / 1_000_000).toFixed(2));
}

function formatMoney(value: number) {
  const sign = value < 0 ? "-" : "";
  const absolute = Math.abs(value);
  if (absolute >= 1_000_000) return `${sign}$${(absolute / 1_000_000).toFixed(1)}M`;
  if (absolute >= 1_000) return `${sign}$${Math.round(absolute / 1_000)}K`;
  return `${sign}$${Math.round(absolute)}`;
}

function signed(value: number) {
  return `${value >= 0 ? "+" : ""}${value.toFixed(1)}`;
}

function signedInt(value: number) {
  return `${value >= 0 ? "+" : ""}${Math.round(value)}`;
}

function riskTextColor(level: CompanySimulationRiskLevel) {
  if (level === "critical") return "text-pink-300";
  if (level === "high") return "text-signal";
  if (level === "medium") return "text-amber-300";
  return "text-mint";
}

function riskBarColor(level: CompanySimulationRiskLevel) {
  if (level === "critical") return "h-2 bg-pink-400 transition-all duration-700";
  if (level === "high") return "h-2 bg-signal transition-all duration-700";
  if (level === "medium") return "h-2 bg-amber-300 transition-all duration-700";
  return "h-2 bg-mint transition-all duration-700";
}

function shortMetric(value: string) {
  return value.replace(" Forecast", "").replace("Productivity", "Prod").replace("Attrition", "Attr").replace("Delivery", "Delay");
}

function scenarioShort(value: CompanySimulationScenarioType) {
  return value
    .replace("work_from_home_policy", "WFH")
    .replace("employee_resignation", "Resign")
    .replace("department_restructure", "Restructure")
    .replace("budget_reduction", "Budget")
    .replace("meeting_reduction", "Meetings")
    .replace("hiring_freeze", "Freeze")
    .replace("hiring_growth", "Hire")
    .replace("revenue_change", "Revenue")
    .replace("client_loss", "Client")
    .replace("market_expansion", "Expand");
}
