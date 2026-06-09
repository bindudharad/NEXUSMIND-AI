"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { BriefcaseBusiness, Loader2, Microscope, Radio, RefreshCw, Rocket, ShieldCheck, Trophy } from "lucide-react";

import type { ImpressionStatus, RecruiterImpressionResponse } from "@/types/recruiter-impression";

type SnakeRecord = Record<string, unknown>;

const statusStyle: Record<ImpressionStatus, string> = {
  elite: "border-mint/45 bg-mint/10 text-mint",
  strong: "border-cyan/45 bg-cyan/10 text-cyan",
  needs_work: "border-amber/45 bg-amber/10 text-amber",
  weak: "border-signal/45 bg-signal/10 text-signal",
};

const categoryColor: Record<string, string> = {
  real_world: "#2EE9D3",
  business: "#7CF0A6",
  ai_engineering: "#A78BFA",
  full_stack: "#38BDF8",
  data_science: "#F6B44B",
  scalability: "#8BE9FD",
  startup_product: "#7CF0A6",
  industry_platform: "#2EE9D3",
  research: "#C084FC",
  recruiter: "#F6B44B",
  judge_wow: "#FF3B6B",
};

export function RecruiterImpressionPanel() {
  const [audit, setAudit] = useState<RecruiterImpressionResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [streamStatus, setStreamStatus] = useState("connecting");

  const loadAudit = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/recruiter-impression/summary", { cache: "no-store" });
      if (!response.ok) throw new Error("Recruiter impression audit failed");
      setAudit((await response.json()) as RecruiterImpressionResponse);
    } catch {
      setError("Recruiter impression auditor could not verify the platform.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    async function connectStream() {
      try {
        const response = await fetch("/api/recruiter-impression/stream", { cache: "no-store", signal: controller.signal });
        const reader = response.body?.getReader();
        if (!reader) throw new Error("Missing recruiter stream");
        const decoder = new TextDecoder();
        let buffer = "";
        setStreamStatus("streaming");
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const events = buffer.split("\n\n");
          buffer = events.pop() ?? "";
          for (const event of events) {
            const dataLine = event.split("\n").find((line) => line.startsWith("data: "));
            if (dataLine) {
              setAudit(toCamel<RecruiterImpressionResponse>(JSON.parse(dataLine.slice(6))));
              setLoading(false);
            }
          }
        }
        setStreamStatus("polling");
      } catch {
        if (!controller.signal.aborted) setStreamStatus("polling");
      }
    }

    const firstRefresh = window.setTimeout(() => {
      void loadAudit();
    }, 4200);
    const streamRefresh = window.setTimeout(() => {
      void connectStream();
    }, 14000);
    return () => {
      controller.abort();
      window.clearTimeout(firstRefresh);
      window.clearTimeout(streamRefresh);
    };
  }, [loadAudit]);

  const dimensionChart = useMemo(
    () =>
      audit?.dimensions.map((dimension) => ({
        name: shortName(dimension.name),
        score: Math.round(dimension.score),
        category: dimension.category,
      })) ?? [],
    [audit],
  );

  return (
    <section className="border border-mint/25 bg-panel/85 p-5 shadow-control backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <Trophy className="size-5 text-mint" />
          <div>
            <p className="text-xs uppercase text-mint">Recruiter Impression Auditor</p>
            <h2 className="text-xl font-semibold text-white">Startup, industry, research, recruiter, and judge impact verification</h2>
          </div>
        </div>
        <button onClick={() => void loadAudit()} className="inline-flex items-center gap-2 border border-line bg-panel2 px-3 py-2 text-sm text-slate-300">
          {loading ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />}
          Verify impression
        </button>
      </div>

      {error ? <p className="mt-4 text-sm text-signal">{error}</p> : null}
      {loading ? <p className="mt-5 text-sm text-slate-400">Auditing business realism, AI engineering, full-stack quality, research depth, and demo impact...</p> : null}

      {audit ? (
        <>
          <div className="mt-5 grid gap-3 md:grid-cols-6">
            <Score label="Overall" value={audit.summary.overallScore} tone="text-mint" />
            <Score label="Startup" value={audit.summary.startupScore} tone="text-cyan" />
            <Score label="Industry" value={audit.summary.industryScore} tone="text-cyan" />
            <Score label="Research" value={audit.summary.researchScore} tone="text-purple-300" />
            <Score label="Recruiter" value={audit.summary.recruiterScore} tone="text-amber" />
            <Score label="Wow" value={audit.summary.judgeWowScore} tone="text-signal" />
          </div>

          <div className="mt-5 grid gap-4 xl:grid-cols-[1fr_0.9fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-mint">
                <ShieldCheck className="size-4" />
                Product-quality verdict
              </div>
              <p className="text-sm leading-6 text-slate-300">{audit.summary.verdict}</p>
              <p className="mt-3 text-sm leading-6 text-slate-400">{audit.summary.strongestSignal}</p>
              <div className="mt-4 grid gap-2 sm:grid-cols-3">
                {audit.metrics.slice(0, 6).map((metric) => (
                  <div key={metric.label} className="border border-line/60 bg-panel/60 p-3">
                    <span className="block text-[11px] uppercase text-slate-500">{metric.label}</span>
                    <strong className="mt-1 block break-words text-lg text-white">{metric.value}</strong>
                    <p className="mt-1 text-xs leading-5 text-slate-500">{metric.explanation}</p>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
                <Rocket className="size-4" />
                Investor-grade scorecard
              </div>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={dimensionChart} layout="vertical" margin={{ left: 24, right: 10, top: 2, bottom: 2 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis type="number" domain={[0, 100]} stroke="#64748b" tickLine={false} axisLine={false} />
                    <YAxis type="category" dataKey="name" width={94} stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Bar dataKey="score" radius={[0, 3, 3, 0]}>
                      {dimensionChart.map((entry) => (
                        <Cell key={entry.name} fill={categoryColor[entry.category] ?? "#2EE9D3"} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[1fr_1fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-purple-300">
                <Microscope className="size-4" />
                Verified dimensions
              </div>
              <div className="grid gap-3">
                {audit.dimensions.map((dimension) => (
                  <div key={dimension.name} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <h3 className="text-sm font-medium text-white">{dimension.name}</h3>
                      <span className={`border px-2 py-1 text-[11px] uppercase ${statusStyle[dimension.status]}`}>{dimension.status.replace("_", " ")}</span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{dimension.verdict}</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {dimension.evidence.slice(0, 4).map((item) => (
                        <span key={item} className="border border-line/50 px-2 py-1 text-[11px] text-slate-500">
                          {item}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-amber">
                <BriefcaseBusiness className="size-4" />
                Demo moments and proof
              </div>
              <div className="grid gap-3">
                {audit.demoMoments.map((moment) => (
                  <div key={moment.title} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <h3 className="text-sm font-medium text-white">{moment.title}</h3>
                      <span className="text-[11px] text-cyan">{moment.component}</span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{moment.narrative}</p>
                    <p className="mt-2 text-xs leading-5 text-slate-300">{moment.proof}</p>
                  </div>
                ))}
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[1fr_0.85fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-mint">
                <Radio className="size-4" />
                Technical receipts
              </div>
              <div className="grid gap-2">
                {audit.technicalProof.slice(0, 8).map((proof) => (
                  <p key={proof} className="border border-line/50 bg-panel/60 px-3 py-2 text-xs leading-5 text-slate-400">
                    {proof}
                  </p>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 text-xs uppercase text-slate-500">Residual risk and stream</div>
              <div className="grid gap-3">
                <Score label="Risk level" value={audit.summary.residualRiskLevel === "low" ? 92 : audit.summary.residualRiskLevel === "medium" ? 70 : 45} tone="text-slate-300" />
                <div className="border border-line/60 bg-panel/60 p-3">
                  <span className="block text-[11px] uppercase text-slate-500">Stream</span>
                  <strong className="mt-1 block text-base text-cyan">{streamStatus}</strong>
                </div>
                {audit.residualRisks.slice(0, 4).map((risk) => (
                  <p key={risk} className="border border-line/50 bg-panel/60 px-3 py-2 text-xs leading-5 text-slate-400">
                    {risk}
                  </p>
                ))}
              </div>
            </article>
          </div>
        </>
      ) : null}
    </section>
  );
}

function Score({ label, value, tone }: { label: string; value: number; tone: string }) {
  return (
    <div className="border border-line/70 bg-panel2/65 p-3">
      <span className="block text-[11px] uppercase text-slate-500">{label}</span>
      <strong className={`mt-1 block text-2xl font-semibold ${tone}`}>{Math.round(value)}</strong>
    </div>
  );
}

function shortName(name: string) {
  return name
    .replace("Enterprise ", "")
    .replace("Engineering ", "Eng ")
    .replace("Quality", "")
    .replace("Problem Solving", "Problems")
    .replace("Recruiter Signal Strength", "Recruiter")
    .replace("Judge WOW Factor", "Wow");
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
