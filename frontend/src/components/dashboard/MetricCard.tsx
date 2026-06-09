"use client";

import { ArrowDownRight, ArrowUpRight } from "lucide-react";

import type { EnterpriseMetric } from "@/types/dashboard";

const statusTone: Record<EnterpriseMetric["status"], string> = {
  optimal: "border-mint/30 text-mint",
  watch: "border-amber/40 text-amber",
  risk: "border-signal/40 text-signal",
};

export function MetricCard({ metric }: { metric: EnterpriseMetric }) {
  const isPositive = metric.trend >= 0;
  const TrendIcon = isPositive ? ArrowUpRight : ArrowDownRight;
  const progress = Math.min(100, Math.max(16, Math.abs(metric.trend) * 4 + 44));

  return (
    <article className="cinematic-card p-4 transition">
      <div className="hud-content">
        <div className="flex items-start justify-between gap-3">
          <p className="text-xs uppercase text-slate-500">{metric.label}</p>
          <span className={`border px-2 py-1 text-[10px] uppercase ${statusTone[metric.status]}`}>
            {metric.status}
          </span>
        </div>
        <div className="mt-5 flex items-end justify-between">
          <strong className="count-up text-3xl font-semibold text-white">{metric.value}</strong>
          <span className={`flex items-center gap-1 text-sm ${isPositive ? "text-mint" : "text-amber"}`}>
            <TrendIcon className="size-4" />
            {Math.abs(metric.trend).toFixed(1)}%
          </span>
        </div>
        <div className="hud-progress mt-4 h-1">
          <span style={{ width: `${progress}%` }} />
        </div>
      </div>
    </article>
  );
}
