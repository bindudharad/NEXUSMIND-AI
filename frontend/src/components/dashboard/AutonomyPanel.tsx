"use client";

import { BrainCircuit, Network, Workflow } from "lucide-react";

import type { AgentCouncilResponse, OrgBrainResponse } from "@/types/intelligence";

export function AutonomyPanel({
  council,
  orgBrain,
}: {
  council: AgentCouncilResponse;
  orgBrain: OrgBrainResponse;
}) {
  return (
    <section className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
      <article className="border border-line/80 bg-panel/85 p-5 shadow-control backdrop-blur">
        <div className="flex items-center gap-3">
          <BrainCircuit className="size-5 text-cyan" />
          <div>
            <p className="text-xs uppercase text-cyan">Autonomous Agent Council</p>
            <h2 className="text-xl font-semibold text-white">{council.topic}</h2>
          </div>
          <span className="ml-auto border border-mint/30 px-3 py-1 text-xs uppercase text-mint">
            coordination {council.coordinationScore}%
          </span>
        </div>
        <div className="mt-5 grid gap-3 md:grid-cols-2">
          {council.turns.map((turn) => (
            <div key={turn.agent} className="border border-line/70 bg-panel2/65 p-4">
              <div className="flex items-center justify-between gap-3">
                <strong className="text-sm text-white">{turn.agent}</strong>
                <span className="text-sm text-mint">{turn.confidence}%</span>
              </div>
              <p className="mt-3 text-sm leading-6 text-slate-400">{turn.observation}</p>
              <p className="mt-3 text-sm leading-6 text-cyan">{turn.recommendation}</p>
              <div className="mt-3 grid gap-2 text-xs text-slate-500">
                <span>tools: {turn.toolCalls.slice(0, 2).join(" / ")}</span>
                <span>memory: {turn.memoryKeys.slice(0, 2).join(" / ")}</span>
              </div>
            </div>
          ))}
        </div>
        <div className="mt-4 border border-cyan/30 bg-cyan/10 p-4 text-sm leading-6 text-slate-200">
          {council.decision}
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          {council.workflowTriggers.slice(0, 6).map((trigger) => (
            <span key={trigger} className="border border-line/70 bg-void/60 px-3 py-1 text-xs text-slate-400">
              {trigger.replace(/_/g, " ")}
            </span>
          ))}
        </div>
      </article>

      <article className="border border-line/80 bg-panel/85 p-5 shadow-control backdrop-blur">
        <div className="flex items-center gap-3">
          <Network className="size-5 text-amber" />
          <div>
            <p className="text-xs uppercase text-amber">Organizational Brain AI</p>
            <h2 className="text-xl font-semibold text-white">Dependency graph</h2>
          </div>
        </div>
        <div className="mt-5 grid grid-cols-2 gap-3">
          {orgBrain.nodes.map((node, nodeIndex) => (
            <div key={`${node.id}-${nodeIndex}`} className="border border-line/70 bg-panel2/65 p-3">
              <span className="text-sm text-white">{node.label}</span>
              <div className="mt-2 h-2 bg-line">
                <div className="h-full bg-amber" style={{ width: `${node.risk}%` }} />
              </div>
              <span className="mt-2 block text-xs text-slate-500">risk {node.risk}</span>
            </div>
          ))}
        </div>
        <div className="mt-4 space-y-2">
          {orgBrain.bottlenecks.map((bottleneck, bottleneckIndex) => (
            <p key={`${bottleneck}-${bottleneckIndex}`} className="text-sm leading-6 text-slate-400">
              {bottleneck}
            </p>
          ))}
        </div>
        <div className="mt-4 flex items-start gap-3 border border-line/70 bg-void/50 p-3 text-sm leading-6 text-slate-300">
          <Workflow className="mt-1 size-4 text-cyan" />
          {orgBrain.recommendation}
        </div>
      </article>
    </section>
  );
}
