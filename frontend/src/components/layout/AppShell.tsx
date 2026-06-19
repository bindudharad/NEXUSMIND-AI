"use client";

import { Activity, BrainCircuit, Command, Cpu, Database, Gauge, ShieldCheck, Sparkles } from "lucide-react";
import { motion } from "framer-motion";

import { Button } from "@/components/ui/button";
import { useEnterpriseStore } from "@/stores/enterprise-store";

const navigation = [
  { label: "Command Center", group: "Operate", icon: Command },
  { label: "Digital Twin", group: "Mirror", icon: BrainCircuit },
  { label: "AI Managers", group: "Council", icon: Cpu },
  { label: "Risk Shield", group: "Protect", icon: ShieldCheck },
  { label: "Company Memory", group: "Recall", icon: Database },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const activeWorkspace = useEnterpriseStore((state) => state.activeWorkspace);
  const setActiveWorkspace = useEnterpriseStore((state) => state.setActiveWorkspace);

  return (
    <main className="cinematic-shell min-h-screen overflow-hidden text-slate-100">
      <div className="pointer-events-none fixed inset-0 control-grid opacity-60" />
      <div className="pointer-events-none fixed inset-x-0 top-0 h-px bg-cyan/70 shadow-electric" />
      <div className="pointer-events-none fixed inset-0 scanline opacity-18" />

      <div className="relative min-h-screen">
        <aside className="nav-rail group fixed bottom-4 left-4 top-4 z-50 hidden w-[88px] border border-cyan/15 shadow-control backdrop-blur-2xl transition-[width] duration-300 ease-out hover:w-[260px] lg:block">
          <div className="flex h-full flex-col gap-5 p-3">
            <div className="flex min-h-14 items-center gap-3 border border-cyan/25 bg-cyan/10 px-3 shadow-electric">
              <div className="grid size-10 shrink-0 place-items-center border border-cyan/40 bg-void/55">
                <Activity className="size-5 text-cyan" />
              </div>
              <div className="luxury-nav-label min-w-0 opacity-0 group-hover:opacity-100">
                <p className="text-xs uppercase text-cyan">NEXUSMIND AI</p>
                <p className="truncate text-[11px] text-slate-400">Enterprise OS</p>
              </div>
            </div>

            <nav className="flex flex-1 flex-col gap-2" aria-label="Primary command navigation">
              {navigation.map((item) => (
                <Button
                  key={item.label}
                  type="button"
                  variant={activeWorkspace === item.label ? "default" : "secondary"}
                  onClick={() => setActiveWorkspace(item.label)}
                  className={`nav-button h-12 w-full justify-start overflow-hidden px-3 shadow-electric ${
                    activeWorkspace === item.label ? "border-cyan/60 bg-cyan/15 text-white" : ""
                  }`}
                  title={item.label}
                  aria-pressed={activeWorkspace === item.label}
                >
                  <item.icon className="size-5 shrink-0" />
                  <span className="luxury-nav-label min-w-0 translate-x-1 opacity-0 group-hover:translate-x-0 group-hover:opacity-100">
                    <span className="block truncate text-sm">{item.label}</span>
                    <span className="block truncate text-[10px] uppercase text-slate-500">{item.group}</span>
                  </span>
                </Button>
              ))}
            </nav>

            <div className="border border-line/70 bg-void/45 p-3">
              <div className="flex items-center gap-2 text-cyan">
                <Sparkles className="size-4 shrink-0" />
                <span className="luxury-nav-label text-xs uppercase opacity-0 group-hover:opacity-100">Live Intelligence</span>
              </div>
              <div className="luxury-nav-label mt-3 grid gap-2 opacity-0 group-hover:opacity-100">
                <div className="flex items-center justify-between text-[11px] text-slate-400">
                  <span>AI confidence</span>
                  <span className="text-cyan">87%</span>
                </div>
                <div className="hud-progress h-1">
                  <span style={{ width: "87%" }} />
                </div>
              </div>
            </div>
          </div>
        </aside>

        <section className="relative px-4 py-4 sm:px-6 lg:px-8 lg:pl-[120px]">
          <motion.div
            className="mx-auto max-w-[1600px]"
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
          >
            {children}
          </motion.div>
        </section>
      </div>

      <nav
        className="fixed inset-x-3 bottom-3 z-40 grid grid-cols-5 border border-cyan/20 bg-panel/90 p-1 shadow-control backdrop-blur-xl lg:hidden"
        aria-label="Mobile primary"
      >
        {navigation.map((item) => (
          <button
            key={item.label}
            type="button"
            onClick={() => setActiveWorkspace(item.label)}
            className={`grid min-h-12 place-items-center border text-[10px] transition ${
              activeWorkspace === item.label
                ? "border-cyan/50 bg-cyan/15 text-cyan"
                : "border-transparent text-slate-500 hover:border-line/70 hover:text-slate-200"
            }`}
            aria-pressed={activeWorkspace === item.label}
            title={item.label}
          >
            <item.icon className="size-4" />
            <span className="sr-only">{item.label}</span>
          </button>
        ))}
      </nav>

      <div className="pointer-events-none fixed bottom-4 right-4 z-30 hidden border border-cyan/20 bg-panel/80 px-3 py-2 text-[11px] uppercase text-slate-400 shadow-control backdrop-blur-xl xl:flex xl:items-center xl:gap-2">
        <Gauge className="size-4 text-cyan" />
        <span>87% Forecast Confidence</span>
      </div>
    </main>
  );
}
