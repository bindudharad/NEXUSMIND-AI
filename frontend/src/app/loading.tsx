import { BrainCircuit, Radio, Sparkles } from "lucide-react";

export default function Loading() {
  return (
    <main className="cinematic-shell grid min-h-screen place-items-center px-4 text-slate-100">
      <section className="hud-panel neural-loader p-6">
        <div className="neural-mesh" />
        <div className="hud-content grid min-h-[220px] place-items-center text-center">
          <div className="voice-orb grid size-24 place-items-center border border-cyan/40 bg-cyan/10">
            <BrainCircuit className="size-10 text-cyan" />
          </div>
          <div>
            <p className="premium-kicker mx-auto mt-6 w-fit">
              <Radio className="size-3" />
              Synchronizing enterprise intelligence
            </p>
            <h1 className="mt-4 text-2xl font-semibold text-white sm:text-3xl">Preparing the command center</h1>
            <p className="mt-2 text-sm text-slate-400">Loading digital twins, forecasts, AI agents, and executive memory.</p>
          </div>
          <div className="mt-6 grid w-full gap-2">
            <div className="skeleton-shimmer h-2 w-full" />
            <div className="skeleton-shimmer h-2 w-4/5" />
            <div className="skeleton-shimmer h-2 w-2/3" />
          </div>
          <div className="mt-5 flex items-center gap-2 text-xs uppercase text-cyan">
            <Sparkles className="size-4 animate-pulse" />
            AI systems online
          </div>
        </div>
      </section>
    </main>
  );
}
