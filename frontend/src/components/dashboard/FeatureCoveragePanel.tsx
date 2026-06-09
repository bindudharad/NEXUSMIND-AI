"use client";

import { useEffect, useMemo, useState } from "react";
import { BrainCircuit, CheckCircle2, RefreshCw, ShieldCheck, TriangleAlert, XCircle } from "lucide-react";

import type { FeatureCoverageCheck, FeatureCoverageResponse, FeatureCoverageStatus } from "@/types/feature-coverage";

const statusClass: Record<FeatureCoverageStatus, string> = {
  ready: "border-mint/45 bg-mint/10 text-mint",
  warning: "border-amber/45 bg-amber/10 text-amber",
  missing: "border-signal/45 bg-signal/10 text-signal",
  error: "border-signal/45 bg-signal/10 text-signal",
};

const categoryLabel: Record<string, string> = {
  ml: "ML",
  nlp: "NLP",
  forecasting: "Forecasting",
  recommendations: "Recommendations",
  anomaly: "Anomaly",
  dashboard: "Dashboards",
  alerts: "Alerts",
  stack: "Stack",
  realtime: "Realtime",
  database: "Database",
  ui: "UI/UX",
  scope: "Original scope",
};

export function FeatureCoveragePanel() {
  const [coverage, setCoverage] = useState<FeatureCoverageResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadCoverage() {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/system/feature-coverage", { cache: "no-store" });
      if (!response.ok) throw new Error("Coverage request failed");
      setCoverage((await response.json()) as FeatureCoverageResponse);
    } catch {
      setError("Feature coverage auditor could not complete the enterprise verification pass.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const firstRefresh = window.setTimeout(() => {
      void loadCoverage();
    }, 500);
    return () => window.clearTimeout(firstRefresh);
  }, []);

  const grouped = useMemo(() => {
    const groups = new Map<string, FeatureCoverageCheck[]>();
    for (const check of coverage?.checks ?? []) {
      groups.set(check.category, [...(groups.get(check.category) ?? []), check]);
    }
    return Array.from(groups.entries());
  }, [coverage]);

  return (
    <section className="border border-line/80 bg-panel/85 p-5 shadow-control backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <BrainCircuit className="size-5 text-mint" />
          <div>
            <p className="text-xs uppercase text-mint">Master Feature Coverage Audit</p>
            <h2 className="text-xl font-semibold text-white">Burnout, productivity, delay, NLP, anomaly, alerts, and recommendations</h2>
          </div>
        </div>
        <button
          onClick={() => void loadCoverage()}
          className="inline-flex items-center gap-2 border border-line bg-panel2 px-3 py-2 text-sm text-slate-300"
        >
          <RefreshCw className="size-4" />
          Run coverage audit
        </button>
      </div>

      {loading ? <p className="mt-5 text-sm text-slate-400">Auditing every original NEXUSMIND feature against live AI modules and dashboard integrations...</p> : null}
      {error ? <p className="mt-4 text-sm text-signal">{error}</p> : null}

      {coverage ? (
        <>
          <div className="mt-5 grid gap-3 md:grid-cols-5">
            <AuditStat label="Coverage" value={`${coverage.summary.coverageScore.toFixed(1)}%`} tone="text-mint" />
            <AuditStat label="Ready" value={String(coverage.summary.ready)} tone="text-mint" />
            <AuditStat label="Warnings" value={String(coverage.summary.warnings)} tone="text-amber" />
            <AuditStat label="Missing" value={String(coverage.summary.missing)} tone="text-signal" />
            <AuditStat label="Errors" value={String(coverage.summary.errors)} tone="text-signal" />
          </div>

          <div className="mt-5 border border-mint/25 bg-mint/10 p-4">
            <div className="flex items-start gap-3">
              {coverage.criticalGaps.length ? <TriangleAlert className="mt-0.5 size-5 text-amber" /> : <ShieldCheck className="mt-0.5 size-5 text-mint" />}
              <div>
                <p className="text-xs uppercase text-mint">Audit verdict</p>
                <p className="mt-2 text-sm leading-6 text-slate-300">{coverage.verdict}</p>
              </div>
            </div>
          </div>

          <div className="mt-5 grid gap-4 xl:grid-cols-2">
            {grouped.map(([category, checks]) => (
              <article key={category} className="border border-line/70 bg-panel2/65 p-4">
                <div className="mb-3 text-xs uppercase text-slate-500">{categoryLabel[category] ?? category}</div>
                <div className="grid gap-3">
                  {checks.map((check) => (
                    <div key={check.name} className="border border-line/60 bg-panel/60 p-3">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <h3 className="text-sm font-medium text-white">{check.name}</h3>
                        <span className={`inline-flex items-center gap-1 border px-2 py-1 text-[11px] uppercase ${statusClass[check.status]}`}>
                          {check.status === "ready" ? <CheckCircle2 className="size-3" /> : <XCircle className="size-3" />}
                          {check.status}
                        </span>
                      </div>
                      <p className="mt-2 text-xs leading-5 text-slate-400">{check.details}</p>
                      <div className="mt-3 flex flex-wrap gap-2">
                        {check.evidence.slice(0, 4).map((item) => (
                          <span key={item} className="border border-line/50 px-2 py-1 text-[11px] text-slate-500">
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
