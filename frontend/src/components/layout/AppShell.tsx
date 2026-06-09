"use client";

import { Activity, BrainCircuit, Command, Cpu, Database, ShieldCheck } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useEnterpriseStore } from "@/stores/enterprise-store";

const navigation = [
  { label: "Command Center", icon: Command },
  { label: "Digital Twin", icon: BrainCircuit },
  { label: "AI Managers", icon: Cpu },
  { label: "Risk Shield", icon: ShieldCheck },
  { label: "Company Memory", icon: Database },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const activeWorkspace = useEnterpriseStore((state) => state.activeWorkspace);
  const setActiveWorkspace = useEnterpriseStore((state) => state.setActiveWorkspace);

  return (
    <main className="cinematic-shell min-h-screen overflow-hidden text-slate-100">
      <div className="pointer-events-none fixed inset-0 control-grid opacity-60" />
      <div className="pointer-events-none fixed inset-x-0 top-0 h-px bg-cyan/70 shadow-electric" />
      <div className="pointer-events-none fixed inset-0 scanline opacity-18" />

      <div className="relative grid min-h-screen grid-cols-1 lg:grid-cols-[88px_1fr]">
        <aside className="hidden border-r border-cyan/15 bg-panel/70 shadow-control backdrop-blur-xl lg:block">
          <div className="flex h-full flex-col items-center gap-6 py-6">
            <div className="grid size-12 place-items-center border border-cyan/40 bg-cyan/10 shadow-control">
              <Activity className="size-6 text-cyan" />
            </div>
            <nav className="flex flex-1 flex-col gap-3" aria-label="Primary command navigation">
              {navigation.map((item) => (
                <Button
                  key={item.label}
                  type="button"
                  variant={activeWorkspace === item.label ? "default" : "secondary"}
                  size="icon"
                  onClick={() => setActiveWorkspace(item.label)}
                  className="grid shadow-electric"
                  title={item.label}
                  aria-pressed={activeWorkspace === item.label}
                >
                  <item.icon className="size-5" />
                </Button>
              ))}
            </nav>
          </div>
        </aside>

        <section className="relative px-4 py-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-[1600px]">
            {children}
          </div>
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
          </button>
        ))}
      </nav>
    </main>
  );
}
