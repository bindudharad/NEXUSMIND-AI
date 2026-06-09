import { SelfLearningCompanyAIPanel } from "@/components/dashboard/SelfLearningCompanyAIPanel";
import { AppShell } from "@/components/layout/AppShell";

export default function SelfLearningAIPage() {
  return (
    <AppShell>
      <header className="mb-4 border border-line/80 bg-panel/80 p-5 shadow-control backdrop-blur">
        <div className="flex flex-wrap items-center gap-3 text-xs uppercase text-cyan">
          <span>NEXUSMIND AI</span>
          <span className="h-px w-8 bg-cyan/40" />
          <span>Adaptive Intelligence Engine</span>
        </div>
        <h1 className="mt-3 text-3xl font-semibold text-white sm:text-5xl">AI Self-Learning System</h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-400">
          Feedback, forecast accuracy, drift detection, retraining, digital twin signals, and agent learning operate as one autonomous improvement loop.
        </p>
      </header>

      <SelfLearningCompanyAIPanel />
    </AppShell>
  );
}
