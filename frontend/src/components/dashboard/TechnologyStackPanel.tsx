"use client";

import { useEffect, useMemo, useState } from "react";
import { CheckCircle2, Cloud, Container, Database, RefreshCw, ServerCog, TriangleAlert, Workflow, XCircle } from "lucide-react";

import type { TechnologyCheck, TechnologyStackResponse, TechnologyStatus } from "@/types/technology-stack";

const statusStyles: Record<TechnologyStatus, string> = {
  ready: "border-mint/45 bg-mint/10 text-mint",
  configured: "border-cyan/45 bg-cyan/10 text-cyan",
  missing: "border-amber/45 bg-amber/10 text-amber",
  error: "border-signal/45 bg-signal/10 text-signal",
};

const categoryLabels: Record<string, string> = {
  frontend: "Frontend",
  backend: "Backend",
  ai_ml: "AI/ML",
  database: "Database",
  deployment: "Deployment",
  cloud: "Cloud",
};

const categoryIcons: Record<string, typeof Workflow> = {
  frontend: Workflow,
  backend: ServerCog,
  ai_ml: CheckCircle2,
  database: Database,
  deployment: Container,
  cloud: Cloud,
};

export function TechnologyStackPanel() {
  const [stack, setStack] = useState<TechnologyStackResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadStack() {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/system/technology-stack", { cache: "no-store" });
      if (!response.ok) throw new Error("Technology stack request failed");
      setStack((await response.json()) as TechnologyStackResponse);
    } catch {
      setError("Technology stack verifier could not reach the backend.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const firstRefresh = window.setTimeout(() => {
      void loadStack();
    }, 250);
    const interval = window.setInterval(() => {
      void loadStack();
    }, 60000);
    return () => {
      window.clearTimeout(firstRefresh);
      window.clearInterval(interval);
    };
  }, []);

  const grouped = useMemo(() => {
    const groups = new Map<string, TechnologyCheck[]>();
    for (const check of stack?.checks ?? []) {
      groups.set(check.category, [...(groups.get(check.category) ?? []), check]);
    }
    return Array.from(groups.entries());
  }, [stack]);

  return (
    <section className="border border-line/80 bg-panel/85 p-5 shadow-control backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <ServerCog className="size-5 text-cyan" />
          <div>
            <p className="text-xs uppercase text-cyan">Technology Stack Verification</p>
            <h2 className="text-xl font-semibold text-white">React, Next.js, FastAPI, AI, databases, Docker, AWS</h2>
          </div>
        </div>
        <button
          onClick={() => void loadStack()}
          className="inline-flex items-center gap-2 border border-line bg-panel2 px-3 py-2 text-sm text-slate-300"
        >
          <RefreshCw className="size-4" />
          Refresh stack audit
        </button>
      </div>

      {loading ? <p className="mt-5 text-sm text-slate-400">Verifying runtime imports, API routes, database probes, containers, and cloud assets...</p> : null}
      {error ? <p className="mt-4 text-sm text-signal">{error}</p> : null}

      {stack ? (
        <>
          <div className="mt-5 grid gap-3 md:grid-cols-5">
            <StackStat label="Production Score" value={`${stack.summary.productionReadyScore.toFixed(1)}%`} tone="text-mint" />
            <StackStat label="Ready" value={String(stack.summary.ready)} tone="text-mint" />
            <StackStat label="Configured" value={String(stack.summary.configured)} tone="text-cyan" />
            <StackStat label="Missing" value={String(stack.summary.missing)} tone="text-amber" />
            <StackStat label="Errors" value={String(stack.summary.errors)} tone="text-signal" />
          </div>

          <div className="mt-5 grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
            <div className="grid gap-3">
              {grouped.map(([category, checks]) => {
                const Icon = categoryIcons[category] ?? CheckCircle2;
                return (
                  <article key={category} className="border border-line/70 bg-panel2/65 p-4">
                    <div className="mb-3 flex items-center gap-2 text-xs uppercase text-slate-500">
                      <Icon className="size-4 text-cyan" />
                      {categoryLabels[category] ?? category}
                    </div>
                    <div className="grid gap-2 md:grid-cols-2">
                      {checks.map((check) => (
                        <div key={check.name} className="border border-line/60 bg-panel/60 p-3">
                          <div className="flex items-center justify-between gap-2">
                            <h3 className="text-sm font-medium text-white">{check.name}</h3>
                            <span className={`border px-2 py-1 text-[11px] uppercase ${statusStyles[check.status]}`}>
                              {check.status}
                            </span>
                          </div>
                          <p className="mt-2 text-xs leading-5 text-slate-400">{check.details}</p>
                          <div className="mt-3 flex flex-wrap gap-2">
                            {check.evidence.slice(0, 3).map((item) => (
                              <span key={item} className="border border-line/50 px-2 py-1 text-[11px] text-slate-500">
                                {item}
                              </span>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </article>
                );
              })}
            </div>

            <aside className="border border-cyan/25 bg-cyan/10 p-4">
              <div className="flex items-center gap-2 text-xs uppercase text-cyan">
                {stack.summary.missing || stack.summary.errors ? <TriangleAlert className="size-4" /> : <CheckCircle2 className="size-4" />}
                Enterprise readiness notes
              </div>
              <p className="mt-3 text-sm leading-6 text-slate-300">
                Verified {stack.summary.total} technologies at {new Date(stack.verifiedAt).toLocaleTimeString()} with live imports, route inspection,
                database probes, Docker asset checks, and AWS deployment asset validation.
              </p>
              <div className="mt-4 grid gap-2">
                {stack.recommendations.map((item) => (
                  <div key={item} className="flex items-start gap-2 border border-line/60 bg-panel/50 p-3 text-sm text-slate-300">
                    {item.toLowerCase().includes("missing") || item.toLowerCase().includes("error") ? (
                      <XCircle className="mt-0.5 size-4 text-signal" />
                    ) : (
                      <CheckCircle2 className="mt-0.5 size-4 text-mint" />
                    )}
                    <span>{item}</span>
                  </div>
                ))}
              </div>
            </aside>
          </div>
        </>
      ) : null}
    </section>
  );
}

function StackStat({ label, value, tone }: { label: string; value: string; tone: string }) {
  return (
    <div className="border border-line/70 bg-panel2/65 p-4">
      <span className="block text-[11px] uppercase text-slate-500">{label}</span>
      <strong className={`mt-2 block text-2xl font-semibold ${tone}`}>{value}</strong>
    </div>
  );
}
