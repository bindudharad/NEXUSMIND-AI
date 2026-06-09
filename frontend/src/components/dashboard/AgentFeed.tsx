"use client";

import { Bot } from "lucide-react";

import type { AgentMessage } from "@/types/dashboard";

const severityTone: Record<AgentMessage["severity"], string> = {
  optimal: "text-mint border-mint/30",
  watch: "text-amber border-amber/30",
  risk: "text-signal border-signal/30",
  critical: "text-signal border-signal/50",
};

export function AgentFeed({ messages }: { messages: AgentMessage[] }) {
  return (
    <section className="border border-line/80 bg-panel/85 p-5 shadow-control backdrop-blur">
      <div className="flex items-center gap-3">
        <Bot className="size-5 text-cyan" />
        <div>
          <p className="text-xs uppercase text-cyan">Multi-Agent Brain</p>
          <h2 className="text-xl font-semibold text-white">Live agent discussion</h2>
        </div>
      </div>
      <div className="mt-5 space-y-3">
        {messages.map((message) => (
          <article key={`${message.agent}-${message.message}`} className="border border-line/70 bg-panel2/70 p-4">
            <div className="flex items-center justify-between gap-3">
              <strong className="text-sm text-white">{message.agent}</strong>
              <span className={`border px-2 py-1 text-[10px] uppercase ${severityTone[message.severity]}`}>
                {message.severity}
              </span>
            </div>
            <p className="mt-3 text-sm leading-6 text-slate-400">{message.message}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
