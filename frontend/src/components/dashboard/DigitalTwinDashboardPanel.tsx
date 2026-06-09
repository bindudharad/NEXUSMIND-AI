"use client";

import { Activity, BrainCircuit, GitBranch, Loader2, Network, RadioTower, Users } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import type { DigitalTwinSnapshotResponse } from "@/types/intelligence";

export function DigitalTwinDashboardPanel() {
  const [snapshot, setSnapshot] = useState<DigitalTwinSnapshotResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const response = await fetch("/api/intelligence/digital-twin/company", { cache: "no-store" });
        if (!response.ok) throw new Error("snapshot failed");
        const data = (await response.json()) as DigitalTwinSnapshotResponse;
        if (active) setSnapshot(data);
      } catch {
        if (active) setError("Digital Twin snapshot is unavailable.");
      } finally {
        if (active) setLoading(false);
      }
    }
    void load();
    const interval = window.setInterval(() => void load(), 15000);
    return () => {
      active = false;
      window.clearInterval(interval);
    };
  }, []);

  const highRiskEmployee = useMemo(
    () => snapshot?.employees.slice().sort((a, b) => b.attritionProbability - a.attritionProbability)[0],
    [snapshot],
  );
  const riskiestProject = useMemo(() => snapshot?.projects.slice().sort((a, b) => b.risk - a.risk)[0], [snapshot]);

  return (
    <section className="border border-cyan/25 bg-panel/85 p-5 shadow-control backdrop-blur">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <BrainCircuit className="mt-1 size-5 text-cyan" />
          <div>
            <p className="text-xs uppercase text-cyan">Company Digital Twin</p>
            <h2 className="mt-1 text-xl font-semibold text-white">Virtual company model and scenario graph</h2>
          </div>
        </div>
        {loading ? <Loader2 className="size-5 animate-spin text-cyan" /> : null}
      </div>

      <div className="mt-4 flex flex-wrap gap-2 text-xs uppercase text-slate-400">
        {["Company Graph", "Employee Graph", "Team Graph", "Department Graph", "Project Graph", "Risk Heatmaps", "Forecast Charts", "Scenario Results"].map((item) => (
          <span key={item} className="border border-line/70 bg-void/40 px-2 py-1">
            {item}
          </span>
        ))}
      </div>

      {error ? <p className="mt-4 text-sm text-signal">{error}</p> : null}

      {snapshot ? (
        <>
          <div className="mt-5 grid gap-3 md:grid-cols-4">
            <TwinMetric icon={Users} label="Employee twins" value={snapshot.employees.length} detail={highRiskEmployee?.name ?? "none"} />
            <TwinMetric icon={Network} label="Team twins" value={snapshot.teams.length} detail={`${snapshot.departments.length} departments`} />
            <TwinMetric icon={GitBranch} label="Project twins" value={snapshot.projects.length} detail={riskiestProject?.name ?? "none"} />
            <TwinMetric icon={RadioTower} label="Operations" value={snapshot.operations.length} detail={`${snapshot.graphEdges.length} graph edges`} />
          </div>

          <div className="mt-5 grid gap-4 xl:grid-cols-[1.05fr_0.95fr]">
            <div className="border border-line/70 bg-panel2/60 p-4">
              <div className="flex items-center gap-2 text-xs uppercase text-cyan">
                <GitBranch className="size-4" />
                <span>Risk propagation graph</span>
              </div>
              <div className="mt-4 grid gap-2">
                {snapshot.graphEdges.slice(0, 7).map((edge) => (
                  <div key={`${edge.source}-${edge.target}`} className="grid gap-2 border border-line/60 bg-void/45 p-3 sm:grid-cols-[1fr_auto]">
                    <div>
                      <p className="text-sm text-white">
                        {edge.source} {"->"} {edge.target}
                      </p>
                      <p className="mt-1 text-xs text-slate-500">{edge.relationship}</p>
                    </div>
                    <RiskBadge value={edge.riskTransfer} />
                  </div>
                ))}
              </div>
            </div>

            <div className="grid gap-4">
              <TwinScenario title="Baseline forecast" delay={snapshot.baseline.delayProbability} collapse={snapshot.baseline.teamCollapseProbability} stability={snapshot.baseline.stabilityScore} revenue={snapshot.baseline.revenueImpactPercent} />
              <TwinScenario title="Stress simulation" delay={snapshot.stressCase.delayProbability} collapse={snapshot.stressCase.teamCollapseProbability} stability={snapshot.stressCase.stabilityScore} revenue={snapshot.stressCase.revenueImpactPercent} />
              <div className="border border-line/70 bg-panel2/60 p-4">
                <div className="flex items-center gap-2 text-xs uppercase text-mint">
                  <Activity className="size-4" />
                  <span>Forecast models</span>
                </div>
                <div className="mt-3 flex flex-wrap gap-2">
                  {snapshot.forecastModels.map((model) => (
                    <span key={model} className="border border-line/70 bg-void/50 px-2 py-1 text-xs text-slate-300">
                      {model}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <div className="mt-5 grid gap-4 lg:grid-cols-3">
            <TwinList
              title="Employee heatmap"
              items={snapshot.employees.map((employee) => ({
                name: employee.name,
                value: employee.attritionProbability,
                detail: `${employee.experienceYears}y exp, wellness ${employee.wellnessScore}%, ${employee.skills.slice(0, 2).join(", ")}`,
              }))}
            />
            <TwinList title="Team health" items={snapshot.teams.map((team) => ({ name: team.name, value: team.risk, detail: `${team.productivity}% productivity` }))} />
            <TwinList title="Project forecasts" items={snapshot.projects.map((project) => ({ name: project.name, value: project.delayPrediction, detail: `${project.timelineForecastDays}d forecast` }))} />
          </div>

          <div className="mt-5 grid gap-4 lg:grid-cols-2">
            <TwinList
              title="Department graph"
              items={snapshot.departments.map((department) => ({
                name: department.name,
                value: department.risk,
                detail: `${department.productivity}% productivity, ${department.cost}% cost, ${department.hiringNeed}% hiring need`,
              }))}
            />
            <TwinList
              title="Resource load"
              items={snapshot.resources.map((resource) => ({
                name: resource.name,
                value: resource.risk,
                detail: `${resource.utilization}% utilization, ${resource.capacity}% capacity`,
              }))}
            />
          </div>
        </>
      ) : null}
    </section>
  );
}

function TwinMetric({ icon: Icon, label, value, detail }: { icon: typeof Users; label: string; value: number; detail: string }) {
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

function TwinScenario({ title, delay, collapse, stability, revenue }: { title: string; delay: number; collapse: number; stability: number; revenue: number }) {
  return (
    <div className="border border-line/70 bg-panel2/60 p-4">
      <p className="text-xs uppercase text-cyan">{title}</p>
      <div className="mt-3 grid grid-cols-4 gap-2">
        <MiniMetric label="Delay" value={`${delay}%`} />
        <MiniMetric label="Collapse" value={`${collapse}%`} />
        <MiniMetric label="Stability" value={`${stability}%`} />
        <MiniMetric label="Revenue" value={`${revenue}%`} />
      </div>
    </div>
  );
}

function TwinList({ title, items }: { title: string; items: Array<{ name: string; value: number; detail: string }> }) {
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
            <p className="mt-1 text-xs text-slate-500">{item.detail}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function MiniMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-line/60 bg-void/45 p-2">
      <span className="block text-xs uppercase text-slate-500">{label}</span>
      <strong className="mt-1 block text-sm text-white">{value}</strong>
    </div>
  );
}

function RiskBadge({ value }: { value: number }) {
  return <span className={`self-center border px-2 py-1 text-xs ${value >= 70 ? "border-signal/50 text-signal" : value >= 50 ? "border-amber/50 text-amber" : "border-mint/50 text-mint"}`}>{value}% transfer</span>;
}

function barColor(value: number) {
  const color = value >= 70 ? "bg-signal" : value >= 50 ? "bg-amber" : "bg-mint";
  return `h-2 ${color}`;
}
