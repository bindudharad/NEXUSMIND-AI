"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type React from "react";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { BrainCircuit, CheckCircle2, Database, GitBranch, Loader2, Radio, RefreshCw, ShieldCheck, Workflow } from "lucide-react";
import type { LucideIcon } from "lucide-react";

import type { UnifiedEnterpriseResponse, UnifiedStatus } from "@/types/unified-enterprise";

type SnakeRecord = Record<string, unknown>;

const statusTone: Record<UnifiedStatus, string> = {
  connected: "border-mint/40 bg-mint/10 text-mint",
  partial: "border-amber/40 bg-amber/10 text-amber",
  disconnected: "border-rose/40 bg-rose/10 text-rose",
};

const scoreColors = ["#2EE9D3", "#7CF0A6", "#38BDF8", "#A78BFA", "#F6B44B", "#FF3B6B"];

export function UnifiedEnterpriseSystemPanel() {
  const [audit, setAudit] = useState<UnifiedEnterpriseResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [streamStatus, setStreamStatus] = useState("connecting");
  const [error, setError] = useState("");

  const loadAudit = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/unified-enterprise/verification", { cache: "no-store" });
      if (!response.ok) throw new Error("Unified enterprise verification failed");
      setAudit((await response.json()) as UnifiedEnterpriseResponse);
      setStreamStatus((status) => (status === "connecting" ? "polling" : status));
    } catch {
      setError("Unified enterprise operating-system verification could not load.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => void loadAudit(), 0);
    return () => window.clearTimeout(timer);
  }, [loadAudit]);

  useEffect(() => {
    const source = new EventSource("/api/unified-enterprise/stream");
    source.addEventListener("unified_enterprise_system", (event) => {
      try {
        setAudit(toCamel<UnifiedEnterpriseResponse>(JSON.parse((event as MessageEvent).data)));
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
      { name: "Unified", score: audit.scorecard.unifiedPlatformScore },
      { name: "Architecture", score: audit.scorecard.enterpriseArchitectureScore },
      { name: "Integration", score: audit.scorecard.integrationScore },
      { name: "Automation", score: audit.scorecard.automationScore },
      { name: "AI", score: audit.scorecard.aiIntelligenceScore },
      { name: "Production", score: audit.scorecard.productionReadinessScore },
    ];
  }, [audit]);

  return (
    <section
      id="unified-enterprise-system-panel"
      data-testid="unified-enterprise-system-panel"
      className="border border-cyan/30 bg-panel/90 p-5 shadow-control backdrop-blur"
    >
      <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div className="max-w-4xl">
          <div className="flex flex-wrap items-center gap-2 text-xs uppercase text-cyan">
            <BrainCircuit className="size-4" />
            <span>Unified Enterprise AI Operating System</span>
            <span className="border border-cyan/25 bg-cyan/10 px-2 py-1 text-cyan">{streamStatus}</span>
          </div>
          <h2 className="mt-2 text-2xl font-semibold text-white">Autonomous enterprise intelligence, not disconnected modules</h2>
          <p className="mt-3 text-sm leading-6 text-slate-400">
            {audit?.proofStatement ??
              "Verifying shared identity, shared enterprise data, cross-module workflows, autonomous actions, digital twin synchronization, agent collaboration, boardroom intelligence, and voice access."}
          </p>
        </div>
        <button
          type="button"
          onClick={() => void loadAudit()}
          className="inline-flex h-10 items-center gap-2 border border-line bg-panel2 px-3 text-sm text-white transition hover:border-cyan/60"
        >
          {loading ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />}
          Verify
        </button>
      </div>

      {error ? <div className="mt-4 border border-rose/40 bg-rose/10 px-3 py-2 text-sm text-rose">{error}</div> : null}

      <div className="mt-5 grid gap-3 md:grid-cols-5">
        <Metric icon={CheckCircle2} label="Final Verdict" value={audit?.finalVerdict ?? "verifying"} />
        <Metric icon={ShieldCheck} label="Minimum Score" value={audit ? `${Math.round(audit.scorecard.minimumScore)}/100` : "verifying"} />
        <Metric icon={Workflow} label="Modules" value={audit ? `${audit.modulesConnected.length}/${audit.moduleStatus.length}` : "verifying"} />
        <Metric icon={GitBranch} label="Workflows" value={audit ? String(audit.crossModuleWorkflows.length) : "verifying"} />
        <Metric icon={Database} label="Data Layer" value={audit ? `${audit.singleSourceOfTruth.length}/9` : "verifying"} />
      </div>

      <div className="mt-5 grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
        <Panel title="Unified Scorecard" icon={ShieldCheck}>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={scoreRows} layout="vertical" margin={{ left: 18, right: 10, top: 4, bottom: 4 }}>
                <CartesianGrid stroke="#1C2B3A" strokeDasharray="3 3" />
                <XAxis type="number" domain={[0, 100]} stroke="#64748b" tickLine={false} axisLine={false} />
                <YAxis type="category" dataKey="name" width={98} stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
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

        <Panel title="Modules Connected" icon={Workflow}>
          <div className="grid max-h-72 gap-2 overflow-y-auto pr-1 md:grid-cols-2">
            {audit?.moduleStatus.map((item) => (
              <div key={item.module} className="border border-line/60 bg-void/35 p-3">
                <div className="flex items-start justify-between gap-3">
                  <h3 className="text-sm font-semibold text-white">{item.module}</h3>
                  <span className={`border px-2 py-1 text-[10px] uppercase ${statusTone[item.status]}`}>{item.status}</span>
                </div>
                <p className="mt-2 text-xs leading-5 text-slate-500">
                  Boardroom {flag(item.boardroomVisible)} · Agent {flag(item.agentAccessible)} · Workflow {flag(item.workflowConnected)}
                </p>
              </div>
            ))}
          </div>
        </Panel>
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-3">
        <Panel title="Single Source of Truth" icon={Database}>
          <div className="grid max-h-72 gap-2 overflow-y-auto pr-1">
            {audit?.singleSourceOfTruth.map((item) => (
              <div key={item.entity} className="border border-line/60 bg-panel2/45 p-3">
                <div className="flex items-center justify-between gap-3">
                  <h3 className="text-sm font-semibold text-white">{item.entity}</h3>
                  <span className={`border px-2 py-1 text-[10px] uppercase ${statusTone[item.status]}`}>{item.status}</span>
                </div>
                <p className="mt-2 break-words text-xs text-slate-500">{item.sourceOfTruth}</p>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Cross-Module Workflows" icon={GitBranch}>
          <div className="grid max-h-72 gap-2 overflow-y-auto pr-1">
            {audit?.crossModuleWorkflows.map((workflow) => (
              <div key={workflow.name} className="border border-line/60 bg-void/35 p-3">
                <h3 className="text-sm font-semibold text-white">{workflow.name}</h3>
                <p className="mt-2 text-xs leading-5 text-slate-500">{workflow.chain.join(" -> ")}</p>
                <p className="mt-2 text-xs leading-5 text-slate-300">{workflow.autonomousAction}</p>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="AI Workforce and Executive Layer" icon={Radio}>
          <div className="border border-line/60 bg-void/35 p-3">
            <div className="text-xs uppercase text-cyan">{audit?.agentCollaboration.status ?? "verifying"}</div>
            <div className="mt-3 grid grid-cols-2 gap-2">
              <MiniMetric label="Agents" value={audit?.agentCollaboration.agents.length} />
              <MiniMetric label="Messages" value={audit?.agentCollaboration.messages} />
              <MiniMetric label="Memory" value={audit?.agentCollaboration.sharedMemoryRecords} />
              <MiniMetric label="Decisions" value={audit?.agentCollaboration.decisions} />
            </div>
            <p className="mt-3 text-xs leading-5 text-slate-500">{audit?.executiveExperience.dashboard ?? "Boardroom dashboard verification pending."}</p>
          </div>
        </Panel>
      </div>
    </section>
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

function MiniMetric({ label, value }: { label: string; value?: number }) {
  return (
    <div className="border border-line/60 bg-panel/50 p-2">
      <span className="text-[10px] uppercase text-slate-500">{label}</span>
      <strong className="mt-1 block text-sm text-white">{typeof value === "number" ? Math.round(value) : "verifying"}</strong>
    </div>
  );
}

function flag(value: boolean) {
  return value ? "yes" : "no";
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
