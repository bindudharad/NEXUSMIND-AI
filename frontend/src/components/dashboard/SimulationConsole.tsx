"use client";

import { GitBranch, Loader2, TimerReset } from "lucide-react";
import { useState } from "react";

import type { SimulationResponse, SimulationScenario } from "@/types/intelligence";

export function SimulationConsole({ simulations }: { simulations: SimulationScenario[] }) {
  const [scenario, setScenario] = useState({
    resignation_count: 20,
    workload_delta_percent: 30,
    budget_delta_percent: 6,
    security_incident: true,
  });
  const [result, setResult] = useState<SimulationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function runSimulation() {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/intelligence/digital-twin/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(scenario),
      });
      if (!response.ok) throw new Error("simulation failed");
      setResult((await response.json()) as SimulationResponse);
    } catch {
      setError("Shadow Company simulation could not complete.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="border border-line/80 bg-panel/85 p-5 shadow-control backdrop-blur">
      <div className="flex items-center gap-3">
        <TimerReset className="size-5 text-cyan" />
        <div>
          <p className="text-xs uppercase text-cyan">Company Time Machine</p>
          <h2 className="text-xl font-semibold text-white">What-if simulation engine</h2>
        </div>
      </div>

      <div className="mt-5 grid gap-3 border border-cyan/20 bg-cyan/5 p-4">
        <Control
          label="Resignations"
          value={scenario.resignation_count}
          min={0}
          max={80}
          onChange={(value) => setScenario((current) => ({ ...current, resignation_count: value }))}
        />
        <Control
          label="Workload delta"
          value={scenario.workload_delta_percent}
          min={-20}
          max={80}
          suffix="%"
          onChange={(value) => setScenario((current) => ({ ...current, workload_delta_percent: value }))}
        />
        <Control
          label="Budget delta"
          value={scenario.budget_delta_percent}
          min={-30}
          max={80}
          suffix="%"
          onChange={(value) => setScenario((current) => ({ ...current, budget_delta_percent: value }))}
        />
        <label className="flex items-center justify-between gap-3 text-sm text-slate-300">
          <span>Security incident</span>
          <input
            type="checkbox"
            checked={scenario.security_incident}
            onChange={(event) => setScenario((current) => ({ ...current, security_incident: event.target.checked }))}
            className="size-4 accent-cyan"
          />
        </label>
        <button
          type="button"
          onClick={() => void runSimulation()}
          className="inline-flex items-center justify-center gap-2 border border-cyan/40 bg-cyan/10 px-3 py-2 text-sm text-cyan"
        >
          {loading ? <Loader2 className="size-4 animate-spin" /> : <TimerReset className="size-4" />}
          Run what-if simulation
        </button>
        {error ? <p className="text-xs text-signal">{error}</p> : null}
        {result ? (
          <div className="grid gap-2 sm:grid-cols-3">
            <Impact label="Collapse" value={`${result.teamCollapseProbability}%`} />
            <Impact label="Stability" value={`${result.stabilityScore}%`} />
            <Impact label="Productivity loss" value={`${result.productivityLossPercent}%`} />
            <Impact label="Monte Carlo success" value={`${result.monteCarlo.successProbability}%`} />
            <Impact label="P90 delay" value={`${result.monteCarlo.delayProbabilityP90}%`} />
            <Impact label="Worst revenue" value={`${result.monteCarlo.worstCaseRevenueImpactPercent}%`} />
            <div className="border border-line/70 bg-void/50 p-3 sm:col-span-3">
              <span className="block text-xs uppercase text-slate-500">Affected departments</span>
              <strong className="mt-1 block text-sm text-white">{result.affectedDepartments.join(", ")}</strong>
            </div>
            <div className="border border-line/70 bg-void/50 p-3 sm:col-span-3">
              <span className="block text-xs uppercase text-slate-500">Outcome distribution</span>
              <strong className="mt-1 block text-sm text-white">
                Stable {result.monteCarlo.riskDistribution.stable}% / Strained{" "}
                {result.monteCarlo.riskDistribution.strained}% / Crisis {result.monteCarlo.riskDistribution.crisis}%
              </strong>
            </div>
            <div className="border border-line/70 bg-void/50 p-3 sm:col-span-3">
              <span className="block text-xs uppercase text-slate-500">Risk propagation</span>
              <strong className="mt-1 block text-sm text-white">{result.riskPropagationPath.join(" -> ")}</strong>
            </div>
            <div className="grid gap-2 border border-line/70 bg-void/50 p-3 sm:col-span-3">
              <span className="block text-xs uppercase text-slate-500">Workflow impacts</span>
              {Object.entries(result.workflowImpacts).map(([workflow, impact]) => (
                <div key={workflow} className="grid grid-cols-[1fr_auto] items-center gap-3 text-xs">
                  <span className="truncate text-slate-300">{workflow}</span>
                  <strong className="text-white">{impact}%</strong>
                </div>
              ))}
            </div>
            <div className="border border-line/70 bg-void/50 p-3 sm:col-span-3">
              <span className="block text-xs uppercase text-slate-500">Forecast models</span>
              <strong className="mt-1 block text-sm text-white">{result.forecastModels.join(", ")}</strong>
            </div>
          </div>
        ) : null}
      </div>

      <div className="mt-5 grid gap-4">
        {simulations.map((simulation) => (
          <article key={simulation.id} className="border border-line/70 bg-panel2/65 p-4">
            <div className="flex items-start gap-3">
              <GitBranch className="mt-1 size-5 text-cyan" />
              <div>
                <h3 className="font-medium text-white">{simulation.scenario}</h3>
                <p className="mt-2 text-sm leading-6 text-slate-400">{simulation.recoveryPlan}</p>
              </div>
            </div>
            <div className="mt-4 grid grid-cols-3 gap-2">
              <Impact label="Revenue" value={simulation.revenueImpact} />
              <Impact label="Delay" value={`${simulation.delayProbability}%`} />
              <Impact label="Burnout" value={`${simulation.burnoutDelta > 0 ? "+" : ""}${simulation.burnoutDelta}`} />
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function Control({
  label,
  value,
  min,
  max,
  suffix = "",
  onChange,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  suffix?: string;
  onChange: (value: number) => void;
}) {
  return (
    <label className="grid gap-2 text-sm text-slate-300">
      <span className="flex justify-between">
        <span>{label}</span>
        <strong className="text-white">
          {value}
          {suffix}
        </strong>
      </span>
      <input
        type="range"
        value={value}
        min={min}
        max={max}
        onChange={(event) => onChange(Number(event.target.value))}
        className="accent-cyan"
      />
    </label>
  );
}

function Impact({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-line/70 bg-void/50 p-3">
      <span className="block text-xs uppercase text-slate-500">{label}</span>
      <strong className="mt-1 block text-xl text-white">{value}</strong>
    </div>
  );
}
