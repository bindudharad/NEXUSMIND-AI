"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type React from "react";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import {
  BrainCircuit,
  CheckCircle2,
  Database,
  GitBranch,
  Loader2,
  Network,
  Orbit,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  Users,
  Workflow,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import type { UniverseStatus, VirtualEnterpriseUniverseResponse } from "@/types/virtual-enterprise-universe";

const statusTone: Record<UniverseStatus, string> = {
  complete: "border-mint/40 bg-mint/10 text-mint",
  working: "border-cyan/40 bg-cyan/10 text-cyan",
  partial: "border-amber/40 bg-amber/10 text-amber",
  missing: "border-rose/40 bg-rose/10 text-rose",
};

const scoreColors = ["#2EE9D3", "#7CF0A6", "#38BDF8", "#A78BFA", "#F6B44B", "#FF3B6B"];

export function VirtualEnterpriseUniversePanel() {
  const [audit, setAudit] = useState<VirtualEnterpriseUniverseResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [streamStatus, setStreamStatus] = useState("connecting");
  const [error, setError] = useState("");

  const loadAudit = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/virtual-enterprise-universe/verification", { cache: "no-store" });
      if (!response.ok) throw new Error("Virtual Enterprise Universe verification failed");
      setAudit((await response.json()) as VirtualEnterpriseUniverseResponse);
      setStreamStatus((status) => (status === "connecting" ? "polling" : status));
    } catch {
      setError("Virtual Enterprise Universe audit could not load.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => void loadAudit(), 0);
    return () => window.clearTimeout(timer);
  }, [loadAudit]);

  useEffect(() => {
    const source = new EventSource("/api/virtual-enterprise-universe/stream");
    source.addEventListener("virtual_enterprise_universe", (event) => {
      try {
        setAudit(JSON.parse((event as MessageEvent).data) as VirtualEnterpriseUniverseResponse);
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
      { name: "Architecture", score: audit.scorecard.architectureScore },
      { name: "AI Innovation", score: audit.scorecard.aiInnovationScore },
      { name: "Digital Twin", score: audit.scorecard.digitalTwinScore },
      { name: "Multi-Agent", score: audit.scorecard.multiAgentScore },
      { name: "Simulation", score: audit.scorecard.simulationScore },
      { name: "Knowledge", score: audit.scorecard.knowledgeBrainScore },
      { name: "Executive", score: audit.scorecard.executiveIntelligenceScore },
      { name: "Metaverse", score: audit.scorecard.metaverseScore },
      { name: "Security", score: audit.scorecard.securityScore },
      { name: "Competition", score: audit.scorecard.competitionReadinessScore },
    ];
  }, [audit]);

  return (
    <section
      id="virtual-enterprise-universe-panel"
      data-testid="virtual-enterprise-universe-panel"
      className="w-full max-w-[calc(100vw-2rem)] overflow-hidden border border-cyan/30 bg-panel/90 p-5 shadow-control backdrop-blur lg:max-w-full"
    >
      <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div className="min-w-0 max-w-[calc(100vw-4rem)] xl:max-w-5xl">
          <div className="flex flex-wrap items-center gap-2 text-xs uppercase text-cyan">
            <Orbit className="size-4" />
            <span>Virtual Enterprise Universe</span>
            <span className="border border-cyan/25 bg-cyan/10 px-2 py-1 text-cyan">{streamStatus}</span>
            <span className="border border-mint/25 bg-mint/10 px-2 py-1 text-mint">{audit?.finalVerdict ?? "verifying"}</span>
          </div>
          <h2 className="mt-2 break-words text-2xl font-semibold text-white">AI-powered virtual company ecosystem for competition readiness</h2>
          <p className="mt-3 break-words text-sm leading-6 text-slate-400">
            {audit?.executiveSummary ??
              "Auditing whether NEXUSMIND AI operates as one connected virtual enterprise universe across executive intelligence, twins, agents, simulations, memory, risk, workforce, and metaverse systems."}
          </p>
        </div>
        <button type="button" onClick={() => void loadAudit()} className="inline-flex h-10 items-center justify-center gap-2 border border-line bg-panel2 px-3 text-sm text-white transition hover:border-cyan/60">
          {loading ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />}
          Verify
        </button>
      </div>

      {error ? <div className="mt-4 border border-rose/40 bg-rose/10 px-3 py-2 text-sm text-rose">{error}</div> : null}

      <div className="mt-5 grid gap-3 md:grid-cols-3 xl:grid-cols-6">
        <Metric icon={ShieldCheck} label="Production" value={audit ? `${Math.round(audit.productionReadinessScore)}/100` : "verifying"} />
        <Metric icon={Sparkles} label="Competition" value={audit ? `${Math.round(audit.competitionReadinessScore)}/100` : "verifying"} />
        <Metric icon={Orbit} label="Judge Wow" value={audit ? `${Math.round(audit.judgeWowFactorScore)}/100` : "verifying"} />
        <Metric icon={Workflow} label="Modules" value={audit ? `${audit.moduleAudit.length}/18` : "verifying"} />
        <Metric icon={GitBranch} label="Workflows" value={audit ? String(audit.connectivityWorkflows.length) : "verifying"} />
        <Metric icon={Users} label="Agents" value={audit ? String(audit.agentEcosystem.length) : "verifying"} />
      </div>

      <div className="mt-5 grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
        <Panel title="Competition Scorecard" icon={ShieldCheck}>
          <div className="h-80 min-w-0">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={scoreRows} layout="vertical" margin={{ left: 22, right: 8, top: 4, bottom: 4 }}>
                <CartesianGrid stroke="#1C2B3A" strokeDasharray="3 3" />
                <XAxis type="number" domain={[0, 100]} tick={{ fill: "#94a3b8", fontSize: 11 }} />
                <YAxis type="category" dataKey="name" width={104} tick={{ fill: "#94a3b8", fontSize: 11 }} />
                <Tooltip contentStyle={{ background: "#101827", border: "1px solid #22324a", color: "#fff" }} />
                <Bar dataKey="score" radius={[0, 3, 3, 0]}>
                  {scoreRows.map((entry, index) => (
                    <Cell key={entry.name} fill={scoreColors[index % scoreColors.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel title="Master Platform Audit" icon={BrainCircuit}>
          <div className="grid max-h-80 gap-2 overflow-y-auto pr-1 md:grid-cols-2">
            {audit?.moduleAudit.map((item) => (
              <div key={item.module} className="border border-line bg-void p-3">
                <div className="flex items-start justify-between gap-3">
                  <h3 className="break-words text-sm font-semibold text-white">{item.module}</h3>
                  <span className={`border px-2 py-1 text-[10px] uppercase ${statusTone[item.status]}`}>{item.status}</span>
                </div>
                <p className="mt-2 text-xs text-slate-500">{commandSurfaceLabel(item.dashboardSurface)}</p>
                <p className="mt-1 text-xs text-cyan">{Math.round(item.score)}/100</p>
              </div>
            )) ?? <Empty label="Loading modules." />}
          </div>
        </Panel>
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-3">
        <Panel title="System Connectivity" icon={GitBranch}>
          <List items={(audit?.connectivityWorkflows ?? []).map((item) => `${item.name}: ${item.chain.join(" -> ")}`)} />
        </Panel>
        <Panel title="Digital Twin Verification" icon={Database}>
          <List items={(audit?.digitalTwinAudit ?? []).map((item) => `${item.twin} twin: ${item.propagationExample}`)} />
        </Panel>
        <Panel title="Multi-Agent Ecosystem" icon={Users}>
          <List items={(audit?.agentEcosystem ?? []).map((item) => `${item.agent}: ${item.responsibilities.slice(0, 2).join(", ")}`)} />
        </Panel>
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-3">
        <Panel title="Knowledge and Organizational Brains" icon={Network}>
          <List items={[...(audit?.knowledgeBrainAudit ?? []), ...(audit?.organizationalBrainAudit ?? [])].map((item) => `${item.module}: ${item.sourceSystems.slice(0, 3).join(", ")}`)} />
        </Panel>
        <Panel title="Enterprise Simulation Audit" icon={Orbit}>
          <List items={(audit?.simulationAudit ?? []).map((item) => `${item.module}: ${commandSurfaceLabel(item.dashboardSurface)}`)} />
        </Panel>
        <Panel title="Metaverse and Command Surfaces" icon={Sparkles}>
          <List items={[...(audit?.metaverseAudit ?? []).map((item) => `${item.module}: ${item.status}`), ...(audit?.dashboardAudit ?? []).slice(0, 5).map((item) => `${commandSurfaceLabel(item.dashboard)}: realtime ${item.realtime ? "yes" : "no"}`)]} />
        </Panel>
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-2">
        <Panel title="Security Audit" icon={ShieldCheck}>
          <List items={(audit?.securityAudit ?? []).map((item) => `${item.control}: ${item.evidence}`)} />
        </Panel>
        <Panel title="Performance Audit" icon={CheckCircle2}>
          <List items={(audit?.performanceAudit ?? []).map((item) => `${item.area}: ${item.value}/${item.target} ${item.metric}`)} />
        </Panel>
      </div>

      <div className="mt-4 border border-mint/30 bg-mint/10 p-4 text-sm leading-6 text-mint">
        {audit?.finalEvaluation ?? "Final evaluation pending."}
      </div>
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
    <div className="min-w-0 border border-line bg-panel2/80 p-4">
      <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-white">
        <Icon className="size-4 text-cyan" />
        <span>{title}</span>
      </div>
      {children}
    </div>
  );
}

function List({ items }: { items: string[] }) {
  if (!items.length) return <Empty label="No records loaded yet." />;
  return (
    <div className="space-y-2">
      {items.slice(0, 7).map((item) => (
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

function commandSurfaceLabel(value: string) {
  return value.replaceAll("Dashboard", "Command Surface").replaceAll("dashboard", "command surface");
}
