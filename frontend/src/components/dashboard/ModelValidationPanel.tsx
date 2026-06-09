"use client";

import { Brain, GitCompareArrows } from "lucide-react";

import type { ModelValidationResponse } from "@/types/intelligence";

export function ModelValidationPanel({ validation }: { validation: ModelValidationResponse }) {
  return (
    <section className="border border-line/80 bg-panel/85 p-5 shadow-control backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <Brain className="size-5 text-mint" />
          <div>
            <p className="text-xs uppercase text-mint">Verified ML Systems</p>
            <h2 className="text-xl font-semibold text-white">Random Forest, XGBoost, Neural Network</h2>
          </div>
        </div>
        <span className="border border-mint/40 bg-mint/10 px-3 py-1 text-sm text-mint">
          {validation.available ? "Artifacts online" : "Training required"}
        </span>
      </div>

      <div className="mt-5 grid gap-3 md:grid-cols-3">
        {validation.metrics.map((metric) => (
          <article key={metric.model} className="border border-line/70 bg-panel2/65 p-4">
            <h3 className="font-medium text-white">{metric.model}</h3>
            <div className="mt-4 grid grid-cols-3 gap-2">
              <Score label="Acc" value={metric.accuracy} />
              <Score label="AUC" value={metric.rocAuc} />
              <Score label="F1" value={metric.f1} />
            </div>
            <p className="mt-3 text-xs text-slate-500">{metric.trainedSamples} processed samples</p>
          </article>
        ))}
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-3 border border-cyan/25 bg-cyan/10 p-4">
        <GitCompareArrows className="size-5 text-cyan" />
        {Object.entries(validation.predictionSample).map(([model, value]) => (
          <span key={model} className="text-sm text-slate-300">
            {model.replaceAll("_", " ")}: <strong className="text-white">{Math.round(value * 100)}%</strong>
          </span>
        ))}
      </div>
    </section>
  );
}

function Score({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <span className="block text-[11px] uppercase text-slate-500">{label}</span>
      <strong className="mt-1 block text-lg text-white">{value.toFixed(3)}</strong>
    </div>
  );
}
