"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type React from "react";
import { Area, AreaChart, Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { BrainCircuit, CheckCircle2, GitBranch, Loader2, Radar, RefreshCw, ShieldCheck, Sparkles, Workflow } from "lucide-react";
import type { LucideIcon } from "lucide-react";

import type { FeatureGroupStatus, UltimateFeatureCoverageResponse, UltimateFeatureGroupAudit } from "@/types/ultimate-feature-coverage";

const statusTone: Record<FeatureGroupStatus, string> = {
  present: "border-mint/40 bg-mint/10 text-mint",
  fixed: "border-cyan/40 bg-cyan/10 text-cyan",
  partial: "border-amber/40 bg-amber/10 text-amber",
  missing: "border-rose/40 bg-rose/10 text-rose",
  broken: "border-rose/40 bg-rose/10 text-rose",
};

export function UltimateFeatureCoverageAuditPanel() {
  const [audit, setAudit] = useState<UltimateFeatureCoverageResponse | null>(null);
  const [activeGroup, setActiveGroup] = useState<UltimateFeatureGroupAudit | null>(null);
  const [loading, setLoading] = useState(true);
  const [streamStatus, setStreamStatus] = useState("connecting");
  const [error, setError] = useState("");

  const loadAudit = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/ultimate-feature-coverage/audit", { cache: "no-store" });
      if (!response.ok) throw new Error("Ultimate feature coverage audit failed");
      const payload = (await response.json()) as UltimateFeatureCoverageResponse;
      setAudit(payload);
      setActiveGroup(payload.featureStatusTable[0] ?? null);
      setStreamStatus((status) => (status === "connecting" ? "polling" : status));
    } catch {
      setError("Ultimate Feature Coverage Audit could not load.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => void loadAudit(), 0);
    return () => window.clearTimeout(timer);
  }, [loadAudit]);

  useEffect(() => {
    const source = new EventSource("/api/ultimate-feature-coverage/stream");
    source.addEventListener("ultimate_feature_coverage", (event) => {
      try {
        const payload = JSON.parse((event as MessageEvent).data) as UltimateFeatureCoverageResponse;
        setAudit(payload);
        setActiveGroup(payload.activeGroup ?? payload.featureStatusTable[0] ?? null);
        setLoading(false);
        setStreamStatus("live");
      } catch {
        setStreamStatus((status) => (status === "live" ? "live" : "degraded"));
      }
    });
    source.onerror = () => setStreamStatus((status) => (status === "live" ? "live" : "degraded"));
    return () => source.close();
  }, []);

  const featureRows = useMemo(
    () =>
      (audit?.featureStatusTable ?? []).map((item) => ({
        name: `${item.groupKey}: ${item.featureGroup.replace(" AI", "")}`,
        coverage: item.coveragePercent,
      })),
    [audit],
  );

  const scoreRows = useMemo(() => {
    if (!audit) return [];
    return [
      { name: "AI", score: audit.aiInnovationScore },
      { name: "Complexity", score: audit.technicalComplexityScore },
      { name: "Research", score: audit.researchScore },
      { name: "Startup", score: audit.startupPotentialScore },
      { name: "Enterprise", score: audit.enterpriseReadinessScore },
      { name: "Judge Wow", score: audit.judgeWowFactorScore },
    ];
  }, [audit]);

  return (
    <section
      id="ultimate-feature-coverage-audit-panel"
      data-testid="ultimate-feature-coverage-audit-panel"
      className="w-full max-w-[calc(100vw-2rem)] overflow-hidden border border-cyan/30 bg-[#07111f]/95 p-5 shadow-control backdrop-blur lg:max-w-full"
    >
      <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div className="min-w-0 max-w-[calc(100vw-4rem)] xl:max-w-5xl">
          <div className="flex flex-wrap items-center gap-2 text-xs uppercase text-cyan">
            <Radar className="size-4" />
            <span>Ultimate Feature Coverage Audit</span>
            <span className="border border-cyan/25 bg-cyan/10 px-2 py-1 text-cyan">Feature Groups A-P</span>
            <span className="border border-cyan/25 bg-cyan/10 px-2 py-1 text-cyan">{streamStatus}</span>
            <span className="border border-mint/25 bg-mint/10 px-2 py-1 text-mint">{audit?.finalVerdict ?? "verifying"}</span>
          </div>
          <h2 className="mt-2 break-words text-2xl font-semibold text-white">
            Autonomous Enterprise Intelligence & Digital Twin Platform coverage matrix
          </h2>
          <p className="mt-3 break-words text-sm leading-6 text-slate-400">
            {audit?.executiveSummary ??
              "Auditing NEXUSMIND AI against the complete A-P feature stack: AI CEO, live simulation, What-If, Shadow Company, digital twins, emotion radar, conflict prediction, hidden leaders, agents, memory, organizational brain, crisis, global risk, self-learning, metaverse, and cinematic UI."}
          </p>
        </div>
        <button type="button" onClick={() => void loadAudit()} className="inline-flex h-10 items-center justify-center gap-2 border border-line bg-panel2 px-3 text-sm text-white transition hover:border-cyan/60">
          {loading ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />}
          Verify
        </button>
      </div>

      {error ? <div className="mt-4 border border-rose/40 bg-rose/10 px-3 py-2 text-sm text-rose">{error}</div> : null}

      <div className="mt-5 grid gap-3 md:grid-cols-3 xl:grid-cols-6">
        <Metric icon={ShieldCheck} label="Coverage" value={audit ? `${Math.round(audit.overallCoveragePercent)}/100` : "verifying"} />
        <Metric icon={Sparkles} label="AI Innovation" value={audit ? `${Math.round(audit.aiInnovationScore)}/100` : "verifying"} />
        <Metric icon={BrainCircuit} label="Research" value={audit ? `${Math.round(audit.researchScore)}/100` : "verifying"} />
        <Metric icon={Workflow} label="Enterprise" value={audit ? `${Math.round(audit.enterpriseReadinessScore)}/100` : "verifying"} />
        <Metric icon={Radar} label="Judge Wow" value={audit ? `${Math.round(audit.judgeWowFactorScore)}/100` : "verifying"} />
        <Metric icon={CheckCircle2} label="A-P Groups" value={audit ? `${audit.featureStatusTable.length}/16` : "verifying"} />
      </div>

      <div className="mt-5 grid gap-4 xl:grid-cols-[1.05fr_0.95fr]">
        <Panel title="Feature Status Table" icon={Radar}>
          <div className="grid max-h-[28rem] gap-2 overflow-y-auto pr-1 md:grid-cols-2">
            {audit?.featureStatusTable.map((item) => (
              <button
                type="button"
                key={item.groupKey}
                onClick={() => setActiveGroup(item)}
                className="border border-line bg-void p-3 text-left transition hover:border-cyan/45"
              >
                <div className="flex items-start justify-between gap-3">
                  <h3 className="break-words text-sm font-semibold text-white">
                    {item.groupKey}. {item.featureGroup}
                  </h3>
                  <span className={`shrink-0 border px-2 py-1 text-[10px] uppercase ${statusTone[item.status]}`}>{item.status}</span>
                </div>
                <p className="mt-2 text-xs text-mint">{Math.round(item.coveragePercent)}% coverage</p>
                <p className="mt-2 line-clamp-2 text-xs leading-5 text-slate-500">{item.integrationLinks.join(" | ")}</p>
              </button>
            )) ?? <Empty label="Loading feature groups." />}
          </div>
        </Panel>

        <Panel title="Active Group Evidence" icon={CheckCircle2}>
          <div className="border border-cyan/20 bg-void p-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span className="text-xs uppercase text-cyan">Feature Group {activeGroup?.groupKey ?? "A"}</span>
              <span className={`border px-2 py-1 text-[10px] uppercase ${statusTone[activeGroup?.status ?? "present"]}`}>{activeGroup?.status ?? "present"}</span>
            </div>
            <h3 className="mt-3 break-words text-xl font-semibold text-white">{activeGroup?.featureGroup ?? "Live AI Digital CEO"}</h3>
            <div className="mt-3 grid gap-2">
              {(activeGroup?.requiredCapabilities ?? ["AI CEO Assistant", "Voice Input", "Voice Output"]).slice(0, 6).map((item) => (
                <div key={item} className="flex gap-2 text-sm leading-6 text-slate-300">
                  <CheckCircle2 className="mt-1 size-4 shrink-0 text-mint" />
                  <span className="break-words">{item}</span>
                </div>
              ))}
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              {(activeGroup?.apiRoutes ?? []).slice(0, 4).map((route) => (
                <span key={route} className="border border-line bg-panel2 px-2 py-1 text-xs text-slate-300">
                  {route}
                </span>
              ))}
            </div>
          </div>
        </Panel>
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
        <Panel title="A-P Coverage Trend" icon={ShieldCheck}>
          <div className="h-72 min-w-0">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={featureRows} margin={{ left: 0, right: 8, top: 8, bottom: 0 }}>
                <CartesianGrid stroke="#1C2B3A" strokeDasharray="3 3" />
                <XAxis dataKey="name" interval={0} tick={{ fill: "#94a3b8", fontSize: 9 }} height={76} angle={-40} textAnchor="end" />
                <YAxis domain={[80, 100]} tick={{ fill: "#94a3b8", fontSize: 11 }} />
                <Tooltip contentStyle={{ background: "#101827", border: "1px solid #22324a", color: "#fff" }} />
                <Area type="monotone" dataKey="coverage" stroke="#2EE9D3" fill="#2EE9D3" fillOpacity={0.18} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel title="Final Scores" icon={Sparkles}>
          <div className="h-72 min-w-0">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={scoreRows} layout="vertical" margin={{ left: 22, right: 8, top: 4, bottom: 4 }}>
                <CartesianGrid stroke="#1C2B3A" strokeDasharray="3 3" />
                <XAxis type="number" domain={[0, 100]} tick={{ fill: "#94a3b8", fontSize: 11 }} />
                <YAxis type="category" dataKey="name" width={96} tick={{ fill: "#94a3b8", fontSize: 11 }} />
                <Tooltip contentStyle={{ background: "#101827", border: "1px solid #22324a", color: "#fff" }} />
                <Bar dataKey="score" fill="#7CF0A6" radius={[0, 3, 3, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-3">
        <Panel title="Integration Report" icon={GitBranch}>
          <List items={(audit?.integrationWorkflows ?? []).map((item) => `${item.name}: ${item.chain.join(" -> ")}`)} />
        </Panel>
        <Panel title="Fixed Components" icon={CheckCircle2}>
          <List items={audit?.fixedComponents ?? []} />
        </Panel>
        <Panel title="Errors Fixed" icon={ShieldCheck}>
          <List
            items={[
              ...(audit?.runtimeErrorsFixed ?? []),
              ...(audit?.apiErrorsFixed ?? []),
              ...(audit?.dashboardErrorsFixed ?? []),
              ...(audit?.agentErrorsFixed ?? []),
              ...(audit?.simulationErrorsFixed ?? []),
            ]}
          />
        </Panel>
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
  if (!items.length) return <div className="border border-line bg-void p-3 text-sm text-slate-500">No issues loaded.</div>;
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
