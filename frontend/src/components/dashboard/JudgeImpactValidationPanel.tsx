"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type React from "react";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import {
  Award,
  CheckCircle2,
  CircuitBoard,
  Gauge,
  Loader2,
  Radio,
  RefreshCw,
  Rocket,
  ShieldCheck,
  Sparkles,
  TriangleAlert,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import type { JudgeImpactStatus, JudgeImpactValidationResponse } from "@/types/judge-impact";

type SnakeRecord = Record<string, unknown>;

const statusTone: Record<JudgeImpactStatus, string> = {
  elite: "border-mint/40 bg-mint/10 text-mint",
  strong: "border-cyan/40 bg-cyan/10 text-cyan",
  needs_work: "border-amber/40 bg-amber/10 text-amber",
  weak: "border-rose/40 bg-rose/10 text-rose",
};

const barColors = ["#2EE9D3", "#7CF0A6", "#38BDF8", "#A78BFA", "#F6B44B", "#FF3B6B"];

export function JudgeImpactValidationPanel() {
  const [audit, setAudit] = useState<JudgeImpactValidationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [streamStatus, setStreamStatus] = useState("connecting");
  const [error, setError] = useState("");

  const loadAudit = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/judge-impact/validation", { cache: "no-store" });
      if (!response.ok) throw new Error("Judge impact validation failed");
      setAudit((await response.json()) as JudgeImpactValidationResponse);
      setStreamStatus((status) => (status === "connecting" ? "polling" : status));
    } catch {
      setError("Judge impact validation could not verify the product.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => void loadAudit(), 0);
    return () => window.clearTimeout(timer);
  }, [loadAudit]);

  useEffect(() => {
    const source = new EventSource("/api/judge-impact/stream");
    source.addEventListener("judge_impact_validation", (event) => {
      try {
        const payload = toCamel<JudgeImpactValidationResponse>(JSON.parse((event as MessageEvent).data));
        setAudit(payload);
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
      { name: "Innovation", score: audit.scorecard.innovationScore },
      { name: "Enterprise", score: audit.scorecard.enterpriseReadinessScore },
      { name: "Maturity", score: audit.scorecard.productMaturityScore },
      { name: "Startup", score: audit.scorecard.startupPotentialScore },
      { name: "Technical", score: audit.scorecard.technicalComplexityScore },
      { name: "Wow", score: audit.scorecard.judgeWowFactorScore },
      { name: "Recruiter", score: audit.scorecard.recruiterImpactScore },
      { name: "Production", score: audit.scorecard.productionReadinessScore },
    ];
  }, [audit]);

  const connected = audit?.integrationStatus.filter((item) => item.status === "connected").length ?? 0;

  return (
    <section
      id="judge-impact-validation-panel"
      data-testid="judge-impact-validation-panel"
      className="border border-mint/25 bg-panel/85 p-5 shadow-control backdrop-blur"
    >
      <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div className="max-w-4xl">
          <div className="flex flex-wrap items-center gap-2 text-xs uppercase text-mint">
            <Award className="size-4" />
            <span>Judge Impact Validation</span>
            <span className="border border-mint/25 bg-mint/10 px-2 py-1 text-mint">{streamStatus}</span>
          </div>
          <h2 className="mt-2 text-2xl font-semibold text-white">Enterprise-grade product audit and evaluator proof</h2>
          <p className="mt-3 text-sm leading-6 text-slate-400">
            {audit?.executiveSummary ??
              "Verifying judge impact, startup maturity, enterprise SaaS readiness, research-level innovation, integrations, and production evidence."}
          </p>
        </div>
        <button
          type="button"
          onClick={() => void loadAudit()}
          className="inline-flex h-10 items-center gap-2 border border-line bg-panel2 px-3 text-sm text-white transition hover:border-mint/60"
        >
          {loading ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />}
          Validate
        </button>
      </div>

      {error ? <div className="mt-4 border border-rose/40 bg-rose/10 px-3 py-2 text-sm text-rose">{error}</div> : null}

      <div className="mt-5 grid gap-3 md:grid-cols-4">
        <Metric icon={Rocket} label="Final Verdict" value={audit?.finalVerdict ?? "verifying"} />
        <Metric icon={Gauge} label="Minimum Score" value={audit ? `${Math.round(audit.scorecard.minimumScore)}/100` : "verifying"} />
        <Metric icon={CheckCircle2} label="Integrations" value={audit ? `${connected}/${audit.integrationStatus.length}` : "verifying"} />
        <Metric icon={ShieldCheck} label="Missing" value={audit ? String(audit.missingComponents.length) : "verifying"} />
      </div>

      <div className="mt-5 grid gap-4 xl:grid-cols-[0.92fr_1.08fr]">
        <Panel title="Scorecard" icon={Sparkles}>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={scoreRows} layout="vertical" margin={{ left: 16, right: 10, top: 4, bottom: 4 }}>
                <CartesianGrid stroke="#1C2B3A" strokeDasharray="3 3" />
                <XAxis type="number" domain={[0, 100]} stroke="#64748b" tickLine={false} axisLine={false} />
                <YAxis type="category" dataKey="name" width={82} stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ background: "#08111f", border: "1px solid #223044", color: "#e2e8f0" }} />
                <Bar dataKey="score" radius={[0, 3, 3, 0]}>
                  {scoreRows.map((entry, index) => (
                    <Cell key={entry.name} fill={barColors[index % barColors.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel title="Evaluator Audit" icon={CircuitBoard}>
          <div className="grid max-h-72 gap-2 overflow-y-auto pr-1 md:grid-cols-2">
            {audit?.evaluatorAudits.map((item) => (
              <div key={item.evaluator} className="border border-line/60 bg-void/35 p-3">
                <div className="flex items-start justify-between gap-3">
                  <h3 className="text-sm font-semibold text-white">{item.evaluator}</h3>
                  <span className={`border px-2 py-1 text-[10px] uppercase ${statusTone[item.status]}`}>{item.status.replace("_", " ")}</span>
                </div>
                <p className="mt-2 text-xs leading-5 text-slate-500">{item.productionBelief}</p>
                <div className="mt-3 grid grid-cols-3 gap-2">
                  <MiniMetric label="Innovation" value={item.innovationScore} />
                  <MiniMetric label="Enterprise" value={item.enterpriseReadinessScore} />
                  <MiniMetric label="Market" value={item.marketPotentialScore} />
                </div>
              </div>
            ))}
          </div>
        </Panel>
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-3">
        <Panel title="Product Audit" icon={ShieldCheck}>
          <div className="grid max-h-72 gap-2 overflow-y-auto pr-1">
            {audit?.productAudit.map((dimension) => (
              <div key={dimension.name} className="border border-line/60 bg-void/35 p-3">
                <div className="flex items-start justify-between gap-3">
                  <h3 className="text-sm font-semibold text-white">{dimension.name}</h3>
                  <strong className="text-sm text-mint">{Math.round(dimension.score)}</strong>
                </div>
                <div className="mt-2 flex flex-wrap gap-1">
                  {dimension.evidence.slice(0, 3).map((item) => (
                    <span key={item} className="border border-line/60 bg-panel2/60 px-2 py-1 text-[10px] text-slate-500">
                      {item}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Differentiation" icon={Rocket}>
          <div className="grid max-h-72 gap-2 overflow-y-auto pr-1">
            {audit?.differentiationReport.map((item) => (
              <div key={item.question} className="border border-line/60 bg-panel2/45 p-3">
                <h3 className="text-xs font-semibold uppercase text-cyan">{item.question}</h3>
                <p className="mt-2 text-xs leading-5 text-slate-400">{item.answer}</p>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Integration Status" icon={Radio}>
          <div className="grid max-h-72 gap-2 overflow-y-auto pr-1">
            {audit?.integrationStatus.map((item) => (
              <div key={item.integration} className="border border-line/60 bg-void/35 p-3">
                <div className="flex items-center justify-between gap-3">
                  <span className="text-xs font-semibold text-white">{item.integration}</span>
                  <span className={`border px-2 py-1 text-[10px] uppercase ${item.status === "connected" ? statusTone.elite : statusTone.weak}`}>
                    {item.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </Panel>
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-[1fr_1fr]">
        <Panel title="Fixed and Regenerated Components" icon={CheckCircle2}>
          <div className="grid gap-2">
            {[...(audit?.fixedComponents ?? []), ...(audit?.regeneratedComponents ?? [])].slice(0, 8).map((item) => (
              <p key={item} className="border border-line/60 bg-panel2/45 px-3 py-2 text-xs leading-5 text-slate-400">
                {item}
              </p>
            ))}
          </div>
        </Panel>

        <Panel title="Residual Risk" icon={TriangleAlert}>
          <div className="grid gap-2">
            {(audit?.residualRisks ?? ["Verifying residual product risks."]).slice(0, 6).map((item) => (
              <p key={item} className="border border-line/60 bg-void/35 px-3 py-2 text-xs leading-5 text-slate-400">
                {item}
              </p>
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
        <Icon className="size-4 text-mint" />
        <span>{label}</span>
      </div>
      <strong className="mt-2 block break-words text-xl font-semibold text-white">{value}</strong>
    </div>
  );
}

function MiniMetric({ label, value }: { label: string; value: number }) {
  return (
    <div className="border border-line/60 bg-panel/50 p-2">
      <span className="text-[10px] uppercase text-slate-500">{label}</span>
      <strong className="mt-1 block text-sm text-white">{Math.round(value)}</strong>
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
