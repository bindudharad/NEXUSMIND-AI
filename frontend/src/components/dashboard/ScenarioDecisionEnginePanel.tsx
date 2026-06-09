"use client";

import {
  AlertTriangle,
  BarChart3,
  BrainCircuit,
  BriefcaseBusiness,
  CircleDollarSign,
  GitBranch,
  Loader2,
  Network,
  TrendingUp,
  Users,
} from "lucide-react";
import type React from "react";
import { useEffect, useMemo, useState } from "react";

import type { EnterpriseScenarioType, ScenarioDecisionSuiteResponse, ScenarioSimulationResponse } from "@/types/intelligence";

const scenarioConfigs: Array<{
  type: EnterpriseScenarioType;
  label: string;
  payload: Record<string, unknown>;
}> = [
  { type: "employee_resignation", label: "20 engineers resign", payload: { scenario_type: "employee_resignation", resignation_count: 20, seniority: "mixed" } },
  { type: "project_completion", label: "Project Alpha in 2 months", payload: { scenario_type: "project_completion", project_name: "Project Alpha Revenue Platform", deadline_months: 2 } },
  { type: "hiring_freeze", label: "Hiring freeze", payload: { scenario_type: "hiring_freeze", freeze_months: 6 } },
  { type: "team_restructure", label: "Team restructure", payload: { scenario_type: "team_restructure", source_team: "Platform Reliability", target_team: "Security Response" } },
  { type: "budget_cut", label: "20% budget cut", payload: { scenario_type: "budget_cut", budget_cut_percent: 20 } },
  { type: "productivity_change", label: "Meetings -50%", payload: { scenario_type: "productivity_change", workload_delta_percent: 25, meeting_reduction_percent: 50 } },
];

