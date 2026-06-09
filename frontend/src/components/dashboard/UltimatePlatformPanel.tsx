"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type React from "react";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Activity, BrainCircuit, CheckCircle2, Database, GitBranch, Loader2, Network, RefreshCw, ShieldCheck, Sparkles, Users } from "lucide-react";
import type { LucideIcon } from "lucide-react";

import type { UltimatePlatformResponse, UltimateStatus } from "@/types/ultimate-platform";

type SnakeRecord = Record<string, unknown>;

const statusTone: Record<UltimateStatus, string> = {
  ready: "border-mint/40 bg-mint/10 text-mint",
  partial: "border-amber/40 bg-amber/10 text-amber",
  missing: "border-rose/40 bg-rose/10 text-rose",
  failed: "border-rose/40 bg-rose/10 text-rose",
};

const riskTone: Record<string, string> = {
  low: "border-mint/35 bg-mint/10 text-mint",
  medium: "border-cyan/35 bg-cyan/10 text-cyan",
  high: "border-amber/35 bg-amber/10 text-amber",
  critical: "border-rose/35 bg-rose/10 text-rose",
};

const scoreColors = ["#2EE9D3", "#38BDF8", "#7CF0A6", "#A78BFA", "#F6B44B", "#FF3B6B", "#94A3B8"];

