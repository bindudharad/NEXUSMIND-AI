import { BrainCircuit, Database, GitBranch, Network, Workflow } from "lucide-react";
import type React from "react";

import { LivingCompanyBrainPanel } from "@/components/dashboard/LivingCompanyBrainPanel";
import { AppShell } from "@/components/layout/AppShell";

export default function LivingCompanyBrainPage() {
  return (
    <AppShell>
      <header className="mb-4 border border-cyan/30 bg-panel/90 p-5 shadow-control backdrop-blur">
        <div className="flex flex-wrap items-center gap-2 text-xs uppercase text-cyan">
          <BrainCircuit className="size-4" />
          <span>NEXUSMIND AI</span>
          <span className="h-px w-8 bg-cyan/40" />
          <span>Living AI Company Brain</span>
        </div>
        <h1 className="mt-3 text-3xl font-semibold text-white sm:text-5xl">A Living Digital Organism For Enterprise Intelligence</h1>
        <p className="mt-3 max-w-4xl text-sm leading-6 text-slate-400">
          This focused demo shows the connected brain layer: company awareness, enterprise memory, causal reasoning, predictions, simulations,
          digital twins, autonomous AI managers, and self-learning intelligence operating as one system.
        </p>
        <div className="mt-4 grid gap-3 md:grid-cols-5">
          <DemoSignal icon={Database} label="Memory" />
          <DemoSignal icon={Network} label="Digital Twins" />
          <DemoSignal icon={GitBranch} label="Reasoning" />
          <DemoSignal icon={Workflow} label="AI Agents" />
          <DemoSignal icon={BrainCircuit} label="Learning" />
        </div>
      </header>
      <LivingCompanyBrainPanel />
    </AppShell>
  );
}

function DemoSignal({ icon: Icon, label }: { icon: React.ComponentType<{ className?: string }>; label: string }) {
  return (
    <div className="border border-line bg-panel2 px-3 py-2 text-xs uppercase text-slate-300">
      <div className="flex items-center gap-2">
        <Icon className="size-4 text-cyan" />
        <span>{label}</span>
      </div>
    </div>
  );
}