export function ScenarioDecisionEnginePanel() {
  const [suite, setSuite] = useState<ScenarioDecisionSuiteResponse | null>(null);
  const [selected, setSelected] = useState<ScenarioSimulationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState<EnterpriseScenarioType | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    async function loadSuite() {
      try {
        const response = await fetch("/api/intelligence/scenario/decision-suite", { cache: "no-store" });
        if (!response.ok) throw new Error("decision suite failed");
        const data = (await response.json()) as ScenarioDecisionSuiteResponse;
        if (active) {
          setSuite(data);
          setSelected((current) => current ?? data.scenarios[0] ?? null);
          setError("");
        }
      } catch {
        if (active) setError("Scenario decision engine is unavailable.");
      } finally {
        if (active) setLoading(false);
      }
    }
    void loadSuite();
    const interval = window.setInterval(() => void loadSuite(), 20000);
    return () => {
      active = false;
      window.clearInterval(interval);
    };
  }, []);

  const activeScenario = selected ?? suite?.scenarios[0] ?? null;
  const highestRisk = useMemo(
    () => suite?.scenarios.slice().sort((a, b) => b.failureProbability - a.failureProbability)[0] ?? activeScenario,
    [suite, activeScenario],
  );

  async function runScenario(config: (typeof scenarioConfigs)[number]) {
    setRunning(config.type);
    setError("");
    try {
      const response = await fetch("/api/intelligence/scenario/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config.payload),
        cache: "no-store",
      });
      if (!response.ok) throw new Error("simulation failed");
      setSelected((await response.json()) as ScenarioSimulationResponse);
    } catch {
      setError("Scenario simulation failed.");
    } finally {
      setRunning(null);
    }
  }

  return (
    <section className="border border-cyan/25 bg-panel/85 p-5 shadow-control backdrop-blur">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <BrainCircuit className="mt-1 size-5 text-cyan" />
          <div>
            <p className="text-xs uppercase text-cyan">Enterprise Scenario Simulation & Decision Engine</p>
            <h2 className="mt-1 text-xl font-semibold text-white">Executive what-if simulator and impact forecast</h2>
          </div>
        </div>
        <div className="flex items-center gap-2 text-xs uppercase text-slate-500">
          {loading ? <Loader2 className="size-4 animate-spin text-cyan" /> : null}
          <span>{suite ? `${suite.scenarios.length} scenarios` : "verifying"}</span>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-2 text-xs uppercase text-slate-400">
        {["Scenario Simulator", "Risk Heatmaps", "Prediction Charts", "Impact Analysis", "Resource Analysis", "Financial Impact", "Workforce Impact"].map((item) => (
          <span key={item} className="border border-line/70 bg-void/40 px-2 py-1">
            {item}
          </span>
        ))}
      </div>

      {error ? <p className="mt-4 text-sm text-signal">{error}</p> : null}

      <div className="mt-5 grid gap-2 md:grid-cols-3 xl:grid-cols-6">
        {scenarioConfigs.map((config) => (
          <button
            key={config.type}
            type="button"
            onClick={() => void runScenario(config)}
            disabled={running !== null}
            className={`min-h-16 border px-3 py-2 text-left text-xs uppercase transition ${
              activeScenario?.scenarioType === config.type ? "border-cyan bg-cyan/10 text-white" : "border-line/70 bg-void/45 text-slate-400 hover:border-cyan/60 hover:text-white"
            } disabled:cursor-wait disabled:opacity-70`}
          >
            <span>{config.label}</span>
            {running === config.type ? <Loader2 className="mt-2 size-4 animate-spin text-cyan" /> : null}
          </button>
        ))}
      </div>

      {activeScenario ? (
        <>
          <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-5">
            <ScenarioMetric icon={TrendingUp} label="Success" value={`${activeScenario.successProbability}%`} detail={activeScenario.riskLevel} />
            <ScenarioMetric icon={AlertTriangle} label="Delay risk" value={`${activeScenario.deliveryDelayProbability}%`} detail={`${activeScenario.failureProbability}% failure`} />
            <ScenarioMetric icon={Users} label="Engineers" value={String(activeScenario.requiredEngineers)} detail="required capacity" />
            <ScenarioMetric icon={CircleDollarSign} label="Budget" value={formatMoney(activeScenario.requiredBudget)} detail={`${activeScenario.revenueImpactPercent}% revenue`} />
            <ScenarioMetric icon={Network} label="Knowledge" value={`${activeScenario.knowledgeLossRisk}%`} detail={`${activeScenario.forecastHorizonDays}d horizon`} />
          </div>

          <div className="mt-5 grid gap-4 xl:grid-cols-[1.05fr_0.95fr]">
            <div className="border border-line/70 bg-panel2/60 p-4">
              <div className="flex items-center gap-2 text-xs uppercase text-cyan">
                <BarChart3 className="size-4" />
                <span>Impact Analysis</span>
              </div>
              <p className="mt-3 text-sm leading-6 text-slate-300">{activeScenario.scenarioSummary}</p>
              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                {activeScenario.impactVectors.map((vector) => (
                  <ImpactVector key={vector.domain} domain={vector.domain} value={vector.impactPercent} severity={vector.severity} />
                ))}
              </div>
            </div>

            <div className="border border-line/70 bg-panel2/60 p-4">
              <div className="flex items-center gap-2 text-xs uppercase text-mint">
                <GitBranch className="size-4" />
                <span>Decision trace</span>
              </div>
              <div className="mt-4 grid gap-2">
                {activeScenario.decisionTrace.map((item) => (
                  <p key={item} className="border border-line/60 bg-void/45 px-3 py-2 text-sm leading-6 text-slate-300">
                    {item}
                  </p>
                ))}
              </div>
            </div>
          </div>

          <div className="mt-5 grid gap-4 xl:grid-cols-3">
            <ScenarioList title="Risk Heatmaps" items={activeScenario.riskHeatmap.map((row) => ({ name: row.department, value: row.risk, detail: `${row.workload}% workload, ${row.hiringNeed}% hiring need` }))} />
            <ScenarioList title="Resource Analysis" items={activeScenario.bottlenecks.map((item, index) => ({ name: item, value: Math.max(22, activeScenario.deliveryDelayProbability - index * 9), detail: "bottleneck pressure" }))} />
            <ScenarioList title="Workforce Impact" items={activeScenario.hiringRequirements.map((item, index) => ({ name: item, value: Math.max(18, activeScenario.knowledgeLossRisk - index * 8), detail: "capacity requirement" }))} />
          </div>

          <div className="mt-5 grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
            <div className="border border-line/70 bg-panel2/60 p-4">
              <div className="flex items-center gap-2 text-xs uppercase text-cyan">
                <BriefcaseBusiness className="size-4" />
                <span>Executive recommendations</span>
              </div>
              <div className="mt-4 grid gap-2">
                {activeScenario.recommendations.slice(0, 4).map((item) => (
                  <p key={item} className="border border-line/60 bg-void/45 px-3 py-2 text-sm leading-6 text-slate-300">
                    {item}
                  </p>
                ))}
              </div>
            </div>

            <div className="border border-line/70 bg-panel2/60 p-4">
              <div className="flex items-center gap-2 text-xs uppercase text-mint">
                <BrainCircuit className="size-4" />
                <span>Prediction Charts</span>
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                {activeScenario.forecastModels.map((model) => (
                  <span key={model} className="border border-line/70 bg-void/50 px-2 py-1 text-xs text-slate-300">
                    {model}
                  </span>
                ))}
              </div>
              {suite ? (
                <p className="mt-4 text-sm leading-6 text-slate-400">
                  Decision readiness {suite.decisionReadinessScore}%. Highest current risk: {highestRisk?.scenarioSummary ?? "verifying"}.
                </p>
              ) : null}
            </div>
          </div>
        </>
      ) : null}
    </section>
  );
}

