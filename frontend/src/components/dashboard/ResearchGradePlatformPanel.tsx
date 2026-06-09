"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type React from "react";
import { Activity, BrainCircuit, CheckCircle2, Database, Loader2, Network, RefreshCw, ShieldCheck, Sparkles } from "lucide-react";
import type { LucideIcon } from "lucide-react";

import type { ResearchGradePlatformResponse, ResearchGradeStatus } from "@/types/research-grade";

type SnakeRecord = Record<string, unknown>;

const statusTone: Record<ResearchGradeStatus, string> = {
  fully_implemented: "border-mint/40 bg-mint/10 text-mint",
  partial: "border-amber/40 bg-amber/10 text-amber",
  missing: "border-rose/40 bg-rose/10 text-rose",
  broken: "border-rose/40 bg-rose/10 text-rose",
};

export function ResearchGradePlatformPanel() {
  const [audit, setAudit] = useState<ResearchGradePlatformResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [streamStatus, setStreamStatus] = useState("connecting");
  const [error, setError] = useState("");

  const loadAudit = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/research-grade/verification", { cache: "no-store" });
      if (!response.ok) throw new Error("Research-grade verification failed");
      setAudit((await response.json()) as ResearchGradePlatformResponse);
      setStreamStatus((status) => (status === "connecting" ? "polling" : status));
    } catch {
      setError("Research-grade enterprise AI verification could not load.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => void loadAudit(), 0);
    return () => window.clearTimeout(timer);
  }, [loadAudit]);

  useEffect(() => {
    const source = new EventSource("/api/research-grade/stream");
    source.addEventListener("research_grade_platform", (event) => {
      try {
        setAudit(toCamel<ResearchGradePlatformResponse>(JSON.parse((event as MessageEvent).data)));
        setLoading(false);
        setStreamStatus("live");
      } catch {
        setStreamStatus((status) => (status === "live" ? "live" : "degraded"));
      }
    });
    source.onerror = () => setStreamStatus((status) => (status === "live" ? "live" : "degraded"));
    return () => source.close();
  }, []);

  const fullCount = audit?.featureCoverageMatrix.filter((feature) => feature.status === "fully_implemented").length ?? 0;
  const scoreRows = useMemo(() => {
    if (!audit) return [];
    return [
      { label: "Research", score: audit.scorecard.researchLevelScore },
      { label: "Innovation", score: audit.scorecard.innovationScore },
      { label: "Enterprise", score: audit.scorecard.enterpriseScore },
      { label: "Integration", score: audit.scorecard.integrationScore },
      { label: "Judge Wow", score: audit.scorecard.judgeWowFactorScore },
      { label: "Production", score: audit.scorecard.productionReadinessScore },
    ];
  }, [audit]);

  return (
    <section
      id="research-grade-platform-panel"
      data-testid="research-grade-platform-panel"
      className="border border-fuchsia-400/25 bg-panel/90 p-5 shadow-control backdrop-blur"
    >
      <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div className="max-w-5xl">
          <div className="flex flex-wrap items-center gap-2 text-xs uppercase text-fuchsia-200">
            <BrainCircuit className="size-4" />
            <span>Research-Grade Futuristic Feature Audit</span>
            <span className="border border-fuchsia-300/25 bg-fuchsia-400/10 px-2 py-1 text-fuchsia-100">{streamStatus}</span>
          </div>
          <h2 className="mt-2 text-2xl font-semibold text-white">17-feature future operating system verification</h2>
          <p className="mt-3 text-sm leading-6 text-slate-400">
            {audit
              ? `Final verdict: ${audit.finalVerdict}. The audit verifies ${fullCount}/17 research-grade features with explicit Digital Twin Ecosystem and Boardroom AI coverage.`
              : "Scanning futuristic AI modules, digital twins, agents, memory, simulations, voice, metaverse, risk, crisis, and executive boardroom integrations."}
          </p>
        </div>
        <button
          type="button"
          onClick={() => void loadAudit()}
          className="inline-flex h-10 items-center gap-2 border border-line bg-panel2 px-3 text-sm text-white transition hover:border-fuchsia-300/60"
        >
          {loading ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />}
          Verify
        </button>
      </div>

      {error ? <div className="mt-4 border border-rose/40 bg-rose/10 px-3 py-2 text-sm text-rose">{error}</div> : null}

      <div className="mt-5 grid gap-3 md:grid-cols-5">
        <Metric icon={CheckCircle2} label="Feature Matrix" value={audit ? `${fullCount}/17 full` : "verifying"} />
        <Metric icon={Sparkles} label="Research Score" value={audit ? `${Math.round(audit.scorecard.researchLevelScore)}/100` : "verifying"} />
        <Metric icon={Network} label="Integrations" value={audit ? `${audit.integrationAudit.length} linked` : "verifying"} />
        <Metric icon={ShieldCheck} label="Minimum Score" value={audit ? `${Math.round(audit.scorecard.minimumScore)}/100` : "verifying"} />
        <Metric icon={Database} label="Source Systems" value={audit ? `${audit.sourceSystems.length}` : "verifying"} />
      </div>

      <div className="mt-5 grid gap-4 xl:grid-cols-[0.8fr_1.2fr]">
        <Panel title="Research Scorecard" icon={Activity}>
          <div className="grid gap-2">
            {scoreRows.map((row) => (
              <div key={row.label} className="grid grid-cols-[110px_1fr_48px] items-center gap-3">
                <span className="text-xs uppercase text-slate-500">{row.label}</span>
                <div className="h-2 overflow-hidden bg-void">
                  <div className="h-full bg-fuchsia-300" style={{ width: `${Math.min(100, Math.max(0, row.score))}%` }} />
                </div>
                <strong className="text-right text-xs text-white">{Math.round(row.score)}</strong>
              </div>
            ))}
          </div>
          <div className="mt-4 grid gap-2">
            {audit?.errorsFixed.slice(0, 3).map((item) => (
              <p key={item} className="border border-line/60 bg-void/35 p-2 text-xs leading-5 text-slate-400">{item}</p>
            ))}
          </div>
        </Panel>

        <Panel title="Feature Coverage Matrix" icon={CheckCircle2}>
          <div className="grid max-h-96 gap-2 overflow-y-auto pr-1 md:grid-cols-2">
            {audit?.featureCoverageMatrix.map((feature) => (
              <div key={feature.featureId} className="border border-line/60 bg-void/35 p-3">
                <div className="flex items-start justify-between gap-3">
                  <h3 className="text-sm font-semibold text-white">{feature.featureId}. {feature.name}</h3>
                  <span className={`border px-2 py-1 text-[10px] uppercase ${statusTone[feature.status]}`}>{feature.status.replace("_", " ")}</span>
                </div>
                <p className="mt-2 text-xs text-slate-500">Coverage {Math.round(feature.coveragePercent)} | {feature.integrations.slice(0, 2).join(" + ")}</p>
                <p className="mt-2 text-xs leading-5 text-slate-400">{feature.requiredCapabilities.slice(0, 4).join(" | ")}</p>
              </div>
            ))}
          </div>
        </Panel>
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-[1fr_0.9fr]">
        <Panel title="Integration Audit" icon={Network}>
          <div className="grid max-h-72 gap-2 overflow-y-auto pr-1 md:grid-cols-2">
            {audit?.integrationAudit.map((link) => (
              <div key={`${link.source}-${link.target}`} className="border border-line/60 bg-panel2/45 p-3">
                <div className="flex items-start justify-between gap-3">
                  <h3 className="text-sm font-semibold text-white">{link.source} {"->"} {link.target}</h3>
                  <span className={`border px-2 py-1 text-[10px] uppercase ${statusTone[link.status]}`}>{link.status.replace("_", " ")}</span>
                </div>
                <p className="mt-2 text-xs leading-5 text-slate-500">{link.evidence.join(" | ")}</p>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Implemented Components" icon={Database}>
          <div className="grid max-h-72 gap-2 overflow-y-auto pr-1">
            {audit?.implementedComponents.map((item) => (
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
      <div className="mb-3 flex items-center gap-2 text-xs uppercase text-fuchsia-200">
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
        <Icon className="size-4 text-fuchsia-200" />
        <span>{label}</span>
      </div>
      <strong className="mt-2 block break-words text-lg font-semibold text-white">{value}</strong>
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