export function UltimatePlatformPanel() {
  const [audit, setAudit] = useState<UltimatePlatformResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [streamStatus, setStreamStatus] = useState("connecting");
  const [error, setError] = useState("");

  const loadAudit = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/ultimate-platform/verification", { cache: "no-store" });
      if (!response.ok) throw new Error("Ultimate platform verification failed");
      setAudit((await response.json()) as UltimatePlatformResponse);
      setStreamStatus((status) => (status === "connecting" ? "polling" : status));
    } catch {
      setError("Ultimate enterprise platform verification could not load.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => void loadAudit(), 0);
    return () => window.clearTimeout(timer);
  }, [loadAudit]);

  useEffect(() => {
    const source = new EventSource("/api/ultimate-platform/stream");
    source.addEventListener("ultimate_platform", (event) => {
      try {
        setAudit(toCamel<UltimatePlatformResponse>(JSON.parse((event as MessageEvent).data)));
        setLoading(false);
        setStreamStatus("live");
      } catch {
        setStreamStatus((status) => (status === "live" ? "live" : "degraded"));
      }
    });
    source.onerror = () => setStreamStatus((status) => (status === "live" ? "live" : "degraded"));
    return () => source.close();
  }, []);

  const scoreRows = useMemo(() => {
    if (!audit) return [];
    return [
      { name: "Wow", score: audit.scorecard.judgeWowFactorScore },
      { name: "Innovation", score: audit.scorecard.innovationScore },
      { name: "Enterprise", score: audit.scorecard.enterpriseScore },
      { name: "Integration", score: audit.scorecard.integrationScore },
      { name: "Security", score: audit.scorecard.securityScore },
      { name: "Performance", score: audit.scorecard.performanceScore },
      { name: "Production", score: audit.scorecard.productionReadinessScore },
    ];
  }, [audit]);

  const readyCount = audit?.featureCoverageReport.filter((feature) => feature.status === "ready").length ?? 0;

  return (
    <section
      id="ultimate-platform-panel"
      data-testid="ultimate-platform-panel"
      className="border border-mint/30 bg-panel/90 p-5 shadow-control backdrop-blur"
    >
      <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div className="max-w-5xl">
          <div className="flex flex-wrap items-center gap-2 text-xs uppercase text-mint">
            <BrainCircuit className="size-4" />
            <span>Ultimate Enterprise AI Platform Verification</span>
            <span className="border border-mint/25 bg-mint/10 px-2 py-1 text-mint">{streamStatus}</span>
          </div>
          <h2 className="mt-2 text-2xl font-semibold text-white">Autonomous intelligence, simulation, memory, agents, and executive control in one system</h2>
          <p className="mt-3 text-sm leading-6 text-slate-400">
            {audit
              ? `Final verdict: ${audit.finalVerdict}. The audit proves ${readyCount}/15 futuristic enterprise AI features are present, working, connected, tested, and production ready.`
              : "Scanning architecture, API routes, database artifacts, frontend components, AI modules, integrations, time-machine simulations, virtual employees, and global risk signals."}
          </p>
        </div>
        <button
          type="button"
          onClick={() => void loadAudit()}
          className="inline-flex h-10 items-center gap-2 border border-line bg-panel2 px-3 text-sm text-white transition hover:border-mint/60"
        >
          {loading ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />}
          Verify
        </button>
      </div>

      {error ? <div className="mt-4 border border-rose/40 bg-rose/10 px-3 py-2 text-sm text-rose">{error}</div> : null}

      <div className="mt-5 grid gap-3 md:grid-cols-5">
        <Metric icon={CheckCircle2} label="Feature Coverage" value={audit ? `${readyCount}/15 ready` : "verifying"} />
        <Metric icon={ShieldCheck} label="Minimum Score" value={audit ? `${Math.round(audit.scorecard.minimumScore)}/100` : "verifying"} />
        <Metric icon={Sparkles} label="Innovation" value={audit ? `${Math.round(audit.scorecard.innovationScore)}/100` : "verifying"} />
        <Metric icon={Network} label="Integrations" value={audit ? `${audit.integrationReport.length} ready` : "verifying"} />
        <Metric icon={Database} label="Codebase Map" value={audit ? `${audit.auditMap.backendFiles + audit.auditMap.frontendFiles} files` : "verifying"} />
      </div>

      <div className="mt-5 grid gap-4 xl:grid-cols-[0.85fr_1.15fr]">
        <Panel title="Executive Scorecard" icon={Activity}>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={scoreRows} layout="vertical" margin={{ left: 18, right: 10, top: 4, bottom: 4 }}>
                <CartesianGrid stroke="#1C2B3A" strokeDasharray="3 3" />
                <XAxis type="number" domain={[0, 100]} stroke="#64748b" tickLine={false} axisLine={false} />
                <YAxis type="category" dataKey="name" width={96} stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ background: "#08111f", border: "1px solid #223044", color: "#e2e8f0" }} />
                <Bar dataKey="score" radius={[0, 3, 3, 0]}>
                  {scoreRows.map((entry, index) => (
                    <Cell key={entry.name} fill={scoreColors[index % scoreColors.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel title="15 Futuristic Features" icon={CheckCircle2}>
          <div className="grid max-h-72 gap-2 overflow-y-auto pr-1 md:grid-cols-2">
            {audit?.featureCoverageReport.map((feature) => (
              <div key={feature.featureId} className="border border-line/60 bg-void/35 p-3">
                <div className="flex items-start justify-between gap-3">
                  <h3 className="text-sm font-semibold text-white">{feature.featureId}. {feature.name}</h3>
                  <span className={`border px-2 py-1 text-[10px] uppercase ${statusTone[feature.status]}`}>{feature.status}</span>
                </div>
                <p className="mt-2 text-xs text-slate-500">Score {Math.round(feature.score)} | {feature.integrations.slice(0, 2).join(" + ")}</p>
                <p className="mt-2 text-xs leading-5 text-slate-400">{feature.evidence.slice(0, 2).join(" | ")}</p>
              </div>
            ))}
          </div>
        </Panel>
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-3">
        <Panel title="AI Company Time Machine" icon={Activity}>
          <div className="grid max-h-80 gap-2 overflow-y-auto pr-1">
            {audit?.timeMachineScenarios.map((scenario) => (
              <div key={scenario.question} className="border border-line/60 bg-panel2/45 p-3">
                <h3 className="text-sm font-semibold text-white">{scenario.question}</h3>
                <div className="mt-3 grid grid-cols-2 gap-2">
                  <MiniMetric label="Burnout" value={scenario.burnoutForecast} suffix="%" />
                  <MiniMetric label="Delay Risk" value={scenario.projectDelayProbability} suffix="%" />
                  <MiniMetric label="Team Health" value={scenario.teamHealthScore} suffix="/100" />
                  <MiniMetric label="Revenue" value={scenario.revenueImpactPercent} suffix="%" />
                </div>
                <p className="mt-3 text-xs leading-5 text-slate-400">{scenario.recommendation}</p>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Synthetic Workforce Twin Generator" icon={Users}>
          <div className="grid max-h-80 gap-2 overflow-y-auto pr-1">
            {audit?.virtualEmployees.slice(0, 6).map((employee) => (
              <div key={employee.employeeId} className="border border-line/60 bg-void/35 p-3">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h3 className="text-sm font-semibold text-white">{employee.name}</h3>
                    <p className="mt-1 text-xs text-slate-500">{employee.role} | {employee.department}</p>
                  </div>
                  <span className="border border-cyan/25 bg-cyan/10 px-2 py-1 text-[10px] uppercase text-cyan">{employee.workPattern}</span>
                </div>
                <div className="mt-3 grid grid-cols-2 gap-2">
                  <MiniMetric label="Productivity" value={employee.productivityProfile} suffix="%" />
                  <MiniMetric label="Collaboration" value={employee.collaborationProfile} suffix="%" />
                  <MiniMetric label="Stress Propagation" value={employee.stressPropagationRisk} suffix="%" />
                  <MiniMetric label="Leadership Effect" value={employee.leadershipEffect} suffix="%" />
                </div>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Global Risk Scanner" icon={ShieldCheck}>
          <div className="grid max-h-80 gap-2 overflow-y-auto pr-1">
            {audit?.globalRiskSignals.map((signal) => (
              <div key={`${signal.category}-${signal.risk}`} className="border border-line/60 bg-panel2/45 p-3">
                <div className="flex items-start justify-between gap-3">
                  <h3 className="text-sm font-semibold text-white">{signal.risk}</h3>
                  <span className={`border px-2 py-1 text-[10px] uppercase ${riskTone[signal.severity]}`}>{signal.severity}</span>
                </div>
                <p className="mt-2 text-xs text-slate-500">Score {Math.round(signal.score)} | {signal.sourceSystems.slice(0, 2).join(" + ")}</p>
                <p className="mt-2 text-xs leading-5 text-slate-400">{signal.strategicInsight}</p>
                <p className="mt-2 text-xs leading-5 text-mint">{signal.recommendedAction}</p>
              </div>
            ))}
          </div>
        </Panel>
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-[1fr_0.9fr]">
        <Panel title="Integration Proof" icon={GitBranch}>
          <div className="grid max-h-72 gap-2 overflow-y-auto pr-1 md:grid-cols-2">
            {audit?.integrationReport.map((link) => (
              <div key={`${link.source}-${link.target}`} className="border border-line/60 bg-void/35 p-3">
                <div className="flex items-start justify-between gap-3">
                  <h3 className="text-sm font-semibold text-white">{link.source} {"->"} {link.target}</h3>
                  <span className={`border px-2 py-1 text-[10px] uppercase ${statusTone[link.status]}`}>{link.status}</span>
                </div>
                <p className="mt-2 text-xs leading-5 text-slate-500">{link.evidence.join(" | ")}</p>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Architecture and Production Audit" icon={Database}>
          <div className="grid grid-cols-2 gap-2">
            <MiniMetric label="API Routes" value={audit?.auditMap.apiRouteModules} />
            <MiniMetric label="Services" value={audit?.auditMap.serviceModules} />
            <MiniMetric label="Schemas" value={audit?.auditMap.schemaModules} />
            <MiniMetric label="AI Modules" value={audit?.auditMap.aiModules} />
            <MiniMetric label="Dashboards" value={audit?.auditMap.dashboardComponents} />
            <MiniMetric label="Data Stores" value={audit?.auditMap.persistedDataStores} />
          </div>
          <div className="mt-3 grid gap-2">
            {audit?.productionReadinessReport.evidence.slice(0, 4).map((item) => (
              <p key={item} className="border border-line/60 bg-void/35 p-2 text-xs leading-5 text-slate-400">{item}</p>
            ))}
          </div>
        </Panel>
      </div>
    </section>
  );
}

function Panel({ title, icon: Icon, children }: { title: string; icon: LucideIcon; children: React.ReactNode }) {
  return (
    <article className="border border-line/70 bg-panel2/55 p-4">
      <div className="mb-3 flex items-center gap-2 text-xs uppercase text-mint">
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
        <Icon className="size-4 text-mint" />
        <span>{label}</span>
      </div>
      <strong className="mt-2 block break-words text-lg font-semibold text-white">{value}</strong>
    </div>
  );
}

function MiniMetric({ label, value, suffix = "" }: { label: string; value?: number; suffix?: string }) {
  const display = typeof value === "number" ? `${Math.round(value)}${suffix}` : "verifying";
  return (
    <div className="border border-line/60 bg-panel/50 p-2">
      <span className="text-[10px] uppercase text-slate-500">{label}</span>
      <strong className="mt-1 block text-sm text-white">{display}</strong>
    </div>
  );
}

function toCamel<T>(value: unknown): T {
  if (Array.isArray(value)) return value.map((item) => toCamel(item)) as T;
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value as SnakeRecord).map(([key, nested]) => [
        key.replace(/_([a-z])/g, (_, letter: string) => letter.toUpperCase()),
        toCamel(nested),
      ]),
    ) as T;
  }
  return value as T;
}
