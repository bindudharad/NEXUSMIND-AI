"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type React from "react";
import { Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import {
  BrainCircuit,
  CheckCircle2,
  Cpu,
  GitBranch,
  Loader2,
  Network,
  RefreshCw,
  Rocket,
  ShieldCheck,
  Sparkles,
  TrendingUp,
  Workflow,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import type { InnovationStackStatus, JudgeWinningInnovationStackResponse } from "@/types/judge-innovation-stack";

const statusTone: Record<InnovationStackStatus, string> = {
  complete: "border-mint/40 bg-mint/10 text-mint",
  working: "border-cyan/40 bg-cyan/10 text-cyan",
  partial: "border-amber/40 bg-amber/10 text-amber",
  missing: "border-rose/40 bg-rose/10 text-rose",
};

const scoreColors = ["#2EE9D3", "#38BDF8", "#7CF0A6", "#A78BFA", "#F6B44B", "#FF3B6B", "#22C55E", "#60A5FA"];

export function JudgeWinningInnovationStackPanel() {
  const [audit, setAudit] = useState<JudgeWinningInnovationStackResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [streamStatus, setStreamStatus] = useState("connecting");
  const [error, setError] = useState("");

  const loadAudit = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/judge-winning-innovation-stack/verification", { cache: "no-store" });
      if (!response.ok) throw new Error("Judge-winning innovation stack verification failed");
      setAudit((await response.json()) as JudgeWinningInnovationStackResponse);
      setStreamStatus((status) => (status === "connecting" ? "polling" : status));
    } catch {
      setError("Judge-winning innovation stack audit could not load.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => void loadAudit(), 0);
    return () => window.clearTimeout(timer);
  }, [loadAudit]);

  useEffect(() => {
    const source = new EventSource("/api/judge-winning-innovation-stack/stream");
    source.addEventListener("judge_winning_innovation_stack", (event) => {
      try {
        setAudit(JSON.parse((event as MessageEvent).data) as JudgeWinningInnovationStackResponse);
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
      { name: "AI Innovation", score: audit.scorecard.aiInnovation },
      { name: "Complexity", score: audit.scorecard.technicalComplexity },
      { name: "Research", score: audit.scorecard.researchValue },
      { name: "Business", score: audit.scorecard.businessValue },
      { name: "Visual", score: audit.scorecard.visualImpact },
      { name: "Scalability", score: audit.scorecard.scalability },
      { name: "Judge Appeal", score: audit.scorecard.judgeAppeal },
      { name: "Production", score: audit.scorecard.productionReadiness },
    ];
  }, [audit]);

  const pillarTrend = useMemo(() => {
    if (!audit) return [];
    return audit.capabilityAudit.map((item, index) => ({ name: item.capability.split(" ")[0], score: item.score, index }));
  }, [audit]);

  return (
    <section
      id="judge-winning-innovation-stack-panel"
      data-testid="judge-winning-innovation-stack-panel"
      className="w-full max-w-[calc(100vw-2rem)] overflow-hidden border border-mint/30 bg-panel/90 p-5 shadow-control backdrop-blur lg:max-w-full"
    >
      <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div className="min-w-0 max-w-[calc(100vw-4rem)] xl:max-w-5xl">
          <div className="flex flex-wrap items-center gap-2 text-xs uppercase text-mint">
            <Rocket className="size-4" />
            <span>Judge-Winning Innovation Stack</span>
            <span className="border border-cyan/25 bg-cyan/10 px-2 py-1 text-cyan">{streamStatus}</span>
            <span className="border border-mint/25 bg-mint/10 px-2 py-1 text-mint">{audit?.finalVerdict ?? "verifying"}</span>
          </div>
          <h2 className="mt-2 break-words text-2xl font-semibold text-white">Connected AI, simulations, predictions, agents, twins, learning, and real-time analytics</h2>
          <p className="mt-3 break-words text-sm leading-6 text-slate-400">
            {audit?.executiveSummary ??
              "Verifying that NEXUSMIND AI is presented and functioning as an integrated autonomous enterprise intelligence platform, not a generic dashboard or isolated HR tool."}
          </p>
        </div>
        <button type="button" onClick={() => void loadAudit()} className="inline-flex h-10 items-center justify-center gap-2 border border-line bg-panel2 px-3 text-sm text-white transition hover:border-mint/60">
          {loading ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />}
          Verify
        </button>
      </div>

      {error ? <div className="mt-4 border border-rose/40 bg-rose/10 px-3 py-2 text-sm text-rose">{error}</div> : null}

      <div className="mt-5 grid gap-3 md:grid-cols-3 xl:grid-cols-6">
        <Metric icon={ShieldCheck} label="Production" value={audit ? `${Math.round(audit.productionReadinessScore)}/100` : "verifying"} />
        <Metric icon={Sparkles} label="Innovation" value={audit ? `${Math.round(audit.innovationScore)}/100` : "verifying"} />
        <Metric icon={BrainCircuit} label="Research" value={audit ? `${Math.round(audit.researchScore)}/100` : "verifying"} />
        <Metric icon={Rocket} label="Startup" value={audit ? `${Math.round(audit.startupPotentialScore)}/100` : "verifying"} />
        <Metric icon={TrendingUp} label="Judge Wow" value={audit ? `${Math.round(audit.judgeWowFactorScore)}/100` : "verifying"} />
        <Metric icon={Workflow} label="Pillars" value={audit ? `${audit.capabilityAudit.length}/10` : "verifying"} />
      </div>

      <div className="mt-5 grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
        <Panel title="Competition Scorecard" icon={ShieldCheck}>
          <div className="h-80 min-w-0">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={scoreRows} layout="vertical" margin={{ left: 20, right: 8, top: 4, bottom: 4 }}>
                <CartesianGrid stroke="#1C2B3A" strokeDasharray="3 3" />
                <XAxis type="number" domain={[0, 100]} tick={{ fill: "#94a3b8", fontSize: 11 }} />
                <YAxis type="category" dataKey="name" width={96} tick={{ fill: "#94a3b8", fontSize: 11 }} />
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

        <Panel title="Innovation Pillar Coverage" icon={Cpu}>
          <div className="grid max-h-80 gap-2 overflow-y-auto pr-1 md:grid-cols-2">
            {audit?.capabilityAudit.map((item) => (
              <div key={item.capability} className="border border-line bg-void p-3">
                <div className="flex items-start justify-between gap-3">
                  <h3 className="break-words text-sm font-semibold text-white">{item.capability}</h3>
                  <span className={`border px-2 py-1 text-[10px] uppercase ${statusTone[item.status]}`}>{item.status}</span>
                </div>
                <p className="mt-2 text-xs text-slate-500">{item.verifiedSystems.slice(0, 4).join(", ")}</p>
                <p className="mt-1 text-xs text-mint">{Math.round(item.score)}/100</p>
              </div>
            )) ?? <Empty label="Loading innovation pillars." />}
          </div>
        </Panel>
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
        <Panel title="Pillar Continuity" icon={TrendingUp}>
          <div className="h-56 min-w-0">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={pillarTrend} margin={{ left: 0, right: 8, top: 8, bottom: 0 }}>
                <CartesianGrid stroke="#1C2B3A" strokeDasharray="3 3" />
                <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 10 }} />
                <YAxis domain={[80, 100]} tick={{ fill: "#94a3b8", fontSize: 11 }} />
                <Tooltip contentStyle={{ background: "#101827", border: "1px solid #22324a", color: "#fff" }} />
                <Area type="monotone" dataKey="score" stroke="#2EE9D3" fill="#2EE9D3" fillOpacity={0.18} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Panel>
        <Panel title="Connected Ecosystem Workflows" icon={GitBranch}>
          <List items={(audit?.integrationWorkflows ?? []).map((item) => `${item.name}: ${item.chain.join(" -> ")}`)} />
        </Panel>
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-3">
        <Panel title="Enterprise Decisions Solved" icon={Network}>
          <List items={(audit?.enterpriseProblemSolving ?? []).map((item) => `${item.problem}: ${item.decisionSupport}`)} />
        </Panel>
        <Panel title="Competition Differentiation" icon={Sparkles}>
          <List items={(audit?.competitionComparison ?? []).map((item) => `${item.comparator}: ${item.verdict}`)} />
        </Panel>
        <Panel title="Runtime Proof Points" icon={CheckCircle2}>
          <List items={(audit?.performanceMetrics ?? []).map((item) => `${item.metric}: ${item.value}/${item.target} ${item.unit}`)} />
        </Panel>
      </div>

      <div className="mt-4 border border-mint/30 bg-mint/10 p-4 text-sm leading-6 text-mint">
        {audit?.finalAnswer ?? "Final innovation-stack answer pending."}
      </div>
    </section>
  );
}

function Metric({ icon: Icon, label, value }: { icon: LucideIcon; label: string; value: string }) {
  return (
    <div className="border border-line bg-void p-4">
      <div className="flex items-center gap-2 text-xs uppercase text-slate-500">
        <Icon className="size-4 text-mint" />
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
        <Icon className="size-4 text-mint" />
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
