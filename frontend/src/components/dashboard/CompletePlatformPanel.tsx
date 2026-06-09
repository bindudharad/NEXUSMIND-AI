"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type React from "react";
import { motion } from "framer-motion";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { BrainCircuit, CheckCircle2, Cloud, Database, Layers3, Loader2, Network, RefreshCw, ShieldCheck, Sparkles } from "lucide-react";

import type { CompletePlatformResponse, PlatformCapability, PlatformCapabilityStatus } from "@/types/platform";

const statusClass: Record<PlatformCapabilityStatus, string> = {
  ready: "border-mint/45 bg-mint/10 text-mint",
  configured: "border-cyan/45 bg-cyan/10 text-cyan",
  warning: "border-amber/45 bg-amber/10 text-amber",
  missing: "border-signal/45 bg-signal/10 text-signal",
  error: "border-signal/45 bg-signal/10 text-signal",
};

const categoryColor: Record<string, string> = {
  ai_product: "#2EE9D3",
  deployment: "#7CF0A6",
};

export function CompletePlatformPanel() {
  const [platform, setPlatform] = useState<CompletePlatformResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadPlatform = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/platform/operating-system", { cache: "no-store" });
      if (!response.ok) throw new Error("Complete platform endpoint failed");
      setPlatform((await response.json()) as CompletePlatformResponse);
    } catch {
      setError("Complete platform verification could not reach the live enterprise AI backend.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const firstRefresh = window.setTimeout(() => {
      void loadPlatform();
    }, 2200);
    return () => window.clearTimeout(firstRefresh);
  }, [loadPlatform]);

  const capabilityChart = useMemo(
    () =>
      platform?.capabilities.map((capability) => ({
        name: capability.name.replace("AI ", "").replace("Prediction", "Pred."),
        score: Math.round(capability.score),
        category: capability.category,
      })) ?? [],
    [platform],
  );

  const productCapabilities = useMemo(
    () => platform?.capabilities.filter((capability) => capability.category === "ai_product") ?? [],
    [platform],
  );
  const deploymentCapabilities = useMemo(
    () => platform?.capabilities.filter((capability) => capability.category === "deployment") ?? [],
    [platform],
  );

  return (
    <section className="border border-cyan/25 bg-panel/85 p-5 shadow-control backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <Sparkles className="size-5 text-cyan" />
          <div>
            <p className="text-xs uppercase text-cyan">Complete NEXUSMIND AI Enterprise Platform</p>
            <h2 className="text-xl font-semibold text-white">AI operating system coverage across product, models, data, realtime, and cloud infrastructure</h2>
          </div>
        </div>
        <button onClick={() => void loadPlatform()} className="inline-flex items-center gap-2 border border-line bg-panel2 px-3 py-2 text-sm text-slate-300">
          {loading ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />}
          Verify complete platform
        </button>
      </div>

      {loading ? <p className="mt-5 text-sm text-slate-400">Validating the full enterprise operating system feature map...</p> : null}
      {error ? <p className="mt-4 text-sm text-signal">{error}</p> : null}

      {platform ? (
        <>
          <div className="mt-5 grid gap-3 md:grid-cols-5">
            <ScoreTile icon={ShieldCheck} label="Platform score" value={`${platform.summary.platformScore.toFixed(1)}%`} tone="text-mint" />
            <ScoreTile icon={CheckCircle2} label="Ready systems" value={`${platform.summary.ready}/${platform.summary.totalCapabilities}`} tone="text-cyan" />
            <ScoreTile icon={Network} label="Realtime streams" value={String(platform.summary.realtimeStreams)} tone="text-amber" />
            <ScoreTile icon={Cloud} label="Cloud native" value={`${platform.summary.cloudNativeScore.toFixed(0)}%`} tone="text-mint" />
            <ScoreTile icon={BrainCircuit} label="AI systems" value={String(productCapabilities.length)} tone="text-purple-300" />
          </div>

          <div className="mt-5 border border-cyan/25 bg-cyan/10 p-4">
            <p className="text-xs uppercase text-cyan">Executive brief</p>
            <p className="mt-2 text-sm leading-6 text-slate-300">{platform.executiveBrief}</p>
          </div>

          <div className="mt-5 grid gap-4 xl:grid-cols-[1.15fr_0.85fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-mint">
                <Layers3 className="size-4" />
                Capability readiness map
              </div>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={capabilityChart.slice(0, 25)} margin={{ left: -18, right: 8, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="name" stroke="#64748b" tickLine={false} axisLine={false} tick={false} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} domain={[0, 100]} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Bar dataKey="score" radius={[3, 3, 0, 0]}>
                      {capabilityChart.slice(0, 25).map((entry) => (
                        <Cell key={entry.name} fill={categoryColor[entry.category] ?? "#2EE9D3"} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
                <Database className="size-4" />
                Enterprise stacks
              </div>
              <StackList title="AI infrastructure" items={platform.aiStack} />
              <StackList title="Data systems" items={platform.dataStack} />
              <StackList title="DevOps" items={platform.devopsStack} />
            </article>
          </div>

          <div className="mt-5 grid gap-4 xl:grid-cols-[1fr_0.75fr]">
            <div className="grid gap-3 md:grid-cols-2">
              {productCapabilities.map((capability, index) => (
                <motion.div
                  key={capability.id}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.25, delay: Math.min(index * 0.015, 0.2) }}
                >
                  <CapabilityCard capability={capability} />
                </motion.div>
              ))}
            </div>

            <div className="grid content-start gap-3">
              {deploymentCapabilities.map((capability) => (
                <CapabilityCard key={capability.id} capability={capability} />
              ))}
              <article className="border border-line/70 bg-panel2/65 p-4">
                <p className="text-xs uppercase text-slate-500">Enterprise dashboards</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {platform.dashboards.map((dashboard) => (
                    <span key={dashboard} className="border border-line/60 bg-panel/70 px-2 py-1 text-[11px] text-slate-400">
                      {dashboard}
                    </span>
                  ))}
                </div>
              </article>
            </div>
          </div>
        </>
      ) : null}
    </section>
  );
}

function CapabilityCard({ capability }: { capability: PlatformCapability }) {
  return (
    <article className="border border-line/70 bg-panel2/65 p-4">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <p className="text-[11px] uppercase text-slate-500">{capability.category.replace("_", " ")}</p>
          <h3 className="mt-1 text-sm font-medium text-white">{capability.name}</h3>
        </div>
        <span className={`border px-2 py-1 text-[11px] uppercase ${statusClass[capability.status]}`}>{capability.status}</span>
      </div>
      <div className="mt-3 h-2 bg-void">
        <div className="h-full bg-cyan" style={{ width: `${capability.score}%` }} />
      </div>
      <p className="mt-3 text-xs leading-5 text-slate-400">{capability.details}</p>
      <p className="mt-3 text-xs leading-5 text-mint">{capability.recommendation}</p>
      <div className="mt-3 flex flex-wrap gap-2">
        {capability.evidence.slice(0, 3).map((item) => (
          <span key={item} className="border border-line/50 px-2 py-1 text-[11px] text-slate-500">
            {item}
          </span>
        ))}
      </div>
    </article>
  );
}

function StackList({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="mb-4 last:mb-0">
      <p className="text-[11px] uppercase text-slate-500">{title}</p>
      <div className="mt-2 grid gap-2">
        {items.map((item) => (
          <div key={item} className="border border-line/50 bg-panel/60 px-3 py-2 text-xs leading-5 text-slate-400">
            {item}
          </div>
        ))}
      </div>
    </div>
  );
}

function ScoreTile({
  icon: Icon,
  label,
  value,
  tone,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
  tone: string;
}) {
  return (
    <div className="border border-line/70 bg-panel2/65 p-4">
      <div className="flex items-center gap-2 text-slate-500">
        <Icon className="size-4 text-cyan" />
        <span className="text-[11px] uppercase">{label}</span>
      </div>
      <strong className={`mt-2 block text-2xl font-semibold ${tone}`}>{value}</strong>
    </div>
  );
}
