"use client";

import { Flame, HeartPulse } from "lucide-react";

import type { BurnoutSignal } from "@/types/intelligence";

const metrics: Array<keyof Pick<BurnoutSignal, "burnout" | "stress" | "attrition" | "meetingLoad">> = [
  "burnout",
  "stress",
  "attrition",
  "meetingLoad",
];

function cellColor(value: number) {
  if (value >= 75) return "bg-signal text-white shadow-signal";
  if (value >= 55) return "bg-amber/80 text-void";
  return "bg-mint/70 text-void";
}

export function BurnoutHeatmap({ signals }: { signals: BurnoutSignal[] }) {
  return (
    <section className="border border-line/80 bg-panel/85 p-5 shadow-control backdrop-blur">
      <div className="flex items-center gap-3">
        <HeartPulse className="size-5 text-signal" />
        <div>
          <p className="text-xs uppercase text-signal">Employee Intelligence AI</p>
          <h2 className="text-xl font-semibold text-white">Burnout and attrition heatmap</h2>
        </div>
      </div>

      <div className="mt-5 grid gap-3">
        {signals.map((signal) => (
          <article key={signal.department} className="border border-line/70 bg-panel2/65 p-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h3 className="font-medium text-white">{signal.department}</h3>
              <span className="flex items-center gap-2 text-sm text-slate-400">
                <Flame className="size-4 text-signal" />
                {signal.recommendation}
              </span>
            </div>
            <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
              {metrics.map((metric) => (
                <div key={metric} className={`p-3 ${cellColor(signal[metric])}`}>
                  <span className="block text-[11px] uppercase">{metric.replace("Load", " load")}</span>
                  <strong className="mt-1 block text-2xl">{signal[metric]}</strong>
                </div>
              ))}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
