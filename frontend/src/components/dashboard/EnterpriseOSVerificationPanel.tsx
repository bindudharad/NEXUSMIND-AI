"use client";

import { useEffect, useMemo, useState } from "react";
import type React from "react";
import { BrainCircuit, Building2, CheckCircle2, DatabaseZap, Network, RefreshCw, ShieldCheck, TriangleAlert } from "lucide-react";

import type { FeatureCoverageCheck, FeatureCoverageResponse, FeatureCoverageStatus } from "@/types/feature-coverage";

const statusClass: Record<FeatureCoverageStatus, string> = {
  ready: "border-mint/45 bg-mint/10 text-mint",
  warning: "border-amber/45 bg-amber/10 text-amber",
  missing: "border-signal/45 bg-signal/10 text-signal",
  error: "border-signal/45 bg-signal/10 text-signal",
};

const categoryIcon: Record<string, React.ComponentType<{ className?: string }>> = {
  simulation: Building2,
  agents: Network,
  assistant: BrainCircuit,
  knowledge: DatabaseZap,
  security: ShieldCheck,
  visualization: Building2,
  learning: BrainCircuit,
  decision: BrainCircuit,
  realtime: Network,
  ui: Building2,
  backend: DatabaseZap,
  data: DatabaseZap,
};

export function EnterpriseOSVerificationPanel() {
  const [audit, setAudit] = useState<FeatureCoverageResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadAudit() {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/system/enterprise-ai-features", { cache: "no-store" });
      if (!response.ok) throw new Error("Enterprise OS audit failed");
      setAudit((await response.json()) as FeatureCoverageResponse);
    } catch {
      setError("Enterprise OS verifier could not complete the Fortune 500 readiness pass.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const firstRefresh = window.setTimeout(() => {
      void loadAudit();
    }, 1500);
    return () => window.clearTimeout(firstRefresh);
  }, []);

  const topChecks = useMemo(() => audit?.checks.slice(0, 6) ?? [], [audit]);
  const infrastructureChecks = useMemo(
    () => audit?.checks.filter((check) => ["realtime", "backend", "data", "ui"].includes(check.category)) ?? [],
    [audit],
  );

  return (
    <section className="border border-mint/25 bg-panel/85 p-5 shadow-control backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <ShieldCheck className="size-5 text-mint" />
          <div>
            <p className="text-xs uppercase text-mint">Enterprise AI Operating System Verification</p>
            <h2 className="text-xl font-semibold text-white">Fortune 500 readiness: twin, agents, CEO assistant, memory, security, realtime, and control-room UI</h2>
          </div>
        </div>
        <button
          onClick={() => void loadAudit()}
          className="inline-flex items-center gap-2 border border-line bg-panel2 px-3 py-2 text-sm text-slate-300"
        >
          <RefreshCw className="size-4" />
          Run enterprise audit
        </button>
      </div>

      {loading ? <p className="mt-5 text-sm text-slate-400">Auditing the advanced enterprise AI command layer against live backend systems...</p> : null}
      {error ? <p className="mt-4 text-sm text-signal">{error}</p> : null}

      {audit ? (
        <>
          <div className="mt-5 grid gap-3 md:grid-cols-5">
            <AuditStat label="OS score" value={`${audit.summary.coverageScore.toFixed(1)}%`} tone="text-mint" />
            <AuditStat label="Ready" value={String(audit.summary.ready)} tone="text-cyan" />
            <AuditStat label="Warnings" value={String(audit.summary.warnings)} tone="text-amber" />
            <AuditStat label="Critical gaps" value={String(audit.criticalGaps.length)} tone={audit.criticalGaps.length ? "text-signal" : "text-mint"} />
            <AuditStat label="Systems checked" value={String(audit.summary.total)} tone="text-white" />
          </div>

          <div className="mt-5 border border-mint/25 bg-mint/10 p-4">
            <div className="flex items-start gap-3">
              {audit.criticalGaps.length ? <TriangleAlert className="mt-0.5 size-5 text-amber" /> : <CheckCircle2 className="mt-0.5 size-5 text-mint" />}
              <div>
                <p className="text-xs uppercase text-mint">Executive verdict</p>
                <p className="mt-2 text-sm leading-6 text-slate-300">{audit.verdict}</p>
              </div>
            </div>
          </div>

          <div className="mt-5 grid gap-4 xl:grid-cols-2">
            <div className="grid gap-3">
              {topChecks.map((check) => (
                <EnterpriseCheck key={check.name} check={check} />
              ))}
            </div>
            <div className="grid gap-3">
              {infrastructureChecks.map((check) => (
                <EnterpriseCheck key={check.name} check={check} />
              ))}
            </div>
          </div>
        </>
      ) : null}
    </section>
  );
}

function EnterpriseCheck({ check }: { check: FeatureCoverageCheck }) {
  const Icon = categoryIcon[check.category] ?? BrainCircuit;
  return (
    <article className="border border-line/70 bg-panel2/65 p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Icon className="size-4 text-cyan" />
          <h3 className="text-sm font-medium text-white">{check.name}</h3>
        </div>
        <span className={`border px-2 py-1 text-[11px] uppercase ${statusClass[check.status]}`}>{check.status}</span>
      </div>
      <p className="mt-2 text-xs leading-5 text-slate-400">{check.details}</p>
      <div className="mt-3 flex flex-wrap gap-2">
        {check.evidence.slice(0, 5).map((item) => (
          <span key={item} className="border border-line/50 px-2 py-1 text-[11px] text-slate-500">
            {item}
          </span>
        ))}
      </div>
    </article>
  );
}

function AuditStat({ label, value, tone }: { label: string; value: string; tone: string }) {
  return (
    <div className="border border-line/70 bg-panel2/65 p-4">
      <span className="block text-[11px] uppercase text-slate-500">{label}</span>
      <strong className={`mt-2 block text-2xl font-semibold ${tone}`}>{value}</strong>
    </div>
  );
}
