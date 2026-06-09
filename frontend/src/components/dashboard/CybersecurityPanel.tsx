"use client";

import { LockKeyhole, ShieldAlert } from "lucide-react";

import type { SecurityEvent } from "@/types/intelligence";

export function CybersecurityPanel({ events }: { events: SecurityEvent[] }) {
  return (
    <section className="border border-line/80 bg-panel/85 p-5 shadow-control backdrop-blur">
      <div className="flex items-center gap-3">
        <ShieldAlert className="size-5 text-amber" />
        <div>
          <p className="text-xs uppercase text-amber">AI Cybersecurity System</p>
          <h2 className="text-xl font-semibold text-white">Threat response console</h2>
        </div>
      </div>

      <div className="mt-5 space-y-3">
        {events.map((event) => (
          <article key={event.id} className="border border-line/70 bg-panel2/65 p-4">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="font-medium text-white">{event.title}</h3>
                <p className="mt-1 text-sm text-slate-500">{event.actor}</p>
              </div>
              <span className="border border-amber/40 bg-amber/10 px-2 py-1 text-xs uppercase text-amber">
                {event.status}
              </span>
            </div>
            <div className="mt-4 flex items-center gap-3">
              <LockKeyhole className="size-4 text-cyan" />
              <div className="h-2 flex-1 bg-line">
                <div className="h-full bg-amber" style={{ width: `${event.threatScore}%` }} />
              </div>
              <span className="w-10 text-right text-sm text-white">{event.threatScore}</span>
            </div>
            <p className="mt-3 text-sm leading-6 text-slate-400">{event.response}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
