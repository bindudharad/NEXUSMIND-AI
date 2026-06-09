"use client";

import { AlertTriangle } from "lucide-react";

import type { RiskSignal } from "@/types/dashboard";

export function RiskPanel({ risks }: { risks: RiskSignal[] }) {
  return (
    <section className="border border-line/80 bg-panel/85 p-5 shadow-signal backdrop-blur">
      <div className="flex items-center gap-3">
        <AlertTriangle className="size-5 text-amber" />
        <div>
          <p className="text-xs uppercase text-amber">Risk Analyzer</p>
          <h2 className="text-xl font-semibold text-white">Predictive alerts</h2>
        </div>
      </div>
      <div className="mt-5 space-y-4">
        {risks.map((risk) => (
          <article key={risk.id} className="border border-line/70 bg-panel2/70 p-4">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="font-medium text-white">{risk.name}</h3>
                <p className="mt-2 text-sm leading-6 text-slate-400">{risk.recommendation}</p>
              </div>
              <span className="border border-signal/40 bg-signal/10 px-2 py-1 text-xs uppercase text-signal">
                {risk.impact}
              </span>
            </div>
            <div className="mt-4 flex items-center gap-3">
              <div className="h-2 flex-1 bg-line">
                <div className="h-full bg-signal" style={{ width: `${risk.probability * 100}%` }} />
              </div>
              <span className="text-sm text-slate-300">{Math.round(risk.probability * 100)}%</span>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
