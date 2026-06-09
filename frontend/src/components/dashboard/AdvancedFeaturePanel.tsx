"use client";

import { useEffect, useMemo, useState } from "react";
import { CheckCircle2, Cpu, RefreshCw, ShieldCheck, TriangleAlert, XCircle } from "lucide-react";

import type { FeatureCoverageCheck, FeatureCoverageResponse, FeatureCoverageStatus } from "@/types/feature-coverage";

const statusClass: Record<FeatureCoverageStatus, string> = {
  ready: "border-mint/45 bg-mint/10 text-mint",
  warning: "border-amber/45 bg-amber/10 text-amber",
  missing: "border-signal/45 bg-signal/10 text-signal",
  error: "border-signal/45 bg-signal/10 text-signal",
};

const categoryLabel: Record<string, string> = {
  simulation: "Simulation",
  voice: "Voice AI",
  agents: "Agents",
  emotion: "Emotion AI",
  visualization: "3D",
  alerts: "Alerts",
  recommendations: "Suggestions",
  learning: "Learning",
  knowledge: "Knowledge AI",
  security: "Security",
  meeting: "Meeting AI",
  realtime: "Realtime",
  ui: "UI/UX",
};

export function AdvancedFeaturePanel() {
  const [audit, setAudit] = useState<FeatureCoverageResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadAudit() {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/system/advanced-features", { cache: "no-store" });
      if (!response.ok) throw new Error("Advanced audit failed");
      setAudit((await response.json()) as FeatureCoverageResponse);
    } catch {
      setError("Advanced systems auditor could not complete the verification pass.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const firstRefresh = window.setTimeout(() => {
      void loadAudit();
    }, 1000);
    return () => window.clearTimeout(firstRefresh);
  }, []);

  const grouped = useMemo(() => {
    const groups = new Map<string, FeatureCoverageCheck[]>();
    for (const check of audit?.checks ?? []) {
      groups.set(check.category, [...(groups.get(check.category) ?? []), check]);
    }
    return Array.from(groups.entries());
  }, [audit]);

  return (
    <section className="border border-cyan/25 bg-panel/85 p-5 shadow-control backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <Cpu className="size-5 text-cyan" />
          <div>
            <p className="text-xs uppercase text-cyan">Advanced Systems Verification</p>
            <h2 className="text-xl font-semibold text-white">Digital Twin, voice AI, multi-agent council, vector memory, realtime, and 3D control room</h2>
          </div>
        </div>
        <button
          onClick={() => void loadAudit()}
          className="inline-flex items-center gap-2 border border-line bg-panel2 px-3 py-2 text-sm text-slate-300"
        >
          <RefreshCw className="size-4" />
          Run advanced audit
        </button>
      </div>

      {loading ? <p className="mt-5 text-sm text-slate-400">Verifying the cinematic enterprise operating-system layer against live modules...</p> : null}
      {error ? <p className="mt-4 text-sm text-signal">{error}</p> : null}

      {audit ? (
        <>
          <div className="mt-5 grid gap-3 md:grid-cols-5">
            <AuditStat label="Advanced score" value={`${audit.summary.coverageScore.toFixed(1)}%`} tone="text-cyan" />
            <AuditStat label="Ready" value={String(audit.summary.ready)} tone="text-mint" />
            <AuditStat label="Warnings" value={String(audit.summary.warnings)} tone="text-amber" />
            <AuditStat label="Missing" value={String(audit.summary.missing)} tone="text-signal" />
            <AuditStat label="Errors" value={String(audit.summary.errors)} tone="text-signal" />
          </div>

          <div className="mt-5 border border-cyan/25 bg-cyan/10 p-4">
            <div className="flex items-start gap-3">
              {audit.criticalGaps.length ? <TriangleAlert className="mt-0.5 size-5 text-amber" /> : <ShieldCheck className="mt-0.5 size-5 text-cyan" />}
              <div>
                <p className="text-xs uppercase text-cyan">Advanced verdict</p>
                <p className="mt-2 text-sm leading-6 text-slate-300">{audit.verdict}</p>
              </div>
            </div>
          </div>

          <div className="mt-5 grid gap-4 xl:grid-cols-2">
            {grouped.map(([category, checks]) => (
              <article key={category} className="border border-line/70 bg-panel2/65 p-4">
                <div className="mb-3 text-xs uppercase text-slate-500">{categoryLabel[category] ?? category}</div>
                <div className="grid gap-3">
                  {checks.map((check, checkIndex) => (
                    <div key={`${category}-${check.name}-${checkIndex}`} className="border border-line/60 bg-panel/60 p-3">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <h3 className="text-sm font-medium text-white">{check.name}</h3>
                        <span className={`inline-flex items-center gap-1 border px-2 py-1 text-[11px] uppercase ${statusClass[check.status]}`}>
                          {check.status === "ready" ? <CheckCircle2 className="size-3" /> : <XCircle className="size-3" />}
                          {check.status}
                        </span>
                      </div>
                      <p className="mt-2 text-xs leading-5 text-slate-400">{check.details}</p>
                      <div className="mt-3 flex flex-wrap gap-2">
                        {check.evidence.slice(0, 5).map((item, evidenceIndex) => (
                          <span key={`${check.name}-${item}-${evidenceIndex}`} className="border border-line/50 px-2 py-1 text-[11px] text-slate-500">
                            {item}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </article>
            ))}
          </div>
        </>
      ) : null}
    </section>
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