function ScenarioMetric({
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
    <div className="border border-line/70 bg-void/45 p-4">
      <div className="flex items-center gap-2 text-xs uppercase text-slate-500">
        <Icon className="size-4 text-cyan" />
        <span>{label}</span>
      </div>
      <strong className="mt-2 block text-2xl font-semibold text-white">{value}</strong>
      <span className="mt-1 block text-xs text-slate-500">{detail}</span>
    </div>
  );
}

function ImpactVector({ domain, value, severity }: { domain: string; value: number; severity: string }) {
  return (
    <div>
      <div className="flex items-center justify-between gap-3 text-sm">
        <span className="text-white">{domain}</span>
        <span className={severityColor(severity)}>{value}%</span>
      </div>
      <div className="mt-2 h-2 bg-void">
        <div className={barColor(value)} style={{ width: `${Math.min(100, Math.max(0, value))}%` }} />
      </div>
    </div>
  );
}

function ScenarioList({ title, items }: { title: string; items: Array<{ name: string; value: number; detail: string }> }) {
  return (
    <div className="border border-line/70 bg-panel2/60 p-4">
      <p className="text-xs uppercase text-cyan">{title}</p>
      <div className="mt-4 grid gap-3">
        {items.slice(0, 5).map((item) => (
          <div key={item.name}>
            <div className="flex items-center justify-between gap-3 text-sm">
              <span className="truncate text-white">{item.name}</span>
              <span className="text-slate-400">{item.value}%</span>
            </div>
            <div className="mt-2 h-2 bg-void">
              <div className={barColor(item.value)} style={{ width: `${Math.min(100, Math.max(0, item.value))}%` }} />
            </div>
            <p className="mt-1 text-xs leading-5 text-slate-500">{item.detail}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function formatMoney(value: number) {
  if (Math.abs(value) >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (Math.abs(value) >= 1_000) return `$${Math.round(value / 1_000)}K`;
  return `$${Math.round(value)}`;
}

function severityColor(severity: string) {
  if (severity === "critical") return "text-signal";
  if (severity === "high") return "text-amber";
  return "text-mint";
}

function barColor(value: number) {
  const color = value >= 65 ? "bg-signal" : value >= 35 ? "bg-amber" : "bg-mint";
  return `h-2 ${color}`;
}
